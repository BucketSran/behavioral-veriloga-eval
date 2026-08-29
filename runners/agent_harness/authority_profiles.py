"""Authority profile hashing and replay guards for vaEVAS evaluation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from typing import Any, Literal


InputKind = Literal["candidate_tree", "frozen_submission_tree"]


def public_validation_profile_sha256(profile: Mapping[str, Any]) -> str:
    """Hash one public validation authority profile."""
    if profile.get("schema_version") != "vaevas-public-validation-profile-v1":
        raise ValueError("expected vaevas-public-validation-profile-v1")
    return _canonical_profile_sha256(profile)


def final_test_profile_sha256(profile: Mapping[str, Any]) -> str:
    """Hash one final trusted replay authority profile."""
    if profile.get("schema_version") != "vaevas-final-test-profile-v1":
        raise ValueError("expected vaevas-final-test-profile-v1")
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
    _require_nonempty(previous_judge_attempt_id, field_name="previous_judge_attempt_id")
    _require_nonempty(judge_attempt_id, field_name="judge_attempt_id")
    if failure_kind != "infrastructure_failure":
        raise ValueError("final replay is allowed only for infrastructure_failure")
    if frozen_submission_tree_sha256 != previous_frozen_submission_tree_sha256:
        raise ValueError("final replay must use the same frozen submission")
    if judge_attempt_id == previous_judge_attempt_id:
        raise ValueError("final replay requires a new judge_attempt_id")
    if model_reentry_requested:
        raise ValueError("final replay forbids model reentry")
    return "allowed_infrastructure_replay"


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
