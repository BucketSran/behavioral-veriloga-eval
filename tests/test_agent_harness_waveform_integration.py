"""Fixed public action admission, quiescence, observation and score joins."""

import json
import os
import shlex
from pathlib import Path

import pytest

from test_agent_harness_public_waveform import (  # noqa: F401
    public_case, docker_processes, make_executor,
)
from test_agent_harness_native_episode import native_case as native_case  # noqa: F401
from test_agent_harness_native_conditions import _cell, _native_runtime
from test_agent_harness_native_launcher import Provider, runner


def tool_case(public_case, transitions, **callbacks):  # noqa: F811
    from runners.agent_harness import AgentAction, ToolRegistry
    from runners.agent_harness.tools.public_waveform_tool import PublicWaveformTool

    (public_case[0].runtime / "evaluator/score_policy.json").write_text(json.dumps({"candidate_artifacts": ["model.va"]}))
    executor = make_executor(public_case)
    tool = PublicWaveformTool(
        executor=executor, quiesce=callbacks.get("quiesce", lambda: transitions.append("pause")),
        resume=callbacks.get("resume", lambda: transitions.append("resume")),
    )
    registry = ToolRegistry([tool.descriptor])
    capability = registry.resolve(condition_id="Agentic", model_visible=True).capabilities[0]
    candidate, _ = executor.inspect_candidate()
    action = AgentAction("wave-1", "vaevas_public_simulate", {}, "native-mini-swe", candidate)
    return executor, tool, capability, action


def test_fixed_action_incomplete_resumes_without_execution(public_case, docker_processes):  # noqa: F811
    (public_case[0].workspace / "submission/model.va").unlink()
    transitions = []
    executor, tool, capability, action = tool_case(public_case, transitions)
    step = tool.step(action, capability)
    assert transitions == ["pause", "resume"]
    assert not docker_processes["creates"]
    assert not step.done
    assert step.observation.candidate_tree_sha256 == action.candidate_tree_sha256
    assert step.observation.validation_profile_sha256 == executor.profile_sha256
    assert step.observation.payload["rejection_kind"] == "candidate_incomplete"
    assert step.observation.payload["evas_invocation_executed"] is False
    assert step.observation.payload["receipt"] is None
    assert step.observation.payload["usable_feedback"] is False
    assert executor.inspect_candidate()[1] == ("model.va",)


@pytest.mark.parametrize("exitcode", [0, 2, 124])
def test_fixed_action_binds_actual_receipt(public_case, docker_processes, exitcode):  # noqa: F811
    from runners.agent_harness.tools.public_waveform_tool import validate_waveform_observation
    transitions = []
    executor, tool, capability, action = tool_case(public_case, transitions)
    docker_processes["exitcode"] = exitcode
    observation = tool.step(action, capability).observation
    assert transitions == ["pause", "resume"]
    assert len(docker_processes["simulations"]) == 1
    assert observation.payload["evas_invocation_executed"] is True
    assert observation.payload["receipt"]["returncode"] == exitcode
    assert observation.payload["rejection_kind"] is None
    validate_waveform_observation(observation.to_document(), profile=executor.profile,
                                  attempt_id=executor.context.attempt_id, task_id=executor.context.task_id)


def test_fixed_action_rejects_arguments_before_pause(public_case):  # noqa: F811
    from dataclasses import replace
    transitions = []
    _, tool, capability, action = tool_case(public_case, transitions)
    rejection = tool.step(replace(action, arguments={"path": "private.csv"}), capability)
    assert rejection.code == "invalid_tool_arguments"
    assert transitions == []


def test_fixed_action_preserves_primary_and_resume_incident(public_case):  # noqa: F811
    transitions = []

    def pause():
        transitions.append("pause")
        raise ValueError("pause failed")

    def resume():
        transitions.append("resume")
        raise RuntimeError("resume failed")

    _, tool, capability, action = tool_case(public_case, transitions, quiesce=pause, resume=resume)
    with pytest.raises(RuntimeError, match="pause failed") as caught:
        tool.step(action, capability)
    assert transitions == ["pause", "resume"]
    assert caught.value.cleanup_incidents == [{"stage": "generation_resume", "error_type": "RuntimeError"}]
    assert caught.value.execution_count_status == "confirmed_zero_preflight"


