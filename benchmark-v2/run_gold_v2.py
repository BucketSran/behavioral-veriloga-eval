#!/usr/bin/env python3
"""Run EVAS gold validation on all benchmark-v2 tasks.

Usage:
  python benchmark-v2/run_gold_v2.py                        # run all
  python benchmark-v2/run_gold_v2.py --task clk_divider_p2p3p4  # single
  python benchmark-v2/run_gold_v2.py --timeout 300          # longer timeout
  python benchmark-v2/run_gold_v2.py --keep                 # keep temp run dirs
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

V2_ROOT = Path(__file__).resolve().parent
REPO_ROOT = V2_ROOT.parent
sys.path.insert(0, str(REPO_ROOT))

from runners.simulate_evas import run_case  # noqa: E402


def find_gold_dut(gold_dir: Path) -> Path | None:
    candidates = sorted(gold_dir.glob("*.va"))
    return candidates[0] if candidates else None


def find_gold_tb(gold_dir: Path) -> Path | None:
    preferred = sorted(gold_dir.glob("tb*_ref.scs"))
    if preferred:
        return preferred[0]
    fallbacks = sorted(gold_dir.glob("tb*.scs"))
    return fallbacks[0] if fallbacks else None


def list_v2_tasks(selected: set[str] | None = None) -> list[Path]:
    tasks_root = V2_ROOT / "tasks"
    if not tasks_root.is_dir():
        return []
    task_dirs = []
    for task_dir in sorted(tasks_root.iterdir()):
        if not task_dir.is_dir():
            continue
        gold_dir = task_dir / "gold"
        if not gold_dir.is_dir():
            continue
        task_id = task_dir.name
        if selected and task_id not in selected:
            continue
        task_dirs.append(task_dir)
    return task_dirs


def run_v2_task(
    task_dir: Path, output_root: Path,
    timeout_s: int, keep: bool,
) -> dict:
    gold_dir = task_dir / "gold"
    task_id = task_dir.name

    dut_path = find_gold_dut(gold_dir)
    if dut_path is None:
        return {"task_id": task_id, "status": "FAIL_INFRA",
                "notes": ["no gold .va found"]}

    tb_path = find_gold_tb(gold_dir)
    if tb_path is None:
        return {"task_id": task_id, "status": "FAIL_INFRA",
                "notes": ["no gold testbench found"]}

    result = run_case(
        task_dir,
        dut_path,
        tb_path,
        output_root=output_root / task_id,
        timeout_s=timeout_s,
        task_id_override=task_id,
        keep_run_dir=keep,
    )
    sc = result.get("scoring", {})
    dc = sc.get("dut_compile", "?")
    tc = sc.get("tb_compile", "?")
    sc_correct = sc.get("sim_correct", "?")
    print(f"  dut_compile={dc} tb_compile={tc} sim_correct={sc_correct}")
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="EVAS gold validation for benchmark-v2")
    ap.add_argument("--task", action="append", default=[])
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--keep", action="store_true",
                    help="Keep temporary run directories")
    ap.add_argument("--output-root", default=None)
    args = ap.parse_args()

    selected = set(args.task) if args.task else None
    task_dirs = list_v2_tasks(selected)

    if not task_dirs:
        print("No benchmark-v2 tasks with gold assets found.")
        return

    out_root = Path(args.output_root) if args.output_root \
        else (V2_ROOT / "results" / "gold-suite")
    out_root.mkdir(parents=True, exist_ok=True)

    print(f"Running {len(task_dirs)} benchmark-v2 task(s)\n")

    results = []
    for i, task_dir in enumerate(task_dirs, 1):
        task_id = task_dir.name
        print(f"[{i}/{len(task_dirs)}] {task_id}", flush=True)
        result = run_v2_task(task_dir, out_root, args.timeout, args.keep)
        results.append(result)

    passed = sum(1 for r in results if r.get("status") == "PASS")
    failed = len(results) - passed

    summary = {
        "suite": "benchmark-v2-gold",
        "tasks_total": len(results),
        "pass_count": passed,
        "fail_count": failed,
        "results": results,
    }

    summary_path = out_root / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\n{'='*50}")
    print(f"PASS {passed} / FAIL {failed} / TOTAL {len(results)}")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
