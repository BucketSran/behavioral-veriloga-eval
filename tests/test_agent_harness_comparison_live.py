"""Live-entrypoint contract tests; all external responses are synthetic."""

import importlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"))


@pytest.fixture(autouse=True)
def reviewed_clock(monkeypatch):
    live = importlib.import_module("comparison_live")

    class Clock:
        @staticmethod
        def now(tz):
            return datetime(2026, 8, 31, 12, tzinfo=timezone.utc)

    monkeypatch.setattr(live, "datetime", Clock)


def test_live_preparation_freezes_named_provider_without_granting_spending(tmp_path):
    live = importlib.import_module("comparison_live")
    comparison = importlib.import_module("run_legacy_native_comparison")
    profile = live.build_provider_profile(currency="CNY", cap="0.01")
    root = tmp_path / "live"
    manifest = comparison.freeze_comparison(
        root, image_id="sha256:" + "a" * 64, code_commit="b" * 40,
        evas_identity={"available": True}, currency="CNY", cap="0.01", provider_profile=profile,
    )
    assert manifest["schema_version"] == "vaevas-workflow-comparison-live-v1"
    assert manifest["live_authorized"] is False
    assert manifest["provider_profile"] == profile
    assert profile["model"] == "deepseek-v4-flash"
    assert profile["decoding"]["thinking"] == {"type": "disabled"}
    assert profile["model_snapshot_policy"] == "provider_alias_not_immutable_snapshot"
    assert manifest["evidence_scope"] == "real_model_workflow_comparison"
    for binding in manifest["campaigns"].values():
        campaign = json.loads((root / binding["path"]).read_text())
        assert campaign["model_provider"] == "deepseek"
    assert not (root / "budget.jsonl").exists()
    assert not (root / "live-authorization.json").exists()


def _prepared(tmp_path):
    live = importlib.import_module("comparison_live")
    comparison = importlib.import_module("run_legacy_native_comparison")
    root = tmp_path / "live"
    manifest = comparison.freeze_comparison(
        root, image_id="sha256:" + "a" * 64, code_commit="b" * 40,
        evas_identity={"available": True}, currency="CNY", cap="0.01",
        provider_profile=live.build_provider_profile(currency="CNY", cap="0.01"),
    )
    return live, comparison, root, manifest


@pytest.mark.parametrize("changed", ["hash", "cap", "currency", "profile", "source"])
def test_launch_drift_blocks_before_credential_loading(tmp_path, monkeypatch, changed):
    live, comparison, root, manifest = _prepared(tmp_path)
    expected_hash = comparison.file_sha256(root / "comparison-manifest.json")
    cap, currency = "0.01", "CNY"
    if changed == "hash":
        expected_hash = "f" * 64
    elif changed == "cap":
        cap = "5.00"
    elif changed == "currency":
        currency = "USD"
    else:
        manifest["provider_profile" if changed == "profile" else "source_identity"] = {}
        path = root / "comparison-manifest.json"
        path.chmod(0o600)
        path.write_text(json.dumps(manifest))
        expected_hash = comparison.file_sha256(path)
    monkeypatch.setattr(live, "load_pilot_key", lambda *a: pytest.fail("credentials read"))
    with pytest.raises(ValueError):
        live.execute_live_comparison(root, expected_manifest_sha256=expected_hash,
                                     approved_cap=cap, currency=currency,
                                     credential_file=tmp_path / "absent", evas_command="unused")
    assert not (root / "budget.jsonl").exists()
    assert not (root / "live-authorization.json").exists()


def test_free_execution_cannot_consume_live_preparation(tmp_path):
    _, comparison, root, manifest = _prepared(tmp_path)
    with pytest.raises(ValueError, match="live"):
        comparison.execute_comparison(root, manifest, evas_command="unused",
                                      scripted_response=lambda *a: pytest.fail("sent"))


def test_expired_profile_blocks_launch_but_remains_inspectable(tmp_path, monkeypatch):
    live, comparison, root, manifest = _prepared(tmp_path)

    class Later:
        @staticmethod
        def now(tz):
            return datetime(2026, 9, 1, tzinfo=timezone.utc)

    monkeypatch.setattr(live, "datetime", Later)
    comparison._validate_frozen(root, manifest, current_source=False)
    monkeypatch.setattr(live, "load_pilot_key", lambda *a: pytest.fail("credentials read"))
    with pytest.raises(ValueError, match="expired"):
        live.execute_live_comparison(root, expected_manifest_sha256=comparison.file_sha256(root / "comparison-manifest.json"),
                                     approved_cap="0.01", currency="CNY",
                                     credential_file=tmp_path / "absent", evas_command="unused")


