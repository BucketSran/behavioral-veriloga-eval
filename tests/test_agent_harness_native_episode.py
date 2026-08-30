from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import sys
from types import SimpleNamespace

import pytest

from runners.agent_harness import (
    AgentAction,
    EnvironmentStep,
    EpisodeContext,
    FrozenSubmission,
    ToolRegistry,
    read_trajectory,
    project_model_visible_events,
    validate_scored_result_artifact,
)
from runners.agent_harness.backends.mini_swe import (
    MiniSweBashEnvironmentBridge,
    MiniSwePolicyBridge,
    mini_swe_bash_tool_descriptor,
)
from test_agent_harness_production_public_validation import (
    bind,
    public_case as public_case,
)

import final_replay
import run_campaign as runner


class Submitted(Exception):
    pass


def test_native_runtime_is_resolved_before_replay_changes_working_directory(
    native_case, monkeypatch
):
    import native_episode

    arguments, _, _ = native_case
    runtime = arguments["runtime"]
    monkeypatch.chdir(runtime.parent)
    arguments["runtime"] = Path(runtime.name)
    run = native_episode.run_native_episode(**arguments)
    assert run.result.primary_outcome == "behavior_failure", run.result
    assert run.artifact_path.is_absolute()


@pytest.fixture
def native_case(public_case, tmp_path):  # noqa: F811 - shared pytest fixture
    environment, context, executable = public_case
    runtime = environment.runtime
    adapter, public_profile = bind(public_case)
    (runtime / "evaluator/score_policy.json").write_text(
        json.dumps({"candidate_artifacts": ["model.va"]})
    )
    judge = tmp_path / "judge.py"
    judge.write_text(
        "import os, json\nfrom pathlib import Path\n"
        "root = Path(os.environ['VABENCH_RUNTIME_DIR'])\n"
        "assert Path(os.environ['VABENCH_SUBMISSION_DIR']) == root / 'evidence/final_submission'\n"
        "(root / 'judge-called').touch()\n"
        "Path(os.environ['VABENCH_TRUSTED_REPLAY_RESULT']).write_text(json.dumps({'status': 'behavior_failure', 'private': 'FINAL_JUDGE_SENTINEL'}))\n"
    )
    command = shlex.join([sys.executable, str(judge)])
    final_profile = final_replay.build_final_test_profile(
        runtime=runtime,
        release=runner.DEFAULT_RELEASE,
        campaign_config_sha256=public_profile["campaign_config_sha256"],
        command=command,
        timeout_s=10,
        evas_command=str(executable),
    )
    gate = {"passed": True, "expected_artifacts": ["model.va"], "diagnostics": []}
    environment.submission_gate = lambda _: gate
    environment.bind_submitted_exception(Submitted)

    def freeze():
        manifest = runner.RESULT_PROTOCOL.snapshot_submission(runtime, gate)
        return FrozenSubmission(manifest["tree_sha256"], ("model.va",))

    bridge = MiniSweBashEnvironmentBridge(
        legacy_environment=environment,
        task_payload={"instruction": "submit model.va"},
        candidate_tree_sha256=adapter.candidate_tree_sha256,
        freeze_submission=freeze,
        submitted_exception_types=(Submitted,),
    )
    seen = []

    def propose(observation):
        assert not (runtime / "judge-called").exists()
        seen.append(observation.to_document())
        return [
            {
                "type": "function",
                "function": {
                    "name": "bash",
                    "arguments": json.dumps({"command": "vabench-submit"}),
                },
            }
        ]

    return (
        dict(
            runtime=runtime,
            context=context,
            policy=MiniSwePolicyBridge(
                propose=propose, action_id_prefix=context.attempt_id
            ),
            environment=bridge,
            tool_registry=ToolRegistry(
                [mini_swe_bash_tool_descriptor(allowed_conditions=[context.condition])]
            ),
            backend_profile_sha256="b" * 64,
            public_validation_profile=public_profile,
            final_test_profile=final_profile,
            command=command,
            timeout_s=10,
            evas_command=str(executable),
        ),
        seen,
        adapter,
    )


