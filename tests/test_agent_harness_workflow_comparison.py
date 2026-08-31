"""Free tests for the single-attempt legacy/native comparison coordinator."""

import importlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"))


def test_freeze_comparison_reuses_blueprint_without_authorizing_live_calls(tmp_path):
    comparison = importlib.import_module("run_legacy_native_comparison")
    root = tmp_path / "comparison"
    manifest = comparison.freeze_comparison(
        root, image_id="sha256:" + "a" * 64, code_commit="b" * 40,
        evas_identity={"version_output": "evas-sim 0.8.7", "available": True}, cap="0.01",
    )
    assert json.loads((root / "comparison-manifest.json").read_text()) == manifest
    assert manifest["live_authorized"] is False
    assert manifest["controls"]["model_call_limit"] is None
    assert manifest["controls"]["request_timeout_s"] == 1800
    assert manifest["budget"]["cap"] == "0.01"
    assert len(manifest["schedule"]) == 6
    assert [(r["task_id"], r["backend"]) for r in manifest["schedule"]] == [
        ("v4-001", "legacy"), ("v4-001", "native-mini-swe"),
        ("v4-1001", "native-mini-swe"), ("v4-1001", "legacy"),
        ("v4-501", "legacy"), ("v4-501", "native-mini-swe"),
    ]
    assert len({row["runtime"] for row in manifest["schedule"]}) == 6
    for backend, binding in manifest["campaigns"].items():
        campaign = json.loads((root / binding["path"]).read_text())
        assert {row["form"] for row in campaign["cells"]} == {"dut", "bugfix", "testbench"}
        assert all(row["experimental_arm"] == "Agentic" for row in campaign["cells"])
        assert campaign["execution_config"]["episode_backend"] == backend


def test_changed_manifest_is_rejected_before_execution_journal_or_transport(tmp_path):
    comparison = importlib.import_module("run_legacy_native_comparison")
    root = tmp_path / "comparison"
    manifest = comparison.freeze_comparison(
        root, image_id="sha256:" + "a" * 64, code_commit="b" * 40,
        evas_identity={"version_output": "evas-sim 0.8.7", "available": True},
    )
    manifest["controls"]["request_timeout_s"] = 120
    sent = []
    with pytest.raises(ValueError, match="manifest"):
        comparison.execute_comparison(root, manifest, evas_command="fixture-unused",
                                      scripted_response=lambda *args: sent.append(args))
    assert not sent
    assert not (root / "budget.jsonl").exists()
    assert not (root / "execution.jsonl").exists()


def _unstarted_fixture(tmp_path):
    comparison = importlib.import_module("run_legacy_native_comparison")
    root = tmp_path / "comparison"
    manifest = comparison.freeze_comparison(root, image_id="sha256:" + "a" * 64,
                                           code_commit="b" * 40, evas_identity={"available": True})
    rows = [{**{key: scheduled[key] for key in ("comparison_cell_id", "cell_id", "task_id", "family_id", "form", "backend", "runtime")},
             "started": False, "disposition": "not_started", "reason": "fixture_preflight_stop",
             "score": None, "evidence": None, "surface": None, "elapsed_s": None,
             "model_calls": 0, "guard_upper_bound": "0"} for scheduled in manifest["schedule"]]
    with comparison.DeepSeekPilotBudget(root / "budget.jsonl", cell_ids=[r["comparison_cell_id"] for r in rows],
                                        model_call_limit=None):
        pass
    _seal_fixture_execution(comparison, root, rows)
    return comparison, root, manifest, rows


def _seal_fixture_execution(comparison, root, rows):
    (root / "execution.jsonl").write_text("".join(json.dumps({"event": "cell_terminal", "row": row}) + "\n" for row in rows))
    execution = {"schema_version": "vaevas-comparison-execution-v1", "rows": rows,
                 **{key: comparison.file_sha256(root / relative) for key, relative in (
                     ("manifest_sha256", "comparison-manifest.json"), ("budget_sha256", "budget.jsonl"), ("execution_sha256", "execution.jsonl"))}}
    (root / "comparison-execution.json").write_text(json.dumps(execution))


