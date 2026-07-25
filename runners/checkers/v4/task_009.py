"""Task-specific checker for canonical v4 DUT 009."""
from __future__ import annotations

from bisect import bisect_left

from ..api import Checker

PROPERTY_IDS = (
    "P_ALIGNMENT_STREAK",
    "P_PREMATURE_LOCK",
    "P_MISS_BREAKS_STREAK",
    "P_RESET_REACQUIRE",
)


def _with_property_diagnostics(result: tuple[bool, str]) -> tuple[bool, str]:
    passed, note = result
    return passed, f"{note} properties_checked={','.join(PROPERTY_IDS)}"


def rising_edges(values: list[float], times: list[float], threshold: float = 0.45) -> list[float]:
    edges: list[float] = []
    for i in range(1, len(values)):
        if values[i - 1] < threshold <= values[i]:
            edges.append(times[i])
    return edges


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return 0.5 * (ordered[midpoint - 1] + ordered[midpoint])


def check_v3_009_lock_detector(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "ref_clk", "fb_clk", "rst_n", "lock"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing)

    times = [r["time"] for r in rows]
    ref_edges = rising_edges([r["ref_clk"] for r in rows], times, threshold=0.45)
    fb_edges = rising_edges([r["fb_clk"] for r in rows], times, threshold=0.45)
    if not ref_edges or not fb_edges:
        return False, f"too_few_edges ref={len(ref_edges)} fb={len(fb_edges)}"

    ref_periods = [right - left for left, right in zip(ref_edges, ref_edges[1:])]
    nominal_period = _median(ref_periods) if ref_periods else max(rows[-1]["time"] - rows[0]["time"], 1e-9)
    alignment_tolerance = 2.0e-9
    observation_delay = min(max(0.08 * nominal_period, 0.2e-9), 1.0e-9)
    reset_falls = [
        current["time"]
        for previous, current in zip(rows, rows[1:])
        if previous["rst_n"] > 0.45 >= current["rst_n"]
    ]
    reset_falls_sorted = sorted(reset_falls)
    valid_fb_edges = [
        fb_t for fb_t in fb_edges if (sample_signal_at(rows, "rst_n", fb_t) or 0.0) > 0.45
    ]
    events: list[tuple[float, int, bool, bool]] = []
    for ref_t in ref_edges:
        rst = sample_signal_at(rows, "rst_n", ref_t)
        if rst is None or rst <= 0.45:
            continue
        epoch = bisect_left(reset_falls_sorted, ref_t)
        reset_boundary = reset_falls_sorted[epoch - 1] if epoch else rows[0]["time"] - 1.0
        prior_fb = [fb_t for fb_t in valid_fb_edges if reset_boundary < fb_t <= ref_t]
        separation = ref_t - prior_fb[-1] if prior_fb else 1.0
        aligned = 0.0 <= separation <= alignment_tolerance
        lock_after = sample_signal_at(rows, "lock", ref_t + observation_delay)
        events.append((ref_t, epoch, aligned, bool(lock_after is not None and lock_after > 0.45)))

    streak = 0
    good_lock_after_three = 0
    acquisition_times: list[tuple[float, int]] = []
    acquired_in_streak = False
    early_locks = 0
    late_lock_failures = 0
    mismatch_clears = 0
    mismatch_failures = 0
    current_epoch: int | None = None
    for ref_t, epoch, aligned, lock_high in events:
        if current_epoch is None:
            current_epoch = epoch
        elif epoch != current_epoch:
            streak = 0
            acquired_in_streak = False
            current_epoch = epoch
        if aligned:
            streak += 1
            if streak >= 3:
                if lock_high:
                    good_lock_after_three += 1
                    if not acquired_in_streak:
                        acquisition_times.append((ref_t, epoch))
                        acquired_in_streak = True
                else:
                    late_lock_failures += 1
            if streak < 3 and lock_high:
                early_locks += 1
        else:
            if lock_high:
                mismatch_failures += 1
            else:
                mismatch_clears += 1
            streak = 0
            acquired_in_streak = False

    reset_probe_times = [time_s + observation_delay for time_s in reset_falls]
    if rows[0]["rst_n"] < 0.45:
        reset_probe_times.insert(0, rows[0]["time"] + observation_delay)
    reset_samples = [sample_signal_at(rows, "lock", time_s) for time_s in reset_probe_times]
    reset_low = len(reset_samples) >= 1 and all(
        value is not None and value < 0.45 for value in reset_samples
    )
    reset_reacquire = any(
        first_epoch < second_epoch
        for _, first_epoch in acquisition_times
        for _, second_epoch in acquisition_times
    )
    ok = (
        reset_low
        and early_locks == 0
        and late_lock_failures == 0
        and mismatch_failures == 0
        and mismatch_clears >= 1
        and good_lock_after_three >= 2
        and reset_reacquire
    )
    aligned_count = sum(1 for _, _, aligned, _ in events if aligned)
    mismatch_count = sum(1 for _, _, aligned, _ in events if not aligned)
    return ok, (
        f"events={len(events)} aligned={aligned_count} mismatch={mismatch_count} "
        f"good_lock_after_three={good_lock_after_three} early_locks={early_locks} "
        f"late_lock_failures={late_lock_failures} "
        f"mismatch_clears={mismatch_clears} mismatch_failures={mismatch_failures} "
        f"reset_low={reset_low} acquisitions={len(acquisition_times)} "
        f"reset_reacquire={reset_reacquire}"
    )

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

CHECKER_ID = "v4_009_lock_detector"


def check(rows: list[dict[str, float]]) -> tuple[bool, str]:
    return _with_property_diagnostics(check_v3_009_lock_detector(rows))


CHECKER: Checker = check
