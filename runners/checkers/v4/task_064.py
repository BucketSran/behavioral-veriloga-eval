"""Task-specific checker for canonical v4 DUT 064."""
from __future__ import annotations

from ..api import Checker
from .stimulus_relative import (
    crossings,
    diagnostic,
    event_label,
    pass_note,
    probe_time,
    require_signals,
    sample,
)


PROPERTIES = (
    "P_RESET_DISABLE_CLEAR",
    "P_STABLE_EDGE_QUALIFICATION",
    "P_DELAYED_EDGE_EMISSION",
    "P_NARROW_GLITCH_REJECTION",
    "P_VALID_EMISSION_PULSE",
    "P_BIDIRECTIONAL_LEVELS",
)

DEFAULT_VTH = 0.45
DEFAULT_TICK_S = 250e-12
DEFAULT_MIN_WIDTH_TICKS = 3
DEFAULT_DELAY_TICKS = 4
DEFAULT_QUALIFICATION_S = DEFAULT_MIN_WIDTH_TICKS * DEFAULT_TICK_S
DEFAULT_EMISSION_MIN_S = (
    DEFAULT_MIN_WIDTH_TICKS + DEFAULT_DELAY_TICKS - 0.4
) * DEFAULT_TICK_S
DEFAULT_EMISSION_MAX_S = (
    DEFAULT_MIN_WIDTH_TICKS + DEFAULT_DELAY_TICKS + 2.4
) * DEFAULT_TICK_S
DEFAULT_STATUS_PULSE_MAX_S = 4.0 * DEFAULT_TICK_S


def _match_status_pulses(
    event_times: list[float],
    rising_times: list[float],
    falling_times: list[float],
    *,
    before_s: float,
    after_s: float,
) -> tuple[int, int, list[float]]:
    matched_rises: set[int] = set()
    misses = 0
    widths: list[float] = []
    for event_time in event_times:
        candidates = [
            (index, rise_time)
            for index, rise_time in enumerate(rising_times)
            if index not in matched_rises
            and event_time - before_s <= rise_time <= event_time + after_s
        ]
        if len(candidates) != 1:
            misses += 1
            continue
        rise_index, rise_time = candidates[0]
        fall_time = next((time_s for time_s in falling_times if time_s > rise_time), None)
        if fall_time is None or fall_time - rise_time > DEFAULT_STATUS_PULSE_MAX_S:
            misses += 1
            continue
        matched_rises.add(rise_index)
        widths.append(fall_time - rise_time)
    extras = len(rising_times) - len(matched_rises)
    return misses, extras, widths


