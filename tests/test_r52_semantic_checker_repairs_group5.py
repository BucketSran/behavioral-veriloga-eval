from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

from checkers.v4.task_302 import check_v3_505_fractional_n_divider_accumulator_flow
from checkers.v4.task_322 import check_v4_1020_glitchless_clock_mux_selector


VDD = 0.9
VTH = 0.45


def _logic(value: bool) -> float:
    return VDD if value else 0.0


def _clock_high(time_ns: float, edges_ns: list[float], width_ns: float) -> bool:
    return any(edge <= time_ns < edge + width_ns for edge in edges_ns)


def _fracn_rows(
    *,
    shift_ns: float = 0.0,
    counts: list[int] | None = None,
    constant_vctrl: bool = False,
) -> list[dict[str, float]]:
    dco_edges_ns = [30.0 + 10.0 * index for index in range(120)]
    counts = counts or [16, 15, 15, 16, 15, 15, 15]
    fb_edges_ns = [20.0]
    dco_index = 0
    for count in counts:
        dco_index += count
        fb_edges_ns.append(dco_edges_ns[dco_index - 1])
    ref_edges_ns = [20.0, 180.0, 340.0, 500.0, 660.0, 810.0, 960.0, 1110.0]

    times_ns = set(float(step * 5) for step in range(0, 241))
    for edge in ref_edges_ns + fb_edges_ns + dco_edges_ns:
        times_ns.update({edge - 1.0, edge, edge + 1.0})
    rows: list[dict[str, float]] = []
    for time_ns in sorted(t for t in times_ns if 0.0 <= t <= 1200.0):
        shifted = (time_ns + shift_ns) * 1.0e-9
        if constant_vctrl:
            vctrl = 0.45
        elif time_ns < 660.0:
            vctrl = 0.45
        elif time_ns < 960.0:
            vctrl = 0.55
        else:
            vctrl = 0.48
        lock = (300.0 <= time_ns < 660.0) or time_ns >= 960.0
        rows.append(
            {
                "time": shifted,
                "VDD": VDD,
                "VSS": 0.0,
                "ref_clk": _logic(_clock_high(time_ns, ref_edges_ns, 8.0)),
                "fb_clk": _logic(_clock_high(time_ns, fb_edges_ns, 70.0)),
                "dco_clk": _logic(_clock_high(time_ns, dco_edges_ns, 5.0)),
                "vctrl_mon": vctrl,
                "lock": _logic(lock),
            }
        )
    return rows


def _mux_input(time_ns: float, delay_ns: float) -> bool:
    phase = (time_ns - delay_ns) % 8.0
    return 0.0 <= phase < 2.4


def _mux_rows(
    *,
    scale: float = 1.0,
    shift_ns: float = 0.0,
    no_wait: bool = False,
    missing_valid: bool = False,
) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    active = 0
    valid = False
    switch_end_ns = -1.0
    last_out = False
    for index in range(153):
        base_ns = index * 0.5
        clk_a = _mux_input(base_ns, 1.0)
        clk_b = _mux_input(base_ns, 3.0)
        rst = base_ns < 4.0
        enable = 5.0 <= base_ns < 64.0 or base_ns >= 72.0
        pending = 1 if 20.0 <= base_ns < 36.0 or base_ns >= 52.0 else 0
        if rst or not enable:
            active = 0
            valid = False
            switch_end_ns = -1.0
        elif pending != active and (no_wait or (not clk_a and not clk_b)):
            active = pending
            valid = False
            switch_end_ns = base_ns + 8.0
        out = (clk_b if active else clk_a) if enable and not rst else False
        if enable and not rst and (not last_out and out):
            valid = True
        last_out = out
        rows.append(
            {
                "time": (base_ns * scale + shift_ns) * 1.0e-9,
                "clk_a": _logic(clk_a),
                "clk_b": _logic(clk_b),
                "sel": _logic(bool(pending)),
                "rst": _logic(rst),
                "enable": _logic(enable),
                "clk_out": _logic(out),
                "switch_metric": _logic(enable and not rst and base_ns <= switch_end_ns),
                "valid": 0.0 if missing_valid else _logic(valid and enable and not rst),
            }
        )
    return rows


def test_task302_accepts_shifted_sparse_fractional_tracking_trace() -> None:
    rows = _fracn_rows(shift_ns=77.0)
    ok, note = check_v3_505_fractional_n_divider_accumulator_flow(rows)
    assert ok, note
    assert "P_USE_REF_CLK_AS_THE_REFERENCE mismatch_count=0" in note


def test_task302_rejects_wrong_integer_divider_counts() -> None:
    rows = _fracn_rows(counts=[17, 18, 17, 18, 17, 18])
    ok, note = check_v3_505_fractional_n_divider_accumulator_flow(rows)
    assert not ok
    assert "dco_edges_per_fb_period_out_of_range" in note or "fractional_short_count" in note


def test_task302_rejects_missing_control_correction() -> None:
    rows = _fracn_rows(constant_vctrl=True)
    ok, note = check_v3_505_fractional_n_divider_accumulator_flow(rows)
    assert not ok
    assert "vctrl_span" in note


def test_task322_accepts_scaled_sparse_event_relative_mux_trace() -> None:
    rows = _mux_rows(scale=2.5, shift_ns=31.0)
    ok, note = check_v4_1020_glitchless_clock_mux_selector(rows)
    assert ok, note


def test_task322_rejects_switch_without_both_low_wait() -> None:
    rows = _mux_rows(no_wait=True)
    ok, note = check_v4_1020_glitchless_clock_mux_selector(rows)
    assert not ok
    assert "glitch_errors" in note


def test_task322_rejects_missing_valid_flag() -> None:
    rows = _mux_rows(missing_valid=True)
    ok, note = check_v4_1020_glitchless_clock_mux_selector(rows)
    assert not ok
    assert "valid_errors" in note


def test_task322_short_trace_returns_a_checker_diagnostic() -> None:
    row = {
        "time": 0.0,
        "clk_a": 0.0,
        "clk_b": 0.0,
        "sel": 0.0,
        "rst": VDD,
        "enable": 0.0,
        "clk_out": 0.0,
        "switch_metric": 0.0,
        "valid": 0.0,
    }
    ok, note = check_v4_1020_glitchless_clock_mux_selector([row])
    assert not ok
    assert "insufficient_clock_coverage" in note
