"""Compatibility checker for the released v4 crossing-metric-writer task."""

from __future__ import annotations

from ..api import Checker
from .stimulus_relative import (
    crossings,
    diagnostic,
    pass_note,
    probe_time,
    require_signals,
    sample,
)


PROPERTY_IDS = (
    "P_FILE_OPEN",
    "P_FIRST_RISING_CROSSING",
    "P_RECORDED_TIME",
    "P_DONE_LATCH",
    "P_SINGLE_RECORD",
)


def check_file_metric_writer(
    rows: list[dict[str, float]],
) -> tuple[bool, str]:
    missing = require_signals(
        rows,
        {"time", "vin", "done"},
        "P_FIRST_RISING_CROSSING",
    )
    if missing is not None:
        return False, missing

    rising = crossings(rows, "vin", threshold=0.45, direction="rising")
    if not rising:
        return False, diagnostic(
            "P_FIRST_RISING_CROSSING",
            "missing_event",
            expected="vin_rising>=1",
            observed="vin_rising:0",
            event="full_trace",
        )

    cross_t = rising[0]
    before_t = rows[0]["time"] + 0.5 * max(0.0, cross_t - rows[0]["time"])
    after_t = probe_time(
        rows,
        cross_t,
        rising[1] if len(rising) > 1 else None,
        fraction=0.25,
    )
    before = sample(rows, "done", before_t)
    after = sample(rows, "done", after_t) if after_t is not None else None
    final = rows[-1].get("done")
    if before is None or after is None or final is None:
        return False, diagnostic(
            "P_DONE_LATCH",
            "invalid_trace",
            expected="done_probes",
            observed="missing_probe",
            event="vin_rise[0]",
        )

    if before >= 0.1:
        return False, diagnostic(
            "P_FIRST_RISING_CROSSING",
            "value_mismatch",
            expected="done_before<=0.1",
            observed=f"done_before:{before:.3f}",
            event="pre_vin_rise[0]",
        )
    if after <= 0.8 or final <= 0.8:
        return False, diagnostic(
            "P_DONE_LATCH",
            "value_mismatch",
            expected="done_after>=0.8",
            observed=f"done_after:{after:.3f},done_final:{final:.3f}",
            event="post_vin_rise[0]",
        )

    for index, extra_t in enumerate(rising[1:], start=1):
        next_t = rising[index + 1] if index + 1 < len(rising) else None
        probe_t = probe_time(rows, extra_t, next_t, fraction=0.25)
        extra_done = sample(rows, "done", probe_t) if probe_t is not None else None
        if extra_done is None or extra_done < 0.8:
            return False, diagnostic(
                "P_SINGLE_RECORD",
                "value_mismatch",
                expected="done_latched_after_extra_crossings",
                observed="done_low_after_extra_crossing",
                event="vin_rises[1:]",
            )

    return True, pass_note(
        PROPERTY_IDS,
        f"crossing_metric_writer crossings={len(rising)}",
    )


CHECKER_ID = "v4_074_crossing_metric_writer"
CHECKER: Checker = check_file_metric_writer
