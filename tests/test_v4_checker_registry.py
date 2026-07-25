from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNERS = ROOT / "runners"
if str(RUNNERS) not in sys.path:
    sys.path.insert(0, str(RUNNERS))


TARGET_TASKS = {
    "544-successive-approximation-calibration-search-fsm-testbench":
        "v4_044_successive_approximation_calibration_search_fsm",
    "558-masked-config-update-32b-testbench": "v4_058_masked_config_update_32b",
    "647-control-word-encoder-7b-testbench": "v4_147_control_word_encoder_7b",
    "821-charge-pump-pulse-balancer-testbench": "v4_321_charge_pump_pulse_balancer",
    "822-glitchless-clock-mux-selector-testbench": "v4_322_glitchless_clock_mux_selector",
    "823-programmable-clock-skew-aligner-testbench": "v4_323_programmable_clock_skew_aligner",
    "824-duty-cycle-window-monitor-testbench": "v4_324_duty_cycle_window_monitor",
    "825-fine-coarse-tdc-encoder-testbench": "v4_325_fine_coarse_tdc_encoder",
    "826-fractional-delay-dtc-macro-testbench": "v4_326_fractional_delay_dtc_macro",
    "827-cdr-eye-monitor-testbench": "v4_327_cdr_eye_monitor",
    "828-pam4-linearity-monitor-testbench": "v4_328_pam4_linearity_monitor",
    "829-ctle-adaptation-loop-testbench": "v4_329_ctle_adaptation_loop",
    "830-ffe-tap-adaptation-monitor-testbench": "v4_330_ffe_tap_adaptation_monitor",
    "864-iq-upconversion-mixer-chain-testbench": "v4_364_iq_upconversion_mixer_chain",
    "898-two-stage-opamp-slew-macromodel-testbench":
        "v4_398_two_stage_opamp_slew_macromodel",
}


def test_current_v4_profiles_resolve_exact_modular_checkers() -> None:
    from checkers.v4.registry import load_checker

    tasks_root = (
        ROOT
        / "benchmark-vabench-release-v4"
        / "release"
        / "benchmarkv4"
        / "tasks"
    )
    for task_slug, expected_checker_id in TARGET_TASKS.items():
        profile = json.loads(
            (tasks_root / task_slug / "evaluator" / "checker_profile.json").read_text(
                encoding="utf-8"
            )
        )
        checker_id = profile["checker_task_id"]
        assert checker_id == expected_checker_id
        assert callable(load_checker(checker_id)), checker_id


def test_v4_checker_loader_fails_closed_for_unknown_or_malformed_ids() -> None:
    from checkers.v4.registry import load_checker

    assert load_checker("v4_999_not_published") is None
    assert load_checker("v3_044_successive_approximation_calibration_search_fsm") is None
    assert load_checker("../../task_044") is None


def test_v4_checker_loader_preserves_released_checker_semantics() -> None:
    from checkers.v4.registry import load_checker, published_checker_ids

    crossing_checker = load_checker("v4_074_crossing_metric_writer")
    current_074_checker = load_checker(
        "v4_074_sampled_true_rms_to_dc_converter"
    )
    assert crossing_checker is not None
    assert current_074_checker is not None

    crossing_rows = [
        {"time": 0.0, "vin": 0.0, "done": 0.0},
        {"time": 1.0e-9, "vin": 0.0, "done": 0.0},
        {"time": 2.0e-9, "vin": 0.9, "done": 0.9},
        {"time": 4.0e-9, "vin": 0.9, "done": 0.9},
    ]
    assert crossing_checker(crossing_rows)[0]
    assert not current_074_checker(crossing_rows)[0]

    final_step_checker = load_checker("v4_091_final_step_file_metric")
    current_091_checker = load_checker(
        "v4_091_chopper_stabilized_differential_amplifier"
    )
    assert final_step_checker is not None
    assert current_091_checker is not None

    final_step_rows: list[dict[str, float]] = []
    for edge, level in zip(
        (10e-9, 30e-9, 50e-9, 70e-9),
        (0.225, 0.45, 0.675, 0.9),
    ):
        final_step_rows.extend(
            [
                {"time": edge - 0.2e-9, "ref": 0.0, "metric_out": level},
                {"time": edge, "ref": 0.9, "metric_out": level},
                {"time": edge + 1.0e-9, "ref": 0.0, "metric_out": level},
                {"time": edge + 2.0e-9, "ref": 0.0, "metric_out": level},
                {"time": edge + 5.0e-9, "ref": 0.0, "metric_out": level},
                {"time": edge + 8.0e-9, "ref": 0.0, "metric_out": level},
            ]
        )
    final_step_rows.sort(key=lambda row: row["time"])
    assert final_step_checker(final_step_rows)[0]
    assert not current_091_checker(final_step_rows)[0]

    published = published_checker_ids()
    assert len(published) == 400
    assert "v4_074_crossing_metric_writer" not in published
    assert "v4_091_final_step_file_metric" not in published


