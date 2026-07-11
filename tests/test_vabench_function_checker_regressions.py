from __future__ import annotations

import math
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

import simulate_evas as sim  # noqa: E402


def _write_rows_csv(csv_path: Path, rows: list[dict[str, float]], fieldnames: list[str]) -> None:
    with csv_path.open("w", encoding="utf-8") as f:
        f.write(",".join(fieldnames) + "\n")
        for row in rows:
            f.write(",".join(str(row[name]) for name in fieldnames) + "\n")


def _evaluate_row_and_streaming(
    task_id: str,
    csv_path: Path,
) -> tuple[tuple[float, list[str]], tuple[float, list[str]]]:
    try:
        os.environ["VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS"] = "1"
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)
        row_result = sim.evaluate_behavior(task_id, csv_path)

        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ["VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS"] = "1"
        stream_result = sim.evaluate_behavior(task_id, csv_path)
    finally:
        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)
    return row_result, stream_result


PROMOTED_DUTS = {
    "vbr1_l1_burst_clock_source",
    "vbr1_l1_clocked_adc_quantizer",
    "vbr1_l1_clocked_sample_and_hold",
    "vbr1_l1_sample_and_hold_with_droop_leakage",
    "vbr1_l1_acquisition_limited_sample_and_hold",
    "vbr1_l1_aperture_delay_track_and_hold",
    "vbr1_l1_digital_phase_accumulator_with_modulo_wrap",
    "vbr1_l1_dither_or_noise_like_deterministic_source",
    "vbr1_l1_dwa_dem_encoder",
    "vbr1_l1_first_order_lowpass",
    "vbr1_l1_higher_order_filter",
    "vbr1_l1_hysteresis_comparator",
    "vbr1_l1_propagation_delay_comparator",
    "vbr1_l1_programmable_gain_amplifier",
    "vbr1_l1_ramp_or_step_source",
    "vbr1_l1_resettable_integrator",
    "vbr1_l1_slew_rate_limiter",
    "vbr1_l1_soft_hysteretic_limiter",
    "vbr1_l1_threshold_comparator",
    "vbr1_l1_unit_element_thermometer_dac",
    "vbr1_l1_precision_rectifier_envelope_detector",
    "vbr1_l1_window_comparator_detector",
}


def test_promoted_duts_have_release_behavior_aliases() -> None:
    for entry_id in PROMOTED_DUTS:
        assert sim.has_behavior_check(f"{entry_id}_dut"), entry_id


def test_hierarchy_l0_checkers_follow_visible_input_values() -> None:
    base_columns = {
        "clk": 0.0,
        "mode": 0.0,
        "rst": 0.0,
    }
    rows_431 = [
        {"time": 0.0, "vin": 0.40, "out": 0.30, "metric": 0.30, **base_columns},
        {"time": 100e-9, "vin": 0.40, "out": 0.30, "metric": 0.30, **base_columns},
        {"time": 220e-9, "vin": 1.40, "out": 0.90, "metric": 1.05, **base_columns},
        {"time": 260e-9, "vin": 1.40, "out": 0.90, "metric": 1.05, **base_columns},
    ]
    rows_432 = [
        {"time": 0.0, "vin": 0.50, "out": 0.30, "metric": 0.60, **base_columns},
        {"time": 80e-9, "vin": 0.50, "out": 0.30, "metric": 0.60, **base_columns},
        {"time": 220e-9, "vin": 1.00, "out": 0.60, "metric": 1.20, **base_columns},
        {"time": 260e-9, "vin": 1.00, "out": 0.60, "metric": 1.20, **base_columns},
    ]

    assert sim.check_v3_431_hierarchy_support_artifact_staging(rows_431)[0]
    assert sim.check_v3_432_hierarchy_nested_parameter_chain(rows_432)[0]

    rows_431_bad = [dict(row) for row in rows_431]
    rows_431_bad[1]["out"] = 0.7125
    assert not sim.check_v3_431_hierarchy_support_artifact_staging(rows_431_bad)[0]


def _sar_calibration_rows_with_dense_transition_samples() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = [
        {"time": 0.0, "clk": 0.0, "rst": 0.9, "vin": 0.45, "out": 0.45, "metric": 0.0},
        {"time": 1.0e-9, "clk": 0.0, "rst": 0.9, "vin": 0.45, "out": 0.45, "metric": 0.0},
        {"time": 2.5e-9, "clk": 0.0, "rst": 0.9, "vin": 0.45, "out": 0.45, "metric": 0.0},
        {"time": 3.5e-9, "clk": 0.0, "rst": 0.0, "vin": 0.455, "out": 0.45, "metric": 0.0},
    ]
    previous = 0.45
    for time_ns, target, vin in [
        (4.0, 0.63, 0.460),
        (6.0, 0.72, 0.465),
        (8.0, 0.765, 0.470),
        (10.0, 0.7875, 0.456),
    ]:
        edge_time = time_ns * 1e-9
        rows.append(
            {"time": edge_time - 10e-12, "clk": 0.0, "rst": 0.0, "vin": vin, "out": previous, "metric": 0.0}
        )
        rows.append({"time": edge_time, "clk": 0.9, "rst": 0.0, "vin": vin, "out": previous, "metric": 0.0})
        for offset_s, frac in [(10e-12, 0.25), (20e-12, 0.50), (30e-12, 0.60), (80e-12, 1.0)]:
            rows.append(
                {
                    "time": edge_time + offset_s,
                    "clk": 0.9,
                    "rst": 0.0,
                    "vin": vin,
                    "out": previous + (target - previous) * frac,
                    "metric": 0.0,
                }
            )
        rows.append({"time": edge_time + 120e-12, "clk": 0.0, "rst": 0.0, "vin": vin, "out": target, "metric": 0.0})
        rows.append({"time": edge_time + 300e-12, "clk": 0.0, "rst": 0.0, "vin": vin, "out": target, "metric": 0.0})
        previous = target
    rows.extend(
        {
            "time": time_ns * 1e-9,
            "clk": 0.0,
            "rst": 0.0,
            "vin": 0.456,
            "out": previous,
            "metric": 0.9,
        }
        for time_ns in (20.0, 22.0, 24.0, 26.0)
    )
    return sorted(rows, key=lambda row: row["time"])


def test_sar_calibration_checker_uses_physical_settle_delay() -> None:
    rows = _sar_calibration_rows_with_dense_transition_samples()

    settled = [value for _edge, value in sim.edge_settled_values(rows, "out")]
    early = [value for _edge, value in sim.edge_settled_values(rows, "out", settle_delay_s=0.03e-9)]
    ok, note = sim.check_release_sar_calibration_fsm(rows)

    assert settled == [0.63, 0.72, 0.765, 0.7875]
    assert early != settled
    assert ok, note


