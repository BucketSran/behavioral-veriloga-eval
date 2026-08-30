from __future__ import annotations

import hashlib
import math

import pytest

from runners.agent_harness.training_export import (
    TrainingExportError,
    build_training_export,
    validate_training_export,
)


SHA_A = "a" * 64
OBS_SHA = hashlib.sha256(b"public observation").hexdigest()


def test_sft_export_binds_synthetic_source_and_keeps_observations_out_of_targets():
    source = _synthetic_source()
    split_manifest = _split_manifest()

    exported = build_training_export(
        source,
        split_manifest=split_manifest,
        mode="sft",
    )

    assert exported["schema_version"] == "vaevas-training-export-v1"
    assert exported["mode"] == "sft"
    assert exported["identity"]["task_id"] == "synthetic/task-001"
    assert exported["split"]["name"] == "train"
    assert exported["source"]["source_kind"] == "synthetic"
    assert exported["source"]["exporter_contract_sha256"] != exported["source"]["normalizer_sha256"]
    assert exported["sft"]["assistant_targets"] == [
        {"event_id": "a1", "content": "```verilog-a\nmodule demo; endmodule\n```"}
    ]
    assert exported["sft"]["environment_observations"] == [
        {"event_id": "o1", "content_sha256": OBS_SHA}
    ]
    assert exported["sft"]["messages"] == [
        {
            "event_id": "u1",
            "role": "user",
            "content": "Create a tiny Verilog-A module.",
            "loss": False,
        },
        {
            "event_id": "a1",
            "role": "assistant",
            "content": "```verilog-a\nmodule demo; endmodule\n```",
            "loss": True,
        },
        {
            "event_id": "o1",
            "role": "environment",
            "content": "public observation",
            "loss": False,
        },
    ]
    assert "public observation" not in str(exported["sft"]["assistant_targets"])
    validate_training_export(exported, source=source, split_manifest=split_manifest)


@pytest.mark.parametrize(
    ("source_update", "message"),
    [
        ({"source_kind": "reviewer_export"}, "synthetic"),
        ({"task_id": "v4-001"}, "non-synthetic"),
        ({"release_identity": "benchmarkv4-r53"}, "r53"),
        ({"release_identity": "synthetic-training-fixtures-v2"}, "release identity"),
    ],
)
def test_export_rejects_real_or_r53_sources(source_update, message):
    with pytest.raises(TrainingExportError, match=message):
        build_training_export(
            _synthetic_source(**source_update),
            split_manifest=_split_manifest(),
            mode="sft",
        )


@pytest.mark.parametrize(
    "source_update",
    [
        {"source_id": "synthetic-private-fixture"},
        {"episode_id": "trusted-episode"},
        {"provenance": {"artifact": "final-artifact", "generator": "handwritten", "version": "1"}},
        {"normalizer": {"id": "hidden-normalizer", "version": "1"}},
        {
            "project_authorization": {
                "project": "private-vaEVAS",
                "allows_training_export": True,
            }
        },
    ],
)
def test_export_rejects_forbidden_metadata_markers(source_update):
    with pytest.raises(TrainingExportError, match="metadata|authority marker"):
        build_training_export(
            _synthetic_source(**source_update),
            split_manifest=_split_manifest(),
            mode="sft",
        )


def test_export_rejects_split_overlap_and_missing_r53_exclusion():
    with pytest.raises(TrainingExportError, match="multiple splits"):
        build_training_export(
            _synthetic_source(),
            split_manifest=_split_manifest(
                splits={
                    "train": ["synthetic/task-001"],
                    "dev": ["synthetic/task-001"],
                    "heldout": ["synthetic/task-003"],
                }
            ),
            mode="sft",
        )

    with pytest.raises(TrainingExportError, match="exclude r53"):
        build_training_export(
            _synthetic_source(),
            split_manifest=_split_manifest(excluded_releases=[]),
            mode="sft",
        )


def test_export_rejects_unknown_split_buckets():
    with pytest.raises(TrainingExportError, match="split buckets|unknown"):
        build_training_export(
            _synthetic_source(),
            split_manifest=_split_manifest(
                splits={
                    "train": ["synthetic/task-001"],
                    "dev": ["synthetic/task-002"],
                    "heldout": ["synthetic/task-003"],
                    "test": ["synthetic/task-004"],
                }
            ),
            mode="sft",
        )