def test_post_execution_failure_preserves_unknown_count_in_private_evidence(public_case, docker_processes):  # noqa: F811
    from run_native_mini_swe import _RecordedEnvironment
    from public_waveform import read_native_waveform_evidence
    executor, tool, capability, action = tool_case(public_case, [])
    records = []
    bridge = _RecordedEnvironment(record=lambda event_type, payload: records.append({"event_type": event_type, "payload": payload}),
        waveform_tool=tool, legacy_environment=public_case[0], task_payload={},
        candidate_tree_sha256=executor.candidate_tree_sha256, freeze_submission=lambda: None,
        submitted_exception_types=())
    bridge.start(public_case[1])
    docker_processes["on_simulation"] = lambda: (executor.runtime / "public/submission/model.va").write_text("changed")
    with pytest.raises(RuntimeError, match="candidate drift"):
        bridge.step(action, capability)
    assert len(docker_processes["simulations"]) == 1
    failure = records[-1]
    assert failure["event_type"] == "tool_failure"
    assert failure["payload"]["execution_count_status"] == "unknown_after_executor_entered"
    assert failure["payload"]["execution_receipt"] is None
    assert not any(record["event_type"] == "tool_result" for record in records)
    counts = read_native_waveform_evidence(**waveform_reader_case(executor, action, records))
    assert counts["public_validation_calls"] == 1
    assert counts["public_waveform_evas_invocations_executed"] is None
    assert counts["public_waveform_evas_invocations_confirmed"] == 0
    assert counts["public_waveform_execution_count_complete"] is False


def waveform_reader_case(executor, action, records):
    import hashlib
    import public_waveform
    from runners.agent_harness.tools import waveform_summary
    root = Path(public_waveform.__file__).parent
    sources = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in (
        "public_waveform.py", "mini_swe_vabench.py", "public_validation.py", "run_campaign.py")}
    sources["waveform_summary.py"] = hashlib.sha256(Path(waveform_summary.__file__).read_bytes()).hexdigest()
    return {"runtime": executor.runtime, "profile": executor.profile,
        "manifest": {"condition": "Agentic", "attempt_id": executor.context.attempt_id,
            "cell": {"task_id": executor.context.task_id}, "tool_timeout_s": 60,
            "source_sha256": sources, "public_validation_profile_sha256": executor.profile_sha256,
            "extensions": {"public_waveform": {"intervention": "isolated-public-waveform-v1",
                "tool_name": "vaevas_public_simulate", "max_public_validation_calls": 1}},
            "environment": {"sandbox_backend": "docker", "image_id": executor.image_id}},
        "events": [{"event_type": "action_authorized", "payload": {"action_id": action.action_id,
            "tool_name": action.tool_name}}], "private": records}


@pytest.mark.parametrize("when", ["before_execution", "after_receipt"])
def test_failure_count_preserves_confirmed_execution_state(public_case, docker_processes, when):  # noqa: F811
    from run_native_mini_swe import _RecordedEnvironment
    from public_waveform import read_native_waveform_evidence
    def failure():
        raise RuntimeError("fixture failure")
    executor, tool, capability, action = tool_case(public_case, [], **{
        "quiesce" if when == "before_execution" else "resume": failure})
    records = []
    bridge = _RecordedEnvironment(record=lambda event_type, payload: records.append({"event_type": event_type, "payload": payload}),
        waveform_tool=tool, legacy_environment=public_case[0], task_payload={},
        candidate_tree_sha256=executor.candidate_tree_sha256, freeze_submission=lambda: None,
        submitted_exception_types=())
    bridge.start(public_case[1])
    with pytest.raises(RuntimeError, match="fixture failure"):
        bridge.step(action, capability)
    counts = read_native_waveform_evidence(**waveform_reader_case(executor, action, records))
    assert counts["public_waveform_execution_count_complete"] is True
    assert counts["public_waveform_evas_invocations_executed"] == (0 if when == "before_execution" else 1)


def test_score_reader_rejects_failure_without_execution_metadata(public_case):  # noqa: F811
    from public_waveform import read_native_waveform_evidence
    executor, _, _, action = tool_case(public_case, [])
    records = [{"event_type": "tool_request", "payload": action.to_document()},
        {"event_type": "tool_failure", "payload": {"action_id": action.action_id, "error_type": "RuntimeError"}}]
    with pytest.raises(ValueError, match="failure count"):
        read_native_waveform_evidence(**waveform_reader_case(executor, action, records))


