"""Immutable join from a scored trajectory to its trusted score sidecar."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from typing import Any

from .authority_profiles import (
    final_test_profile_sha256,
    profile_input_identity_sha256,
    public_validation_profile_sha256,
)
from .state import EpisodeResult, FinalJudgment, FrozenSubmission
from .trajectory import validate_trajectory_semantics


_ARTIFACT_FIELDS = {
    "schema_version",
    "episode",
    "contract_identity",
    "trajectory",
    "submission",
    "final_judgment",
    "score_sidecar",
    "artifact_sha256",
}
_SIDECAR_FIELDS = {
    "schema_version",
    "benchmark_release",
    "benchmark_manifest_sha256",
    "score_authority",
    "immutable",
    "binds_submission_tree",
    "submission_tree_sha256",
    "judge",
    "checker_identity_sha256",
    "runtime_identity_sha256",
    "campaign_config_sha256",
    "command_signature_sha256",
    "structured_result",
    "model_observation_allowed",
    "memory_entry_allowed",
}


def result_artifact_sha256(artifact: Mapping[str, Any]) -> str:
    """Hash one artifact without trusting its recorded self-hash."""
    document = _require_mapping(artifact, field_name="result artifact")
    unhashed = dict(document)
    unhashed.pop("artifact_sha256", None)
    return _canonical_sha256(unhashed)


def score_sidecar_sha256(score_sidecar: Mapping[str, Any]) -> str:
    """Validate and hash one immutable score sidecar document."""
    return _canonical_sha256(_validate_score_sidecar(score_sidecar))


def validate_score_sidecar_authority(
    *,
    score_sidecar: Mapping[str, Any],
    final_test_profile: Mapping[str, Any],
    judgment: FinalJudgment,
    submission: FrozenSubmission,
) -> Mapping[str, Any]:
    """Validate a sidecar against one frozen submission and final profile."""
    if not isinstance(judgment, FinalJudgment):
        raise TypeError("judgment must be a FinalJudgment")
    if not isinstance(submission, FrozenSubmission):
        raise TypeError("submission must be a FrozenSubmission")
    final_test_profile_sha256(final_test_profile)
    if judgment.submission_tree_sha256 != submission.tree_sha256:
        raise ValueError("final judgment is not bound to the frozen submission")
    sidecar = _validate_score_sidecar(score_sidecar)
    _validate_sidecar_authority(
        sidecar=sidecar,
        final_profile=final_test_profile,
        judgment_status=judgment.status,
        judgment_engine=judgment.judge_engine,
        judgment_score=judgment.score,
        submission_tree_sha256=submission.tree_sha256,
    )
    return sidecar


def build_scored_result_artifact(
    *,
    result: EpisodeResult,
    trajectory_events: list[dict[str, Any]],
    backend_profile_sha256: str,
    registry_sha256: str,
    effective_capability_sha256: str,
    public_validation_profile: Mapping[str, Any],
    final_test_profile: Mapping[str, Any],
    score_sidecar: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a content-addressed artifact for one terminal scored episode."""
    if not isinstance(result, EpisodeResult):
        raise TypeError("result must be an EpisodeResult")
    if (
        result.submission is None
        or result.final_judgment is None
        or result.trajectory_tail_sha256 is None
        or result.failure is not None
    ):
        raise ValueError("result must be a scored terminal episode")
    _require_sha256(backend_profile_sha256, field_name="backend_profile_sha256")
    _require_sha256(registry_sha256, field_name="registry_sha256")
    _require_sha256(
        effective_capability_sha256,
        field_name="effective_capability_sha256",
    )
    public_profile_sha256 = public_validation_profile_sha256(
        public_validation_profile
    )
    final_profile_sha256 = final_test_profile_sha256(final_test_profile)
    for field_name in (
        "benchmark_release",
        "benchmark_manifest_sha256",
        "campaign_config_sha256",
    ):
        if public_validation_profile[field_name] != final_test_profile[field_name]:
            raise ValueError(
                f"public and final authority disagree on {field_name}"
            )
    submission = result.submission
    judgment = result.final_judgment
    if result.primary_outcome != judgment.status:
        raise ValueError("episode outcome does not match final judgment")
    if result.terminal_reason != "submitted":
        raise ValueError("scored episode must terminate through submission")
    sidecar = validate_score_sidecar_authority(
        score_sidecar=score_sidecar,
        final_test_profile=final_test_profile,
        judgment=judgment,
        submission=submission,
    )
    final_input_sha256 = profile_input_identity_sha256(
        profile_sha256=final_profile_sha256,
        input_kind="frozen_submission_tree",
        input_sha256=submission.tree_sha256,
        attempt_id=result.context.attempt_id,
        task_id=result.context.task_id,
    )
    artifact: dict[str, Any] = {
        "schema_version": "vaevas-result-artifact-v1",
        "episode": {
            "episode_id": result.context.episode_id,
            "attempt_id": result.context.attempt_id,
            "task_id": result.context.task_id,
            "condition": result.context.condition,
            "primary_outcome": result.primary_outcome,
            "terminal_reason": result.terminal_reason,
            "incidents": [
                {"category": row.category, "message": row.message}
                for row in result.incidents
            ],
        },
        "contract_identity": {
            "backend_profile_sha256": backend_profile_sha256,
            "registry_sha256": registry_sha256,
            "effective_capability_sha256": effective_capability_sha256,
            "public_validation_profile_sha256": public_profile_sha256,
            "final_test_profile_sha256": final_profile_sha256,
            "final_profile_input_identity_sha256": final_input_sha256,
        },
        "trajectory": {"tail_sha256": result.trajectory_tail_sha256},
        "submission": {
            "tree_sha256": submission.tree_sha256,
            "artifacts": list(submission.artifacts),
        },
        "final_judgment": {
            "status": judgment.status,
            "judge_engine": judgment.judge_engine,
            "score": judgment.score,
            "submission_tree_sha256": judgment.submission_tree_sha256,
        },
        "score_sidecar": {
            "schema_id": sidecar["schema_version"],
            "sha256": _canonical_sha256(sidecar),
            "immutable": sidecar["immutable"],
            "submission_tree_sha256": sidecar["submission_tree_sha256"],
            "score_authority": sidecar["score_authority"],
        },
    }
    artifact["artifact_sha256"] = result_artifact_sha256(artifact)
    if not validate_scored_result_artifact(
        artifact,
        trajectory_events=trajectory_events,
        score_sidecar=sidecar,
        public_validation_profile=public_validation_profile,
        final_test_profile=final_test_profile,
    ):
        raise ValueError("result artifact does not match terminal trajectory")
    return artifact


