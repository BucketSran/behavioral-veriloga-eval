from __future__ import annotations

import pytest

from runners.agent_harness import Observation, ProposalNormalizationError
from runners.agent_harness.backends.mini_swe import MiniSwePolicyBridge


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
