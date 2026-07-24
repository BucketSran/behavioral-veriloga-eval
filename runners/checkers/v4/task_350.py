"""Task-specific checker for canonical v4 DUT 350."""
from __future__ import annotations

from ..api import Checker
from .stimulus_relative import representative_clear_rows as _representative_clear_rows
from dataclasses import dataclass

VCM = 0.45
VDD = 0.9
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

def check_v4_350_sigma_delta_mini_loop(rows: list[dict[str, float]]) -> tuple[bool, str]:
    results = [PropertyResult(pid) for pid in [
        "P_RESET_CLEAR", "P_FEEDBACK_STATE_UPDATE", "P_COMPARATOR_DECISION",
        "P_DECIMATOR_WINDOW", "P_STATE_BOUNDED",
    ]]
    prop = {item.property_id: item for item in results}
    required = {"time", "vin", "clk", "rst", "bit_out", "avg_3", "avg_2", "avg_1", "avg_0", "state_metric"}
    missing = _missing(rows, required, results)
    if missing:
        return missing

    for row in _representative_clear_rows(rows, has_enable=False):
        item = prop["P_RESET_CLEAR"]
        item.checked += 1
        observed = max(abs(float(row[name])) for name in ["bit_out", "avg_3", "avg_2", "avg_1", "avg_0", "state_metric"])
        if observed > 0.08:
            item.mismatch(expected="all_reset_outputs<=0.08", observed=observed, time=float(row["time"]), gap=observed - 0.08)

    state = 0.0
    bit_count = 0
    sample_count = 0
    for edge in _rising_times(rows, "clk"):
        before = _before(rows, edge)
        if _high(before, "rst"):
            state = 0.0
            bit_count = 0
            sample_count = 0
            continue
        after = _after(rows, edge + 0.7e-9)
        previous_bit = 1 if _high(before, "bit_out") else 0
        state = max(-1.8, min(1.8, state + float(before["vin"]) - VDD * previous_bit + VCM))
        item = prop["P_FEEDBACK_STATE_UPDATE"]
        item.checked += 1
        observed_state = float(after["state_metric"])
        gap = abs(observed_state - state)
        if gap > 0.10:
            item.mismatch(expected=f"state={state:.5g}", observed=f"state={observed_state:.5g}", time=edge, gap=gap)

        item = prop["P_COMPARATOR_DECISION"]
        item.checked += 1
        expected_bit = state >= VCM
        observed_bit = _high(after, "bit_out")
        if observed_bit != expected_bit:
            item.mismatch(expected=f"bit={int(expected_bit)}", observed=f"bit={int(observed_bit)}", time=edge, gap=1.0)

        sample_count += 1
        bit_count += previous_bit
        if sample_count == 16:
            item = prop["P_DECIMATOR_WINDOW"]
            item.checked += 1
            expected_avg = min(bit_count, 15)
            observed_avg = _code(after, ["avg_0", "avg_1", "avg_2", "avg_3"])
            if observed_avg != expected_avg:
                item.mismatch(expected=f"avg_code={expected_avg}", observed=f"avg_code={observed_avg}", time=edge, gap=abs(observed_avg - expected_avg))
            sample_count = 0
            bit_count = 0

    for row in rows[:: max(1, len(rows) // 1000)]:
        item = prop["P_STATE_BOUNDED"]
        item.checked += 1
        observed = abs(float(row["state_metric"]))
        if observed > 1.85:
            item.mismatch(expected="abs(state)<=1.8", observed=observed, time=float(row["time"]), gap=observed - 1.8)
    return _finish(results)

CHECKER_ID = "v4_350_sigma_delta_mini_loop"
CHECKER: Checker = check_v4_350_sigma_delta_mini_loop
