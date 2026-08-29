from __future__ import annotations

import hashlib
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
    select_last_sealed_incumbent,
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
            "metrics": [
                {"name": "sim_correct", "direction": "maximize"},
                {"name": "dut_compile", "direction": "maximize"},
                {"name": "tb_compile", "direction": "maximize"},
                {"name": "diagnostic_cost", "direction": "minimize"},
            ],
            "tiebreak": ["candidate_tree_sha256", "candidate_id"],
        },
        "final_submission_policy": "freeze_selected_candidate_then_final_test_once",
    }
    manifest.update(updates)
    return manifest


def _metrics(**updates: float) -> dict[str, float]:
    metrics = {
        "sim_correct": 1.0,
        "dut_compile": 1.0,
        "tb_compile": 1.0,
        "diagnostic_cost": 1.0,
    }
    metrics.update(updates)
    return metrics


def _candidate(
    candidate_id: str,
    tree_sha256: str,
    metrics: dict[str, Any],
    *,
    branch_id: str = "branch-a",
    status: str = "completed",
    round_index: int = 1,
    completion_order: int = 0,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "branch_id": branch_id,
        "round_index": round_index,
        "candidate_tree_sha256": tree_sha256,
        "public_validation": {
            "profile_sha256": SHA_B,
            "metrics": metrics,
            "event_sha256": SHA_D,
        },
        "status": status,
        "completion_order": completion_order,
    }


