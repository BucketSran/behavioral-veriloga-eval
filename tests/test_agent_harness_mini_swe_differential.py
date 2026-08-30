"""Scripted-provider comparisons of real legacy/native mini-swe execution.

The provider and final evaluator are fixtures; model parsing, mini-swe's loop,
Bash execution, submission gate and native persistence are production code.
These tests freeze differences, not a blanket backend parity claim.
"""

from copy import deepcopy
import json
import shutil

import pytest

from test_agent_harness_native_launcher import (
    Provider,
    mini,
    runner,
    native_case as native_case,
    public_case as public_case,
)
from runners.agent_harness import read_trajectory, validate_trajectory_semantics
from run_native_mini_swe import run_prepared_native_mini_swe


WRITE = "printf 'module model; endmodule\\n' > public/submission/model.va"
SUBMIT = "vabench-submit"


def assert_operational_guidance_is_only_message_delta(legacy, native):
    """AA-VAE-053 names the initial guidance delta; all later feedback is equal."""
    expected = deepcopy(legacy)
    for request in expected:
        request[1]["content"] = request[1]["content"].replace(
            "Every assistant turn must contain at\nleast one bash tool call.",
            "Choose exactly one bash action per turn in the configured response format.",
        ).replace(
            "Workspace:\n",
            "Workspace:\n- Each command starts in /workspace in a fresh shell; cd does not persist\n"
            "  across calls. Relative public/ paths are resolved from /workspace.\n",
        )
    assert expected == native


def reply(*commands, finish_reason="tool_calls"):
    return {
        "choices": [{
            "finish_reason": finish_reason,
            "message": {
                "role": "assistant",
                "content": "public reasoning",
                "tool_calls": [{
                    "type": "function",
                    "function": {"name": "bash", "arguments": json.dumps({"command": command})},
                } for command in commands],
            },
        }],
        "usage": {"prompt_tokens": 17, "completion_tokens": 5},
    }


class ScriptedProvider(Provider):
    def __init__(self, responses, on_response=None):
        super().__init__([])
        self.responses = iter(responses)
        self.request_contracts = []
        self.on_response = on_response

    def complete(self, messages, max_tokens, tools, *, timeout_s=None):
        self.requests.append(deepcopy(messages))
        self.request_contracts.append({"max_tokens": max_tokens, "tools": deepcopy(tools)})
        response = next(self.responses)
        if self.on_response is not None:
            self.on_response(len(self.requests))
        if isinstance(response, Exception):
            raise response
        response = deepcopy(response)
        number = len(self.requests)
        response.update(id=f"response-{number}", model=self.model)
        for index, call in enumerate(response["choices"][0]["message"]["tool_calls"]):
            call["id"] = f"call-{number}-{index}"
        return response


@pytest.fixture
def execute_path(native_case):  # noqa: F811
    arguments, _, _ = native_case
    source = arguments["runtime"]

    def execute(kind, responses, *, expected_error=None, on_response=None):
        runtime = source.with_name(kind)
        shutil.copytree(source / "public/task", runtime / "public/task")
        shutil.copytree(source / "evaluator", runtime / "evaluator")
        (runtime / "public/submission").mkdir()
        prompt = "Implement the public task."
        (runtime / "agent_prompt.txt").write_text(prompt)
        provider = ScriptedProvider(responses, on_response)
        if kind == "legacy":
            try:
                outcome = mini.run_mini_swe_episode(
                    runtime=runtime, prompt=prompt, client=provider,
                    per_turn_max_tokens=128, agent_timeout_s=1800,
                    request_timeout_s=10, tool_timeout_s=10,
                    sandbox_backend="none", evas_command=arguments["evas_command"],
                    candidate_artifacts=("model.va",),
                    submission_gate=runner.submission_artifact_gate,
                    usage_parser=runner.provider_output_usage,
                    response_metadata=runner.provider_response_metadata,
                    trajectory_path=runtime / "evidence/mini_swe_trajectory.json",
                )
            except Exception as exc:
                if expected_error is None or not isinstance(exc, expected_error):
                    raise
                outcome = exc
        else:
            outcome = run_prepared_native_mini_swe(
                runtime=runtime,
                cell={
                    "cell_id": "cell-001", "task_id": "v4-001", "mode": "G2",
                    "form": "dut", "experimental_arm": "Agentic",
                    "executable_feedback": True, "per_turn_max_tokens": 128,
                },
                client=provider, attempt_id="attempt-001",
                evas_command=arguments["evas_command"],
                final_judge_command=arguments["command"], judge_timeout_s=10,
                allow_insecure_test_sandbox=True,
            )
        return outcome, provider, runtime

    return execute


