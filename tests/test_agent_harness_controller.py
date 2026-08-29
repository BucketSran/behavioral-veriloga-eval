from __future__ import annotations

import pytest

from runners.agent_harness import (
    AgentAction,
    EpisodeContext,
    EpisodeController,
    EnvironmentStep,
    FinalJudgment,
    FrozenSubmission,
    Observation,
    PublicValidator,
    project_model_visible_events,
    JsonlTrajectoryRecorder,
    read_trajectory,
    validate_trajectory,
)


def test_action_and_observation_use_versioned_structured_protocol() -> None:
    action = AgentAction(
        action_id="action-001",
        tool_name="public_validate",
        arguments={"profile": "syntax"},
        source_backend="alphapollo-reasoning",
        candidate_tree_sha256="b" * 64,
    )
    observation = Observation(
        observation_id="observation-001",
        tool_name="public_validate",
        status="succeeded",
        payload={"message": "syntax ok", "errors": []},
        candidate_tree_sha256="b" * 64,
        truncated=False,
        budget_delta={"public_validation_calls": 1},
    )

    assert action.schema_version == "vaevas-action-v1"
    assert action.arguments_sha256 == (
        "b8b1bf12dcb79df7973a5f6b4af7732e446c5a1d80bce30780f8192ba56af043"
    )
    assert observation.schema_version == "vaevas-observation-v1"
    assert observation.payload_sha256 == (
        "a57a12793f9d2efdc00502b959443530d9ec329a2fb458381bf5c857fbfa3dc4"
    )
    with pytest.raises(TypeError):
        action.arguments["profile"] = "full"  # type: ignore[index]
    with pytest.raises(TypeError):
        observation.payload["message"] = "changed"  # type: ignore[index]


def test_frozen_submission_normalizes_artifacts_and_validates_tree_hash() -> None:
    mutable_artifacts = ["model.va"]
    submission = FrozenSubmission(
        tree_sha256="a" * 64,
        artifacts=mutable_artifacts,  # type: ignore[arg-type]
    )

    mutable_artifacts.append("late-change.va")

    assert submission.artifacts == ("model.va",)
    with pytest.raises(ValueError, match="tree_sha256"):
        FrozenSubmission(tree_sha256="not-a-hash", artifacts=("model.va",))
    with pytest.raises(ValueError, match="artifact"):
        FrozenSubmission(tree_sha256="a" * 64, artifacts=("",))


@pytest.mark.parametrize(
    "field_name",
    ["episode_id", "attempt_id", "task_id", "condition"],
)
def test_episode_context_requires_joinable_identity(field_name: str) -> None:
    values = {
        "episode_id": "episode-001",
        "attempt_id": "attempt-001",
        "task_id": "v4-001",
        "condition": "Agentic+EVAS",
    }
    values[field_name] = ""

    with pytest.raises(ValueError, match=field_name):
        EpisodeContext(max_steps=4, **values)


class PublicFeedbackPolicy:
    def __init__(self) -> None:
        self.seen: list[str] = []

    def act(self, observation: Observation) -> AgentAction:
        self.seen.append(str(observation.payload["message"]))
        if len(self.seen) == 1:
            return AgentAction(
                action_id="action-validate",
                tool_name="public_validate",
                arguments={},
                source_backend="fake-backend",
                candidate_tree_sha256="a" * 64,
            )
        return AgentAction(
            action_id="action-submit",
            tool_name="submit",
            arguments={},
            source_backend="fake-backend",
            candidate_tree_sha256="a" * 64,
        )


class FakePublicValidator:
    def __init__(self, boundary_log: list[str]) -> None:
        self.boundary_log = boundary_log

    def validate(
        self,
        *,
        candidate_tree_sha256: str,
        profile_id: str,
    ) -> Observation:
        self.boundary_log.append(
            f"public_validate:{profile_id}:{candidate_tree_sha256}"
        )
        return Observation(
            observation_id="observation-validation",
            tool_name="public_validate",
            status="succeeded",
            payload={"message": "public validation: syntax ok"},
            candidate_tree_sha256=candidate_tree_sha256,
            budget_delta={"public_validation_calls": 1},
        )


