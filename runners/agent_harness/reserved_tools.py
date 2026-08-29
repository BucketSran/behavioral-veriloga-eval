"""Non-callable namespace markers for deferred vaEVAS domain tools."""

from __future__ import annotations

from typing import Any

_RESERVED_DOMAIN_TOOL_NAMES = (
    "vaevas.reserved.candidate",
    "vaevas.reserved.public_validation",
    "vaevas.reserved.retrieval",
    "vaevas.reserved.submission",
    "vaevas.reserved.waveform",
)


def reserved_domain_tool_descriptors() -> list[dict[str, Any]]:
    """Return fail-closed markers without granting model or dispatch authority."""
    return [_reserved_descriptor(tool_name) for tool_name in _RESERVED_DOMAIN_TOOL_NAMES]


def _reserved_descriptor(tool_name: str) -> dict[str, Any]:
    namespace = tool_name.removeprefix("vaevas.reserved.")
    return {
        "schema_version": "vaevas-tool-descriptor-v1",
        "tool_id": f"reserved/{namespace}-v1",
        "tool_name": tool_name,
        "tool_version": "1",
        "lifecycle": "reserved",
        "model_visibility": "harness_internal",
        "allowed_conditions": ["*"],
        "budget_class": "reserved",
        "state_effect": "read_only",
        "candidate_effect": "none",
        "argument_schema": {"type": "object", "additionalProperties": False},
        "observation_schema": {"type": "object", "additionalProperties": False},
        "evidence_policy": {
            "records_private_evidence": False,
            "may_enter_model_observation": False,
            "may_enter_shared_memory": False,
            "requires_candidate_binding": False,
        },
        "handler_id": None,
    }
