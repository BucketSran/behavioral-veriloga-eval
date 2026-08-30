"""Bounded runtime coordinator for round-based candidate evolution.

This module does not execute model calls, tools, or final judging directly. A
caller-owned branch callback runs one independent candidate branch and returns
public-validation-bound candidate evidence. The coordinator only freezes the
round contract, allocates budgets, records write-once receipts, and delegates
selection to the existing evolution reducer.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import time
from types import MappingProxyType
from typing import Any

from .evolution_manifest import (
    build_round_snapshot,
    evolution_manifest_sha256,
    select_last_sealed_incumbent,
)
from .evolution_state import (
    CandidateLineage,
    MemorySnapshot,
    freeze_memory_snapshot,
    validate_candidate_lineage_graph,
)


BudgetMap = Mapping[str, int]
UsageMap = Mapping[str, int | None]
BranchCallback = Callable[["EvolutionBranchRequest"], Mapping[str, Any]]

_BUDGET_COUNTERS = (
    "model_calls",
    "tool_calls",
    "public_validation_calls",
)
_EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


class EvolutionRuntimeError(ValueError):
    """A classified runtime-level evolution contract violation."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class EvolutionBranchFailure(RuntimeError):
    """Callback failure that carries observed usage without declassifying output."""

    def __init__(
        self,
        message: str,
        *,
        observed_usage: Mapping[str, int | None] | None = None,
    ) -> None:
        self.observed_usage = observed_usage
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class EvolutionBranchRequest:
    """Frozen inputs for one caller-owned candidate branch."""

    manifest_sha256: str
    branch_id: str
    round_index: int
    allowance: BudgetMap
    deadline_monotonic: float | None
    public_snapshot: Mapping[str, Any]
    output_path: Path


@dataclass(frozen=True, slots=True)
class EvolutionRuntimeResult:
    """Terminal public result of a candidate-only evolution run."""

    manifest_sha256: str
    selected_candidate: Mapping[str, Any] | None
    round_snapshots: tuple[Mapping[str, Any], ...]
    memory_snapshots: tuple[Mapping[str, Any], ...]
    branch_records: tuple[Mapping[str, Any], ...]
    usage: Mapping[str, int | None]
    receipts: Mapping[str, Mapping[str, str]]
    final_judgment: None = None


