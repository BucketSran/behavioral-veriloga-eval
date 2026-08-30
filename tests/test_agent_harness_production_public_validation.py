from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

from runners.agent_harness import (
    AgentAction,
    EnvironmentStep,
    EpisodeContext,
    EpisodeController,
    JsonlTrajectoryRecorder,
    Observation,
    ToolRegistry,
    read_trajectory,
    public_validation_profile_sha256,
    validate_trajectory_semantics,
)

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
sys.path.insert(0, str(CALIBRATION))

import mini_swe_vabench as mini  # noqa: E402
import public_validation as validation  # noqa: E402

RELEASE = ROOT / "benchmark-vabench-release-v4/release/benchmarkv4-r53"
COMMAND = (
    "evas simulate public/task/visible_test.scs "
    "-o /tmp/vabench-visible/evas-output --spectre-strict"
)


@pytest.fixture
def public_case(tmp_path):
    runtime = tmp_path / "runtime"
    task = runtime / "public/task"
    task.mkdir(parents=True)
    (task / "instruction.md").write_text("Write model.va.\n")
    (task / "visible_test.scs").write_text("tran tran stop=1n\n")
    (task / "evas_runtime.json").write_text(
        json.dumps(
            {
                "schema_version": "r53-direct-evas-runtime-v2",
                "working_directory": "runtime_package_root",
                "command": COMMAND,
            }
        )
    )
    submission = runtime / "public/submission"
    submission.mkdir()
    (submission / "model.va").write_text("module model; endmodule\n")
    (runtime / "evaluator").mkdir()
    (runtime / "evaluator/secret.txt").write_text("FINAL_PRIVATE_SENTINEL")
    executable = tmp_path / "evas"
    executable.write_text(
        "#!/bin/bash\n"
        "if [[ $1 == --version ]]; then echo 'evas-sim 0.8.7 (test double)'; exit; fi\n"
        "echo 'public simulator diagnostic'\n"
    )
    executable.chmod(0o755)
    environment = mini.VaBenchBashEnvironment(
        runtime,
        timeout_s=10,
        sandbox_backend="none",
        evas_command=str(executable),
        submission_gate=lambda _: {"passed": False},
        candidate_artifacts=("model.va",),
    )
    context = EpisodeContext("cell-001", "attempt-001", "v4-001", "Agentic", 2)
    yield environment, context, executable
    environment.close()


def bind(public_case):
    environment, context, _ = public_case
    profile = validation.build_public_validation_profile(
        environment=environment,
        release=RELEASE,
        campaign_config_sha256="a" * 64,
        allow_insecure_test_sandbox=True,
    )
    adapter = validation.PublicEvasValidator(
        environment=environment,
        context=context,
        public_validation_profile=profile,
        allow_insecure_test_sandbox=True,
    )
    return adapter, profile


def test_real_public_execution_returns_candidate_and_profile_bound_observation(
    public_case,
):
    environment, context, _ = public_case
    adapter, profile = bind(public_case)
    candidate = adapter.candidate_tree_sha256()

    observation = adapter.validate(candidate_tree_sha256=candidate)

    assert observation.status == "succeeded"
    assert observation.candidate_tree_sha256 == candidate
    assert observation.validation_profile_sha256 == public_validation_profile_sha256(
        profile
    )
    assert observation.payload["attempt_id"] == context.attempt_id
    assert observation.payload["feedback_scope"] == "public_simulation_only"
    assert "public simulator diagnostic" in observation.payload["output"]
    assert "FINAL_PRIVATE_SENTINEL" not in json.dumps(observation.to_document())
    assert "score" not in observation.payload
    assert "passed" not in observation.payload
    assert len(environment.evas_invocations) == 1
    assert (
        observation.payload["output_sha256"]
        == hashlib.sha256(observation.payload["output"].encode()).hexdigest()
    )
    assert adapter.candidate_tree_sha256() == candidate


def test_public_invocation_digest_is_independent_of_agent_working_directory(public_case):
    environment, _, _ = public_case
    adapter, _ = bind(public_case)
    expected = validation._invocation_tree_sha256(
        environment.workspace / "submission", environment.candidate_artifacts
    )
    environment.execute({"command": "cd work && evas --version"})
    assert environment.evas_invocations[-1]["candidate_tree_sha256"] == expected


def test_resource_failure_cannot_be_reported_as_successful_public_validation(
    public_case, monkeypatch
):
    monkeypatch.setattr(mini, "SUBMISSION_QUOTA_BYTES", 10)
    adapter, _ = bind(public_case)
    with pytest.raises(ValueError, match="resource"):
        adapter.validate(candidate_tree_sha256=adapter.candidate_tree_sha256())


