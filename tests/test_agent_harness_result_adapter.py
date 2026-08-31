"""Read-only framework integration: no generation, replay, or denominator loss."""

import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path
import sys

import pytest

from test_agent_harness_native_episode import native_case as native_case  # noqa: F401
from test_agent_harness_production_public_validation import public_case as public_case  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"))


@pytest.fixture
def failed_campaign(tmp_path):
    from test_agent_harness_result_ledger import _campaign

    campaign = _campaign()
    from run_native_attempts import retry_policy
    campaign["execution_config"]["native_retry_policy"] = retry_policy(1).to_document()
    path = tmp_path / "campaign.json"
    path.write_text(json.dumps(campaign))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    root = tmp_path / "run"
    for cell in campaign["cells"]:
        receipt = root / cell["cell_id"] / "evidence/native-dispatch/result.json"
        receipt.parent.mkdir(parents=True)
        receipt.write_text(json.dumps({
            "schema_version": "v4-native-dispatch-result-v1",
            "backend": "native-mini-swe", "cell": cell,
            "campaign_file_sha256": digest, "status": "provider_timeout",
            "termination_reason": "provider_timeout", "attempt_id": "attempt-1",
        }))
    return path, root


def test_parallel_read_preserves_every_failure_unknown_cost_and_source_bytes(failed_campaign):
    from result_adapter import read_campaign_ledger

    path, root = failed_campaign
    before = {p: p.read_bytes() for p in path.parent.rglob("*") if p.is_file()}
    serial = read_campaign_ledger(path, root, workers=1)
    parallel = read_campaign_ledger(path, root, workers=3)
    assert serial == parallel
    assert serial["denominator"]["scheduled_cells"] == 3
    assert serial["denominator"]["eligible_actual_score_cells"] == 0
    assert all(r["actual_score"] is None for r in serial["records"])
    assert all(r["usage"]["output_tokens"] is None for r in serial["records"])
    assert before == {p: p.read_bytes() for p in path.parent.rglob("*") if p.is_file()}


@pytest.mark.parametrize("workers", [0, -1, True, 1.5])
def test_reader_rejects_invalid_concurrency(failed_campaign, workers):
    from result_adapter import read_campaign_ledger
    with pytest.raises(ValueError, match="workers"):
        read_campaign_ledger(*failed_campaign, workers=workers)


@pytest.mark.parametrize("drift", ["missing", "identity", "duplicate", "escape", "symlink"])
def test_corrupt_or_incomplete_input_never_becomes_a_zero(failed_campaign, drift):
    from result_adapter import read_campaign_ledger

    path, root = failed_campaign
    campaign = json.loads(path.read_text())
    receipt = root / campaign["cells"][0]["cell_id"] / "evidence/native-dispatch/result.json"
    if drift == "missing":
        receipt.unlink()
    elif drift == "identity":
        value = json.loads(receipt.read_text())
        value["cell"]["task_id"] = "wrong"
        receipt.write_text(json.dumps(value))
    elif drift == "symlink":
        external = receipt.with_name("other.json")
        receipt.rename(external)
        receipt.symlink_to(external)
    else:
        if drift == "duplicate":
            campaign["cells"].append(campaign["cells"][0])
        else:
            campaign["cells"][0]["cell_id"] = "../outside"
        path.write_text(json.dumps(campaign))
    with pytest.raises((ValueError, FileNotFoundError)):
        read_campaign_ledger(path, root, workers=2)


