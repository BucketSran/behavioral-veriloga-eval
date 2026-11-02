"""Task-specific checker for canonical v4 DUT 312."""
from __future__ import annotations

import math
from bisect import bisect_left

from ..api import Checker
from .stimulus_relative import crossings, require_signals, sample


PROPERTY_IDS = (
    "P_ON_RESET_OR_WHEN_DISABLED_CLEAR",
    "P_CAPTURE_VIN_A_ON_RISING_CLK",
    "P_ESTIMATE_A_SKEW_PROXY_FROM_THE",
    "P_DRIVE_SKEW_METRIC_WITH_THE_ABSOLUTE",
    "P_ASSERT_ALARM_WHEN_SKEW_METRIC_EXCEEDS",
    "P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE",
)

TICK_S = 500e-12
TRANSITION_S = 200e-12
PROBE_DELAY_S = TRANSITION_S + 50e-12
TIME_EPS_S = 1e-15
VTH = 0.45
VDD = 0.9
VSS = 0.0
VCM = 0.45
SKEW_LIMIT = 40e-3
PROBE_SUPPORT_S = 0.24e-9
MIN_LOW_SKEW_CHECKS = 4


def _sample(rows: list[dict[str, float]], signal: str, time_s: float) -> float:
    value = sample(rows, signal, time_s)
    assert value is not None
    return float(value)


def _has_probe_support(times: list[float], time_s: float) -> bool:
    index = bisect_left(times, time_s)
    return any(
        abs(times[candidate] - time_s) <= PROBE_SUPPORT_S
        for candidate in (index - 1, index)
        if 0 <= candidate < len(times)
    )


def _transition_value(
    start_value: float, target_value: float, start_time_s: float, time_s: float
) -> float:
    if time_s <= start_time_s:
        return start_value
    fraction = (time_s - start_time_s) / TRANSITION_S
    if fraction >= 1.0:
        return target_value
    return start_value + (target_value - start_value) * max(0.0, fraction)


