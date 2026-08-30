from __future__ import annotations

# Imported pytest fixtures are intentionally shadowed by injected arguments.
# ruff: noqa: F811

from dataclasses import replace
import json
from pathlib import Path

import jsonschema
import pytest

from test_agent_harness_native_episode import native_case as native_case  # noqa: F401
from test_agent_harness_production_public_validation import public_case as public_case  # noqa: F401
from runners.agent_harness import (
    JsonlTrajectoryRecorder,
    ToolRegistry,
    read_trajectory,
    result_artifact_sha256,
    validate_scored_result_artifact,
    validate_trajectory_semantics,
)
from runners.agent_harness.backends.mini_swe import mini_swe_bash_tool_descriptor


@pytest.mark.parametrize("payload", [None, [], "invalid"])
def test_absence_validation_rejects_malformed_start_payload(payload):
    from runners.agent_harness.trajectory import validate_absent_public_authority

    assert not validate_absent_public_authority([{"payload": payload}])


def test_native_no_evas_can_score_without_a_public_authority(native_case):
    import native_episode

    arguments, seen, _ = native_case
    arguments["context"] = replace(arguments["context"], condition="Agent-No-EVAS")
    arguments["tool_registry"] = ToolRegistry(
        [mini_swe_bash_tool_descriptor(allowed_conditions=["Agent-No-EVAS"])]
    )
    arguments["public_validation_profile"] = None
    run = native_episode.run_native_episode(**arguments)

    assert run.result.primary_outcome == "behavior_failure"
    assert run.artifact_path is not None
    assert "FINAL_JUDGE_SENTINEL" not in json.dumps(seen)
    artifact = json.loads(run.artifact_path.read_text())
    assert artifact["schema_version"] == "vaevas-result-artifact-v2"
    assert artifact["contract_identity"]["public_validation_profile_sha256"] is None
    jsonschema.validate(
        artifact,
        json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas/vaevas-result-artifact-v2.schema.json"
            ).read_text()
        ),
    )
    request = json.loads((run.trajectory_path.parent / "request.json").read_text())
    assert request["schema_version"] == "vaevas-native-episode-request-v2"
    assert request["public_validation_profile"] is None
    assert request["public_validation_profile_sha256"] is None
    sidecar = json.loads(
        (arguments["runtime"] / run.score_sidecar_receipt["path"]).read_text()
    )
    assert validate_scored_result_artifact(
        artifact,
        trajectory_events=read_trajectory(run.trajectory_path),
        score_sidecar=sidecar,
        public_validation_profile=None,
        final_test_profile=arguments["final_test_profile"],
    )


@pytest.mark.parametrize("condition", ["OneShot", "Agent-No-EVAS"])
def test_no_feedback_conditions_reject_enabled_public_authority(native_case, condition):
    import native_episode

    arguments, seen, _ = native_case
    arguments["context"] = replace(arguments["context"], condition=condition)
    with pytest.raises(ValueError, match="forbidden"):
        native_episode.run_native_episode(**arguments)
    assert seen == []


def test_agentic_cannot_omit_public_authority(native_case):
    import native_episode

    arguments, seen, _ = native_case
    arguments["public_validation_profile"] = None
    with pytest.raises(ValueError, match="required"):
        native_episode.run_native_episode(**arguments)
    assert seen == []


def test_absent_public_authority_cannot_expose_a_validation_capability(native_case):
    import native_episode
    from test_agent_harness_authority_runtime import _descriptor

    arguments, seen, _ = native_case
    arguments["context"] = replace(arguments["context"], condition="Agent-No-EVAS")
    arguments["public_validation_profile"] = None
    descriptor = _descriptor()
    descriptor["allowed_conditions"] = ["Agent-No-EVAS"]
    arguments["tool_registry"] = ToolRegistry(
        [
            mini_swe_bash_tool_descriptor(allowed_conditions=["Agent-No-EVAS"]),
            descriptor,
        ]
    )
    with pytest.raises(ValueError, match="public-validation capability"):
        native_episode.run_native_episode(**arguments)
    assert seen == []


