from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

from checkers.v4.task_008 import check_v4_gain_trim_controller
from checkers.v4.task_009 import check
from checkers.v4.task_053 import check_v3_495_slew_rate_dac4


VDD = 0.9


def _logic(value: bool) -> float:
    return VDD if value else 0.0


def _gain_rows(*, include_deadband: bool = True, shift_ns: float = 0.0) -> list[dict[str, float]]:
    edge_ns = [20.0 + 8.0 * index for index in range(31)]
    meas_by_edge: dict[float, float] = {}
    rst_edges = {edge_ns[0]}
    for index, edge in enumerate(edge_ns):
        if index == 0:
            meas_by_edge[edge] = 0.45
        elif 1 <= index <= 12:
            meas_by_edge[edge] = 0.20
        elif index == 13 and include_deadband:
            meas_by_edge[edge] = 0.45
        else:
            meas_by_edge[edge] = 0.70

    expected_by_edge: dict[float, float] = {}
    expected = 0.30
    for edge in edge_ns:
        meas = meas_by_edge[edge]
        if edge in rst_edges:
            expected = 0.30
        elif meas < 0.43:
            expected = min(0.85, expected + 0.05)
        elif meas > 0.47:
            expected = max(0.05, expected - 0.05)
        expected_by_edge[edge] = expected

    rows: list[dict[str, float]] = []
    gain = 0.30
    stop_ns = edge_ns[-1] + 8.0
    for step in range(int(stop_ns * 2) + 1):
        local_ns = step * 0.5
        for edge, value in expected_by_edge.items():
            if local_ns >= edge + 2.0:
                gain = value
        active_edge = any(edge <= local_ns < edge + 2.0 for edge in edge_ns)
        next_edge = max((edge for edge in edge_ns if edge <= local_ns), default=edge_ns[0])
        rows.append(
            {
                "time": (local_ns + shift_ns) * 1e-9,
                "clk": _logic(active_edge),
                "rst": _logic(next_edge in rst_edges and local_ns < next_edge + 6.0),
                "meas": meas_by_edge[next_edge],
                "target": 0.45,
                "gain_ctrl": gain,
            }
        )
    return rows


def _lock_rows(*, include_mismatch: bool = True, shift_ns: float = 0.0) -> list[dict[str, float]]:
    ref_edges = [10.0, 20.0, 30.0, 40.0, 60.0, 70.0, 80.0]
    fb_edges = [9.0, 19.0, 29.0, 35.0 if include_mismatch else 39.0, 59.0, 69.0, 79.0]
    reset_low_windows = [(48.0, 54.0)]

    def reset_high(time_ns: float) -> bool:
        return not any(start <= time_ns <= stop for start, stop in reset_low_windows)

    lock_after_ref: dict[float, float] = {}
    streak = 0
    locked = False
    for ref_ns, fb_ns in zip(ref_edges, fb_edges):
        if not reset_high(ref_ns):
            streak = 0
            locked = False
        elif 0.0 <= ref_ns - fb_ns <= 2.0:
            streak += 1
            if streak >= 3:
                locked = True
        else:
            streak = 0
            locked = False
        lock_after_ref[ref_ns] = 0.9 if locked else 0.0
        if ref_ns == 40.0:
            streak = 0
            locked = False

    rows: list[dict[str, float]] = []
    lock = 0.0
    for step in range(181):
        local_ns = step * 0.5
        if not reset_high(local_ns):
            lock = 0.0
        for ref_ns, level in lock_after_ref.items():
            if local_ns >= ref_ns + 0.5:
                lock = level
        rows.append(
            {
                "time": (local_ns + shift_ns) * 1e-9,
                "ref_clk": _logic(any(edge <= local_ns < edge + 1.0 for edge in ref_edges)),
                "fb_clk": _logic(any(edge <= local_ns < edge + 1.0 for edge in fb_edges)),
                "rst_n": _logic(reset_high(local_ns)),
                "lock": lock,
            }
        )
    return rows


def _dac_rows(codes: list[int], *, shift_ns: float = 0.0) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    expected = 0.0
    last_ns = 0.0
    for code_index, code in enumerate(codes):
        segment_start_ns = code_index * 14.0
        for sample in range(29):
            local_ns = segment_start_ns + sample * 0.5
            target = code / 15.0
            dt = (local_ns - last_ns) * 1e-9
            step = 1e8 * max(dt, 0.0)
            if expected < target:
                expected = min(target, expected + step)
            elif expected > target:
                expected = max(target, expected - step)
            last_ns = local_ns
            rows.append(
                {
                    "time": (local_ns + shift_ns) * 1e-9,
                    "d3": _logic(bool(code & 8)),
                    "d2": _logic(bool(code & 4)),
                    "d1": _logic(bool(code & 2)),
                    "d0": _logic(bool(code & 1)),
                    "vout": expected,
                }
            )
    return rows


def test_task_008_accepts_shifted_behavioral_coverage_layout() -> None:
    ok, note = check_v4_gain_trim_controller(_gain_rows(shift_ns=125.0))
    assert ok, note


def test_task_008_rejects_missing_deadband_case() -> None:
    ok, note = check_v4_gain_trim_controller(_gain_rows(include_deadband=False))
    assert not ok
    assert "'deadband': 0" in note


def test_task_009_accepts_seven_ref_event_reset_reacquire_layout() -> None:
    ok, note = check(_lock_rows(shift_ns=37.0))
    assert ok, note


def test_task_009_rejects_missing_mismatch_break_case() -> None:
    ok, note = check(_lock_rows(include_mismatch=False))
    assert not ok
    assert "mismatch_clears=0" in note


def test_task_053_accepts_shifted_settled_codes_and_ramp_layout() -> None:
    ok, note = check_v3_495_slew_rate_dac4(_dac_rows([0, 15, 3, 12], shift_ns=91.0))
    assert ok, note


def test_task_053_rejects_missing_binary_mapping_discriminator() -> None:
    ok, note = check_v3_495_slew_rate_dac4(_dac_rows([0, 15, 6]))
    assert not ok
    assert "bit_order_discriminator" in note
