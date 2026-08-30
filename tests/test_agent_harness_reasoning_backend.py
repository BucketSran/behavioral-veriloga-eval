from __future__ import annotations

from copy import deepcopy
import json

import pytest

from runners.agent_harness import EpisodeContext, Observation, ProposalNormalizationError
from runners.agent_harness.backends import reasoning as reasoning_module
from runners.agent_harness.backends.reasoning import ReasoningPolicy


SHA_A = "a" * 64
SHA_B = "b" * 64
MISSING = object()


def _context() -> EpisodeContext:
    return EpisodeContext(
        episode_id="episode-001",
        attempt_id="attempt-001",
        task_id="v4-001",
        condition="Reasoning+EVAS",
        max_steps=4,
    )


def _observation(
    observation_id: str = "observation-001",
    *,
    candidate_tree_sha256: str | None = SHA_A,
    payload: dict | None = None,
    validation_profile_sha256: str | None = None,
) -> Observation:
    return Observation(
        observation_id=observation_id,
        tool_name="task",
        status="ready",
        payload=payload or {"message": "implement model.va"},
        candidate_tree_sha256=candidate_tree_sha256,
        validation_profile_sha256=validation_profile_sha256,
    )


def _bash_tool() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a command in the public candidate workspace.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
                "additionalProperties": False,
            },
        },
    }


def _request_content(context: EpisodeContext, observation: Observation) -> str:
    return json.dumps(
        {
            "schema_version": "vaevas-reasoning-request-v1",
            "context": {
                "episode_id": context.episode_id,
                "attempt_id": context.attempt_id,
                "task_id": context.task_id,
                "condition": context.condition,
            },
            "observation": observation.to_document(),
        },
        sort_keys=True,
    )


class FakeClient:
    model = "fixture-reasoning-model"

    def __init__(self, responses: list[dict]) -> None:
        self.responses = iter(responses)
        self.requests: list[dict] = []

    def complete(self, messages, max_tokens, tools, *, timeout_s=None):
        self.requests.append(
            {
                "messages": deepcopy(messages),
                "max_tokens": max_tokens,
                "tools": deepcopy(tools),
                "timeout_s": timeout_s,
            }
        )
        return next(self.responses)


def _native_response(
    command: str,
    *,
    usage: dict | None = None,
    call_id: object = "call-1",
) -> dict:
    tool_call = {
        "type": "function",
        "function": {
            "name": "bash",
            "arguments": json.dumps({"command": command}),
        },
    }
    if call_id is not MISSING:
        tool_call["id"] = call_id
    response = {
        "id": f"response-{call_id if call_id is not MISSING else 'missing'}",
        "model": "provider-model",
        "choices": [
            {
                "finish_reason": "tool_calls",
                "message": {
                    "role": "assistant",
                    "content": "reasoning hidden from action",
                    "tool_calls": [tool_call],
                },
            }
        ],
    }
    if usage is not None:
        response["usage"] = usage
    return response


def test_reasoning_policy_normalizes_native_tool_calls_and_records_unknown_usage() -> None:
    client = FakeClient([_native_response("sed -n '1,80p' public/task/instruction.md")])
    context = _context()
    policy = ReasoningPolicy(
        client=client,
        context=context,
        proposal_format="native_tool_calls",
        tools=[_bash_tool()],
        accepted_tool_names=frozenset({"bash"}),
        max_tokens=128,
        timeout_s=7.5,
    )

    action = policy.act(_observation())

    assert action.action_id == "attempt-001-0001"
    assert action.source_backend == "alphaapollo/reasoning-v1"
    assert action.tool_name == "bash"
    assert dict(action.arguments) == {"command": "sed -n '1,80p' public/task/instruction.md"}
    assert action.candidate_tree_sha256 == SHA_A
    assert client.requests == [
        {
            "messages": [
                {
                    "role": "system",
                    "content": policy.system_prompt,
                },
                {"role": "user", "content": _request_content(context, _observation())},
            ],
            "max_tokens": 128,
            "tools": [_bash_tool()],
            "timeout_s": 7.5,
        }
    ]
    assert policy.serialize()["info"]["calls"][0]["usage"] == {
        "input_tokens": None,
        "output_tokens": None,
        "reasoning_tokens": None,
        "source": "missing",
    }


