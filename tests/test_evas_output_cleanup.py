import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

import simulate_evas  # noqa: E402


def test_run_case_removes_stale_tran_csv_before_evas(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("EVAS_ENGINE", raising=False)
    monkeypatch.delenv("VAEVAS_DEFAULT_EVAS_ENGINE", raising=False)
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    (task_dir / "meta.json").write_text(
        json.dumps({"id": "stale_output_case", "scoring": ["tb_compile"]}),
        encoding="utf-8",
    )
    dut = tmp_path / "dut.va"
    tb = tmp_path / "tb.scs"
    dut.write_text('`include "disciplines.vams"\nmodule m(a); electrical a; endmodule\n', encoding="utf-8")
    tb.write_text("tran tran stop=1n\n", encoding="utf-8")

    output_root = tmp_path / "persistent_output"
    output_root.mkdir()
    (output_root / "tran.csv").write_text("time,out\n0,1\n", encoding="utf-8")

    def fake_run_evas(
        run_dir: Path,
        tb_file: Path,
        output_dir: Path,
        timeout_s: int,
        required_trace_signals=None,
    ):
        assert not (output_dir / "tran.csv").exists()
        return subprocess.CompletedProcess(["evas"], 1, stdout="", stderr="parse failed")

    monkeypatch.setattr(simulate_evas, "run_evas", fake_run_evas)

    result = simulate_evas.run_case(
        task_dir,
        dut,
        tb,
        output_root=output_root,
        timeout_s=1,
    )

    assert result["scores"]["tb_compile"] == 0.0
    assert result["status"] == "FAIL_TB_COMPILE"
    assert result["evas_engine_used"] == "evas2"


def test_load_csv_skips_incomplete_rows_and_keeps_lowercase_aliases(tmp_path: Path) -> None:
    csv_path = tmp_path / "tran.csv"
    csv_path.write_text(
        "\n".join(
            [
                "time,VOUT,metric",
                "0,0.1,0.2",
                "1e-9,,0.3",
                "2e-9,0.4,0.5",
            ]
        ),
        encoding="utf-8",
    )

    rows = simulate_evas.load_csv(csv_path)

    assert len(rows) == 2
    assert rows[0]["VOUT"] == rows[0]["vout"] == 0.1
    assert rows[1]["time"] == 2e-9


def test_run_evas_defaults_to_strict_rust_evas2(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("EVAS_ENGINE", raising=False)
    monkeypatch.delenv("VAEVAS_DEFAULT_EVAS_ENGINE", raising=False)
    monkeypatch.setenv("VAEVAS_EVAS_PERSISTENT_WORKER", "0")
    run_dir = tmp_path / "run"
    out_dir = tmp_path / "out"
    run_dir.mkdir()
    tb = run_dir / "tb.scs"
    tb.write_text("tran tran stop=1n\n", encoding="utf-8")
    captured: dict[str, object] = {}

    monkeypatch.setattr(simulate_evas, "evas_command_and_env", lambda: (["evas"], {}))

    def fake_subprocess_run(*args, **kwargs):
        captured["cmd"] = args[0]
        captured["env"] = kwargs["env"]
        return subprocess.CompletedProcess(args[0], 0, stdout="", stderr="")

    monkeypatch.setattr(simulate_evas.subprocess, "run", fake_subprocess_run)

    proc = simulate_evas.run_evas(run_dir, tb, out_dir, timeout_s=1)

    assert proc.returncode == 0
    assert captured["cmd"] == ["evas", "simulate", "tb.scs", "-o", str(out_dir)]
    assert captured["env"]["EVAS_ENGINE"] == "evas2"
    assert (out_dir / "evas.log").read_text(encoding="utf-8") == "\n"


def test_v2_lowpass_checker_uses_yaml_thresholds(tmp_path: Path) -> None:
    csv_path = tmp_path / "tran.csv"
    csv_path.write_text(
        "\n".join(
            [
                "time,vin,vout",
                "0,0.0,0.00",
                "1e-8,0.0,0.05",
                "2.1e-8,0.8,0.10",
                "3.0e-8,0.8,0.30",
                "5.0e-8,0.8,0.60",
                "9.0e-8,0.8,0.74",
                "1.5e-7,0.8,0.79",
                "1.6e-7,0.8,0.80",
            ]
        ),
        encoding="utf-8",
    )
    checks_config = {
        "checker_parameters": {
            "sample_times_ns": [30.0, 50.0, 90.0, 150.0],
            "response_sample_1_min_v": "0.55",
            "response_sample_2_min_v": "0.70",
            "response_sample_3_min_v": "0.76",
        }
    }

    score, notes = simulate_evas.evaluate_behavior(
        "vbr1_l1_first_order_lowpass",
        csv_path,
        checks_config=checks_config,
    )
    assert score == 1.0
    assert "checker_config_parameters=first_order_lowpass" in notes[0]

    strict_config = {
        "checker_parameters": {
            **checks_config["checker_parameters"],
            "response_sample_1_min_v": "0.65",
        }
    }
    strict_score, strict_notes = simulate_evas.evaluate_behavior(
        "vbr1_l1_first_order_lowpass",
        csv_path,
        checks_config=strict_config,
    )
    assert strict_score == 0.0
    assert "response_fast_enough=False" in strict_notes[0]


def test_behavior_checker_policy_marks_streaming_validated(monkeypatch) -> None:
    monkeypatch.delenv("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", raising=False)
    monkeypatch.delenv("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", raising=False)

    policy = simulate_evas.behavior_checker_policy(
        "lfsr_smoke",
        ["streaming_checker:transitions=196 hi_frac=0.473"],
    )

    assert policy["implementation"] == "streaming_validated"
    assert policy["streaming_registered"] is True
    assert policy["streaming_validated"] is True
    assert policy["streaming_used"] is True


def test_behavior_checker_policy_marks_row_fallback(monkeypatch) -> None:
    monkeypatch.delenv("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", raising=False)
    monkeypatch.delenv("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", raising=False)

    policy = simulate_evas.behavior_checker_policy("lfsr_smoke", ["expected column missing"])

    assert policy["implementation"] == "row_based_fallback_from_streaming"
    assert policy["streaming_used"] is False


def test_parse_evas_performance_counters_keeps_rust_backend_evidence() -> None:
    text = """
Performance counters:
    rust_static_eval_available = 1
    rust_static_eval_calls = 42
    rust_static_eval_segments = 3
    rust_static_eval_max_segment_models = 7
Indexed array profile:
    node_count = 128
    max_abs_diff = 0.0
Indexed model IO plan:
    model_count = 9
"""

    counters = simulate_evas.parse_evas_performance_counters(text)

    assert counters["rust_static_eval_available"] == 1
    assert counters["rust_static_eval_calls"] == 42
    assert counters["rust_static_eval_segments"] == 3
    assert counters["rust_static_eval_max_segment_models"] == 7
    assert counters["indexed_array_profile.node_count"] == 128
    assert counters["indexed_array_profile.max_abs_diff"] == 0.0
    assert counters["indexed_model_io_plan.model_count"] == 9


def test_evas_reported_timing_is_bridged_into_split_without_step_count() -> None:
    text = """
Tran analysis time: CPU = 120.0 ms, elapsed = 125.0 ms
Number of accepted tran steps = 4096
Runner timing counters:
    derive_bus_signals_s = 0.012345 s
    csv_write_s = 0.067890 s

Total time: CPU = 210.0 ms, elapsed = 220.0 ms.
"""

    timing = simulate_evas.parse_evas_timing(text)
    split = {"evas_subprocess_wall_s": 0.300}

    simulate_evas.add_evas_reported_timing_split(split, timing)

    assert split["evas_reported_tran_elapsed_s"] == 0.125
    assert split["evas_reported_total_elapsed_s"] == 0.220
    assert split["evas_runner_derive_bus_signals_s"] == 0.012345
    assert split["evas_runner_csv_write_s"] == 0.067890
    assert abs(split["evas_subprocess_unattributed_s"] - 0.080) < 1e-12
    assert "evas_runner_accepted_tran_steps" not in split


def test_required_trace_signals_follow_streaming_checker_contract() -> None:
    signals = simulate_evas.required_trace_signals_for_checker(
        "vbr1_l2_weighted_sar_adc_dac_loop_tb"
    )

    assert "vin_sample" in signals
    assert "trial_vdac" in signals
    assert {f"dout_{idx}" for idx in range(8)}.issubset(signals)
    assert "dco_clk" not in signals
    assert simulate_evas.required_trace_signals_for_checker("unknown_task") == frozenset()


def test_spectre_preflight_rejects_reserved_port_names(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "bad.va").write_text(
        '`include "disciplines.vams"\n'
        "module bad(sin, out);\n"
        "input sin; output out; electrical sin, out;\n"
        "analog begin V(out) <+ V(sin); end\n"
        "endmodule\n",
        encoding="utf-8",
    )

    failures = simulate_evas.spectre_aligned_veriloga_preflight(run_dir)

    assert "bad.va:spectre_reserved_identifier:module_port:sin" in failures
    assert "bad.va:spectre_reserved_identifier:input:sin" in failures
    assert "bad.va:spectre_reserved_identifier:electrical:sin" in failures


def test_spectre_preflight_rejects_reserved_variables_and_parameters(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "bad.va").write_text(
        '`include "disciplines.vams"\n'
        "module bad(vin, out);\n"
        "input vin; output out; electrical vin, out;\n"
        "parameter real transition = 1n;\n"
        "real cross;\n"
        "analog begin cross = V(vin); V(out) <+ cross; end\n"
        "endmodule\n",
        encoding="utf-8",
    )

    failures = simulate_evas.spectre_aligned_veriloga_preflight(run_dir)

    assert "bad.va:spectre_reserved_identifier:parameter:transition" in failures
    assert "bad.va:spectre_reserved_identifier:real:cross" in failures


def test_spectre_preflight_allows_reserved_function_calls(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "ok.va").write_text(
        '`include "disciplines.vams"\n'
        "module ok(vin, out);\n"
        "input vin; output out; electrical vin, out;\n"
        "real y;\n"
        "analog begin @(initial_step) y = 0.0; "
        "@(timer(0, 1n)) y = tanh(V(vin)); V(out) <+ transition(y, 0, 1p); end\n"
        "endmodule\n",
        encoding="utf-8",
    )

    failures = simulate_evas.spectre_aligned_veriloga_preflight(run_dir)

    assert failures == []


def test_row_checker_required_set_gets_sparse_trace_contract(monkeypatch) -> None:
    monkeypatch.delenv("VAEVAS_DISABLE_REQUIRED_TRACE", raising=False)
    monkeypatch.delenv("VAEVAS_DISABLE_ROW_CHECKER_TRACE_CONTRACTS", raising=False)

    task_id = "vbr1_l1_log_rssi_power_detector_tb"
    signals = simulate_evas.required_trace_signals_for_checker(task_id)
    policy = simulate_evas.behavior_checker_policy(task_id, [])

    assert simulate_evas.required_trace_contract_kind_for_checker(task_id) == "row_required_set"
    assert {"time", "clk", "rst", "vin", "out", "metric"}.issubset(signals)
    assert policy["trace_contract_kind"] == "row_required_set"
    assert policy["trace_contract_signal_count"] == 5


def test_row_checker_trace_contract_infers_structured_bit_columns(monkeypatch) -> None:
    monkeypatch.delenv("VAEVAS_DISABLE_REQUIRED_TRACE", raising=False)
    monkeypatch.delenv("VAEVAS_DISABLE_ROW_CHECKER_TRACE_CONTRACTS", raising=False)
    simulate_evas._CHECKER_TRACE_CONTRACT_CACHE.clear()

    divider = simulate_evas.required_trace_signals_for_checker("vbm1_resettable_counter_divider_tb")
    dwa_smoke = simulate_evas.required_trace_signals_for_checker("dwa_ptr_gen_smoke")
    dwa = simulate_evas.required_trace_signals_for_checker("vbr1_l1_dwa_dem_encoder_tb")
    therm = simulate_evas.required_trace_signals_for_checker("vbr1_l1_unit_element_thermometer_dac_tb")
    flash = simulate_evas.required_trace_signals_for_checker("vbr1_l2_flash_adc_mini_array_tb")

    assert {"clk_in", "clk_out", "lock"}.issubset(divider)
    assert {f"div_code_{idx}" for idx in range(8)}.issubset(divider)
    assert {f"ptr_{idx}" for idx in range(16)}.issubset(dwa_smoke)
    assert {f"cell_en_{idx}" for idx in range(16)}.issubset(dwa_smoke)
    assert {f"ptr_{idx}" for idx in range(16)}.issubset(dwa)
    assert {f"cell_en_{idx}" for idx in range(16)}.issubset(dwa)
    assert {f"code_{idx}" for idx in range(4)}.issubset(dwa)
    assert {f"seg{idx}" for idx in range(15)}.issubset(therm)
    assert {f"cmp{idx}" for idx in range(7)}.issubset(flash)


def test_required_trace_signals_allow_extra_debug_columns(monkeypatch) -> None:
    monkeypatch.delenv("VAEVAS_DISABLE_REQUIRED_TRACE", raising=False)
    monkeypatch.delenv("VAEVAS_DISABLE_ROW_CHECKER_TRACE_CONTRACTS", raising=False)
    monkeypatch.setenv("VAEVAS_EXTRA_TRACE_SIGNALS", "debug_a, debug_b")
    monkeypatch.setenv(
        "VAEVAS_EXTRA_TRACE_SIGNALS_BY_TASK",
        "vbr1_l1_precision_rectifier_envelope_detector=debug_entry;other=ignored",
    )
    monkeypatch.setenv(
        "VAEVAS_EXTRA_TRACE_SIGNALS_VBR1_L1_PRECISION_RECTIFIER_ENVELOPE_DETECTOR_TB",
        "debug_exact",
    )

    signals = simulate_evas.required_trace_signals_for_checker(
        "vbr1_l1_precision_rectifier_envelope_detector_tb"
    )
    policy = simulate_evas.behavior_checker_policy(
        "vbr1_l1_precision_rectifier_envelope_detector_tb",
        [],
    )

    assert {"time", "clk", "rst", "vin", "rect", "env", "metric"}.issubset(signals)
    assert {"debug_a", "debug_b", "debug_entry", "debug_exact"}.issubset(signals)
    assert "ignored" not in signals
    assert policy["trace_contract_kind"] == "streaming"
    assert policy["extra_trace_signal_count"] == 4


def test_sparse_row_checker_failure_does_not_rerun_full_trace(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("VAEVAS_DISABLE_REQUIRED_TRACE", raising=False)
    monkeypatch.delenv("VAEVAS_DISABLE_ROW_CHECKER_TRACE_CONTRACTS", raising=False)

    task_id = "vbr1_l1_log_rssi_power_detector_tb"
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    (task_dir / "meta.json").write_text(
        json.dumps({"id": task_id, "scoring": ["dut_compile", "tb_compile", "sim_correct"]}),
        encoding="utf-8",
    )
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    dut = src_dir / "dut.va"
    tb = src_dir / "tb.scs"
    dut.write_text('`include "disciplines.vams"\nmodule m(a); electrical a; endmodule\n', encoding="utf-8")
    tb.write_text("tran tran stop=1n\n", encoding="utf-8")

    calls: list[bool] = []

    def fake_run_evas(
        run_dir: Path,
        tb_file: Path,
        output_dir: Path,
        timeout_s: int,
        required_trace_signals=None,
    ):
        calls.append(bool(required_trace_signals))
        (output_dir / "tran.csv").write_text("time,out\n0,1\n", encoding="utf-8")
        return subprocess.CompletedProcess(
            ["evas"],
            0,
            stdout=(
                "Compiled Verilog-A module: m\n"
                "Transient Analysis\n"
                "Tran analysis time: CPU = 1.0 ms, elapsed = 1.0 ms\n"
                "Total time: CPU = 1.0 ms, elapsed = 1.0 ms.\n"
            ),
            stderr="",
        )

    def fake_evaluate_behavior_with_timeout(
        task_id_arg: str,
        csv_path: Path,
        *,
        timeout_s: int,
        checks_config=None,
    ):
        assert task_id_arg == task_id
        return 0.0, ["missing inferred column"]

    monkeypatch.setattr(simulate_evas, "run_evas", fake_run_evas)
    monkeypatch.setattr(
        simulate_evas,
        "evaluate_behavior_with_timeout",
        fake_evaluate_behavior_with_timeout,
    )

    result = simulate_evas.run_case(task_dir, dut, tb, output_root=tmp_path / "out", timeout_s=5)

    assert calls == [True]
    assert result["status"] == "FAIL_SIM_CORRECTNESS"
    assert result["scores"]["sim_correct"] == 0.0
    assert "missing inferred column" in result["notes"]
    assert "sparse_trace_evas_subprocess_wall_s" not in result["timing_split"]


def test_parse_evas_performance_counters_includes_trace_contract() -> None:
    text = """
Trace counters:
    required_trace_signal_count = 18
    required_trace_record_node_count = 18
    required_trace_missing_node_count = 0
Runner timing counters:
    csv_write_s = 0.012345 s
Trace counters:
    required_trace_csv_signal_count = 18
"""

    counters = simulate_evas.parse_evas_performance_counters(text)

    assert counters["trace.required_trace_signal_count"] == 18
    assert counters["trace.required_trace_record_node_count"] == 18
    assert counters["trace.required_trace_missing_node_count"] == 0
    assert counters["trace.required_trace_csv_signal_count"] == 18
