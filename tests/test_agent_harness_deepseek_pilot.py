"""Pilot orchestration tests; no real provider credentials or paid requests."""

import importlib
import json
import os
from pathlib import Path
import shlex
import subprocess

import pytest

from scripts import run_v4_r53_clean_room_smoke as smoke  # noqa: F401


@pytest.mark.parametrize("currency", ["CNY", "USD"])
def test_metadata_only_preflight_is_bounded_and_redacted(monkeypatch, currency):
    pilot = importlib.import_module("run_deepseek_pilot")
    requested = []

    class Connection:
        def __init__(self, host, timeout):
            assert host == "api.deepseek.com" and timeout == 30

        def request(self, method, path, headers):
            assert method == "GET" and headers["Authorization"] == "Bearer fixture-key"
            requested.append(path)

        def getresponse(self):
            return self

        status = 200

        def read(self, limit):
            assert limit == 65537
            payload = ({"data": [{"id": "deepseek-v4-flash"}]}
                       if requested[-1] == "/models" else
                       {"is_available": True, "balance_infos": [
                           {"currency": currency, "total_balance": "42.00"}]})
            return json.dumps(payload).encode()

        def close(self):
            pass

    monkeypatch.setattr(pilot.http.client, "HTTPSConnection", Connection)
    result = pilot.provider_preflight("fixture-key")
    assert requested == ["/models", "/user/balance"]
    assert result["currency"] == currency and result["model_available"]
    assert "42.00" not in json.dumps(result)
    assert "fixture-key" not in json.dumps(result)


@pytest.mark.parametrize("status,body", [
    (401, b"fixture-key"), (302, b"fixture-key"), (200, b"x" * 65537),
    (200, b"not-json fixture-key"), (200, b"{}"),
], ids=["unauthorized", "redirect", "oversize", "invalid-json", "invalid-schema"])
def test_bad_metadata_never_starts_generation_or_echoes_response(monkeypatch, status, body):
    pilot = importlib.import_module("run_deepseek_pilot")

    class Connection:
        def __init__(self, *args, **kwargs):
            self.status = status

        def request(self, method, path, headers):
            assert method == "GET"

        def getresponse(self):
            return self

        def read(self, limit):
            return body

        def close(self):
            pass

    monkeypatch.setattr(pilot.http.client, "HTTPSConnection", Connection)
    with pytest.raises(ValueError, match="metadata preflight failed") as error:
        pilot.provider_preflight("fixture-key")
    assert "fixture-key" not in str(error.value)


@pytest.mark.parametrize("limit", [1, 8, 13])
def test_freeze_keeps_six_cells_order_bindings_and_refuses_resume(tmp_path, limit):
    pilot = importlib.import_module("run_deepseek_pilot")
    root = tmp_path / "pilot"
    manifest = pilot.freeze_pilot(
        root, preflight={"currency": "CNY", "model_available": True},
        image_id="sha256:" + "a" * 64, code_commit="b" * 40,
        evas_identity={"available": True, "version_output": "evas-sim 0.8.7"},
        model_call_limit=limit,
    )
    assert [(row["form"], row["backend"]) for row in manifest["schedule"]] == [
        ("dut", "native-mini-swe"), ("dut", "native-reasoning"),
        ("bugfix", "native-reasoning"), ("bugfix", "native-mini-swe"),
        ("testbench", "native-mini-swe"), ("testbench", "native-reasoning"),
    ]
    assert {row["family_id"] for row in manifest["schedule"]} == {"029"}
    assert len({row["pilot_cell_id"] for row in manifest["schedule"]}) == 6
    assert manifest["cap"] == "5.00" and manifest["native_max_attempts"] == 1
    assert manifest["model_calls_per_cell"] == limit
    for backend, binding in manifest["campaigns"].items():
        path = root / binding["path"]
        assert pilot.sha256(path) == binding["sha256"]
        campaign = json.loads(path.read_text())
        assert len(campaign["cells"]) == 3
        assert campaign["execution_config"]["episode_backend"] == backend
        assert campaign["execution_config"]["native_model_call_limit"] == limit
    before = {path: path.read_bytes() for path in root.rglob("*.json")}
    with pytest.raises(FileExistsError):
        pilot.freeze_pilot(root, preflight={}, image_id="", code_commit="", evas_identity={})
    assert before == {path: path.read_bytes() for path in root.rglob("*.json")}
    assert Path(root / "pilot-manifest.json").stat().st_mode & 0o777 == 0o600


def test_campaign_drift_keeps_six_unstarted_without_any_provider_or_native_call(tmp_path, monkeypatch):
    pilot = importlib.import_module("run_deepseek_pilot")
    root = tmp_path / "pilot"
    manifest = pilot.freeze_pilot(root, preflight={"currency": "CNY", "model_available": True},
                                 image_id="sha256:" + "a" * 64, code_commit="b" * 40,
                                 evas_identity={"available": True})
    (root / "native-mini-swe/campaign.json").write_text("{}")

    def forbidden(*args, **kwargs):
        pytest.fail("drift must stop before native execution or HTTP")

    monkeypatch.setattr(subprocess, "run", forbidden)
    result = pilot.execute_pilot(root, manifest, api_key="fixture-key", evas_command="unused")
    assert result["dispositions"] == {"not_started": 6}
    assert result["http_attempts"] == result["started_count"] == 0
    assert result["committed_upper_bound"] == "0"
    assert result["stop_reason"] == "pilot_execution_or_evidence_failure"


