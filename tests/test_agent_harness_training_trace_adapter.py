from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import pytest

from runners.agent_harness import (
    EpisodeContext,
    JsonlTrajectoryRecorder,
    read_trajectory,
)
from runners.agent_harness.training_export import (
    TrainingExportError,
    build_training_export,
    validate_training_export,
)
from runners.agent_harness.training_trace_adapter import (
    TrainingTraceAdapterError,
    project_synthetic_native_trace_to_training_source,
)


SHA_A = "a" * 64
SHA_B = "b" * 64


def test_synthetic_native_trace_projects_to_valid_sft_source(tmp_path):
    events = _submitted_trace(tmp_path)
    source = project_synthetic_native_trace_to_training_source(
        events,
        synthetic_metadata=_synthetic_metadata(
            initial_messages=[
                {"role": "user", "content": "Create a tiny Verilog-A module."}
            ],
            labels={"sft": {"authority": "synthetic_fixture", "accepted": True}},
        ),
        split_manifest=_split_manifest(),
        mode="sft",
    )

    exported = build_training_export(
        source, split_manifest=_split_manifest(), mode="sft"
    )

    assert source["source_kind"] == "synthetic"
    assert source["task_id"] == "synthetic/task-001"
    assert (
        "vaevas-synthetic-native-training-adapter-v1" in source["provenance"]["version"]
    )
    trace_sha = hashlib.sha256(
        json.dumps(
            {"events": events},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()
    assert source["provenance"]["version"].endswith(trace_sha)
    assert exported["sft"]["assistant_targets"] == [
        {
            "event_id": "native-action-1",
            "content": (
                '{"arguments_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",'
                '"candidate_tree_sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",'
                '"source_backend":"synthetic-native",'
                '"tool_name":"submit"}'
            ),
        }
    ]
    assert exported["sft"]["environment_observations"]
    assert "public compile passed" not in str(exported["sft"]["assistant_targets"])
    validate_training_export(exported, source=source, split_manifest=_split_manifest())


def test_public_reward_projects_to_valid_rl_source_without_final_score(tmp_path):
    source = project_synthetic_native_trace_to_training_source(
        _submitted_trace(tmp_path),
        synthetic_metadata=_synthetic_metadata(
            initial_messages=[
                {"role": "user", "content": "Create a tiny Verilog-A module."}
            ],
            reward={
                "authority": "public_validation",
                "value": 0.25,
                "definition": "public compile and visible simulation checks",
                "generator_sha256": SHA_A,
            },
        ),
        split_manifest=_split_manifest(),
        mode="rl",
    )

    exported = build_training_export(
        source, split_manifest=_split_manifest(), mode="rl"
    )

    assert exported["rl"]["reward"]["authority"] == "public_validation"
    assert exported["rl"]["final_score_exported"] is False
    assert exported["rl"]["reward"]["value"] == 0.25
    assert "score" not in str(exported["rl"]["public_observations"])
    validate_training_export(exported, source=source, split_manifest=_split_manifest())


@pytest.mark.parametrize(
    ("metadata_update", "match"),
    [
        ({"source_id": "real-source-001"}, "synthetic"),
        (
            {"license": {"spdx": "LicenseRef-Internal", "redistributable": True}},
            "license",
        ),
        (
            {
                "provider_use": {
                    "terms": "synthetic-fixture",
                    "allows_training": True,
                    "raw_provider_payload": True,
                }
            },
            "raw provider payload",
        ),
        (
            {
                "project_authorization": {
                    "project": "private-project",
                    "allows_training_export": True,
                }
            },
            "forbidden",
        ),
    ],
)
def test_adapter_rejects_unauthorized_synthetic_metadata(
    tmp_path, metadata_update, match
):
    metadata = _synthetic_metadata(
        labels={"sft": {"authority": "synthetic_fixture", "accepted": True}},
        **metadata_update,
    )

    with pytest.raises(TrainingExportError, match=match):
        project_synthetic_native_trace_to_training_source(
            _submitted_trace(tmp_path),
            synthetic_metadata=metadata,
            split_manifest=_split_manifest(),
            mode="sft",
        )


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        ("broken_chain", "lifecycle"),
        ("cross_attempt", "lifecycle"),
        ("observation_without_action", "lifecycle"),
        ("unsupported_action_payload", "action payload"),
        ("model_reentry_after_freeze", "lifecycle"),
        ("private_initial_message", "forbidden training material"),
    ],
)
def test_adapter_rejects_malformed_or_leaking_native_traces(tmp_path, mutation, match):
    events = _mutated_trace(_submitted_trace(tmp_path), mutation)
    initial_content = (
        "This contains private hidden material."
        if mutation == "private_initial_message"
        else "Create a tiny Verilog-A module."
    )

    with pytest.raises(TrainingTraceAdapterError, match=match):
        project_synthetic_native_trace_to_training_source(
            events,
            synthetic_metadata=_synthetic_metadata(
                initial_messages=[{"role": "user", "content": initial_content}],
                labels={"sft": {"authority": "synthetic_fixture", "accepted": True}},
            ),
            split_manifest=_split_manifest(),
            mode="sft",
        )