def test_native_episode_joins_real_freeze_replay_and_immutable_result(native_case):
    import native_episode

    arguments, seen, _ = native_case
    run = native_episode.run_native_episode(**arguments)

    assert run.result.primary_outcome == "behavior_failure", run.result
    assert run.result.failure is None
    assert len(seen) == 1
    assert "FINAL_JUDGE_SENTINEL" not in json.dumps(seen)
    artifact = json.loads(run.artifact_path.read_text())
    events = read_trajectory(run.trajectory_path)
    receipt = run.score_sidecar_receipt
    sidecar = json.loads((arguments["runtime"] / receipt["path"]).read_text())
    assert validate_scored_result_artifact(
        artifact,
        trajectory_events=events,
        score_sidecar=sidecar,
        public_validation_profile=arguments["public_validation_profile"],
        final_test_profile=arguments["final_test_profile"],
    )
    assert artifact["trajectory"]["tail_sha256"] == run.result.trajectory_tail_sha256
    assert artifact["submission"]["tree_sha256"] == run.result.submission.tree_sha256
    assert artifact["score_sidecar"]["score_authority"] == "development_only"
    assert run.artifact_path.stat().st_mode & 0o222 == 0
    assert run.trajectory_path.stat().st_mode & 0o222 == 0


def test_native_deadline_result_retains_timeout_and_real_score(native_case):
    import native_episode

    arguments, seen, adapter = native_case
    run = native_episode.run_native_episode(
        **arguments, deadline_monotonic=0.0,
        deadline_finalizer=adapter.candidate_tree_sha256,
    )
    assert seen == []
    assert run.result.terminal_reason == "agent_timeout"
    assert run.result.final_judgment.status == "behavior_failure"
    artifact = json.loads(run.artifact_path.read_text())
    assert artifact["episode"]["terminal_reason"] == "agent_timeout"


def test_failed_native_attempt_blocks_both_native_and_legacy_reentry(native_case):
    import native_episode

    arguments, _, _ = native_case

    class FailedPolicy:
        def act(self, observation):
            raise RuntimeError("provider unavailable")

    arguments["policy"] = FailedPolicy()
    run = native_episode.run_native_episode(**arguments)
    assert run.result.failure.category == "backend_failure"
    assert run.artifact_path is None
    assert run.score_sidecar_receipt is None
    assert not (arguments["runtime"] / "judge-called").exists()
    outcome = json.loads((run.trajectory_path.parent / "outcome.json").read_text())
    assert outcome["primary_outcome"] == "infrastructure_failure"
    before = run.trajectory_path.read_bytes()
    with pytest.raises(RuntimeError, match="native episode.*reserved"):
        native_episode.run_native_episode(**arguments)
    with pytest.raises(RuntimeError, match="native episode.*reserved"):
        runner.run_cell(
            {"cell_id": arguments["runtime"].name},
            SimpleNamespace(output=arguments["runtime"].parent, resume=True),
            None,
        )
    assert run.trajectory_path.read_bytes() == before


@pytest.mark.parametrize(
    "marker",
    ["final_submission", "campaign_result.json", "conversation_checkpoint.json"],
)
def test_native_entry_rejects_used_generation_runtime_before_policy(
    native_case, marker
):
    import native_episode

    arguments, seen, _ = native_case
    path = arguments["runtime"] / "evidence" / marker
    path.parent.mkdir(exist_ok=True)
    path.write_text("prior attempt evidence")
    with pytest.raises(RuntimeError, match="fresh runtime"):
        native_episode.run_native_episode(**arguments)
    assert seen == []
    assert path.read_text() == "prior attempt evidence"
    assert not (path.parent / "native-episode").exists()