def _hysteresis_rows_with_transition_microstep(*, weak_high: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for time_ns in range(83):
        if time_ns < 25:
            vinp = 0.54
        elif time_ns <= 30:
            vinp = 0.54 + (time_ns - 25) * (0.016 / 5.0)
        elif time_ns < 60:
            vinp = 0.556
        elif time_ns <= 70:
            vinp = 0.556 - (time_ns - 60) * (0.012 / 10.0)
        else:
            vinp = 0.544
        high = 30 <= time_ns < 70
        high_out = 0.7 if weak_high else 0.9
        low_out = 0.3 if weak_high else 0.1
        rows.append(
            {
                "time": time_ns * 1e-9,
                "vinp": vinp,
                "vinn": 0.55,
                "vdd": 0.9,
                "vss": 0.1,
                "out_p": high_out if high else 0.1,
                "out_n": low_out if high else 0.9,
            }
        )
    rows.append(
        {
            "time": 69.201e-9,
            "vinp": 0.545,
            "vinn": 0.55,
            "vdd": 0.9,
            "vss": 0.1,
            "out_p": 0.347,
            "out_n": 0.653,
        }
    )
    return sorted(rows, key=lambda row: row["time"])


def test_hysteresis_checker_ignores_only_post_cross_transition_microsteps() -> None:
    ok, note = sim.check_cmp_hysteresis(_hysteresis_rows_with_transition_microstep())
    weak_ok, weak_note = sim.check_cmp_hysteresis(
        _hysteresis_rows_with_transition_microstep(weak_high=True)
    )

    assert ok, note
    assert "guarded_transition_samples=" in note
    assert not weak_ok
    assert "rail_or_complement_error" in weak_note


def _cmp_delay_rows(*, mode: str = "good") -> list[dict[str, float]]:
    phases = [
        (0.0e-9, 4.0e-9, 10e-3),
        (4.0e-9, 8.0e-9, 1e-3),
        (8.0e-9, 12.0e-9, 0.1e-3),
        (12.0e-9, 16.0e-9, 0.01e-3),
    ]
    delays_ns = [0.055, 0.070, 0.085, 0.100]
    if mode == "flat_delay":
        delays_ns = [0.055, 0.055, 0.055, 0.055]

    rows: list[dict[str, float]] = []
    step = 10e-12
    for idx in range(int(16e-9 / step) + 1):
        time = idx * step
        phase_idx = min(int(time // 4.0e-9), 3)
        start_t, _end_t, diff = phases[phase_idx]
        search_start = start_t + 0.1e-9
        delay = delays_ns[phase_idx] * 1e-9
        pulse_start = search_start + delay
        pulse_end = pulse_start + 0.25e-9
        out_high = pulse_start <= time < pulse_end
        if mode == "stuck_high":
            out_high = True
        rows.append(
            {
                "time": time,
                "clk": 0.9 if search_start <= time < search_start + 0.45e-9 else 0.0,
                "vinp": 0.45 + diff / 2,
                "vinn": 0.45 - diff / 2,
                "out_p": 0.9 if out_high else 0.0,
                "out_n": 0.0 if out_high else 0.9,
                "delay_ps": delays_ns[phase_idx] * 1000 if time >= pulse_start else 0.0,
            }
        )
    return rows


def test_cmp_delay_checker_requires_real_delay_growth() -> None:
    assert sim.check_cmp_delay(_cmp_delay_rows())[0]
    assert not sim.check_cmp_delay(_cmp_delay_rows(mode="flat_delay"))[0]
    assert not sim.check_cmp_delay(_cmp_delay_rows(mode="stuck_high"))[0]


def test_cmp_delay_checker_accepts_sparse_spectre_like_samples() -> None:
    dense_rows = _cmp_delay_rows()
    keep_times = {
        0.0,
        16.0e-9,
        *[start + offset for start in (0.0e-9, 4.0e-9, 8.0e-9, 12.0e-9) for offset in (0.0, 0.08e-9, 0.10e-9, 0.18e-9, 0.36e-9, 3.90e-9)],
    }
    sparse_rows = [
        row
        for row in dense_rows
        if any(math.isclose(row["time"], keep, rel_tol=0.0, abs_tol=0.5e-12) for keep in keep_times)
    ]

    assert sim.check_cmp_delay(sparse_rows)[0]


def test_cmp_delay_streaming_checker_matches_row_based(tmp_path: Path) -> None:
    rows = _cmp_delay_rows()
    csv_path = tmp_path / "tran.csv"
    fieldnames = ["time", "clk", "vinp", "vinn", "out_p", "out_n", "delay_ps"]
    with csv_path.open("w", encoding="utf-8") as f:
        f.write(",".join(fieldnames) + "\n")
        for row in rows:
            f.write(",".join(str(row[name]) for name in fieldnames) + "\n")

    try:
        os.environ["VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS"] = "1"
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)
        row_score, row_notes = sim.evaluate_behavior("vbr1_l1_propagation_delay_comparator_dut", csv_path)

        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ["VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS"] = "1"
        stream_score, stream_notes = sim.evaluate_behavior("vbr1_l1_propagation_delay_comparator_dut", csv_path)
        tb_score, tb_notes = sim.evaluate_behavior("vbr1_l1_propagation_delay_comparator_tb", csv_path)
    finally:
        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)

    assert stream_score == row_score
    assert stream_notes == [f"streaming_checker:{row_notes[0]}"]
    assert tb_score == row_score
    assert tb_notes == [f"streaming_checker:{row_notes[0]}"]


def _first_order_lowpass_rows(*, mode: str = "good") -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    tau = 18.0e-9
    for idx in range(0, 161):
        time = idx * 1.0e-9
        vin = 0.8 if time >= 21.0e-9 else 0.0
        if mode == "no_input_step":
            vin = 0.0
        if mode == "passthrough":
            vout = vin
        elif time < 21.0e-9:
            vout = 0.0
        else:
            vout = 0.8 * (1.0 - math.exp(-(time - 21.0e-9) / tau))
        rows.append({"time": time, "vin": vin, "vout": vout})
    return rows


def test_first_order_lowpass_checker_requires_input_step_and_lag() -> None:
    assert sim.check_vbm1_first_order_lowpass(_first_order_lowpass_rows())[0]
    assert not sim.check_vbm1_first_order_lowpass(_first_order_lowpass_rows(mode="no_input_step"))[0]
    assert not sim.check_vbm1_first_order_lowpass(_first_order_lowpass_rows(mode="passthrough"))[0]


def _resettable_integrator_rows(*, mode: str = "good") -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for idx in range(0, 321):
        time = idx * 1.0e-9
        t_ns = float(idx)
        rst = 0.9 if t_ns <= 25.0 or 221.0 <= t_ns <= 250.0 else 0.0
        vin = 0.002
        if mode == "no_reset_stimulus":
            rst = 0.0
        if rst > 0.45:
            vout = 0.0 if mode != "stale_reset" else 0.34
        elif t_ns < 221.0:
            vout = max(0.0, min(0.85, (t_ns - 26.0) * 0.002))
        else:
            vout = max(0.0, min(0.85, (t_ns - 251.0) * 0.002))
        rows.append({"time": time, "vin": vin, "rst": rst, "vout": vout})
    return rows


def test_resettable_integrator_checker_requires_reset_stimulus_and_restart() -> None:
    assert sim.check_vbm1_resettable_integrator(_resettable_integrator_rows())[0]
    assert not sim.check_vbm1_resettable_integrator(_resettable_integrator_rows(mode="no_reset_stimulus"))[0]
    assert not sim.check_vbm1_resettable_integrator(_resettable_integrator_rows(mode="stale_reset"))[0]


def _slew_rate_limiter_rows(*, mode: str = "good") -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for idx in range(0, 171):
        time = idx * 1.0e-9
        t_ns = float(idx)
        if t_ns < 21.0:
            vin = 0.0
            vout = 0.0
        elif t_ns < 96.0:
            vin = 0.8
            vout = min(0.8, (t_ns - 21.0) * 0.015)
        else:
            vin = 0.1
            vout = max(0.1, 0.8 - (t_ns - 96.0) * 0.015)
        if mode == "no_input_sequence":
            vin = 0.0
        if mode == "passthrough":
            vout = vin
        rows.append({"time": time, "vin": vin, "vout": vout})
    return rows


def test_slew_rate_limiter_checker_requires_input_sequence_and_limited_edges() -> None:
    assert sim.check_vbm1_slew_rate_limiter(_slew_rate_limiter_rows())[0]
    assert not sim.check_vbm1_slew_rate_limiter(_slew_rate_limiter_rows(mode="no_input_sequence"))[0]
    assert not sim.check_vbm1_slew_rate_limiter(_slew_rate_limiter_rows(mode="passthrough"))[0]


def test_noise_source_checker_rejects_flat_passthrough() -> None:
    ok_rows = [
        {"time": idx, "vin_i": 1.0, "vout_o": 1.0 + delta}
        for idx, delta in enumerate([0.08, -0.04, 0.06, -0.07, 0.03, -0.09])
    ]
    bad_rows = [{"time": idx, "vin_i": 1.0, "vout_o": 1.0} for idx in range(6)]

    assert sim.check_noise_gen(ok_rows)[0]
    assert not sim.check_noise_gen(bad_rows)[0]


def _prbs7_rows(*, tap: tuple[int, int] = (6, 5)) -> list[dict[str, float]]:
    state = 127
    rows: list[dict[str, float]] = []
    for step in range(24):
        row = {
            "time": step * 1e-9 + 3e-9,
            "clk": 0.9,
            "rst_n": 0.9,
            "en": 0.9,
            "serial_out": 0.9 if ((state >> 6) & 1) else 0.0,
        }
        for idx in range(7):
            row[f"state_{idx}"] = 0.9 if ((state >> idx) & 1) else 0.0
        rows.append(row)
        feedback = ((state >> tap[0]) & 1) ^ ((state >> tap[1]) & 1)
        state = ((state & 0x3F) << 1) | feedback
    return rows


def test_prbs7_checker_rejects_wrong_feedback_tap() -> None:
    assert sim.check_prbs7(_prbs7_rows())[0]
    assert not sim.check_prbs7(_prbs7_rows(tap=(6, 4)))[0]


def _threshold_comparator_rows(*, inverted: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for idx in range(60):
        time = idx * 0.5e-9
        vinp = 0.7 if idx >= 30 else 0.2
        vinn = 0.2 if idx >= 30 else 0.7
        out_high = vinp > vinn
        if inverted:
            out_high = not out_high
        rows.append({"time": time, "vinp": vinp, "vinn": vinn, "out_p": 0.9 if out_high else 0.0})
    return rows


def test_threshold_comparator_checker_rejects_inverted_polarity() -> None:
    assert sim.check_comparator(_threshold_comparator_rows())[0]
    assert not sim.check_comparator(_threshold_comparator_rows(inverted=True))[0]


def test_release_threshold_comparator_accepts_sparse_spectre_samples() -> None:
    rows = [
        {"time": 0.0e-9, "vinp": 0.2, "vinn": 0.45, "out_p": 0.0},
        {"time": 5.0e-9, "vinp": 0.2, "vinn": 0.45, "out_p": 0.0},
        {"time": 9.93e-9, "vinp": 0.2, "vinn": 0.45, "out_p": 0.0},
        {"time": 10.0447e-9, "vinp": 0.4233, "vinn": 0.45, "out_p": 0.0},
        {"time": 10.0500e-9, "vinp": 0.4501, "vinn": 0.45, "out_p": 0.0},
        {"time": 10.0608e-9, "vinp": 0.5038, "vinn": 0.45, "out_p": 0.0966},
        {"time": 10.0822e-9, "vinp": 0.6111, "vinn": 0.45, "out_p": 0.2897},
        {"time": 10.0911e-9, "vinp": 0.6555, "vinn": 0.45, "out_p": 0.3697},
        {"time": 10.1000e-9, "vinp": 0.7000, "vinn": 0.45, "out_p": 0.4498},
        {"time": 10.1012e-9, "vinp": 0.7000, "vinn": 0.45, "out_p": 0.4603},
        {"time": 10.1033e-9, "vinp": 0.7000, "vinn": 0.45, "out_p": 0.4791},
        {"time": 10.1074e-9, "vinp": 0.7000, "vinn": 0.45, "out_p": 0.5168},
        {"time": 10.1158e-9, "vinp": 0.7000, "vinn": 0.45, "out_p": 0.5922},
        {"time": 10.1326e-9, "vinp": 0.7000, "vinn": 0.45, "out_p": 0.7429},
        {"time": 10.1500e-9, "vinp": 0.7000, "vinn": 0.45, "out_p": 0.9000},
        {"time": 10.6736e-9, "vinp": 0.7000, "vinn": 0.45, "out_p": 0.9000},
        {"time": 11.8321e-9, "vinp": 0.7000, "vinn": 0.45, "out_p": 0.9000},
        {"time": 20.0000e-9, "vinp": 0.7000, "vinn": 0.45, "out_p": 0.9000},
        {"time": 20.0500e-9, "vinp": 0.4499, "vinn": 0.45, "out_p": 0.9000},
        {"time": 20.1000e-9, "vinp": 0.2000, "vinn": 0.45, "out_p": 0.4502},
        {"time": 20.1500e-9, "vinp": 0.2000, "vinn": 0.45, "out_p": 0.0000},
        {"time": 20.6381e-9, "vinp": 0.2000, "vinn": 0.45, "out_p": 0.0000},
        {"time": 21.1555e-9, "vinp": 0.2000, "vinn": 0.45, "out_p": 0.0000},
        {"time": 21.7555e-9, "vinp": 0.2000, "vinn": 0.45, "out_p": 0.0000},
        {"time": 30.0e-9, "vinp": 0.2000, "vinn": 0.45, "out_p": 0.0000},
    ]

    ok, note = sim.check_release_threshold_comparator(rows)
    assert ok, note


def _window_comparator_rows(*, mode: str = "true_window") -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    schmitt_state = False
    previous_vin = 0.0
    for idx in range(91):
        time = idx * 1.0e-9
        vin = 0.9 * (idx / 45.0) if idx <= 45 else 0.9 * ((90 - idx) / 45.0)
        if mode == "true_window":
            high = 0.3 < vin < 0.6
        elif mode == "above_high_stuck":
            high = vin > 0.3
        elif mode == "old_hysteresis":
            if previous_vin < 0.6 <= vin:
                schmitt_state = True
            if previous_vin > 0.3 >= vin:
                schmitt_state = False
            high = schmitt_state
        else:
            raise ValueError(mode)
        rows.append({"time": time, "vin": vin, "out": 0.9 if high else 0.0})
        previous_vin = vin
    return rows


def test_true_window_comparator_checker_rejects_hysteresis_semantics() -> None:
    assert sim.check_true_window_comparator(_window_comparator_rows())[0]
    assert not sim.check_true_window_comparator(_window_comparator_rows(mode="old_hysteresis"))[0]
    assert not sim.check_true_window_comparator(_window_comparator_rows(mode="above_high_stuck"))[0]


def test_window_comparator_streaming_checker_matches_row_based(tmp_path: Path) -> None:
    task_ids = [
        "window_comparator_smoke",
        "vbr1_l1_window_comparator_detector",
        "vbr1_l1_window_comparator_detector_dut",
        "vbr1_l1_window_comparator_detector_tb",
        "vbr1_l1_window_comparator_detector_bugfix",
        "vbr1_l1_window_comparator_detector_e2e",
    ]
    rows = _window_comparator_rows()
    csv_path = tmp_path / "window.csv"
    _write_rows_csv(csv_path, rows, ["time", "vin", "out"])

    for task_id in task_ids:
        row_result, stream_result = _evaluate_row_and_streaming(task_id, csv_path)
        assert stream_result[0] == row_result[0], task_id
        assert stream_result[1] == [f"streaming_checker:{row_result[1][0]}"], task_id


def _comparator_measurement_flow_rows(*, mode: str = "good") -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for idx in range(101):
        time = idx * 1.0e-9
        inp = 0.490 + 0.030 * min(time / 80e-9, 1.0)
        inn = 0.500
        tripped = inp >= 0.505
        outp = 0.9 if tripped else 0.0
        valid = 0.9 if tripped else 0.0
        trip_v = 0.505 if tripped else 0.0
        offset_est = 0.005 if tripped else 0.0
        if mode == "early_output":
            outp = 0.9 if inp >= 0.502 else 0.0
        if mode == "early_valid":
            valid = 0.9 if inp >= 0.502 else 0.0
            if valid > 0.45:
                trip_v = 0.505
                offset_est = 0.005
        if mode == "wrong_trip" and tripped:
            trip_v = 0.510
            offset_est = 0.010
        row = {
            "time": time,
            "inp": inp,
            "inn": inn,
            "outp": outp,
            "trip_v": trip_v,
            "offset_est": offset_est,
            "valid": valid,
        }
        if mode == "missing_metric":
            row.pop("trip_v")
        if mode == "shallow_output_only":
            row = {"time": time, "inp": inp, "inn": inn, "outp": outp}
        rows.append(row)
    return rows


def test_comparator_measurement_flow_checker_requires_latched_metrics() -> None:
    assert sim.check_comparator_measurement_flow(_comparator_measurement_flow_rows())[0]
    assert not sim.check_comparator_measurement_flow(_comparator_measurement_flow_rows(mode="missing_metric"))[0]
    assert not sim.check_comparator_measurement_flow(_comparator_measurement_flow_rows(mode="wrong_trip"))[0]
    assert not sim.check_comparator_measurement_flow(_comparator_measurement_flow_rows(mode="shallow_output_only"))[0]
    assert not sim.check_comparator_measurement_flow(_comparator_measurement_flow_rows(mode="early_output"))[0]
    assert not sim.check_comparator_measurement_flow(_comparator_measurement_flow_rows(mode="early_valid"))[0]


def test_comparator_measurement_flow_allows_same_transition_valid_and_outp() -> None:
    rows: list[dict[str, float]] = []
    for idx in range(101):
        time = idx * 1.0e-9
        inp = 0.490 + 0.030 * min(time / 100e-9, 1.0)
        tripped = time >= 50.011e-9
        rows.append(
            {
                "time": time,
                "inp": inp,
                "inn": 0.500,
                "outp": 0.9 if tripped else 0.0,
                "valid": 0.9 if tripped else 0.0,
                "trip_v": 0.505 if tripped else 0.0,
                "offset_est": 0.005 if tripped else 0.0,
            }
        )
    rows.extend(
        [
            {
                "time": 50.007e-9,
                "inp": 0.5050021,
                "inn": 0.500,
                "outp": 0.450,
                "valid": 0.540,
                "trip_v": 0.303,
                "offset_est": 0.003,
            },
            {
                "time": 50.009e-9,
                "inp": 0.5050027,
                "inn": 0.500,
                "outp": 0.585,
                "valid": 0.675,
                "trip_v": 0.379,
                "offset_est": 0.0038,
            },
        ]
    )
    rows.sort(key=lambda row: row["time"])

    ok, note = sim.check_comparator_measurement_flow(rows)
    assert ok, note


def test_spectre_aligned_preflight_rejects_missing_disciplines(tmp_path: Path) -> None:
    (tmp_path / "bad.va").write_text(
        "module bad(out);\n  output out;\n  electrical out;\nendmodule\n",
        encoding="utf-8",
    )
    (tmp_path / "ok.va").write_text(
        '`include "disciplines.vams"\nmodule ok(out);\n  output out;\n  electrical out;\nendmodule\n',
        encoding="utf-8",
    )

    assert sim.spectre_aligned_veriloga_preflight(tmp_path) == ["bad.va:missing_disciplines_vams"]


def test_spectre_aligned_preflight_rejects_unbounded_event_loop(tmp_path: Path) -> None:
    (tmp_path / "loop.va").write_text(
        '`include "disciplines.vams"\n'
        "module loop(clk, out);\n"
        "  input clk; output out; electrical clk, out;\n"
        "  real state;\n"
        "  analog begin\n"
        "    while (1) begin\n"
        "      @(cross(V(clk)-0.5,+1)); state = 1;\n"
        "    end\n"
        "    V(out) <+ state;\n"
        "  end\n"
        "endmodule\n",
        encoding="utf-8",
    )

    assert sim.spectre_aligned_veriloga_preflight(tmp_path) == [
        "loop.va:unsupported_unbounded_event_loop"
    ]


def _xor_pd_rows(*, and_gate: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for idx in range(240):
        phase = idx % 40
        ref = phase < 20
        div = 10 <= phase < 30
        out = (ref and div) if and_gate else (ref ^ div)
        rows.append(
            {
                "time": idx * 0.5e-9,
                "ref": 0.9 if ref else 0.0,
                "div": 0.9 if div else 0.0,
                "pd_out": 0.9 if out else 0.0,
            }
        )
    return rows


def test_xor_pd_checker_rejects_non_xor_logic() -> None:
    assert sim.check_xor_pd(_xor_pd_rows())[0]
    assert not sim.check_xor_pd(_xor_pd_rows(and_gate=True))[0]


def _bbpd_rows(*, swapped_outputs: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    data_high = False
    for idx in range(16):
        edge_t = idx * 1.0e-9 + 0.2e-9
        if idx < 6:
            expected_kind: str | None = "up"
            clk = 0.9
            retimed_data = 0.0
        elif idx < 12:
            expected_kind = "down"
            clk = 0.0
            retimed_data = 0.9
        else:
            expected_kind = None
            clk = 0.9
            retimed_data = 0.9
        rows.append(
            {
                "time": edge_t - 0.02e-9,
                "data": 0.9 if data_high else 0.0,
                "clk": clk,
                "retimed_data": retimed_data,
                "up": 0.0,
                "down": 0.0,
            }
        )
        data_high = not data_high
        pulse = {"up": 0.0, "down": 0.0}
        if expected_kind is not None:
            if swapped_outputs:
                observed_signal = "down" if expected_kind == "up" else "up"
            else:
                observed_signal = expected_kind
            pulse[observed_signal] = 0.9
        rows.append(
            {
                "time": edge_t,
                "data": 0.9 if data_high else 0.0,
                "clk": clk,
                "retimed_data": retimed_data,
                "up": 0.0,
                "down": 0.0,
            }
        )
        rows.append(
            {
                "time": edge_t + 0.02e-9,
                "data": 0.9 if data_high else 0.0,
                "clk": clk,
                "retimed_data": retimed_data,
                **pulse,
            }
        )
        rows.append(
            {
                "time": edge_t + 0.12e-9,
                "data": 0.9 if data_high else 0.0,
                "clk": clk,
                "retimed_data": retimed_data,
                "up": 0.0,
                "down": 0.0,
            }
        )
    return rows


def test_bbpd_checker_rejects_swapped_up_down_direction() -> None:
    assert sim.check_bbpd(_bbpd_rows())[0]
    assert not sim.check_bbpd(_bbpd_rows(swapped_outputs=True))[0]


def test_bbpd_streaming_checker_matches_row_based(tmp_path: Path) -> None:
    rows = _bbpd_rows()
    csv_path = tmp_path / "tran.csv"
    fieldnames = ["time", "data", "clk", "retimed_data", "up", "down"]
    with csv_path.open("w", encoding="utf-8") as f:
        f.write(",".join(fieldnames) + "\n")
        for row in rows:
            f.write(",".join(str(row[name]) for name in fieldnames) + "\n")

    try:
        os.environ["VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS"] = "1"
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)
        row_score, row_notes = sim.evaluate_behavior("bbpd", csv_path)

        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ["VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS"] = "1"
        stream_score, stream_notes = sim.evaluate_behavior("bbpd", csv_path)
    finally:
        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)

    assert stream_score == row_score
    assert stream_notes == [f"streaming_checker:{row_notes[0]}"]


def _dwa_rows(*, corrupt_cell_span: bool = False) -> list[dict[str, float]]:
    codes = [3, 7, 2, 5, 1, 8, 4, 6, 6]
    rows: list[dict[str, float]] = []
    ptr = 0
    previous_code: int | None = None
    zero_bus = {f"code_{bit}": 0.0 for bit in range(4)}
    zero_bus.update({f"ptr_{bit}": 0.0 for bit in range(16)})
    zero_bus.update({f"cell_en_{bit}": 0.0 for bit in range(16)})
    for idx, code in enumerate(codes):
        edge_t = idx * 10e-9 + 1e-9
        rows.append({"time": edge_t - 0.1e-9, "clk_i": 0.0, "rst_ni": 0.9, **zero_bus})
        rows.append({"time": edge_t, "clk_i": 0.9, "rst_ni": 0.9, **zero_bus})
        effective_code = code if previous_code is None else previous_code
        ptr = (ptr + effective_code) % 16
        active_cells = {(ptr - offset) % 16 for offset in range(effective_code + 1)}
        if corrupt_cell_span and idx == len(codes) - 1:
            active_cells = set()
        sample = {"time": edge_t + 1.0e-9, "clk_i": 0.9, "rst_ni": 0.9}
        for bit in range(4):
            sample[f"code_{bit}"] = 0.9 if ((code >> bit) & 1) else 0.0
        for bit in range(16):
            sample[f"ptr_{bit}"] = 0.9 if bit == ptr else 0.0
            sample[f"cell_en_{bit}"] = 0.9 if bit in active_cells else 0.0
        rows.append(sample)
        previous_code = code
    return rows


def test_dwa_release_checker_rejects_wrong_cell_span() -> None:
    assert sim.check_dwa_dem_encoder_release(_dwa_rows())[0]
    assert not sim.check_dwa_dem_encoder_release(_dwa_rows(corrupt_cell_span=True))[0]


def _element_shuffler_rows(sequence: list[int], *, reset_low_probe: bool = True) -> list[dict[str, float]]:
    sample_times_ns = [20.0, 40.0, 60.0, 80.0, 100.0, 120.0, 160.0, 180.0, 200.0, 220.0]
    active_by_time = dict(zip(sample_times_ns, sequence))
    rows: list[dict[str, float]] = []
    for time_ns in sorted(set(sample_times_ns[: len(sequence)]) | {138.0}):
        active = active_by_time.get(time_ns)
        row = {
            "time": time_ns * 1e-9,
            "clk": 0.0,
            "rst_n": 0.0 if reset_low_probe and time_ns == 138.0 else 0.9,
        }
        for idx in range(4):
            row[f"out{idx}"] = 0.9 if idx == active else 0.0
        rows.append(row)
    return rows


def test_release_element_shuffler_checker_keeps_public_window() -> None:
    assert sim.check_release_element_shuffler(_element_shuffler_rows([2, 0, 3, 1, 2, 0]))[0]
    assert not sim.check_release_element_shuffler(_element_shuffler_rows([1, 2, 3, 0, 1, 2]))[0]


def test_v3_element_shuffler_checker_rejects_plain_rotation() -> None:
    assert sim.check_v3_element_shuffler(_element_shuffler_rows([2, 0, 3, 1, 2, 0, 2, 0, 3, 1]))[0]
    assert not sim.check_v3_element_shuffler(_element_shuffler_rows([1, 2, 3, 0, 1, 2, 3, 0, 1, 2]))[0]


def test_v3_element_shuffler_checker_rejects_missing_reset_restart() -> None:
    assert not sim.check_v3_element_shuffler(_element_shuffler_rows([2, 0, 3, 1, 2, 0, 1, 2, 3, 0]))[0]


def test_v3_element_shuffler_checker_rejects_missing_reset_probe() -> None:
    rows = _element_shuffler_rows([2, 0, 3, 1, 2, 0, 2, 0, 3, 1], reset_low_probe=False)
    assert not sim.check_v3_element_shuffler(rows)[0]


def _ramp_rows(*, flat_phase: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    period = 8.0
    pulse_w = 1.5
    step = 0.25
    for idx in range(int(34.0 / step) + 1):
        time = idx * step
        phase = 0.0 if flat_phase else time % period
        rows.append(
            {
                "time": time,
                "phase_out": 0.9 * phase / period,
                "guard_out": 0.9 if phase <= pulse_w else 0.0,
            }
        )
    return rows


def test_bound_step_period_guard_checker_rejects_flat_phase() -> None:
    assert sim.check_bound_step_period_guard(_ramp_rows())[0]
    assert not sim.check_bound_step_period_guard(_ramp_rows(flat_phase=True))[0]


def _release_loop_filter_rows(*, metric_stuck_low: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    state = 0.45
    step = 0.20
    integ = 0.0
    cycle = 0
    donev = 0.0
    previous_clk = 0.9

    def vin_at(time_s: float) -> float:
        t_ns = time_s * 1e9
        if t_ns < 8:
            return 0.45 + 0.02 * t_ns / 8
        if t_ns < 14:
            return 0.47 - 0.04 * (t_ns - 8) / 6
        if t_ns < 20:
            return 0.43 + 0.32 * (t_ns - 14) / 6
        if t_ns < 40:
            return 0.75 - 0.57 * (t_ns - 20) / 20
        if t_ns < 58:
            return 0.18 + 0.54 * (t_ns - 40) / 18
        if t_ns < 68:
            return 0.72 - 0.25 * (t_ns - 58) / 10
        if t_ns < 74:
            return 0.47 + 0.31 * (t_ns - 68) / 6
        return 0.78

    for idx in range(161):
        time_s = idx * 0.5e-9
        phase = (time_s * 1e9) % 2.0
        clk = 0.9 if phase < 1.0 else 0.0
        rst = 0.9 if time_s <= 2.0e-9 or 62.1e-9 <= time_s <= 70.0e-9 else 0.0
        vin = vin_at(time_s)
        if previous_clk <= 0.45 < clk:
            errv = vin - 0.45
            if rst > 0.45:
                state = 0.45
                step = 0.20
                integ = 0.0
                cycle = 0
                donev = 0.0
            elif abs(errv) > 0.05:
                state += step if errv > 0 else -step
                integ += errv * 0.04
                step *= 0.5
                cycle += 1
                donev = 0.9 if cycle >= 4 else 0.0
            state = min(max(state, 0.05), 0.85)
        previous_clk = clk
        rows.append(
            {
                "time": time_s,
                "clk": clk,
                "rst": rst,
                "vin": vin,
                "out": state + integ,
                "metric": 0.0 if metric_stuck_low else donev,
            }
        )
    return rows


def test_release_loop_filter_checker_requires_metric_and_pi_semantics() -> None:
    assert sim.check_release_loop_filter(_release_loop_filter_rows())[0]
    ok, note = sim.check_release_loop_filter(_release_loop_filter_rows(metric_stuck_low=True))
    assert not ok
    assert "metric_timing" in note


def _release_charge_pump_rows(*, swapped: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    ctrl = 0.45
    previous_clk = 0.0
    up_edges = {6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0}
    dn_edges = {32.0, 34.0, 36.0, 38.0, 40.0}

    for idx in range(161):
        time_s = idx * 0.5e-9
        t_ns = time_s * 1e9
        clk = 0.9 if (t_ns % 2.0) < 1.0 else 0.0
        rst = 0.9 if time_s <= 2.0e-9 or 62.1e-9 <= time_s <= 66.0e-9 else 0.0
        up = 0.9 if any(abs(t_ns - edge) <= 0.25 for edge in up_edges) else 0.0
        dn = 0.9 if any(abs(t_ns - edge) <= 0.25 for edge in dn_edges) else 0.0
        metric = 0.45
        if previous_clk <= 0.45 < clk:
            if rst > 0.45:
                ctrl = 0.45
                metric = 0.45
            elif up > 0.45 and dn <= 0.45:
                ctrl += -0.06 if swapped else 0.06
                metric = 0.75
            elif dn > 0.45 and up <= 0.45:
                ctrl += 0.06 if swapped else -0.06
                metric = 0.15
            ctrl = min(max(ctrl, 0.05), 0.85)
        previous_clk = clk
        rows.append(
            {
                "time": time_s,
                "clk": clk,
                "rst": rst,
                "up": up,
                "dn": dn,
                "vctrl": ctrl,
                "metric": metric,
            }
        )
    return rows


def test_release_charge_pump_checker_requires_up_dn_pulse_polarity() -> None:
    assert sim.check_release_charge_pump(_release_charge_pump_rows())[0]
    ok, note = sim.check_release_charge_pump(_release_charge_pump_rows(swapped=True))
    assert not ok
    assert "charge_pump_polarity" in note


def _cppll_tracking_rows(*, lock_low: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for idx in range(int(5.0e-6 / 5.0e-9) + 1):
        time_s = idx * 5.0e-9
        ref = 0.9 if idx % 4 < 2 else 0.0
        fb = 0.9 if idx % 4 < 2 else 0.0
        rows.append(
            {
                "time": time_s,
                "ref_clk": ref,
                "fb_clk": fb,
                "lock": 0.0 if lock_low else (0.9 if time_s >= 1.0e-6 else 0.0),
                "vctrl_mon": 0.45,
            }
        )
    return rows


def test_cppll_tracking_checker_requires_late_lock_assertion() -> None:
    assert sim.check_cppll_tracking(_cppll_tracking_rows())[0]
    ok, note = sim.check_cppll_tracking(_cppll_tracking_rows(lock_low=True))
    assert not ok
    assert "late_lock_frac" in note


def _simultaneous_event_rows(*, bad_levels: bool = False, shifted_ref: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    edges = [10e-9, 30e-9, 50e-9, 70e-9]
    levels = [0.18, 0.36, 0.54, 0.72]
    if bad_levels:
        levels = [0.18, 0.32, 0.46, 0.60]
    for edge, level in zip(edges, levels):
        ref_edge = edge + (1.0e-9 if shifted_ref else 0.0)
        rows.append({"time": ref_edge - 0.2e-9, "ref": 0.0, "out": level})
        rows.append({"time": ref_edge, "ref": 0.9, "out": level})
        rows.append({"time": ref_edge + 1.0e-9, "ref": 0.0, "out": level})
        for offset in (2e-9, 5e-9, 8e-9):
            rows.append({"time": edge + offset, "ref": 0.0, "out": level})
    return sorted(rows, key=lambda row: row["time"])


def test_simultaneous_event_order_checker_requires_timed_ref_edges_and_encoded_plateaus() -> None:
    assert sim.check_simultaneous_event_order(_simultaneous_event_rows())[0]
    assert not sim.check_simultaneous_event_order(_simultaneous_event_rows(bad_levels=True))[0]
    assert not sim.check_simultaneous_event_order(_simultaneous_event_rows(shifted_ref=True))[0]


def _conversion_event_controller_rows(*, missing_timeout_readout: bool = False, extra_cmp_done: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for idx in range(171):
        t = idx * 1.0e-9
        rst = 0.9 if t <= 5e-9 else 0.0
        start = 0.9 if (10e-9 <= t <= 12e-9 or 90e-9 <= t <= 92e-9) else 0.0
        cmp_done = 0.9 if 36e-9 <= t <= 39e-9 else 0.0
        if extra_cmp_done and 118e-9 <= t <= 121e-9:
            cmp_done = 0.9
        sample = 0.9 if (10e-9 <= t < 22e-9 or 90e-9 <= t < 102e-9) else 0.0
        compare = 0.9 if (22e-9 <= t < 36e-9 or 102e-9 <= t < 130e-9) else 0.0
        readout = 0.9 if (36e-9 <= t < 52e-9 or 130e-9 <= t < 146e-9) else 0.0
        if missing_timeout_readout and t >= 120e-9:
            readout = 0.0
        done = 0.9 if (52e-9 <= t < 60e-9 or 146e-9 <= t < 154e-9) else 0.0
        if rst > 0.45:
            sample = compare = readout = done = 0.0
        if sample > 0.45:
            state = 0.225
        elif compare > 0.45:
            state = 0.450
        elif readout > 0.45:
            state = 0.675
        elif done > 0.45:
            state = 0.900
        else:
            state = 0.0
        rows.append(
            {
                "time": t,
                "rst": rst,
                "start": start,
                "cmp_done": cmp_done,
                "sample_en": sample,
                "compare_en": compare,
                "readout_en": readout,
                "done": done,
                "state_mon": state,
            }
        )
    return rows


def test_conversion_event_controller_checker_requires_normal_and_timeout_transactions() -> None:
    assert sim.check_conversion_event_controller(_conversion_event_controller_rows())[0]
    assert not sim.check_conversion_event_controller(_conversion_event_controller_rows(missing_timeout_readout=True))[0]
    assert not sim.check_conversion_event_controller(_conversion_event_controller_rows(extra_cmp_done=True))[0]


def _serializer_frame_monitor_rows(*, bad_word_mon: bool = False, frame_error: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    bit_events = []
    for base_t, word in ((16e-9, 0xA5), (86e-9, 0x3C)):
        bits = [(word >> bit) & 1 for bit in range(7, -1, -1)]
        for offset, bit in enumerate(bits):
            bit_events.append((base_t + offset * 5e-9, bit, offset == 0, word, offset == 7))
    for idx in range(281):
        t = idx * 0.5e-9
        phase = (t - 1e-9) % 5e-9
        clk = 0.9 if t >= 1e-9 and phase < 2.5e-9 else 0.0
        load = 0.9 if (2e-9 <= t <= 12e-9 or 72e-9 <= t <= 82e-9) else 0.0
        sout = 0.0
        frame = 0.0
        word_ok = 0.0
        word_mon = 0.0
        for edge_t, bit, is_frame, word, is_last in bit_events:
            if edge_t <= t < edge_t + 5e-9:
                sout = 0.9 if bit else 0.0
                frame = 0.9 if is_frame else 0.0
            if is_last and edge_t <= t < edge_t + 5e-9:
                word_ok = 0.9
                word_mon = 0.9 * word / 255.0
        if t >= 121e-9:
            word_mon = 0.9 * 0x3C / 255.0
        elif t >= 51e-9:
            word_mon = 0.9 * 0xA5 / 255.0
        if bad_word_mon and t >= 51e-9:
            word_mon = 0.05
        rows.append(
            {
                "time": t,
                "clk": clk,
                "load": load,
                "frame": frame,
                "sout": sout,
                "word_ok": word_ok,
                "frame_error": 0.9 if frame_error and 100e-9 <= t <= 102e-9 else 0.0,
                "word_mon": word_mon,
                "din7": 0.9 if t < 70e-9 else 0.0,
                "din6": 0.0,
                "din5": 0.9,
                "din4": 0.0 if t < 70e-9 else 0.9,
                "din3": 0.0 if t < 70e-9 else 0.9,
                "din2": 0.9,
                "din1": 0.0,
                "din0": 0.9 if t < 70e-9 else 0.0,
            }
        )
    return rows


def test_serializer_frame_monitor_checker_requires_word_monitor_and_error_flag() -> None:
    assert sim.check_serializer_frame_monitor_flow(_serializer_frame_monitor_rows())[0]
    assert not sim.check_serializer_frame_monitor_flow(_serializer_frame_monitor_rows(bad_word_mon=True))[0]
    assert not sim.check_serializer_frame_monitor_flow(_serializer_frame_monitor_rows(frame_error=True))[0]


def _final_step_metric_rows(*, bad_levels: bool = False, missing_edge: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    edges = [10e-9, 30e-9, 50e-9, 70e-9]
    levels = [0.225, 0.45, 0.675, 0.9]
    if bad_levels:
        levels = [0.225, 0.35, 0.50, 0.62]
    if missing_edge:
        edges = edges[:-1]
        levels = levels[:-1]
    for edge, level in zip(edges, levels):
        rows.append({"time": edge - 0.2e-9, "ref": 0.0, "metric_out": level})
        rows.append({"time": edge, "ref": 0.9, "metric_out": level})
        rows.append({"time": edge + 1.0e-9, "ref": 0.0, "metric_out": level})
        for offset in (2e-9, 5e-9, 8e-9):
            rows.append({"time": edge + offset, "ref": 0.0, "metric_out": level})
    return sorted(rows, key=lambda row: row["time"])


def test_final_step_metric_checker_requires_exact_edge_count_and_normalized_plateaus() -> None:
    assert sim.check_final_step_file_metric(_final_step_metric_rows())[0]
    assert not sim.check_final_step_file_metric(_final_step_metric_rows(bad_levels=True))[0]
    assert not sim.check_final_step_file_metric(_final_step_metric_rows(missing_edge=True))[0]


def _gain_estimator_rows(*, bad_gain_out: bool = False, missing_valid: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for idx in range(240):
        time = idx * 1e-9
        phase = 2.0 * math.pi * idx / 40.0
        vin_diff = 0.03 * math.sin(phase)
        vout_diff = 0.18 * math.sin(phase)
        valid = 0.9 if time >= 60e-9 and not missing_valid else 0.0
        gain = 2.0 if bad_gain_out else 6.0
        rows.append(
            {
                "time": time,
                "vinp": 0.45 + 0.5 * vin_diff,
                "vinn": 0.45 - 0.5 * vin_diff,
                "voutp": 0.45 + 0.5 * vout_diff,
                "voutn": 0.45 - 0.5 * vout_diff,
                "gain_out": 0.9 * gain / 10.0,
                "valid": valid,
            }
        )
    return rows


def test_gain_estimator_checker_requires_late_valid_and_gain_output() -> None:
    assert sim.check_gain_estimator(_gain_estimator_rows())[0]
    assert not sim.check_gain_estimator(_gain_estimator_rows(bad_gain_out=True))[0]
    assert not sim.check_gain_estimator(_gain_estimator_rows(missing_valid=True))[0]


def test_gain_estimator_streaming_checker_matches_row_based(tmp_path: Path) -> None:
    rows = _gain_estimator_rows()
    csv_path = tmp_path / "tran.csv"
    fieldnames = ["time", "vinp", "vinn", "voutp", "voutn", "gain_out", "valid"]
    with csv_path.open("w", encoding="utf-8") as f:
        f.write(",".join(fieldnames) + "\n")
        for row in rows:
            f.write(",".join(str(row[name]) for name in fieldnames) + "\n")

    try:
        os.environ["VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS"] = "1"
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)
        row_score, row_notes = sim.evaluate_behavior("vbr1_l1_gain_estimator_tb", csv_path)

        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ["VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS"] = "1"
        stream_score, stream_notes = sim.evaluate_behavior("vbr1_l1_gain_estimator_tb", csv_path)
    finally:
        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)

    assert stream_score == row_score
    assert stream_notes == [f"streaming_checker:{row_notes[0]}"]


def test_cdac_cal_streaming_checker_matches_row_based(tmp_path: Path) -> None:
    rows = [
        {"time": idx * 1e-9, "voutp": 0.2 + 0.01 * idx, "voutn": 0.7 - 0.001 * idx}
        for idx in range(12)
    ]
    csv_path = tmp_path / "tran.csv"
    fieldnames = ["time", "voutp", "voutn"]
    with csv_path.open("w", encoding="utf-8") as f:
        f.write(",".join(fieldnames) + "\n")
        for row in rows:
            f.write(",".join(str(row[name]) for name in fieldnames) + "\n")

    try:
        os.environ["VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS"] = "1"
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)
        row_score, row_notes = sim.evaluate_behavior("cdac_cal", csv_path)

        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ["VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS"] = "1"
        stream_score, stream_notes = sim.evaluate_behavior("cdac_cal", csv_path)
    finally:
        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)

    assert stream_score == row_score
    assert stream_notes == [f"streaming_checker:{row_notes[0]}"]


def test_release_lfsr_streaming_checker_matches_row_based(tmp_path: Path) -> None:
    rows = [
        {"time": idx * 1e-9, "rstb": 0.0 if idx < 2 else 0.9, "dpn": 0.9 if (idx * 5) % 11 < 5 else 0.0}
        for idx in range(80)
    ]
    csv_path = tmp_path / "tran.csv"
    fieldnames = ["time", "rstb", "dpn"]
    with csv_path.open("w", encoding="utf-8") as f:
        f.write(",".join(fieldnames) + "\n")
        for row in rows:
            f.write(",".join(str(row[name]) for name in fieldnames) + "\n")

    try:
        os.environ["VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS"] = "1"
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)
        row_score, row_notes = sim.evaluate_behavior("vbr1_l1_lfsr_prbs_generator_tb", csv_path)

        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ["VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS"] = "1"
        stream_score, stream_notes = sim.evaluate_behavior("vbr1_l1_lfsr_prbs_generator_tb", csv_path)
    finally:
        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)

    assert stream_score == row_score
    assert stream_notes == [f"streaming_checker:{row_notes[0]}"]


def test_prbs7_streaming_checker_matches_row_based(tmp_path: Path) -> None:
    rows = _prbs7_rows()
    csv_path = tmp_path / "tran.csv"
    fieldnames = ["time", "clk", "rst_n", "en", "serial_out", *(f"state_{idx}" for idx in range(7))]
    with csv_path.open("w", encoding="utf-8") as f:
        f.write(",".join(fieldnames) + "\n")
        for row in rows:
            f.write(",".join(str(row[name]) for name in fieldnames) + "\n")

    try:
        os.environ["VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS"] = "1"
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)
        row_score, row_notes = sim.evaluate_behavior("prbs7", csv_path)

        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ["VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS"] = "1"
        stream_score, stream_notes = sim.evaluate_behavior("prbs7", csv_path)
    finally:
        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)

    assert stream_score == row_score
    assert stream_notes == [f"streaming_checker:{row_notes[0]}"]


def test_edge_interval_streaming_checker_matches_row_based(tmp_path: Path) -> None:
    rows = []
    for idx in range(120):
        time = idx * 1e-9
        seen = 0.9 if time >= 50e-9 else 0.0
        delay = 0.72 if time >= 51e-9 else 0.0
        rows.append({"time": time, "delay_out": delay, "seen_out": seen})

    csv_path = tmp_path / "tran.csv"
    fieldnames = ["time", "delay_out", "seen_out"]
    with csv_path.open("w", encoding="utf-8") as f:
        f.write(",".join(fieldnames) + "\n")
        for row in rows:
            f.write(",".join(str(row[name]) for name in fieldnames) + "\n")

    try:
        os.environ["VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS"] = "1"
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)
        row_score, row_notes = sim.evaluate_behavior("vbr1_l1_edge_interval_timer_tb", csv_path)

        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ["VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS"] = "1"
        stream_score, stream_notes = sim.evaluate_behavior("vbr1_l1_edge_interval_timer_tb", csv_path)
    finally:
        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)

    assert stream_score == row_score
    assert stream_notes == [f"streaming_checker:{row_notes[0]}"]


def test_final_step_metric_side_output_requires_candidate_file(tmp_path: Path) -> None:
    csv_path = tmp_path / "out" / "tran.csv"
    csv_path.parent.mkdir()
    csv_path.write_text("time,ref,metric_out\n", encoding="utf-8")

    missing_ok, missing_note = sim.validate_behavior_side_outputs(
        "final_step_file_metric_smoke",
        tmp_path,
        csv_path,
    )
    assert not missing_ok
    assert missing_note == "candidate_file_missing"

    (tmp_path / "candidate.out").write_text("count=3 metric=0.750", encoding="utf-8")
    bad_ok, bad_note = sim.validate_behavior_side_outputs(
        "final_step_file_metric_smoke",
        tmp_path,
        csv_path,
    )
    assert not bad_ok
    assert "candidate_file_count=3" in bad_note

    (tmp_path / "candidate.out").write_text("count=4 metric=1.000", encoding="utf-8")
    ok, note = sim.validate_behavior_side_outputs(
        "final_step_file_metric_smoke",
        tmp_path,
        csv_path,
    )
    assert ok
    assert "candidate_file_count=4" in note


def test_final_step_average_metric_side_output_requires_average_record(tmp_path: Path) -> None:
    csv_path = tmp_path / "out" / "tran.csv"
    csv_path.parent.mkdir()
    csv_path.write_text("time,vin,clk,mode,rst,out,metric\n", encoding="utf-8")

    missing_ok, missing_note = sim.validate_behavior_side_outputs(
        "v3_317_final_step_average_metric_file",
        tmp_path,
        csv_path,
    )
    assert not missing_ok
    assert missing_note == "candidate_file_missing"

    (tmp_path / "candidate.out").write_text("count=4 avg=0.600 metric=0.667", encoding="utf-8")
    bad_ok, bad_note = sim.validate_behavior_side_outputs(
        "v3_317_final_step_average_metric_file",
        tmp_path,
        csv_path,
    )
    assert not bad_ok
    assert "avg=0.600" in bad_note

    (tmp_path / "candidate.out").write_text("count=4 avg=0.450 metric=0.500", encoding="utf-8")
    ok, note = sim.validate_behavior_side_outputs(
        "v3_317_final_step_average_metric_file",
        tmp_path,
        csv_path,
    )
    assert ok
    assert "candidate_file_count=4" in note


def test_final_step_max_metric_side_output_requires_max_record(tmp_path: Path) -> None:
    csv_path = tmp_path / "out" / "tran.csv"
    csv_path.parent.mkdir()
    csv_path.write_text("time,vin,clk,mode,rst,out,metric\n", encoding="utf-8")

    missing_ok, missing_note = sim.validate_behavior_side_outputs(
        "v3_318_final_step_max_observer_file",
        tmp_path,
        csv_path,
    )
    assert not missing_ok
    assert missing_note == "candidate_file_missing"

    (tmp_path / "candidate.out").write_text("count=4 max=0.720 metric=0.800", encoding="utf-8")
    bad_ok, bad_note = sim.validate_behavior_side_outputs(
        "v3_318_final_step_max_observer_file",
        tmp_path,
        csv_path,
    )
    assert not bad_ok
    assert "max=0.720" in bad_note

    (tmp_path / "candidate.out").write_text("count=4 max=0.810 metric=0.900", encoding="utf-8")
    ok, note = sim.validate_behavior_side_outputs(
        "v3_318_final_step_max_observer_file",
        tmp_path,
        csv_path,
    )
    assert ok
    assert "candidate_file_count=4" in note


def test_sampled_metric_writer_side_output_requires_four_sample_records(tmp_path: Path) -> None:
    csv_path = tmp_path / "out" / "tran.csv"
    csv_path.parent.mkdir()
    csv_path.write_text("time,vin,clk,mode,rst,out,metric\n", encoding="utf-8")

    missing_ok, missing_note = sim.validate_behavior_side_outputs(
        "v3_320_file_io_sampled_metric_writer",
        tmp_path,
        csv_path,
    )
    assert not missing_ok
    assert missing_note == "samples_file_missing"

    (tmp_path / "samples.out").write_text(
        "sample=1 value=0.180 metric=0.200\n"
        "sample=2 value=0.360 metric=0.400\n"
        "sample=3 value=0.720 metric=0.800\n",
        encoding="utf-8",
    )
    short_ok, short_note = sim.validate_behavior_side_outputs(
        "v3_320_file_io_sampled_metric_writer",
        tmp_path,
        csv_path,
    )
    assert not short_ok
    assert "samples_file_record_count=3" in short_note

    (tmp_path / "samples.out").write_text(
        "sample=1 value=0.180 metric=0.200\n"
        "sample=2 value=0.360 metric=0.400\n"
        "sample=3 value=0.720 metric=0.800\n"
        "sample=4 value=0.540 metric=0.600\n",
        encoding="utf-8",
    )
    ok, note = sim.validate_behavior_side_outputs(
        "v3_320_file_io_sampled_metric_writer",
        tmp_path,
        csv_path,
    )
    assert ok
    assert "samples_file_records=4" in note

    (tmp_path / "samples.out").write_text(
        "sample=1 value=0.180 metric=0.200n"
        "sample=2 value=0.360 metric=0.400n"
        "sample=3 value=0.720 metric=0.800n"
        "sample=4 value=0.540 metric=0.600n",
        encoding="utf-8",
    )
    evas_ok, evas_note = sim.validate_behavior_side_outputs(
        "v3_320_file_io_sampled_metric_writer",
        tmp_path,
        csv_path,
    )
    assert evas_ok
    assert "samples_file_records=4" in evas_note


def _gain_trim_rows(*, cap_upper: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    ctrl = 0.30
    previous_clk = 0.0
    for idx in range(1241):
        time_s = idx * 0.5e-9
        t_ns = time_s * 1e9
        phase = (t_ns - 10.0) % 20.0
        clk = 0.9 if t_ns >= 10.0 and phase < 5.0 else 0.0
        rst = 0.9 if t_ns <= 15.0 else 0.0
        meas = 0.2 if t_ns <= 260.0 else 0.7
        target = 0.45
        if previous_clk <= 0.45 < clk:
            if rst > 0.45:
                ctrl = 0.30
            elif meas < target - 0.02:
                ctrl += 0.05
            elif meas > target + 0.02:
                ctrl -= 0.05
            upper = 0.75 if cap_upper else 0.85
            ctrl = min(max(ctrl, 0.05), upper)
        previous_clk = clk
        rows.append({"time": time_s, "clk": clk, "rst": rst, "meas": meas, "target": target, "gain_ctrl": ctrl})
    return rows


def test_gain_trim_checker_requires_both_clamps() -> None:
    assert sim.check_vbm1_gain_trim_controller(_gain_trim_rows())[0]
    ok, note = sim.check_vbm1_gain_trim_controller(_gain_trim_rows(cap_upper=True))
    assert not ok
    assert "reaches_upper_clamp=False" in note


def _differential_driver_rows(
    *, ignore_enable: bool = False, inverted: bool = False
) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for idx in range(100):
        time = idx * 1e-9
        if idx < 12:
            en = 0.0
            din = 0.0
        elif idx < 35:
            en = 0.9
            din = 0.0
        elif idx < 58:
            en = 0.9
            din = 0.9
        elif idx < 75:
            en = 0.0
            din = 0.9
        else:
            en = 0.9
            din = 0.0
        enabled = en > 0.45 or ignore_enable
        if not enabled:
            diff = 0.0
        else:
            diff = 0.4 if din > 0.45 else -0.4
        if inverted:
            diff = -diff
        rows.append(
            {
                "time": time,
                "din": din,
                "en": en,
                "outp": 0.45 + 0.5 * diff,
                "outn": 0.45 - 0.5 * diff,
            }
        )
    return rows


def test_differential_driver_checker_rejects_enable_and_polarity_bugs() -> None:
    assert sim.check_differential_voltage_output(_differential_driver_rows())[0]
    assert not sim.check_differential_voltage_output(
        _differential_driver_rows(ignore_enable=True)
    )[0]
    assert not sim.check_differential_voltage_output(
        _differential_driver_rows(inverted=True)
    )[0]


def _therm_rows(*, nonmonotonic: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for count in [0, 4, 8, 12, 16]:
        row = {"time": float(count), "vout": float(count)}
        if nonmonotonic and count == 12:
            row["vout"] = 3.0
        for bit in range(16):
            row[f"d{bit}"] = 0.9 if bit < count else 0.0
        rows.append(row)
    return rows


def test_thermometer_dac_checker_rejects_nonmonotonic_output() -> None:
    assert sim.check_dac_therm_16b(_therm_rows())[0]
    assert not sim.check_dac_therm_16b(_therm_rows(nonmonotonic=True))[0]


def _therm15_rows(*, omit_full_scale_segment: bool = False) -> list[dict[str, float]]:
    checkpoints = [
        (15e-9, 0),
        (45e-9, 1),
        (75e-9, 2),
        (105e-9, 7),
        (135e-9, 14),
        (165e-9, 15),
    ]
    rows: list[dict[str, float]] = []
    for time, count in checkpoints:
        effective_count = 14 if omit_full_scale_segment and count == 15 else count
        row = {"time": time, "aout": 0.9 * effective_count / 15.0}
        for bit in range(15):
            row[f"seg{bit}"] = 0.9 if bit < effective_count else 0.0
        rows.append(row)
    return rows


def test_thermometer_dac_15seg_checker_rejects_missing_full_scale_segment() -> None:
    assert sim.check_vbm1_thermometer_dac_15seg(_therm15_rows())[0]
    assert not sim.check_vbm1_thermometer_dac_15seg(
        _therm15_rows(omit_full_scale_segment=True)
    )[0]


def _pfd_small_phase_rows(*, sustained_overlap: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for idx in range(1000):
        phase = idx % 50
        up = 0.9 if phase in {2, 3} else 0.0
        dn = 0.9 if sustained_overlap and 2 <= phase <= 18 else 0.0
        rows.append(
            {
                "time": float(idx),
                "ref": 0.9 if phase < 25 else 0.0,
                "div": 0.9 if 5 <= phase < 30 else 0.0,
                "up": up,
                "dn": dn,
            }
        )
    return rows


def test_pfd_small_phase_checker_rejects_sustained_overlap() -> None:
    assert sim.check_pfd_small_phase_error_response(_pfd_small_phase_rows())[0]
    assert not sim.check_pfd_small_phase_error_response(
        _pfd_small_phase_rows(sustained_overlap=True)
    )[0]


def _retriggerable_stretcher_rows(*, ignore_retrigger: bool = False) -> list[dict[str, float]]:
    times_ns = [
        0.0,
        1.0,
        1.1,
        1.3,
        1.8,
        3.0,
        3.1,
        3.3,
        4.4,
        5.0,
        6.4,
        8.4,
        10.4,
        16.0,
        16.1,
        16.3,
        17.2,
        18.0,
        18.1,
        18.3,
        19.4,
        21.4,
        23.4,
        24.0,
        24.1,
        24.3,
        24.6,
        25.1,
        26.0,
        28.1,
    ]
    trig_pulses = [(1.1, 1.3), (3.1, 3.3), (16.1, 16.3), (18.1, 18.3), (24.1, 24.3)]
    rows: list[dict[str, float]] = []
    for time_ns in times_ns:
        trig = 0.9 if any(lo <= time_ns <= hi for lo, hi in trig_pulses) else 0.0
        rst = 0.9 if 25.1 <= time_ns <= 28.0 else 0.0
        if ignore_retrigger:
            pulse_high = (1.1 <= time_ns <= 5.1) or (16.1 <= time_ns <= 20.1) or (24.1 <= time_ns < 25.1)
        else:
            pulse_high = (1.1 <= time_ns <= 7.1) or (16.1 <= time_ns <= 22.1) or (24.1 <= time_ns < 25.1)
        rows.append(
            {
                "time": time_ns * 1e-9,
                "trig": trig,
                "rst": rst,
                "pulse": 0.9 if pulse_high and rst < 0.45 else 0.0,
            }
        )
    return rows


def test_retriggerable_pulse_stretcher_checker_requires_burst_extension() -> None:
    assert sim.check_release_event_pulse_stretcher(_retriggerable_stretcher_rows())[0]
    assert not sim.check_release_event_pulse_stretcher(
        _retriggerable_stretcher_rows(ignore_retrigger=True)
    )[0]


def _code_capture_row(time_ns: float, *, clk: bool = False, load: bool = False, word: int = 0, over: bool = False) -> dict[str, float]:
    row = {
        "time": time_ns * 1e-9,
        "clk": 0.9 if clk else 0.0,
        "load": 0.9 if load else 0.0,
        "over_lo": 0.0,
        "over_hi": 0.9 if over else 0.0,
        "valid": 0.9 if time_ns >= 21.0 else 0.0,
        "overrange": 0.9 if over else 0.0,
        "code_mon": 0.9 * word / 15.0,
    }
    for bit in range(4):
        row[f"din{bit}"] = 0.9 if (word >> bit) & 1 else 0.0
        row[f"bit{bit}"] = 0.9 if (word >> bit) & 1 else 0.0
    return row


def _adc_code_capture_rows(*, drift_between_loads: bool = False) -> list[dict[str, float]]:
    rows = [
        _code_capture_row(0.0, word=0),
        _code_capture_row(19.9, word=0),
        _code_capture_row(20.0, clk=True, load=True, word=3),
        _code_capture_row(21.0, word=3),
        _code_capture_row(35.0, word=3),
        _code_capture_row(59.9, word=3),
        _code_capture_row(60.0, clk=True, load=True, word=12),
        _code_capture_row(61.0, word=12),
        _code_capture_row(75.0, word=2 if drift_between_loads else 12),
        _code_capture_row(99.9, word=12),
        _code_capture_row(100.0, clk=True, load=True, word=15, over=True),
        _code_capture_row(101.0, word=15, over=True),
    ]
    return rows


def test_adc_code_capture_checker_requires_load_gated_hold_and_overrange() -> None:
    assert sim.check_adc_code_capture_register(_adc_code_capture_rows())[0]
    assert not sim.check_adc_code_capture_register(
        _adc_code_capture_rows(drift_between_loads=True)
    )[0]


def _deser_row(time_ns: float, *, clk: bool = False, frame: bool = False, sin: bool = False, word: int = 0, valid: bool = False) -> dict[str, float]:
    row = {
        "time": time_ns * 1e-9,
        "clk": 0.9 if clk else 0.0,
        "frame": 0.9 if frame else 0.0,
        "sin": 0.9 if sin else 0.0,
        "word_valid": 0.9 if valid else 0.0,
        "word_mon": 0.9 * word / 15.0,
    }
    for bit in range(4):
        row[f"bit{bit}"] = 0.9 if (word >> bit) & 1 else 0.0
    return row


def _serial_deserializer_rows(*, wrong_word: bool = False) -> list[dict[str, float]]:
    first = 0x6 if wrong_word else 0x9
    return [
        _deser_row(0.0),
        _deser_row(19.9),
        _deser_row(20.0, clk=True, frame=True, sin=True),
        _deser_row(30.0, clk=True, sin=False),
        _deser_row(40.0, clk=True, sin=False),
        _deser_row(50.0, clk=True, sin=True, word=first, valid=True),
        _deser_row(51.0, word=first, valid=True),
        _deser_row(60.0, word=first),
        _deser_row(69.9, word=first),
        _deser_row(70.0, clk=True, frame=True, sin=False, word=first),
        _deser_row(80.0, clk=True, sin=True, word=first),
        _deser_row(90.0, clk=True, sin=True, word=first),
        _deser_row(100.0, clk=True, sin=False, word=0x6, valid=True),
        _deser_row(101.0, word=0x6, valid=True),
    ]


def test_serial_readout_deserializer_checker_requires_msb_first_words() -> None:
    assert sim.check_serial_readout_deserializer(_serial_deserializer_rows())[0]
    assert not sim.check_serial_readout_deserializer(_serial_deserializer_rows(wrong_word=True))[0]


def _vin_sampled_droop_hold_rows(*, mode: str = "good") -> list[dict[str, float]]:
    sample_edges_ns = [20.0, 80.0, 145.0]
    reset_start_ns = 120.0
    reset_end_ns = 136.0

    def vin_at(time_ns: float) -> float:
        if time_ns < 55.0:
            return 0.20
        if time_ns < 110.0:
            return 0.72
        if time_ns < 138.0:
            return 0.34
        return 0.34

    rows: list[dict[str, float]] = []
    held = 0.0
    last_sample_idx = -1
    for idx in range(341):
        time_ns = idx * 0.5
        reset_high = reset_start_ns <= time_ns <= reset_end_ns
        sample_high = any(edge <= time_ns <= edge + 2.0 for edge in sample_edges_ns)

        for sample_idx, edge in enumerate(sample_edges_ns):
            if time_ns == edge and not reset_high:
                last_sample_idx = sample_idx
                held = 0.75 if mode == "fixed_internal_level" else vin_at(time_ns)

        if reset_high and mode != "ignore_reset":
            held = 0.0
        elif last_sample_idx >= 0 and mode != "no_droop":
            held *= 0.992

        rows.append(
            {
                "time": time_ns * 1e-9,
                "sample": 0.9 if sample_high else 0.0,
                "rst": 0.9 if reset_high else 0.0,
                "vin": vin_at(time_ns),
                "vout": held,
            }
        )
    return rows


def test_vin_sampled_droop_hold_checker_requires_input_capture_droop_and_reset() -> None:
    assert sim.check_release_vin_sampled_droop_hold(_vin_sampled_droop_hold_rows())[0]
    assert not sim.check_release_vin_sampled_droop_hold(
        _vin_sampled_droop_hold_rows(mode="fixed_internal_level")
    )[0]
    assert not sim.check_release_vin_sampled_droop_hold(
        _vin_sampled_droop_hold_rows(mode="no_droop")
    )[0]
    assert not sim.check_release_vin_sampled_droop_hold(
        _vin_sampled_droop_hold_rows(mode="ignore_reset")
    )[0]


def _acquisition_limited_sample_hold_rows(*, mode: str = "good") -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    held = 0.45
    tracking = False
    sample_windows = [(5.0, 10.0), (25.0, 30.0), (45.0, 50.0)]

    def vin_at(time_ns: float) -> float:
        if time_ns < 20.0:
            return 0.25
        if time_ns < 40.0:
            return 0.72
        return 0.32

    for idx in range(181):
        time_ns = idx * 0.5
        rst = time_ns <= 2.0
        sample = any(start <= time_ns < stop for start, stop in sample_windows)
        vin = vin_at(time_ns)
        if rst:
            held = 0.45
            tracking = False
        elif sample and not tracking:
            tracking = True
            if mode == "instantaneous":
                held = vin
        elif not sample:
            tracking = False

        if sample and mode != "instantaneous" and abs(time_ns - round(time_ns)) < 1e-12:
            held = held + 0.32 * (vin - held)
        if not sample and mode == "hold_drift" and time_ns > 10.0:
            held += 0.003

        rows.append(
            {
                "time": time_ns * 1e-9,
                "sample": 0.9 if sample else 0.0,
                "rst": 0.9 if rst else 0.0,
                "vin": vin,
                "vout": held,
                "metric": 0.9 if sample else 0.0,
            }
        )
    return rows


def test_acquisition_limited_sample_hold_checker_rejects_ideal_jump_and_hold_drift() -> None:
    assert sim.check_acquisition_limited_sample_hold(_acquisition_limited_sample_hold_rows())[0]
    assert not sim.check_acquisition_limited_sample_hold(
        _acquisition_limited_sample_hold_rows(mode="instantaneous")
    )[0]
    assert not sim.check_acquisition_limited_sample_hold(
        _acquisition_limited_sample_hold_rows(mode="hold_drift")
    )[0]


def _wreal_assign_rows(expected_fn, *, wrong: bool = False) -> list[dict[str, float]]:
    base_rows = [
        (0.0, 0.60, 0.10, 0.0),
        (100.0, 0.60, 0.10, 0.0),
        (210.0, 0.45, 0.10, 0.9),
        (330.0, 0.45, 0.32, 0.9),
        (390.0, 0.50, 0.32, 0.9),
        (470.0, 0.72, 0.32, 0.0),
        (620.0, 0.72, 0.32, 0.0),
    ]
    rows: list[dict[str, float]] = []
    for time_ns, a_value, b_value, sel_value in base_rows:
        row = {
            "time": time_ns * 1e-9,
            "a": a_value,
            "b": b_value,
            "sel": sel_value,
            "y": 0.0,
        }
        row["y"] = 0.0 if wrong else expected_fn(row)
        rows.append(row)
    return rows


def test_v3_wreal_assign_checkers_follow_hidden_stimulus_values() -> None:
    cases = [
        (
            sim.check_v3_341_wreal_gain_pass_through,
            lambda row: 0.75 * row["a"] + 0.1 if row["sel"] > 0.45 else 0.75 * row["b"],
        ),
        (
            sim.check_v3_342_wreal_two_input_summer,
            lambda row: row["a"] + row["b"] + (0.1 if row["sel"] > 0.45 else 0.0),
        ),
        (
            sim.check_v3_343_wreal_threshold_flag,
            lambda row: 0.9
            if ((row["a"] + (0.1 if row["sel"] > 0.45 else 0.0)) > 0.45)
            else 0.0,
        ),
        (
            sim.check_v3_344_wreal_clamped_mux,
            lambda row: min(0.9, max(0.0, row["a"] if row["sel"] > 0.45 else row["b"])),
        ),
        (
            sim.check_v3_345_wreal_scale_offset,
            lambda row: 0.75 * row["b"] - 0.1 if row["sel"] > 0.45 else 0.75 * row["a"] + 0.1,
        ),
    ]
    for checker, expected_fn in cases:
        assert checker(_wreal_assign_rows(expected_fn))[0]
        assert not checker(_wreal_assign_rows(expected_fn, wrong=True))[0]


def _logic_assign_rows(expected_fn, *, wrong: bool = False) -> list[dict[str, float]]:
    base_rows = [
        (0.0, 0.0, 0.0, 0.0),
        (120.0, 0.0, 1.0, 1.0),
        (150.0, 0.0, 1.0, 1.0),
        (220.0, 1.0, 0.0, 1.0),
        (340.0, 1.0, 1.0, 1.0),
        (390.0, 1.0, 1.0, 1.0),
        (430.0, 1.0, 1.0, 1.0),
        (500.0, 0.0, 1.0, 0.0),
        (570.0, 1.0, 0.0, 0.0),
    ]
    rows: list[dict[str, float]] = []
    for time_ns, a_value, b_value, en_value in base_rows:
        expected = expected_fn(a_value > 0.45, b_value > 0.45, en_value > 0.45)
        rows.append(
            {
                "time": time_ns * 1e-9,
                "a": a_value,
                "b": b_value,
                "en": en_value,
                "y": 0.0 if wrong else (1.0 if expected else 0.0),
            }
        )
    return rows


def test_v3_logic_assign_checkers_follow_hidden_stimulus_values() -> None:
    cases = [
        (
            sim.check_v3_346_logic_assign_inverter,
            lambda a_bit, b_bit, en_bit: (not a_bit) if en_bit else b_bit,
        ),
        (
            sim.check_v3_347_logic_assign_and_or,
            lambda a_bit, b_bit, en_bit: (a_bit and b_bit) or en_bit,
        ),
        (
            sim.check_v3_348_logic_assign_xor_flag,
            lambda a_bit, b_bit, en_bit: (a_bit ^ b_bit) if en_bit else False,
        ),
        (
            sim.check_v3_349_logic_assign_priority_mux,
            lambda a_bit, b_bit, en_bit: a_bit if en_bit else b_bit,
        ),
        (
            sim.check_v3_350_logic_assign_reduction,
            lambda a_bit, b_bit, en_bit: a_bit and b_bit and en_bit,
        ),
    ]
    for checker, expected_fn in cases:
        assert checker(_logic_assign_rows(expected_fn))[0]
        assert not checker(_logic_assign_rows(expected_fn, wrong=True))[0]


def _clocked_dff_rows(*, edge: str = "posedge", wrong: bool = False) -> list[dict[str, float]]:
    if edge == "posedge":
        samples = [
            (0.0, 0.0, 1.0, 1.0, 1.0),
            (10.0, 0.2, 1.0, 1.0, 1.0),
            (20.0, 0.0, 0.0, 1.0, 1.0),
            (30.0, 0.2, 0.0, 1.0, 1.0),
            (35.0, 0.0, 0.0, 1.0, 1.0),
            (40.0, 0.0, 0.0, 0.0, 0.0),
            (50.0, 0.2, 0.0, 0.0, 1.0),
            (55.0, 0.0, 0.0, 0.0, 1.0),
            (60.0, 0.0, 0.0, 1.0, 0.0),
            (70.0, 0.2, 0.0, 1.0, 0.0),
        ]
    else:
        samples = [
            (0.0, 1.0, 1.0, 1.0, 1.0),
            (10.0, 0.0, 1.0, 1.0, 1.0),
            (20.0, 1.0, 0.0, 1.0, 1.0),
            (30.0, 0.0, 0.0, 1.0, 1.0),
            (35.0, 1.0, 0.0, 1.0, 1.0),
            (40.0, 1.0, 0.0, 0.0, 0.0),
            (50.0, 0.0, 0.0, 0.0, 1.0),
            (55.0, 1.0, 0.0, 0.0, 1.0),
            (60.0, 1.0, 0.0, 1.0, 0.0),
            (70.0, 0.0, 0.0, 1.0, 0.0),
        ]
    q = 0.0
    prev_clk = samples[0][1]
    rows: list[dict[str, float]] = []
    for time_ns, clk, rst, d, en in samples:
        if rows:
            is_edge = prev_clk <= 1e-9 < clk if edge == "posedge" else prev_clk > 1e-9 >= clk
            if is_edge:
                if rst > 1e-9:
                    q = 0.0
                elif en > 1e-9:
                    q = 1.0 if d > 1e-9 else 0.0
        rows.append(
            {
                "time": time_ns * 1e-9,
                "clk": clk,
                "rst": rst,
                "d": d,
                "en": en,
                "q": 1.0 - q if wrong else q,
            }
        )
        prev_clk = clk
    return rows


def _counter_msb_rows(*, wrong: bool = False) -> list[dict[str, float]]:
    samples = [
        (0.0, 0.0, 1.0, 1.0, 1.0),
        (10.0, 1.0, 1.0, 1.0, 1.0),
        (20.0, 0.0, 0.0, 1.0, 1.0),
        (30.0, 1.0, 0.0, 1.0, 1.0),
        (40.0, 0.0, 0.0, 1.0, 1.0),
        (50.0, 1.0, 0.0, 1.0, 1.0),
        (60.0, 0.0, 0.0, 0.0, 1.0),
        (70.0, 1.0, 0.0, 0.0, 1.0),
        (80.0, 0.0, 0.0, 1.0, 1.0),
        (90.0, 1.0, 0.0, 1.0, 1.0),
    ]
    count = 0
    prev_clk = samples[0][1]
    rows: list[dict[str, float]] = []
    for time_ns, clk, rst, d, en in samples:
        if rows and prev_clk <= 0.45 < clk:
            if rst > 0.45:
                count = 0
            elif en > 0.45 and d > 0.45:
                count = (count + 1) & 0x3
        q = 1.0 if (count & 0x2) else 0.0
        rows.append(
            {
                "time": time_ns * 1e-9,
                "clk": clk,
                "rst": rst,
                "d": d,
                "en": en,
                "q": 1.0 - q if wrong else q,
            }
        )
        prev_clk = clk
    return rows


def test_v3_clocked_checkers_follow_edge_stimulus_values() -> None:
    assert sim.check_v3_351_always_posedged_dff(_clocked_dff_rows())[0]
    assert not sim.check_v3_351_always_posedged_dff(_clocked_dff_rows(wrong=True))[0]
    assert sim.check_v3_352_always_negedge_sampler(_clocked_dff_rows(edge="negedge"))[0]
    assert not sim.check_v3_352_always_negedge_sampler(
        _clocked_dff_rows(edge="negedge", wrong=True)
    )[0]
    assert sim.check_v3_354_always_counter_two_bit(_counter_msb_rows())[0]
    assert not sim.check_v3_354_always_counter_two_bit(_counter_msb_rows(wrong=True))[0]


def _mixed_rows(expected_fn, *, wrong: bool = False) -> list[dict[str, float]]:
    base_rows = [
        (0.0, 0.55, 0.0, 1.0, 0.0, 0.25, 0.75),
        (100.0, 0.55, 0.0, 1.0, 0.0, 0.25, 0.75),
        (220.0, 0.25, 0.0, 0.0, 1.0, 0.68, 0.75),
        (280.0, 0.30, 0.0, 0.0, 0.0, 0.70, 0.24),
        (340.0, 0.82, 0.0, 0.0, 0.0, 0.68, 0.22),
        (520.0, 0.82, 0.0, 1.0, 1.0, 0.42, 0.22),
        (610.0, 0.35, 0.0, 1.0, 0.0, 0.30, 0.56),
        (700.0, 0.40, 0.0, 0.0, 1.0, 0.42, 0.56),
    ]
    rows: list[dict[str, float]] = []
    for time_ns, vin, clk, en, sel, a_value, b_value in base_rows:
        for offset_ns in range(6):
            row = {
                "time": (time_ns + offset_ns) * 1e-9,
                "vin": vin,
                "clk": clk,
                "en": en,
                "sel": sel,
                "a": a_value,
                "b": b_value,
                "vout": 0.0,
            }
            row["vout"] = 0.0 if wrong else expected_fn(row)
            rows.append(row)
    return rows


def _mixed_sampler_rows(*, wrong: bool = False) -> list[dict[str, float]]:
    samples = [
        (0.0, 0.45, 0.0, 0.0),
        (80.0, 0.45, 1.0, 0.0),
        (120.0, 0.45, 0.0, 0.0),
        (220.0, 0.72, 1.0, 1.0),
        (300.0, 0.72, 0.0, 1.0),
        (520.0, 0.30, 1.0, 0.0),
        (600.0, 0.30, 0.0, 0.0),
        (680.0, 0.86, 1.0, 1.0),
    ]
    sampled = False
    prev_clk = samples[0][2]
    rows: list[dict[str, float]] = []
    for time_ns, vin, clk, en in samples:
        if rows and prev_clk <= 1e-9 < clk:
            sampled = en > 1e-9
        expected = vin if sampled else 0.0
        for offset_ns in range(6):
            rows.append(
                {
                    "time": (time_ns + offset_ns) * 1e-9,
                    "vin": vin,
                    "clk": clk,
                    "en": en,
                    "sel": 0.0,
                    "a": 0.2,
                    "b": 0.7,
                    "vout": 0.0 if wrong else expected,
                }
            )
        prev_clk = clk
    return rows


def test_v3_mixed_signal_checkers_follow_hidden_stimulus_values() -> None:
    cases = [
        (
            sim.check_v3_356_mixed_logic_enable_voltage_driver,
            lambda row: row["vin"] if row["en"] > 1e-9 else 0.0,
        ),
        (
            sim.check_v3_357_mixed_wreal_to_electrical_buffer,
            lambda row: row["a"],
        ),
        (
            sim.check_v3_358_mixed_electrical_threshold_logic_flag,
            lambda row: 0.9 if row["vin"] > 0.45 else 0.0,
        ),
        (
            sim.check_v3_360_mixed_wreal_logic_select_driver,
            lambda row: row["a"] if row["sel"] > 1e-9 else row["b"],
        ),
    ]
    for checker, expected_fn in cases:
        assert checker(_mixed_rows(expected_fn))[0]
        assert not checker(_mixed_rows(expected_fn, wrong=True))[0]

    assert sim.check_v3_359_mixed_logic_clocked_voltage_sampler(_mixed_sampler_rows())[0]
    assert not sim.check_v3_359_mixed_logic_clocked_voltage_sampler(
        _mixed_sampler_rows(wrong=True)
    )[0]


def _noise_metric_rows(metric_fn, *, out_fn=None, wrong: bool = False) -> list[dict[str, float]]:
    samples = [
        (0.0, 0.25, 0.0),
        (60.0, 0.25, 1.0),
        (90.0, 0.25, 0.0),
        (170.0, 0.72, 1.0),
        (200.0, 0.72, 0.0),
        (310.0, 0.38, 1.0),
        (340.0, 0.38, 0.0),
        (450.0, 0.82, 1.0),
        (480.0, 0.82, 0.0),
    ]
    metric = 0.0
    prev_clk = samples[0][2]
    edge_count = 0
    rows: list[dict[str, float]] = []
    for time_ns, ctrl, clk in samples:
        if rows and prev_clk <= 0.45 < clk:
            edge_count += 1
            metric = metric_fn(ctrl, edge_count)
        out = ctrl if out_fn is None else out_fn(ctrl)
        for offset_ns in range(6):
            rows.append(
                {
                    "time": (time_ns + offset_ns) * 1e-9,
                    "ctrl": ctrl,
                    "clk": clk,
                    "out": out,
                    "metric": 0.0 if wrong else metric,
                }
            )
        prev_clk = clk
    return rows


def test_v3_noise_analysis_checkers_follow_hidden_stimulus_values() -> None:
    cases = [
        (sim.check_v3_361_white_noise_voltage_source, lambda ctrl, _edge: ctrl, None),
        (sim.check_v3_362_white_noise_gated_source, lambda ctrl, _edge: 0.9 if ctrl > 0.45 else 0.0, None),
        (sim.check_v3_363_flicker_noise_voltage_source, lambda _ctrl, _edge: 1.0, None),
        (sim.check_v3_364_flicker_noise_corner_selector, lambda ctrl, _edge: 0.9 if ctrl > 0.45 else 0.0, None),
        (sim.check_v3_365_noise_table_voltage_shaper, lambda ctrl, _edge: 0.3 + ctrl * 0.2, None),
        (sim.check_v3_366_noise_table_gated_shaper, lambda ctrl, _edge: 0.9 if ctrl > 0.45 else 0.0, None),
        (sim.check_v3_367_analysis_dependent_dc_tran_mode, lambda _ctrl, _edge: 0.9, lambda ctrl: ctrl),
        (sim.check_v3_368_analysis_dependent_noise_enable, lambda ctrl, _edge: ctrl, None),
        (sim.check_v3_369_ac_stim_small_signal_source, lambda _ctrl, _edge: 1.0, lambda ctrl: ctrl),
        (sim.check_v3_370_ac_stim_phase_selector, lambda ctrl, _edge: 0.9 if ctrl > 0.45 else 0.0, lambda ctrl: ctrl),
        (sim.check_v3_371_combined_white_flicker_noise, lambda _ctrl, _edge: 1.5, None),
        (sim.check_v3_372_analysis_aware_noise_metric, lambda _ctrl, edge: edge / 8.0, lambda ctrl: ctrl),
    ]
    for checker, metric_fn, out_fn in cases:
        assert checker(_noise_metric_rows(metric_fn, out_fn=out_fn))[0]
        assert not checker(_noise_metric_rows(metric_fn, out_fn=out_fn, wrong=True))[0]


def _task_input_from_segments(time_ns: float, segments: list[tuple[float, float]]) -> float:
    value = segments[0][1]
    for start_ns, segment_value in segments:
        if time_ns >= start_ns:
            value = segment_value
        else:
            break
    return value


def _task_clocked_rows(update_fn, input_fn, *, wrong: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    state: dict[str, float | int] = {
        "count": 0,
        "state_q": 0,
        "phase": 0,
        "sum": 0.0,
        "threshold": 0.45,
    }
    out = 0.0
    metric = 0.0
    prev_clk = 0.0
    for idx in range(521):
        time_ns = float(idx)
        clk = 1.0 if any(edge <= time_ns <= edge + 29.0 for edge in [50.0, 150.0, 250.0, 350.0, 450.0]) else 0.0
        vin, mode, rst = input_fn(time_ns)
        row = {
            "time": time_ns * 1e-9,
            "vin": vin,
            "clk": clk,
            "mode": mode,
            "rst": rst,
            "out": out,
            "metric": metric,
        }
        if prev_clk <= 0.45 < clk:
            out, metric = update_fn(state, row)
        row["out"] = 0.0 if wrong else out
        row["metric"] = 0.0 if wrong else metric
        rows.append(row)
        prev_clk = clk
    return rows


def test_v3_task_checkers_follow_hidden_stimulus_values() -> None:
    def limiter_update(state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            state["count"] = 0
            state["state_q"] = 0
            return 0.0, 0.0
        state["count"] = int(state["count"]) + 1
        state_q = int(state["count"]) % 3
        sample = row["vin"]
        if state_q == 0:
            out = sample
        elif state_q == 1:
            out = 0.9 if sample > 0.45 else 0.0
        else:
            out = min(0.9, max(0.0, sample))
        return out, out / 0.9

    def dual_update(_state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            return 0.0, 0.0
        out = min(0.9, max(0.0, row["vin"] + row["mode"]))
        metric = min(0.9, max(0.0, row["vin"] - row["mode"] + 0.3)) / 0.9
        return out, metric

    def counter_update(state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            state["count"] = 0
            state["sum"] = 0.0
            return 0.0, 0.0
        if row["mode"] > 0.45:
            state["count"] = int(state["count"]) + 1
            state["sum"] = float(state["sum"]) + row["vin"]
        count = int(state["count"])
        return min(0.9, 0.15 * count), float(state["sum"]) / count if count else 0.0

    def reset_update(state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            state["phase"] = 0
            return 0.0, 0.0
        state["phase"] = int(state["phase"]) + 1
        out = row["vin"] + (0.2 if row["mode"] > 0.45 else 0.0)
        return min(0.9, max(0.0, out)), int(state["phase"]) / 4.0

    def threshold_update(state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            state["threshold"] = 0.45
            return 0.0, 0.0
        threshold = float(state["threshold"])
        out = 0.9 if row["vin"] > threshold else 0.0
        if row["mode"] > 0.45:
            state["threshold"] = min(0.75, threshold + 0.1)
        return out, threshold

    def normalizer_update(_state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            return 0.0, 0.0
        out = min(0.9, max(0.0, row["vin"]))
        norm_span = 0.9 if row["mode"] > 0.45 else 0.45
        metric = min(0.9, max(0.0, 0.9 * abs(row["vin"] - 0.45) / norm_span))
        return out, metric

    cases = [
        (
            sim.check_v3_373_task_output_limiter,
            limiter_update,
            lambda t: (
                _task_input_from_segments(t, [(0.0, 0.15), (100.0, 0.95), (200.0, -0.20), (300.0, 0.55), (400.0, 1.25)]),
                0.0,
                0.0,
            ),
        ),
        (
            sim.check_v3_374_task_dual_output_update,
            dual_update,
            lambda t: (
                _task_input_from_segments(t, [(0.0, -0.10), (100.0, 0.35), (200.0, 0.95), (300.0, 0.45), (400.0, 0.10)]),
                _task_input_from_segments(t, [(0.0, 0.25), (100.0, 0.10), (200.0, -0.30), (300.0, 0.55), (400.0, -0.15)]),
                0.0,
            ),
        ),
        (
            sim.check_v3_375_task_event_counter_service,
            counter_update,
            lambda t: (
                _task_input_from_segments(t, [(0.0, 0.75), (100.0, 0.20), (200.0, 0.85), (300.0, 0.40), (400.0, 0.65)]),
                _task_input_from_segments(t, [(0.0, 0.0), (100.0, 0.9), (200.0, 0.9), (300.0, 0.0), (400.0, 0.9)]),
                0.0,
            ),
        ),
        (
            sim.check_v3_376_task_reset_sequencer,
            reset_update,
            lambda t: (
                _task_input_from_segments(t, [(0.0, 0.55), (100.0, 0.10), (200.0, 0.75), (300.0, 0.35), (400.0, 0.95)]),
                _task_input_from_segments(t, [(0.0, 0.9), (100.0, 0.0), (200.0, 0.9), (300.0, 0.0)]),
                0.9 if 230.0 <= t <= 289.0 else 0.0,
            ),
        ),
        (
            sim.check_v3_377_task_stateful_threshold_update,
            threshold_update,
            lambda t: (
                _task_input_from_segments(t, [(0.0, 0.30), (100.0, 0.62), (200.0, 0.58), (300.0, 0.72), (400.0, 0.50)]),
                _task_input_from_segments(t, [(0.0, 0.9), (200.0, 0.0), (300.0, 0.9), (400.0, 0.0)]),
                0.9 if 230.0 <= t <= 289.0 else 0.0,
            ),
        ),
        (
            sim.check_v3_378_task_metric_normalizer,
            normalizer_update,
            lambda t: (
                _task_input_from_segments(t, [(0.0, 0.10), (100.0, 0.45), (200.0, 0.82), (300.0, -0.20), (400.0, 1.10)]),
                _task_input_from_segments(t, [(0.0, 0.9), (100.0, 0.0), (200.0, 0.9), (300.0, 0.0), (400.0, 0.9)]),
                0.0,
            ),
        ),
    ]
    for checker, update_fn, input_fn in cases:
        assert checker(_task_clocked_rows(update_fn, input_fn))[0]
        assert not checker(_task_clocked_rows(update_fn, input_fn, wrong=True))[0]


def test_v3_file_io_checkers_follow_hidden_stimulus_values() -> None:
    def file_gate_update(_state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            return 0.0, 0.9
        return (0.9 if row["vin"] > 0.45 else 0.0), 0.9

    def input_fn(time_ns: float) -> tuple[float, float, float]:
        return (
            _task_input_from_segments(
                time_ns,
                [(0.0, 0.82), (100.0, 0.20), (200.0, 0.55), (300.0, 0.10), (400.0, 0.95)],
            ),
            0.0,
            0.9 if 230.0 <= time_ns <= 289.0 else 0.0,
        )

    checkers = [
        sim.check_v3_379_file_fgets_config_loader,
        sim.check_v3_380_file_feof_line_counter,
        sim.check_v3_381_file_fseek_offset_reader,
        sim.check_v3_382_file_ftell_position_meter,
        sim.check_v3_383_file_rewind_second_pass,
        sim.check_v3_384_file_fopen_mode_selector,
    ]
    for checker in checkers:
        good_rows = _task_clocked_rows(file_gate_update, input_fn)
        for row in good_rows:
            row["metric"] = 0.9
        assert checker(good_rows)[0]
        assert not checker(_task_clocked_rows(file_gate_update, input_fn, wrong=True))[0]


def test_v3_table_model_checkers_follow_hidden_stimulus_values() -> None:
    cases = [
        (
            sim.check_v3_385_table_model_linear_gain,
            [(0.0, 0.0), (0.45, 0.35), (0.9, 0.9)],
            [(0.0, 0.05), (100.0, 0.42), (200.0, 0.63), (300.0, 0.88), (400.0, 0.18)],
        ),
        (
            sim.check_v3_386_table_model_clamped_transfer,
            [(0.0, 0.0), (0.45, 0.35), (0.9, 0.9)],
            [(0.0, -0.35), (100.0, 0.15), (200.0, 0.72), (300.0, 1.25), (400.0, 0.48)],
        ),
        (
            sim.check_v3_387_table_model_threshold_map,
            [(0.0, 0.0), (0.44, 0.0), (0.46, 0.9), (0.9, 0.9)],
            [(0.0, 0.43), (100.0, 0.455), (200.0, 0.20), (300.0, 0.70), (400.0, 0.445)],
        ),
        (
            sim.check_v3_388_table_model_dac_code_map,
            [(0.0, 0.0), (1.0, 0.3), (2.0, 0.6), (3.0, 0.9)],
            [(0.0, 0.5), (100.0, 1.5), (200.0, 2.5), (300.0, -0.2), (400.0, 3.4)],
        ),
        (
            sim.check_v3_389_table_model_temperature_profile,
            [(-40.0, 0.55), (25.0, 0.9), (85.0, 0.7), (125.0, 0.5)],
            [(0.0, -20.0), (100.0, 60.0), (200.0, 105.0), (300.0, 140.0), (400.0, -55.0)],
        ),
        (
            sim.check_v3_390_table_model_piecewise_calibrator,
            [(0.0, 0.0), (0.3, 0.25), (0.6, 0.65), (0.9, 0.9)],
            [(0.0, 0.05), (100.0, 0.33), (200.0, 0.58), (300.0, 0.82), (400.0, 1.05)],
        ),
    ]

    def make_update(points):
        def update(_state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
            if row["rst"] > 0.45:
                return 0.0, 0.0
            out = sim._piecewise_linear_table(row["vin"], points)
            return out, out / 0.9

        return update

    for checker, points, vin_segments in cases:
        input_fn = lambda time_ns, segments=vin_segments: (
            _task_input_from_segments(time_ns, segments),
            0.0,
            0.0,
        )
        assert checker(_task_clocked_rows(make_update(points), input_fn))[0]
        assert not checker(_task_clocked_rows(make_update(points), input_fn, wrong=True))[0]


def _rdist_sequence_rows(metric_sequence: list[float], *, wrong: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    vin_segments = [(0.0, 0.62), (100.0, 0.74), (200.0, 0.66), (300.0, 0.81)]
    metric = 0.0
    out = 0.0
    prev_clk = 0.0
    edge_count = 0
    for idx in range(421):
        time_ns = float(idx)
        clk = 1.0 if any(edge <= time_ns <= edge + 29.0 for edge in [50.0, 150.0, 250.0, 350.0]) else 0.0
        vin = _task_input_from_segments(time_ns, vin_segments)
        if prev_clk <= 0.45 < clk:
            metric = metric_sequence[edge_count]
            out = vin + 0.01 * metric
            edge_count += 1
        rows.append(
            {
                "time": time_ns * 1e-9,
                "vin": vin,
                "clk": clk,
                "mode": 0.0,
                "rst": 0.0,
                "out": 0.0 if wrong else out,
                "metric": 0.0 if wrong else metric,
            }
        )
        prev_clk = clk
    return rows


def test_v3_rdist_checkers_follow_hidden_vin_values() -> None:
    cases = [
        (
            sim.check_v3_391_rdist_exponential_jitter,
            [3.7943, 0.5581, 0.6179, 0.1685],
            [5.06912, 1.22615, 1.74085, 0.261145],
        ),
        (
            sim.check_v3_392_rdist_poisson_count_noise,
            [3.0, 2.0, 0.0, 0.0],
            [0.0, 2.0, 3.0, 6.0],
        ),
        (
            sim.check_v3_393_rdist_normal_offset_dither,
            [0.0113, -0.0160, 0.0591, 0.0312],
            [-0.0110707, -0.0234803, -0.0361837, -0.062261],
        ),
        (sim.check_v3_394_rdist_chi_square_energy, [0.5044, 0.5387, 0.9852, 1.6858]),
        (sim.check_v3_395_rdist_t_tail_dither, [-1.7540, 0.0963, 0.4683, -1.5343]),
        (
            sim.check_v3_396_rdist_erlang_latency,
            [1.0851, 1.0945, 0.5121, 0.2559],
            [1.30561, 0.24618, 0.275805, 0.191614],
        ),
    ]
    for case in cases:
        checker = case[0]
        sequence = case[1]
        assert checker(_rdist_sequence_rows(sequence))[0]
        if len(case) > 2:
            assert checker(_rdist_sequence_rows(case[2]))[0]
        assert not checker(_rdist_sequence_rows(sequence, wrong=True))[0]


def _hierarchy_rows(out_fn, *, metric_fn=None, wrong: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    vin_segments = [(0.0, 0.25), (50.0, 0.72), (100.0, 0.45), (150.0, 0.9)]
    for idx in range(201):
        time_ns = float(idx)
        vin = _task_input_from_segments(time_ns, vin_segments)
        row = {
            "time": time_ns * 1e-9,
            "vin": vin,
            "clk": 0.0,
            "mode": 0.0,
            "rst": 0.0,
            "out": 0.0,
            "metric": 0.0,
        }
        row["out"] = 0.0 if wrong else out_fn(row)
        row["metric"] = 0.0 if wrong else (metric_fn(row) if metric_fn else 0.0)
        rows.append(row)
    return rows


def test_v3_hierarchy_checkers_follow_hidden_vin_values() -> None:
    cases = [
        (sim.check_v3_397_hierarchy_gain_child, lambda row: 0.8 * row["vin"], None),
        (sim.check_v3_398_hierarchy_two_stage_chain, lambda row: 0.4 * row["vin"], lambda row: 0.8 * row["vin"]),
        (sim.check_v3_399_hierarchy_parameter_override, lambda row: 1.5 * row["vin"], None),
        (sim.check_v3_400_hierarchy_named_port_map, lambda row: 0.8 * row["vin"], None),
        (sim.check_v3_401_hierarchy_ordered_port_map, lambda row: 0.4 * row["vin"], lambda row: 0.8 * row["vin"]),
        (sim.check_v3_402_hierarchy_shared_threshold_child, lambda row: 0.9 if row["vin"] > 0.45 else 0.0, None),
    ]
    for checker, out_fn, metric_fn in cases:
        assert checker(_hierarchy_rows(out_fn, metric_fn=metric_fn))[0]
        assert not checker(_hierarchy_rows(out_fn, metric_fn=metric_fn, wrong=True))[0]


def _vector_counter_rows(expected_fn, *, reset_edges: set[int] | None = None, wrong: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    reset_edges = reset_edges or set()
    count = 0
    out = 0.0
    metric = 0.0
    prev_clk = 0.0
    edges = [50.0, 150.0, 250.0, 350.0, 450.0, 550.0, 650.0, 750.0, 850.0]
    for idx in range(921):
        time_ns = float(idx)
        clk = 1.0 if any(edge <= time_ns <= edge + 29.0 for edge in edges) else 0.0
        edge_index = sum(1 for edge in edges if edge <= time_ns)
        rst = 0.9 if edge_index in reset_edges and clk > 0.45 else 0.0
        if prev_clk <= 0.45 < clk:
            if rst > 0.45:
                count = 0
                out = 0.0
                metric = 0.0
            else:
                out, metric = expected_fn(count)
                count += 1
        rows.append(
            {
                "time": time_ns * 1e-9,
                "vin": 0.7,
                "clk": clk,
                "mode": 0.0,
                "rst": rst,
                "out": 0.0 if wrong else out,
                "metric": 0.0 if wrong else metric,
            }
        )
        prev_clk = clk
    return rows


def test_v3_vector_checkers_follow_counter_and_reset_values() -> None:
    cases = [
        (sim.check_v3_403_vector_bit_select_flag, lambda c: (0.9 if ((c + 4) & 0x4) else 0.0, float((c + 4) & 1))),
        (sim.check_v3_404_vector_part_select_window, lambda c: (0.9 if (((c + 9) >> 1) & 7) > 3 else 0.0, float(((c + 9) >> 1) & 7))),
        (sim.check_v3_405_vector_concat_code_build, lambda c: (0.9 if (8 | (c & 3)) > 8 else 0.0, float(8 | (c & 3)))),
        (sim.check_v3_406_vector_replication_mask, lambda c: (0.9 if (10 & c) != 0 else 0.0, 10.0)),
        (sim.check_v3_407_vector_reduction_parity, lambda c: (0.9 if sim._odd_parity(c + 1) else 0.0, 1.0)),
        (sim.check_v3_408_vector_shift_and_mask_decoder, lambda c: (0.9 if (((c + 12) >> 1) & 3) == 2 else 0.0, float(((c + 12) >> 1) & 3))),
    ]
    for checker, expected_fn in cases:
        assert checker(_vector_counter_rows(expected_fn, reset_edges={3}))[0]
        assert not checker(_vector_counter_rows(expected_fn, reset_edges={3}, wrong=True))[0]


def test_v3_macro_lifecycle_loop_parameter_checkers_follow_hidden_stimulus_values() -> None:
    def clamp_update(_state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            return 0.0, 0.0
        out = min(0.9, max(0.0, row["vin"]))
        return out, out / 0.9

    def escaped_update(_state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            return 0.0, 0.0
        trim = 0.2 if row["mode"] > 0.45 else 0.1
        return row["vin"] + trim, trim

    def lifecycle_update(state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            state["count"] = 0
            return 0.0, 0.0
        metric = float(state["count"])
        state["count"] = int(state["count"]) + 1
        return row["vin"], metric

    def loop_update(state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            state["count"] = 0
            return 0.0, 0.0
        acc = 3.0 + 3.0 * int(state["count"])
        state["count"] = int(state["count"]) + 1
        return 0.9 if acc > 3.0 else 0.0, acc

    def parameter_update(state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            state["count"] = 0
            return 0.0, 0.0
        state["count"] = (int(state["count"]) + 1) % 8
        return 0.8 * row["vin"], float(state["count"])

    def input_from(vin_segments, mode_segments=None):
        return lambda time_ns: (
            _task_input_from_segments(time_ns, vin_segments),
            _task_input_from_segments(time_ns, mode_segments or [(0.0, 0.0)]),
            0.9 if 230.0 <= time_ns <= 289.0 else 0.0,
        )

    cases = [
        (
            sim.check_v3_409_macro_functionlike_clamp,
            clamp_update,
            input_from([(0.0, 1.1), (100.0, -0.15), (200.0, 0.52), (300.0, 0.95), (400.0, 0.25)]),
        ),
        (
            sim.check_v3_411_escaped_identifier_state,
            escaped_update,
            input_from(
                [(0.0, 0.55), (100.0, 0.25), (200.0, 0.75), (300.0, 0.35), (400.0, 0.55)],
                [(0.0, 0.0), (100.0, 0.9), (200.0, 0.0), (300.0, 0.9), (400.0, 0.0)],
            ),
        ),
        (
            sim.check_v3_412_initial_final_step_lifecycle,
            lifecycle_update,
            input_from([(0.0, 0.65), (100.0, 0.15), (200.0, 0.85), (300.0, 0.45), (400.0, 0.65)]),
        ),
        (
            sim.check_v3_413_while_loop_array_sum,
            loop_update,
            input_from([(0.0, 0.1), (100.0, 0.9), (200.0, 0.3), (300.0, 0.8), (400.0, 0.1)]),
        ),
        (
            sim.check_v3_414_parameter_range_real_control,
            parameter_update,
            input_from([(0.0, 0.35), (100.0, 0.75), (200.0, 0.15), (300.0, 0.9), (400.0, 0.35)]),
        ),
    ]
    for checker, update_fn, input_fn in cases:
        assert checker(_task_clocked_rows(update_fn, input_fn))[0]
        assert not checker(_task_clocked_rows(update_fn, input_fn, wrong=True))[0]


def test_v3_mixed_file_string_random_preprocessor_checkers_follow_hidden_values() -> None:
    def logic_bridge_rows(*, wrong: bool = False) -> list[dict[str, float]]:
        rows: list[dict[str, float]] = []
        for idx in range(501):
            time_ns = float(idx)
            ain = _task_input_from_segments(
                time_ns,
                [(0.0, 0.20), (80.0, 0.55), (180.0, 0.35), (280.0, 0.82), (380.0, 0.42)],
            )
            en = _task_input_from_segments(time_ns, [(0.0, 1.0), (150.0, 0.0), (250.0, 1.0)])
            flag = 1.0 if en > 0.45 and ain > 0.45 else 0.0
            rows.append({"time": time_ns * 1e-9, "ain": ain, "en": en, "flag": 0.0 if wrong else flag})
        return rows

    def latch_rows(*, wrong: bool = False) -> list[dict[str, float]]:
        rows: list[dict[str, float]] = []
        flag = 0.0
        prev_clk = 0.0
        for idx in range(551):
            time_ns = float(idx)
            vin = _task_input_from_segments(
                time_ns,
                [(0.0, 0.75), (80.0, 0.50), (150.0, 0.40), (250.0, 0.65), (350.0, 0.30), (450.0, 0.80)],
            )
            clk = 1.0 if any(edge <= time_ns <= edge + 49.0 for edge in [100.0, 200.0, 300.0, 400.0, 500.0]) else 0.0
            if prev_clk <= 0.45 < clk:
                flag = 1.0 if vin > 0.45 else 0.0
            rows.append({"time": time_ns * 1e-9, "vin": vin, "clk": clk, "flag": 0.0 if wrong else flag})
            prev_clk = clk
        return rows

    def clocked_rows(update_fn, input_fn, *, initial_out=0.0, initial_metric=0.0, wrong: bool = False) -> list[dict[str, float]]:
        rows: list[dict[str, float]] = []
        state: dict[str, float | int] = {"count": 0, "metric": initial_metric}
        out = initial_out
        metric = initial_metric
        prev_clk = 0.0
        for idx in range(551):
            time_ns = float(idx)
            clk = 1.0 if any(edge <= time_ns <= edge + 49.0 for edge in [100.0, 200.0, 300.0, 400.0, 500.0]) else 0.0
            vin, mode, rst = input_fn(time_ns)
            row = {"time": time_ns * 1e-9, "vin": vin, "clk": clk, "mode": mode, "rst": rst, "out": out, "metric": metric}
            if prev_clk <= 0.45 < clk:
                out, metric = update_fn(state, row)
            row["out"] = 0.0 if wrong else out
            row["metric"] = 0.0 if wrong else metric
            rows.append(row)
            prev_clk = clk
        return rows

    input_general = lambda t: (
        _task_input_from_segments(t, [(0.0, 0.25), (150.0, 0.85), (250.0, 0.35), (350.0, 0.75)]),
        0.0,
        0.9 if 350.0 <= t <= 429.0 else 0.0,
    )

    def clamp_update(_state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            return 0.0, 0.0
        out = min(0.9, max(0.0, row["vin"]))
        return out, out / 0.9

    def file_constant_update(out_value: float, metric_value: float):
        def update(_state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
            if row["rst"] > 0.45:
                return 0.0, 0.0
            return out_value, metric_value

        return update

    def profile_update(state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            state["count"] = 0
            state["metric"] = 0.0
            return 0.0, 0.0
        out = 0.9 if row["vin"] > 0.45 else 0.0
        metric = float(state["metric"]) + 0.01 * int(state["count"])
        state["metric"] = metric
        state["count"] = int(state["count"]) + 1
        return out, metric

    def count_threshold_update(state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            state["count"] = 0
            return 0.0, 0.0
        metric = float(state["count"])
        state["count"] = int(state["count"]) + 1
        return 0.9 if row["vin"] > 0.45 else 0.0, metric

    def config_update(state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            state["count"] = 0
            return 0.0, 0.0
        count = int(state["count"])
        state["count"] = count + 1
        if row["mode"] > 0.45:
            return 0.0 if row["vin"] > 0.45 else 0.9, float(count + 10)
        return 0.9 if row["vin"] > 0.45 else 0.0, float(count)

    def rdist_update(_state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            return 0.0, 0.0
        return row["vin"] + 0.03, 1.0

    def uniform_update(_state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            return 0.0, 0.0
        return row["vin"] + 0.01, 0.5

    def exp_update(_state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            return 0.0, 0.0
        out = math.exp(row["vin"])
        return out, out

    def gain_update(_state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            return 0.0, 0.0
        return 0.75 * row["vin"], 0.75

    def repeat_update(state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            state["count"] = 0
            return 0.0, 0.0
        acc = 4 * (int(state["count"]) + 1)
        state["count"] = int(state["count"]) + 1
        return 0.9 if acc > 4 else 0.0, float(acc)

    def multi_array_update(state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            state["count"] = 0
            return 0.0, 0.0
        metric = int(state["count"]) + 1
        state["count"] = int(state["count"]) + 1
        return 0.9 if metric > 2 else 0.0, float(metric)

    def nested_rows(*, wrong: bool = False) -> list[dict[str, float]]:
        rows: list[dict[str, float]] = []
        for idx in range(401):
            time_ns = float(idx)
            vin = _task_input_from_segments(
                time_ns,
                [(0.0, -0.75), (100.0, 0.25), (200.0, 0.90), (300.0, -0.10)],
            )
            out = vin * vin + 1.0
            rows.append({"time": time_ns * 1e-9, "vin": vin, "out": 0.0 if wrong else out})
        return rows

    assert sim.check_v3_419_wreal_logic_threshold_bridge(logic_bridge_rows())[0]
    assert not sim.check_v3_419_wreal_logic_threshold_bridge(logic_bridge_rows(wrong=True))[0]
    assert sim.check_v3_420_mixed_analog_digital_mode_latch(latch_rows())[0]
    assert not sim.check_v3_420_mixed_analog_digital_mode_latch(latch_rows(wrong=True))[0]
    assert sim.check_v3_457_nested_function_pipeline(nested_rows())[0]
    assert not sim.check_v3_457_nested_function_pipeline(nested_rows(wrong=True))[0]

    cases = [
        (sim.check_v3_421_task_local_variable_transform, clamp_update, input_general, 0.0, 0.0),
        (sim.check_v3_422_file_fscanf_table_stimulus, file_constant_update(0.7, 0.0), input_general, 0.7, 2.0),
        (sim.check_v3_423_file_profile_replay_controller, profile_update, input_general, 0.0, 1.0),
        (sim.check_v3_424_file_fscanf_multi_column_profile, file_constant_update(0.7, 0.5), input_general, 0.7, 3.0),
        (sim.check_v3_425_string_swrite_label_builder, count_threshold_update, input_general, 0.0, 0.0),
        (sim.check_v3_426_string_sformat_mode_tag, count_threshold_update, input_general, 0.0, 0.0),
        (sim.check_v3_427_string_formatted_metric_line, count_threshold_update, input_general, 0.0, 0.0),
        (sim.check_v3_428_string_mode_tagged_log, count_threshold_update, input_general, 0.0, 0.0),
        (
            sim.check_v3_429_string_config_label_select,
            config_update,
            lambda t: (
                _task_input_from_segments(t, [(0.0, 0.20), (150.0, 0.82), (250.0, 0.35), (350.0, 0.68)]),
                _task_input_from_segments(t, [(0.0, 1.0), (150.0, 0.0), (250.0, 1.0)]),
                0.9 if 350.0 <= t <= 429.0 else 0.0,
            ),
            0.0,
            0.0,
        ),
        (
            sim.check_v3_430_rdist_seed_reproducibility,
            rdist_update,
            lambda t: (
                _task_input_from_segments(t, [(0.0, 0.62), (150.0, 0.18), (250.0, 0.76), (350.0, 0.44)]),
                0.0,
                0.9 if 350.0 <= t <= 429.0 else 0.0,
            ),
            0.0,
            0.0,
        ),
        (
            sim.check_v3_445_limexp_soft_exponential,
            exp_update,
            lambda t: (
                _task_input_from_segments(t, [(0.0, -0.25), (150.0, 0.75), (250.0, 0.20), (350.0, -0.60)]),
                0.0,
                0.9 if 350.0 <= t <= 429.0 else 0.0,
            ),
            0.0,
            0.0,
        ),
        (sim.check_v3_446_fstrobe_file_line_writer, count_threshold_update, input_general, 0.0, 0.0),
        (sim.check_v3_447_display_warning_debug_log, count_threshold_update, input_general, 0.0, 0.0),
        (
            sim.check_v3_448_rdist_uniform_seeded_dither,
            uniform_update,
            lambda t: (
                _task_input_from_segments(t, [(0.0, 0.62), (150.0, 0.18), (250.0, 0.76), (350.0, 0.44)]),
                0.0,
                0.9 if 350.0 <= t <= 429.0 else 0.0,
            ),
            0.0,
            0.0,
        ),
        (
            sim.check_v3_454_multidimensional_array_state,
            multi_array_update,
            lambda t: (
                0.0,
                0.0,
                0.9 if 360.0 <= t <= 429.0 else 0.0,
            ),
            0.0,
            0.0,
        ),
        (sim.check_v3_433_preprocessor_ifndef_elsif_undef, gain_update, input_general, 0.0, 0.0),
        (sim.check_v3_434_repeat_loop_accumulator, repeat_update, input_general, 0.0, 0.0),
    ]
    for checker, update_fn, input_fn, initial_out, initial_metric in cases:
        assert checker(clocked_rows(update_fn, input_fn, initial_out=initial_out, initial_metric=initial_metric))[0]
        assert not checker(
            clocked_rows(update_fn, input_fn, initial_out=initial_out, initial_metric=initial_metric, wrong=True)
        )[0]


def test_v3_clocked_semantic_gap_checkers_follow_hidden_values() -> None:
    def input_fn(time_ns: float) -> tuple[float, float, float]:
        return (
            _task_input_from_segments(time_ns, [(0.0, 0.48), (100.0, 0.62), (200.0, 0.52), (300.0, 0.22), (400.0, 0.82)]),
            _task_input_from_segments(time_ns, [(0.0, 0.9), (100.0, 0.0), (200.0, 0.9), (400.0, 0.0)]),
            0.9 if 330.0 <= time_ns <= 389.0 else 0.0,
        )

    def threshold_update(_state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            return 0.0, 0.0
        eff_th = 0.5 if row["mode"] > 0.45 else 0.6
        return 0.9 if row["vin"] > eff_th else 0.0, eff_th

    def gain_update(_state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            return 0.0, 0.0
        effective = row["vin"] + (0.2 if row["mode"] > 0.45 else 0.0)
        raw = 1.25 * effective
        return min(0.9, max(0.0, raw)), raw

    def trig_update(_state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            return 0.0, 0.0
        phase = 2.0 * math.pi * row["vin"]
        if row["mode"] > 0.45:
            phase -= 0.5 * math.pi
        out = min(0.9, max(0.0, 0.45 + 0.25 * math.sin(phase)))
        return out, math.sqrt(abs(out))

    def random_rows(*, wrong: bool = False) -> list[dict[str, float]]:
        rows = _task_clocked_rows(
            lambda _state, row: (
                0.0 if row["rst"] > 0.45 else row["vin"] + 0.5 * (0.2 if row["mode"] > 0.45 else 0.1),
                0.0 if row["rst"] > 0.45 else (0.2 if row["mode"] > 0.45 else 0.1),
            ),
            input_fn,
            wrong=wrong,
        )
        return rows

    def guard_update(state: dict[str, float | int], row: dict[str, float]) -> tuple[float, float]:
        if row["rst"] > 0.45:
            state["out"] = 0.0
            return 0.0, 0.0
        if row["mode"] > 0.45:
            out = min(0.9, max(0.0, row["vin"]))
            state["out"] = out
            return out, 0.8
        return float(state.get("out", 0.0)), 0.2

    cases = [
        (sim.check_v3_336_directive_configurable_threshold, threshold_update),
        (sim.check_v3_337_parameter_range_limited_gain, gain_update),
        (sim.check_v3_338_math_trig_envelope_detector, trig_update),
        (sim.check_v3_340_bound_step_clock_guard, guard_update),
    ]
    for checker, update_fn in cases:
        assert checker(_task_clocked_rows(update_fn, input_fn))[0]
        assert not checker(_task_clocked_rows(update_fn, input_fn, wrong=True))[0]

    assert sim.check_v3_339_random_seeded_dither_source(random_rows())[0]
    assert not sim.check_v3_339_random_seeded_dither_source(random_rows(wrong=True))[0]


def test_v3_event_or_timer_checker_follows_hidden_events() -> None:
    def rows(*, wrong: bool = False) -> list[dict[str, float]]:
        output_rows: list[dict[str, float]] = []
        out = 0.0
        metric = 0.0
        prev_clk = 0.0
        next_timer = 1.0
        for idx in range(0, 5601, 10):
            time_ns = idx / 1000.0
            vin = _task_input_from_segments(time_ns, [(0.0, 0.35), (1.7, 0.75), (3.7, 0.15)])
            clk = 1.0 if 2.2 <= time_ns <= 2.7 or 4.2 <= time_ns <= 4.7 else 0.0
            while time_ns + 1e-6 >= next_timer:
                metric += 1.0
                out = vin
                next_timer += 1.0
            if prev_clk <= 0.45 < clk:
                metric += 1.0
                out = vin
            output_rows.append(
                {
                    "time": time_ns * 1e-9,
                    "vin": vin,
                    "clk": clk,
                    "out": 0.0 if wrong else out,
                    "metric": 0.0 if wrong else metric,
                }
            )
            prev_clk = clk
        return output_rows

    assert sim.check_v3_456_event_or_cross_timer(rows())[0]
    assert not sim.check_v3_456_event_or_cross_timer(rows(wrong=True))[0]


def test_v3_custom_nature_checker_tracks_input_potential() -> None:
    good_rows = [
        {"time": idx * 1e-9, "a": value, "y": value}
        for idx, value in enumerate([0.0, 0.2, 0.7, 0.4, 0.9, 0.1, 0.55, 0.8] * 3)
    ]
    zero_rows = [{**row, "y": 0.0} for row in good_rows]
    offset_rows = [{**row, "y": row["a"] + 0.12} for row in good_rows]

    assert sim.check_v3_450_custom_nature_discipline_voltage(good_rows)[0]
    assert not sim.check_v3_450_custom_nature_discipline_voltage(zero_rows)[0]
    assert not sim.check_v3_450_custom_nature_discipline_voltage(offset_rows)[0]


def test_v3_connectmodule_checkers_track_input_potential() -> None:
    good_rows = [
        {"time": idx * 1e-9, "a": value, "y": value}
        for idx, value in enumerate([0.65, 0.2, 0.85, 0.1, 0.5, 0.9, 0.15, 0.7] * 3)
    ]
    threshold_rows = [{**row, "y": 0.9 if row["a"] > 0.55 else 0.0} for row in good_rows]

    assert sim.check_v3_451_connectmodule_electrical_bridge(good_rows)[0]
    assert sim.check_v3_452_connectrules_electrical_map(good_rows)[0]
    assert not sim.check_v3_451_connectmodule_electrical_bridge(threshold_rows)[0]
    assert not sim.check_v3_452_connectrules_electrical_map(threshold_rows)[0]


def test_v3_recursive_function_checker_follows_hidden_depth_override() -> None:
    def rows(*, stim: float, out: float) -> list[dict[str, float]]:
        return [
            {"time": 0.0, "stim": stim, "out": out},
            {"time": 10e-9, "stim": stim, "out": out},
            {"time": 20e-9, "stim": stim, "out": out},
        ]

    assert sim.check_v3_458_recursive_function_candidate(rows(stim=0.0, out=6.0))[0]
    assert sim.check_v3_458_recursive_function_candidate(rows(stim=1.0, out=24.0))[0]
    assert not sim.check_v3_458_recursive_function_candidate(rows(stim=1.0, out=6.0))[0]
    assert not sim.check_v3_458_recursive_function_candidate(rows(stim=0.0, out=24.0))[0]


def test_v3_above_last_crossing_checkers_follow_hidden_events() -> None:
    def make_rows(vin_segments, rst_segments, model_fn, *, stop_ns: int = 760, wrong: bool = False) -> list[dict[str, float]]:
        rows: list[dict[str, float]] = []
        state: dict[str, float | int] = {}
        prev_vin = _task_input_from_segments(0.0, vin_segments)
        prev_rst = _task_input_from_segments(0.0, rst_segments)
        for idx in range(stop_ns + 1):
            time_ns = float(idx)
            row = {
                "time": time_ns * 1e-9,
                "vin": _task_input_from_segments(time_ns, vin_segments),
                "clk": 0.0,
                "mode": 0.0,
                "rst": _task_input_from_segments(time_ns, rst_segments),
                "out": 0.0,
                "metric": 0.0,
            }
            out, metric = model_fn(state, row, prev_vin, prev_rst)
            row["out"] = 0.0 if wrong else out
            row["metric"] = 0.0 if wrong else metric
            rows.append(row)
            prev_vin = row["vin"]
            prev_rst = row["rst"]
        return rows

    def latch_model(metric_fn):
        def model(state, row, prev_vin, prev_rst):
            if "state" not in state:
                state.update({"state": 0, "last_t": -1.0, "prev_t": -1.0, "metric": 0.0})
            if prev_rst <= 0.45 < row["rst"]:
                state.update({"state": 0, "last_t": -1.0, "prev_t": -1.0, "metric": 0.0})
            if prev_vin <= 0.45 < row["vin"]:
                state["state"] = 1
                state["prev_t"] = state["last_t"]
                state["last_t"] = row["time"]
                if state["prev_t"] > 0.0:
                    state["metric"] = metric_fn(state["last_t"] - state["prev_t"])
                else:
                    state["metric"] = 0.0
            return (0.9 if state["state"] else 0.0), float(state["metric"])

        return model

    def period_model(state, row, prev_vin, prev_rst):
        if "last_t" not in state:
            state.update({"last_t": -1.0, "prev_t": -1.0, "out": 0.0, "metric": 0.0})
        if prev_rst <= 0.45 < row["rst"]:
            state.update({"last_t": -1.0, "prev_t": -1.0, "out": 0.0, "metric": 0.0})
        if prev_vin <= 0.45 < row["vin"]:
            state["prev_t"] = state["last_t"]
            state["last_t"] = row["time"]
            if state["prev_t"] > 0.0:
                state["out"] = min(0.9, max(0.0, 0.9 * (state["last_t"] - state["prev_t"]) / 400e-9))
                state["metric"] = 0.9
            else:
                state["out"] = 0.0
                state["metric"] = 0.0
        return float(state["out"]), float(state["metric"])

    def age_model(state, row, prev_vin, prev_rst):
        if "next_timer" not in state:
            state.update({"active": 0, "last_t": -1.0, "out": 0.0, "metric": 0.0, "next_timer": 0.0})
        if prev_rst <= 0.45 < row["rst"]:
            state.update({"active": 0, "last_t": -1.0, "out": 0.0, "metric": 0.0})
        if prev_vin <= 0.45 < row["vin"]:
            state["active"] = 1
            state["last_t"] = row["time"]
        while row["time"] + 1e-15 >= state["next_timer"]:
            if state["active"]:
                age = state["next_timer"] - state["last_t"]
                state["out"] = min(0.9, max(0.0, 0.9 * age / 300e-9))
                state["metric"] = 0.9 if age <= 150e-9 else 0.0
            state["next_timer"] += 50e-9
        return float(state["out"]), float(state["metric"])

    def peak_model(state, row, prev_vin, prev_rst):
        if "next_timer" not in state:
            state.update({"active": 0, "peak": 0.0, "metric": 0.0, "next_timer": 0.0})
        if prev_rst <= 0.45 < row["rst"]:
            state.update({"active": 0, "peak": 0.0, "metric": 0.0})
        if prev_vin <= 0.45 < row["vin"]:
            state["active"] = 1
        while row["time"] + 1e-15 >= state["next_timer"]:
            if state["active"]:
                state["peak"] = min(0.9, max(0.0, max(state["peak"], row["vin"])))
                state["metric"] = state["peak"]
            state["next_timer"] += 50e-9
        return (0.9 if state["active"] else 0.0), float(state["metric"])

    cases = [
        (
            sim.check_v3_331_above_threshold_latch,
            [(0.0, 0.1), (80.0, 0.75), (151.0, 0.1), (260.0, 0.82), (341.0, 0.1), (580.0, 0.78)],
            [(0.0, 0.0), (420.0, 0.9), (450.0, 0.0)],
            latch_model(lambda period: 0.9 if period < 250e-9 else 0.0),
            700,
        ),
        (
            sim.check_v3_332_above_window_qualifier,
            [(0.0, 0.1), (90.0, 0.76), (161.0, 0.1), (240.0, 0.80), (331.0, 0.1), (640.0, 0.78)],
            [(0.0, 0.0), (420.0, 0.9), (450.0, 0.0)],
            latch_model(lambda period: 0.9 if 120e-9 <= period <= 260e-9 else 0.0),
            760,
        ),
        (
            sim.check_v3_333_last_crossing_period_meter,
            [(0.0, 0.1), (90.0, 0.8), (161.0, 0.1), (260.0, 0.8), (351.0, 0.1), (560.0, 0.8), (651.0, 0.1), (820.0, 0.8)],
            [(0.0, 0.0), (720.0, 0.9), (750.0, 0.0)],
            period_model,
            900,
        ),
        (
            sim.check_v3_334_last_crossing_edge_age,
            [(0.0, 0.1), (80.0, 0.8), (161.0, 0.1), (460.0, 0.8), (561.0, 0.1)],
            [(0.0, 0.0), (670.0, 0.9), (700.0, 0.0)],
            age_model,
            800,
        ),
        (
            sim.check_v3_335_above_resettable_peak_marker,
            [(0.0, 0.1), (80.0, 0.50), (260.0, 0.85), (351.0, 0.25), (560.0, 0.65)],
            [(0.0, 0.0), (420.0, 0.9), (450.0, 0.0)],
            peak_model,
            720,
        ),
    ]

    for checker, vin_segments, rst_segments, model_fn, stop_ns in cases:
        assert checker(make_rows(vin_segments, rst_segments, model_fn, stop_ns=stop_ns))[0]
        assert not checker(make_rows(vin_segments, rst_segments, model_fn, stop_ns=stop_ns, wrong=True))[0]


def test_v3_idtmod_phase_checkers_follow_hidden_waveforms() -> None:
    def base_rows(vin_segments, mode_segments, rst_segments, clk_segments=None, *, stop_ns: int = 900) -> list[dict[str, float]]:
        rows: list[dict[str, float]] = []
        for idx in range(stop_ns + 1):
            time_ns = float(idx)
            rows.append(
                {
                    "time": time_ns * 1e-9,
                    "vin": _task_input_from_segments(time_ns, vin_segments),
                    "clk": _task_input_from_segments(time_ns, clk_segments or [(0.0, 0.0)]),
                    "mode": _task_input_from_segments(time_ns, mode_segments),
                    "rst": _task_input_from_segments(time_ns, rst_segments),
                    "out": 0.0,
                    "metric": 0.0,
                }
            )
        return rows

    def fill_continuous(rows, freq_fn, metric_fn, *, modulus=1.0, wrong: bool = False):
        phases = sim._v3_integrated_mod_phase_values(rows, freq_fn=freq_fn, modulus=modulus)
        for row, phase in zip(rows, phases):
            if row["rst"] > 0.45:
                out = 0.0
                metric = 0.0
            else:
                out = 0.9 * phase / modulus
                metric = metric_fn(row, phase)
            row["out"] = 0.0 if wrong else out
            row["metric"] = 0.0 if wrong else metric
        return rows

    rows_327 = lambda wrong=False: fill_continuous(
        base_rows(
            [(0.0, 0.30), (250.0, 0.70), (550.0, 0.45)],
            [(0.0, 0.55)],
            [(0.0, 0.9), (80.0, 0.0), (650.0, 0.9), (700.0, 0.0)],
        ),
        lambda row: 0.75e6 + 1.5e6 * row["vin"],
        lambda row, phase: 0.9 if phase > row["mode"] else 0.0,
        wrong=wrong,
    )
    rows_328 = lambda wrong=False: fill_continuous(
        base_rows(
            [(0.0, 0.25), (300.0, 0.55), (600.0, 0.15)],
            [(0.0, 0.0), (350.0, 0.9), (750.0, 0.0)],
            [(0.0, 0.0)],
        ),
        lambda row: 0.5e6 + (2.0e6 if row["mode"] > 0.45 else 1.0e6) * row["vin"],
        lambda _row, phase: 0.9 if phase > 0.75 else 0.0,
        wrong=wrong,
    )
    rows_329 = lambda wrong=False: fill_continuous(
        base_rows(
            [(0.0, 0.20), (200.0, 0.80), (500.0, 0.35)],
            [(0.0, 0.9), (250.0, 0.0), (550.0, 0.9)],
            [(0.0, 0.0)],
            stop_ns=750,
        ),
        lambda row: 0.5e6 + 0.5e6 * row["vin"],
        lambda row, phase: 0.9 if phase < (0.05 if row["mode"] > 0.45 else 0.025) else 0.0,
        modulus=0.25,
        wrong=wrong,
    )

    def rows_330(wrong: bool = False):
        rows = base_rows(
            [(0.0, 0.20), (250.0, 0.65), (550.0, 0.35)],
            [(0.0, 0.55)],
            [(0.0, 0.0)],
            [
                (0.0, 0.0),
                (120.0, 0.9),
                (146.0, 0.0),
                (280.0, 0.9),
                (306.0, 0.0),
                (460.0, 0.9),
                (486.0, 0.0),
                (640.0, 0.9),
                (666.0, 0.0),
                (740.0, 0.9),
                (766.0, 0.0),
            ],
            stop_ns=780,
        )
        phases = sim._v3_integrated_mod_phase_values(
            rows,
            freq_fn=lambda row: 1.25e6 + 0.5e6 * row["vin"],
            modulus=1.0,
        )
        sample = 0.0
        metric = 0.0
        prev_clk = rows[0]["clk"]
        for row, phase in zip(rows, phases):
            if prev_clk <= 0.45 < row["clk"]:
                sample = phase
                metric = 0.9 if sample > row["mode"] else 0.0
            row["out"] = 0.0 if wrong else 0.9 * sample
            row["metric"] = 0.0 if wrong else metric
            prev_clk = row["clk"]
        return rows

    cases = [
        (sim.check_v3_327_idtmod_wrapped_ramp_source, rows_327),
        (sim.check_v3_328_idtmod_frequency_control, rows_328),
        (sim.check_v3_329_idtmod_modulo_phase_marker, rows_329),
        (sim.check_v3_330_idtmod_clock_phase_meter, rows_330),
    ]
    for checker, make_rows in cases:
        assert checker(make_rows())[0]
        assert not checker(make_rows(wrong=True))[0]


def _converter_front_end_chain_rows(*, mode: str = "good") -> list[dict[str, float]]:
    edges_ns = [5.0 + 20.0 * idx for idx in range(9)]
    aperture_levels = [0.18, 0.72, 0.32, 0.78, 0.40, 0.70, 0.25, 0.65, 0.38]
    pre_levels = [0.18, 0.18, 0.72, 0.32, 0.78, 0.40, 0.70, 0.25, 0.65]
    rows: list[dict[str, float]] = []

    def add(time_ns: float, clk: float, vin: float, vout: float, valid: float, coarse: float) -> None:
        rows.append(
            {
                "time": time_ns * 1e-9,
                "clk": clk,
                "vin": vin,
                "vout": vout,
                "valid": valid,
                "coarse": coarse,
            }
        )

    held = 0.0
    coarse = 0.0
    for idx, edge_ns in enumerate(edges_ns):
        pre = pre_levels[idx]
        aperture = aperture_levels[idx]
        sampled = pre if mode == "sample_edge_not_aperture" else aperture
        coarse = 0.9 if sampled > 0.45 else 0.0
        if mode == "wrong_coarse" and idx in {1, 3}:
            coarse = 0.0 if coarse > 0.45 else 0.9

        add(edge_ns, 0.45, pre, held, 0.0, coarse)
        add(edge_ns + 0.001, 0.9, pre, held, 0.0, coarse)
        add(edge_ns + 0.2, 0.9, aperture, held, 0.0, coarse)
        add(edge_ns + 0.8, 0.9, aperture, sampled, 0.9, coarse)
        add(edge_ns + 1.0, 0.9, aperture, sampled, 0.9, coarse)
        add(edge_ns + 3.5, 0.9, aperture, sampled, 0.9 if mode == "valid_stuck_high" else 0.0, coarse)
        add(edge_ns + 8.0, 0.0, aperture, sampled, 0.0, coarse)

        held = sampled
        if idx + 1 < len(edges_ns):
            next_edge = edges_ns[idx + 1]
            window_points = [edge_ns + offset for offset in (9, 10, 11, 12, 13, 14, 15, 16, 17, 18)]
            for point_idx, time_ns in enumerate(window_points):
                if time_ns >= next_edge - 1.5:
                    continue
                if held > 0.55:
                    droop = 0.0 if mode == "no_hold_droop" else 0.006 * point_idx
                    vout = held - droop
                else:
                    vout = held
                add(time_ns, 0.0, aperture, vout, 0.0, coarse)
            if held > 0.55 and mode != "no_hold_droop":
                held = max(0.0, held - 0.006 * 8)

    return sorted(rows, key=lambda row: row["time"])


def test_converter_front_end_checker_requires_aperture_coarse_valid_and_droop() -> None:
    assert sim.check_release_converter_front_end_chain(_converter_front_end_chain_rows())[0]
    assert not sim.check_release_converter_front_end_chain(
        _converter_front_end_chain_rows(mode="sample_edge_not_aperture")
    )[0]
    assert not sim.check_release_converter_front_end_chain(
        _converter_front_end_chain_rows(mode="wrong_coarse")
    )[0]
    assert not sim.check_release_converter_front_end_chain(
        _converter_front_end_chain_rows(mode="valid_stuck_high")
    )[0]
    assert not sim.check_release_converter_front_end_chain(
        _converter_front_end_chain_rows(mode="no_hold_droop")
    )[0]


def _ct04_common_vin(time_ns: float) -> float:
    if time_ns < 8.0:
        return 0.45
    if time_ns < 12.0:
        return 0.45 + (0.9 - 0.45) * (time_ns - 8.0) / 4.0
    if time_ns < 28.0:
        return 0.9
    if time_ns < 31.0:
        return 0.9 + (0.45 - 0.9) * (time_ns - 28.0) / 3.0
    if time_ns < 37.0:
        return 0.45
    if time_ns < 42.0:
        return 0.45 + (0.1 - 0.45) * (time_ns - 37.0) / 5.0
    if time_ns < 58.0:
        return 0.1
    if time_ns < 61.0:
        return 0.1 + (0.45 - 0.1) * (time_ns - 58.0) / 3.0
    if time_ns < 67.0:
        return 0.45
    if time_ns < 72.0:
        return 0.45 + (0.85 - 0.45) * (time_ns - 67.0) / 5.0
    return 0.85


def _ct04_rows(kind: str, *, mode: str = "good") -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for idx in range(161):
        time_ns = idx * 0.5
        clk = 0.9 if (time_ns % 2.0) < 1.0 else 0.0
        rst = 0.9 if time_ns <= 2.0 else 0.0
        vin = _ct04_common_vin(time_ns)
        out = 0.45
        metric = 0.45
        extra: dict[str, float] = {}

        if kind == "gain":
            target = 1.8 * (vin - 0.45) + 0.45
            clipped = max(0.0, min(0.9, target))
            out = target if mode == "unclamped" else clipped
            metric = 0.0 if mode == "flat_metric" else (0.9 if clipped != target else 0.0)
            if rst > 0.45:
                out = 0.45
                metric = 0.0
        elif kind == "two_pole":
            if 14.0 <= time_ns <= 16.0:
                out, metric = 0.56, 0.62
            elif 24.0 <= time_ns <= 28.0:
                out, metric = 0.76, 0.54
            elif 44.0 <= time_ns <= 52.0:
                out, metric = 0.40, 0.32
            elif 54.0 <= time_ns <= 58.0:
                out, metric = 0.22, 0.36
            if mode == "single_pole":
                if 14.0 <= time_ns <= 16.0:
                    out = 0.78
                metric = 0.45
        elif kind == "soft_limiter":
            if 16.0 <= time_ns <= 24.0:
                out, metric = 0.80, 0.65
            elif 31.0 <= time_ns <= 36.0:
                out, metric = 0.51, 0.65
            elif 46.0 <= time_ns <= 55.0:
                out, metric = 0.12, 0.25
            elif 61.0 <= time_ns <= 66.0:
                out, metric = 0.39, 0.25
            if mode == "memoryless":
                if 31.0 <= time_ns <= 36.0 or 61.0 <= time_ns <= 66.0:
                    out, metric = 0.45, 0.45
        elif kind == "amp_filter":
            if 12.5 <= time_ns <= 15.0:
                out, metric = 0.70, 0.90
                extra.update({"preamp_mon": 0.90, "filt1_mon": 0.76, "filt2_mon": 0.70})
            elif 24.0 <= time_ns <= 28.0:
                out, metric = 0.84, 0.90
                extra.update({"preamp_mon": 0.90, "filt1_mon": 0.86, "filt2_mon": 0.84})
            elif 33.0 <= time_ns <= 36.0:
                out, metric = 0.70, 0.45
                extra.update({"preamp_mon": 0.45, "filt1_mon": 0.58, "filt2_mon": 0.70})
            elif 46.0 <= time_ns <= 53.5:
                out, metric = 0.42, 0.0
                extra.update({"preamp_mon": 0.0, "filt1_mon": 0.20, "filt2_mon": 0.38})
            elif 54.0 <= time_ns <= 58.0:
                out, metric = 0.25, 0.0
                extra.update({"preamp_mon": 0.0, "filt1_mon": 0.12, "filt2_mon": 0.25})
            else:
                extra.update({"preamp_mon": metric, "filt1_mon": out, "filt2_mon": out})
            extra["settle_metric"] = 0.9 if 24.0 <= time_ns <= 28.0 or 54.0 <= time_ns <= 58.0 else 0.0
            if mode == "direct_gain":
                out = metric
        else:
            raise ValueError(kind)

        rows.append(
            {"time": time_ns * 1e-9, "clk": clk, "rst": rst, "vin": vin, "out": out, "metric": metric, **extra}
        )
    return rows


def _rectifier_envelope_rows(*, mode: str = "good") -> list[dict[str, float]]:
    knots = [
        (0.0, 0.45),
        (8.0, 0.75),
        (16.0, 0.45),
        (24.0, 0.15),
        (32.0, 0.45),
        (42.0, 0.85),
        (54.0, 0.45),
        (66.0, 0.35),
        (78.0, 0.45),
        (90.0, 0.45),
    ]

    def interp(time_ns: float) -> float:
        for (t0, v0), (t1, v1) in zip(knots, knots[1:]):
            if t0 <= time_ns <= t1:
                frac = (time_ns - t0) / (t1 - t0)
                return v0 + frac * (v1 - v0)
        return knots[-1][1]

    rows: list[dict[str, float]] = []
    env = 0.45
    for idx in range(181):
        time_ns = idx * 0.5
        rst = 0.9 if time_ns <= 2.0 else 0.0
        clk = 0.9 if (time_ns % 2.0) < 1.0 else 0.0
        vin = interp(time_ns)
        rect = min(0.9, 0.45 + abs(vin - 0.45))
        if mode == "half_wave":
            rect = vin if vin > 0.45 else 0.45

        if rst > 0.45:
            env = 0.45
        elif mode == "no_envelope":
            env = rect
        else:
            env = max(rect, max(0.45, env - 0.006))
        metric = 0.9 if env - rect > 0.03 else 0.0
        rows.append(
            {
                "time": time_ns * 1e-9,
                "clk": clk,
                "rst": rst,
                "vin": vin,
                "rect": rect,
                "env": env,
                "metric": metric,
            }
        )
    return rows


def test_precision_rectifier_envelope_checker_requires_full_wave_and_hold() -> None:
    assert sim.check_precision_rectifier_envelope_detector(_rectifier_envelope_rows())[0]
    assert not sim.check_precision_rectifier_envelope_detector(_rectifier_envelope_rows(mode="half_wave"))[0]
    assert not sim.check_precision_rectifier_envelope_detector(_rectifier_envelope_rows(mode="no_envelope"))[0]


def test_precision_rectifier_streaming_checker_matches_row_based_all_release_forms(tmp_path: Path) -> None:
    task_ids = [
        "vbr1_l1_precision_rectifier_envelope_detector",
        "vbr1_l1_precision_rectifier_envelope_detector_dut",
        "vbr1_l1_precision_rectifier_envelope_detector_tb",
        "vbr1_l1_precision_rectifier_envelope_detector_bugfix",
        "vbr1_l1_precision_rectifier_envelope_detector_e2e",
    ]
    rows = _rectifier_envelope_rows()
    csv_path = tmp_path / "rectifier.csv"
    _write_rows_csv(csv_path, rows, ["time", "clk", "rst", "vin", "rect", "env", "metric"])

    for task_id in task_ids:
        row_result, stream_result = _evaluate_row_and_streaming(task_id, csv_path)
        assert stream_result[0] == row_result[0], task_id
        assert stream_result[1] == [f"streaming_checker:{row_result[1][0]}"], task_id


def _sar_adc_dac_rows(*, mode: str = "good") -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    vdd = 0.9

    def append_row(
        time_s: float,
        clks: float,
        rst_n: float,
        vin: float,
        vin_sh: float,
        code: int,
        vout: float,
        *,
        bit_index: float = 0.0,
        trial_vdac: float = 0.0,
        cmp_decision: float = 0.0,
        conv_done: float = 0.0,
        vin_sample: float | None = None,
    ) -> None:
        row = {
            "time": time_s,
            "vin": vin,
            "vin_sh": vin_sh,
            "clks": clks,
            "rst_n": rst_n,
            "vout": vout,
            "bit_index": bit_index,
            "trial_code_mon": trial_vdac,
            "trial_vdac": trial_vdac,
            "cmp_decision": cmp_decision,
            "conv_done": conv_done,
            "vin_sample": vin if vin_sample is None else vin_sample,
        }
        for bit in range(8):
            row[f"dout_{bit}"] = vdd if (code >> bit) & 1 else 0.0
        rows.append(row)

    for cycle in range(502):
        base = cycle * 20.0e-9
        rst_n = vdd if cycle >= 4 else 0.0
        sample_time = base + 1.0e-9
        vin = 0.45 + 0.45 * math.sin(2.0 * math.pi * 100.0e3 * sample_time)
        vin = max(0.0, min(vdd, vin))
        code = max(0, min(255, int(math.floor(vin / vdd * 255.0))))
        vout = code / 255.0 * vdd

        if mode == "vout_tracks_input_but_code_fake":
            code = (cycle * 37) % 256
            vout = vin
        elif mode == "code_offset":
            code = max(0, min(255, code + 40))
            vout = code / 255.0 * vdd
        elif mode != "good":
            raise ValueError(mode)

        append_row(base + 0.2e-9, 0.0, rst_n, vin, vin, code, vout)
        append_row(base + 1.0e-9, vdd, rst_n, vin, vin, code, vout)
        append_row(base + 2.0e-9, vdd, rst_n, vin, vin, code, vout, conv_done=vdd)
        for trial_bit in range(1, 9):
            trial_vdac = trial_bit / 9.0 * vdd
            append_row(
                base + (2.5 + 0.5 * trial_bit) * 1.0e-9,
                vdd,
                rst_n,
                vin,
                vin,
                code,
                vout,
                bit_index=trial_bit / 8.0 * 0.9,
                trial_vdac=trial_vdac,
                cmp_decision=vdd if vin >= trial_vdac else 0.0,
                conv_done=0.0,
                vin_sample=vin,
            )
        append_row(base + 11.0e-9, 0.0, rst_n, vin, vin, code, vout)

    return rows


def test_sar_adc_dac_checker_requires_code_dac_sample_alignment() -> None:
    assert sim.check_sar_adc_dac_weighted_8b(_sar_adc_dac_rows())[0]
    assert not sim.check_sar_adc_dac_weighted_8b(
        _sar_adc_dac_rows(mode="vout_tracks_input_but_code_fake")
    )[0]
    assert not sim.check_sar_adc_dac_weighted_8b(_sar_adc_dac_rows(mode="code_offset"))[0]


def test_csv_checker_runtime_maps_common_signal_aliases(tmp_path: Path) -> None:
    csv_path = tmp_path / "tran.csv"
    csv_path.write_text("time,V(vin),dout[0]\n0.0,0.125,0.9\n", encoding="utf-8")

    runtime = sim.CsvCheckerRuntime(csv_path)
    assert runtime.missing({"time", "vin", "dout_0"}) == []
    row = next(runtime.rows())
    assert runtime.float(row, "vin") == 0.125
    assert runtime.float(row, "dout_0") == 0.9


def test_release_sar_streaming_checker_matches_row_based(tmp_path: Path) -> None:
    rows = _sar_adc_dac_rows()
    csv_path = tmp_path / "tran.csv"
    fieldnames = [
        "time",
        "vin",
        "vin_sh",
        "clks",
        "vout",
        "rst_n",
        "bit_index",
        "trial_code_mon",
        "trial_vdac",
        "cmp_decision",
        "conv_done",
        "vin_sample",
    ] + [f"dout_{idx}" for idx in range(8)]
    with csv_path.open("w", encoding="utf-8") as f:
        f.write(",".join(fieldnames) + "\n")
        for row in rows:
            values = []
            for name in fieldnames:
                source = name.replace("[", "_").replace("]", "")
                values.append(str(row[source]))
            f.write(",".join(values) + "\n")

    try:
        os.environ["VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS"] = "1"
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)
        row_score, row_notes = sim.evaluate_behavior("vbr1_l2_weighted_sar_adc_dac_loop_tb", csv_path)

        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ["VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS"] = "1"
        stream_score, stream_notes = sim.evaluate_behavior("vbr1_l2_weighted_sar_adc_dac_loop_tb", csv_path)
        e2e_score, e2e_notes = sim.evaluate_behavior("vbr1_l2_weighted_sar_adc_dac_loop_e2e", csv_path)
    finally:
        os.environ.pop("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS", None)
        os.environ.pop("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS", None)

    assert stream_score == row_score
    assert stream_notes[0] == "streaming_checker:public_contract"
    assert stream_notes[1].startswith("streaming_checker:done_samples=")
    assert "avg_quant_err=" in stream_notes[1]
    assert e2e_score == row_score
    assert e2e_notes[0] == "streaming_checker:public_contract"
    assert e2e_notes[1].startswith("streaming_checker:done_samples=")
    assert "avg_quant_err=" in e2e_notes[1]


def _converter_static_linearity_rows(*, mode: str = "good") -> list[dict[str, float]]:
    recon_table = {
        0: 0.000,
        1: 0.055,
        2: 0.118,
        3: 0.182,
        4: 0.245,
        5: 0.303,
        6: 0.366,
        7: 0.428,
        8: 0.491,
        9: 0.553,
        10: 0.612,
        11: 0.674,
        12: 0.735,
        13: 0.798,
        14: 0.855,
        15: 0.900,
    }
    rows: list[dict[str, float]] = []
    code_int = 0
    recon = 0.0
    dnl = 0.45
    inl = 0.45
    prev_valid = False
    prev_code = 0
    prev_recon = 0.0
    prev_clk = 0.0
    for idx in range(385):
        time_ns = idx * 0.25
        rst = 0.9 if time_ns <= 2.0 else 0.0
        clk_phase = (time_ns - 1.0) % 4.0
        clk = 0.9 if 0.0 <= clk_phase < 2.0 else 0.0
        vin = min(0.9, max(0.0, 0.9 * max(time_ns - 4.0, 0.0) / 84.0))
        if prev_clk <= 0.45 < clk:
            if rst > 0.45:
                code_int = 0
                recon = 0.0
                dnl = 0.45
                inl = 0.45
                prev_valid = False
                prev_code = 0
                prev_recon = 0.0
            else:
                code_int = max(0, min(15, round((vin / 0.9) * 15.0)))
                recon = 0.06 * code_int if mode == "ideal_converter" else recon_table[code_int]
                inl = max(0.05, min(0.85, 0.45 + 3.0 * (recon - 0.06 * code_int)))
                if prev_valid and code_int > prev_code:
                    ideal_step = 0.06 * (code_int - prev_code)
                    dnl = max(0.05, min(0.85, 0.45 + 4.0 * ((recon - prev_recon) - ideal_step)))
                else:
                    dnl = 0.45
                if mode == "flat_metrics":
                    dnl = 0.45
                    inl = 0.45
                elif mode == "fake_metrics":
                    dnl = 0.30 + 0.015 * code_int
                    inl = 0.60 - 0.008 * code_int
                prev_code = code_int
                prev_recon = recon
                prev_valid = True
        prev_clk = clk
        rows.append(
            {
                "time": time_ns * 1e-9,
                "clk": clk,
                "rst": rst,
                "vin": vin,
                "code": 0.06 * code_int,
                "recon": recon,
                "dnl": dnl,
                "inl": inl,
            }
        )
    return rows


def test_converter_static_linearity_checker_requires_linearity_metrics() -> None:
    assert sim.check_converter_static_linearity_measurement_flow(_converter_static_linearity_rows())[0]
    assert not sim.check_converter_static_linearity_measurement_flow(
        _converter_static_linearity_rows(mode="ideal_converter")
    )[0]
    assert not sim.check_converter_static_linearity_measurement_flow(
        _converter_static_linearity_rows(mode="flat_metrics")
    )[0]
    assert not sim.check_converter_static_linearity_measurement_flow(
        _converter_static_linearity_rows(mode="fake_metrics")
    )[0]


def _programmable_stimulus_sequencer_rows(*, mode: str = "chirp") -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    prbs_state = 7
    burst_level = 0.45
    for idx in range(361):
        time_ns = idx * 0.25
        time_s = time_ns * 1e-9
        rst = 0.9 if time_ns <= 2.0 else 0.0
        clk = 0.9 if (time_ns % 2.0) < 1.0 else 0.0
        mode_v = 0.0 if time_ns < 26.0 else 0.45 if time_ns < 62.0 else 0.9
        gate = 0.9 if 66.0 <= time_ns < 76.0 or 79.5 <= time_ns <= 88.0 else 0.0

        if mode_v < 0.30:
            ramp_frac = min(1.0, max(0.0, (time_s - 3.0e-9) / 23.0e-9))
            out = 0.18 + 0.27 * ramp_frac
            metric = 0.20
        elif mode_v < 0.60:
            sweep_t = min(36.0e-9, max(0.0, time_s - 26.0e-9))
            if mode == "fixed_sine":
                phase = 2.0 * math.pi * 82.0e6 * sweep_t
            else:
                sweep_k = (116.666666e6 - 50.0e6) / 36.0e-9
                phase = 2.0 * math.pi * (50.0e6 * sweep_t + 0.5 * sweep_k * sweep_t * sweep_t)
            out = 0.45 + 0.15 * math.sin(phase)
            metric = 0.50
        elif gate > 0.45:
            if idx % 8 == 0:
                feedback = ((prbs_state >> 2) & 1) ^ ((prbs_state >> 1) & 1)
                prbs_state = ((prbs_state & 3) << 1) | feedback
                burst_level = 0.62 if (prbs_state & 1) else 0.28
            out = burst_level
            metric = 0.80
        else:
            out = 0.45
            metric = 0.65
        if rst > 0.45:
            out = 0.45
            metric = 0.0
        rows.append(
            {
                "time": time_s,
                "clk": clk,
                "rst": rst,
                "mode": mode_v,
                "gate": gate,
                "out": out,
                "metric": metric,
            }
        )
    return rows


def test_programmable_stimulus_checker_requires_chirp_sweep_not_fixed_sine() -> None:
    assert sim.check_programmable_stimulus_sequencer(_programmable_stimulus_sequencer_rows())[0]
    assert not sim.check_programmable_stimulus_sequencer(
        _programmable_stimulus_sequencer_rows(mode="fixed_sine")
    )[0]


def test_programmable_stimulus_streaming_checker_matches_row_based_all_release_forms(tmp_path: Path) -> None:
    task_ids = [
        "vbr1_l2_programmable_stimulus_sequencer",
        "vbr1_l2_programmable_stimulus_sequencer_dut",
        "vbr1_l2_programmable_stimulus_sequencer_tb",
        "vbr1_l2_programmable_stimulus_sequencer_bugfix",
        "vbr1_l2_programmable_stimulus_sequencer_e2e",
    ]
    rows = _programmable_stimulus_sequencer_rows()
    csv_path = tmp_path / "stimulus.csv"
    _write_rows_csv(csv_path, rows, ["time", "clk", "rst", "mode", "gate", "out", "metric"])

    for task_id in task_ids:
        row_result, stream_result = _evaluate_row_and_streaming(task_id, csv_path)
        assert stream_result[0] == row_result[0], task_id
        assert stream_result[1] == [f"streaming_checker:{row_result[1][0]}"], task_id


def _programmable_gain_amplifier_rows(*, mode: str = "good") -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for idx in range(181):
        time_ns = idx * 0.5
        rst = time_ns <= 2.0
        clk = 0.9 if (time_ns % 8.0) < 4.0 else 0.0
        gain_sel = 0.9 if (20.0 <= time_ns < 48.0 or time_ns >= 72.0) else 0.0
        if time_ns < 8.0:
            vin = 0.45
        elif time_ns < 16.0:
            vin = 0.60
        elif time_ns < 28.0:
            vin = 0.30
        elif time_ns < 38.0:
            vin = 0.72
        elif time_ns < 50.0:
            vin = 0.20
        elif time_ns < 70.0:
            vin = 0.55
        elif time_ns < 83.0:
            vin = 0.85
        else:
            vin = 0.45

        if rst:
            gain = 1.0
        elif mode == "unity_gain":
            gain = 1.0
        elif gain_sel > 0.45:
            gain = 2.4
        else:
            gain = 0.8
        raw = 0.45 + gain * (vin - 0.45)
        if rst:
            out = 0.45
            metric = 0.0
        elif mode == "unbounded":
            out = raw
            metric = 0.0
        else:
            out = max(0.0, min(0.9, raw))
            metric = 0.9 if out != raw else 0.0
        rows.append(
            {
                "time": time_ns * 1e-9,
                "clk": clk,
                "rst": 0.9 if rst else 0.0,
                "gain_sel": gain_sel,
                "vin": vin,
                "out": out,
                "metric": metric,
            }
        )
    return rows


def test_programmable_gain_amplifier_checker_requires_gain_select_and_clamps() -> None:
    assert sim.check_programmable_gain_amplifier(_programmable_gain_amplifier_rows())[0]
    assert not sim.check_programmable_gain_amplifier(
        _programmable_gain_amplifier_rows(mode="unity_gain")
    )[0]
    assert not sim.check_programmable_gain_amplifier(
        _programmable_gain_amplifier_rows(mode="unbounded")
    )[0]


def test_two_pole_filter_checker_requires_lag_and_state_difference_metric() -> None:
    assert sim.check_release_two_pole_filter(_ct04_rows("two_pole"))[0]
    assert not sim.check_release_two_pole_filter(_ct04_rows("two_pole", mode="single_pole"))[0]


def test_soft_hysteretic_limiter_checker_requires_memory_state() -> None:
    assert sim.check_release_soft_hysteretic_limiter(_ct04_rows("soft_limiter"))[0]
    assert not sim.check_release_soft_hysteretic_limiter(
        _ct04_rows("soft_limiter", mode="memoryless")
    )[0]


def test_amplifier_filter_chain_checker_requires_preamp_metric_and_lagged_output() -> None:
    assert sim.check_release_amplifier_filter_chain(_ct04_rows("amp_filter"))[0]
    assert not sim.check_release_amplifier_filter_chain(
        _ct04_rows("amp_filter", mode="direct_gain")
    )[0]


def _rf_mixer_downconverter_rows(*, active_metric: float = 0.44) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for idx in range(0, 161):
        time_ns = idx * 0.5
        rst = time_ns <= 2.0
        clk_high = (time_ns % 4.0) < 2.0
        if time_ns < 8.0:
            vin = 0.45
        elif time_ns < 34.0:
            vin = 0.66
        elif time_ns < 58.0:
            vin = 0.24
        else:
            vin = 0.55
        if rst:
            out = 0.45
            metric = 0.0
        elif vin > 0.55:
            out = 0.66 if clk_high else 0.24
            metric = active_metric
        elif vin < 0.38:
            out = 0.24 if clk_high else 0.66
            metric = active_metric
        else:
            out = 0.45
            metric = 0.0
        rows.append(
            {
                "time": time_ns * 1e-9,
                "clk": 0.9 if clk_high else 0.0,
                "rst": 0.9 if rst else 0.0,
                "vin": vin,
                "out": out,
                "metric": metric,
            }
        )
    return rows


def test_rf_mixer_checker_accepts_half_duty_activity_metric_with_margin() -> None:
    assert sim.check_rf_mixer_downconverter_macro(_rf_mixer_downconverter_rows())[0]
    assert not sim.check_rf_mixer_downconverter_macro(
        _rf_mixer_downconverter_rows(active_metric=0.20)
    )[0]


def _log_rssi_rows_with_dense_transition_tail() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []

    def add(time_ns: float, out: float, metric: float = 0.0, vin: float = 0.0) -> None:
        rows.append(
            {
                "time": time_ns * 1e-9,
                "clk": 0.0,
                "rst": 0.0,
                "vin": vin,
                "out": out,
                "metric": metric,
            }
        )

    add(0.0, 0.12)
    add(5.0, 0.12)
    add(7.5, 0.12)
    add(12.0, 0.12)
    add(22.0, 0.12)
    add(30.0, 0.60, vin=0.35)
    add(39.90, 0.60, vin=0.35)
    for idx in range(10):
        add(39.91 + idx * 0.009, 0.72, vin=0.35)
    add(40.0, 0.72, vin=0.35)
    add(50.0, 0.72, metric=0.70, vin=0.70)
    add(60.0, 0.72, metric=0.70, vin=0.70)
    add(61.0, 0.72, metric=0.70, vin=0.70)
    return rows


def test_log_rssi_checker_uses_time_weighted_windows_for_adaptive_sample_density() -> None:
    rows = _log_rssi_rows_with_dense_transition_tail()
    unweighted_mid = sim.mean_in_window(rows, "out", 30.0e-9, 40.0e-9)
    weighted_mid = sim.time_weighted_mean_in_window(rows, "out", 30.0e-9, 40.0e-9)

    assert unweighted_mid is not None and unweighted_mid > 0.62
    assert weighted_mid is not None and weighted_mid < 0.61
    assert sim.check_log_rssi_power_detector(rows)[0]