def test_reasoning_policy_appends_native_assistant_and_tool_feedback_between_turns() -> None:
    client = FakeClient(
        [
            _native_response("false", usage={"prompt_tokens": 12, "completion_tokens": 4}),
            _native_response("true", call_id="call-2"),
        ]
    )
    context = _context()
    policy = ReasoningPolicy(
        client=client,
        context=context,
        proposal_format="native_tool_calls",
        tools=[_bash_tool()],
        accepted_tool_names=frozenset({"bash"}),
        max_tokens=128,
    )

    first = policy.act(_observation("observation-001", candidate_tree_sha256=SHA_A))
    second = policy.act(
        _observation(
            "observation-002",
            candidate_tree_sha256=SHA_B,
            payload={"output": "PUBLIC_FAILURE", "returncode": 1, "exception_info": ""},
            validation_profile_sha256="c" * 64,
        )
    )

    assert first.action_id == "attempt-001-0001"
    assert second.action_id == "attempt-001-0002"
    assert second.candidate_tree_sha256 == SHA_B
    assert [message["role"] for message in client.requests[1]["messages"]] == [
        "system",
        "user",
        "assistant",
        "tool",
    ]
    assert client.requests[1]["messages"][-2]["tool_calls"][0]["id"] == "call-1"
    assert client.requests[1]["messages"][-1] == {
        "role": "tool",
        "tool_call_id": "call-1",
        "content": _request_content(
            context,
            _observation(
                "observation-002",
                candidate_tree_sha256=SHA_B,
                payload={"output": "PUBLIC_FAILURE", "returncode": 1, "exception_info": ""},
                validation_profile_sha256="c" * 64,
            ),
        ),
    }
    assert json.dumps(client.requests[1]["messages"]).count("observation-002") == 1
    assert policy.serialize()["info"]["calls"][0]["usage"] == {
        "input_tokens": 12,
        "output_tokens": 4,
        "reasoning_tokens": None,
        "source": "provider",
    }


def test_reasoning_policy_strict_json_uses_public_observation_without_tools() -> None:
    client = FakeClient(
        [
            {
                "id": "response-json",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": '{"tool_name":"bash","arguments":{"command":"true"}}',
                        },
                    }
                ],
                "usage": {"input_tokens": 5, "output_tokens": 9, "reasoning_tokens": 2},
            }
        ]
    )
    context = _context()
    policy = ReasoningPolicy(
        client=client,
        context=context,
        proposal_format="strict_json",
        tools=[_bash_tool()],
        accepted_tool_names=frozenset({"bash"}),
        max_tokens=64,
    )

    action = policy.act(_observation())

    assert dict(action.arguments) == {"command": "true"}
    assert client.requests[0]["tools"] == []
    assert client.requests[0]["messages"] == [
        {"role": "system", "content": policy.system_prompt},
        {"role": "user", "content": _request_content(context, _observation())},
    ]
    system = client.requests[0]["messages"][0]["content"]
    assert '"tool_name"' in system
    assert '"arguments"' in system
    assert "bash" in system
    assert "additionalProperties" in system


def test_reasoning_policy_strict_json_preserves_episode_local_public_history() -> None:
    client = FakeClient(
        [
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": '{"tool_name":"bash","arguments":{"command":"first"}}',
                        },
                    }
                ]
            },
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": '{"tool_name":"bash","arguments":{"command":"second"}}',
                        },
                    }
                ]
            },
        ]
    )
    policy = ReasoningPolicy(
        client=client,
        context=_context(),
        proposal_format="strict_json",
        tools=[_bash_tool()],
        accepted_tool_names=frozenset({"bash"}),
        max_tokens=128,
    )

    assert policy.act(_observation("observation-001")).arguments["command"] == "first"
    assert policy.act(_observation("observation-002")).arguments["command"] == "second"

    assert [message["role"] for message in client.requests[1]["messages"]] == [
        "system",
        "user",
        "assistant",
        "user",
    ]
    serialized = json.dumps(client.requests[1]["messages"])
    assert "observation-001" in serialized
    assert "first" in serialized
    assert "observation-002" in serialized