class PublicValidationEnvironment:
    def __init__(
        self,
        boundary_log: list[str],
        public_validator: PublicValidator,
    ) -> None:
        self.boundary_log = boundary_log
        self.public_validator = public_validator

    def start(self, context: EpisodeContext) -> Observation:
        self.boundary_log.append(f"start:{context.attempt_id}")
        return Observation(
            observation_id="observation-task",
            tool_name="task",
            status="ready",
            payload={"message": "implement the public task"},
        )

    def step(self, action: AgentAction) -> EnvironmentStep:
        self.boundary_log.append(f"step:{action.tool_name}")
        if action.tool_name == "public_validate":
            return EnvironmentStep(
                observation=self.public_validator.validate(
                    candidate_tree_sha256=action.candidate_tree_sha256 or "",
                    profile_id="public-default",
                ),
                done=False,
            )
        return EnvironmentStep(
            observation=Observation(
                observation_id="observation-submission",
                tool_name="submit",
                status="succeeded",
                payload={"message": "submission accepted"},
                candidate_tree_sha256="a" * 64,
            ),
            done=True,
            terminal_reason="submitted",
        )

    def freeze_submission(self) -> FrozenSubmission:
        self.boundary_log.append("freeze")
        return FrozenSubmission(tree_sha256="a" * 64, artifacts=("model.va",))

    def close(self) -> None:
        self.boundary_log.append("close")


class TerminalFinalJudge:
    def __init__(self, boundary_log: list[str]) -> None:
        self.boundary_log = boundary_log

    def judge(self, submission: FrozenSubmission) -> FinalJudgment:
        self.boundary_log.append("final_judge")
        return FinalJudgment(
            status="passed",
            judge_engine="evas",
            score=1.0,
            submission_tree_sha256=submission.tree_sha256,
        )


def test_public_feedback_can_continue_but_final_judgment_cannot() -> None:
    boundary_log: list[str] = []
    policy = PublicFeedbackPolicy()
    controller = EpisodeController(
        policy=policy,
        environment=PublicValidationEnvironment(
            boundary_log,
            FakePublicValidator(boundary_log),
        ),
        final_judge=TerminalFinalJudge(boundary_log),
    )

    result = controller.run(
        EpisodeContext(
            episode_id="episode-001",
            attempt_id="attempt-001",
            task_id="v4-001",
            condition="Agentic+EVAS",
            max_steps=4,
        )
    )

    assert policy.seen == [
        "implement the public task",
        "public validation: syntax ok",
    ]
    assert result.final_judgment is not None
    assert result.final_judgment.status == "passed"
    assert boundary_log == [
        "start:attempt-001",
        "step:public_validate",
        f"public_validate:public-default:{'a' * 64}",
        "step:submit",
        "freeze",
        "final_judge",
        "close",
    ]


def test_model_visible_trajectory_projection_excludes_final_judgment(
    tmp_path,
) -> None:
    trajectory_path = tmp_path / "visibility.jsonl"
    boundary_log: list[str] = []
    controller = EpisodeController(
        policy=PublicFeedbackPolicy(),
        environment=PublicValidationEnvironment(
            boundary_log,
            FakePublicValidator(boundary_log),
        ),
        final_judge=TerminalFinalJudge(boundary_log),
        trajectory=JsonlTrajectoryRecorder(trajectory_path),
    )

    controller.run(
        EpisodeContext(
            episode_id="episode-001",
            attempt_id="attempt-001",
            task_id="v4-001",
            condition="Agentic+EVAS",
            max_steps=4,
        )
    )

    events = read_trajectory(trajectory_path)
    model_visible = project_model_visible_events(events)
    assert any(
        event["payload"].get("observation_id") == "observation-validation"
        for event in model_visible
    )
    assert not any(
        event["event_type"] == "final_judgment_completed"
        for event in model_visible
    )
    final_event = next(
        event
        for event in events
        if event["event_type"] == "final_judgment_completed"
    )
    assert final_event["visibility"] == "trusted"


class SubmitPolicy:
    def act(self, observation: Observation) -> AgentAction:
        assert observation.payload["message"] == "implement the public task"
        return AgentAction(
            action_id="action-submit",
            tool_name="submit",
            arguments={},
            source_backend="fake-backend",
            candidate_tree_sha256="a" * 64,
        )


