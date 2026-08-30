from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys

import pytest

from test_agent_harness_native_episode import native_case as native_case  # noqa: F401
from test_agent_harness_production_public_validation import public_case as public_case  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
sys.path.insert(0, str(CALIBRATION))

import mini_swe_vabench as mini  # noqa: E402


class Provider:
    model = "fixture-model"
    endpoint = "https://provider.invalid/v1/chat/completions"
    temperature = 0.0
    stream = False

    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def complete(self, messages, max_tokens, tools, *, timeout_s=None):
        self.requests.append(
            {
                "messages": deepcopy(messages),
                "tools": deepcopy(tools),
                "max_tokens": max_tokens,
                "timeout_s": timeout_s,
            }
        )
        return next(self.responses)


def _native_runtime(case, tmp_path: Path, *, name: str = "runtime") -> Path:
    arguments, _, _ = case
    source = arguments["runtime"]
    runtime = tmp_path / name
    shutil.copytree(source / "public/task", runtime / "public/task")
    shutil.copytree(source / "evaluator", runtime / "evaluator")
    (runtime / "public/submission").mkdir()
    (runtime / "agent_prompt.txt").write_text("Implement the public task.")
    (runtime / "direct_prompt.txt").write_text("Implement the public task.")
    return runtime


def _cell(*, arm: str, form: str = "dut") -> dict:
    if arm == "OneShot":
        return {
            "cell_id": "cell-oneshot",
            "task_id": "v4-001",
            "mode": "G0",
            "form": form,
            "process": "direct_one_shot",
            "experimental_arm": "OneShot",
            "executable_feedback": False,
            "per_turn_max_tokens": 128,
        }
    if arm == "Agent-No-EVAS":
        return {
            "cell_id": "cell-no-evas",
            "task_id": "v4-001",
            "mode": "G2",
            "form": form,
            "experimental_arm": "Agent-No-EVAS",
            "executable_feedback": False,
            "per_turn_max_tokens": 128,
        }
    return {
        "cell_id": "cell-agentic",
        "task_id": "v4-001",
        "mode": "G2",
        "form": form,
        "experimental_arm": "Agentic",
        "executable_feedback": True,
        "per_turn_max_tokens": 128,
    }


def _bash_response(command: str) -> dict:
    return {
        "id": "response-bash",
        "model": "fixture-model",
        "choices": [{
            "finish_reason": "tool_calls",
            "message": {
                "role": "assistant",
                "content": "public reasoning",
                "tool_calls": [{
                    "id": "call-bash",
                    "type": "function",
                    "function": {
                        "name": "bash",
                        "arguments": json.dumps({"command": command}),
                    },
                }],
            },
        }],
        "usage": {"prompt_tokens": 10, "completion_tokens": 4},
    }


def _submit_response(artifacts: dict[str, str], *, tool: str = "submit_artifacts") -> dict:
    return {
        "id": "response-submit",
        "model": "fixture-model",
        "choices": [{
            "finish_reason": "tool_calls",
            "message": {
                "role": "assistant",
                "content": "final bundle",
                "tool_calls": [{
                    "id": "call-submit",
                    "type": "function",
                    "function": {
                        "name": tool,
                        "arguments": json.dumps({"artifacts": artifacts}),
                    },
                }],
            },
        }],
        "usage": {"prompt_tokens": 11, "completion_tokens": 5},
    }


def test_native_oneshot_unknown_usage_is_not_a_zero_cost_score(native_case, tmp_path):  # noqa: F811
    import score_campaign
    from run_native_mini_swe import run_prepared_native_mini_swe

    arguments, _, _ = native_case
    runtime = _native_runtime(native_case, tmp_path, name="oneshot-unknown-usage")
    response = _submit_response({"model.va": "module model; endmodule\n"})
    response.pop("usage")
    cell = {**_cell(arm="OneShot"), "family_id": "001"}
    run_prepared_native_mini_swe(
        runtime=runtime, cell=cell, client=Provider([response]), attempt_id="one",
        evas_command=arguments["evas_command"], final_judge_command=arguments["command"],
        campaign_file_sha256="c" * 64,
    )
    row = score_campaign.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)
    assert row["output_tokens"] is None
    assert row["metering"]["provider"]["requests"] == 1
    assert row["metering"]["tools"]["requests"] == 0
    assert row["judge_status"] == "behavior_failure"


def test_native_no_evas_uses_absent_public_authority_and_no_evas_runtime(native_case, tmp_path):  # noqa: F811
    from run_native_mini_swe import run_prepared_native_mini_swe

    arguments, _, _ = native_case
    runtime = _native_runtime(native_case, tmp_path, name="no-evas-runtime")
    provider = Provider([
        _bash_response("printf 'module model; endmodule\\n' > public/submission/model.va"),
        _bash_response("vabench-submit"),
    ])

    run = run_prepared_native_mini_swe(
        runtime=runtime,
        cell=_cell(arm="Agent-No-EVAS"),
        client=provider,
        attempt_id="attempt-no-evas",
        evas_command=arguments["evas_command"],
        final_judge_command=arguments["command"],
        allow_insecure_test_sandbox=True,
    )

    assert run.result.primary_outcome == "behavior_failure"
    assert run.artifact_path is not None
    assert len(provider.requests) == 2
    assert all(
        call["function"]["name"] == "bash"
        for request in provider.requests
        for call in request["tools"]
    )
    evidence = runtime / "evidence/native-launcher"
    manifest = json.loads((evidence / "manifest.json").read_text())
    assert manifest["condition"] == "Agent-No-EVAS"
    assert manifest["public_validation_profile_sha256"] is None
    assert manifest["environment"]["evaluator_mounted"] is False
    assert manifest["environment"]["docker_image"] == mini.DEFAULT_NO_EVAS_DOCKER_IMAGE
    assert manifest["environment"]["executable_feedback"] is False
    request = json.loads((runtime / "evidence/native-episode/request.json").read_text())
    assert request["public_validation_profile"] is None
    assert request["public_validation_profile_sha256"] is None
    assert "FINAL_JUDGE_SENTINEL" not in json.dumps(provider.requests)