def test_invalid_arguments_record_confirmed_zero_before_pause(public_case, docker_processes):  # noqa: F811
    from dataclasses import replace
    from run_native_mini_swe import _RecordedEnvironment
    from public_waveform import read_native_waveform_evidence
    transitions = []
    executor, tool, capability, action = tool_case(public_case, transitions)
    action = replace(action, arguments={"command": "invalid"})
    records = []
    bridge = _RecordedEnvironment(record=lambda event_type, payload: records.append({"event_type": event_type, "payload": payload}),
        waveform_tool=tool, legacy_environment=public_case[0], task_payload={},
        candidate_tree_sha256=executor.candidate_tree_sha256, freeze_submission=lambda: None,
        submitted_exception_types=())
    bridge.start(public_case[1])
    assert bridge.step(action, capability).code == "invalid_tool_arguments"
    assert records[-1]["payload"]["execution_count_status"] == "confirmed_zero_preflight"
    assert records[-1]["payload"]["execution_receipt"] is None
    assert not transitions and not docker_processes["creates"]
    counts = read_native_waveform_evidence(**waveform_reader_case(executor, action, records))
    assert counts["public_validation_calls"] == 1
    assert counts["public_waveform_evas_invocations_executed"] == 0
    assert counts["public_waveform_execution_count_complete"] is True


def test_incomplete_request_budget_blocks_second_pause_and_execution(public_case, docker_processes, tmp_path):  # noqa: F811
    from dataclasses import replace
    from runners.agent_harness import AgentAction, EpisodeController, Observation, ToolRegistry, JsonlTrajectoryRecorder, read_trajectory
    (public_case[0].workspace / "submission/model.va").unlink()
    transitions = []
    executor, tool, _, action = tool_case(public_case, transitions)

    class Environment:
        def start(self, context):
            return Observation("initial", "task", "ready", {}, candidate_tree_sha256=action.candidate_tree_sha256)

        def step(self, action, capability):
            return tool.step(action, capability)

        def close(self):
            pass

    class Policy:
        count = 0

        def act(self, observation):
            self.count += 1
            return AgentAction(f"wave-{self.count}", action.tool_name, {}, "fixture", observation.candidate_tree_sha256)

    trajectory = tmp_path / "budget.jsonl"
    controller = EpisodeController(policy=Policy(), environment=Environment(), tool_registry=ToolRegistry([tool.descriptor]),
        final_judge=object(), trajectory=JsonlTrajectoryRecorder(trajectory),
        public_validation_profile_sha256=executor.profile_sha256)
    result = controller.run(replace(public_case[1], max_steps=3, budget_limits={"public_validation_calls": 1}))
    assert result.primary_outcome == "budget_exhausted"
    assert transitions == ["pause", "resume"]
    assert not docker_processes["creates"]
    updates = [event["payload"] for event in read_trajectory(trajectory) if event["event_type"] == "budget_updated"]
    assert len(updates) == 1
    assert updates[0]["delta"] == {"tool_calls": 1, "public_validation_calls": 1}


@pytest.mark.parametrize("field,value", [("image_id", "sha256:" + "d" * 64),
    ("candidate_tree_sha256", "e" * 64), ("command_sha256", "f" * 64),
    ("profile_input_identity_sha256", "b" * 64), ("public_task_tree_sha256", "c" * 64)])
def test_score_reader_rejects_rehashed_receipt_drift(public_case, docker_processes, field, value):  # noqa: F811
    from result_protocol import canonical_sha256
    from runners.agent_harness import Observation
    from public_waveform import read_native_waveform_evidence
    executor, tool, capability, action = tool_case(public_case, [])
    observation = tool.step(action, capability).observation
    payload = observation.to_document()["payload"]
    payload["receipt"][field] = value
    receipt = payload["receipt"]
    receipt["receipt_sha256"] = canonical_sha256({key: item for key, item in receipt.items() if key != "receipt_sha256"})
    forged = Observation("forged", action.tool_name, observation.status, payload,
        candidate_tree_sha256=observation.candidate_tree_sha256, validation_profile_sha256=executor.profile_sha256)
    records = [{"event_type": "tool_request", "payload": action.to_document()},
        {"event_type": "tool_result", "payload": {"action_id": action.action_id, "observation": forged.to_document()}}]
    with pytest.raises(ValueError, match="waveform"):
        read_native_waveform_evidence(**waveform_reader_case(executor, action, records))


def test_fixed_tool_schema_is_closed_and_not_shared_memory(public_case):  # noqa: F811
    import jsonschema
    from runners.agent_harness.tools.public_waveform_tool import waveform_tool_descriptor
    descriptor = waveform_tool_descriptor()
    assert descriptor["evidence_policy"]["may_enter_shared_memory"] is False
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"command": "evil"}, descriptor["argument_schema"])
    (public_case[0].workspace / "submission/model.va").unlink()
    _, tool, capability, action = tool_case(public_case, [])
    payload = tool.step(action, capability).observation.to_document()["payload"]
    jsonschema.validate(payload, descriptor["observation_schema"])
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**payload, "final_score": 1}, descriptor["observation_schema"])


@pytest.mark.parametrize("field,value", [("evas_invocation_executed", True), ("usable_feedback", True),
                                        ("receipt", {"invocation_id": "invented"})])
