"""Fail-closed normalization from untrusted model proposals to trusted actions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
import math
from typing import Any, Literal, TypeAlias

from .state import AgentAction


ProposalFormat: TypeAlias = Literal["native_tool_calls", "strict_json"]


class ProposalNormalizationError(ValueError):
    """A classified fail-closed rejection of an untrusted proposal."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True, slots=True)
class ProposalEnvelope:
    """Harness-owned identity and syntax policy for one proposed action."""

    action_id: str
    source_backend: str
    accepted_tool_names: frozenset[str]
    proposal_format: ProposalFormat
    candidate_tree_sha256: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.action_id, field_name="action_id")
        _require_nonempty_string(self.source_backend, field_name="source_backend")
        if self.proposal_format not in {"native_tool_calls", "strict_json"}:
            raise ValueError(f"unsupported proposal format: {self.proposal_format}")
        if not isinstance(self.accepted_tool_names, frozenset):
            raise TypeError("accepted_tool_names must be a frozenset")
        for tool_name in self.accepted_tool_names:
            _require_nonempty_string(tool_name, field_name="accepted tool name")
        if self.candidate_tree_sha256 is not None and (
            len(self.candidate_tree_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in self.candidate_tree_sha256
            )
        ):
            raise ValueError(
                "candidate_tree_sha256 must be a lowercase SHA-256 digest"
            )


def normalize_proposal(
    envelope: ProposalEnvelope,
    proposal: object,
) -> AgentAction:
    """Normalize exactly one untrusted proposal without executing its tool."""
    if envelope.proposal_format == "native_tool_calls":
        tool_name, arguments = _parse_native_tool_calls(proposal)
    elif envelope.proposal_format == "strict_json":
        tool_name, arguments = _parse_strict_json(proposal)
    else:
        raise ProposalNormalizationError(
            "unsupported_format",
            f"unsupported proposal format: {envelope.proposal_format}",
        )
    if tool_name not in envelope.accepted_tool_names:
        raise ProposalNormalizationError(
            "unknown_tool",
            f"tool is not accepted by this proposal envelope: {tool_name}",
        )
    return AgentAction(
        action_id=envelope.action_id,
        tool_name=tool_name,
        arguments=arguments,
        source_backend=envelope.source_backend,
        candidate_tree_sha256=envelope.candidate_tree_sha256,
    )


def _parse_native_tool_calls(proposal: object) -> tuple[str, Mapping[str, Any]]:
    if not isinstance(proposal, Sequence) or isinstance(proposal, (str, bytes)):
        raise ProposalNormalizationError(
            "invalid_native_transport",
            "native_tool_calls proposal must be a sequence",
        )
    if len(proposal) != 1:
        raise ProposalNormalizationError(
            "action_count",
            "native_tool_calls proposal must contain exactly one call",
        )
    call = proposal[0]
    if not isinstance(call, Mapping):
        raise ProposalNormalizationError(
            "invalid_call_shape",
            "native tool call must be an object",
        )
    _require_exact_fields(
        call,
        {"type", "function"},
        optional={"id"},
        context="native tool call",
    )
    if "id" in call:
        _require_provider_call_id(call["id"])
    if call["type"] != "function":
        raise ProposalNormalizationError(
            "invalid_call_type",
            "native tool call type must be function",
        )
    function = call["function"]
    if not isinstance(function, Mapping):
        raise ProposalNormalizationError(
            "invalid_function_shape",
            "native function call must be an object",
        )
    _require_exact_fields(
        function,
        {"name", "arguments"},
        context="native function call",
    )
    tool_name = function["name"]
    _require_proposal_tool_name(tool_name)
    arguments = _load_json_object(function["arguments"])
    return tool_name, arguments


def _parse_strict_json(proposal: object) -> tuple[str, Mapping[str, Any]]:
    document = _load_json_object(proposal)
    _require_exact_fields(
        document,
        {"tool_name", "arguments"},
        context="strict JSON proposal",
    )
    tool_name = document["tool_name"]
    arguments = document["arguments"]
    _require_proposal_tool_name(tool_name)
    if not isinstance(arguments, Mapping):
        raise ProposalNormalizationError(
            "invalid_arguments",
            "arguments must be a JSON object",
        )
    return tool_name, arguments


def _load_json_object(value: object) -> Mapping[str, Any]:
    if not isinstance(value, str):
        raise ProposalNormalizationError(
            "invalid_json_transport",
            "JSON proposal content must be a string",
        )
    try:
        document = json.loads(
            value,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite_number,
            parse_float=_parse_finite_float,
        )
    except ProposalNormalizationError:
        raise
    except json.JSONDecodeError as exc:
        raise ProposalNormalizationError(
            "malformed_json",
            f"proposal is not standalone JSON: {exc.msg}",
        ) from exc
    if not isinstance(document, Mapping):
        raise ProposalNormalizationError(
            "invalid_json_root",
            "JSON proposal content must be an object",
        )
    return document


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {}
    for key, value in pairs:
        if key in document:
            raise ProposalNormalizationError(
                "duplicate_key",
                f"duplicate JSON object key: {key}",
            )
        document[key] = value
    return document


def _reject_nonfinite_number(token: str) -> None:
    raise ProposalNormalizationError(
        "invalid_number",
        f"non-finite JSON number is forbidden: {token}",
    )


def _parse_finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise ProposalNormalizationError(
            "invalid_number",
            f"JSON number exceeds the finite range: {token}",
        )
    return value


def _require_exact_fields(
    document: Mapping[str, Any],
    expected: set[str],
    *,
    optional: set[str] | None = None,
    context: str,
) -> None:
    optional = optional or set()
    actual = set(document)
    unexpected = sorted(actual - expected - optional)
    if unexpected:
        raise ProposalNormalizationError(
            "unexpected_fields",
            f"{context} contains unexpected fields: {unexpected}",
        )
    missing = sorted(expected - actual)
    if missing:
        raise ProposalNormalizationError(
            "missing_fields",
            f"{context} is missing required fields: {missing}",
        )


def _require_provider_call_id(value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ProposalNormalizationError(
            "invalid_provider_call_id",
            "provider call id must be a non-empty string when present",
        )


def _require_proposal_tool_name(value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ProposalNormalizationError(
            "invalid_tool_name",
            "tool name must be a non-empty string",
        )


def _require_nonempty_string(value: object, *, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