class PassingEnvironment:
    def __init__(self, boundary_log: list[str]) -> None:
        self.boundary_log = boundary_log

    def start(self, context: EpisodeContext) -> Observation:
        self.boundary_log.append(f"start:{context.attempt_id}")
        return Observation(
            observation_id="observation-task",
            tool_name="task",
            status="ready",
            payload={"message": "implement the public task"},
        )

    def step(self, action: AgentAction) -> EnvironmentStep:
        assert action.tool_name == "submit"
        self.boundary_log.append("step:submit")
        return EnvironmentStep(
            observation=Observation(
                observation_id="observation-submission",
                tool_name="submit",
                status="succeeded",
                payload={"message": "submission accepted"},
                candidate_tree_sha256="a" * 64,
            ),
            done=True,
            terminal_reason="submitted",
        )

    def freeze_submission(self) -> FrozenSubmission:
        self.boundary_log.append("freeze")
        return FrozenSubmission(
            tree_sha256="a" * 64,
            artifacts=("model.va",),
        )

    def close(self) -> None:
        self.boundary_log.append("close")


class PassingFinalJudge:
    def __init__(self, boundary_log: list[str]) -> None:
        self.boundary_log = boundary_log

    def judge(self, submission: FrozenSubmission) -> FinalJudgment:
        assert submission.tree_sha256 == "a" * 64
        self.boundary_log.append("final_judge")
        return FinalJudgment(
            status="passed",
            judge_engine="evas",
            score=1.0,
            submission_tree_sha256=submission.tree_sha256,
        )


class CleanupFailingEnvironment(PassingEnvironment):
    def close(self) -> None:
        self.boundary_log.append("close")
        raise RuntimeError("docker rm failed")


class MismatchedFinalJudge:
    def judge(self, submission: FrozenSubmission) -> FinalJudgment:
        return FinalJudgment(
            status="passed",
            judge_engine="evas",
            score=1.0,
            submission_tree_sha256="b" * 64,
        )


def test_final_judgment_must_bind_the_frozen_submission_hash() -> None:
    controller = EpisodeController(
        policy=SubmitPolicy(),
        environment=PassingEnvironment([]),
        final_judge=MismatchedFinalJudge(),
    )

    result = controller.run(
        EpisodeContext(
            episode_id="episode-001",
            attempt_id="attempt-001",
            task_id="v4-001",
            condition="Agentic+EVAS",
            max_steps=4,
        )
    )

    assert result.primary_outcome == "protocol_failure"
    assert result.submission is not None
    assert result.submission.tree_sha256 == "a" * 64
    assert result.final_judgment is None
    assert result.failure is not None
    assert result.failure.category == "final_judgment_submission_mismatch"
    assert result.failure.phase == "final_judge"


class InvalidTerminalEnvironment(PassingEnvironment):
    def step(self, action: AgentAction) -> EnvironmentStep:
        self.boundary_log.append("step:invalid-terminal")
        return EnvironmentStep(
            observation=Observation(
                observation_id="observation-invalid-terminal",
                tool_name="submit",
                status="rejected",
                payload={"message": "unsupported terminal state"},
                candidate_tree_sha256="a" * 64,
            ),
            done=True,
            terminal_reason="unexpected_terminal",
        )


class StartFailingEnvironment(PassingEnvironment):
    def start(self, context: EpisodeContext) -> Observation:
        self.boundary_log.append(f"start:{context.attempt_id}")
        raise RuntimeError("sandbox failed to start")


class NeverTerminalEnvironment(PassingEnvironment):
    def step(self, action: AgentAction) -> EnvironmentStep:
        self.boundary_log.append("step:continue")
        return EnvironmentStep(
            observation=Observation(
                observation_id=f"observation-{len(self.boundary_log)}",
                tool_name="shell",
                status="succeeded",
                payload={"message": "continue working"},
                candidate_tree_sha256="a" * 64,
            ),
            done=False,
        )


def test_step_budget_exhaustion_is_a_terminal_result() -> None:
    controller = EpisodeController(
        policy=SubmitPolicy(),
        environment=NeverTerminalEnvironment([]),
        final_judge=PassingFinalJudge([]),
    )

    result = controller.run(
        EpisodeContext(
            episode_id="episode-001",
            attempt_id="attempt-001",
            task_id="v4-001",
            condition="Agentic+EVAS",
            max_steps=1,
        )
    )

    assert result.primary_outcome == "budget_exhausted"
    assert result.terminal_reason == "max_steps_exhausted"
    assert result.failure is not None
    assert result.failure.category == "step_budget_exhausted"
    assert result.failure.phase == "controller_budget"
    assert result.submission is None
    assert result.final_judgment is None


