"""Native evidence joins and mixed-backend campaign connectivity, not parity."""

import hashlib
import json
from pathlib import Path
import shutil
import sys
import os

import pytest

from test_agent_harness_native_episode import native_case as native_case  # noqa: F401
from test_agent_harness_production_public_validation import public_case as public_case  # noqa: F401
from test_agent_harness_native_launcher import Provider

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"))
import score_campaign as scorer  # noqa: E402


def test_summary_rejects_missing_scheduled_cell():
    from scripts import run_v4_r53_clean_room_smoke as smoke

    cells = smoke.three_arm_cells(smoke.DEFAULT_RELEASE, "v4-001", "fixture-model")
    rows = [
        {**cell, "submission_status": "submitted", "judge_status": "passed"}
        for cell in cells[:-1]
    ]
    with pytest.raises(ValueError, match="scheduled"):
        scorer.summarize(rows, "final_trusted_replay", scheduled_cells=cells)


@pytest.fixture
def launched(native_case):  # noqa: F811
    from run_native_mini_swe import run_prepared_native_mini_swe

    arguments, _, _ = native_case
    source = arguments["runtime"]
    runtime = source.with_name("fresh-launcher")
    shutil.copytree(source / "public/task", runtime / "public/task")
    shutil.copytree(source / "evaluator", runtime / "evaluator")
    (runtime / "public/submission").mkdir()
    (runtime / "agent_prompt.txt").write_text("Implement the public task.")
    cell = {
        "cell_id": "cell-001", "task_id": "v4-001", "family_id": "001",
        "mode": "G2", "form": "dut", "experimental_arm": "Agentic",
        "executable_feedback": True, "per_turn_max_tokens": 128,
    }

    def launch(provider=None):
        provider = provider or Provider([
            "printf 'module model; endmodule\\n' > public/submission/model.va",
            "vabench-submit",
        ])
        run = run_prepared_native_mini_swe(
            runtime=runtime, cell=cell, client=provider, attempt_id="attempt-001",
            evas_command=arguments["evas_command"],
            final_judge_command=arguments["command"], judge_timeout_s=10,
            allow_insecure_test_sandbox=True, campaign_file_sha256="c" * 64,
        )
        return runtime, cell, provider, run

    return launch


def file_hashes(root):
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file()
    }


def test_native_row_reads_verified_evidence_without_execution_or_mutation(launched):
    runtime, cell, provider, run = launched()
    before = file_hashes(runtime)
    calls = len(provider.requests)
    row = scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)
    assert row["judge_status"] == "behavior_failure"
    assert row["score"] == 0
    assert row["terminal_reason"] == "submitted"
    assert row["failure_class"] == "behavior_unspecified"
    assert row["backend"] == "native-mini-swe"
    assert "score_sidecar_receipt" not in row["trusted_replay"]
    assert row["trusted_replay"]["derived_score_sidecar_reference"]["sha256"]
    assert row["attempt_id"] == "attempt-001"
    assert row["metering"]["provider"]["requests"] == 2
    assert row["output_tokens"] == 10
    assert row["telemetry"]["tool_calls_total"] == 2
    assert row["native_evidence"]["artifact_sha256"] == json.loads(run.artifact_path.read_text())["artifact_sha256"]
    assert row["native_evidence"]["artifact_path"] == str(run.artifact_path.relative_to(runtime))
    assert row["native_evidence"]["artifact_file_sha256"] == before[
        str(run.artifact_path.relative_to(runtime))
    ]
    assert scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64) == row
    assert len(provider.requests) == calls
    assert file_hashes(runtime) == before
    assert "FINAL_JUDGE_SENTINEL" not in json.dumps(row)
    with pytest.raises(ValueError, match="authority"):
        scorer.summarize([row], "final_spectre", scheduled_cells=[cell])


def test_native_unknown_tokens_stay_unknown_through_report(launched):
    class MissingUsageProvider(Provider):
        def complete(self, *args, **kwargs):
            response = super().complete(*args, **kwargs)
            response.pop("usage")
            return response

    runtime, cell, _, _ = launched(MissingUsageProvider([
        "printf 'module model; endmodule\\n' > public/submission/model.va",
        "vabench-submit",
    ]))
    row = scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)
    assert row["output_tokens"] is None
    assert row["metering"]["provider"]["usage_status"] == "partial"
    report = scorer.summarize([row], "final_trusted_replay", scheduled_cells=[cell])
    summary = report["telemetry_by_arm"]["Agentic"]
    assert summary["output_tokens_total"] is None
    assert summary["output_tokens_median"] is None
    assert summary["output_tokens_reported_subtotal"] == 0
    assert summary["output_tokens_unknown_cells"] == 1


