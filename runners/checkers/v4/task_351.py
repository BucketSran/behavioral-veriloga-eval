"""Task-specific checker for canonical v4 DUT 351."""
from __future__ import annotations

from bisect import bisect_left, bisect_right

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
    minimum_checks = {
        "P_RESET_DISABLE_CLEAR": 2,
        "P_PHASE_COMPARE": 4,
        "P_PHASE_CODE": 4,
        "P_DIVIDE_BY_FOUR_EDGES": 4,
        "P_LOCK_REACQUIRE": 6,
    }
    for item in results:
        minimum = minimum_checks[item.property_id]
        if item.checked < minimum:
            item.mismatch(
                expected=f"checked>={minimum}",
                observed=f"checked={item.checked}",
                time=0.0,
                gap=float(minimum - item.checked),
            )
    ok = all(item.mismatch_count == 0 for item in results)
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

def check_v4_351_pll_timing_monitor_system(rows: list[dict[str, float]]) -> tuple[bool, str]:
    ids = ["P_RESET_DISABLE_CLEAR", "P_PHASE_COMPARE", "P_PHASE_CODE", "P_DIVIDE_BY_FOUR_EDGES", "P_LOCK_REACQUIRE"]
    results = [PropertyResult(pid) for pid in ids]
    prop = {item.property_id: item for item in results}
    required = {"time", "ref_clk", "fb_clk", "rst", "enable", "up", "down", "lock", "reacquire", "div2_clk", "phase_3", "phase_2", "phase_1", "phase_0"}
    missing = _missing(rows, required, results)
    if missing:
        return missing

    times = [float(row["time"]) for row in rows]
    inactive_prefix = [0]
    for row in rows:
        inactive_prefix.append(
            inactive_prefix[-1]
            + int(_high(row, "rst") or not _high(row, "enable"))
        )

    def inactive_between(start_time: float, stop_time: float) -> bool:
        left = bisect_right(times, start_time)
        right = bisect_left(times, stop_time)
        return inactive_prefix[right] > inactive_prefix[left]

    for row in _representative_clear_rows(rows, has_enable=True):
        item = prop["P_RESET_DISABLE_CLEAR"]
        item.checked += 1
        code = _code(row, ["phase_0", "phase_1", "phase_2", "phase_3"])
        flags = sum(int(_high(row, name)) for name in ["up", "down", "lock", "reacquire", "div2_clk"])
        if code != 8 or flags:
            item.mismatch(expected="phase_code=8 flags=0", observed=f"phase_code={code} flags={flags}", time=float(row["time"]), gap=abs(code - 8) + flags)

    ref_edges = _rising_times(rows, "ref_clk")
    fb_edges = _rising_times(rows, "fb_clk")
    events = sorted([(time, "ref") for time in ref_edges] + [(time, "fb") for time in fb_edges])
    first: tuple[float, str] | None = None
    phase_est = 0
    good_count = 0
    was_locked = False
    bad_count = 0
    previous_event_time = times[0]
    for time, kind in events:
        state = _before(rows, time)
        crossed_clear_window = inactive_between(previous_event_time, time)
        previous_event_time = time
        if crossed_clear_window:
            first = None
            phase_est = 0
            good_count = 0
            was_locked = False
            bad_count = 0
        if _high(state, "rst") or not _high(state, "enable"):
            first = None
            phase_est = 0
            good_count = 0
            was_locked = False
            bad_count = 0
            continue
        if first is None:
            first = (time, kind)
            sample = _after(rows, time + 0.3e-9)
            item = prop["P_PHASE_COMPARE"]
            item.checked += 1
            expected_up = kind == "ref"
            expected_down = kind == "fb"
            observed = (_high(sample, "up"), _high(sample, "down"))
            if observed != (expected_up, expected_down):
                item.mismatch(expected=f"up/down={int(expected_up)}/{int(expected_down)}", observed=f"up/down={int(observed[0])}/{int(observed[1])}", time=time, gap=1.0)
            continue
        if first[1] == kind:
            first = (time, kind)
            continue
        first_kind = first[1]
        phase_est += 1 if first_kind == "ref" else -1
        phase_est = max(-8, min(7, phase_est))
        sample = _after(rows, time + 0.5e-9)
        item = prop["P_PHASE_CODE"]
        item.checked += 1
        observed_code = _code(sample, ["phase_0", "phase_1", "phase_2", "phase_3"])
        expected_code = phase_est + 8
        if observed_code != expected_code:
            item.mismatch(expected=f"phase_code={expected_code}", observed=f"phase_code={observed_code}", time=time, gap=abs(observed_code - expected_code))

        in_window = abs(phase_est) <= 2
        good_count = good_count + 1 if in_window else 0
        expected_lock = good_count >= 4
        if expected_lock:
            was_locked = True
        if was_locked and not in_window:
            bad_count += 1
        elif in_window:
            bad_count = 0
        expected_reacquire = was_locked and bad_count >= 2
        item = prop["P_LOCK_REACQUIRE"]
        item.checked += 1
        observed_pair = (_high(sample, "lock"), _high(sample, "reacquire"))
        expected_pair = (expected_lock, expected_reacquire)
        if observed_pair != expected_pair:
            item.mismatch(expected=f"lock/reacquire={int(expected_lock)}/{int(expected_reacquire)}", observed=f"lock/reacquire={int(observed_pair[0])}/{int(observed_pair[1])}", time=time, gap=float(sum(a != b for a, b in zip(observed_pair, expected_pair))))
        first = None

    expected_div = False
    edge_count = 0
    previous_fb_time = times[0]
    for edge in fb_edges:
        before = _before(rows, edge)
        if inactive_between(previous_fb_time, edge):
            expected_div = False
            edge_count = 0
        previous_fb_time = edge
        if _high(before, "rst") or not _high(before, "enable"):
            expected_div = False
            edge_count = 0
            continue
        edge_count += 1
        if edge_count == 2:
            expected_div = not expected_div
            edge_count = 0
        sample = _after(rows, edge + 0.5e-9)
        item = prop["P_DIVIDE_BY_FOUR_EDGES"]
        item.checked += 1
        observed = _high(sample, "div2_clk")
        if observed != expected_div:
            item.mismatch(expected=f"div2={int(expected_div)}", observed=f"div2={int(observed)}", time=edge, gap=1.0)
    return _finish(results)

CHECKER_ID = "v4_351_pll_timing_monitor_system"
CHECKER: Checker = check_v4_351_pll_timing_monitor_system
