from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from runners.agent_harness.controller import EpisodeController
from runners.agent_harness.state import (
    AgentAction,
    CandidateEpisodeResult,
    CandidateSnapshot,
    EnvironmentStep,
    EpisodeContext,
    FinalJudgment,
    FrozenSubmission,
    Observation,
)
from runners.agent_harness.tool_registry import ToolCapability, ToolRegistry
from runners.agent_harness.trajectory import (
    JsonlTrajectoryRecorder,
    read_trajectory,
    validate_candidate_trajectory_semantics,
    validate_trajectory_semantics,
)


SHA_A = "a" * 64
SHA_B = "b" * 64


class SubmitPolicy:
    def __init__(self) -> None:
        self.calls = 0

    def act(self, observation: Observation) -> AgentAction:
        self.calls += 1
        return AgentAction(
            action_id=f"action-{self.calls:04d}",
            tool_name="submit",
            arguments={},
            source_backend="candidate-test",
            candidate_tree_sha256=observation.candidate_tree_sha256,
        )


class SubmitEnvironment:
    def __init__(self, log: list[str], *, tree_sha256: str = SHA_A) -> None:
        self.log = log
        self.tree_sha256 = tree_sha256

    def start(self, context: EpisodeContext) -> Observation:
        self.log.append(f"start:{context.attempt_id}")
        return Observation(
            observation_id="observation-start",
            tool_name="task",
            status="ready",
            payload={"message": "write model.va"},
            candidate_tree_sha256=self.tree_sha256,
        )

    def step(
        self,
        action: AgentAction,
        _capability: ToolCapability,
    ) -> EnvironmentStep:
        self.log.append(f"step:{action.tool_name}")
        return EnvironmentStep(
            observation=Observation(
                observation_id="observation-submit",
                tool_name="submit",
                status="succeeded",
                payload={"message": "candidate submitted"},
                candidate_tree_sha256=self.tree_sha256,
            ),
            done=True,
            terminal_reason="submitted",
        )

    def freeze_submission(self) -> FrozenSubmission:
        raise AssertionError("candidate-only episodes must not use final freeze")

    def close(self) -> None:
        self.log.append("close")


class MutateOnceEnvironment(SubmitEnvironment):
    def step(
        self,
        action: AgentAction,
        _capability: ToolCapability,
    ) -> EnvironmentStep:
        self.log.append(f"step:{action.tool_name}")
        return EnvironmentStep(
            observation=Observation(
                observation_id="observation-mutated",
                tool_name="edit",
                status="succeeded",
                payload={"message": "candidate changed"},
                candidate_tree_sha256=self.tree_sha256,
            ),
            done=False,
        )


class FinalJudgeMustNotRun:
    def judge(self, submission: FrozenSubmission) -> FinalJudgment:
        raise AssertionError("candidate-only episodes must not invoke final judge")


class RecordingCandidateTerminal:
    def __init__(self, log: list[str]) -> None:
        self.log = log
        self.snapshots: list[CandidateSnapshot] = []

    def capture_candidate(
        self,
        *,
        context: EpisodeContext,
        expected_candidate_tree_sha256: str,
        terminal_reason: str,
    ) -> CandidateSnapshot:
        self.log.append("capture_candidate")
        assert context.attempt_id == "attempt"
        assert terminal_reason in {"submitted", "agent_timeout"}
        return CandidateSnapshot(
            tree_sha256=expected_candidate_tree_sha256,
            artifacts=("model.va",),
        )

    def complete(
        self,
        *,
        context: EpisodeContext,
        candidate_snapshot: CandidateSnapshot,
        terminal_reason: str,
    ) -> CandidateEpisodeResult:
        self.log.append("candidate_terminal")
        self.snapshots.append(candidate_snapshot)
        return CandidateEpisodeResult(
            context=context,
            terminal_reason=terminal_reason,
            candidate_snapshot=candidate_snapshot,
            incidents=(),
        )