def test_adapter_rejects_final_reward_authority(tmp_path):
    with pytest.raises(TrainingExportError, match="public_validation"):
        project_synthetic_native_trace_to_training_source(
            _submitted_trace(tmp_path),
            synthetic_metadata=_synthetic_metadata(
                reward={
                    "authority": "final_test",
                    "value": 1.0,
                    "definition": "final score",
                    "generator_sha256": SHA_A,
                },
            ),
            split_manifest=_split_manifest(),
            mode="rl",
        )


def test_adapter_requires_mode_specific_training_declaration(tmp_path):
    with pytest.raises(TrainingTraceAdapterError, match="missing \\['labels'\\]"):
        project_synthetic_native_trace_to_training_source(
            _submitted_trace(tmp_path),
            synthetic_metadata=_synthetic_metadata(),
            split_manifest=_split_manifest(),
            mode="sft",
        )
    with pytest.raises(TrainingTraceAdapterError, match="unknown \\['labels'\\]"):
        project_synthetic_native_trace_to_training_source(
            _submitted_trace(tmp_path),
            synthetic_metadata=_synthetic_metadata(
                labels={"sft": {"authority": "synthetic_fixture", "accepted": True}},
            ),
            split_manifest=_split_manifest(),
            mode="rl",
        )


def test_projection_is_deterministic_and_export_validation_detects_mutation(tmp_path):
    kwargs = {
        "synthetic_metadata": _synthetic_metadata(
            initial_messages=[
                {"role": "user", "content": "Create a tiny Verilog-A module."}
            ],
            labels={"sft": {"authority": "synthetic_fixture", "accepted": True}},
        ),
        "split_manifest": _split_manifest(),
        "mode": "sft",
    }
    events = _submitted_trace(tmp_path)
    source_a = project_synthetic_native_trace_to_training_source(events, **kwargs)
    source_b = project_synthetic_native_trace_to_training_source(
        deepcopy(events), **kwargs
    )
    exported = build_training_export(
        source_a, split_manifest=_split_manifest(), mode="sft"
    )
    exported["sft"]["assistant_targets"][0]["content"] = "{}"

    assert source_a == source_b
    with pytest.raises(TrainingExportError, match="does not match"):
        validate_training_export(
            exported, source=source_a, split_manifest=_split_manifest()
        )


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        ("unknown_event_type", "unsupported native event type"),
        ("oversized_payload", "maximum"),
    ],
)
def test_adapter_rejects_unknown_and_oversized_event_documents(
    tmp_path, mutation, match
):
    events = _mutated_trace(_submitted_trace(tmp_path), mutation)

    with pytest.raises(TrainingTraceAdapterError, match=match):
        project_synthetic_native_trace_to_training_source(
            events,
            synthetic_metadata=_synthetic_metadata(
                labels={"sft": {"authority": "synthetic_fixture", "accepted": True}},
            ),
            split_manifest=_split_manifest(),
            mode="sft",
        )


