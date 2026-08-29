"""Deterministic contracts for round-based candidate evolution."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any


class EvolutionReducerError(ValueError):
    """A classified contract violation while reducing evolution evidence."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def evolution_manifest_sha256(manifest: Mapping[str, Any]) -> str:
    """Hash a schema-shaped evolution manifest with canonical JSON ordering."""
    normalized = _normalize_manifest(manifest)
    return _canonical_sha256(normalized)


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
    """Canonicalize one round without preserving provider completion order."""
    normalized_manifest = _normalize_manifest(manifest)
    if not isinstance(round_index, int) or isinstance(round_index, bool) or round_index < 0:
        raise ValueError("round_index must be a non-negative integer")
    if round_index >= normalized_manifest["rounds"]:
        raise EvolutionReducerError(
            "round_index_out_of_range",
            "round_index must be within the frozen manifest round range",
        )
    if not isinstance(round_sealed, bool):
        raise TypeError("round_sealed must be a boolean")
    if not isinstance(global_deadline_reached, bool):
        raise TypeError("global_deadline_reached must be a boolean")
    if global_deadline_reached and not round_sealed:
        raise EvolutionReducerError(
            "unsealed_round_after_global_deadline",
            "global deadline reached with an unsealed round",
        )
    _require_optional_nonempty(
        retry_parent_attempt_id,
        field_name="retry_parent_attempt_id",
    )
    _require_optional_sha256(memory_snapshot_sha256, field_name="memory_snapshot_sha256")
    _require_optional_sha256(frozen_input_sha256, field_name="frozen_input_sha256")
    if retry_parent_attempt_id is not None and (
        round_index != 0
        or memory_snapshot_sha256 is not None
        or frozen_input_sha256 is None
    ):
        raise EvolutionReducerError(
            "retry_round_contract",
            "retry rounds must restart round 0 from frozen input without memory inheritance",
        )

    branch_roster = _branch_roster(normalized_manifest)
    normalized_candidates = [
        _normalize_candidate(
            candidate,
            manifest=normalized_manifest,
            round_index=round_index,
            branch_roster=branch_roster,
        )
        for candidate in candidates
    ]
    _require_unique_round_candidates(normalized_candidates)
    if round_sealed:
        _require_strict_barrier(normalized_candidates, branch_roster=branch_roster)
    normalized_candidates.sort(
        key=lambda candidate: (
            candidate["candidate_id"],
            candidate["candidate_tree_sha256"],
            candidate["branch_id"],
        )
    )
    selected_candidate = None
    completed = [
        candidate
        for candidate in normalized_candidates
        if candidate["status"] == "completed"
    ]
    if round_sealed and completed:
        selected_candidate = _select_normalized_candidate(
            manifest=normalized_manifest,
            candidates=completed,
        )
    snapshot = {
        "schema_version": "vaevas-evolution-round-snapshot-v1",
        "manifest_sha256": evolution_manifest_sha256(normalized_manifest),
        "round_index": round_index,
        "round_sealed": round_sealed,
        "global_deadline_reached": global_deadline_reached,
        "retry_parent_attempt_id": retry_parent_attempt_id,
        "memory_snapshot_sha256": memory_snapshot_sha256,
        "frozen_input_sha256": frozen_input_sha256,
        "selected_candidate": selected_candidate,
        "candidates": normalized_candidates,
    }
    snapshot["round_snapshot_sha256"] = _canonical_sha256(snapshot)
    return snapshot


