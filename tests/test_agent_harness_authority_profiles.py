from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from runners.agent_harness.authority_profiles import (
    classify_final_replay_request,
    final_test_profile_sha256,
    profile_input_identity_sha256,
    public_validation_profile_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SCHEMA_PATH = ROOT / "schemas" / "vaevas-public-validation-profile-v1.schema.json"
FINAL_SCHEMA_PATH = ROOT / "schemas" / "vaevas-final-test-profile-v1.schema.json"
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64
SHA_F = "f" * 64
SHA_0 = "0" * 64


def _schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _public_profile(**updates: Any) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "schema_version": "vaevas-public-validation-profile-v1",
        "profile_id": "r53/evas-0.8.7-public-validation",
        "benchmark_release": "benchmarkv4-r53",
        "benchmark_manifest_sha256": SHA_A,
        "evaluator": {"engine": "evas", "version": "0.8.7"},
        "evaluator_identity_sha256": SHA_B,
        "checker_identity_sha256": SHA_C,
        "runtime_identity_sha256": SHA_D,
        "campaign_config_sha256": SHA_E,
        "authority_phase": "in_episode",
        "visibility": "model_observation",
        "memory_policy": "episode_local_public_only",
        "input_scope": "candidate_tree",
        "allowed_feedback": [
            "compile",
            "runtime",
            "metric",
            "log_excerpt",
            "waveform_summary",
        ],
        "candidate_binding_required": True,
        "may_select_candidates": True,
    }
    profile.update(updates)
    return profile


def _final_profile(**updates: Any) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "schema_version": "vaevas-final-test-profile-v1",
        "profile_id": "r53/evas-0.8.7-final-test",
        "benchmark_release": "benchmarkv4-r53",
        "benchmark_manifest_sha256": SHA_A,
        "judge": {"engine": "evas", "version": "0.8.7"},
        "judge_identity_sha256": SHA_B,
        "checker_identity_sha256": SHA_C,
        "runtime_identity_sha256": SHA_D,
        "campaign_config_sha256": SHA_E,
        "command_signature_sha256": SHA_F,
        "authority_phase": "post_submission_freeze_only",
        "visibility": "trusted_only",
        "model_observation_allowed": False,
        "memory_entry_allowed": False,
        "candidate_selection_allowed": False,
        "repair_allowed": False,
        "input_scope": "frozen_submission_tree",
        "submission_binding_required": True,
        "score_sidecar_required": True,
        "structured_result_contract": {
            "schema_id": "vaevas-structured-result-v1",
            "requires_structured_verdict": True,
        },
        "score_sidecar_contract": {
            "schema_id": "vaevas-score-sidecar-v1",
            "immutable": True,
            "binds_submission_tree": True,
        },
        "spectre_policy": {
            "required": False,
            "trigger": "conditional_evas_or_external_protocol_change",
            "spectre_judge_identity_sha256": None,
            "spectre_command_signature_sha256": None,
            "spectre_report_schema_id": None,
        },
    }
    profile.update(updates)
    return profile


def test_public_validation_profile_is_model_visible_and_hashable() -> None:
    profile = _public_profile()

    jsonschema.validate(profile, _schema(PUBLIC_SCHEMA_PATH))

    assert len(public_validation_profile_sha256(profile)) == 64
    assert public_validation_profile_sha256(profile) == public_validation_profile_sha256(
        dict(reversed(list(profile.items())))
    )
    assert profile["benchmark_release"] == "benchmarkv4-r53"
    assert profile["evaluator"] == {"engine": "evas", "version": "0.8.7"}


def test_final_test_profile_is_terminal_trusted_and_hashable() -> None:
    profile = _final_profile()

    jsonschema.validate(profile, _schema(FINAL_SCHEMA_PATH))

    assert len(final_test_profile_sha256(profile)) == 64
    assert final_test_profile_sha256(profile) == final_test_profile_sha256(
        dict(reversed(list(profile.items())))
    )
    assert profile["benchmark_release"] == "benchmarkv4-r53"
    assert profile["judge"] == {"engine": "evas", "version": "0.8.7"}


def test_authority_profile_schemas_are_generic_but_instances_pin_current_baseline() -> None:
    jsonschema.validate(
        _public_profile(
            benchmark_release="future-release",
            evaluator={"engine": "alternate-evaluator", "version": "1.2.3"},
        ),
        _schema(PUBLIC_SCHEMA_PATH),
    )
    jsonschema.validate(
        _final_profile(
            benchmark_release="future-release",
            judge={"engine": "alternate-judge", "version": "1.2.3"},
        ),
        _schema(FINAL_SCHEMA_PATH),
    )