def _submitted_trace(tmp_path):
    context = EpisodeContext(
        episode_id="synthetic-episode-001",
        attempt_id="synthetic-attempt-001",
        task_id="synthetic/task-001",
        condition="Synthetic+Native",
        max_steps=2,
    )
    path = (
        tmp_path / f"trajectory-{len(list(tmp_path.glob('trajectory-*.jsonl')))}.jsonl"
    )
    recorder = JsonlTrajectoryRecorder(path)
    for actor, event_type, visibility, payload in (
        ("controller", "episode_started", "harness", {"budget_limits": {}}),
        (
            "policy",
            "action_proposed",
            "model",
            {
                "schema_version": "vaevas-agent-action-v1",
                "action_id": "native-action-1",
                "tool_name": "submit",
                "arguments_sha256": SHA_A,
                "source_backend": "synthetic-native",
                "candidate_tree_sha256": SHA_B,
            },
        ),
        (
            "controller",
            "action_authorized",
            "harness",
            {
                "action_id": "native-action-1",
                "tool_name": "submit",
                "tool_id": "synthetic/submit",
                "tool_version": "1",
                "handler_id": "synthetic.submit",
                "descriptor_sha256": SHA_A,
                "candidate_tree_sha256": SHA_B,
                "condition": "Synthetic+Native",
                "effective_capability_sha256": SHA_B,
            },
        ),
        (
            "controller",
            "budget_updated",
            "harness",
            {
                "action_id": "native-action-1",
                "tool_name": "submit",
                "budget_class": "tool",
                "delta": {"tool_calls": 1},
                "consumed": {"tool_calls": 1},
                "remaining": {},
            },
        ),
        (
            "environment",
            "environment_observed",
            "model",
            {
                "action_id": "native-action-1",
                "schema_version": "vaevas-observation-v1",
                "observation_id": "obs-001",
                "tool_name": "submit",
                "status": "ok",
                "payload_sha256": SHA_A,
                "truncated": False,
                "candidate_tree_sha256": SHA_B,
                "validation_profile_sha256": None,
                "budget_delta": {"tool_calls": 1},
                "done": True,
                "terminal_reason": "submitted",
            },
        ),
        (
            "environment",
            "submission_frozen",
            "harness",
            {"tree_sha256": SHA_B, "artifacts": ["model.va"]},
        ),
        ("final_judge", "final_judgment_completed", "trusted", {"score": 1.0}),
        ("environment", "cleanup_completed", "harness", {}),
        (
            "controller",
            "episode_completed",
            "harness",
            {"terminal_reason": "submitted"},
        ),
    ):
        recorder.append(
            context=context,
            actor=actor,
            event_type=event_type,
            visibility=visibility,  # type: ignore[arg-type]
            payload=payload,
        )
    return read_trajectory(path)


def _mutated_trace(events, mutation):
    events = deepcopy(events)
    if mutation == "broken_chain":
        events[1]["payload"]["tool_name"] = "bash"
    elif mutation == "cross_attempt":
        events[1]["attempt_id"] = "synthetic-attempt-002"
    elif mutation == "observation_without_action":
        events = [event for event in events if event["event_type"] != "action_proposed"]
    elif mutation == "unsupported_action_payload":
        events[1]["payload"]["raw_provider_payload"] = {"message": "not exportable"}
        _recompute_chain_from(events, 1)
    elif mutation == "model_reentry_after_freeze":
        model_event = deepcopy(events[1])
        model_event["sequence"] = 6
        events.insert(6, model_event)
        _recompute_chain_from(events, 6)
    elif mutation == "private_initial_message":
        return events
    elif mutation == "unknown_event_type":
        events[3]["event_type"] = "raw_provider_response"
        _recompute_chain_from(events, 3)
    elif mutation == "oversized_payload":
        events[3]["payload"]["opaque"] = "x" * (33 * 1024)
        _recompute_chain_from(events, 3)
    else:
        raise AssertionError(mutation)
    return events


def _recompute_chain_from(events, start):
    for index in range(start, len(events)):
        events[index]["sequence"] = index
        events[index]["prev_event_sha256"] = (
            None if index == 0 else events[index - 1]["event_sha256"]
        )
        unhashed = dict(events[index])
        unhashed.pop("event_sha256", None)
        events[index]["event_sha256"] = _event_sha256(unhashed)


def _event_sha256(event_without_hash):
    import hashlib
    import json

    canonical = json.dumps(
        event_without_hash,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _synthetic_metadata(**overrides):
    metadata = {
        "source_id": "synthetic-native-source-001",
        "release_identity": "synthetic-training-fixtures-v1",
        "provenance": {
            "artifact": "synthetic-native-trace",
            "generator": "unit-test-fixture",
            "version": "1",
        },
        "normalizer": {"id": "synthetic-native-trace-adapter", "version": "1"},
        "license": {"spdx": "CC0-1.0", "redistributable": True},
        "provider_use": {
            "terms": "synthetic-fixture",
            "allows_training": True,
            "raw_provider_payload": False,
        },
        "project_authorization": {
            "project": "vaEVAS",
            "allows_training_export": True,
        },
        "exposure_policy": {
            "contains_private": False,
            "contains_trusted": False,
            "contains_hidden": False,
            "contains_final": False,
            "may_enter_model_training": True,
        },
        "initial_messages": [],
    }
    metadata.update(overrides)
    return metadata


def _split_manifest(**overrides):
    manifest = {
        "schema_version": "vaevas-training-split-manifest-v1",
        "splits": {
            "train": ["synthetic/task-001"],
            "dev": ["synthetic/task-002"],
            "heldout": ["synthetic/task-003"],
        },
        "excluded_releases": ["benchmarkv4-r53"],
    }
    manifest.update(overrides)
    return manifest
