"""Task-specific checker for canonical v4 DUT 008."""
from __future__ import annotations

from ..api import Checker
def sample_signal_at(rows: list[dict[str, float]], signal: str, time_s: float) -> float | None:
    if not rows or "time" not in rows[0] or signal not in rows[0]:
        return None
    first_time = rows[0]["time"]
    last_time = rows[-1].get("time")
    if last_time is None or time_s < first_time or time_s > last_time:
        return None
    if time_s == first_time:
        return rows[0].get(signal)
    for idx in range(1, len(rows)):
        prev = rows[idx - 1]
        cur = rows[idx]
        t0 = prev.get("time")
        t1 = cur.get("time")
        if t0 is None or t1 is None:
            continue
        if t0 <= time_s <= t1:
            v0 = prev.get(signal)
            v1 = cur.get(signal)
            if v0 is None or v1 is None:
                return None
            if t1 == t0:
                return v1
            alpha = (time_s - t0) / (t1 - t0)
            return v0 + alpha * (v1 - v0)
    return None

def _v4_edge_times(
    rows: list[dict[str, float]], signal: str, *, rising: bool, threshold: float = 0.45
) -> list[float]:
    times: list[float] = []
    for previous, current in zip(rows, rows[1:]):
        before = previous[signal]
        after = current[signal]
        if rising and before < threshold <= after:
            times.append(current["time"])
        elif not rising and before > threshold >= after:
            times.append(current["time"])
    return times

def _v4_hold_spans(
    rows: list[dict[str, float]],
    signal: str,
    edge_times: list[float],
    *,
    settle_s: float,
    guard_s: float,
) -> list[tuple[float, float, float]]:
    spans: list[tuple[float, float, float]] = []
    for start, stop in zip(edge_times, edge_times[1:]):
        window_start = start + settle_s
        window_stop = stop - guard_s
        values = [
            row[signal]
            for row in rows
            if window_start <= row["time"] <= window_stop
        ]
        if len(values) >= 2:
            spans.append((window_start, window_stop, max(values) - min(values)))
    return spans

def check_v4_gain_trim_controller(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "meas", "target", "gain_ctrl"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing)

    edges = _v4_edge_times(rows, "clk", rising=True)
    expected = 0.30
    mismatches: list[str] = []
    coverage = {"reset": 0, "increase": 0, "decrease": 0, "deadband": 0, "upper_clamp": 0, "lower_clamp": 0}
    for edge_time in edges:
        rst = sample_signal_at(rows, "rst", edge_time)
        meas = sample_signal_at(rows, "meas", edge_time)
        target = sample_signal_at(rows, "target", edge_time)
        observed = sample_signal_at(rows, "gain_ctrl", edge_time + 2.0e-9)
        if rst is None or meas is None or target is None or observed is None:
            mismatches.append(f"missing@{edge_time * 1e9:.3f}ns")
            continue
        if rst > 0.45:
            expected = 0.30
            coverage["reset"] += 1
        elif meas < target - 0.02:
            expected += 0.05
            coverage["increase"] += 1
        elif meas > target + 0.02:
            expected -= 0.05
            coverage["decrease"] += 1
        else:
            coverage["deadband"] += 1
        if expected > 0.85:
            expected = 0.85
            coverage["upper_clamp"] += 1
        if expected < 0.05:
            expected = 0.05
            coverage["lower_clamp"] += 1
        if abs(observed - expected) > 0.025:
            mismatches.append(
                f"clk@{edge_time * 1e9:.3f}ns_meas={meas:.3f}_target={target:.3f}_"
                f"observed={observed:.3f}_expected={expected:.3f}"
            )

    spans = _v4_hold_spans(rows, "gain_ctrl", edges, settle_s=2.0e-9, guard_s=0.25e-9)
    hold_violations = [item for item in spans if item[2] > 0.015]
    first_edge = edges[0] if edges else rows[-1]["time"]
    initial_candidates = [
        row["gain_ctrl"]
        for row in rows
        if row["time"] <= first_edge - 0.25e-9
    ]
    initial = initial_candidates[-1] if initial_candidates else rows[0]["gain_ctrl"]
    trace_values = [row["gain_ctrl"] for row in rows]
    range_ok = min(trace_values) >= 0.035 and max(trace_values) <= 0.865
    coverage_ok = all(coverage[key] >= 1 for key in ("reset", "increase", "decrease", "deadband"))
    clamp_ok = coverage["upper_clamp"] >= 1 and coverage["lower_clamp"] >= 1
    ok = (
        initial is not None
        and abs(initial - 0.30) <= 0.025
        and coverage_ok
        and clamp_ok
        and not mismatches
        and not hold_violations
        and range_ok
    )
    return ok, (
        f"clock_edges={len(edges)} initial={initial} edge_mismatches={len(mismatches)} "
        f"hold_intervals={len(spans)} hold_violations={len(hold_violations)} "
        f"range=({min(trace_values):.3f},{max(trace_values):.3f}) coverage={coverage}"
        + (" mismatch_detail=" + ";".join(mismatches[:5]) if mismatches else "")
        + (
            " hold_detail="
            + ";".join(
                f"{start * 1e9:.3f}-{stop * 1e9:.3f}ns:{span:.4f}"
                for start, stop, span in hold_violations[:4]
            )
            if hold_violations
            else ""
        )
    )

CHECKER_ID = "v4_008_gain_trim_controller"
CHECKER: Checker = check_v4_gain_trim_controller
