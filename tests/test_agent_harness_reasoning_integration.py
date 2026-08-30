"""Distinct reasoning policy must traverse the production controller and judge."""

import json
import subprocess
import sys

import pytest

from test_agent_harness_attempt_integration import attempt_case as attempt_case  # noqa: F401
from test_agent_harness_native_episode import native_case as native_case  # noqa: F401
from test_agent_harness_production_public_validation import public_case as public_case  # noqa: F401
from test_agent_harness_native_launcher import Provider
from test_agent_harness_native_campaign_dispatch import WRAPPER
import run_campaign as runner
import score_campaign as scorer
from test_agent_harness_native_conditions import _cell, _native_runtime


@pytest.mark.parametrize("backend,proposal_format", [
    ("native-mini-swe", "native_tool_calls"),
    ("native-reasoning", "native_tool_calls"),
    ("native-reasoning", "strict_json"),
])
@pytest.mark.parametrize("arm", ["Agentic", "Agent-No-EVAS"])
def test_interactive_request_explains_actual_shell_authority(
    native_case, tmp_path, backend, proposal_format, arm,  # noqa: F811
):
    from run_native_mini_swe import run_prepared_native_mini_swe

    arguments, _, _ = native_case
    runtime = _native_runtime(native_case, tmp_path, name="contract-runtime")
    client = Provider(["true"])
    original = client.complete

    def complete(messages, max_tokens, tools, **kwargs):
        response = original(messages, max_tokens, tools, **kwargs)
        if proposal_format == "strict_json":
            message = response["choices"][0]["message"]
            call = message.pop("tool_calls")[0]["function"]
            message["content"] = json.dumps({
                "tool_name": call["name"], "arguments": json.loads(call["arguments"]),
            })
        return response

    client.complete = complete
    run_prepared_native_mini_swe(
        runtime=runtime, cell=_cell(arm=arm), client=client, attempt_id="contract",
        evas_command=arguments["evas_command"], final_judge_command=arguments["command"],
        allow_insecure_test_sandbox=True, episode_backend=backend,
        reasoning_proposal_format=proposal_format,
    )
    initial = json.dumps(client.requests[0])
    assert "vabench_bash_contract" in initial
    assert "vabench-submit" in initial
    assert "public/submission/" in initial
    assert "/workspace" in initial
    assert "Each command starts" in initial
    assert "exactly one bash action" in initial
    assert "at least one bash tool call" not in initial
    assert "FINAL_JUDGE_SENTINEL" not in json.dumps(client.requests)
    if arm == "Agent-No-EVAS":
        assert "EVAS execution is not available" in initial
        assert "real, pinned executable" not in initial
        assert "evas_runtime.json" not in initial
    else:
        assert "evas_runtime.json" in initial
        assert "real, pinned executable" in initial


@pytest.mark.parametrize("proposal_format", ["native_tool_calls", "strict_json"])
def test_reasoning_runs_real_native_pipeline_and_readonly_score(attempt_case, proposal_format):  # noqa: F811
    cell, args = attempt_case
    args.episode_backend = "native-reasoning"
    args.native_max_attempts = 1
    args.reasoning_proposal_format = proposal_format
    client = Provider([
        "printf 'module model; endmodule\\n' > public/submission/model.va",
        "vabench-submit",
    ])
    requests = []
    original = client.complete

    def complete(messages, max_tokens, tools, **kwargs):
        requests.append((messages, tools))
        response = original(messages, max_tokens, tools, **kwargs)
        if proposal_format == "strict_json":
            message = response["choices"][0]["message"]
            call = message.pop("tool_calls")[0]["function"]
            message["content"] = json.dumps({
                "tool_name": call["name"], "arguments": json.loads(call["arguments"]),
            })
        return response

    client.complete = complete
    result = runner.run_cell_preserving_failure(cell, args, client)
    assert result["backend"] == "native-reasoning"
    assert result["status"] == "behavior_failure"
    assert len(requests) == 2
    assert "reasoning backend" in requests[0][0][0]["content"]
    initial_request = json.dumps(requests[0][0])
    assert "vabench_bash_contract" in initial_request
    assert "vabench-submit" in initial_request
    assert "public/submission/" in initial_request
    assert bool(requests[0][1]) == (proposal_format == "native_tool_calls")
    runtime = args.output / cell["cell_id"]
    row = scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)
    assert row["backend"] == "native-reasoning"
    assert row["telemetry"]["model_calls"] == 2
    manifest = runner.read_json(runtime / "evidence/native-launcher/manifest.json")
    assert manifest["backend_profile"]["backend_family"] == "alphaapollo_reasoning"
    assert manifest["backend_profile"]["preferred_proposal_format"] == proposal_format
    assert "reasoning_policy.py" in manifest["source_sha256"]
    assert len(requests) == 2


def test_reasoning_wrapper_freezes_and_forwards_format(tmp_path):
    output = tmp_path / "reasoning"
    completed = subprocess.run([
        sys.executable, str(WRAPPER), "--output-root", str(output),
        "--model", "fixture-model", "--task-id", "v4-001", "--form", "dut",
        "--comparison-profile", "executable-feedback-control", "--dry-run",
        "--episode-backend", "native-reasoning",
        "--reasoning-proposal-format", "strict_json",
    ], text=True, capture_output=True, timeout=60, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    campaign = runner.read_json(output / "campaign.json")
    assert campaign["execution_config"]["episode_backend"] == "native-reasoning"
    assert campaign["execution_config"]["reasoning_proposal_format"] == "strict_json"


def test_score_rejects_proposal_format_different_from_frozen_campaign(tmp_path, monkeypatch):
    campaign_path = tmp_path / "campaign.json"
    cell = {"cell_id": "cell", "experimental_arm": "Agentic"}
    campaign_path.write_text(json.dumps({
        "cells": [cell], "execution_config": {
            "episode_backend": "native-reasoning", "reasoning_proposal_format": "strict_json",
        },
    }))
    monkeypatch.setattr(scorer, "read_native_cell", lambda *a, **k: {
        **cell, "backend": "native-reasoning", "proposal_format": "native_tool_calls",
    })
    monkeypatch.setattr(scorer, "summarize", lambda *a, **k: {})
    monkeypatch.setattr(sys, "argv", [
        "score_campaign.py", "--campaign-output", str(tmp_path),
        "--campaign", str(campaign_path), "--episode-backend", "native-reasoning",
        "--judge-kind", "final_trusted_replay", "--output", str(tmp_path / "score.json"),
    ])
    with pytest.raises(ValueError, match="proposal format"):
        scorer.main()
    assert not (tmp_path / "score.json").exists()
