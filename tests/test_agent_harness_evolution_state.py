from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from runners.agent_harness.evolution_state import (
    CandidateLineage,
    candidate_lineage_sha256,
    freeze_memory_snapshot,
    validate_candidate_lineage_graph,
)


ROOT = Path(__file__).resolve().parents[1]
MEMORY_SCHEMA_PATH = ROOT / "schemas" / "vaevas-memory-snapshot-v1.schema.json"
CANDIDATE_SCHEMA_PATH = ROOT / "schemas" / "vaevas-candidate-lineage-v1.schema.json"
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


def _load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_memory_snapshot_is_schema_valid_and_content_addressed() -> None:
    snapshot = freeze_memory_snapshot(
        snapshot_id="memory-round-1",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=1,
        parent_snapshot_sha256=None,
        entries=[
            {
                "entry_id": "public-validator-candidate-a",
                "source_kind": "public_validation",
                "source_event_sha256": SHA_A,
                "candidate_id": "candidate-a",
                "candidate_tree_sha256": SHA_B,
                "summary": {
                    "dut_compile": 1.0,
                    "tb_compile": 1.0,
                    "sim_correct": 0.0,
                    "primary_failure": "metric_mismatch",
                },
            }
        ],
    )

    document = snapshot.to_document()

    jsonschema.validate(document, _load_schema(MEMORY_SCHEMA_PATH))
    assert document["snapshot_sha256"] == snapshot.snapshot_sha256
    assert document["redaction_policy"] == "public-feedback-redaction-v1"
    assert len(snapshot.snapshot_sha256) == 64
    assert document["entries"][0]["source_kind"] == "public_validation"


def test_memory_snapshot_hash_is_stable_and_parent_sensitive() -> None:
    first = freeze_memory_snapshot(
        snapshot_id="memory-round-1",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=1,
        parent_snapshot_sha256=None,
        entries=[
            {
                "entry_id": "candidate-summary",
                "source_kind": "candidate_summary",
                "source_event_sha256": SHA_A,
                "candidate_id": "candidate-a",
                "candidate_tree_sha256": SHA_B,
                "summary": {"status": "valid"},
            }
        ],
    )
    reordered_summary = freeze_memory_snapshot(
        snapshot_id="memory-round-1",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=1,
        parent_snapshot_sha256=None,
        entries=[
            {
                "summary": {"status": "valid"},
                "candidate_tree_sha256": SHA_B,
                "candidate_id": "candidate-a",
                "source_event_sha256": SHA_A,
                "source_kind": "candidate_summary",
                "entry_id": "candidate-summary",
            }
        ],
    )
    child = freeze_memory_snapshot(
        snapshot_id="memory-round-2",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=2,
        parent_snapshot_sha256=first.snapshot_sha256,
        entries=[],
    )

    assert first.snapshot_sha256 == reordered_summary.snapshot_sha256
    assert child.snapshot_sha256 != first.snapshot_sha256
    assert child.parent_snapshot_sha256 == first.snapshot_sha256


def test_memory_snapshot_hash_is_stable_for_same_entry_set_order() -> None:
    first = freeze_memory_snapshot(
        snapshot_id="memory-round-1",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=1,
        parent_snapshot_sha256=None,
        entries=[
            {
                "entry_id": "b-entry",
                "source_kind": "public_validation",
                "source_event_sha256": SHA_B,
                "summary": {"status": "b"},
            },
            {
                "entry_id": "a-entry",
                "source_kind": "candidate_summary",
                "source_event_sha256": SHA_A,
                "summary": {"status": "a"},
            },
        ],
    )
    second = freeze_memory_snapshot(
        snapshot_id="memory-round-1",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=1,
        parent_snapshot_sha256=None,
        entries=[
            {
                "entry_id": "a-entry",
                "source_kind": "candidate_summary",
                "source_event_sha256": SHA_A,
                "summary": {"status": "a"},
            },
            {
                "entry_id": "b-entry",
                "source_kind": "public_validation",
                "source_event_sha256": SHA_B,
                "summary": {"status": "b"},
            },
        ],
    )

    assert first.snapshot_sha256 == second.snapshot_sha256
    assert [entry["entry_id"] for entry in first.to_document()["entries"]] == [
        "a-entry",
        "b-entry",
    ]


