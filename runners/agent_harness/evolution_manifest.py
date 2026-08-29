"""Deterministic contracts for round-based candidate evolution."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from typing import Any


class EvolutionReducerError(ValueError):
    """A classified contract violation while reducing evolution evidence."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def evolution_manifest_sha256(manifest: Mapping[str, Any]) -> str:
    """Hash a schema-shaped evolution manifest with canonical JSON ordering."""
    if not isinstance(manifest, Mapping):
        raise TypeError("evolution manifest must be a JSON object")
    _require_canonical_json(manifest, label="evolution manifest")
    return _canonical_sha256(manifest)


def build_round_snapshot(
    *,
    manifest: Mapping[str, Any],
    round_index: int,
    candidates: Sequence[Mapping[str, Any]],
    round_sealed: bool = True,
    global_deadline_reached: bool = False,
    retry_parent_attempt_id: str | None = None,
    memory_snapshot_sha256: str | None = None,
    frozen_input_sha256: str | None = None,
) -> dict[str, Any]:
    """Canonicalize the feedback visible at the next evolution round."""
    if round_index < 0:
        raise ValueError("round_index cannot be negative")
    if global_deadline_reached and not round_sealed:
        raise EvolutionReducerError(
            "unsealed_round_after_global_deadline",
            "global deadline reached with an unsealed round",
        )
    manifest_hash = evolution_manifest_sha256(manifest)
    _require_optional_sha256(memory_snapshot_sha256, field_name="memory_snapshot_sha256")
    _require_optional_sha256(frozen_input_sha256, field_name="frozen_input_sha256")
    normalized_candidates = [
        _normalize_candidate(candidate, manifest=manifest)
        for candidate in candidates
    ]
    normalized_candidates.sort(
        key=lambda candidate: (
            candidate["round_index"],
            candidate["candidate_tree_sha256"],
            candidate["candidate_id"],
            candidate["branch_id"],
        )
    )
    snapshot = {
        "schema_version": "vaevas-evolution-round-snapshot-v1",
        "manifest_sha256": manifest_hash,
        "round_index": round_index,
        "round_sealed": round_sealed,
        "global_deadline_reached": global_deadline_reached,
        "retry_parent_attempt_id": retry_parent_attempt_id,
        "memory_snapshot_sha256": memory_snapshot_sha256,
        "frozen_input_sha256": frozen_input_sha256,
        "candidates": normalized_candidates,
    }
    snapshot["round_snapshot_sha256"] = _canonical_sha256(snapshot)
    return snapshot


def select_candidate(
    *,
    manifest: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Select the incumbent using public metrics and deterministic tie-breaks."""
    if not candidates:
        raise EvolutionReducerError("no_candidates", "cannot select from no candidates")
    metric_order = manifest["selection_rule"]["metric_order"]
    normalized = [
        _normalize_candidate(candidate, manifest=manifest)
        for candidate in candidates
        if candidate.get("status", "completed") == "completed"
    ]
    if not normalized:
        raise EvolutionReducerError(
            "no_completed_candidates",
            "no completed candidates are eligible for selection",
        )

    def sort_key(candidate: Mapping[str, Any]) -> tuple[Any, ...]:
        metrics = candidate["public_validation"]["metrics"]
        metric_key = tuple(
            -float(metrics.get(metric_name, 0.0)) for metric_name in metric_order
        )
        return (
            *metric_key,
            candidate["candidate_tree_sha256"],
            candidate["candidate_id"],
        )

    return dict(sorted(normalized, key=sort_key)[0])


def _normalize_candidate(
    candidate: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    if "final_test" in candidate or "trusted_feedback" in candidate:
        raise EvolutionReducerError(
            "final_feedback_leakage",
            "final feedback cannot enter evolution rounds",
        )
    for field_name in (
        "candidate_id",
        "branch_id",
        "round_index",
        "candidate_tree_sha256",
        "public_validation",
        "status",
    ):
        if field_name not in candidate:
            raise EvolutionReducerError(
                "candidate_missing_field",
                f"candidate record missing field: {field_name}",
            )
    _require_nonempty_string(candidate["candidate_id"], field_name="candidate_id")
    _require_nonempty_string(candidate["branch_id"], field_name="branch_id")
    if candidate["round_index"] < 0:
        raise ValueError("candidate round_index cannot be negative")
    _require_sha256(
        candidate["candidate_tree_sha256"],
        field_name="candidate_tree_sha256",
    )
    status = candidate["status"]
    if status not in {"completed", "branch_timeout", "branch_failed"}:
        raise EvolutionReducerError("invalid_candidate_status", f"invalid status: {status}")
    validation = candidate["public_validation"]
    if not isinstance(validation, Mapping):
        raise TypeError("public_validation must be a JSON object")
    if validation.get("profile_sha256") != manifest["public_validation_profile_sha256"]:
        raise EvolutionReducerError(
            "validation_profile_mismatch",
            "candidate validation profile does not match manifest",
        )
    metrics = validation.get("metrics")
    if not isinstance(metrics, Mapping):
        raise TypeError("public_validation.metrics must be a JSON object")
    _require_sha256(validation.get("event_sha256"), field_name="event_sha256")
    _require_canonical_json(metrics, label="public validation metrics")
    return {
        "candidate_id": candidate["candidate_id"],
        "branch_id": candidate["branch_id"],
        "round_index": candidate["round_index"],
        "candidate_tree_sha256": candidate["candidate_tree_sha256"],
        "public_validation": {
            "profile_sha256": validation["profile_sha256"],
            "metrics": dict(sorted(metrics.items())),
            "event_sha256": validation["event_sha256"],
        },
        "status": status,
    }


def _canonical_sha256(value: Any) -> str:
    canonical = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _require_canonical_json(value: Any, *, label: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{label} JSON object keys must be strings")
            _require_canonical_json(item, label=label)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            _require_canonical_json(item, label=label)
        return
    if value is None or isinstance(value, (str, int, bool)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{label} JSON numbers must be finite")
        return
    raise TypeError(f"{label} contains a non-JSON value: {type(value).__name__}")


def _require_sha256(value: object, *, field_name: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


def _require_optional_sha256(value: object, *, field_name: str) -> None:
    if value is None:
        return
    _require_sha256(value, field_name=field_name)


def _require_nonempty_string(value: object, *, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
