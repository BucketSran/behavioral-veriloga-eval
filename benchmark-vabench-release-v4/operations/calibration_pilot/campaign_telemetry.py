"""Shared generation/scoring summaries; diagnostic markers are not authority."""
from __future__ import annotations

from typing import Any

from mini_swe_vabench import CANDIDATE_TREE_SCHEMA_VERSION, summarize_evas_operations


def model_event_hit_limit(event: dict[str, Any]) -> bool:
    if event.get("finish_reason") == "length":
        return True
    requested = event.get("requested_max_tokens")
    generated = event.get("provider_output_tokens")
    return (
        isinstance(requested, int)
        and requested > 0
        and isinstance(generated, int)
        and generated >= requested
    )


def summarize_evas_invocations(invocations: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = [str(row.get("status") or "unknown") for row in invocations]
    candidate_tree_hash_call_counts: dict[str, int] = {}
    modified_rerun_count = 0
    unchanged_repeat_count = 0
    previous_hash: str | None = None
    for row in invocations:
        raw_hash = row.get("candidate_tree_sha256")
        candidate_hash = raw_hash if isinstance(raw_hash, str) and raw_hash else None
        if candidate_hash is None:
            previous_hash = None
            continue
        candidate_tree_hash_call_counts[candidate_hash] = (
            candidate_tree_hash_call_counts.get(candidate_hash, 0) + 1
        )
        if previous_hash is not None:
            if candidate_hash == previous_hash:
                unchanged_repeat_count += 1
            else:
                modified_rerun_count += 1
        previous_hash = candidate_hash
    return {
        "schema_version": "v4-direct-evas-usage-v2",
        "calls_executed": len(invocations),
        "calls_succeeded": statuses.count("succeeded"),
        "calls_failed": statuses.count("failed"),
        "calls_timed_out": statuses.count("timed_out"),
        "calls_interrupted": statuses.count("interrupted"),
        "last_status": statuses[-1] if statuses else None,
        "candidate_tree_schema_version": CANDIDATE_TREE_SCHEMA_VERSION,
        "calls_with_candidate_tree_hash": sum(
            candidate_tree_hash_call_counts.values()
        ),
        "unique_candidate_tree_hashes": list(
            candidate_tree_hash_call_counts
        ),
        "candidate_tree_hash_call_counts": candidate_tree_hash_call_counts,
        "modified_rerun_count": modified_rerun_count,
        "unchanged_repeat_count": unchanged_repeat_count,
        **({"untrusted_operation_summary": summarize_evas_operations(invocations)}
           if any("operation" in row for row in invocations) else {}),
    }
