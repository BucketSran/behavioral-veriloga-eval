#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import subprocess
from pathlib import Path

from bridge_preflight import bridge_preflight, resolve_cadence_cshrc
from run_gold_suite import (
    ahdl_includes,
    benchmark_root,
    choose_gold_tb,
    list_gold_task_dirs,
    read_meta,
)
from simulate_evas import evaluate_behavior, rising_edges


def project_root() -> Path:
    return benchmark_root().parents[1]


def default_bridge_repo() -> Path:
    return project_root() / "iccad" / "virtuoso-bridge-lite"


def load_csv_rows(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed: dict[str, float] = {}
            for key, value in row.items():
                if key is None or value is None or value == "":
                    continue
                parsed[key] = float(value)
            rows.append(parsed)
    return rows


def interp_at(rows: list[dict[str, float]], sig: str, t: float) -> float:
    if t <= rows[0]["time"]:
        return rows[0].get(sig, 0.0)
    if t >= rows[-1]["time"]:
        return rows[-1].get(sig, 0.0)

    lo = 0
    hi = len(rows) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if rows[mid]["time"] <= t:
            lo = mid
        else:
            hi = mid

    t0 = rows[lo]["time"]
    t1 = rows[hi]["time"]
    y0 = rows[lo].get(sig, 0.0)
    y1 = rows[hi].get(sig, 0.0)
    if t1 == t0:
        return y0
    a = (t - t0) / (t1 - t0)
    return y0 + a * (y1 - y0)


ADPLL_TIMER_TASK_IDS = {"adpll_lock_smoke", "adpll_ratio_hop_smoke", "adpll_timer", "adpll_timer_smoke"}
CPPLL_REACQUIRE_TASK_IDS = {"cppll_freq_step_reacquire_smoke"}
CPPLL_TRACKING_TASK_IDS = {"cppll_timer", "cppll_tracking_smoke"}


def first_rising_time(rows: list[dict[str, float]], sig: str, threshold: float = 0.45) -> float:
    if not rows or sig not in rows[0]:
        return float("nan")
    times = [r["time"] for r in rows]
    edges = rising_edges([r[sig] for r in rows], times, threshold=threshold)
    return edges[0] if edges else float("nan")


def first_rising_time_after(
    rows: list[dict[str, float]],
    sig: str,
    start_t: float,
    threshold: float = 0.45,
) -> float:
    if not rows or sig not in rows[0]:
        return float("nan")
    times = [r["time"] for r in rows]
    edges = rising_edges([r[sig] for r in rows], times, threshold=threshold)
    for edge_t in edges:
        if edge_t >= start_t:
            return edge_t
    return float("nan")


def weighted_logic_high_fraction(
    rows: list[dict[str, float]],
    signal: str,
    threshold: float,
    *,
    start_t: float | None = None,
    end_t: float | None = None,
) -> float:
    if len(rows) < 2:
        return 0.0
    start = rows[0]["time"] if start_t is None else start_t
    end = rows[-1]["time"] if end_t is None else end_t
    if end <= start:
        return 0.0

    total_dt = 0.0
    high_dt = 0.0
    for idx in range(1, len(rows)):
        seg_start = max(rows[idx - 1]["time"], start)
        seg_end = min(rows[idx]["time"], end)
        dt = seg_end - seg_start
        if dt <= 0.0:
            continue
        total_dt += dt
        v_mid = 0.5 * (rows[idx - 1].get(signal, 0.0) + rows[idx].get(signal, 0.0))
        if v_mid > threshold:
            high_dt += dt
    if total_dt <= 0.0:
        return 0.0
    return high_dt / total_dt


def late_edge_metrics(
    rows: list[dict[str, float]],
    sig: str,
    *,
    start_frac: float = 0.8,
    threshold: float = 0.45,
) -> dict[str, float]:
    if not rows or sig not in rows[0]:
        return {
            "edge_count": 0.0,
            "late_edge_count": 0.0,
            "late_mean_period_s": float("nan"),
            "late_freq_hz": float("nan"),
        }

    times = [r["time"] for r in rows]
    edges = rising_edges([r[sig] for r in rows], times, threshold=threshold)
    if not edges:
        return {
            "edge_count": 0.0,
            "late_edge_count": 0.0,
            "late_mean_period_s": float("nan"),
            "late_freq_hz": float("nan"),
        }

    t_start = times[-1] * start_frac
    late_edges = [t for t in edges if t_start <= t <= times[-1]]
    late_periods = [b - a for a, b in zip(late_edges, late_edges[1:])]
    late_mean_period = (
        sum(late_periods) / len(late_periods) if late_periods else float("nan")
    )
    late_freq = (
        1.0 / late_mean_period if late_mean_period and late_mean_period > 0.0 else float("nan")
    )
    return {
        "edge_count": float(len(edges)),
        "late_edge_count": float(len(late_edges)),
        "late_mean_period_s": late_mean_period,
        "late_freq_hz": late_freq,
    }


def late_window_stats(
    rows: list[dict[str, float]],
    sig: str,
    *,
    start_frac: float = 0.8,
) -> dict[str, float]:
    if not rows or sig not in rows[0]:
        return {"min": float("nan"), "max": float("nan"), "mean": float("nan")}

    t_start = rows[-1]["time"] * start_frac
    vals = [r[sig] for r in rows if t_start <= r["time"] <= rows[-1]["time"]]
    if not vals:
        return {"min": float("nan"), "max": float("nan"), "mean": float("nan")}
    return {
        "min": min(vals),
        "max": max(vals),
        "mean": sum(vals) / len(vals),
    }


def rel_delta(a: float, b: float) -> float:
    if not math.isfinite(a) or not math.isfinite(b):
        return float("inf")
    denom = max(abs(a), abs(b), 1e-12)
    return abs(a - b) / denom


def compare_adpll_timer_parity(
    evas_rows: list[dict[str, float]],
    spectre_rows: list[dict[str, float]],
) -> dict:
    ev_ref = late_edge_metrics(evas_rows, "ref_clk")
    ev_fb = late_edge_metrics(evas_rows, "fb_clk")
    sp_ref = late_edge_metrics(spectre_rows, "ref_clk")
    sp_fb = late_edge_metrics(spectre_rows, "fb_clk")

    ev_lock = first_rising_time(evas_rows, "lock")
    sp_lock = first_rising_time(spectre_rows, "lock")
    ev_vctrl = late_window_stats(evas_rows, "vctrl_mon")
    sp_vctrl = late_window_stats(spectre_rows, "vctrl_mon")

    ev_ratio = ev_fb["late_edge_count"] / max(ev_ref["late_edge_count"], 1.0)
    sp_ratio = sp_fb["late_edge_count"] / max(sp_ref["late_edge_count"], 1.0)

    failures: list[str] = []
    if ev_ref["late_edge_count"] < 4 or sp_ref["late_edge_count"] < 4:
        failures.append("insufficient_ref_edges")
    if ev_fb["late_edge_count"] < 4 or sp_fb["late_edge_count"] < 4:
        failures.append("insufficient_fb_edges")
    if abs(ev_ratio - sp_ratio) > 0.02:
        failures.append(f"late_edge_ratio_delta={abs(ev_ratio - sp_ratio):.4f}")
    if rel_delta(ev_fb["late_freq_hz"], sp_fb["late_freq_hz"]) > 0.01:
        failures.append(
            "late_fb_freq_delta="
            f"{rel_delta(ev_fb['late_freq_hz'], sp_fb['late_freq_hz']):.4f}"
        )

    if math.isfinite(ev_lock) != math.isfinite(sp_lock):
        failures.append("lock_presence_mismatch")
    elif math.isfinite(ev_lock) and math.isfinite(sp_lock):
        lock_delta = abs(ev_lock - sp_lock)
        if lock_delta > 5e-9:
            failures.append(f"lock_time_delta={lock_delta:.3e}")
    else:
        lock_delta = float("nan")

    notes = []
    if math.isfinite(ev_vctrl["mean"]) and math.isfinite(sp_vctrl["mean"]):
        notes.append(
            "vctrl_monitor_informational="
            f"evas:{ev_vctrl['mean']:.6f},spectre:{sp_vctrl['mean']:.6f}"
        )

    return {
        "status": "passed" if not failures else "needs_review",
        "mode": "pll_task_aware",
        "task_family": "adpll_timer",
        "metrics": {
            "evas": {
                "late_edge_ratio": ev_ratio,
                "late_fb_freq_hz": ev_fb["late_freq_hz"],
                "lock_time_s": ev_lock,
                "late_vctrl_mean_v": ev_vctrl["mean"],
                "late_vctrl_min_v": ev_vctrl["min"],
                "late_vctrl_max_v": ev_vctrl["max"],
            },
            "spectre": {
                "late_edge_ratio": sp_ratio,
                "late_fb_freq_hz": sp_fb["late_freq_hz"],
                "lock_time_s": sp_lock,
                "late_vctrl_mean_v": sp_vctrl["mean"],
                "late_vctrl_min_v": sp_vctrl["min"],
                "late_vctrl_max_v": sp_vctrl["max"],
            },
            "late_edge_ratio_delta": abs(ev_ratio - sp_ratio),
            "late_fb_freq_rel_delta": rel_delta(ev_fb["late_freq_hz"], sp_fb["late_freq_hz"]),
            "lock_time_delta_s": lock_delta,
        },
        "notes": notes,
        "failures": failures,
    }


def compare_cppll_tracking_parity(
    evas_rows: list[dict[str, float]],
    spectre_rows: list[dict[str, float]],
) -> dict:
    ev_ref = late_edge_metrics(evas_rows, "ref_clk")
    ev_fb = late_edge_metrics(evas_rows, "fb_clk")
    sp_ref = late_edge_metrics(spectre_rows, "ref_clk")
    sp_fb = late_edge_metrics(spectre_rows, "fb_clk")
    ev_vctrl = late_window_stats(evas_rows, "vctrl_mon")
    sp_vctrl = late_window_stats(spectre_rows, "vctrl_mon")

    ev_ratio = ev_fb["late_edge_count"] / max(ev_ref["late_edge_count"], 1.0)
    sp_ratio = sp_fb["late_edge_count"] / max(sp_ref["late_edge_count"], 1.0)
    vctrl_mean_delta = abs(ev_vctrl["mean"] - sp_vctrl["mean"])
    vctrl_min_delta = abs(ev_vctrl["min"] - sp_vctrl["min"])
    vctrl_max_delta = abs(ev_vctrl["max"] - sp_vctrl["max"])

    failures: list[str] = []
    if ev_ref["late_edge_count"] < 4 or sp_ref["late_edge_count"] < 4:
        failures.append("insufficient_ref_edges")
    if ev_fb["late_edge_count"] < 4 or sp_fb["late_edge_count"] < 4:
        failures.append("insufficient_fb_edges")
    if abs(ev_ratio - sp_ratio) > 0.03:
        failures.append(f"late_edge_ratio_delta={abs(ev_ratio - sp_ratio):.4f}")
    if rel_delta(ev_fb["late_freq_hz"], sp_fb["late_freq_hz"]) > 0.03:
        failures.append(
            "late_fb_freq_delta="
            f"{rel_delta(ev_fb['late_freq_hz'], sp_fb['late_freq_hz']):.4f}"
        )
    if not (
        math.isfinite(ev_vctrl["mean"])
        and math.isfinite(sp_vctrl["mean"])
        and math.isfinite(ev_vctrl["min"])
        and math.isfinite(sp_vctrl["min"])
        and math.isfinite(ev_vctrl["max"])
        and math.isfinite(sp_vctrl["max"])
    ):
        failures.append("missing_vctrl_metrics")
    else:
        if vctrl_mean_delta > 0.05:
            failures.append(f"late_vctrl_mean_delta={vctrl_mean_delta:.4f}")
        if vctrl_min_delta > 0.08:
            failures.append(f"late_vctrl_min_delta={vctrl_min_delta:.4f}")
        if vctrl_max_delta > 0.08:
            failures.append(f"late_vctrl_max_delta={vctrl_max_delta:.4f}")

    return {
        "status": "passed" if not failures else "needs_review",
        "mode": "pll_task_aware",
        "task_family": "cppll_tracking",
        "metrics": {
            "evas": {
                "late_edge_ratio": ev_ratio,
                "late_fb_freq_hz": ev_fb["late_freq_hz"],
                "late_vctrl_mean_v": ev_vctrl["mean"],
                "late_vctrl_min_v": ev_vctrl["min"],
                "late_vctrl_max_v": ev_vctrl["max"],
            },
            "spectre": {
                "late_edge_ratio": sp_ratio,
                "late_fb_freq_hz": sp_fb["late_freq_hz"],
                "late_vctrl_mean_v": sp_vctrl["mean"],
                "late_vctrl_min_v": sp_vctrl["min"],
                "late_vctrl_max_v": sp_vctrl["max"],
            },
            "late_edge_ratio_delta": abs(ev_ratio - sp_ratio),
            "late_fb_freq_rel_delta": rel_delta(ev_fb["late_freq_hz"], sp_fb["late_freq_hz"]),
            "late_vctrl_mean_delta_v": vctrl_mean_delta,
            "late_vctrl_min_delta_v": vctrl_min_delta,
            "late_vctrl_max_delta_v": vctrl_max_delta,
        },
        "notes": [
            "ignored_signals=dco_clk,lock"
        ],
        "failures": failures,
    }


def compare_cppll_reacquire_parity(
    evas_rows: list[dict[str, float]],
    spectre_rows: list[dict[str, float]],
) -> dict:
    # This task uses a reference-frequency step at 2.0 us. The first meaningful
    # relock edge can occur shortly after that boundary, so the parity anchor
    # should guard only against the step transition itself rather than skip deep
    # into the disturbance window.
    relock_anchor_t = 2.05e-6

    ev_ref = late_edge_metrics(evas_rows, "ref_clk", start_frac=0.75)
    ev_fb = late_edge_metrics(evas_rows, "fb_clk", start_frac=0.75)
    sp_ref = late_edge_metrics(spectre_rows, "ref_clk", start_frac=0.75)
    sp_fb = late_edge_metrics(spectre_rows, "fb_clk", start_frac=0.75)
    ev_vctrl = late_window_stats(evas_rows, "vctrl_mon", start_frac=0.75)
    sp_vctrl = late_window_stats(spectre_rows, "vctrl_mon", start_frac=0.75)

    ev_disturb_lock = weighted_logic_high_fraction(
        evas_rows, "lock", 0.45, start_t=2.05e-6, end_t=2.8e-6
    )
    sp_disturb_lock = weighted_logic_high_fraction(
        spectre_rows, "lock", 0.45, start_t=2.05e-6, end_t=2.8e-6
    )

    ev_ratio = ev_fb["late_edge_count"] / max(ev_ref["late_edge_count"], 1.0)
    sp_ratio = sp_fb["late_edge_count"] / max(sp_ref["late_edge_count"], 1.0)
    ev_pre_lock = first_rising_time(evas_rows, "lock")
    sp_pre_lock = first_rising_time(spectre_rows, "lock")
    ev_relock = first_rising_time_after(evas_rows, "lock", relock_anchor_t)
    sp_relock = first_rising_time_after(spectre_rows, "lock", relock_anchor_t)
    ev_post_lock_count = len(
        [
            t
            for t in rising_edges([r["lock"] for r in evas_rows], [r["time"] for r in evas_rows])
            if relock_anchor_t <= t <= 5.9e-6
        ]
    )
    sp_post_lock_count = len(
        [
            t
            for t in rising_edges([r["lock"] for r in spectre_rows], [r["time"] for r in spectre_rows])
            if relock_anchor_t <= t <= 5.9e-6
        ]
    )

    failures: list[str] = []
    if ev_ref["late_edge_count"] < 4 or sp_ref["late_edge_count"] < 4:
        failures.append("insufficient_ref_edges")
    if ev_fb["late_edge_count"] < 4 or sp_fb["late_edge_count"] < 4:
        failures.append("insufficient_fb_edges")
    if abs(ev_ratio - sp_ratio) > 0.03:
        failures.append(f"late_edge_ratio_delta={abs(ev_ratio - sp_ratio):.4f}")
    if rel_delta(ev_fb["late_freq_hz"], sp_fb["late_freq_hz"]) > 0.03:
        failures.append(
            "late_fb_freq_delta="
            f"{rel_delta(ev_fb['late_freq_hz'], sp_fb['late_freq_hz']):.4f}"
        )
    if abs(ev_disturb_lock - sp_disturb_lock) > 0.20:
        failures.append(
            f"disturb_lock_window_delta={abs(ev_disturb_lock - sp_disturb_lock):.4f}"
        )

    if math.isfinite(ev_pre_lock) != math.isfinite(sp_pre_lock):
        failures.append("pre_lock_presence_mismatch")
    pre_lock_delta = (
        abs(ev_pre_lock - sp_pre_lock)
        if math.isfinite(ev_pre_lock) and math.isfinite(sp_pre_lock)
        else float("nan")
    )

    if math.isfinite(ev_relock) != math.isfinite(sp_relock):
        failures.append("relock_presence_mismatch")
        relock_delta = float("inf")
    elif math.isfinite(ev_relock) and math.isfinite(sp_relock):
        relock_delta = abs(ev_relock - sp_relock)
        if relock_delta > 5e-8:
            failures.append(f"relock_time_delta={relock_delta:.3e}")
    else:
        relock_delta = float("nan")

    if not (math.isfinite(ev_vctrl["mean"]) and math.isfinite(sp_vctrl["mean"])):
        failures.append("missing_vctrl_metrics")
    elif abs(ev_vctrl["mean"] - sp_vctrl["mean"]) > 0.08:
        failures.append(
            f"late_vctrl_mean_delta={abs(ev_vctrl['mean'] - sp_vctrl['mean']):.4f}"
        )
    if abs(ev_post_lock_count - sp_post_lock_count) > 6:
        failures.append(f"post_lock_count_delta={abs(ev_post_lock_count - sp_post_lock_count)}")

    return {
        "status": "passed" if not failures else "needs_review",
        "mode": "pll_task_aware",
        "task_family": "cppll_reacquire",
        "metrics": {
            "evas": {
                "late_edge_ratio": ev_ratio,
                "late_fb_freq_hz": ev_fb["late_freq_hz"],
                "disturb_lock_high_frac": ev_disturb_lock,
                "pre_lock_time_s": ev_pre_lock,
                "relock_time_s": ev_relock,
                "post_lock_count": ev_post_lock_count,
                "late_vctrl_mean_v": ev_vctrl["mean"],
            },
            "spectre": {
                "late_edge_ratio": sp_ratio,
                "late_fb_freq_hz": sp_fb["late_freq_hz"],
                "disturb_lock_high_frac": sp_disturb_lock,
                "pre_lock_time_s": sp_pre_lock,
                "relock_time_s": sp_relock,
                "post_lock_count": sp_post_lock_count,
                "late_vctrl_mean_v": sp_vctrl["mean"],
            },
            "late_edge_ratio_delta": abs(ev_ratio - sp_ratio),
            "late_fb_freq_rel_delta": rel_delta(ev_fb["late_freq_hz"], sp_fb["late_freq_hz"]),
            "disturb_lock_window_delta": abs(ev_disturb_lock - sp_disturb_lock),
            "pre_lock_time_delta_s": pre_lock_delta,
            "relock_time_delta_s": relock_delta,
            "post_lock_count_delta": abs(ev_post_lock_count - sp_post_lock_count),
            "late_vctrl_mean_delta_v": abs(ev_vctrl["mean"] - sp_vctrl["mean"]),
        },
        "notes": [
            "ignored_signals=dco_clk"
        ],
        "failures": failures,
    }


def compare_waveforms(
    task_id: str,
    evas_csv: Path,
    spectre_csv: Path,
    sample_n: int = 1200,
) -> dict:
    evas_rows = load_csv_rows(evas_csv)
    spectre_rows = load_csv_rows(spectre_csv)
    if not evas_rows or not spectre_rows:
        return {
            "status": "blocked",
            "reason": "empty waveform rows",
        }

    if task_id in ADPLL_TIMER_TASK_IDS:
        return compare_adpll_timer_parity(evas_rows, spectre_rows)
    if task_id in CPPLL_REACQUIRE_TASK_IDS:
        return compare_cppll_reacquire_parity(evas_rows, spectre_rows)
    if task_id in CPPLL_TRACKING_TASK_IDS:
        return compare_cppll_tracking_parity(evas_rows, spectre_rows)

    common_signals = sorted((set(evas_rows[0]) & set(spectre_rows[0])) - {"time"})
    if not common_signals:
        return {
            "status": "blocked",
            "reason": "no common saved signals",
        }

    common_start = max(evas_rows[0]["time"], spectre_rows[0]["time"])
    common_end = min(evas_rows[-1]["time"], spectre_rows[-1]["time"])
    if common_end <= common_start:
        return {
            "status": "blocked",
            "reason": "no overlapping time window",
        }

    per_signal: dict[str, dict[str, float]] = {}
    nrmse_values: list[float] = []
    rmse_values: list[float] = []
    max_abs_values: list[float] = []

    dt = (common_end - common_start) / max(sample_n - 1, 1)
    # Keep digital parity strict: do not shift timelines to hide timing skew.
    max_lag_samples = 0

    def infer_digital(vals: list[float]) -> tuple[bool, float, float]:
        if not vals:
            return False, 0.0, 0.0
        lo = min(vals)
        hi = max(vals)
        span = hi - lo
        if span < 1e-6:
            return False, lo, hi
        # Relaxed tolerance: accept values within 30% of span from rails
        # This handles clock signals with transition region samples
        tol = max(0.15 * span, 0.05)
        near = sum(1 for v in vals if abs(v - lo) <= tol or abs(v - hi) <= tol)
        return (near / len(vals)) >= 0.95, lo, hi

    def infer_constant_logic(vals: list[float]) -> int | None:
        if not vals:
            return None
        lo = min(vals)
        hi = max(vals)
        if hi - lo > 1e-6:
            return None
        level = vals[0]
        if level >= 0.45:
            return 1
        return 0

    for sig in common_signals:
        ev_vals: list[float] = []
        sp_vals: list[float] = []
        merged_vals: list[float] = []
        for idx in range(sample_n):
            t = common_start + (common_end - common_start) * idx / max(sample_n - 1, 1)
            ev = interp_at(evas_rows, sig, t)
            sp = interp_at(spectre_rows, sig, t)
            ev_vals.append(ev)
            sp_vals.append(sp)
            merged_vals.append(ev)
            merged_vals.append(sp)

        digital_ev, ev_lo, ev_hi = infer_digital(ev_vals)
        digital_sp, sp_lo, sp_hi = infer_digital(sp_vals)
        is_digital = digital_ev and digital_sp

        if not is_digital:
            const_ev = infer_constant_logic(ev_vals)
            const_sp = infer_constant_logic(sp_vals)
            if const_ev is not None and const_sp is not None and const_ev == const_sp:
                is_digital = True
                ev_lo = 0.0 if const_ev == 1 else min(ev_vals)
                ev_hi = max(ev_vals) if const_ev == 1 else 0.0
                sp_lo = 0.0 if const_sp == 1 else min(sp_vals)
                sp_hi = max(sp_vals) if const_sp == 1 else 0.0

        if is_digital:
            ev_thr = 0.5 * (ev_lo + ev_hi)
            sp_thr = 0.5 * (sp_lo + sp_hi)
            ev_bits = [1 if v >= ev_thr else 0 for v in ev_vals]
            sp_bits = [1 if v >= sp_thr else 0 for v in sp_vals]

            best_lag = 0
            best_mismatch = 1.0
            for lag in range(-max_lag_samples, max_lag_samples + 1):
                if lag < 0:
                    xa = ev_bits[-lag:]
                    xb = sp_bits[: sample_n + lag]
                elif lag > 0:
                    xa = ev_bits[: sample_n - lag]
                    xb = sp_bits[lag:]
                else:
                    xa = ev_bits
                    xb = sp_bits

                if not xa or not xb:
                    continue
                mismatches = sum(1 for a, b in zip(xa, xb) if a != b)
                mismatch = mismatches / len(xa)
                if mismatch < best_mismatch:
                    best_mismatch = mismatch
                    best_lag = lag

            span = max(merged_vals) - min(merged_vals)
            # For digital-like signals, treat mismatch ratio as normalized error.
            nrmse = best_mismatch
            rmse = math.sqrt(best_mismatch) * max(span, 1.0)
            max_abs = float(max(span, 1.0)) if best_mismatch > 0 else 0.0
            per_signal[sig] = {
                "rmse_v": rmse,
                "max_abs_v": max_abs,
                "span_v": span,
                "nrmse": nrmse,
                "kind": "digital",
                "best_lag_samples": best_lag,
                "best_lag_s": best_lag * dt,
                "mismatch_ratio": best_mismatch,
            }
        else:
            diffs = [a - b for a, b in zip(ev_vals, sp_vals)]
            mse = sum(d * d for d in diffs) / len(diffs)
            rmse = math.sqrt(mse)
            max_abs = max(abs(d) for d in diffs)
            span = max(merged_vals) - min(merged_vals)
            nrmse = rmse / max(span, 1e-6)
            per_signal[sig] = {
                "rmse_v": rmse,
                "max_abs_v": max_abs,
                "span_v": span,
                "nrmse": nrmse,
                "kind": "analog",
            }

        nrmse_values.append(nrmse)
        rmse_values.append(rmse)
        max_abs_values.append(max_abs)

    sorted_nrmse = sorted(nrmse_values)
    p95_idx = min(len(sorted_nrmse) - 1, max(0, math.ceil(0.95 * len(sorted_nrmse)) - 1))
    max_nrmse = max(sorted_nrmse)
    p95_nrmse = sorted_nrmse[p95_idx]
    max_rmse = max(rmse_values)
    max_abs = max(max_abs_values)
    mean_nrmse = sum(sorted_nrmse) / len(sorted_nrmse)

    passed = (p95_nrmse <= 0.14 and max_nrmse <= 0.22) or (
        max_rmse <= 0.05 and max_abs <= 0.30
    ) or (mean_nrmse <= 0.08 and max_nrmse <= 0.25)

    return {
        "status": "passed" if passed else "needs_review",
        "common_window_s": [common_start, common_end],
        "signals_compared": len(common_signals),
        "samples": sample_n,
        "max_rmse_v": max_rmse,
        "max_abs_v": max_abs,
        "mean_nrmse": mean_nrmse,
        "p95_nrmse": p95_nrmse,
        "max_nrmse": max_nrmse,
        "per_signal": per_signal,
    }


def run_cmd(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None, timeout_s: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )


def run_spectre_case(
    *,
    task_id: str,
    tb_path: Path,
    include_paths: list[Path],
    output_dir: Path,
    bridge_repo: Path,
    cadence_cshrc: str | None,
    timeout_s: int,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    bridge_py = bridge_repo / ".venv" / "bin" / "python"
    result_json = output_dir / "spectre_result.json"
    csv_path = output_dir / "tran_spectre.csv"

    payload = {
        "bridge_repo": str(bridge_repo.resolve()),
        "tb_path": str(tb_path.resolve()),
        "include_paths": [str(p.resolve()) for p in include_paths],
        "output_dir": str(output_dir.resolve()),
        "result_json": str(result_json.resolve()),
        "csv_path": str(csv_path.resolve()),
        "cadence_cshrc": cadence_cshrc or "",
    }

    inline = (
        "import csv, json, os\n"
        "from pathlib import Path\n"
        "from dotenv import load_dotenv\n"
        "payload = json.loads(" + repr(json.dumps(payload)) + ")\n"
        "bridge_repo = Path(payload['bridge_repo'])\n"
        "load_dotenv(bridge_repo / '.env')\n"
        "if payload['cadence_cshrc']:\n"
        "    os.environ['VB_CADENCE_CSHRC'] = payload['cadence_cshrc']\n"
        "from virtuoso_bridge.spectre.runner import SpectreSimulator, spectre_mode_args\n"
        "tb = Path(payload['tb_path'])\n"
        "out = Path(payload['output_dir'])\n"
        "out.mkdir(parents=True, exist_ok=True)\n"
        "sim = SpectreSimulator.from_env(spectre_args=spectre_mode_args('ax'), work_dir=out, output_format='psfascii')\n"
        "res = sim.run_simulation(tb, {'include_files': payload['include_paths']})\n"
        "keys = sorted(res.data.keys())\n"
        "if 'time' in keys:\n"
        "    keys = ['time'] + [k for k in keys if k != 'time']\n"
        "nrows = max((len(v) for v in res.data.values()), default=0)\n"
        "csv_path = Path(payload['csv_path'])\n"
        "with csv_path.open('w', newline='') as f:\n"
        "    writer = csv.writer(f)\n"
        "    writer.writerow(keys)\n"
        "    for i in range(nrows):\n"
        "        writer.writerow([(res.data.get(k, [])[i] if i < len(res.data.get(k, [])) else '') for k in keys])\n"
        "summary = {\n"
        "    'status': res.status.value,\n"
        "    'ok': bool(res.ok),\n"
        "    'errors': list(res.errors),\n"
        "    'warnings': list(res.warnings),\n"
        "    'signals': keys,\n"
        "    'rows': nrows,\n"
        "    'csv_path': str(csv_path),\n"
        "}\n"
        "Path(payload['result_json']).write_text(json.dumps(summary, indent=2), encoding='utf-8')\n"
        "print(json.dumps(summary, indent=2))\n"
    )

    env = os.environ.copy()
    py_path = str(bridge_repo)
    if env.get("PYTHONPATH"):
        py_path = py_path + os.pathsep + env["PYTHONPATH"]
    env["PYTHONPATH"] = py_path

    proc = run_cmd(
        [str(bridge_py), "-c", inline],
        cwd=bridge_repo,
        env=env,
        timeout_s=max(timeout_s, 600),
    )

    if not result_json.exists():
        return {
            "status": "blocked",
            "ok": False,
            "notes": ["spectre_result.json missing"],
            "stdout_tail": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-4000:],
        }

    try:
        result = json.loads(result_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {
            "status": "blocked",
            "ok": False,
            "notes": [f"spectre_result.json unreadable: {exc}"],
            "stdout_tail": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-4000:],
        }
    result["stdout_tail"] = ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-4000:]
    if proc.returncode != 0 and result.get("status") != "success":
        result["status"] = "error"
        result["ok"] = False
    return result


