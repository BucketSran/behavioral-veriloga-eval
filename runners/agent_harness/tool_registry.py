"""Fail-closed tool capability registry for agent-harness episodes."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal, TypeAlias

ToolLifecycle: TypeAlias = Literal["active", "reserved"]
ToolVisibility: TypeAlias = Literal["model_visible", "harness_internal"]


class ToolRegistryError(ValueError):
    """A classified rejection from the trusted tool registry."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True, slots=True)
class ToolCapability:
    """One resolved, callable tool capability."""

    tool_id: str
    tool_name: str
    tool_version: str
    model_visibility: ToolVisibility
    budget_class: str
    state_effect: str
    candidate_effect: str
    argument_schema: Mapping[str, Any]
    argument_schema_sha256: str
    observation_schema: Mapping[str, Any]
    observation_schema_sha256: str
    evidence_policy: Mapping[str, Any]
    evidence_policy_sha256: str
    handler_id: str
    descriptor_sha256: str


@dataclass(frozen=True, slots=True)
class EffectiveToolset:
    """The exact tool set exposed to one authority boundary."""

    capabilities: tuple[ToolCapability, ...]
    effective_capability_sha256: str

    @property
    def accepted_tool_names(self) -> frozenset[str]:
        return frozenset(capability.tool_name for capability in self.capabilities)


class ToolRegistry:
    """Resolve trusted descriptors into condition-specific capabilities."""

    def __init__(self, descriptors: Sequence[Mapping[str, Any]]) -> None:
        self._descriptors = tuple(_normalize_descriptor(item) for item in descriptors)
        self._by_tool_name = _index_by_tool_name(self._descriptors)

    def resolve(
        self,
        *,
        condition_id: str,
        model_visible: bool,
    ) -> EffectiveToolset:
        """Return active callable tools available to the requested boundary."""
        _require_nonempty_string(condition_id, field_name="condition_id")
        capabilities = tuple(
            sorted(
                (
                    _capability_from_descriptor(descriptor)
                    for descriptor in self._descriptors
                    if _is_resolved(
                        descriptor,
                        condition_id=condition_id,
                        model_visible=model_visible,
                    )
                ),
                key=lambda capability: (capability.tool_name, capability.tool_id),
            )
        )
        canonical = [
            {
                "tool_id": capability.tool_id,
                "tool_name": capability.tool_name,
                "tool_version": capability.tool_version,
                "model_visibility": capability.model_visibility,
                "budget_class": capability.budget_class,
                "state_effect": capability.state_effect,
                "candidate_effect": capability.candidate_effect,
                "argument_schema_sha256": capability.argument_schema_sha256,
                "observation_schema_sha256": capability.observation_schema_sha256,
                "evidence_policy_sha256": capability.evidence_policy_sha256,
                "handler_id": capability.handler_id,
                "descriptor_sha256": capability.descriptor_sha256,
            }
            for capability in capabilities
        ]
        return EffectiveToolset(
            capabilities=capabilities,
            effective_capability_sha256=_canonical_sha256(canonical),
        )

    def authorize(
        self,
        tool_name: str,
        *,
        condition_id: str,
        model_visible: bool,
    ) -> ToolCapability:
        """Return the trusted capability for one tool call or fail closed."""
        _require_nonempty_string(tool_name, field_name="tool_name")
        _require_nonempty_string(condition_id, field_name="condition_id")
        descriptor = self._by_tool_name.get(tool_name)
        if descriptor is None:
            raise ToolRegistryError(
                "unknown_tool",
                f"tool is not registered in this harness registry: {tool_name}",
            )
        if descriptor["lifecycle"] == "reserved":
            raise ToolRegistryError(
                "reserved_tool",
                f"tool is reserved and has no callable authority: {tool_name}",
            )
        if not _condition_matches(descriptor, condition_id):
            raise ToolRegistryError(
                "condition_ineligible",
                f"tool is not enabled for condition: {condition_id}",
            )
        if model_visible and descriptor["model_visibility"] != "model_visible":
            raise ToolRegistryError(
                "not_model_visible",
                f"tool must not be exposed to the model: {tool_name}",
            )
        if not isinstance(descriptor["handler_id"], str):
            raise ToolRegistryError(
                "missing_handler",
                f"active tool has no callable handler: {tool_name}",
            )
        return _capability_from_descriptor(descriptor)


