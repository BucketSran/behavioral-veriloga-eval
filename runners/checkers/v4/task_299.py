"""Task-specific checker for canonical v4 DUT 299."""
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

def check_v3_502_sine_vco_idtmod_bound_step(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing)

    center_freq = 20.0e6
    vco_gain = 40.0e6
    vco_amp = 0.9
    freqs = [center_freq + vco_gain * row["vin"] for row in rows]
    if not all(math.isfinite(freq) and freq > 0.0 for freq in freqs):
        return False, "invalid_or_nonpositive_frequency_stimulus"
    freq_span = max(freqs) - min(freqs)
    frequency_scale = max(abs(freq) for freq in freqs)
    if freq_span <= max(1.0, 1.0e-9 * frequency_scale):
        return False, f"insufficient_frequency_stimulus_span={freq_span:.4g}"

    phases, cycle_counts = _v3_integrated_mod_phase_values(
        rows,
        freq_fn=lambda row: center_freq + vco_gain * row["vin"],
        modulus=1.0,
    )
    total_phase_advance = max(cycle_counts) - min(cycle_counts)
    if total_phase_advance < 0.75:
        return False, f"insufficient_phase_coverage_cycles={total_phase_advance:.4f}"

    two_pi = 2.0 * math.pi
    stride = max(1, len(rows) // 160)
    checked = 0
    max_out_err = 0.0
    max_metric_err = 0.0
    out_span_lo: float | None = None
    out_span_hi: float | None = None
    for index in range(0, len(rows), stride):
        phase = phases[index]
        out_expected = vco_amp * math.sin(two_pi * phase)
        metric_expected = vco_amp * phase
        out_err = abs(rows[index]["out"] - out_expected)
        out_span_lo = out_expected if out_span_lo is None else min(out_span_lo, out_expected)
        out_span_hi = out_expected if out_span_hi is None else max(out_span_hi, out_expected)
        max_out_err = max(max_out_err, out_err)
        checked += 1
        if out_err > 0.08:
            return False, (
                f"out@{rows[index]['time'] * 1e9:g}ns={rows[index]['out']:.4f} "
                f"expected={out_expected:.4f} tol=0.0800"
            )
        if 0.05 < phase < 0.95:
            metric_err = abs(rows[index]["metric"] - metric_expected)
            max_metric_err = max(max_metric_err, metric_err)
            if metric_err > 0.06:
                return False, (
                    f"metric@{rows[index]['time'] * 1e9:g}ns={rows[index]['metric']:.4f} "
                    f"expected={metric_expected:.4f} tol=0.0600"
                )
    if checked < 4:
        return False, f"insufficient_observation_points={checked}"
    out_span = (out_span_hi - out_span_lo) if (out_span_lo is not None) else 0.0
    if out_span < 0.6 * vco_amp:
        return False, f"insufficient_out_dynamic_range={out_span:.4f}"
    return True, (
        f"out_samples={checked} phase_cycles={total_phase_advance:.4f} "
        f"freq_span={freq_span:.4g} out_span={out_span:.4f} "
        f"max_out_err={max_out_err:.4f} max_metric_err={max_metric_err:.4f}"
    )

CHECKER_ID = "v4_299_sine_vco_idtmod_bound_step"
CHECKER: Checker = check_v3_502_sine_vco_idtmod_bound_step