def validate_scored_result_artifact(
    artifact: Mapping[str, Any],
    *,
    trajectory_events: list[dict[str, Any]],
    score_sidecar: Mapping[str, Any],
    public_validation_profile: Mapping[str, Any],
    final_test_profile: Mapping[str, Any],
) -> bool:
    """Validate cryptographic and semantic joins for a scored result."""
    try:
        document = _require_mapping(artifact, field_name="result artifact")
        _require_exact_fields(document, _ARTIFACT_FIELDS, field_name="artifact")
        if document["schema_version"] != "vaevas-result-artifact-v1":
            return False
        if document["artifact_sha256"] != result_artifact_sha256(document):
            return False
        if not validate_trajectory_semantics(trajectory_events):
            return False
        episode = _require_mapping(document["episode"], field_name="episode")
        _require_exact_fields(
            episode,
            {
                "episode_id",
                "attempt_id",
                "task_id",
                "condition",
                "primary_outcome",
                "terminal_reason",
                "incidents",
            },
            field_name="episode",
        )
        identity_fields = ("episode_id", "attempt_id", "task_id", "condition")
        if any(episode[field] != trajectory_events[0].get(field) for field in identity_fields):
            return False
        trajectory = _require_mapping(
            document["trajectory"], field_name="trajectory"
        )
        _require_exact_fields(
            trajectory,
            {"tail_sha256"},
            field_name="trajectory",
        )
        if trajectory["tail_sha256"] != trajectory_events[-1].get("event_sha256"):
            return False
        _require_sha256(trajectory["tail_sha256"], field_name="tail_sha256")
        contracts = _require_mapping(
            document["contract_identity"],
            field_name="contract_identity",
        )
        contract_fields = {
            "backend_profile_sha256",
            "registry_sha256",
            "effective_capability_sha256",
            "public_validation_profile_sha256",
            "final_test_profile_sha256",
            "final_profile_input_identity_sha256",
        }
        _require_exact_fields(
            contracts,
            contract_fields,
            field_name="contract_identity",
        )
        for field_name in contract_fields:
            _require_sha256(contracts[field_name], field_name=field_name)
        public_profile_sha256 = public_validation_profile_sha256(
            public_validation_profile
        )
        final_profile_sha256 = final_test_profile_sha256(final_test_profile)
        if contracts["public_validation_profile_sha256"] != public_profile_sha256:
            return False
        if contracts["final_test_profile_sha256"] != final_profile_sha256:
            return False
        for field_name in (
            "benchmark_release",
            "benchmark_manifest_sha256",
            "campaign_config_sha256",
        ):
            if public_validation_profile[field_name] != final_test_profile[field_name]:
                return False
        submission = _require_mapping(
            document["submission"], field_name="submission"
        )
        _require_exact_fields(
            submission,
            {"tree_sha256", "artifacts"},
            field_name="submission",
        )
        _require_sha256(submission["tree_sha256"], field_name="tree_sha256")
        _require_artifacts(submission["artifacts"])
        judgment = _require_mapping(
            document["final_judgment"], field_name="final_judgment"
        )
        _require_exact_fields(
            judgment,
            {"status", "judge_engine", "score", "submission_tree_sha256"},
            field_name="final_judgment",
        )
        _require_nonempty(judgment["status"], field_name="judgment status")
        _require_nonempty(
            judgment["judge_engine"], field_name="judge_engine"
        )
        _require_score(judgment["score"], field_name="judgment score")
        if judgment["submission_tree_sha256"] != submission["tree_sha256"]:
            return False
        if episode["primary_outcome"] != judgment["status"]:
            return False
        if episode["terminal_reason"] != "submitted":
            return False
        sidecar = _validate_score_sidecar(score_sidecar)
        sidecar_ref = _require_mapping(
            document["score_sidecar"], field_name="score_sidecar"
        )
        _require_exact_fields(
            sidecar_ref,
            {
                "schema_id",
                "sha256",
                "immutable",
                "submission_tree_sha256",
                "score_authority",
            },
            field_name="score_sidecar",
        )
        if sidecar_ref != {
            "schema_id": sidecar["schema_version"],
            "sha256": _canonical_sha256(sidecar),
            "immutable": True,
            "submission_tree_sha256": submission["tree_sha256"],
            "score_authority": sidecar["score_authority"],
        }:
            return False
        expected_input_identity = profile_input_identity_sha256(
            profile_sha256=contracts["final_test_profile_sha256"],
            input_kind="frozen_submission_tree",
            input_sha256=submission["tree_sha256"],
            attempt_id=episode["attempt_id"],
            task_id=episode["task_id"],
        )
        if (
            contracts["final_profile_input_identity_sha256"]
            != expected_input_identity
        ):
            return False
        freeze_event = next(
            event
            for event in trajectory_events
            if event["event_type"] == "submission_frozen"
        )
        final_event = next(
            event
            for event in trajectory_events
            if event["event_type"] == "final_judgment_completed"
        )
        if freeze_event["payload"].get("tree_sha256") != submission["tree_sha256"]:
            return False
        if final_event["payload"] != judgment:
            return False
        if sidecar["submission_tree_sha256"] != submission["tree_sha256"]:
            return False
        if sidecar["structured_result"] != {
            "status": judgment["status"],
            "score": judgment["score"],
        }:
            return False
        if sidecar["judge"]["engine"] != judgment["judge_engine"]:
            return False
        _validate_sidecar_authority(
            sidecar=sidecar,
            final_profile=final_test_profile,
            judgment_status=judgment["status"],
            judgment_engine=judgment["judge_engine"],
            judgment_score=judgment["score"],
            submission_tree_sha256=submission["tree_sha256"],
        )
    except (KeyError, StopIteration, TypeError, ValueError):
        return False
    return True