def check_v4_312_interleaved_adc_skew_monitor(rows: list[dict[str, float]]) -> tuple[bool, str]:
    missing = require_signals(
        rows,
        {
            "time",
            "vin_a",
            "vin_b",
            "clk_a",
            "clk_b",
            "rst",
            "enable",
            "skew_metric",
            "magnitude_metric",
            "alarm",
        },
        PROPERTY_IDS[0],
    )
    if missing:
        return False, missing

    clock_events = sorted(
        [(time_s, "a") for time_s in crossings(rows, "clk_a", threshold=VTH, direction="rising")]
        + [(time_s, "b") for time_s in crossings(rows, "clk_b", threshold=VTH, direction="rising")]
    )
    sa_start = sb_start = sa_target = sb_target = VCM
    sa_start_time = sb_start_time = float(rows[0]["time"])
    ready_start = ready_target = VSS
    ready_start_time = float(rows[0]["time"])
    ready_a = ready_b = False
    consecutive = 0
    checked = skew_errors = mag_errors = alarm_errors = 0
    reset_clear = late_reset_clear = late_reset_violation = disabled_clear = False
    high_skew_seen = alarm_seen = False
    high_skew_checks = low_skew_checks = 0
    first_high_alarm_low_seen = False
    first_mismatch = ""
    saw_active = False
    event_index = 0
    tick_index = max(0, math.ceil((float(rows[0]["time"]) - TIME_EPS_S) / TICK_S))
    stop_time = float(rows[-1]["time"])
    times = [float(row["time"]) for row in rows]

    def update_ready_target(event_time_s: float) -> None:
        nonlocal ready_start, ready_target, ready_start_time
        new_target = VDD if ready_a and ready_b else VSS
        if new_target != ready_target:
            ready_start = _transition_value(
                ready_start, ready_target, ready_start_time, event_time_s
            )
            ready_target = new_target
            ready_start_time = event_time_s

    while True:
        tick_time = tick_index * TICK_S
        probe_time = tick_time + PROBE_DELAY_S
        if probe_time > stop_time + TIME_EPS_S:
            break

        while (
            event_index < len(clock_events)
            and clock_events[event_index][0] <= tick_time + TIME_EPS_S
        ):
            event_time, channel = clock_events[event_index]
            rst_at_edge = _sample(rows, "rst", event_time) > VTH
            enabled_at_edge = _sample(rows, "enable", event_time) > VTH
            if rst_at_edge or not enabled_at_edge:
                sa_start = _transition_value(sa_start, sa_target, sa_start_time, event_time)
                sb_start = _transition_value(sb_start, sb_target, sb_start_time, event_time)
                sa_target = sb_target = VCM
                sa_start_time = sb_start_time = event_time
                ready_a = ready_b = False
                consecutive = 0
            else:
                if channel == "a":
                    sa_start = _transition_value(
                        sa_start, sa_target, sa_start_time, event_time
                    )
                    sa_target = _sample(rows, "vin_a", event_time)
                    sa_start_time = event_time
                    ready_a = True
                else:
                    sb_start = _transition_value(
                        sb_start, sb_target, sb_start_time, event_time
                    )
                    sb_target = _sample(rows, "vin_b", event_time)
                    sb_start_time = event_time
                    ready_b = True
            update_ready_target(event_time)
            event_index += 1

        rst = _sample(rows, "rst", tick_time) > VTH
        enabled = _sample(rows, "enable", tick_time) > VTH
        observed_skew = _sample(rows, "skew_metric", probe_time)
        observed_mag = _sample(rows, "magnitude_metric", probe_time)
        observed_alarm = _sample(rows, "alarm", probe_time) > VTH

        if rst:
            cleared = (
                observed_skew < 0.1 and observed_mag < 0.1 and not observed_alarm
            )
            if saw_active:
                late_reset_clear = late_reset_clear or cleared
                late_reset_violation = late_reset_violation or not cleared
            else:
                reset_clear = reset_clear or cleared
            consecutive = 0
            tick_index += 1
            continue
        if not enabled:
            disabled_clear = disabled_clear or (
                observed_skew < 0.1 and observed_mag < 0.1 and not observed_alarm
            )
            consecutive = 0
            tick_index += 1
            continue
        expected_ready = _transition_value(
            ready_start, ready_target, ready_start_time, tick_time
        ) > VTH
        if not expected_ready:
            consecutive = 0
            tick_index += 1
            continue

        saw_active = True
        expected_sa = _transition_value(sa_start, sa_target, sa_start_time, tick_time)
        expected_sb = _transition_value(sb_start, sb_target, sb_start_time, tick_time)
        expected_skew = abs(expected_sa - expected_sb)
        expected_mag = 0.5 * (abs(expected_sa - VCM) + abs(expected_sb - VCM))
        if expected_skew > SKEW_LIMIT:
            consecutive += 1
            high_skew_checks += 1
            high_skew_seen = True
        else:
            consecutive = 0
            if _has_probe_support(times, probe_time):
                low_skew_checks += 1
        expected_alarm = consecutive >= 2
        if expected_skew > SKEW_LIMIT and consecutive == 1 and not observed_alarm:
            first_high_alarm_low_seen = True
        checked += 1
        alarm_seen = alarm_seen or observed_alarm
        if abs(observed_skew - expected_skew) > 0.08:
            skew_errors += 1
            if not first_mismatch:
                first_mismatch = (
                    "P_DRIVE_SKEW_METRIC_WITH_THE_ABSOLUTE "
                    f"signal=skew_metric time={probe_time:.6e} "
                    f"expected={expected_skew:.6g} observed={observed_skew:.6g} tolerance=0.08"
                )
        if abs(observed_mag - expected_mag) > 0.08:
            mag_errors += 1
            if not first_mismatch:
                first_mismatch = (
                    "P_DRIVE_SKEW_METRIC_WITH_THE_ABSOLUTE "
                    f"signal=magnitude_metric time={probe_time:.6e} "
                    f"expected={expected_mag:.6g} observed={observed_mag:.6g} tolerance=0.08"
                )
        if observed_alarm != expected_alarm:
            alarm_errors += 1
            if not first_mismatch:
                first_mismatch = (
                    "P_ASSERT_ALARM_WHEN_SKEW_METRIC_EXCEEDS "
                    f"signal=alarm time={probe_time:.6e} "
                    f"expected={int(expected_alarm)} observed={int(observed_alarm)} tolerance=logic"
                )
        tick_index += 1
    ok = (
        checked >= 20
        and reset_clear
        and late_reset_clear
        and not late_reset_violation
        and disabled_clear
        and high_skew_seen
        and low_skew_checks >= MIN_LOW_SKEW_CHECKS
        and alarm_seen
        and first_high_alarm_low_seen
        and skew_errors == 0
        and mag_errors == 0
        and alarm_errors == 0
    )
    summary = (
        f"v4_312 checked={checked} reset_clear={reset_clear} late_reset_clear={late_reset_clear} "
        f"late_reset_violation={late_reset_violation} "
        f"disabled_clear={disabled_clear} "
        f"high_skew={high_skew_seen} low_skew={low_skew_checks >= MIN_LOW_SKEW_CHECKS} "
        f"high_skew_checks={high_skew_checks} low_skew_checks={low_skew_checks} "
        f"alarm_seen={alarm_seen} "
        f"first_high_alarm_low={first_high_alarm_low_seen} "
        f"skew_errors={skew_errors} mag_errors={mag_errors} alarm_errors={alarm_errors}"
    )
    if not ok and first_mismatch:
        summary += f"; first_mismatch={first_mismatch}"
    property_mismatches = {
        "P_ON_RESET_OR_WHEN_DISABLED_CLEAR": int(
            not reset_clear
            or not late_reset_clear
            or late_reset_violation
            or not disabled_clear
        ),
        "P_CAPTURE_VIN_A_ON_RISING_CLK": skew_errors + mag_errors,
        "P_ESTIMATE_A_SKEW_PROXY_FROM_THE": skew_errors,
        "P_DRIVE_SKEW_METRIC_WITH_THE_ABSOLUTE": skew_errors + mag_errors,
        "P_ASSERT_ALARM_WHEN_SKEW_METRIC_EXCEEDS": alarm_errors,
        "P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE": 0,
    }
    summary += "; " + "; ".join(
        f"{property_id} mismatch_count={property_mismatches[property_id]}"
        for property_id in PROPERTY_IDS
    )
    return ok, summary

CHECKER_ID = "v4_312_interleaved_adc_skew_monitor"
CHECKER: Checker = check_v4_312_interleaved_adc_skew_monitor
