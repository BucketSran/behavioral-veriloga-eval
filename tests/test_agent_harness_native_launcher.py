from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import time
import shutil
import subprocess
import os
import shlex
import pytest

from test_agent_harness_native_episode import native_case as native_case  # noqa: F401
from test_agent_harness_production_public_validation import public_case as public_case  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
sys.path.insert(0, str(CALIBRATION))

import mini_swe_vabench as mini  # noqa: E402
import run_campaign as runner  # noqa: E402
from runners.agent_harness import Observation  # noqa: E402


class Provider:
    model = "fixture-model"
    endpoint = "https://provider.invalid/v1/chat/completions"
    temperature = 0.0
    stream = False

    def __init__(self, commands):
        self.commands = iter(commands)
        self.requests = []

    def complete(self, messages, max_tokens, tools, *, timeout_s=None):
        self.requests.append(deepcopy(messages))
        number = len(self.requests)
        return {
            "id": f"response-{number}",
            "model": self.model,
            "choices": [
                {
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": "public reasoning",
                        "tool_calls": [
                            {
                                "id": f"call-{number}",
                                "type": "function",
                                "function": {
                                    "name": "bash",
                                    "arguments": json.dumps(
                                        {
                                            "command": next(self.commands),
                                        }
                                    ),
                                },
                            }
                        ],
                    },
                }
            ],
            "usage": {"prompt_tokens": 17, "completion_tokens": 5},
        }


def test_native_policy_reuses_real_mini_swe_messages_and_public_feedback():
    from run_native_mini_swe import NativeMiniSwePolicy

    provider = Provider(["echo first", "vabench-submit"])
    model = mini.VaBenchMiniModel(
        provider,
        per_turn_max_tokens=128,
        request_timeout_s=10,
        deadline_monotonic=time.monotonic() + 60,
        usage_parser=runner.provider_output_usage,
        response_metadata=runner.provider_response_metadata,
    )
    policy = NativeMiniSwePolicy(
        model=model, prompt="public task", action_id_prefix="attempt"
    )
    initial = Observation(
        "initial", "task", "ready", {}, candidate_tree_sha256="a" * 64
    )
    action = policy.act(initial)
    assert action.action_id == "attempt-0001"
    assert action.arguments["command"] == "echo first"
    feedback = Observation(
        "second",
        "bash",
        "succeeded",
        {
            "output": "PUBLIC_DIAGNOSTIC",
            "returncode": 0,
            "exception_info": "",
        },
        candidate_tree_sha256="b" * 64,
    )
    action = policy.act(feedback)
    assert action.candidate_tree_sha256 == "b" * 64
    assert provider.requests[0] == [
        {"role": "system", "content": mini.SYSTEM_PROMPT},
        {"role": "user", "content": "public task\n\n" + mini.BASH_CONTRACT},
    ]
    assert provider.requests[1][-1]["role"] == "tool"
    assert provider.requests[1][-1]["tool_call_id"] == "call-1"
    assert "PUBLIC_DIAGNOSTIC" in provider.requests[1][-1]["content"]
    assert model.events[0]["provider_usage"]["completion_tokens"] == 5
    assert model.events[0]["provider_response"]["response_id"] == "response-1"


def test_prepared_launcher_joins_provider_bash_freeze_and_final_result(native_case):  # noqa: F811
    from run_native_mini_swe import run_prepared_native_mini_swe

    arguments, _, _ = native_case
    source = arguments["runtime"]
    runtime = source.with_name("fresh-runtime")
    shutil.copytree(source / "public/task", runtime / "public/task")
    shutil.copytree(source / "evaluator", runtime / "evaluator")
    (runtime / "public/submission").mkdir()
    (runtime / "agent_prompt.txt").write_text("Implement the public task.")
    provider = Provider(
        [
            "printf 'module model; endmodule\\n' > public/submission/model.va",
            "evas simulate public/task/visible_test.scs -o /tmp/vabench-visible/evas-output --spectre-strict",
            "vabench-submit",
        ]
    )
    run = run_prepared_native_mini_swe(
        runtime=runtime,
        cell={
            "cell_id": "cell-001",
            "task_id": "v4-001",
            "mode": "G2",
            "form": "dut",
            "experimental_arm": "Agentic",
            "executable_feedback": True,
            "per_turn_max_tokens": 128,
        },
        client=provider,
        attempt_id="attempt-001",
        evas_command=arguments["evas_command"],
        final_judge_command=arguments["command"],
        judge_timeout_s=10,
        allow_insecure_test_sandbox=True,
    )
    assert run.result.primary_outcome == "behavior_failure", run.result
    assert run.artifact_path.is_file()
    assert len(provider.requests) == 3
    assert "public simulator diagnostic" in provider.requests[-1][-1]["content"]
    assert "FINAL_JUDGE_SENTINEL" not in json.dumps(provider.requests)
    assert not (runtime / "evidence/mini_swe_trajectory.json").exists()
    evidence = runtime / "evidence/native-launcher"
    assert (evidence / "manifest.json").is_file()
    private_events = (evidence / "private-events.jsonl").read_text()
    assert "response-1" in private_events
    assert "public simulator diagnostic" in private_events
    assert "FINAL_JUDGE_SENTINEL" not in private_events
    assert json.loads((evidence / "result.json").read_text())["artifact_file_sha256"]
    with pytest.raises(RuntimeError, match="fresh"):
        run_prepared_native_mini_swe(
            runtime=runtime,
            cell={
                "cell_id": "cell-001",
                "task_id": "v4-001",
                "mode": "G2",
                "form": "dut",
                "experimental_arm": "Agentic",
                "executable_feedback": True,
            },
            client=provider,
            attempt_id="retry",
            evas_command=arguments["evas_command"],
        )
    assert len(provider.requests) == 3