def _validate_sidecar_authority(
    *,
    sidecar: Mapping[str, Any],
    final_profile: Mapping[str, Any],
    judgment_status: str,
    judgment_engine: str,
    judgment_score: float | None,
    submission_tree_sha256: str,
) -> None:
    if (
        sidecar["schema_version"]
        != final_profile["score_sidecar_contract"]["schema_id"]
    ):
        raise ValueError("score sidecar schema does not match final profile")
    expected_score_authority = final_profile["score_sidecar_contract"].get(
        "score_authority",
        "development_only",
    )
    if sidecar["score_authority"] != expected_score_authority:
        raise ValueError("score sidecar does not match score_authority")
    expected = {
        "benchmark_release": final_profile["benchmark_release"],
        "benchmark_manifest_sha256": final_profile[
            "benchmark_manifest_sha256"
        ],
        "submission_tree_sha256": submission_tree_sha256,
        "checker_identity_sha256": final_profile["checker_identity_sha256"],
        "runtime_identity_sha256": final_profile["runtime_identity_sha256"],
        "campaign_config_sha256": final_profile["campaign_config_sha256"],
        "command_signature_sha256": final_profile["command_signature_sha256"],
    }
    for field_name, expected_value in expected.items():
        if sidecar[field_name] != expected_value:
            raise ValueError(f"score sidecar does not match {field_name}")
    if sidecar["judge"] != {
        "engine": final_profile["judge"]["engine"],
        "version": final_profile["judge"]["version"],
        "identity_sha256": final_profile["judge_identity_sha256"],
    }:
        raise ValueError("score sidecar does not match final judge identity")
    if judgment_engine != final_profile["judge"]["engine"]:
        raise ValueError("final judgment engine does not match final profile")
    if sidecar["structured_result"] != {
        "status": judgment_status,
        "score": judgment_score,
    }:
        raise ValueError("score sidecar does not match final judgment")


