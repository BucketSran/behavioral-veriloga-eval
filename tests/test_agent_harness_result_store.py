from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from runners.agent_harness import result_store
from runners.agent_harness.result_store import (
    ImmutableEvidenceError,
    write_immutable_score_sidecar,
)
from runners.agent_harness.state import (
    EpisodeContext,
    FinalJudgment,
    FrozenSubmission,
)
from runners.agent_harness.trajectory import (
    JsonlTrajectoryRecorder,
    project_model_visible_events,
    read_trajectory,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64
SHA_F = "f" * 64


def _context() -> EpisodeContext:
    return EpisodeContext(
        episode_id="episode-001",
        attempt_id="attempt-001",
        task_id="v4-001",
        condition="Agentic+EVAS",
        max_steps=4,
    )


def _submission() -> FrozenSubmission:
    return FrozenSubmission(
        tree_sha256=SHA_A,
        artifacts=("model.va",),
    )


def _judgment() -> FinalJudgment:
    return FinalJudgment(
        status="passed",
        judge_engine="evas",
        score=1.0,
        submission_tree_sha256=SHA_A,
    )


def _profile() -> dict[str, Any]:
    return {
        "schema_version": "vaevas-final-test-profile-v1",
        "profile_id": "r53/evas-0.8.7-final-test",
        "benchmark_release": "benchmarkv4-r53",
        "benchmark_manifest_sha256": SHA_A,
        "judge": {"engine": "evas", "version": "0.8.7"},
        "judge_identity_sha256": SHA_B,
        "checker_identity_sha256": SHA_C,
        "runtime_identity_sha256": SHA_D,
        "campaign_config_sha256": SHA_E,
        "command_signature_sha256": SHA_F,
        "authority_phase": "post_submission_freeze_only",
        "visibility": "trusted_only",
        "model_observation_allowed": False,
        "memory_entry_allowed": False,
        "candidate_selection_allowed": False,
        "repair_allowed": False,
        "input_scope": "frozen_submission_tree",
        "submission_binding_required": True,
        "score_sidecar_required": True,
        "structured_result_contract": {
            "schema_id": "vaevas-structured-result-v1",
            "requires_structured_verdict": True,
        },
        "score_sidecar_contract": {
            "schema_id": "vaevas-score-sidecar-v1",
            "immutable": True,
            "binds_submission_tree": True,
            "score_authority": "development_only",
        },
        "spectre_policy": {
            "required": False,
            "trigger": "conditional_evas_or_external_protocol_change",
            "spectre_judge_identity_sha256": None,
            "spectre_command_signature_sha256": None,
            "spectre_report_schema_id": None,
        },
    }


def _sidecar(**updates: Any) -> dict[str, Any]:
    sidecar: dict[str, Any] = {
        "schema_version": "vaevas-score-sidecar-v1",
        "benchmark_release": "benchmarkv4-r53",
        "benchmark_manifest_sha256": SHA_A,
        "score_authority": "development_only",
        "immutable": True,
        "binds_submission_tree": True,
        "submission_tree_sha256": SHA_A,
        "judge": {
            "engine": "evas",
            "version": "0.8.7",
            "identity_sha256": SHA_B,
        },
        "checker_identity_sha256": SHA_C,
        "runtime_identity_sha256": SHA_D,
        "campaign_config_sha256": SHA_E,
        "command_signature_sha256": SHA_F,
        "structured_result": {"status": "passed", "score": 1.0},
        "model_observation_allowed": False,
        "memory_entry_allowed": False,
    }
    sidecar.update(updates)
    return sidecar


def _write(output_dir: Path, *, sidecar: dict[str, Any] | None = None):
    return write_immutable_score_sidecar(
        output_dir=output_dir,
        context=_context(),
        submission=_submission(),
        judgment=_judgment(),
        final_test_profile=_profile(),
        score_sidecar=sidecar or _sidecar(),
    )


def test_writer_persists_canonical_content_addressed_sidecar(tmp_path) -> None:
    sidecar = _sidecar()

    record = _write(tmp_path, sidecar=sidecar)

    assert record.path == tmp_path / "score-sidecars" / f"{record.sha256}.json"
    expected_payload = json.dumps(
        sidecar,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert record.path.read_text(encoding="utf-8") == expected_payload
    assert hashlib.sha256(record.path.read_bytes()).hexdigest() == record.sha256
    assert record.submission_tree_sha256 == SHA_A
    assert len(record.final_profile_sha256) == 64
    assert len(record.final_profile_input_identity_sha256) == 64
    assert record.path.stat().st_mode & 0o222 == 0


def test_writer_rejects_existing_sidecar_even_when_content_matches(tmp_path) -> None:
    first = _write(tmp_path)
    original = first.path.read_bytes()

    with pytest.raises(ImmutableEvidenceError, match="already exists"):
        _write(tmp_path)

    assert first.path.read_bytes() == original
    assert not list(first.path.parent.glob(".*.tmp-*"))


def test_writer_leaves_no_file_after_authority_validation_failure(tmp_path) -> None:
    bad_sidecar = _sidecar(checker_identity_sha256=SHA_D)

    with pytest.raises(ValueError, match="checker_identity_sha256"):
        _write(tmp_path, sidecar=bad_sidecar)

    assert not list(tmp_path.rglob("*.json"))


def test_writer_cleans_temporary_file_when_atomic_publish_fails(
    tmp_path,
    monkeypatch,
) -> None:
    def fail_publish(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise OSError("simulated publish failure")

    monkeypatch.setattr(result_store, "_publish_exclusive", fail_publish)

    with pytest.raises(ImmutableEvidenceError, match="publish"):
        _write(tmp_path)

    sidecar_dir = tmp_path / "score-sidecars"
    assert not list(sidecar_dir.glob("*.json"))
    assert not list(sidecar_dir.glob(".*.tmp-*"))


@pytest.mark.parametrize(
    "visibility_update",
    [
        {"model_observation_allowed": True},
        {"memory_entry_allowed": True},
    ],
)
def test_writer_rejects_model_or_memory_visible_sidecar(
    tmp_path,
    visibility_update,
) -> None:
    with pytest.raises(ValueError):
        _write(tmp_path, sidecar=_sidecar(**visibility_update))

    assert not list(tmp_path.rglob("*.json"))


def test_writer_rejects_symlinked_evidence_directory(tmp_path) -> None:
    external = tmp_path / "external"
    external.mkdir()
    (tmp_path / "score-sidecars").symlink_to(external, target_is_directory=True)

    with pytest.raises(ImmutableEvidenceError, match="symlink"):
        _write(tmp_path)

    assert not list(external.iterdir())


def test_writer_does_not_modify_model_visible_trajectory(tmp_path) -> None:
    trajectory_path = tmp_path / "trajectory.jsonl"
    recorder = JsonlTrajectoryRecorder(trajectory_path)
    recorder.append(
        context=_context(),
        actor="policy",
        event_type="action_proposed",
        visibility="model",
        payload={"tool_name": "submit"},
    )
    before = read_trajectory(trajectory_path)

    record = _write(tmp_path / "trusted-results")

    after = read_trajectory(trajectory_path)
    assert after == before
    projected = project_model_visible_events(after)
    serialized = json.dumps(projected, sort_keys=True)
    for forbidden in (
        "score_sidecar",
        record.sha256,
        record.final_profile_input_identity_sha256,
        "structured_result",
    ):
        assert forbidden not in serialized


def test_writer_detaches_mutable_inputs_before_persistence(tmp_path) -> None:
    sidecar = _sidecar()
    original = deepcopy(sidecar)

    record = _write(tmp_path, sidecar=sidecar)
    sidecar["structured_result"]["status"] = "tampered"

    assert json.loads(record.path.read_text(encoding="utf-8")) == original