def select_candidate(
    *,
    manifest: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Select an incumbent from public metrics and deterministic tie-breaks."""
    normalized_manifest = _normalize_manifest(manifest)
    if not candidates:
        raise EvolutionReducerError("no_candidates", "cannot select from no candidates")
    branch_roster = _branch_roster(normalized_manifest)
    normalized_all = [
        _normalize_candidate(
            candidate,
            manifest=normalized_manifest,
            round_index=None,
            branch_roster=branch_roster,
        )
        for candidate in candidates
    ]
    _require_unique_round_candidates(normalized_all)
    round_indices = {candidate["round_index"] for candidate in normalized_all}
    if len(round_indices) != 1:
        raise EvolutionReducerError(
            "round_index_mismatch",
            "candidate selection must use records from exactly one round",
        )
    normalized = [
        candidate
        for candidate in normalized_all
        if candidate["status"] == "completed"
    ]
    if not normalized:
        raise EvolutionReducerError(
            "no_completed_candidates",
            "no completed candidates are eligible for selection",
        )
    return dict(
        _select_normalized_candidate(manifest=normalized_manifest, candidates=normalized)
    )


def select_last_sealed_incumbent(
    round_snapshots: Sequence[Mapping[str, Any]],
    *,
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the incumbent from the highest sealed round snapshot."""
    normalized_manifest = _normalize_manifest(manifest)
    manifest_hash = evolution_manifest_sha256(normalized_manifest)
    seen_rounds = set()
    sealed = []
    for snapshot in round_snapshots:
        _validate_round_snapshot(
            snapshot,
            manifest=normalized_manifest,
            manifest_hash=manifest_hash,
            seen_rounds=seen_rounds,
        )
        if snapshot["round_sealed"] is True and snapshot["selected_candidate"]:
            sealed.append(snapshot)
    if not sealed:
        raise EvolutionReducerError(
            "no_sealed_incumbent",
            "no sealed incumbent is available before the global deadline",
        )
    selected_snapshot = max(sealed, key=lambda snapshot: snapshot["round_index"])
    return dict(selected_snapshot["selected_candidate"])


def _normalize_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, Mapping):
        raise TypeError("evolution manifest must be a JSON object")
    required = {
        "schema_version",
        "manifest_id",
        "condition",
        "benchmark_release",
        "evaluator",
        "rounds",
        "branch_roster",
        "budgets",
        "tool_registry_sha256",
        "public_validation_profile_sha256",
        "final_test_profile_sha256",
        "memory_policy",
        "round_barrier_policy",
        "branch_timeout_policy",
        "global_deadline_policy",
        "selection_rule",
        "final_submission_policy",
    }
    extra = sorted(set(manifest) - required)
    if extra:
        raise EvolutionReducerError(
            "unknown_manifest_fields",
            f"unknown manifest fields: {extra}",
        )
    missing = sorted(required - set(manifest))
    if missing:
        raise EvolutionReducerError(
            "missing_manifest_fields",
            f"manifest missing fields: {missing}",
        )
    if manifest["schema_version"] != "vaevas-evolution-manifest-v1":
        raise EvolutionReducerError(
            "unsupported_manifest_schema",
            "unsupported evolution manifest schema",
        )
    _require_canonical_json(manifest, label="evolution manifest")
    normalized = dict(manifest)

    _require_nonempty_string(normalized["manifest_id"], field_name="manifest_id")
    _require_nonempty_string(normalized["condition"], field_name="condition")
    _require_nonempty_string(
        normalized["benchmark_release"],
        field_name="benchmark_release",
    )
    _normalize_evaluator(normalized["evaluator"])
    if (
        not isinstance(normalized["rounds"], int)
        or isinstance(normalized["rounds"], bool)
        or normalized["rounds"] < 1
    ):
        raise EvolutionReducerError(
            "invalid_rounds",
            "rounds must be a positive integer",
        )
    _normalize_budgets(normalized["budgets"])
    for field_name in (
        "tool_registry_sha256",
        "public_validation_profile_sha256",
        "final_test_profile_sha256",
    ):
        _require_manifest_sha256(normalized[field_name], field_name=field_name)
    expected_policies = {
        "memory_policy": "episode_local_public_only",
        "round_barrier_policy": "strict_all_branches_or_declared_timeout",
        "branch_timeout_policy": "classify_branch_timeout_and_seal_round",
        "global_deadline_policy": "discard_unsealed_round_use_prior_incumbent",
        "final_submission_policy": "freeze_selected_candidate_then_final_test_once",
    }
    for field_name, expected in expected_policies.items():
        if normalized[field_name] != expected:
            raise EvolutionReducerError(
                "invalid_manifest_policy",
                f"{field_name} must be {expected}",
            )
    _normalize_selection_rule(normalized["selection_rule"])
    _branch_roster(normalized)
    return normalized