def _lowpass_rows(
    *,
    vin_low: float,
    vin_high: float,
    passthrough: bool = False,
    initial_vout: float = 0.0,
    end_time: float = 110e-9,
) -> list[dict[str, float]]:
    step_time = 10e-9
    response_span = vin_high - vin_low
    samples = [
        (0.0, vin_low, initial_vout),
        (0.3e-9, vin_low, initial_vout),
        (9.9e-9, vin_low, vin_low),
    ]
    for index in range(0, 41):
        time_s = step_time + index * 0.25e-9
        update_count = max(0, math.floor((time_s - step_time) / 0.5e-9) + 1)
        normalized = 1.0 if passthrough else 1.0 - 0.975**update_count
        samples.append((time_s, vin_high, vin_low + normalized * response_span))
    samples.append((end_time, vin_high, vin_high))
    samples.sort()
    return [{"time": time_s, "vin": vin, "vout": vout} for time_s, vin, vout in samples]


def test_first_order_lowpass_checker_is_relative_to_observed_step_amplitude() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_007_first_order_lowpass")
    assert checker is not None
    assert checker(_lowpass_rows(vin_low=0.0, vin_high=0.3))[0]
    assert checker(_lowpass_rows(vin_low=0.0, vin_high=0.5))[0]
    assert checker(_lowpass_rows(vin_low=0.1, vin_high=1.0))[0]

    passed, detail = checker(_lowpass_rows(vin_low=0.0, vin_high=0.5, passthrough=True))
    assert not passed
    assert "first_mismatch=P_LOW_PASS_RESPONSE" in detail


def test_first_order_lowpass_checker_is_independent_of_tran_stop() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_007_first_order_lowpass")
    assert checker is not None
    for end_time in (25e-9, 160e-9, 500e-9):
        passed, detail = checker(
            _lowpass_rows(vin_low=0.0, vin_high=1.0, end_time=end_time)
        )
        assert passed, detail


def test_registry_normalizes_annotated_affine_trace_coordinates() -> None:
    from checkers.v4.registry import load_checker
    from checkers.v4.stimulus_relative import transformed_rows

    checker = load_checker("v4_007_first_order_lowpass")
    assert checker is not None
    rows = _lowpass_rows(vin_low=0.0, vin_high=0.8)

    assert checker(rows) == checker(transformed_rows(rows))


def test_first_order_lowpass_registry_checker_preserves_initial_state_gate() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_007_first_order_lowpass")
    assert checker is not None

    passed, detail = checker(
        _lowpass_rows(vin_low=0.0, vin_high=0.8, initial_vout=0.195)
    )

    assert not passed
    assert "first_mismatch=P_INITIAL_STATE" in detail


