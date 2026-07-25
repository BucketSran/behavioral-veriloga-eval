"""Task-specific checker for canonical v4 DUT 001."""
from __future__ import annotations

from ..api import Checker
def check_bbpd(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "data", "clk", "retimed_data", "up", "down"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/data/clk/retimed_data/up/down"

    vth = 0.45
    data_edges = [
        i
        for i in range(1, len(rows))
        if rows[i - 1]["data"] < vth <= rows[i]["data"] or rows[i - 1]["data"] > vth >= rows[i]["data"]
    ]
    up_edges = [i for i in range(1, len(rows)) if rows[i - 1]["up"] < vth <= rows[i]["up"]]
    down_edges = [i for i in range(1, len(rows)) if rows[i - 1]["down"] < vth <= rows[i]["down"]]

    if len(data_edges) < 6:
        return False, "not enough data edges"

    overlap = sum(1 for r in rows if r["up"] > vth and r["down"] > vth)
    overlap_frac = overlap / max(len(rows), 1)

    edge_trigger_ok = len(up_edges) + len(down_edges) >= max(4, len(data_edges) // 4)
    pulse_presence_ok = len(up_edges) >= 2 and len(down_edges) >= 2
    non_overlap_ok = overlap == 0

    directional_counts = {
        "up_expected": 0,
        "down_expected": 0,
        "up_correct": 0,
        "down_correct": 0,
        "none_expected": 0,
        "none_correct": 0,
        "wrong": 0,
        "missing": 0,
        "false_pulse": 0,
    }
    response_window_s = 0.2e-9
    for edge_idx in data_edges:
        clk_high = rows[edge_idx]["clk"] > vth
        retimed_high = rows[edge_idx]["retimed_data"] > vth
        if clk_high and not retimed_high:
            expected = "up"
        elif not clk_high and retimed_high:
            expected = "down"
        else:
            expected = "none"

        edge_time = rows[edge_idx]["time"]
        window_rows = []
        for row in rows[edge_idx:]:
            if row["time"] > edge_time + response_window_s:
                break
            window_rows.append(row)
        if expected == "none":
            directional_counts["none_expected"] += 1
            if any(row["up"] > vth or row["down"] > vth for row in window_rows):
                directional_counts["false_pulse"] += 1
            else:
                directional_counts["none_correct"] += 1
            continue

        directional_counts[f"{expected}_expected"] += 1
        wrong = "down" if expected == "up" else "up"
        expected_hit = any(row[expected] > vth for row in window_rows)
        wrong_hit = any(row[wrong] > vth for row in window_rows)
        if expected_hit and not wrong_hit:
            directional_counts[f"{expected}_correct"] += 1
        elif wrong_hit:
            directional_counts["wrong"] += 1
        else:
            directional_counts["missing"] += 1

    directional_ok = (
        directional_counts["up_expected"] >= 2
        and directional_counts["down_expected"] >= 2
        and directional_counts["up_correct"] >= max(2, int(0.75 * directional_counts["up_expected"]))
        and directional_counts["down_correct"] >= max(2, int(0.75 * directional_counts["down_expected"]))
        and directional_counts["wrong"] == 0
        and directional_counts["none_expected"] >= 2
        and directional_counts["false_pulse"] == 0
    )
    ok = edge_trigger_ok and pulse_presence_ok and non_overlap_ok and directional_ok
    return ok, (
        f"data_edges={len(data_edges)} up_edges={len(up_edges)} down_edges={len(down_edges)} "
        f"overlap_frac={overlap_frac:.4f} "
        f"direction_up={directional_counts['up_correct']}/{directional_counts['up_expected']} "
        f"direction_down={directional_counts['down_correct']}/{directional_counts['down_expected']} "
        f"none={directional_counts['none_correct']}/{directional_counts['none_expected']} "
        f"wrong_direction={directional_counts['wrong']} missing_direction={directional_counts['missing']} "
        f"false_pulse={directional_counts['false_pulse']}"
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

def check_v4_bbpd(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "data", "clk", "retimed_data", "up", "down"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0])) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing)

    data_edges = [
        (index, "rising" if rows[index - 1]["data"] < 0.45 <= rows[index]["data"] else "falling")
        for index in range(1, len(rows))
        if (
            rows[index - 1]["data"] < 0.45 <= rows[index]["data"]
            or rows[index - 1]["data"] > 0.45 >= rows[index]["data"]
        )
    ]
    clock_edges = sorted(
        _v4_edge_times(rows, "clk", rising=True)
        + _v4_edge_times(rows, "clk", rising=False)
    )
    rail_failures: list[str] = []
    clear_failures: list[str] = []
    coverage = {
        "up": 0,
        "down": 0,
        "none": 0,
        "rising_direction": 0,
        "falling_direction": 0,
        "clear": 0,
    }
    checked_pulses = 0
    overlap = sum(1 for row in rows if row["up"] > 0.45 and row["down"] > 0.45)
    overlap_frac = overlap / max(len(rows), 1)
    for index, polarity in data_edges:
        edge_time = rows[index]["time"]
        clk_high = rows[index]["clk"] > 0.45
        retimed_high = rows[index]["retimed_data"] > 0.45
        expected = "up" if clk_high and not retimed_high else "down" if not clk_high and retimed_high else ""
        window = [row for row in rows[index:] if row["time"] <= edge_time + 0.25e-9]
        if not window:
            continue
        if expected:
            checked_pulses += 1
            coverage[expected] += 1
            coverage[f"{polarity}_direction"] += 1
            inactive = "down" if expected == "up" else "up"
            expected_peak = max(row[expected] for row in window)
            inactive_peak = max(row[inactive] for row in window)
            if expected_peak < 0.81:
                rail_failures.append(
                    f"{expected}@{edge_time * 1e9:.3f}ns_high={expected_peak:.3f}<0.810"
                )
            if inactive_peak > 0.09:
                rail_failures.append(
                    f"{inactive}@{edge_time * 1e9:.3f}ns_low={inactive_peak:.3f}>0.090"
                )
            next_clock = next((time_s for time_s in clock_edges if time_s > edge_time + 1e-13), None)
            if next_clock is None:
                clear_failures.append(f"{expected}@{edge_time * 1e9:.3f}ns_no_following_clk")
                continue
            up_after = sample_signal_at(rows, "up", next_clock + 0.10e-9)
            down_after = sample_signal_at(rows, "down", next_clock + 0.10e-9)
            if up_after is None or down_after is None or up_after > 0.09 or down_after > 0.09:
                clear_failures.append(
                    f"clk@{next_clock * 1e9:.3f}ns_up={up_after}_down={down_after}"
                )
            else:
                coverage["clear"] += 1
        else:
            coverage["none"] += 1
            up_peak = max(row["up"] for row in window)
            down_peak = max(row["down"] for row in window)
            if up_peak > 0.09 or down_peak > 0.09:
                rail_failures.append(
                    f"none@{edge_time * 1e9:.3f}ns_up={up_peak:.3f}_down={down_peak:.3f}"
                )

    coverage_ok = (
        coverage["up"] >= 1
        and coverage["down"] >= 1
        and coverage["none"] >= 1
        and coverage["rising_direction"] >= 1
        and coverage["falling_direction"] >= 1
        and coverage["clear"] >= 1
    )
    ok = coverage_ok and overlap == 0 and checked_pulses >= 2 and not rail_failures and not clear_failures
    return ok, (
        f"data_edges={len(data_edges)} strict_pulses={checked_pulses} "
        f"overlap_frac={overlap_frac:.4f} coverage={coverage} "
        f"rail_failures={len(rail_failures)} clear_failures={len(clear_failures)}"
        + (" rail_detail=" + ";".join(rail_failures[:4]) if rail_failures else "")
        + (" clear_detail=" + ";".join(clear_failures[:4]) if clear_failures else "")
    )

CHECKER_ID = "v4_001_bang_bang_phase_detector"
CHECKER: Checker = check_v4_bbpd