@pytest.mark.parametrize("malformation", ["missing", "json", "unknown", "nonobject", "command_type"])
def test_format_recovery_is_legacy_only_and_native_is_protocol_failure(execute_path, malformation):
    malformed = reply("echo forbidden")
    function = malformed["choices"][0]["message"]["tool_calls"][0]["function"]
    if malformation == "missing":
        malformed["choices"][0]["message"]["tool_calls"] = []
    elif malformation == "json":
        function["arguments"] = "{broken"
    elif malformation == "unknown":
        function["name"] = "undeclared-tool"
    elif malformation == "nonobject":
        function["arguments"] = "[]"
    else:
        function["arguments"] = '{"command": 7}'
    responses = [malformed, reply(WRITE), reply(SUBMIT)]
    old, old_provider, _ = execute_path("legacy", responses)
    new, new_provider, runtime = execute_path("native", responses)
    assert old["submitted"] and len(old_provider.requests) == 3
    assert old_provider.requests[1][-1]["role"] == "user"
    assert any(m.get("extra", {}).get("interrupt_type") == "FormatError" for m in old["messages"])
    assert new.result.primary_outcome == "protocol_failure", new.result
    assert new.result.failure.category == "proposal_rejected"
    assert len(new_provider.requests) == 1
    assert new.artifact_path is None and new.result.final_judgment is None
    assert not (runtime / "judge-called").exists()
    assert not list((runtime / "public/submission").iterdir())
    events = read_trajectory(new.trajectory_path)
    validate_trajectory_semantics(events)
    assert not any(e["event_type"] == "action_authorized" for e in events)


@pytest.mark.parametrize("reject_first", [False, True])
def test_single_action_feedback_submission_and_candidate_bytes_match(execute_path, reject_first):
    commands = ([SUBMIT] if reject_first else []) + [
        "printf 'PUBLIC_DIAGNOSTIC\\n'; exit 2", WRITE, SUBMIT,
        "touch public/submission/after-final",  # Must never be requested.
    ]
    responses = [reply(command) for command in commands]
    old, old_provider, old_runtime = execute_path("legacy", responses)
    new, new_provider, runtime = execute_path("native", responses)
    assert old["submitted"] and new.result.terminal_reason == "submitted"
    assert new.result.primary_outcome == "behavior_failure"  # fixture judge, not model quality
    assert_operational_guidance_is_only_message_delta(old_provider.requests, new_provider.requests)
    assert old_provider.request_contracts == new_provider.request_contracts
    assert len(new_provider.requests) == len(commands) - 1
    assert "PUBLIC_DIAGNOSTIC" in json.dumps(new_provider.requests)
    if reject_first:
        assert "submission_rejected" in new_provider.requests[1][-1]["content"]
    assert (old_runtime / "public/submission/model.va").read_bytes() == (
        runtime / "evidence/final_submission/model.va"
    ).read_bytes()
    gate = runner.submission_artifact_gate(old_runtime)
    snapshot = runner.RESULT_PROTOCOL.snapshot_submission(old_runtime, gate)
    assert snapshot["tree_sha256"] == new.result.submission.tree_sha256
    assert not (runtime / "public/submission/after-final").exists()
    assert "FINAL_JUDGE_SENTINEL" not in json.dumps(new_provider.requests)
    events = read_trajectory(new.trajectory_path)
    assert validate_trajectory_semantics(events)
    assert sum(e["event_type"] == "final_judgment_completed" for e in events) == 1