def test_bandgap_checker_reports_first_hold_mismatch(monkeypatch) -> None:
    from checkers.v4 import task_020

    edges = [float(index) for index in range(1, 25)]
    samples: dict[tuple[str, float], float] = {}
    expected = 0.0
    for index, edge in enumerate(edges):
        next_edge = edges[index + 1] if index + 1 < len(edges) else 25.0
        if index == 0:
            rst, vin = 0.9, 0.8
        elif index == 1:
            rst, vin = 0.0, 0.5
        else:
            rst, vin = 0.0, 0.8
        samples[("rst", edge)] = rst
        samples[("vin", edge)] = vin
        if rst > 0.45 or vin < 0.58:
            expected = 0.0
            expected_metric = 0.0
        else:
            target = 0.55 + 0.020 * (vin - 0.75)
            expected += 0.35 * (target - expected)
            expected_metric = 0.9 if expected > 0.48 else 0.2
        early_time = edge + 0.36 * (next_edge - edge)
        late_time = edge + 0.76 * (next_edge - edge)
        for sample_time in (early_time, late_time):
            samples[("rst", sample_time)] = rst
            samples[("vin", sample_time)] = vin
        samples[("out", early_time)] = expected
        samples[("metric", early_time)] = expected_metric
        samples[("out", late_time)] = expected + (0.1 if index == 10 else 0.0)

    monkeypatch.setattr(task_020, "threshold_crossings", lambda *_args, **_kwargs: edges)
    monkeypatch.setattr(
        task_020,
        "sample_signal",
        lambda _rows, signal, time_s: samples.get((signal, time_s)),
    )
    rows = [
        {"time": 0.0, "clk": 0.0, "rst": 0.0, "vin": 0.0, "out": 0.0, "metric": 0.0},
        {"time": 25.0, "clk": 0.0, "rst": 0.0, "vin": 0.0, "out": 0.0, "metric": 0.0},
    ]

    passed, detail = task_020.check_bandgap_reference_macro_model(rows)

    assert not passed
    assert "first_mismatch=P_CLOCKED_HOLD" in detail
    assert "expected=" in detail
    assert "observed=" in detail
    assert "time=" in detail
    assert "tolerance=0.025" in detail


def test_bandgap_checker_does_not_treat_midcycle_brownout_as_hold_failure(
    monkeypatch,
) -> None:
    from checkers.v4 import task_020

    edges = [float(index) for index in range(1, 25)]
    samples: dict[tuple[str, float], float] = {}
    expected = 0.0
    for index, edge in enumerate(edges):
        next_edge = edges[index + 1] if index + 1 < len(edges) else 25.0
        if index == 0:
            rst, vin = 0.9, 0.8
        elif index == 1:
            rst, vin = 0.0, 0.5
        else:
            rst, vin = 0.0, 0.8
        samples[("rst", edge)] = rst
        samples[("vin", edge)] = vin
        if rst > 0.45 or vin < 0.58:
            expected = 0.0
            expected_metric = 0.0
        else:
            target = 0.55 + 0.020 * (vin - 0.75)
            expected += 0.35 * (target - expected)
            expected_metric = 0.9 if expected > 0.48 else 0.2
        early_time = edge + 0.36 * (next_edge - edge)
        late_time = edge + 0.76 * (next_edge - edge)
        early_vin = vin
        late_vin = 0.5 if index == 10 else vin
        samples[("rst", early_time)] = rst
        samples[("rst", late_time)] = rst
        samples[("vin", early_time)] = early_vin
        samples[("vin", late_time)] = late_vin
        samples[("out", early_time)] = expected
        samples[("metric", early_time)] = expected_metric
        samples[("out", late_time)] = 0.0 if index == 10 else expected

    monkeypatch.setattr(task_020, "threshold_crossings", lambda *_args, **_kwargs: edges)
    monkeypatch.setattr(
        task_020,
        "sample_signal",
        lambda _rows, signal, time_s: samples.get((signal, time_s)),
    )
    rows = [
        {"time": 0.0, "clk": 0.0, "rst": 0.0, "vin": 0.0, "out": 0.0, "metric": 0.0},
        {"time": 25.0, "clk": 0.0, "rst": 0.0, "vin": 0.0, "out": 0.0, "metric": 0.0},
    ]

    passed, detail = task_020.check_bandgap_reference_macro_model(rows)

    assert passed, detail
    assert "P_CLOCKED_HOLD mismatch_count=0" in detail


def _divide_8_9_rows(first_count: int, *, honor_mc: bool = True) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    count = first_count
    rising_index = 0
    previous_clk = 0.0
    out = 0.0
    for step in range(321):
        time_ns = step * 0.1
        clk = 1.2 if any(start <= time_ns < start + 0.5 for start in [1.0 + 2.0 * i for i in range(15)]) else 0.0
        mc = 1.2 if 12.0 <= time_ns < 24.0 else 0.0
        if previous_clk < 0.6 <= clk:
            if rising_index:
                modulus = 9 if honor_mc and mc > 0.6 else 8
                count = (count + 1) % modulus
            out = 1.2 if count < 4 else 0.0
            rising_index += 1
        rows.append({"time": time_ns * 1e-9, "clkin": clk, "mc": mc, "out": out})
        previous_clk = clk
    return rows


