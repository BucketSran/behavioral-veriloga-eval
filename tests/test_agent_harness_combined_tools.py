"""Combined entrypoint tests: synthetic documents/provider responses only."""

import hashlib
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

from test_agent_harness_native_episode import native_case as native_case  # noqa: F401
from test_agent_harness_production_public_validation import public_case as public_case  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
sys.path.insert(0, str(OPS))


@pytest.fixture(autouse=True)
def reviewed_clock(monkeypatch):
    class Clock:
        @staticmethod
        def now(tz):
            return datetime(2026, 8, 31, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(importlib.import_module("comparison_live"), "datetime", Clock)


def corpus(tmp_path):
    from runners.agent_harness.tools.offline_docs import OfflineDocsCorpus
    root = tmp_path / "corpus"
    root.mkdir()
    content = "Synthetic reference: analog contribution uses the <+ operator."
    (root / "reference.md").write_text(content)
    manifest = {
        "schema_version": 1, "synthetic_only": True, "network_enabled": False,
        "builder": "combined-test", "exclusions": ["hidden", "r53-test-task"],
        "documents": [{"id": "reference", "path": "reference.md",
                       "source": "synthetic_fixture", "license": "CC0-1.0",
                       "section": "language", "sha256": hashlib.sha256(content.encode()).hexdigest()}],
    }
    return OfflineDocsCorpus.from_manifest(root, manifest)


def prepared(tmp_path, *, backend="evolution", live=False, cap="5.00"):
    module = importlib.import_module("run_combined_tools")
    docs = corpus(tmp_path)
    root = tmp_path / "acceptance"
    manifest = module.freeze_combined(
        root, backend=backend, family_id="001", form="DUT", docs_corpus=docs,
        image_id="sha256:" + "a" * 64, branch_image_id="sha256:" + "b" * 64,
        evas_identity={"available": True}, currency="CNY", cap=cap, live=live,
    )
    return module, root, manifest, docs


def test_prepare_freezes_all_extensions_without_spending(tmp_path):
    module, root, manifest, docs = prepared(tmp_path)
    assert manifest["schema_version"] == "vaevas-combined-tools-v1"
    assert manifest["live_authorized"] is False
    assert manifest["controls"]["rounds"] == 2
    assert len(manifest["budget_ids"]) == 2
    assert manifest["docs_profile"] == docs.profile
    assert manifest["public_waveform"] is True
    assert module.inspect_combined(root)["manifest_sha256"] == module.file_sha256(root / "combined-manifest.json")
    assert not (root / "budget.jsonl").exists()
    assert not (root / "live-authorization.json").exists()


@pytest.mark.parametrize("field,value", [
    ("evidence_scope", "real_model_combined_acceptance"),
    ("claim_scope", "formal_model_quality"),
])
def test_free_manifest_cannot_relabel_its_claim_boundary(tmp_path, field, value):
    module, root, manifest, _ = prepared(tmp_path)
    manifest[field] = value
    path = root / "combined-manifest.json"
    path.chmod(0o600)
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="scope"):
        module.read_combined(root)


def test_prepared_native_enforces_declared_tool_limit(native_case, tmp_path):  # noqa: F811
    from run_native_mini_swe import run_prepared_native_mini_swe
    from test_agent_harness_native_conditions import _cell, _native_runtime
    from test_agent_harness_native_launcher import Provider
    from runners.agent_harness import read_trajectory
    from score_campaign import read_native_cell
    arguments, _, _ = native_case
    runtime = _native_runtime(native_case, tmp_path, name="tool-limit")
    cell = {**_cell(arm="Agent-No-EVAS"), "family_id": "001"}
    run = run_prepared_native_mini_swe(
        runtime=runtime, cell=cell, client=Provider(["pwd", "pwd"]), attempt_id="limited",
        evas_command=arguments["evas_command"], final_judge_command=arguments["command"],
        allow_insecure_test_sandbox=True, episode_backend="native-reasoning",
        model_call_limit=3, tool_call_limit=1, campaign_file_sha256="c" * 64,
    )
    events = read_trajectory(run.trajectory_path)
    assert len([event for event in events if event["event_type"] == "environment_observed"
                and event["payload"]["tool_name"] == "bash"]) == 1
    row = read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)
    assert row["tool_call_limit"] == 1