def _normalize_evaluator(evaluator: object) -> None:
    if not isinstance(evaluator, Mapping):
        raise TypeError("evaluator must be a JSON object")
    if set(evaluator) != {"engine", "version"}:
        raise EvolutionReducerError(
            "invalid_evaluator",
            "evaluator must contain engine and version only",
        )
    _require_manifest_nonempty(evaluator["engine"], field_name="evaluator.engine")
    _require_manifest_nonempty(evaluator["version"], field_name="evaluator.version")


def _normalize_budgets(budgets: object) -> None:
    if not isinstance(budgets, Mapping):
        raise TypeError("budgets must be a JSON object")
    if set(budgets) != {"per_branch", "total"}:
        raise EvolutionReducerError(
            "invalid_budgets",
            "budgets must contain per_branch and total only",
        )
    for scope in ("per_branch", "total"):
        budget = budgets[scope]
        if not isinstance(budget, Mapping):
            raise TypeError(f"budgets.{scope} must be a JSON object")
        expected = {"model_calls", "tool_calls", "public_validation_calls"}
        if set(budget) != expected:
            raise EvolutionReducerError(
                "invalid_budgets",
                f"budgets.{scope} must contain exact budget counters",
            )
        for field_name in expected:
            value = budget[field_name]
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise EvolutionReducerError(
                    "invalid_budgets",
                    f"budgets.{scope}.{field_name} must be a non-negative integer",
                )


def _normalize_selection_rule(selection_rule: object) -> tuple[dict[str, str], ...]:
    if not isinstance(selection_rule, Mapping):
        raise TypeError("selection_rule must be a JSON object")
    if set(selection_rule) != {"metrics", "tiebreak"}:
        raise EvolutionReducerError(
            "invalid_selection_rule",
            "selection_rule must contain metrics and tiebreak only",
        )
    if selection_rule["tiebreak"] != ["candidate_tree_sha256", "candidate_id"]:
        raise EvolutionReducerError(
            "invalid_tiebreak",
            "selection tiebreak must be candidate_tree_sha256 then candidate_id",
        )
    metrics = selection_rule["metrics"]
    if not isinstance(metrics, Sequence) or isinstance(metrics, (str, bytes)):
        raise TypeError("selection_rule.metrics must be an array")
    if not metrics:
        raise EvolutionReducerError(
            "invalid_selection_metrics",
            "selection_rule.metrics cannot be empty",
        )
    normalized = []
    names = set()
    for metric in metrics:
        if not isinstance(metric, Mapping):
            raise TypeError("selection metric entries must be JSON objects")
        if set(metric) != {"name", "direction"}:
            raise EvolutionReducerError(
                "invalid_selection_metric",
                "selection metric entries require name and direction only",
            )
        _require_nonempty_string(metric["name"], field_name="selection metric name")
        if metric["direction"] not in {"maximize", "minimize"}:
            raise EvolutionReducerError(
                "invalid_metric_direction",
                "metric direction must be maximize or minimize",
            )
        if metric["name"] in names:
            raise EvolutionReducerError(
                "duplicate_metric",
                f"duplicate selection metric: {metric['name']}",
            )
        names.add(metric["name"])
        normalized.append({"name": metric["name"], "direction": metric["direction"]})
    return tuple(normalized)


def _branch_roster(manifest: Mapping[str, Any]) -> frozenset[str]:
    roster = manifest["branch_roster"]
    if not isinstance(roster, Sequence) or isinstance(roster, (str, bytes)):
        raise TypeError("branch_roster must be an array")
    branch_ids = []
    for entry in roster:
        if not isinstance(entry, Mapping):
            raise TypeError("branch_roster entries must be JSON objects")
        if set(entry) != {"branch_id", "backend_profile_sha256", "model_ref"}:
            raise EvolutionReducerError(
                "invalid_branch_roster",
                "branch_roster entries require branch_id, backend_profile_sha256, and model_ref only",
            )
        _require_manifest_nonempty(entry["branch_id"], field_name="branch_id")
        _require_manifest_sha256(
            entry["backend_profile_sha256"],
            field_name="backend_profile_sha256",
        )
        _require_manifest_nonempty(entry["model_ref"], field_name="model_ref")
        if entry["branch_id"] in branch_ids:
            raise EvolutionReducerError(
                "duplicate_branch_id",
                f"duplicate branch_id in branch_roster: {entry['branch_id']}",
            )
        branch_ids.append(entry["branch_id"])
    if not branch_ids:
        raise EvolutionReducerError(
            "empty_branch_roster",
            "branch_roster must contain at least one branch",
        )
    return frozenset(branch_ids)


