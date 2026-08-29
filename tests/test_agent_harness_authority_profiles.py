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


def _schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _public_profile(**updates: Any) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "schema_version": "vaevas-public-validation-profile-v1",
        "profile_id": "r53/evas-0.8.7-public-validation",
        "benchmark_release": "benchmarkv4-r53",
        "evaluator": {"engine": "evas", "version": "0.8.7"},
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
        "judge": {"engine": "evas", "version": "0.8.7"},
        "authority_phase": "post_submission_freeze_only",
        "visibility": "trusted_only",
        "model_observation_allowed": False,
        "memory_entry_allowed": False,
        "candidate_selection_allowed": False,
        "repair_allowed": False,
        "input_scope": "frozen_submission_tree",
        "submission_binding_required": True,
        "score_sidecar_required": True,
        "spectre_policy": {
            "required": False,
            "trigger": "conditional_evas_or_external_protocol_change",
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


def test_final_test_profile_is_terminal_trusted_and_hashable() -> None:
    profile = _final_profile()

    jsonschema.validate(profile, _schema(FINAL_SCHEMA_PATH))

    assert len(final_test_profile_sha256(profile)) == 64
    assert final_test_profile_sha256(profile) == final_test_profile_sha256(
        dict(reversed(list(profile.items())))
    )


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
                }
            ),
            _schema(FINAL_SCHEMA_PATH),
        )


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
    replay = classify_final_replay_request(
        failure_kind="infrastructure_failure",
        frozen_submission_tree_sha256=SHA_A,
        previous_frozen_submission_tree_sha256=SHA_A,
        previous_judge_attempt_id="judge-attempt-1",
        judge_attempt_id="judge-attempt-2",
        model_reentry_requested=False,
    )

    assert replay == "allowed_infrastructure_replay"

    with pytest.raises(ValueError, match="same frozen submission"):
        classify_final_replay_request(
            failure_kind="infrastructure_failure",
            frozen_submission_tree_sha256=SHA_A,
            previous_frozen_submission_tree_sha256=SHA_B,
            previous_judge_attempt_id="judge-attempt-1",
            judge_attempt_id="judge-attempt-2",
            model_reentry_requested=False,
        )
    with pytest.raises(ValueError, match="new judge_attempt_id"):
        classify_final_replay_request(
            failure_kind="infrastructure_failure",
            frozen_submission_tree_sha256=SHA_A,
            previous_frozen_submission_tree_sha256=SHA_A,
            previous_judge_attempt_id="judge-attempt-1",
            judge_attempt_id="judge-attempt-1",
            model_reentry_requested=False,
        )
    with pytest.raises(ValueError, match="model reentry"):
        classify_final_replay_request(
            failure_kind="infrastructure_failure",
            frozen_submission_tree_sha256=SHA_A,
            previous_frozen_submission_tree_sha256=SHA_A,
            previous_judge_attempt_id="judge-attempt-1",
            judge_attempt_id="judge-attempt-2",
            model_reentry_requested=True,
        )
