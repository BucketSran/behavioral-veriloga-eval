from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from runners.agent_harness.evolution_state import (
    CandidateLineage,
    MemorySnapshot,
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
        mutation_kind="seed",
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


def test_candidate_lineage_graph_requires_parents_before_children() -> None:
    child = CandidateLineage(
        candidate_id="candidate-b",
        episode_id="episode-1",
        attempt_id="attempt-1",
        task_id="task-001",
        condition="AlphaApollo-Evolution+EVAS",
        round_index=1,
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
