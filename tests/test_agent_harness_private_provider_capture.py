"""Private transport evidence separates HTTP attempts from model decisions."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"))
import run_campaign as runner  # noqa: E402
from run_native_mini_swe import _RecordedClient  # noqa: E402
from runners.agent_harness import EpisodeContext  # noqa: E402


@pytest.mark.parametrize("stream", [False, True])
def test_transport_retries_are_private_and_join_one_logical_request(monkeypatch, stream):
    response = {"id": "response-1", "choices": [{"message": {"role": "assistant", "content": "ok"}}]}
    content = (
        'data: {"id":"response-1","choices":[{"delta":{"content":"ok"}}]}\n\ndata: [DONE]\n'
        if stream else json.dumps(response)
    )
    results = iter([
        subprocess.CompletedProcess([], 7, "", "network unavailable token-secret"),
        subprocess.CompletedProcess([], 0, content, ""),
    ])
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **k: next(results))
    monkeypatch.setattr(runner.time, "sleep", lambda _: None)
    client = runner.OpenAICompatible(base_url="https://fixture.invalid", model="fixture",
        api_key="token-secret", timeout_s=10, temperature=0, stream=stream)
    events = []
    wrapped = _RecordedClient(client, lambda kind, payload: events.append((kind, payload)),
        EpisodeContext("cell", "attempt", "task", "Agentic", None))
    wrapped.complete([{"role": "user", "content": "public task"}], 10, [])
    assert [kind for kind, _ in events].count("provider_request") == 1
    assert [kind for kind, _ in events].count("provider_response") == 1
    transport = [payload for kind, payload in events if kind == "provider_transport_attempt"]
    assert [event["transport_attempt"] for event in transport] == [1, 2]
    assert [event["returncode"] for event in transport] == [7, 0]
    assert all(event["request_id"] == "attempt/request-0001" for event in transport)
    assert transport[-1]["stdout"]["bytes_sha256"] == hashlib.sha256(content.encode()).hexdigest()
    assert "token-secret" not in json.dumps(events)
    assert "Authorization" not in json.dumps(events)


def test_timeout_preserves_partial_transport_evidence(monkeypatch):
    def timeout(*a, **k):
        raise subprocess.TimeoutExpired("curl", 1, output=b"partial", stderr=b"network")
    monkeypatch.setattr(runner.subprocess, "run", timeout)
    client = runner.OpenAICompatible(base_url="https://fixture.invalid", model="fixture",
        api_key="", timeout_s=1, temperature=0)
    events = []
    wrapped = _RecordedClient(client, lambda kind, payload: events.append((kind, payload)),
        EpisodeContext("cell", "attempt", "task", "Agentic", None))
    with pytest.raises(RuntimeError):
        wrapped.complete([], 10, [])
    attempt = next(payload for kind, payload in events if kind == "provider_transport_attempt")
    assert attempt["capture_complete"] is False
    assert attempt["stdout"]["text"] == "partial"
    assert events[-1][0] == "provider_failure"


def test_cli_module_identity_does_not_disable_transport_capture(monkeypatch):
    # Running run_campaign.py as __main__ creates a distinct Python class from
    # the launcher's imported run_campaign module; this is still the same adapter.
    spec = importlib.util.spec_from_file_location("campaign_cli_identity", runner.__file__)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    client = module.OpenAICompatible(base_url="https://fixture.invalid", model="fixture",
        api_key="", timeout_s=1, temperature=0)
    assert not isinstance(client, runner.OpenAICompatible)
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k:
        subprocess.CompletedProcess([], 0, '{"choices":[]}', ""))
    events = []
    wrapped = _RecordedClient(client, lambda kind, payload: events.append((kind, payload)),
        EpisodeContext("cell", "attempt", "task", "Agentic", None))
    wrapped.complete([], 10, [])
    assert events[0][1]["transport_capture_supported"] is True
    assert [kind for kind, _ in events].count("provider_transport_attempt") == 1