def test_divide_8_9_checker_accepts_all_public_initial_high_window_phases() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_160_divide_by_8_9_switch")
    assert checker is not None
    for first_count in range(4):
        passed, detail = checker(_divide_8_9_rows(first_count))
        assert passed, (first_count, detail)

    passed, detail = checker(_divide_8_9_rows(0, honor_mc=False))
    assert not passed
    assert "first_mismatch=P_MODULUS_SWITCHING_ON_MC_EDGES" in detail


def test_all_current_benchmarkv4_tasks_resolve_migrated_checker_candidates() -> None:
    from checkers.v4.registry import load_checker

    tasks_root = (
        ROOT
        / "benchmark-vabench-release-v4"
        / "release"
        / "benchmarkv4"
        / "tasks"
    )
    missing: list[tuple[str, str]] = []
    for task_dir in sorted(tasks_root.iterdir()):
        if not task_dir.is_dir():
            continue
        record = json.loads((task_dir / "task_record.json").read_text(encoding="utf-8"))
        checker_id = record["checker_task_id"]
        if not callable(load_checker(checker_id)):
            missing.append((task_dir.name, checker_id))

    assert missing == []


def _masked_row(time_s: float, old_word: int, new_word: int, mask_word: int) -> dict[str, float]:
    row: dict[str, float] = {"time": time_s}
    for bit in range(32):
        old = (old_word >> bit) & 1
        new = (new_word >> bit) & 1
        mask = (mask_word >> bit) & 1
        row[f"old{bit}"] = 0.9 * old
        row[f"new{bit}"] = 0.9 * new
        row[f"mask{bit}"] = 0.9 * mask
        row[f"out{bit}"] = 0.9 * (new if mask else old)
    return row


def test_masked_config_checker_is_relative_to_observed_vectors_not_fixed_times() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_058_masked_config_update_32b")
    assert checker is not None
    alternating = 0xAAAAAAAA
    inverse = 0x55555555
    rows = [
        _masked_row(101e-9, alternating, inverse, 0),
        _masked_row(103e-9, alternating, inverse, 0xFFFFFFFF),
        _masked_row(107e-9, alternating, inverse, alternating),
    ]
    assert checker(rows)[0]


def _thermometer_row(time_s: float, vin: float, output_code: int | None = None) -> dict[str, float]:
    code = output_code
    if code is None:
        code = max(0, min(16, int(16.0 * min(1.0, max(0.0, vin)))))
    row = {"time": time_s, "vin": vin}
    for bit in range(16):
        row[f"t{bit}"] = 0.9 if bit < code else 0.0
    return row


def test_thermometer_checker_is_relative_to_observed_vin_segments() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_052_thermometer_bus_encoder")
    assert checker is not None
    rows = [
        _thermometer_row(77.0e-9, 0.02),
        _thermometer_row(78.5e-9, 0.22),
        _thermometer_row(81.0e-9, 0.51),
        _thermometer_row(83.5e-9, 0.88),
        _thermometer_row(89.0e-9, 1.05),
    ]
    assert checker(rows)[0]

    rows[2]["t15"] = 0.9
    passed, detail = checker(rows)
    assert not passed
    assert "property_id=P_UNIFORM_SEGMENTS" in detail
    assert "category=wrong_segment_count" in detail


def test_thermometer_checker_ignores_single_row_vin_ramp_transients() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_052_thermometer_bus_encoder")
    assert checker is not None
    rows = [
        _thermometer_row(0.0e-9, 0.02),
        _thermometer_row(0.8e-9, 0.02),
        _thermometer_row(1.01e-9, 0.08, output_code=0),
        _thermometer_row(1.03e-9, 0.14, output_code=1),
        _thermometer_row(1.10e-9, 0.22),
        _thermometer_row(2.80e-9, 0.22),
        _thermometer_row(3.01e-9, 0.31, output_code=3),
        _thermometer_row(3.12e-9, 0.51),
        _thermometer_row(4.80e-9, 0.51),
        _thermometer_row(5.10e-9, 0.88),
        _thermometer_row(6.80e-9, 0.88),
        _thermometer_row(7.10e-9, 1.05),
        _thermometer_row(8.80e-9, 1.05),
    ]
    assert checker(rows)[0]


