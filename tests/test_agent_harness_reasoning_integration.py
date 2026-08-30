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
def test_public_evas_process_failure_reaches_next_native_request(
    native_case, tmp_path, backend, proposal_format,  # noqa: F811
):
    from pathlib import Path
    from run_native_mini_swe import run_prepared_native_mini_swe

    arguments, _, _ = native_case
    executable = Path(arguments["evas_command"])
    executable.write_text(
        "#!/bin/bash\n"
        "if [[ $1 == --version ]]; then echo 'evas-sim 0.8.7 (test double)'; exit; fi\n"
        "echo 'public simulator failure'; exit 7\n"
    )
    runtime = _native_runtime(native_case, tmp_path, name="public-feedback-runtime")
    client = Provider(["evas simulate public/task/visible_test.scs 2>&1 | tail -20", "true"])
    original = client.complete

    def complete(*args, **kwargs):
        response = original(*args, **kwargs)
        if proposal_format == "strict_json":
            message = response["choices"][0]["message"]
            call = message.pop("tool_calls")[0]["function"]
            message["content"] = json.dumps({
                "tool_name": call["name"], "arguments": json.loads(call["arguments"]),
            })
        return response

    client.complete = complete
    cell = {**_cell(arm="Agentic"), "family_id": "001"}
    run = run_prepared_native_mini_swe(
        runtime=runtime, cell=cell, client=client, attempt_id="feedback",
        evas_command=str(executable), final_judge_command=arguments["command"],
        allow_insecure_test_sandbox=True, episode_backend=backend,
        reasoning_proposal_format=proposal_format, model_call_limit=2,
        campaign_file_sha256="c" * 64,
    )
    assert len(client.requests) == 2
    visible = "\n".join(str(message["content"]) for message in client.requests[1])
    assert "vaevas-public-evas-feedback-v1" in visible
    assert '"operation": "simulate"' in visible
    assert '"status": "failed"' in visible
    assert '"returncode": 7' in visible
    assert '"task_correctness": "not_evaluated"' in visible
    assert '"authenticated": false' in visible
    assert '"authority": "diagnostic_only"' in visible
    assert "FINAL_JUDGE_SENTINEL" not in visible
    assert "VABENCH_EVAS:" not in visible
    assert run.artifact_path is None
    manifest = runner.read_json(runtime / "evidence/native-launcher/manifest.json")
    assert manifest["environment"]["public_evas_feedback_schema_version"] == "vaevas-public-evas-feedback-v1"
    row = scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)
    usage = row["evas_usage"]["untrusted_operation_summary"]
    assert usage["reported_simulation_calls"] == 1
    assert usage["reported_simulation_status_counts"]["failed"] == 1
    assert usage["authenticated"] is False


@pytest.mark.parametrize("backend,proposal_format", [
    ("native-mini-swe", "native_tool_calls"),
    ("native-reasoning", "native_tool_calls"),
    ("native-reasoning", "strict_json"),
])
@pytest.mark.parametrize("limit,submit", [(1, False), (1, True), (3, False), (3, True)])
@pytest.mark.parametrize("arm", ["Agentic", "Agent-No-EVAS"])
def test_native_call_horizon_reaches_real_requests_and_frozen_evidence(
    native_case, tmp_path, backend, proposal_format, limit, submit, arm,  # noqa: F811
):
    from run_native_mini_swe import run_prepared_native_mini_swe
    import score_campaign as scorer

    runtime = _native_runtime(native_case, tmp_path, name="budget-runtime")
    arguments, _, _ = native_case
    (runtime / "public/submission/model.va").write_text("module model; endmodule\n")
    client = Provider(["true"] * (limit - 1) + ["vabench-submit" if submit else "true"])
    complete = client.complete

    def response(*args, **kwargs):
        result = complete(*args, **kwargs)
        if proposal_format == "strict_json":
            message = result["choices"][0]["message"]
            command = json.loads(message.pop("tool_calls")[0]["function"]["arguments"])
            message["content"] = json.dumps({"tool_name": "bash", "arguments": command})
        return result

    client.complete = response
    cell = {**_cell(arm=arm), "family_id": "001"}
    run = run_prepared_native_mini_swe(
        runtime=runtime, cell=cell, client=client, attempt_id="budget",
        evas_command=arguments["evas_command"], final_judge_command=arguments["command"],
        allow_insecure_test_sandbox=True, episode_backend=backend,
        reasoning_proposal_format=proposal_format, model_call_limit=limit,
        campaign_file_sha256="c" * 64,
    )
    assert len(client.requests) == limit
    for index, request in enumerate(client.requests, 1):
        # Current horizon must be in the latest model-visible content, not stale history.
        latest = request[-1]["content"]
        assert f'"call_number": {index}' in latest
        assert f'"remaining_after_this_call": {limit - index}' in latest
        assert "FINAL_JUDGE_SENTINEL" not in json.dumps(request)
    row = scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)
    assert row["model_call_budget"] == {
        "limit": limit, "used_before_attempt": 0, "admitted_in_attempt": limit,
        "used_total": limit, "remaining": 0,
    }
    assert row["termination_reason"] == ("submitted" if submit else "model_call_limit")
    if not submit:
        assert run.artifact_path is None and row["score"] is None
        assert not (runtime / "judge-called").exists()


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