def test_memory_snapshot_rejects_extra_fields_and_duplicate_entry_ids() -> None:
    with pytest.raises(ValueError, match="extra fields"):
        freeze_memory_snapshot(
            snapshot_id="memory-round-1",
            episode_id="episode-1",
            attempt_id="attempt-1",
            task_id="task-001",
            condition="AlphaApollo-Evolution+EVAS",
            round_index=1,
            parent_snapshot_sha256=None,
            entries=[
                {
                    "entry_id": "entry-a",
                    "source_kind": "candidate_summary",
                    "source_event_sha256": SHA_A,
                    "summary": {"status": "a"},
                    "final_score": 1.0,
                }
            ],
        )

    with pytest.raises(ValueError, match="duplicate memory entry_id"):
        freeze_memory_snapshot(
            snapshot_id="memory-round-1",
            episode_id="episode-1",
            attempt_id="attempt-1",
            task_id="task-001",
            condition="AlphaApollo-Evolution+EVAS",
            round_index=1,
            parent_snapshot_sha256=None,
            entries=[
                {
                    "entry_id": "entry-a",
                    "source_kind": "candidate_summary",
                    "source_event_sha256": SHA_A,
                    "summary": {"status": "a"},
                },
                {
                    "entry_id": "entry-a",
                    "source_kind": "public_validation",
                    "source_event_sha256": SHA_B,
                    "summary": {"status": "b"},
                },
            ],
        )


@pytest.mark.parametrize(
    "forbidden_source_kind",
    [
        "final_judgment",
        "final_score_sidecar",
        "private_checker",
        "trusted_event",
    ],
)
def test_memory_snapshot_rejects_final_or_private_feedback(
    forbidden_source_kind: str,
) -> None:
    with pytest.raises(ValueError):
        freeze_memory_snapshot(
            snapshot_id="leaky-memory",
            episode_id="episode-1",
            attempt_id="attempt-1",
            task_id="task-001",
            condition="AlphaApollo-Evolution+EVAS",
            round_index=1,
            parent_snapshot_sha256=None,
            entries=[
                {
                    "entry_id": "leaky-entry",
                    "source_kind": forbidden_source_kind,
                    "source_event_sha256": SHA_A,
                    "summary": {"status": "pass"},
                }
            ],
        )


def test_memory_snapshot_rejects_nested_private_summary_keys() -> None:
    with pytest.raises(ValueError, match="forbidden memory summary key"):
        freeze_memory_snapshot(
            snapshot_id="leaky-memory",
            episode_id="episode-1",
            attempt_id="attempt-1",
            task_id="task-001",
            condition="AlphaApollo-Evolution+EVAS",
            round_index=1,
            parent_snapshot_sha256=None,
            entries=[
                {
                    "entry_id": "public-validation-with-hidden-score",
                    "source_kind": "public_validation",
                    "source_event_sha256": SHA_A,
                    "summary": {
                        "compile": {"status": "pass"},
                        "nested": {
                            "score_sidecar_hash": SHA_B,
                            "provider_response": {"raw_cot": "hidden"},
                        },
                    },
                }
            ],
        )


def test_memory_snapshot_accepts_public_validation_summary_fields() -> None:
    snapshot = freeze_memory_snapshot(
        snapshot_id="public-memory",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=1,
        parent_snapshot_sha256=None,
        entries=[
            {
                "entry_id": "public-validation",
                "source_kind": "public_validation",
                "source_event_sha256": SHA_A,
                "summary": {
                    "compile": {"dut_compile": 1.0, "tb_compile": 1.0},
                    "runtime": {"exit_code": 0},
                    "metric": {"sim_correct": 0.0},
                    "authoritative_metric": "public-evas-observation",
                    "log_excerpt": "public excerpt",
                    "waveform_summary": {"settled": False},
                },
            }
        ],
    )

    jsonschema.validate(snapshot.to_document(), _load_schema(MEMORY_SCHEMA_PATH))