@pytest.mark.parametrize(
    ("profile_factory", "field_name", "hash_fn"),
    [
        (_public_profile, "benchmark_manifest_sha256", public_validation_profile_sha256),
        (_public_profile, "evaluator_identity_sha256", public_validation_profile_sha256),
        (_public_profile, "checker_identity_sha256", public_validation_profile_sha256),
        (_public_profile, "runtime_identity_sha256", public_validation_profile_sha256),
        (_public_profile, "campaign_config_sha256", public_validation_profile_sha256),
        (_final_profile, "benchmark_manifest_sha256", final_test_profile_sha256),
        (_final_profile, "judge_identity_sha256", final_test_profile_sha256),
        (_final_profile, "checker_identity_sha256", final_test_profile_sha256),
        (_final_profile, "runtime_identity_sha256", final_test_profile_sha256),
        (_final_profile, "campaign_config_sha256", final_test_profile_sha256),
        (_final_profile, "command_signature_sha256", final_test_profile_sha256),
        (_final_profile, "structured_result_contract", final_test_profile_sha256),
        (_final_profile, "score_sidecar_contract", final_test_profile_sha256),
    ],
)
def test_runtime_profile_hashing_fails_closed_on_missing_contract_fields(
    profile_factory: Any,
    field_name: str,
    hash_fn: Any,
) -> None:
    profile = profile_factory()
    profile.pop(field_name)

    with pytest.raises(ValueError, match=field_name):
        hash_fn(profile)


@pytest.mark.parametrize(
    "updates",
    [
        {"visibility": "model_observation"},
        {"model_observation_allowed": True},
        {"memory_entry_allowed": True},
        {"candidate_selection_allowed": True},
        {"repair_allowed": True},
        {"authority_phase": "in_episode"},
    ],
)
def test_final_profile_rejects_leaky_or_adaptive_authority(
    updates: dict[str, object],
) -> None:
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_final_profile(**updates), _schema(FINAL_SCHEMA_PATH))


def test_spectre_is_conditional_not_routine_for_evas_0_8_7() -> None:
    jsonschema.validate(_final_profile(), _schema(FINAL_SCHEMA_PATH))

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _final_profile(
                spectre_policy={
                    "required": True,
                    "trigger": "routine_development_scoring",
                    "spectre_judge_identity_sha256": SHA_B,
                    "spectre_command_signature_sha256": SHA_F,
                    "spectre_report_schema_id": "spectre-parity-report-v1",
                }
            ),
            _schema(FINAL_SCHEMA_PATH),
        )
    with pytest.raises(ValueError, match="routine_development_scoring"):
        final_test_profile_sha256(
            _final_profile(
                spectre_policy={
                    "required": True,
                    "trigger": "routine_development_scoring",
                    "spectre_judge_identity_sha256": SHA_B,
                    "spectre_command_signature_sha256": SHA_F,
                    "spectre_report_schema_id": "spectre-parity-report-v1",
                }
            )
        )


def test_default_evas_final_profile_forbids_spectre_authority_bindings() -> None:
    profile = _final_profile(
        spectre_policy={
            "required": False,
            "trigger": "conditional_evas_or_external_protocol_change",
            "spectre_judge_identity_sha256": SHA_B,
            "spectre_command_signature_sha256": SHA_F,
            "spectre_report_schema_id": "spectre-parity-report-v1",
        }
    )

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(profile, _schema(FINAL_SCHEMA_PATH))
    with pytest.raises(ValueError, match="spectre_judge_identity_sha256"):
        final_test_profile_sha256(profile)


@pytest.mark.parametrize(
    "trigger",
    [
        "external_protocol_requires_spectre",
        "evas_abi_changed",
        "evas_compiler_changed",
        "evas_simulator_changed",
        "evas_package_changed",
    ],
)
def test_final_profile_allows_explicit_spectre_required_authority(trigger: str) -> None:
    profile = _final_profile(
        profile_id=f"r53/spectre-required/{trigger}",
        spectre_policy={
            "required": True,
            "trigger": trigger,
            "spectre_judge_identity_sha256": SHA_B,
            "spectre_command_signature_sha256": SHA_F,
            "spectre_report_schema_id": "spectre-parity-report-v1",
        },
    )

    jsonschema.validate(profile, _schema(FINAL_SCHEMA_PATH))

    assert len(final_test_profile_sha256(profile)) == 64


@pytest.mark.parametrize(
    "missing_field",
    [
        "spectre_judge_identity_sha256",
        "spectre_command_signature_sha256",
        "spectre_report_schema_id",
    ],
)
def test_spectre_required_profile_requires_parity_authority_bindings(
    missing_field: str,
) -> None:
    spectre_policy = {
        "required": True,
        "trigger": "external_protocol_requires_spectre",
        "spectre_judge_identity_sha256": SHA_B,
        "spectre_command_signature_sha256": SHA_F,
        "spectre_report_schema_id": "spectre-parity-report-v1",
    }
    spectre_policy.pop(missing_field)
    profile = _final_profile(spectre_policy=spectre_policy)

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(profile, _schema(FINAL_SCHEMA_PATH))
    with pytest.raises(ValueError, match=missing_field):
        final_test_profile_sha256(profile)