@pytest.mark.parametrize("limit", [None, 1, 5, 13])
def test_reasoning_wrapper_freezes_and_forwards_format(tmp_path, limit):
    output = tmp_path / "reasoning"
    completed = subprocess.run([
        sys.executable, str(WRAPPER), "--output-root", str(output),
        "--model", "fixture-model", "--task-id", "v4-001", "--form", "dut",
        "--comparison-profile", "executable-feedback-control", "--dry-run",
        "--episode-backend", "native-reasoning",
        "--reasoning-proposal-format", "strict_json",
        *([] if limit is None else ["--native-model-call-limit", str(limit)]),
    ], text=True, capture_output=True, timeout=60, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    campaign = runner.read_json(output / "campaign.json")
    assert campaign["execution_config"]["episode_backend"] == "native-reasoning"
    assert campaign["execution_config"]["reasoning_proposal_format"] == "strict_json"
    assert campaign["execution_config"].get("native_model_call_limit") == limit


@pytest.mark.parametrize("mismatch", ["proposal format", "model-call limit"])
def test_score_rejects_proposal_format_different_from_frozen_campaign(tmp_path, monkeypatch, mismatch):
    campaign_path = tmp_path / "campaign.json"
    cell = {"cell_id": "cell", "experimental_arm": "Agentic"}
    campaign_path.write_text(json.dumps({
        "cells": [cell], "execution_config": {
            "episode_backend": "native-reasoning", "reasoning_proposal_format": "strict_json",
            **({"native_model_call_limit": 3} if mismatch == "model-call limit" else {}),
        },
    }))
    monkeypatch.setattr(scorer, "read_native_cell", lambda *a, **k: {
        **cell, "backend": "native-reasoning",
        "proposal_format": "strict_json" if mismatch == "model-call limit" else "native_tool_calls",
        **({"model_call_limit": 2} if mismatch == "model-call limit" else {}),
    })
    monkeypatch.setattr(scorer, "summarize", lambda *a, **k: {})
    monkeypatch.setattr(sys, "argv", [
        "score_campaign.py", "--campaign-output", str(tmp_path),
        "--campaign", str(campaign_path), "--episode-backend", "native-reasoning",
        "--judge-kind", "final_trusted_replay", "--output", str(tmp_path / "score.json"),
    ])
    with pytest.raises(ValueError, match=mismatch):
        scorer.main()
    assert not (tmp_path / "score.json").exists()


@pytest.mark.parametrize("backend,limit", [
    ("native-mini-swe", "0"), ("native-reasoning", "-1"),
    ("native-mini-swe", "1.5"), ("legacy", "1"),
])
def test_wrapper_rejects_invalid_or_legacy_call_limits_before_export(tmp_path, backend, limit):
    output = tmp_path / "invalid"
    completed = subprocess.run([
        sys.executable, str(WRAPPER), "--output-root", str(output), "--model", "fixture",
        "--dry-run", "--episode-backend", backend, "--native-model-call-limit", limit,
    ], capture_output=True, text=True, timeout=30)
    assert completed.returncode != 0
    assert not output.exists()


@pytest.mark.parametrize("limit", [0, -1, True, "3", 1.5])
def test_prepared_launcher_rejects_invalid_limit_before_runtime_reservation(
    native_case, tmp_path, limit,  # noqa: F811
):
    from run_native_mini_swe import run_prepared_native_mini_swe
    runtime = _native_runtime(native_case, tmp_path, name="invalid-budget-runtime")
    arguments, _, _ = native_case
    client = Provider([])
    with pytest.raises(ValueError, match="model-call limit"):
        run_prepared_native_mini_swe(
            runtime=runtime, cell=_cell(arm="Agentic"), client=client, attempt_id="budget",
            evas_command=arguments["evas_command"], model_call_limit=limit,
        )
    assert client.requests == []
    assert not (runtime / "evidence/native-launcher").exists()