def test_retry_memory_snapshot_starts_fresh_unless_explicit_parent_is_declared() -> None:
    retry_snapshot = freeze_memory_snapshot(
        snapshot_id="retry-memory",
        episode_id="episode-1",
        attempt_id="attempt-2",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=0,
        parent_snapshot_sha256=None,
        retry_parent_attempt_id="attempt-1",
        entries=[],
    )

    assert retry_snapshot.parent_snapshot_sha256 is None
    assert retry_snapshot.retry_parent_attempt_id == "attempt-1"

    with pytest.raises(ValueError, match="fresh retry"):
        freeze_memory_snapshot(
            snapshot_id="retry-memory-leak",
            episode_id="episode-1",
            attempt_id="attempt-2",
            task_id="task-001",
            condition="AlphaApollo-Evolution+EVAS",
            round_index=1,
            parent_snapshot_sha256=SHA_A,
            retry_parent_attempt_id="attempt-1",
            entries=[
                {
                    "entry_id": "entry-a",
                    "source_kind": "candidate_summary",
                    "source_event_sha256": SHA_A,
                    "summary": {"status": "a"},
                }
            ],
        )


def test_memory_snapshot_round_index_rejects_bool_and_non_int() -> None:
    for round_index in (True, 1.0):
        with pytest.raises(TypeError, match="round_index must be a non-bool int"):
            freeze_memory_snapshot(
                snapshot_id="memory-round-1",
                episode_id="episode-1",
                attempt_id="attempt-1",
                task_id="task-001",
                condition="AlphaApollo-Evolution+EVAS",
                round_index=round_index,  # type: ignore[arg-type]
                parent_snapshot_sha256=None,
                entries=[],
            )


def test_candidate_lineage_is_schema_valid_hashable_and_freeze_terminal() -> None:
    lineage = CandidateLineage(
        candidate_id="candidate-b",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=1,
        candidate_tree_sha256=SHA_C,
        artifact_parent_candidate_id="candidate-a",
        influence_candidate_ids=("candidate-seed", "candidate-peer"),
        mutation_kind="refine",
        source_event_sha256=SHA_A,
        status="frozen",
    )

    document = lineage.to_document()

    jsonschema.validate(document, _load_schema(CANDIDATE_SCHEMA_PATH))
    assert len(candidate_lineage_sha256(document)) == 64

    with pytest.raises(ValueError):
        lineage.with_mutation(candidate_tree_sha256=SHA_B, source_event_sha256=SHA_C)


def test_candidate_lineage_schema_matches_runtime_local_constraints() -> None:
    schema = _load_schema(CANDIDATE_SCHEMA_PATH)
    valid_seed = CandidateLineage(
        candidate_id="candidate-a",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=0,
        candidate_tree_sha256=SHA_A,
        artifact_parent_candidate_id=None,
        influence_candidate_ids=(),
        mutation_kind="seed",
        source_event_sha256=SHA_B,
        status="active",
    ).to_document()

    for invalid_update in (
        {"round_index": True},
        {"round_index": 1},
        {"influence_candidate_ids": "candidate-b"},
        {
            "mutation_kind": "failed_mutation",
            "status": "failed",
            "artifact_parent_candidate_id": None,
            "failure_reason": "patch_did_not_apply",
        },
    ):
        invalid_document = valid_seed | invalid_update
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid_document, schema)