def test_cli_dry_run_exports_one_fresh_cell_without_provider_credentials(tmp_path):
    from scripts import run_v4_r53_clean_room_smoke as smoke
    import build_campaign

    campaign = build_campaign.build_campaign(
        release=runner.DEFAULT_RELEASE,
        family_ids=[
            str(smoke.task_index_row(runner.DEFAULT_RELEASE, "v4-001")["family_id"])
        ],
        model_provider="fixture",
        model="fixture-model",
        per_turn_max_tokens=128,
        repetitions=1,
        three_arm_g0_g2=True,
    )
    cell = next(
        row
        for row in campaign["cells"]
        if row["task_id"] == "v4-001" and row["experimental_arm"] == "Agentic"
    )
    campaign_path = tmp_path / "campaign.json"
    smoke.write_json(campaign_path, campaign)
    command = [
        sys.executable,
        str(CALIBRATION / "run_native_mini_swe.py"),
        "--campaign",
        str(campaign_path),
        "--cell",
        cell["cell_id"],
        "--output",
        str(tmp_path / "launch"),
        "--dry-run",
    ]
    process = subprocess.run(command, text=True, capture_output=True, timeout=60)
    assert process.returncode == 0, process.stderr
    assert json.loads(process.stdout)["status"] == "prepared"
    assert (tmp_path / "launch/runtime/agent_prompt.txt").is_file()
    again = subprocess.run(command, text=True, capture_output=True, timeout=60)
    assert again.returncode != 0
    assert "fresh" in again.stderr


def test_cli_executable_composition_uses_pinned_host_evas_and_removes_key(
    tmp_path, monkeypatch
):
    import run_native_mini_swe as launcher
    import build_campaign
    from types import SimpleNamespace
    from scripts import run_v4_r53_clean_room_smoke as smoke

    campaign = build_campaign.build_campaign(
        runner.DEFAULT_RELEASE,
        family_ids=[
            str(smoke.task_index_row(runner.DEFAULT_RELEASE, "v4-001")["family_id"])
        ],
        model_provider="fixture",
        model="fixture-model",
        per_turn_max_tokens=128,
        three_arm_g0_g2=True,
    )
    cell = next(
        row
        for row in campaign["cells"]
        if row["task_id"] == "v4-001" and row["experimental_arm"] == "Agentic"
    )
    path = tmp_path / "campaign.json"
    smoke.write_json(path, campaign)
    monkeypatch.setenv("NATIVE_TEST_API_KEY", "fixture-secret")
    calls = []

    def capture(**kwargs):
        assert "NATIVE_TEST_API_KEY" not in os.environ
        assert kwargs["client"].api_key == "fixture-secret"
        assert kwargs["campaign_file_sha256"]
        calls.append(kwargs)
        return SimpleNamespace(
            result=SimpleNamespace(
                primary_outcome="behavior_failure", terminal_reason="submitted"
            ),
            artifact_path=kwargs["runtime"] / "fixture-artifact",
        )

    monkeypatch.setattr(launcher, "run_prepared_native_mini_swe", capture)
    assert (
        launcher.main(
            [
                "--campaign",
                str(path),
                "--cell",
                cell["cell_id"],
                "--output",
                str(tmp_path / "launch"),
                "--base-url",
                "https://provider.invalid",
                "--api-key-env",
                "NATIVE_TEST_API_KEY",
                "--evas-command",
                str(ROOT / ".venv/bin/evas"),
            ]
        )
        == 0
    )
    assert len(calls) == 1


def test_legacy_rejects_native_launcher_reservation_before_model_or_export(tmp_path):
    from argparse import Namespace

    reserved = tmp_path / "cell/evidence/native-launcher"
    reserved.mkdir(parents=True)
    with pytest.raises(runner.FinalReplayReservedError, match="native"):
        runner.run_cell({"cell_id": "cell"}, Namespace(output=tmp_path), None)