@pytest.mark.parametrize("cap,unknown,expected_calls", [("0.01", False, 0), ("5.00", True, 1), ("5.00", False, 2)])
def test_live_transport_reuses_one_guard_and_observes_actual_curl(tmp_path, monkeypatch, cap, unknown, expected_calls):
    live = importlib.import_module("comparison_live")
    budget_module = importlib.import_module("deepseek_budget")
    sent, observed = [], []
    journal = tmp_path / "budget.jsonl"

    def http(argv, **kwargs):
        assert argv[0] == "curl" and live.ENDPOINT in argv
        assert kwargs["timeout"] <= 1800.5
        assert json.loads(journal.read_text().splitlines()[-1])["event"] == "reserved"
        payload = json.loads(Path(argv[argv.index("--data-binary") + 1][1:]).read_text())
        assert payload["model"] == live.MODEL and payload["max_tokens"] == 4096
        assert payload["thinking"] == {"type": "disabled"}
        sent.append(payload)
        chunk = {"model": live.MODEL, "choices": [{"delta": {"content": "ok"}, "finish_reason": "stop"}],
                 "usage": None if unknown else {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11}}
        return subprocess.CompletedProcess(argv, 0, "data: " + json.dumps(chunk) + "\n\ndata: [DONE]\n", "")

    monkeypatch.setattr(subprocess, "run", http)
    with budget_module.DeepSeekPilotBudget(journal, cell_ids=["left", "right"], cap=cap, model_call_limit=None) as budget:
        for cell in ("left", "right"):
            client = live.LiveComparisonClient(budget=budget, cell_id=cell, api_key="synthetic-secret",
                                               profile=live.build_provider_profile(currency="CNY", cap=cap),
                                               request_observer=lambda payload, timeout: observed.append(payload))
            if expected_calls < 2:
                with pytest.raises(budget_module.PilotBudgetStop):
                    client.complete([], 4096, [])
            else:
                assert client.complete([], 4096, [])["choices"][0]["message"]["content"] == "ok"
    assert len(sent) == expected_calls
    assert len(observed) >= len(sent)
    assert "synthetic-secret" not in journal.read_text()


def test_live_client_rejects_output_cap_drift_before_transport(tmp_path, monkeypatch):
    live = importlib.import_module("comparison_live")
    budget_module = importlib.import_module("deepseek_budget")
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: pytest.fail("HTTP admitted"))
    with budget_module.DeepSeekPilotBudget(tmp_path / "budget.jsonl", cell_ids=["a"], cap="5.00") as budget:
        client = live.LiveComparisonClient(budget=budget, cell_id="a", api_key="synthetic-key",
                                           profile=live.build_provider_profile(currency="CNY", cap="5.00"),
                                           request_observer=lambda *a: None)
        with pytest.raises(ValueError, match="decoding"):
            client.complete([], 10, [])


def test_rehashed_budget_rate_drift_is_rejected_before_credentials(tmp_path, monkeypatch):
    live, comparison, root, manifest = _prepared(tmp_path)
    manifest["budget"]["output_peak_per_million"] = "0.01"
    path = root / "comparison-manifest.json"
    path.chmod(0o600)
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(live, "load_pilot_key", lambda *a: pytest.fail("credentials read"))
    monkeypatch.setattr(comparison.runner, "validate_pinned_evas_identity", lambda *a: pytest.fail("runtime validation reached"))
    with pytest.raises(ValueError, match="budget"):
        live.execute_live_comparison(root, expected_manifest_sha256=comparison.file_sha256(path), approved_cap="0.01",
                                     currency="CNY", credential_file=tmp_path / "absent", evas_command="unused")