def test_candidate_lineage_v1_rejects_merge_and_invalid_local_state() -> None:
    with pytest.raises(ValueError, match="unsupported mutation_kind"):
        CandidateLineage(
            candidate_id="candidate-merge",
            episode_id="episode-1",
            attempt_id="attempt-1",
            task_id="task-001",
            condition="AlphaApollo-Evolution+EVAS",
            round_index=1,
            candidate_tree_sha256=SHA_C,
            artifact_parent_candidate_id="candidate-a",
            influence_candidate_ids=("candidate-b",),
            mutation_kind="merge",  # type: ignore[arg-type]
            source_event_sha256=SHA_A,
            status="active",
        )

    with pytest.raises(ValueError, match="seed candidates"):
        CandidateLineage(
            candidate_id="candidate-seed",
            episode_id="episode-1",
            attempt_id="attempt-1",
            task_id="task-001",
            condition="AlphaApollo-Evolution+EVAS",
            round_index=0,
            candidate_tree_sha256=SHA_A,
            artifact_parent_candidate_id="candidate-a",
            influence_candidate_ids=(),
            mutation_kind="seed",
            source_event_sha256=SHA_B,
            status="active",
        )

    with pytest.raises(ValueError, match="seed candidates must start at round_index=0"):
        CandidateLineage(
            candidate_id="candidate-late-seed",
            episode_id="episode-1",
            attempt_id="attempt-1",
            task_id="task-001",
            condition="AlphaApollo-Evolution+EVAS",
            round_index=1,
            candidate_tree_sha256=SHA_A,
            artifact_parent_candidate_id=None,
            influence_candidate_ids=(),
            mutation_kind="seed",
            source_event_sha256=SHA_B,
            status="active",
        )

    with pytest.raises(ValueError, match="failed_mutation"):
        CandidateLineage(
            candidate_id="candidate-failed",
            episode_id="episode-1",
            attempt_id="attempt-1",
            task_id="task-001",
            condition="AlphaApollo-Evolution+EVAS",
            round_index=1,
            candidate_tree_sha256=SHA_A,
            artifact_parent_candidate_id="candidate-a",
            influence_candidate_ids=(),
            mutation_kind="failed_mutation",
            source_event_sha256=SHA_B,
            status="active",
        )

    with pytest.raises(ValueError, match="refine requires"):
        CandidateLineage(
            candidate_id="candidate-refine-without-parent",
            episode_id="episode-1",
            attempt_id="attempt-1",
            task_id="task-001",
            condition="AlphaApollo-Evolution+EVAS",
            round_index=1,
            candidate_tree_sha256=SHA_A,
            artifact_parent_candidate_id=None,
            influence_candidate_ids=(),
            mutation_kind="refine",
            source_event_sha256=SHA_B,
            status="active",
        )

    with pytest.raises(ValueError, match="create candidates"):
        CandidateLineage(
            candidate_id="candidate-create-with-parent",
            episode_id="episode-1",
            attempt_id="attempt-1",
            task_id="task-001",
            condition="AlphaApollo-Evolution+EVAS",
            round_index=1,
            candidate_tree_sha256=SHA_A,
            artifact_parent_candidate_id="candidate-a",
            influence_candidate_ids=(),
            mutation_kind="create",
            source_event_sha256=SHA_B,
            status="active",
        )

    with pytest.raises(ValueError, match="failed_mutation requires an artifact parent"):
        CandidateLineage(
            candidate_id="candidate-failed",
            episode_id="episode-1",
            attempt_id="attempt-1",
            task_id="task-001",
            condition="AlphaApollo-Evolution+EVAS",
            round_index=1,
            candidate_tree_sha256=SHA_A,
            artifact_parent_candidate_id=None,
            influence_candidate_ids=(),
            mutation_kind="failed_mutation",
            source_event_sha256=SHA_B,
            status="failed",
            failure_reason="patch_did_not_apply",
        )


def test_candidate_lineage_rejects_multiple_artifact_parents_and_self_cycles() -> None:
    with pytest.raises(TypeError):
        CandidateLineage(
            candidate_id="candidate-b",
            episode_id="episode-1",
            attempt_id="attempt-1",
            task_id="task-001",
            condition="AlphaApollo-Evolution+EVAS",
            round_index=1,
            candidate_tree_sha256=SHA_C,
            artifact_parent_candidate_id=("candidate-a", "candidate-z"),  # type: ignore[arg-type]
            influence_candidate_ids=(),
            mutation_kind="refine",
            source_event_sha256=SHA_A,
            status="active",
        )

    with pytest.raises(ValueError):
        CandidateLineage(
            candidate_id="candidate-a",
            episode_id="episode-1",
            attempt_id="attempt-1",
            task_id="task-001",
            condition="AlphaApollo-Evolution+EVAS",
            round_index=1,
            candidate_tree_sha256=SHA_C,
            artifact_parent_candidate_id="candidate-a",
            influence_candidate_ids=("candidate-b",),
            mutation_kind="refine",
            source_event_sha256=SHA_A,
            status="active",
        )

    with pytest.raises(ValueError):
        CandidateLineage(
            candidate_id="candidate-a",
            episode_id="episode-1",
            attempt_id="attempt-1",
            task_id="task-001",
            condition="AlphaApollo-Evolution+EVAS",
            round_index=1,
            candidate_tree_sha256=SHA_C,
            artifact_parent_candidate_id=None,
            influence_candidate_ids=("candidate-a",),
            mutation_kind="refine",
            source_event_sha256=SHA_A,
            status="active",
        )


