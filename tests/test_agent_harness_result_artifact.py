from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from runners.agent_harness import (
    EpisodeContext,
    EpisodeResult,
    FinalJudgment,
    FrozenSubmission,
    JsonlTrajectoryRecorder,
    build_scored_result_artifact,
    read_trajectory,
    result_artifact_sha256,
    validate_scored_result_artifact,
)


ROOT = Path(__file__).resolve().parents[1]
RESULT_SCHEMA_PATH = ROOT / "schemas" / "vaevas-result-artifact-v1.schema.json"
SIDECAR_SCHEMA_PATH = ROOT / "schemas" / "vaevas-score-sidecar-v1.schema.json"
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64
SHA_F = "f" * 64


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
        "allowed_feedback": ["compile", "runtime", "metric"],
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
            "score_authority": "development_only",
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


def _context() -> EpisodeContext:
    return EpisodeContext(
        episode_id="episode-001",
        attempt_id="attempt-001",
        task_id="v4-001",
        condition="Agentic+EVAS",
        max_steps=4,
    )


def _trajectory(tmp_path, *, final_visibility: str = "trusted"):
    path = tmp_path / "trajectory.jsonl"
    recorder = JsonlTrajectoryRecorder(path)
    context = _context()
    for actor, event_type, visibility, payload in (
        ("controller", "episode_started", "harness", {}),
        (
            "environment",
            "submission_frozen",
            "harness",
            {"tree_sha256": SHA_A, "artifacts": ["model.va"]},
        ),
        (
            "final_judge",
            "final_judgment_completed",
            final_visibility,
            {
                "status": "passed",
                "judge_engine": "evas",
                "score": 1.0,
                "submission_tree_sha256": SHA_A,
            },
        ),
        ("environment", "cleanup_completed", "harness", {}),
        (
            "controller",
            "episode_completed",
            "harness",
            {"primary_outcome": "passed", "terminal_reason": "submitted"},
        ),
    ):
        recorder.append(
            context=context,
            actor=actor,
            event_type=event_type,
            visibility=visibility,  # type: ignore[arg-type]
            payload=payload,
        )
    return read_trajectory(path)


def _result(events) -> EpisodeResult:
    return EpisodeResult(
        context=_context(),
        primary_outcome="passed",
        terminal_reason="submitted",
        submission=FrozenSubmission(
            tree_sha256=SHA_A,
            artifacts=("model.va",),
        ),
        final_judgment=FinalJudgment(
            status="passed",
            judge_engine="evas",
            score=1.0,
            submission_tree_sha256=SHA_A,
        ),
        incidents=(),
        trajectory_tail_sha256=events[-1]["event_sha256"],
    )


def _sidecar(**updates: Any) -> dict[str, Any]:
    sidecar: dict[str, Any] = {
        "schema_version": "vaevas-score-sidecar-v1",
        "benchmark_release": "benchmarkv4-r53",
        "benchmark_manifest_sha256": SHA_A,
        "score_authority": "development_only",
        "immutable": True,
        "binds_submission_tree": True,
        "submission_tree_sha256": SHA_A,
        "judge": {
            "engine": "evas",
            "version": "0.8.7",
            "identity_sha256": SHA_B,
        },
        "checker_identity_sha256": SHA_C,
        "runtime_identity_sha256": SHA_D,
        "campaign_config_sha256": SHA_E,
        "command_signature_sha256": SHA_F,
        "structured_result": {"status": "passed", "score": 1.0},
        "model_observation_allowed": False,
        "memory_entry_allowed": False,
    }
    sidecar.update(updates)
    return sidecar


def _build(events, **updates):
    arguments = {
        "result": _result(events),
        "trajectory_events": events,
        "backend_profile_sha256": SHA_A,
        "registry_sha256": SHA_B,
        "effective_capability_sha256": SHA_C,
        "public_validation_profile": _public_profile(),
        "final_test_profile": _final_profile(),
        "score_sidecar": _sidecar(),
    }
    arguments.update(updates)
    return build_scored_result_artifact(**arguments)


def test_scored_result_artifact_binds_all_terminal_evidence(tmp_path) -> None:
    events = _trajectory(tmp_path)
    sidecar = _sidecar()
    artifact = _build(events, score_sidecar=sidecar)

    jsonschema.validate(
        sidecar,
        json.loads(SIDECAR_SCHEMA_PATH.read_text(encoding="utf-8")),
    )
    jsonschema.validate(
        artifact,
        json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8")),
    )
    assert validate_scored_result_artifact(
        artifact,
        trajectory_events=events,
        score_sidecar=sidecar,
        public_validation_profile=_public_profile(),
        final_test_profile=_final_profile(),
    )
    assert artifact["episode"]["attempt_id"] == "attempt-001"
    assert artifact["submission"]["tree_sha256"] == SHA_A
    assert artifact["score_sidecar"]["score_authority"] == "development_only"
    assert len(artifact["artifact_sha256"]) == 64


