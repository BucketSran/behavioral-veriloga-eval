from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

from compile_hard_guard import apply_compile_skill_actions  # noqa: E402
from compile_skill_library import render_compile_skill_guidance, select_compile_skills  # noqa: E402
from materialize_cultra_candidates import _wrong_function_gate_action  # noqa: E402
from run_wrong_function_regeneration import (  # noqa: E402
    _choose_module_block,
    _include_filename_for_module,
    _missing_module_from_notes,
    _response_from_replay_va,
)


def test_compile_skill_router_selects_expected_skills() -> None:
    notes = [
        "spectre_strict:conditional_transition=not_gate.va",
        "spectre_strict:nonincreasing_pwl_time=21:t1=4e-09,t2=4e-09",
    ]

    selected = select_compile_skills(notes)
    ids = {skill.id for skill in selected}

    assert "conditional_transition_target_buffer" in ids
    assert "pwl_monotonic_time" in ids
    assert "module_name_linkage" not in ids


def test_compile_skill_guidance_can_render_selected_skill() -> None:
    guidance = render_compile_skill_guidance(["conditional_transition_target_buffer"])

    assert "conditional_transition_target_buffer" in guidance
    assert "target-buffer" in guidance
    assert "transition()" in guidance


def test_wrong_function_gate_is_judge_only_and_renderable() -> None:
    selected = select_compile_skills(
        [
            "spectre_strict:undefined_module=v2b_4b;available_modules=dwa_ptr_gen_no_overlap",
            "spectre_strict:instance_port_count_mismatch=24:IV2B:v2b_4b:nodes=6:ports=38",
        ]
    )
    selected_by_id = {skill.id: skill for skill in selected}
    guidance = render_compile_skill_guidance(["wrong_function_regeneration_gate"])

    assert selected_by_id["wrong_function_regeneration_gate"].fixer is None
    assert not selected_by_id["wrong_function_regeneration_gate"].safe_autofix
    assert "wrong-function generation" in guidance
    assert "Do not synthesize a replacement module in a hard guard" in guidance


def test_wrong_function_gate_action_routes_rejected_module_rename() -> None:
    action = _wrong_function_gate_action(
        before_notes=["spectre_strict:undefined_module=v2b_4b;available_modules=dwa_ptr_gen_no_overlap"],
        rejected_result={
            "status": "FAIL_DUT_COMPILE",
            "evas_notes": [
                "spectre_strict:instance_port_count_mismatch=24:IV2B:v2b_4b:nodes=6:ports=38",
            ],
        },
        pass_idx=1,
    )

    assert action is not None
    assert action["id"] == "wrong_function_regeneration_gate"
    assert action["decision"] == "route_to_prompt_regeneration"
    assert action["missing_module"] == "v2b_4b"
    assert action["renamed_from"] == "dwa_ptr_gen_no_overlap"
    assert action["safe_autofix"] is False


def test_wrong_function_regeneration_helpers_extract_public_contract() -> None:
    notes = ["spectre_strict:undefined_module=v2b_4b;available_modules=dwa_ptr_gen_no_overlap"]
    tb_text = (
        'ahdl_include "v2b_4b.va"\n'
        'IV2B (clk_i vin_node code_3 code_2 code_1 code_0) v2b_4b vdd=0.9\n'
    )
    response = (
        "```verilog\n"
        "module helper(out); output out; electrical out; analog V(out)<+0; endmodule\n"
        "```\n"
        "```verilog\n"
        "module v2b_4b(clk, vin, out_3, out_2, out_1, out_0);\n"
        "endmodule\n"
        "```\n"
    )

    assert _missing_module_from_notes(notes) == ("v2b_4b", "dwa_ptr_gen_no_overlap")
    assert _include_filename_for_module(tb_text, "v2b_4b") == "v2b_4b.va"
    assert "module v2b_4b" in (_choose_module_block(response, "v2b_4b") or "")