def test_slew_rate_dac_checker_rejects_unexcited_trace() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_053_slew_rate_dac4")
    assert checker is not None
    rows = [
        {
            "time": index * 0.1e-9,
            "d3": 0.0,
            "d2": 0.0,
            "d1": 0.0,
            "d0": 0.0,
            "vout": 0.0,
        }
        for index in range(80)
    ]
    passed, detail = checker(rows)
    assert not passed
    assert "insufficient_code_excitation" in detail


def _config_latch_row(
    time_s: float,
    *,
    en: bool,
    data_word: int,
    output_word: int | None = None,
) -> dict[str, float]:
    if output_word is None:
        output_word = data_word if en else 0
    row = {"time": time_s, "en": 0.9 if en else 0.0}
    for bit in range(32):
        row[f"d{bit}"] = 0.9 if (data_word >> bit) & 1 else 0.0
        row[f"q{bit}"] = 0.9 if (output_word >> bit) & 1 else 0.0
    return row


def test_config_latch_checker_is_relative_to_observed_vectors() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_056_config_latch_32b_clocked")
    assert checker is not None
    rows = [
        _config_latch_row(201.0e-9, en=True, data_word=0x0000000F),
        _config_latch_row(204.0e-9, en=True, data_word=0x00F0000F),
        _config_latch_row(211.0e-9, en=False, data_word=0xFFFFFFFF),
        _config_latch_row(219.0e-9, en=True, data_word=0xA5A55A5A),
    ]
    assert checker(rows)[0]

    rows[2] = _config_latch_row(
        211.0e-9,
        en=False,
        data_word=0xFFFFFFFF,
        output_word=0x00F0000F,
    )
    passed, detail = checker(rows)
    assert not passed
    assert "property_id=P_DISABLED_CLEAR" in detail
    assert "category=disabled_clear_mismatch" in detail


def test_control_word_checker_accepts_a_short_stable_public_trace() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_147_control_word_encoder_7b")
    assert checker is not None
    rows: list[dict[str, float]] = []
    for time_s in (0.2e-9, 0.4e-9):
        row: dict[str, float] = {"time": time_s}
        for ctrl in (42, 85):
            for bit in range(7):
                row[f"d{bit}_{ctrl}"] = 0.9 if (ctrl >> bit) & 1 else 0.0
        rows.append(row)
    assert checker(rows)[0]


def _control_word_rows(control_words: tuple[int, ...]) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for time_s in (100.0e-9, 101.0e-9, 102.0e-9, 103.0e-9):
        row: dict[str, float] = {"time": time_s}
        for ctrl in control_words:
            for bit in range(7):
                row[f"d{bit}_{ctrl}"] = 0.9 if (ctrl >> bit) & 1 else 0.0
        rows.append(row)
    return rows


def test_control_word_checker_accepts_the_original_score_profile() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_147_control_word_encoder_7b")
    assert checker is not None
    assert checker(_control_word_rows((0, 19, 108, 127)))[0]


def test_control_word_checker_rejects_partial_or_single_group_traces() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_147_control_word_encoder_7b")
    assert checker is not None

    partial = _control_word_rows((42, 85))
    for row in partial:
        row.pop("d6_85")
    passed, detail = checker(partial)
    assert not passed
    assert detail == "missing_columns=d6_85"

    passed, detail = checker(_control_word_rows((42,)))
    assert not passed
    assert detail == "insufficient_control_word_coverage=[42]"


def test_control_word_checker_rejects_bit_and_rail_mutations() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_147_control_word_encoder_7b")
    assert checker is not None

    bit_wrong = _control_word_rows((42, 85))
    for row in bit_wrong:
        row["d1_42"] = 0.0
    assert not checker(bit_wrong)[0]

    off_rail = _control_word_rows((0, 19, 108, 127))
    for row in off_rail:
        row["d3_19"] = 0.45
    assert not checker(off_rail)[0]