@pytest.mark.parametrize("limit", [None, 1, 7])
def test_native_oneshot_submits_once_without_bash_or_public_feedback(native_case, tmp_path, limit):  # noqa: F811
    from run_native_mini_swe import run_prepared_native_mini_swe

    arguments, _, _ = native_case
    runtime = _native_runtime(native_case, tmp_path, name="oneshot-runtime")
    provider = Provider([
        _submit_response({"model.va": "module model; endmodule\n"}),
    ])

    run = run_prepared_native_mini_swe(
        runtime=runtime,
        cell=_cell(arm="OneShot"),
        client=provider,
        attempt_id="attempt-oneshot",
        model_call_limit=limit,
        evas_command=arguments["evas_command"],
        final_judge_command=arguments["command"],
        allow_insecure_test_sandbox=True,
    )

    assert run.result.primary_outcome == "behavior_failure"
    assert run.artifact_path is not None
    assert len(provider.requests) == 1
    latest = provider.requests[0]["messages"][-1]["content"]
    if limit is None:
        assert "remaining_after_this_call" not in latest
    else:
        assert f'"remaining_after_this_call": {limit - 1}' in latest
    assert provider.requests[0]["tools"][0]["function"]["name"] == "submit_artifacts"
    assert "bash" not in json.dumps(provider.requests[0]["tools"])
    evidence = runtime / "evidence/native-launcher"
    summary = json.loads((evidence / "result.json").read_text())
    manifest = json.loads((evidence / "manifest.json").read_text())
    assert manifest["condition"] == "OneShot"
    assert manifest["public_validation_profile_sha256"] is None
    assert summary["model_telemetry"]["call_count"] == 1
    assert summary["evas_invocations"] == []
    assert "FINAL_JUDGE_SENTINEL" not in json.dumps(provider.requests)


def test_oneshot_rejects_symlink_parent_before_writing(tmp_path, monkeypatch):
    import run_native_mini_swe as launcher

    runtime = tmp_path / "runtime"
    submission = runtime / "public/submission"
    submission.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (submission / "nested").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(launcher.runner, "expected_candidate_artifacts", lambda _: ["nested/model.va"])
    environment = launcher._OneShotSubmissionEnvironment(runtime=runtime, task_payload={})
    with pytest.raises(ValueError, match="symlink"):
        environment._write_submission({"artifacts": {"nested/model.va": "unsafe"}})
    assert not (outside / "model.va").exists()


def test_invalid_native_oneshot_protocol_fails_without_reprompt(native_case, tmp_path):  # noqa: F811
    from run_native_mini_swe import run_prepared_native_mini_swe

    arguments, _, _ = native_case
    runtime = _native_runtime(native_case, tmp_path, name="bad-oneshot-runtime")
    provider = Provider([
        _submit_response({"model.va": "module model; endmodule\n"}, tool="bash"),
    ])

    run = run_prepared_native_mini_swe(
        runtime=runtime,
        cell=_cell(arm="OneShot"),
        client=provider,
        attempt_id="attempt-bad-oneshot",
        evas_command=arguments["evas_command"],
        final_judge_command=arguments["command"],
        allow_insecure_test_sandbox=True,
    )

    assert run.result.primary_outcome == "protocol_failure"
    assert run.artifact_path is None
    assert len(provider.requests) == 1
    assert not (runtime / "evidence/bound-final-test").exists()


def test_native_no_evas_rejects_agentic_runtime_image():
    from run_native_mini_swe import _select_docker_image

    assert (
        _select_docker_image("Agent-No-EVAS", None)
        == mini.DEFAULT_NO_EVAS_DOCKER_IMAGE
    )
    with pytest.raises(ValueError, match="no-EVAS Docker image"):
        _select_docker_image("Agent-No-EVAS", mini.DEFAULT_DOCKER_IMAGE)


@pytest.mark.parametrize("form", ["dut", "bugfix"])
@pytest.mark.parametrize("arm", ["OneShot", "Agent-No-EVAS", "Agentic"])
def test_native_condition_form_validation_accepts_only_dut_bugfix(arm, form):
    from run_native_mini_swe import validate_native_cell

    assert validate_native_cell(_cell(arm=arm, form=form)) == arm

    bad = _cell(arm=arm, form="unsupported")
    with pytest.raises(ValueError, match="DUT/bugfix"):
        validate_native_cell(bad)