@pytest.mark.parametrize(
    ("tool_calls", "error_code"),
    [
        (
            [
                {
                    "id": "call-python",
                    "type": "function",
                    "function": {"name": "python", "arguments": "{}"},
                }
            ],
            "unknown_tool",
        ),
        (
            [
                {
                    "type": "function",
                    "function": {"name": "bash", "arguments": "{}"},
                },
                {
                    "type": "function",
                    "function": {"name": "bash", "arguments": "{}"},
                },
            ],
            "action_count",
        ),
    ],
)
def test_reasoning_policy_fails_closed_on_wrong_or_multiple_native_calls(
    tool_calls: list[dict],
    error_code: str,
) -> None:
    client = FakeClient(
        [{"choices": [{"message": {"role": "assistant", "tool_calls": tool_calls}}]}]
    )
    policy = ReasoningPolicy(
        client=client,
        context=_context(),
        proposal_format="native_tool_calls",
        tools=[_bash_tool()],
        accepted_tool_names=frozenset({"bash"}),
        max_tokens=128,
    )

    with pytest.raises(ProposalNormalizationError, match=error_code):
        policy.act(_observation())


@pytest.mark.parametrize(
    ("call_id", "error_code"),
    [
        (MISSING, "missing_provider_call_id"),
        ("", "invalid_provider_call_id"),
        (7, "invalid_provider_call_id"),
    ],
)
def test_reasoning_policy_requires_native_provider_call_ids(
    call_id: object,
    error_code: str,
) -> None:
    client = FakeClient([_native_response("true", call_id=call_id)])
    policy = ReasoningPolicy(
        client=client,
        context=_context(),
        proposal_format="native_tool_calls",
        tools=[_bash_tool()],
        accepted_tool_names=frozenset({"bash"}),
        max_tokens=128,
    )

    with pytest.raises(ProposalNormalizationError, match=error_code):
        policy.act(_observation())


def test_reasoning_policy_rejects_duplicate_native_provider_call_ids() -> None:
    client = FakeClient(
        [
            _native_response("first", call_id="call-reused"),
            _native_response("second", call_id="call-reused"),
        ]
    )
    policy = ReasoningPolicy(
        client=client,
        context=_context(),
        proposal_format="native_tool_calls",
        tools=[_bash_tool()],
        accepted_tool_names=frozenset({"bash"}),
        max_tokens=128,
    )

    assert policy.act(_observation("observation-001")).arguments["command"] == "first"
    with pytest.raises(ProposalNormalizationError, match="duplicate_provider_call_id"):
        policy.act(_observation("observation-002"))


