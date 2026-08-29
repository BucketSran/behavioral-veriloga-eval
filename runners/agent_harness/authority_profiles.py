"""Authority profile hashing and replay guards for vaEVAS evaluation."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any, Literal

InputKind = Literal["candidate_tree", "frozen_submission_tree"]

_PUBLIC_PROFILE_FIELDS = {
    "schema_version",
    "profile_id",
    "benchmark_release",
    "benchmark_manifest_sha256",
    "evaluator",
    "evaluator_identity_sha256",
    "checker_identity_sha256",
    "runtime_identity_sha256",
    "campaign_config_sha256",
    "authority_phase",
    "visibility",
    "memory_policy",
    "input_scope",
    "allowed_feedback",
    "candidate_binding_required",
    "may_select_candidates",
}
_FINAL_PROFILE_FIELDS = {
    "schema_version",
    "profile_id",
    "benchmark_release",
    "benchmark_manifest_sha256",
    "judge",
    "judge_identity_sha256",
    "checker_identity_sha256",
    "runtime_identity_sha256",
    "campaign_config_sha256",
    "command_signature_sha256",
    "authority_phase",
    "visibility",
    "model_observation_allowed",
    "memory_entry_allowed",
    "candidate_selection_allowed",
    "repair_allowed",
    "input_scope",
    "submission_binding_required",
    "score_sidecar_required",
    "structured_result_contract",
    "score_sidecar_contract",
    "spectre_policy",
}
_PUBLIC_FEEDBACK_KINDS = {
    "compile",
    "runtime",
    "metric",
    "log_excerpt",
    "waveform_summary",
}
_SPECTRE_REQUIRED_TRIGGERS = {
    "external_protocol_requires_spectre",
    "evas_abi_changed",
    "evas_compiler_changed",
    "evas_simulator_changed",
    "evas_package_changed",
}
_SPECTRE_POLICY_FIELDS = {
    "required",
    "trigger",
    "spectre_judge_identity_sha256",
    "spectre_command_signature_sha256",
    "spectre_report_schema_id",
}


def public_validation_profile_sha256(profile: Mapping[str, Any]) -> str:
    """Hash one public validation authority profile."""
    _validate_public_validation_profile(profile)
    return _canonical_profile_sha256(profile)


def final_test_profile_sha256(profile: Mapping[str, Any]) -> str:
    """Hash one final trusted replay authority profile."""
    _validate_final_test_profile(profile)
    return _canonical_profile_sha256(profile)


def profile_input_identity_sha256(
    *,
    profile_sha256: str,
    input_kind: InputKind,
    input_sha256: str,
    attempt_id: str,
    task_id: str,
) -> str:
    """Bind an authority profile to the exact candidate/submission input."""
    _require_sha256(profile_sha256, field_name="profile_sha256")
    _require_sha256(input_sha256, field_name="input_sha256")
    if input_kind not in {"candidate_tree", "frozen_submission_tree"}:
        raise ValueError("unsupported input_kind")
    _require_nonempty(attempt_id, field_name="attempt_id")
    _require_nonempty(task_id, field_name="task_id")
    return _canonical_sha256(
        {
            "schema_version": "vaevas-profile-input-identity-v1",
            "profile_sha256": profile_sha256,
            "input_kind": input_kind,
            "input_sha256": input_sha256,
            "attempt_id": attempt_id,
            "task_id": task_id,
        }
    )


def classify_final_replay_request(
    *,
    failure_kind: str,
    frozen_submission_tree_sha256: str,
    previous_frozen_submission_tree_sha256: str,
    final_profile_sha256: str,
    previous_final_profile_sha256: str,
    profile_input_identity_sha256: str,
    previous_profile_input_identity_sha256: str,
    judge_identity_sha256: str,
    previous_judge_identity_sha256: str,
    checker_identity_sha256: str,
    previous_checker_identity_sha256: str,
    runtime_identity_sha256: str,
    previous_runtime_identity_sha256: str,
    campaign_config_sha256: str,
    previous_campaign_config_sha256: str,
    command_signature_sha256: str,
    previous_command_signature_sha256: str,
    previous_judge_attempt_id: str,
    judge_attempt_id: str,
    model_reentry_requested: bool,
) -> str:
    """Validate whether a final replay is an infrastructure-only retry."""
    _require_nonempty(failure_kind, field_name="failure_kind")
    _require_sha256(
        frozen_submission_tree_sha256,
        field_name="frozen_submission_tree_sha256",
    )
    _require_sha256(
        previous_frozen_submission_tree_sha256,
        field_name="previous_frozen_submission_tree_sha256",
    )
    _require_sha256(final_profile_sha256, field_name="final_profile_sha256")
    _require_sha256(
        previous_final_profile_sha256,
        field_name="previous_final_profile_sha256",
    )
    _require_sha256(
        profile_input_identity_sha256,
        field_name="profile_input_identity_sha256",
    )
    _require_sha256(
        previous_profile_input_identity_sha256,
        field_name="previous_profile_input_identity_sha256",
    )
    _require_sha256(judge_identity_sha256, field_name="judge_identity_sha256")
    _require_sha256(
        previous_judge_identity_sha256,
        field_name="previous_judge_identity_sha256",
    )
    _require_sha256(checker_identity_sha256, field_name="checker_identity_sha256")
    _require_sha256(
        previous_checker_identity_sha256,
        field_name="previous_checker_identity_sha256",
    )
    _require_sha256(runtime_identity_sha256, field_name="runtime_identity_sha256")
    _require_sha256(
        previous_runtime_identity_sha256,
        field_name="previous_runtime_identity_sha256",
    )
    _require_sha256(campaign_config_sha256, field_name="campaign_config_sha256")
    _require_sha256(
        previous_campaign_config_sha256,
        field_name="previous_campaign_config_sha256",
    )
    _require_sha256(command_signature_sha256, field_name="command_signature_sha256")
    _require_sha256(
        previous_command_signature_sha256,
        field_name="previous_command_signature_sha256",
    )
    _require_nonempty(previous_judge_attempt_id, field_name="previous_judge_attempt_id")
    _require_nonempty(judge_attempt_id, field_name="judge_attempt_id")
    if failure_kind != "infrastructure_failure":
        raise ValueError("final replay is allowed only for infrastructure_failure")
    if frozen_submission_tree_sha256 != previous_frozen_submission_tree_sha256:
        raise ValueError("final replay must use the same frozen submission")
    if final_profile_sha256 != previous_final_profile_sha256:
        raise ValueError("final replay must use the same final profile")
    if profile_input_identity_sha256 != previous_profile_input_identity_sha256:
        raise ValueError("final replay must use the same profile input identity")
    if judge_identity_sha256 != previous_judge_identity_sha256:
        raise ValueError("final replay must use the same judge identity")
    if checker_identity_sha256 != previous_checker_identity_sha256:
        raise ValueError("final replay must use the same checker identity")
    if runtime_identity_sha256 != previous_runtime_identity_sha256:
        raise ValueError("final replay must use the same runtime identity")
    if campaign_config_sha256 != previous_campaign_config_sha256:
        raise ValueError("final replay must use the same campaign config")
    if command_signature_sha256 != previous_command_signature_sha256:
        raise ValueError("final replay must use the same command signature")
    if judge_attempt_id == previous_judge_attempt_id:
        raise ValueError("final replay requires a new judge_attempt_id")
    if model_reentry_requested:
        raise ValueError("final replay forbids model reentry")
    return "allowed_infrastructure_replay"


def _validate_public_validation_profile(profile: Mapping[str, Any]) -> None:
    _require_mapping(profile, field_name="profile")
    _require_exact_fields(profile, _PUBLIC_PROFILE_FIELDS, field_name="profile")
    _require_const(
        profile["schema_version"],
        "vaevas-public-validation-profile-v1",
        field_name="schema_version",
    )
    _require_nonempty(profile["profile_id"], field_name="profile_id")
    _require_nonempty(profile["benchmark_release"], field_name="benchmark_release")
    _require_sha256(
        profile["benchmark_manifest_sha256"],
        field_name="benchmark_manifest_sha256",
    )
    _require_engine_version(profile["evaluator"], field_name="evaluator")
    _require_sha256(
        profile["evaluator_identity_sha256"],
        field_name="evaluator_identity_sha256",
    )
    _require_sha256(
        profile["checker_identity_sha256"],
        field_name="checker_identity_sha256",
    )
    _require_sha256(
        profile["runtime_identity_sha256"],
        field_name="runtime_identity_sha256",
    )
    _require_sha256(
        profile["campaign_config_sha256"],
        field_name="campaign_config_sha256",
    )
    _require_const(profile["authority_phase"], "in_episode", field_name="authority_phase")
    _require_const(profile["visibility"], "model_observation", field_name="visibility")
    _require_const(
        profile["memory_policy"],
        "episode_local_public_only",
        field_name="memory_policy",
    )
    _require_const(profile["input_scope"], "candidate_tree", field_name="input_scope")
    _require_feedback_kinds(profile["allowed_feedback"])
    _require_const(
        profile["candidate_binding_required"],
        True,
        field_name="candidate_binding_required",
    )
    _require_const(profile["may_select_candidates"], True, field_name="may_select_candidates")


def _validate_final_test_profile(profile: Mapping[str, Any]) -> None:
    _require_mapping(profile, field_name="profile")
    _require_exact_fields(profile, _FINAL_PROFILE_FIELDS, field_name="profile")
    _require_const(
        profile["schema_version"],
        "vaevas-final-test-profile-v1",
        field_name="schema_version",
    )
    _require_nonempty(profile["profile_id"], field_name="profile_id")
    _require_nonempty(profile["benchmark_release"], field_name="benchmark_release")
    _require_sha256(
        profile["benchmark_manifest_sha256"],
        field_name="benchmark_manifest_sha256",
    )
    _require_engine_version(profile["judge"], field_name="judge")
    _require_sha256(profile["judge_identity_sha256"], field_name="judge_identity_sha256")
    _require_sha256(
        profile["checker_identity_sha256"],
        field_name="checker_identity_sha256",
    )
    _require_sha256(
        profile["runtime_identity_sha256"],
        field_name="runtime_identity_sha256",
    )
    _require_sha256(
        profile["campaign_config_sha256"],
        field_name="campaign_config_sha256",
    )
    _require_sha256(
        profile["command_signature_sha256"],
        field_name="command_signature_sha256",
    )
    _require_const(
        profile["authority_phase"],
        "post_submission_freeze_only",
        field_name="authority_phase",
    )
    _require_const(profile["visibility"], "trusted_only", field_name="visibility")
    _require_const(
        profile["model_observation_allowed"],
        False,
        field_name="model_observation_allowed",
    )
    _require_const(
        profile["memory_entry_allowed"],
        False,
        field_name="memory_entry_allowed",
    )
    _require_const(
        profile["candidate_selection_allowed"],
        False,
        field_name="candidate_selection_allowed",
    )
    _require_const(profile["repair_allowed"], False, field_name="repair_allowed")
    _require_const(
        profile["input_scope"],
        "frozen_submission_tree",
        field_name="input_scope",
    )
    _require_const(
        profile["submission_binding_required"],
        True,
        field_name="submission_binding_required",
    )
    _require_const(
        profile["score_sidecar_required"],
        True,
        field_name="score_sidecar_required",
    )
    _require_structured_result_contract(profile["structured_result_contract"])
    _require_score_sidecar_contract(profile["score_sidecar_contract"])
    _require_spectre_policy(profile["spectre_policy"])


def _require_mapping(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a JSON object")
    return value


def _require_exact_fields(
    value: Mapping[str, Any],
    expected_fields: set[str],
    *,
    field_name: str,
) -> None:
    missing = expected_fields - set(value)
    if missing:
        raise ValueError(f"{field_name} missing required field: {min(missing)}")
    unexpected = set(value) - expected_fields
    if unexpected:
        raise ValueError(f"{field_name} has unexpected field: {min(unexpected)}")


def _require_const(value: Any, expected: Any, *, field_name: str) -> None:
    if value != expected:
        raise ValueError(f"{field_name} must be {expected!r}")


def _require_engine_version(value: Any, *, field_name: str) -> None:
    engine_version = _require_mapping(value, field_name=field_name)
    _require_exact_fields(
        engine_version,
        {"engine", "version"},
        field_name=field_name,
    )
    _require_nonempty(engine_version["engine"], field_name=f"{field_name}.engine")
    _require_nonempty(engine_version["version"], field_name=f"{field_name}.version")


def _require_feedback_kinds(value: Any) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TypeError("allowed_feedback must be an array")
    if not value:
        raise ValueError("allowed_feedback must be non-empty")
    seen: set[str] = set()
    for item in value:
        if item not in _PUBLIC_FEEDBACK_KINDS:
            raise ValueError(f"allowed_feedback contains unsupported kind: {item!r}")
        if item in seen:
            raise ValueError(f"allowed_feedback contains duplicate kind: {item!r}")
        seen.add(item)


def _require_structured_result_contract(value: Any) -> None:
    contract = _require_mapping(value, field_name="structured_result_contract")
    _require_exact_fields(
        contract,
        {"schema_id", "requires_structured_verdict"},
        field_name="structured_result_contract",
    )
    _require_nonempty(
        contract["schema_id"],
        field_name="structured_result_contract.schema_id",
    )
    _require_const(
        contract["requires_structured_verdict"],
        True,
        field_name="structured_result_contract.requires_structured_verdict",
    )


def _require_score_sidecar_contract(value: Any) -> None:
    contract = _require_mapping(value, field_name="score_sidecar_contract")
    _require_exact_fields(
        contract,
        {"schema_id", "immutable", "binds_submission_tree"},
        field_name="score_sidecar_contract",
    )
    _require_nonempty(
        contract["schema_id"],
        field_name="score_sidecar_contract.schema_id",
    )
    _require_const(
        contract["immutable"],
        True,
        field_name="score_sidecar_contract.immutable",
    )
    _require_const(
        contract["binds_submission_tree"],
        True,
        field_name="score_sidecar_contract.binds_submission_tree",
    )


def _require_spectre_policy(value: Any) -> None:
    policy = _require_mapping(value, field_name="spectre_policy")
    _require_exact_fields(policy, _SPECTRE_POLICY_FIELDS, field_name="spectre_policy")
    required = policy["required"]
    trigger = policy["trigger"]
    if required is False and trigger == "conditional_evas_or_external_protocol_change":
        _require_const(
            policy["spectre_judge_identity_sha256"],
            None,
            field_name="spectre_judge_identity_sha256",
        )
        _require_const(
            policy["spectre_command_signature_sha256"],
            None,
            field_name="spectre_command_signature_sha256",
        )
        _require_const(
            policy["spectre_report_schema_id"],
            None,
            field_name="spectre_report_schema_id",
        )
        return
    if required is True and trigger in _SPECTRE_REQUIRED_TRIGGERS:
        _require_sha256(
            policy["spectre_judge_identity_sha256"],
            field_name="spectre_judge_identity_sha256",
        )
        _require_sha256(
            policy["spectre_command_signature_sha256"],
            field_name="spectre_command_signature_sha256",
        )
        _require_nonempty(
            policy["spectre_report_schema_id"],
            field_name="spectre_report_schema_id",
        )
        return
    raise ValueError(
        "spectre_policy permits only conditional EVAS scoring or explicit Spectre "
        f"change triggers, got required={required!r}, trigger={trigger!r}"
    )


def _canonical_profile_sha256(profile: Mapping[str, Any]) -> str:
    if not isinstance(profile, Mapping):
        raise TypeError("profile must be a JSON object")
    _require_canonical_json(profile)
    return _canonical_sha256(profile)


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _require_canonical_json(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("JSON object keys must be strings")
            _require_canonical_json(item)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            _require_canonical_json(item)
        return
    if value is None or isinstance(value, (str, int, bool)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        return
    raise TypeError(f"value is not JSON-compatible: {type(value).__name__}")


def _require_nonempty(value: str, *, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be non-empty")


def _require_sha256(value: str, *, field_name: str) -> None:
    _require_nonempty(value, field_name=field_name)
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
