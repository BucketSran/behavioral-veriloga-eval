"""Task-specific checker for canonical v4 DUT 359."""
from __future__ import annotations

from ..api import Checker
from .stimulus_relative import representative_clear_rows as _representative_clear_rows
from dataclasses import dataclass

VTH = 0.45

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

def check_v4_359_duty_cycle_corrector(rows: list[dict[str, float]]) -> tuple[bool, str]:
    ids = ["P_RESET_DISABLE_CLEAR", "P_DUTY_MEASUREMENT", "P_TRIM_DIRECTION", "P_EDGE_DELAY", "P_LOCK_QUALIFICATION"]
    results = [PropertyResult(pid) for pid in ids]
    prop = {item.property_id: item for item in results}
    required = {"time", "clk_in", "rst", "enable", "clk_out", "trim_3", "trim_2", "trim_1", "trim_0", "duty_metric", "locked"}
    missing = _missing(rows, required, results)
    if missing:
        return missing
    for row in _representative_clear_rows(rows, has_enable=True):
        item = prop["P_RESET_DISABLE_CLEAR"]
        item.checked += 1
        code = _code(row, ["trim_0", "trim_1", "trim_2", "trim_3"])
        flags = int(_high(row, "clk_out")) + int(_high(row, "locked"))
        metric = abs(float(row["duty_metric"]))
        if code != 0 or flags or metric > 0.08:
            item.mismatch(expected="trim=0 metric=0 flags=0", observed=f"trim={code} metric={metric:.5g} flags={flags}", time=float(row["time"]), gap=code + flags + metric)

    rises = _rising_times(rows, "clk_in")
    falls = _falling_times(rows, "clk_in")
    out_rises = _rising_times(rows, "clk_out")
    out_falls = _falling_times(rows, "clk_out")
    previous_code = 0
    good_count = 0
    for index in range(1, len(rises)):
        previous_rise = rises[index - 1]
        current_rise = rises[index]
        cycle_falls = [time for time in falls if previous_rise < time < current_rise]
        if not cycle_falls:
            continue
        state = _before(rows, current_rise)
        if _high(state, "rst") or not _high(state, "enable"):
            previous_code = 0
            good_count = 0
            continue
        expected_duty = (cycle_falls[0] - previous_rise) / (current_rise - previous_rise)
        sample = _after(rows, current_rise + 0.35e-9)
        item = prop["P_DUTY_MEASUREMENT"]
        item.checked += 1
        observed_duty = float(sample["duty_metric"])
        gap = abs(observed_duty - expected_duty)
        if gap > 0.035:
            item.mismatch(expected=f"duty={expected_duty:.5g}", observed=f"duty={observed_duty:.5g}", time=current_rise, gap=gap)
        expected_code = previous_code
        if expected_duty < 0.47:
            expected_code = min(15, previous_code + 1)
            good_count = 0
        elif expected_duty > 0.53:
            expected_code = max(0, previous_code - 1)
            good_count = 0
        else:
            good_count += 1
        observed_code = _code(sample, ["trim_0", "trim_1", "trim_2", "trim_3"])
        item = prop["P_TRIM_DIRECTION"]
        item.checked += 1
        if observed_code != expected_code:
            item.mismatch(expected=f"trim={expected_code}", observed=f"trim={observed_code}", time=current_rise, gap=abs(observed_code - expected_code))
        expected_lock = good_count >= 3
        observed_lock = _high(sample, "locked")
        item = prop["P_LOCK_QUALIFICATION"]
        item.checked += 1
        if observed_lock != expected_lock:
            item.mismatch(expected=f"lock={int(expected_lock)}", observed=f"lock={int(observed_lock)}", time=current_rise, gap=1.0)
        previous_code = expected_code

    for source, destinations, edge_name in [(time, out_rises, "rising") for time in rises] + [(time, out_falls, "falling") for time in falls]:
        state = _before(rows, source)
        if _high(state, "rst") or not _high(state, "enable"):
            continue
        destination = _nearest_after(destinations, source, limit=source + 0.5e-9)
        item = prop["P_EDGE_DELAY"]
        item.checked += 1
        if destination is None:
            item.mismatch(expected=f"matching_{edge_name}_edge", observed="missing_edge", time=source, gap=1.0)
            continue
        delay = destination - source
        code = _code(state, ["trim_0", "trim_1", "trim_2", "trim_3"])
        expected_delay = 0.0 if edge_name == "rising" else code * 5e-12
        gap = abs(delay - expected_delay)
        if gap > 35e-12:
            item.mismatch(expected=f"delay={expected_delay:.5g}", observed=f"delay={delay:.5g}", time=source, gap=gap)
    return _finish(results)

CHECKER_ID = "v4_359_duty_cycle_corrector"
CHECKER: Checker = check_v4_359_duty_cycle_corrector