def test_reviewed_docs_join_native_score_without_synthetic_label(native_case, tmp_path):  # noqa: F811
    from run_native_mini_swe import run_prepared_native_mini_swe
    from test_agent_harness_native_conditions import _cell, _native_runtime
    from test_agent_harness_native_launcher import Provider
    from test_agent_harness_reviewed_docs import _write_reviewed_corpus
    from score_campaign import read_native_cell
    arguments, _, _ = native_case
    runtime = _native_runtime(native_case, tmp_path, name="reviewed-score")
    (runtime / "public/submission/model.va").write_text("module model; endmodule\n")
    cell = {**_cell(arm="Agent-No-EVAS"), "family_id": "001"}
    docs = _write_reviewed_corpus(tmp_path)
    client = Provider(["unused", "vabench-submit"])
    original = client.complete

    def complete(*args, **kwargs):
        reply = original(*args, **kwargs)
        if len(client.requests) == 1:
            reply["choices"][0]["message"]["tool_calls"][0]["function"].update(
                name="vaevas_docs_search", arguments=json.dumps({"query": "resistor"}))
        return reply

    client.complete = complete
    run_prepared_native_mini_swe(
        runtime=runtime, cell=cell, client=client, attempt_id="reviewed",
        evas_command=arguments["evas_command"], final_judge_command=arguments["command"],
        allow_insecure_test_sandbox=True, episode_backend="native-reasoning",
        model_call_limit=2, docs_corpus=docs, campaign_file_sha256="c" * 64,
    )
    row = read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)
    assert row["extensions"]["offline_docs"]["intervention"] == "reviewed-local-docs-v2"
    assert "LOCAL_DOC" in json.dumps(client.requests[-1])


@pytest.mark.parametrize("backend", ["legacy", "native-mini-swe", "unknown"])
def test_combined_does_not_silently_change_legacy_protocol(tmp_path, backend):
    with pytest.raises(ValueError, match="backend"):
        prepared(tmp_path, backend=backend)


@pytest.mark.parametrize("drift", ["hash", "cap", "source", "corpus"])
def test_live_drift_rejects_before_keys_or_http(tmp_path, monkeypatch, drift):
    module, root, manifest, docs = prepared(tmp_path, live=True)
    digest = module.file_sha256(root / "combined-manifest.json")
    cap = "5.00"
    if drift == "hash":
        digest = "f" * 64
    elif drift == "cap":
        cap = "0.01"
    elif drift == "source":
        monkeypatch.setattr(module, "source_identity", lambda repo: {})
    else:
        docs._profile["builder"] = "changed"
    monkeypatch.setattr(module.live_transport, "load_pilot_key", lambda *a: pytest.fail("key read"))
    with pytest.raises(ValueError):
        module.execute_live(
            root, docs_corpus=docs, expected_manifest_sha256=digest,
            approved_cap=cap, currency="CNY", credential_file=tmp_path / "absent",
            evas_command="unused",
        )
    assert not (root / "live-authorization.json").exists()
    assert not (root / "budget.jsonl").exists()


def test_cli_inspect_and_run_requires_explicit_fee_assertion(tmp_path, capsys):
    module, root, _, _ = prepared(tmp_path)
    assert module.main(["inspect", "--output-root", str(root)]) == 0
    assert json.loads(capsys.readouterr().out)["live_authorized"] is False
    with pytest.raises(SystemExit) as missing:
        module.main(["run", "--output-root", str(root)])
    assert missing.value.code == 2
    assert not (root / "live-authorization.json").exists()


def test_reviewed_local_only_corpus_rejects_live_preparation_before_keys(tmp_path, monkeypatch):
    from test_agent_harness_reviewed_docs import _write_reviewed_corpus
    module = importlib.import_module("run_combined_tools")
    docs = _write_reviewed_corpus(tmp_path)
    assert docs.profile["review"]["external_provider_allowed"] is False
    monkeypatch.setattr(module.live_transport, "load_pilot_key", lambda *a: pytest.fail("key read"))
    with pytest.raises(PermissionError):
        module.freeze_combined(
            tmp_path / "denied", backend="evolution", family_id="001", form="dut", docs_corpus=docs,
            image_id="sha256:" + "a" * 64, branch_image_id="sha256:" + "b" * 64,
            evas_identity={"available": True}, currency="CNY", cap="5.00", live=True)
    assert not (tmp_path / "denied").exists()