def _sealed_live_unstarted(tmp_path):
    live, comparison, root, manifest = _prepared(tmp_path)
    live._atomic_once(root / "live-authorization.json", live._authorization(root, manifest))
    live._atomic_once(root / "provider-preflight.json", {
        "currency": "CNY", "model_available": True,
        "response_sha256": {"/models": "a" * 64, "/user/balance": "b" * 64},
    })
    rows = [{**{key: scheduled[key] for key in ("comparison_cell_id", "cell_id", "task_id", "family_id", "form", "backend", "runtime")},
             "started": False, "disposition": "not_started", "reason": "fixture_preflight_stop",
             "score": None, "evidence": None, "surface": None, "elapsed_s": None,
             "model_calls": 0, "guard_upper_bound": "0"} for scheduled in manifest["schedule"]]
    with comparison.DeepSeekPilotBudget(root / "budget.jsonl", cell_ids=[r["comparison_cell_id"] for r in rows],
                                        cap="0.01", model_call_limit=None):
        pass
    (root / "execution.jsonl").write_text("".join(json.dumps({"event": "cell_terminal", "row": row}) + "\n" for row in rows))
    live._atomic_once(root / "comparison-execution.json", {
        "schema_version": "vaevas-comparison-execution-v1", "rows": rows,
        **{key: comparison.file_sha256(root / relative) for key, relative in (
            ("manifest_sha256", "comparison-manifest.json"), ("budget_sha256", "budget.jsonl"),
            ("execution_sha256", "execution.jsonl"), ("authorization_sha256", "live-authorization.json"),
            ("preflight_sha256", "provider-preflight.json"))},
    })
    return comparison, root


def test_live_reader_does_not_claim_zero_paid_fixture_and_binds_launch_receipt(tmp_path):
    comparison, root = _sealed_live_unstarted(tmp_path)
    report = comparison.read_comparison(root)
    assert report["paid_requests"] is None  # Billing is not observed by the runner.
    assert report["potentially_billable_attempts"] == 0
    assert report["authorization_sha256"] == comparison.file_sha256(root / "live-authorization.json")
    assert report["preflight_sha256"] == comparison.file_sha256(root / "provider-preflight.json")


@pytest.mark.parametrize("filename", ["live-authorization.json", "provider-preflight.json"])
def test_live_reader_rejects_modified_launch_evidence(tmp_path, filename):
    comparison, root = _sealed_live_unstarted(tmp_path)
    path = root / filename
    path.chmod(0o600)
    path.write_text("{}")
    with pytest.raises(ValueError):
        comparison.read_comparison(root)


def test_inspect_command_never_loads_credentials_and_default_cli_cannot_launch(tmp_path, monkeypatch, capsys):
    live, comparison, root, manifest = _prepared(tmp_path)
    monkeypatch.setattr(live, "load_pilot_key", lambda *a: pytest.fail("credentials read"))
    assert live.main(["inspect", "--output-root", str(root)]) == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected["manifest_sha256"] == comparison.file_sha256(root / "comparison-manifest.json")
    assert inspected["live_authorized"] is False
    assert inspected["provider_profile"] == manifest["provider_profile"]
    with pytest.raises(SystemExit) as missing:
        live.main(["run", "--output-root", str(root)])
    assert missing.value.code == 2
    assert not (root / "live-authorization.json").exists()


def test_cli_prepare_is_free_and_leaves_a_reviewable_manifest(tmp_path, capsys):
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in Docker/EVAS identity preparation; no HTTP")
    live = importlib.import_module("comparison_live")
    root = tmp_path / "prepared"
    assert live.main(["prepare", "--output-root", str(root), "--currency", "CNY", "--cap", "0.01",
                      "--evas-command", str(ROOT / ".venv/bin/evas"),
                      "--image", "vabench-agent-runtime:0.8.7"]) == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected["live_authorized"] is False
    assert inspected["provider_profile"]["cap"] == "0.01"
    assert not (root / "live-authorization.json").exists()