def _normalize_candidate(
    candidate: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any],
    round_index: int | None,
    branch_roster: frozenset[str],
) -> dict[str, Any]:
    if not isinstance(candidate, Mapping):
        raise TypeError("candidate must be a JSON object")
    if "final_test" in candidate or "trusted_feedback" in candidate:
        raise EvolutionReducerError(
            "final_feedback_leakage",
            "final feedback cannot enter evolution rounds",
        )
    allowed = {
        "candidate_id",
        "branch_id",
        "round_index",
        "candidate_tree_sha256",
        "public_validation",
        "status",
        "completion_order",
    }
    extra = sorted(set(candidate) - allowed)
    if extra:
        raise EvolutionReducerError(
            "unknown_candidate_fields",
            f"unknown candidate fields: {extra}",
        )
    for field_name in allowed - {"completion_order"}:
        if field_name not in candidate:
            raise EvolutionReducerError(
                "candidate_missing_field",
                f"candidate record missing field: {field_name}",
            )
    _require_nonempty_string(candidate["candidate_id"], field_name="candidate_id")
    _require_nonempty_string(candidate["branch_id"], field_name="branch_id")
    if candidate["branch_id"] not in branch_roster:
        raise EvolutionReducerError(
            "unknown_branch",
            f"candidate branch is not in the frozen roster: {candidate['branch_id']}",
        )
    if (
        not isinstance(candidate["round_index"], int)
        or isinstance(candidate["round_index"], bool)
        or candidate["round_index"] < 0
    ):
        raise ValueError("candidate round_index must be a non-negative integer")
    if round_index is not None and candidate["round_index"] != round_index:
        raise EvolutionReducerError(
            "round_index_mismatch",
            "candidate round_index does not match the reduced round",
        )
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
    if set(validation) != {"profile_sha256", "metrics", "event_sha256"}:
        raise EvolutionReducerError(
            "invalid_public_validation",
            "public_validation must contain profile_sha256, metrics, and event_sha256 only",
        )
    if candidate["round_index"] >= manifest["rounds"]:
        raise EvolutionReducerError(
            "round_index_out_of_range",
            "candidate round_index must be within the frozen manifest round range",
        )
    if validation.get("profile_sha256") != manifest["public_validation_profile_sha256"]:
        raise EvolutionReducerError(
            "validation_profile_mismatch",
            "candidate validation profile does not match manifest",
        )
    _require_manifest_sha256(validation.get("event_sha256"), field_name="event_sha256")
    metrics = validation.get("metrics")
    if not isinstance(metrics, Mapping):
        raise TypeError("public_validation.metrics must be a JSON object")
    if status == "completed":
        normalized_metrics = _normalize_metrics(
            metrics,
            selection_metrics=_normalize_selection_rule(manifest["selection_rule"]),
        )
    else:
        if metrics:
            raise EvolutionReducerError(
                "invalid_metric",
                "non-completed branch terminal records cannot carry public metrics",
            )
        normalized_metrics = {}
    return {
        "candidate_id": candidate["candidate_id"],
        "branch_id": candidate["branch_id"],
        "round_index": candidate["round_index"],
        "candidate_tree_sha256": candidate["candidate_tree_sha256"],
        "public_validation": {
            "profile_sha256": validation["profile_sha256"],
            "metrics": normalized_metrics,
            "event_sha256": validation["event_sha256"],
        },
        "status": status,
    }


