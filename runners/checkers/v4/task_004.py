"""Task-specific checker for canonical v4 DUT 004."""
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

def check_v4_trim_calibration_controller(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "err", "trim"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing)

    edges = _v4_edge_times(rows, "clk", rising=True)
    expected = 0.45
    mismatches: list[str] = []
    coverage = {"reset": 0, "increment": 0, "decrement": 0, "upper_clamp": 0, "lower_clamp": 0}
    for edge_time in edges:
        rst = sample_signal_at(rows, "rst", edge_time)
        err = sample_signal_at(rows, "err", edge_time)
        observed = sample_signal_at(rows, "trim", edge_time + 2.0e-9)
        if rst is None or err is None or observed is None:
            mismatches.append(f"missing@{edge_time * 1e9:.3f}ns")
            continue
        if rst > 0.45:
            expected = 0.45
            coverage["reset"] += 1
        elif err > 0.45:
            expected += 0.06
            coverage["increment"] += 1
        else:
            expected -= 0.06
            coverage["decrement"] += 1
        if expected > 0.85:
            expected = 0.85
            coverage["upper_clamp"] += 1
        if expected < 0.05:
            expected = 0.05
            coverage["lower_clamp"] += 1
        if abs(observed - expected) > 0.025:
            mismatches.append(
                f"clk@{edge_time * 1e9:.3f}ns_observed={observed:.3f}_expected={expected:.3f}"
            )

    spans = _v4_hold_spans(rows, "trim", edges, settle_s=2.0e-9, guard_s=0.25e-9)
    hold_violations = [item for item in spans if item[2] > 0.015]
    err_edges = sorted(
        _v4_edge_times(rows, "err", rising=True) + _v4_edge_times(rows, "err", rising=False)
    )
    async_hold_failures: list[str] = []
    for err_time in err_edges:
        if any(abs(err_time - edge_time) <= 1.0e-9 for edge_time in edges):
            continue
        before = sample_signal_at(rows, "trim", max(0.0, err_time - 0.50e-9))
        after = sample_signal_at(rows, "trim", err_time + 1.50e-9)
        if before is None or after is None:
            continue
        if abs(after - before) > 0.025:
            async_hold_failures.append(
                f"err@{err_time * 1e9:.3f}ns_before={before:.3f}_after={after:.3f}"
            )
    initial = None
    if edges:
        first_edge = edges[0]
        initial_candidates = [
            row["trim"]
            for row in rows
            if row["time"] < first_edge
        ]
        if initial_candidates:
            initial = initial_candidates[-1]
    trace_values = [row["trim"] for row in rows]
    range_ok = min(trace_values) >= 0.035 and max(trace_values) <= 0.865
    coverage_ok = (
        coverage["reset"] >= 1
        and coverage["increment"] >= 1
        and coverage["decrement"] >= 1
        and coverage["upper_clamp"] >= 1
        and coverage["lower_clamp"] >= 1
    )
    ok = (
        initial is not None
        and abs(initial - 0.45) <= 0.025
        and coverage_ok
        and not mismatches
        and not hold_violations
        and not async_hold_failures
        and range_ok
    )
    return ok, (
        f"clock_edges={len(edges)} initial={initial} edge_mismatches={len(mismatches)} "
        f"hold_intervals={len(spans)} hold_violations={len(hold_violations)} "
        f"async_hold_failures={len(async_hold_failures)} "
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
        + (" async_hold_detail=" + ";".join(async_hold_failures[:4]) if async_hold_failures else "")
    )

CHECKER_ID = "v4_004_trim_calibration_controller"
CHECKER: Checker = check_v4_trim_calibration_controller