def should_retry_spectre_upload(result: dict) -> bool:
    if result.get("ok"):
        return False
    errors = result.get("errors") or []
    return any("Failed to upload files" in str(err) for err in errors)


def run_dual_case(
    *,
    task_dir: Path,
    output_root: Path,
    bridge_repo: Path,
    cadence_cshrc: str | None,
    timeout_s: int,
) -> dict:
    gold_dir = task_dir / "gold"
    meta = read_meta(task_dir)
    task_id = meta.get("task_id", task_dir.name)
    scoring = set(meta.get("scoring", ["dut_compile", "tb_compile", "sim_correct"]))

    tb_path = choose_gold_tb(gold_dir)
    if tb_path is None:
        return {
            "task_id": task_id,
            "status": "FAIL_INFRA",
            "notes": ["no gold testbench found"],
        }

    includes = ahdl_includes(tb_path)
    if not includes:
        return {
            "task_id": task_id,
            "status": "FAIL_INFRA",
            "notes": [f"no ahdl_include found in {tb_path.name}"],
        }

    include_paths = [gold_dir / name for name in includes]
    missing = [str(path.name) for path in include_paths if not path.exists()]
    if missing:
        return {
            "task_id": task_id,
            "status": "FAIL_INFRA",
            "notes": [f"missing included files: {', '.join(missing)}"],
        }

    case_root = output_root / task_id
    evas_root = case_root / "evas"
    spectre_root = case_root / "spectre"
    primary_dut = include_paths[0]
    notes = [
        f"gold_tb={tb_path.name}",
        f"gold_primary_dut={primary_dut.name}",
    ]

    from run_gold_suite import run_gold_case

    evas_result = run_gold_case(task_dir, output_root, timeout_s)
    evas_csv = evas_root / "tran.csv"
    if not evas_csv.exists():
        evas_csv = case_root / "tran.csv"

    spectre_result = run_spectre_case(
        task_id=task_id,
        tb_path=tb_path,
        include_paths=include_paths,
        output_dir=spectre_root,
        bridge_repo=bridge_repo,
        cadence_cshrc=cadence_cshrc,
        timeout_s=timeout_s,
    )
    if should_retry_spectre_upload(spectre_result):
        notes.append("spectre:retry_after_upload_failure")
        spectre_result = run_spectre_case(
            task_id=task_id,
            tb_path=tb_path,
            include_paths=include_paths,
            output_dir=spectre_root,
            bridge_repo=bridge_repo,
            cadence_cshrc=cadence_cshrc,
            timeout_s=timeout_s,
        )

    spectre_csv = spectre_root / "tran_spectre.csv"
    if "sim_correct" not in scoring:
        spectre_sim_correct = 1.0
        spectre_behavior_notes = ["behavior_not_required_by_scoring"]
        notes.append("spectre:behavior_not_required_by_scoring")
    elif spectre_result.get("ok") and spectre_csv.exists():
        spectre_sim_correct, spectre_behavior_notes = evaluate_behavior(task_id, spectre_csv)
        notes.extend(f"spectre:{note}" for note in spectre_behavior_notes)
    else:
        spectre_sim_correct = 0.0
        notes.append("spectre:tran_spectre.csv missing or run failed")
        spectre_behavior_notes = []

    if "sim_correct" not in scoring:
        parity = {
            "status": "not_required",
            "reason": "task scoring does not require sim_correct parity",
        }
    elif evas_result["status"] == "PASS" and spectre_sim_correct == 1.0 and spectre_csv.exists() and evas_csv.exists():
        parity = compare_waveforms(task_id, evas_csv, spectre_csv)
    else:
        parity = {
            "status": "blocked",
            "reason": "prerequisites not met for waveform comparison",
        }

    if evas_result["status"] != "PASS":
        status = "FAIL_EVAS"
    elif not spectre_result.get("ok"):
        status = "FAIL_SPECTRE"
    elif spectre_sim_correct < 1.0:
        status = "FAIL_SPECTRE_BEHAVIOR"
    elif parity.get("status") not in {"passed", "not_required"}:
        status = "FAIL_PARITY"
    else:
        status = "PASS"

    return {
        "task_id": task_id,
        "status": status,
        "gold_dir": str(gold_dir),
        "gold_tb": str(tb_path),
        "gold_includes": includes,
        "evas": evas_result,
        "spectre": {
            **spectre_result,
            "behavior_score": spectre_sim_correct,
            "behavior_notes": spectre_behavior_notes,
        },
        "parity": parity,
        "notes": notes,
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run EVAS + Spectre dual validation on gold tasks.")
    ap.add_argument(
        "--output-root",
        default="results/gold-dual-suite",
        help="Output directory relative to benchmark root unless absolute.",
    )
    ap.add_argument("--timeout-s", type=int, default=240)
    ap.add_argument(
        "--family",
        action="append",
        choices=("end-to-end", "spec-to-va", "bugfix", "tb-generation"),
        help="Task family to scan for gold assets. Defaults to end-to-end only.",
    )
    ap.add_argument(
        "--task",
        action="append",
        default=[],
        help="Restrict to one or more task IDs with gold assets.",
    )
    ap.add_argument(
        "--bridge-repo",
        default=str(default_bridge_repo()),
        help="Path to virtuoso-bridge-lite repository.",
    )
    ap.add_argument(
        "--cadence-cshrc",
        default=os.environ.get("VB_CADENCE_CSHRC", ""),
        help="Remote Cadence cshrc path used to expose spectre on PATH.",
    )
    ap.add_argument(
        "--skip-bridge-preflight",
        action="store_true",
        help="Skip bridge health checks and run Spectre directly.",
    )
    ap.add_argument(
        "--require-virtuoso-daemon",
        action="store_true",
        help="Treat a disconnected Virtuoso CIW daemon as a hard blocker.",
    )
    ap.add_argument(
        "--allow-direct-run",
        action="store_true",
        help="Allow calling this runner directly without scripts/run_with_bridge.sh.",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    via_wrapper = os.environ.get("VAEVAS_BRIDGE_WRAPPER") == "1"
    if not via_wrapper and not args.allow_direct_run:
        summary = {
            "status": "blocked",
            "reason": "direct invocation blocked; use scripts/run_with_bridge.sh",
            "remediation": [
                "cd /Users/bucketsran/Documents/TsingProject/vaEvas/behavioral-veriloga-eval",
                "./scripts/run_with_bridge.sh python3 runners/run_gold_dual_suite.py <args>",
                "or add --allow-direct-run if you intentionally run without wrapper",
            ],
        }
        print(json.dumps(summary, indent=2))
        return 2

    bridge_repo = Path(args.bridge_repo).resolve()
    if not bridge_repo.exists():
        print(json.dumps({"status": "blocked", "reason": f"bridge repo not found: {bridge_repo}"}, indent=2))
        return 2

    out_root = Path(args.output_root)
    if not out_root.is_absolute():
        out_root = benchmark_root() / out_root
    out_root.mkdir(parents=True, exist_ok=True)

    effective_cshrc = resolve_cadence_cshrc(bridge_repo, args.cadence_cshrc)
    if args.skip_bridge_preflight:
        preflight = {
            "status": "skipped",
            "bridge_repo": str(bridge_repo),
            "cadence_cshrc": effective_cshrc,
        }
    else:
        preflight = bridge_preflight(
            bridge_repo,
            cadence_cshrc=effective_cshrc,
            require_daemon=args.require_virtuoso_daemon,
        )
        if preflight.get("status") == "blocked":
            summary = {
                "status": "blocked",
                "reason": preflight.get("reason", "bridge preflight failed"),
                "tasks_total": 0,
                "pass_count": 0,
                "fail_count": 0,
                "task_ids": [],
                "families": list(tuple(args.family) if args.family else ("end-to-end",)),
                "bridge_repo": str(bridge_repo),
                "cadence_cshrc": effective_cshrc,
                "bridge_preflight": preflight,
                "results": [],
            }
            (out_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
            print(json.dumps(summary, indent=2))
            return 2

    selected = set(args.task) if args.task else None
    families = tuple(args.family) if args.family else ("end-to-end",)
    results = [
        run_dual_case(
            task_dir=task_dir,
            output_root=out_root,
            bridge_repo=bridge_repo,
            cadence_cshrc=effective_cshrc or None,
            timeout_s=args.timeout_s,
        )
        for task_dir in list_gold_task_dirs(selected, families=families)
    ]

    summary = {
        "tasks_total": len(results),
        "pass_count": sum(1 for r in results if r["status"] == "PASS"),
        "fail_count": sum(1 for r in results if r["status"] != "PASS"),
        "task_ids": [r["task_id"] for r in results],
        "families": list(families),
        "bridge_repo": str(bridge_repo),
        "cadence_cshrc": effective_cshrc,
        "bridge_preflight": preflight,
        "results": results,
    }
    (out_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if summary["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
