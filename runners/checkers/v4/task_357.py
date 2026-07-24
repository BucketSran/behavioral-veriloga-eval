"""Task-specific checker for canonical v4 DUT 357."""
from __future__ import annotations

from ..api import Checker
from .stimulus_relative import representative_clear_rows as _representative_clear_rows
from dataclasses import dataclass

VTH = 0.45
LOCK_WINDOW_STEPS = 2.0
UNIT_PHASE_DELAY = 40e-12
DECISION_SAMPLE_FRACTION = 0.5

@dataclass
class PropertyResult:
    property_id: str
    checked: int = 0
    mismatch_count: int = 0
    expected: str = "contract_satisfied"
    observed: str = "contract_satisfied"
    sample_time: float = 0.0
    metric_gap: float = 0.0

    def mismatch(self, *, expected: object, observed: object, time: float, gap: float = 0.0) -> None:
        self.mismatch_count += 1
        if self.mismatch_count == 1:
            self.expected = str(expected)
            self.observed = str(observed)
            self.sample_time = float(time)
            self.metric_gap = float(gap)

    def render(self) -> str:
        return (
            f"{self.property_id} checked={self.checked} mismatch_count={self.mismatch_count} "
            f"expected={self.expected} observed={self.observed} "
            f"sample_time={self.sample_time:.12g} metric_gap={self.metric_gap:.6g}"
        )

def _finish(results: list[PropertyResult]) -> tuple[bool, str]:
    ok = all(item.checked > 0 and item.mismatch_count == 0 for item in results)
    return ok, " ; ".join(item.render() for item in results)

def _missing(rows: list[dict[str, float]], required: set[str], results: list[PropertyResult]) -> tuple[bool, str] | None:
    missing = sorted(required - set(rows[0])) if rows else sorted(required)
    if not missing:
        return None
    observed = "missing_signals:" + ",".join(missing)
    for item in results:
        item.checked = 1
        item.mismatch(expected="complete_trace", observed=observed, time=0.0, gap=float(len(missing)))
    return _finish(results)

def _high(row: dict[str, float], signal: str, threshold: float = VTH) -> bool:
    return float(row.get(signal, 0.0)) > threshold

def _code(row: dict[str, float], bits_lsb_first: list[str]) -> int:
    return sum(1 << index for index, bit in enumerate(bits_lsb_first) if _high(row, bit))

def _rising_times(rows: list[dict[str, float]], signal: str, threshold: float = VTH) -> list[float]:
    result: list[float] = []
    for previous, current in zip(rows, rows[1:]):
        if float(previous[signal]) <= threshold < float(current[signal]):
            result.append(float(current["time"]))
    return result

def _falling_times(rows: list[dict[str, float]], signal: str, threshold: float = VTH) -> list[float]:
    result: list[float] = []
    for previous, current in zip(rows, rows[1:]):
        if float(previous[signal]) > threshold >= float(current[signal]):
            result.append(float(current["time"]))
    return result

def _before(rows: list[dict[str, float]], time: float) -> dict[str, float]:
    candidate = rows[0]
    for row in rows:
        if float(row["time"]) >= time:
            break
        candidate = row
    return candidate

def _after(rows: list[dict[str, float]], time: float) -> dict[str, float]:
    for row in rows:
        if float(row["time"]) >= time:
            return row
    return rows[-1]

def _nearest_after(times: list[float], time: float, *, limit: float | None = None) -> float | None:
    for value in times:
        if value >= time and (limit is None or value <= limit):
            return value
    return None

def _inactive_between(rows: list[dict[str, float]], start: float, stop: float) -> bool:
    return any(
        _high(row, "rst") or not _high(row, "enable")
        for row in rows
        if start < float(row["time"]) <= stop
    )

def _last_inactive_time(rows: list[dict[str, float]], stop: float) -> float:
    return max(
        (
            float(row["time"])
            for row in rows
            if float(row["time"]) < stop
            and (_high(row, "rst") or not _high(row, "enable"))
        ),
        default=float(rows[0]["time"]),
    )

