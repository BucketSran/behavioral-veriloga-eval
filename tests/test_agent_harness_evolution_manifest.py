from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from runners.agent_harness.evolution_manifest import (
    EvolutionReducerError,
    build_round_snapshot,
    evolution_manifest_sha256,
    select_candidate,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "vaevas-evolution-manifest-v1.schema.json"
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _manifest(**updates: Any) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "schema_version": "vaevas-evolution-manifest-v1",
        "manifest_id": "r53/alphapollo-evolution-v1",
        "condition": "AlphaApollo-Evolution+EVAS",
        "benchmark_release": "benchmarkv4-r53",
        "evaluator": {"engine": "evas", "version": "0.8.7"},
        "rounds": 2,
        "branch_roster": [
            {
                "branch_id": "branch-a",
                "backend_profile_sha256": SHA_A,
                "model_ref": "provider/model-a",
            },
            {
                "branch_id": "branch-b",
                "backend_profile_sha256": SHA_B,
                "model_ref": "provider/model-b",
            },
        ],
        "budgets": {
            "per_branch": {
                "model_calls": 2,
                "tool_calls": 8,
                "public_validation_calls": 2,
            },
            "total": {
                "model_calls": 4,
                "tool_calls": 16,
                "public_validation_calls": 4,
            },
        },
        "tool_registry_sha256": SHA_A,
        "public_validation_profile_sha256": SHA_B,
        "final_test_profile_sha256": SHA_C,
        "memory_policy": "episode_local_public_only",
        "round_barrier_policy": "strict_all_branches_or_declared_timeout",
        "branch_timeout_policy": "classify_branch_timeout_and_seal_round",
        "global_deadline_policy": "discard_unsealed_round_use_prior_incumbent",
        "selection_rule": {
            "metric_order": ["sim_correct", "dut_compile", "tb_compile"],
            "tiebreak": ["candidate_tree_sha256", "candidate_id"],
        },
        "final_submission_policy": "freeze_selected_candidate_then_final_test_once",
    }
    manifest.update(updates)
    return manifest


def _candidate(
    candidate_id: str,
    tree_sha256: str,
    metrics: dict[str, float],
    *,
    branch_id: str = "branch-a",
    status: str = "completed",
    completion_order: int = 0,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "branch_id": branch_id,
        "round_index": 1,
        "candidate_tree_sha256": tree_sha256,
        "public_validation": {
            "profile_sha256": SHA_B,
            "metrics": metrics,
            "event_sha256": SHA_D,
        },
        "status": status,
        "completion_order": completion_order,
    }


def test_evolution_manifest_is_schema_valid_and_hashable() -> None:
    manifest = _manifest()

    jsonschema.validate(manifest, _schema())

    assert len(evolution_manifest_sha256(manifest)) == 64
    assert evolution_manifest_sha256(manifest) == evolution_manifest_sha256(
        dict(reversed(list(manifest.items())))
    )


def test_round_snapshot_is_completion_order_invariant() -> None:
    manifest = _manifest()
    first_order = [
        _candidate("candidate-b", SHA_B, {"sim_correct": 1.0}, completion_order=1),
        _candidate("candidate-a", SHA_A, {"sim_correct": 1.0}, completion_order=0),
    ]
    second_order = list(reversed(first_order))

    first = build_round_snapshot(manifest=manifest, round_index=1, candidates=first_order)
    second = build_round_snapshot(manifest=manifest, round_index=1, candidates=second_order)

    assert first["round_snapshot_sha256"] == second["round_snapshot_sha256"]
    assert [item["candidate_id"] for item in first["candidates"]] == [
        "candidate-a",
        "candidate-b",
    ]


def test_selection_uses_public_metrics_then_tree_hash_then_candidate_id() -> None:
    manifest = _manifest()
    candidates = [
        _candidate(
            "candidate-later",
            SHA_B,
            {"sim_correct": 1.0, "dut_compile": 1.0, "tb_compile": 1.0},
            completion_order=99,
        ),
        _candidate(
            "candidate-winner",
            SHA_A,
            {"sim_correct": 1.0, "dut_compile": 1.0, "tb_compile": 1.0},
            completion_order=1,
        ),
        _candidate(
            "candidate-low",
            SHA_C,
            {"sim_correct": 0.0, "dut_compile": 1.0, "tb_compile": 1.0},
            completion_order=0,
        ),
    ]

    selected = select_candidate(manifest=manifest, candidates=candidates)

    assert selected["candidate_id"] == "candidate-winner"


def test_final_or_trusted_feedback_is_rejected_from_evolution_rounds() -> None:
    manifest = _manifest()
    candidate = _candidate("candidate-a", SHA_A, {"sim_correct": 1.0})
    candidate["final_test"] = {"verdict": "pass", "event_sha256": SHA_C}

    with pytest.raises(EvolutionReducerError, match="final_feedback"):
        build_round_snapshot(manifest=manifest, round_index=1, candidates=[candidate])


def test_timeout_and_global_deadline_policies_are_deterministic() -> None:
    manifest = _manifest()
    timeout_candidate = _candidate(
        "candidate-timeout",
        SHA_A,
        {},
        status="branch_timeout",
    )
    sealed = build_round_snapshot(
        manifest=manifest,
        round_index=1,
        candidates=[timeout_candidate],
        round_sealed=True,
        global_deadline_reached=False,
    )

    assert sealed["candidates"][0]["status"] == "branch_timeout"

    with pytest.raises(EvolutionReducerError, match="unsealed round"):
        build_round_snapshot(
            manifest=manifest,
            round_index=2,
            candidates=[_candidate("candidate-late", SHA_B, {"sim_correct": 1.0})],
            round_sealed=False,
            global_deadline_reached=True,
        )


def test_retry_round_uses_same_frozen_input_without_partial_memory_inheritance() -> None:
    manifest = _manifest()
    snapshot = build_round_snapshot(
        manifest=manifest,
        round_index=0,
        candidates=[],
        retry_parent_attempt_id="attempt-1",
        memory_snapshot_sha256=None,
        frozen_input_sha256=SHA_A,
    )

    assert snapshot["frozen_input_sha256"] == SHA_A
    assert snapshot["memory_snapshot_sha256"] is None
    assert snapshot["retry_parent_attempt_id"] == "attempt-1"
