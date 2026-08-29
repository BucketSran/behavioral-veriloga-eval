from __future__ import annotations

import pytest

from runners.agent_harness import (
    AgentAction,
    EnvironmentStep,
    EpisodeContext,
    EpisodeController,
    FinalJudgment,
    FrozenSubmission,
    Observation,
    ToolCapability,
    ToolRegistry,
    ToolRegistryError,
)

SHA_A = "a" * 64
PUBLIC_PROFILE_SHA256 = "b" * 64


def _descriptor(*, valid_public_evidence: bool = True) -> dict:
    return {
        "schema_version": "vaevas-tool-descriptor-v1",
        "tool_id": "public/evas-validation-v1",
        "tool_name": "public_validate",
        "tool_version": "1",
        "lifecycle": "active",
        "model_visibility": "model_visible",
        "allowed_conditions": ["Agentic+EVAS"],
        "budget_class": "public_validation",
        "state_effect": "read_only",
        "candidate_effect": "read",
        "argument_schema": {"type": "object"},
        "observation_schema": {"type": "object"},
        "evidence_policy": {
            "records_private_evidence": not valid_public_evidence,
            "may_enter_model_observation": True,
            "may_enter_shared_memory": True,
            "requires_candidate_binding": valid_public_evidence,
        },
        "handler_id": "public.run_evas",
    }


class PublicValidationPolicy:
    def __init__(self) -> None:
        self.seen_messages: list[str] = []

    def act(self, observation: Observation) -> AgentAction:
        self.seen_messages.append(str(observation.payload["message"]))
        return AgentAction(
            action_id="action-public-validate",
            tool_name="public_validate",
            arguments={},
            source_backend="fake-backend",
            candidate_tree_sha256=SHA_A,
        )


class PublicValidationEnvironment:
    def __init__(self, *, profile_sha256: str | None) -> None:
        self.profile_sha256 = profile_sha256
        self.step_calls = 0

    def start(self, context: EpisodeContext) -> Observation:
        return Observation(
            observation_id="observation-task",
            tool_name="task",
            status="ready",
            payload={"message": "task"},
            candidate_tree_sha256=SHA_A,
        )

    def step(
        self,
        action: AgentAction,
        capability: ToolCapability,
    ) -> EnvironmentStep:
        self.step_calls += 1
        assert action.tool_name == "public_validate"
        assert capability.budget_class == "public_validation"
        return EnvironmentStep(
            observation=Observation(
                observation_id="observation-public-validation",
                tool_name="public_validate",
                status="succeeded",
                payload={"message": "public feedback"},
                candidate_tree_sha256=SHA_A,
                validation_profile_sha256=self.profile_sha256,
                budget_delta={"public_validation_calls": 1},
            ),
            done=False,
        )

    def freeze_submission(self) -> FrozenSubmission:
        raise AssertionError("public validation does not freeze a submission")

    def close(self) -> None:
        return None


class UnusedFinalJudge:
    def judge(self, submission: FrozenSubmission) -> FinalJudgment:
        raise AssertionError("final judge must not run")


def _context() -> EpisodeContext:
    return EpisodeContext(
        episode_id="episode-001",
        attempt_id="attempt-001",
        task_id="v4-001",
        condition="Agentic+EVAS",
        max_steps=1,
        budget_limits={"tool_calls": 1, "public_validation_calls": 1},
    )


def test_public_validation_requires_campaign_bound_profile_before_dispatch() -> None:
    environment = PublicValidationEnvironment(profile_sha256=PUBLIC_PROFILE_SHA256)
    controller = EpisodeController(
        policy=PublicValidationPolicy(),
        environment=environment,
        final_judge=UnusedFinalJudge(),
        tool_registry=ToolRegistry([_descriptor()]),
    )

    result = controller.run(_context())

    assert result.failure is not None
    assert result.failure.category == "public_validation_profile_unbound"
    assert result.failure.phase == "public_validation_authority"
    assert environment.step_calls == 0


@pytest.mark.parametrize("observed_profile", [None, "c" * 64])
def test_public_validation_rejects_missing_or_mismatched_observation_profile(
    observed_profile: str | None,
) -> None:
    policy = PublicValidationPolicy()
    environment = PublicValidationEnvironment(profile_sha256=observed_profile)
    controller = EpisodeController(
        policy=policy,
        environment=environment,
        final_judge=UnusedFinalJudge(),
        tool_registry=ToolRegistry([_descriptor()]),
        public_validation_profile_sha256=PUBLIC_PROFILE_SHA256,
    )

    result = controller.run(_context())

    assert result.failure is not None
    assert result.failure.category == "public_validation_profile_mismatch"
    assert result.failure.phase == "public_validation_authority"
    assert policy.seen_messages == ["task"]
    assert environment.step_calls == 1


def test_public_validation_profile_binding_reaches_canonical_observation() -> None:
    observation = Observation(
        observation_id="observation-public-validation",
        tool_name="public_validate",
        status="succeeded",
        payload={"message": "public feedback"},
        candidate_tree_sha256=SHA_A,
        validation_profile_sha256=PUBLIC_PROFILE_SHA256,
    )

    assert observation.to_document()["validation_profile_sha256"] == (
        PUBLIC_PROFILE_SHA256
    )


def test_public_validation_descriptor_rejects_private_or_unbound_evidence() -> None:
    with pytest.raises(ToolRegistryError, match="invalid_public_validation_evidence"):
        ToolRegistry([_descriptor(valid_public_evidence=False)])


@pytest.mark.parametrize("invalid_profile", ["not-a-hash", True])
def test_controller_rejects_invalid_campaign_profile_identity(
    invalid_profile: object,
) -> None:
    with pytest.raises(ValueError, match="public_validation_profile_sha256"):
        EpisodeController(
            policy=PublicValidationPolicy(),
            environment=PublicValidationEnvironment(profile_sha256=None),
            final_judge=UnusedFinalJudge(),
            tool_registry=ToolRegistry([_descriptor()]),
            public_validation_profile_sha256=invalid_profile,  # type: ignore[arg-type]
        )
