from __future__ import annotations

import pytest

from runners.agent_harness import (
    AgentAction,
    EpisodeController,
    EpisodeContext,
    FinalJudgment,
    FrozenSubmission,
    Observation,
    ProposalNormalizationError,
    ToolExecutionRejection,
    ToolRegistry,
)
from runners.agent_harness.backends.mini_swe import (
    MINI_SWE_BASH_HANDLER_ID,
    MiniSweBashEnvironmentBridge,
    MiniSwePolicyBridge,
    mini_swe_bash_tool_descriptor,
)


SHA_A = "a" * 64
SHA_B = "b" * 64


def _observation(candidate_tree_sha256: str = SHA_A) -> Observation:
    return Observation(
        observation_id="observation-001",
        tool_name="task",
        status="ready",
        payload={"message": "implement model.va"},
        candidate_tree_sha256=candidate_tree_sha256,
    )


def test_mini_swe_policy_bridge_normalizes_native_bash_calls() -> None:
    responses = iter(
        [
            {
                "role": "assistant",
                "content": "inspect",
                "tool_calls": [
                    {
                        "id": "provider-call-1",
                        "type": "function",
                        "function": {
                            "name": "bash",
                            "arguments": '{"command":"sed -n 1,80p public/task/instruction.md"}',
                        },
                    }
                ],
            },
            {
                "role": "assistant",
                "content": "edit",
                "tool_calls": [
                    {
                        "id": "provider-call-2",
                        "type": "function",
                        "function": {
                            "name": "bash",
                            "arguments": '{"command":"printf model > public/submission/model.va"}',
                        },
                    }
                ],
            },
        ]
    )
    bridge = MiniSwePolicyBridge(
        propose=lambda _observation: next(responses),
        action_id_prefix="attempt-007/action",
        source_backend="mini-swe-agent-2.4.5",
    )

    first = bridge.act(_observation(SHA_A))
    second = bridge.act(_observation(SHA_B))

    assert first.action_id == "attempt-007/action-0001"
    assert first.tool_name == "bash"
    assert dict(first.arguments) == {
        "command": "sed -n 1,80p public/task/instruction.md"
    }
    assert first.source_backend == "mini-swe-agent-2.4.5"
    assert first.candidate_tree_sha256 == SHA_A
    assert second.action_id == "attempt-007/action-0002"
    assert second.candidate_tree_sha256 == SHA_B
    assert "provider-call-1" not in first.to_document().values()


def test_mini_swe_policy_bridge_accepts_the_raw_tool_call_sequence() -> None:
    bridge = MiniSwePolicyBridge(
        propose=lambda _observation: [
            {
                "type": "function",
                "function": {
                    "name": "bash",
                    "arguments": '{"command":"true"}',
                },
            }
        ],
        action_id_prefix="attempt-001/action",
    )

    action = bridge.act(_observation())

    assert dict(action.arguments) == {"command": "true"}
    assert action.source_backend == "mini-swe"


@pytest.mark.parametrize(
    ("proposal", "error_code"),
    [
        ({"role": "assistant", "content": "no tool"}, "missing_tool_calls"),
        (
            {
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {"name": "bash", "arguments": "{}"},
                    },
                    {
                        "type": "function",
                        "function": {"name": "bash", "arguments": "{}"},
                    },
                ]
            },
            "action_count",
        ),
        (
            {
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {"name": "python", "arguments": "{}"},
                    }
                ]
            },
            "unknown_tool",
        ),
    ],
)
def test_mini_swe_policy_bridge_fails_closed_on_ambiguous_proposals(
    proposal: object,
    error_code: str,
) -> None:
    bridge = MiniSwePolicyBridge(
        propose=lambda _observation: proposal,
        action_id_prefix="attempt-001/action",
    )

    with pytest.raises(ProposalNormalizationError, match=error_code):
        bridge.act(_observation())


def test_mini_swe_policy_bridge_requires_candidate_binding() -> None:
    bridge = MiniSwePolicyBridge(
        propose=lambda _observation: [
            {
                "type": "function",
                "function": {"name": "bash", "arguments": '{"command":"true"}'},
            }
        ],
        action_id_prefix="attempt-001/action",
    )

    with pytest.raises(ValueError, match="candidate_tree_sha256"):
        bridge.act(_observation(candidate_tree_sha256=None))  # type: ignore[arg-type]


class Submitted(Exception):
    pass


