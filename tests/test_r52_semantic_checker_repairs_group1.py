from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

from checkers.v4.task_001 import check_v4_bbpd
from checkers.v4.task_004 import check_v4_trim_calibration_controller
from checkers.v4.task_006 import check_v4_element_shuffler


def _bbpd_rows(*, include_none_case: bool = True) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for step in range(701):
        time_ns = step * 0.05
        data = 0.9 if 10.0 <= time_ns < 20.0 or time_ns >= 30.0 else 0.0
        clk = 0.9 if time_ns < 15.0 or time_ns >= 25.0 else 0.0
        retimed = 0.9 if time_ns >= 18.0 else 0.0
        up = 0.9 if 10.0 <= time_ns < 15.0 else 0.0
        down = 0.9 if 20.0 <= time_ns < 25.0 else 0.0
        if not include_none_case and 30.0 <= time_ns < 35.0:
            up = 0.9
        rows.append(
            {
                "time": time_ns * 1e-9,
                "data": data,
                "clk": clk,
                "retimed_data": retimed,
                "up": up,
                "down": down,
            }
        )
    return rows


def _trim_rows(*, reach_lower_clamp: bool = True) -> list[dict[str, float]]:
    clock_edges = [5.0 + 10.0 * index for index in range(24)]
    trim_by_edge: dict[float, float] = {}
    trim = 0.45
    for edge in clock_edges:
        rst = edge == 5.0
        err_high = edge < 90.0 or edge >= 230.0
        if rst:
            trim = 0.45
        elif err_high:
            trim = min(0.85, trim + 0.06)
        else:
            trim = max(0.05, trim - 0.06)
        trim_by_edge[edge] = trim

    rows: list[dict[str, float]] = []
    current_trim = 0.45
    stop_ns = 250.0 if reach_lower_clamp else 130.0
    for step in range(int(stop_ns * 10) + 1):
        time_ns = step / 10.0
        for edge, edge_trim in trim_by_edge.items():
            if abs(time_ns - (edge + 0.5)) < 0.051:
                current_trim = edge_trim
        err = 0.9 if time_ns < 90.0 or time_ns >= 230.0 else 0.0
        rows.append(
            {
                "time": time_ns * 1e-9,
                "clk": 0.9 if any(edge <= time_ns < edge + 2.0 for edge in clock_edges) else 0.0,
                "rst": 0.9 if time_ns < 14.0 else 0.0,
                "err": err,
                "trim": current_trim,
            }
        )
    return rows


def _shuffler_rows(*, include_reset: bool = True) -> list[dict[str, float]]:
    clock_edges = [10.0, 20.0, 30.0, 40.0, 55.0]
    reset_assert_ns = 45.0
    reset_release_ns = 50.0
    output_for_state = (1, 2, 0, 3)
    state = 0
    active = 1
    rows: list[dict[str, float]] = []
    for step in range(601):
        time_ns = step / 10.0
        if include_reset and abs(time_ns - (reset_assert_ns + 0.5)) < 0.051:
            state = 0
            active = output_for_state[state]
        for edge in clock_edges:
            if abs(time_ns - (edge + 0.5)) < 0.051:
                state = (state + 1) % 4
                active = output_for_state[state]
        rst_n = 0.9
        if include_reset and (
            time_ns < 5.0 or reset_assert_ns <= time_ns < reset_release_ns
        ):
            rst_n = 0.0
        row = {
            "time": time_ns * 1e-9,
            "clk": 0.9 if any(edge <= time_ns < edge + 1.0 for edge in clock_edges) else 0.0,
            "rst_n": rst_n,
        }
        for index in range(4):
            row[f"out{index}"] = 0.9 if index == active else 0.0
        rows.append(row)
    return rows


def test_task_001_accepts_semantic_three_edge_layout() -> None:
    ok, note = check_v4_bbpd(_bbpd_rows())
    assert ok, note


def test_task_001_rejects_missing_neither_direction_case() -> None:
    ok, note = check_v4_bbpd(_bbpd_rows(include_none_case=False))
    assert not ok
    assert "none" in note


def test_task_004_initial_check_is_relative_to_first_clock() -> None:
    rows = _trim_rows()
    shifted = [{**row, "time": row["time"] + 100e-9} for row in rows]
    ok, note = check_v4_trim_calibration_controller(shifted)
    assert ok, note


def test_task_004_rejects_missing_lower_clamp_coverage() -> None:
    ok, note = check_v4_trim_calibration_controller(_trim_rows(reach_lower_clamp=False))
    assert not ok
    assert "lower_clamp" in note


def test_task_006_accepts_reset_after_activity_and_one_permutation_cycle() -> None:
    ok, note = check_v4_element_shuffler(_shuffler_rows())
    assert ok, note


def test_task_006_rejects_missing_reset_exercise() -> None:
    ok, note = check_v4_element_shuffler(_shuffler_rows(include_reset=False))
    assert not ok
    assert "reset_samples=0" in note