def test_candidate_lineage_rejects_invalid_round_and_influence_container() -> None:
    for round_index in (False, 0.5):
        with pytest.raises(TypeError, match="round_index must be a non-bool int"):
            CandidateLineage(
                candidate_id="candidate-a",
                episode_id="episode-1",
                attempt_id="attempt-1",
                task_id="task-001",
                condition="AlphaApollo-Evolution+EVAS",
                round_index=round_index,  # type: ignore[arg-type]
                candidate_tree_sha256=SHA_A,
                artifact_parent_candidate_id=None,
                influence_candidate_ids=(),
                mutation_kind="seed",
                source_event_sha256=SHA_B,
                status="active",
            )

    for influence_candidate_ids in ("candidate-b", 123):
        with pytest.raises(TypeError, match="influence_candidate_ids must be a sequence"):
            CandidateLineage(
                candidate_id="candidate-a",
                episode_id="episode-1",
                attempt_id="attempt-1",
                task_id="task-001",
                condition="AlphaApollo-Evolution+EVAS",
                round_index=0,
                candidate_tree_sha256=SHA_A,
                artifact_parent_candidate_id=None,
                influence_candidate_ids=influence_candidate_ids,  # type: ignore[arg-type]
                mutation_kind="seed",
                source_event_sha256=SHA_B,
                status="active",
            )


def test_failed_candidate_mutation_preserves_tree_hash_with_explicit_lineage() -> None:
    base = CandidateLineage(
        candidate_id="candidate-a",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=0,
        candidate_tree_sha256=SHA_A,
        artifact_parent_candidate_id=None,
        influence_candidate_ids=(),
        mutation_kind="create",
        source_event_sha256=SHA_B,
        status="active",
    )

    failed = base.with_failed_mutation(
        candidate_id="candidate-a-failed-edit",
        source_event_sha256=SHA_C,
        failure_reason="patch_did_not_apply",
    )

    assert failed.artifact_parent_candidate_id == "candidate-a"
    assert failed.candidate_tree_sha256 == base.candidate_tree_sha256
    assert failed.status == "failed"
    assert failed.failure_reason == "patch_did_not_apply"

    for terminal in ("rejected", "failed"):
        terminal_record = CandidateLineage(
            candidate_id=f"candidate-{terminal}",
            episode_id="episode-1",
            attempt_id="attempt-1",
            task_id="task-001",
            condition="AlphaApollo-Evolution+EVAS",
            round_index=1,
            candidate_tree_sha256=SHA_A,
            artifact_parent_candidate_id=(
                "candidate-a" if terminal == "failed" else None
            ),
            influence_candidate_ids=(),
            mutation_kind="failed_mutation" if terminal == "failed" else "create",
            source_event_sha256=SHA_B,
            status=terminal,
            failure_reason="failed edit" if terminal == "failed" else None,
        )
        with pytest.raises(ValueError, match="cannot be mutated"):
            terminal_record.with_mutation(
                candidate_tree_sha256=SHA_B,
                source_event_sha256=SHA_C,
            )


@pytest.mark.parametrize("mutation_kind", ["seed", "create", "failed_mutation"])
def test_with_mutation_only_allows_refine(mutation_kind: str) -> None:
    base = CandidateLineage(
        candidate_id="candidate-a",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=0,
        candidate_tree_sha256=SHA_A,
        artifact_parent_candidate_id=None,
        influence_candidate_ids=(),
        mutation_kind="seed",
        source_event_sha256=SHA_B,
        status="active",
    )

    with pytest.raises(ValueError, match="with_mutation supports only refine"):
        base.with_mutation(
            candidate_tree_sha256=SHA_B,
            source_event_sha256=SHA_C,
            mutation_kind=mutation_kind,  # type: ignore[arg-type]
        )