def test_reader_rejects_edited_projection_even_if_journal_digest_unchanged(tmp_path):
    comparison, root, _, _ = _unstarted_fixture(tmp_path)
    assert len(comparison.read_comparison(root)["audit_rows"]) == 6
    path = root / "comparison-execution.json"
    value = json.loads(path.read_text())
    value["rows"][0]["reason"] = "silently_reclassified"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="journal"):
        comparison.read_comparison(root)


def test_reader_requires_surface_for_completed_terminal_evidence(tmp_path, monkeypatch):
    comparison, root, _, rows = _unstarted_fixture(tmp_path)
    for row in rows:
        row.update(started=True, disposition="completed", elapsed_s=1.0,
                   evidence={key: row[key] for key in ("cell_id", "task_id", "family_id", "form", "backend", "score")})
    module = importlib.import_module("comparison_results")
    monkeypatch.setattr(module, "read_backend_cell", lambda runtime, backend, cell, **kw: next(
        row["evidence"] for row in rows if row["backend"] == backend and row["cell_id"] == cell["cell_id"]))
    _seal_fixture_execution(comparison, root, rows)
    with pytest.raises(ValueError, match="surface"):
        comparison.read_comparison(root)


def test_reader_validates_campaign_bytes_even_when_every_cell_unstarted(tmp_path):
    comparison, root, _, _ = _unstarted_fixture(tmp_path)
    (root / "legacy/campaign.json").chmod(0o600)
    (root / "legacy/campaign.json").write_text("{}")
    with pytest.raises(ValueError, match="campaign"):
        comparison.read_comparison(root)


@pytest.mark.parametrize("field,value", [("model_calls", 10), ("guard_upper_bound", "0.3")])
def test_report_accounting_must_match_shared_budget_journal(tmp_path, field, value):
    comparison, root, _, rows = _unstarted_fixture(tmp_path)
    rows[0][field] = value
    _seal_fixture_execution(comparison, root, rows)
    with pytest.raises(ValueError, match="budget"):
        comparison.read_comparison(root)


def test_reader_rejects_symlinked_source_evidence(tmp_path):
    comparison, root, _, _ = _unstarted_fixture(tmp_path)
    path = root / "execution.jsonl"
    target = tmp_path / "external.jsonl"
    path.rename(target)
    path.symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        comparison.read_comparison(root)


def test_reader_rejects_requests_missing_from_surface_projection(tmp_path):
    comparison, root, _, rows = _unstarted_fixture(tmp_path)
    path = root / "execution.jsonl"
    path.write_text(json.dumps({"event": "request_observed", "comparison_cell_id": rows[0]["comparison_cell_id"],
                               "request": {"request_sha256": "a" * 64}}) + "\n" + path.read_text())
    path = root / "comparison-execution.json"
    value = json.loads(path.read_text())
    value["execution_sha256"] = comparison.file_sha256(root / "execution.jsonl")
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="request"):
        comparison.read_comparison(root)


@pytest.mark.parametrize("mutation", ["model", "timeout", "cell"])
def test_rehashed_campaign_must_still_follow_comparison_protocol(tmp_path, monkeypatch, mutation):
    comparison, root, manifest, _ = _unstarted_fixture(tmp_path)
    path = root / "legacy/campaign.json"
    value = json.loads(path.read_text())
    if mutation == "model":
        value["model"] = "another-model"
    elif mutation == "timeout":
        value["execution_config"]["request_timeout_s"] = 120
    else:
        value["cells"][0]["per_turn_max_tokens"] = 2
    path.chmod(0o600)
    path.write_text(json.dumps(value))
    manifest["campaigns"]["legacy"]["sha256"] = comparison.file_sha256(path)
    path = root / "comparison-manifest.json"
    path.chmod(0o600)
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(comparison.runner, "validate_pinned_evas_identity", lambda *a: pytest.fail("reached evaluator validation"))
    with pytest.raises(ValueError, match="campaign"):
        comparison.execute_comparison(root, manifest, evas_command="not-run", scripted_response=lambda *a: pytest.fail("sent"))