def test_wrong_function_regeneration_replay_va_wraps_saved_candidate(tmp_path: Path) -> None:
    va_path = tmp_path / "v2b_4b.va"
    va_path.write_text(
        "module v2b_4b(clk, vin, out_3, out_2, out_1, out_0);\nendmodule\n",
        encoding="utf-8",
    )

    replay_response = _response_from_replay_va(va_path)

    assert replay_response.startswith("```verilog\n")
    assert replay_response.endswith("\n```")
    assert "module v2b_4b" in (_choose_module_block(replay_response, "v2b_4b") or "")


def test_compile_skill_action_records_judge_only_skill(tmp_path: Path) -> None:
    sample = tmp_path / "sample_0"
    sample.mkdir()
    notes = [
        "spectre_strict:sourced_port_voltage_drive=7:XDUT:dut:vss->0",
    ]

    manifest = apply_compile_skill_actions(sample, notes=notes)

    assert manifest["edits"] == []
    selected = manifest["selected_skills"]
    selected_by_id = {skill["id"]: skill for skill in selected}
    assert selected_by_id["sourced_port_drive_boundary"]["action"] == "judge_only"
    assert selected_by_id["sourced_port_role_repair"]["action"] == "fixer"


def test_sourced_port_role_repair_detaches_source_fixed_node(tmp_path: Path) -> None:
    sample = tmp_path / "sample_0"
    sample.mkdir()
    (sample / "dut.va").write_text(
        "module dut(out, vss);\n"
        "  output out; inout vss; electrical out, vss;\n"
        "  analog begin\n"
        "    V(vss) <+ 0;\n"
        "    V(out) <+ V(vss);\n"
        "  end\n"
        "endmodule\n",
        encoding="utf-8",
    )
    tb = sample / "tb_generated.scs"
    tb.write_text("simulator lang=spectre\nXDUT (out 0) dut\n", encoding="utf-8")

    manifest = apply_compile_skill_actions(
        sample,
        notes=["spectre_strict:sourced_port_voltage_drive=7:XDUT:dut:vss->0"],
    )
    updated = tb.read_text(encoding="utf-8")

    assert any(skill["id"] == "sourced_port_role_repair" for skill in manifest["selected_skills"])
    assert "__cg_XDUT_vss_free" in updated
    assert "XDUT (out 0) dut" not in updated


def test_missing_testbench_generation_writes_public_smoke_harness(tmp_path: Path) -> None:
    sample = tmp_path / "sample_0"
    sample.mkdir()
    (sample / "dut.va").write_text(
        "module dut(vdd, vin, out);\n"
        "  inout vdd; input vin; output out; electrical vdd, vin, out;\n"
        "  analog begin V(out) <+ V(vin); end\n"
        "endmodule\n",
        encoding="utf-8",
    )

    manifest = apply_compile_skill_actions(
        sample,
        notes=["missing_generated_files=testbench.scs", "spectre_strict:missing_staged_tb"],
    )
    tb = sample / "tb_generated.scs"
    updated = tb.read_text(encoding="utf-8")

    assert any(skill["id"] == "missing_testbench_generation" for skill in manifest["selected_skills"])
    assert tb.exists()
    assert 'ahdl_include "dut.va"' in updated
    assert "XSKEL (vdd vin out) dut" in updated
    assert "save out" in updated


def test_missing_testbench_generation_bootstraps_transition_skill(tmp_path: Path) -> None:
    sample = tmp_path / "sample_0"
    sample.mkdir()
    va = sample / "dut.va"
    va.write_text(
        "module dut(clk, out);\n"
        "  input clk; output out; electrical clk, out;\n"
        "  analog begin\n"
        "    if (V(clk) > 0.5) begin\n"
        "      V(out) <+ transition(1.0, 0, 1n);\n"
        "    end\n"
        "  end\n"
        "endmodule\n",
        encoding="utf-8",
    )

    manifest = apply_compile_skill_actions(
        sample,
        notes=["missing_generated_files=testbench.scs"],
    )
    updated = va.read_text(encoding="utf-8")

    assert any("missing_testbench_skeleton" in edit for edit in manifest["edits"])
    assert any("missing_testbench_bootstrap:transition_target_buffer" in edit for edit in manifest["edits"])
    assert "__cg_out_target" in updated
    assert "V(out) <+ transition(__cg_out_target" in updated