def check_v4_edge_delay_line_with_deglitch(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "rst", "enable", "vout", "edge_valid", "rejected"}
    invalid = require_signals(rows, required, "P_RESET_DISABLE_CLEAR")
    if invalid:
        return False, invalid
    reset_rows = [row for row in rows if row["rst"] > DEFAULT_VTH]
    if not reset_rows:
        return False, diagnostic(
            "P_RESET_DISABLE_CLEAR",
            "insufficient_coverage",
            expected="reset_assertion_observed",
            observed="reset_samples=0",
            event="full_trace",
        )
    reset_peak = max(max(row["vout"], row["edge_valid"], row["rejected"]) for row in reset_rows)
    if reset_peak > 0.16:
        return False, diagnostic(
            "P_RESET_DISABLE_CLEAR",
            "semantic_mismatch",
            expected="outputs<=0.16_during_reset",
            observed=f"max_output={reset_peak:.3f}",
            event="rst_high",
        )
    input_events = sorted(
        [(time_s, 1) for time_s in crossings(rows, "vin", threshold=DEFAULT_VTH, direction="rising")]
        + [(time_s, -1) for time_s in crossings(rows, "vin", threshold=DEFAULT_VTH, direction="falling")]
    )
    output_events = sorted(
        [(time_s, 1) for time_s in crossings(rows, "vout", threshold=DEFAULT_VTH, direction="rising")]
        + [(time_s, -1) for time_s in crossings(rows, "vout", threshold=DEFAULT_VTH, direction="falling")]
    )
    input_edges = [time_s for time_s, _ in input_events]
    output_edges = [time_s for time_s, _ in output_events]
    qualified_events: list[tuple[float, int]] = []
    narrow_events: list[tuple[float, float]] = []
    skip_as_narrow_reversal: set[int] = set()
    for index, (in_edge, direction) in enumerate(input_events):
        if index in skip_as_narrow_reversal:
            continue
        next_edge = input_events[index + 1][0] if index + 1 < len(input_events) else rows[-1]["time"]
        rst_at_edge = sample(rows, "rst", in_edge)
        enable_at_edge = sample(rows, "enable", in_edge)
        if (
            rst_at_edge is None
            or enable_at_edge is None
            or rst_at_edge > DEFAULT_VTH
            or enable_at_edge <= DEFAULT_VTH
        ):
            continue
        if next_edge - in_edge < DEFAULT_QUALIFICATION_S:
            narrow_events.append((in_edge, next_edge))
            skip_as_narrow_reversal.add(index + 1)
            continue
        emit_probe = min(rows[-1]["time"], in_edge + DEFAULT_EMISSION_MAX_S)
        enable_at_emit = sample(rows, "enable", emit_probe)
        rst_at_emit = sample(rows, "rst", emit_probe)
        if (
            enable_at_emit is not None
            and rst_at_emit is not None
            and enable_at_emit > DEFAULT_VTH
            and rst_at_emit <= DEFAULT_VTH
        ):
            qualified_events.append((in_edge, direction))

    matched_output_indices: set[int] = set()
    delays: list[float] = []
    for in_edge, direction in qualified_events:
        match = next(
            (
                (index, out_edge)
                for index, (out_edge, out_direction) in enumerate(output_events)
                if index not in matched_output_indices
                and out_direction == direction
                and DEFAULT_EMISSION_MIN_S
                <= out_edge - in_edge
                <= DEFAULT_EMISSION_MAX_S
            ),
            None,
        )
        if match is None:
            continue
        output_index, out_edge = match
        matched_output_indices.add(output_index)
        delays.append(out_edge - in_edge)
    valid_misses, extra_valid_pulses, valid_widths = _match_status_pulses(
        [out_edge for index, (out_edge, _) in enumerate(output_events) if index in matched_output_indices],
        crossings(rows, "edge_valid", threshold=DEFAULT_VTH, direction="rising"),
        crossings(rows, "edge_valid", threshold=DEFAULT_VTH, direction="falling"),
        before_s=0.2e-9,
        after_s=1.0e-9,
    )
    rejected_misses, extra_rejected_pulses, rejected_widths = _match_status_pulses(
        [reverse_edge for _, reverse_edge in narrow_events],
        crossings(rows, "rejected", threshold=DEFAULT_VTH, direction="rising"),
        crossings(rows, "rejected", threshold=DEFAULT_VTH, direction="falling"),
        before_s=0.2e-9,
        after_s=1.5e-9,
    )
    disabled_clear_checks = 0
    disabled_clear_failures = 0
    enable_falls = crossings(rows, "enable", threshold=DEFAULT_VTH, direction="falling")
    enable_rises = crossings(rows, "enable", threshold=DEFAULT_VTH, direction="rising")
    for disable_t in enable_falls:
        next_enable = next((rise for rise in enable_rises if rise > disable_t), None)
        clear_t = probe_time(rows, disable_t, next_enable, fraction=0.35)
        clear_values = (
            [sample(rows, signal, clear_t) for signal in ("vout", "edge_valid", "rejected")]
            if clear_t is not None
            else []
        )
        if not clear_values or any(value is None for value in clear_values):
            continue
        disabled_clear_checks += 1
        if any(value is not None and value >= 0.2 for value in clear_values):
            disabled_clear_failures += 1
    disabled_clears = disabled_clear_checks >= 1 and disabled_clear_failures == 0
    min_delay = min(delays, default=0.0)
    max_delay = max(delays, default=0.0)
    qualified_directions = {direction for _, direction in qualified_events}
    ok = (
        qualified_directions == {-1, 1}
        and len(matched_output_indices) == len(qualified_events)
        and len(matched_output_indices) == len(output_events)
        and valid_misses == 0
        and extra_valid_pulses == 0
        and len(narrow_events) >= 1
        and rejected_misses == 0
        and extra_rejected_pulses == 0
        and disabled_clears
        and DEFAULT_EMISSION_MIN_S <= min_delay <= DEFAULT_EMISSION_MAX_S
        and max_delay <= DEFAULT_EMISSION_MAX_S
    )
    summary = (
        f"input_edges={len(input_edges)} output_edges={len(output_edges)} "
        f"qualified={len(qualified_events)} matched={len(matched_output_indices)} "
        f"directions={sorted(qualified_directions)} "
        f"narrow={len(narrow_events)} rejected_misses={rejected_misses} "
        f"extra_rejected_pulses={extra_rejected_pulses} rejected_widths={rejected_widths} "
        f"valid_misses={valid_misses} extra_valid_pulses={extra_valid_pulses} "
        f"valid_widths={valid_widths} delay_range=({min_delay:.3e},{max_delay:.3e}) "
        f"disabled_clear_checks={disabled_clear_checks} "
        f"disabled_clear_failures={disabled_clear_failures}"
    )
    if not ok:
        output_mapping_failed = (
            qualified_directions != {-1, 1}
            or len(matched_output_indices) != len(qualified_events)
            or len(matched_output_indices) != len(output_events)
            or not (
                DEFAULT_EMISSION_MIN_S
                <= min_delay
                <= max_delay
                <= DEFAULT_EMISSION_MAX_S
            )
        )
        property_id = (
            "P_DELAYED_EDGE_EMISSION"
            if output_mapping_failed
            else "P_RESET_DISABLE_CLEAR"
            if not disabled_clears
            else "P_VALID_EMISSION_PULSE"
            if valid_misses or extra_valid_pulses
            else "P_NARROW_GLITCH_REJECTION"
            if rejected_misses or extra_rejected_pulses
            else "P_DELAYED_EDGE_EMISSION"
        )
        return False, diagnostic(
            property_id,
            "semantic_mismatch",
            expected="qualified_edges_match_once,status_pulses_bounded,no_extra_pulses,all_outputs_clear",
            observed=summary.replace(" ", "_"),
            event="full_trace",
        )
    return True, pass_note(PROPERTIES, summary)

CHECKER_ID = "v4_064_edge_delay_line_with_deglitch"
CHECKER: Checker = check_v4_edge_delay_line_with_deglitch
