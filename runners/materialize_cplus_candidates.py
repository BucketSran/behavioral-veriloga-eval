#!/usr/bin/env python3
"""Materialize C-PLUS candidates from an existing generated root.

C-PLUS is defined as C plus deterministic compile-hard guards.  This script
copies an existing generated candidate root, applies local guards only to tasks
that failed the compile/interface gate in a prior strict-EVAS result, and writes
an auditable manifest.  It does not call an LLM.
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from compile_hard_guard import apply_compile_skill_actions


COMPILE_STATUSES = {"FAIL_DUT_COMPILE", "FAIL_TB_COMPILE", "FAIL_INFRA"}


def _json_read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def _copy_generated_root(source_root: Path, output_root: Path) -> None:
    if output_root.exists():
        shutil.rmtree(output_root)
    shutil.copytree(source_root, output_root)


def _update_generation_meta(
    sample_dir: Path,
    *,
    source_root: Path,
    action_manifest: dict[str, object],
    status: str,
    notes: list[str],
) -> None:
    meta_path = sample_dir / "generation_meta.json"
    if meta_path.exists():
        try:
            meta = _json_read(meta_path)
        except Exception:
            meta = {}
    else:
        meta = {}
    meta.setdefault("mode", "candidate")
    meta["cplus_source_generated_root"] = str(source_root)
    meta["cplus_compile_hard_guard"] = {
        "applied": True,
        "source_status": status,
        "source_notes": notes,
        "selected_skills": action_manifest.get("selected_skills", []),
        "edits": action_manifest.get("edits", []),
        "edited_at": datetime.now(timezone.utc).isoformat(),
    }
    _json_write(meta_path, meta)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-generated-dir", required=True, type=Path)
    parser.add_argument("--source-summary", required=True, type=Path)
    parser.add_argument("--output-generated-dir", required=True, type=Path)
    parser.add_argument("--model", default="kimi-k2.5")
    parser.add_argument("--sample-idx", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = args.source_generated_dir.resolve()
    output_root = args.output_generated_dir.resolve()
    _copy_generated_root(source_root, output_root)

    selected = _compile_failures_from_summary(args.source_summary)
    manifest: dict[str, object] = {
        "mode": "C-PLUS",
        "source_generated_dir": str(source_root),
        "source_summary": str(args.source_summary.resolve()),
        "output_generated_dir": str(output_root),
        "model": args.model,
        "sample_idx": args.sample_idx,
        "selected_tasks": len(selected),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tasks": {},
    }

    for task_id, info in sorted(selected.items()):
        sample_dir = _task_sample_dir(output_root, args.model, task_id, args.sample_idx)
        if not sample_dir.exists():
            manifest["tasks"][task_id] = {
                "status": info["status"],
                "notes": info["notes"],
                "edits": [],
                "error": "sample_dir_missing",
            }
            continue
        action_manifest = apply_compile_skill_actions(sample_dir, notes=info["notes"])
        _update_generation_meta(
            sample_dir,
            source_root=source_root,
            action_manifest=action_manifest,
            status=info["status"],
            notes=info["notes"],
        )
        manifest["tasks"][task_id] = {
            "status": info["status"],
            "notes": info["notes"],
            "selected_skills": action_manifest.get("selected_skills", []),
            "edits": action_manifest.get("edits", []),
        }

    _json_write(output_root / "cplus_manifest.json", manifest)
    print(json.dumps({"output_generated_dir": str(output_root), "selected_tasks": len(selected)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
