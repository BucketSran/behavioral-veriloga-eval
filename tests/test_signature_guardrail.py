from __future__ import annotations

import json
from pathlib import Path

from runners.simulate_evas import run_case
from runners.signature_guardrail import (
    SignatureSpec,
    check_candidate_signature,
    check_testbench_signature,
    spec_from_meta,
)


def test_signature_guardrail_accepts_required_items() -> None:
    spec = SignatureSpec(
        required_ports=("OUTP", "OUTN", "VCTR", "VDD", "VSS"),
        required_parameters=("Kvco",),
        required_tokens=("idtmod(", "$bound_step(", "flicker_noise("),
    )
    text = """
module vco(input electrical VCTR, inout electrical VDD, inout electrical VSS,
           output electrical OUTP, output electrical OUTN);
parameter real Kvco = 200e6;
analog begin
    $bound_step(1.0 / 80.0 / freq);
    phase = idtmod(freq, 0, 1);
    n = flicker_noise(1e-12, 1, "vco_fn");
end
endmodule
"""

    assert check_candidate_signature(text, spec) == []


def test_signature_guardrail_reports_missing_and_forbidden_items() -> None:
    spec = SignatureSpec(
        required_ports=("OUTP", "OUTN", "VCTR"),
        required_parameters=("Kvco",),
        required_tokens=("idtmod(", "$bound_step(", "flicker_noise("),
        forbidden_tokens=("ddt(",),
    )
    text = """
module vco(input electrical VCTR, output electrical OUTP);
analog begin
    phase = idtmod(freq, 0, 1);
    I(x) <+ ddt(charge);
end
endmodule
"""

    findings = check_candidate_signature(text, spec)

    assert "missing required port `OUTN`" in findings
    assert "missing required parameter `Kvco`" in findings
    assert "missing required token `$bound_step(`" in findings
    assert "missing required token `flicker_noise(`" in findings
    assert "forbidden token present `ddt(`" in findings


def test_spec_from_meta_uses_explicit_signature_requirements_only() -> None:
    meta = {
        "must_include": ["transition("],
        "must_not_include": ["I("],
        "signature_requirements": {
            "required_ports": ["CLK", "OUT"],
            "required_parameters": ["div_ratio"],
            "required_tokens": ["@(cross("],
            "forbidden_tokens": ["ddt("],
        },
    }

    spec = spec_from_meta(meta)

    assert spec.required_ports == ("CLK", "OUT")
    assert spec.required_parameters == ("div_ratio",)
    assert spec.required_tokens == ("@(cross(",)
    assert spec.forbidden_tokens == ("ddt(",)


def test_spec_from_meta_supports_explicit_testbench_tokens() -> None:
    meta = {
        "family": "tb-generation",
        "must_include": ["simulator lang=spectre", "tran", "save", "ahdl_include"],
        "must_not_include": ["I("],
        "signature_requirements": {
            "required_tb_tokens": ["simulator lang=spectre", "tran", "save", "ahdl_include"],
        },
    }

    spec = spec_from_meta(meta)

    assert spec.required_tokens == ()
    assert spec.forbidden_tokens == ()
    assert spec.required_tb_tokens == ("simulator lang=spectre", "tran", "save", "ahdl_include")
    assert check_candidate_signature("module given_dut; endmodule", spec) == []
    assert check_testbench_signature("simulator lang=spectre\ntran tran stop=1n\n", spec) == [
        "missing required testbench token `save`",
        "missing required testbench token `ahdl_include`",
    ]


def test_run_case_fails_before_evas_when_signature_is_missing(tmp_path: Path) -> None:
    task_dir = tmp_path / "task"
    case_dir = tmp_path / "case"
    task_dir.mkdir()
    case_dir.mkdir()
    (task_dir / "meta.json").write_text(
        json.dumps(
            {
                "id": "eval_vco_signature",
                "signature_requirements": {
                    "required_ports": ["OUTP", "OUTN", "VCTR"],
                    "required_parameters": ["Kvco"],
                    "required_tokens": ["idtmod(", "$bound_step(", "flicker_noise("],
                },
            }
        ),
        encoding="utf-8",
    )
    dut = case_dir / "dut.va"
    dut.write_text(
        """
module weak_vco(input electrical VCTR, output electrical OUTP);
analog begin
    phase = idtmod(freq, 0, 1);
end
endmodule
""",
        encoding="utf-8",
    )
    tb = case_dir / "tb.scs"
    tb.write_text('simulator lang=spectre\nahdl_include "dut.va"\n', encoding="utf-8")

    result = run_case(task_dir, dut, tb, output_root=tmp_path / "out")

    assert result["status"] == "FAIL_DUT_COMPILE"
    assert result["scores"]["dut_compile"] == 0.0
    assert "signature_guardrail_failed" in result["notes"]
    assert "missing required port `OUTN`" in result["notes"]


def test_run_case_routes_tb_signature_failure_to_tb_compile(tmp_path: Path) -> None:
    task_dir = tmp_path / "task"
    case_dir = tmp_path / "case"
    task_dir.mkdir()
    case_dir.mkdir()
    (task_dir / "meta.json").write_text(
        json.dumps(
            {
                "id": "eval_tb_signature",
                "family": "tb-generation",
                "signature_requirements": {
                    "required_tb_tokens": ["simulator lang=spectre", "tran", "save", "ahdl_include"],
                },
                "scoring": ["tb_compile"],
            }
        ),
        encoding="utf-8",
    )
    dut = case_dir / "dut.va"
    dut.write_text("module given_dut; endmodule\n", encoding="utf-8")
    tb = case_dir / "tb.scs"
    tb.write_text("simulator lang=spectre\ntran tran stop=1n\n", encoding="utf-8")

    result = run_case(task_dir, dut, tb, output_root=tmp_path / "out")

    assert result["status"] == "FAIL_TB_COMPILE"
    assert "signature_guardrail_failed" in result["notes"]
    assert "missing required testbench token `save`" in result["notes"]