def tool_descriptor_sha256(descriptor: Mapping[str, Any]) -> str:
    """Hash one schema-shaped tool descriptor using canonical JSON ordering."""
    if not isinstance(descriptor, Mapping):
        raise TypeError("tool descriptor must be a JSON object")
    _require_canonical_json(descriptor)
    return _canonical_sha256(descriptor)


def _is_resolved(
    descriptor: Mapping[str, Any],
    *,
    condition_id: str,
    model_visible: bool,
) -> bool:
    return (
        descriptor["lifecycle"] == "active"
        and _condition_matches(descriptor, condition_id)
        and isinstance(descriptor["handler_id"], str)
        and (
            not model_visible
            or descriptor["model_visibility"] == "model_visible"
        )
    )


def _condition_matches(descriptor: Mapping[str, Any], condition_id: str) -> bool:
    allowed = descriptor["allowed_conditions"]
    return "*" in allowed or condition_id in allowed


def _capability_from_descriptor(descriptor: Mapping[str, Any]) -> ToolCapability:
    handler_id = descriptor["handler_id"]
    if not isinstance(handler_id, str):
        raise ToolRegistryError(
            "missing_handler",
            f"active tool has no callable handler: {descriptor['tool_name']}",
        )
    return ToolCapability(
        tool_id=descriptor["tool_id"],
        tool_name=descriptor["tool_name"],
        tool_version=descriptor["tool_version"],
        model_visibility=descriptor["model_visibility"],
        budget_class=descriptor["budget_class"],
        state_effect=descriptor["state_effect"],
        candidate_effect=descriptor["candidate_effect"],
        argument_schema=descriptor["argument_schema"],
        argument_schema_sha256=_canonical_sha256(descriptor["argument_schema"]),
        observation_schema=descriptor["observation_schema"],
        observation_schema_sha256=_canonical_sha256(descriptor["observation_schema"]),
        evidence_policy=descriptor["evidence_policy"],
        evidence_policy_sha256=_canonical_sha256(descriptor["evidence_policy"]),
        handler_id=handler_id,
        descriptor_sha256=tool_descriptor_sha256(descriptor),
    )


