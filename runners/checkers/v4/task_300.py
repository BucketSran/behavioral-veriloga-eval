"""Task-specific checker for canonical v4 DUT 300."""
from __future__ import annotations

from ..api import Checker
import math

def _v3_integrated_mod_phase_values(
    rows: list[dict[str, float]],
    *,
    freq_fn,
    modulus: float,
) -> tuple[list[float], list[float]]:
    phase = 0.0
    phases = [phase]
    cycle_counts = [0.0]
    total_cycles = 0.0
    for prev, row in zip(rows, rows[1:]):
        dt = max(0.0, row["time"] - prev["time"])
        if prev.get("rst", 0.0) <= 0.45 and row.get("rst", 0.0) <= 0.45:
            f0 = freq_fn(prev)
            f1 = freq_fn(row)
            total_cycles += 0.5 * (f0 + f1) * dt
            phase = total_cycles % modulus
        phases.append(phase)
        cycle_counts.append(total_cycles)
    return phases, cycle_counts

def check_v3_503_differential_vco_clip_idtmod(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vinp", "vinm", "outp", "outm", "metric"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing)

    fnom = 20.0e6
    dfdv = 160.0e6
    fmin = 5.0e6
    fmax = 80.0e6
    vcm = 0.45
    vac = 0.4

    def _clip(x: float) -> float:
        return fmin if x < fmin else (fmax if x > fmax else x)

    raw_freqs = [fnom + dfdv * (row["vinp"] - row["vinm"]) for row in rows]
    clipped_freqs = [_clip(freq) for freq in raw_freqs]
    if not all(math.isfinite(freq) and freq > 0.0 for freq in clipped_freqs):
        return False, "invalid_or_nonpositive_clipped_frequency"

    saw_lower_clamp_case = any(freq < fmin for freq in raw_freqs)
    saw_upper_clamp_case = any(freq > fmax for freq in raw_freqs)
    saw_inband_case = any(fmin <= freq <= fmax for freq in raw_freqs)
    if not (saw_lower_clamp_case and saw_inband_case and saw_upper_clamp_case):
        return False, (
            "insufficient_clamp_coverage="
            f"lower:{saw_lower_clamp_case},inband:{saw_inband_case},upper:{saw_upper_clamp_case}"
        )

    phases, cycle_counts = _v3_integrated_mod_phase_values(
        rows,
        freq_fn=lambda row: _clip(fnom + dfdv * (row["vinp"] - row["vinm"])),
        modulus=1.0,
    )
    total_phase_advance = max(cycle_counts) - min(cycle_counts)
    if total_phase_advance < 0.75:
        return False, f"insufficient_phase_coverage_cycles={total_phase_advance:.4f}"

    two_pi = 2.0 * math.pi
    stride = max(1, len(rows) // 160)
    checked = 0
    max_err = 0.0
    outp_span_lo: float | None = None
    outp_span_hi: float | None = None
    for index in range(0, len(rows), stride):
        phase = phases[index]
        outp_expected = vcm + vac * math.sin(two_pi * phase)
        outm_expected = vcm - vac * math.sin(two_pi * phase)
        metric_expected = 0.9 * phase
        outp_err = abs(rows[index]["outp"] - outp_expected)
        outm_err = abs(rows[index]["outm"] - outm_expected)
        max_err = max(max_err, outp_err, outm_err)
        checked += 1
        outp_span_lo = outp_expected if outp_span_lo is None else min(outp_span_lo, outp_expected)
        outp_span_hi = outp_expected if outp_span_hi is None else max(outp_span_hi, outp_expected)
        if outp_err > 0.08:
            return False, (
                f"outp@{rows[index]['time'] * 1e9:g}ns={rows[index]['outp']:.4f} "
                f"expected={outp_expected:.4f} tol=0.0800"
            )
        if outm_err > 0.08:
            return False, (
                f"outm@{rows[index]['time'] * 1e9:g}ns={rows[index]['outm']:.4f} "
                f"expected={outm_expected:.4f} tol=0.0800"
            )
        if 0.05 < phase < 0.95:
            metric_err = abs(rows[index]["metric"] - metric_expected)
            max_err = max(max_err, metric_err)
            if metric_err > 0.06:
                return False, (
                    f"metric@{rows[index]['time'] * 1e9:g}ns={rows[index]['metric']:.4f} "
                    f"expected={metric_expected:.4f} tol=0.0600"
                )
    if checked < 4:
        return False, f"insufficient_observation_points={checked}"
    outp_span = (outp_span_hi - outp_span_lo) if (outp_span_lo is not None) else 0.0
    if outp_span < 0.5 * vac:
        return False, f"insufficient_outp_dynamic_range={outp_span:.4f}"
    clamp_note = " lower_clamp_exercised inband_exercised upper_clamp_exercised"
    return True, (
        f"samples={checked} phase_cycles={total_phase_advance:.4f} "
        f"outp_span={outp_span:.4f} max_err={max_err:.4f}{clamp_note}"
    )

CHECKER_ID = "v4_300_differential_vco_clip_idtmod"
CHECKER: Checker = check_v3_503_differential_vco_clip_idtmod