def run_evolution_rounds(
    *,
    manifest: Mapping[str, Any],
    output_dir: Path,
    branch_callback: BranchCallback,
    initial_public_snapshot: Mapping[str, Any] | None = None,
    deadline_monotonic: float | None = None,
    max_workers: int | None = None,
) -> EvolutionRuntimeResult:
    """Run sealed evolution rounds and return the selected candidate only.

    Branch callbacks receive immutable public memory from the previous sealed
    round. They must create independent candidates in their fresh output path,
    run only public validation, and report bounded public metrics. The final
    judge remains outside this coordinator and is never passed to branches.
    """

    if not callable(branch_callback):
        raise TypeError("branch_callback must be callable")
    if output_dir.exists() or output_dir.is_symlink():
        raise EvolutionRuntimeError(
            "output_exists",
            "evolution output_dir must be a fresh path",
        )
    if deadline_monotonic is not None and (
        not isinstance(deadline_monotonic, (int, float))
        or not math.isfinite(deadline_monotonic)
    ):
        raise ValueError("deadline_monotonic must be finite when supplied")
    normalized_manifest = _json_ready(manifest)
    branch_roster = _branch_roster(normalized_manifest)
    manifest_hash = evolution_manifest_sha256(manifest)
    per_branch = _budget_map(normalized_manifest["budgets"]["per_branch"])
    total_budget = _budget_map(normalized_manifest["budgets"]["total"])
    _validate_total_budget_capacity(
        per_branch=per_branch,
        total_budget=total_budget,
        branch_count=len(branch_roster),
        rounds=int(normalized_manifest["rounds"]),
    )
    output_dir.mkdir(mode=0o700)
    receipts: dict[str, Mapping[str, str]] = {}
    receipts["manifest"] = _write_once_json(
        output_dir / "manifest.json",
        {
            "schema_version": "vaevas-evolution-runtime-manifest-v1",
            "manifest_sha256": manifest_hash,
            "manifest": normalized_manifest,
        },
        base_dir=output_dir,
    )
    frozen_initial = _json_ready(initial_public_snapshot or {})
    receipts["request"] = _write_once_json(
        output_dir / "request.json",
        {
            "schema_version": "vaevas-evolution-runtime-request-v1",
            "manifest_sha256": manifest_hash,
            "initial_public_snapshot_sha256": _canonical_sha256(frozen_initial),
            "deadline_monotonic": deadline_monotonic,
            "max_workers": max_workers,
        },
        base_dir=output_dir,
    )

    rounds_dir = output_dir / "rounds"
    branches_dir = output_dir / "branches"
    memory_dir = output_dir / "memory"
    rounds_dir.mkdir()
    branches_dir.mkdir()
    memory_dir.mkdir()

    usage = _empty_usage_summary()
    public_snapshot: Mapping[str, Any] = _freeze_json_object(
        {
            "schema_version": "vaevas-evolution-public-snapshot-v1",
            "round_index": -1,
            "memory_snapshot": frozen_initial,
        },
        field_name="initial_public_snapshot",
    )
    round_snapshots: list[Mapping[str, Any]] = []
    memory_snapshots: list[Mapping[str, Any]] = []
    branch_records: list[Mapping[str, Any]] = []
    lineage_records: list[CandidateLineage] = []
    previous_selected: Mapping[str, Any] | None = None
    previous_completed_ids: tuple[str, ...] = ()

    for round_index in range(int(normalized_manifest["rounds"])):
        if _deadline_expired(deadline_monotonic):
            break
        round_result = _run_one_round(
            manifest=normalized_manifest,
            manifest_hash=manifest_hash,
            round_index=round_index,
            branch_roster=branch_roster,
            per_branch=per_branch,
            public_snapshot=public_snapshot,
            output_dir=output_dir,
            branches_dir=branches_dir,
            branch_callback=branch_callback,
            deadline_monotonic=deadline_monotonic,
            max_workers=max_workers,
        )
        branch_records.extend(round_result.branch_records)
        _merge_usage_summary(usage, round_result.usage)
        for counter in _BUDGET_COUNTERS:
            charged = (
                int(usage[f"{counter}_reported_subtotal"])
                + int(usage[f"{counter}_unknown_count"]) * per_branch[counter]
            )
            if charged > total_budget[counter]:
                raise EvolutionRuntimeError(
                    "total_budget_exceeded",
                    f"total {counter} budget exceeded",
                )
        if _deadline_expired(deadline_monotonic):
            receipts[f"round-{round_index:04d}-discarded"] = _write_once_json(
                rounds_dir / f"round-{round_index:04d}-discarded.json",
                {
                    "schema_version": "vaevas-evolution-discarded-round-v1",
                    "manifest_sha256": manifest_hash,
                    "round_index": round_index,
                    "reason": "global_deadline_reached_after_callbacks",
                    "branch_records": round_result.branch_records,
                    "usage": round_result.usage,
                },
                base_dir=output_dir,
            )
            break

        snapshot = build_round_snapshot(
            manifest=normalized_manifest,
            round_index=round_index,
            candidates=round_result.candidates,
            memory_snapshot_sha256=_snapshot_sha(public_snapshot),
        )
        round_snapshots.append(snapshot)
        receipts[f"round-{round_index:04d}"] = _write_once_json(
            rounds_dir / f"round-{round_index:04d}.json",
            snapshot,
            base_dir=output_dir,
        )
        previous_parent = previous_selected
        selected = snapshot["selected_candidate"]
        lineages = _lineage_for_completed_candidates(
            candidates=snapshot["candidates"],
            manifest=normalized_manifest,
            round_index=round_index,
            parent_candidate=previous_parent if round_index > 0 else None,
            influence_candidate_ids=previous_completed_ids,
        )
        lineage_records.extend(lineages)
        if lineage_records:
            validate_candidate_lineage_graph(lineage_records)
        memory = _memory_for_round(
            manifest=normalized_manifest,
            round_index=round_index,
            parent_snapshot_sha256=(
                memory_snapshots[-1]["snapshot_sha256"] if memory_snapshots else None
            ),
            candidates=snapshot["candidates"],
        )
        memory_doc = memory.to_document()
        memory_snapshots.append(memory_doc)
        receipts[f"memory-{round_index:04d}"] = _write_once_json(
            memory_dir / f"round-{round_index:04d}.json",
            memory_doc,
            base_dir=output_dir,
        )
        public_snapshot = _freeze_json_object(
            {
                "schema_version": "vaevas-evolution-public-snapshot-v1",
                "round_index": round_index,
                "memory_snapshot": memory_doc,
                "selected_candidate": snapshot["selected_candidate"],
            },
            field_name="public_snapshot",
        )
        previous_selected = dict(selected) if selected else previous_selected
        previous_completed_ids = tuple(
            candidate["candidate_id"]
            for candidate in snapshot["candidates"]
            if candidate["status"] == "completed"
        )

    selected_candidate: Mapping[str, Any] | None
    if round_snapshots:
        selected_candidate = select_last_sealed_incumbent(
            round_snapshots,
            manifest=normalized_manifest,
        )
    else:
        selected_candidate = None
    receipts["selection"] = _write_once_json(
        output_dir / "selection.json",
        {
            "schema_version": "vaevas-evolution-runtime-selection-v1",
            "manifest_sha256": manifest_hash,
            "selected_candidate": selected_candidate,
            "sealed_round_count": len(round_snapshots),
            "branch_record_count": len(branch_records),
            "usage": usage,
            "final_judgment": None,
        },
        base_dir=output_dir,
    )
    receipts["receipts"] = _write_once_json(
        output_dir / "receipts.json",
        {
            "schema_version": "vaevas-evolution-runtime-receipts-v1",
            "manifest_sha256": manifest_hash,
            "receipts": receipts,
        },
        base_dir=output_dir,
    )
    return EvolutionRuntimeResult(
        manifest_sha256=manifest_hash,
        selected_candidate=selected_candidate,
        round_snapshots=tuple(round_snapshots),
        memory_snapshots=tuple(memory_snapshots),
        branch_records=tuple(branch_records),
        usage=MappingProxyType(dict(usage)),
        receipts=MappingProxyType(dict(receipts)),
    )