def test_export_rejects_trusted_or_final_material_even_when_marked_synthetic():
    trusted_source = _synthetic_source(
        trajectory=[
            {
                "event_id": "u1",
                "role": "user",
                "visibility": "model",
                "content": "Create a tiny Verilog-A module.",
            },
            {
                "event_id": "j1",
                "role": "environment",
                "visibility": "trusted",
                "content": "public-looking output",
            },
        ],
    )
    with pytest.raises(TrainingExportError, match="forbidden training material|model-visible"):
        build_training_export(trusted_source, split_manifest=_split_manifest(), mode="sft")

    final_source = _synthetic_source(
        trajectory=[
            {
                "event_id": "u1",
                "role": "user",
                "visibility": "model",
                "content": "Create a tiny Verilog-A module.",
            }
        ],
        final_sidecar={"score": 1.0},
    )
    with pytest.raises(TrainingExportError, match="unknown"):
        build_training_export(final_source, split_manifest=_split_manifest(), mode="sft")


@pytest.mark.parametrize(
    "termination",
    [
        {"reason": "budget_exhausted", "budget_exhausted": True},
        {"reason": "model_call_limit", "budget_exhausted": False},
        {"reason": "submitted", "budget_exhausted": "false"},
    ],
)
def test_sft_rejects_budget_or_contradictory_termination_as_positive_label(termination):
    source = _synthetic_source(
        termination=termination
    )

    with pytest.raises(TrainingExportError, match="budget|positive"):
        build_training_export(source, split_manifest=_split_manifest(), mode="sft")


def test_export_rejects_heldout_split_for_training():
    source = _synthetic_source(task_id="synthetic/task-003")

    with pytest.raises(TrainingExportError, match="heldout"):
        build_training_export(source, split_manifest=_split_manifest(), mode="sft")


def test_rl_export_requires_public_validation_reward_and_excludes_final_score():
    source = _rl_source(
        reward={
            "authority": "public_validation",
            "value": 0.5,
            "definition": "compile and public simulation checks",
            "generator_sha256": SHA_A,
        }
    )

    exported = build_training_export(source, split_manifest=_split_manifest(), mode="rl")

    assert exported["rl"]["reward"]["authority"] == "public_validation"
    assert exported["rl"]["final_score_exported"] is False
    assert exported["rl"]["accepted_actions"] == [
        {"event_id": "a1", "content_sha256": exported["rl"]["accepted_actions"][0]["content_sha256"]}
    ]
    validate_training_export(exported, source=source, split_manifest=_split_manifest())


def test_rl_export_rejects_final_or_unknown_reward_authority():
    for authority in ("final_test", "trusted_replay"):
        source = _rl_source(
            reward={
                "authority": authority,
                "value": 1.0,
                "definition": "compile and public simulation checks",
                "generator_sha256": SHA_A,
            }
        )
        with pytest.raises(TrainingExportError, match="public_validation"):
            build_training_export(source, split_manifest=_split_manifest(), mode="rl")
    unknown_source = _rl_source(
        reward={
            "authority": "unknown",
            "value": 1.0,
            "definition": "compile and public simulation checks",
            "generator_sha256": SHA_A,
        }
    )
    with pytest.raises(TrainingExportError, match="public_validation"):
        build_training_export(unknown_source, split_manifest=_split_manifest(), mode="rl")


def test_validate_training_export_rejects_tampered_output():
    source = _synthetic_source()
    split_manifest = _split_manifest()
    exported = build_training_export(source, split_manifest=split_manifest, mode="sft")
    exported["identity"]["task_id"] = "synthetic/task-999"

    with pytest.raises(TrainingExportError, match="does not match"):
        validate_training_export(exported, source=source, split_manifest=split_manifest)


def test_export_rejects_provider_payload_and_exposure_policy_leaks():
    provider_payload = _synthetic_source(
        provider_use={
            "terms": "synthetic-fixture",
            "allows_training": True,
            "raw_provider_payload": True,
        }
    )
    with pytest.raises(TrainingExportError, match="raw provider payload"):
        build_training_export(provider_payload, split_manifest=_split_manifest(), mode="sft")

    hidden_exposure = _synthetic_source(
        exposure_policy={
            "contains_private": False,
            "contains_trusted": False,
            "contains_hidden": True,
            "contains_final": False,
            "may_enter_model_training": True,
        }
    )
    with pytest.raises(TrainingExportError, match="contains_hidden"):
        build_training_export(hidden_exposure, split_manifest=_split_manifest(), mode="sft")


