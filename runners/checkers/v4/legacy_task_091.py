"""Compatibility checker for the released v4 final-step file-metric task."""

from __future__ import annotations

from ..api import Checker


def _rising_edges(
    values: list[float],
    times: list[float],
    threshold: float = 0.45,
) -> list[float]:
    return [
        times[index]
        for index in range(1, len(values))
        if values[index - 1] < threshold <= values[index]
    ]


def check_final_step_file_metric(
    rows: list[dict[str, float]],
) -> tuple[bool, str]:
    required = {"time", "ref", "metric_out"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - (set(rows[0]) if rows else set()))
        return False, "missing_columns=" + ",".join(missing)

    ref_high = max(row["ref"] for row in rows)
    threshold = 0.45 if ref_high < 1.0 else 0.5 * ref_high
    ref_edges = _rising_edges(
        [row["ref"] for row in rows],
        [row["time"] for row in rows],
        threshold=threshold,
    )
    if len(ref_edges) != 4:
        return False, f"expected_ref_edges=4 observed_ref_edges={len(ref_edges)}"

    metric_values = [row["metric_out"] for row in rows]
    maximum = max(metric_values)
    if maximum < 0.2:
        return False, f"metric_out_max={maximum:.3f} expected_min=0.200"

    levels: list[float] = []
    expected_levels: list[float] = []
    for index, edge_time in enumerate(ref_edges):
        next_edge = (
            ref_edges[index + 1]
            if index + 1 < len(ref_edges)
            else rows[-1]["time"]
        )
        start = edge_time + 0.8e-9
        stop = min(next_edge - 0.4e-9, edge_time + 6.0e-9, rows[-1]["time"])
        if stop <= start:
            continue
        samples = [
            row["metric_out"] for row in rows if start <= row["time"] <= stop
        ]
        if not samples:
            continue
        levels.append(sum(samples) / len(samples))
        expected_levels.append(ref_high * (index + 1) / 4.0)

    if len(levels) < 3:
        return False, f"metric_plateau_samples={len(levels)} expected_min=3"

    level_errors = [
        abs(level - expected)
        for level, expected in zip(levels, expected_levels)
    ]
    maximum_level_error = max(level_errors)
    final_normalized = levels[-1] / max(ref_high, 1e-6)
    expected_final_normalized = len(ref_edges) / 4.0
    dips = sum(
        1
        for left, right in zip(metric_values, metric_values[1:])
        if right + 0.03 < left
    )
    passed = (
        maximum_level_error <= 0.08
        and abs(final_normalized - expected_final_normalized) <= 0.10
        and dips <= 3
    )
    return passed, (
        f"ref_edges={len(ref_edges)} "
        f"metric_levels={[round(value, 3) for value in levels]} "
        f"max_level_err={maximum_level_error:.3f} "
        f"final_norm={final_normalized:.3f}/{expected_final_normalized:.3f} "
        f"metric_dips={dips}"
    )


CHECKER_ID = "v4_091_final_step_file_metric"
CHECKER: Checker = check_final_step_file_metric