@pytest.mark.parametrize("tamper", ["replace", "remove_reference"])
def test_native_reviewer_export_is_required_and_recomputed(launched, tamper):
    runtime, cell, _, _ = launched()
    directory = runtime / "evidence/native-launcher"
    result_path = directory / "result.json"
    result = json.loads(result_path.read_text())
    if tamper == "replace":
        export_path = directory / "reviewer-export.json"
        export = json.loads(export_path.read_text())
        export["usage"]["provider"]["requests"] = 999
        export_path.chmod(0o600)
        export_path.write_text(json.dumps(export))
        result["reviewer_export_sha256"] = hashlib.sha256(export_path.read_bytes()).hexdigest()
    else:
        result.pop("reviewer_export_sha256")
    result_path.chmod(0o600)
    result_path.write_text(json.dumps(result))
    with pytest.raises(ValueError, match="reviewer"):
        scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)


@pytest.mark.parametrize("kind", ["protocol", "provider"])
def test_native_row_preserves_unscored_terminal_failures(launched, kind):
    provider = Provider([])

    def respond(*args, **kwargs):
        if kind == "provider":
            raise TimeoutError("fixture timeout")
        return {"choices": [{"message": {"role": "assistant", "content": "no action"}}]}

    provider.complete = respond
    runtime, cell, _, run = launched(provider)
    assert run.artifact_path is None
    row = scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)
    assert row["score"] is None
    assert "trusted_replay" not in row
    assert row["judge_status"] == ("infrastructure_failure" if kind == "provider" else "protocol_failure")
    assert row["failure_class"] == ("infrastructure" if kind == "provider" else "invalid")
    assert not (runtime / "evidence/bound-final-test").exists()


@pytest.mark.parametrize("drift", ["missing", "duplicate", "extra", "identity"])
def test_summary_rejects_denominator_drift(drift):
    from scripts import run_v4_r53_clean_room_smoke as smoke

    cells = smoke.three_arm_cells(smoke.DEFAULT_RELEASE, "v4-001", "fixture-model")
    rows = [
        {**cell, "submission_status": "submitted", "judge_status": "passed"}
        for cell in cells
    ]
    if drift == "missing":
        rows.pop()
    elif drift == "duplicate":
        rows[-1] = rows[0]
    elif drift == "extra":
        rows.append({**rows[0], "cell_id": "extra"})
    else:
        rows[0]["experimental_arm"] = "wrong"
    with pytest.raises(ValueError, match="scheduled"):
        scorer.summarize(rows, "final_trusted_replay", scheduled_cells=cells)


@pytest.mark.parametrize("target", [
    "campaign", "cell", "trajectory", "private", "artifact", "submission", "sidecar", "outcome",
])
def test_native_row_rejects_broken_evidence_joins(launched, target):
    runtime, cell, _, run = launched()
    expected = "c" * 64
    if target == "campaign":
        expected = "d" * 64
    elif target == "cell":
        cell = {**cell, "task_id": "wrong-task"}
    else:
        path = {
            "trajectory": runtime / "evidence/native-episode/trajectory.jsonl",
            "private": runtime / "evidence/native-launcher/private-events.jsonl",
            "artifact": run.artifact_path,
            "submission": runtime / "evidence/final_submission/model.va",
            "sidecar": runtime / run.score_sidecar_receipt["path"],
            "outcome": runtime / "evidence/native-episode/outcome.json",
        }[target]
        path.chmod(0o600)
        if target == "outcome":
            outcome = json.loads(path.read_text())
            outcome["primary_outcome"] = "passed"
            path.write_text(json.dumps(outcome))
        else:
            path.write_text(path.read_text() + "\nCORRUPTION")
    with pytest.raises(ValueError):
        scorer.read_native_cell(runtime, cell, campaign_file_sha256=expected)


def test_mixed_smoke_rejects_unbound_final_before_runtime_creation(tmp_path):
    from scripts import run_v4_r53_clean_room_smoke as smoke

    root = tmp_path / "smoke"
    args = smoke.parse_args([
        "--output-root", str(root), "--evas-command", "/unused/evas",
        "--agentic-backend", "native-mini-swe",
    ])
    with pytest.raises(ValueError, match="bound-final-authority"):
        smoke.run_smoke(args)
    assert not root.exists()


