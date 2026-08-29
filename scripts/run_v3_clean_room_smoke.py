#!/usr/bin/env python3
"""Run a one-task v3 clean-room generation-to-hidden-scoring smoke.

The smoke creates a temporary public task room containing only the public
instruction, starter artifacts, and one deterministic candidate output. Hidden
testbenches, checker routing, and the canonical solution stay in the evaluator
repository and are consumed only by the existing v3 hidden scoring path.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import tempfile
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNERS = ROOT / "runners"
if str(RUNNERS) not in sys.path:
    sys.path.insert(0, str(RUNNERS))

import run_vabench_v3_model_eval as v3_eval  # noqa: E402


DEFAULT_TASK = "014-sar-logic"
DEFAULT_MODEL = "deterministic-clean-room-fixture"
FORBIDDEN_CLEAN_ROOM_PARTS = {
    "solution",
    "test_hidden",
    "test_harness",
    "negative_variants",
    "evaluator",
}
PIPELINE_CLAIM_SCOPE = "single_task_clean_room_pipeline"


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_identity(path: Path) -> dict[str, Any]:
    identity: dict[str, Any] = {"path": rel(path), "exists": path.is_file()}
    if path.is_file():
        identity.update({"sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    return identity


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def resolve_repo_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


@contextmanager
def installed_evaluator_runtime(evas_command: str):
    updates = {
        "VABENCH_EVAS_COMMAND": evas_command,
        "VAEVAS_EVAS_PERSISTENT_WORKER": "0",
    }
    previous = {name: os.environ.get(name) for name in updates}
    try:
        os.environ.update(updates)
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def selected_single_row(task: str, selection_surface: str) -> dict[str, Any]:
    args = v3_eval.parse_args(
        [
            "--list",
            "--selection-surface",
            selection_surface,
            "--task",
            task,
        ]
    )
    rows = v3_eval.selected_rows(args)
    if len(rows) != 1:
        raise ValueError(f"expected exactly one v3 task for {task!r}, selected {len(rows)}")
    return rows[0]


def copy_public_room(task_dir: Path, row: dict[str, Any], clean_room: Path) -> dict[str, Any]:
    public_task = clean_room / "task"
    public_task.mkdir(parents=True, exist_ok=True)
    instruction_src = task_dir / "instruction.md"
    instruction_dst = public_task / "instruction.md"
    shutil.copyfile(instruction_src, instruction_dst)

    starter_dir = public_task / "starter"
    starter_dir.mkdir()
    copied_starter: list[str] = []
    for artifact_name in list(row.get("target_artifacts") or []) + list(row.get("support_artifacts") or []):
        src = task_dir / "starter" / artifact_name
        if src.is_file():
            dst = starter_dir / Path(artifact_name).name
            shutil.copyfile(src, dst)
            copied_starter.append(dst.relative_to(clean_room).as_posix())

    return {
        "instruction": file_identity(instruction_dst),
        "starter_artifacts": copied_starter,
    }


def deterministic_candidate_source(task_dir: Path, target_artifacts: list[str], adapter: str, fixture: Path | None) -> Path:
    if not target_artifacts:
        raise ValueError("selected task has no target artifact")
    target_name = target_artifacts[0]
    if adapter == "solution":
        source = task_dir / "solution" / target_name
    elif adapter == "starter":
        source = task_dir / "starter" / target_name
    elif adapter == "fixture":
        if fixture is None:
            raise ValueError("--fixture-candidate is required when --adapter=fixture")
        source = fixture
    else:  # pragma: no cover - argparse owns choices.
        raise ValueError(f"unsupported adapter {adapter!r}")
    if not source.is_file():
        raise FileNotFoundError(f"missing deterministic candidate source: {source}")
    return source


def write_deterministic_candidate(
    *,
    row: dict[str, Any],
    task_dir: Path,
    clean_room: Path,
    adapter: str,
    fixture: Path | None,
    model: str,
    sample_idx: int,
) -> dict[str, Any]:
    slug = str(row["release_entry_id"])
    target_artifacts = list(row.get("target_artifacts") or [])
    source = deterministic_candidate_source(task_dir, target_artifacts, adapter, fixture)
    sample_dir = clean_room / "generated" / v3_eval.model_slug(model) / slug / f"sample_{sample_idx}"
    submission_dir = clean_room / "submission"
    sample_dir.mkdir(parents=True, exist_ok=True)
    submission_dir.mkdir(parents=True, exist_ok=True)

    target_name = target_artifacts[0]
    sample_candidate = sample_dir / target_name
    public_candidate = submission_dir / target_name
    shutil.copyfile(source, sample_candidate)
    shutil.copyfile(sample_candidate, public_candidate)

    generation_meta = {
        "status": "generated",
        "source": "deterministic_clean_room_adapter",
        "adapter": adapter,
        "benchmark": "benchmark-vabench-release-v3",
        "model": model,
        "model_slug": v3_eval.model_slug(model),
        "task_slug": slug,
        "task_id": row.get("task_id"),
        "sample_idx": sample_idx,
        "target_artifacts": target_artifacts,
        "saved_files": [sample_candidate.relative_to(clean_room / "generated").as_posix()],
        "claim_allowed": False,
        "claim_boundary": v3_eval.CLAIM_BOUNDARY,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(sample_dir / "generation_meta.json", generation_meta)

    return {
        "adapter": adapter,
        "adapter_source": file_identity(source),
        "sample_candidate": file_identity(sample_candidate),
        "public_candidate": file_identity(public_candidate),
        "generation_meta": file_identity(sample_dir / "generation_meta.json"),
    }


def clean_room_manifest(clean_room: Path) -> dict[str, Any]:
    files = sorted(path.relative_to(clean_room).as_posix() for path in clean_room.rglob("*") if path.is_file())
    forbidden = [
        item
        for item in files
        if any(part in FORBIDDEN_CLEAN_ROOM_PARTS for part in Path(item).parts)
    ]
    return {
        "path": str(clean_room),
        "file_count": len(files),
        "files": files,
        "forbidden_private_paths": forbidden,
        "private_paths_absent": not forbidden,
    }


def score_clean_room_candidate(
    *,
    row: dict[str, Any],
    clean_room: Path,
    output_root: Path,
    model: str,
    sample_idx: int,
    score_timeout_s: int,
    selection_surface: str,
) -> dict[str, Any]:
    args = v3_eval.parse_args(
        [
            "--stage",
            "score",
            "--selection-surface",
            selection_surface,
            "--task",
            str(row["release_entry_id"]),
            "--model",
            model,
            "--sample-idx",
            str(sample_idx),
            "--score-timeout-s",
            str(score_timeout_s),
            "--score-workers",
            "1",
            "--generated-root",
            str(clean_room / "generated"),
            "--output-root",
            str(output_root),
        ]
    )
    return v3_eval.score_one(row, args, output_root / "evas_results")


def failure_evidence(score: dict[str, Any]) -> dict[str, Any] | None:
    status = str(score.get("status") or "")
    if status == "PASS":
        return None
    notes = [str(note) for note in score.get("evas_notes", [])]
    identity = score.get("evas_identity")
    infrastructure_markers = (
        "rust_core_loadable",
        "rust_core_present",
        "rust_core_error",
        "EVAS does not fall back",
    )
    likely_infrastructure = False
    if isinstance(identity, dict):
        likely_infrastructure = identity.get("rust_core_loadable") is False or bool(identity.get("rust_core_error"))
    if any(any(marker in note for marker in infrastructure_markers) for note in notes):
        likely_infrastructure = True
    return {
        "status": status,
        "runner_failure_class": score.get("failure_class"),
        "smoke_failure_class": "infrastructure" if likely_infrastructure else score.get("failure_class"),
        "termination_reason": score.get("termination_reason"),
        "notes": notes,
        "evas_identity": identity,
    }


def run_smoke(args: argparse.Namespace) -> dict[str, Any]:
    started = time.perf_counter()
    row = selected_single_row(args.task, args.selection_surface)
    task_dir = ROOT / str(row["task_dir"])
    out_path = resolve_repo_path(args.out)
    output_root = resolve_repo_path(args.output_root)

    temp_parent_ctx: tempfile.TemporaryDirectory[str] | None = None
    clean_room_ctx: tempfile.TemporaryDirectory[str] | None = None
    try:
        if output_root is None:
            temp_parent_ctx = tempfile.TemporaryDirectory(prefix="v3_clean_room_smoke_output_")
            output_root = Path(temp_parent_ctx.name) / "output"
        if args.clean_room:
            clean_room = resolve_repo_path(args.clean_room)
            assert clean_room is not None
            if clean_room.exists():
                raise FileExistsError(f"clean room already exists: {clean_room}")
            clean_room.mkdir(parents=True)
        else:
            clean_room_ctx = tempfile.TemporaryDirectory(prefix="v3_clean_room_public_")
            clean_room = Path(clean_room_ctx.name)

        public_inputs = copy_public_room(task_dir, row, clean_room)
        candidate = write_deterministic_candidate(
            row=row,
            task_dir=task_dir,
            clean_room=clean_room,
            adapter=args.adapter,
            fixture=resolve_repo_path(args.fixture_candidate),
            model=args.model,
            sample_idx=args.sample_idx,
        )
        before_score_manifest = clean_room_manifest(clean_room)
        if not before_score_manifest["private_paths_absent"]:
            raise RuntimeError(
                "clean room contains private evaluator paths: "
                + ",".join(before_score_manifest["forbidden_private_paths"])
            )

        with installed_evaluator_runtime(args.evas_command):
            score = score_clean_room_candidate(
                row=row,
                clean_room=clean_room,
                output_root=output_root,
                model=args.model,
                sample_idx=args.sample_idx,
                score_timeout_s=args.score_timeout_s,
                selection_surface=args.selection_surface,
            )

        pre_cleanup_exists = clean_room.exists()
        if clean_room_ctx is not None and not args.keep_clean_room:
            clean_room_ctx.cleanup()
            clean_room_ctx = None
        post_cleanup_exists = clean_room.exists()
        environment_provenance, environment_problems = v3_eval.environment_evidence(args)
        claim_blockers: list[str] = []
        if score.get("status") != "PASS":
            claim_blockers.append("hidden_scoring_smoke_failed")
        if not before_score_manifest["private_paths_absent"]:
            claim_blockers.append("private_evaluator_path_exposed")
        if clean_room_ctx is None and post_cleanup_exists:
            claim_blockers.append("clean_room_cleanup_not_managed")
        elif post_cleanup_exists:
            claim_blockers.append("clean_room_cleanup_failed")
        claim_blockers.extend(environment_problems)
        verified_live_evas = (
            (environment_provenance or {}).get("payload", {}).get("live_evas", {})
        )
        verified_command = (
            verified_live_evas.get("command")
            if isinstance(verified_live_evas, dict)
            else None
        )
        if verified_command != args.evas_command:
            claim_blockers.append("executed_evas_command_not_bound_to_environment_evidence")
        if platform.python_version() != v3_eval.EXPECTED_PYTHON_VERSION:
            claim_blockers.append("executed_python_version_mismatch")

        payload = {
            "date": datetime.now(timezone.utc).isoformat(),
            "benchmark": "benchmark-vabench-release-v3",
            "smoke": "v3_clean_room_hidden_scoring",
            "status": "PASS" if score.get("status") == "PASS" else "FAIL",
            "task": {
                "release_entry_id": row.get("release_entry_id"),
                "task_id": row.get("task_id"),
                "form": row.get("form"),
                "target_artifacts": row.get("target_artifacts"),
                "support_artifacts": row.get("support_artifacts"),
            },
            "model": args.model,
            "sample_idx": args.sample_idx,
            "selection_surface": args.selection_surface,
            "execution_policy": {
                "python_version": platform.python_version(),
                "evas_command": args.evas_command,
                "persistent_worker": False,
                "score_timeout_s": args.score_timeout_s,
                "retry_count": 0,
            },
            "clean_room_contract": {
                "visible_to_candidate": [
                    "task/instruction.md",
                    "task/starter/*",
                    "submission/*",
                ],
                "hidden_evaluator_only": [
                    "solution/*",
                    "test_hidden/*",
                    "test_harness/*",
                    "CHECKS.yaml",
                ],
                "private_paths_absent": before_score_manifest["private_paths_absent"],
                "forbidden_private_paths": before_score_manifest["forbidden_private_paths"],
            },
            "provenance": {
                "public_inputs": public_inputs,
                "candidate": candidate,
                "hidden_score_result": file_identity(output_root / "evas_results" / str(row["release_entry_id"]) / "result.json"),
                "score_outputs_root": rel(output_root / "evas_results"),
                "environment": environment_provenance,
            },
            "score": score,
            "failure": failure_evidence(score),
            "cleanup": {
                "clean_room_path": str(clean_room),
                "managed_temporary_clean_room": args.clean_room == "",
                "keep_clean_room": args.keep_clean_room,
                "pre_cleanup_exists": pre_cleanup_exists,
                "post_cleanup_exists": post_cleanup_exists,
            },
            "wall_s": round(time.perf_counter() - started, 6),
            "claim_scope": PIPELINE_CLAIM_SCOPE,
            "claim_allowed": not claim_blockers,
            "claim_gate": {
                "scope": PIPELINE_CLAIM_SCOPE,
                "status": "allowed" if not claim_blockers else "blocked",
                "allowed": not claim_blockers,
                "blocking_reasons": claim_blockers,
                "supports": "one-task generation-to-hidden-scoring pipeline connectivity only",
                "model_score_claim_allowed": False,
                "spectre_required": False,
            },
            "claim_boundary": v3_eval.CLAIM_BOUNDARY,
        }
        if out_path is not None:
            write_json(out_path, payload)
            payload["paths"] = {"smoke_json": rel(out_path)}
        return payload
    finally:
        if clean_room_ctx is not None and not args.keep_clean_room:
            clean_room_ctx.cleanup()
        if temp_parent_ctx is not None:
            temp_parent_ctx.cleanup()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default=DEFAULT_TASK, help="Single v3 task slug, number, or v3 task id.")
    parser.add_argument(
        "--selection-surface",
        choices=["candidate", "all"],
        default="candidate",
        help="Task selection surface for the one-row smoke.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--sample-idx", type=int, default=0)
    parser.add_argument("--score-timeout-s", type=int, default=180)
    parser.add_argument(
        "--adapter",
        choices=["solution", "starter", "fixture"],
        default="solution",
        help="Deterministic candidate adapter. solution is evaluator-side and not copied as a hidden asset.",
    )
    parser.add_argument("--fixture-candidate", default="")
    parser.add_argument(
        "--evas-command",
        default="evas",
        help="Installed evaluator command. The smoke disables source-tree auto-discovery and persistent workers.",
    )
    parser.add_argument(
        "--environment-evidence",
        default="",
        help="PASS JSON emitted by scripts/verify_evaluator_environment.py.",
    )
    parser.add_argument("--clean-room", default="", help="Optional explicit clean-room directory; must not exist.")
    parser.add_argument("--output-root", default="", help="Optional persistent evaluator output root.")
    parser.add_argument("--out", default="", help="Optional path for persistent smoke JSON.")
    parser.add_argument("--keep-clean-room", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print the JSON payload.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = run_smoke(args)
    except Exception as exc:  # noqa: BLE001 - CLI smoke must emit structured failure.
        payload = {
            "date": datetime.now(timezone.utc).isoformat(),
            "benchmark": "benchmark-vabench-release-v3",
            "smoke": "v3_clean_room_hidden_scoring",
            "status": "FAIL",
            "failure": f"{type(exc).__name__}: {exc}",
            "claim_allowed": False,
            "claim_boundary": v3_eval.CLAIM_BOUNDARY,
        }
        out_path = resolve_repo_path(getattr(args, "out", ""))
        if out_path is not None:
            write_json(out_path, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    if args.json or not args.out:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"[v3-clean-room-smoke] status={payload['status']} task={payload['task']['release_entry_id']}")
    if payload.get("status") != "PASS":
        return 1
    return 0 if payload.get("claim_allowed") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