def test_candidate_lineage_graph_requires_parents_before_children() -> None:
    child = CandidateLineage(
        candidate_id="candidate-b",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=2,
        candidate_tree_sha256=SHA_B,
        artifact_parent_candidate_id="candidate-a",
        influence_candidate_ids=(),
        mutation_kind="refine",
        source_event_sha256=SHA_A,
        status="active",
    )
    parent = CandidateLineage(
        candidate_id="candidate-a",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=0,
        candidate_tree_sha256=SHA_A,
        artifact_parent_candidate_id=None,
        influence_candidate_ids=(),
        mutation_kind="seed",
        source_event_sha256=SHA_B,
        status="active",
    )

    with pytest.raises(ValueError, match="parent must appear before child"):
        validate_candidate_lineage_graph([child, parent])

    validate_candidate_lineage_graph([parent, child])


def test_candidate_lineage_graph_requires_same_scope_and_existing_references() -> None:
    parent = CandidateLineage(
        candidate_id="candidate-a",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=0,
        candidate_tree_sha256=SHA_A,
        artifact_parent_candidate_id=None,
        influence_candidate_ids=(),
        mutation_kind="seed",
        source_event_sha256=SHA_B,
        status="active",
    )
    child_wrong_task = CandidateLineage(
        candidate_id="candidate-b",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-002",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=1,
        candidate_tree_sha256=SHA_B,
        artifact_parent_candidate_id="candidate-a",
        influence_candidate_ids=(),
        mutation_kind="refine",
        source_event_sha256=SHA_A,
        status="active",
    )
    child_missing_influence = CandidateLineage(
        candidate_id="candidate-c",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=1,
        candidate_tree_sha256=SHA_C,
        artifact_parent_candidate_id="candidate-a",
        influence_candidate_ids=("missing-candidate",),
        mutation_kind="refine",
        source_event_sha256=SHA_A,
        status="active",
    )

    with pytest.raises(ValueError, match="same episode/attempt/task/condition"):
        validate_candidate_lineage_graph([parent, child_wrong_task])

    with pytest.raises(ValueError, match="influence must exist before child"):
        validate_candidate_lineage_graph([parent, child_missing_influence])


def test_candidate_lineage_graph_rejects_future_round_and_frozen_references() -> None:
    frozen_parent = CandidateLineage(
        candidate_id="candidate-a",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=1,
        candidate_tree_sha256=SHA_A,
        artifact_parent_candidate_id=None,
        influence_candidate_ids=(),
        mutation_kind="create",
        source_event_sha256=SHA_B,
        status="frozen",
    )
    child = CandidateLineage(
        candidate_id="candidate-b",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=2,
        candidate_tree_sha256=SHA_B,
        artifact_parent_candidate_id="candidate-a",
        influence_candidate_ids=(),
        mutation_kind="refine",
        source_event_sha256=SHA_A,
        status="active",
    )
    future_reference = CandidateLineage(
        candidate_id="candidate-c",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=1,
        candidate_tree_sha256=SHA_C,
        artifact_parent_candidate_id=None,
        influence_candidate_ids=(),
        mutation_kind="create",
        source_event_sha256=SHA_A,
        status="active",
    )
    future_round_influence = CandidateLineage(
        candidate_id="candidate-d",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=0,
        candidate_tree_sha256=SHA_C,
        artifact_parent_candidate_id=None,
        influence_candidate_ids=("candidate-c",),
        mutation_kind="create",
        source_event_sha256=SHA_A,
        status="active",
    )

    with pytest.raises(ValueError, match="frozen terminal"):
        validate_candidate_lineage_graph([frozen_parent, child])

    same_round_parent = CandidateLineage(
        candidate_id="candidate-e",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=1,
        candidate_tree_sha256=SHA_A,
        artifact_parent_candidate_id=None,
        influence_candidate_ids=(),
        mutation_kind="create",
        source_event_sha256=SHA_B,
        status="active",
    )
    same_round_child = CandidateLineage(
        candidate_id="candidate-f",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=1,
        candidate_tree_sha256=SHA_B,
        artifact_parent_candidate_id="candidate-e",
        influence_candidate_ids=(),
        mutation_kind="refine",
        source_event_sha256=SHA_A,
        status="active",
    )

    with pytest.raises(ValueError, match="reference round"):
        validate_candidate_lineage_graph([future_reference, future_round_influence])

    with pytest.raises(ValueError, match="reference round"):
        validate_candidate_lineage_graph([same_round_parent, same_round_child])


