"""Task-specific checker for canonical v4 DUT 355."""
from __future__ import annotations

from ..api import Checker
from .stimulus_relative import representative_clear_rows as _representative_clear_rows
from dataclasses import dataclass

VDD = 0.9
VSS = 0.0
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

def _pam4_level(row: dict[str, float]) -> int:
    msb = int(_high(row, "bit_msb"))
    lsb = int(_high(row, "bit_lsb"))
    return {(0, 0): 0, (0, 1): 1, (1, 1): 2, (1, 0): 3}[(msb, lsb)]

def check_v4_355_pam4_tx_driver(rows: list[dict[str, float]]) -> tuple[bool, str]:
    ids = ["P_RESET_CLEAR", "P_GRAY_LEVEL_MAP", "P_LEVEL_DAC", "P_PREEMPHASIS", "P_OUTPUT_CLAMP"]
    results = [PropertyResult(pid) for pid in ids]
    prop = {item.property_id: item for item in results}
    required = {"time", "bit_msb", "bit_lsb", "clk", "rst", "emph_en", "vout", "level_1", "level_0", "delta_dbg"}
    missing = _missing(rows, required, results)
    if missing:
        return missing
    for row in _representative_clear_rows(rows, has_enable=False):
        item = prop["P_RESET_CLEAR"]
        item.checked += 1
        observed = max(abs(float(row[name])) for name in ["vout", "level_1", "level_0", "delta_dbg"])
        if observed > 0.08:
            item.mismatch(expected="all_reset_outputs=0", observed=observed, time=float(row["time"]), gap=observed)
    previous_level = 0
    for edge in _rising_times(rows, "clk"):
        before = _before(rows, edge)
        if _high(before, "rst"):
            previous_level = 0
            continue
        expected_level = _pam4_level(before)
        after = _after(rows, edge + 0.6e-9)
        observed_level = _code(after, ["level_0", "level_1"])
        item = prop["P_GRAY_LEVEL_MAP"]
        item.checked += 1
        if observed_level != expected_level:
            item.mismatch(expected=f"level={expected_level}", observed=f"level={observed_level}", time=edge, gap=abs(observed_level - expected_level))
        delta = expected_level - previous_level
        base = 0.3 * expected_level
        expected_vout = base
        if _high(before, "emph_en"):
            expected_vout += 0.06 if delta > 0 else (-0.06 if delta < 0 else 0.0)
        expected_vout = max(VSS, min(VDD, expected_vout))
        item = prop["P_LEVEL_DAC"]
        item.checked += 1
        vout = float(after["vout"])
        gap = abs(vout - expected_vout)
        if gap > 0.08:
            item.mismatch(expected=f"vout={expected_vout:.5g}", observed=f"vout={vout:.5g}", time=edge, gap=gap)
        item = prop["P_PREEMPHASIS"]
        item.checked += 1
        observed_delta = float(after["delta_dbg"])
        delta_gap = abs(observed_delta - delta)
        if delta_gap > 0.15:
            item.mismatch(expected=f"delta={delta}", observed=f"delta={observed_delta:.5g}", time=edge, gap=delta_gap)
        previous_level = expected_level
    for row in rows[:: max(1, len(rows) // 1000)]:
        item = prop["P_OUTPUT_CLAMP"]
        item.checked += 1
        value = float(row["vout"])
        if value < -0.03 or value > 0.93:
            gap = -value if value < 0 else value - 0.9
            item.mismatch(expected="0<=vout<=0.9", observed=value, time=float(row["time"]), gap=gap)
    return _finish(results)

CHECKER_ID = "v4_355_pam4_tx_driver"
CHECKER: Checker = check_v4_355_pam4_tx_driver
