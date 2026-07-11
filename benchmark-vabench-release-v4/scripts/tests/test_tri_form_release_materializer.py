from __future__ import annotations

import sys
from pathlib import Path


PREP = Path(__file__).resolve().parents[2] / "operations" / "tri_form_derivation_prep"
if str(PREP) not in sys.path:
    sys.path.insert(0, str(PREP))

from materialize_tri_form_release import (  # noqa: E402
    COMPONENT_METADATA,
    MODES,
    REFERENCE_TOKENIZER,
    reference_token_count,
    render_bugfix_instruction,
    render_testbench_instruction,
    select_bugfix_seed,
)
from export_tri_form_runtime import install_public  # noqa: E402


def sample_spec() -> dict:
    return {
        "family_id": "001",
        "identity": {"title": "Sample Hold", "category": "sampling", "level": "L1", "difficulty": "D2"},
        "artifact_contract": {"mode": "single_file", "files": [{"path": "dut.va", "modules": [{
            "name": "dut", "role": "entry", "depends_on": [],
            "ports": [{"name": "vin", "direction": "input", "discipline": "electrical", "position": 0}],
            "parameters": [],
        }]}]},
        "testbench_binding": {"source_path_template": "./dut/{artifact_path}", "instances": [{
            "name": "XDUT", "module_ref": "dut", "connections": [{"port_ref": "vin", "net": "vin", "position": 0}],
        }]},
        "properties": [{"id": "P_HOLD", "observable_contract": "hold the sampled value", "required_signals": ["time", "vin"]}],
        "trace_contract": {"required_signals": ["time", "vin"]},
        "modeling_constraints": ["Remain deterministic."],
    }


def test_mode_matrix_is_two_direct_plus_four_agentic() -> None:
    assert [name for name, row in MODES.items() if row["process"] == "direct_one_shot"] == ["G0", "G1"]
    assert [name for name, row in MODES.items() if row["feedback_cli"]] == ["G2", "G3", "G4", "G5"]


def test_bugfix_instruction_does_not_localize_fault() -> None:
    text = render_bugfix_instruction(sample_spec()).lower()
    for forbidden in ("mutation", "faulty file", "root cause", "changed line", "baseline result"):
        assert forbidden not in text


def test_testbench_instruction_has_one_candidate_and_five_anonymous_negatives() -> None:
    text = render_testbench_instruction(sample_spec())
    assert "`testbench.scs`" in text
    assert "five anonymous semantic negative DUTs" in text
    assert "hidden" not in text.lower()


def test_seed_policy_prefers_temporal_semantic_fault_over_force_zero() -> None:
    row = {
        "bugfix_seed": "neg_001_force_zero",
        "active_mutations": [
            {"mutation_id": "neg_001_force_zero", "fault_class": "stuck_zero", "trigger_condition": "all time", "violated_property_ids": ["P_OUT"]},
            {"mutation_id": "neg_002_wrong_edge", "fault_class": "wrong_sampling_edge", "trigger_condition": "falling edge after reset", "violated_property_ids": ["P_EDGE", "P_HOLD"]},
        ],
    }
    selected = select_bugfix_seed(row)
    assert selected["mutation_id"] == "neg_002_wrong_edge"
    assert not selected["triviality_markers"]


def test_prompt_components_have_pinned_reference_tokenizer_metadata() -> None:
    assert REFERENCE_TOKENIZER["id"] == "vabench_utf8_lexeme"
    assert set(COMPONENT_METADATA) == {
        "neutral_wrapper.md",
        "dut_modeling.md",
        "testbench_verification.md",
        "bugfix_diagnosis.md",
        "feedback_core.md",
        "feedback_dut.md",
        "feedback_testbench.md",
        "feedback_bugfix.md",
    }
    assert reference_token_count("one two; three") == 4


def test_agentic_bugfix_export_seeds_editable_submission(tmp_path: Path) -> None:
    task = tmp_path / "task"
    (task / "buggy_bundle").mkdir(parents=True)
    (task / "buggy_bundle" / "a.va").write_text("module a; endmodule\n", encoding="utf-8")
    (task / "instruction.md").write_text("Repair the bundle.\n", encoding="utf-8")
    (task / "public_contract.json").write_text("{}\n", encoding="utf-8")
    public = tmp_path / "public"
    (public / "submission").mkdir(parents=True)
    install_public(task, public, "bugfix", "G2")
    assert (public / "submission" / "a.va").read_bytes() == (task / "buggy_bundle" / "a.va").read_bytes()
    assert (public / "task" / "buggy_bundle" / "a.va").is_file()
