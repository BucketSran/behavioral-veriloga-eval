from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

from checkers.v4.task_091 import CHECKER as CHECKER_091
from checkers.v4.task_219 import CHECKER as CHECKER_219
from checkers.v4.task_235 import CHECKER as CHECKER_235


VDD = 0.9
VTH = 0.45


def _pwl(time_ns: float, points: list[tuple[float, float]]) -> float:
    for (left_time, left_value), (right_time, right_value) in zip(points, points[1:]):
        if left_time <= time_ns <= right_time:
            if right_time == left_time:
                return right_value
            fraction = (time_ns - left_time) / (right_time - left_time)
            return left_value + fraction * (right_value - left_value)
    return points[-1][1]


def _logic(value: bool, high: float = VDD) -> float:
    return high if value else 0.0


def _chop_value(time_ns: float) -> float:
    if time_ns < 2.0:
        return 0.0
    phase_ns = (time_ns - 2.0) % 2.0
    if phase_ns <= 0.05:
        return VDD * phase_ns / 0.05
    if phase_ns <= 0.95:
        return VDD
    if phase_ns <= 1.0:
        return VDD * (1.0 - (phase_ns - 0.95) / 0.05)
    return 0.0


def _chopper_rows_single_clear(*, omit_hold: bool = False) -> list[dict[str, float]]:
    vinp_points = [(0.0, 0.47), (18.0, 0.47), (18.1, 0.435), (34.0, 0.435), (34.1, 0.46), (44.0, 0.46)]
    vinn_points = [(0.0, 0.43), (18.0, 0.43), (18.1, 0.465), (34.0, 0.465), (34.1, 0.44), (44.0, 0.44)]
    rst_points = [(0.0, 0.0), (28.0, 0.0), (28.1, VDD), (29.4, VDD), (29.5, 0.0), (44.0, 0.0)]
    hold_points = [(0.0, 0.0), (20.0, 0.0), (20.1, 0.0 if omit_hold else VDD), (22.0, 0.0 if omit_hold else VDD), (22.1, 0.0), (44.0, 0.0)]

    events: list[tuple[float, str, int]] = [(28.05, "clear", 0)]
    for base_ns in range(2, 44, 2):
        events.append((base_ns + 0.025, "chop", +1))
        events.append((base_ns + 0.975, "chop", -1))
    events.sort()

    baseband = 0.0
    residual = 0.0
    settled = 0.0
    converged = 0
    event_index = 0
    rows: list[dict[str, float]] = []
    for step in range(881):
        time_ns = step * 0.05
        while event_index < len(events) and events[event_index][0] <= time_ns + 1.0e-12:
            event_time_ns, kind, polarity = events[event_index]
            rst = _pwl(event_time_ns, rst_points)
            hold = _pwl(event_time_ns, hold_points)
            if kind == "clear" or rst > VTH:
                baseband = 0.0
                residual = 0.0
                settled = 0.0
                converged = 0
            elif hold <= VTH:
                input_diff = _pwl(event_time_ns, vinp_points) - _pwl(event_time_ns, vinn_points)
                demodulated = 3.0 * (input_diff + polarity * 0.020)
                baseband += 0.25 * (demodulated - baseband)
                residual = baseband - 3.0 * input_diff
                converged = converged + 1 if abs(residual) <= 0.020 else 0
                settled = VDD if converged >= 3 else 0.0
            event_index += 1

        rows.append(
            {
                "time": time_ns * 1e-9,
                "vinp": _pwl(time_ns, vinp_points),
                "vinn": _pwl(time_ns, vinn_points),
                "chop_clk": _chop_value(time_ns),
                "rst": _pwl(time_ns, rst_points),
                "enable": VDD,
                "hold": _pwl(time_ns, hold_points),
                "voutp": min(VDD, max(0.0, 0.45 + 0.5 * baseband)),
                "voutn": min(VDD, max(0.0, 0.45 - 0.5 * baseband)),
                "settled": settled,
                "offset_residual": residual,
            }
        )
    return rows


