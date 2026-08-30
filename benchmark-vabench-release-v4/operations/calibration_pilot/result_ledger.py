#!/usr/bin/env python3
"""Deterministic reviewer-safe native campaign result ledger projection."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math
import re
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "vabench-native-campaign-ledger-v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_IDENTITY_FIELDS = (
    "cell_id",
    "task_id",
    "family_id",
    "form",
    "mode",
    "experimental_arm",
)
_OPTIONAL_IDENTITY_FIELDS = ("model", "repetition")
_COST_FIELDS = (
    "provider_requests",
    "tool_requests",
    "output_tokens",
    "evas_invocations",
)
_THREE_ARM_ORDER = ("Agent-No-EVAS", "Agentic", "OneShot")
_DELTA_PAIRS = (
    ("Agentic", "OneShot"),
    ("Agentic", "Agent-No-EVAS"),
    ("Agent-No-EVAS", "OneShot"),
)
_INFRA_STATUSES = {
    "infrastructure_failure",
    "agent_timeout",
    "agent_resource_exhausted",
}
_ALLOWED_SINGLE_TRAJECTORY_ARMS = frozenset({
    "OneShot",
    "Agent-No-EVAS",
    "Agentic",
})
_ALLOWED_BACKENDS = frozenset({"native-mini-swe", "native-reasoning"})
_SCORE_AUTHORITIES = frozenset({"development_only", "formal"})


def build_native_campaign_ledger(
    campaign: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    *,
    campaign_file_sha256: str,
) -> dict[str, Any]:
    """Project verified native score rows into a safe result ledger.

    This is a pure in-memory projection. The caller owns reading, score-row
    verification, and persistence. The ledger intentionally exports structural
    statuses, hashes, usage, and attempt references only; it does not declassify
    prompts, raw tool/provider output, hidden judge payloads, or model-quality
    claims.
    """

    _sha256(campaign_file_sha256, "campaign_file_sha256")
    campaign_obj = _mapping(campaign, "campaign")
    cells = _cells(campaign_obj)
    row_list = [_mapping(row, "row") for row in rows]
    if any("extensions" in row for row in row_list):
        raise ValueError("synthetic extension rows require a separately frozen comparison protocol")
    _validate_schedule_join(campaign_obj, cells, row_list)
    _validate_campaign_backend(campaign_obj, row_list)
    limit = (campaign_obj.get("execution_config") or {}).get("native_model_call_limit")
    if limit is not None and (type(limit) is not int or limit <= 0):
        raise ValueError("invalid campaign model-call limit")
    if any(row.get("model_call_limit") != limit for row in row_list):
        raise ValueError("row model-call limit differs from frozen campaign")
    records = [
        _record_projection(campaign_obj, cell, row)
        for cell, row in _ordered_pairs(cells, row_list)
    ]
    paired = _paired_coverage(records)
    infra_count = sum(
        1 for record in records
        if record["status"]["judge_status"] in _INFRA_STATUSES
    )
    eligible_count = sum(1 for record in records if record["actual_score_eligible"])
    result = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "campaign_file_sha256": campaign_file_sha256,
            "campaign_sha256": _canonical_sha256(campaign_obj),
            "row_count": len(row_list),
            "row_hashes": [
                {
                    "cell_id": row["cell_id"],
                    "row_sha256": _canonical_sha256(row),
                }
                for row in sorted(row_list, key=lambda item: str(item["cell_id"]))
            ],
        },
        "denominator": {
            "scheduled_cells": len(cells),
            "observed_rows": len(row_list),
            "eligible_actual_score_cells": eligible_count,
            "infrastructure_failure_cells": infra_count,
            "null_infra_denominator": None if infra_count else len(cells),
        },
        "deadline_terminal_stats": _deadline_terminal_stats(records),
        "paired_coverage": paired["coverage"],
        "unmatched_reasons": paired["unmatched_reasons"],
        "claim_index": _claim_index(records),
        "records": records,
    }
    result["ledger_sha256"] = _canonical_sha256(result)
    return result


def _model_call_budget_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    if "model_call_limit" not in row:
        return {}
    limit, budget = row["model_call_limit"], row.get("model_call_budget")
    if budget is not None:
        fields = {"limit", "used_before_attempt", "admitted_in_attempt", "used_total", "remaining"}
        if (not isinstance(budget, Mapping) or set(budget) != fields
                or any(type(value) is not int or value < 0 for value in budget.values())
                or budget["limit"] != limit
                or budget["used_total"] != budget["used_before_attempt"] + budget["admitted_in_attempt"]
                or budget["remaining"] != limit - budget["used_total"]):
            raise ValueError("invalid model-call budget summary")
        budget = dict(budget)
    return {"model_call_limit": limit, "model_call_budget": budget}


def _cells(campaign: Mapping[str, Any]) -> list[dict[str, Any]]:
    cells = campaign.get("cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError("campaign cells must be a non-empty list")
    return [_mapping(cell, "campaign cell") for cell in cells]


def _validate_schedule_join(
    campaign: Mapping[str, Any],
    cells: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
) -> None:
    scheduled = {}
    for cell in cells:
        cell_id = _string(cell.get("cell_id"), "scheduled cell_id")
        if cell_id in scheduled:
            raise ValueError("scheduled cells must be unique")
        _arm(cell.get("experimental_arm"))
        _effective_model(campaign, cell, {})
        _effective_repetition(cell, {})
        scheduled[cell_id] = cell
    observed = {}
    for row in rows:
        cell_id = _string(row.get("cell_id"), "row cell_id")
        if cell_id in observed:
            raise ValueError("rows must cover every scheduled cell exactly once")
        observed[cell_id] = row
    if set(scheduled) != set(observed):
        raise ValueError("rows must cover every scheduled cell exactly once")
    for cell_id, cell in scheduled.items():
        row = observed[cell_id]
        for key in (*_IDENTITY_FIELDS, *_OPTIONAL_IDENTITY_FIELDS):
            if key in _OPTIONAL_IDENTITY_FIELDS:
                continue
            if key in cell and row.get(key) != cell.get(key):
                raise ValueError("scheduled row metadata mismatch")
        _effective_model(campaign, cell, row)
        _effective_repetition(cell, row)


def _validate_campaign_backend(
    campaign: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> None:
    observed = [_backend(row.get("backend")) for row in rows]
    config = campaign.get("execution_config")
    bound_backend = (
        config.get("episode_backend") if isinstance(config, Mapping) else None
    )
    if bound_backend is not None:
        expected = _backend(bound_backend)
        if any(backend != expected for backend in observed):
            raise ValueError("row backend differs from campaign execution_config.episode_backend")
        return
    if len(set(observed)) > 1:
        raise ValueError("unannounced mixed backends are not allowed")


def _ordered_pairs(
    cells: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
) -> list[tuple[Mapping[str, Any], Mapping[str, Any]]]:
    by_cell = {str(row["cell_id"]): row for row in rows}
    return [(cell, by_cell[str(cell["cell_id"])]) for cell in cells]


def _record_projection(
    campaign: Mapping[str, Any],
    cell: Mapping[str, Any],
    row: Mapping[str, Any],
) -> dict[str, Any]:
    backend = _backend(row.get("backend"))
    model, model_source = _effective_model_for_record(campaign, cell, row)
    repetition, repetition_source = _effective_repetition_for_record(cell, row)
    identity = {
        "cell_id": _string(row.get("cell_id"), "cell_id"),
        "task_id": _string(row.get("task_id"), "task_id"),
        "family_id": _string(row.get("family_id"), "family_id"),
        "form": _string(row.get("form"), "form"),
        "mode": _string(row.get("mode"), "mode"),
        "experimental_arm": _arm(row.get("experimental_arm")),
        "model": model,
        "repetition": repetition,
    }
    judge_status = _string(row.get("judge_status"), "judge_status")
    score = _score(row.get("score"))
    attempt_costs = _attempt_costs(row)
    selected_attempt = _selected_attempt(row, attempt_costs["attempts"])
    score_authority = _score_authority(row)
    return {
        "backend": backend,
        **_model_call_budget_projection(row),
        "identity": identity,
        "identity_sources": {
            "model": model_source,
            "repetition": repetition_source,
        },
        "status": {
            "backend": backend,
            "submission_status": _optional_identity(
                row.get("submission_status"), "submission_status"
            ),
            "judge_status": judge_status,
            "terminal_reason": _optional_identity(
                row.get("terminal_reason"), "terminal_reason"
            ),
            "termination_reason": _optional_identity(
                row.get("termination_reason"), "termination_reason"
            ),
            "deadline_bucket": _optional_identity(
                row.get("deadline_bucket"), "deadline_bucket"
            ),
        },
        "hashes": _hash_references(row),
        "usage": _usage_projection(row),
        "selected_attempt": selected_attempt,
        "attempt_costs": attempt_costs,
        "actual_score": score,
        "actual_score_eligible": (
            score is not None
            and judge_status not in _INFRA_STATUSES
            and score_authority in _SCORE_AUTHORITIES
        ),
        "actual_score_ineligible_reason": _ineligible_reason(
            score, judge_status, score_authority
        ),
        "score_authority": score_authority,
    }


def _hash_references(row: Mapping[str, Any]) -> dict[str, Any]:
    trusted = row.get("trusted_replay")
    final_profile = trusted.get("final_test_profile") if isinstance(trusted, Mapping) else None
    contract = (
        final_profile.get("score_sidecar_contract")
        if isinstance(final_profile, Mapping)
        else None
    )
    sidecar = (
        trusted.get("derived_score_sidecar_reference")
        if isinstance(trusted, Mapping)
        else None
    )
    native = row.get("native_evidence")
    files = native.get("files") if isinstance(native, Mapping) else None
    return {
        "row_sha256": _canonical_sha256(row),
        "runtime_sha256": _optional_sha(
            files.get("runtime_sha256") if isinstance(files, Mapping) else None,
            "runtime_sha256",
        ),
        "artifact_sha256": _optional_sha(
            native.get("artifact_sha256") if isinstance(native, Mapping) else None,
            "artifact_sha256",
        ),
        "score_sidecar_sha256": _optional_sha(
            sidecar.get("sha256") if isinstance(sidecar, Mapping) else None,
            "score_sidecar_sha256",
        ),
        "score_authority": _optional_identity(
            contract.get("score_authority") if isinstance(contract, Mapping) else None,
            "score_authority",
        ),
    }


def _usage_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    metering = row.get("metering")
    provider = metering.get("provider") if isinstance(metering, Mapping) else None
    provider_usage = provider.get("usage") if isinstance(provider, Mapping) else None
    tools = metering.get("tools") if isinstance(metering, Mapping) else None
    evas_usage = row.get("evas_usage")
    return {
        "provider_requests": _optional_cost(
            provider.get("requests") if isinstance(provider, Mapping) else None,
            "provider_requests",
        ),
        "tool_requests": _optional_cost(
            tools.get("requests") if isinstance(tools, Mapping) else None,
            "tool_requests",
        ),
        "output_tokens": _optional_cost(
            provider_usage.get("completion_tokens")
            if isinstance(provider_usage, Mapping)
            else row.get("output_tokens"),
            "output_tokens",
        ),
        "evas_invocations": _optional_cost(
            evas_usage.get("calls_executed") if isinstance(evas_usage, Mapping) else None,
            "evas_invocations",
        ),
    }


def _attempt_costs(row: Mapping[str, Any]) -> dict[str, Any]:
    sequence = row.get("attempt_sequence")
    if isinstance(sequence, Mapping):
        raw_attempts = sequence.get("attempts")
        if not isinstance(raw_attempts, list) or not raw_attempts:
            raise ValueError("attempt_sequence attempts must be a non-empty list")
        attempts = [_attempt_projection(attempt) for attempt in raw_attempts]
    else:
        attempts = [
            {
                "attempt_id": _string(row.get("attempt_id"), "attempt_id"),
                "costs": _usage_projection(row),
            }
        ]
    return {
        "attempts": attempts,
        "totals": _cost_totals([attempt["costs"] for attempt in attempts]),
    }


def _attempt_projection(raw: Any) -> dict[str, Any]:
    attempt = _mapping(raw, "attempt")
    costs = _mapping(attempt.get("costs"), "attempt costs")
    return {
        "attempt_id": _string(attempt.get("attempt_id"), "attempt_id"),
        "costs": {
            field: _optional_cost(costs.get(field), field)
            for field in _COST_FIELDS
        },
    }


def _cost_totals(costs: Sequence[Mapping[str, int | None]]) -> dict[str, Any]:
    totals: dict[str, Any] = {}
    for field in _COST_FIELDS:
        known_values = [cost[field] for cost in costs if cost[field] is not None]
        known_subtotal = sum(int(value) for value in known_values)
        unknown_count = len(costs) - len(known_values)
        totals[field] = None if unknown_count else known_subtotal
        totals[f"{field}_known_subtotal"] = known_subtotal
        totals[f"{field}_unknown_count"] = unknown_count
    return totals


def _selected_attempt(
    row: Mapping[str, Any],
    attempts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    attempt_id = _string(row.get("attempt_id"), "attempt_id")
    matches = [attempt for attempt in attempts if attempt["attempt_id"] == attempt_id]
    if len(matches) != 1:
        raise ValueError("selected attempt must match exactly one attempt")
    return {"attempt_id": attempt_id, "costs": matches[0]["costs"]}


def _paired_coverage(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    groups: dict[str, dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for record in records:
        identity = record["identity"]
        key = "|".join(
            [str(record["backend"])]
            + [
                str(identity[field])
                for field in ("task_id", "form", "model", "repetition")
            ]
        )
        arm = str(identity["experimental_arm"])
        if arm in groups[key]:
            raise ValueError("paired coverage contains duplicate arm")
        groups[key][arm] = record

    coverage = {}
    missing_reasons: Counter[str] = Counter()
    ineligible_reasons: Counter[str] = Counter()
    for key in sorted(groups):
        by_arm = groups[key]
        missing = [arm for arm in _THREE_ARM_ORDER if arm not in by_arm]
        for arm in missing:
            missing_reasons[arm] += 1
        eligible = {
            arm: record
            for arm, record in by_arm.items()
            if record["actual_score_eligible"]
        }
        ineligible = {
            arm: str(record["actual_score_ineligible_reason"])
            for arm, record in by_arm.items()
            if not record["actual_score_eligible"]
        }
        for reason in ineligible.values():
            ineligible_reasons[reason] += 1
        deltas = {}
        for left, right in _DELTA_PAIRS:
            label = f"{left}_minus_{right}"
            if left in eligible and right in eligible:
                deltas[label] = eligible[left]["actual_score"] - eligible[right]["actual_score"]
            else:
                deltas[label] = None
        coverage[key] = {
            "present_arms": sorted(by_arm),
            "eligible_arms": sorted(eligible),
            "missing_arms": missing,
            "ineligible_arms": dict(sorted(ineligible.items())),
            "complete_three_arm_actual_score": not missing and not ineligible,
            "deltas": deltas,
        }
    return {
        "coverage": coverage,
        "unmatched_reasons": {
            "ineligible_actual_score": dict(sorted(ineligible_reasons.items())),
            "missing_arm": dict(sorted(missing_reasons.items())),
        },
    }


def _deadline_terminal_stats(records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    deadline_primary = 0
    post_deadline = 0
    non_deadline = 0
    for record in records:
        status = record["status"]
        terminal = str(status.get("terminal_reason") or status.get("termination_reason") or "")
        if status.get("deadline_bucket") == "post_deadline" or "post_deadline" in terminal:
            post_deadline += 1
        elif "deadline" in terminal or terminal in {"agent_timeout", "submitted_at_budget"}:
            deadline_primary += 1
        else:
            non_deadline += 1
    return {
        "deadline_primary": deadline_primary,
        "post_deadline": post_deadline,
        "non_deadline_terminal": non_deadline,
    }


def _claim_index(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    authorities = Counter(record.get("score_authority") or "unknown" for record in records)
    actual_scores = sum(1 for record in records if record["actual_score_eligible"])
    all_development = authorities and set(authorities) == {"development_only"}
    unknown = "unknown" in authorities
    return {
        "development_only": {
            "allowed": bool(all_development and actual_scores),
            "evidence": {
                "score_authorities": dict(sorted(authorities.items())),
                "eligible_actual_score_cells": actual_scores,
            },
        },
        "connectivity_only": {
            "allowed": bool(not actual_scores and not unknown),
            "reason": "no eligible actual scores" if not actual_scores else "actual scores present",
        },
        "realrununknown": {
            "allowed": bool(unknown),
            "reason": "one or more rows lack bound score authority"
            if unknown
            else "all rows have declared score authority",
        },
        "model_quality_claim": {
            "allowed": False,
            "reason": "ledger projection only; no formal/model-quality claim is generated",
        },
    }


def _score_authority(row: Mapping[str, Any]) -> str | None:
    trusted = row.get("trusted_replay")
    profile = trusted.get("final_test_profile") if isinstance(trusted, Mapping) else None
    contract = (
        profile.get("score_sidecar_contract") if isinstance(profile, Mapping) else None
    )
    return _optional_identity(
        contract.get("score_authority") if isinstance(contract, Mapping) else None,
        "score_authority",
    )


def _ineligible_reason(
    score: int | float | None,
    judge_status: str,
    score_authority: str | None,
) -> str | None:
    if judge_status in _INFRA_STATUSES:
        return judge_status
    if score is None:
        return "score_null"
    if score_authority not in _SCORE_AUTHORITIES:
        return "score_authority_unknown"
    return None


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return dict(value)


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _optional_identity(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return _string(value, label)


def _effective_model(
    campaign: Mapping[str, Any],
    cell: Mapping[str, Any],
    row: Mapping[str, Any],
) -> str:
    value, _ = _effective_model_for_record(campaign, cell, row)
    return value


def _effective_model_for_record(
    campaign: Mapping[str, Any],
    cell: Mapping[str, Any],
    row: Mapping[str, Any],
) -> tuple[str, str]:
    if "model" in cell:
        expected = _string(cell.get("model"), "model")
        base_source = "campaign_cell"
    else:
        expected = _string(campaign.get("model"), "model")
        base_source = "campaign"
    if "model" in row:
        observed = _string(row.get("model"), "model")
        if observed != expected:
            raise ValueError("scheduled row metadata mismatch")
        return observed, "row"
    return expected, base_source


def _effective_repetition(
    cell: Mapping[str, Any],
    row: Mapping[str, Any],
) -> str | int:
    value, _ = _effective_repetition_for_record(cell, row)
    return value


def _effective_repetition_for_record(
    cell: Mapping[str, Any],
    row: Mapping[str, Any],
) -> tuple[str | int, str]:
    expected = _required_scalar(cell.get("repetition"), "repetition")
    if "repetition" in row:
        observed = _required_scalar(row.get("repetition"), "repetition")
        if observed != expected:
            raise ValueError("scheduled row metadata mismatch")
        return observed, "row"
    return expected, "campaign_cell"


def _arm(value: Any) -> str:
    text = _string(value, "experimental_arm")
    if text not in _ALLOWED_SINGLE_TRAJECTORY_ARMS:
        raise ValueError("experimental_arm must be OneShot, Agent-No-EVAS, or Agentic")
    return text


def _backend(value: Any) -> str:
    text = _string(value, "backend")
    if text not in _ALLOWED_BACKENDS:
        raise ValueError("backend must be native-mini-swe or native-reasoning")
    return text


def _optional_scalar(value: Any, label: str) -> str | int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError(f"{label} must be string, integer, or null")
    if isinstance(value, str) and not value:
        raise ValueError(f"{label} must be non-empty when present")
    if isinstance(value, int) and value < 0:
        raise ValueError(f"{label} must be non-negative when present")
    return value


def _required_scalar(value: Any, label: str) -> str | int:
    observed = _optional_scalar(value, label)
    if observed is None:
        raise ValueError(f"{label} must be present")
    return observed


def _score(value: Any) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("score must be a finite number or null")
    if not math.isfinite(value):
        raise ValueError("score must be a finite number or null")
    return value


def _optional_cost(value: Any, label: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer or null")
    return value


def _optional_sha(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return _sha256(value, label)


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{label} must be a SHA-256 hex digest")
    return value


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
