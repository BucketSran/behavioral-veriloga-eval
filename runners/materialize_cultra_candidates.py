#!/usr/bin/env python3
"""Materialize C-ULTRA candidates with skill accept/reject validation.

C-ULTRA starts from an existing compile-guarded generated root, routes each
compile/interface failure through compile skills, applies one safe fixer action
at a time, and accepts the edit only if a quick strict-EVAS score improves the
compile-closure rank.  Rejected edits are rolled back.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from compile_hard_guard import _apply_fixer_action, apply_compile_skill_actions
from compile_skill_library import select_compile_skills, skill_summary
from generate import list_bench_task_dirs
from run_adaptive_repair import _compile_closure_rank
from score import score_one_task


COMPILE_STATUSES = {"FAIL_DUT_COMPILE", "FAIL_TB_COMPILE", "FAIL_INFRA"}


def _json_read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _copy_sample(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for path in sorted(src.glob("*")):
        if path.is_file():
            shutil.copy2(path, dst / path.name)


def _compile_failures_from_summary(summary_path: Path) -> dict[str, dict]:
    summary = _json_read(summary_path)
    failures = summary.get("evas", {}).get("fail_tasks", [])
    selected: dict[str, dict] = {}
    for item in failures:
        status = item.get("status")
        if status not in COMPILE_STATUSES:
            continue
        notes = [str(note) for note in item.get("notes", [])]
        if status == "FAIL_INFRA" and not any(
            marker in " ".join(notes).lower()
            for marker in ("missing_generated_files", "missing_staged_tb", "compile", "preflight")
        ):
            continue
        task_id = item.get("task_id")
        if task_id:
            selected[task_id] = {"status": status, "notes": notes}
    return selected


def _task_sample_dir(root: Path, model: str, task_id: str, sample_idx: int) -> Path:
    return root / model / task_id / f"sample_{sample_idx}"


def _existing_result(result_root: Path, task_id: str) -> dict | None:
    for name in ("evas_result.json", "result.json"):
        path = result_root / task_id / name
        if path.exists():
            return _json_read(path)
    return None


def _result_notes(result: dict | None, fallback_notes: list[str]) -> list[str]:
    if not result:
        return fallback_notes
    notes = result.get("evas_notes") or result.get("notes") or []
    return [str(note) for note in notes]


def _wrong_function_gate_action(
    *,
    before_notes: list[str],
    rejected_result: dict | None,
    pass_idx: int,
) -> dict | None:
    """Classify rejected unique module renames that reveal wrong-function bodies.

    The gate intentionally does not edit files.  It records that a linkage fix
    was tried, but the renamed body still had a public-interface mismatch, so
    the case should be routed to prompt-side regeneration rather than another
    deterministic compile patch.
    """
    before_text = " ".join(str(note) for note in before_notes)
    before_match = re.search(
        r"undefined_module=(?P<missing>[^;|\s]+);available_modules=(?P<available>[^|\s]+)",
        before_text,
    )
    if not before_match:
        return None
    missing = [item for item in before_match.group("missing").split(",") if item and item != "<none>"]
    available = [item for item in before_match.group("available").split(",") if item and item != "<none>"]
    if len(missing) != 1 or len(available) != 1:
        return None

    after_notes = _result_notes(rejected_result, [])
    after_text = " ".join(after_notes)
    mismatch_re = re.compile(
        r"instance_port_count_mismatch=[^:]+:(?P<inst>[^:]+):(?P<model>[^:]+):"
        r"nodes=(?P<nodes>\d+):ports=(?P<ports>\d+)"
    )
    for match in mismatch_re.finditer(after_text):
        if match.group("model") != missing[0]:
            continue
        nodes = int(match.group("nodes"))
        ports = int(match.group("ports"))
        return {
            "id": "wrong_function_regeneration_gate",
            "version": "0.1",
            "description": (
                "Classify rejected module-name repairs that expose a public "
                "interface mismatch as wrong-function generation."
            ),
            "fixer": None,
            "judge": "spectre_strict_preflight",
            "safe_autofix": False,
            "pass": pass_idx,
            "edits": [],
            "decision": "route_to_prompt_regeneration",
            "missing_module": missing[0],
            "renamed_from": available[0],
            "evidence": [
                f"undefined_module={missing[0]};available_modules={available[0]}",
                (
                    f"instance_port_count_mismatch:{match.group('inst')}:{match.group('model')}:"
                    f"nodes={nodes}:ports={ports}"
                ),
            ],
            "reason": (
                "A unique module rename was rejected because the renamed body "
                "does not match the public harness port signature; this is not "
                "a safe deterministic compile fix."
            ),
        }
    return None


def _score_candidate(
    *,
    task_id: str,
    task_dir: Path,
    sample_dir: Path,
    output_root: Path,
    model: str,
    sample_idx: int,
    timeout_s: int,
) -> dict:
    return score_one_task(
        task_id,
        task_dir,
        sample_dir,
        output_root,
        model=model,
        sample_idx=sample_idx,
        temperature=0.0,
        top_p=1.0,
        timeout_s=timeout_s,
    )


def _update_meta(sample_dir: Path, *, actions: list[dict], source_root: Path) -> None:
    meta_path = sample_dir / "generation_meta.json"
    try:
        meta = _json_read(meta_path) if meta_path.exists() else {}
    except Exception:
        meta = {}
    meta["cultra_skill_accept_reject"] = {
        "applied": True,
        "source_generated_root": str(source_root),
        "actions": actions,
        "edited_at": datetime.now(timezone.utc).isoformat(),
    }
    _json_write(meta_path, meta)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bench-dir", required=True, type=Path)
    parser.add_argument("--source-generated-dir", required=True, type=Path)
    parser.add_argument("--source-result-root", required=True, type=Path)
    parser.add_argument("--source-summary", required=True, type=Path)
    parser.add_argument("--output-generated-dir", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--model", default="kimi-k2.5")
    parser.add_argument("--sample-idx", type=int, default=0)
    parser.add_argument("--timeout-s", type=int, default=240)
    parser.add_argument("--max-skill-passes", type=int, default=2)
    parser.add_argument(
        "--batch-fallback",
        action="store_true",
        help=(
            "After all single-skill attempts in a pass fail to improve, try one "
            "transaction candidate with all currently routed safe fixers applied together."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = args.source_generated_dir.resolve()
    output_root = args.output_generated_dir.resolve()
    if output_root.exists():
        shutil.rmtree(output_root)
    shutil.copytree(source_root, output_root)
    if args.output_root.exists():
        shutil.rmtree(args.output_root)
    args.output_root.mkdir(parents=True, exist_ok=True)

    selected = _compile_failures_from_summary(args.source_summary)
    task_dirs = {
        task_id: task_dir
        for task_id, task_dir in list_bench_task_dirs(args.bench_dir, selected=set(selected))
    }
    manifest: dict[str, object] = {
        "mode": "C-ULTRA",
        "source_generated_dir": str(source_root),
        "source_result_root": str(args.source_result_root.resolve()),
        "source_summary": str(args.source_summary.resolve()),
        "output_generated_dir": str(output_root),
        "output_root": str(args.output_root.resolve()),
        "model": args.model,
        "sample_idx": args.sample_idx,
        "batch_fallback": args.batch_fallback,
        "selected_tasks": len(selected),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tasks": {},
    }

    for task_id, info in sorted(selected.items()):
        sample_dir = _task_sample_dir(output_root, args.model, task_id, args.sample_idx)
        task_dir = task_dirs.get(task_id)
        actions: list[dict] = []
        if task_dir is None or not sample_dir.exists():
            manifest["tasks"][task_id] = {
                "status": info["status"],
                "notes": info["notes"],
                "actions": actions,
                "error": "missing_task_or_sample",
            }
            continue

        current_result = _existing_result(args.source_result_root, task_id) or {
            "status": info["status"],
            "scores": {},
            "evas_notes": info["notes"],
        }
        current_rank = _compile_closure_rank(task_id, current_result)
        current_notes = _result_notes(current_result, info["notes"])
        attempted: set[str] = set()

        for pass_idx in range(1, args.max_skill_passes + 1):
            selected_skills = [
                skill
                for skill in select_compile_skills(current_notes)
                if skill.fixer and skill.safe_autofix and skill.id not in attempted
            ]
            if not selected_skills:
                break
            accepted_this_pass = False
            for skill in selected_skills:
                attempted.add(skill.id)
                candidate_dir = args.output_root / "_candidates" / task_id / f"pass{pass_idx}_{skill.id}"
                _copy_sample(sample_dir, candidate_dir)
                edits = _apply_fixer_action(candidate_dir, fixer=str(skill.fixer), notes=current_notes)
                action = skill_summary(skill)
                action.update({
                    "pass": pass_idx,
                    "edits": edits,
                    "decision": "no_edit",
                    "before_status": current_result.get("status"),
                    "before_rank": list(current_rank),
                })
                if edits:
                    scored = _score_candidate(
                        task_id=task_id,
                        task_dir=task_dir,
                        sample_dir=candidate_dir,
                        output_root=args.output_root / "quick" / f"pass{pass_idx}_{skill.id}",
                        model=args.model,
                        sample_idx=args.sample_idx,
                        timeout_s=args.timeout_s,
                    )
                    next_rank = _compile_closure_rank(task_id, scored)
                    improved = next_rank > current_rank
                    action.update({
                        "after_status": scored.get("status"),
                        "after_rank": list(next_rank),
                        "improved": improved,
                    })
                    if improved:
                        _copy_sample(candidate_dir, sample_dir)
                        current_result = scored
                        current_rank = next_rank
                        current_notes = _result_notes(scored, current_notes)
                        action["decision"] = "accepted"
                        accepted_this_pass = True
                    else:
                        action["decision"] = "rejected"
                actions.append(action)
                if action.get("decision") == "rejected" and skill.id == "module_name_linkage":
                    gate = _wrong_function_gate_action(
                        before_notes=current_notes,
                        rejected_result=locals().get("scored"),
                        pass_idx=pass_idx,
                    )
                    if gate:
                        actions.append(gate)
            if not accepted_this_pass and args.batch_fallback and len(selected_skills) > 1:
                candidate_dir = args.output_root / "_candidates" / task_id / f"pass{pass_idx}_batch"
                _copy_sample(sample_dir, candidate_dir)
                batch_manifest = apply_compile_skill_actions(candidate_dir, notes=current_notes)
                batch_edits = [str(edit) for edit in batch_manifest.get("edits", [])]
                action = {
                    "id": "batch_transaction",
                    "version": "0.1",
                    "description": "Apply all currently routed safe compile fixers as one transaction.",
                    "fixer": "batch",
                    "judge": "spectre_strict_preflight",
                    "safe_autofix": True,
                    "pass": pass_idx,
                    "selected_skills": batch_manifest.get("selected_skills", []),
                    "edits": batch_edits,
                    "decision": "no_edit",
                    "before_status": current_result.get("status"),
                    "before_rank": list(current_rank),
                }
                if batch_edits:
                    scored = _score_candidate(
                        task_id=task_id,
                        task_dir=task_dir,
                        sample_dir=candidate_dir,
                        output_root=args.output_root / "quick" / f"pass{pass_idx}_batch",
                        model=args.model,
                        sample_idx=args.sample_idx,
                        timeout_s=args.timeout_s,
                    )
                    next_rank = _compile_closure_rank(task_id, scored)
                    improved = next_rank > current_rank
                    action.update({
                        "after_status": scored.get("status"),
                        "after_rank": list(next_rank),
                        "improved": improved,
                    })
                    if improved:
                        _copy_sample(candidate_dir, sample_dir)
                        current_result = scored
                        current_rank = next_rank
                        current_notes = _result_notes(scored, current_notes)
                        action["decision"] = "accepted"
                        accepted_this_pass = True
                    else:
                        action["decision"] = "rejected"
                actions.append(action)
            if not accepted_this_pass:
                break

        _update_meta(sample_dir, actions=actions, source_root=source_root)
        _json_write(args.output_root / "best" / task_id / "result.json", current_result)
        manifest["tasks"][task_id] = {
            "source_status": info["status"],
            "final_status": current_result.get("status"),
            "final_rank": list(current_rank),
            "actions": actions,
        }

    _json_write(output_root / "cultra_manifest.json", manifest)
    print(json.dumps({"output_generated_dir": str(output_root), "selected_tasks": len(selected)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