@pytest.mark.parametrize(
    "field", ["benchmark_manifest_sha256", "campaign_config_sha256"]
)
def test_profile_mismatch_stops_before_generation(native_case, field):
    import native_episode

    arguments, seen, _ = native_case
    arguments["final_test_profile"][field] = "c" * 64
    with pytest.raises(ValueError, match="authority mismatch"):
        native_episode.run_native_episode(**arguments)
    assert seen == []
    assert not (arguments["runtime"] / "evidence/native-episode").exists()


@pytest.mark.parametrize(
    "drift",
    ["attempt_id", "path", "sha256", "final_profile_input_identity_sha256", "bytes"],
)
def test_bad_published_receipt_never_becomes_a_scored_native_row(
    native_case, monkeypatch, drift
):
    import native_episode

    arguments, seen, _ = native_case
    execute = runner.run_trusted_replay

    def replay_then_corrupt(*args, **kwargs):
        replay = execute(*args, **kwargs)
        receipt = replay["score_sidecar_receipt"]
        if drift == "bytes":
            path = arguments["runtime"] / receipt["path"]
            path.chmod(0o644)
            path.write_text("{}")
        else:
            receipt[drift] = "invalid"
        return replay

    monkeypatch.setattr(runner, "run_trusted_replay", replay_then_corrupt)
    run = native_episode.run_native_episode(**arguments)
    assert run.result.failure.category == "final_judge_failure"
    assert run.artifact_path is None
    assert run.score_sidecar_receipt is None
    assert len(seen) == 1
    assert (arguments["runtime"] / "evidence/bound-final-test").is_dir()


def test_missing_structured_verdict_retains_infrastructure_null_score(native_case):
    import native_episode

    arguments, _, _ = native_case
    judge = Path(shlex.split(arguments["command"])[1])
    judge.write_text("# no structured verdict\n")
    arguments["final_test_profile"] = final_replay.build_final_test_profile(
        runtime=arguments["runtime"],
        release=runner.DEFAULT_RELEASE,
        campaign_config_sha256=arguments["public_validation_profile"][
            "campaign_config_sha256"
        ],
        command=arguments["command"],
        timeout_s=10,
        evas_command=arguments["evas_command"],
    )
    run = native_episode.run_native_episode(**arguments)
    assert run.result.primary_outcome == "infrastructure_failure"
    assert (
        run.result.failure is None
    )  # The judge ran and classified infrastructure failure.
    artifact = json.loads(run.artifact_path.read_text())
    assert artifact["final_judgment"]["score"] is None


def test_artifact_publish_failure_keeps_final_reserved_without_model_reentry(
    native_case, monkeypatch
):
    import native_episode
    from runners.agent_harness import result_store

    arguments, seen, _ = native_case
    publish = result_store._publish_exclusive

    def fail_only_result(source, destination):
        if destination.parent.name == "scored-results":
            raise OSError("disk full")
        publish(source, destination)

    monkeypatch.setattr(result_store, "_publish_exclusive", fail_only_result)
    with pytest.raises(result_store.ImmutableEvidenceError, match="disk full"):
        native_episode.run_native_episode(**arguments)
    assert len(seen) == 1
    assert list((arguments["runtime"] / "evidence/score-sidecars").glob("*.json"))
    assert not list(
        (arguments["runtime"] / "evidence/native-episode/scored-results").iterdir()
    )
    with pytest.raises(RuntimeError, match="reserved"):
        native_episode.run_native_episode(**arguments)


