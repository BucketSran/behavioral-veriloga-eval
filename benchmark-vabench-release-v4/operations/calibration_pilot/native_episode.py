"""Opt-in, trusted composition of native episodes and production final replay.

No backend or model tool is installed here. The coordinator supplies the public
policy/environment, frozen authority, and an exclusively owned fresh runtime.
Only the coordinator receives this module's terminal outputs; they are never
observations or evolution memory. Legacy campaign defaults are unchanged.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any
from collections.abc import Callable

import run_campaign as runner

from runners.agent_harness import (
    EpisodeContext,
    EpisodeController,
    EpisodeResult,
    FinalJudgment,
    FrozenSubmission,
    JsonlTrajectoryRecorder,
    ToolRegistry,
    build_scored_result_artifact,
    final_test_profile_sha256,
    profile_input_identity_sha256,
    public_validation_profile_sha256,
    read_trajectory,
    validate_score_sidecar_authority,
)
from runners.agent_harness.contracts import Environment, Policy
from runners.agent_harness.result_store import write_immutable_scored_result


@dataclass(frozen=True)
class NativeEpisodeRun:
    result: EpisodeResult
    trajectory_path: Path
    artifact_path: Path | None
    score_sidecar_receipt: dict[str, Any] | None


class _ProductionFinalJudge:
    def __init__(self, *, runtime, context, profile, command, timeout_s, evas_command):
        self.runtime = runtime
        self.context = context
        self.profile = profile
        self.command = command
        self.timeout_s = timeout_s
        self.evas_command = evas_command
        self.sidecar = None
        self.receipt = None

    def judge(self, submission: FrozenSubmission) -> FinalJudgment:
        # Translate the controller-owned freeze, never refreeze the live candidate.
        observed = runner.RESULT_PROTOCOL.hash_test_tree(
            self.runtime / "evidence/final_submission"
        )
        if (
            observed["tree_sha256"] != submission.tree_sha256
            or tuple(row["path"] for row in observed["files"]) != submission.artifacts
        ):
            raise ValueError("controller frozen submission identity mismatch")
        manifest = {
            "status": "available",
            "immutable": True,
            "tree_sha256": submission.tree_sha256,
            "artifacts": observed["files"],
        }
        replay = runner.run_trusted_replay(
            self.runtime,
            self.command,
            self.timeout_s,
            self.evas_command,
            manifest,
            final_test_profile=self.profile,
            episode_context=self.context,
        )
        receipt = replay["score_sidecar_receipt"]
        digest = receipt["sha256"]
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("invalid sidecar receipt digest")
        expected = {
            "path": f"evidence/score-sidecars/{digest}.json",
            "episode_id": self.context.episode_id,
            "attempt_id": self.context.attempt_id,
            "task_id": self.context.task_id,
            "submission_tree_sha256": submission.tree_sha256,
            "final_profile_sha256": final_test_profile_sha256(self.profile),
            "final_profile_input_identity_sha256": profile_input_identity_sha256(
                profile_sha256=final_test_profile_sha256(self.profile),
                input_kind="frozen_submission_tree",
                input_sha256=submission.tree_sha256,
                attempt_id=self.context.attempt_id,
                task_id=self.context.task_id,
            ),
        }
        if any(receipt.get(key) != value for key, value in expected.items()):
            raise ValueError("sidecar receipt identity mismatch")
        path = self.runtime / expected["path"]
        if any(part.is_symlink() for part in (path, path.parent, path.parent.parent)):
            raise ValueError("sidecar receipt must not reference a symlink")
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError("sidecar receipt content mismatch")
        sidecar = json.loads(payload)
        structured = sidecar["structured_result"]
        judgment = FinalJudgment(
            structured["status"],
            sidecar["judge"]["engine"],
            structured["score"],
            submission.tree_sha256,
        )
        validate_score_sidecar_authority(
            score_sidecar=sidecar,
            final_test_profile=self.profile,
            judgment=judgment,
            submission=submission,
        )
        self.sidecar, self.receipt = sidecar, deepcopy(receipt)
        return judgment


def run_native_episode(
    *,
    runtime: Path,
    context: EpisodeContext,
    policy: Policy,
    environment: Environment,
    tool_registry: ToolRegistry,
    backend_profile_sha256: str,
    public_validation_profile: dict[str, Any],
    final_test_profile: dict[str, Any],
    command: str,
    timeout_s: int,
    evas_command: str,
    deadline_monotonic: float | None = None,
    deadline_finalizer: Callable[[], str | None] | None = None,
) -> NativeEpisodeRun:
    """Run once, then publish a scored join only if terminal evidence validates.

    Preflight rejection leaves environment ownership with the caller. Once the
    controller starts, it owns normal cleanup. A crash or publication failure
    leaves the runtime reserved; neither generation nor scoring is retried.
    """
    if runtime.is_symlink():
        raise ValueError("native runtime must not be a symlink")
    # The legacy judge executor changes cwd to REPO; never pass relative input
    # or output paths into that process environment.
    runtime = runtime.resolve()
    public_profile = deepcopy(public_validation_profile)
    final_profile = deepcopy(final_test_profile)
    public_sha = public_validation_profile_sha256(public_profile)
    final_sha = final_test_profile_sha256(final_profile)
    if not isinstance(backend_profile_sha256, str) or not re.fullmatch(
        r"[0-9a-f]{64}", backend_profile_sha256
    ):
        raise ValueError("backend_profile_sha256 must be a lowercase SHA-256")
    for field in (
        "benchmark_release",
        "benchmark_manifest_sha256",
        "campaign_config_sha256",
    ):
        if public_profile[field] != final_profile[field]:
            raise ValueError(f"public/final authority mismatch: {field}")
    if (
        public_profile["benchmark_release"] != "benchmarkv4-r53"
        or public_profile["evaluator"] != {"engine": "evas", "version": "0.8.7"}
        or final_profile["judge"] != {"engine": "evas", "version": "0.8.7"}
    ):
        raise ValueError("native production join requires r53 + EVAS 0.8.7")
    toolset = tool_registry.resolve(condition_id=context.condition, model_visible=True)
    runner.assert_final_replay_not_started(runtime)
    evidence = runtime / "evidence"
    if runtime.is_symlink() or evidence.is_symlink():
        raise ValueError("native evidence must not use a symlink")
    directory = evidence / "native-episode"
    if directory.exists() or directory.is_symlink():
        raise RuntimeError("native episode already reserved; in-place retry forbidden")
    for name in (
        "final_submission",
        "campaign_result.json",
        "conversation_checkpoint.json",
        "mini_swe_trajectory.json",
        "trusted_replay_result.json",
        "score-sidecars",
    ):
        marker = evidence / name
        if marker.exists() or marker.is_symlink():
            raise RuntimeError(f"native episode requires a fresh runtime: {name}")
    evidence.mkdir(parents=True, exist_ok=True)
    try:
        directory.mkdir()
    except FileExistsError as exc:
        raise RuntimeError(
            "native episode already reserved; in-place retry forbidden"
        ) from exc
    _write_once(
        directory / "request.json",
        {
            "schema_version": "vaevas-native-episode-request-v1",
            "episode_id": context.episode_id,
            "attempt_id": context.attempt_id,
            "task_id": context.task_id,
            "condition": context.condition,
            "max_steps": context.max_steps,
            "deadline_monotonic": deadline_monotonic,
            "budget_limits": dict(context.budget_limits),
            "parent_attempt_id": context.parent_attempt_id,
            "retry_index": context.retry_index,
            "retry_reason": context.retry_reason,
            "backend_profile_sha256": backend_profile_sha256,
            "registry_sha256": tool_registry.registry_sha256,
            "effective_capability_sha256": toolset.effective_capability_sha256,
            "public_validation_profile": public_profile,
            "final_test_profile": final_profile,
            "public_validation_profile_sha256": public_sha,
            "final_test_profile_sha256": final_sha,
        },
    )
    judge = _ProductionFinalJudge(
        runtime=runtime,
        context=context,
        profile=final_profile,
        command=command,
        timeout_s=timeout_s,
        evas_command=evas_command,
    )
    trajectory_path = directory / "trajectory.jsonl"
    result = EpisodeController(
        policy=policy,
        environment=environment,
        final_judge=judge,
        tool_registry=tool_registry,
        trajectory=JsonlTrajectoryRecorder(trajectory_path),
        public_validation_profile_sha256=public_sha,
        deadline_monotonic=deadline_monotonic,
        deadline_finalizer=deadline_finalizer,
    ).run(context)
    with trajectory_path.open("rb") as handle:
        os.fsync(handle.fileno())
    trajectory_path.chmod(0o444)
    _write_once(
        directory / "outcome.json",
        {
            "primary_outcome": result.primary_outcome,
            "terminal_reason": result.terminal_reason,
            "failure": asdict(result.failure) if result.failure else None,
            "incidents": [asdict(incident) for incident in result.incidents],
            "trajectory_tail_sha256": result.trajectory_tail_sha256,
        },
    )
    artifact_path = None
    if result.failure is None and result.final_judgment is not None:
        events = read_trajectory(trajectory_path)
        joins = dict(
            trajectory_events=events,
            score_sidecar=judge.sidecar,
            public_validation_profile=public_profile,
            final_test_profile=final_profile,
        )
        artifact = build_scored_result_artifact(
            result=result,
            backend_profile_sha256=backend_profile_sha256,
            registry_sha256=tool_registry.registry_sha256,
            effective_capability_sha256=toolset.effective_capability_sha256,
            **joins,
        )
        artifact_path = write_immutable_scored_result(
            output_dir=directory,
            artifact=artifact,
            **joins,
        )
    return NativeEpisodeRun(result, trajectory_path, artifact_path, judge.receipt)


def _write_once(path: Path, document: dict[str, Any]) -> None:
    # Reservation/request/outcome files are journals, not atomic scored records.
    with path.open("x", encoding="utf-8") as handle:
        json.dump(document, handle, sort_keys=True, ensure_ascii=False, allow_nan=False)
        handle.flush()
        os.fsync(handle.fileno())
        os.fchmod(handle.fileno(), 0o444)
