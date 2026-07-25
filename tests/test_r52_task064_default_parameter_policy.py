from __future__ import annotations

import sys
from pathlib import Path


RUNNERS = Path(__file__).resolve().parents[1] / "runners"
if str(RUNNERS) not in sys.path:
    sys.path.insert(0, str(RUNNERS))

from checkers.v4.task_064 import check_v4_edge_delay_line_with_deglitch


def _step(
    time_s: float,
    initial: float,
    transitions: tuple[tuple[float, float], ...],
) -> float:
    value = initial
    for edge_s, next_value in transitions:
        if time_s >= edge_s:
            value = next_value
    return value


def _trace(*, output_delay_ns: float = 2.2, omit_falling_output: bool = False) -> list[dict[str, float]]:
    start = 100e-9
    vin_edges = (
        (start + 5e-9, 0.9),
        (start + 15e-9, 0.0),
        (start + 24e-9, 0.9),
        (start + 24.4e-9, 0.0),
    )
    vout_edges = [(start + (5 + output_delay_ns) * 1e-9, 0.9)]
    if not omit_falling_output:
        vout_edges.append((start + (15 + output_delay_ns) * 1e-9, 0.0))
    vout_transitions = tuple(vout_edges)
    rst_edges = ((start + 1e-9, 0.0),)
    enable_edges = (
        (start + 2e-9, 0.9),
        (start + 30e-9, 0.0),
        (start + 34e-9, 0.9),
    )
    valid_edges: list[tuple[float, float]] = []
    for edge_s, _ in vout_transitions:
        valid_edges.extend(((edge_s, 0.9), (edge_s + 0.5e-9, 0.0)))
    rejected_edges = (
        (start + 24.45e-9, 0.9),
        (start + 25.0e-9, 0.0),
    )

    sample_times = {
        start,
        start + 0.5e-9,
        start + 1.5e-9,
        start + 31.5e-9,
        start + 35e-9,
    }
    all_transitions = (
        vin_edges
        + vout_transitions
        + rst_edges
        + enable_edges
        + tuple(valid_edges)
        + rejected_edges
    )
    for edge_s, _ in all_transitions:
        sample_times.update(
            {
                edge_s - 0.05e-9,
                edge_s,
                edge_s + 0.05e-9,
                edge_s + 0.8e-9,
            }
        )

    rows: list[dict[str, float]] = []
    for time_s in sorted(sample_times):
        rows.append(
            {
                "time": time_s,
                "vin": _step(time_s, 0.0, vin_edges),
                "rst": _step(time_s, 0.9, rst_edges),
                "enable": _step(time_s, 0.0, enable_edges),
                "vout": _step(time_s, 0.0, vout_transitions),
                "edge_valid": _step(time_s, 0.0, tuple(valid_edges)),
                "rejected": _step(time_s, 0.0, rejected_edges),
            }
        )
    return rows


def test_task064_accepts_semantic_coverage_without_reference_event_multiplicity() -> None:
    passed, detail = check_v4_edge_delay_line_with_deglitch(_trace())

    assert passed, detail
    assert "input_edges=4" in detail
    assert "qualified=2" in detail
    assert "P_PARAMETER_OVERRIDE" not in detail


def test_task064_rejects_nondefault_timing_under_default_parameter_policy() -> None:
    passed, detail = check_v4_edge_delay_line_with_deglitch(
        _trace(output_delay_ns=3.8)
    )

    assert not passed
    assert "P_DELAYED_EDGE_EMISSION" in detail


def test_task064_still_requires_bidirectional_qualified_behavior() -> None:
    passed, detail = check_v4_edge_delay_line_with_deglitch(
        _trace(omit_falling_output=True)
    )

    assert not passed
    assert "P_DELAYED_EDGE_EMISSION" in detail