@pytest.mark.parametrize("mode", ["complete", "insufficient", "unknown"])
def test_real_live_entrypoint_six_cell_chain_with_fake_external_http(tmp_path, monkeypatch, mode):
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in actual Docker/EVAS; only synthetic external HTTP")
    import http.client
    from scripts import run_v4_r53_clean_room_smoke as smoke
    from runners.agent_harness.batch_resume import docker_image_identity
    live = importlib.import_module("comparison_live")
    comparison = importlib.import_module("run_legacy_native_comparison")
    evas, identity = smoke.resolve_evas_command(str(ROOT / ".venv/bin/evas"))
    cap = "0.01" if mode == "insufficient" else "5.00"
    root = tmp_path / "comparison"
    manifest = comparison.freeze_comparison(
        root, image_id=docker_image_identity(smoke.DEFAULT_EVAS_IMAGE),
        code_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        evas_identity=identity, cap=cap, provider_profile=live.build_provider_profile(currency="CNY", cap=cap),
    )
    commands = {}
    for row in manifest["schedule"]:
        artifacts = smoke.public_stub_artifacts(smoke.public_contract(smoke.DEFAULT_RELEASE, row["task_id"]))
        commands[row["comparison_cell_id"]] = iter([
            *[f"printf %s {shlex.quote(content)} > public/submission/{name}" for name, content in artifacts.items()],
            "vabench-submit",
        ])
    metadata, sent = [], []

    class MetadataConnection:
        def __init__(self, host, timeout):
            assert host == "api.deepseek.com"

        def request(self, method, path, headers):
            assert method == "GET" and headers["Authorization"] == "Bearer synthetic-key"
            metadata.append(path)
            self.path = path

        def getresponse(self):
            return self

        status = 200

        def read(self, limit):
            value = ({"data": [{"id": live.MODEL}]} if self.path == "/models" else
                     {"is_available": True, "balance_infos": [{"currency": "CNY", "total_balance": "5.00"}]})
            return json.dumps(value).encode()

        def close(self):
            pass

    original_run = subprocess.run

    def external(argv, **kwargs):
        if not isinstance(argv, list) or argv[0] != "curl":
            return original_run(argv, **kwargs)
        assert live.ENDPOINT in argv
        assert all(name not in os.environ for name in ("DEEPSEEK_API_KEY", "GLM_API_KEY"))
        reservation = json.loads((root / "budget.jsonl").read_text().splitlines()[-1])
        assert reservation["event"] == "reserved"
        cell_id = reservation["cell_id"]
        sent.append(cell_id)
        if mode == "unknown":
            return subprocess.CompletedProcess(argv, 16, "", "synthetic unknown cost")
        chunk = {"id": f"fixture-{len(sent)}", "model": live.MODEL, "choices": [{
            "finish_reason": "tool_calls", "delta": {"tool_calls": [{"index": 0, "id": f"call-{len(sent)}",
                "type": "function", "function": {"name": "bash", "arguments": json.dumps({
                    "command": next(commands[cell_id])})}}]}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}}
        return subprocess.CompletedProcess(argv, 0, "data: " + json.dumps(chunk) + "\n\ndata: [DONE]\n", "")

    monkeypatch.setattr(http.client, "HTTPSConnection", MetadataConnection)
    monkeypatch.setattr(subprocess, "run", external)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "must-not-reach-child")
    monkeypatch.setenv("GLM_API_KEY", "must-not-reach-child")
    with tempfile.TemporaryDirectory(prefix="vaevas-synthetic-key-") as directory:
        credential = Path(directory) / "keys.env"
        credential.write_text('DEEPSEEK_API_KEY="synthetic-key"\n')
        credential.chmod(0o600)
        kwargs = dict(expected_manifest_sha256=comparison.file_sha256(root / "comparison-manifest.json"),
                      approved_cap=cap, currency="CNY", credential_file=credential, evas_command=evas)
        report = live.execute_live_comparison(root, **kwargs)
        assert len(report["audit_rows"]) == 6, report
        assert report["paid_requests"] is None
        assert report["potentially_billable_attempts"] == len(sent)
        assert metadata == ["/models", "/user/balance"]
        if mode == "complete":
            assert len(sent) == 12
            assert all(row["score"] is not None for row in report["audit_rows"]), report
            assert all(row["complete"] and row["matched_surface"] for row in report["paired_rows"])
        else:
            assert len(sent) == (0 if mode == "insufficient" else 1)
            assert report["audit_rows"][0]["disposition"] == "budget_censored"
            assert all(row["disposition"] == "not_started" for row in report["audit_rows"][1:])
        assert comparison.read_comparison(root) == report
        count = len(sent)
        with pytest.raises((ValueError, FileExistsError)):
            live.execute_live_comparison(root, **kwargs)
        assert len(sent) == count and len(metadata) == 2
        assert "synthetic-key" not in json.dumps(report)
        assert str(credential) not in json.dumps(report)
