#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from simulate_evas import has_behavior_check, run_case


def benchmark_root() -> Path:
    return Path(__file__).resolve().parents[1]


def task_root() -> Path:
    return benchmark_root() / "tasks" / "end-to-end" / "voltage"


def read_meta(task_dir: Path) -> dict:
    return json.loads((task_dir / "meta.json").read_text(encoding="utf-8"))


def list_gold_task_dirs(selected: set[str] | None = None) -> list[Path]:
    task_dirs: list[Path] = []
    for task_dir in sorted(p for p in task_root().iterdir() if p.is_dir()):
        gold_dir = task_dir / "gold"
        if not gold_dir.is_dir():
            continue
        task_id = task_dir.name
        if selected and task_id not in selected:
            continue
        task_dirs.append(task_dir)
    return task_dirs


def choose_gold_tb(gold_dir: Path) -> Path | None:
    preferred = sorted(gold_dir.glob("tb*_ref.scs"))
    if preferred:
        return preferred[0]
    fallbacks = sorted(gold_dir.glob("tb*.scs"))
    return fallbacks[0] if fallbacks else None


def ahdl_includes(tb_path: Path) -> list[str]:
    text = tb_path.read_text(encoding="utf-8")
    return re.findall(r'^\s*ahdl_include\s+"([^"]+)"', text, flags=re.MULTILINE)


def run_gold_case(task_dir: Path, output_root: Path, timeout_s: int) -> dict:
    gold_dir = task_dir / "gold"
    meta = read_meta(task_dir)
    task_id = meta.get("task_id", task_dir.name)

    tb_path = choose_gold_tb(gold_dir)
    if tb_path is None:
        return {
            "task_id": task_id,
            "status": "FAIL_INFRA",
            "notes": ["no gold testbench found"],
        }

    includes = ahdl_includes(tb_path)
    if not includes:
        return {
            "task_id": task_id,
            "status": "FAIL_INFRA",
            "notes": [f"no ahdl_include found in {tb_path.name}"],
        }

    primary_dut = gold_dir / includes[0]
    missing = [name for name in includes if not (gold_dir / name).exists()]
    if missing:
        return {
            "task_id": task_id,
            "status": "FAIL_INFRA",
            "notes": [f"missing included files: {', '.join(missing)}"],
        }

    result = run_case(
        task_dir,
        primary_dut,
        tb_path,
        output_root=output_root / task_id,
        timeout_s=timeout_s,
        task_id_override=task_id,
    )
    result["gold_dir"] = str(gold_dir)
    result["gold_tb"] = str(tb_path)
    result["gold_includes"] = includes
    result["behavior_check_available"] = has_behavior_check(task_id)
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--output-root",
        default="results/gold-suite",
        help="Output directory relative to the benchmark root unless absolute.",
    )
    ap.add_argument("--timeout-s", type=int, default=180)
    ap.add_argument(
        "--task",
        action="append",
        default=[],
        help="Restrict to one or more task IDs with gold assets.",
    )
    args = ap.parse_args()

    selected = set(args.task) if args.task else None
    out_root = Path(args.output_root)
    if not out_root.is_absolute():
        out_root = benchmark_root() / out_root
    out_root.mkdir(parents=True, exist_ok=True)

    results = [
        run_gold_case(task_dir, out_root, args.timeout_s)
        for task_dir in list_gold_task_dirs(selected)
    ]

    summary = {
        "tasks_total": len(results),
        "pass_count": sum(1 for r in results if r["status"] == "PASS"),
        "fail_count": sum(1 for r in results if r["status"] != "PASS"),
        "task_ids": [r["task_id"] for r in results],
        "results": results,
    }
    (out_root / "summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
