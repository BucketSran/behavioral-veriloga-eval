from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
sys.path.insert(0, str(CALIBRATION))

import run_native_evolution as evolution  # noqa: E402
from runners.agent_harness.evolution_runtime import EvolutionBranchRequest  # noqa: E402


MANIFEST_SHA = "a" * 64


def _runtime_with_submission(tmp_path: Path, content: str = "module chosen; endmodule") -> Path:
    runtime = tmp_path / "runtime"
    submission = runtime / "public/submission"
    submission.mkdir(parents=True)
    (submission / "model.va").write_text(content, encoding="utf-8")
    return runtime


def _store_candidate(
    *,
    runtime: Path,
    destination: Path,
    tree_sha256: str,
) -> None:
    evolution._store_candidate_snapshot(
        runtime=runtime,
        destination=destination,
        artifacts=("model.va",),
        tree_sha256=tree_sha256,
        terminal_reason="submitted",
    )


@pytest.mark.parametrize("frozen", [False, True])
def test_prior_candidate_payload_uses_sealed_candidate_identity_not_hash_glob(tmp_path: Path, frozen):
    runtime = _runtime_with_submission(tmp_path)
    tree_sha = evolution._candidate_tree_sha256(runtime)
    branches = tmp_path / "evolution/branches"
    _store_candidate(
        runtime=runtime,
        destination=branches / "round-0000/branch-a/candidate-store" / tree_sha,
        tree_sha256=tree_sha,
    )
    _store_candidate(
        runtime=runtime,
        destination=branches / "round-0000/branch-b/candidate-store" / tree_sha,
        tree_sha256=tree_sha,
    )
    event_sha = "c" * 64
    profile_sha = "d" * 64
    receipt = {
        "schema_version": "vaevas-native-evolution-public-validation-receipt-v1",
        "manifest_sha256": MANIFEST_SHA,
        "branch_id": "branch-b",
        "round_index": 0,
        "candidate_tree_sha256": tree_sha,
        "candidate_store_sha256": "e" * 64,
        "context": {"attempt_id": "branch-b-round-0000", "task_id": "task-1"},
        "profile_input_identity_sha256": "f" * 64,
        "result": {
            "status": "failed",
            "sim_success": 0.0,
            "event_sha256": event_sha,
        },
        "observation": {
            "schema_version": "vaevas-observation-v1",
            "observation_id": "branch-b/public-validation-1",
            "tool_name": "run_evas",
            "status": "failed",
            "payload": {
                "output": "compile error: missing branch",
                "profile_sha256": profile_sha,
            },
            "candidate_tree_sha256": tree_sha,
            "validation_profile_sha256": profile_sha,
            "truncated": False,
            "budget_delta": {"public_validation_calls": 1},
        },
    }
    event_sha = evolution._canonical_sha256(receipt["observation"])
    receipt["result"]["event_sha256"] = event_sha
    receipt["candidate_store_sha256"] = evolution._candidate_store_manifest_sha(
        branches / "round-0000/branch-b/candidate-store" / tree_sha)
    (branches / "round-0000/branch-b/public-validation.json").write_text(
        json.dumps(receipt, sort_keys=True),
        encoding="utf-8",
    )
    request = EvolutionBranchRequest(
        manifest_sha256=MANIFEST_SHA,
        branch_id="branch-c",
        round_index=1,
        allowance={"model_calls": 1, "tool_calls": 1, "public_validation_calls": 1},
        deadline_monotonic=None,
        output_path=branches / "round-0001/branch-c",
        public_snapshot={
            "memory_snapshot": {
                "entries": [
                        {
                            "candidate_id": f"branch-b-round-0000-{tree_sha[:12]}",
                            "candidate_tree_sha256": tree_sha,
                            "source_event_sha256": event_sha,
                            "summary": {"metrics": {"sim_success": 1.0}},
                        }
                    ]
            }
        },
    )

    if frozen:
        from dataclasses import replace
        from runners.agent_harness.evolution_runtime import _freeze_json_object
        request = replace(request, public_snapshot=_freeze_json_object(request.public_snapshot, field_name="test"))

    payloads = evolution._prior_candidate_payloads(request)

    assert payloads == [
        {
            "candidate_id": f"branch-b-round-0000-{tree_sha[:12]}",
            "candidate_tree_sha256": tree_sha,
            "artifacts": {"model.va": "module chosen; endmodule"},
            "public_validation": {
                "summary": {"metrics": {"sim_success": 1.0}},
                "result": {
                    "status": "failed",
                    "sim_success": 0.0,
                    "event_sha256": event_sha,
                },
                "observation": receipt["observation"],
            },
        }
    ]
    receipt["observation"]["payload"]["output"] = "tampered public feedback"
    (branches / "round-0000/branch-b/public-validation.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="observation hash"):
        evolution._prior_candidate_payloads(request)


def test_candidate_snapshot_rejects_artifact_path_escape(tmp_path: Path):
    runtime = _runtime_with_submission(tmp_path)
    (runtime / "public/secret.va").write_text("leak", encoding="utf-8")

    with pytest.raises(ValueError, match="candidate artifact path"):
        evolution._store_candidate_snapshot(
            runtime=runtime,
            destination=tmp_path / "store",
            artifacts=("../secret.va",),
            tree_sha256="b" * 64,
            terminal_reason="submitted",
        )


def test_candidate_artifact_reader_rejects_manifest_bytes_drift(tmp_path: Path):
    runtime = _runtime_with_submission(tmp_path, content="module original; endmodule")
    tree_sha = evolution._candidate_tree_sha256(runtime)
    store = tmp_path / "store" / tree_sha
    _store_candidate(runtime=runtime, destination=store, tree_sha256=tree_sha)
    artifact = store / "submission/model.va"
    artifact.chmod(0o644)
    artifact.write_text("module tampered; endmodule", encoding="utf-8")

    with pytest.raises(ValueError, match="candidate store hash mismatch"):
        evolution._read_candidate_artifacts(store)


def test_replace_submission_rejects_symlink_and_verifies_copied_tree(tmp_path: Path):
    runtime = _runtime_with_submission(tmp_path, content="module original; endmodule")
    tree_sha = evolution._candidate_tree_sha256(runtime)
    store = tmp_path / "store" / tree_sha
    _store_candidate(runtime=runtime, destination=store, tree_sha256=tree_sha)
    artifact = store / "submission/model.va"
    store.chmod(0o755)
    (store / "submission").chmod(0o755)
    artifact.chmod(0o644)
    artifact.unlink()
    artifact.symlink_to(tmp_path / "outside.va")

    with pytest.raises(ValueError, match="stored candidate artifact"):
        evolution._replace_submission_from_store(
            source=store / "submission",
            runtime=tmp_path / "final-runtime",
            artifacts=tuple(json.loads((store / "manifest.json").read_text())["artifacts"]),
        )
