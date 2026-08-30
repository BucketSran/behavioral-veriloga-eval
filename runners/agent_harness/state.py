"""Explicit public state carried across an agent-harness episode."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any, Literal, TypeAlias


EventVisibility: TypeAlias = Literal["model", "harness", "trusted"]


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("JSON object keys must be strings")
            frozen[key] = _freeze_json(item)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        return value
    raise TypeError(f"value is not JSON-compatible: {type(value).__name__}")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    return value


def _json_sha256(value: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        _json_ready(value),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _freeze_json_object(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a JSON object")
    return _freeze_json(value)


def _require_identity(value: str, *, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must be non-empty")


def _require_optional_sha256(value: str | None, *, field_name: str) -> None:
    if value is None:
        return
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


def _require_sha256(value: str, *, field_name: str) -> None:
    if value is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    _require_optional_sha256(value, field_name=field_name)


@dataclass(frozen=True, slots=True)
class EpisodeContext:
    episode_id: str
    attempt_id: str
    task_id: str
    condition: str
    max_steps: int | None
    budget_limits: Mapping[str, int] = field(default_factory=dict)
    parent_attempt_id: str | None = None
    retry_index: int = 0
    retry_reason: str | None = None
    model_calls_before_attempt: int = 0

    def __post_init__(self) -> None:
        for field_name in ("episode_id", "attempt_id", "task_id", "condition"):
            _require_identity(getattr(self, field_name), field_name=field_name)
        if self.max_steps is not None and self.max_steps <= 0:
            raise ValueError("max_steps must be positive")
        frozen_budget_limits = _freeze_json_object(
            self.budget_limits,
            field_name="budget_limits",
        )
        for counter, value in frozen_budget_limits.items():
            _require_identity(counter, field_name="budget counter")
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("budget_limits values must be integers")
            if value < 0:
                raise ValueError("budget_limits values cannot be negative")
            if counter == "model_calls" and value == 0:
                raise ValueError("model-call limit must be positive")
        object.__setattr__(self, "budget_limits", frozen_budget_limits)
        prior = self.model_calls_before_attempt
        if type(prior) is not int or prior < 0:
            raise ValueError("model_calls_before_attempt must be a non-negative integer")
        if prior > frozen_budget_limits.get("model_calls", 0):
            raise ValueError("prior model calls exceed the configured limit")
        if self.retry_index < 0:
            raise ValueError("retry_index cannot be negative")
        if self.retry_index == 0:
            if self.parent_attempt_id is not None or self.retry_reason is not None:
                raise ValueError("an initial attempt cannot have retry lineage")
        elif self.parent_attempt_id is None or not self.retry_reason:
            raise ValueError("a retry requires parent_attempt_id and retry_reason")
        if self.parent_attempt_id == self.attempt_id:
            raise ValueError("a retry cannot reuse its parent attempt_id")

    def next_attempt(self, *, attempt_id: str, reason: str) -> "EpisodeContext":
        if attempt_id == self.attempt_id:
            raise ValueError("a retry requires a new attempt_id")
        return replace(
            self,
            attempt_id=attempt_id,
            parent_attempt_id=self.attempt_id,
            retry_index=self.retry_index + 1,
            retry_reason=reason,
        )


@dataclass(frozen=True, slots=True)
class Observation:
    observation_id: str
    tool_name: str
    status: str
    payload: Mapping[str, Any]
    candidate_tree_sha256: str | None = None
    validation_profile_sha256: str | None = None
    truncated: bool = False
    budget_delta: Mapping[str, int] = field(default_factory=dict)
    schema_version: str = field(default="vaevas-observation-v1", init=False)
    payload_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        _require_identity(self.observation_id, field_name="observation_id")
        _require_identity(self.tool_name, field_name="tool_name")
        _require_identity(self.status, field_name="status")
        _require_optional_sha256(
            self.candidate_tree_sha256,
            field_name="candidate_tree_sha256",
        )
        _require_optional_sha256(
            self.validation_profile_sha256,
            field_name="validation_profile_sha256",
        )
        frozen_payload = _freeze_json_object(self.payload, field_name="payload")
        frozen_budget_delta = _freeze_json_object(
            self.budget_delta,
            field_name="budget_delta",
        )
        for value in frozen_budget_delta.values():
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("budget_delta values must be integers")
            if value < 0:
                raise ValueError("budget_delta values cannot be negative")
        object.__setattr__(self, "payload", frozen_payload)
        object.__setattr__(self, "budget_delta", frozen_budget_delta)
        object.__setattr__(self, "payload_sha256", _json_sha256(frozen_payload))

    def to_document(self) -> dict[str, Any]:
        """Return a detached JSON-compatible canonical observation document."""
        return {
            "schema_version": self.schema_version,
            "observation_id": self.observation_id,
            "tool_name": self.tool_name,
            "status": self.status,
            "payload": _json_ready(self.payload),
            "payload_sha256": self.payload_sha256,
            "candidate_tree_sha256": self.candidate_tree_sha256,
            "validation_profile_sha256": self.validation_profile_sha256,
            "truncated": self.truncated,
            "budget_delta": _json_ready(self.budget_delta),
        }


@dataclass(frozen=True, slots=True)
class AgentAction:
    action_id: str
    tool_name: str
    arguments: Mapping[str, Any]
    source_backend: str
    candidate_tree_sha256: str | None = None
    schema_version: str = field(default="vaevas-action-v1", init=False)
    arguments_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        _require_identity(self.action_id, field_name="action_id")
        _require_identity(self.tool_name, field_name="tool_name")
        _require_identity(self.source_backend, field_name="source_backend")
        _require_optional_sha256(
            self.candidate_tree_sha256,
            field_name="candidate_tree_sha256",
        )
        frozen_arguments = _freeze_json_object(
            self.arguments,
            field_name="arguments",
        )
        object.__setattr__(self, "arguments", frozen_arguments)
        object.__setattr__(
            self,
            "arguments_sha256",
            _json_sha256(frozen_arguments),
        )

    def to_document(self) -> dict[str, Any]:
        """Return a detached JSON-compatible canonical action document."""
        return {
            "schema_version": self.schema_version,
            "action_id": self.action_id,
            "tool_name": self.tool_name,
            "arguments": _json_ready(self.arguments),
            "arguments_sha256": self.arguments_sha256,
            "source_backend": self.source_backend,
            "candidate_tree_sha256": self.candidate_tree_sha256,
        }


@dataclass(frozen=True, slots=True)
class EnvironmentStep:
    observation: Observation
    done: bool
    terminal_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ToolExecutionRejection:
    """Classified fail-closed outcome from a trusted environment dispatcher."""

    code: str
    failure_category: str
    primary_outcome: str
    message: str
    candidate_tree_sha256: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "code",
            "failure_category",
            "primary_outcome",
            "message",
        ):
            _require_identity(getattr(self, field_name), field_name=field_name)
        _require_optional_sha256(
            self.candidate_tree_sha256,
            field_name="candidate_tree_sha256",
        )


@dataclass(frozen=True, slots=True)
class FrozenSubmission:
    tree_sha256: str
    artifacts: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_sha256(self.tree_sha256, field_name="tree_sha256")
        artifacts = tuple(self.artifacts)
        if not artifacts or any(
            not isinstance(artifact, str) or not artifact.strip()
            for artifact in artifacts
        ):
            raise ValueError("artifacts must contain non-empty artifact paths")
        object.__setattr__(self, "artifacts", artifacts)


@dataclass(frozen=True, slots=True)
class CandidateSnapshot:
    """A content-addressed candidate tree frozen for public evolution only."""

    tree_sha256: str
    artifacts: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_sha256(self.tree_sha256, field_name="tree_sha256")
        artifacts = tuple(self.artifacts)
        if not artifacts or any(
            not isinstance(artifact, str) or not artifact.strip()
            for artifact in artifacts
        ):
            raise ValueError("artifacts must contain non-empty artifact paths")
        object.__setattr__(self, "artifacts", artifacts)

@dataclass(frozen=True, slots=True)
class FinalJudgment:
    status: str
    judge_engine: str
    score: float | None
    submission_tree_sha256: str

    def __post_init__(self) -> None:
        _require_identity(self.status, field_name="status")
        _require_identity(self.judge_engine, field_name="judge_engine")
        _require_sha256(
            self.submission_tree_sha256,
            field_name="submission_tree_sha256",
        )


@dataclass(frozen=True, slots=True)
class Incident:
    category: str
    message: str


@dataclass(frozen=True, slots=True)
class FailureDisposition:
    category: str
    phase: str
    message: str


@dataclass(frozen=True, slots=True)
class EpisodeResult:
    context: EpisodeContext
    primary_outcome: str
    terminal_reason: str
    submission: FrozenSubmission | None
    final_judgment: FinalJudgment | None
    incidents: tuple[Incident, ...]
    failure: FailureDisposition | None = None
    trajectory_tail_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class CandidateEpisodeResult:
    """Candidate-only terminal result for evolution branches.

    This intentionally carries no final judgment, score, or pass/fail outcome.
    The selected candidate is scored later by a separate trusted final replay.
    """

    context: EpisodeContext
    terminal_reason: str
    candidate_snapshot: CandidateSnapshot
    incidents: tuple[Incident, ...]
    failure: FailureDisposition | None = None
    trajectory_tail_sha256: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.context, EpisodeContext):
            raise TypeError("context must be an EpisodeContext")
        _require_identity(self.terminal_reason, field_name="terminal_reason")
        if not isinstance(self.candidate_snapshot, CandidateSnapshot):
            raise TypeError("candidate_snapshot must be a CandidateSnapshot")
        object.__setattr__(self, "incidents", tuple(self.incidents))