def test_undeclared_candidate_dependency_is_rejected_before_execution(public_case):
    environment, _, _ = public_case
    adapter, _ = bind(public_case)
    candidate = adapter.candidate_tree_sha256()
    (environment.workspace / "submission/helper.va").write_text(
        "undeclared dependency\n"
    )
    with pytest.raises(ValueError, match="undeclared"):
        adapter.validate(candidate_tree_sha256=candidate)
    assert environment.evas_invocations == []


@pytest.mark.parametrize(
    "marker", ["evidence/final_submission", "evidence/bound-final-test"]
)
def test_validation_cannot_reenter_after_terminal_freeze(public_case, marker):
    environment, _, _ = public_case
    adapter, _ = bind(public_case)
    (environment.runtime / marker).mkdir(parents=True)

    with pytest.raises(ValueError, match="terminal"):
        adapter.validate(candidate_tree_sha256=adapter.candidate_tree_sha256())

    assert environment.evas_invocations == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("allowed_feedback", ["metric"]),
        ("benchmark_release", "benchmarkv4-r44"),
    ],
)
def test_adapter_rejects_profiles_outside_its_actual_feedback_contract(
    public_case, field, value
):
    environment, context, _ = public_case
    _, profile = bind(public_case)
    profile[field] = value
    with pytest.raises(ValueError, match="profile"):
        validation.PublicEvasValidator(
            environment=environment,
            context=context,
            public_validation_profile=profile,
            allow_insecure_test_sandbox=True,
        )


@pytest.mark.parametrize(
    "change", ["candidate", "public_input", "wrapper", "timeout", "version"]
)
def test_drift_is_rejected_before_public_execution(public_case, change):
    environment, _, executable = public_case
    adapter, _ = bind(public_case)
    candidate = adapter.candidate_tree_sha256()
    paths = {
        "candidate": environment.workspace / "submission/model.va",
        "public_input": environment.workspace / "task/visible_test.scs",
        "wrapper": environment.tools_dir / "evas",
    }
    if change in paths:
        paths[change].chmod(0o644)
        paths[change].write_text("changed\n")
    elif change == "timeout":
        environment.config.timeout = 9
    else:
        executable.write_text("#!/bin/sh\necho 'evas-sim 0.8.6'\n")
    with pytest.raises(ValueError):
        adapter.validate(candidate_tree_sha256=candidate)
    assert environment.evas_invocations == []


def test_unsupported_public_contract_cannot_fall_back_to_legacy_checker(public_case):
    environment, _, _ = public_case
    path = environment.workspace / "task/evas_runtime.json"
    contract = json.loads(path.read_text())
    contract["schema_version"] = "r52-direct-evas-testbench-reference-v1"
    path.write_text(json.dumps(contract))
    with pytest.raises(ValueError, match="unsupported"):
        bind(public_case)
    assert environment.evas_invocations == []


def test_drift_during_execution_invalidates_adapter_before_feedback(public_case):
    environment, _, executable = public_case
    executable.write_text(
        "#!/bin/bash\n"
        "if [[ $1 == --version ]]; then echo 'evas-sim 0.8.7 (test double)'; exit; fi\n"
        "echo changed > public/submission/model.va\n"
        "echo DO_NOT_DELIVER_THIS_RESULT\n"
    )
    adapter, _ = bind(public_case)
    candidate = adapter.candidate_tree_sha256()
    with pytest.raises(ValueError, match="candidate drift"):
        adapter.validate(candidate_tree_sha256=candidate)
    (environment.workspace / "submission/model.va").write_text(
        "module model; endmodule\n"
    )
    with pytest.raises(ValueError, match="invalidated"):
        adapter.validate(candidate_tree_sha256=candidate)
    assert len(environment.evas_invocations) == 1


def test_non_docker_environment_requires_explicit_test_override(public_case):
    environment, _, _ = public_case
    with pytest.raises(ValueError, match="Docker"):
        validation.build_public_validation_profile(
            environment=environment,
            release=RELEASE,
            campaign_config_sha256="a" * 64,
        )


@pytest.mark.parametrize("exit_code,expected_status", [(0, "succeeded"), (7, "failed")])
def test_process_status_and_truncation_are_not_task_correctness(
    public_case, exit_code, expected_status
):
    _, _, executable = public_case
    executable.write_text(
        "#!/bin/bash\n"
        "if [[ $1 == --version ]]; then echo 'evas-sim 0.8.7 (test double)'; exit; fi\n"
        "printf '%15000s' x\n"
        f"exit {exit_code}\n"
    )
    adapter, profile = bind(public_case)
    # Caller mutation must not change the adapter's frozen identity.
    profile["runtime_identity_sha256"] = "b" * 64
    observation = adapter.validate(
        candidate_tree_sha256=adapter.candidate_tree_sha256()
    )
    assert observation.status == expected_status
    assert observation.payload["returncode"] == exit_code
    assert observation.truncated
    assert len(observation.payload["output"]) < 15000
    assert not {"passed", "score", "metric"}.intersection(observation.payload)