@pytest.mark.parametrize("transport_raises", [False, True])
def test_private_provider_record_redacts_escaped_credentials(
    native_case, transport_raises  # noqa: F811
):
    from run_native_mini_swe import run_prepared_native_mini_swe

    arguments, _, _ = native_case
    source = arguments["runtime"]
    runtime = source.with_name("provider-failure-runtime")
    shutil.copytree(source / "public/task", runtime / "public/task")
    shutil.copytree(source / "evaluator", runtime / "evaluator")
    (runtime / "public/submission").mkdir()
    (runtime / "agent_prompt.txt").write_text("Implement the public task.")
    provider = Provider(["echo unused"])
    provider.api_key = 'fixture-secret-"escaped\\value'

    def malformed(*args, **kwargs):
        if transport_raises:
            raise RuntimeError(provider.api_key)
        return {"id": "bad-response", "error": provider.api_key}

    provider.complete = malformed
    run = run_prepared_native_mini_swe(
        runtime=runtime,
        cell={
            "cell_id": "cell",
            "task_id": "v4-001",
            "mode": "G2",
            "form": "dut",
            "experimental_arm": "Agentic",
            "executable_feedback": True,
            "per_turn_max_tokens": 128,
        },
        client=provider,
        attempt_id="attempt",
        evas_command=arguments["evas_command"],
        final_judge_command=arguments["command"],
        allow_insecure_test_sandbox=True,
    )
    assert run.artifact_path is None
    text = (runtime / "evidence/native-launcher/private-events.jsonl").read_text()
    if not transport_raises:
        assert "bad-response" in text and "<redacted-provider-credential>" in text
    for path in (runtime / "evidence").rglob("*"):
        if path.is_file():
            assert "fixture-secret" not in path.read_text()
    assert not (runtime / "evidence/bound-final-test").exists()


def test_launcher_backend_profile_conforms_to_shared_schema():
    from run_native_mini_swe import _backend_profile
    from jsonschema import Draft202012Validator

    schema = json.loads((ROOT / "schemas/vaevas-backend-profile-v1.schema.json").read_text())
    Draft202012Validator(schema).validate(_backend_profile())


def test_r53_docker_native_launcher_provider_to_score(tmp_path):
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in real Docker native launcher")
    from run_native_mini_swe import run_prepared_native_mini_swe
    from scripts import run_v4_r53_clean_room_smoke as smoke

    release = runner.DEFAULT_RELEASE
    artifacts = smoke.public_stub_artifacts(smoke.public_contract(release, "v4-001"))
    cell = next(
        row
        for row in smoke.three_arm_cells(release, "v4-001", "fixture-model")
        if row["experimental_arm"] == "Agentic"
    )
    runtime = tmp_path / "runtime"
    runner.export_runtime(cell, release, runtime, timeout_s=60)
    write_command = " && ".join(
        f"printf %s {shlex.quote(content)} > {shlex.quote('public/submission/' + name)}"
        for name, content in artifacts.items()
    )
    provider = Provider(
        [
            write_command,
            "evas simulate public/task/visible_test.scs -o /tmp/vabench-visible/evas-output --spectre-strict",
            "vabench-submit",
        ]
    )
    run = run_prepared_native_mini_swe(
        runtime=runtime,
        cell=cell,
        client=provider,
        attempt_id="native-launcher-smoke-001",
        evas_command=str(ROOT / ".venv/bin/evas"),
        judge_timeout_s=150,
        docker_image=os.environ.get(
            "VABENCH_TEST_DOCKER_IMAGE", mini.DEFAULT_DOCKER_IMAGE
        ),
    )
    assert run.result.primary_outcome == "behavior_failure", run.result
    assert run.artifact_path.is_file()
    evidence = runtime / "evidence/native-launcher"
    manifest = json.loads((evidence / "manifest.json").read_text())
    summary = json.loads((evidence / "result.json").read_text())
    assert manifest["environment"]["network"] is False
    assert manifest["environment"]["evaluator_mounted"] is False
    assert len(summary["evas_invocations"]) == 1
    assert len(provider.requests) == 3
    events = [
        json.loads(line)
        for line in (evidence / "private-events.jsonl").read_text().splitlines()
    ]
    assert any(event["event_type"] == "workspace_quiesced" for event in events)
    assert [
        event["payload"]["action_id"]
        for event in events
        if event["event_type"] == "provider_request"
    ] == [
        event["payload"]["action_id"]
        for event in events
        if event["event_type"] == "tool_request"
    ]
    smoke.write_json(
        tmp_path / "native-launcher-smoke.json",
        {
            "status": "PASS",
            "claim_scope": "single_cell_provider_fixture_not_model_quality",
            "manifest": manifest,
            "summary": summary,
            "artifact": json.loads(run.artifact_path.read_text()),
        },
    )