def _with_public_validation(arguments, adapter, seen):
    """Test-only dispatcher: NOT a production model-tool capability activation."""
    bridge, policy = arguments["environment"], arguments["policy"]
    context = arguments["context"]

    class ValidateThenSubmit:
        validated = False

        def act(self, observation):
            if self.validated:
                return policy.act(observation)
            self.validated = True
            seen.append(observation.to_document())
            return AgentAction(
                action_id="public-validation-001",
                tool_name="run_evas",
                arguments={},
                source_backend="test-only-public-dispatch",
                candidate_tree_sha256=observation.candidate_tree_sha256,
            )

    class PublicEnvironment:
        def start(self, received):
            return bridge.start(received)

        def step(self, action, capability):
            if capability.handler_id == "smoke.public_evas":
                assert action.arguments == {}
                return EnvironmentStep(
                    observation=adapter.validate(
                        candidate_tree_sha256=action.candidate_tree_sha256
                    ),
                    done=False,
                )
            return bridge.step(action, capability)

        def freeze_submission(self):
            return bridge.freeze_submission()

        def close(self):
            bridge.close()

    bash = mini_swe_bash_tool_descriptor(allowed_conditions=[context.condition])
    public = {
        **bash,
        "tool_id": "smoke/public-evas",
        "tool_name": "run_evas",
        "handler_id": "smoke.public_evas",
        "budget_class": "public_validation",
        "state_effect": "read_only",
        "candidate_effect": "read",
        "argument_schema": {"type": "object", "additionalProperties": False},
        "observation_schema": {"type": "object"},
        "evidence_policy": {
            **bash["evidence_policy"],
            "may_enter_shared_memory": False,
        },
    }
    return {
        **arguments,
        "policy": ValidateThenSubmit(),
        "environment": PublicEnvironment(),
        "tool_registry": ToolRegistry([bash, public]),
    }


def _assert_public_final_join(run, arguments, seen):
    assert run.result.primary_outcome == "behavior_failure", run.result
    assert run.result.failure is None
    assert len(seen) == 2
    assert seen[1]["tool_name"] == "run_evas"
    assert seen[1]["validation_profile_sha256"]
    assert seen[1]["candidate_tree_sha256"] == run.result.submission.tree_sha256
    events = read_trajectory(run.trajectory_path)
    types = [event["event_type"] for event in events]
    assert types.index("environment_observed") < types.index("submission_frozen")
    assert types.index("submission_frozen") < types.index("final_judgment_completed")
    assert "final_judgment_completed" not in [
        event["event_type"] for event in project_model_visible_events(events)
    ]
    assert "FINAL_JUDGE_SENTINEL" not in json.dumps(seen)
    artifact = json.loads(run.artifact_path.read_text())
    sidecar = json.loads(
        (arguments["runtime"] / run.score_sidecar_receipt["path"]).read_text()
    )
    assert validate_scored_result_artifact(
        artifact,
        trajectory_events=events,
        score_sidecar=sidecar,
        public_validation_profile=arguments["public_validation_profile"],
        final_test_profile=arguments["final_test_profile"],
    )


def test_public_feedback_and_final_result_share_one_native_trajectory(native_case):
    import native_episode

    arguments, seen, adapter = native_case
    arguments = _with_public_validation(arguments, adapter, seen)
    run = native_episode.run_native_episode(**arguments)
    _assert_public_final_join(run, arguments, seen)