def _bin2ther_constant_shifted_rail_rows(*, hardcoded_default_rail: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for step in range(121):
        time_ns = step * 0.05
        if time_ns < 1.5:
            b1, b0 = 0.6, 0.6
        elif time_ns < 3.0:
            b1, b0 = 0.6, 0.8
        elif time_ns < 4.5:
            b1, b0 = 0.8, 0.6
        else:
            b1, b0 = 0.8, 0.8
        vdd = 1.2
        gnd = 0.2
        threshold = 0.45 if hardcoded_default_rail else 0.5 * (vdd + gnd)
        high = 0.9 if hardcoded_default_rail else vdd
        low = 0.0 if hardcoded_default_rail else gnd
        rows.append(
            {
                "time": time_ns * 1e-9,
                "vdd": vdd,
                "gnd": gnd,
                "b1": b1,
                "b0": b0,
                "t0": high if b1 > threshold else low,
                "t1": high if b1 > threshold else low,
                "t2": high if b0 > threshold else low,
            }
        )
    return rows


def _pfd_rows(*, immediate_reset: bool = False) -> list[dict[str, float]]:
    edge_events = [(10.0, "a"), (12.0, "b"), (22.0, "b"), (24.0, "a")]
    sample_times = {
        0.0,
        9.95, 10.03, 11.0, 11.95, 12.03, 12.06, 12.15, 13.0,
        21.95, 22.03, 23.0, 23.95, 24.03, 24.06, 24.15, 25.0,
    }
    for edge_ns, _ in edge_events:
        sample_times.update({edge_ns - 0.02, edge_ns + 0.02, edge_ns + 0.08})
    times_ns = sorted(sample_times)

    up = False
    down = False
    pending_reset: float | None = None
    event_index = 0
    rows: list[dict[str, float]] = []
    for time_ns in times_ns:
        if pending_reset is not None and pending_reset <= time_ns:
            up = False
            down = False
            pending_reset = None
        while event_index < len(edge_events) and edge_events[event_index][0] <= time_ns:
            event_time_ns, signal = edge_events[event_index]
            if signal == "a":
                up = True
            else:
                down = True
            if up and down:
                pending_reset = event_time_ns if immediate_reset else event_time_ns + 0.1
            event_index += 1
        if pending_reset is not None and pending_reset <= time_ns:
            up = False
            down = False
            pending_reset = None
        rows.append(
            {
                "time": time_ns * 1e-9,
                "a": _logic(any(edge <= time_ns < edge + 0.05 for edge, signal in edge_events if signal == "a")),
                "b": _logic(any(edge <= time_ns < edge + 0.05 for edge, signal in edge_events if signal == "b")),
                "ub": 0.0 if up else VDD,
                "d": VDD if down else 0.0,
            }
        )
    return rows


def test_task091_accepts_single_clear_semantic_chopper_layout() -> None:
    ok, note = CHECKER_091(_chopper_rows_single_clear())
    assert ok, note


def test_task091_rejects_missing_hold_exercise() -> None:
    ok, note = CHECKER_091(_chopper_rows_single_clear(omit_hold=True))
    assert not ok
    assert "hold_edges=0" in note


def test_task219_accepts_constant_shifted_local_rails() -> None:
    ok, note = CHECKER_219(_bin2ther_constant_shifted_rail_rows())
    assert ok, note


def test_task219_rejects_default_rail_hardcoding_on_shifted_rails() -> None:
    ok, note = CHECKER_219(_bin2ther_constant_shifted_rail_rows(hardcoded_default_rail=True))
    assert not ok
    assert "expected" in note


def test_task235_accepts_sparse_event_relative_pfd_coverage() -> None:
    ok, note = CHECKER_235(_pfd_rows())
    assert ok, note


def test_task235_rejects_immediate_reset_instead_of_delayed_reset() -> None:
    ok, note = CHECKER_235(_pfd_rows(immediate_reset=True))
    assert not ok
    assert "pfd_level_error" in note