def test_export_rejects_unknown_provenance_and_missing_license_authority():
    unknown_provenance = _synthetic_source(
        provenance={
            "artifact": "unknown",
            "generator": "handwritten",
            "version": "1",
        }
    )
    with pytest.raises(TrainingExportError, match="provenance"):
        build_training_export(unknown_provenance, split_manifest=_split_manifest(), mode="sft")

    missing_license = _synthetic_source(license={"spdx": "LicenseRef-Unknown", "redistributable": True})
    with pytest.raises(TrainingExportError, match="license"):
        build_training_export(missing_license, split_manifest=_split_manifest(), mode="sft")


def test_export_rejects_unknown_fields_duplicate_events_and_hash_mismatch():
    extra_source = _synthetic_source(unexpected="value")
    with pytest.raises(TrainingExportError, match="unknown"):
        build_training_export(extra_source, split_manifest=_split_manifest(), mode="sft")

    duplicate_events = _synthetic_source(
        trajectory=[
            {
                "event_id": "u1",
                "role": "user",
                "visibility": "model",
                "content": "Create a tiny Verilog-A module.",
            },
            {
                "event_id": "u1",
                "role": "assistant",
                "visibility": "model",
                "content": "module demo; endmodule",
            },
        ]
    )
    with pytest.raises(TrainingExportError, match="duplicate"):
        build_training_export(duplicate_events, split_manifest=_split_manifest(), mode="sft")

    mismatch = _synthetic_source(
        trajectory=[
            {
                "event_id": "u1",
                "role": "user",
                "visibility": "model",
                "content": "Create a tiny Verilog-A module.",
            },
            {
                "event_id": "a1",
                "role": "assistant",
                "visibility": "model",
                "content": "module demo; endmodule",
                "content_sha256": SHA_A,
            },
        ]
    )
    with pytest.raises(TrainingExportError, match="does not match"):
        build_training_export(mismatch, split_manifest=_split_manifest(), mode="sft")


def test_export_rejects_bounds_nonfinite_json_and_empty_assistant_targets():
    many_events = _synthetic_source(
        trajectory=[
            {
                "event_id": f"u{i}",
                "role": "user",
                "visibility": "model",
                "content": "x",
            }
            for i in range(257)
        ]
    )
    with pytest.raises(TrainingExportError, match="event count"):
        build_training_export(many_events, split_manifest=_split_manifest(), mode="sft")

    nonfinite = _rl_source(
        reward={
            "authority": "public_validation",
            "value": math.nan,
            "definition": "compile and public simulation checks",
            "generator_sha256": SHA_A,
        }
    )
    with pytest.raises(TrainingExportError, match="non-finite"):
        build_training_export(nonfinite, split_manifest=_split_manifest(), mode="rl")

    empty_targets = _synthetic_source(
        trajectory=[
            {
                "event_id": "u1",
                "role": "user",
                "visibility": "model",
                "content": "Create a tiny Verilog-A module.",
            }
        ]
    )
    with pytest.raises(TrainingExportError, match="assistant target"):
        build_training_export(empty_targets, split_manifest=_split_manifest(), mode="sft")


def _synthetic_source(**overrides):
    source = {
        "source_kind": "synthetic",
        "source_id": "synthetic-fixture-001",
        "release_identity": "synthetic-training-fixtures-v1",
        "task_id": "synthetic/task-001",
        "episode_id": "episode-001",
        "provenance": {
            "artifact": "unit-test-fixture",
            "generator": "handwritten",
            "version": "1",
        },
        "normalizer": {"id": "synthetic-normalizer", "version": "1"},
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
        "trajectory": [
            {
                "event_id": "u1",
                "role": "user",
                "visibility": "model",
                "content": "Create a tiny Verilog-A module.",
            },
            {
                "event_id": "a1",
                "role": "assistant",
                "visibility": "model",
                "content": "```verilog-a\nmodule demo; endmodule\n```",
            },
            {
                "event_id": "o1",
                "role": "environment",
                "visibility": "model",
                "content": "public observation",
                "content_sha256": OBS_SHA,
            },
        ],
        "termination": {
            "reason": "submitted",
            "budget_exhausted": False,
        },
        "labels": {
            "sft": {"authority": "synthetic_fixture", "accepted": True},
        },
    }
    source.update(overrides)
    return source


def _rl_source(**overrides):
    source = _synthetic_source()
    source.pop("labels")
    source.update(overrides)
    return source


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