def test_r53_docker_mixed_native_campaign(tmp_path):
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in real Docker mixed native campaign")
    from scripts import run_v4_r53_clean_room_smoke as smoke

    args = smoke.parse_args([
        "--output-root", str(tmp_path / "smoke"),
        "--evas-command", str(ROOT / ".venv/bin/evas"),
        "--bound-final-authority", "--agentic-backend", "native-mini-swe",
    ])
    report = smoke.run_smoke(args)
    assert report["status"] == "PASS", report
    assert report["comparison_profile"] == "mixed-backend-connectivity-v1"
    assert report["claim_gate"]["model_score_claim_allowed"] is False
    assert report["backend_by_arm"] == {
        "OneShot": "legacy-direct", "Agent-No-EVAS": "legacy-mini-swe",
        "Agentic": "native-mini-swe",
    }
    rows = smoke.read_json(Path(report["score_report"]["path"]))["rows"]
    assert len(rows) == len({row["cell_id"] for row in rows}) == 3
    assert {row["judge_status"] for row in rows} == {"behavior_failure"}
    native = next(row for row in rows if row["experimental_arm"] == "Agentic")
    assert native["native_evidence"]["artifact_file_sha256"]
    by_arm = {cell["experimental_arm"]: cell for cell in report["cells"]}
    assert by_arm["Agent-No-EVAS"]["evas_usage"]["calls_executed"] == 0
    assert by_arm["Agentic"]["evas_usage"]["calls_executed"] >= 1
    runtime = Path(by_arm["Agentic"]["clean_room_contract"]["runtime"])
    assert not (runtime / "evidence/campaign_result.json").exists()
    assert len(list((runtime / "evidence/score-sidecars").glob("*.json"))) == 1
    assert by_arm["Agentic"]["bound_final_test"]["generation_evidence_unchanged"]
    frozen = smoke.read_json(tmp_path / "smoke/campaign.json")
    assert frozen["backend_by_arm"] == report["backend_by_arm"]
    smoke.write_json(tmp_path / "mixed-native-smoke.json", report)


def test_native_row_preserves_final_infrastructure_score_as_null(launched, native_case):  # noqa: F811
    arguments, _, _ = native_case
    # The external judge exits successfully without the required structured verdict.
    judge = Path(arguments["command"].split()[-1])
    judge.write_text("pass\n")
    runtime, cell, _, run = launched()
    assert run.artifact_path is not None
    row = scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)
    assert row["judge_status"] == "infrastructure_failure"
    assert row["score"] is None
    assert row["failure_responsibility"] == "system"
    assert row["trusted_replay"]["derived_score_sidecar_reference"]


def test_mixed_smoke_keeps_native_provider_failure_in_denominator(tmp_path, monkeypatch):
    from scripts import run_v4_r53_clean_room_smoke as smoke
    from test_v4_r53_clean_room_smoke import fake_evas_087

    complete = smoke.ScriptedClient.complete

    def failing_public_call(self, messages, max_tokens, tools, **kwargs):
        command = json.dumps(self._responses[0]) if self._responses else ""
        if "evas simulate" in command:
            raise TimeoutError("fixture provider unavailable")
        return complete(self, messages, max_tokens, tools, **kwargs)

    # Deterministic provider boundary; real exporter, controllers, runtime and scorer.
    monkeypatch.setattr(smoke.ScriptedClient, "complete", failing_public_call)
    args = smoke.parse_args([
        "--output-root", str(tmp_path / "smoke"),
        "--evas-command", str(fake_evas_087(tmp_path)),
        "--bound-final-authority", "--agentic-backend", "native-mini-swe",
        "--sandbox", "none", "--allow-insecure-test-sandbox",
    ])
    report = smoke.run_smoke(args)
    assert report["status"] == "FAIL"
    rows = smoke.read_json(Path(report["score_report"]["path"]))["rows"]
    assert len(rows) == 3
    native = next(row for row in rows if row["experimental_arm"] == "Agentic")
    assert native["outcome"] == "infrastructure_failure"
    assert native["score"] is None
    assert "trusted_replay" not in native
    assert native["native_evidence"]["files"]


def test_ci_runs_mixed_native_campaign_gate():
    workflow = (ROOT / ".github/workflows/evaluator-closure.yml").read_text()
    assert "tests/test_agent_harness_native_campaign.py::test_r53_docker_mixed_native_campaign" in workflow


def test_native_row_rejects_symlinked_frozen_candidate(launched):
    runtime, cell, _, _ = launched()
    frozen = runtime / "evidence/final_submission/model.va"
    copy = runtime / "same-bytes.va"
    copy.write_bytes(frozen.read_bytes())
    frozen.parent.chmod(0o700)
    frozen.unlink()
    frozen.symlink_to(copy)
    with pytest.raises(ValueError, match="symlink"):
        scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)


def test_native_row_rejects_request_backend_drift(launched):
    runtime, cell, _, _ = launched()
    path = runtime / "evidence/native-episode/request.json"
    request = json.loads(path.read_text())
    request["backend_profile_sha256"] = "d" * 64
    path.chmod(0o600)
    path.write_text(json.dumps(request))
    with pytest.raises(ValueError, match="backend"):
        scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)


def test_scheduled_summary_requires_terminal_dispositions():
    cell = {
        "cell_id": "cell", "task_id": "task", "family_id": "family",
        "form": "dut", "mode": "G2", "experimental_arm": "Agentic",
    }
    row = {**cell, "submission_status": "prepared", "judge_status": "not_run"}
    with pytest.raises(ValueError, match="terminal"):
        scorer.summarize([row], "final_trusted_replay", scheduled_cells=[cell])