def test_shared_transport_guard_independently_enforces_all_round_call_cap(tmp_path, monkeypatch):
    module, root, manifest, docs = prepared(tmp_path)
    import run_native_evolution
    from run_legacy_native_comparison import _ScriptedComparisonClient
    sent = []

    def response(key, payload):
        sent.append(key)
        event = {"id": "guard-test", "model": module.MODEL, "choices": [{
            "finish_reason": "stop", "delta": {"content": "done"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}
        return subprocess.CompletedProcess([], 0, "data: " + json.dumps(event) + "\n\ndata: [DONE]\n", "")

    def regressed_controller(**kwargs):
        # Deliberately overcall below the controller to test the independent guard.
        client = kwargs["branches"][0].client_factory()
        for _ in range(17):
            client.complete([], module.MAX_OUTPUT_TOKENS, [])

    monkeypatch.setattr(run_native_evolution, "run_native_evolution", regressed_controller)
    module._execute(root, manifest, docs_corpus=docs, evas_command="synthetic-unused",
                    client_factory=lambda **kw: _ScriptedComparisonClient(**kw, scripted_response=response))
    journal = [json.loads(line) for line in (root / "budget.jsonl").read_text().splitlines()]
    assert journal[0]["model_call_limit_per_cell"] == 16
    assert len(sent) == 16
    assert journal[-1]["event"] == "cell_stopped"


@pytest.mark.parametrize("fault", ["authorization", "preflight", "campaign", "start", "budget"])
def test_rehashed_terminal_metadata_still_requires_semantic_binding(tmp_path, monkeypatch, fault):
    module, root, manifest, docs = prepared(tmp_path, live=True)
    import run_native_evolution
    module._atomic_once(root / "live-authorization.json", {
        "schema_version": "vaevas-combined-live-authorization-v1",
        "manifest_sha256": module.file_sha256(root / "combined-manifest.json"),
        "approved_cap": "5.00", "currency": "CNY",
        "authority": "operator_assertion_not_authenticated_identity",
    })
    module._atomic_once(root / "provider-preflight.json", {
        "currency": "CNY", "model_available": True,
        "response_sha256": {"/models": "a" * 64, "/user/balance": "b" * 64},
    })

    def stopped(**kwargs):
        raise RuntimeError("synthetic pre-model engine failure")

    monkeypatch.setattr(run_native_evolution, "run_native_evolution", stopped)
    result = module._execute(root, manifest, docs_corpus=docs, evas_command="synthetic-unused",
                             client_factory=lambda **kw: pytest.fail("unexpected model"))
    assert result["disposition"] == "incomplete_evidence"
    filename, field, value = {
        "authorization": ("live-authorization.json", "approved_cap", "0.01"),
        "preflight": ("provider-preflight.json", "currency", "USD"),
        "campaign": ("campaign.json", "rounds", 9),
        "start": ("execution-start.json", "manifest_sha256", "f" * 64),
        "budget": ("budget.jsonl", "model_call_limit_per_cell", None),
    }[fault]
    path = root / filename
    document = json.loads(path.read_text())
    document[field] = value
    path.chmod(0o600)
    path.write_text(json.dumps(document) + "\n")
    execution_path = root / "execution.json"
    execution = json.loads(execution_path.read_text())
    execution["files"][filename] = module.file_sha256(path)
    execution_path.chmod(0o600)
    execution_path.write_text(json.dumps(execution))
    with pytest.raises(ValueError):
        module.read_combined(root)


@pytest.mark.parametrize("mode, expected_sent", [("insufficient", 0), ("unknown_usage", 1)])
def test_combined_budget_failure_stops_before_extra_transport(tmp_path, monkeypatch, mode, expected_sent):
    module, root, manifest, docs = prepared(tmp_path, cap="0.01" if mode == "insufficient" else "5.00")
    import run_native_evolution
    from run_legacy_native_comparison import _ScriptedComparisonClient
    sent = []

    def response(key, payload):
        sent.append(key)
        return subprocess.CompletedProcess([], 0, "data: [DONE]\n", "")

    def controller(**kwargs):
        for branch in kwargs["branches"]:
            try:
                branch.client_factory().complete([], module.MAX_OUTPUT_TOKENS, [])
            except module.PilotBudgetStop:
                pass

    monkeypatch.setattr(run_native_evolution, "run_native_evolution", controller)
    report = module._execute(
        root, manifest, docs_corpus=docs, evas_command="synthetic-unused",
        client_factory=lambda **kw: _ScriptedComparisonClient(**kw, scripted_response=response))
    assert len(sent) == expected_sent
    assert report["disposition"] == "budget_censored"
    assert report["score"] is None
    assert not report["combined_acceptance_passed"]
    assert report["cost"]["transport_reservations"] == expected_sent


@pytest.mark.parametrize("backend,live", [("native-reasoning", False), ("evolution", False), ("evolution", True)])
def test_real_docker_combined_tools_and_readonly_report(tmp_path, monkeypatch, backend, live):
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in actual Docker/EVAS with synthetic model replies only")
    module = importlib.import_module("run_combined_tools")
    from scripts import run_v4_r53_clean_room_smoke as smoke
    from runners.agent_harness.batch_resume import docker_image_identity
    evas, identity = smoke.resolve_evas_command(str(ROOT / ".venv/bin/evas"))
    docs = corpus(tmp_path)
    root = tmp_path / "combined"
    manifest = module.freeze_combined(
        root, backend=backend, family_id="001", form="dut", docs_corpus=docs,
        image_id=docker_image_identity(smoke.DEFAULT_EVAS_IMAGE),
        branch_image_id=docker_image_identity(smoke.DEFAULT_NO_EVAS_IMAGE),
        evas_identity=identity, currency="CNY", cap="5.00", live=live,
    )
    artifacts = smoke.public_stub_artifacts(smoke.public_contract(smoke.DEFAULT_RELEASE, "v4-001"))
    write = " && ".join(f"printf %s {shlex.quote(text)} > public/submission/{name}"
                        for name, text in artifacts.items())
    sequence = [("vaevas_docs_search", {"query": "analog contribution"}), ("bash", {"command": write})]
    if backend == "native-reasoning":
        sequence.append(("vaevas_public_simulate", {}))
    sequence.append(("bash", {"command": "vabench-submit"}))
    calls = dict.fromkeys(manifest["budget_ids"], 0)
    seen = []

    def response(key, payload):
        index = calls[key]
        calls[key] += 1
        name, arguments = sequence[index % len(sequence)]
        seen.append(payload)
        event = {"id": f"reply-{key}-{index}", "model": module.MODEL, "choices": [{
            "finish_reason": "tool_calls", "delta": {"tool_calls": [{
                "index": 0, "id": f"tool-{key}-{index}", "type": "function",
                "function": {"name": name, "arguments": json.dumps(arguments)},
            }]}}], "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}}
        return subprocess.CompletedProcess([], 0, "data: " + json.dumps(event) + "\n\ndata: [DONE]\n", "")

    if live:
        original_run = subprocess.run

        def external(argv, **kwargs):
            if not isinstance(argv, list) or argv[0] != "curl":
                return original_run(argv, **kwargs)
            assert module.live_transport.ENDPOINT in argv
            reservation = json.loads((root / "budget.jsonl").read_text().splitlines()[-1])
            assert reservation["event"] == "reserved"
            payload = json.loads(Path(argv[argv.index("--data-binary") + 1][1:]).read_text())
            return response(reservation["cell_id"], payload)

        monkeypatch.setattr(subprocess, "run", external)
        monkeypatch.setattr(module.live_transport, "provider_preflight", lambda key: {
            "currency": "CNY", "model_available": True,
            "response_sha256": {"/models": "a" * 64, "/user/balance": "b" * 64},
        })
        with tempfile.TemporaryDirectory(prefix="vaevas-combined-synthetic-key-") as key_root:
            key_file = Path(key_root) / "key.env"
            key_file.write_text('DEEPSEEK_API_KEY="synthetic-combined-key"\n')
            key_file.chmod(0o600)
            report = module.execute_live(
                root, docs_corpus=docs, evas_command=evas, credential_file=key_file,
                expected_manifest_sha256=module.file_sha256(root / "combined-manifest.json"),
                approved_cap="5.00", currency="CNY",
            )
    else:
        report = module.execute_fixture(root, docs_corpus=docs, evas_command=evas, scripted_response=response)
    assert report["disposition"] == "completed", report
    assert report["score"] is not None, report
    assert report["combined_acceptance_passed"], report
    use = report["feature_use"]["features"]
    assert use["offline_docs"]["succeeded"] == (4 if backend == "evolution" else 1)
    assert use["public_waveform"]["succeeded"] == (4 if backend == "evolution" else 1)
    assert report["cost"]["model_calls"] == len(seen)
    assert report["paid_requests"] is None if live else report["paid_requests"] == 0
    if backend == "evolution":
        assert use["public_waveform"]["feedback_exposed_requests"] > 0
    monkeypatch.setattr(module, "_execute", lambda *a, **k: pytest.fail("report executed engine"))
    assert module.read_combined(root) == report
    with pytest.raises(ValueError, match="resume|fixture entry"):
        module.execute_fixture(root, docs_corpus=docs, evas_command=evas, scripted_response=response)
    evidence = root / "run" / ("final-result.json" if backend == "evolution"
                                else "evidence/native-launcher/result.json")
    evidence.chmod(0o600)
    evidence.write_text("{}")
    with pytest.raises(ValueError, match="drift"):
        module.read_combined(root)
