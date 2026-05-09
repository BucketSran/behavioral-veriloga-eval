from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runners"))

from runners.run_adaptive_repair import (
    ROOT,
    _compact_controller_prompt,
    _compact_controller_should_use,
)
from runners.validate_benchmark_v2_gold import _candidate_va_for_gold_tb


def test_compact_controller_prompt_is_bounded_and_fact_bearing(tmp_path: Path) -> None:
    task_dir = ROOT / "benchmark-vabench-main-v1" / "tasks" / "vbm1_first_order_lowpass_dut"
    sample_dir = tmp_path / "sample_0"
    sample_dir.mkdir()
    (sample_dir / "first_order_lowpass.va").write_text(
        """
`include "constants.vams"
`include "disciplines.vams"
module first_order_lowpass(input electrical vin, output electrical vout);
  parameter real tau = 1n;
  real y;
  analog begin
    @(initial_step) y = 0.0;
    y = y + (V(vin) - y) / tau;
    V(vout) <+ transition(y, 0, 1p);
  end
endmodule
""".strip(),
        encoding="utf-8",
    )
    result = {
        "status": "FAIL_SIM_CORRECTNESS",
        "scores": {"dut_compile": 1.0, "tb_compile": 1.0, "sim_correct": 0.0, "weighted_total": 0.35},
        "evas_notes": [
            "returncode=1",
            "tran.csv missing",
            "ZeroDivisionError: float division by zero",
            "evas_failure_stage=simulation",
        ],
        "required_axes": ["dut_compile", "tb_compile", "sim_correct"],
    }

    prompt = _compact_controller_prompt(
        task_dir,
        sample_dir,
        result,
        history=[],
        round_idx=1,
        public_spec_mode="prompt-only",
        max_candidate_chars=2500,
    )

    assert len(prompt) < 9000
    assert "Compact-Controller Repair Mode v1" in prompt
    assert "tran.csv missing" in prompt
    assert "first_order_lowpass.va" in prompt
    assert "Current Candidate Artifacts" in prompt
    assert "EVAS-Guided Repair Skill" not in prompt
    assert "Public Behavioral Contract (Evaluator-Aligned)" not in prompt


def test_compact_controller_fallback_targets_artifact_blockers() -> None:
    result = {
        "status": "FAIL_SIM_CORRECTNESS",
        "scores": {"dut_compile": 1.0, "tb_compile": 1.0, "sim_correct": 0.0},
        "evas_notes": ["returncode=1", "tran.csv missing"],
    }

    assert _compact_controller_should_use("fallback", "runtime_interface", result)
    assert not _compact_controller_should_use("off", "runtime_interface", result)


def test_gold_tb_include_selects_matching_candidate_va(tmp_path: Path) -> None:
    sample_dir = tmp_path / "sample_0"
    sample_dir.mkdir()
    (sample_dir / "wrong_first.va").write_text("module wrong_first(); endmodule\n", encoding="utf-8")
    expected = sample_dir / "clk_divider_ref.va"
    expected.write_text("module clk_divider_ref(); endmodule\n", encoding="utf-8")
    gold_tb = tmp_path / "tb_ref.scs"
    gold_tb.write_text('simulator lang=spectre\nahdl_include "clk_divider_ref.va"\n', encoding="utf-8")

    assert _candidate_va_for_gold_tb(sample_dir, gold_tb) == expected