class FakeLegacyBashEnvironment:
    def __init__(self, candidate_state: dict[str, str]) -> None:
        self.candidate_state = candidate_state
        self.actions: list[dict[str, str]] = []
        self.close_calls = 0

    def execute(self, action: dict[str, str], cwd: str = "") -> dict[str, object]:
        assert cwd == ""
        self.actions.append(dict(action))
        command = action["command"]
        if command == "mutate":
            self.candidate_state["sha256"] = SHA_B
            return {
                "output": "changed model.va",
                "returncode": 0,
                "exception_info": "",
                "elapsed_s": 0.25,
                "output_total_bytes": 16,
                "output_captured_bytes": 16,
                "output_truncated_bytes": 0,
                "resources": {"submission_bytes": 16, "exceeded": []},
            }
        if command == "reject-submit":
            return {
                "output": '{"status":"submission_rejected"}',
                "returncode": 2,
                "exception_info": "",
            }
        if command == "submit":
            raise Submitted("legacy private exit payload")
        if command == "explode":
            raise RuntimeError("sandbox disappeared")
        return {"output": "ok", "returncode": 0, "exception_info": ""}

    def close(self) -> None:
        self.close_calls += 1


def _bash_capability():
    registry = ToolRegistry(
        [mini_swe_bash_tool_descriptor(allowed_conditions=["Agentic+EVAS"])]
    )
    return registry.authorize(
        "bash",
        condition_id="Agentic+EVAS",
        model_visible=True,
    )


def _bash_action(command: object, *, candidate_tree_sha256: str = SHA_A) -> AgentAction:
    return AgentAction(
        action_id="attempt-001/action-0001",
        tool_name="bash",
        arguments={"command": command},
        source_backend="mini-swe",
        candidate_tree_sha256=candidate_tree_sha256,
    )


def _environment_bridge(
    legacy: FakeLegacyBashEnvironment,
    candidate_state: dict[str, str],
) -> MiniSweBashEnvironmentBridge:
    return MiniSweBashEnvironmentBridge(
        legacy_environment=legacy,
        task_payload={"message": "implement model.va"},
        candidate_tree_sha256=lambda: candidate_state["sha256"],
        freeze_submission=lambda: FrozenSubmission(
            tree_sha256=candidate_state["sha256"],
            artifacts=("model.va",),
        ),
        submitted_exception_types=(Submitted,),
    )


def _context() -> EpisodeContext:
    return EpisodeContext(
        episode_id="episode-001",
        attempt_id="attempt-001",
        task_id="v4-001",
        condition="Agentic+EVAS",
        max_steps=4,
    )


def test_mini_swe_bash_descriptor_freezes_the_compatibility_contract() -> None:
    descriptor = mini_swe_bash_tool_descriptor(
        allowed_conditions=["Agentic+EVAS", "Agentic-no-EVAS"]
    )

    assert descriptor["tool_name"] == "bash"
    assert descriptor["handler_id"] == MINI_SWE_BASH_HANDLER_ID
    assert descriptor["budget_class"] == "tool_call"
    assert descriptor["state_effect"] == "candidate_mutation"
    assert descriptor["candidate_effect"] == "mutate"
    assert descriptor["allowed_conditions"] == [
        "Agentic+EVAS",
        "Agentic-no-EVAS",
    ]
    assert descriptor["argument_schema"] == {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
        "additionalProperties": False,
    }


def test_mini_swe_environment_bridge_maps_legacy_bash_output_and_candidate_state() -> None:
    candidate_state = {"sha256": SHA_A}
    legacy = FakeLegacyBashEnvironment(candidate_state)
    bridge = _environment_bridge(legacy, candidate_state)

    start = bridge.start(_context())
    step = bridge.step(_bash_action("mutate"), _bash_capability())

    assert start.observation_id == "attempt-001/observation-0000"
    assert start.candidate_tree_sha256 == SHA_A
    assert not isinstance(step, ToolExecutionRejection)
    assert step.done is False
    assert step.terminal_reason is None
    assert step.observation.status == "succeeded"
    assert step.observation.candidate_tree_sha256 == SHA_B
    assert step.observation.truncated is False
    assert step.observation.payload == {
        "output": "changed model.va",
        "returncode": 0,
        "exception_info": "",
        "elapsed_s": 0.25,
        "output_total_bytes": 16,
        "output_captured_bytes": 16,
        "output_truncated_bytes": 0,
        "resources": {"submission_bytes": 16, "exceeded": ()},
    }
    assert legacy.actions == [{"command": "mutate"}]


def test_mini_swe_environment_bridge_keeps_rejected_submission_nonterminal() -> None:
    candidate_state = {"sha256": SHA_A}
    legacy = FakeLegacyBashEnvironment(candidate_state)
    bridge = _environment_bridge(legacy, candidate_state)
    bridge.start(_context())

    step = bridge.step(_bash_action("reject-submit"), _bash_capability())

    assert not isinstance(step, ToolExecutionRejection)
    assert step.done is False
    assert step.observation.status == "failed"
    assert step.observation.payload["returncode"] == 2