def _rehash_snapshot(snapshot: dict[str, Any]) -> None:
    unsigned = dict(snapshot)
    unsigned.pop("round_snapshot_sha256", None)
    canonical = json.dumps(
        unsigned,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    snapshot["round_snapshot_sha256"] = hashlib.sha256(canonical).hexdigest()


def test_current_manifest_instance_is_schema_valid_hashable_and_pinned() -> None:
    manifest = _manifest()

    jsonschema.validate(manifest, _schema())

    assert manifest["benchmark_release"] == "benchmarkv4-r53"
    assert manifest["evaluator"] == {"engine": "evas", "version": "0.8.7"}
    assert len(evolution_manifest_sha256(manifest)) == 64
    assert evolution_manifest_sha256(manifest) == evolution_manifest_sha256(
        dict(reversed(list(manifest.items())))
    )


def test_schema_is_generic_but_requires_explicit_metric_directions() -> None:
    successor = _manifest(
        benchmark_release="benchmarkv4-r54",
        evaluator={"engine": "evas", "version": "0.8.8"},
    )

    jsonschema.validate(successor, _schema())

    invalid = _manifest(selection_rule={"metric_order": ["sim_correct"]})
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(invalid, _schema())


@pytest.mark.parametrize(
    "updates",
    [
        {"rounds": 0},
        {"evaluator": {"engine": "", "version": "0.8.7"}},
        {"evaluator": {"engine": "evas", "version": "0.8.7", "extra": "x"}},
        {
            "branch_roster": [
                {
                    "branch_id": "branch-a",
                    "backend_profile_sha256": SHA_A,
                    "model_ref": "provider/model-a",
                    "extra": "x",
                }
            ]
        },
        {
            "branch_roster": [
                {
                    "branch_id": "branch-a",
                    "backend_profile_sha256": SHA_A,
                    "model_ref": "provider/model-a",
                },
                {
                    "branch_id": "branch-a",
                    "backend_profile_sha256": SHA_B,
                    "model_ref": "provider/model-b",
                },
            ]
        },
        {
            "budgets": {
                "per_branch": {
                    "model_calls": True,
                    "tool_calls": 8,
                    "public_validation_calls": 2,
                },
                "total": {
                    "model_calls": 4,
                    "tool_calls": 16,
                    "public_validation_calls": 4,
                },
            }
        },
        {"tool_registry_sha256": "not-a-sha"},
        {"memory_policy": "global"},
        {"round_barrier_policy": "best_effort"},
    ],
)
def test_runtime_rejects_malformed_manifest_contracts(
    updates: dict[str, object],
) -> None:
    with pytest.raises(EvolutionReducerError):
        evolution_manifest_sha256(_manifest(**updates))


def test_round_snapshot_is_completion_order_invariant() -> None:
    manifest = _manifest()
    first_order = [
        _candidate(
            "candidate-b",
            SHA_B,
            _metrics(diagnostic_cost=3.0),
            branch_id="branch-b",
            completion_order=1,
        ),
        _candidate("candidate-a", SHA_A, _metrics(diagnostic_cost=1.0)),
    ]
    second_order = list(reversed(first_order))

    first = build_round_snapshot(manifest=manifest, round_index=1, candidates=first_order)
    second = build_round_snapshot(manifest=manifest, round_index=1, candidates=second_order)

    assert first["round_snapshot_sha256"] == second["round_snapshot_sha256"]
    assert [item["candidate_id"] for item in first["candidates"]] == [
        "candidate-a",
        "candidate-b",
    ]


def test_round_index_must_be_within_manifest_rounds() -> None:
    with pytest.raises(EvolutionReducerError, match="round_index_out_of_range"):
        build_round_snapshot(
            manifest=_manifest(rounds=2),
            round_index=2,
            candidates=[],
            round_sealed=False,
        )


def test_selection_uses_metric_directions_then_tree_hash_then_candidate_id() -> None:
    manifest = _manifest()
    candidates = [
        _candidate(
            "candidate-expensive",
            SHA_A,
            _metrics(diagnostic_cost=4.0),
        ),
        _candidate(
            "candidate-cheap",
            SHA_B,
            _metrics(diagnostic_cost=2.0),
            branch_id="branch-b",
            completion_order=99,
        ),
    ]

    assert select_candidate(manifest=manifest, candidates=candidates)["candidate_id"] == (
        "candidate-cheap"
    )

    tied = [
        _candidate("candidate-z", SHA_B, _metrics()),
        _candidate("candidate-a", SHA_A, _metrics(), branch_id="branch-b"),
    ]

    assert select_candidate(manifest=manifest, candidates=tied)["candidate_id"] == (
        "candidate-a"
    )


@pytest.mark.parametrize(
    "metrics",
    [
        {"dut_compile": 1.0, "tb_compile": 1.0, "diagnostic_cost": 1.0},
        {
            "sim_correct": True,
            "dut_compile": 1.0,
            "tb_compile": 1.0,
            "diagnostic_cost": 1.0,
        },
        {
            "sim_correct": "1.0",
            "dut_compile": 1.0,
            "tb_compile": 1.0,
            "diagnostic_cost": 1.0,
        },
        {
            "sim_correct": float("nan"),
            "dut_compile": 1.0,
            "tb_compile": 1.0,
            "diagnostic_cost": 1.0,
        },
        {
            "sim_correct": float("inf"),
            "dut_compile": 1.0,
            "tb_compile": 1.0,
            "diagnostic_cost": 1.0,
        },
    ],
)
def test_selection_rejects_missing_boolean_non_numeric_or_non_finite_metrics(
    metrics: dict[str, Any],
) -> None:
    with pytest.raises(EvolutionReducerError, match="invalid_metric"):
        select_candidate(
            manifest=_manifest(),
            candidates=[_candidate("candidate-a", SHA_A, metrics)],
        )


def test_selection_rejects_extra_metrics_and_invalid_sibling_candidates() -> None:
    extra_metrics = dict(_metrics())
    extra_metrics["final_score"] = 1.0
    with pytest.raises(EvolutionReducerError, match="invalid_metric"):
        select_candidate(
            manifest=_manifest(),
            candidates=[_candidate("candidate-a", SHA_A, extra_metrics)],
        )


def test_candidate_round_and_public_validation_contract_fail_closed() -> None:
    boolean_round = _candidate("candidate-a", SHA_A, _metrics(), round_index=True)
    with pytest.raises(ValueError, match="round_index"):
        build_round_snapshot(
            manifest=_manifest(),
            round_index=1,
            candidates=[
                boolean_round,
                _candidate("candidate-b", SHA_B, _metrics(), branch_id="branch-b"),
            ],
        )

    leaky_validation = _candidate("candidate-a", SHA_A, _metrics())
    leaky_validation["public_validation"]["private_checker_hint"] = "hidden"
    with pytest.raises(EvolutionReducerError, match="public_validation"):
        build_round_snapshot(
            manifest=_manifest(),
            round_index=1,
            candidates=[
                leaky_validation,
                _candidate("candidate-b", SHA_B, _metrics(), branch_id="branch-b"),
            ],
        )

    invalid_sibling = _candidate(
        "candidate-bad",
        SHA_B,
        _metrics(),
        branch_id="branch-b",
        status="invalid_status",
    )
    with pytest.raises(EvolutionReducerError, match="invalid_candidate_status"):
        select_candidate(
            manifest=_manifest(),
            candidates=[
                _candidate("candidate-good", SHA_A, _metrics()),
                invalid_sibling,
            ],
        )

    with pytest.raises(EvolutionReducerError, match="duplicate_branch_id"):
        select_candidate(
            manifest=_manifest(),
            candidates=[
                _candidate("candidate-a", SHA_A, _metrics()),
                _candidate("candidate-b", SHA_B, _metrics()),
            ],
        )

    with pytest.raises(EvolutionReducerError, match="round_index_mismatch"):
        select_candidate(
            manifest=_manifest(),
            candidates=[
                _candidate("candidate-a", SHA_A, _metrics(), round_index=0),
                _candidate(
                    "candidate-b",
                    SHA_B,
                    _metrics(),
                    branch_id="branch-b",
                    round_index=1,
                ),
            ],
        )


def test_final_trusted_and_unknown_candidate_fields_are_rejected() -> None:
    final_candidate = _candidate("candidate-a", SHA_A, _metrics())
    final_candidate["final_test"] = {"verdict": "pass", "event_sha256": SHA_C}

    with pytest.raises(EvolutionReducerError, match="final_feedback"):
        build_round_snapshot(
            manifest=_manifest(),
            round_index=1,
            candidates=[
                final_candidate,
                _candidate("candidate-b", SHA_B, _metrics(), branch_id="branch-b"),
            ],
        )

    unknown_candidate = _candidate("candidate-a", SHA_A, _metrics())
    unknown_candidate["unexpected"] = "leaky"
    with pytest.raises(EvolutionReducerError, match="unknown_candidate_fields"):
        build_round_snapshot(
            manifest=_manifest(),
            round_index=1,
            candidates=[
                unknown_candidate,
                _candidate("candidate-b", SHA_B, _metrics(), branch_id="branch-b"),
            ],
        )


def test_candidate_records_must_match_roster_round_and_unique_identities() -> None:
    manifest = _manifest()

    with pytest.raises(EvolutionReducerError, match="unknown_branch"):
        build_round_snapshot(
            manifest=manifest,
            round_index=1,
            candidates=[
                _candidate("candidate-a", SHA_A, _metrics(), branch_id="branch-z"),
                _candidate("candidate-b", SHA_B, _metrics(), branch_id="branch-b"),
            ],
        )

    with pytest.raises(EvolutionReducerError, match="round_index_mismatch"):
        build_round_snapshot(
            manifest=manifest,
            round_index=1,
            candidates=[
                _candidate("candidate-a", SHA_A, _metrics(), round_index=2),
                _candidate("candidate-b", SHA_B, _metrics(), branch_id="branch-b"),
            ],
        )

    with pytest.raises(EvolutionReducerError, match="duplicate_candidate_id"):
        build_round_snapshot(
            manifest=manifest,
            round_index=1,
            candidates=[
                _candidate("candidate-a", SHA_A, _metrics()),
                _candidate("candidate-a", SHA_B, _metrics(), branch_id="branch-b"),
            ],
        )

    with pytest.raises(EvolutionReducerError, match="duplicate_branch_id"):
        build_round_snapshot(
            manifest=manifest,
            round_index=1,
            candidates=[
                _candidate("candidate-a", SHA_A, _metrics()),
                _candidate("candidate-b", SHA_B, _metrics()),
            ],
        )


def test_strict_barrier_requires_one_terminal_record_per_roster_branch() -> None:
    manifest = _manifest()

    sealed = build_round_snapshot(
        manifest=manifest,
        round_index=1,
        candidates=[
            _candidate("candidate-timeout", SHA_A, {}, status="branch_timeout"),
            _candidate(
                "candidate-failed",
                SHA_B,
                {},
                branch_id="branch-b",
                status="branch_failed",
            ),
        ],
    )

    assert {candidate["status"] for candidate in sealed["candidates"]} == {
        "branch_timeout",
        "branch_failed",
    }

    with pytest.raises(EvolutionReducerError, match="strict_barrier"):
        build_round_snapshot(
            manifest=manifest,
            round_index=1,
            candidates=[_candidate("candidate-a", SHA_A, _metrics())],
        )

    with pytest.raises(EvolutionReducerError, match="strict_barrier"):
        build_round_snapshot(
            manifest=manifest,
            round_index=1,
            candidates=[],
            round_sealed=True,
        )


def test_global_deadline_never_adopts_unsealed_round_and_uses_last_sealed_incumbent() -> None:
    manifest = _manifest()
    round_zero = build_round_snapshot(
        manifest=manifest,
        round_index=0,
        candidates=[
            _candidate("candidate-old", SHA_C, _metrics(), round_index=0),
            _candidate(
                "candidate-old-b",
                SHA_D,
                _metrics(),
                branch_id="branch-b",
                round_index=0,
            ),
        ],
    )
    round_one = build_round_snapshot(
        manifest=manifest,
        round_index=1,
        candidates=[
            _candidate("candidate-new", SHA_A, _metrics()),
            _candidate("candidate-new-b", SHA_B, _metrics(), branch_id="branch-b"),
        ],
    )

    assert select_last_sealed_incumbent(
        [round_one, round_zero],
        manifest=_manifest(),
    )["candidate_id"] == "candidate-new"

    with pytest.raises(EvolutionReducerError, match="unsealed round"):
        build_round_snapshot(
            manifest=manifest,
            round_index=1,
            candidates=[
                _candidate("candidate-late", SHA_A, _metrics(), round_index=1),
                _candidate(
                    "candidate-late-b",
                    SHA_B,
                    _metrics(),
                    branch_id="branch-b",
                    round_index=1,
                ),
            ],
            round_sealed=False,
            global_deadline_reached=True,
        )
    with pytest.raises(EvolutionReducerError, match="no sealed incumbent"):
        select_last_sealed_incumbent([], manifest=_manifest())


def test_last_sealed_incumbent_rejects_forged_or_mismatched_snapshots() -> None:
    manifest = _manifest()
    snapshot = build_round_snapshot(
        manifest=manifest,
        round_index=1,
        candidates=[
            _candidate("candidate-a", SHA_A, _metrics()),
            _candidate("candidate-b", SHA_B, _metrics(), branch_id="branch-b"),
        ],
    )

    forged = dict(snapshot)
    forged["selected_candidate"] = dict(forged["selected_candidate"])
    forged["selected_candidate"]["candidate_id"] = "forged"
    with pytest.raises(EvolutionReducerError, match="snapshot_hash_mismatch"):
        select_last_sealed_incumbent([forged], manifest=manifest)

    mismatched = dict(snapshot)
    mismatched["manifest_sha256"] = SHA_D
    mismatched["round_snapshot_sha256"] = SHA_D
    with pytest.raises(EvolutionReducerError, match="manifest_mismatch"):
        select_last_sealed_incumbent([mismatched], manifest=manifest)

    duplicate_round = build_round_snapshot(
        manifest=manifest,
        round_index=1,
        candidates=[
            _candidate("candidate-c", SHA_C, _metrics()),
            _candidate("candidate-d", SHA_D, _metrics(), branch_id="branch-b"),
        ],
    )
    with pytest.raises(EvolutionReducerError, match="duplicate_round"):
        select_last_sealed_incumbent([snapshot, duplicate_round], manifest=manifest)


def test_last_sealed_incumbent_recomputes_selection_and_requires_canonical_snapshot() -> None:
    manifest = _manifest()
    snapshot = build_round_snapshot(
        manifest=manifest,
        round_index=1,
        candidates=[
            _candidate("candidate-a", SHA_A, _metrics()),
            _candidate("candidate-b", SHA_B, _metrics(), branch_id="branch-b"),
        ],
    )

    wrong_incumbent = json.loads(json.dumps(snapshot))
    wrong_incumbent["selected_candidate"] = wrong_incumbent["candidates"][1]
    _rehash_snapshot(wrong_incumbent)
    with pytest.raises(EvolutionReducerError, match="selected_candidate"):
        select_last_sealed_incumbent([wrong_incumbent], manifest=manifest)

    reordered = json.loads(json.dumps(snapshot))
    reordered["candidates"].reverse()
    _rehash_snapshot(reordered)
    with pytest.raises(EvolutionReducerError, match="canonical"):
        select_last_sealed_incumbent([reordered], manifest=manifest)


def test_last_sealed_incumbent_revalidates_deadline_and_retry_contracts() -> None:
    manifest = _manifest()
    snapshot = build_round_snapshot(
        manifest=manifest,
        round_index=0,
        candidates=[],
        round_sealed=False,
        retry_parent_attempt_id="attempt-1",
        frozen_input_sha256=SHA_A,
    )

    deadline_violation = dict(snapshot)
    deadline_violation["global_deadline_reached"] = True
    _rehash_snapshot(deadline_violation)
    with pytest.raises(EvolutionReducerError, match="unsealed_round"):
        select_last_sealed_incumbent([deadline_violation], manifest=manifest)

    retry_violation = dict(snapshot)
    retry_violation["memory_snapshot_sha256"] = SHA_B
    _rehash_snapshot(retry_violation)
    with pytest.raises(EvolutionReducerError, match="retry_round_contract"):
        select_last_sealed_incumbent([retry_violation], manifest=manifest)


def test_retry_round_uses_same_frozen_input_without_partial_memory_inheritance() -> None:
    snapshot = build_round_snapshot(
        manifest=_manifest(),
        round_index=0,
        candidates=[],
        round_sealed=False,
        retry_parent_attempt_id="attempt-1",
        memory_snapshot_sha256=None,
        frozen_input_sha256=SHA_A,
    )

    assert snapshot["frozen_input_sha256"] == SHA_A
    assert snapshot["memory_snapshot_sha256"] is None
    assert snapshot["retry_parent_attempt_id"] == "attempt-1"

    with pytest.raises(EvolutionReducerError, match="retry_round_contract"):
        build_round_snapshot(
            manifest=_manifest(),
            round_index=1,
            candidates=[],
            round_sealed=False,
            retry_parent_attempt_id="attempt-1",
            memory_snapshot_sha256=None,
            frozen_input_sha256=SHA_A,
        )
    with pytest.raises(EvolutionReducerError, match="retry_round_contract"):
        build_round_snapshot(
            manifest=_manifest(),
            round_index=0,
            candidates=[],
            round_sealed=False,
            retry_parent_attempt_id="attempt-1",
            memory_snapshot_sha256=SHA_B,
            frozen_input_sha256=SHA_A,
        )
    with pytest.raises(EvolutionReducerError, match="retry_round_contract"):
        build_round_snapshot(
            manifest=_manifest(),
            round_index=0,
            candidates=[],
            round_sealed=False,
            retry_parent_attempt_id="attempt-1",
            memory_snapshot_sha256=None,
            frozen_input_sha256=None,
        )