@pytest.mark.parametrize("corruption", ["missing", "hash_error", "wrong_schema", "wrong_candidate"])
def test_invalid_invocation_evidence_cannot_reach_observation(
    public_case, monkeypatch, corruption
):
    environment, _, _ = public_case
    adapter, _ = bind(public_case)
    execute = environment.execute

    def corrupt(action):
        result = execute(action)
        if corruption == "missing":
            environment.evas_invocations.clear()
        elif corruption == "hash_error":
            environment.evas_invocations[-1]["candidate_tree_sha256"] = (
                mini.CANDIDATE_TREE_HASH_ERROR_SHA256
            )
        elif corruption == "wrong_candidate":
            environment.evas_invocations[-1]["candidate_tree_sha256"] = "b" * 64
        else:
            environment.evas_invocations[-1]["candidate_tree_schema_version"] = (
                "unknown"
            )
        return result

    monkeypatch.setattr(environment, "execute", corrupt)
    with pytest.raises(ValueError, match="invocation"):
        adapter.validate(candidate_tree_sha256=adapter.candidate_tree_sha256())


def test_public_timeout_retains_process_disposition(public_case):
    environment, _, executable = public_case
    # Leave room for the wrapper's real Python hash probe to start under suite
    # contention. A timeout before START is correctly rejected as missing evidence.
    environment.config.timeout = 5
    executable.write_text(
        "#!/bin/bash\n"
        "if [[ $1 == --version ]]; then echo 'evas-sim 0.8.7 (test double)'; exit; fi\n"
        "echo before-timeout\nsleep 30\n"
    )
    adapter, _ = bind(public_case)
    observation = adapter.validate(
        candidate_tree_sha256=adapter.candidate_tree_sha256()
    )
    assert observation.status == "timed_out"
    assert observation.payload["returncode"] is None
    assert "before-timeout" in observation.payload["output"]


def _controller_smoke(environment, context, adapter, evidence_root):
    """Test-only routing seam; not an activated production domain tool."""
    seen = []

    class RepeatValidationPolicy:
        def act(self, observation):
            seen.append(observation)
            return AgentAction(
                action_id=f"{context.attempt_id}/action-{len(seen)}",
                tool_name="run_evas",
                arguments={},
                source_backend="deterministic-public-validation-smoke",
                candidate_tree_sha256=observation.candidate_tree_sha256,
            )

    class ValidationEnvironment:
        def start(self, received_context):
            assert received_context == context
            return Observation(
                observation_id="task",
                tool_name="task",
                status="ready",
                payload={"instruction": "Validate the current public candidate."},
                candidate_tree_sha256=adapter.candidate_tree_sha256(),
            )

        def step(self, action, capability):
            assert capability.handler_id == "smoke.public_evas"
            return EnvironmentStep(
                observation=adapter.validate(
                    candidate_tree_sha256=action.candidate_tree_sha256
                ),
                done=False,
            )

        def freeze_submission(self):
            raise AssertionError("budget exhaustion cannot submit")

        def close(self):
            environment.close()

    class UnusedJudge:
        def judge(self, submission):
            raise AssertionError("no terminal score is requested by this smoke")

    descriptor = {
        "schema_version": "vaevas-tool-descriptor-v1",
        "tool_id": "smoke/public-evas",
        "tool_name": "run_evas",
        "tool_version": "1",
        "lifecycle": "active",
        "model_visibility": "model_visible",
        "allowed_conditions": [context.condition],
        "budget_class": "public_validation",
        "state_effect": "read_only",
        "candidate_effect": "read",
        "argument_schema": {"type": "object"},
        "observation_schema": {"type": "object"},
        "handler_id": "smoke.public_evas",
        "evidence_policy": {
            "records_private_evidence": False,
            "may_enter_model_observation": True,
            "may_enter_shared_memory": False,
            "requires_candidate_binding": True,
        },
    }
    trajectory_path = evidence_root / "trajectory.jsonl"
    result = EpisodeController(
        policy=RepeatValidationPolicy(),
        environment=ValidationEnvironment(),
        final_judge=UnusedJudge(),
        tool_registry=ToolRegistry([descriptor]),
        public_validation_profile_sha256=adapter.profile_sha256,
        trajectory=JsonlTrajectoryRecorder(trajectory_path),
    ).run(context)
    assert result.failure is not None
    assert result.failure.category == "public_validation_budget_exhausted", result
    assert len(environment.evas_invocations) == 1
    assert len(seen) == 2
    observation = seen[1]
    events = read_trajectory(trajectory_path)
    assert validate_trajectory_semantics(events)
    public_events = [
        event for event in events if event["event_type"] == "environment_observed"
    ]
    assert len(public_events) == 1
    assert public_events[0]["payload"]["payload_sha256"] == observation.payload_sha256
    assert (
        public_events[0]["payload"]["validation_profile_sha256"]
        == adapter.profile_sha256
    )
    assert (
        public_events[0]["payload"]["candidate_tree_sha256"]
        == observation.candidate_tree_sha256
    )
    assert not any(
        event["event_type"] == "final_judgment_completed" for event in events
    )
    return observation, events


