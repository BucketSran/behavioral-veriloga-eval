"""Opt-in production bridge from EVAS trusted replay to immutable evidence.

This module has no model, tool-observation, or trajectory output. Profiles are
trusted scoring inputs, not fields accepted from a candidate or judge output.
"""

from __future__ import annotations

from dataclasses import asdict
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shlex
import shutil
import sys
from typing import Any, Callable

import result_protocol as protocol

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runners.agent_harness import (  # noqa: E402
    EpisodeContext,
    FinalJudgment,
    FinalTestExecution,
    FrozenSubmission,
    ProfileBoundFinalJudge,
    final_test_profile_sha256,
    write_immutable_score_sidecar,
)


def _file_identity(path: Path) -> dict[str, str]:
    return {
        "path": str(path.resolve()),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _observed_authority(
    runtime: Path, command: str, timeout_s: int, evas_command: str
) -> dict[str, Any]:
    if not command or timeout_s <= 0:
        raise ValueError("bound final replay requires command and positive watchdog")
    evaluator = runtime / "evaluator"
    if (
        not evaluator.is_dir()
        or evaluator.is_symlink()
        or any(path.is_symlink() for path in evaluator.rglob("*"))
    ):
        raise ValueError("evaluator tree must exist without symlinks")
    identity = protocol.evas_identity(shlex.split(evas_command))
    if not identity.get("available") or not re.search(
        r"\bevas-sim\s+0\.8\.7\b", str(identity.get("version_output") or "")
    ):
        raise ValueError("bound final replay requires available evas-sim 0.8.7")
    command_files = []
    for index, token in enumerate(shlex.split(command)):
        # command_result executes in REPO, not the operator's working directory.
        resolved = shutil.which(token) if index == 0 and "/" not in token else None
        path = Path(resolved or token)
        if not path.is_absolute():
            path = REPO / path
        if path.is_file():
            command_files.append(_file_identity(path))
    runtime_identity = {
        "python": _file_identity(Path(sys.executable)),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "bridge_sources": [
            _file_identity(Path(__file__).parent / name)
            for name in (
                "final_replay.py",
                "run_campaign.py",
                "result_protocol.py",
            )
        ],
        "rust_core_override": (
            _file_identity(Path(os.environ["EVAS_RUST_CORE_LIB"]))
            if os.environ.get("EVAS_RUST_CORE_LIB")
            else None
        ),
    }
    return {
        "judge": {"engine": "evas", "version": "0.8.7"},
        "judge_identity_sha256": protocol.canonical_sha256(identity),
        "checker_identity_sha256": protocol.hash_test_tree(runtime / "evaluator")[
            "tree_sha256"
        ],
        "runtime_identity_sha256": protocol.canonical_sha256(runtime_identity),
        "command_signature_sha256": protocol.canonical_sha256(
            {
                "command": command,
                "command_files": command_files,
                "timeout_s": timeout_s,
                "evas_command": evas_command,
                "evas_profile": os.environ.get("VABENCH_EVAS_PROFILE", "r52").strip()
                or "r52",
            }
        ),
    }


def build_final_test_profile(
    *,
    runtime: Path,
    release: Path,
    campaign_config_sha256: str,
    command: str,
    timeout_s: int,
    evas_command: str,
) -> dict[str, Any]:
    """Freeze observed scoring authority; callers retain the campaign provenance."""
    manifest_path = release / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    if (
        manifest.get("release_revision") != "r53"
        or manifest.get("runtime_requirements", {}).get("evas_version") != "0.8.7"
    ):
        raise ValueError("bound final replay requires r53 + EVAS 0.8.7")
    profile = {
        "schema_version": "vaevas-final-test-profile-v1",
        "profile_id": "r53/evas-0.8.7-production-final",
        "benchmark_release": "benchmarkv4-r53",
        "benchmark_manifest_sha256": hashlib.sha256(
            manifest_path.read_bytes()
        ).hexdigest(),
        "campaign_config_sha256": campaign_config_sha256,
        **_observed_authority(runtime, command, timeout_s, evas_command),
        "authority_phase": "post_submission_freeze_only",
        "visibility": "trusted_only",
        "model_observation_allowed": False,
        "memory_entry_allowed": False,
        "candidate_selection_allowed": False,
        "repair_allowed": False,
        "input_scope": "frozen_submission_tree",
        "submission_binding_required": True,
        "score_sidecar_required": True,
        "structured_result_contract": {
            "schema_id": "vabench-trusted-replay-status-v1",
            "requires_structured_verdict": True,
        },
        "score_sidecar_contract": {
            "schema_id": "vaevas-score-sidecar-v1",
            "immutable": True,
            "binds_submission_tree": True,
            "score_authority": "development_only",
        },
        "spectre_policy": {
            "required": False,
            "trigger": "conditional_evas_or_external_protocol_change",
            "spectre_judge_identity_sha256": None,
            "spectre_command_signature_sha256": None,
            "spectre_report_schema_id": None,
        },
    }
    final_test_profile_sha256(profile)
    return profile


def _verify_submission(runtime: Path, manifest: dict[str, Any]) -> FrozenSubmission:
    if manifest.get("status") != "available" or manifest.get("immutable") is not True:
        raise ValueError("bound replay requires an immutable frozen submission")
    evidence = runtime / "evidence"
    root = evidence / "final_submission"
    if evidence.is_symlink() or root.is_symlink() or not root.is_dir():
        raise ValueError(
            "frozen submission must be a trusted directory without symlinks"
        )
    if any(path.is_symlink() for path in root.rglob("*")):
        raise ValueError("frozen submission must not contain symlinks")
    rows = manifest.get("artifacts") or []
    names = [row["path"] for row in rows]
    if not names or len(names) != len(set(names)):
        raise ValueError("frozen submission artifacts must be nonempty and unique")
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or path.as_posix() != name:
            raise ValueError("invalid frozen artifact path")
    observed = protocol.hash_test_tree(root)
    # Do not apply evaluator cache exclusions to candidate files.
    actual_names = sorted(
        p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
    )
    expected_rows = sorted(
        [{"path": row["path"], "sha256": row["sha256"]} for row in rows],
        key=lambda row: row["path"],
    )
    observed_rows = [
        {"path": row["path"], "sha256": row["sha256"]} for row in observed["files"]
    ]
    if (
        actual_names != sorted(names)
        or observed_rows != expected_rows
        or observed["tree_sha256"] != manifest.get("tree_sha256")
    ):
        raise ValueError("frozen submission identity drift")
    return FrozenSubmission(
        tree_sha256=manifest["tree_sha256"], artifacts=tuple(sorted(names))
    )


def execute_bound_replay(
    *,
    runtime: Path,
    command: str,
    timeout_s: int,
    evas_command: str,
    final_submission: dict[str, Any],
    final_test_profile: dict[str, Any],
    context: EpisodeContext,
    execute: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """Execute the existing production replay and publish its typed sidecar."""
    final_test_profile = deepcopy(final_test_profile)
    final_submission = deepcopy(final_submission)
    final_test_profile_sha256(final_test_profile)
    if final_test_profile["judge"] != {"engine": "evas", "version": "0.8.7"}:
        raise ValueError("bound final replay requires EVAS 0.8.7 authority")
    submission = _verify_submission(runtime, final_submission)

    def verify_authority() -> None:
        for field, observed in _observed_authority(
            runtime, command, timeout_s, evas_command
        ).items():
            if final_test_profile[field] != observed:
                raise ValueError(f"final authority identity drift: {field}")

    verify_authority()
    replay: dict[str, Any] = {}

    def invoke(frozen: FrozenSubmission, profile: dict[str, Any]) -> FinalTestExecution:
        replay.update(
            execute(runtime, command, timeout_s, evas_command, final_submission)
        )
        protocol.normalize_trusted_replay_watchdog(replay)
        _verify_submission(runtime, final_submission)
        verify_authority()
        if replay.get("submission_tree_sha256") != frozen.tree_sha256:
            raise ValueError("replay submission identity drift")
        if (
            protocol.canonical_sha256(replay["evas_identity"])
            != profile["judge_identity_sha256"]
        ):
            raise ValueError("replay judge identity drift")
        if replay["test_manifest"]["tree_sha256"] != profile["checker_identity_sha256"]:
            raise ValueError("replay checker identity drift")
        status = replay["status"]
        score = (
            1.0
            if status == "passed"
            else 0.0
            if status
            in {
                "compile_failure",
                "runtime_failure",
                "behavior_failure",
            }
            else None
        )
        judgment = FinalJudgment(status, "evas", score, frozen.tree_sha256)
        sidecar = {
            key: profile[key]
            for key in (
                "benchmark_release",
                "benchmark_manifest_sha256",
                "checker_identity_sha256",
                "runtime_identity_sha256",
                "campaign_config_sha256",
                "command_signature_sha256",
            )
        }
        sidecar.update(
            {
                "schema_version": "vaevas-score-sidecar-v1",
                "score_authority": "development_only",
                "immutable": True,
                "binds_submission_tree": True,
                "submission_tree_sha256": frozen.tree_sha256,
                "judge": {
                    **profile["judge"],
                    "identity_sha256": profile["judge_identity_sha256"],
                },
                "structured_result": {"status": status, "score": score},
                "model_observation_allowed": False,
                "memory_entry_allowed": False,
            }
        )
        return FinalTestExecution(judgment, sidecar)

    judge = ProfileBoundFinalJudge(
        context=context, final_test_profile=final_test_profile, execute=invoke
    )
    reservation = runtime / "evidence/bound-final-test"
    try:
        reservation.mkdir()
    except FileExistsError as exc:
        raise RuntimeError(
            "final replay already reserved; in-place retry is forbidden"
        ) from exc
    # A crash after reservation stays terminal. No automatic retry or repair is
    # authorized by this bridge, including when publication did not finish.
    request = {
        "profile": final_test_profile,
        "episode_id": context.episode_id,
        "attempt_id": context.attempt_id,
        "task_id": context.task_id,
        "submission_tree_sha256": submission.tree_sha256,
    }
    with (reservation / "request.json").open("x") as handle:
        json.dump(request, handle, sort_keys=True, allow_nan=False)
        handle.flush()
        os.fsync(handle.fileno())
    judgment = judge.judge(submission)
    receipt = write_immutable_score_sidecar(
        output_dir=runtime / "evidence",
        context=context,
        submission=submission,
        judgment=judgment,
        final_test_profile=final_test_profile,
        score_sidecar=judge.score_sidecar,
    )
    replay["final_test_profile"] = final_test_profile
    replay["score_sidecar_receipt"] = {
        **asdict(receipt),
        "path": receipt.path.relative_to(runtime).as_posix(),
        "episode_id": context.episode_id,
        "attempt_id": context.attempt_id,
        "task_id": context.task_id,
    }
    return replay