def test_incomplete_observation_rejects_contradictory_receipts(public_case, field, value):  # noqa: F811
    from runners.agent_harness import Observation
    from runners.agent_harness.tools.public_waveform_tool import validate_waveform_observation
    (public_case[0].workspace / "submission/model.va").unlink()
    executor, tool, capability, action = tool_case(public_case, [])
    observation = tool.step(action, capability).observation
    payload = observation.to_document()["payload"]
    payload[field] = value
    forged = Observation("forged", observation.tool_name, observation.status, payload,
                         candidate_tree_sha256=observation.candidate_tree_sha256,
                         validation_profile_sha256=executor.profile_sha256)
    with pytest.raises(ValueError, match="waveform"):
        validate_waveform_observation(forged.to_document(), profile=executor.profile,
                                      attempt_id=executor.context.attempt_id, task_id=executor.context.task_id)


@pytest.mark.parametrize("arm,limit,insecure", [("OneShot", 1, False), ("Agent-No-EVAS", 1, False),
    ("Agentic", True, False), ("Agentic", 0, False), ("Agentic", -1, False), ("Agentic", 1, True)])
def test_waveform_activation_rejects_before_runtime_reservation(native_case, tmp_path, arm, limit, insecure):  # noqa: F811
    from run_native_mini_swe import run_prepared_native_mini_swe
    args, _, _ = native_case
    runtime = _native_runtime(native_case, tmp_path, name="invalid-waveform")
    with pytest.raises(ValueError, match="waveform"):
        run_prepared_native_mini_swe(runtime=runtime, cell=_cell(arm=arm), client=Provider([]),
            attempt_id="wave", evas_command=args["evas_command"], public_waveform_max_calls=limit,
            allow_insecure_test_sandbox=insecure)
    assert not (runtime / "evidence/native-launcher").exists()


@pytest.mark.skipif(os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1", reason="explicit Docker opt-in")
@pytest.mark.parametrize("backend,fmt", [("native-mini-swe", "native_tool_calls"),
    ("native-reasoning", "native_tool_calls"), ("native-reasoning", "strict_json")])
def test_real_waveform_feedback_freeze_final_score(tmp_path, backend, fmt):
    from scripts import run_v4_r53_clean_room_smoke as smoke
    import score_campaign as scorer
    from run_native_mini_swe import run_prepared_native_mini_swe
    from runners.agent_harness import read_trajectory
    from test_agent_harness_production_public_validation import RELEASE
    cell = next(cell for cell in smoke.three_arm_cells(RELEASE, "v4-001", "fixture-model") if cell["experimental_arm"] == "Agentic")
    runtime = tmp_path / "waveform-runtime"
    runner.export_runtime(cell, RELEASE, runtime, timeout_s=60)
    artifacts = smoke.public_stub_artifacts(smoke.public_contract(RELEASE, "v4-001"))
    write = "\n".join(f"printf %s {shlex.quote(content)} > public/submission/{name}" for name, content in artifacts.items())
    client = Provider(["unused", write, "unused", "vabench-submit"])
    original = client.complete

    def complete(messages, max_tokens, tools, **kwargs):
        response = original(messages, max_tokens, tools, **kwargs)
        message = response["choices"][0]["message"]
        function = message["tool_calls"][0]["function"]
        if len(client.requests) in (1, 3):
            function.update(name="vaevas_public_simulate", arguments="{}")
        if fmt == "strict_json":
            message.pop("tool_calls")
            message["content"] = json.dumps({"tool_name": function["name"], "arguments": json.loads(function["arguments"])})
        return response

    client.complete = complete
    run = run_prepared_native_mini_swe(runtime=runtime, cell=cell, client=client, attempt_id="wave",
        evas_command=str(Path(__file__).resolve().parents[1] / ".venv/bin/evas"), episode_backend=backend,
        reasoning_proposal_format=fmt, model_call_limit=4, public_waveform_max_calls=2,
        campaign_file_sha256="c" * 64)
    assert run.artifact_path is not None, run.result
    assert "candidate_incomplete" in json.dumps(client.requests[1])
    assert "waveform_summary" in json.dumps(client.requests[-1])
    row = scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)
    assert row["public_validation_calls"] == 2
    assert row["public_waveform_evas_invocations_executed"] == 1
    assert row["extensions"]["public_waveform"]["max_public_validation_calls"] == 2
    events = read_trajectory(run.trajectory_path)
    assert len([event for event in events if event["event_type"] == "final_judgment_completed"]) == 1
    assert len([event for event in events if event["event_type"] == "budget_updated"
                and event["payload"]["delta"].get("public_validation_calls") == 1]) == 2
