"""Reviewer-only safe exports for private native harness evidence."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
import re
from typing import Any, Mapping, Sequence

from .trajectory import (
    validate_trajectory,
    validate_trajectory_semantics,
)


NORMALIZER_ID = "vaevas-reviewer-evidence-normalizer-v1"
SCHEMA_VERSION = "vaevas-reviewer-evidence-export-v1"
_IDENTITY_FIELDS = ("episode_id", "attempt_id", "task_id", "condition")
_SHA_FIELDS = frozenset({
    "backend_profile_sha256",
    "candidate_tree_sha256",
    "final_test_profile_sha256",
    "public_validation_profile_sha256",
    "submission_tree_sha256",
    "validation_profile_sha256",
})
_STRING_FIELDS = frozenset({
    "action_id",
    "failure_category",
    "request_id",
    "status",
    "tool_name",
})
_NULLABLE_STRING_FIELDS = frozenset({"primary_outcome", "terminal_reason"})
_INT_FIELDS = frozenset({"max_tokens"})
_FLOAT_FIELDS = frozenset({"timeout_s"})
_BOOL_FIELDS = frozenset({"transport_capture_supported"})
_BUDGET_COUNTER_FIELDS = frozenset({
    "model_calls",
    "public_validation_calls",
    "tool_calls",
})
_USAGE_FIELDS = ("prompt_tokens", "completion_tokens", "total_tokens")
_OPTIONAL_USAGE_FIELDS = ("reasoning_tokens",)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class EvidenceExportError(ValueError):
    """Raised when raw evidence cannot be safely normalized."""


def build_reviewer_evidence_export(
    *,
    trajectory_events: Sequence[Mapping[str, Any]],
    private_events: Sequence[Mapping[str, Any]],
    trajectory_bytes: bytes,
    private_event_bytes: bytes,
) -> dict[str, Any]:
    """Build a deterministic reviewer ledger without model-visible content.

    The caller owns file reading and persistence. This function validates the
    supplied event chains, binds the raw bytes by hash, and exports only a small
    structural allowlist for audit/review. The allowlist preserves identifiers
    and provider metadata, but it is not a universal free-text declassifier.
    The result is not suitable as model memory or environment feedback.
    """

    trajectory = [_mapping(event, "trajectory event") for event in trajectory_events]
    private = [_mapping(event, "private event") for event in private_events]
    _validate_raw_bytes("trajectory", trajectory, trajectory_bytes)
    _validate_raw_bytes("private events", private, private_event_bytes)
    if not validate_trajectory_semantics(trajectory):
        raise EvidenceExportError("trajectory semantic validation failed")
    if not validate_trajectory(private):
        raise EvidenceExportError("private event chain validation failed")
    identity = _identity(trajectory[0])
    for event in [*trajectory, *private]:
        if _identity(event) != identity:
            raise EvidenceExportError("event identity mismatch")
    usage = _usage_summary(private)
    ledger = [
        _ledger_row("trajectory", index, event)
        for index, event in enumerate(trajectory)
    ] + [
        _ledger_row("private_events", index, event)
        for index, event in enumerate(private)
    ]
    export: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "normalizer_id": NORMALIZER_ID,
        "source": {
            "trajectory": _source_summary(trajectory, trajectory_bytes),
            "private_events": _source_summary(private, private_event_bytes),
        },
        "identity": identity,
        "usage": usage,
        "ledger": ledger,
        "visibility_contract": {
            "audience": "reviewer_only",
            "may_enter_model_observation": False,
            "may_enter_shared_memory": False,
            "final_judge_payload_exported": False,
        },
    }
    export["export_sha256"] = _canonical_sha256(export)
    return export


def _mapping(value: Mapping[str, Any], label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise EvidenceExportError(f"{label} must be an object")
    return dict(value)


def _identity(event: Mapping[str, Any]) -> dict[str, str]:
    identity: dict[str, str] = {}
    for field in _IDENTITY_FIELDS:
        value = event.get(field)
        if not isinstance(value, str) or not value:
            raise EvidenceExportError(f"{field} must be a non-empty string")
        identity[field] = value
    return identity


def _source_summary(events: Sequence[Mapping[str, Any]], raw_bytes: bytes) -> dict[str, Any]:
    if not isinstance(raw_bytes, bytes):
        raise EvidenceExportError("raw evidence bytes must be bytes")
    return {
        "bytes_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "event_count": len(events),
        "tail_event_sha256": events[-1].get("event_sha256") if events else None,
    }


def _validate_raw_bytes(
    label: str, events: Sequence[Mapping[str, Any]], raw_bytes: bytes
) -> None:
    if not isinstance(raw_bytes, bytes):
        raise EvidenceExportError("raw evidence bytes must be bytes")
    parsed: list[dict[str, Any]] = []
    try:
        for line in raw_bytes.decode("utf-8").splitlines():
            if line.strip():
                parsed.append(json.loads(line))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceExportError(f"{label} bytes are not JSONL") from exc
    if parsed != list(events):
        raise EvidenceExportError(f"{label} bytes do not match supplied events")


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    material = dict(value)
    material.pop("export_sha256", None)
    return hashlib.sha256(
        json.dumps(
            material,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _ledger_row(stream: str, index: int, event: Mapping[str, Any]) -> dict[str, Any]:
    event_type = _string(event.get("event_type"), "event_type")
    payload = event.get("payload")
    if not isinstance(payload, Mapping):
        raise EvidenceExportError("event payload must be an object")
    return {
        "source_stream": stream,
        "source_index": index,
        "source_event_sha256": _string(event.get("event_sha256"), "event_sha256"),
        "source_prev_event_sha256": event.get("prev_event_sha256"),
        "identity": _identity(event),
        "sequence": event.get("sequence"),
        "actor": _string(event.get("actor"), "actor"),
        "event_type": event_type,
        "visibility": _string(event.get("visibility"), "visibility"),
        "payload": _safe_payload(event_type, payload),
    }


def _safe_payload(event_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key in sorted(payload):
        value = payload[key]
        if key in _SHA_FIELDS:
            safe[key] = _optional_sha256(value, key)
        elif key in _STRING_FIELDS:
            safe[key] = _string(value, key)
        elif key in _NULLABLE_STRING_FIELDS:
            safe[key] = _optional_string(value, key)
        elif key in _INT_FIELDS:
            safe[key] = _int(value, key)
        elif key in _FLOAT_FIELDS:
            safe[key] = _optional_number(value, key)
        elif key in _BOOL_FIELDS:
            safe[key] = _bool(value, key)
        elif key in {"consumed", "delta", "budget_delta"}:
            safe[key] = _safe_counter_map(value, key)
    if event_type == "provider_response":
        safe["provider_response"] = _provider_response_metadata(payload)
    if event_type == "provider_transport_attempt":
        safe["transport"] = _transport_metadata(payload)
    if event_type == "tool_output_capture":
        safe["tool_output_capture"] = _tool_output_capture_metadata(payload)
    if event_type == "tool_result":
        observation = payload.get("observation")
        if not isinstance(observation, Mapping):
            raise EvidenceExportError("tool_result observation must be an object")
        safe["observation"] = _safe_observation(observation)
    return safe


def _safe_observation(observation: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in {
            "tool_name": _optional_string(observation.get("tool_name"), "tool_name"),
            "status": _optional_string(observation.get("status"), "status"),
            "candidate_tree_sha256": _optional_sha256(
                observation.get("candidate_tree_sha256"), "candidate_tree_sha256"
            ),
        }.items()
        if value is not None
    }


def _provider_response_metadata(payload: Mapping[str, Any]) -> dict[str, Any]:
    response = payload.get("response")
    if not isinstance(response, Mapping):
        raise EvidenceExportError("provider_response response must be an object")
    choices = response.get("choices") or []
    first = choices[0] if isinstance(choices, list) and choices else {}
    finish_reason = first.get("finish_reason") if isinstance(first, Mapping) else None
    metadata = {
        "response_id_sha256": _optional_string_sha256(response.get("id"), "response.id"),
        "model_sha256": _optional_string_sha256(response.get("model"), "response.model"),
        "finish_reason": _optional_string(finish_reason, "finish_reason"),
    }
    if finish_reason not in {None, "stop", "length", "tool_calls", "function_call", "content_filter"}:
        metadata["finish_reason"] = "other"
        metadata["unknown_finish_reason_sha256"] = _optional_string_sha256(finish_reason, "finish_reason")
    return metadata


def _usage_summary(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    request_actions: dict[str, str] = {}
    resolved_ids: set[str] = set()
    transport_ordinals: dict[str, int] = {}
    requests_supporting_transport: set[str] = set()
    tool_requests: set[str] = set()
    tool_resolutions: set[str] = set()
    tool_captures: set[str] = set()
    provider = Counter()
    tool = Counter()
    usage_totals: dict[str, int | None] = dict.fromkeys(
        (*_USAGE_FIELDS, *_OPTIONAL_USAGE_FIELDS)
    )
    unknown_usage_fields: set[str] = set()
    unknown_optional_usage_fields: set[str] = set(_OPTIONAL_USAGE_FIELDS)
    transport_complete: bool | None = None
    transport_elapsed_s: float | None = None
    transport_stdout_total = 0
    transport_stderr_total = 0
    tool_capture_complete: bool | None = None
    tool_capture_total = 0
    tool_capture_captured = 0
    tool_capture_truncated = 0
    for event in events:
        event_type = event.get("event_type")
        payload = event.get("payload")
        if not isinstance(payload, Mapping):
            raise EvidenceExportError("event payload must be an object")
        if event_type == "provider_request":
            request_id = _string(payload.get("request_id"), "request_id")
            action_id = _string(payload.get("action_id"), "action_id")
            if request_id in request_actions:
                raise EvidenceExportError("duplicate provider request")
            request_actions[request_id] = action_id
            if payload.get("transport_capture_supported", False) is True:
                requests_supporting_transport.add(request_id)
            provider["requests"] += 1
        elif event_type == "provider_transport_attempt":
            request_id = _string(payload.get("request_id"), "request_id")
            action_id = _string(payload.get("action_id"), "action_id")
            if request_id not in request_actions:
                raise EvidenceExportError(
                    "provider_transport_attempt before provider request"
                )
            if request_actions[request_id] != action_id:
                raise EvidenceExportError("provider transport action_id mismatch")
            if request_id in resolved_ids:
                raise EvidenceExportError("provider transport attempt after response")
            metadata = _transport_metadata(payload)
            ordinal = metadata["transport_attempt"]
            expected = transport_ordinals.get(request_id, 0) + 1
            if ordinal < expected:
                raise EvidenceExportError("duplicate provider transport attempt")
            if ordinal != expected:
                raise EvidenceExportError("transport_attempt ordinal mismatch")
            transport_ordinals[request_id] = ordinal
            provider["transport_attempts"] += 1
            transport_complete = (
                metadata["capture_complete"]
                if transport_complete is None
                else transport_complete and metadata["capture_complete"]
            )
            if metadata["elapsed_s"] is not None:
                transport_elapsed_s = (
                    metadata["elapsed_s"]
                    if transport_elapsed_s is None
                    else transport_elapsed_s + metadata["elapsed_s"]
                )
            transport_stdout_total += metadata["stdout"]["total_bytes"]
            transport_stderr_total += metadata["stderr"]["total_bytes"]
        elif event_type in {"provider_response", "provider_failure"}:
            request_id = _string(payload.get("request_id"), "request_id")
            action_id = _string(payload.get("action_id"), "action_id")
            if request_id not in request_actions:
                raise EvidenceExportError(
                    f"{event_type} before provider request"
                )
            if request_actions[request_id] != action_id:
                raise EvidenceExportError("provider action_id mismatch")
            if request_id in resolved_ids:
                raise EvidenceExportError("duplicate provider endpoint")
            resolved_ids.add(request_id)
            provider["responses" if event_type == "provider_response" else "failures"] += 1
            if event_type == "provider_response":
                observed = _response_usage(payload)
                for key, value in observed.items():
                    if key in _OPTIONAL_USAGE_FIELDS:
                        if value is None:
                            unknown_optional_usage_fields.add(key)
                        else:
                            unknown_optional_usage_fields.discard(key)
                            if usage_totals[key] is None:
                                usage_totals[key] = value
                            else:
                                usage_totals[key] += value
                    elif value is None:
                        unknown_usage_fields.add(key)
                    elif usage_totals[key] is None:
                        usage_totals[key] = value
                    else:
                        usage_totals[key] += value
            else:
                unknown_usage_fields.update(_USAGE_FIELDS)
                unknown_optional_usage_fields.update(_OPTIONAL_USAGE_FIELDS)
        elif event_type == "tool_request":
            action_id = _string(payload.get("action_id"), "action_id")
            if action_id in tool_requests:
                raise EvidenceExportError("duplicate tool request")
            tool_requests.add(action_id)
            tool["requests"] += 1
        elif event_type == "tool_output_capture":
            action_id = _string(payload.get("action_id"), "action_id")
            if action_id not in tool_requests:
                raise EvidenceExportError("tool_output_capture before tool request")
            if action_id in tool_resolutions:
                raise EvidenceExportError("tool_output_capture after tool resolution")
            if action_id in tool_captures:
                raise EvidenceExportError("duplicate tool output capture")
            metadata = _tool_output_capture_metadata(payload)
            tool_captures.add(action_id)
            tool["captures"] += 1
            tool_capture_complete = (
                metadata["output_capture_complete"]
                if tool_capture_complete is None
                else tool_capture_complete and metadata["output_capture_complete"]
            )
            tool_capture_total += metadata["output_total_bytes"]
            tool_capture_captured += metadata["output_captured_bytes"]
            tool_capture_truncated += metadata["output_truncated_bytes"]
        elif event_type in {"tool_result", "tool_failure"}:
            action_id = _string(payload.get("action_id"), "action_id")
            if action_id not in tool_requests:
                raise EvidenceExportError(f"{event_type} before tool request")
            if action_id in tool_resolutions:
                raise EvidenceExportError("duplicate tool resolution")
            tool_resolutions.add(action_id)
            tool["results" if event_type == "tool_result" else "failures"] += 1
    missing_resolutions = set(request_actions) - resolved_ids
    orphan_resolutions = resolved_ids - set(request_actions)
    if missing_resolutions:
        raise EvidenceExportError("unresolved provider request")
    if orphan_resolutions:
        raise EvidenceExportError("provider response without request")
    if provider["requests"] == 0:
        unknown_usage_fields.update(_USAGE_FIELDS)
        unknown_optional_usage_fields.update(_OPTIONAL_USAGE_FIELDS)
    for key in unknown_usage_fields:
        usage_totals[key] = None
    for key in unknown_optional_usage_fields:
        usage_totals[key] = None
    usage_status = (
        "no_calls"
        if provider["requests"] == 0
        else "partial"
        if unknown_usage_fields
        else "reported"
    )
    provider_usage_complete = (
        provider["requests"] > 0
        and not unknown_usage_fields
        and provider["failures"] == 0
    )
    unresolved_tools = len(tool_requests - tool_resolutions)
    unobserved_transport_requests = sum(
        1 for request_id in request_actions if request_id not in transport_ordinals
    )
    transport_supported = (
        len(requests_supporting_transport) == len(request_actions)
        if request_actions
        else False
    )
    return {
        "completeness": {
            "all_provider_requests_joined": not orphan_resolutions,
            "all_provider_requests_resolved": not missing_resolutions,
            "all_provider_transport_attempts_joined": unobserved_transport_requests == 0,
            "provider_usage_complete": provider_usage_complete,
            "all_tool_requests_resolved": unresolved_tools == 0,
        },
        "provider": {
            "requests": provider["requests"],
            "responses": provider["responses"],
            "failures": provider["failures"],
            "transport_attempts": provider["transport_attempts"],
            "unobserved_transport_request_count": unobserved_transport_requests,
            "transport_capture_supported": transport_supported,
            "transport_capture_complete": transport_complete,
            "transport_elapsed_s": transport_elapsed_s,
            "transport_stdout_total_bytes": transport_stdout_total,
            "transport_stderr_total_bytes": transport_stderr_total,
            "usage_status": usage_status,
            "unknown_usage_fields": sorted(unknown_usage_fields),
            "unknown_optional_usage_fields": sorted(unknown_optional_usage_fields),
            "usage": usage_totals,
        },
        "tools": {
            "requests": tool["requests"],
            "results": tool["results"],
            "failures": tool["failures"],
            "captures": tool["captures"],
            "unresolved_requests": unresolved_tools,
            "capture_complete": tool_capture_complete,
            "capture_truncated_bytes": tool_capture_truncated,
            "capture_total_bytes": tool_capture_total,
            "capture_captured_bytes": tool_capture_captured,
        },
    }


def _response_usage(payload: Mapping[str, Any]) -> dict[str, int | None]:
    response = payload.get("response")
    if not isinstance(response, Mapping):
        raise EvidenceExportError("provider_response response must be an object")
    usage = response.get("usage")
    if usage is None:
        return dict.fromkeys(_USAGE_FIELDS)
    if not isinstance(usage, Mapping):
        raise EvidenceExportError("response usage must be an object")
    result = {key: _optional_int(usage.get(key), key) for key in _USAGE_FIELDS}
    result["reasoning_tokens"] = _reasoning_tokens(usage)
    return result


def _reasoning_tokens(usage: Mapping[str, Any]) -> int | None:
    details = usage.get("completion_tokens_details")
    detail_value = None
    if details is not None:
        if not isinstance(details, Mapping):
            raise EvidenceExportError("completion_tokens_details must be an object")
        detail_value = _optional_int(
            details.get("reasoning_tokens"), "completion_tokens_details.reasoning_tokens"
        )
    direct_value = _optional_int(usage.get("reasoning_tokens"), "reasoning_tokens")
    if (
        detail_value is not None
        and direct_value is not None
        and detail_value != direct_value
    ):
        raise EvidenceExportError("reasoning_tokens sources disagree")
    return detail_value if detail_value is not None else direct_value


def _transport_metadata(payload: Mapping[str, Any]) -> dict[str, Any]:
    stdout = _stream_capture_metadata(payload.get("stdout"), "stdout")
    stderr = _stream_capture_metadata(payload.get("stderr"), "stderr")
    return {
        "transport_attempt": _positive_int(
            payload.get("transport_attempt"), "transport_attempt"
        ),
        "returncode": _signed_int(payload["returncode"], "returncode")
        if payload.get("returncode") is not None else None,
        "error_type": _optional_string(payload.get("error_type"), "error_type"),
        "capture_complete": _bool(payload.get("capture_complete"), "capture_complete"),
        "elapsed_s": _optional_number(payload.get("elapsed_s"), "elapsed_s"),
        "stdout": stdout,
        "stderr": stderr,
    }


def _stream_capture_metadata(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise EvidenceExportError(f"{label} capture must be an object")
    total = _int(value.get("total_bytes"), f"{label}.total_bytes")
    retained = _int(value.get("retained_bytes"), f"{label}.retained_bytes")
    truncated = _int(value.get("truncated_bytes"), f"{label}.truncated_bytes")
    if retained + truncated != total:
        raise EvidenceExportError(f"{label} byte counts do not join")
    return {
        "encoding": _string(value.get("encoding"), f"{label}.encoding"),
        "bytes_sha256": _optional_sha256(
            value.get("bytes_sha256"), f"{label}.bytes_sha256"
        ),
        "total_bytes": total,
        "retained_bytes": retained,
        "truncated_bytes": truncated,
    }


def _tool_output_capture_metadata(payload: Mapping[str, Any]) -> dict[str, Any]:
    total = _int(payload.get("output_total_bytes"), "output_total_bytes")
    captured = _int(payload.get("output_captured_bytes"), "output_captured_bytes")
    truncated = _int(payload.get("output_truncated_bytes"), "output_truncated_bytes")
    if captured + truncated != total:
        raise EvidenceExportError("tool output byte counts do not join")
    return {
        "schema_version": _const_string(
            payload.get("schema_version"),
            "vabench-private-tool-output-capture-v1",
            "schema_version",
        ),
        "tool_name": _string(payload.get("tool_name"), "tool_name"),
        "returncode": _signed_int(payload.get("returncode"), "returncode"),
        "elapsed_s": _optional_number(payload.get("elapsed_s"), "elapsed_s"),
        "output_sha256": _optional_sha256(
            payload.get("output_sha256"), "output_sha256"
        ),
        "output_total_bytes": total,
        "output_captured_bytes": captured,
        "output_truncated_bytes": truncated,
        "output_capture_complete": _bool(
            payload.get("output_capture_complete"), "output_capture_complete"
        ),
        "output_capture_eof": _bool(
            payload.get("output_capture_eof"), "output_capture_eof"
        ),
        "output_capture_read_error": _bool(
            payload.get("output_capture_read_error"), "output_capture_read_error"
        ),
        "retained_output_scope": _string(
            payload.get("retained_output_scope"), "retained_output_scope"
        ),
    }


def _safe_counter_map(value: Any, label: str) -> dict[str, int]:
    if not isinstance(value, Mapping):
        raise EvidenceExportError(f"{label} must be an object")
    result: dict[str, int] = {}
    for key, item in value.items():
        counter = _string(key, f"{label} key")
        if counter not in _BUDGET_COUNTER_FIELDS:
            raise EvidenceExportError(f"unknown budget counter: {counter}")
        result[counter] = _int(item, f"{label}.{counter}")
    return result


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise EvidenceExportError(f"{label} must be a non-empty string")
    return value


def _optional_string(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return _string(value, label)


def _optional_sha256(value: Any, label: str) -> str | None:
    if value is None:
        return None
    text = _string(value, label)
    if not _SHA256_RE.match(text):
        raise EvidenceExportError(f"{label} must be sha256 hex64")
    return text


def _optional_string_sha256(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(_string(value, label).encode("utf-8")).hexdigest()


def _const_string(value: Any, expected: str, label: str) -> str:
    text = _string(value, label)
    if text != expected:
        raise EvidenceExportError(f"{label} must be {expected}")
    return text


def _bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise EvidenceExportError(f"{label} must be a boolean")
    return value


def _int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise EvidenceExportError(f"{label} must be a non-negative integer")
    if value < 0:
        raise EvidenceExportError(f"{label} must be a non-negative integer")
    return value


def _signed_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise EvidenceExportError(f"{label} must be an integer process status")
    return value


def _positive_int(value: Any, label: str) -> int:
    number = _int(value, label)
    if number <= 0:
        raise EvidenceExportError(f"{label} must be a positive integer")
    return number


def _optional_int(value: Any, label: str) -> int | None:
    if value is None:
        return None
    return _int(value, label)


def _optional_number(value: Any, label: str) -> int | float | None:
    if value is None:
        return None
    return _number(value, label)


def _number(value: Any, label: str) -> int | float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise EvidenceExportError(f"{label} must be a finite non-negative number")
    if not math.isfinite(value) or value < 0:
        raise EvidenceExportError(f"{label} must be a finite non-negative number")
    return value
