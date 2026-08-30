from __future__ import annotations

import json
import time
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import pytest

from runners.agent_harness.evolution_runtime import (
    EvolutionBranchFailure,
    EvolutionBranchRequest,
    EvolutionRuntimeError,
    run_evolution_rounds,
)


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64
SHA_F = "f" * 64


def _manifest(**updates: Any) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "schema_version": "vaevas-evolution-manifest-v1",
        "manifest_id": "r53/alphapollo-evolution-runtime-v1",
        "condition": "AlphaApollo-Evolution+EVAS",
        "benchmark_release": "benchmarkv4-r53",
        "evaluator": {"engine": "evas", "version": "0.8.7"},
        "rounds": 1,
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
                "tool_calls": 4,
                "public_validation_calls": 1,
            },
            "total": {
                "model_calls": 4,
                "tool_calls": 8,
                "public_validation_calls": 2,
            },
        },
        "tool_registry_sha256": SHA_C,
        "public_validation_profile_sha256": SHA_D,
        "final_test_profile_sha256": SHA_E,
        "memory_policy": "episode_local_public_only",
        "round_barrier_policy": "strict_all_branches_or_declared_timeout",
        "branch_timeout_policy": "classify_branch_timeout_and_seal_round",
        "global_deadline_policy": "discard_unsealed_round_use_prior_incumbent",
        "selection_rule": {
            "metrics": [
                {"name": "sim_correct", "direction": "maximize"},
                {"name": "diagnostic_cost", "direction": "minimize"},
            ],
            "tiebreak": ["candidate_tree_sha256", "candidate_id"],
        },
        "final_submission_policy": "freeze_selected_candidate_then_final_test_once",
    }
    manifest.update(updates)
    return manifest


def _candidate(
    candidate_id: str,
    tree_sha256: str,
    *,
    sim_correct: float = 1.0,
    diagnostic_cost: float = 1.0,
    usage: dict[str, int] | None = None,
    status: str = "completed",
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "candidate_tree_sha256": tree_sha256,
        "status": status,
        "public_validation": {
            "profile_sha256": SHA_D,
            "metrics": (
                {"sim_correct": sim_correct, "diagnostic_cost": diagnostic_cost}
                if status == "completed"
                else {}
            ),
            "event_sha256": SHA_F,
        },
        "usage": usage
        or {"model_calls": 1, "tool_calls": 2, "public_validation_calls": 1},
    }


def _sha(character: str) -> str:
    return character * 64


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_round_coordinator_runs_candidate_branches_with_same_immutable_public_snapshot(
    tmp_path: Path,
) -> None:
    calls: list[tuple[str, int, object, dict[str, int], Path]] = []
    initial_snapshot = {"entries": [{"entry_id": "seed"}]}

    def branch(request: EvolutionBranchRequest) -> dict[str, Any]:
        assert isinstance(request.public_snapshot, MappingProxyType)
        with pytest.raises(TypeError):
            request.public_snapshot["mutate"] = True  # type: ignore[index]
        calls.append(
            (
                request.branch_id,
                request.round_index,
                request.public_snapshot,
                dict(request.allowance),
                request.output_path,
            )
        )
        if request.branch_id == "branch-a":
            time.sleep(0.02)
            return _candidate("candidate-a", SHA_A, diagnostic_cost=3.0)
        return _candidate("candidate-b", SHA_B, diagnostic_cost=1.0)

    result = run_evolution_rounds(
        manifest=_manifest(),
        output_dir=tmp_path / "evolution",
        branch_callback=branch,
        initial_public_snapshot=initial_snapshot,
        max_workers=2,
    )

    assert result.selected_candidate["candidate_id"] == "candidate-b"
    assert result.final_judgment is None
    assert len(result.round_snapshots) == 1
    assert [row["candidate_id"] for row in result.round_snapshots[0]["candidates"]] == [
        "candidate-a",
        "candidate-b",
    ]
    assert len({id(call[2]) for call in calls}) == 1
    assert {call[3]["model_calls"] for call in calls} == {2}
    assert all(call[4].exists() and call[4].is_dir() for call in calls)
    assert result.usage == {
        "model_calls": 2,
        "model_calls_reported_subtotal": 2,
        "model_calls_unknown_count": 0,
        "tool_calls": 4,
        "tool_calls_reported_subtotal": 4,
        "tool_calls_unknown_count": 0,
        "public_validation_calls": 2,
        "public_validation_calls_reported_subtotal": 2,
        "public_validation_calls_unknown_count": 0,
    }
    assert _read_json(tmp_path / "evolution" / "selection.json")[
        "selected_candidate"
    ]["candidate_id"] == "candidate-b"