@dataclass(frozen=True, slots=True)
class _RoundResult:
    candidates: tuple[Mapping[str, Any], ...]
    branch_records: tuple[Mapping[str, Any], ...]
    usage: Mapping[str, int | None]


def _run_one_round(
    *,
    manifest: Mapping[str, Any],
    manifest_hash: str,
    round_index: int,
    branch_roster: tuple[str, ...],
    per_branch: Mapping[str, int],
    public_snapshot: Mapping[str, Any],
    output_dir: Path,
    branches_dir: Path,
    branch_callback: BranchCallback,
    deadline_monotonic: float | None,
    max_workers: int | None,
) -> _RoundResult:
    round_dir = branches_dir / f"round-{round_index:04d}"
    round_dir.mkdir()
    request_snapshot = public_snapshot
    records: list[Mapping[str, Any]] = []
    usage = _empty_usage_summary()

    def invoke(branch_id: str) -> Mapping[str, Any]:
        branch_path = _branch_output_path(
            round_dir=round_dir,
            output_dir=output_dir,
            branch_id=branch_id,
        )
        branch_path.mkdir(mode=0o700)
        _require_confined_path(branch_path, output_dir)
        request = EvolutionBranchRequest(
            manifest_sha256=manifest_hash,
            branch_id=branch_id,
            round_index=round_index,
            allowance=MappingProxyType(dict(per_branch)),
            deadline_monotonic=deadline_monotonic,
            public_snapshot=request_snapshot,
            output_path=branch_path,
        )
        _write_once_json(
            branch_path / "request.json",
            _branch_request_document(request),
            base_dir=output_dir,
        )
        try:
            raw_result = branch_callback(request)
            record = _normalize_branch_result(
                raw_result,
                manifest=manifest,
                branch_id=branch_id,
                round_index=round_index,
                allowance=per_branch,
            )
        except Exception as exc:
            observed_usage = (
                exc.observed_usage
                if isinstance(exc, EvolutionBranchFailure)
                else getattr(exc, "observed_usage", None)
            )
            record = _branch_failure_record(
                manifest=manifest,
                manifest_hash=manifest_hash,
                branch_id=branch_id,
                round_index=round_index,
                error_type=type(exc).__name__,
                message=str(exc),
                observed_usage=observed_usage,
            )
        _write_once_json(
            branch_path / "result.json",
            {
                "schema_version": "vaevas-evolution-branch-result-v1",
                "manifest_sha256": manifest_hash,
                "branch_record": record,
            },
            base_dir=output_dir,
        )
        return record

    workers = max_workers or len(branch_roster)
    workers = max(1, min(workers, len(branch_roster)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_by_branch = {
            pool.submit(invoke, branch_id): branch_id for branch_id in branch_roster
        }
        for future in as_completed(future_by_branch):
            records.append(future.result())
    records.sort(key=lambda record: (record["candidate_id"], record["branch_id"]))
    usage = _usage_summary(record["usage"] for record in records)
    candidates = tuple(_candidate_for_reducer(record) for record in records)
    return _RoundResult(
        candidates=candidates,
        branch_records=tuple(records),
        usage=MappingProxyType(usage),
    )


def _normalize_branch_result(
    raw_result: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any],
    branch_id: str,
    round_index: int,
    allowance: Mapping[str, int],
) -> Mapping[str, Any]:
    if not isinstance(raw_result, Mapping):
        raise EvolutionRuntimeError(
            "invalid_branch_result",
            "branch callback must return a JSON object",
        )
    forbidden = {"final_judgment", "final_test", "trusted_feedback", "score_sidecar"}
    if forbidden & set(raw_result):
        raise EvolutionRuntimeError(
            "trusted_feedback_leakage",
            "branch result cannot contain final or trusted judge evidence",
        )
    expected = {
        "candidate_id",
        "candidate_tree_sha256",
        "status",
        "public_validation",
        "usage",
    }
    if set(raw_result) != expected:
        raise EvolutionRuntimeError(
            "invalid_branch_result_fields",
            "branch result must contain exact candidate, validation, status, and usage fields",
        )
    usage = _observed_usage_map(raw_result["usage"])
    for counter in _BUDGET_COUNTERS:
        observed = usage[counter]
        if observed is None:
            raise EvolutionRuntimeError(
                "unknown_completed_branch_usage",
                f"completed branch {counter} usage is unknown",
            )
        if observed > allowance[counter]:
            raise EvolutionBranchFailure(
                f"branch {counter} budget exceeded",
                observed_usage=usage,
            )
    candidate = {
        "candidate_id": _nonempty_string(raw_result["candidate_id"], "candidate_id"),
        "branch_id": branch_id,
        "round_index": round_index,
        "candidate_tree_sha256": _sha256(
            raw_result["candidate_tree_sha256"],
            "candidate_tree_sha256",
        ),
        "public_validation": _public_validation(
            raw_result["public_validation"],
            manifest=manifest,
        ),
        "status": _status(raw_result["status"]),
    }
    build_round_snapshot(
        manifest=manifest,
        round_index=round_index,
        candidates=[candidate],
        round_sealed=False,
    )
    return MappingProxyType(
        {
            "schema_version": "vaevas-evolution-branch-record-v1",
            **candidate,
            "usage": MappingProxyType(dict(usage)),
            "failure": None,
        }
    )


def _branch_failure_record(
    *,
    manifest: Mapping[str, Any],
    manifest_hash: str,
    branch_id: str,
    round_index: int,
    error_type: str,
    message: str,
    observed_usage: Mapping[str, int | None] | None = None,
) -> Mapping[str, Any]:
    event = {
        "schema_version": "vaevas-evolution-branch-failure-event-v1",
        "manifest_sha256": manifest_hash,
        "branch_id": branch_id,
        "round_index": round_index,
        "error_type": error_type,
        "message_sha256": hashlib.sha256(message.encode("utf-8")).hexdigest(),
    }
    event_sha = _canonical_sha256(event)
    candidate_sha = _canonical_sha256(
        {
            "kind": "branch_failure_sentinel",
            "manifest_sha256": manifest_hash,
            "branch_id": branch_id,
            "round_index": round_index,
        }
    )
    usage = (
        _observed_usage_map(observed_usage)
        if observed_usage is not None
        else dict.fromkeys(_BUDGET_COUNTERS)
    )
    return MappingProxyType(
        {
            "schema_version": "vaevas-evolution-branch-record-v1",
            "candidate_id": f"{branch_id}-round-{round_index:04d}-failed",
            "branch_id": branch_id,
            "round_index": round_index,
            "candidate_tree_sha256": candidate_sha,
            "public_validation": {
                "profile_sha256": manifest["public_validation_profile_sha256"],
                "metrics": {},
                "event_sha256": event_sha,
            },
            "status": "branch_failed",
            "usage": MappingProxyType(dict(usage)),
            "failure": {
                "category": "branch_callback_failure",
                "error_type": error_type,
                "message_sha256": event["message_sha256"],
            },
        }
    )


def _candidate_for_reducer(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": record["candidate_id"],
        "branch_id": record["branch_id"],
        "round_index": record["round_index"],
        "candidate_tree_sha256": record["candidate_tree_sha256"],
        "public_validation": _json_ready(record["public_validation"]),
        "status": record["status"],
    }


def _lineage_for_completed_candidates(
    *,
    candidates: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    round_index: int,
    parent_candidate: Mapping[str, Any] | None,
    influence_candidate_ids: Sequence[str],
) -> tuple[CandidateLineage, ...]:
    lineages: list[CandidateLineage] = []
    for candidate in candidates:
        if candidate["status"] != "completed":
            continue
        parent_id = None
        mutation_kind = "create"
        influences: tuple[str, ...] = ()
        if round_index > 0:
            if parent_candidate is None:
                continue
            parent_id = str(parent_candidate["candidate_id"])
            mutation_kind = "refine"
            influences = tuple(
                item
                for item in influence_candidate_ids
                if item != candidate["candidate_id"] and item != parent_id
            )
        lineages.append(
            CandidateLineage(
                candidate_id=str(candidate["candidate_id"]),
                episode_id=str(manifest["manifest_id"]),
                attempt_id=str(manifest["manifest_id"]),
                task_id=str(manifest["benchmark_release"]),
                condition=str(manifest["condition"]),
                round_index=round_index,
                candidate_tree_sha256=str(candidate["candidate_tree_sha256"]),
                artifact_parent_candidate_id=parent_id,
                influence_candidate_ids=influences,
                mutation_kind=mutation_kind,  # type: ignore[arg-type]
                source_event_sha256=str(candidate["public_validation"]["event_sha256"]),
                status="active",
            )
        )
    return tuple(lineages)


def _memory_for_round(
    *,
    manifest: Mapping[str, Any],
    round_index: int,
    parent_snapshot_sha256: str | None,
    candidates: Sequence[Mapping[str, Any]],
) -> MemorySnapshot:
    entries = []
    for candidate in candidates:
        if candidate["status"] != "completed":
            continue
        entries.append(
            {
                "entry_id": f"{candidate['candidate_id']}/public-validation",
                "source_kind": "public_validation",
                "source_event_sha256": candidate["public_validation"]["event_sha256"],
                "candidate_id": candidate["candidate_id"],
                "candidate_tree_sha256": candidate["candidate_tree_sha256"],
                "summary": {
                    "status": candidate["status"],
                    "metrics": dict(candidate["public_validation"]["metrics"]),
                },
            }
        )
    return freeze_memory_snapshot(
        snapshot_id=f"{manifest['manifest_id']}/round-{round_index:04d}",
        episode_id=str(manifest["manifest_id"]),
        attempt_id=str(manifest["manifest_id"]),
        task_id=str(manifest["benchmark_release"]),
        condition=str(manifest["condition"]),
        round_index=round_index,
        parent_snapshot_sha256=parent_snapshot_sha256,
        entries=entries,
    )


def _branch_request_document(request: EvolutionBranchRequest) -> dict[str, Any]:
    return {
        "schema_version": "vaevas-evolution-branch-request-v1",
        "manifest_sha256": request.manifest_sha256,
        "branch_id": request.branch_id,
        "round_index": request.round_index,
        "allowance": dict(request.allowance),
        "deadline_monotonic": request.deadline_monotonic,
        "public_snapshot_sha256": _canonical_sha256(_json_ready(request.public_snapshot)),
    }


def _validate_total_budget_capacity(
    *,
    per_branch: Mapping[str, int],
    total_budget: Mapping[str, int],
    branch_count: int,
    rounds: int,
) -> None:
    for counter in _BUDGET_COUNTERS:
        required = per_branch[counter] * branch_count * rounds
        if total_budget[counter] < required:
            raise EvolutionRuntimeError(
                "insufficient_total_budget",
                f"total {counter} budget cannot cover the frozen per-branch schedule",
            )


def _branch_roster(manifest: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(
        _safe_path_segment(row["branch_id"], "branch_id")
        for row in manifest["branch_roster"]
    )


def _branch_output_path(*, round_dir: Path, output_dir: Path, branch_id: str) -> Path:
    safe_id = _safe_path_segment(branch_id, "branch_id")
    base = output_dir.resolve()
    parent = round_dir.resolve()
    if base != parent and base not in parent.parents:
        raise EvolutionRuntimeError(
            "unsafe_branch_path",
            "round directory must stay inside evolution output_dir",
        )
    branch_path = parent / safe_id
    resolved = branch_path.resolve(strict=False)
    if base != resolved and base not in resolved.parents:
        raise EvolutionRuntimeError(
            "unsafe_branch_path",
            "branch output path escaped evolution output_dir",
        )
    return branch_path


def _require_confined_path(path: Path, base_dir: Path) -> None:
    base = base_dir.resolve()
    resolved = path.resolve()
    if base != resolved and base not in resolved.parents:
        raise EvolutionRuntimeError(
            "unsafe_branch_path",
            "branch output path escaped evolution output_dir",
        )


def _public_validation(value: object, *, manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise EvolutionRuntimeError(
            "invalid_public_validation",
            "public_validation must be a JSON object",
        )
    if set(value) != {"profile_sha256", "metrics", "event_sha256"}:
        raise EvolutionRuntimeError(
            "invalid_public_validation",
            "public_validation must contain exact profile, metrics, and event hash fields",
        )
    return MappingProxyType(
        {
            "profile_sha256": _sha256(value["profile_sha256"], "profile_sha256"),
            "metrics": _json_ready(value["metrics"]),
            "event_sha256": _sha256(value["event_sha256"], "event_sha256"),
        }
    )


def _status(value: object) -> str:
    if value not in {"completed", "branch_timeout", "branch_failed"}:
        raise EvolutionRuntimeError(
            "invalid_branch_status",
            "branch status must be completed, branch_timeout, or branch_failed",
        )
    return str(value)


def _budget_map(value: object) -> dict[str, int]:
    if not isinstance(value, Mapping) or set(value) != set(_BUDGET_COUNTERS):
        raise EvolutionRuntimeError(
            "invalid_budget_map",
            "budget maps must contain exact evolution counters",
        )
    budget: dict[str, int] = {}
    for counter in _BUDGET_COUNTERS:
        observed = value[counter]
        if not isinstance(observed, int) or isinstance(observed, bool) or observed < 0:
            raise EvolutionRuntimeError(
                "invalid_budget_value",
                f"{counter} must be a non-negative integer",
            )
        budget[counter] = observed
    return budget


def _observed_usage_map(value: object) -> dict[str, int | None]:
    if not isinstance(value, Mapping) or set(value) != set(_BUDGET_COUNTERS):
        raise EvolutionRuntimeError(
            "invalid_usage_map",
            "usage maps must contain exact evolution counters",
        )
    usage: dict[str, int | None] = {}
    for counter in _BUDGET_COUNTERS:
        observed = value[counter]
        if observed is None:
            usage[counter] = None
            continue
        if not isinstance(observed, int) or isinstance(observed, bool) or observed < 0:
            raise EvolutionRuntimeError(
                "invalid_usage_value",
                f"{counter} must be a non-negative integer or null",
            )
        usage[counter] = observed
    return usage


def _empty_usage_summary() -> dict[str, int | None]:
    return _usage_summary(())


def _usage_summary(usages: Iterable[Mapping[str, int | None]]) -> dict[str, int | None]:
    usage_rows = list(usages)
    summary: dict[str, int | None] = {}
    for counter in _BUDGET_COUNTERS:
        reported = 0
        unknown = 0
        for usage in usage_rows:
            value = usage[counter]
            if value is None:
                unknown += 1
            else:
                reported += int(value)
        summary[counter] = None if unknown else reported
        summary[f"{counter}_reported_subtotal"] = reported
        summary[f"{counter}_unknown_count"] = unknown
    return summary


def _merge_usage_summary(
    target: dict[str, int | None],
    update: Mapping[str, int | None],
) -> None:
    for counter in _BUDGET_COUNTERS:
        subtotal_key = f"{counter}_reported_subtotal"
        unknown_key = f"{counter}_unknown_count"
        target[subtotal_key] = int(target[subtotal_key]) + int(update[subtotal_key])
        target[unknown_key] = int(target[unknown_key]) + int(update[unknown_key])
        target[counter] = (
            None if target[unknown_key] else int(target[subtotal_key])
        )


def _snapshot_sha(snapshot: Mapping[str, Any]) -> str | None:
    memory = snapshot.get("memory_snapshot")
    if isinstance(memory, Mapping):
        observed = memory.get("snapshot_sha256")
        if isinstance(observed, str):
            return observed
    return None


def _deadline_expired(deadline_monotonic: float | None) -> bool:
    return deadline_monotonic is not None and time.monotonic() >= deadline_monotonic


def _write_once_json(path: Path, document: Mapping[str, Any], *, base_dir: Path) -> Mapping[str, str]:
    if path.exists() or path.is_symlink():
        raise EvolutionRuntimeError(
            "write_once_violation",
            f"evolution receipt already exists: {path}",
        )
    payload = json.dumps(
        _json_ready(document),
        allow_nan=False,
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    with path.open("xb") as handle:
        handle.write(payload)
        handle.write(b"\n")
        handle.flush()
        os.fsync(handle.fileno())
        os.fchmod(handle.fileno(), 0o444)
    return MappingProxyType(
        {
            "path": path.relative_to(base_dir).as_posix(),
            "sha256": hashlib.sha256(payload + b"\n").hexdigest(),
        }
    )


def _freeze_json_object(value: object, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a JSON object")
    return _freeze_json(value)


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_json(item) for key, item in value.items()}
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
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
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _json_ready(value),
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _sha256(value: object, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise EvolutionRuntimeError(
            "invalid_sha256",
            f"{field_name} must be a lowercase SHA-256 digest",
        )
    return value


def _safe_path_segment(value: object, field_name: str) -> str:
    text = _nonempty_string(value, field_name)
    if (
        text in {".", ".."}
        or "/" in text
        or "\\" in text
        or Path(text).is_absolute()
    ):
        raise EvolutionRuntimeError(
            "invalid_branch_id",
            f"{field_name} must be one safe path segment",
        )
    return text


def _nonempty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvolutionRuntimeError(
            "invalid_string",
            f"{field_name} must be a non-empty string",
        )
    return value
