"""Task-specific checker for canonical v4 DUT 354."""
from __future__ import annotations

from ..api import Checker
from .stimulus_relative import representative_clear_rows as _representative_clear_rows
from dataclasses import dataclass

VCM = 0.45
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

def check_v4_354_dfe_receiver_2tap(rows: list[dict[str, float]]) -> tuple[bool, str]:
    ids = ["P_RESET_CLEAR", "P_TWO_TAP_FEEDBACK", "P_CORRECTED_INPUT", "P_CLOCKED_DECISION", "P_HISTORY_ORDER"]
    results = [PropertyResult(pid) for pid in ids]
    prop = {item.property_id: item for item in results}
    required = {"time", "vin", "clk", "rst", "tap1_1", "tap1_0", "tap2_1", "tap2_0", "decision", "fb_metric", "slicer_in_dbg"}
    missing = _missing(rows, required, results)
    if missing:
        return missing

    for row in _representative_clear_rows(rows, has_enable=False):
        item = prop["P_RESET_CLEAR"]
        item.checked += 1
        observed = max(abs(float(row[name])) for name in ["decision", "fb_metric", "slicer_in_dbg"])
        if observed > 0.08:
            item.mismatch(expected="decision/fb/debug=0", observed=observed, time=float(row["time"]), gap=observed)

    hist1 = 0
    hist2 = 0
    for edge in _rising_times(rows, "clk"):
        before = _before(rows, edge)
        if _high(before, "rst"):
            hist1 = hist2 = 0
            continue
        tap1 = _code(before, ["tap1_0", "tap1_1"])
        tap2 = _code(before, ["tap2_0", "tap2_1"])
        active_fb = 0.020 * (tap1 * (1 if hist1 else -1) + tap2 * (1 if hist2 else -1))
        expected_corrected = float(before["vin"]) - active_fb
        for pid, observed_value, expected_value in [
            ("P_CORRECTED_INPUT", float(before["slicer_in_dbg"]), expected_corrected),
            ("P_HISTORY_ORDER", float(before["fb_metric"]), active_fb),
        ]:
            item = prop[pid]
            item.checked += 1
            gap = abs(observed_value - expected_value)
            if gap > 0.05:
                item.mismatch(expected=f"value={expected_value:.5g}", observed=f"value={observed_value:.5g}", time=edge, gap=gap)
        expected_decision = expected_corrected >= VCM
        after = _after(rows, edge + 1.0e-9)
        item = prop["P_CLOCKED_DECISION"]
        item.checked += 1
        observed_decision = _high(after, "decision")
        if observed_decision != expected_decision:
            item.mismatch(expected=f"decision={int(expected_decision)}", observed=f"decision={int(observed_decision)}", time=edge, gap=1.0)
        # The public trace exposes the latched decision, not private history
        # nodes. Advance the reference state from that observable contract.
        hist2, hist1 = hist1, int(observed_decision)
        expected_next_fb = 0.020 * (tap1 * (1 if hist1 else -1) + tap2 * (1 if hist2 else -1))
        item = prop["P_TWO_TAP_FEEDBACK"]
        item.checked += 1
        observed_fb = float(after["fb_metric"])
        gap = abs(observed_fb - expected_next_fb)
        if gap > 0.05:
            item.mismatch(expected=f"fb={expected_next_fb:.5g}", observed=f"fb={observed_fb:.5g}", time=edge, gap=gap)
    return _finish(results)

CHECKER_ID = "v4_354_dfe_receiver_2tap"
CHECKER: Checker = check_v4_354_dfe_receiver_2tap
