from __future__ import annotations

from pathlib import Path
import math
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

from checkers.v4.task_299 import check_v3_502_sine_vco_idtmod_bound_step
from checkers.v4.task_300 import check_v3_503_differential_vco_clip_idtmod


def _phase_rows_299(
    vins: list[float],
    *,
    shift_ns: float = 0.0,
    output_scale: float = 1.0,
) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    phase_cycles = 0.0
    previous_time = 0.0
    for index, vin in enumerate(vins):
        local_time = index * 25e-9
        if index:
            previous_vin = vins[index - 1]
            f0 = 20.0e6 + 40.0e6 * previous_vin
            f1 = 20.0e6 + 40.0e6 * vin
            phase_cycles += 0.5 * (f0 + f1) * (local_time - previous_time)
        previous_time = local_time
        phase = phase_cycles % 1.0
        rows.append(
            {
                "time": local_time + shift_ns * 1e-9,
                "vin": vin,
                "out": output_scale * 0.9 * math.sin(2.0 * math.pi * phase),
                "metric": 0.9 * phase,
            }
        )
    return rows


def _clip(value: float, low: float, high: float) -> float:
    return low if value < low else high if value > high else value


def _phase_rows_300(
    diffs: list[float],
    *,
    shift_ns: float = 0.0,
    single_ended: bool = False,
) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    phase_cycles = 0.0
    previous_time = 0.0
    previous_diff = diffs[0]
    for index, diff in enumerate(diffs):
        local_time = index * 20e-9
        if index:
            f0 = _clip(20.0e6 + 160.0e6 * previous_diff, 5.0e6, 80.0e6)
            f1 = _clip(20.0e6 + 160.0e6 * diff, 5.0e6, 80.0e6)
            phase_cycles += 0.5 * (f0 + f1) * (local_time - previous_time)
        previous_time = local_time
        previous_diff = diff
        phase = phase_cycles % 1.0
        sine = 0.4 * math.sin(2.0 * math.pi * phase)
        outp = 0.45 + sine
        outm = 0.45 + sine if single_ended else 0.45 - sine
        rows.append(
            {
                "time": local_time + shift_ns * 1e-9,
                "vinp": 0.45 + 0.5 * diff,
                "vinm": 0.45 - 0.5 * diff,
                "outp": outp,
                "outm": outm,
                "metric": 0.9 * phase,
            }
        )
    return rows


def test_task_299_accepts_shifted_semantic_vco_trace_with_fewer_than_20_points() -> None:
    rows = _phase_rows_299([0.05] * 5 + [0.20] * 5 + [0.55] * 6, shift_ns=125.0)
    ok, note = check_v3_502_sine_vco_idtmod_bound_step(rows)
    assert ok, note


def test_task_299_rejects_weak_frequency_stimulus() -> None:
    rows = _phase_rows_299([0.20] * 16)
    ok, note = check_v3_502_sine_vco_idtmod_bound_step(rows)
    assert not ok
    assert "frequency_stimulus_span" in note


def test_task_299_rejects_low_output_scale() -> None:
    rows = _phase_rows_299([0.05] * 5 + [0.20] * 5 + [0.55] * 6, output_scale=0.5)
    ok, note = check_v3_502_sine_vco_idtmod_bound_step(rows)
    assert not ok
    assert "out@" in note


def test_task_300_accepts_shifted_semantic_clip_trace_with_fewer_than_20_points() -> None:
    rows = _phase_rows_300([-0.30] * 5 + [0.30] * 5 + [0.50] * 6, shift_ns=87.0)
    ok, note = check_v3_503_differential_vco_clip_idtmod(rows)
    assert ok, note


def test_task_300_rejects_missing_inband_clip_coverage() -> None:
    rows = _phase_rows_300([-0.30] * 8 + [0.50] * 8)
    ok, note = check_v3_503_differential_vco_clip_idtmod(rows)
    assert not ok
    assert "inband:False" in note


def test_task_300_rejects_single_ended_output_fault() -> None:
    rows = _phase_rows_300([-0.30] * 5 + [0.30] * 5 + [0.50] * 6, single_ended=True)
    ok, note = check_v3_503_differential_vco_clip_idtmod(rows)
    assert not ok
    assert "outm@" in note
