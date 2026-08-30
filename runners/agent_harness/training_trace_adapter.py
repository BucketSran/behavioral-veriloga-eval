"""Synthetic native trace adapter for the training export contract."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from typing import Any

from .training_export import TrainingExportError, build_training_export
from .trajectory import (
    validate_candidate_trajectory_semantics,
    validate_trajectory_semantics,
)


ADAPTER_ID = "vaevas-synthetic-native-training-adapter-v1"
_ALLOWED_MODES = frozenset({"sft", "rl"})
_METADATA_KEYS = frozenset(
    {
        "source_id",
        "release_identity",
        "provenance",
        "normalizer",
        "license",
        "provider_use",
        "project_authorization",
        "exposure_policy",
        "initial_messages",
    }
)
_EVENT_KEYS = frozenset(
    {
        "schema_version",
        "episode_id",
        "attempt_id",
        "task_id",
        "condition",
        "sequence",
        "timestamp_utc",
        "monotonic_ns",
        "actor",
        "event_type",
        "visibility",
        "payload",
        "prev_event_sha256",
        "event_sha256",
    }
)
_ACTION_PAYLOAD_KEYS = frozenset(
    {
        "schema_version",
        "action_id",
        "tool_name",
        "arguments_sha256",
        "source_backend",
        "candidate_tree_sha256",
    }
)
_OBSERVATION_PAYLOAD_KEYS = frozenset(
    {
        "action_id",
        "schema_version",
        "observation_id",
        "tool_name",
        "status",
        "payload_sha256",
        "truncated",
        "candidate_tree_sha256",
        "validation_profile_sha256",
        "budget_delta",
        "done",
        "terminal_reason",
    }
)
_ALLOWED_EVENT_TYPES = frozenset(
    {
        "episode_started",
        "model_call_admitted",
        "action_proposed",
        "action_authorized",
        "action_rejected",
        "candidate_transition_rejected",
        "budget_updated",
        "environment_observed",
        "candidate_snapshot_frozen",
        "submission_freeze_rejected",
        "submission_frozen",
        "final_judgment_completed",
        "episode_failed",
        "cleanup_failed",
        "cleanup_completed",
        "deadline_reached",
        "deadline_interruption",
        "episode_completed",
    }
)
_MAX_EVENTS = 256
_MAX_JSON_BYTES = 32 * 1024
_MAX_CONTENT_BYTES = 16 * 1024
_FORBIDDEN_WORDS = ("private", "hidden", "trusted", "final")
_SHA256_CHARS = frozenset("0123456789abcdef")


class TrainingTraceAdapterError(TrainingExportError):
    """Raised when a native trace cannot be projected safely."""


def project_synthetic_native_trace_to_training_source(
    events: Sequence[Mapping[str, Any]],
    *,
    synthetic_metadata: Mapping[str, Any],
    split_manifest: Mapping[str, Any],
    mode: str,
) -> dict[str, Any]:
    """Project an explicitly synthetic native event chain into a training source.

    The adapter is intentionally narrow: it accepts only in-memory synthetic
    documents, exports only model-visible actions/observations, and invokes the
    existing training-export builder before returning.
    """

    if mode not in _ALLOWED_MODES:
        raise TrainingTraceAdapterError(f"unsupported projection mode: {mode}")
    event_docs = _events(events)
    metadata = _metadata(synthetic_metadata, mode=mode)
    if not (
        validate_trajectory_semantics(event_docs)
        or validate_candidate_trajectory_semantics(event_docs)
    ):
        raise TrainingTraceAdapterError("native trajectory lifecycle is invalid")
    if not event_docs[0]["task_id"].startswith("synthetic/"):
        raise TrainingTraceAdapterError("adapter accepts only synthetic task ids")

    source = {
        "source_kind": "synthetic",
        "source_id": _string(metadata, "source_id"),
        "release_identity": _string(metadata, "release_identity"),
        "task_id": _string(event_docs[0], "task_id"),
        "episode_id": _string(event_docs[0], "episode_id"),
        "provenance": _with_adapter_identity(
            _mapping(metadata["provenance"], "provenance"),
            trace_sha256=_trace_sha256(event_docs),
        ),
        "normalizer": _mapping(metadata["normalizer"], "normalizer"),
        "license": _mapping(metadata["license"], "license"),
        "provider_use": _mapping(metadata["provider_use"], "provider_use"),
        "project_authorization": _mapping(
            metadata["project_authorization"],
            "project_authorization",
        ),
        "exposure_policy": _mapping(metadata["exposure_policy"], "exposure_policy"),
        "trajectory": _project_training_events(event_docs, metadata),
        "termination": _termination(event_docs),
    }
    if mode == "sft":
        source["labels"] = _mapping(metadata.get("labels"), "labels")
    else:
        source["reward"] = _mapping(metadata.get("reward"), "reward")
    build_training_export(source, split_manifest=split_manifest, mode=mode)
    return source


def _events(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(events, (str, bytes)) or not isinstance(events, Sequence):
        raise TrainingTraceAdapterError("events must be a list")
    if not events:
        raise TrainingTraceAdapterError("events must not be empty")
    if len(events) > _MAX_EVENTS:
        raise TrainingTraceAdapterError("events exceed maximum count")
    docs = []
    for event in events:
        doc = _mapping(event, "event")
        _require_keys(doc, _EVENT_KEYS, "event")
        _assert_finite_json(doc, "event")
        if _json_size(doc) > _MAX_JSON_BYTES:
            raise TrainingTraceAdapterError("event exceeds maximum JSON byte length")
        if doc.get("schema_version") != "vaevas-trajectory-event-v1":
            raise TrainingTraceAdapterError("unsupported native event schema")
        if doc.get("event_type") not in _ALLOWED_EVENT_TYPES:
            raise TrainingTraceAdapterError("unsupported native event type")
        _validate_event_payload(doc)
        docs.append(doc)
    return docs


def _metadata(metadata: Mapping[str, Any], *, mode: str) -> dict[str, Any]:
    doc = _mapping(metadata, "synthetic_metadata")
    expected = set(_METADATA_KEYS)
    if mode == "sft":
        expected.add("labels")
    else:
        expected.add("reward")
    _require_keys(doc, expected, "synthetic_metadata")
    _assert_finite_json(doc, "synthetic_metadata")
    if _json_size(doc) > _MAX_JSON_BYTES:
        raise TrainingTraceAdapterError(
            "synthetic_metadata exceeds maximum JSON byte length"
        )
    if not _string(doc, "source_id").startswith("synthetic-"):
        raise TrainingTraceAdapterError("source_id must use synthetic namespace")
    _initial_training_events(doc["initial_messages"])
    return doc


def _project_training_events(
    events: Sequence[Mapping[str, Any]],
    metadata: Mapping[str, Any],
) -> list[dict[str, Any]]:
    projected = _initial_training_events(metadata["initial_messages"])
    seen_ids = {event["event_id"] for event in projected}
    for event in events:
        event_type = event["event_type"]
        visibility = event["visibility"]
        if visibility == "model" and event_type not in {
            "action_proposed",
            "environment_observed",
        }:
            raise TrainingTraceAdapterError("unsupported model-visible native event")
        if event_type == "action_proposed":
            projected_event = _assistant_action_event(event)
        elif event_type == "environment_observed":
            projected_event = _environment_observation_event(event)
        else:
            continue
        if projected_event["event_id"] in seen_ids:
            raise TrainingTraceAdapterError("duplicate projected event_id")
        seen_ids.add(projected_event["event_id"])
        projected.append(projected_event)
    return projected


def _initial_training_events(messages: Any) -> list[dict[str, Any]]:
    result = []
    for index, message in enumerate(_sequence(messages, "initial_messages")):
        doc = _mapping(message, "initial_message")
        _require_keys(doc, {"role", "content"}, "initial_message")
        role = _string(doc, "role")
        if role not in {"system", "user"}:
            raise TrainingTraceAdapterError("initial messages must be system or user")
        content = _content(_string(doc, "content"), "initial_message.content")
        _reject_forbidden_content(content, "initial_message.content")
        result.append(
            {
                "event_id": f"synthetic-prompt-{index + 1}",
                "role": role,
                "visibility": "model",
                "content": content,
            }
        )
    return result


def _assistant_action_event(event: Mapping[str, Any]) -> dict[str, Any]:
    payload = _mapping(event["payload"], "action payload")
    content = _canonical_json(
        {
            "arguments_sha256": _sha256(
                payload.get("arguments_sha256"), "arguments_sha256"
            ),
            "candidate_tree_sha256": _sha256(
                payload.get("candidate_tree_sha256"),
                "candidate_tree_sha256",
            ),
            "source_backend": _string(payload, "source_backend"),
            "tool_name": _string(payload, "tool_name"),
        }
    )
    _reject_forbidden_content(content, "projected action content")
    return {
        "event_id": _string(payload, "action_id"),
        "role": "assistant",
        "visibility": "model",
        "content": content,
    }


def _environment_observation_event(event: Mapping[str, Any]) -> dict[str, Any]:
    payload = _mapping(event["payload"], "observation payload")
    content = _canonical_json(
        {
            "action_id": _string(payload, "action_id"),
            "budget_delta": _mapping(payload["budget_delta"], "budget_delta"),
            "candidate_tree_sha256": payload.get("candidate_tree_sha256"),
            "done": _bool(payload.get("done"), "done"),
            "observation_id": _string(payload, "observation_id"),
            "payload_sha256": _sha256(payload.get("payload_sha256"), "payload_sha256"),
            "status": _string(payload, "status"),
            "terminal_reason": payload.get("terminal_reason"),
            "tool_name": _string(payload, "tool_name"),
            "truncated": _bool(payload.get("truncated"), "truncated"),
            "validation_profile_sha256": payload.get("validation_profile_sha256"),
        }
    )
    _reject_forbidden_content(content, "projected observation content")
    return {
        "event_id": _string(payload, "observation_id"),
        "role": "environment",
        "visibility": "model",
        "content": content,
    }


def _termination(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    payload = _mapping(events[-1]["payload"], "episode_completed payload")
    reason = payload.get("terminal_reason")
    if not isinstance(reason, str) or not reason:
        reason = (
            "candidate_frozen"
            if any(
                event["event_type"] == "candidate_snapshot_frozen" for event in events
            )
            else "submitted"
        )
    return {
        "reason": reason,
        "budget_exhausted": reason
        in {
            "budget_exhausted",
            "model_call_limit",
            "tool_call_limit",
            "hard_budget_exhausted",
        },
    }


def _validate_event_payload(event: Mapping[str, Any]) -> None:
    event_type = event["event_type"]
    payload = _mapping(event["payload"], "event payload")
    if event_type == "action_proposed":
        _require_keys(payload, _ACTION_PAYLOAD_KEYS, "action payload")
    elif event_type == "environment_observed":
        _require_keys(payload, _OBSERVATION_PAYLOAD_KEYS, "observation payload")
    elif event["visibility"] == "model":
        raise TrainingTraceAdapterError("unsupported model-visible native event")


def _with_adapter_identity(
    provenance: dict[str, Any],
    *,
    trace_sha256: str,
) -> dict[str, Any]:
    artifact = _string(provenance, "artifact")
    generator = _string(provenance, "generator")
    version = _string(provenance, "version")
    return {
        "artifact": artifact,
        "generator": generator,
        "version": f"{version}-{ADAPTER_ID}-{trace_sha256}",
    }


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TrainingTraceAdapterError(f"{label} must be an object")
    return dict(value)


def _sequence(value: Any, label: str) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TrainingTraceAdapterError(f"{label} must be a list")
    return list(value)


def _require_keys(
    value: Mapping[str, Any], expected: set[str] | frozenset[str], label: str
) -> None:
    keys = set(value)
    if keys != set(expected):
        missing = sorted(set(expected) - keys)
        extra = sorted(keys - set(expected))
        details = []
        if missing:
            details.append(f"missing {missing}")
        if extra:
            details.append(f"unknown {extra}")
        raise TrainingTraceAdapterError(
            f"{label} has invalid fields: {', '.join(details)}"
        )


def _string(mapping: Mapping[str, Any], field: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value:
        raise TrainingTraceAdapterError(f"{field} must be a non-empty string")
    return value


def _content(value: str, label: str) -> str:
    if len(value.encode("utf-8")) > _MAX_CONTENT_BYTES:
        raise TrainingTraceAdapterError(f"{label} exceeds maximum byte length")
    return value


def _bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise TrainingTraceAdapterError(f"{label} must be boolean")
    return value


def _sha256(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _SHA256_CHARS for character in value)
    ):
        raise TrainingTraceAdapterError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _reject_forbidden_content(value: str, label: str) -> None:
    lowered = value.lower()
    if any(word in lowered for word in _FORBIDDEN_WORDS):
        raise TrainingTraceAdapterError(f"{label} contains forbidden training material")


def _canonical_json(value: Mapping[str, Any]) -> str:
    content = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return _content(content, "projected content")


def _json_size(value: Mapping[str, Any]) -> int:
    return len(_canonical_json(value).encode("utf-8"))


def _trace_sha256(events: Sequence[Mapping[str, Any]]) -> str:
    return hashlib.sha256(
        _canonical_json({"events": list(events)}).encode("utf-8")
    ).hexdigest()


def _assert_finite_json(value: Any, label: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TrainingTraceAdapterError(f"{label} keys must be strings")
            _assert_finite_json(item, f"{label}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _assert_finite_json(item, f"{label}[{index}]")
        return
    if isinstance(value, float) and not math.isfinite(value):
        raise TrainingTraceAdapterError(f"{label} contains non-finite number")