def test_sar_calibration_checker_uses_clock_and_reset_events_not_absolute_windows() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_044_successive_approximation_calibration_search_fsm")
    assert checker is not None
    rows = [
        {"time": 100.0e-9, "clk": 0.0, "rst": 0.9, "vin": 0.45, "out": 0.45, "metric": 0.0},
        {"time": 100.3e-9, "clk": 0.0, "rst": 0.9, "vin": 0.45, "out": 0.45, "metric": 0.0},
        {"time": 100.5e-9, "clk": 0.0, "rst": 0.0, "vin": 0.60, "out": 0.45, "metric": 0.0},
    ]
    state = 0.45
    step = 0.18
    for index, vin in enumerate((0.60, 0.30, 0.70, 0.20, 0.80), start=1):
        edge = (100.5 + 2.0 * index) * 1e-9
        rows.append({"time": edge - 0.2e-9, "clk": 0.0, "rst": 0.0, "vin": vin, "out": state, "metric": 0.9 if index > 4 else 0.0})
        rows.append({"time": edge, "clk": 0.9, "rst": 0.0, "vin": vin, "out": state, "metric": 0.9 if index > 4 else 0.0})
        if index <= 4:
            state += step if vin > 0.45 else -step
            state = min(0.85, max(0.05, state))
            step *= 0.5
        rows.append({"time": edge + 0.3e-9, "clk": 0.9, "rst": 0.0, "vin": vin, "out": state, "metric": 0.9 if index >= 4 else 0.0})
    assert checker(rows)[0]


def test_debounce_checker_uses_observed_edges_after_a_time_shift() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_005_debounce_latch")
    assert checker is not None
    rows = [
        {"time": 100.0e-9, "sig": 0.0, "rst_n": 0.0, "out": 0.0},
        {"time": 101.0e-9, "sig": 0.0, "rst_n": 0.9, "out": 0.0},
        {"time": 110.0e-9, "sig": 0.0, "rst_n": 0.9, "out": 0.0},
        {"time": 110.1e-9, "sig": 0.9, "rst_n": 0.9, "out": 0.0},
        {"time": 122.1e-9, "sig": 0.9, "rst_n": 0.9, "out": 0.0},
        {"time": 122.4e-9, "sig": 0.9, "rst_n": 0.9, "out": 0.9},
        {"time": 124.1e-9, "sig": 0.9, "rst_n": 0.9, "out": 0.9},
        {"time": 140.0e-9, "sig": 0.9, "rst_n": 0.9, "out": 0.9},
        {"time": 140.1e-9, "sig": 0.0, "rst_n": 0.9, "out": 0.9},
        {"time": 140.4e-9, "sig": 0.0, "rst_n": 0.9, "out": 0.0},
        {"time": 142.1e-9, "sig": 0.0, "rst_n": 0.9, "out": 0.0},
    ]
    assert checker(rows)[0]


def test_simulate_evas_resolves_the_modular_v4_registry() -> None:
    import simulate_evas

    for checker_id in TARGET_TASKS.values():
        assert simulate_evas.has_behavior_check(checker_id), checker_id


def test_checker_package_imports_from_a_clean_repository_root() -> None:
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from runners.checkers.v4.registry import load_checker; "
                "assert load_checker('v4_364_iq_upconversion_mixer_chain')"
            ),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert probe.returncode == 0, probe.stderr


def test_all_checker_modules_import_from_a_clean_repository_root() -> None:
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from runners.checkers.v4.registry import "
                "load_checker, published_checker_ids; "
                "ids = published_checker_ids(); "
                "assert len(ids) == 400, len(ids); "
                "missing = [checker_id for checker_id in ids if load_checker(checker_id) is None]; "
                "assert not missing, missing"
            ),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
    )
    assert probe.returncode == 0, probe.stderr