def test_profile_input_identity_binds_profile_and_candidate_or_submission() -> None:
    public_profile = _public_profile()
    final_profile = _final_profile()

    public_identity = profile_input_identity_sha256(
        profile_sha256=public_validation_profile_sha256(public_profile),
        input_kind="candidate_tree",
        input_sha256=SHA_A,
        attempt_id="attempt-1",
        task_id="v4-001",
    )
    final_identity = profile_input_identity_sha256(
        profile_sha256=final_test_profile_sha256(final_profile),
        input_kind="frozen_submission_tree",
        input_sha256=SHA_A,
        attempt_id="attempt-1",
        task_id="v4-001",
    )

    assert len(public_identity) == 64
    assert public_identity != final_identity
    assert public_identity != profile_input_identity_sha256(
        profile_sha256=public_validation_profile_sha256(public_profile),
        input_kind="candidate_tree",
        input_sha256=SHA_B,
        attempt_id="attempt-1",
        task_id="v4-001",
    )


def test_final_replay_retry_allows_only_infrastructure_replay_without_model_reentry() -> None:
    replay_kwargs: dict[str, Any] = {
        "failure_kind": "infrastructure_failure",
        "frozen_submission_tree_sha256": SHA_A,
        "previous_frozen_submission_tree_sha256": SHA_A,
        "final_profile_sha256": SHA_B,
        "previous_final_profile_sha256": SHA_B,
        "profile_input_identity_sha256": SHA_C,
        "previous_profile_input_identity_sha256": SHA_C,
        "judge_identity_sha256": SHA_D,
        "previous_judge_identity_sha256": SHA_D,
        "checker_identity_sha256": SHA_E,
        "previous_checker_identity_sha256": SHA_E,
        "runtime_identity_sha256": SHA_F,
        "previous_runtime_identity_sha256": SHA_F,
        "campaign_config_sha256": SHA_0,
        "previous_campaign_config_sha256": SHA_0,
        "command_signature_sha256": SHA_A,
        "previous_command_signature_sha256": SHA_A,
        "previous_judge_attempt_id": "judge-attempt-1",
        "judge_attempt_id": "judge-attempt-2",
        "model_reentry_requested": False,
    }
    replay = classify_final_replay_request(
        **replay_kwargs,
    )

    assert replay == "allowed_infrastructure_replay"

    with pytest.raises(ValueError, match="same frozen submission"):
        classify_final_replay_request(
            **(
                replay_kwargs
                | {
                    "frozen_submission_tree_sha256": SHA_A,
                    "previous_frozen_submission_tree_sha256": SHA_B,
                }
            ),
        )
    with pytest.raises(ValueError, match="same final profile"):
        classify_final_replay_request(
            **(
                replay_kwargs
                | {
                    "final_profile_sha256": SHA_A,
                    "previous_final_profile_sha256": SHA_B,
                }
            ),
        )
    with pytest.raises(ValueError, match="same profile input identity"):
        classify_final_replay_request(
            **(
                replay_kwargs
                | {
                    "profile_input_identity_sha256": SHA_A,
                    "previous_profile_input_identity_sha256": SHA_B,
                }
            ),
        )
    with pytest.raises(ValueError, match="same judge identity"):
        classify_final_replay_request(
            **(
                replay_kwargs
                | {
                    "judge_identity_sha256": SHA_A,
                    "previous_judge_identity_sha256": SHA_B,
                }
            ),
        )
    with pytest.raises(ValueError, match="same checker identity"):
        classify_final_replay_request(
            **(
                replay_kwargs
                | {
                    "checker_identity_sha256": SHA_A,
                    "previous_checker_identity_sha256": SHA_B,
                }
            ),
        )
    with pytest.raises(ValueError, match="same runtime identity"):
        classify_final_replay_request(
            **(
                replay_kwargs
                | {
                    "runtime_identity_sha256": SHA_A,
                    "previous_runtime_identity_sha256": SHA_B,
                }
            ),
        )
    with pytest.raises(ValueError, match="same campaign config"):
        classify_final_replay_request(
            **(
                replay_kwargs
                | {
                    "campaign_config_sha256": SHA_A,
                    "previous_campaign_config_sha256": SHA_B,
                }
            ),
        )
    with pytest.raises(ValueError, match="same command signature"):
        classify_final_replay_request(
            **(
                replay_kwargs
                | {
                    "command_signature_sha256": SHA_A,
                    "previous_command_signature_sha256": SHA_B,
                }
            ),
        )
    with pytest.raises(ValueError, match="new judge_attempt_id"):
        classify_final_replay_request(
            **(
                replay_kwargs
                | {
                    "previous_judge_attempt_id": "judge-attempt-1",
                    "judge_attempt_id": "judge-attempt-1",
                }
            ),
        )
    with pytest.raises(ValueError, match="model reentry"):
        classify_final_replay_request(
            **(replay_kwargs | {"model_reentry_requested": True}),
        )