def test_r53_docker_native_episode_result_join(tmp_path):
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in real r53 native episode / final result join")
    import native_episode
    import mini_swe_vabench as mini
    import public_validation as validation
    from scripts import run_v4_r53_clean_room_smoke as smoke

    release = runner.DEFAULT_RELEASE
    # Derive fixture ONLY from the public contract, before trusted export.
    artifacts = smoke.public_stub_artifacts(smoke.public_contract(release, "v4-001"))
    cell = next(
        row
        for row in smoke.three_arm_cells(release, "v4-001", smoke.DEFAULT_MODEL)
        if row["experimental_arm"] == "Agentic"
    )
    runtime = tmp_path / "runtime"
    runner.export_runtime(cell, release, runtime, timeout_s=60)
    for name, content in artifacts.items():
        (runtime / "public/submission" / name).write_text(content)
    context = EpisodeContext(
        "native-smoke-v4-001",
        "native-smoke-attempt-001",
        "v4-001",
        "Agentic",
        2,
        budget_limits={"tool_calls": 2, "public_validation_calls": 1},
    )
    environment = mini.VaBenchBashEnvironment(
        runtime,
        timeout_s=60,
        sandbox_backend="docker",
        evas_command="",
        docker_image=os.environ.get(
            "VABENCH_TEST_DOCKER_IMAGE", mini.DEFAULT_DOCKER_IMAGE
        ),
        candidate_artifacts=tuple(sorted(artifacts)),
        submission_gate=runner.submission_artifact_gate,
    )
    try:
        environment.bind_submitted_exception(Submitted)
        campaign_sha = smoke.canonical_sha256(
            {
                "fixture": "native-result-join-smoke-v1",
                "cell": cell,
                "max_steps": context.max_steps,
                "budgets": dict(context.budget_limits),
            }
        )
        public_profile = validation.build_public_validation_profile(
            environment=environment,
            release=release,
            campaign_config_sha256=campaign_sha,
        )
        adapter = validation.PublicEvasValidator(
            environment=environment,
            context=context,
            public_validation_profile=public_profile,
        )
        command = shlex.join(
            [sys.executable, str(smoke.CALIBRATION / "trusted_replay_adapter.py")]
        )
        evas_command = str(smoke.ROOT / ".venv/bin/evas")
        final_profile = final_replay.build_final_test_profile(
            runtime=runtime,
            release=release,
            campaign_config_sha256=campaign_sha,
            command=command,
            timeout_s=150,
            evas_command=evas_command,
        )

        def freeze():
            manifest = runner.RESULT_PROTOCOL.snapshot_submission(
                runtime, runner.submission_artifact_gate(runtime)
            )
            return FrozenSubmission(manifest["tree_sha256"], tuple(sorted(artifacts)))

        bridge = MiniSweBashEnvironmentBridge(
            legacy_environment=environment,
            task_payload={
                "instruction": "Validate and submit the public-contract fixture."
            },
            candidate_tree_sha256=adapter.candidate_tree_sha256,
            freeze_submission=freeze,
            submitted_exception_types=(Submitted,),
        )
        seen = []

        def propose(observation):
            assert not (runtime / "evidence/bound-final-test").exists()
            seen.append(observation.to_document())
            return [smoke.tool_call("bash", {"command": "vabench-submit"}, 1)]

        arguments = _with_public_validation(
            dict(
                runtime=runtime,
                context=context,
                environment=bridge,
                policy=MiniSwePolicyBridge(
                    propose=propose, action_id_prefix=context.attempt_id
                ),
                backend_profile_sha256=smoke.canonical_sha256(
                    {"fixture": "scripted-native-smoke-v1"}
                ),
                public_validation_profile=public_profile,
                final_test_profile=final_profile,
                command=command,
                timeout_s=150,
                evas_command=evas_command,
            ),
            adapter,
            seen,
        )
        run = native_episode.run_native_episode(**arguments)
        _assert_public_final_join(run, arguments, seen)
        config = environment.serialize()["info"]["config"]["environment"]
        assert config["network"] is False
        assert config["evaluator_mounted"] is False
        assert len(environment.evas_invocations) == 1
        assert seen[1]["status"] == "succeeded"
        with pytest.raises(ValueError, match="terminal"):
            adapter.validate(candidate_tree_sha256=run.result.submission.tree_sha256)
        smoke.write_json(
            tmp_path / "native-episode-smoke.json",
            {
                "status": "PASS",
                "claim_scope": "single_task_native_episode_result_join",
                "model_score_claim_allowed": False,
                "paper_result_claim_allowed": False,
                "public_dispatch": "test_only_not_a_production_tool",
                "public_observation": seen[1],
                "environment": config,
                "artifact_path": str(run.artifact_path),
                "artifact": json.loads(run.artifact_path.read_text()),
                "score_sidecar_receipt": run.score_sidecar_receipt,
            },
        )
    finally:
        environment.close()