def _normalize_descriptor(descriptor: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(descriptor, Mapping):
        raise TypeError("tool descriptor must be a JSON object")
    _require_canonical_json(descriptor)
    required = {
        "schema_version",
        "tool_id",
        "tool_name",
        "tool_version",
        "lifecycle",
        "model_visibility",
        "allowed_conditions",
        "budget_class",
        "state_effect",
        "candidate_effect",
        "argument_schema",
        "observation_schema",
        "evidence_policy",
        "handler_id",
    }
    unexpected = sorted(set(descriptor) - required)
    if unexpected:
        raise ToolRegistryError(
            "unexpected_descriptor_fields",
            f"tool descriptor contains unexpected fields: {unexpected}",
        )
    missing = sorted(required - set(descriptor))
    if missing:
        raise ToolRegistryError(
            "missing_descriptor_fields",
            f"tool descriptor is missing required fields: {missing}",
        )
    if descriptor["schema_version"] != "vaevas-tool-descriptor-v1":
        raise ToolRegistryError(
            "unsupported_descriptor_schema",
            f"unsupported schema_version: {descriptor['schema_version']}",
        )
    for field_name in ("tool_id", "tool_name", "tool_version"):
        _require_nonempty_string(descriptor[field_name], field_name=field_name)
    if descriptor["lifecycle"] not in {"active", "reserved"}:
        raise ToolRegistryError(
            "invalid_lifecycle",
            f"unsupported tool lifecycle: {descriptor['lifecycle']}",
        )
    if descriptor["model_visibility"] not in {
        "model_visible",
        "harness_internal",
    }:
        raise ToolRegistryError(
            "invalid_visibility",
            f"unsupported tool visibility: {descriptor['model_visibility']}",
        )
    if descriptor["budget_class"] not in {
        "no_budget",
        "tool_call",
        "public_validation",
        "submission",
        "reserved",
    }:
        raise ToolRegistryError(
            "invalid_budget_class",
            f"unsupported tool budget class: {descriptor['budget_class']}",
        )
    if descriptor["state_effect"] not in {
        "read_only",
        "candidate_mutation",
        "terminal_submission",
    }:
        raise ToolRegistryError(
            "invalid_state_effect",
            f"unsupported tool state effect: {descriptor['state_effect']}",
        )
    if descriptor["candidate_effect"] not in {"none", "read", "mutate", "freeze"}:
        raise ToolRegistryError(
            "invalid_candidate_effect",
            f"unsupported tool candidate effect: {descriptor['candidate_effect']}",
        )
    for schema_field in ("argument_schema", "observation_schema"):
        io_schema = descriptor[schema_field]
        if not isinstance(io_schema, Mapping) or io_schema.get("type") != "object":
            raise ToolRegistryError(
                "invalid_io_schema",
                f"{schema_field} must declare root type object",
            )
    allowed_conditions = descriptor["allowed_conditions"]
    if (
        not isinstance(allowed_conditions, Sequence)
        or isinstance(allowed_conditions, (str, bytes))
        or not allowed_conditions
        or any(
            not isinstance(condition, str) or not condition.strip()
            for condition in allowed_conditions
        )
    ):
        raise ToolRegistryError(
            "invalid_conditions",
            "allowed_conditions must be a non-empty string array",
        )
    if len(set(allowed_conditions)) != len(allowed_conditions):
        raise ToolRegistryError(
            "duplicate_conditions",
            "allowed_conditions must not contain duplicates",
        )
    if "*" in allowed_conditions and len(allowed_conditions) > 1:
        raise ToolRegistryError(
            "ambiguous_conditions",
            "wildcard allowed_conditions must not be mixed with explicit conditions",
        )
    _require_evidence_policy(descriptor["evidence_policy"])
    handler_id = descriptor["handler_id"]
    if descriptor["lifecycle"] == "active":
        _require_nonempty_string(handler_id, field_name="handler_id")
    elif handler_id is not None:
        raise ToolRegistryError(
            "reserved_tool_handler",
            "reserved tool descriptors must not declare a handler",
        )
    return _freeze_json(dict(descriptor))


def _require_evidence_policy(value: object) -> None:
    expected = {
        "records_private_evidence",
        "may_enter_model_observation",
        "may_enter_shared_memory",
        "requires_candidate_binding",
    }
    if not isinstance(value, Mapping):
        raise ToolRegistryError(
            "invalid_evidence_policy",
            "evidence_policy must be a JSON object",
        )
    if set(value) != expected:
        raise ToolRegistryError(
            "invalid_evidence_policy",
            "evidence_policy must contain exactly the required boolean fields",
        )
    if any(not isinstance(item, bool) for item in value.values()):
        raise ToolRegistryError(
            "invalid_evidence_policy",
            "evidence_policy values must be booleans",
        )


def _index_by_tool_name(
    descriptors: Sequence[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    by_tool_name: dict[str, Mapping[str, Any]] = {}
    by_tool_id: set[str] = set()
    for descriptor in descriptors:
        tool_id = descriptor["tool_id"]
        if tool_id in by_tool_id:
            raise ToolRegistryError(
                "duplicate_tool_id",
                f"duplicate tool descriptor id: {tool_id}",
            )
        by_tool_id.add(tool_id)
        tool_name = descriptor["tool_name"]
        if tool_name in by_tool_name:
            raise ToolRegistryError(
                "duplicate_tool",
                f"duplicate tool descriptor: {tool_name}",
            )
        by_tool_name[tool_name] = descriptor
    return by_tool_name


def _canonical_sha256(value: Any) -> str:
    canonical = json.dumps(
        _json_value(value),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze_json(item) for key, item in value.items()}
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(_freeze_json(item) for item in value)
    return value


def _json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_json_value(item) for item in value]
    return value


def _require_canonical_json(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("tool descriptor JSON object keys must be strings")
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
            raise ValueError("tool descriptor JSON numbers must be finite")
        return
    raise TypeError(
        f"tool descriptor contains a non-JSON value: {type(value).__name__}"
    )


def _require_nonempty_string(value: object, *, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ToolRegistryError(
            "invalid_string",
            f"{field_name} must be a non-empty string",
        )
