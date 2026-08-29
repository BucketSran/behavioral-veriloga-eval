from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from runners.agent_harness.tool_registry import (
    ToolRegistry,
    ToolRegistryError,
    tool_descriptor_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "vaevas-tool-descriptor-v1.schema.json"


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _descriptor(**updates: Any) -> dict[str, Any]:
    descriptor: dict[str, Any] = {
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
        "argument_schema": {
            "type": "object",
            "required": ["command"],
            "properties": {"command": {"type": "string", "minLength": 1}},
            "additionalProperties": False,
        },
        "observation_schema": {
            "type": "object",
            "required": ["exit_code", "stdout_sha256"],
            "properties": {
                "exit_code": {"type": "integer"},
                "stdout_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            },
            "additionalProperties": False,
        },
        "evidence_policy": {
            "records_private_evidence": True,
            "may_enter_model_observation": True,
            "may_enter_shared_memory": False,
            "requires_candidate_binding": True,
        },
        "handler_id": "tool.bash",
    }
    descriptor.update(updates)
    return descriptor


def test_active_model_visible_descriptor_is_valid_hashable_and_resolvable() -> None:
    descriptor = _descriptor()

    jsonschema.validate(descriptor, _schema())
    resolved = ToolRegistry([descriptor]).resolve(
        condition_id="Agentic+EVAS",
        model_visible=True,
    )

    assert resolved.accepted_tool_names == frozenset({"bash"})
    assert resolved.capabilities[0].tool_name == "bash"
    assert len(resolved.effective_capability_sha256) == 64
    assert resolved.capabilities[0].argument_schema["required"] == ("command",)
    assert len(resolved.capabilities[0].argument_schema_sha256) == 64
    assert resolved.capabilities[0].observation_schema["required"] == (
        "exit_code",
        "stdout_sha256",
    )
    assert len(resolved.capabilities[0].observation_schema_sha256) == 64
    assert resolved.capabilities[0].evidence_policy["may_enter_model_observation"]
    assert len(resolved.capabilities[0].evidence_policy_sha256) == 64
    assert tool_descriptor_sha256(descriptor) == tool_descriptor_sha256(
        dict(reversed(list(descriptor.items())))
    )


def test_reserved_placeholder_is_valid_but_not_callable() -> None:
    descriptor = _descriptor(
        tool_id="domain/waveform-v1",
        tool_name="waveform.inspect",
        lifecycle="reserved",
        budget_class="reserved",
        state_effect="read_only",
        candidate_effect="read",
        handler_id=None,
    )

    jsonschema.validate(descriptor, _schema())
    registry = ToolRegistry([descriptor])

    with pytest.raises(ToolRegistryError, match="reserved_tool"):
        registry.authorize(
            "waveform.inspect",
            condition_id="Agentic+EVAS",
            model_visible=True,
        )


def test_inactive_tool_is_valid_but_not_resolved_or_callable() -> None:
    descriptor = _descriptor(lifecycle="inactive", handler_id="tool.bash")

    jsonschema.validate(descriptor, _schema())
    registry = ToolRegistry([descriptor])

    assert registry.resolve(
        condition_id="Agentic+EVAS",
        model_visible=True,
    ).accepted_tool_names == frozenset()
    with pytest.raises(ToolRegistryError, match="inactive_tool"):
        registry.authorize(
            "bash",
            condition_id="Agentic+EVAS",
            model_visible=True,
        )


@pytest.mark.parametrize(
    ("tool_name", "condition_id", "error_code"),
    [
        ("unknown.tool", "Agentic+EVAS", "unknown_tool"),
        ("bash", "One-shot", "condition_ineligible"),
    ],
)
def test_registry_authorization_fails_closed(
    tool_name: str,
    condition_id: str,
    error_code: str,
) -> None:
    registry = ToolRegistry([_descriptor()])

    with pytest.raises(ToolRegistryError, match=error_code):
        registry.authorize(
            tool_name,
            condition_id=condition_id,
            model_visible=True,
        )


def test_final_judge_shaped_descriptor_is_rejected_by_schema_and_registry() -> None:
    final_judge = _descriptor(
        tool_id="judge/evas-final-v1",
        tool_name="evas.final_judge",
        model_visibility="final_judge_only",
        budget_class="final_judge",
        state_effect="final_judgment",
        candidate_effect="judge",
        evidence_policy={
            "records_private_evidence": True,
            "may_enter_model_observation": False,
            "may_enter_shared_memory": False,
            "requires_candidate_binding": True,
        },
        handler_id="judge.evas.final",
    )

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(final_judge, _schema())
    with pytest.raises(ToolRegistryError, match="invalid_visibility"):
        ToolRegistry([final_judge])


def test_accepted_tool_names_are_syntax_not_authority() -> None:
    registry = ToolRegistry([_descriptor(allowed_conditions=["Agentic+EVAS"])])
    model_syntax_allowlist = frozenset({"bash", "evas.final_judge"})

    assert "evas.final_judge" in model_syntax_allowlist
    with pytest.raises(ToolRegistryError, match="final_judge_forbidden"):
        registry.authorize(
            "evas.final_judge",
            condition_id="Agentic+EVAS",
            model_visible=True,
        )


def test_effective_capability_hash_changes_with_resolved_contract() -> None:
    first = ToolRegistry([_descriptor()]).resolve(
        condition_id="Agentic+EVAS",
        model_visible=True,
    )
    changed = ToolRegistry([_descriptor(budget_class="public_validation")]).resolve(
        condition_id="Agentic+EVAS",
        model_visible=True,
    )

    assert first.effective_capability_sha256 != changed.effective_capability_sha256


@pytest.mark.parametrize(
    "updates",
    [
        {"state_effect": "read_only", "candidate_effect": "mutate"},
        {"state_effect": "candidate_mutation", "candidate_effect": "read"},
        {"state_effect": "terminal_submission", "candidate_effect": "mutate"},
        {
            "budget_class": "submission",
            "state_effect": "candidate_mutation",
            "candidate_effect": "mutate",
        },
        {
            "budget_class": "tool_call",
            "state_effect": "terminal_submission",
            "candidate_effect": "freeze",
        },
    ],
)
def test_registry_and_schema_reject_inconsistent_effect_contracts(
    updates: dict[str, str],
) -> None:
    descriptor = _descriptor(**updates)

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(descriptor, _schema())
    with pytest.raises(ToolRegistryError, match="inconsistent_effect_contract"):
        ToolRegistry([descriptor])


def test_registry_hash_includes_non_effective_descriptors() -> None:
    active = _descriptor()
    first_reserved = _descriptor(
        tool_id="domain/waveform-v1",
        tool_name="waveform.inspect",
        lifecycle="reserved",
        budget_class="reserved",
        state_effect="read_only",
        candidate_effect="read",
        handler_id=None,
    )
    changed_reserved = dict(first_reserved, tool_version="2")
    first = ToolRegistry([active, first_reserved])
    changed = ToolRegistry([active, changed_reserved])

    assert len(first.registry_sha256) == 64
    assert first.registry_sha256 != changed.registry_sha256
    assert first.resolve(
        condition_id="Agentic+EVAS",
        model_visible=True,
    ).effective_capability_sha256 == changed.resolve(
        condition_id="Agentic+EVAS",
        model_visible=True,
    ).effective_capability_sha256


def test_registry_deep_freezes_descriptor_inputs() -> None:
    descriptor = _descriptor()
    registry = ToolRegistry([descriptor])
    before = registry.resolve(condition_id="Agentic+EVAS", model_visible=True)
    descriptor["allowed_conditions"].clear()
    descriptor["argument_schema"]["required"].append("forged")
    descriptor["evidence_policy"]["may_enter_model_observation"] = False

    after = registry.resolve(condition_id="Agentic+EVAS", model_visible=True)
    authorized = registry.authorize(
        "bash",
        condition_id="Agentic+EVAS",
        model_visible=True,
    )

    assert before.effective_capability_sha256 == after.effective_capability_sha256
    assert authorized.argument_schema["required"] == ("command",)
    assert authorized.evidence_policy["may_enter_model_observation"]
    with pytest.raises(TypeError):
        authorized.argument_schema["required"] += ("forged",)


def test_registry_rejects_duplicate_tool_id_even_with_distinct_names() -> None:
    first = _descriptor(tool_id="shared/id-v1", tool_name="bash")
    second = _descriptor(tool_id="shared/id-v1", tool_name="public_validate")

    with pytest.raises(ToolRegistryError, match="duplicate_tool_id"):
        ToolRegistry([first, second])


@pytest.mark.parametrize("schema_field", ["argument_schema", "observation_schema"])
def test_tool_io_schema_root_must_be_object(schema_field: str) -> None:
    descriptor = _descriptor(**{schema_field: {"type": "array"}})

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(descriptor, _schema())


@pytest.mark.parametrize(
    ("updates", "error_code"),
    [
        ({"unexpected_field": True}, "unexpected_descriptor_fields"),
        ({"budget_class": "hidden_score"}, "invalid_budget_class"),
        ({"state_effect": "hidden_mutation"}, "invalid_state_effect"),
        ({"candidate_effect": "hidden_candidate"}, "invalid_candidate_effect"),
        (
            {
                "evidence_policy": {
                    "records_private_evidence": True,
                    "may_enter_model_observation": True,
                    "may_enter_shared_memory": False,
                }
            },
            "invalid_evidence_policy",
        ),
        (
            {
                "evidence_policy": {
                    "records_private_evidence": True,
                    "may_enter_model_observation": True,
                    "may_enter_shared_memory": False,
                    "requires_candidate_binding": True,
                    "extra": False,
                }
            },
            "invalid_evidence_policy",
        ),
        (
            {
                "evidence_policy": {
                    "records_private_evidence": True,
                    "may_enter_model_observation": "yes",
                    "may_enter_shared_memory": False,
                    "requires_candidate_binding": True,
                }
            },
            "invalid_evidence_policy",
        ),
        (
            {"allowed_conditions": ["Agentic+EVAS", "Agentic+EVAS"]},
            "duplicate_conditions",
        ),
        (
            {"allowed_conditions": ["*", "Agentic+EVAS"]},
            "ambiguous_conditions",
        ),
    ],
)
def test_registry_validates_descriptor_contract_at_runtime(
    updates: dict[str, Any],
    error_code: str,
) -> None:
    with pytest.raises(ToolRegistryError, match=error_code):
        ToolRegistry([_descriptor(**updates)])
