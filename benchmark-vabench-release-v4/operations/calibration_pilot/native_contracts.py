"""Static backend/tool declarations shared by launchers and evidence readers.

These describe allowed information surfaces, not observed information parity.
No model, environment or campaign is started while constructing a declaration.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from mini_swe_vabench import MINI_SWE_AGENT_VERSION
from submission_contract import submit_artifacts_tool_schema


def declared_information_surface(
    condition: str, *, evolution: bool = False, extensions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Disclose expected access, not observed image contents or a fairness proof."""
    return {
        "schema_version": "vaevas-declared-information-surface-v1",
        "evidence_kind": "declared_expected_policy",
        "logical_condition": condition,
        "generation_export_arm": "Agent-No-EVAS" if evolution else condition,
        "generation_bash_available": condition != "OneShot",
        "generation_evas_available": condition == "Agentic" and not evolution,
        "public_validation_access": (
            "coordinator_after_branch" if evolution else "in_episode" if condition == "Agentic" else "none"
        ),
        "extension_interventions": {
            name: profile["intervention"] for name, profile in sorted((extensions or {}).items())
        },
        "final_feedback_may_reenter_generation": False,
        "information_parity_established": False,
        "observed_image_audit": False,
        "uncontrolled_or_intentional_differences": [
            "condition_specific_prompt_and_tool_guidance",
            "installed_runtime_examples_may_differ",
            "model_backend_and_budget_require_separate_matching",
            "extensions_require_separate_comparison_protocol",
        ],
    }


def backend_profile(episode_backend="native-mini-swe", proposal_format="native_tool_calls"):
    if episode_backend not in {"native-mini-swe", "native-reasoning"}:
        raise ValueError("unsupported native backend")
    if proposal_format not in {"native_tool_calls", "strict_json"}:
        raise ValueError("unsupported proposal format")
    if episode_backend != "native-reasoning" and proposal_format != "native_tool_calls":
        raise ValueError("strict_json requires native-reasoning")
    profile = {
        "schema_version": "vaevas-backend-profile-v1",
        "backend_profile_id": "mini-swe/native-single-cell-v1",
        "backend_family": "mini_swe",
        "backend_version": MINI_SWE_AGENT_VERSION,
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
    if episode_backend == "native-reasoning":
        profile.update({
            "backend_profile_id": "alphaapollo/reasoning-single-cell-v1",
            "backend_family": "alphaapollo_reasoning", "backend_version": "1",
            "supported_proposal_formats": ["native_tool_calls", "strict_json"],
            "preferred_proposal_format": proposal_format,
        })
        profile["model_interface"]["supports_strict_json"] = True
    return profile


def submit_artifacts_tool_descriptor(runtime: Path) -> dict:
    schema = submit_artifacts_tool_schema(runtime)["function"]["parameters"]
    return {
        "schema_version": "vaevas-tool-descriptor-v1",
        "tool_id": "native/submit-artifacts-v1",
        "tool_name": "submit_artifacts",
        "tool_version": "1",
        "lifecycle": "active",
        "model_visibility": "model_visible",
        "allowed_conditions": ["OneShot"],
        "budget_class": "submission",
        "state_effect": "terminal_submission",
        "candidate_effect": "freeze",
        "argument_schema": schema,
        "observation_schema": {
            "type": "object",
            "properties": {"output": {"type": "string"}},
            "required": ["output"],
            "additionalProperties": False,
        },
        "evidence_policy": {
            "records_private_evidence": False,
            "may_enter_model_observation": True,
            "may_enter_shared_memory": False,
            "requires_candidate_binding": True,
        },
        "handler_id": "native.submit_artifacts",
    }
