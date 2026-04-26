#!/usr/bin/env python3
"""Run a small 2x2 DUT/TB isolation probe for end-to-end failures."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
from pathlib import Path

from score import choose_gold_tb, find_generated_dir, find_tb_file, find_va_file, list_all_task_dirs, read_meta
from simulate_evas import run_case


ROOT = Path(__file__).resolve().parents[1]


def _json_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _first_gold_va(task_dir: Path) -> Path | None:
    vas = sorted((task_dir / "gold").glob("*.va"))
    return vas[0] if vas else None


def _classify(cases: dict[str, dict], family: str) -> tuple[str, str]:
    gg = cases.get("generated_dut__generated_tb", {}).get("status")
    gt = cases.get("generated_dut__gold_tb", {}).get("status")
    tg = cases.get("gold_dut__generated_tb", {}).get("status")

    if family in {"spec-to-va", "bugfix"}:
        if gt == "PASS":
            return "dut_confirmed_with_gold_harness", "generated DUT passes with the benchmark gold TB"
        return "dut_or_gold_harness_failure", "generated DUT does not pass with the benchmark gold TB"

    if gg == "PASS":
        return "already_pass", "generated DUT and generated TB pass together"
    if gt == "PASS" and tg != "PASS":
        return "tb_or_harness", "generated DUT passes with gold TB, but gold DUT does not pass with generated TB"
    if gt != "PASS" and tg == "PASS":
        return "dut", "gold DUT passes with generated TB, but generated DUT does not pass with gold TB"
    if gt == "PASS" and tg == "PASS":
        return "integration_or_scoring", "both crossed pairs pass, but generated/generated fails"
    return "mixed_or_unknown", "neither generated DUT with gold TB nor gold DUT with generated TB passes"


def run_one(
    task_id: str,
    task_dir: Path,
    generated_root: Path,
    model: str,
    output_root: Path,
    timeout_s: int,
) -> dict:
    sample_dir = find_generated_dir(generated_root, model, task_id, 0)
    gold_tb = choose_gold_tb(task_dir / "gold")
    gold_dut = _first_gold_va(task_dir)
    record = {
        "task_id": task_id,
        "task_dir": str(task_dir),
        "family": read_meta(task_dir).get("family", "unknown"),
        "sample_dir": str(sample_dir) if sample_dir else None,
        "gold_tb": str(gold_tb) if gold_tb else None,
        "gold_dut": str(gold_dut) if gold_dut else None,
        "cases": {},
    }
    if sample_dir is None:
        record.update({"layer": "missing_generated_sample", "reason": "sample_0 not found"})
        _json_write(output_root / task_id / "summary.json", record)
        return record

    generated_dut = find_va_file(sample_dir)
    generated_tb = find_tb_file(sample_dir)
    pairs = {
        "generated_dut__generated_tb": (generated_dut, generated_tb),
        "generated_dut__gold_tb": (generated_dut, gold_tb),
        "gold_dut__generated_tb": (gold_dut, generated_tb),
    }
    for case_name, (dut, tb) in pairs.items():
        case_out = output_root / task_id / case_name
        if dut is None or tb is None or not dut.exists() or not tb.exists():
            result = {"status": "MISSING", "notes": [f"dut={dut}", f"tb={tb}"]}
        else:
            try:
                result = run_case(
                    task_dir,
                    dut,
                    tb,
                    output_root=case_out,
                    timeout_s=timeout_s,
                    task_id_override=task_id,
                )
            except Exception as exc:  # noqa: BLE001 - long-running probe should keep records.
                result = {"status": "ERROR", "notes": [f"{type(exc).__name__}: {exc}"]}
        record["cases"][case_name] = {
            "dut": str(dut) if dut else None,
            "tb": str(tb) if tb else None,
            "status": result.get("status"),
            "scores": result.get("scores"),
            "notes": result.get("notes"),
        }
        _json_write(case_out / "result.json", result)

    layer, reason = _classify(record["cases"], record["family"])
    record["layer"] = layer
    record["reason"] = reason
    _json_write(output_root / task_id / "summary.json", record)
    return record


def run(args: argparse.Namespace) -> dict:
    generated_root = Path(args.generated_dir).resolve()
    output_root = Path(args.output_dir).resolve()
    model = args.model.replace("/", "_")
    selected = set(args.task or [])
    task_map = {task_id: task_dir for task_id, task_dir in list_all_task_dirs(selected=selected)}

    def _run_task(task_id: str) -> dict:
        task_dir = task_map.get(task_id)
        if task_dir is None:
            return {"task_id": task_id, "layer": "missing_task", "reason": "task not found"}
        return run_one(task_id, task_dir, generated_root, model, output_root, args.timeout_s)

    task_ids = args.task or sorted(task_map)
    records: list[dict] = []
    workers = max(1, min(args.workers, len(task_ids)))
    if workers == 1:
        for task_id in task_ids:
            records.append(_run_task(task_id))
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            for record in executor.map(_run_task, task_ids):
                records.append(record)

    counts: dict[str, int] = {}
    for record in records:
        counts[record.get("layer", "unknown")] = counts.get(record.get("layer", "unknown"), 0) + 1
    summary = {
        "mode": "layered_isolation_probe",
        "generated_root": str(generated_root),
        "output_root": str(output_root),
        "model": model,
        "timeout_s": args.timeout_s,
        "task_count": len(records),
        "layer_counts": counts,
        "records": records,
    }
    _json_write(output_root / "summary.json", summary)
    print(json.dumps({"task_count": len(records), "layer_counts": counts}, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 2x2 generated/gold DUT/TB isolation probes.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--generated-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--timeout-s", type=int, default=120)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--task", action="append", default=[])
    run(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