class MismatchingCandidateTerminal(RecordingCandidateTerminal):
    def complete(
        self,
        *,
        context: EpisodeContext,
        candidate_snapshot: CandidateSnapshot,
        terminal_reason: str,
    ) -> CandidateEpisodeResult:
        return replace(
            super().complete(
                context=context,
                candidate_snapshot=candidate_snapshot,
                terminal_reason=terminal_reason,
            ),
            candidate_snapshot=CandidateSnapshot(
                tree_sha256=SHA_B,
                artifacts=candidate_snapshot.artifacts,
            ),
        )


class EditPolicy:
    def act(self, observation: Observation) -> AgentAction:
        return AgentAction(
            action_id="action-edit",
            tool_name="edit",
            arguments={},
            source_backend="candidate-test",
            candidate_tree_sha256=observation.candidate_tree_sha256,
        )


def test_candidate_episode_snapshots_submission_without_final_judgment(
    tmp_path: Path,
) -> None:
    log: list[str] = []
    terminal = RecordingCandidateTerminal(log)
    trajectory_path = tmp_path / "candidate.jsonl"

    result = EpisodeController(
        policy=SubmitPolicy(),
        environment=SubmitEnvironment(log),
        candidate_terminal_handler=terminal,
        tool_registry=_controller_registry("submit"),
        trajectory=JsonlTrajectoryRecorder(trajectory_path),
    ).run(EpisodeContext("cell", "attempt", "v4-001", "Evolution+EVAS", 2))

    assert isinstance(result, CandidateEpisodeResult)
    assert result.candidate_snapshot.tree_sha256 == SHA_A
    assert result.candidate_snapshot.artifacts == ("model.va",)
    assert terminal.snapshots == [result.candidate_snapshot]
    assert log == [
        "start:attempt",
        "step:submit",
        "capture_candidate",
        "candidate_terminal",
        "close",
    ]
    assert not hasattr(result, "final_judgment")
    events = read_trajectory(trajectory_path)
    assert validate_candidate_trajectory_semantics(events)
    assert not validate_trajectory_semantics(events)
    assert "candidate_snapshot_frozen" in [event["event_type"] for event in events]
    assert "submission_frozen" not in [event["event_type"] for event in events]
    assert "final_judgment_completed" not in [
        event["event_type"] for event in events
    ]


def test_candidate_terminal_is_explicit_and_mutually_exclusive() -> None:
    log: list[str] = []
    with pytest.raises(ValueError, match="exactly one"):
        EpisodeController(
            policy=SubmitPolicy(),
            environment=SubmitEnvironment(log),
            final_judge=FinalJudgeMustNotRun(),
            candidate_terminal_handler=RecordingCandidateTerminal(log),
            tool_registry=_controller_registry("submit"),
        )

    with pytest.raises(ValueError, match="exactly one"):
        EpisodeController(
            policy=SubmitPolicy(),
            environment=SubmitEnvironment(log),
            tool_registry=_controller_registry("submit"),
        )


def test_candidate_terminal_result_must_match_snapshot(tmp_path: Path) -> None:
    log: list[str] = []
    trajectory_path = tmp_path / "mismatch.jsonl"

    result = EpisodeController(
        policy=SubmitPolicy(),
        environment=SubmitEnvironment(log),
        candidate_terminal_handler=MismatchingCandidateTerminal(log),
        tool_registry=_controller_registry("submit"),
        trajectory=JsonlTrajectoryRecorder(trajectory_path),
    ).run(EpisodeContext("cell", "attempt", "v4-001", "Evolution+EVAS", 2))

    assert result.failure is not None
    assert result.failure.category == "candidate_terminal_mismatch"
    assert "candidate_terminal" in log
    events = read_trajectory(trajectory_path)
    assert validate_candidate_trajectory_semantics(events)
    assert not any(
        event["event_type"] == "final_judgment_completed" for event in events
    )


def test_candidate_deadline_uses_same_loop_without_model_reentry(
    tmp_path: Path,
) -> None:
    log: list[str] = []
    policy = SubmitPolicy()
    trajectory_path = tmp_path / "deadline.jsonl"

    result = EpisodeController(
        policy=policy,
        environment=SubmitEnvironment(log),
        candidate_terminal_handler=RecordingCandidateTerminal(log),
        tool_registry=_controller_registry("submit"),
        trajectory=JsonlTrajectoryRecorder(trajectory_path),
        deadline_monotonic=0.0,
        deadline_finalizer=lambda: SHA_A,
    ).run(EpisodeContext("cell", "attempt", "v4-001", "Evolution+EVAS", None))

    assert isinstance(result, CandidateEpisodeResult)
    assert result.terminal_reason == "agent_timeout"
    assert policy.calls == 0
    assert log == ["start:attempt", "capture_candidate", "candidate_terminal", "close"]
    assert validate_candidate_trajectory_semantics(read_trajectory(trajectory_path))