def test_environment_failure_is_materialized_separately_from_cleanup() -> None:
    boundary_log: list[str] = []
    controller = EpisodeController(
        policy=SubmitPolicy(),
        environment=StartFailingEnvironment(boundary_log),
        final_judge=PassingFinalJudge(boundary_log),
    )

    result = controller.run(
        EpisodeContext(
            episode_id="episode-001",
            attempt_id="attempt-001",
            task_id="v4-001",
            condition="Agentic+EVAS",
            max_steps=4,
        )
    )

    assert result.primary_outcome == "infrastructure_failure"
    assert result.terminal_reason == "infrastructure_failure"
    assert result.failure is not None
    assert result.failure.category == "environment_failure"
    assert result.failure.phase == "environment_start"
    assert result.failure.message == "sandbox failed to start"
    assert result.incidents == ()
    assert boundary_log == ["start:attempt-001", "close"]


def test_start_failure_still_has_a_complete_attempt_trajectory(tmp_path) -> None:
    trajectory_path = tmp_path / "start-failure.jsonl"
    controller = EpisodeController(
        policy=SubmitPolicy(),
        environment=StartFailingEnvironment([]),
        final_judge=PassingFinalJudge([]),
        trajectory=JsonlTrajectoryRecorder(trajectory_path),
    )

    result = controller.run(
        EpisodeContext(
            episode_id="episode-001",
            attempt_id="attempt-001",
            task_id="v4-001",
            condition="Agentic+EVAS",
            max_steps=4,
        )
    )

    events = read_trajectory(trajectory_path)
    assert validate_trajectory(events) is True
    assert [event["event_type"] for event in events] == [
        "episode_started",
        "episode_failed",
        "cleanup_completed",
        "episode_completed",
    ]
    assert result.trajectory_tail_sha256 == events[-1]["event_sha256"]


def test_trajectory_rejects_unknown_visibility(tmp_path) -> None:
    recorder = JsonlTrajectoryRecorder(tmp_path / "invalid-visibility.jsonl")
    context = EpisodeContext(
        episode_id="episode-001",
        attempt_id="attempt-001",
        task_id="v4-001",
        condition="Agentic+EVAS",
        max_steps=4,
    )

    with pytest.raises(ValueError, match="visibility"):
        recorder.append(
            context=context,
            actor="controller",
            event_type="episode_started",
            visibility="models",  # type: ignore[arg-type]
            payload={},
        )


def test_protocol_failure_is_materialized_in_the_episode_result() -> None:
    controller = EpisodeController(
        policy=SubmitPolicy(),
        environment=InvalidTerminalEnvironment([]),
        final_judge=PassingFinalJudge([]),
    )

    result = controller.run(
        EpisodeContext(
            episode_id="episode-001",
            attempt_id="attempt-001",
            task_id="v4-001",
            condition="Agentic+EVAS",
            max_steps=4,
        )
    )

    assert result.primary_outcome == "protocol_failure"
    assert result.terminal_reason == "protocol_failure"
    assert result.submission is None
    assert result.final_judgment is None
    assert result.failure is not None
    assert result.failure.category == "invalid_terminal_reason"
    assert result.failure.phase == "environment_step"
    assert result.failure.message == "unsupported terminal reason: unexpected_terminal"


def test_controller_freezes_submission_before_verification() -> None:
    boundary_log: list[str] = []
    controller = EpisodeController(
        policy=SubmitPolicy(),
        environment=PassingEnvironment(boundary_log),
        final_judge=PassingFinalJudge(boundary_log),
    )

    result = controller.run(
        EpisodeContext(
            episode_id="episode-001",
            attempt_id="attempt-001",
            task_id="v4-001",
            condition="Agentic+EVAS",
            max_steps=4,
        )
    )

    assert result.primary_outcome == "passed"
    assert result.terminal_reason == "submitted"
    assert result.submission is not None
    assert result.submission.tree_sha256 == "a" * 64
    assert result.final_judgment is not None
    assert result.final_judgment.judge_engine == "evas"
    assert result.incidents == ()
    assert boundary_log == [
        "start:attempt-001",
        "step:submit",
        "freeze",
        "final_judge",
        "close",
    ]


