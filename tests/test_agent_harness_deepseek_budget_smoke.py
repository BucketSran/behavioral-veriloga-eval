"""Free provider-boundary fixture through real native Docker/EVAS scoring."""

import importlib
import json
import os
import shlex
import subprocess

import pytest

from scripts import run_v4_r53_clean_room_smoke as smoke


@pytest.mark.parametrize("backend", ["native-mini-swe", "native-reasoning"])
def test_budgeted_client_reaches_native_freeze_and_evas_sidecar(tmp_path, monkeypatch, backend):
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in real Docker/EVAS; HTTP remains a free fixture")
    pilot = importlib.import_module("deepseek_budget")
    campaign = smoke.campaign_builder.build_campaign(
        smoke.DEFAULT_RELEASE, family_ids=["001"], model_provider="free-budget-fixture",
        model=pilot.MODEL, per_turn_max_tokens=4096, repetitions=1, three_arm_g0_g2=True,
    )
    cell = next(cell for cell in campaign["cells"]
                if cell["form"] == "dut" and cell["experimental_arm"] == "Agentic")
    campaign["cells"] = [cell]
    campaign["execution_config"] = {"episode_backend": backend, "workers": 1,
                                    "evidence_scope": "free_fixture_not_real_model"}
    campaign_path = tmp_path / "campaign.json"
    smoke.write_immutable_json(campaign_path, campaign)
    args = smoke.parse_args(["--output-root", str(tmp_path),
                             "--evas-command", str(smoke.ROOT / ".venv/bin/evas")])
    args.evas_command, identity = smoke.resolve_evas_command(args.evas_command)
    smoke.configure_runner_args(args, tmp_path / "run", identity)
    args.episode_backend = backend
    args.native_max_attempts = 1
    args.campaign_file_sha256 = smoke.sha256_file(campaign_path)
    artifacts = smoke.public_stub_artifacts(smoke.public_contract(smoke.DEFAULT_RELEASE, cell["task_id"]))
    commands = iter([
        "test ! -r /runtime/evaluator/check.py",
        *[f"printf %s {shlex.quote(content)} > public/submission/{name}"
          for name, content in artifacts.items()],
        "vabench-submit",
    ])
    real_run = subprocess.run
    requests = []

    def http_or_real(argv, **kwargs):
        if argv[0] != "curl":
            return real_run(argv, **kwargs)
        from pathlib import Path
        payload = json.loads(Path(argv[argv.index("--data-binary") + 1][1:]).read_text())
        assert payload["thinking"] == {"type": "disabled"}
        assert payload["model"] == pilot.MODEL
        requests.append(payload)
        number = len(requests)
        chunk = {
            "id": f"response-{number}", "model": pilot.MODEL,
            "choices": [{"finish_reason": "tool_calls", "delta": {"tool_calls": [{
                "index": 0, "id": f"call-{number}", "type": "function", "function": {
                    "name": "bash", "arguments": json.dumps({"command": next(commands)}),
                },
            }]}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }
        return subprocess.CompletedProcess(argv, 0, "data: " + json.dumps(chunk) + "\n\ndata: [DONE]\n", "")

    monkeypatch.setattr(subprocess, "run", http_or_real)
    with pilot.DeepSeekPilotBudget(tmp_path / "spend.jsonl", cell_ids=[cell["cell_id"]]) as budget:
        client = pilot.BudgetedDeepSeekClient(budget=budget, cell_id=cell["cell_id"], api_key="fixture-only")
        result = smoke.run_campaign.run_cell_preserving_failure(cell, args, client)
        assert result["status"] == "behavior_failure", result
        assert len(requests) <= 8
        assert budget.committed < budget.cap
    report = tmp_path / "SCORE.json"
    scored = real_run([
        str(smoke.ROOT / ".venv/bin/python"), str(smoke.CALIBRATION / "score_campaign.py"),
        "--campaign-output", str(args.output), "--campaign", str(campaign_path),
        "--episode-backend", backend, "--workers", "1", "--judge-kind", "final_trusted_replay",
        "--output", str(report),
    ], text=True, capture_output=True, timeout=60, check=False)
    assert scored.returncode == 0, scored.stdout + scored.stderr
    summary = smoke.read_json(report)
    assert summary["cell_count"] == 1
    assert summary["judge_statuses"] == {"behavior_failure": 1}
    assert summary["score_authority"] == "development_only"
    smoke.write_immutable_json(tmp_path / "budget-smoke-index.json", {
        "backend": backend, "paid_requests": 0, "fixture_http_attempts": len(requests),
        "claim_scope": "budgeted_transport_native_connectivity_only",
        "campaign_sha256": smoke.sha256_file(campaign_path),
        "journal_sha256": smoke.sha256_file(tmp_path / "spend.jsonl"),
        "score_report_sha256": smoke.sha256_file(report),
    })
