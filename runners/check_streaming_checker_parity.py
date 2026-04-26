#!/usr/bin/env python3
"""Check pass/fail parity between default and streaming behavior checkers.

This script is intentionally separate from normal scoring.  It is a validation
tool for the experimental streaming-checker path:

1. find existing ``tran.csv`` files for supported streaming tasks;
2. run the default checker with streaming disabled;
3. run the streaming checker on the same CSV;
4. require exact score parity whenever the default checker completes.

If the default checker times out, the row is reported as ``original_timeout`` and
is not counted as parity evidence.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import multiprocessing as mp
import os
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from simulate_evas import evaluate_behavior, evaluate_streaming_behavior


ROOT = Path(__file__).resolve().parents[1]

STREAMING_TASKS = {
    "pfd_deadzone_smoke",
    "pfd_reset_race_smoke",
    "dac_binary_clk_4b_smoke",
    "sar_adc_dac_weighted_8b_smoke",
    "dwa_ptr_gen_no_overlap_smoke",
    "digital_basics_smoke",
    "gray_counter_one_bit_change_smoke",
    "dwa_wraparound_smoke",
    "gain_extraction_smoke",
    "multimod_divider_ratio_switch_smoke",
}


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def _infer_task_id(csv_path: Path) -> str | None:
    for parent in [csv_path.parent, *csv_path.parents]:
        if parent.name in STREAMING_TASKS:
            return parent.name
        result_path = parent / "result.json"
        if result_path.exists():
            try:
                result = json.loads(result_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            task_id = str(result.get("task_id") or parent.name)
            if task_id in STREAMING_TASKS:
                return task_id
    return None


def _worker(task_id: str, csv_path: str, mode: str, queue: mp.Queue) -> None:
    try:
        if mode == "original":
            os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)
            queue.put(("ok", evaluate_behavior(task_id, Path(csv_path))))
        elif mode == "streaming":
            os.environ["VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS"] = "1"
            result = evaluate_streaming_behavior(task_id, Path(csv_path))
            if result is None:
                queue.put(("error", "streaming_checker_not_registered"))
            else:
                queue.put(("ok", result))
        else:
            queue.put(("error", f"unknown_mode={mode}"))
    except Exception as exc:  # noqa: BLE001 - worker boundary for experiment audit.
        queue.put(("error", f"{type(exc).__name__}: {str(exc)[:300]}"))


def _run_with_timeout(task_id: str, csv_path: Path, mode: str, timeout_s: float) -> dict[str, Any]:
    ctx = mp.get_context("spawn")
    queue: mp.Queue = ctx.Queue(maxsize=1)
    proc = ctx.Process(target=_worker, args=(task_id, str(csv_path), mode, queue))
    start = time.perf_counter()
    proc.start()
    proc.join(timeout_s)
    elapsed = time.perf_counter() - start
    if proc.is_alive():
        proc.terminate()
        proc.join(2)
        if proc.is_alive():
            proc.kill()
            proc.join(2)
        return {"kind": "timeout", "elapsed_s": elapsed, "score": None, "notes": [f"{mode}_timeout>{timeout_s}s"]}
    if queue.empty():
        return {"kind": "error", "elapsed_s": elapsed, "score": None, "notes": [f"{mode}_no_result"]}
    status, payload = queue.get()
    if status != "ok":
        return {"kind": "error", "elapsed_s": elapsed, "score": None, "notes": [str(payload)]}
    score, notes = payload
    return {"kind": "ok", "elapsed_s": elapsed, "score": float(score), "notes": [str(note) for note in notes]}


def _write_csv(csv_path: Path, fieldnames: list[str], rows: list[dict[str, float]]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, 0.0) for name in fieldnames})


def _bits(prefix: str, width: int, code: int) -> dict[str, float]:
    return {f"{prefix}_{idx}": 1.0 if (code >> idx) & 1 else 0.0 for idx in range(width)}


def _dwa_row(
    time_s: float,
    clk: float,
    rst: float,
    *,
    ptr_idx: int | None = None,
    cell_set: set[int] | None = None,
    code: int = 0,
) -> dict[str, float]:
    row = {"time": time_s, "clk_i": clk, "rst_ni": rst}
    row.update({f"ptr_{idx}": 1.0 if ptr_idx == idx else 0.0 for idx in range(16)})
    row.update({f"cell_en_{idx}": 1.0 if cell_set and idx in cell_set else 0.0 for idx in range(16)})
    row.update(_bits("code", 4, code))
    return row


def _dwa_fieldnames(include_code: bool) -> list[str]:
    fields = ["time", "clk_i", "rst_ni"]
    fields.extend(f"ptr_{idx}" for idx in range(16))
    fields.extend(f"cell_en_{idx}" for idx in range(16))
    if include_code:
        fields.extend(f"code_{idx}" for idx in range(4))
    return fields


def _dwa_edge_sample_rows(samples: list[dict[str, float]]) -> list[dict[str, float]]:
    rows = [_dwa_row(0.0, 0.0, 0.0), _dwa_row(5e-9, 0.0, 1.0)]
    for idx, sample in enumerate(samples):
        edge_t = (10 + idx * 10) * 1e-9
        rows.extend(
            [
                _dwa_row(edge_t - 0.2e-9, 0.0, 1.0, **sample),
                _dwa_row(edge_t, 1.0, 1.0, **sample),
                _dwa_row(edge_t + 1.0e-9, 1.0, 1.0, **sample),
                _dwa_row(edge_t + 5.0e-9, 0.0, 1.0, **sample),
            ]
        )
    return sorted(rows, key=lambda row: row["time"])


def _pfd_rows(deadzone: bool, passing: bool) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    if deadzone:
        dt = 0.1e-9
        total_steps = 2000
        pulse_starts = {int(round((5e-9 + idx * 9e-9) / dt)) for idx in range(20)}
        for step in range(total_steps + 1):
            time_s = step * dt
            up_high = passing and any(start <= step < start + 3 for start in pulse_starts)
            rows.append(
                {
                    "time": time_s,
                    "ref": 1.0 if (step // 50) % 2 == 0 else 0.0,
                    "div": 0.0,
                    "up": 1.0 if up_high else 0.0,
                    "dn": 0.0,
                }
            )
        return rows

    dt = 0.5e-9
    total_steps = 600
    first_pulses = {int(round((25e-9 + idx * 18e-9) / dt)) for idx in range(5)}
    second_pulses = {int(round((170e-9 + idx * 18e-9) / dt)) for idx in range(5)}
    for step in range(total_steps + 1):
        time_s = step * dt
        up_high = any(start <= step < start + 3 for start in first_pulses)
        dn_high = passing and any(start <= step < start + 3 for start in second_pulses)
        rows.append(
            {
                "time": time_s,
                "ref": 1.0 if (step // 20) % 2 == 0 else 0.0,
                "div": 0.0,
                "up": 1.0 if up_high else 0.0,
                "dn": 1.0 if dn_high else 0.0,
            }
        )
    return rows


def _gray_rows(passing: bool) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    dt = 1.0e-9
    bad_code_at = 8
    for step in range(260):
        time_s = step * dt
        clk = 1.0 if step % 10 < 5 else 0.0
        rst = 1.0 if step < 6 else 0.0
        seq_idx = max(0, (step - 18) // 10)
        code = int(seq_idx % 16) ^ (int(seq_idx % 16) >> 1)
        if not passing and seq_idx == bad_code_at:
            code ^= 0b0011
        row = {"time": time_s, "clk": clk, "rst": rst}
        row.update({f"g{idx}": 1.0 if (code >> idx) & 1 else 0.0 for idx in range(4)})
        rows.append(row)
    return rows


def _multimod_rows(passing: bool) -> list[dict[str, float]]:
    pre = {12, 20, 28, 36, 44, 52, 60, 68, 76, 84}
    mid = {122, 132, 142, 152, 162, 172, 182}
    post = {222, 230, 238, 246, 254, 262, 270, 278, 286, 294}
    out_edges = pre | mid | post if passing else set()
    rows: list[dict[str, float]] = []
    for ns in range(0, 311):
        rows.append(
            {
                "time": ns * 1e-9,
                "clk_in": 1.0 if ns % 2 == 0 else 0.0,
                "div_out": 1.0 if ns in out_edges else 0.0,
            }
        )
    return rows


def _fixture_cases(output_dir: Path, tasks: set[str]) -> list[tuple[str, Path, str]]:
    fixture_dir = output_dir / "fixtures"
    cases: list[tuple[str, Path, str]] = []

    def add(task_id: str, label: str, fields: list[str], rows: list[dict[str, float]]) -> None:
        if task_id not in tasks:
            return
        csv_path = fixture_dir / task_id / f"{label}.csv"
        _write_csv(csv_path, fields, rows)
        cases.append((task_id, csv_path, label))

    add("pfd_deadzone_smoke", "pass", ["time", "ref", "div", "up", "dn"], _pfd_rows(True, True))
    add("pfd_deadzone_smoke", "fail", ["time", "ref", "div", "up", "dn"], _pfd_rows(True, False))
    add("pfd_reset_race_smoke", "pass", ["time", "ref", "div", "up", "dn"], _pfd_rows(False, True))
    add("pfd_reset_race_smoke", "fail", ["time", "ref", "div", "up", "dn"], _pfd_rows(False, False))

    dac_rows = [
        {
            "time": code * 1e-9,
            "din3": 1.0 if (code >> 3) & 1 else 0.0,
            "din2": 1.0 if (code >> 2) & 1 else 0.0,
            "din1": 1.0 if (code >> 1) & 1 else 0.0,
            "din0": 1.0 if code & 1 else 0.0,
            "aout": code / 15.0,
        }
        for code in range(16)
    ]
    add("dac_binary_clk_4b_smoke", "pass", ["time", "din3", "din2", "din1", "din0", "aout"], dac_rows)
    add(
        "dac_binary_clk_4b_smoke",
        "fail",
        ["time", "din3", "din2", "din1", "din0", "aout"],
        [{**row, "aout": 0.0} for row in dac_rows],
    )

    sar_fields = ["time", "vin", "vin_sh", "vout", "rst_n"] + [f"dout_{idx}" for idx in range(8)]
    sar_rows = [
        {
            "time": idx * 1e-9,
            "vin": (idx % 64) / 63.0 * 0.8,
            "vin_sh": (idx % 64) / 63.0 * 0.8,
            "vout": (idx % 64) / 63.0 * 0.8,
            "rst_n": 1.0 if idx > 2 else 0.0,
            **_bits("dout", 8, idx % 64),
        }
        for idx in range(80)
    ]
    add("sar_adc_dac_weighted_8b_smoke", "pass", sar_fields, sar_rows)
    add(
        "sar_adc_dac_weighted_8b_smoke",
        "fail",
        sar_fields,
        [{**row, "vout": 0.0, **_bits("dout", 8, 0)} for row in sar_rows],
    )

    no_overlap_pass = [
        {"ptr_idx": idx % 16, "cell_set": {idx % 16}, "code": 0}
        for idx in range(8)
    ]
    no_overlap_fail = [
        {"ptr_idx": idx % 16, "cell_set": {0}, "code": 0}
        for idx in range(8)
    ]
    add("dwa_ptr_gen_no_overlap_smoke", "pass", _dwa_fieldnames(False), _dwa_edge_sample_rows(no_overlap_pass))
    add("dwa_ptr_gen_no_overlap_smoke", "fail", _dwa_fieldnames(False), _dwa_edge_sample_rows(no_overlap_fail))

    codes = [4, 5, 6, 7, 8, 4, 5]
    expected_ptr = 13
    wrap_samples: list[dict[str, float]] = []
    for code in codes:
        prev_ptr = expected_ptr
        expected_ptr = (expected_ptr + code) % 16
        wraps = expected_ptr < prev_ptr
        cells = {0, 1, 14, 15} if wraps and code == 4 else set(range(code))
        if wraps and code != 4:
            cells = set(range(code - 2)) | {14, 15}
        wrap_samples.append({"ptr_idx": expected_ptr, "cell_set": cells, "code": code})
    wrap_fail = [dict(sample) for sample in wrap_samples]
    wrap_fail[2] = {**wrap_fail[2], "ptr_idx": 0}
    add("dwa_wraparound_smoke", "pass", _dwa_fieldnames(True), _dwa_edge_sample_rows(wrap_samples))
    add("dwa_wraparound_smoke", "fail", _dwa_fieldnames(True), _dwa_edge_sample_rows(wrap_fail))

    digital_rows = [
        {"time": idx * 1e-9, "a": float(idx % 2), "y": float(1 - (idx % 2))}
        for idx in range(24)
    ]
    add("digital_basics_smoke", "pass", ["time", "a", "y"], digital_rows)
    add("digital_basics_smoke", "fail", ["time", "a", "y"], [{**row, "y": row["a"]} for row in digital_rows])

    add("gray_counter_one_bit_change_smoke", "pass", ["time", "clk", "rst", "g0", "g1", "g2", "g3"], _gray_rows(True))
    add("gray_counter_one_bit_change_smoke", "fail", ["time", "clk", "rst", "g0", "g1", "g2", "g3"], _gray_rows(False))

    gain_rows = [
        {
            "time": idx * 1e-9,
            "vinp": 0.5 + 0.01 * math.sin(idx / 5.0),
            "vinn": 0.5 - 0.01 * math.sin(idx / 5.0),
            "vamp_p": 0.5 + 0.08 * math.sin(idx / 5.0),
            "vamp_n": 0.5 - 0.08 * math.sin(idx / 5.0),
        }
        for idx in range(80)
    ]
    add("gain_extraction_smoke", "pass", ["time", "vinp", "vinn", "vamp_p", "vamp_n"], gain_rows)
    add(
        "gain_extraction_smoke",
        "fail",
        ["time", "vinp", "vinn", "vamp_p", "vamp_n"],
        [{**row, "vamp_p": row["vinp"], "vamp_n": row["vinn"]} for row in gain_rows],
    )

    add("multimod_divider_ratio_switch_smoke", "pass", ["time", "clk_in", "div_out"], _multimod_rows(True))
    add("multimod_divider_ratio_switch_smoke", "fail", ["time", "clk_in", "div_out"], _multimod_rows(False))
    return cases


def _candidate_csvs(result_roots: list[Path], tasks: set[str], max_cases_per_task: int) -> list[tuple[str, Path, str]]:
    by_task: dict[str, list[Path]] = defaultdict(list)
    for root in result_roots:
        if root.is_file() and root.name == "tran.csv":
            paths = [root]
        else:
            paths = sorted(root.rglob("tran.csv")) if root.exists() else []
        for csv_path in paths:
            task_id = _infer_task_id(csv_path)
            if task_id is None or task_id not in tasks:
                continue
            by_task[task_id].append(csv_path)

    selected: list[tuple[str, Path, str]] = []
    for task_id in sorted(by_task):
        # Prefer smaller CSVs for parity because the default checker must finish
        # for a row to count as evidence.
        ordered = sorted(by_task[task_id], key=lambda path: path.stat().st_size)
        for csv_path in ordered[:max_cases_per_task]:
            selected.append((task_id, csv_path, csv_path.parent.name))
    return selected


def _write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fields = [
        "task_id",
        "case_id",
        "csv_path",
        "csv_mb",
        "original_kind",
        "original_score",
        "original_elapsed_s",
        "original_notes",
        "streaming_kind",
        "streaming_score",
        "streaming_elapsed_s",
        "streaming_notes",
        "parity_status",
    ]
    with (output_dir / "parity.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (output_dir / "parity.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Streaming Checker Parity Report",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- Comparable cases: `{summary['comparable_count']}`",
        f"- Matches: `{summary['match_count']}`",
        f"- Mismatches: `{summary['mismatch_count']}`",
        f"- Original timeouts: `{summary['original_timeout_count']}`",
        "",
        "## By Task",
        "",
        "| task | cases | comparable | matches | mismatches | original_timeout |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for task_id, stats in sorted(summary["by_task"].items()):
        lines.append(
            f"| `{task_id}` | {stats.get('case_count', 0)} | {stats.get('comparable_count', 0)} | "
            f"{stats.get('match_count', 0)} | {stats.get('mismatch_count', 0)} | "
            f"{stats.get('original_timeout_count', 0)} |"
        )
    lines.extend(["", "## Interpretation", ""])
    if summary["mismatch_count"] == 0:
        lines.append("- No pass/fail mismatches were observed on comparable cases.")
    else:
        lines.append("- At least one mismatch was observed; do not promote the streaming path yet.")
    lines.append("- Rows where the default checker timed out are not parity evidence; they show where streaming improves evaluator throughput.")
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    tasks = set(args.task or STREAMING_TASKS)
    result_roots = [Path(root).resolve() for root in (args.result_root or [])]
    if args.fixture_suite:
        cases = _fixture_cases(Path(args.output_dir), tasks)
    else:
        if not result_roots:
            raise SystemExit("--result-root is required unless --fixture-suite is used")
        cases = _candidate_csvs(result_roots, tasks, args.max_cases_per_task)

    rows: list[dict[str, Any]] = []
    for idx, (task_id, csv_path, case_id) in enumerate(cases, start=1):
        print(f"[parity] {idx}/{len(cases)} {task_id} {case_id} {csv_path}")
        original = _run_with_timeout(task_id, csv_path, "original", args.original_timeout_s)
        streaming = _run_with_timeout(task_id, csv_path, "streaming", args.streaming_timeout_s)
        if original["kind"] == "ok" and streaming["kind"] == "ok":
            parity_status = "match" if original["score"] == streaming["score"] else "mismatch"
        elif original["kind"] == "timeout":
            parity_status = "original_timeout"
        elif streaming["kind"] != "ok":
            parity_status = "streaming_error"
        else:
            parity_status = f"original_{original['kind']}"
        rows.append(
            {
                "task_id": task_id,
                "case_id": case_id,
                "csv_path": _rel(csv_path),
                "csv_mb": round(csv_path.stat().st_size / 1_000_000, 3),
                "original_kind": original["kind"],
                "original_score": original["score"],
                "original_elapsed_s": round(original["elapsed_s"], 3),
                "original_notes": " ; ".join(original["notes"]),
                "streaming_kind": streaming["kind"],
                "streaming_score": streaming["score"],
                "streaming_elapsed_s": round(streaming["elapsed_s"], 3),
                "streaming_notes": " ; ".join(streaming["notes"]),
                "parity_status": parity_status,
            }
        )

    counts = Counter(row["parity_status"] for row in rows)
    by_task: dict[str, dict[str, int]] = {}
    for task_id in sorted({row["task_id"] for row in rows}):
        task_rows = [row for row in rows if row["task_id"] == task_id]
        task_counts = Counter(row["parity_status"] for row in task_rows)
        by_task[task_id] = {
            "case_count": len(task_rows),
            "comparable_count": task_counts["match"] + task_counts["mismatch"],
            "match_count": task_counts["match"],
            "mismatch_count": task_counts["mismatch"],
            "original_timeout_count": task_counts["original_timeout"],
        }
    summary = {
        "mode": "streaming_checker_parity",
        "fixture_suite": bool(args.fixture_suite),
        "result_roots": [_rel(root) for root in result_roots],
        "tasks": sorted(tasks),
        "case_count": len(rows),
        "comparable_count": counts["match"] + counts["mismatch"],
        "match_count": counts["match"],
        "mismatch_count": counts["mismatch"],
        "original_timeout_count": counts["original_timeout"],
        "status_counts": dict(counts),
        "by_task": by_task,
    }
    _write_outputs(rows, summary, Path(args.output_dir))
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Check default-vs-streaming checker pass/fail parity.")
    parser.add_argument("--result-root", action="append")
    parser.add_argument("--fixture-suite", action="store_true", help="Generate small synthetic fixtures and check parity on them.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--task", action="append", choices=sorted(STREAMING_TASKS))
    parser.add_argument("--max-cases-per-task", type=int, default=6)
    parser.add_argument("--original-timeout-s", type=float, default=25.0)
    parser.add_argument("--streaming-timeout-s", type=float, default=25.0)
    args = parser.parse_args()
    summary = run(args)
    return 1 if summary["mismatch_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
