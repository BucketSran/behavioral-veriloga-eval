from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from runners.agent_harness import backend_profile_sha256


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "vaevas-backend-profile-v1.schema.json"


def _profile(**updates: Any) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "schema_version": "vaevas-backend-profile-v1",
        "backend_profile_id": "mini-swe/bash-native-v1",
        "backend_family": "mini_swe",
        "backend_version": "1",
        "inference_mode": "single_trajectory",
        "supported_proposal_formats": ["native_tool_calls"],
        "preferred_proposal_format": "native_tool_calls",
        "action_schema_id": "vaevas-action-v1",
        "observation_schema_id": "vaevas-observation-v1",
        "proposal_normalizer_id": "vaevas-proposal-normalizer-v1",
        "model_interface": {
            "protocol": "openai_compatible_chat_completions",
            "supports_streaming": True,
            "supports_native_tool_calls": True,
            "supports_strict_json": False,
        },
        "state_scope": {
            "memory_scope": "episode_local",
            "shares_state_across_tasks": False,
            "shares_state_across_conditions": False,
        },
        "requires_campaign_contracts": [
            "model_identity",
            "decoding_policy",
            "turn_budget",
            "wall_time_budget",
            "condition_identity",
        ],
        "requires_environment_contracts": [
            "clean_room_runtime",
            "proposal_tool_allowlist",
            "trajectory_sink",
            "candidate_store",
            "submission_freeze",
            "final_judge",
        ],
    }
    profile.update(updates)
    return profile


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_minimal_mini_swe_backend_profile_is_valid_and_hashable() -> None:
    profile = _profile()

    jsonschema.validate(profile, _schema())
    assert len(backend_profile_sha256(profile)) == 64


def test_alphapollo_reasoning_backend_profile_uses_the_same_contract() -> None:
    profile = _profile(
        backend_profile_id="alphapollo/reasoning-v1",
        backend_family="alphapollo",
        supported_proposal_formats=["strict_json", "native_tool_calls"],
        preferred_proposal_format="strict_json",
        model_interface={
            "protocol": "local_or_api_chat",
            "supports_streaming": True,
            "supports_native_tool_calls": True,
            "supports_strict_json": True,
        },
    )

    jsonschema.validate(profile, _schema())


def test_alphapollo_evolution_profile_declares_external_evolution_contracts() -> None:
    campaign_contracts = [
        *_profile()["requires_campaign_contracts"],
        "evolution_roster",
        "evolution_round_budget",
        "feedback_scope",
        "selection_policy",
        "submission_policy",
    ]
    profile = _profile(
        backend_profile_id="alphapollo/evolution-v1",
        backend_family="alphapollo",
        inference_mode="round_based_evolution",
        requires_campaign_contracts=campaign_contracts,
    )

    jsonschema.validate(profile, _schema())


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("model", "provider/model"),
        ("base_url", "https://provider.invalid"),
        ("temperature", 0.2),
        ("per_turn_max_tokens", 4096),
        ("release", "r53"),
        ("condition", "reasoning"),
        ("rounds", 3),
        ("branch_fanout", 4),
        ("tools", ["bash"]),
        ("tool_descriptors", []),
        ("domain_tools", []),
        ("accepted_tool_names", ["bash"]),
    ],
)
def test_backend_profile_rejects_campaign_environment_and_tool_values(
    field_name: str,
    value: object,
) -> None:
    profile = _profile(**{field_name: value})

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(profile, _schema())


@pytest.mark.parametrize(
    "state_scope",
    [
        {
            "memory_scope": "global",
            "shares_state_across_tasks": False,
            "shares_state_across_conditions": False,
        },
        {
            "memory_scope": "episode_local",
            "shares_state_across_tasks": True,
            "shares_state_across_conditions": False,
        },
        {
            "memory_scope": "episode_local",
            "shares_state_across_tasks": False,
            "shares_state_across_conditions": True,
        },
    ],
)
def test_backend_profile_rejects_cross_cell_state(state_scope: object) -> None:
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_profile(state_scope=state_scope), _schema())


def test_preferred_proposal_format_must_be_supported_by_the_interface() -> None:
    profile = _profile(
        preferred_proposal_format="strict_json",
        model_interface={
            "protocol": "openai_compatible_chat_completions",
            "supports_streaming": True,
            "supports_native_tool_calls": True,
            "supports_strict_json": True,
        },
    )

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(profile, _schema())


def test_declared_proposal_format_requires_matching_interface_support() -> None:
    profile = _profile(
        model_interface={
            "protocol": "openai_compatible_chat_completions",
            "supports_streaming": True,
            "supports_native_tool_calls": False,
            "supports_strict_json": False,
        }
    )

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(profile, _schema())


def test_interface_support_cannot_exceed_declared_proposal_formats() -> None:
    profile = _profile(
        model_interface={
            "protocol": "openai_compatible_chat_completions",
            "supports_streaming": True,
            "supports_native_tool_calls": True,
            "supports_strict_json": True,
        }
    )

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(profile, _schema())


def test_evolution_profile_requires_all_external_evolution_contracts() -> None:
    profile = _profile(inference_mode="round_based_evolution")

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(profile, _schema())


def test_backend_profile_hash_is_order_stable_and_change_sensitive() -> None:
    profile = _profile()
    reordered = dict(reversed(list(profile.items())))
    changed = _profile(backend_version="2")

    assert backend_profile_sha256(profile) == backend_profile_sha256(reordered)
    assert backend_profile_sha256(profile) != backend_profile_sha256(changed)


@pytest.mark.parametrize(
    "profile",
    [
        {1: "non-string-key"},
        {"value": float("nan")},
        {"value": object()},
    ],
)
def test_backend_profile_hash_rejects_noncanonical_json(profile: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        backend_profile_sha256(profile)  # type: ignore[arg-type]
