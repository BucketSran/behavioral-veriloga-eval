from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import jsonschema
import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def load_render_module():
    spec = importlib.util.spec_from_file_location("render_v4_harness", SCRIPTS / "render_v4_harness.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["render_v4_harness"] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def minimal_spec() -> dict:
    return {
        "schema_version": "v4-harness-spec-v1",
        "family_id": "001",
        "task_id": "v4-001",
        "generator": {"name": "render_v4_harness.py", "version": "v4-harness-renderer-v1"},
        "candidate": {"source_root": "./dut", "artifact_paths": ["dut.va"]},
        "deck": {
            "header": ["simulator lang=spectre", "global 0"],
            "include_templates": ['ahdl_include "{candidate_source_root}/{artifact_path}"'],
            "body_lines": ["VDD vdd 0 vsource dc={vdd}", "XDUT vin vout dut"],
            "analyses": ["tran tran stop={stop_time} maxstep={maxstep}"],
            "save_signals": ["v(vin)", "v(vout)"],
        },
        "property_ids": ["P_GAIN", "P_SETTLE"],
        "profile_defaults": {
            "feedback": {
                "parameters": {"vdd": "1.0", "stop_time": "20n", "maxstep": "100p"},
                "simulatorOptions": {},
            },
            "score": {
                "parameters": {"vdd": "0.95", "stop_time": "30n", "maxstep": "50p"},
                "simulatorOptions": {"reltol": "1e-4"},
            },
        },
    }


def test_feedback_and_score_profiles_are_generated_from_one_spec(tmp_path: Path) -> None:
    render = load_render_module()
    spec_path = tmp_path / "harness_spec.json"
    payload = minimal_spec()
    write_json(spec_path, payload)

    spec, spec_hash = render.load_spec(spec_path)
    feedback = render.build_profile(spec, "feedback", spec_hash)
    score = render.build_profile(spec, "score", spec_hash)

    assert feedback["harness_spec_sha256"] == score["harness_spec_sha256"] == hashlib.sha256(
        spec_path.read_bytes()
    ).hexdigest()
    assert feedback["property_ids"] == score["property_ids"] == ["P_GAIN", "P_SETTLE"]
    assert feedback["simulatorOptions"]["evas_profile"] == "balanced"
    assert score["simulatorOptions"] == {"reltol": "1e-4"}

    feedback_deck = render.render_scs(spec, feedback)
    score_deck = render.render_scs(spec, score)
    assert "simulatorOptions options evas_profile=balanced" in feedback_deck
    assert "simulatorOptions options reltol=1e-4" in score_deck
    assert "VDD vdd 0 vsource dc=1.0" in feedback_deck
    assert "VDD vdd 0 vsource dc=0.95" in score_deck


def test_renderer_chunks_wide_save_lists_without_losing_signals() -> None:
    render = load_render_module()
    spec = minimal_spec()
    signals = ["en", *[f"th{index}" for index in range(256)], *[f"metric{index}" for index in range(8)]]
    spec["deck"]["save_signals"] = signals
    profile = render.build_profile(spec, "feedback", "a" * 64)

    deck = render.render_scs(spec, profile)
    save_lines = [line for line in deck.splitlines() if line.startswith("save ")]
    recovered = [token for line in save_lines for token in line.split()[1:]]

    assert len(save_lines) > 1
    assert all(len(line) <= render.MAX_SAVE_LINE_LENGTH for line in save_lines)
    assert recovered == signals


def test_renderer_includes_declared_readonly_support_after_candidate() -> None:
    render = load_render_module()
    spec = minimal_spec()
    spec["support"] = {
        "source_root": "./support",
        "artifact_paths": ["clock.va", "blocks/comparator.va"],
    }
    spec["deck"]["support_include_templates"] = [
        'ahdl_include "{support_source_root}/{support_artifact_path}"'
    ]
    profile = render.build_profile(spec, "feedback", "a" * 64)

    deck = render.render_scs(spec, profile)

    assert deck.index('ahdl_include "./dut/dut.va"') < deck.index(
        'ahdl_include "./support/clock.va"'
    )
    assert 'ahdl_include "./support/blocks/comparator.va"' in deck


def test_feedback_profile_schema_rejects_non_balanced_evas_profile() -> None:
    schema = json.loads((ROOT / "schemas" / "harness_profile.schema.json").read_text(encoding="utf-8"))
    profile = {
        "schema_version": "v4-harness-profile-v1",
        "profile_name": "feedback",
        "harness_spec_sha256": "a" * 64,
        "generated_from": {"script": "render_v4_harness.py", "version": "v4-harness-renderer-v1"},
        "property_ids": ["P_GAIN"],
        "parameters": {},
        "corners": [],
        "deterministic_seed": 0,
        "simulatorOptions": {"evas_profile": "fast"},
        "public_visible": True,
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(profile, schema)


def test_runtime_validation_works_without_jsonschema(tmp_path: Path) -> None:
    render = load_render_module()
    render.Draft202012Validator = None
    spec_path = tmp_path / "harness_spec.json"
    write_json(spec_path, minimal_spec())

    spec, spec_hash = render.load_spec(spec_path)
    profile = render.build_profile(spec, "feedback", spec_hash)

    assert profile["simulatorOptions"]["evas_profile"] == "balanced"
    bad = minimal_spec()
    bad["candidate"]["artifact_paths"] = ["../escape.va"]
    write_json(spec_path, bad)
    with pytest.raises(ValueError, match="unsafe harness artifact path"):
        render.load_spec(spec_path)