def test_dynamic_scatter_skill_materializes_runtime_vector_target(tmp_path: Path) -> None:
    sample = tmp_path / "sample_0"
    sample.mkdir()
    va = sample / "dut.va"
    va.write_text(
        "module dut(sel, out);\n"
        "  input [1:0] sel; output [1:0] out;\n"
        "  electrical [1:0] sel; electrical [1:0] out;\n"
        "  integer i, idx;\n"
        "  analog begin\n"
        "    for (i = 0; i < 2; i = i + 1) begin\n"
        "      if (V(sel[i]) > 0.5) begin\n"
        "        idx = i;\n"
        "        V(out[idx]) <+ transition(1.0, 0, 1n);\n"
        "      end\n"
        "    end\n"
        "  end\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (sample / "tb_generated.scs").write_text(
        "simulator lang=spectre\nXDUT (sel_1 sel_0 out_1 out_0) dut\n",
        encoding="utf-8",
    )

    manifest = apply_compile_skill_actions(
        sample,
        notes=[
            "spectre_strict:instance_port_count_mismatch=2:XDUT:dut:nodes=4:ports=2",
            "spectre_strict:dynamic_analog_vector_index=dut.va:V(out[idx])",
        ],
    )
    updated = va.read_text(encoding="utf-8")

    assert any(skill["id"] == "dynamic_scatter_index_materialization" for skill in manifest["selected_skills"])
    assert "V(out[idx])" not in updated
    assert "V(out_1)" in updated
    assert "V(out_0)" in updated


def test_parameter_range_skill_routes_open_upper_range_and_removes_clause(tmp_path: Path) -> None:
    sample = tmp_path / "sample_0"
    sample.mkdir()
    va = sample / "dut.va"
    va.write_text(
        "module dut(out);\n"
        "  output out; electrical out;\n"
        "  parameter real tr = 1n from (0:);\n"
        "  parameter real td = 0n from [0:);\n"
        "endmodule\n",
        encoding="utf-8",
    )
    notes = [
        "spectre_strict:parameter_open_upper_range=dut.va:3:tr",
    ]

    manifest = apply_compile_skill_actions(sample, notes=notes)
    updated = va.read_text(encoding="utf-8")

    assert any(skill["id"] == "parameter_default_range" for skill in manifest["selected_skills"])
    assert "from (0:)" not in updated
    assert "from [0:)" not in updated
    assert "parameter real tr = 1n;" in updated
    assert "parameter real td = 0n;" in updated


def test_instance_parameter_keyword_skill_handles_continued_instance(tmp_path: Path) -> None:
    sample = tmp_path / "sample_0"
    sample.mkdir()
    tb = sample / "tb_generated.scs"
    tb.write_text(
        "simulator lang=spectre\n"
        "parameters vdd=0.9\n"
        "XDUT (clk rst \\\n"
        "      out) my_model \\\n"
        "      parameters vdd=vdd vth=0.45\n",
        encoding="utf-8",
    )

    manifest = apply_compile_skill_actions(
        sample,
        notes=["spectre_strict:instance_parameters_keyword=3:XDUT:my_model:parameters_keyword"],
    )
    updated = tb.read_text(encoding="utf-8")

    assert any(skill["id"] == "instance_parameter_keyword" for skill in manifest["selected_skills"])
    assert "parameters vdd=0.9" in updated
    assert "      parameters vdd=vdd" not in updated
    assert "      vdd=vdd vth=0.45" in updated
