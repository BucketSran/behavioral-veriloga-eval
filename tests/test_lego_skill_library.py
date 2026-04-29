from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

from lego_skill_library import extract_functional_ir, retrieve_lego_skills  # noqa: E402


def _prompt(task_id: str) -> str:
    return (ROOT / "benchmark-v2" / "tasks" / task_id / "prompt.md").read_text(encoding="utf-8")


def _top_skill(task_id: str) -> str:
    result = retrieve_lego_skills(_prompt(task_id), top_k=3)
    return result["skills"][0]["skill_id"]


def test_keywordless_adc_dac_routes_to_quantize_reconstruct() -> None:
    result = retrieve_lego_skills(_prompt("v2_adc_dac_keywordless_ramp_5b"), top_k=3)
    assert result["skills"][0]["skill_id"] == "adc_dac_quantize_reconstruct"
    assert "held_state" in result["functional_ir"]["concepts"]
    assert "reconstruct_from_code" in result["functional_ir"]["concepts"]


def test_keywordless_dwa_routes_to_rotating_window() -> None:
    result = retrieve_lego_skills(_prompt("v2_dwa_keywordless_cursor_wrap"), top_k=3)
    assert result["skills"][0]["skill_id"] == "dwa_pointer_window"
    assert "rotating_window" in result["functional_ir"]["concepts"]
    assert "contiguous_window" in result["functional_ir"]["concepts"]


def test_keywordless_pfd_routes_to_edge_pulse_window() -> None:
    result = retrieve_lego_skills(_prompt("v2_pfd_keywordless_mutual_exclusion"), top_k=3)
    assert result["skills"][0]["skill_id"] == "pfd_edge_pulse_window"
    assert "edge_pair" in result["functional_ir"]["concepts"]
    assert "mutual_exclusion" in result["functional_ir"]["concepts"]


def test_composition_prompt_retrieves_full_skill_set() -> None:
    result = retrieve_lego_skills(_prompt("v2_binary_dac_segmented_glitch_guard"), top_k=3)
    skill_ids = {item["skill_id"] for item in result["skills"]}
    assert {"dac_decode_binary_thermometer", "transition_glitch_guard"} <= skill_ids
    assert "weighted_sum" in result["functional_ir"]["concepts"]
    assert "bounded_transition_glitch" in result["functional_ir"]["concepts"]


def test_not_follower_sample_hold_routes_and_captures_negative_constraint() -> None:
    result = retrieve_lego_skills(_prompt("v2_sample_hold_not_follower"), top_k=3)
    assert result["skills"][0]["skill_id"] == "sample_hold_track_latch"
    assert "continuous_follower" in result["functional_ir"]["negative_constraints"]


def test_audit_payload_is_json_serializable() -> None:
    result = retrieve_lego_skills(_prompt("v2_divider_keywordless_ratio_counter"), top_k=2)
    json.dumps(result)
