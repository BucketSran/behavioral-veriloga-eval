from __future__ import annotations

import pytest

from runners.agent_harness import ToolRegistry, ToolRegistryError
from runners.agent_harness.reserved_tools import reserved_domain_tool_descriptors


def _active_bash_descriptor() -> dict:
    return {
        "schema_version": "vaevas-tool-descriptor-v1",
        "tool_id": "core/bash-v1",
        "tool_name": "bash",
        "tool_version": "1",
        "lifecycle": "active",
        "model_visibility": "model_visible",
        "allowed_conditions": ["Agentic+EVAS"],
        "budget_class": "tool_call",
        "state_effect": "candidate_mutation",
        "candidate_effect": "mutate",
        "argument_schema": {"type": "object"},
        "observation_schema": {"type": "object"},
        "evidence_policy": {
            "records_private_evidence": False,
            "may_enter_model_observation": True,
            "may_enter_shared_memory": True,
            "requires_candidate_binding": True,
        },
        "handler_id": "core.execute_bash",
    }


def test_reserved_domain_tool_families_are_non_callable_namespace_markers() -> None:
    descriptors = reserved_domain_tool_descriptors()

    assert [row["tool_name"] for row in descriptors] == [
        "vaevas.reserved.candidate",
        "vaevas.reserved.public_validation",
        "vaevas.reserved.retrieval",
        "vaevas.reserved.submission",
        "vaevas.reserved.waveform",
    ]
    for descriptor in descriptors:
        assert descriptor["lifecycle"] == "reserved"
        assert descriptor["handler_id"] is None
        assert descriptor["model_visibility"] == "harness_internal"
        assert descriptor["budget_class"] == "reserved"
        assert descriptor["state_effect"] == "read_only"
        assert descriptor["candidate_effect"] == "none"


def test_reserved_families_change_full_registry_identity_but_not_effective_tools() -> None:
    active = _active_bash_descriptor()
    baseline = ToolRegistry([active])
    with_placeholders = ToolRegistry(
        [active, *reserved_domain_tool_descriptors()]
    )

    baseline_effective = baseline.resolve(
        condition_id="Agentic+EVAS",
        model_visible=True,
    )
    placeholder_effective = with_placeholders.resolve(
        condition_id="Agentic+EVAS",
        model_visible=True,
    )

    assert baseline.registry_sha256 != with_placeholders.registry_sha256
    assert (
        baseline_effective.effective_capability_sha256
        == placeholder_effective.effective_capability_sha256
    )
    assert placeholder_effective.accepted_tool_names == frozenset({"bash"})


@pytest.mark.parametrize(
    "tool_name",
    [row["tool_name"] for row in reserved_domain_tool_descriptors()],
)
def test_reserved_domain_tool_families_fail_before_dispatch(tool_name: str) -> None:
    registry = ToolRegistry(reserved_domain_tool_descriptors())

    with pytest.raises(ToolRegistryError, match="reserved_tool"):
        registry.authorize(
            tool_name,
            condition_id="AlphaApollo-Reasoning+EVAS",
            model_visible=True,
        )


def test_reserved_domain_tool_families_do_not_include_final_judges() -> None:
    names = {row["tool_name"] for row in reserved_domain_tool_descriptors()}

    assert "evas.final_judge" not in names
    assert "spectre.final_judge" not in names