def test_cleanup_failure_is_an_incident_not_the_primary_outcome() -> None:
    boundary_log: list[str] = []
    controller = EpisodeController(
        policy=SubmitPolicy(),
        environment=CleanupFailingEnvironment(boundary_log),
        final_judge=PassingFinalJudge(boundary_log),
    )

    result = controller.run(
        EpisodeContext(
            episode_id="episode-001",
            attempt_id="attempt-001",
            task_id="v4-001",
            condition="Agentic+EVAS",
            max_steps=4,
        )
    )

    assert result.primary_outcome == "passed"
    assert [(row.category, row.message) for row in result.incidents] == [
        ("sandbox_cleanup_failure", "docker rm failed")
    ]
    assert boundary_log[-2:] == ["final_judge", "close"]


def test_controller_writes_attempt_scoped_tamper_evident_trajectory(
    tmp_path,
) -> None:
    boundary_log: list[str] = []
    trajectory_path = tmp_path / "trajectory.jsonl"
    controller = EpisodeController(
        policy=SubmitPolicy(),
        environment=PassingEnvironment(boundary_log),
        final_judge=PassingFinalJudge(boundary_log),
        trajectory=JsonlTrajectoryRecorder(trajectory_path),
    )

    result = controller.run(
        EpisodeContext(
            episode_id="episode-001",
            attempt_id="attempt-002",
            task_id="v4-001",
            condition="Agentic+EVAS",
            max_steps=4,
        )
    )

    events = read_trajectory(trajectory_path)
    assert validate_trajectory(events) is True
    assert [row["sequence"] for row in events] == list(range(len(events)))
    assert {row["attempt_id"] for row in events} == {"attempt-002"}
    assert [row["event_type"] for row in events] == [
        "episode_started",
        "action_proposed",
        "environment_observed",
        "submission_frozen",
        "final_judgment_completed",
        "cleanup_completed",
        "episode_completed",
    ]
    assert events[0]["prev_event_sha256"] is None
    action_payload = events[1]["payload"]
    assert action_payload["schema_version"] == "vaevas-action-v1"
    assert action_payload["action_id"] == "action-submit"
    assert action_payload["tool_name"] == "submit"
    assert action_payload["source_backend"] == "fake-backend"
    assert action_payload["candidate_tree_sha256"] == "a" * 64
    observation_payload = events[2]["payload"]
    assert observation_payload["schema_version"] == "vaevas-observation-v1"
    assert observation_payload["observation_id"] == "observation-submission"
    assert observation_payload["tool_name"] == "submit"
    assert observation_payload["status"] == "succeeded"
    assert observation_payload["candidate_tree_sha256"] == "a" * 64
    assert all(
        current["prev_event_sha256"] == previous["event_sha256"]
        for previous, current in zip(events, events[1:])
    )
    assert result.trajectory_tail_sha256 == events[-1]["event_sha256"]


def test_retry_creates_a_linked_attempt_without_reusing_identity(tmp_path) -> None:
    original = EpisodeContext(
        episode_id="episode-001",
        attempt_id="attempt-001",
        task_id="v4-001",
        condition="Agentic+EVAS",
        max_steps=4,
    )
    retry = original.next_attempt(
        attempt_id="attempt-002",
        reason="provider_transport_failure",
    )
    controller = EpisodeController(
        policy=SubmitPolicy(),
        environment=PassingEnvironment([]),
        final_judge=PassingFinalJudge([]),
        trajectory=JsonlTrajectoryRecorder(tmp_path / "attempt-002.jsonl"),
    )

    result = controller.run(retry)

    assert result.context.attempt_id == "attempt-002"
    assert result.context.parent_attempt_id == "attempt-001"
    assert result.context.retry_index == 1
    assert result.context.retry_reason == "provider_transport_failure"
    first_event = read_trajectory(tmp_path / "attempt-002.jsonl")[0]
    assert first_event["payload"]["attempt_lineage"] == {
        "parent_attempt_id": "attempt-001",
        "retry_index": 1,
        "retry_reason": "provider_transport_failure",
    }
