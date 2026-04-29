#!/usr/bin/env python3
"""Common CSV checkers for benchmark-v2 draft tasks."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def load_rows(csv_path: str | Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with Path(csv_path).open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed: dict[str, float] = {}
            for key, value in row.items():
                try:
                    parsed[key] = float(value)
                except (TypeError, ValueError):
                    parsed[key] = 0.0
            rows.append(parsed)
    return rows


def _has_fields(rows: list[dict[str, float]], fields: list[str]) -> tuple[bool, str]:
    if not rows:
        return False, "empty_csv"
    missing = [field for field in fields if field not in rows[0]]
    if missing:
        return False, "missing_fields=" + ",".join(missing)
    return True, "fields_ok"


def _bit(row: dict[str, float], name: str, threshold: float) -> int:
    return 1 if row.get(name, 0.0) >= threshold else 0


def _decode(row: dict[str, float], bits_lsb_first: list[str], threshold: float) -> int:
    code = 0
    for idx, name in enumerate(bits_lsb_first):
        code |= _bit(row, name, threshold) << idx
    return code


def _rising_edges(rows: list[dict[str, float]], signal: str, threshold: float) -> list[int]:
    edges: list[int] = []
    prev = rows[0].get(signal, 0.0)
    for idx, row in enumerate(rows[1:], start=1):
        cur = row.get(signal, 0.0)
        if prev < threshold <= cur:
            edges.append(idx)
        prev = cur
    return edges


def _sample_indices(rows: list[dict[str, float]], step: int = 10) -> list[int]:
    if len(rows) <= 80:
        return list(range(len(rows)))
    return list(range(5, len(rows), max(1, step)))


def _check_adc_dac(rows: list[dict[str, float]], spec: dict[str, Any]) -> tuple[bool, str]:
    bits = spec["bits_lsb_first"]
    fields = [spec["vin"], spec["vout"], *bits]
    if spec.get("settled"):
        fields.append(spec["settled"])
    ok, note = _has_fields(rows, fields)
    if not ok:
        return False, note
    threshold = float(spec.get("threshold", 0.45))
    width = int(spec["width"])
    max_code = (1 << width) - 1
    codes = [_decode(row, bits, threshold) for row in rows]
    nondecreasing = sum(1 for a, b in zip(codes, codes[1:]) if b >= a)
    unique_codes = len(set(codes))
    if unique_codes < int(spec.get("min_unique_codes", min(max_code + 1, 4))):
        return False, f"unique_codes={unique_codes}"
    if nondecreasing < 0.96 * max(1, len(codes) - 1):
        return False, f"code_not_mostly_nondecreasing={nondecreasing}/{len(codes)-1}"
    max_err = 0.0
    for idx in _sample_indices(rows, 8):
        row = rows[idx]
        expected = float(spec.get("vlo", 0.0)) + (float(spec.get("vhi", 0.9)) - float(spec.get("vlo", 0.0))) * codes[idx] / max_code
        max_err = max(max_err, abs(row[spec["vout"]] - expected))
    if max_err > float(spec.get("vout_tolerance", 0.18)):
        return False, f"vout_max_err={max_err:.4f}"
    if spec.get("settled") and max(row[spec["settled"]] for row in rows[-max(5, len(rows)//5):]) < threshold:
        return False, "settled_never_high"
    return True, f"adc_dac_ok unique_codes={unique_codes} max_err={max_err:.4f}"


def _check_binary_dac(rows: list[dict[str, float]], spec: dict[str, Any]) -> tuple[bool, str]:
    bits = spec["bits_lsb_first"]
    ok, note = _has_fields(rows, [spec["vout"], *bits])
    if not ok:
        return False, note
    threshold = float(spec.get("threshold", 0.45))
    max_code = (1 << len(bits)) - 1
    unique_codes = set()
    max_err = 0.0
    prev_code: int | None = None
    stable_count = 0
    checked = 0
    for idx, row in enumerate(rows):
        code_now = _decode(row, bits, threshold)
        if prev_code is None or code_now != prev_code:
            stable_count = 0
            prev_code = code_now
        else:
            stable_count += 1
        if stable_count < int(spec.get("settle_samples", 5)):
            continue
        if idx % int(spec.get("sample_stride", 4)) != 0:
            continue
        row = rows[idx]
        code = _decode(row, bits, threshold)
        unique_codes.add(code)
        expected = float(spec.get("vlo", 0.0)) + (float(spec.get("vhi", 0.9)) - float(spec.get("vlo", 0.0))) * code / max_code
        max_err = max(max_err, abs(row[spec["vout"]] - expected))
        checked += 1
    if checked < 5:
        return False, f"insufficient_stable_samples={checked}"
    if len(unique_codes) < int(spec.get("min_unique_codes", 4)):
        return False, f"unique_codes={len(unique_codes)}"
    if max_err > float(spec.get("vout_tolerance", 0.18)):
        return False, f"vout_max_err={max_err:.4f}"
    if spec.get("guard") and max(row[spec["guard"]] for row in rows[-max(5, len(rows)//5):]) < threshold:
        return False, "guard_never_high"
    return True, f"binary_dac_ok unique_codes={len(unique_codes)} max_err={max_err:.4f}"


def _check_dwa(rows: list[dict[str, float]], spec: dict[str, Any]) -> tuple[bool, str]:
    cells = spec["cell_outputs"]
    ok, note = _has_fields(rows, cells)
    if not ok:
        return False, note
    threshold = float(spec.get("threshold", 0.45))
    expected = int(spec.get("active_count", 3))
    active_sets: set[tuple[int, ...]] = set()
    bad = 0
    seen_active = 0
    for idx in _sample_indices(rows, 8):
        row = rows[idx]
        active = tuple(i for i, name in enumerate(cells) if row[name] >= threshold)
        if active:
            seen_active += 1
            active_sets.add(active)
            if len(active) != expected:
                bad += 1
    if seen_active < 5:
        return False, "no_active_windows"
    if bad > max(2, 0.12 * seen_active):
        return False, f"active_count_bad={bad}/{seen_active}"
    if len(active_sets) < int(spec.get("min_distinct_windows", 3)):
        return False, f"distinct_windows={len(active_sets)}"
    return True, f"dwa_ok distinct_windows={len(active_sets)}"


def _check_pfd(rows: list[dict[str, float]], spec: dict[str, Any]) -> tuple[bool, str]:
    up = spec["up"]
    dn = spec["dn"]
    fields = [up, dn]
    if spec.get("lock"):
        fields.append(spec["lock"])
    ok, note = _has_fields(rows, fields)
    if not ok:
        return False, note
    threshold = float(spec.get("threshold", 0.45))
    up_count = sum(1 for row in rows if row[up] >= threshold)
    dn_count = sum(1 for row in rows if row[dn] >= threshold)
    overlap = sum(1 for row in rows if row[up] >= threshold and row[dn] >= threshold)
    if up_count < int(spec.get("min_up_samples", 2)) or dn_count < int(spec.get("min_dn_samples", 2)):
        return False, f"pulse_samples_up_dn={up_count},{dn_count}"
    if overlap > int(spec.get("max_overlap_samples", 1)):
        return False, f"overlap_samples={overlap}"
    if spec.get("lock") and max(row[spec["lock"]] for row in rows[-max(5, len(rows)//4):]) < threshold:
        return False, "lock_never_high_late"
    return True, f"pfd_ok up={up_count} dn={dn_count} overlap={overlap}"


def _check_divider(rows: list[dict[str, float]], spec: dict[str, Any]) -> tuple[bool, str]:
    if spec.get("counter_bits"):
        bits = spec["counter_bits"]
        ok, note = _has_fields(rows, bits)
        if not ok:
            return False, note
        threshold = float(spec.get("threshold", 0.45))
        codes = [_decode(row, bits, threshold) for row in rows]
        unique = len(set(codes))
        if unique < int(spec.get("min_unique_codes", 4)):
            return False, f"counter_unique={unique}"
        return True, f"counter_ok unique={unique}"
    clk = spec["clock"]
    out = spec["output"]
    ok, note = _has_fields(rows, [clk, out])
    if not ok:
        return False, note
    threshold = float(spec.get("threshold", 0.45))
    in_edges = len(_rising_edges(rows, clk, threshold))
    out_edges = len(_rising_edges(rows, out, threshold))
    if in_edges < 6 or out_edges < 1:
        return False, f"edges_in_out={in_edges},{out_edges}"
    ratio = in_edges / max(1, out_edges * 2)
    target = float(spec.get("ratio", 3))
    if abs(ratio - target) > float(spec.get("ratio_tolerance", 1.25)):
        return False, f"ratio_est={ratio:.2f} target={target:.2f}"
    return True, f"divider_ok ratio_est={ratio:.2f} edges={in_edges}/{out_edges}"


def _check_sample_hold(rows: list[dict[str, float]], spec: dict[str, Any]) -> tuple[bool, str]:
    fields = [spec["vin"], spec["vout"]]
    if spec.get("settled"):
        fields.append(spec["settled"])
    ok, note = _has_fields(rows, fields)
    if not ok:
        return False, note
    vin = spec["vin"]
    vout = spec["vout"]
    vin_span = max(row[vin] for row in rows) - min(row[vin] for row in rows)
    vout_span = max(row[vout] for row in rows) - min(row[vout] for row in rows)
    mean_diff = sum(abs(row[vin] - row[vout]) for row in rows) / max(1, len(rows))
    if vin_span < 0.35 or vout_span < 0.25:
        return False, f"span_vin_vout={vin_span:.3f},{vout_span:.3f}"
    if mean_diff < float(spec.get("min_mean_diff", 0.025)):
        return False, f"looks_like_follower mean_diff={mean_diff:.4f}"
    if spec.get("settled") and max(row[spec["settled"]] for row in rows[-max(5, len(rows)//5):]) < float(spec.get("threshold", 0.45)):
        return False, "settled_never_high"
    return True, f"sample_hold_ok vin_span={vin_span:.3f} vout_span={vout_span:.3f} mean_diff={mean_diff:.4f}"


def _check_threshold(rows: list[dict[str, float]], spec: dict[str, Any]) -> tuple[bool, str]:
    vin = spec["vin"]
    out = spec["vout"]
    ok, note = _has_fields(rows, [vin, out])
    if not ok:
        return False, note
    threshold = float(spec.get("threshold", 0.45))
    margin = float(spec.get("margin", 0.06))
    logic_threshold = float(spec.get("logic_threshold", 0.45))
    checked = 0
    mismatches = 0
    high_seen = False
    low_seen = False
    for row in rows:
        x = row[vin]
        if abs(x - threshold) < margin:
            continue
        expected = 1 if x > threshold else 0
        observed = 1 if row[out] >= logic_threshold else 0
        checked += 1
        high_seen |= observed == 1
        low_seen |= observed == 0
        if expected != observed:
            mismatches += 1
    if checked < 12:
        return False, f"insufficient_threshold_samples={checked}"
    if not (high_seen and low_seen):
        return False, "threshold_output_not_toggling"
    if mismatches > max(3, 0.12 * checked):
        return False, f"threshold_mismatch={mismatches}/{checked}"
    return True, f"threshold_ok mismatch={mismatches}/{checked}"


def _check_window(rows: list[dict[str, float]], spec: dict[str, Any]) -> tuple[bool, str]:
    vin = spec["vin"]
    inside = spec["inside"]
    below = spec["below"]
    above = spec["above"]
    ok, note = _has_fields(rows, [vin, inside, below, above])
    if not ok:
        return False, note
    lo = float(spec.get("lo", 0.25))
    hi = float(spec.get("hi", 0.65))
    margin = float(spec.get("margin", 0.04))
    threshold = float(spec.get("threshold", 0.45))
    checked = 0
    bad = 0
    seen = {"below": False, "inside": False, "above": False}
    for row in rows:
        x = row[vin]
        if abs(x - lo) < margin or abs(x - hi) < margin:
            continue
        obs = {
            "below": row[below] >= threshold,
            "inside": row[inside] >= threshold,
            "above": row[above] >= threshold,
        }
        exp = {
            "below": x < lo,
            "inside": lo <= x <= hi,
            "above": x > hi,
        }
        checked += 1
        for key, value in obs.items():
            if value:
                seen[key] = True
        if obs != exp:
            bad += 1
    if checked < 12:
        return False, f"insufficient_window_samples={checked}"
    missing = [key for key, value in seen.items() if not value]
    if missing:
        return False, "window_region_missing=" + ",".join(missing)
    if bad > max(4, 0.15 * checked):
        return False, f"window_bad={bad}/{checked}"
    return True, f"window_ok bad={bad}/{checked}"


def _check_limiter(rows: list[dict[str, float]], spec: dict[str, Any]) -> tuple[bool, str]:
    vin = spec["vin"]
    out = spec["vout"]
    ok, note = _has_fields(rows, [vin, out])
    if not ok:
        return False, note
    vlo = float(spec.get("vlo", 0.18))
    vhi = float(spec.get("vhi", 0.72))
    tol = float(spec.get("tolerance", 0.08))
    outputs = [row[out] for row in rows]
    if min(outputs) < vlo - tol or max(outputs) > vhi + tol:
        return False, f"limiter_bounds={min(outputs):.3f},{max(outputs):.3f}"
    low_seen = any(row[vin] < vlo - 0.04 and abs(row[out] - vlo) < tol for row in rows)
    mid_seen = any(vlo + 0.08 < row[vin] < vhi - 0.08 and abs(row[out] - row[vin]) < tol for row in rows)
    high_seen = any(row[vin] > vhi + 0.04 and abs(row[out] - vhi) < tol for row in rows)
    if not (low_seen and mid_seen and high_seen):
        return False, f"limiter_regions low_mid_high={int(low_seen)},{int(mid_seen)},{int(high_seen)}"
    return True, f"limiter_ok out_range={min(outputs):.3f},{max(outputs):.3f}"


def _check_pulse(rows: list[dict[str, float]], spec: dict[str, Any]) -> tuple[bool, str]:
    trig = spec["trigger"]
    out = spec["vout"]
    ok, note = _has_fields(rows, [trig, out])
    if not ok:
        return False, note
    threshold = float(spec.get("threshold", 0.45))
    trig_edges = len(_rising_edges(rows, trig, threshold))
    out_edges = len(_rising_edges(rows, out, threshold))
    out_high = sum(1 for row in rows if row[out] >= threshold)
    if trig_edges < 3:
        return False, f"pulse_trigger_edges={trig_edges}"
    if out_edges < max(2, trig_edges - 2):
        return False, f"pulse_output_edges={out_edges} trigger_edges={trig_edges}"
    if out_high < int(spec.get("min_high_samples", 6)):
        return False, f"pulse_high_samples={out_high}"
    if rows[-1][out] >= threshold:
        return False, "pulse_did_not_return_low"
    return True, f"pulse_ok trigger_edges={trig_edges} out_edges={out_edges} high={out_high}"


CHECKERS = {
    "adc_dac": _check_adc_dac,
    "binary_dac": _check_binary_dac,
    "dwa": _check_dwa,
    "pfd": _check_pfd,
    "divider": _check_divider,
    "sample_hold": _check_sample_hold,
    "threshold": _check_threshold,
    "window": _check_window,
    "limiter": _check_limiter,
    "pulse": _check_pulse,
}


def check_csv(csv_path: str | Path, spec: dict[str, Any]) -> dict[str, Any]:
    rows = load_rows(csv_path)
    kind = spec["kind"]
    ok, note = CHECKERS[kind](rows, spec)
    return {
        "pass": bool(ok),
        "score": 1.0 if ok else 0.0,
        "notes": [note],
        "rows": len(rows),
        "kind": kind,
    }


def check_with_meta(csv_path: str | Path, task_dir: str | Path) -> dict[str, Any]:
    meta = json.loads((Path(task_dir) / "meta.json").read_text(encoding="utf-8"))
    return check_csv(csv_path, meta["v2_checker_spec"])