def test_official_inspect_roundtrip_preserves_zero_null_and_eligible_denominator(tmp_path):
    pytest.importorskip("inspect_ai")
    from inspect_ai.log import read_eval_log, write_eval_log
    from result_adapter import build_inspect_log
    from test_agent_harness_result_ledger import _campaign, _row, result_ledger

    campaign = _campaign()
    rows = [_row(cell, score=score, status=status) for cell, score, status in zip(
        campaign["cells"], [1, 0, None], ["passed", "behavior_failure", "infrastructure_failure"],
    )]
    ledger = result_ledger.build_native_campaign_ledger(campaign, rows, campaign_file_sha256="a" * 64)
    log = build_inspect_log(ledger)
    path = tmp_path / "import.eval"
    write_eval_log(log, path, format="eval")
    loaded = read_eval_log(path)
    records = {r["identity"]["cell_id"]: r for r in ledger["records"]}
    assert len(loaded.samples) == 3
    for sample in loaded.samples:
        record = records[sample.id]
        score = sample.scores["vaevas_final"]
        if record["actual_score"] is None:
            assert math.isnan(score.value)
        else:
            assert score.value == record["actual_score"]
        assert sample.metadata["vaevas"] == record
        assert not sample.messages and not sample.events
    assert loaded.results.total_samples == 3
    assert loaded.results.scores[0].scored_samples == 2
    assert loaded.results.scores[0].unscored_samples == 1
    # No headline pooled across distinct experimental conditions.
    assert loaded.results.headline is None
    assert loaded.eval.metadata["vaevas_ledger"] == ledger
    assert "do not leak" not in loaded.model_dump_json()


def test_official_export_is_write_once_outside_evidence(failed_campaign, tmp_path, monkeypatch):
    pytest.importorskip("inspect_ai")
    from inspect_ai.log import read_eval_log
    from result_adapter import export_inspect

    def forbidden(*args, **kwargs):
        raise AssertionError("read-only export attempted external execution or network")

    import socket
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)

    campaign, root = failed_campaign
    output = tmp_path / "export"
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    receipt = export_inspect(campaign, root, output, workers=2)
    log = read_eval_log(output / "results.eval")
    assert len(log.samples) == 3
    assert receipt["scheduled_cells"] == 3
    assert log.eval.metadata["execution_performed"] is False
    assert receipt["read_workers"] == 2
    assert receipt["read_elapsed_s"] >= 0
    assert before == {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert (output / "ledger.json").is_file()
    with pytest.raises(FileExistsError):
        export_inspect(campaign, root, output)
    with pytest.raises(ValueError, match="outside"):
        export_inspect(campaign, root, root / "export")


def test_scored_evidence_to_inspect_cli_never_reexecutes_judge(native_case, tmp_path):  # noqa: F811
    pytest.importorskip("inspect_ai")
    from inspect_ai.log import read_eval_log
    from run_native_mini_swe import run_prepared_native_mini_swe
    from test_agent_harness_native_launcher import Provider
    from test_agent_harness_result_ledger import _campaign

    arguments, _, _ = native_case
    campaign = _campaign()
    campaign["cells"] = [campaign["cells"][2]]
    campaign["execution_config"].pop("native_retry_policy")
    cell = campaign["cells"][0]
    cell.update(executable_feedback=True, per_turn_max_tokens=128)
    path = tmp_path / "scored-campaign.json"
    path.write_text(json.dumps(campaign))
    root = tmp_path / "scored-run"
    runtime = root / cell["cell_id"]
    for directory in ("public/task", "evaluator"):
        shutil.copytree(arguments["runtime"] / directory, runtime / directory)
    (runtime / "public/submission").mkdir()
    (runtime / "agent_prompt.txt").write_text("Implement the public task.")
    provider = Provider(["printf 'module model; endmodule\\n' > public/submission/model.va", "vabench-submit"])
    run_prepared_native_mini_swe(
        runtime=runtime, cell=cell, client=provider, attempt_id="attempt-001",
        evas_command=arguments["evas_command"], final_judge_command=arguments["command"],
        judge_timeout_s=10, allow_insecure_test_sandbox=True,
        campaign_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )
    # The external test judge leaves a marker. Its timestamp and ALL source
    # bytes must remain unchanged across an actual separate-process import.
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()}
    output = tmp_path / "scored-export"
    completed = subprocess.run([
        sys.executable, str(ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot/result_adapter.py"),
        "--campaign", str(path), "--run-root", str(root), "--output-dir", str(output), "--workers", "2",
    ], capture_output=True, text=True, timeout=60, check=False)
    assert completed.returncode == 0, completed.stderr
    log = read_eval_log(output / "results.eval")
    assert log.samples[0].scores["vaevas_final"].value == 0
    assert log.samples[0].metadata["vaevas"]["hashes"]["score_sidecar_sha256"]
    assert "FINAL_JUDGE_SENTINEL" not in log.model_dump_json()
    assert before == {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()}
