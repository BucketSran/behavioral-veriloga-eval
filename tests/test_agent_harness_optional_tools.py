"""Native opt-in tools preserve the legacy Bash-only default."""

import json
import time

import pytest

from test_agent_harness_native_launcher import Provider, mini, runner
from runners.agent_harness import Observation


DOC_TOOL = {
    "type": "function", "function": {
        "name": "vaevas_docs_search", "description": "Search frozen synthetic docs.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}},
                       "required": ["query"], "additionalProperties": False},
    },
}


@pytest.mark.parametrize("enabled", [False, True])
def test_mini_swe_optional_tool_is_explicit_and_feedback_reaches_next_request(enabled):
    from run_native_mini_swe import NativeMiniSwePolicy

    provider = Provider(["ignored", "vabench-submit"])
    original = provider.complete
    seen_tools = []

    def complete(messages, max_tokens, tools, **kwargs):
        seen_tools.append(tools)
        result = original(messages, max_tokens, tools, **kwargs)
        if len(seen_tools) == 1:
            function = result["choices"][0]["message"]["tool_calls"][0]["function"]
            function.update(name="vaevas_docs_search", arguments=json.dumps({"query": "resistor"}))
        return result

    provider.complete = complete
    model = mini.VaBenchMiniModel(
        provider, per_turn_max_tokens=128, request_timeout_s=10,
        deadline_monotonic=time.monotonic() + 60,
        usage_parser=runner.provider_output_usage, response_metadata=runner.provider_response_metadata,
        **({"tools": [mini.BASH_TOOL, DOC_TOOL]} if enabled else {}),
    )
    policy = NativeMiniSwePolicy(
        model=model, prompt="synthetic task", action_id_prefix="attempt",
        **({"accepted_tool_names": frozenset({"bash", "vaevas_docs_search"})} if enabled else {}),
    )
    observation = Observation("initial", "task", "ready", {}, candidate_tree_sha256="a" * 64)
    if not enabled:
        from runners.agent_harness import ProposalNormalizationError
        with pytest.raises(ProposalNormalizationError):
            policy.act(observation)
        assert seen_tools == [[mini.BASH_TOOL]]
        return
    action = policy.act(observation)
    assert action.tool_name == "vaevas_docs_search"
    assert action.arguments == {"query": "resistor"}
    policy.act(Observation(
        "docs", "vaevas_docs_search", "succeeded",
        {"matches": [{"snippet": "SYNTHETIC_DOC"}], "corpus_profile_sha256": "c" * 64},
        candidate_tree_sha256="a" * 64,
    ))
    assert seen_tools == [[mini.BASH_TOOL, DOC_TOOL]] * 2
    assert "SYNTHETIC_DOC" in provider.requests[-1][-1]["content"]
    assert "c" * 64 in provider.requests[-1][-1]["content"]
    initial = json.dumps(provider.requests[0])
    assert "exactly one bash action" not in initial
    assert "vaevas_docs_search" in initial