def test_branch_failure_is_recorded_without_dropping_the_round_denominator(
    tmp_path: Path,
) -> None:
    def branch(request: EvolutionBranchRequest) -> dict[str, Any]:
        if request.branch_id == "branch-b":
            raise RuntimeError("provider unavailable")
        return _candidate("candidate-a", SHA_A)

    result = run_evolution_rounds(
        manifest=_manifest(),
        output_dir=tmp_path / "evolution",
        branch_callback=branch,
        max_workers=2,
    )

    statuses = {record["branch_id"]: record["status"] for record in result.branch_records}
    assert statuses == {"branch-a": "completed", "branch-b": "branch_failed"}
    assert len(result.round_snapshots[0]["candidates"]) == 2
    assert result.selected_candidate["candidate_id"] == "candidate-a"
    assert result.usage["model_calls"] is None
    assert result.usage["model_calls_reported_subtotal"] == 1
    assert result.usage["model_calls_unknown_count"] == 1
    assert result.usage["tool_calls"] is None
    assert result.usage["tool_calls_reported_subtotal"] == 2
    assert result.usage["tool_calls_unknown_count"] == 1
    assert result.usage["public_validation_calls"] is None
    assert result.usage["public_validation_calls_reported_subtotal"] == 1
    assert result.usage["public_validation_calls_unknown_count"] == 1
    failed = _read_json(
        tmp_path / "evolution" / "branches" / "round-0000" / "branch-b" / "result.json"
    )["branch_record"]
    assert failed["failure"]["category"] == "branch_callback_failure"
    assert failed["public_validation"]["metrics"] == {}
    assert failed["usage"] == {
        "model_calls": None,
        "tool_calls": None,
        "public_validation_calls": None,
    }


def test_branch_failure_preserves_observed_partial_usage(tmp_path: Path) -> None:
    def branch(request: EvolutionBranchRequest) -> dict[str, Any]:
        if request.branch_id == "branch-b":
            raise EvolutionBranchFailure(
                "provider unavailable",
                observed_usage={
                    "model_calls": 1,
                    "tool_calls": None,
                    "public_validation_calls": 0,
                },
            )
        return _candidate("candidate-a", SHA_A)

    result = run_evolution_rounds(
        manifest=_manifest(),
        output_dir=tmp_path / "evolution",
        branch_callback=branch,
        max_workers=2,
    )

    failed = next(record for record in result.branch_records if record["branch_id"] == "branch-b")
    assert failed["usage"] == {
        "model_calls": 1,
        "tool_calls": None,
        "public_validation_calls": 0,
    }
    assert result.usage == {
        "model_calls": 2,
        "model_calls_reported_subtotal": 2,
        "model_calls_unknown_count": 0,
        "tool_calls": None,
        "tool_calls_reported_subtotal": 2,
        "tool_calls_unknown_count": 1,
        "public_validation_calls": 1,
        "public_validation_calls_reported_subtotal": 1,
        "public_validation_calls_unknown_count": 0,
    }


def test_branch_budget_violation_becomes_a_failed_branch_record(tmp_path: Path) -> None:
    def branch(request: EvolutionBranchRequest) -> dict[str, Any]:
        if request.branch_id == "branch-b":
            return _candidate(
                "candidate-b",
                SHA_B,
                usage={
                    "model_calls": request.allowance["model_calls"] + 1,
                    "tool_calls": 0,
                    "public_validation_calls": 0,
                },
            )
        return _candidate("candidate-a", SHA_A)

    result = run_evolution_rounds(
        manifest=_manifest(),
        output_dir=tmp_path / "evolution",
        branch_callback=branch,
        max_workers=2,
    )

    assert {record["branch_id"]: record["status"] for record in result.branch_records} == {
        "branch-a": "completed",
        "branch-b": "branch_failed",
    }
    assert result.selected_candidate["candidate_id"] == "candidate-a"
    failed = next(record for record in result.branch_records if record["branch_id"] == "branch-b")
    assert failed["usage"]["model_calls"] == 3
    assert result.usage["model_calls"] == 4
    assert result.usage["model_calls_reported_subtotal"] == 4