def test_result_artifact_hash_is_canonical_across_sidecar_key_order(tmp_path) -> None:
    events = _trajectory(tmp_path)
    ordered = _build(events, score_sidecar=_sidecar())
    reordered = _build(
        events,
        score_sidecar=dict(reversed(list(_sidecar().items()))),
    )

    assert ordered["artifact_sha256"] == reordered["artifact_sha256"]


@pytest.mark.parametrize(
    "sidecar_updates",
    [
        {"submission_tree_sha256": SHA_B},
        {"model_observation_allowed": True},
        {"memory_entry_allowed": True},
        {"immutable": False},
    ],
)
def test_builder_rejects_untrusted_or_unbound_sidecar(
    tmp_path,
    sidecar_updates,
) -> None:
    events = _trajectory(tmp_path)

    with pytest.raises(ValueError):
        _build(events, score_sidecar=_sidecar(**sidecar_updates))


def test_builder_rejects_sidecar_schema_not_bound_by_final_profile(tmp_path) -> None:
    events = _trajectory(tmp_path)
    profile = _final_profile(
        score_sidecar_contract={
            "schema_id": "future-score-sidecar-v2",
            "immutable": True,
            "binds_submission_tree": True,
            "score_authority": "development_only",
        }
    )

    with pytest.raises(ValueError, match="score sidecar schema"):
        _build(events, final_test_profile=profile)


def test_builder_rejects_overstated_score_authority(tmp_path) -> None:
    events = _trajectory(tmp_path)

    with pytest.raises(ValueError, match="score_authority"):
        _build(events, score_sidecar=_sidecar(score_authority="formal"))


def test_builder_rejects_model_visible_final_judgment(tmp_path) -> None:
    events = _trajectory(tmp_path, final_visibility="model")

    with pytest.raises(ValueError, match="trajectory"):
        _build(events)


def test_builder_rejects_non_scored_episode(tmp_path) -> None:
    events = _trajectory(tmp_path)
    result = _result(events)
    failed = EpisodeResult(
        context=result.context,
        primary_outcome="protocol_failure",
        terminal_reason="protocol_failure",
        submission=None,
        final_judgment=None,
        incidents=(),
        failure=None,
        trajectory_tail_sha256=result.trajectory_tail_sha256,
    )

    with pytest.raises(ValueError, match="scored terminal episode"):
        _build(events, result=failed)


def test_validator_rejects_rehashed_semantic_tamper(tmp_path) -> None:
    events = _trajectory(tmp_path)
    sidecar = _sidecar()
    artifact = _build(events, score_sidecar=sidecar)
    tampered = deepcopy(artifact)
    tampered["final_judgment"]["status"] = "behavior_failure"
    tampered["artifact_sha256"] = result_artifact_sha256(tampered)

    assert not validate_scored_result_artifact(
        tampered,
        trajectory_events=events,
        score_sidecar=sidecar,
        public_validation_profile=_public_profile(),
        final_test_profile=_final_profile(),
    )


def test_validator_rejects_sidecar_document_hash_mismatch(tmp_path) -> None:
    events = _trajectory(tmp_path)
    sidecar = _sidecar()
    artifact = _build(events, score_sidecar=sidecar)
    changed_sidecar = deepcopy(sidecar)
    changed_sidecar["structured_result"]["score"] = 0.0

    assert not validate_scored_result_artifact(
        artifact,
        trajectory_events=events,
        score_sidecar=changed_sidecar,
        public_validation_profile=_public_profile(),
        final_test_profile=_final_profile(),
    )


def test_validator_rejects_authority_profile_substitution(tmp_path) -> None:
    events = _trajectory(tmp_path)
    sidecar = _sidecar()
    artifact = _build(events, score_sidecar=sidecar)
    substituted_final_profile = _final_profile(judge_identity_sha256="0" * 64)

    assert not validate_scored_result_artifact(
        artifact,
        trajectory_events=events,
        score_sidecar=sidecar,
        public_validation_profile=_public_profile(),
        final_test_profile=substituted_final_profile,
    )
