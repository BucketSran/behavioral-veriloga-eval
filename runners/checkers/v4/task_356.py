"""Task-specific checker for canonical v4 DUT 356."""
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

def check_v4_356_sst_driver_impedance_macro(rows: list[dict[str, float]]) -> tuple[bool, str]:
    ids = ["P_RESET_DISABLE_CLEAR", "P_CLOCKED_DATA", "P_SWING_MAPPING", "P_DATA_POLARITY", "P_TRIM_METRIC"]
    results = [PropertyResult(pid) for pid in ids]
    prop = {item.property_id: item for item in results}
    required = {"time", "data", "enable", "clk", "rst", "z_2", "z_1", "z_0", "vout", "swing_metric", "z_metric"}
    missing = _missing(rows, required, results)
    if missing:
        return missing
    for row in _representative_clear_rows(rows, has_enable=True):
        item = prop["P_RESET_DISABLE_CLEAR"]
        item.checked += 1
        observed = (float(row["vout"]), float(row["swing_metric"]), float(row["z_metric"]))
        gap = max(abs(observed[0] - VCM), abs(observed[1]), abs(observed[2]))
        if gap > 0.08:
            item.mismatch(expected="vout=0.45 metrics=0", observed=observed, time=float(row["time"]), gap=gap)
    latched = False
    for edge in _rising_times(rows, "clk"):
        before = _before(rows, edge)
        if _high(before, "rst") or not _high(before, "enable"):
            latched = False
            continue
        latched = _high(before, "data")
        code = _code(before, ["z_0", "z_1", "z_2"])
        expected_swing = 0.15 + 0.025 * code
        expected_vout = VCM + expected_swing if latched else VCM - expected_swing
        expected_metric = VDD * code / 7.0
        after = _after(rows, edge + 0.6e-9)
        for pid, expected, observed, tolerance in [
            ("P_SWING_MAPPING", expected_swing, float(after["swing_metric"]), 0.05),
            ("P_DATA_POLARITY", expected_vout, float(after["vout"]), 0.07),
            ("P_TRIM_METRIC", expected_metric, float(after["z_metric"]), 0.06),
        ]:
            item = prop[pid]
            item.checked += 1
            gap = abs(expected - observed)
            if gap > tolerance:
                item.mismatch(expected=f"value={expected:.5g}", observed=f"value={observed:.5g}", time=edge, gap=gap)
        item = prop["P_CLOCKED_DATA"]
        item.checked += 1
        observed_high = float(after["vout"]) > VCM
        if observed_high != latched:
            item.mismatch(expected=f"latched_data={int(latched)}", observed=f"vout_high={int(observed_high)}", time=edge, gap=1.0)
    return _finish(results)

CHECKER_ID = "v4_356_sst_driver_impedance_macro"
CHECKER: Checker = check_v4_356_sst_driver_impedance_macro
