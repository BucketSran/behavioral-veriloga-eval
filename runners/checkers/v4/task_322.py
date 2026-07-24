"""Task-specific checker for canonical v4 DUT 322."""
from __future__ import annotations

from ..api import Checker
from ..common.relative_events import event_period, sample_step


def _v4_topup_logic_high(row: dict[str, float], name: str, threshold: float = 0.45) -> bool:
    return float(row.get(name, 0.0)) > threshold

def _v4_rising(prev_v: float, now_v: float, vth: float = 0.45) -> bool:
    return now_v > vth and prev_v <= vth

def check_v4_1020_glitchless_clock_mux_selector(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "v4_1020 empty_trace"
    required = {"time", "clk_a", "clk_b", "sel", "rst", "enable", "clk_out", "switch_metric", "valid"}
    if not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0]))
        return False, "missing_columns=" + ",".join(missing)
    step = sample_step(rows)
    clock_periods = [
        period
        for period in (event_period(rows, "clk_a"), event_period(rows, "clk_b"))
        if period > 0.0
    ]
    if step <= 0.0 or not clock_periods:
        return False, (
            f"insufficient_clock_coverage rows={len(rows)} "
            f"sample_step={step:.4g} clock_periods={clock_periods}"
        )
    clock_period = max(clock_periods)
    settle_guard = max(3.0 * step, 0.08 * clock_period)
    edge_guard = max(3.0 * step, 0.12 * clock_period)
    active = 0
    pending = 0
    switched_at = -1.0
    first_edge_seen = False
    checked = out_errors = glitch_errors = metric_errors = valid_errors = clear_errors = 0
    valid_early_errors = 0
    reset_clear = disabled_clear = switch_seen = both_sources_seen = False
    src_seen: set[int] = set()
    inactive_time: float | None = None
    prev_clk_a = float(rows[0].get("clk_a", 0.0))
    prev_clk_b = float(rows[0].get("clk_b", 0.0))
    last_input_rise = -1.0
    prev_out = float(rows[0].get("clk_out", 0.0))
    switch_windows: list[dict[str, float | bool]] = []
    metric_high_outside_window_errors = 0
    for row in rows:
        t = float(row["time"])
        rst = _v4_topup_logic_high(row, "rst")
        clk_a = float(row["clk_a"])
        clk_b = float(row["clk_b"])
        enabled = _v4_topup_logic_high(row, "enable") and not rst
        if not enabled:
            if inactive_time is None:
                inactive_time = t
            inactive_ready = t >= inactive_time + settle_guard
            active = 0
            pending = 0
            first_edge_seen = False
            clear = abs(float(row["clk_out"])) < 0.08 and abs(float(row["switch_metric"])) < 0.08 and not _v4_topup_logic_high(row, "valid")
            disabled = not rst and not _v4_topup_logic_high(row, "enable")
            if rst and inactive_ready and clear:
                reset_clear = True
            if disabled and inactive_ready and clear:
                disabled_clear = True
            if inactive_ready and not clear:
                clear_errors += 1
            prev_out = float(row.get("clk_out", 0.0))
            prev_clk_a = clk_a
            prev_clk_b = clk_b
            prev_metric_high = _v4_topup_logic_high(row, "switch_metric")
            continue
        inactive_time = None
        pending = 1 if _v4_topup_logic_high(row, "sel") else 0
        both_low = float(row["clk_a"]) <= 0.45 and float(row["clk_b"]) <= 0.45
        if pending != active and both_low:
            active = pending
            switched_at = t
            switch_seen = True
            first_edge_seen = False
            switch_windows.append({"start": t, "end": t + clock_period, "seen": False})
        expected = float(row["clk_b" if active else "clk_a"])
        src_seen.add(active)
        now_out = float(row["clk_out"])
        if _v4_rising(prev_clk_a, clk_a) or _v4_rising(prev_clk_b, clk_b):
            last_input_rise = t
        if prev_out <= 0.45 and now_out > 0.45:
            if last_input_rise < 0 or t - last_input_rise > edge_guard:
                glitch_errors += 1
            first_edge_seen = True
        prev_out = now_out
        prev_clk_a = clk_a
        prev_clk_b = clk_b
        metric_high = _v4_topup_logic_high(row, "switch_metric")
        metric_in_window = False
        for window in switch_windows:
            if float(window["start"]) <= t <= float(window["end"]) + edge_guard:
                metric_in_window = True
            if bool(window["seen"]):
                continue
            if float(window["start"]) <= t <= float(window["end"]) + edge_guard and metric_high:
                window["seen"] = True
        if metric_high and not metric_in_window:
            metric_high_outside_window_errors += 1
        valid_high = _v4_topup_logic_high(row, "valid")
        valid_transition_grace = switched_at >= 0 and t <= switched_at + settle_guard
        if not first_edge_seen and valid_high and not valid_transition_grace:
            valid_early_errors += 1
            valid_errors += 1
        if not first_edge_seen or (switched_at >= 0 and t < switched_at + settle_guard):
            continue
        checked += 1
        if abs(now_out - expected) > 0.14:
            out_errors += 1
        if first_edge_seen and not valid_high:
            valid_errors += 1
    both_sources_seen = len(src_seen) >= 2
    metric_errors = (
        sum(not bool(window["seen"]) for window in switch_windows)
        + metric_high_outside_window_errors
    )
    out_budget = max(2, checked // 5)
    # Count one missing event once; dense waveform sampling must not dilute it.
    metric_budget = 0
    valid_budget = max(2, checked // 10)
    clear_budget = 2
    ok = (
        checked >= 8
        and reset_clear
        and disabled_clear
        and switch_seen
        and both_sources_seen
        and out_errors <= out_budget
        and glitch_errors <= 1
        and metric_errors == 0
        and valid_early_errors == 0
        and valid_errors <= valid_budget
        and clear_errors <= clear_budget
    )
    return ok, (
        f"v4_1020 checked={checked} sources={sorted(src_seen)} reset_clear={reset_clear} "
        f"disabled_clear={disabled_clear} switch_seen={switch_seen} out_errors={out_errors} glitch_errors={glitch_errors} "
        f"metric_errors={metric_errors} metric_high_outside_window_errors={metric_high_outside_window_errors} "
        f"valid_errors={valid_errors} valid_early_errors={valid_early_errors} clear_errors={clear_errors}; "
        f"P_ON_RESET_OR_WHEN_DISABLED_DRIVE mismatch_count={max(0, clear_errors - clear_budget) + int(not reset_clear) + int(not disabled_clear)}; "
        f"P_ROUTE_CLK_A_WHEN_SEL_IS mismatch_count={max(0, out_errors - out_budget) + int(not both_sources_seen)}; "
        f"P_WHEN_SEL_CHANGES_WAIT_UNTIL_BOTH mismatch_count={max(0, glitch_errors - 1) + int(not switch_seen)}; "
        f"P_EXPOSE_A_SWITCH_EVENT_ON_SWITCH mismatch_count={max(0, metric_errors - metric_budget) + int(not switch_seen)}; "
        f"P_ASSERT_VALID_AFTER_THE_SELECTED_SOURCE mismatch_count={valid_early_errors + max(0, valid_errors - valid_budget)}"
    )

CHECKER_ID = "v4_322_glitchless_clock_mux_selector"
CHECKER: Checker = check_v4_1020_glitchless_clock_mux_selector