def _validate_score_sidecar(value: Mapping[str, Any]) -> Mapping[str, Any]:
    sidecar = _require_mapping(value, field_name="score sidecar")
    _require_exact_fields(sidecar, _SIDECAR_FIELDS, field_name="score sidecar")
    if sidecar["schema_version"] != "vaevas-score-sidecar-v1":
        raise ValueError("unsupported score sidecar schema")
    _require_nonempty(
        sidecar["benchmark_release"], field_name="benchmark_release"
    )
    for field_name in (
        "benchmark_manifest_sha256",
        "submission_tree_sha256",
        "checker_identity_sha256",
        "runtime_identity_sha256",
        "campaign_config_sha256",
        "command_signature_sha256",
    ):
        _require_sha256(sidecar[field_name], field_name=field_name)
    if sidecar["score_authority"] not in {"development_only", "formal"}:
        raise ValueError("unsupported score_authority")
    for field_name in (
        "immutable",
        "binds_submission_tree",
    ):
        if sidecar[field_name] is not True:
            raise ValueError(f"score sidecar requires {field_name}=true")
    for field_name in ("model_observation_allowed", "memory_entry_allowed"):
        if sidecar[field_name] is not False:
            raise ValueError(f"score sidecar requires {field_name}=false")
    judge = _require_mapping(sidecar["judge"], field_name="judge")
    _require_exact_fields(
        judge,
        {"engine", "version", "identity_sha256"},
        field_name="judge",
    )
    _require_nonempty(judge["engine"], field_name="judge.engine")
    _require_nonempty(judge["version"], field_name="judge.version")
    _require_sha256(judge["identity_sha256"], field_name="judge.identity_sha256")
    structured = _require_mapping(
        sidecar["structured_result"], field_name="structured_result"
    )
    _require_exact_fields(
        structured,
        {"status", "score"},
        field_name="structured_result",
    )
    _require_nonempty(structured["status"], field_name="structured_result.status")
    _require_score(structured["score"], field_name="structured_result.score")
    _require_canonical_json(sidecar)
    return sidecar


def _require_artifacts(value: Any) -> None:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise ValueError("submission artifacts must be non-empty paths")


def _require_score(value: Any, *, field_name: str) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a finite number or null")
    if not math.isfinite(float(value)):
        raise ValueError(f"{field_name} must be finite")


def _require_nonempty(value: Any, *, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_sha256(value: Any, *, field_name: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


def _require_mapping(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a JSON object")
    return value


def _require_exact_fields(
    value: Mapping[str, Any],
    expected: set[str],
    *,
    field_name: str,
) -> None:
    if set(value) != expected:
        raise ValueError(f"{field_name} must contain exactly the required fields")


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    _require_canonical_json(value)
    encoded = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