def test_graph_checks_failed_mutation_hash_and_influence_cycles() -> None:
    parent = CandidateLineage(
        candidate_id="candidate-a",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=0,
        candidate_tree_sha256=SHA_A,
        artifact_parent_candidate_id=None,
        influence_candidate_ids=(),
        mutation_kind="seed",
        source_event_sha256=SHA_B,
        status="active",
    )
    bad_failed = CandidateLineage(
        candidate_id="candidate-a-failed",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=1,
        candidate_tree_sha256=SHA_B,
        artifact_parent_candidate_id="candidate-a",
        influence_candidate_ids=(),
        mutation_kind="failed_mutation",
        source_event_sha256=SHA_C,
        status="failed",
        failure_reason="patch_did_not_apply",
    )

    with pytest.raises(ValueError, match="failed_mutation tree hash"):
        validate_candidate_lineage_graph([parent, bad_failed])

    rejected_parent = CandidateLineage(
        candidate_id="candidate-rejected",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=0,
        candidate_tree_sha256=SHA_A,
        artifact_parent_candidate_id=None,
        influence_candidate_ids=(),
        mutation_kind="create",
        source_event_sha256=SHA_B,
        status="rejected",
    )
    child_of_rejected = CandidateLineage(
        candidate_id="candidate-after-rejected",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=1,
        candidate_tree_sha256=SHA_B,
        artifact_parent_candidate_id="candidate-rejected",
        influence_candidate_ids=(),
        mutation_kind="refine",
        source_event_sha256=SHA_C,
        status="active",
    )
    with pytest.raises(ValueError, match="artifact parent status"):
        validate_candidate_lineage_graph([rejected_parent, child_of_rejected])

    influence_a = CandidateLineage(
        candidate_id="candidate-cycle-a",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=0,
        candidate_tree_sha256=SHA_A,
        artifact_parent_candidate_id=None,
        influence_candidate_ids=("candidate-cycle-b",),
        mutation_kind="create",
        source_event_sha256=SHA_B,
        status="active",
    )
    influence_b = CandidateLineage(
        candidate_id="candidate-cycle-b",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=0,
        candidate_tree_sha256=SHA_B,
        artifact_parent_candidate_id=None,
        influence_candidate_ids=("candidate-cycle-a",),
        mutation_kind="create",
        source_event_sha256=SHA_A,
        status="active",
    )

    with pytest.raises(ValueError, match="candidate lineage cycle"):
        validate_candidate_lineage_graph(
            [influence_a, influence_b],
            require_parent_before_child=False,
        )


def test_candidate_lineage_graph_rejects_cycles_across_records() -> None:
    candidate_a = CandidateLineage(
        candidate_id="candidate-a",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=0,
        candidate_tree_sha256=SHA_A,
        artifact_parent_candidate_id="candidate-b",
        influence_candidate_ids=(),
        mutation_kind="refine",
        source_event_sha256=SHA_B,
        status="active",
    )
    candidate_b = CandidateLineage(
        candidate_id="candidate-b",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=0,
        candidate_tree_sha256=SHA_B,
        artifact_parent_candidate_id="candidate-a",
        influence_candidate_ids=(),
        mutation_kind="refine",
        source_event_sha256=SHA_A,
        status="active",
    )

    with pytest.raises(ValueError, match="candidate lineage cycle"):
        validate_candidate_lineage_graph(
            [candidate_a, candidate_b],
            require_parent_before_child=False,
        )