def test_multi_action_is_legacy_sequential_but_native_rejected_before_any_dispatch(execute_path):
    responses = [reply(WRITE, SUBMIT, "touch public/submission/after-final")]
    old, old_provider, old_runtime = execute_path("legacy", responses)
    new, new_provider, runtime = execute_path("native", responses)
    assert old["submitted"] and len(old_provider.requests) == 1
    assert [row["kind"] for row in old["commands"]] == ["bash", "bash-submit"]
    assert not (old_runtime / "public/submission/after-final").exists()
    assert len(new_provider.requests) == 1
    assert new.result.primary_outcome == "protocol_failure"
    assert new.result.failure.message == "proposal rejected (action_count)"
    assert new.result.submission is new.result.final_judgment is new.artifact_path is None
    assert not list((runtime / "public/submission").iterdir())
    assert not (runtime / "judge-called").exists()


def test_valid_bash_at_provider_output_cap_remains_telemetry_in_both_loops(execute_path):
    responses = [reply(WRITE, finish_reason="length"), reply(SUBMIT)]
    old, old_provider, _ = execute_path("legacy", responses)
    new, new_provider, runtime = execute_path("native", responses)
    assert old["submitted"] and new.result.terminal_reason == "submitted"
    assert_operational_guidance_is_only_message_delta(old_provider.requests, new_provider.requests)
    assert old["events"][0]["finish_reason"] == "length"
    metadata = json.loads((runtime / "evidence/native-launcher/result.json").read_text())
    assert metadata["model_telemetry"]["provider_events"][0]["finish_reason"] == "length"
    assert old["output_tokens"] == metadata["model_telemetry"]["provider_output_tokens"] == 10


@pytest.mark.parametrize("error_type", [
    runner.ProviderRequestTimeout, runner.ProviderContextWindowExceeded, runner.ProviderAPIError,
])
def test_provider_failures_are_not_model_protocol_rejections_or_scores(execute_path, error_type):
    error = error_type("scripted provider failure")
    old, old_provider, old_runtime = execute_path("legacy", [error], expected_error=error_type)
    new, new_provider, runtime = execute_path("native", [error])
    assert isinstance(old, error_type)  # Legacy campaign wrapper, not DefaultAgent, classifies it.
    assert len(old_provider.requests) == len(new_provider.requests) == 1
    assert (old_runtime / "evidence/mini_swe_trajectory.json").is_file()
    assert new.result.primary_outcome == "infrastructure_failure"
    assert new.result.failure.category == "backend_failure"
    assert new.artifact_path is new.result.final_judgment is None
    assert not (runtime / "judge-called").exists()
    private = read_trajectory(runtime / "evidence/native-launcher/private-events.jsonl")
    failures = [e for e in private if e["event_type"] == "provider_failure"]
    assert [e["payload"]["error_type"] for e in failures] == [error_type.__name__]


@pytest.mark.parametrize("complete", [False, True])
def test_late_response_is_not_dispatched_by_native_but_legacy_checks_next_turn(
    execute_path, monkeypatch, complete,
):
    # Advance only the external clock boundary, not either controller or gate.
    clock = [0.0]
    monkeypatch.setattr(mini.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(mini.time, "time", lambda: clock[0])

    def late_response(number):
        if number == 2:
            clock[0] = 1801.0

    responses = [reply(WRITE if complete else "printf ready"), reply("printf late")]
    old, old_provider, _ = execute_path("legacy", responses, on_response=late_response)
    clock[0] = 0.0
    new, new_provider, runtime = execute_path("native", responses, on_response=late_response)
    assert old["exit_status"] == "TimeExceeded" and old["artifact_complete"] is complete
    assert len(old["commands"]) == 2  # Legacy executes the late reply before checking wall time.
    assert len(old_provider.requests) == len(new_provider.requests) == 2
    private = read_trajectory(runtime / "evidence/native-launcher/private-events.jsonl")
    assert sum(e["event_type"] == "tool_request" for e in private) == 1
    assert new.result.terminal_reason == "agent_timeout"
    assert (new.result.final_judgment is not None) is complete
    assert (new.artifact_path is not None) is complete
    assert (runtime / "judge-called").exists() is complete
    assert validate_trajectory_semantics(read_trajectory(new.trajectory_path))