@pytest.mark.parametrize("max_tokens", [0, -1, True, 1.5])
def test_reasoning_policy_requires_strict_positive_integer_max_tokens(
    max_tokens: object,
) -> None:
    with pytest.raises((TypeError, ValueError), match="max_tokens"):
        ReasoningPolicy(
            client=FakeClient([]),
            context=_context(),
            proposal_format="native_tool_calls",
            tools=[_bash_tool()],
            accepted_tool_names=frozenset({"bash"}),
            max_tokens=max_tokens,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("timeout_s", [0, -1.0, True, "5", float("inf"), float("nan")])
def test_reasoning_policy_requires_finite_positive_timeout_when_set(
    timeout_s: object,
) -> None:
    with pytest.raises((TypeError, ValueError), match="timeout_s"):
        ReasoningPolicy(
            client=FakeClient([]),
            context=_context(),
            proposal_format="native_tool_calls",
            tools=[_bash_tool()],
            accepted_tool_names=frozenset({"bash"}),
            max_tokens=128,
            timeout_s=timeout_s,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("deadline_monotonic", [True, "5", float("inf"), float("nan")])
def test_reasoning_policy_requires_finite_deadline_when_set(
    deadline_monotonic: object,
) -> None:
    with pytest.raises((TypeError, ValueError), match="deadline_monotonic"):
        ReasoningPolicy(
            client=FakeClient([]),
            context=_context(),
            proposal_format="native_tool_calls",
            tools=[_bash_tool()],
            accepted_tool_names=frozenset({"bash"}),
            max_tokens=128,
            deadline_monotonic=deadline_monotonic,  # type: ignore[arg-type]
        )


def test_reasoning_policy_clamps_request_timeout_to_remaining_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(reasoning_module.time, "monotonic", lambda: 97.0)
    client = FakeClient([_native_response("true")])
    policy = ReasoningPolicy(
        client=client,
        context=_context(),
        proposal_format="native_tool_calls",
        tools=[_bash_tool()],
        accepted_tool_names=frozenset({"bash"}),
        max_tokens=128,
        timeout_s=10.0,
        deadline_monotonic=100.0,
    )

    policy.act(_observation())

    assert client.requests[0]["timeout_s"] == 3.0
    assert client.requests[0]["max_tokens"] == 128


def test_reasoning_policy_uses_remaining_deadline_when_no_timeout_is_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(reasoning_module.time, "monotonic", lambda: 97.5)
    client = FakeClient([_native_response("true")])
    policy = ReasoningPolicy(
        client=client,
        context=_context(),
        proposal_format="native_tool_calls",
        tools=[_bash_tool()],
        accepted_tool_names=frozenset({"bash"}),
        max_tokens=128,
        deadline_monotonic=100.0,
    )

    policy.act(_observation())

    assert client.requests[0]["timeout_s"] == 2.5


def test_reasoning_policy_without_deadline_preserves_configured_timeout() -> None:
    client = FakeClient([_native_response("true")])
    policy = ReasoningPolicy(
        client=client,
        context=_context(),
        proposal_format="native_tool_calls",
        tools=[_bash_tool()],
        accepted_tool_names=frozenset({"bash"}),
        max_tokens=128,
        timeout_s=7.0,
    )

    policy.act(_observation())

    assert client.requests[0]["timeout_s"] == 7.0


def test_reasoning_policy_expired_deadline_fails_before_model_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(reasoning_module.time, "monotonic", lambda: 101.0)
    client = FakeClient([_native_response("true")])
    policy = ReasoningPolicy(
        client=client,
        context=_context(),
        proposal_format="native_tool_calls",
        tools=[_bash_tool()],
        accepted_tool_names=frozenset({"bash"}),
        max_tokens=128,
        deadline_monotonic=100.0,
    )

    with pytest.raises(TimeoutError, match="deadline"):
        policy.act(_observation())
    assert client.requests == []


@pytest.mark.parametrize(
    "usage",
    [
        {"prompt_tokens": -1, "completion_tokens": 2},
        {"prompt_tokens": True, "completion_tokens": 2},
        {"prompt_tokens": 1.5, "completion_tokens": 2},
        {"prompt_tokens": 1, "completion_tokens": "2"},
        {"completion_tokens_details": {"reasoning_tokens": -1}},
    ],
)
def test_reasoning_policy_rejects_invalid_provider_usage_metrics(usage: dict) -> None:
    client = FakeClient([_native_response("true", usage=usage)])
    policy = ReasoningPolicy(
        client=client,
        context=_context(),
        proposal_format="native_tool_calls",
        tools=[_bash_tool()],
        accepted_tool_names=frozenset({"bash"}),
        max_tokens=128,
    )

    with pytest.raises(ProposalNormalizationError, match="invalid_provider_usage"):
        policy.act(_observation())


def test_reasoning_policy_keeps_episode_histories_isolated() -> None:
    first_client = FakeClient([_native_response("echo first")])
    second_client = FakeClient([_native_response("echo second")])
    first = ReasoningPolicy(
        client=first_client,
        context=_context(),
        proposal_format="native_tool_calls",
        tools=[_bash_tool()],
        accepted_tool_names=frozenset({"bash"}),
        max_tokens=32,
    )
    second = ReasoningPolicy(
        client=second_client,
        context=EpisodeContext(
            episode_id="episode-002",
            attempt_id="attempt-002",
            task_id="v4-002",
            condition="Reasoning+EVAS",
            max_steps=4,
        ),
        proposal_format="native_tool_calls",
        tools=[_bash_tool()],
        accepted_tool_names=frozenset({"bash"}),
        max_tokens=32,
    )

    assert first.act(_observation()).action_id == "attempt-001-0001"
    assert second.act(_observation()).action_id == "attempt-002-0001"
    assert "episode-001" in first_client.requests[0]["messages"][-1]["content"]
    assert "episode-001" not in second_client.requests[0]["messages"][-1]["content"]


def test_reasoning_policy_requires_candidate_binding_and_excludes_final_metadata() -> None:
    client = FakeClient([_native_response("true")])
    policy = ReasoningPolicy(
        client=client,
        context=_context(),
        proposal_format="native_tool_calls",
        tools=[_bash_tool()],
        accepted_tool_names=frozenset({"bash"}),
        max_tokens=32,
    )

    with pytest.raises(ValueError, match="candidate_tree_sha256"):
        policy.act(_observation(candidate_tree_sha256=None))
    assert client.requests == []

    action = policy.act(_observation(payload={"message": "safe public task"}))

    assert action.tool_name == "bash"
    serialized = json.dumps(client.requests, sort_keys=True)
    assert "final" not in serialized.lower()
    assert "judge" not in serialized.lower()
    assert "score" not in serialized.lower()
