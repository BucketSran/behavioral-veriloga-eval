from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_v4_r53_clean_room_smoke.py"


def load_smoke_module():
    spec = importlib.util.spec_from_file_location("run_v4_r53_clean_room_smoke", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fake_evas_087(tmp_path: Path) -> Path:
    executable = tmp_path / "evas-0.8.7"
    executable.write_text(
        """#!/bin/sh
if [ "$1" = "--version" ]; then
  echo 'evas-sim 0.8.7 (clean-room test double)'
  exit 0
fi
out=''
while [ "$#" -gt 0 ]; do
  if [ "$1" = "-o" ]; then
    shift
    out="$1"
  fi
  shift
done
if [ -n "$out" ]; then
  mkdir -p "$out"
fi
exit 0
""",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable


def structured_compile_failure(smoke, result_path: Path) -> dict:
    result = smoke.read_json(result_path)
    submission = result["experiment_result"]["final_submission"]
    return {
        "cell_id": result["cell"]["cell_id"],
        "family_id": result["cell"]["family_id"],
        "task_id": result["cell"]["task_id"],
        "form": result["cell"]["form"],
        "mode": result["cell"]["mode"],
        "experimental_arm": result["cell"]["experimental_arm"],
        "submission_status": result["status"],
        "judge_status": "compile_failure",
        "outcome": "compile_failure",
        "failure_taxonomy": {
            "schema_version": "vabench-failure-taxonomy-v1",
            "primary_class": "compile",
            "secondary_classes": [],
            "stage": "compile",
            "responsibility": "candidate",
            "retryable": False,
            "case_ids": [],
            "property_ids": [],
            "mutation_ids": [],
        },
        "trusted_replay": {
            "status": "compile_failure",
            "submission_tree_sha256": submission["tree_sha256"],
            "evas_identity": {
                "available": True,
                "version_output": "evas-sim 0.8.7 (clean-room test double)",
                "sha256": "0" * 64,
            },
            "input_signature_sha256": "1" * 64,
            "diagnostics": ["intentional_incomplete_smoke_candidate"],
        },
    }


def test_r53_smoke_uses_actual_runner_without_reading_hidden_solution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    smoke = load_smoke_module()
    output_root = tmp_path / "r53-smoke"
    fake_evas = fake_evas_087(tmp_path)

    def fake_evaluate_cell(result_path, *_args, **_kwargs):
        return structured_compile_failure(smoke, Path(result_path))

    monkeypatch.setattr(smoke.score_campaign, "evaluate_cell", fake_evaluate_cell)
    args = smoke.parse_args(
        [
            "--task-id",
            "v4-001",
            "--output-root",
            str(output_root),
            "--evas-command",
            str(fake_evas),
            "--sandbox",
            "none",
            "--allow-insecure-test-sandbox",
        ]
    )

    payload = smoke.run_smoke(args)

    assert payload["status"] == "FAIL"
    assert payload["claim_gate"]["blocking_reasons"] == [
        "clean_room_requires_docker"
    ]
    assert payload["claim_gate"]["model_score_claim_allowed"] is False
    assert payload["claim_gate"]["spectre_required"] is False
    assert payload["benchmark_release"]["release_revision"] == "r53"
    assert payload["benchmark_release"]["evas_version"] == "0.8.7"

    by_arm = {cell["experimental_arm"]: cell for cell in payload["cells"]}
    assert sorted(by_arm) == ["Agent-No-EVAS", "Agentic", "OneShot"]
    assert by_arm["Agent-No-EVAS"]["evas_usage"]["calls_executed"] == 0
    assert by_arm["Agentic"]["evas_usage"]["calls_executed"] == 1

    for cell in payload["cells"]:
        assert cell["candidate_fixture"] == {
            "kind": "intentionally_incomplete_public_smoke_candidate",
            "source_boundary": "public_contract_only",
        }
        assert cell["trajectory"]["chain_verified"] is True
        assert cell["trajectory"]["event_count"] >= 1
        assert len(cell["trajectory"]["chain_head_sha256"]) == 64
        assert cell["final_submission"]["status"] == "available"
        assert cell["final_submission"]["immutable"] is True
        assert cell["score_sidecar"]["judge_engine"] == "evas"
        assert cell["score_sidecar"]["score_authority"] == "development_only"
        assert cell["score_sidecar"]["judge_status"] == "compile_failure"
        assert cell["score_sidecar"]["submission_tree_sha256"] == cell[
            "final_submission"
        ]["tree_sha256"]
        sidecar = Path(cell["score_sidecar"]["path"])
        assert sidecar.is_file()
        assert smoke.sha256_file(sidecar) == cell["score_sidecar"]["sha256"]

        result = smoke.read_json(
            output_root
            / "run"
            / cell["cell_id"]
            / "evidence"
            / "campaign_result.json"
        )
        serialized = json.dumps(result, sort_keys=True)
        assert "evaluator_solution_fixture" not in serialized
        assert '"fixture_source"' not in serialized
        assert result["candidate_fixture"]["source_boundary"] == (
            "public_contract_only"
        )


def test_r53_smoke_rejects_wrong_evas_version(tmp_path: Path) -> None:
    smoke = load_smoke_module()
    executable = tmp_path / "evas-0.8.3"
    executable.write_text(
        "#!/bin/sh\necho 'evas-sim 0.8.3'\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)

    with pytest.raises(RuntimeError, match="requires evas-sim 0.8.7"):
        smoke.resolve_evas_command(str(executable))


def test_submission_freeze_is_idempotent_and_rejects_source_drift(
    tmp_path: Path,
) -> None:
    smoke = load_smoke_module()
    runtime = tmp_path / "runtime"
    submission = runtime / "public" / "submission"
    submission.mkdir(parents=True)
    (submission / "candidate.va").write_text("first\n", encoding="utf-8")
    gate = {
        "passed": True,
        "expected_artifacts": ["candidate.va"],
        "diagnostics": [],
    }

    first = smoke.result_protocol.snapshot_submission(runtime, gate)
    second = smoke.result_protocol.snapshot_submission(runtime, gate)

    assert second == first
    assert first["immutable"] is True
    (submission / "candidate.va").write_text("changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="frozen submission does not match"):
        smoke.result_protocol.snapshot_submission(runtime, gate)


def test_trusted_replay_fails_closed_without_structured_result() -> None:
    smoke = load_smoke_module()
    replay = smoke.result_protocol.trusted_replay(
        {"execution_status": "completed", "returncode": 0},
        None,
        {"tree_sha256": "evaluator"},
        {"available": True, "version_output": "evas-sim 0.8.7"},
        "submission",
    )

    assert replay["status"] == "infrastructure_failure"
    assert replay["diagnostics"] == ["missing_structured_trusted_replay_result"]
