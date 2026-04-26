#!/usr/bin/env python3
"""Materialize condition-H formal artifacts.

The signature-guided H runner validates repaired DUTs with the benchmark
gold/reference harness.  To measure formal end-to-end impact, this script
creates a normal generated-artifact tree:

1. copy the selected best round from a base condition such as F or G;
2. replace only the DUT file for H strict rescues;
3. keep the base generated testbench/harness intact;
4. score the resulting tree with ``score.py``.

This keeps H's DUT-side evidence separate from full formal scoring while making
the transfer test reproducible.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from score import ALL_FAMILIES, list_all_task_dirs, read_meta


ROOT = Path(__file__).resolve().parents[1]


def _json_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _base_result_path(base_score_root: Path, model: str, task_id: str) -> Path | None:
    candidates = [
        base_score_root / model / task_id / "result.json",
        base_score_root / task_id / "result.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _selected_round(base_score_root: Path, model: str, task_id: str) -> str:
    result_path = _base_result_path(base_score_root, model, task_id)
    if result_path is None:
        return "sample_0"
    try:
        return str(_load_json(result_path).get("round") or "sample_0")
    except Exception:
        return "sample_0"


def _h_summary_path(h_summary_root: Path, task_id: str) -> Path:
    return h_summary_root / task_id / "summary.json"


def _load_h_summary(h_summary_root: Path, task_id: str) -> dict | None:
    path = _h_summary_path(h_summary_root, task_id)
    if not path.exists():
        return None
    try:
        return _load_json(path)
    except Exception:
        return None


def _should_apply_h(summary: dict | None, policy: str) -> bool:
    if not summary:
        return False
    if policy == "rescued":
        return bool(summary.get("rescued")) and summary.get("best_status") == "PASS"
    if policy == "best-pass":
        return summary.get("best_status") == "PASS" and summary.get("best_variant") != "baseline"
    raise ValueError(f"unknown policy: {policy}")


def _copy_sample_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _replace_dut(sample_dir: Path, best_dut_path: Path) -> Path:
    target = sample_dir / best_dut_path.name
    if not target.exists():
        va_files = sorted(sample_dir.glob("*.va"))
        if len(va_files) == 1:
            target = va_files[0]
        else:
            target = sample_dir / best_dut_path.name
    shutil.copy2(best_dut_path, target)
    return target


def materialize_task(
    *,
    task_id: str,
    task_dir: Path,
    model: str,
    base_generated_root: Path,
    base_score_root: Path,
    h_summary_root: Path,
    output_generated_root: Path,
    apply_policy: str,
) -> dict:
    round_name = _selected_round(base_score_root, model, task_id)
    src_sample = base_generated_root / model / task_id / round_name
    dst_sample = output_generated_root / model / task_id / "sample_0"
    meta = read_meta(task_dir)

    record: dict = {
        "task_id": task_id,
        "family": meta.get("family", "unknown"),
        "base_round": round_name,
        "base_sample_dir": str(src_sample),
        "output_sample_dir": str(dst_sample),
        "h_applied": False,
        "h_reason": "not_eligible_or_not_rescued",
    }

    if not src_sample.is_dir():
        record["h_reason"] = "missing_base_sample"
        dst_sample.mkdir(parents=True, exist_ok=True)
        _json_write(dst_sample / "h_materialization.json", record)
        return record

    _copy_sample_tree(src_sample, dst_sample)

    summary = _load_h_summary(h_summary_root, task_id)
    if _should_apply_h(summary, apply_policy):
        best_dut = Path(str(summary.get("best_dut_path", "")))
        if best_dut.exists():
            replaced = _replace_dut(dst_sample, best_dut)
            record.update(
                {
                    "h_applied": True,
                    "h_reason": "strict_rescue_applied" if summary.get("rescued") else "best_pass_applied",
                    "h_template_family": summary.get("template_family"),
                    "h_failure_signature": summary.get("failure_signature"),
                    "h_best_variant": summary.get("best_variant"),
                    "h_best_dut_path": str(best_dut),
                    "replaced_dut_path": str(replaced),
                }
            )
        else:
            record["h_reason"] = "missing_h_best_dut"

    _json_write(dst_sample / "h_materialization.json", record)
    return record


def run(args: argparse.Namespace) -> dict:
    model = args.model
    base_generated_root = Path(args.base_generated_root).resolve()
    base_score_root = Path(args.base_score_root).resolve()
    h_summary_root = Path(args.h_summary_root).resolve()
    output_generated_root = Path(args.output_generated_root).resolve()

    selected = set(args.task or [])
    families = tuple(args.family) if args.family else ALL_FAMILIES
    task_items = list_all_task_dirs(families=families, selected=selected or None)

    records = [
        materialize_task(
            task_id=task_id,
            task_dir=task_dir,
            model=model,
            base_generated_root=base_generated_root,
            base_score_root=base_score_root,
            h_summary_root=h_summary_root,
            output_generated_root=output_generated_root,
            apply_policy=args.apply_policy,
        )
        for task_id, task_dir in task_items
    ]

    aggregate = {
        "mode": "condition_H_formal_materialization",
        "definition": "base best-round artifacts plus H repaired DUT replacements",
        "model": model,
        "base_generated_root": str(base_generated_root),
        "base_score_root": str(base_score_root),
        "h_summary_root": str(h_summary_root),
        "output_generated_root": str(output_generated_root),
        "apply_policy": args.apply_policy,
        "task_count": len(records),
        "h_applied_count": sum(1 for record in records if record.get("h_applied")),
        "h_applied_tasks": [record["task_id"] for record in records if record.get("h_applied")],
        "records": records,
    }
    _json_write(output_generated_root / model / "condition_h_materialization.json", aggregate)
    print(
        f"[materialize-H] tasks={aggregate['task_count']} "
        f"h_applied={aggregate['h_applied_count']} -> {output_generated_root / model}"
    )
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize condition-H formal generated artifacts.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-generated-root", required=True)
    parser.add_argument("--base-score-root", required=True)
    parser.add_argument("--h-summary-root", required=True)
    parser.add_argument("--output-generated-root", required=True)
    parser.add_argument("--apply-policy", choices=("rescued", "best-pass"), default="rescued")
    parser.add_argument("--task", action="append")
    parser.add_argument("--family", action="append", choices=ALL_FAMILIES)
    args = parser.parse_args()
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