def _two_stage_opamp_trace(
    *,
    start_s: float = 250e-9,
    mutation: str | None = None,
    cycles: int = 8,
) -> list[dict[str, float]]:
    signal_names = (
        "vinp",
        "vinn",
        "clk",
        "rst",
        "enable",
        "load_step",
        "vout",
        "stage1_metric",
        "slew_metric",
        "clamp_flag",
        "settled",
    )

    def row(time_s: float, **values: float) -> dict[str, float]:
        result = {name: 0.0 for name in signal_names}
        result.update(values)
        result["time"] = time_s
        return result

    rows = [
        row(
            start_s,
            vinp=0.47,
            vinn=0.43,
            rst=0.9,
            load_step=0.45,
            vout=0.45,
            stage1_metric=0.45,
        ),
        row(
            start_s + 0.7e-9,
            vinp=0.47,
            vinn=0.43,
            load_step=0.45,
            vout=0.45,
            stage1_metric=0.45,
        ),
        row(
            start_s + 1.4e-9,
            vinp=0.47,
            vinn=0.43,
            enable=0.9,
            load_step=0.45,
            vout=0.45,
            stage1_metric=0.45,
        ),
    ]

    vout = 0.45
    settle_count = 0
    active_outputs: dict[str, float] | None = None
    for cycle in range(cycles):
        edge_s = start_s + (3.0 + 3.1 * cycle) * 1e-9
        vinp = 0.455
        vinn = 0.45
        load_step = 0.45
        previous_outputs = active_outputs or {
            "vout": 0.45,
            "stage1_metric": 0.45,
            "slew_metric": 0.0,
            "clamp_flag": 0.0,
            "settled": 0.0,
        }
        rows.append(
            row(
                edge_s - 0.35e-9,
                vinp=vinp,
                vinn=vinn,
                enable=0.9,
                load_step=load_step,
                **previous_outputs,
            )
        )
        rows.append(
            row(
                edge_s,
                vinp=vinp,
                vinn=vinn,
                clk=0.9,
                enable=0.9,
                load_step=load_step,
                **previous_outputs,
            )
        )

        stage1 = 0.45 if mutation == "stage1_wrong" else 0.55
        raw_target = 0.45 + 5.0 * (stage1 - 0.45)
        target = min(0.9, max(0.0, raw_target))
        move = target - vout
        if mutation != "no_slew_limit":
            move = min(0.08, max(-0.08, move))
        vout = min(0.9, max(0.0, vout + move))
        slew = abs(move)
        settle_count = settle_count + 1 if abs(target - vout) < 0.010 else 0
        active_outputs = {
            "vout": vout,
            "stage1_metric": stage1,
            "slew_metric": slew,
            "clamp_flag": 0.0 if mutation == "clamp_stuck_low" else 0.9,
            "settled": 0.9
            if mutation == "settled_stuck_high" or settle_count >= 2
            else 0.0,
        }
        rows.append(
            row(
                edge_s + 0.55e-9,
                vinp=vinp,
                vinn=vinn,
                clk=0.9,
                enable=0.9,
                load_step=load_step,
                **active_outputs,
            )
        )
        rows.append(
            row(
                edge_s + 1.25e-9,
                vinp=vinp,
                vinn=vinn,
                enable=0.9,
                load_step=load_step,
                **active_outputs,
            )
        )

    clear_outputs = active_outputs if mutation == "missing_clear" else {
        "vout": 0.45,
        "stage1_metric": 0.45,
        "slew_metric": 0.0,
        "clamp_flag": 0.0,
        "settled": 0.0,
    }
    assert clear_outputs is not None
    rows.append(
        row(
            rows[-1]["time"] + 1.0e-9,
            vinp=0.455,
            vinn=0.45,
            load_step=0.45,
            **clear_outputs,
        )
    )
    return rows


def test_two_stage_opamp_checker_is_event_relative_and_kills_exact_five() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_398_two_stage_opamp_slew_macromodel")
    assert checker is not None
    assert checker(_two_stage_opamp_trace(start_s=250e-9))[0]
    for mutation in (
        "stage1_wrong",
        "no_slew_limit",
        "settled_stuck_high",
        "missing_clear",
        "clamp_stuck_low",
    ):
        passed, detail = checker(_two_stage_opamp_trace(mutation=mutation))
        assert not passed, (mutation, detail)


def test_two_stage_opamp_checker_requires_every_contract_signal() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_398_two_stage_opamp_slew_macromodel")
    assert checker is not None
    rows = _two_stage_opamp_trace()
    for row in rows:
        row.pop("load_step")
    passed, detail = checker(rows)
    assert not passed
    assert detail == "missing_columns=load_step"


def test_two_stage_opamp_checker_requires_positive_settled_coverage() -> None:
    from checkers.v4.registry import load_checker

    checker = load_checker("v4_398_two_stage_opamp_slew_macromodel")
    assert checker is not None
    passed, detail = checker(_two_stage_opamp_trace(cycles=6))
    assert not passed, detail
    assert "settled_seen=False" in detail