def test_candidate_mode_failure_preserves_budget_events(tmp_path: Path) -> None:
    log: list[str] = []
    trajectory_path = tmp_path / "budget.jsonl"

    result = EpisodeController(
        policy=EditPolicy(),
        environment=MutateOnceEnvironment(log),
        candidate_terminal_handler=RecordingCandidateTerminal(log),
        tool_registry=_controller_registry("edit"),
        trajectory=JsonlTrajectoryRecorder(trajectory_path),
    ).run(EpisodeContext("cell", "attempt", "v4-001", "Evolution+EVAS", 1))

    assert result.failure is not None
    assert result.terminal_reason == "max_steps_exhausted"
    events = read_trajectory(trajectory_path)
    assert any(event["event_type"] == "budget_updated" for event in events)
    assert validate_candidate_trajectory_semantics(events)


def test_candidate_trajectory_rejects_any_trusted_visibility_event(
    tmp_path: Path,
) -> None:
    context = EpisodeContext("cell", "attempt", "v4-001", "Evolution+EVAS", 1)
    recorder = JsonlTrajectoryRecorder(tmp_path / "trusted.jsonl")

    recorder.append(
        context=context,
        actor="controller",
        event_type="episode_started",
        visibility="harness",
        payload={
            "max_steps": 1,
            "budget_limits": {},
            "public_validation_profile_sha256": None,
            "effective_capability_sha256": SHA_A,
            "attempt_lineage": {
                "parent_attempt_id": None,
                "retry_index": 0,
                "retry_reason": None,
            },
        },
    )
    recorder.append(
        context=context,
        actor="trusted_probe",
        event_type="unknown_trusted_event",
        visibility="trusted",
        payload={"payload_sha256": SHA_B},
    )
    recorder.append(
        context=context,
        actor="candidate_terminal",
        event_type="candidate_snapshot_frozen",
        visibility="harness",
        payload={
            "tree_sha256": SHA_A,
            "artifacts": ["model.va"],
            "terminal_reason": "submitted",
        },
    )
    recorder.append(
        context=context,
        actor="environment",
        event_type="cleanup_completed",
        visibility="harness",
        payload={},
    )
    recorder.append(
        context=context,
        actor="controller",
        event_type="episode_completed",
        visibility="harness",
        payload={
            "terminal_reason": "submitted",
            "terminal_kind": "candidate_snapshot",
            "incidents": [],
        },
    )

    assert not validate_candidate_trajectory_semantics(
        read_trajectory(tmp_path / "trusted.jsonl")
    )


def _controller_registry(*tool_names: str) -> ToolRegistry:
    descriptors = []
    for tool_name in tool_names:
        is_submit = tool_name == "submit"
        descriptors.append(
            {
                "schema_version": "vaevas-tool-descriptor-v1",
                "tool_id": f"core/{tool_name}-v1",
                "tool_name": tool_name,
                "tool_version": "1",
                "lifecycle": "active",
                "model_visibility": "model_visible",
                "allowed_conditions": ["Evolution+EVAS"],
                "budget_class": "submission" if is_submit else "tool_call",
                "state_effect": (
                    "terminal_submission" if is_submit else "candidate_mutation"
                ),
                "candidate_effect": "freeze" if is_submit else "mutate",
                "argument_schema": {
                    "type": "object",
                    "additionalProperties": True,
                },
                "observation_schema": {
                    "type": "object",
                    "additionalProperties": True,
                },
                "evidence_policy": {
                    "records_private_evidence": True,
                    "may_enter_model_observation": True,
                    "may_enter_shared_memory": False,
                    "requires_candidate_binding": False,
                },
                "handler_id": f"tool.{tool_name}",
            }
        )
    return ToolRegistry(descriptors)
