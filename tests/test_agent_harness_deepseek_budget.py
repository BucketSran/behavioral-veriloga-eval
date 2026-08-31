"""Free HTTP-boundary tests for the separately budgeted DeepSeek pilot."""

import importlib
import json
from pathlib import Path
import subprocess
import sys
from decimal import Decimal

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"))


def test_insufficient_reservation_sends_no_http_request(tmp_path, monkeypatch):
    pilot = importlib.import_module("deepseek_budget")
    requests = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: requests.append(a))
    with pilot.DeepSeekPilotBudget(tmp_path / "spend.jsonl", cell_ids=["cell-a"], cap="0.01") as budget:
        client = pilot.BudgetedDeepSeekClient(budget=budget, cell_id="cell-a", api_key="fixture")
        with pytest.raises(pilot.PilotBudgetStop, match="reservation"):
            client.complete([{"role": "user", "content": "hello"}], 4096, [])
    assert requests == []
    records = [json.loads(line) for line in (tmp_path / "spend.jsonl").read_text().splitlines()]
    assert records[-1]["event"] == "stopped"
    assert records[-1]["committed_upper_bound"] == "0"


def _stream(usage=None, *, done=True, model="deepseek-v4-flash"):
    chunk = {"id": "fixture-response", "model": model, "choices": [{
        "delta": {"content": "ok"}, "finish_reason": "stop",
    }], "usage": usage}
    return "data: " + json.dumps(chunk) + "\n\n" + ("data: [DONE]\n\n" if done else "")


def test_actual_payload_and_durable_reservation_then_conservative_reconciliation(tmp_path, monkeypatch):
    pilot = importlib.import_module("deepseek_budget")
    path = tmp_path / "spend.jsonl"
    payloads = []

    def http(argv, **kwargs):
        payloads.append(json.loads(Path(argv[argv.index("--data-binary") + 1][1:]).read_text()))
        assert json.loads(path.read_text().splitlines()[-1])["event"] == "reserved"
        return subprocess.CompletedProcess(argv, 0, _stream({
            "prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11,
            "prompt_cache_hit_tokens": 10, "prompt_cache_miss_tokens": 0,
        }), "")

    monkeypatch.setattr(subprocess, "run", http)
    with pilot.DeepSeekPilotBudget(path, cell_ids=["cell-a", "cell-b"]) as budget:
        for cell in ("cell-a", "cell-b"):
            client = pilot.BudgetedDeepSeekClient(budget=budget, cell_id=cell, api_key="fixture-secret")
            response = client.complete([{"role": "user", "content": "private-fixture"}], 4096, [])
            assert response["choices"][0]["message"]["content"] == "ok"
        assert budget.committed == Decimal("0.000078")  # All input at peak/miss, not cache-hit price.
    assert len(payloads) == 2
    assert all(payload["thinking"] == {"type": "disabled"} for payload in payloads)
    assert all(payload["stream_options"] == {"include_usage": True} for payload in payloads)
    assert all(payload["max_tokens"] == 4096 and payload["model"] == pilot.MODEL for payload in payloads)
    assert "fixture-secret" not in path.read_text() and "private-fixture" not in path.read_text()


@pytest.mark.parametrize("usage", [
    None,
    {"prompt_tokens": 10, "completion_tokens": True, "total_tokens": 11},
    {"prompt_tokens": -1, "completion_tokens": 1, "total_tokens": 0},
    {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 999},
    {"prompt_tokens": 10, "completion_tokens": 5000, "total_tokens": 5010},
    {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11,
     "prompt_cache_hit_tokens": 30, "prompt_cache_miss_tokens": 0},
    {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11,
     "completion_tokens_details": {"reasoning_tokens": 1}},
])
def test_ambiguous_usage_keeps_reservation_and_stops_all_cells(tmp_path, monkeypatch, usage):
    pilot = importlib.import_module("deepseek_budget")
    sent = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k:
        (sent.append(a) or subprocess.CompletedProcess([], 0, _stream(usage), "")))
    with pilot.DeepSeekPilotBudget(tmp_path / "spend.jsonl", cell_ids=["a", "b"]) as budget:
        a = pilot.BudgetedDeepSeekClient(budget=budget, cell_id="a", api_key="fixture")
        b = pilot.BudgetedDeepSeekClient(budget=budget, cell_id="b", api_key="fixture")
        with pytest.raises(pilot.PilotBudgetStop):
            a.complete([], 4096, [])
        with pytest.raises(pilot.PilotBudgetStop):
            b.complete([], 4096, [])
        assert budget.committed == Decimal("3.182592")
    assert len(sent) == 1


