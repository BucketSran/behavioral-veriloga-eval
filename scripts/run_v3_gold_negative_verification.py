#!/usr/bin/env python3
"""Run v3 gold and negative-variant EVAS verification for a task range."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from simulate_evas import read_task_artifact_targets, read_task_index_id, run_case

NEGATIVE_LIST_KEYS = ("cases", "negative_cases", "negative_variants", "variants", "negatives")
SLOW_GOLD_THRESHOLD_S = 20.0


def scrub_note(note: str) -> str:
    text = str(note)
    if not text.startswith("checker_config="):
        return text
    marker = "benchmark-vabench-release-v3/"
    if marker in text:
        return f"checker_config={text[text.index(marker):]}"
    return text


def task_number(task_dir: Path) -> int | None:
    try:
        return int(task_dir.name.split("-", 1)[0])
    except ValueError:
        return None


def parse_task_filter(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip() for item in value.split(",") if item.strip()}


def task_matches_filter(task_dir: Path, task_filter: set[str]) -> bool:
    if not task_filter:
        return True
    number = task_number(task_dir)
    return task_dir.name in task_filter or (number is not None and f"{number:03d}" in task_filter)


def task_in_requested_range(task_dir: Path, task_filter: set[str], start: int, end: int) -> bool:
    number = task_number(task_dir)
    if number is not None:
        return start <= number <= end
    return bool(task_filter) and task_dir.name in task_filter


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_negative_cases(manifest_path: Path) -> list[dict[str, Any]]:
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        return []
    for key in NEGATIVE_LIST_KEYS:
        variants = manifest.get(key)
        if not isinstance(variants, list):
            continue
        cases: list[dict[str, Any]] = []
        for item in variants:
            if not isinstance(item, dict):
                continue
            variant_id = str(item.get("id", "")).strip()
            if not variant_id:
                continue
            case = dict(item)
            case["id"] = variant_id
            cases.append(case)
        return cases
    return []


def read_sim_correct_task_slugs(checks_path: Path) -> set[str]:
    if not checks_path.exists():
        return set()
    text = checks_path.read_text(encoding="utf-8", errors="ignore")
    slugs: set[str] = set()
    current_slug: str | None = None
    current_body: list[str] = []
    for line in text.splitlines():
        if line and not line.startswith((" ", "\t")) and line.endswith(": |"):
            if current_slug and any("sim_correct:" in body_line for body_line in current_body):
                slugs.add(current_slug)
            current_slug = line.split(":", 1)[0]
            current_body = []
            continue
        if current_slug is not None:
            current_body.append(line)
    if current_slug and any("sim_correct:" in body_line for body_line in current_body):
        slugs.add(current_slug)
    return slugs


def negative_variant_cases(task_dir: Path) -> list[dict[str, Any]]:
    manifest_path = task_dir / "negative_variants" / "manifest.json"
    if not manifest_path.exists():
        nested_manifests = sorted((task_dir / "negative_variants").glob("*/manifest.json"))
        if len(nested_manifests) != 1:
            return []
        manifest_path = nested_manifests[0]
    cases = manifest_negative_cases(manifest_path)
    if manifest_path.parent != task_dir / "negative_variants":
        prefix = manifest_path.parent.relative_to(task_dir).as_posix()
        for case in cases:
            case.setdefault("legacy_manifest", manifest_path.relative_to(task_dir).as_posix())
            if "files" not in case and "path" not in case and "source" in case:
                continue
            if "files" not in case and "path" not in case and "source" not in case:
                case["files"] = [f"{prefix}/{case['id']}.va"]
    return cases


def negative_variant_ids(task_dir: Path) -> list[str]:
    return [str(case["id"]) for case in negative_variant_cases(task_dir)]


def negative_case_file(task_dir: Path, case: dict[str, Any] | None, target: str) -> Path | None:
    if not case:
        return None
    raw_paths: list[str] = []
    for key in ("files", "source", "path", "artifact", "target"):
        value = case.get(key)
        if isinstance(value, str):
            raw_paths.append(value)
        elif isinstance(value, list):
            raw_paths.extend(str(item) for item in value if isinstance(item, str))
    for raw_path in raw_paths:
        path = Path(raw_path)
        candidates = []
        if path.is_absolute():
            candidates.append(path)
        else:
            candidates.append(task_dir / path)
            if not raw_path.startswith("negative_variants/"):
                candidates.append(task_dir / "negative_variants" / raw_path)
            candidates.append(task_dir / "negative_variants" / str(case["id"]) / raw_path)
        for candidate in candidates:
            if candidate.exists() and candidate.name == target:
                return candidate
    for raw_path in raw_paths:
        path = Path(raw_path)
        candidates = [path] if path.is_absolute() else [
            task_dir / path,
            task_dir / "negative_variants" / path,
            task_dir / "negative_variants" / str(case["id"]) / path,
        ]
        for candidate in candidates:
            if candidate.exists() and candidate.suffix in {".va", ".vams"}:
                return candidate
    return None


def choose_dut(
    task_dir: Path,
    target: str,
    variant: str | None,
    negative_case: dict[str, Any] | None = None,
) -> tuple[Path | None, list[str]]:
    notes: list[str] = []
    case_file = negative_case_file(task_dir, negative_case, target)
    if case_file is not None:
        if case_file.name != target:
            notes.append(f"used_negative_manifest_file={case_file.relative_to(task_dir).as_posix()}")
        return case_file, notes
    dut_root = task_dir / "negative_variants" / variant if variant else task_dir / "solution"
    dut = dut_root / target
    if dut.exists():
        return dut, notes
    va_candidates = sorted([*dut_root.glob("*.va"), *dut_root.glob("*.vams")])
    if len(va_candidates) == 1:
        notes.append(f"used_single_artifact_fallback={va_candidates[0].name}")
        return va_candidates[0], notes
    notes.append(f"missing_candidate_artifact={dut}")
    return None, notes


def choose_split_tb(task_dir: Path, split: str) -> Path | None:
    tb = task_dir / f"test_{split}" / f"{split}.scs"
    if tb.exists():
        return tb
    candidates = sorted((task_dir / f"test_{split}" / "tests").glob("*.scs"))
    return candidates[0] if len(candidates) == 1 else None


def simulator_failure_summary(text: str) -> str | None:
    """Extract a concise simulator failure reason from EVAS output."""
    if not text.strip():
        return None
    patterns = (
        r"ERROR:\s*(?P<msg>[^\n]+)",
        r"CompilationError:\s*(?P<msg>[^\n]+)",
        r"SyntaxError:\s*(?P<msg>[^\n]+)",
        r"NameError:\s*(?P<msg>[^\n]+)",
        r"ValueError:\s*(?P<msg>[^\n]+)",
    )
    for pattern in patterns:
        matches = list(re.finditer(pattern, text))
        if matches:
            message = matches[-1].group("msg").strip()
            message = re.sub(r"\s+", " ", message)
            return f"simulator_error={message[:240]}"
    if "evas completes with 1 errors" in text:
        return "simulator_error=evas completed with 1 error but did not expose a detailed diagnostic in captured output"
    return None


def first_failure_summary(status: str, notes: list[str]) -> str | None:
    if status == "PASS":
        return None
    for note in notes:
        text = str(note).strip()
        if text.startswith("simulator_error="):
            return text
    low_signal_prefixes = (
        "returncode=",
        "evas_engine=",
        "checker_config=",
        "trace_contract=",
        "extra_trace_signals=",
        "used_single_artifact_fallback=",
        "dut_not_compiled",
        "tb_not_executed",
    )
    for note in notes:
        text = str(note).strip()
        if text and not text.startswith(low_signal_prefixes):
            return text
    return notes[0] if notes else None


def run_one(
    task_dir: Path,
    variant: str | None,
    timeout_s: int,
    negative_case: dict[str, Any] | None = None,
    split: str = "hidden",
    omit_stdout_tail: bool = False,
) -> dict[str, Any]:
    started = time.perf_counter()
    targets = read_task_artifact_targets(task_dir)
    task_index_id = read_task_index_id(task_dir) or task_dir.name
    kind = "negative" if variant else "gold"
    case_id = f"{task_dir.name}:{variant}" if variant else f"{task_dir.name}:gold"
    row: dict[str, Any] = {
        "case_id": case_id,
        "task_slug": task_dir.name,
        "task_id": task_index_id,
        "kind": kind,
        "split": split,
        "variant": variant,
    }
    if not targets:
        notes = ["missing target in TASKS.json/task.toml"]
        row.update({
            "status": "FAIL_NO_TARGET",
            "expected_ok": False,
            "meets_expectation": kind == "negative",
            "notes": notes,
            "failure_summary": first_failure_summary("FAIL_NO_TARGET", notes),
            "wall_s": round(time.perf_counter() - started, 6),
        })
        return row
    tb = choose_split_tb(task_dir, split)
    if tb is None:
        notes = [f"missing {split}.scs or unique test_{split}/tests/*.scs"]
        row.update({
            "status": "FAIL_NO_TB",
            "expected_ok": False,
            "meets_expectation": kind == "negative",
            "notes": notes,
            "failure_summary": first_failure_summary("FAIL_NO_TB", notes),
            "wall_s": round(time.perf_counter() - started, 6),
        })
        return row
    dut, selection_notes = choose_dut(task_dir, targets[0], variant, negative_case)
    if dut is None:
        row.update({
            "status": "FAIL_NO_DUT",
            "expected_ok": False,
            "meets_expectation": kind == "negative",
            "notes": selection_notes,
            "failure_summary": first_failure_summary("FAIL_NO_DUT", selection_notes),
            "wall_s": round(time.perf_counter() - started, 6),
        })
        return row

    try:
        result = run_case(
            task_dir,
            dut,
            tb,
            timeout_s=timeout_s,
            keep_run_dir=False,
            task_id_override=task_index_id,
        )
    except Exception as exc:  # pragma: no cover - report boundary.
        result = {
            "status": "FAIL_EXCEPTION",
            "scores": {},
            "notes": [f"{type(exc).__name__}: {exc}"],
            "stdout_tail": "",
        }

    status = str(result.get("status", "FAIL_UNKNOWN"))
    expected_ok = kind == "gold"
    meets_expectation = status == "PASS" if expected_ok else status != "PASS"
    stdout_tail = str(result.get("stdout_tail", ""))
    notes = [scrub_note(note) for note in [*selection_notes, *[str(note) for note in result.get("notes", [])]]]
    if status != "PASS" and not any(note.startswith("simulator_error=") for note in notes):
        failure_summary = simulator_failure_summary(stdout_tail)
        if failure_summary and failure_summary not in notes:
            notes.append(failure_summary)
    row.update({
        "status": status,
        "expected_ok": expected_ok,
        "meets_expectation": meets_expectation,
        "checker_task_id": result.get("checker_task_id"),
        "scores": result.get("scores", {}),
        "notes": notes,
        "failure_summary": first_failure_summary(status, notes),
        "wall_s": round(time.perf_counter() - started, 6),
    })
    if not omit_stdout_tail:
        row["stdout_tail"] = stdout_tail[-4000:]
    return row


def gold_timing_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timings = []
    for row in rows:
        if row.get("kind") != "gold":
            continue
        timings.append({
            "task_slug": row["task_slug"],
            "task_id": row.get("task_id"),
            "case_id": row.get("case_id"),
            "status": row.get("status"),
            "wall_s": row.get("wall_s", 0.0),
        })
    return sorted(timings, key=lambda item: (str(item["task_slug"]), str(item["case_id"])))


def slow_gold_cases(gold_timings: list[dict[str, Any]], threshold_s: float) -> list[dict[str, Any]]:
    return [
        timing
        for timing in sorted(gold_timings, key=lambda item: float(item.get("wall_s") or 0.0), reverse=True)
        if float(timing.get("wall_s") or 0.0) > threshold_s
    ]


def write_markdown_summary(payload: dict[str, Any], out: Path) -> None:
    summary = payload["summary"]
    rows = payload["rows"]
    gold_timings = payload.get("gold_timings", [])
    slow_cases = payload.get("slow_gold_cases", [])
    lines = [
        "# v3 Staged Promotion Gold Probe",
        "",
        f"Date: {time.strftime('%Y-%m-%d')}",
        "",
        "## Summary",
        "",
    ]
    for key in (
        "gold_total",
        "gold_pass",
        "gold_fail",
        "expectation_fail",
        "skipped_staged_tasks",
        "gold_wall_s_total",
        "gold_wall_s_max",
        "slow_gold_threshold_s",
        "slow_gold_count",
        "wall_s",
    ):
        lines.append(f"- `{key}`: {summary[key]}")
    if slow_cases:
        lines.extend([
            "",
            "## Slow Gold Cases",
            "",
            "| Task | Status | Wall s |",
            "| --- | --- | ---: |",
        ])
        for row in slow_cases:
            lines.append(f"| `{row['task_slug']}` | `{row['status']}` | {row['wall_s']} |")
    if gold_timings:
        lines.extend([
            "",
            "## Gold Timing Top 20",
            "",
            "| Task | Status | Wall s |",
            "| --- | --- | ---: |",
        ])
        for row in sorted(gold_timings, key=lambda item: float(item.get("wall_s") or 0.0), reverse=True)[:20]:
            lines.append(f"| `{row['task_slug']}` | `{row['status']}` | {row['wall_s']} |")
    lines.extend([
        "",
        "## Rows",
        "",
        "| Task | Status | First behavior note |",
        "| --- | --- | --- |",
    ])
    for row in rows:
        note = str(row.get("failure_summary") or "")
        note = note.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{row['task_slug']}` | `{row['status']}` | {note} |")
    lines.append("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="benchmark-vabench-release-v3/tasks")
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument(
        "--tasks",
        default="",
        help="Optional comma-separated task slugs or three-digit task numbers to run inside the start/end range.",
    )
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--slow-gold-threshold",
        type=float,
        default=SLOW_GOLD_THRESHOLD_S,
        help="Record gold cases above this per-case wall-clock threshold as slow.",
    )
    parser.add_argument(
        "--md-out",
        default="",
        help="Optional Markdown summary path for staged promotion probes.",
    )
    parser.add_argument("--gold-only", action="store_true")
    parser.add_argument("--negatives-only", action="store_true")
    parser.add_argument("--split", choices=("hidden", "visible"), default="hidden")
    parser.add_argument(
        "--checks",
        default="benchmark-vabench-release-v3/CHECKS.yaml",
        help="CHECKS.yaml path used to identify behavior-certified sim_correct tasks.",
    )
    parser.add_argument(
        "--include-staged",
        action="store_true",
        help="Also run staged syntax/continuous/KCL candidates without sim_correct blocks.",
    )
    parser.add_argument(
        "--omit-stdout-tail",
        action="store_true",
        help="Omit raw simulator stdout tails from JSON rows to keep reports portable.",
    )
    args = parser.parse_args()

    if args.gold_only and args.negatives_only:
        raise SystemExit("--gold-only and --negatives-only are mutually exclusive")

    os.environ.setdefault("VAEVAS_EVAS_PERSISTENT_WORKER", "0")
    root = Path(args.root)
    sim_correct_slugs = read_sim_correct_task_slugs(Path(args.checks))
    task_filter = parse_task_filter(args.tasks)
    cases: list[tuple[Path, str | None, int, dict[str, Any] | None, str, bool]] = []
    skipped_tasks: list[str] = []
    for task_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        if not task_in_requested_range(task_dir, task_filter, args.start, args.end):
            continue
        if not task_matches_filter(task_dir, task_filter):
            continue
        if not args.include_staged and task_dir.name not in sim_correct_slugs:
            skipped_tasks.append(task_dir.name)
            print(task_dir.name, "SKIP_STAGED", flush=True)
            continue
        if not args.negatives_only:
            cases.append((task_dir, None, args.timeout, None, args.split, args.omit_stdout_tail))
        if not args.gold_only:
            for negative_case in negative_variant_cases(task_dir):
                cases.append((
                    task_dir,
                    str(negative_case["id"]),
                    args.timeout,
                    negative_case,
                    args.split,
                    args.omit_stdout_tail,
                ))

    rows: list[dict[str, Any]] = []
    started = time.perf_counter()
    jobs = max(1, args.jobs)
    if jobs == 1:
        for case in cases:
            row = run_one(*case)
            rows.append(row)
            print(row["case_id"], row["status"], "expect_ok=", row["expected_ok"], "ok=", row["meets_expectation"], flush=True)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
            futures = [executor.submit(run_one, *case) for case in cases]
            for future in concurrent.futures.as_completed(futures):
                row = future.result()
                rows.append(row)
                print(row["case_id"], row["status"], "expect_ok=", row["expected_ok"], "ok=", row["meets_expectation"], flush=True)

    rows.sort(key=lambda row: (row["task_slug"], row["kind"], str(row["variant"] or "")))
    gold_rows = [row for row in rows if row["kind"] == "gold"]
    negative_rows = [row for row in rows if row["kind"] == "negative"]
    gold_timings = gold_timing_rows(rows)
    slow_cases = slow_gold_cases(gold_timings, args.slow_gold_threshold)
    gold_wall_times = [float(row.get("wall_s") or 0.0) for row in gold_timings]
    summary = {
        "scope": f"{args.start}-{args.end}",
        "cases_total": len(rows),
        "gold_total": len(gold_rows),
        "gold_pass": sum(row["status"] == "PASS" for row in gold_rows),
        "gold_fail": sum(row["status"] != "PASS" for row in gold_rows),
        "negative_total": len(negative_rows),
        "negative_rejected": sum(row["status"] != "PASS" for row in negative_rows),
        "negative_accepted": sum(row["status"] == "PASS" for row in negative_rows),
        "expectation_pass": sum(row["meets_expectation"] for row in rows),
        "expectation_fail": sum(not row["meets_expectation"] for row in rows),
        "skipped_staged_tasks": len(skipped_tasks),
        "gold_wall_s_total": round(sum(gold_wall_times), 6),
        "gold_wall_s_max": round(max(gold_wall_times), 6) if gold_wall_times else 0.0,
        "slow_gold_threshold_s": args.slow_gold_threshold,
        "slow_gold_count": len(slow_cases),
        "wall_s": round(time.perf_counter() - started, 6),
    }
    payload = {
        "summary": summary,
        "rows": rows,
        "skipped_tasks": skipped_tasks,
        "gold_timings": gold_timings,
        "slow_gold_cases": slow_cases,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.md_out:
        write_markdown_summary(payload, Path(args.md_out))
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("REPORT", out)
    return 0 if summary["expectation_fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