@pytest.mark.parametrize(
    "event_kind,updates",
    [
        ("environment_observed", {"validation_profile_sha256": "a" * 64}),
        ("budget_updated", {"budget_class": "public_validation"}),
        ("episode_started", {"public_validation_profile_sha256": "a" * 64}),
    ],
)
def test_absent_artifact_rejects_rehashed_public_validation_evidence(
    native_case,
    tmp_path,
    event_kind,
    updates,
):
    import native_episode

    arguments, _, _ = native_case
    arguments["context"] = replace(arguments["context"], condition="Agent-No-EVAS")
    arguments["tool_registry"] = ToolRegistry(
        [mini_swe_bash_tool_descriptor(allowed_conditions=["Agent-No-EVAS"])]
    )
    arguments["public_validation_profile"] = None
    run = native_episode.run_native_episode(**arguments)
    forged_path = tmp_path / "rehashed.jsonl"
    recorder = JsonlTrajectoryRecorder(forged_path)
    found = False
    for event in read_trajectory(run.trajectory_path):
        payload = dict(event["payload"])
        if event["event_type"] == event_kind:
            payload.update(updates)
            found = True
        recorder.append(
            context=arguments["context"],
            actor=event["actor"],
            event_type=event["event_type"],
            visibility=event["visibility"],
            payload=payload,
        )
    assert found
    events = read_trajectory(forged_path)
    assert validate_trajectory_semantics(events)
    artifact = json.loads(run.artifact_path.read_text())
    artifact["trajectory"]["tail_sha256"] = recorder.tail_sha256
    artifact["artifact_sha256"] = result_artifact_sha256(artifact)
    sidecar = json.loads(
        (arguments["runtime"] / run.score_sidecar_receipt["path"]).read_text()
    )
    assert not validate_scored_result_artifact(
        artifact,
        trajectory_events=events,
        score_sidecar=sidecar,
        public_validation_profile=None,
        final_test_profile=arguments["final_test_profile"],
    )


@pytest.mark.parametrize("injection_phase", ["start", "step"])
def test_unbound_feedback_is_rejected_before_policy_or_judge(
    native_case, injection_phase
):
    import native_episode

    arguments, seen, _ = native_case
    arguments["context"] = replace(arguments["context"], condition="Agent-No-EVAS")
    arguments["tool_registry"] = ToolRegistry(
        [mini_swe_bash_tool_descriptor(allowed_conditions=["Agent-No-EVAS"])]
    )
    arguments["public_validation_profile"] = None
    wrapped = arguments["environment"]

    class InvalidFeedbackEnvironment:
        """Adversarial environment boundary with an undeclared feedback source."""

        def start(self, context):
            observation = wrapped.start(context)
            return (
                replace(observation, validation_profile_sha256="a" * 64)
                if injection_phase == "start"
                else observation
            )

        def step(self, action, capability):
            step = wrapped.step(action, capability)
            return replace(
                step,
                observation=replace(
                    step.observation, validation_profile_sha256="a" * 64
                ),
            )

        def freeze_submission(self):
            return wrapped.freeze_submission()

        def close(self):
            wrapped.close()

    arguments["environment"] = InvalidFeedbackEnvironment()
    run = native_episode.run_native_episode(**arguments)
    assert run.result.primary_outcome == "protocol_failure"
    assert run.result.failure.category == "public_validation_profile_unbound"
    assert len(seen) == (0 if injection_phase == "start" else 1)
    assert not (arguments["runtime"] / "judge-called").exists()
    assert run.artifact_path is None
    events = read_trajectory(run.trajectory_path)
    assert validate_trajectory_semantics(events)
    assert not any(event["event_type"] == "environment_observed" for event in events)