def test_branch_budget_overrun_counts_consumed_usage_against_total(tmp_path: Path) -> None:
    manifest = _manifest(
        budgets={
            "per_branch": {
                "model_calls": 2,
                "tool_calls": 4,
                "public_validation_calls": 1,
            },
            "total": {
                "model_calls": 4,
                "tool_calls": 8,
                "public_validation_calls": 2,
            },
        },
    )

    def branch(request: EvolutionBranchRequest) -> dict[str, Any]:
        usage = {"model_calls": 3, "tool_calls": 0, "public_validation_calls": 0}
        return _candidate(f"candidate-{request.branch_id}", SHA_A, usage=usage)

    with pytest.raises(EvolutionRuntimeError, match="total_budget_exceeded"):
        run_evolution_rounds(
            manifest=manifest,
            output_dir=tmp_path / "evolution",
            branch_callback=branch,
            max_workers=2,
        )


@pytest.mark.parametrize(
    "branch_id",
    ["", ".", "..", "../escape", "/tmp/escape", "nested/branch", r"nested\\branch"],
)
def test_branch_ids_are_single_safe_path_segments(
    tmp_path: Path,
    branch_id: str,
) -> None:
    manifest = _manifest(branch_roster=[{
        "branch_id": branch_id,
        "backend_profile_sha256": SHA_A,
        "model_ref": "provider/model-a",
    }])

    def branch(request: EvolutionBranchRequest) -> dict[str, Any]:
        return _candidate("candidate-a", SHA_A)

    with pytest.raises(EvolutionRuntimeError, match="branch_id"):
        run_evolution_rounds(
            manifest=manifest,
            output_dir=tmp_path / "evolution",
            branch_callback=branch,
        )


def test_branch_output_path_stays_confined_to_evolution_output(tmp_path: Path) -> None:
    seen: list[Path] = []

    def branch(request: EvolutionBranchRequest) -> dict[str, Any]:
        seen.append(request.output_path)
        assert (tmp_path / "evolution") in request.output_path.resolve().parents
        return _candidate(f"candidate-{request.branch_id}", SHA_A)

    run_evolution_rounds(
        manifest=_manifest(),
        output_dir=tmp_path / "evolution",
        branch_callback=branch,
        max_workers=1,
    )

    assert all(path.parent.name == "round-0000" for path in seen)


def test_result_receipts_remain_canonical_json_after_usage_summary_change(
    tmp_path: Path,
) -> None:
    def branch(request: EvolutionBranchRequest) -> dict[str, Any]:
        return _candidate(f"candidate-{request.branch_id}", SHA_A)

    run_evolution_rounds(
        manifest=_manifest(),
        output_dir=tmp_path / "evolution",
        branch_callback=branch,
        max_workers=1,
    )

    raw = (tmp_path / "evolution" / "selection.json").read_bytes()
    assert raw.endswith(b"\n")
    assert b": " in raw
    loaded = json.loads(raw)
    assert loaded["usage"]["model_calls_reported_subtotal"] == 2