def test_controller_records_real_feedback_and_stops_before_second_execution(
    public_case, tmp_path
):
    environment, _, executable = public_case
    context = EpisodeContext(
        "cell-001",
        "attempt-001",
        "v4-001",
        "Agentic",
        2,
        budget_limits={"tool_calls": 2, "public_validation_calls": 1},
    )
    adapter, _ = bind((environment, context, executable))
    observation, _ = _controller_smoke(environment, context, adapter, tmp_path)
    assert "public simulator diagnostic" in observation.payload["output"]
    assert "FINAL_PRIVATE_SENTINEL" not in json.dumps(observation.to_document())


@pytest.mark.parametrize("task_id,form", [("v4-001", "dut"), ("v4-501", "testbench")])
def test_r53_docker_public_validation_native_trajectory_smoke(tmp_path, task_id, form):
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in real r53 public EVAS Docker smoke")
    from scripts import run_v4_r53_clean_room_smoke as smoke
    from result_protocol import snapshot_submission

    exporter_path = (
        ROOT
        / "benchmark-vabench-release-v4/operations/tri_form_derivation_prep"
        / "export_tri_form_runtime.py"
    )
    spec = importlib.util.spec_from_file_location(
        "public_smoke_exporter", exporter_path
    )
    assert spec is not None and spec.loader is not None
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    row = smoke.task_index_row(RELEASE, task_id)
    artifacts = smoke.public_stub_artifacts(smoke.public_contract(RELEASE, task_id))
    runtime = tmp_path / "runtime"
    # Only the public export path is used; no task record/private binding/checker reads.
    exporter.install_public(RELEASE / row["task_dir"], runtime / "public", form, "G2")
    submission = runtime / "public/submission"
    submission.mkdir()
    for name, content in artifacts.items():
        (submission / name).write_text(content)
    environment = mini.VaBenchBashEnvironment(
        runtime,
        timeout_s=60,
        sandbox_backend="docker",
        evas_command="",
        docker_image=os.environ.get(
            "VABENCH_TEST_DOCKER_IMAGE", mini.DEFAULT_DOCKER_IMAGE
        ),
        candidate_artifacts=tuple(sorted(artifacts)),
        submission_gate=lambda _: {"passed": False},
    )
    try:
        context = EpisodeContext(
            f"public-smoke-{task_id}",
            "public-smoke-attempt-001",
            task_id,
            "Agentic",
            2,
            budget_limits={"tool_calls": 2, "public_validation_calls": 1},
        )
        profile = validation.build_public_validation_profile(
            environment=environment,
            release=RELEASE,
            campaign_config_sha256=smoke.canonical_sha256(
                {
                    "fixture": "public-validation-smoke-v1",
                    "task_id": context.task_id,
                    "max_steps": 2,
                    "budgets": dict(context.budget_limits),
                }
            ),
        )
        adapter = validation.PublicEvasValidator(
            environment=environment,
            context=context,
            public_validation_profile=profile,
        )
        observation, events = _controller_smoke(environment, context, adapter, tmp_path)
        assert observation.status == "succeeded", observation.to_document()
        assert observation.payload["feedback_scope"] == (
            "reference_dut_only" if form == "testbench" else "public_simulation_only"
        )
        config = environment.serialize()["info"]["config"]["environment"]
        assert config["network"] is False
        assert config["evaluator_mounted"] is False
        assert config["image_id"].startswith("sha256:")
        assert not (runtime / "evaluator").exists()
        # Separately verify the public candidate hash agrees with the existing freeze format.
        frozen = snapshot_submission(
            runtime, {"passed": True, "expected_artifacts": list(artifacts)}
        )
        assert frozen["tree_sha256"] == observation.candidate_tree_sha256
        with pytest.raises(ValueError, match="terminal"):
            adapter.validate(candidate_tree_sha256=frozen["tree_sha256"])
        smoke.write_json(
            tmp_path / "public-validation-smoke.json",
            {
                "status": "PASS",
                "claim_scope": "single_task_public_adapter_native_trajectory",
                "model_score_claim_allowed": False,
                "paper_result_claim_allowed": False,
                "profile": profile,
                "observation": observation.to_document(),
                "trajectory_tail_sha256": events[-1]["event_sha256"],
                "final_submission": frozen,
                "final_score_executed": False,
                "budget_rejected_before_second_call": True,
                "environment": config,
            },
        )
    finally:
        environment.close()
