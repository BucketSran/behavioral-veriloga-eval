"""Task-specific checker for canonical v4 DUT 091."""
from __future__ import annotations

from ..api import Checker
def rising_edges(values: list[float], times: list[float], threshold: float = 0.45) -> list[float]:
    edges: list[float] = []
    for i in range(1, len(values)):
        if values[i - 1] < threshold <= values[i]:
            edges.append(times[i])
    return edges

def check_final_step_file_metric(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "ref", "metric_out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/ref/metric_out"
    ref_high = max(r["ref"] for r in rows)
    vth = 0.45 if ref_high < 1.0 else 0.5 * ref_high
    ref_edges = rising_edges([r["ref"] for r in rows], [r["time"] for r in rows], threshold=vth)
    if len(ref_edges) != 4:
        return False, f"expected_4_ref_edges={len(ref_edges)}"

    metric_vals = [r["metric_out"] for r in rows]
    vmax = max(metric_vals)
    if vmax < 0.2:
        return False, f"metric_out_too_low={vmax:.3f}"

    levels: list[float] = []
    expected_levels: list[float] = []
    for idx, edge_t in enumerate(ref_edges):
        next_edge = ref_edges[idx + 1] if idx + 1 < len(ref_edges) else rows[-1]["time"]
        t0 = edge_t + 0.8e-9
        t1 = min(next_edge - 0.4e-9, edge_t + 6.0e-9, rows[-1]["time"])
        if t1 <= t0:
            continue
        vals = [r["metric_out"] for r in rows if t0 <= r["time"] <= t1]
        if not vals:
            continue
        levels.append(sum(vals) / len(vals))
        expected_levels.append(ref_high * (idx + 1) / 4.0)
    if len(levels) < 3:
        return False, f"insufficient_metric_plateau_samples={len(levels)}"
    level_errs = [abs(level - expected) for level, expected in zip(levels, expected_levels)]
    max_level_err = max(level_errs) if level_errs else float("inf")
    final_level = levels[-1] if levels else 0.0
    final_norm = final_level / max(ref_high, 1e-6)
    expected_final_norm = len(ref_edges) / 4.0
    dips = sum(1 for i in range(1, len(metric_vals)) if metric_vals[i] + 0.03 < metric_vals[i - 1])
    ok = max_level_err <= 0.08 and abs(final_norm - expected_final_norm) <= 0.10 and dips <= 3
    return ok, (
        f"ref_edges={len(ref_edges)} "
        f"metric_levels={[round(v,3) for v in levels]} max_level_err={max_level_err:.3f} "
        f"final_norm={final_norm:.3f}/{expected_final_norm:.3f} metric_dips={dips}"
    )

CHECKER_ID = "v4_091_final_step_file_metric"
CHECKER: Checker = check_final_step_file_metric