def test_deadline_after_callbacks_discards_unsealed_round_and_keeps_prior_incumbent(
    tmp_path: Path,
) -> None:
    manifest = _manifest(
        rounds=2,
        budgets={
            "per_branch": {
                "model_calls": 2,
                "tool_calls": 4,
                "public_validation_calls": 1,
            },
            "total": {
                "model_calls": 8,
                "tool_calls": 16,
                "public_validation_calls": 4,
            },
        },
    )
    deadline = time.monotonic() + 0.2

    def branch(request: EvolutionBranchRequest) -> dict[str, Any]:
        if request.round_index == 1:
            time.sleep(0.25)
            return _candidate(
                f"candidate-late-{request.branch_id}",
                SHA_C if request.branch_id == "branch-a" else SHA_D,
                diagnostic_cost=0.0,
            )
        return _candidate(
            f"candidate-r0-{request.branch_id}",
            SHA_A if request.branch_id == "branch-a" else SHA_B,
            diagnostic_cost=1.0 if request.branch_id == "branch-a" else 2.0,
        )

    result = run_evolution_rounds(
        manifest=manifest,
        output_dir=tmp_path / "evolution",
        branch_callback=branch,
        deadline_monotonic=deadline,
        max_workers=2,
    )

    assert len(result.round_snapshots) == 1
    assert result.selected_candidate["candidate_id"] == "candidate-r0-branch-a"
    assert len(result.branch_records) == 4
    assert not (tmp_path / "evolution" / "rounds" / "round-0001.json").exists()
    assert (
        tmp_path / "evolution" / "rounds" / "round-0001-discarded.json"
    ).is_file()


def test_each_round_shares_only_the_prior_sealed_public_memory(tmp_path: Path) -> None:
    manifest = _manifest(
        rounds=2,
        budgets={
            "per_branch": {
                "model_calls": 2,
                "tool_calls": 4,
                "public_validation_calls": 1,
            },
            "total": {
                "model_calls": 8,
                "tool_calls": 16,
                "public_validation_calls": 4,
            },
        },
    )
    snapshots_by_round: dict[int, list[Mapping[str, Any]]] = {0: [], 1: []}

    def branch(request: EvolutionBranchRequest) -> dict[str, Any]:
        snapshots_by_round[request.round_index].append(request.public_snapshot)
        tree = _sha("c" if request.branch_id == "branch-a" else "d")
        if request.round_index == 0:
            tree = _sha("a" if request.branch_id == "branch-a" else "b")
        return _candidate(
            f"candidate-r{request.round_index}-{request.branch_id}",
            tree,
            diagnostic_cost=1.0 if request.branch_id == "branch-a" else 2.0,
        )

    result = run_evolution_rounds(
        manifest=manifest,
        output_dir=tmp_path / "evolution",
        branch_callback=branch,
        max_workers=2,
    )

    assert len({id(snapshot) for snapshot in snapshots_by_round[0]}) == 1
    assert len({id(snapshot) for snapshot in snapshots_by_round[1]}) == 1
    assert snapshots_by_round[0][0]["round_index"] == -1
    assert snapshots_by_round[1][0]["round_index"] == 0
    prior_entries = snapshots_by_round[1][0]["memory_snapshot"]["entries"]
    assert {entry["candidate_id"] for entry in prior_entries} == {
        "candidate-r0-branch-a",
        "candidate-r0-branch-b",
    }
    assert "candidate-r1-branch-a" not in str(prior_entries)
    assert result.selected_candidate["candidate_id"] == "candidate-r1-branch-a"
    assert "final" not in json.dumps(result.memory_snapshots, sort_keys=True)
    assert result.final_judgment is None


def test_evolution_output_is_write_once_and_total_budget_is_reserved_upfront(
    tmp_path: Path,
) -> None:
    def branch(request: EvolutionBranchRequest) -> dict[str, Any]:
        return _candidate(f"candidate-{request.branch_id}", SHA_A)

    output = tmp_path / "evolution"
    run_evolution_rounds(
        manifest=_manifest(),
        output_dir=output,
        branch_callback=branch,
        max_workers=1,
    )

    with pytest.raises(EvolutionRuntimeError, match="output_exists"):
        run_evolution_rounds(
            manifest=_manifest(),
            output_dir=output,
            branch_callback=branch,
        )

    insufficient = _manifest(
        budgets={
            "per_branch": {
                "model_calls": 2,
                "tool_calls": 4,
                "public_validation_calls": 1,
            },
            "total": {
                "model_calls": 1,
                "tool_calls": 8,
                "public_validation_calls": 2,
            },
        }
    )
    with pytest.raises(EvolutionRuntimeError, match="insufficient_total_budget"):
        run_evolution_rounds(
            manifest=insufficient,
            output_dir=tmp_path / "too-small",
            branch_callback=branch,
        )
