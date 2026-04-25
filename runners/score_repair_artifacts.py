#!/usr/bin/env python3
"""Score repair-loop artifacts and keep the best observed round.

Unlike ``score.py``, this runner is meant for D/E/F/G-style repair outputs where
one task may contain ``sample_0`` plus ``sample_0_roundN`` directories.  It
re-scores each available round with the current EVAS/checker code, then reports
the best round per task.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
from pathlib import Path

from score import (
    ALL_FAMILIES,
    build_model_results,
    list_all_task_dirs,
    read_meta,
    score_one_task,
)


ROOT = Path(__file__).resolve().parents[1]


def _json_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _round_key(path: Path) -> tuple[int, str]:
    if path.name == "sample_0":
        return (0, path.name)
    match = re.match(r"sample_0_round([0-9]+)$", path.name)
    if match:
        return (int(match.group(1)), path.name)
    return (9999, path.name)


def _candidate_dirs(generated_root: Path, model: str, task_id: str) -> list[Path]:
    task_root = generated_root / model / task_id
    if not task_root.is_dir():
        return []
    dirs = [
        path
        for path in task_root.iterdir()
        if path.is_dir() and (path.name == "sample_0" or re.match(r"sample_0_round[0-9]+$", path.name))
    ]
    return sorted(dirs, key=_round_key)


def _task_pass(result: dict) -> bool:
    scores = result.get("scores", {})
    required = result.get("required_axes", ["dut_compile", "tb_compile", "sim_correct"])
    return all(scores.get(axis, 0.0) >= 1.0 for axis in required)


def _rank(result: dict) -> tuple[float, float, float, int]:
    scores = result.get("scores", {})
    return (
        1.0 if _task_pass(result) else 0.0,
        float(scores.get("weighted_total", 0.0)),
        float(scores.get("sim_correct", 0.0)),
        1 if result.get("status") == "PASS" else 0,
    )


def score_task(
    *,
    task_id: str,
    task_dir: Path,
    generated_root: Path,
    model: str,
    output_root: Path,
    timeout_s: int,
    save_policy: str,
) -> dict:
    candidates = _candidate_dirs(generated_root, model, task_id)
    if not candidates:
        meta = read_meta(task_dir)
        result = {
            "model": model,
            "task_id": task_id,
            "family": meta.get("family", "unknown"),
            "category": meta.get("category", "unknown"),
            "status": "FAIL_INFRA",
            "scores": {"dut_compile": 0.0, "tb_compile": 0.0, "sim_correct": 0.0, "weighted_total": 0.0},
            "required_axes": meta.get("scoring", ["dut_compile", "tb_compile", "sim_correct"]),
            "evas_notes": ["missing_repair_artifact"],
            "round": None,
            "candidate_count": 0,
            "attempts": [],
        }
        _json_write(output_root / model / task_id / "result.json", result)
        return result

    attempts: list[dict] = []
    best_result: dict | None = None
    best_rank: tuple[float, float, float, int] | None = None
    for sample_dir in candidates:
        round_name = sample_dir.name
        round_output = output_root / model / task_id / round_name
        result = score_one_task(
            task_id,
            task_dir,
            sample_dir,
            round_output,
            model=model,
            sample_idx=0,
            temperature=0.0,
            top_p=1.0,
            timeout_s=timeout_s,
            save_policy=save_policy,
        )
        rank = _rank(result)
        attempts.append(
            {
                "round": round_name,
                "status": result.get("status"),
                "scores": result.get("scores"),
                "rank": list(rank),
                "evas_notes": result.get("evas_notes", []),
                "artifacts": result.get("artifacts", {}),
                "result_json": str(round_output / task_id / "result.json"),
            }
        )
        if best_rank is None or rank > best_rank:
            best_rank = rank
            best_result = dict(result)
            best_result["round"] = round_name

    assert best_result is not None
    best_result["candidate_count"] = len(candidates)
    best_result["attempts"] = attempts
    best_result["best_rank"] = list(best_rank or ())
    _json_write(output_root / model / task_id / "result.json", best_result)
    return best_result


def run(args: argparse.Namespace) -> dict:
    generated_root = Path(args.generated_root).resolve()
    output_root = Path(args.output_dir).resolve()
    selected = set(args.task or [])
    families = tuple(args.family) if args.family else ALL_FAMILIES
    task_items = list_all_task_dirs(families=families, selected=selected or None)

    output_root.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []

    def _one(item: tuple[str, Path]) -> dict:
        task_id, task_dir = item
        result = score_task(
            task_id=task_id,
            task_dir=task_dir,
            generated_root=generated_root,
            model=args.model,
            output_root=output_root,
            timeout_s=args.timeout_s,
            save_policy=args.save_policy,
        )
        print(
            f"[score-repair] {task_id}: round={result.get('round')} "
            f"status={result.get('status')} pass={_task_pass(result)}"
        )
        return result

    worker_count = max(1, min(args.workers, len(task_items)))
    if worker_count == 1:
        for item in task_items:
            results.append(_one(item))
    else:
        print(f"[score-repair] parallel EVAS scoring with {worker_count} workers")
        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [executor.submit(_one, item) for item in task_items]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

    aggregate = build_model_results(args.model, results, temperature=0.0, top_p=1.0)
    aggregate.update(
        {
            "mode": "repair_artifact_best_round",
            "generated_root": str(generated_root),
            "output_root": str(output_root),
            "timeout_s": args.timeout_s,
            "workers": worker_count,
            "save_policy": args.save_policy,
        }
    )
    _json_write(output_root / args.model / "model_results.json", aggregate)
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser(description="Score D/E/F/G repair artifacts and select best round.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--generated-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--task", action="append")
    parser.add_argument("--family", action="append", choices=ALL_FAMILIES)
    parser.add_argument("--timeout-s", type=int, default=120)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--save-policy", choices=("contract", "debug"), default="contract")
    args = parser.parse_args()
    aggregate = run(args)
    print(
        f"[score-repair] {args.model} tasks={aggregate['total_tasks']} "
        f"Pass@1={aggregate['pass_at_1']} ({aggregate['pass_count']}/{aggregate['total_tasks']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

