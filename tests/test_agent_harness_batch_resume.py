"""Durable batch records: reuse is independent of candidate success."""

import json
import subprocess
import sys

import pytest

from runners.agent_harness.batch_resume import BatchRun


def test_completed_zero_score_is_reused_without_rewriting_evidence(tmp_path):
    root = tmp_path / "batch"
    manifest = {"source": "a" * 64, "config": {"max_attempts": 1}}
    with BatchRun(root, manifest, ["cell-a", "cell-b"], resume=False) as batch:
        runtime = root / "cell-a"
        runtime.mkdir()
        evidence = runtime / "result.json"
        evidence.write_text('{"score":0}')
        row = {"cell_id": "cell-a", "status": "completed", "score": 0}
        batch.record("cell-a", row, runtime)
        before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
    with BatchRun(root, manifest, ["cell-a", "cell-b"], resume=True) as batch:
        assert batch.read("cell-a", runtime) == row
        assert batch.read("cell-b", root / "cell-b") is None
    assert all(path.read_bytes() == value for path, value in before.items())


@pytest.mark.parametrize("mutation", ["source", "roster", "config"])
def test_resume_rejects_frozen_identity_drift(tmp_path, mutation):
    manifest = {"source": "original", "config": {"cap": 2}}
    with BatchRun(tmp_path / "batch", manifest, ["a"], resume=False):
        pass
    changed = json.loads(json.dumps(manifest))
    ids = ["a"]
    if mutation == "roster":
        ids = ["b"]
    elif mutation == "config":
        changed["config"]["cap"] = 3
    else:
        changed["source"] = "drift"
    with pytest.raises(ValueError, match="differs"):
        with BatchRun(tmp_path / "batch", changed, ids, resume=True):
            pytest.fail("drift must reject before dispatch")


def test_concurrent_process_cannot_acquire_batch(tmp_path):
    root = tmp_path / "batch"
    code = """
from pathlib import Path
import sys
from runners.agent_harness.batch_resume import BatchRun
try:
    with BatchRun(Path(sys.argv[1]), {}, ['a'], resume=True):
        raise AssertionError('second writer admitted')
except BlockingIOError:
    pass
"""
    with BatchRun(root, {}, ["a"], resume=False):
        result = subprocess.run([sys.executable, "-c", code, str(root)],
                                capture_output=True, text=True, timeout=20)
        assert result.returncode == 0, result.stderr
    # OS releases the lease; stale file does not prevent recovery.
    with BatchRun(root, {}, ["a"], resume=True):
        pass


@pytest.mark.parametrize("mutation", ["files", "row", "symlink", "extra", "empty_reservation"])
def test_changed_completed_evidence_is_not_reused(tmp_path, mutation):
    root = tmp_path / "batch"
    with BatchRun(root, {}, ["a"], resume=False) as batch:
        runtime = root / "a"
        runtime.mkdir()
        evidence = runtime / "score.json"
        evidence.write_text('{"score":0}')
        batch.record("a", {"cell_id": "a", "score": 0}, runtime)
    if mutation == "row":
        path = root / ".batch/cell-a.json"
        value = json.loads(path.read_text())
        value["row"]["score"] = 1
        path.chmod(0o600)
        path.write_text(json.dumps(value))
    elif mutation == "symlink":
        evidence.unlink()
        evidence.symlink_to(tmp_path / "missing")
    elif mutation == "extra":
        (runtime / "unrecorded.json").write_text("{}")
    elif mutation == "empty_reservation":
        (runtime / "bound-final-test").mkdir()
    else:
        evidence.write_text('{"score":1}')
    with BatchRun(root, {}, ["a"], resume=True) as batch:
        with pytest.raises(ValueError):
            batch.read("a", runtime)


def test_indexes_are_append_only_and_keep_not_started_cells(tmp_path):
    with BatchRun(tmp_path / "batch", {}, ["a", "b"], resume=False) as batch:
        rows = [{"cell_id": "a", "status": "completed"},
                {"cell_id": "b", "status": "not_started"}]
        first = batch.snapshot(rows)
        before = first.read_bytes()
        rows[1]["status"] = "blocked"
        assert batch.snapshot(rows) != first
        assert first.read_bytes() == before
        with pytest.raises(ValueError, match="denominator"):
            batch.snapshot(rows[:1])


def test_historical_outputs_are_not_silently_adopted(tmp_path):
    root = tmp_path / "old"
    root.mkdir()
    evidence = root / "existing.json"
    evidence.write_text("{}")
    for resume in (True, False):
        with pytest.raises(ValueError):
            with BatchRun(root, {}, ["a"], resume=resume):
                pytest.fail("old output admitted")
    assert evidence.read_text() == "{}"


def test_confined_runtime_alias_is_recorded_without_following_cycles(tmp_path):
    with BatchRun(tmp_path / "batch", {}, ["a"], resume=False) as batch:
        runtime = batch.root / "a"
        public = runtime / "public"
        public.mkdir(parents=True)
        (public / "public").symlink_to(".")
        (public / "input").write_text("fixture")
        row = {"cell_id": "a", "status": "completed"}
        batch.record("a", row, runtime)
        assert batch.read("a", runtime) == row


def test_unrostered_runtime_is_not_silently_ignored_on_resume(tmp_path):
    root = tmp_path / "batch"
    with BatchRun(root, {}, ["a"], resume=False):
        pass
    (root / "unknown-attempt").mkdir()
    with pytest.raises(ValueError, match="unrostered"):
        with BatchRun(root, {}, ["a"], resume=True):
            pytest.fail("unknown activity cannot authorize more work")


def test_runtime_binding_cannot_escape_via_parent_segments(tmp_path):
    with BatchRun(tmp_path / "batch", {}, ["a"], resume=False) as batch:
        outside = tmp_path / "outside"
        outside.mkdir()
        with pytest.raises(ValueError):
            batch.record("a", {}, batch.root / ".." / "outside")