def _normalize_metrics(
    metrics: Mapping[str, Any],
    *,
    selection_metrics: Sequence[Mapping[str, str]],
) -> dict[str, float]:
    normalized = {}
    expected_names = {metric["name"] for metric in selection_metrics}
    extra_names = sorted(set(metrics) - expected_names)
    if extra_names:
        raise EvolutionReducerError(
            "invalid_metric",
            f"undeclared public metrics are not allowed: {extra_names}",
        )
    for metric in selection_metrics:
        metric_name = metric["name"]
        if metric_name not in metrics:
            raise EvolutionReducerError(
                "invalid_metric",
                f"missing required public metric: {metric_name}",
            )
        value = metrics[metric_name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise EvolutionReducerError(
                "invalid_metric",
                f"public metric must be numeric: {metric_name}",
            )
        if not math.isfinite(value):
            raise EvolutionReducerError(
                "invalid_metric",
                f"public metric must be finite: {metric_name}",
            )
        normalized[metric_name] = float(value)
    return dict(sorted(normalized.items()))


def _select_normalized_candidate(
    *,
    manifest: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    selection_metrics = _normalize_selection_rule(manifest["selection_rule"])

    def sort_key(candidate: Mapping[str, Any]) -> tuple[Any, ...]:
        public_metrics = candidate["public_validation"]["metrics"]
        metric_key = []
        for metric in selection_metrics:
            value = public_metrics[metric["name"]]
            metric_key.append(-value if metric["direction"] == "maximize" else value)
        return (
            *metric_key,
            candidate["candidate_tree_sha256"],
            candidate["candidate_id"],
        )

    return min(candidates, key=sort_key)


def _require_unique_round_candidates(candidates: Sequence[Mapping[str, Any]]) -> None:
    candidate_ids = set()
    branch_ids = set()
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        branch_id = candidate["branch_id"]
        if candidate_id in candidate_ids:
            raise EvolutionReducerError(
                "duplicate_candidate_id",
                f"duplicate candidate_id in round: {candidate_id}",
            )
        if branch_id in branch_ids:
            raise EvolutionReducerError(
                "duplicate_branch_id",
                f"duplicate branch_id in round: {branch_id}",
            )
        candidate_ids.add(candidate_id)
        branch_ids.add(branch_id)


def _require_strict_barrier(
    candidates: Sequence[Mapping[str, Any]],
    *,
    branch_roster: frozenset[str],
) -> None:
    present = {candidate["branch_id"] for candidate in candidates}
    if present != branch_roster:
        missing = sorted(branch_roster - present)
        extra = sorted(present - branch_roster)
        raise EvolutionReducerError(
            "strict_barrier",
            f"sealed round must contain one terminal record per branch; missing={missing}, extra={extra}",
        )


def _validate_round_snapshot(
    snapshot: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any],
    manifest_hash: str,
    seen_rounds: set[int],
) -> None:
    if not isinstance(snapshot, Mapping):
        raise TypeError("round snapshot must be a JSON object")
    expected_keys = {
        "schema_version",
        "manifest_sha256",
        "round_index",
        "round_sealed",
        "global_deadline_reached",
        "retry_parent_attempt_id",
        "memory_snapshot_sha256",
        "frozen_input_sha256",
        "selected_candidate",
        "candidates",
        "round_snapshot_sha256",
    }
    if set(snapshot) != expected_keys:
        raise EvolutionReducerError(
            "invalid_round_snapshot",
            "round snapshot must contain exact v1 fields",
        )
    if snapshot["schema_version"] != "vaevas-evolution-round-snapshot-v1":
        raise EvolutionReducerError(
            "unsupported_round_snapshot_schema",
            "unsupported round snapshot schema",
        )
    if snapshot["manifest_sha256"] != manifest_hash:
        raise EvolutionReducerError(
            "manifest_mismatch",
            "round snapshot manifest hash does not match requested manifest",
        )
    if (
        not isinstance(snapshot["round_index"], int)
        or isinstance(snapshot["round_index"], bool)
        or snapshot["round_index"] < 0
        or snapshot["round_index"] >= manifest["rounds"]
    ):
        raise EvolutionReducerError(
            "round_index_out_of_range",
            "snapshot round_index must be within the manifest round range",
        )
    round_index = snapshot["round_index"]
    if round_index in seen_rounds:
        raise EvolutionReducerError(
            "duplicate_round",
            f"duplicate round snapshot: {round_index}",
        )
    seen_rounds.add(round_index)
    if not isinstance(snapshot["round_sealed"], bool):
        raise TypeError("round_sealed must be a boolean")
    if not isinstance(snapshot["global_deadline_reached"], bool):
        raise TypeError("global_deadline_reached must be a boolean")
    if snapshot["global_deadline_reached"] and not snapshot["round_sealed"]:
        raise EvolutionReducerError(
            "unsealed_round_after_global_deadline",
            "global deadline reached with an unsealed round",
        )
    _require_optional_nonempty(
        snapshot["retry_parent_attempt_id"],
        field_name="retry_parent_attempt_id",
    )
    _require_optional_sha256(
        snapshot["memory_snapshot_sha256"],
        field_name="memory_snapshot_sha256",
    )
    _require_optional_sha256(
        snapshot["frozen_input_sha256"],
        field_name="frozen_input_sha256",
    )
    if snapshot["retry_parent_attempt_id"] is not None and (
        snapshot["round_index"] != 0
        or snapshot["memory_snapshot_sha256"] is not None
        or snapshot["frozen_input_sha256"] is None
    ):
        raise EvolutionReducerError(
            "retry_round_contract",
            "retry rounds must restart round 0 from frozen input without memory inheritance",
        )
    _require_manifest_sha256(
        snapshot["round_snapshot_sha256"],
        field_name="round_snapshot_sha256",
    )
    branch_roster = _branch_roster(manifest)
    candidates = snapshot["candidates"]
    if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)):
        raise TypeError("round snapshot candidates must be an array")
    normalized_candidates = [
        _normalize_candidate(
            candidate,
            manifest=manifest,
            round_index=round_index,
            branch_roster=branch_roster,
        )
        for candidate in candidates
    ]
    _require_unique_round_candidates(normalized_candidates)
    canonical_candidates = sorted(
        normalized_candidates,
        key=lambda candidate: (
            candidate["candidate_id"],
            candidate["candidate_tree_sha256"],
            candidate["branch_id"],
        ),
    )
    if list(candidates) != canonical_candidates:
        raise EvolutionReducerError(
            "noncanonical_round_snapshot",
            "round snapshot candidates must use canonical candidate ordering",
        )
    if snapshot["round_sealed"]:
        _require_strict_barrier(normalized_candidates, branch_roster=branch_roster)
    unsigned_snapshot = dict(snapshot)
    recorded_hash = unsigned_snapshot.pop("round_snapshot_sha256")
    if _canonical_sha256(unsigned_snapshot) != recorded_hash:
        raise EvolutionReducerError(
            "snapshot_hash_mismatch",
            "round snapshot hash does not match its canonical content",
        )
    selected_candidate = snapshot["selected_candidate"]
    if selected_candidate is not None and not isinstance(selected_candidate, Mapping):
        raise TypeError("selected_candidate must be a JSON object or null")
    completed = [
        candidate
        for candidate in normalized_candidates
        if candidate["status"] == "completed"
    ]
    expected_selected = None
    if snapshot["round_sealed"] and completed:
        expected_selected = dict(
            _select_normalized_candidate(manifest=manifest, candidates=completed)
        )
    if selected_candidate != expected_selected:
        raise EvolutionReducerError(
            "selected_candidate_mismatch",
            "selected_candidate must equal the deterministic public-metric winner",
        )


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


def _require_manifest_sha256(value: object, *, field_name: str) -> None:
    try:
        _require_sha256(value, field_name=field_name)
    except ValueError as exc:
        raise EvolutionReducerError("invalid_sha256", str(exc)) from exc


def _require_optional_sha256(value: object, *, field_name: str) -> None:
    if value is None:
        return
    _require_sha256(value, field_name=field_name)


def _require_nonempty_string(value: object, *, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_manifest_nonempty(value: object, *, field_name: str) -> None:
    try:
        _require_nonempty_string(value, field_name=field_name)
    except ValueError as exc:
        raise EvolutionReducerError("invalid_manifest_field", str(exc)) from exc


def _require_optional_nonempty(value: object, *, field_name: str) -> None:
    if value is not None:
        _require_nonempty_string(value, field_name=field_name)