def test_real_six_cell_workflow_comparison_freezes_scores_and_reads_without_reentry(tmp_path):
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in actual Docker/EVAS, scripted HTTP only")
    from scripts import run_v4_r53_clean_room_smoke as smoke
    from runners.agent_harness.batch_resume import docker_image_identity
    comparison = importlib.import_module("run_legacy_native_comparison")
    evas, identity = smoke.resolve_evas_command(str(ROOT / ".venv/bin/evas"))
    root = tmp_path / "comparison"
    manifest = comparison.freeze_comparison(
        root, image_id=docker_image_identity(smoke.DEFAULT_EVAS_IMAGE),
        code_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        evas_identity=identity,
    )
    commands = {}
    for row in manifest["schedule"]:
        artifacts = smoke.public_stub_artifacts(smoke.public_contract(smoke.DEFAULT_RELEASE, row["task_id"]))
        commands[row["comparison_cell_id"]] = iter([
            "test ! -r /runtime/evaluator/check.py",
            *[f"printf %s {shlex.quote(content)} > public/submission/{name}"
              for name, content in artifacts.items()],
            "vabench-submit",
        ])
    requests = []

    def scripted(cell_id, payload):
        requests.append((cell_id, payload))
        chunk = {
            "id": f"fixture-{len(requests)}", "model": comparison.MODEL,
            "choices": [{"finish_reason": "tool_calls", "delta": {"tool_calls": [{
                "index": 0, "id": f"call-{len(requests)}", "type": "function", "function": {
                    "name": "bash", "arguments": json.dumps({"command": next(commands[cell_id])}),
                },
            }]}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }
        return subprocess.CompletedProcess([], 0, "data: " + json.dumps(chunk) + "\n\ndata: [DONE]\n", "")

    report = comparison.execute_comparison(root, manifest, evas_command=evas, scripted_response=scripted)
    assert len(report["audit_rows"]) == 6, report
    assert all(row["score"] is not None for row in report["audit_rows"]), report
    assert len(report["paired_rows"]) == 3
    assert all(row["complete"] for row in report["paired_rows"])
    assert all(pair["all_common_checks_match"] for pair in report["surface_pairs"]), report["surface_pairs"]
    assert {row[0] for row in requests} == {row["comparison_cell_id"] for row in manifest["schedule"]}
    before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*")
              if p.is_file() and not p.is_symlink() and "evaluator" not in p.parts}
    assert comparison.read_comparison(root) == report
    after = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*")
             if p.is_file() and not p.is_symlink() and "evaluator" not in p.parts}
    assert before == after
    with pytest.raises((ValueError, FileExistsError)):
        comparison.execute_comparison(root, manifest, evas_command=evas, scripted_response=scripted)


@pytest.mark.parametrize("cap,expected_requests,expected_committed", [
    ("0.01", 0, "0"), ("5.00", 1, "3.182592"),
])
def test_real_comparison_cost_stop_retains_every_unscored_row(tmp_path, cap, expected_requests, expected_committed):
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in actual Docker, free unknown-usage fixture")
    from scripts import run_v4_r53_clean_room_smoke as smoke
    from runners.agent_harness.batch_resume import docker_image_identity
    comparison = importlib.import_module("run_legacy_native_comparison")
    evas, identity = smoke.resolve_evas_command(str(ROOT / ".venv/bin/evas"))
    root = tmp_path / "comparison"
    manifest = comparison.freeze_comparison(root, image_id=docker_image_identity(smoke.DEFAULT_EVAS_IMAGE),
                                             code_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                                             evas_identity=identity, cap=cap)
    sent = []

    def unknown(cell_id, payload):
        sent.append(cell_id)
        return subprocess.CompletedProcess([], 16, "", "synthetic unknown-cost transport failure")

    report = comparison.execute_comparison(root, manifest, evas_command=evas, scripted_response=unknown)
    assert len(sent) == expected_requests
    assert len(report["audit_rows"]) == 6
    assert all(row["score"] is None for row in report["audit_rows"])
    assert report["audit_rows"][0]["disposition"] == "budget_censored"
    assert report["audit_rows"][0]["reason"] in {"insufficient_reservation", "unknown_request_cost"}
    assert all(row["disposition"] == "not_started" for row in report["audit_rows"][1:])
    assert all(row["reason"] == "budget_stopped" for row in report["audit_rows"][1:])
    assert all(row["score_delta"] is None for row in report["paired_rows"])
    events = [json.loads(line) for line in (root / "budget.jsonl").read_text().splitlines()]
    assert events[-1]["committed_upper_bound"] == expected_committed
    assert comparison.read_comparison(root) == report