@pytest.mark.parametrize("body", [
    _stream({"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11}, done=False),
    _stream({"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11}, model="deepseek-v4-pro"),
    _stream({"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11}).replace('"stop"', "null"),
    _stream({"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11}) + 'data: {}\n',
])
def test_truncated_or_mismatched_response_never_refunds_reservation(tmp_path, monkeypatch, body):
    pilot = importlib.import_module("deepseek_budget")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 0, body, ""))
    with pilot.DeepSeekPilotBudget(tmp_path / "spend.jsonl", cell_ids=["a"]) as budget:
        client = pilot.BudgetedDeepSeekClient(budget=budget, cell_id="a", api_key="fixture")
        with pytest.raises(pilot.PilotBudgetStop):
            client.complete([], 4096, [])
        assert budget.committed == Decimal("3.182592")


@pytest.mark.parametrize("limit", [1, 5, 8, 11])
def test_call_limit_cannot_reset_with_a_fresh_client(tmp_path, monkeypatch, limit):
    pilot = importlib.import_module("deepseek_budget")
    sent = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k:
        (sent.append(a) or subprocess.CompletedProcess([], 0, _stream({
            "prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11,
        }), "")))
    with pilot.DeepSeekPilotBudget(tmp_path / "spend.jsonl", cell_ids=["a", "b"],
                                  model_call_limit=limit) as budget:
        for _ in range(limit):
            pilot.BudgetedDeepSeekClient(budget=budget, cell_id="a", api_key="fixture").complete([], 10, [])
        with pytest.raises(pilot.PilotBudgetStop, match="model-call"):
            pilot.BudgetedDeepSeekClient(budget=budget, cell_id="a", api_key="fixture").complete([], 10, [])
        # A cell-local call ceiling does not discard other scheduled cells.
        pilot.BudgetedDeepSeekClient(budget=budget, cell_id="b", api_key="fixture").complete([], 10, [])
    assert len(sent) == limit + 1


def test_transport_failure_stops_before_inherited_retry_can_spend(tmp_path, monkeypatch):
    pilot = importlib.import_module("deepseek_budget")
    sent = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k:
        (sent.append(a) or subprocess.CompletedProcess([], 7, "", "unreachable")))
    events = []
    with pilot.DeepSeekPilotBudget(tmp_path / "spend.jsonl", cell_ids=["a"]) as budget:
        client = pilot.BudgetedDeepSeekClient(budget=budget, cell_id="a", api_key="fixture")
        with pytest.raises(pilot.PilotBudgetStop, match="unknown"):
            client.complete([], 4096, [], transport_observer=events.append)
        assert budget.committed == Decimal("3.182592")
    assert len(sent) == 1
    assert len(events) == 1 and events[0]["transport_attempt"] == 1


@pytest.mark.parametrize("cap,currency", [("5.01", "CNY"), ("0.71", "USD"), ("0", "CNY"), ("NaN", "CNY")])
def test_cannot_expand_authorized_spending_ceiling(tmp_path, cap, currency):
    pilot = importlib.import_module("deepseek_budget")
    with pytest.raises(ValueError):
        pilot.DeepSeekPilotBudget(tmp_path / "spend.jsonl", cell_ids=["a"], cap=cap, currency=currency)
    assert not (tmp_path / "spend.jsonl").exists()


def test_existing_journal_cannot_be_overwritten_or_resumed(tmp_path):
    pilot = importlib.import_module("deepseek_budget")
    path = tmp_path / "spend.jsonl"
    with pilot.DeepSeekPilotBudget(path, cell_ids=["a"]):
        pass
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        pilot.DeepSeekPilotBudget(path, cell_ids=["a"])
    assert path.read_bytes() == before
    assert path.stat().st_mode & 0o777 == 0o600


def test_reservation_persistence_failure_prevents_http(tmp_path, monkeypatch):
    pilot = importlib.import_module("deepseek_budget")
    sent = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: sent.append(a))
    with pilot.DeepSeekPilotBudget(tmp_path / "spend.jsonl", cell_ids=["a"]) as budget:
        def disk_failure(*args):
            raise OSError("fixture disk failure")
        monkeypatch.setattr(pilot.os, "fsync", disk_failure)
        client = pilot.BudgetedDeepSeekClient(budget=budget, cell_id="a", api_key="fixture")
        with pytest.raises(OSError, match="disk failure"):
            client.complete([], 4096, [])
        with pytest.raises(pilot.PilotBudgetStop):
            client.complete([], 4096, [])
    assert not sent


def test_explicit_unlimited_calls_keeps_shared_spending_admission(tmp_path, monkeypatch):
    pilot = importlib.import_module("deepseek_budget")
    sent = []
    replies = iter([_stream({"prompt_tokens": 10, "completion_tokens": 1,
                              "total_tokens": 11})] * 9 + [_stream(None)])
    monkeypatch.setattr(subprocess, "run", lambda *a, **k:
        (sent.append(a) or subprocess.CompletedProcess([], 0, next(replies), "")))
    path = tmp_path / "spend.jsonl"
    with pilot.DeepSeekPilotBudget(path, cell_ids=["legacy", "native"],
                                  model_call_limit=None) as budget:
        client = pilot.BudgetedDeepSeekClient(budget=budget, cell_id="legacy", api_key="fixture")
        for _ in range(9):
            client.complete([], 4096, [])
        other = pilot.BudgetedDeepSeekClient(budget=budget, cell_id="native", api_key="fixture")
        with pytest.raises(pilot.PilotBudgetStop, match="unknown"):
            other.complete([], 4096, [])
        with pytest.raises(pilot.PilotBudgetStop):
            client.complete([], 4096, [])
        assert budget.model_calls == {"legacy": 9, "native": 1}
        assert budget.committed == Decimal("3.182943")
    assert len(sent) == 10
    assert json.loads(path.read_text().splitlines()[0])["model_call_limit_per_cell"] is None


@pytest.mark.parametrize("watchdog", [120, 1800])
def test_comparison_watchdog_reaches_transport_without_changing_pilot_default(tmp_path, monkeypatch, watchdog):
    pilot = importlib.import_module("deepseek_budget")
    observed = []

    def http(argv, **kwargs):
        observed.append(float(argv[argv.index("--max-time") + 1]))
        return subprocess.CompletedProcess(argv, 0, _stream({
            "prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11,
        }), "")

    monkeypatch.setattr(subprocess, "run", http)
    with pilot.DeepSeekPilotBudget(tmp_path / "spend.jsonl", cell_ids=["a"]) as budget:
        options = {} if watchdog == 120 else {"timeout_s": watchdog}
        client = pilot.BudgetedDeepSeekClient(budget=budget, cell_id="a", api_key="fixture", **options)
        assert client.timeout_s == watchdog
        client.complete([], 4096, [])
    assert observed == [watchdog]


@pytest.mark.parametrize("watchdog", [True, 0, -1, float("nan"), float("inf"), "1800",
                                      pytest.param(10**1000, id="overflow")])
def test_invalid_watchdog_is_rejected_before_any_call(tmp_path, watchdog):
    pilot = importlib.import_module("deepseek_budget")
    with pilot.DeepSeekPilotBudget(tmp_path / "spend.jsonl", cell_ids=["a"]) as budget:
        with pytest.raises(ValueError, match="timeout"):
            pilot.BudgetedDeepSeekClient(budget=budget, cell_id="a", api_key="fixture", timeout_s=watchdog)
        assert budget.model_calls == {"a": 0}