def check_v4_357_bangbang_cdr_loop(rows: list[dict[str, float]]) -> tuple[bool, str]:
    ids = ["P_RESET_DISABLE_CLEAR", "P_BANGBANG_DECISION", "P_PHASE_CODE_UPDATE", "P_PHASE_ROTATION", "P_LOCK_QUALIFICATION"]
    results = [PropertyResult(pid) for pid in ids]
    prop = {item.property_id: item for item in results}
    required = {"time", "data_edge", "ref_clk", "rst", "enable", "recovered_clk", "early", "late", "phase_4", "phase_3", "phase_2", "phase_1", "phase_0", "lock"}
    missing = _missing(rows, required, results)
    if missing:
        return missing
    time_scale = float(rows[0].get("_time_scale", 1.0))
    for row in _representative_clear_rows(rows, has_enable=True):
        item = prop["P_RESET_DISABLE_CLEAR"]
        item.checked += 1
        code = _code(row, ["phase_0", "phase_1", "phase_2", "phase_3", "phase_4"])
        flags = sum(int(_high(row, name)) for name in ["recovered_clk", "early", "late", "lock"])
        if code != 16 or flags:
            item.mismatch(expected="phase_code=16 flags=0", observed=f"phase_code={code} flags={flags}", time=float(row["time"]), gap=abs(code - 16) + flags)

    recovered = _rising_times(rows, "recovered_clk")
    data = _rising_times(rows, "data_edge")
    ref_rise = _rising_times(rows, "ref_clk")
    ref_fall = _falling_times(rows, "ref_clk")
    rec_fall = _falling_times(rows, "recovered_clk")
    unit_estimates: list[tuple[float, float]] = []
    for source_time, destinations in [(time, recovered) for time in ref_rise] + [(time, rec_fall) for time in ref_fall]:
        before = _before(rows, source_time)
        if _high(before, "rst") or not _high(before, "enable"):
            continue
        code = _code(before, ["phase_0", "phase_1", "phase_2", "phase_3", "phase_4"])
        expected_destination = source_time + code * time_scale * UNIT_PHASE_DELAY
        destination = _nearest_after(destinations, source_time, limit=source_time + 0.45 * 10e-9)
        observation_stop = destination if destination is not None else expected_destination
        if (
            expected_destination > float(rows[-1]["time"])
            or _inactive_between(rows, source_time, observation_stop)
        ):
            continue
        if destination is None:
            last_inactive = _last_inactive_time(rows, source_time)
            polarity_synchronized = any(
                last_inactive < edge < source_time for edge in destinations
            )
            if not polarity_synchronized:
                continue
        item = prop["P_PHASE_ROTATION"]
        item.checked += 1
        if destination is None or code == 0:
            item.mismatch(expected="delayed_matching_edge", observed="missing_edge", time=source_time, gap=1.0)
            continue
        delay = destination - source_time
        estimate = delay / code
        unit_estimates.append((source_time, estimate))
        if delay <= 1e-12:
            item.mismatch(expected="positive_phase_delay", observed=f"delay={delay:.5g}", time=source_time, gap=1e-12 - delay)
    median_unit = sorted(value for _, value in unit_estimates)[len(unit_estimates) // 2] if unit_estimates else None

    previous_recovered: float | None = None
    previous_code = 16
    decisions = 0
    good_count = 0
    bad_count = 0
    expected_locked = False
    previous_phase_error_steps = 0.0
    lock_assert_seen = False
    unlock_seen = False
    out_of_window_seen = False
    for current in recovered:
        if previous_recovered is None:
            previous_recovered = current
            continue
        if any(
            _high(row, "rst") or not _high(row, "enable")
            for row in rows
            if previous_recovered < float(row["time"]) <= current
        ):
            previous_recovered = current
            previous_code = 16
            good_count = bad_count = 0
            expected_locked = False
            previous_phase_error_steps = 0.0
            continue
        candidates = [edge for edge in data if previous_recovered < edge <= current]
        if not candidates:
            previous_recovered = current
            continue
        data_edge = candidates[-1]
        expected_early = abs(data_edge - previous_recovered) < abs(current - data_edge)
        expected_late = not expected_early
        sample = _after(rows, current + time_scale * 0.4e-9)
        item = prop["P_BANGBANG_DECISION"]
        item.checked += 1
        observed = (_high(sample, "early"), _high(sample, "late"))
        if observed != (expected_early, expected_late):
            item.mismatch(expected=f"early/late={int(expected_early)}/{int(expected_late)}", observed=f"early/late={int(observed[0])}/{int(observed[1])}", time=current, gap=1.0)
        expected_code = max(0, min(31, previous_code + (1 if expected_late else -1)))
        observed_code = _code(sample, ["phase_0", "phase_1", "phase_2", "phase_3", "phase_4"])
        item = prop["P_PHASE_CODE_UPDATE"]
        item.checked += 1
        if observed_code != expected_code:
            item.mismatch(expected=f"phase_code={expected_code}", observed=f"phase_code={observed_code}", time=current, gap=abs(observed_code - expected_code))
        previous_code = expected_code
        decisions += 1
        item = prop["P_LOCK_QUALIFICATION"]
        item.checked += 1
        observed_lock = _high(sample, "lock")
        if median_unit is not None and median_unit > 0.0:
            if abs(data_edge - previous_recovered) < abs(current - data_edge):
                phase_error_steps = (
                    (data_edge - previous_recovered)
                    / (time_scale * UNIT_PHASE_DELAY)
                )
            else:
                phase_error_steps = (
                    (data_edge - current) / (time_scale * UNIT_PHASE_DELAY)
                )
            sampled_phase_error_steps = abs(
                previous_phase_error_steps
                + DECISION_SAMPLE_FRACTION
                * (phase_error_steps - previous_phase_error_steps)
            )
            previous_phase_error_steps = phase_error_steps
            if sampled_phase_error_steps <= LOCK_WINDOW_STEPS:
                good_count += 1
                bad_count = 0
                if good_count >= 4:
                    expected_locked = True
            else:
                good_count = 0
                if expected_locked:
                    out_of_window_seen = True
                    bad_count += 1
                    if bad_count >= 2:
                        expected_locked = False
                        if lock_assert_seen and not observed_lock:
                            unlock_seen = True
            if observed_lock != expected_locked:
                item.mismatch(
                    expected=(
                        f"lock={int(expected_locked)} "
                        f"sampled_phase_error_steps<={LOCK_WINDOW_STEPS:.4g}"
                    ),
                    observed=f"lock={int(observed_lock)}",
                    time=current,
                    gap=1.0,
                )
            if expected_locked and observed_lock:
                lock_assert_seen = True
        previous_recovered = current
    if not lock_assert_seen:
        prop["P_LOCK_QUALIFICATION"].mismatch(
            expected="lock_assertion_observed_after_four_in_window_decisions",
            observed="lock_assertion_not_activated",
            time=float(rows[-1]["time"]),
            gap=1.0,
        )
    if out_of_window_seen and not unlock_seen:
        prop["P_LOCK_QUALIFICATION"].mismatch(
            expected="lock_deassertion_observed_after_two_out_of_window_decisions",
            observed="unlock_not_activated",
            time=float(rows[-1]["time"]),
            gap=1.0,
        )
    if unit_estimates:
        median = sorted(value for _, value in unit_estimates)[len(unit_estimates) // 2]
        for time, value in unit_estimates:
            gap = abs(value - median)
            if median > 0 and gap > max(15e-12, 0.35 * median):
                prop["P_PHASE_ROTATION"].mismatch(expected=f"unit_delay~{median:.5g}", observed=f"unit_delay={value:.5g}", time=time, gap=gap)
    return _finish(results)

CHECKER_ID = "v4_357_bangbang_cdr_loop"
CHECKER: Checker = check_v4_357_bangbang_cdr_loop