@pytest.mark.parametrize("failure_mode", ["none", "unknown-cost", "cell-limit"])
def test_pilot_real_docker_free_http_preserves_all_six_rows(tmp_path, monkeypatch, failure_mode):
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in real Docker/EVAS; provider HTTP is a free fixture")
    pilot = importlib.import_module("run_deepseek_pilot")
    image_id = subprocess.check_output(
        ["docker", "image", "inspect", "vabench-agent-runtime:0.8.7", "--format", "{{.Id}}"],
        text=True,
    ).strip()
    evas_command, identity = smoke.resolve_evas_command(str(smoke.ROOT / ".venv/bin/evas"))
    root = tmp_path / "pilot"
    limit = 5 if failure_mode == "cell-limit" else 8
    manifest = pilot.freeze_pilot(root, preflight={"currency": "CNY", "model_available": True},
                                 image_id=image_id, code_commit="b" * 40, evas_identity=identity,
                                 model_call_limit=limit)
    commands = []
    for index, row in enumerate(manifest["schedule"]):
        if index == 0 and failure_mode == "cell-limit":
            commands.extend(["true"] * limit)
            continue
        artifacts = smoke.public_stub_artifacts(smoke.public_contract(smoke.DEFAULT_RELEASE, row["task_id"]))
        commands.extend(["test ! -r /runtime/evaluator/check.py", *[
            f"printf %s {shlex.quote(content)} > public/submission/{name}"
            for name, content in artifacts.items()], "vabench-submit"])
    commands = iter(commands)
    requests = []
    real_run = subprocess.run

    def http_or_real(argv, **kwargs):
        assert "DEEPSEEK_API_KEY" not in os.environ and "GLM_API_KEY" not in os.environ
        if argv[0] != "curl":
            return real_run(argv, **kwargs)
        payload = json.loads(Path(argv[argv.index("--data-binary") + 1][1:]).read_text())
        assert payload["thinking"] == {"type": "disabled"}
        assert '"remaining_after_this_call"' in payload["messages"][-1]["content"]
        requests.append(payload)
        if failure_mode == "unknown-cost":
            return subprocess.CompletedProcess(argv, 28, "", "fixture timeout")
        number = len(requests)
        chunk = {"id": f"response-{number}", "model": pilot.MODEL,
                 "choices": [{"finish_reason": "tool_calls", "delta": {"tool_calls": [{
                     "index": 0, "id": f"call-{number}", "type": "function", "function": {
                         "name": "bash", "arguments": json.dumps({"command": next(commands)}),
                     },
                 }]}}], "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}}
        return subprocess.CompletedProcess(argv, 0, "data: " + json.dumps(chunk) + "\n\ndata: [DONE]\n", "")

    monkeypatch.setenv("DEEPSEEK_API_KEY", "fixture-key")
    monkeypatch.setenv("GLM_API_KEY", "unused-fixture-key")
    monkeypatch.setattr(subprocess, "run", http_or_real)
    result = pilot.execute_pilot(root, manifest, api_key="fixture-key", evas_command=evas_command)
    assert result["scheduled_count"] == len(result["rows"]) == 6
    assert result["budget_journal_sha256"] == pilot.sha256(root / "budget.jsonl")
    assert all("fixture-key" not in path.read_text() for path in root.glob("*.json*"))
    if failure_mode == "unknown-cost":
        assert len(requests) == 1
        assert result["dispositions"] == {"operationally_censored": 1, "not_started": 5}
        assert all(row["score"] is None for row in result["rows"])
        assert result["committed_upper_bound"] == "3.182592"
        assert result["rows"][0]["reason"] == "unknown_request_cost"
        assert all(not (root / row["runtime"]).exists() for row in result["rows"][1:])
    elif failure_mode == "cell-limit":
        assert result["dispositions"] == {"operationally_censored": 1, "completed": 5}
        assert result["rows"][0]["score"] is None
        assert result["rows"][0]["reason"] == "model_call_limit"
        assert result["rows"][0]["http_attempts"] == result["rows"][0]["model_calls"] == limit
        assert result["rows"][0]["native_evidence"]["model_call_budget"]["limit"] == limit
        assert result["stop_reason"] is None
    else:
        assert result["dispositions"] == {"completed": 6}
        assert all(row["native_evidence"] for row in result["rows"])
        assert all(row["score"] in (0, 1) for row in result["rows"])
        assert result["http_attempts"] == len(requests) <= 48
    before = len(requests)
    with pytest.raises(FileExistsError):
        pilot.execute_pilot(root, manifest, api_key="fixture-key", evas_command=evas_command)
    assert len(requests) == before
