"""Memory snapshots and candidate lineage for round-based harness evolution."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, TypeAlias

MemorySourceKind: TypeAlias = Literal[
    "candidate_summary",
    "public_validation",
    "public_tool_observation",
]
MemoryEntry: TypeAlias = Mapping[str, Any]
CandidateStatus: TypeAlias = Literal[
    "active",
    "rejected",
    "selected",
    "frozen",
    "failed",
]
MutationKind: TypeAlias = Literal[
    "seed",
    "create",
    "refine",
    "failed_mutation",
]

_ALLOWED_MEMORY_SOURCE_KINDS = frozenset(
    {"candidate_summary", "public_validation", "public_tool_observation"}
)
_ALLOWED_CANDIDATE_STATUSES = frozenset(
    {"active", "rejected", "selected", "frozen", "failed"}
)
_ALLOWED_MUTATION_KINDS = frozenset(
    {"seed", "create", "refine", "failed_mutation"}
)
_MEMORY_REDACTION_POLICY = "public-feedback-redaction-v1"
_FORBIDDEN_MEMORY_SUMMARY_KEY_TOKENS = frozenset(
    {
        "auth",
        "checker",
        "credential",
        "final",
        "password",
        "private",
        "secret",
        "token",
        "trusted",
    }
)
_FORBIDDEN_MEMORY_SUMMARY_COMPOUNDS = frozenset(
    {
        "api_key",
        "apikey",
        "chain_of_thought",
        "provider_response",
        "raw_cot",
        "score_sidecar",
    }
)


@dataclass(frozen=True, slots=True)
class MemorySnapshot:
    snapshot_id: str
    episode_id: str
    attempt_id: str
    task_id: str
    condition: str
    round_index: int
    parent_snapshot_sha256: str | None
    retry_parent_attempt_id: str | None
    entries: tuple[Mapping[str, Any], ...]
    schema_version: str = field(default="vaevas-memory-snapshot-v1", init=False)
    redaction_policy: str = field(default=_MEMORY_REDACTION_POLICY, init=False)
    snapshot_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        for field_name in ("snapshot_id", "episode_id", "attempt_id", "task_id", "condition"):
            _require_nonempty_string(getattr(self, field_name), field_name=field_name)
        _require_nonnegative_int(self.round_index, field_name="round_index")
        _require_optional_sha256(
            self.parent_snapshot_sha256,
            field_name="parent_snapshot_sha256",
        )
        if self.retry_parent_attempt_id is not None:
            _require_nonempty_string(
                self.retry_parent_attempt_id,
                field_name="retry_parent_attempt_id",
            )
            if (
                self.round_index != 0
                or self.parent_snapshot_sha256 is not None
                or self.entries
            ):
                raise ValueError(
                    "fresh retry memory requires round_index=0, "
                    "parent_snapshot_sha256=null, and entries=[]"
                )
        entries = tuple(
            sorted(
                (_normalize_memory_entry(entry) for entry in self.entries),
                key=lambda entry: (
                    entry["entry_id"],
                    entry["source_kind"],
                    entry["source_event_sha256"],
                ),
            )
        )
        entry_ids = [entry["entry_id"] for entry in entries]
        if len(set(entry_ids)) != len(entry_ids):
            raise ValueError("duplicate memory entry_id")
        object.__setattr__(self, "entries", entries)
        object.__setattr__(self, "snapshot_sha256", _self_hash(self.to_document()))

    def to_document(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "redaction_policy": self.redaction_policy,
            "snapshot_id": self.snapshot_id,
            "snapshot_sha256": getattr(self, "snapshot_sha256", None),
            "episode_id": self.episode_id,
            "attempt_id": self.attempt_id,
            "task_id": self.task_id,
            "condition": self.condition,
            "round_index": self.round_index,
            "parent_snapshot_sha256": self.parent_snapshot_sha256,
            "retry_parent_attempt_id": self.retry_parent_attempt_id,
            "entries": [_json_ready(entry) for entry in self.entries],
        }


@dataclass(frozen=True, slots=True)
class CandidateLineage:
    candidate_id: str
    episode_id: str
    attempt_id: str
    task_id: str
    condition: str
    round_index: int
    candidate_tree_sha256: str
    artifact_parent_candidate_id: str | None
    influence_candidate_ids: tuple[str, ...]
    mutation_kind: MutationKind
    source_event_sha256: str
    status: CandidateStatus
    failure_reason: str | None = None
    schema_version: str = field(default="vaevas-candidate-lineage-v1", init=False)
    candidate_lineage_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "episode_id", "attempt_id", "task_id", "condition"):
            _require_nonempty_string(getattr(self, field_name), field_name=field_name)
        _require_nonnegative_int(self.round_index, field_name="round_index")
        _require_sha256(self.candidate_tree_sha256, field_name="candidate_tree_sha256")
        _require_sha256(self.source_event_sha256, field_name="source_event_sha256")
        if self.artifact_parent_candidate_id is not None:
            if not isinstance(self.artifact_parent_candidate_id, str):
                raise TypeError("artifact_parent_candidate_id must be a string or None")
            _require_nonempty_string(
                self.artifact_parent_candidate_id,
                field_name="artifact_parent_candidate_id",
            )
            if self.artifact_parent_candidate_id == self.candidate_id:
                raise ValueError("candidate cannot be its own artifact parent")
        if not isinstance(self.influence_candidate_ids, Sequence) or isinstance(
            self.influence_candidate_ids,
            (str, bytes),
        ):
            raise TypeError("influence_candidate_ids must be a sequence of strings")
        influence_ids = tuple(self.influence_candidate_ids)
        if len(set(influence_ids)) != len(influence_ids):
            raise ValueError("influence_candidate_ids must be unique")
        for influence_id in influence_ids:
            _require_nonempty_string(
                influence_id,
                field_name="influence_candidate_ids",
            )
            if influence_id == self.candidate_id:
                raise ValueError("candidate cannot influence itself")
        if self.mutation_kind not in _ALLOWED_MUTATION_KINDS:
            raise ValueError("unsupported mutation_kind")
        if self.status not in _ALLOWED_CANDIDATE_STATUSES:
            raise ValueError("unsupported candidate status")
        if self.mutation_kind == "seed" and (
            self.artifact_parent_candidate_id is not None or influence_ids
        ):
            raise ValueError("seed candidates cannot have parent or influence refs")
        if self.mutation_kind == "seed" and self.round_index != 0:
            raise ValueError("seed candidates must start at round_index=0")
        if self.mutation_kind == "failed_mutation" and (
            self.artifact_parent_candidate_id is None
        ):
            raise ValueError("failed_mutation requires an artifact parent")
        if self.mutation_kind == "refine" and self.artifact_parent_candidate_id is None:
            raise ValueError("refine requires an artifact parent")
        if self.mutation_kind == "create" and self.artifact_parent_candidate_id is not None:
            raise ValueError("create candidates cannot have an artifact parent")
        if self.mutation_kind == "failed_mutation" and self.status != "failed":
            raise ValueError("failed_mutation records must have failed status")
        if self.status == "failed" and self.mutation_kind != "failed_mutation":
            raise ValueError("failed candidates must use failed_mutation")
        if self.status == "failed":
            _require_nonempty_string(self.failure_reason, field_name="failure_reason")
        elif self.failure_reason is not None:
            raise ValueError("failure_reason is allowed only for failed candidates")
        object.__setattr__(self, "influence_candidate_ids", influence_ids)
        object.__setattr__(
            self,
            "candidate_lineage_sha256",
            candidate_lineage_sha256(self.to_document()),
        )

    def to_document(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "candidate_id": self.candidate_id,
            "candidate_lineage_sha256": getattr(
                self,
                "candidate_lineage_sha256",
                None,
            ),
            "episode_id": self.episode_id,
            "attempt_id": self.attempt_id,
            "task_id": self.task_id,
            "condition": self.condition,
            "round_index": self.round_index,
            "candidate_tree_sha256": self.candidate_tree_sha256,
            "artifact_parent_candidate_id": self.artifact_parent_candidate_id,
            "influence_candidate_ids": list(self.influence_candidate_ids),
            "mutation_kind": self.mutation_kind,
            "source_event_sha256": self.source_event_sha256,
            "status": self.status,
            "failure_reason": self.failure_reason,
        }

    def with_mutation(
        self,
        *,
        candidate_tree_sha256: str,
        source_event_sha256: str,
        candidate_id: str | None = None,
        mutation_kind: MutationKind = "refine",
    ) -> CandidateLineage:
        if self.status not in {"active", "selected"}:
            raise ValueError(f"{self.status} candidate cannot be mutated")
        if mutation_kind != "refine":
            raise ValueError("with_mutation supports only refine")
        return CandidateLineage(
            candidate_id=candidate_id or f"{self.candidate_id}-next",
            episode_id=self.episode_id,
            attempt_id=self.attempt_id,
            task_id=self.task_id,
            condition=self.condition,
            round_index=self.round_index + 1,
            candidate_tree_sha256=candidate_tree_sha256,
            artifact_parent_candidate_id=self.candidate_id,
            influence_candidate_ids=(),
            mutation_kind=mutation_kind,
            source_event_sha256=source_event_sha256,
            status="active",
        )

    def with_failed_mutation(
        self,
        *,
        candidate_id: str,
        source_event_sha256: str,
        failure_reason: str,
    ) -> CandidateLineage:
        if self.status not in {"active", "selected"}:
            raise ValueError(f"{self.status} candidate cannot be mutated")
        return CandidateLineage(
            candidate_id=candidate_id,
            episode_id=self.episode_id,
            attempt_id=self.attempt_id,
            task_id=self.task_id,
            condition=self.condition,
            round_index=self.round_index + 1,
            candidate_tree_sha256=self.candidate_tree_sha256,
            artifact_parent_candidate_id=self.candidate_id,
            influence_candidate_ids=(),
            mutation_kind="failed_mutation",
            source_event_sha256=source_event_sha256,
            status="failed",
            failure_reason=failure_reason,
        )


def freeze_memory_snapshot(
    *,
    snapshot_id: str,
    episode_id: str,
    attempt_id: str,
    task_id: str,
    condition: str,
    round_index: int,
    parent_snapshot_sha256: str | None,
    entries: Sequence[Mapping[str, Any]],
    retry_parent_attempt_id: str | None = None,
) -> MemorySnapshot:
    return MemorySnapshot(
        snapshot_id=snapshot_id,
        episode_id=episode_id,
        attempt_id=attempt_id,
        task_id=task_id,
        condition=condition,
        round_index=round_index,
        parent_snapshot_sha256=parent_snapshot_sha256,
        retry_parent_attempt_id=retry_parent_attempt_id,
        entries=tuple(entries),
    )


def candidate_lineage_sha256(document: Mapping[str, Any]) -> str:
    if not isinstance(document, Mapping):
        raise TypeError("candidate lineage document must be a JSON object")
    _require_canonical_json(document, label="candidate lineage")
    return _self_hash(document)


def validate_candidate_lineage_graph(
    records: Sequence[CandidateLineage],
    *,
    require_parent_before_child: bool = True,
) -> None:
    seen: set[str] = set()
    by_id: dict[str, CandidateLineage] = {}
    expected_scope: tuple[str, str, str, str] | None = None
    for record in records:
        scope = (record.episode_id, record.attempt_id, record.task_id, record.condition)
        if expected_scope is None:
            expected_scope = scope
        elif scope != expected_scope:
            raise ValueError(
                "candidate lineage graph must use the same "
                "episode/attempt/task/condition"
            )
        if record.candidate_id in by_id:
            raise ValueError(f"duplicate candidate lineage: {record.candidate_id}")
        by_id[record.candidate_id] = record
        parent_id = record.artifact_parent_candidate_id
        if require_parent_before_child and parent_id is not None and parent_id not in seen:
            raise ValueError("candidate artifact parent must appear before child")
        for influence_id in record.influence_candidate_ids:
            if require_parent_before_child and influence_id not in seen:
                raise ValueError("candidate influence must exist before child")
        seen.add(record.candidate_id)
    for record in records:
        _detect_parent_cycle(record.candidate_id, by_id, visiting=set(), visited=set())
    for record in records:
        _detect_any_reference_cycle(record.candidate_id, by_id, visiting=set(), visited=set())
    for record in records:
        _validate_record_references(record, by_id)


def _validate_record_references(
    record: CandidateLineage,
    by_id: Mapping[str, CandidateLineage],
) -> None:
    reference_ids = (
        (record.artifact_parent_candidate_id,)
        if record.artifact_parent_candidate_id is not None
        else ()
    ) + tuple(record.influence_candidate_ids)
    for reference_id in reference_ids:
        reference = by_id.get(reference_id)
        if reference is None:
            raise ValueError("candidate reference must exist before child")
        if reference.round_index >= record.round_index:
            raise ValueError("candidate reference round must be earlier than child round")
        if reference.status == "frozen":
            raise ValueError("frozen terminal candidate cannot be referenced later")
    parent_id = record.artifact_parent_candidate_id
    if parent_id is not None and by_id[parent_id].status not in {"active", "selected"}:
        raise ValueError("candidate artifact parent status must be active or selected")
    if record.mutation_kind == "failed_mutation":
        if parent_id is None:
            raise ValueError("failed_mutation requires an artifact parent")
        parent = by_id[parent_id]
        if record.candidate_tree_sha256 != parent.candidate_tree_sha256:
            raise ValueError("failed_mutation tree hash must equal parent tree hash")


def _detect_parent_cycle(
    candidate_id: str,
    by_id: Mapping[str, CandidateLineage],
    *,
    visiting: set[str],
    visited: set[str],
) -> None:
    if candidate_id in visited:
        return
    if candidate_id in visiting:
        raise ValueError("candidate lineage cycle detected")
    visiting.add(candidate_id)
    parent_id = by_id[candidate_id].artifact_parent_candidate_id
    if parent_id in by_id:
        _detect_parent_cycle(parent_id, by_id, visiting=visiting, visited=visited)
    visiting.remove(candidate_id)
    visited.add(candidate_id)


def _detect_any_reference_cycle(
    candidate_id: str,
    by_id: Mapping[str, CandidateLineage],
    *,
    visiting: set[str],
    visited: set[str],
) -> None:
    if candidate_id in visited:
        return
    if candidate_id in visiting:
        raise ValueError("candidate lineage cycle detected")
    visiting.add(candidate_id)
    record = by_id[candidate_id]
    reference_ids = tuple(
        reference_id
        for reference_id in (
            record.artifact_parent_candidate_id,
            *record.influence_candidate_ids,
        )
        if reference_id is not None and reference_id in by_id
    )
    for reference_id in reference_ids:
        _detect_any_reference_cycle(reference_id, by_id, visiting=visiting, visited=visited)
    visiting.remove(candidate_id)
    visited.add(candidate_id)


def _normalize_memory_entry(entry: Mapping[str, Any]) -> Mapping[str, Any]:
    required = {"entry_id", "source_kind", "source_event_sha256", "summary"}
    optional = {"candidate_id", "candidate_tree_sha256"}
    missing = sorted(required - set(entry))
    if missing:
        raise ValueError(f"memory entry missing required fields: {missing}")
    extra = sorted(set(entry) - required - optional)
    if extra:
        raise ValueError(f"memory entry contains extra fields: {extra}")
    source_kind = entry["source_kind"]
    if source_kind not in _ALLOWED_MEMORY_SOURCE_KINDS:
        raise ValueError("memory snapshot may contain only public evidence")
    _require_nonempty_string(entry["entry_id"], field_name="entry_id")
    _require_sha256(entry["source_event_sha256"], field_name="source_event_sha256")
    _reject_forbidden_memory_summary_keys(entry["summary"])
    normalized: dict[str, Any] = {
        "entry_id": entry["entry_id"],
        "source_kind": source_kind,
        "source_event_sha256": entry["source_event_sha256"],
        "candidate_id": entry.get("candidate_id"),
        "candidate_tree_sha256": entry.get("candidate_tree_sha256"),
        "summary": _freeze_json_object(entry["summary"], field_name="summary"),
    }
    if normalized["candidate_id"] is not None:
        _require_nonempty_string(
            normalized["candidate_id"],
            field_name="candidate_id",
        )
    _require_optional_sha256(
        normalized["candidate_tree_sha256"],
        field_name="candidate_tree_sha256",
    )
    return MappingProxyType(normalized)


def _reject_forbidden_memory_summary_keys(value: Any, *, path: str = "summary") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("JSON object keys must be strings")
            normalized_key = key.lower().replace("-", "_")
            key_tokens = frozenset(normalized_key.split("_"))
            if (
                normalized_key in _FORBIDDEN_MEMORY_SUMMARY_COMPOUNDS
                or key_tokens & _FORBIDDEN_MEMORY_SUMMARY_KEY_TOKENS
            ):
                raise ValueError(f"forbidden memory summary key at {path}.{key}")
            _reject_forbidden_memory_summary_keys(item, path=f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, item in enumerate(value):
            _reject_forbidden_memory_summary_keys(item, path=f"{path}[{index}]")


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("JSON object keys must be strings")
            frozen[key] = _freeze_json(item)
        return MappingProxyType(frozen)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(_freeze_json(item) for item in value)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        return value
    raise TypeError(f"value is not JSON-compatible: {type(value).__name__}")


def _freeze_json_object(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a JSON object")
    return _freeze_json(value)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    return value


def _self_hash(document: Mapping[str, Any]) -> str:
    payload = dict(document)
    payload.pop("snapshot_sha256", None)
    payload.pop("candidate_lineage_sha256", None)
    return _canonical_sha256(_json_ready(payload))


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


def _require_nonnegative_int(value: object, *, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{field_name} must be a non-bool int")
    if value < 0:
        raise ValueError(f"{field_name} cannot be negative")


def _require_nonempty_string(value: object, *, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