def test_mini_swe_environment_bridge_maps_only_bound_submission_signal() -> None:
    candidate_state = {"sha256": SHA_B}
    legacy = FakeLegacyBashEnvironment(candidate_state)
    bridge = _environment_bridge(legacy, candidate_state)
    bridge.start(_context())

    step = bridge.step(
        _bash_action("submit", candidate_tree_sha256=SHA_B),
        _bash_capability(),
    )

    assert not isinstance(step, ToolExecutionRejection)
    assert step.done is True
    assert step.terminal_reason == "submitted"
    assert step.observation.status == "submitted"
    assert step.observation.payload == {
        "output": "submission accepted",
        "returncode": 0,
        "exception_info": "",
    }
    assert "legacy private exit payload" not in str(step.observation.payload)
    assert bridge.freeze_submission() == FrozenSubmission(
        tree_sha256=SHA_B,
        artifacts=("model.va",),
    )


def test_mini_swe_environment_bridge_does_not_hide_other_failures() -> None:
    candidate_state = {"sha256": SHA_A}
    legacy = FakeLegacyBashEnvironment(candidate_state)
    bridge = _environment_bridge(legacy, candidate_state)
    bridge.start(_context())

    with pytest.raises(RuntimeError, match="sandbox disappeared"):
        bridge.step(_bash_action("explode"), _bash_capability())


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"command": 7},
        {"command": "true", "extra": True},
    ],
)
def test_mini_swe_environment_bridge_rejects_invalid_arguments_before_execute(
    arguments: dict[str, object],
) -> None:
    candidate_state = {"sha256": SHA_A}
    legacy = FakeLegacyBashEnvironment(candidate_state)
    bridge = _environment_bridge(legacy, candidate_state)
    bridge.start(_context())
    action = AgentAction(
        action_id="attempt-001/action-0001",
        tool_name="bash",
        arguments=arguments,
        source_backend="mini-swe",
        candidate_tree_sha256=SHA_A,
    )

    rejection = bridge.step(action, _bash_capability())

    assert isinstance(rejection, ToolExecutionRejection)
    assert rejection.code == "invalid_tool_arguments"
    assert rejection.candidate_tree_sha256 == SHA_A
    assert legacy.actions == []


def test_mini_swe_environment_bridge_owns_idempotent_legacy_cleanup() -> None:
    candidate_state = {"sha256": SHA_A}
    legacy = FakeLegacyBashEnvironment(candidate_state)
    bridge = _environment_bridge(legacy, candidate_state)

    bridge.close()
    bridge.close()

    assert legacy.close_calls == 1


class PassingJudge:
    def judge(self, submission: FrozenSubmission) -> FinalJudgment:
        return FinalJudgment(
            status="passed",
            judge_engine="evas-0.8.7-test-double",
            score=1.0,
            submission_tree_sha256=submission.tree_sha256,
        )


def test_mini_swe_bridges_run_through_the_generic_controller_without_replacing_legacy_execute() -> None:
    candidate_state = {"sha256": SHA_A}
    legacy = FakeLegacyBashEnvironment(candidate_state)
    environment = _environment_bridge(legacy, candidate_state)
    responses = iter(
        [
            [
                {
                    "type": "function",
                    "function": {
                        "name": "bash",
                        "arguments": '{"command":"mutate"}',
                    },
                }
            ],
            [
                {
                    "type": "function",
                    "function": {
                        "name": "bash",
                        "arguments": '{"command":"submit"}',
                    },
                }
            ],
        ]
    )
    policy = MiniSwePolicyBridge(
        propose=lambda _observation: next(responses),
        action_id_prefix="attempt-001/action",
    )
    registry = ToolRegistry(
        [mini_swe_bash_tool_descriptor(allowed_conditions=["Agentic+EVAS"])]
    )
    controller = EpisodeController(
        policy=policy,
        environment=environment,
        final_judge=PassingJudge(),
        tool_registry=registry,
    )

    result = controller.run(_context())

    assert result.primary_outcome == "passed"
    assert result.terminal_reason == "submitted"
    assert result.submission == FrozenSubmission(
        tree_sha256=SHA_B,
        artifacts=("model.va",),
    )
    assert result.final_judgment is not None
    assert result.final_judgment.submission_tree_sha256 == SHA_B
    assert legacy.actions == [{"command": "mutate"}, {"command": "submit"}]
    assert legacy.close_calls == 1
