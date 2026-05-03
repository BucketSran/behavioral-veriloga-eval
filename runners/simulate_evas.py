#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import multiprocessing as mp
import os
import re
import shutil
import subprocess
import tempfile
import warnings
from pathlib import Path


def read_meta(task_dir: Path) -> dict:
    return json.loads((task_dir / "meta.json").read_text(encoding="utf-8"))


def copy_inputs(run_dir: Path, dut_path: Path, tb_path: Path) -> tuple[Path, Path]:
    example_dir = tb_path.parent
    for src in example_dir.iterdir():
        dst = run_dir / src.name
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    # If the candidate DUT lives outside the example directory, stage it too.
    if dut_path.parent != example_dir:
        shutil.copy2(dut_path, run_dir / dut_path.name)

    dut_dst = run_dir / dut_path.name
    tb_dst = run_dir / tb_path.name
    return dut_dst, tb_dst


def run_evas(run_dir: Path, tb_file: Path, output_dir: Path, timeout_s: int) -> subprocess.CompletedProcess[str]:
    cmd = ["evas", "simulate", tb_file.name, "-o", str(output_dir)]
    return subprocess.run(
        cmd,
        cwd=run_dir,
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )


def load_csv(csv_path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k: float(v) for k, v in row.items()})
    return rows


def evaluate_noise_gen_csv(csv_path: Path) -> tuple[float, list[str]]:
    """Fast streaming checker for noise_gen tasks on very large CSV files."""
    count = 0
    mean = 0.0
    m2 = 0.0
    max_abs = 0.0
    missing_cols = False

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        in_col = "vin_i" if "vin_i" in fields else ("base_signal" if "base_signal" in fields else None)
        out_col = "vout_o" if "vout_o" in fields else ("fluctuated_out" if "fluctuated_out" in fields else None)
        if in_col is None or out_col is None:
            missing_cols = True
        else:
            for row in reader:
                try:
                    x = float(row[out_col]) - float(row[in_col])
                except (TypeError, ValueError):
                    continue
                count += 1
                delta = x - mean
                mean += delta / count
                m2 += delta * (x - mean)
                ax = abs(x)
                if ax > max_abs:
                    max_abs = ax

    if missing_cols:
        return 0.0, ["missing vin_i/vout_o"]
    if count == 0:
        return 0.0, ["noise_gen_empty_csv"]

    var = m2 / count
    std = math.sqrt(max(var, 0.0))
    ok = std > 0.01 and max_abs > 0.05
    return (1.0 if ok else 0.0), [f"noise_std={std:.4f} max_abs={max_abs:.4f} samples={count}"]


def _csv_fields(csv_path: Path) -> set[str]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return set(reader.fieldnames or [])


def _float_cell(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return default


def _stream_max(csv_path: Path, key: str) -> float:
    max_val = 0.0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            max_val = max(max_val, _float_cell(row, key))
    return max_val


def _stream_pfd_deadzone_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"time", "ref", "div", "up", "dn"}
    if not required.issubset(fields):
        return 0.0, ["missing ref/div/up/dn"]

    vth = 0.5 * _stream_max(csv_path, "ref")
    prev_time: float | None = None
    prev_up = 0.0
    prev_dn = 0.0
    prev_up_bit = 0
    initialized = False
    high_up_dt = 0.0
    high_dn_dt = 0.0
    total_dt = 0.0
    run_len = 0
    max_run = 0
    up_pulses = 0

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            time = _float_cell(row, "time")
            up = _float_cell(row, "up")
            dn = _float_cell(row, "dn")
            up_bit = 1 if up > vth else 0
            dn_bit = 1 if dn > vth else 0
            if initialized:
                dt = time - (prev_time if prev_time is not None else time)
                if dt > 0.0:
                    total_dt += dt
                    if 0.5 * (prev_up + up) > vth:
                        high_up_dt += dt
                    if 0.5 * (prev_dn + dn) > vth:
                        high_dn_dt += dt
                if prev_up_bit == 0 and up_bit == 1:
                    up_pulses += 1
            if up_bit and dn_bit:
                run_len += 1
                max_run = max(max_run, run_len)
            else:
                run_len = 0
            initialized = True
            prev_time = time
            prev_up = up
            prev_dn = dn
            prev_up_bit = up_bit

    up_frac = high_up_dt / max(total_dt, 1e-18)
    dn_frac = high_dn_dt / max(total_dt, 1e-18)
    if not (0.001 <= up_frac <= 0.03):
        return 0.0, [f"up_frac_out_of_range={up_frac:.4f}"]
    if dn_frac > 0.002:
        return 0.0, [f"dn_frac_too_high={dn_frac:.4f}"]
    if max_run > 6:
        return 0.0, [f"overlap_too_long={max_run}"]
    if up_pulses < 10:
        return 0.0, [f"too_few_up_pulses={up_pulses}"]
    return 1.0, [f"up_frac={up_frac:.4f} dn_frac={dn_frac:.4f} up_pulses={up_pulses}"]


def _stream_pfd_reset_race_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"time", "ref", "div", "up", "dn"}
    if not required.issubset(fields):
        return 0.0, ["missing ref/div/up/dn"]

    vth = 0.5 * _stream_max(csv_path, "ref")
    windows = {
        "first": {"start": 20e-9, "end": 120e-9, "up_dt": 0.0, "dn_dt": 0.0, "dt": 0.0, "up_pulses": 0, "dn_pulses": 0, "rows": 0},
        "second": {"start": 160e-9, "end": 260e-9, "up_dt": 0.0, "dn_dt": 0.0, "dt": 0.0, "up_pulses": 0, "dn_pulses": 0, "rows": 0},
    }
    total_dt = 0.0
    overlap_dt = 0.0
    prev: dict[str, float] | None = None
    prev_up_bit = 0
    prev_dn_bit = 0

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur = {
                "time": _float_cell(row, "time"),
                "up": _float_cell(row, "up"),
                "dn": _float_cell(row, "dn"),
            }
            up_bit = 1 if cur["up"] > vth else 0
            dn_bit = 1 if cur["dn"] > vth else 0
            for state in windows.values():
                if state["start"] <= cur["time"] <= state["end"]:
                    state["rows"] += 1
                    if prev_up_bit == 0 and up_bit == 1:
                        state["up_pulses"] += 1
                    if prev_dn_bit == 0 and dn_bit == 1:
                        state["dn_pulses"] += 1
            if prev is not None:
                dt = cur["time"] - prev["time"]
                if dt > 0.0:
                    total_dt += dt
                    up_mid = 0.5 * (prev["up"] + cur["up"])
                    dn_mid = 0.5 * (prev["dn"] + cur["dn"])
                    if up_mid > vth and dn_mid > vth:
                        overlap_dt += dt
                    mid_t = 0.5 * (prev["time"] + cur["time"])
                    for state in windows.values():
                        if state["start"] <= mid_t <= state["end"]:
                            state["dt"] += dt
                            if up_mid > vth:
                                state["up_dt"] += dt
                            if dn_mid > vth:
                                state["dn_dt"] += dt
            prev = cur
            prev_up_bit = up_bit
            prev_dn_bit = dn_bit

    first = windows["first"]
    second = windows["second"]
    if first["rows"] < 4 or second["rows"] < 4:
        return 0.0, ["insufficient_window_samples"]
    up_first = first["up_dt"] / max(first["dt"], 1e-18)
    dn_first = first["dn_dt"] / max(first["dt"], 1e-18)
    up_second = second["up_dt"] / max(second["dt"], 1e-18)
    dn_second = second["dn_dt"] / max(second["dt"], 1e-18)
    overlap_frac = overlap_dt / max(total_dt, 1e-18)
    ok = (
        0.001 <= up_first <= 0.08
        and dn_first <= 0.01
        and 0.001 <= dn_second <= 0.08
        and up_second <= 0.01
        and first["up_pulses"] >= 4
        and second["dn_pulses"] >= 4
        and overlap_frac <= 0.01
    )
    return (1.0 if ok else 0.0), [
        f"up_first={up_first:.4f} dn_first={dn_first:.4f} "
        f"up_second={up_second:.4f} dn_second={dn_second:.4f} "
        f"up_pulses_first={int(first['up_pulses'])} "
        f"dn_pulses_second={int(second['dn_pulses'])} "
        f"overlap_frac={overlap_frac:.4f}"
    ]


def _stream_dac_binary_clk_4b_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"din3", "din2", "din1", "din0", "aout"}
    if not required.issubset(fields):
        return 0.0, ["missing din*/aout"]
    sums = {idx: 0.0 for idx in range(16)}
    counts = {idx: 0 for idx in range(16)}
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = (
                (1 if _float_cell(row, "din3") > 0.45 else 0) * 8
                + (1 if _float_cell(row, "din2") > 0.45 else 0) * 4
                + (1 if _float_cell(row, "din1") > 0.45 else 0) * 2
                + (1 if _float_cell(row, "din0") > 0.45 else 0)
            )
            sums[code] += _float_cell(row, "aout")
            counts[code] += 1
    medians = {code: sums[code] / counts[code] for code in counts if counts[code] > 0}
    sorted_codes = sorted(medians)
    monotonic = all(medians[sorted_codes[i]] <= medians[sorted_codes[i + 1]] + 1e-9 for i in range(len(sorted_codes) - 1))
    span = medians[sorted_codes[-1]] - medians[sorted_codes[0]] if sorted_codes else 0.0
    ok = len(sorted_codes) >= 14 and monotonic and span > 0.7
    return (1.0 if ok else 0.0), [f"levels={len(sorted_codes)} aout_span={span:.3f}"]


def _stream_sar_adc_dac_weighted_8b_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"vin", "vin_sh", "vout", "rst_n"} | {f"dout_{idx}" for idx in range(8)}
    if not required.issubset(fields):
        return 0.0, ["missing vin/vin_sh/vout/rst_n or dout_0..7"]
    count = 0
    err_sum = 0.0
    min_vout = float("inf")
    max_vout = float("-inf")
    codes: set[int] = set()
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if _float_cell(row, "rst_n") <= 0.45:
                continue
            code = sum((1 if _float_cell(row, f"dout_{idx}") > 0.45 else 0) << idx for idx in range(8))
            vin_sh = _float_cell(row, "vin_sh")
            vout = _float_cell(row, "vout")
            codes.add(code)
            err_sum += abs(vin_sh - vout)
            min_vout = min(min_vout, vout)
            max_vout = max(max_vout, vout)
            count += 1
    if count == 0:
        return 0.0, ["no post-reset samples"]
    unique_codes = len(codes)
    avg_abs_err = err_sum / count
    vout_span = max_vout - min_vout
    ok = unique_codes >= 48 and vout_span > 0.7 and avg_abs_err < 0.08
    return (1.0 if ok else 0.0), [f"unique_codes={unique_codes} avg_abs_err={avg_abs_err:.4f} vout_span={vout_span:.3f}"]


def _stream_dwa_ptr_gen_no_overlap_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"time", "clk_i", "rst_ni", "ptr_0", "cell_en_0"}
    if not required.issubset(fields):
        return 0.0, ["missing time/clk_i/rst_ni/ptr_0/cell_en_0"]
    ptr_cols = sorted([name for name in fields if re.fullmatch(r"ptr_\d+", name)], key=lambda n: int(n.rsplit("_", 1)[1]))
    cell_cols = sorted([name for name in fields if re.fullmatch(r"cell_en_\d+", name)], key=lambda n: int(n.rsplit("_", 1)[1]))
    if not ptr_cols or not cell_cols:
        return 0.0, ["missing ptr_* or cell_en_* columns"]

    pending_samples: list[float] = []
    sampled_cycles = 0
    bad_ptr_rows = 0
    max_active_cells = 0
    overlap_count = 0
    prev_active: set[int] | None = None
    prev_clk = 0.0
    initialized = False

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            time = _float_cell(row, "time")
            clk = _float_cell(row, "clk_i")
            if initialized and prev_clk < 0.45 <= clk:
                pending_samples.append(time + 1.0e-9)
            while pending_samples and time >= pending_samples[0]:
                pending_samples.pop(0)
                if _float_cell(row, "rst_ni") <= 0.45:
                    continue
                sampled_cycles += 1
                ptr_active = {idx for idx, col in enumerate(ptr_cols) if _float_cell(row, col) > 0.45}
                if len(ptr_active) not in (0, 1):
                    bad_ptr_rows += 1
                active_cells = {idx for idx, col in enumerate(cell_cols) if _float_cell(row, col) > 0.45}
                max_active_cells = max(max_active_cells, len(active_cells))
                if prev_active is not None and prev_active & active_cells:
                    overlap_count += 1
                prev_active = active_cells
            prev_clk = clk
            initialized = True
    if sampled_cycles < 2:
        return 0.0, [f"insufficient_post_reset_samples count={sampled_cycles}"]
    ok = bad_ptr_rows == 0 and max_active_cells > 0 and overlap_count == 0
    return (1.0 if ok else 0.0), [
        f"sampled_cycles={sampled_cycles} bad_ptr_rows={bad_ptr_rows} "
        f"max_active_cells={max_active_cells} overlap_count={overlap_count}"
    ]


def _stream_not_gate_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    if {"a", "y"}.issubset(fields):
        a_col, y_col = "a", "y"
    elif {"not_a", "not_y"}.issubset(fields):
        a_col, y_col = "not_a", "not_y"
    else:
        return 0.0, ["missing a/y"]
    sampled_count = 0
    good = 0
    last_t = -1.0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            time = _float_cell(row, "time")
            if time - last_t < 5e-10:
                continue
            last_t = time
            sampled_count += 1
            if (_float_cell(row, a_col) > 0.4) != (_float_cell(row, y_col) > 0.4):
                good += 1
    if sampled_count < 10:
        return 0.0, [f"too_few_samples={sampled_count}"]
    frac = good / sampled_count
    return (1.0 if frac > 0.9 else 0.0), [f"invert_match_frac={frac:.3f}"]


def _stream_gray_counter_one_bit_change_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)

    def pick(names: list[str]) -> str | None:
        lower = {field.lower(): field for field in fields}
        for name in names:
            if name.lower() in lower:
                return lower[name.lower()]
        return None

    clk_col = pick(["clk", "CLK"])
    rst_col = pick(["rst", "RST", "rstb", "RSTB"])
    g_cols = [pick([f"g{idx}", f"G{idx}"]) for idx in range(4)]
    if clk_col is None or rst_col is None or any(col is None for col in g_cols):
        return 0.0, ["missing clk/rst/g0..g3"]

    total_rows = 0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for _ in reader:
            total_rows += 1
    if total_rows == 0:
        return 0.0, ["empty"]
    reset_prefix_rows = max(4, total_rows // 10)

    rst_prefix_high = False
    edge_count = 0
    post_reset_codes: list[int] = []
    pending_offsets: list[int] = []
    prev_clk: float | None = None

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader):
            clk = _float_cell(row, clk_col)
            rst = _float_cell(row, rst_col)
            if row_idx < reset_prefix_rows and rst > 0.45:
                rst_prefix_high = True
            if prev_clk is not None and prev_clk <= 0.45 < clk:
                # Match the row-based checker's settle=min(edge_idx + 8, last_row).
                # The current edge row is processed below, so start at 9.
                pending_offsets.append(9)
                edge_count += 1
            prev_clk = clk

            for pending_idx in range(len(pending_offsets) - 1, -1, -1):
                pending_offsets[pending_idx] -= 1
                if pending_offsets[pending_idx] > 0:
                    continue
                del pending_offsets[pending_idx]
                if (rst_prefix_high and rst > 0.45) or ((not rst_prefix_high) and rst < 0.45):
                    continue
                code = 0
                for bit_idx, col in enumerate(g_cols):
                    assert col is not None
                    if _float_cell(row, col) > 0.45:
                        code |= 1 << bit_idx
                post_reset_codes.append(code)

    if edge_count < 20:
        return 0.0, [f"not_enough_clk_edges={edge_count}"]
    if len(post_reset_codes) < 16:
        return 0.0, [f"not_enough_post_reset_codes={len(post_reset_codes)}"]

    bad_transitions = sum(
        1
        for a, b in zip(post_reset_codes[:-1], post_reset_codes[1:])
        if bin(a ^ b).count("1") != 1
    )
    unique_codes = set(post_reset_codes)
    expected_grays = {i ^ (i >> 1) for i in range(16)}
    if bad_transitions:
        return 0.0, [f"gray_property_violated bad_transitions={bad_transitions}"]
    missing = 16 - len(expected_grays & unique_codes)
    if missing:
        return 0.0, [f"missing_gray_codes count={missing}"]
    return 1.0, [f"unique_codes={len(unique_codes)} bad_transitions={bad_transitions}"]


def _stream_dwa_wraparound_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"time", "clk_i", "rst_ni", "ptr_0", "cell_en_0", "code_0"}
    if not required.issubset(fields):
        return 0.0, ["missing time/clk_i/rst_ni/ptr_0/cell_en_0/code_0"]

    ptr_cols = sorted(
        [field for field in fields if re.fullmatch(r"ptr_\d+", field)],
        key=lambda item: int(item.rsplit("_", 1)[1]),
    )
    cell_cols = sorted(
        [field for field in fields if re.fullmatch(r"cell_en_\d+", field)],
        key=lambda item: int(item.rsplit("_", 1)[1]),
    )
    code_cols = sorted(
        [field for field in fields if re.fullmatch(r"code_\d+", field)],
        key=lambda item: int(item.rsplit("_", 1)[1]),
    )
    if len(ptr_cols) != 16 or len(cell_cols) != 16 or len(code_cols) != 4:
        return 0.0, ["expected ptr_0..15, cell_en_0..15, and code_0..3 columns"]

    pending_samples: list[float] = []
    sampled: list[tuple[int, list[int], set[int]]] = []
    initialized = False
    prev_clk = 0.0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            time = _float_cell(row, "time")
            clk = _float_cell(row, "clk_i")
            if initialized and prev_clk < 0.45 <= clk:
                pending_samples.append(time + 1.0e-9)
            while pending_samples and time >= pending_samples[0]:
                pending_samples.pop(0)
                if _float_cell(row, "rst_ni") <= 0.45:
                    continue
                code = sum(
                    (1 if _float_cell(row, col) > 0.45 else 0) << int(col[5:])
                    for col in code_cols
                )
                ptr_active = [idx for idx, col in enumerate(ptr_cols) if _float_cell(row, col) > 0.45]
                active_cells = {idx for idx, col in enumerate(cell_cols) if _float_cell(row, col) > 0.45}
                sampled.append((code, ptr_active, active_cells))
            prev_clk = clk
            initialized = True

    if len(sampled) < 5:
        return 0.0, [f"insufficient_post_reset_samples count={len(sampled)}"]

    expected_ptr = 13
    bad_ptr_rows = 0
    bad_count_rows = 0
    wrap_events = 0
    split_wrap_rows = 0
    prev_ptr = expected_ptr
    for code, ptr_active, active_cells in sampled:
        expected_ptr = (expected_ptr + code) % 16
        if expected_ptr < prev_ptr:
            wrap_events += 1
        if ptr_active != [expected_ptr]:
            bad_ptr_rows += 1
        if len(active_cells) != code:
            bad_count_rows += 1
        if active_cells and (max(active_cells) - min(active_cells) + 1) > len(active_cells):
            split_wrap_rows += 1
        prev_ptr = expected_ptr

    ok = bad_ptr_rows == 0 and bad_count_rows == 0 and wrap_events >= 2 and split_wrap_rows >= 2
    return (1.0 if ok else 0.0), [
        f"sampled_cycles={len(sampled)} bad_ptr_rows={bad_ptr_rows} "
        f"bad_count_rows={bad_count_rows} wrap_events={wrap_events} "
        f"split_wrap_rows={split_wrap_rows}"
    ]


def _stream_gain_extraction_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"vinp", "vinn", "vamp_p", "vamp_n"}
    if not required.issubset(fields):
        return 0.0, ["missing vinp/vinn/vamp_p/vamp_n"]

    count = 0
    mean_in = 0.0
    mean_out = 0.0
    m2_in = 0.0
    m2_out = 0.0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vin = _float_cell(row, "vinp") - _float_cell(row, "vinn")
            vout = _float_cell(row, "vamp_p") - _float_cell(row, "vamp_n")
            count += 1
            delta_in = vin - mean_in
            mean_in += delta_in / count
            m2_in += delta_in * (vin - mean_in)
            delta_out = vout - mean_out
            mean_out += delta_out / count
            m2_out += delta_out * (vout - mean_out)
    if count == 0:
        return 0.0, ["empty"]
    std_in = math.sqrt(max(m2_in / count, 0.0))
    std_out = math.sqrt(max(m2_out / count, 0.0))
    gain = std_out / std_in if std_in > 1e-12 else 0.0
    ok = gain > 4.0 and std_out > std_in
    return (1.0 if ok else 0.0), [f"diff_gain={gain:.2f}"]


def _stream_multimod_divider_ratio_switch_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"time", "clk_in", "div_out"}
    if not required.issubset(fields):
        return 0.0, ["missing time/clk_in/div_out"]

    in_edges: list[float] = []
    out_edges: list[float] = []
    initialized = False
    prev_in = 0.0
    prev_out = 0.0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            time = _float_cell(row, "time")
            clk_in = _float_cell(row, "clk_in")
            div_out = _float_cell(row, "div_out")
            if initialized and prev_in < 0.45 <= clk_in:
                in_edges.append(time)
            if initialized and prev_out < 0.45 <= div_out:
                out_edges.append(time)
            prev_in = clk_in
            prev_out = div_out
            initialized = True

    if len(in_edges) < 40 or len(out_edges) < 10:
        return 0.0, [f"not_enough_edges in={len(in_edges)} out={len(out_edges)}"]

    windows = [
        (10e-9, 90e-9, 4, "pre_div4"),
        (120e-9, 190e-9, 5, "mid_div5"),
        (220e-9, 300e-9, 4, "post_div4"),
    ]
    details: list[str] = []
    for t0, t1, expected_ratio, label in windows:
        win_in = [time for time in in_edges if t0 <= time <= t1]
        win_out = [time for time in out_edges if t0 <= time <= t1]
        if len(win_in) < expected_ratio * 2 or len(win_out) < 2:
            return 0.0, [f"{label}_insufficient_edges in={len(win_in)} out={len(win_out)}"]
        measured_ratio = len(win_in) / max(len(win_out), 1)
        details.append(f"{label}={measured_ratio:.2f}")
        if abs(measured_ratio - expected_ratio) > 0.35:
            return 0.0, [";".join(details)]
    return 1.0, [";".join(details)]


STREAMING_BEHAVIOR_CHECKS = {
    "pfd_deadzone_smoke": _stream_pfd_deadzone_csv,
    "pfd_reset_race_smoke": _stream_pfd_reset_race_csv,
    "dac_binary_clk_4b_smoke": _stream_dac_binary_clk_4b_csv,
    "sar_adc_dac_weighted_8b_smoke": _stream_sar_adc_dac_weighted_8b_csv,
    "dwa_ptr_gen_no_overlap_smoke": _stream_dwa_ptr_gen_no_overlap_csv,
    "digital_basics_smoke": _stream_not_gate_csv,
    "gray_counter_one_bit_change_smoke": _stream_gray_counter_one_bit_change_csv,
    "dwa_wraparound_smoke": _stream_dwa_wraparound_csv,
    "gain_extraction_smoke": _stream_gain_extraction_csv,
    "multimod_divider_ratio_switch_smoke": _stream_multimod_divider_ratio_switch_csv,
}

VALIDATED_FAST_CHECKER_TASKS = frozenset(STREAMING_BEHAVIOR_CHECKS)


def _env_enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _streaming_notes_require_row_fallback(notes: list[str]) -> bool:
    """Avoid turning observable/interface mismatches into behavior failures."""
    fallback_prefixes = (
        "missing ",
        "expected ",
    )
    return any(note.startswith(fallback_prefixes) for note in notes)


def evaluate_streaming_behavior(task_id: str, csv_path: Path) -> tuple[float, list[str]] | None:
    force_streaming = _env_enabled("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS")
    if not force_streaming:
        if _env_enabled("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS"):
            return None
        if task_id not in VALIDATED_FAST_CHECKER_TASKS:
            return None

    checker = STREAMING_BEHAVIOR_CHECKS.get(task_id)
    if checker is None:
        return None
    score, notes = checker(csv_path)
    if not force_streaming and _streaming_notes_require_row_fallback(notes):
        return None
    return score, [f"streaming_checker:{note}" for note in notes]


def rising_edges(values: list[float], times: list[float], threshold: float = 0.45) -> list[float]:
    edges: list[float] = []
    for i in range(1, len(values)):
        if values[i - 1] < threshold <= values[i]:
            edges.append(times[i])
    return edges


def sample_rows_at_or_after_times(
    rows: list[dict[str, float]],
    target_times: list[float],
    *,
    rst_key: str | None = None,
    rst_threshold: float = 0.45,
) -> list[dict[str, float]]:
    """Return rows whose time is the first sample at/after each target time.

    This function is linear in len(rows) + len(target_times). It replaces
    repeated per-target full scans that become O(n^2) on large tran.csv files.
    """
    if not rows or not target_times:
        return []

    sampled: list[dict[str, float]] = []
    row_idx = 0
    n_rows = len(rows)
    for t in target_times:
        while row_idx < n_rows and rows[row_idx]["time"] < t:
            row_idx += 1
        if row_idx >= n_rows:
            break
        row = rows[row_idx]
        if rst_key is None or row.get(rst_key, 0.0) > rst_threshold:
            sampled.append(row)
    return sampled


def decode_bus(rows: list[dict[str, float]], bit_names: list[str], threshold: float = 0.45) -> list[int]:
    decoded: list[int] = []
    for row in rows:
        code = 0
        for bit_name in bit_names:
            bit = 1 if row[bit_name] >= threshold else 0
            m = re.search(r"(\d+)$", bit_name)
            if m is None:
                warnings.warn(
                    f"decode_bus: bit_name {bit_name!r} has no trailing digit; "
                    "defaulting to bit index 0, result may be incorrect",
                    stacklevel=2,
                )
            idx = int(m.group(1)) if m else 0
            code |= bit << idx
        decoded.append(code)
    return decoded


def indexed_columns(keys: set[str], prefix: str) -> list[str]:
    cols = [k for k in keys if re.fullmatch(rf"{re.escape(prefix)}\d+", k)]
    return sorted(cols, key=lambda name: int(re.search(r"(\d+)$", name).group(1)))


def _canonical_signal_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _set_alias_if_missing(row: dict[str, float], alias: str, value: float) -> None:
    if alias and alias not in row:
        row[alias] = value


def _expanded_row_aliases(row: dict[str, float]) -> dict[str, float]:
    expanded = dict(row)
    original = list(row.items())
    for raw_key, value in original:
        key = raw_key.strip()
        if not key:
            continue

        candidates = {key, key.lower()}
        for sep in (":", "."):
            if sep in key:
                tail = key.split(sep)[-1]
                candidates.add(tail)
                candidates.add(tail.lower())

        vm = re.match(r"(?i)^v\(\s*([^)]+)\s*\)$", key)
        if vm:
            inner = vm.group(1).strip()
            candidates.add(inner)
            candidates.add(inner.lower())

        for cand in list(candidates):
            cm = re.match(r"^([A-Za-z_][A-Za-z0-9_$]*)\[(\d+)\]$", cand)
            if cm:
                root = cm.group(1)
                idx = cm.group(2)
                candidates.update(
                    {
                        f"{root}_{idx}",
                        f"{root}{idx}",
                        f"{root.lower()}_{idx}",
                        f"{root.lower()}{idx}",
                    }
                )
                # Common generated DWA/vector port names use direction suffixes
                # (`ptr_o[0]`, `cell_en_o[0]`, `code_i[0]`). The checkers use
                # scalar observable names (`ptr_0`, `cell_en_0`, `code_0`).
                stripped_root = root.lower()
                for suffix in ("_msb_i", "_lsb_i", "_o", "_i"):
                    if stripped_root.endswith(suffix):
                        stripped_root = stripped_root[: -len(suffix)]
                        break
                if stripped_root in {"ptr", "cell_en", "code"}:
                    candidates.update(
                        {
                            f"{stripped_root}_{idx}",
                            f"{stripped_root}{idx}",
                        }
                    )

            dm = re.search(r"(dout|din|div_code|cell_en|ptr|state|code|bin_o|g|d)_?(\d+)$", cand.lower())
            if dm:
                root = dm.group(1)
                idx = dm.group(2)
                candidates.update(
                    {
                        f"{root}_{idx}",
                        f"{root}{idx}",
                    }
                )
                if root == "d":
                    candidates.update({f"dout_{idx}", f"dout{idx}"})

        for alias in candidates:
            _set_alias_if_missing(expanded, alias, value)

    canonical_map: dict[str, str] = {}
    for key in expanded:
        canonical_map.setdefault(_canonical_signal_name(key), key)

    for idx in range(16):
        for target in (
            f"dout_{idx}",
            f"dout{idx}",
            f"din_{idx}",
            f"din{idx}",
            f"ptr_{idx}",
            f"cell_en_{idx}",
            f"g{idx}",
            f"state_{idx}",
            f"div_code_{idx}",
        ):
            ckey = _canonical_signal_name(target)
            if target not in expanded and ckey in canonical_map:
                expanded[target] = expanded[canonical_map[ckey]]

    for target in (
        "vin",
        "vout",
        "vin_sh",
        "rst_n",
        "clk",
        "clk_in",
        "clk_out",
        "lock",
        "ref_clk",
        "fb_clk",
        "vctrl_mon",
        "vinp",
        "vinn",
        "out_p",
        "out_n",
        "outp",
        "outn",
        "a",
        "b",
        "y",
        "d",
        "q",
        "qb",
        "rst",
        "ref",
        "div",
        "up",
        "dn",
        "serial_out",
        "dpn",
        "rstb",
        "en",
        "phase_out",
        "guard_out",
        "delay_out",
        "seen_out",
        "first_err_out",
        "max_err_out",
        "count_out",
        "metric_out",
        "mode",
        "out",
        "vin_i",
        "vout_o",
    ):
        ckey = _canonical_signal_name(target)
        if target not in expanded and ckey in canonical_map:
            expanded[target] = expanded[canonical_map[ckey]]

    return expanded


_TASK_ALIAS_CANDIDATES: dict[str, dict[str, tuple[str, ...]]] = {
    "digital_basics_smoke": {
        "a": ("not_a",),
        "y": ("not_y",),
    },
    "and_gate_smoke": {
        "a": ("and_a",),
        "b": ("and_b",),
        "y": ("and_y",),
    },
    "or_gate_smoke": {
        "a": ("or_a",),
        "b": ("or_b",),
        "y": ("or_y",),
    },
    "dff_rst_smoke": {
        "d": ("dff_d",),
        "clk": ("dff_clk",),
        "rst": ("dff_rst",),
        "q": ("dff_q",),
        "qb": ("dff_qb",),
    },
    "dwa_ptr_gen_no_overlap_smoke": {
        "clk_i": ("clk",),
        "rst_ni": ("rst_n",),
    },
    "dwa_wraparound_smoke": {
        "clk_i": ("clk",),
        "rst_ni": ("rst_n",),
        "code_0": ("code0",),
        "code_1": ("code1",),
        "code_2": ("code2",),
        "code_3": ("code3",),
    },
    "noise_gen_smoke": {
        "vin_i": ("vin",),
        "vout_o": ("vout",),
    },
    "sar_adc_dac_weighted_8b_smoke": {
        "vin_sh": ("vin",),
    },
    # benchmark-v2 perturbation tasks — maps check-target → CSV-column
    "gray_counter_4b_p1p2": {
        "clk": ("strobe",),
        "rstb": ("reset_n",),
        "g3": ("qb3",),
        "g2": ("qb2",),
        "g1": ("qb1",),
        "g0": ("qb0",),
    },
    "clk_divider_p2p3p4": {
        "clk_in": ("cadence_in","cadence",),
        "clk_out": ("toggled",),
    },
    "clk_divider_p4p5p6": {
        "clk_in": ("cadence",),
        "clk_out": ("toggled",),
    },
    "xor_pd_p2p3p4": {
        "ref": ("sig_a",),
        "div": ("sig_b",),
        "pd_out": ("match_out",),
    },
    "dff_rst_p2p5": {
        "d": ("sample_in",),
        "clk": ("strobe",),
        "rst": ("force_low",),
        "q": ("state",),
        "qb": ("state_n",),
    },
    "comparator_p2p3p4": {
        "vinp": ("sense_plus",),
        "vinn": ("sense_minus",),
        "out_p": ("decision",),
    },
    "sample_hold_p2p3p4": {
        "in": ("analog_in",),
        "clk": ("sample_cmd",),
        "out": ("held_value",),
    },
    "lfsr_p2p3p4": {
        "dpn": ("prbs_out",),
        "rstb": ("init_n",),
    },
    "clk_burst_gen_p2p3p5": {
        "CLK": ("event_in",),
        "RST_N": ("clear_n",),
        "CLK_OUT": ("burst_out",),
    },
    "pfd_updn_p2p3p4": {
        "ref": ("early_edge",),
        "div": ("late_edge",),
        "up": ("adv",),
        "dn": ("ret",),
    },
    "flash_adc_3b_p2p3p4": {
        "vin": ("analog_level",),
        "clk": ("sample_strobe",),
        "dout2": ("qb2",),
        "dout1": ("qb1",),
        "dout0": ("qb0",),
    },
    # batch 2+3 perturbation tasks
    "mux_4to1_p2p3p4": {
        "sel1": ("pick_1",),
        "sel0": ("pick_0",),
        "y": ("routed",),
        "d0": ("lane_0",),
        "d1": ("lane_1",),
        "d2": ("lane_2",),
        "d3": ("lane_3",),
    },
    "pfd_deadzone_p2p3p4": {
        "ref": ("first_edge",),
        "div": ("second_edge",),
        "up": ("lead_flag",),
    },
    "sample_hold_droop_p2p3p4": {
        "vin": ("analog_in",),
        "clk": ("sample_cmd",),
        "vout": ("held_value",),
    },
    "dac_therm_16b_p2p3p4": {
        "rst_n": ("clear",),
        "vout": ("level_out",),
        "d0": ("active_lines_0",),
        "d1": ("active_lines_1",),
        "d2": ("active_lines_2",),
        "d3": ("active_lines_3",),
        "d4": ("active_lines_4",),
        "d5": ("active_lines_5",),
        "d6": ("active_lines_6",),
        "d7": ("active_lines_7",),
        "d8": ("active_lines_8",),
        "d9": ("active_lines_9",),
        "d10": ("active_lines_10",),
        "d11": ("active_lines_11",),
        "d12": ("active_lines_12",),
        "d13": ("active_lines_13",),
        "d14": ("active_lines_14",),
        "d15": ("active_lines_15",),
    },
    "noise_gen_p2p3p4": {
        "vin_i": ("base_signal",),
        "vout_o": ("fluctuated_out",),
    },
    "serializer_8b_p2p3p4": {
        "load": ("latch_cmd",),
        "clk": ("shift_clock",),
        "sout": ("serial_stream",),
    },
}


def normalize_rows_for_task(task_id: str, rows: list[dict[str, float]]) -> list[dict[str, float]]:
    if not rows:
        return rows
    normalized = [_expanded_row_aliases(row) for row in rows]
    alias_rules = _TASK_ALIAS_CANDIDATES.get(task_id, {})
    if not alias_rules:
        return normalized
    for row in normalized:
        for target, candidates in alias_rules.items():
            if target in row:
                continue
            for cand in candidates:
                if cand in row:
                    row[target] = row[cand]
                    break
    return normalized


def check_clk_div(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or "clk_in" not in rows[0] or "clk_out" not in rows[0]:
        return False, "missing clk_in/clk_out"
    times = [r["time"] for r in rows]
    in_edges = rising_edges([r["clk_in"] for r in rows], times)
    out_edges = rising_edges([r["clk_out"] for r in rows], times)
    if len(in_edges) < 8 or len(out_edges) < 2:
        return False, "not enough clock edges"
    ratio = len(in_edges) / max(len(out_edges), 1)
    return (3.0 <= ratio <= 5.0), f"edge_ratio={ratio:.2f}"


def check_clk_divider(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"clk_in", "clk_out", "lock"}.issubset(rows[0]):
        return False, "missing clk_in/clk_out/lock"

    sample = rows[0]
    div_cols: list[str] = []
    for idx in range(8):
        col = None
        for candidate in (f"div_code_{idx}", f"div_code[{idx}]"):
            if candidate in sample:
                col = candidate
                break
        if col is None:
            return False, "missing div_code_*"
        div_cols.append(col)

    ratio = 0
    for idx, col in enumerate(div_cols):
        if sample[col] > 0.45:
            ratio |= (1 << idx)
    if ratio < 1:
        ratio = 1

    times = [r["time"] for r in rows]
    clk_vals = [r["clk_in"] for r in rows]
    out_vals = [r["clk_out"] for r in rows]
    lock_vals = [r["lock"] for r in rows]

    in_edges = rising_edges(clk_vals, times)
    out_edges = rising_edges(out_vals, times)
    lock_edges = rising_edges(lock_vals, times)
    final_lock_high = lock_vals[-1] > 0.45

    if len(in_edges) < 8 or len(out_edges) < 2:
        return False, "not enough clock edges"

    if ratio == 1:
        level_match = sum(1 for ci, co in zip(clk_vals, out_vals) if ((ci > 0.45) == (co > 0.45))) / max(len(rows), 1)
        edge_ratio = len(in_edges) / max(len(out_edges), 1)
        ok = level_match > 0.98 and 0.95 <= edge_ratio <= 1.05 and final_lock_high
        return ok, f"ratio_code=1 in_edges={len(in_edges)} out_edges={len(out_edges)} lock_edges={len(lock_edges)} final_lock_high={final_lock_high} level_match={level_match:.3f} edge_ratio={edge_ratio:.3f}"

    if len(in_edges) < max(12, ratio * 2) or len(out_edges) < 3:
        return False, "not enough clock edges"

    intervals: list[int] = []
    for idx in range(1, len(out_edges)):
        start_t = out_edges[idx - 1]
        end_t = out_edges[idx]
        in_count = sum(1 for t in in_edges if start_t < t <= end_t)
        intervals.append(in_count)

    if len(intervals) < 2:
        return False, "insufficient output periods"

    measured = intervals[1:] if len(intervals) > 2 else intervals
    mismatch = [n for n in measured if n != ratio]
    period_match = 1.0 - (len(mismatch) / len(measured))

    hist: dict[int, int] = {}
    for n in measured:
        hist[n] = hist.get(n, 0) + 1

    high_seen = any(v > 0.45 for v in out_vals)
    low_seen = any(v <= 0.45 for v in out_vals)

    ok = (len(mismatch) == 0) and final_lock_high and high_seen and low_seen
    return ok, f"ratio_code={ratio} in_edges={len(in_edges)} out_edges={len(out_edges)} lock_edges={len(lock_edges)} final_lock_high={final_lock_high} period_match={period_match:.3f} interval_hist={hist}"


def check_comparator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"vinp", "vinn", "out_p"}.issubset(rows[0]):
        return False, "missing vinp/vinn/out_p"
    before = [r["out_p"] for r in rows if r["time"] < 2e-9]
    after = [r["out_p"] for r in rows if r["time"] >= 2e-9]
    if not before or not after:
        return False, "insufficient time windows"
    delta = abs(sum(before) / len(before) - sum(after) / len(after))
    return (delta > 0.2), f"output_mean_delta={delta:.3f}"


def check_cmp_delay(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "vinp", "vinn", "out_p"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/vinp/vinn/out_p"

    phases = [
        (0.0e-9, 4.0e-9, 10e-3),
        (4.0e-9, 8.0e-9, 1e-3),
        (8.0e-9, 12.0e-9, 0.1e-3),
        (12.0e-9, 16.0e-9, 0.01e-3),
    ]
    threshold = 0.45
    clk_rise_offset = 0.1e-9
    times = [r["time"] for r in rows]
    out_p = [r["out_p"] for r in rows]

    delays_ns: list[float] = []
    missing_high: list[str] = []
    for start_t, end_t, diff_v in phases:
        phase_samples = [r["out_p"] for r in rows if start_t <= r["time"] < end_t]
        if not phase_samples or max(phase_samples) < threshold:
            missing_high.append(f"{diff_v * 1e3:.2g}mV")
            continue

        search_start = start_t + clk_rise_offset
        crossing_t = None
        for idx, t in enumerate(times):
            if t < search_start or t >= min(end_t, search_start + 3.0e-9):
                continue
            if out_p[idx] > threshold:
                crossing_t = t
                break
        if crossing_t is None:
            return False, f"missing_threshold_crossing diff={diff_v * 1e3:.2g}mV"
        delays_ns.append((crossing_t - search_start) * 1e9)

    if missing_high:
        return False, f"out_p_never_high phases={','.join(missing_high)}"
    if len(delays_ns) != len(phases):
        return False, f"insufficient_delay_measurements count={len(delays_ns)}"

    monotonic = all(delays_ns[i] <= delays_ns[i + 1] + 0.12 for i in range(len(delays_ns) - 1))
    ok = monotonic
    return ok, f"delays_ns={[round(v, 3) for v in delays_ns]} monotonic={monotonic}"


def check_cmp_strongarm(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "out_p", "out_n"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/out_p/out_n"

    threshold = 0.45
    out_p = [r["out_p"] for r in rows]
    out_n = [r["out_n"] for r in rows]
    t_ns = [r["time"] * 1e9 for r in rows]

    out_p_span = max(out_p) - min(out_p)
    out_n_span = max(out_n) - min(out_n)
    if out_p_span < threshold or out_n_span < threshold:
        return False, f"insufficient_toggle out_p_span={out_p_span:.3f} out_n_span={out_n_span:.3f}"

    pre = [out_p[idx] for idx, t in enumerate(t_ns) if 0.6 < t < 2.0]
    post = [out_p[idx] for idx, t in enumerate(t_ns) if 2.5 < t < 4.0]
    if not pre or not post:
        return False, "insufficient_polarity_windows"

    pre_high_frac = sum(1 for v in pre if v > threshold) / len(pre)
    post_low_frac = sum(1 for v in post if v < threshold) / len(post)
    ok = pre_high_frac >= 0.4 and post_low_frac >= 0.4
    return ok, f"pre_high_frac={pre_high_frac:.3f} post_low_frac={post_low_frac:.3f}"


def check_strongarm_reset_priority_bug(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "rst", "inp", "inn", "outp", "outn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/rst/inp/inn/outp/outn"

    threshold = 0.45
    reset_window = [r for r in rows if r["rst"] > threshold]
    active_window = [r for r in rows if r["time"] >= 24e-9 and r["rst"] < threshold]
    if not reset_window or not active_window:
        return False, "insufficient_reset_or_active_window"

    reset_outp_max = max(r["outp"] for r in reset_window)
    reset_outn_max = max(r["outn"] for r in reset_window)

    high_rows = [r for r in active_window if r["inp"] > r["inn"] + 5e-3]
    low_rows = [r for r in active_window if r["inp"] + 5e-3 < r["inn"]]
    if not high_rows or not low_rows:
        return False, "missing_post_reset_polarity_windows"

    high_outp = sum(1 for r in high_rows if r["outp"] > threshold) / len(high_rows)
    high_outn = sum(1 for r in high_rows if r["outn"] < threshold) / len(high_rows)
    low_outp = sum(1 for r in low_rows if r["outp"] < threshold) / len(low_rows)
    low_outn = sum(1 for r in low_rows if r["outn"] > threshold) / len(low_rows)

    ok = (
        reset_outp_max < 0.1
        and reset_outn_max < 0.1
        and high_outp > 0.75
        and high_outn > 0.75
        and low_outp > 0.75
        and low_outn > 0.75
    )
    return ok, (
        f"reset_outp_max={reset_outp_max:.3f} "
        f"reset_outn_max={reset_outn_max:.3f} "
        f"high_outp={high_outp:.3f} high_outn={high_outn:.3f} "
        f"low_outp={low_outp:.3f} low_outn={low_outn:.3f}"
    )


def check_cmp_hysteresis(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "out_p", "out_n"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/out_p/out_n"

    threshold = 0.45
    times_ns = [r["time"] * 1e9 for r in rows]
    out_p = [r["out_p"] for r in rows]
    out_n = [r["out_n"] for r in rows]

    if max(out_p) - min(out_p) < threshold or max(out_n) - min(out_n) < threshold:
        return False, "outputs_do_not_toggle"

    pre = [out_p[idx] for idx, t in enumerate(times_ns) if t < 20.0]
    mid = [out_p[idx] for idx, t in enumerate(times_ns) if 35.0 < t < 60.0]
    post = [out_p[idx] for idx, t in enumerate(times_ns) if t > 75.0]
    if not pre or not mid or not post:
        return False, "insufficient_hysteresis_windows"

    pre_low_frac = sum(1 for v in pre if v < threshold) / len(pre)
    mid_high_frac = sum(1 for v in mid if v > threshold) / len(mid)
    post_low_frac = sum(1 for v in post if v < threshold) / len(post)
    if pre_low_frac < 0.95 or mid_high_frac < 0.95 or post_low_frac < 0.95:
        return False, f"window_fracs pre={pre_low_frac:.3f} mid={mid_high_frac:.3f} post={post_low_frac:.3f}"

    rise_t = None
    fall_t = None
    for idx in range(1, len(out_p)):
        if rise_t is None and out_p[idx - 1] < threshold <= out_p[idx]:
            rise_t = times_ns[idx]
        if fall_t is None and out_p[idx - 1] > threshold >= out_p[idx]:
            fall_t = times_ns[idx]

    if rise_t is None or fall_t is None:
        return False, "missing_trip_crossings"
    if not (29.0 <= rise_t <= 31.5):
        return False, f"rise_t_out_of_range={rise_t:.3f}ns"
    if not (68.5 <= fall_t <= 71.5):
        return False, f"fall_t_out_of_range={fall_t:.3f}ns"
    return True, f"rise_t={rise_t:.3f}ns fall_t={fall_t:.3f}ns"


def check_ramp_gen(rows: list[dict[str, float]]) -> tuple[bool, str]:
    bit_names = [f"code_{i}" for i in range(12) if f"code_{i}" in rows[0]]
    if not bit_names:
        return False, "missing code_* bits"
    codes = decode_bus(rows, bit_names)
    nondecreasing = all(codes[i] <= codes[i + 1] for i in range(len(codes) - 1))
    return nondecreasing, f"code_start={codes[0]} code_end={codes[-1]}"


def check_d2b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty tran.csv"
    if all(k in rows[0] for k in ["bin_o_3", "bin_o_2", "bin_o_1", "bin_o_0"]):
        codes = decode_bus(rows, ["bin_o_0", "bin_o_1", "bin_o_2", "bin_o_3"])
        stable = len(set(codes)) == 1
        return stable and codes[0] == 9, f"stable_code={codes[0]}"
    dout_bits = [k for k in rows[0] if re.fullmatch(r"dout[_\[]?\d+\]?", k, flags=re.IGNORECASE)]
    vin_col = next((k for k in rows[0] if k.lower().startswith("vin")), None)
    if vin_col and dout_bits:
        codes = decode_bus(rows, dout_bits)
        vins = [r[vin_col] for r in rows]
        pairs = sorted(zip(vins, codes), key=lambda x: x[0])
        monotonic = all(pairs[i][1] <= pairs[i + 1][1] for i in range(len(pairs) - 1))
        return monotonic, "dynamic monotonic code check"
    return False, "missing d2b outputs"


def check_adc_dac_ideal_4b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"vin", "vout", "rst_n"}.issubset(rows[0]):
        return False, "missing vin/vout/rst_n"
    post = [r for r in rows if r["rst_n"] > 0.45]
    if not post:
        return False, "no post-reset samples"
    if "dout_code" in rows[0]:
        codes = [int(round(r["dout_code"])) for r in post]
    elif {"dout_3", "dout_2", "dout_1", "dout_0"}.issubset(rows[0]):
        codes = [
            ((1 if r["dout_3"] > 0.45 else 0) << 3)
            | ((1 if r["dout_2"] > 0.45 else 0) << 2)
            | ((1 if r["dout_1"] > 0.45 else 0) << 1)
            | (1 if r["dout_0"] > 0.45 else 0)
            for r in post
        ]
    else:
        return False, "missing dout_code or dout_3..0"
    vouts = [r["vout"] for r in post]
    vins = [r["vin"] for r in post]
    unique_codes = len(set(codes))
    monotonic = all(codes[i] <= codes[i + 1] for i in range(len(codes) - 1))
    span = max(vouts) - min(vouts)
    vin_span = max(vins) - min(vins)
    ok = unique_codes >= 12 and monotonic and span > 0.6 and vin_span > 0.6
    return ok, f"unique_codes={unique_codes} vout_span={span:.3f} vin_span={vin_span:.3f}"


def check_dac_binary_clk_4b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"din3", "din2", "din1", "din0", "aout"}.issubset(rows[0]):
        return False, "missing din*/aout"
    levels: dict[int, list[float]] = {}
    for r in rows:
        code = (
            (1 if r["din3"] > 0.45 else 0) * 8
            + (1 if r["din2"] > 0.45 else 0) * 4
            + (1 if r["din1"] > 0.45 else 0) * 2
            + (1 if r["din0"] > 0.45 else 0)
        )
        levels.setdefault(code, []).append(r["aout"])
    medians = {c: sum(vs) / len(vs) for c, vs in levels.items()}
    sorted_codes = sorted(medians)
    monotonic = all(medians[sorted_codes[i]] <= medians[sorted_codes[i + 1]] + 1e-9 for i in range(len(sorted_codes) - 1))
    span = medians[sorted_codes[-1]] - medians[sorted_codes[0]] if sorted_codes else 0.0
    ok = len(sorted_codes) >= 14 and monotonic and span > 0.7
    return ok, f"levels={len(sorted_codes)} aout_span={span:.3f}"


def check_dac_therm_16b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    bit_names = [f"d{i}" for i in range(16) if f"d{i}" in rows[0]]
    if not rows or not bit_names or "vout" not in rows[0]:
        return False, "missing d*/vout"
    ones_counts = [sum(1 for b in bit_names if r[b] > 0.45) for r in rows]
    vouts = [r["vout"] for r in rows]
    max_ones = max(ones_counts)
    max_vout = max(vouts)
    last_pairs: dict[int, float] = {}
    for ones, vout in zip(ones_counts, vouts):
        last_pairs[ones] = vout
    sorted_ones = sorted(last_pairs)
    monotonic = all(last_pairs[sorted_ones[i]] <= last_pairs[sorted_ones[i + 1]] + 1e-9 for i in range(len(sorted_ones) - 1))
    ok = max_ones == 16 and max_vout > 15.0 and monotonic
    return ok, f"max_ones={max_ones} max_vout={max_vout:.3f}"


def check_sar_adc_dac_weighted_8b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"vin", "vin_sh", "vout", "rst_n"}.issubset(rows[0]):
        return False, "missing vin/vin_sh/vout/rst_n"
    post = [r for r in rows if r["rst_n"] > 0.45]
    if not post:
        return False, "no post-reset samples"
    # Always decode from dout bits for consistent comparison across simulators
    # (EVAS has dout_code column, but Spectre does not - using bits ensures fairness)
    bit_names = [f"dout_{idx}" for idx in range(8) if f"dout_{idx}" in rows[0]]
    if len(bit_names) != 8:
        return False, "missing dout_0..7"
    codes = [
        sum((1 if r[name] > 0.45 else 0) << idx for idx, name in enumerate(bit_names))
        for r in post
    ]
    vinsh = [r["vin_sh"] for r in post]
    vouts = [r["vout"] for r in post]
    unique_codes = len(set(codes))
    avg_abs_err = sum(abs(a - b) for a, b in zip(vinsh, vouts)) / len(post)
    vout_span = max(vouts) - min(vouts)
    ok = (
        unique_codes >= 48
        and vout_span > 0.7
        and avg_abs_err < 0.08
    )
    return ok, f"unique_codes={unique_codes} avg_abs_err={avg_abs_err:.4f} vout_span={vout_span:.3f}"


def check_not_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"a", "y"}.issubset(rows[0]):
        return False, "missing a/y"
    # Down-sample to ≥500 ps spacing to avoid over-weighting EVAS transition sub-steps
    sampled: list[dict[str, float]] = []
    last_t = -1.0
    for r in rows:
        if r["time"] - last_t >= 5e-10:
            sampled.append(r)
            last_t = r["time"]
    check_rows = sampled if len(sampled) >= 10 else rows
    good = sum(1 for r in check_rows if (r["a"] > 0.4) != (r["y"] > 0.4))
    frac = good / len(check_rows)
    return frac > 0.9, f"invert_match_frac={frac:.3f}"


def check_and_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"a", "b", "y"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing a/b/y"
    check_rows = [r for r in rows if r["time"] >= rows[0]["time"] + 5e-10]
    if len(check_rows) < 10:
        check_rows = rows
    good = 0
    for r in check_rows:
        a_hi = r["a"] > 0.45
        b_hi = r["b"] > 0.45
        y_hi = r["y"] > 0.45
        if y_hi == (a_hi and b_hi):
            good += 1
    frac = good / len(check_rows)
    return frac > 0.92, f"and_truth_match_frac={frac:.3f}"


def check_or_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"a", "b", "y"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing a/b/y"
    check_rows = [r for r in rows if r["time"] >= rows[0]["time"] + 5e-10]
    if len(check_rows) < 10:
        check_rows = rows
    good = 0
    for r in check_rows:
        a_hi = r["a"] > 0.45
        b_hi = r["b"] > 0.45
        y_hi = r["y"] > 0.45
        if y_hi == (a_hi or b_hi):
            good += 1
    frac = good / len(check_rows)
    return frac > 0.92, f"or_truth_match_frac={frac:.3f}"


def check_dff_rst(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "d", "clk", "rst", "q", "qb"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/d/clk/rst/q/qb"
    clk_max = max(r["clk"] for r in rows)
    vth = 0.45 if clk_max < 0.9 else 0.5 * clk_max
    edges = [
        idx
        for idx in range(1, len(rows))
        if rows[idx - 1]["clk"] <= vth < rows[idx]["clk"]
    ]
    if len(edges) < 6:
        return False, f"too_few_clk_edges={len(edges)}"

    mismatches = 0
    qb_mismatches = 0
    checks = 0
    for idx in edges:
        edge_row = rows[idx]
        edge_time = edge_row["time"]
        settle = idx
        while settle + 1 < len(rows) and rows[settle]["time"] < edge_time + 100e-12:
            settle += 1
        r = rows[settle]
        expected_q_hi = False if edge_row["rst"] > vth else (edge_row["d"] > vth)
        q_hi = r["q"] > vth
        qb_hi = r["qb"] > vth
        checks += 1
        if q_hi != expected_q_hi:
            mismatches += 1
        if qb_hi == q_hi:
            qb_mismatches += 1
    ok = checks >= 6 and mismatches <= 1 and qb_mismatches <= 1
    return ok, f"checks={checks} q_mismatch={mismatches} qb_mismatch={qb_mismatches}"


def check_lfsr(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"dpn", "rstb"}.issubset(rows[0]):
        return False, "missing dpn/rstb"
    post = [r["dpn"] for r in rows if r["rstb"] > 0.45]
    if len(post) < 2:
        return False, "not enough post-reset samples"
    binary = [1 if v > 0.45 else 0 for v in post]
    hi_frac = sum(binary) / len(binary)
    transitions = sum(1 for i in range(len(binary) - 1) if binary[i] != binary[i + 1])
    ok = 0.05 < hi_frac < 0.95 and transitions >= 10
    return ok, f"transitions={transitions} hi_frac={hi_frac:.3f}"


def check_prbs7(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"clk", "rst_n", "en", "serial_out"} | {f"state_{i}" for i in range(7)}
    if not rows or not required.issubset(rows[0]):
        return False, "missing clk/rst_n/en/serial_out/state_*"

    post = [r for r in rows if r["rst_n"] > 0.45 and r["en"] > 0.45]
    if len(post) < 2:
        return False, "no post-reset enabled samples"

    def bit(row: dict[str, float], name: str) -> int:
        return 1 if row[name] > 0.45 else 0

    def state_code(row: dict[str, float]) -> int:
        code = 0
        for idx in range(7):
            code |= bit(row, f"state_{idx}") << idx
        return code

    serial = [bit(r, "serial_out") for r in post]
    states = [state_code(r) for r in post]

    if all(code == 0 for code in states):
        return False, "state stuck at zero"

    serial_transitions = sum(1 for i in range(len(serial) - 1) if serial[i] != serial[i + 1])
    unique_states = len(set(states))
    state_transitions = sum(1 for i in range(len(states) - 1) if states[i] != states[i + 1])

    ok = serial_transitions >= 10 and unique_states >= 8 and state_transitions >= 8
    return ok, f"serial_transitions={serial_transitions} unique_states={unique_states} state_transitions={state_transitions}"


def check_therm2bin(rows: list[dict[str, float]]) -> tuple[bool, str]:
    therm_bits = [f"therm_{i}" for i in range(15)]
    bin_bits = [f"bin_{i}" for i in range(4)]
    required = set(therm_bits + bin_bits)
    if not rows or not required.issubset(rows[0]):
        return False, "missing therm_* or bin_* signals"

    def bit(row: dict[str, float], name: str) -> int:
        return 1 if row[name] > 0.45 else 0

    def thermometer_count(row: dict[str, float]) -> int:
        return sum(bit(row, name) for name in therm_bits)

    def binary_code(row: dict[str, float]) -> int:
        return sum(bit(row, f"bin_{idx}") << idx for idx in range(4))

    counts = [thermometer_count(row) for row in rows]
    codes = [binary_code(row) for row in rows]

    if not counts:
        return False, "empty therm2bin dataset"

    def far_from_threshold(v: float, lo: float = 0.35, hi: float = 0.55) -> bool:
        return v <= lo or v >= hi

    stable_indices = []
    for idx in range(1, len(rows)):
        if counts[idx] != counts[idx - 1]:
            continue
        therm_stable = all(
            far_from_threshold(rows[idx][name]) and far_from_threshold(rows[idx - 1][name])
            for name in therm_bits
        )
        bin_stable = all(
            far_from_threshold(rows[idx][name])
            for name in bin_bits
        )
        if therm_stable and bin_stable:
            stable_indices.append(idx)

    min_stable_points = max(10, len(rows) // 20)
    if len(stable_indices) < min_stable_points:
        return False, f"insufficient_strict_stable_points={len(stable_indices)}"

    mismatches = [idx for idx in stable_indices if codes[idx] != min(counts[idx], 15)]
    stable_ok = len(mismatches) == 0
    distinct_counts = len(set(counts))
    bubble_present = any(
        counts[i] > counts[i + 1]
        for i in range(len(counts) - 1)
    )
    ok = stable_ok and distinct_counts >= 6 and bubble_present
    return ok, f"distinct_counts={distinct_counts} bubble_present={bubble_present} strict_stable_points={len(stable_indices)} strict_mismatches={len(mismatches)}"


def check_multimod_divider(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"clk_in", "mod", "prescaler_out", "mod_0", "mod_1", "mod_2", "mod_3"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing clk_in/mod/prescaler_out/mod_*"

    times = [r["time"] for r in rows]
    clk_edges = [i for i in range(1, len(rows)) if rows[i - 1]["clk_in"] < 0.45 <= rows[i]["clk_in"]]
    out_edges = [i for i in range(1, len(rows)) if rows[i - 1]["prescaler_out"] < 0.45 <= rows[i]["prescaler_out"]]
    clk_edge_times = [times[idx] for idx in clk_edges]

    if len(clk_edges) < 8 or len(out_edges) < 4:
        return False, "not enough clock or output edges"

    base = sum((1 if rows[0][f"mod_{idx}"] > 0.45 else 0) << idx for idx in range(4))
    if base < 1:
        base = 1

    switch_time = None
    for idx in range(1, len(rows)):
        if rows[idx - 1]["mod"] < 0.45 <= rows[idx]["mod"]:
            switch_time = times[idx]
            break

    if switch_time is None:
        return False, "no MOD transition found"

    intervals = []
    for idx in range(1, len(out_edges)):
        start_idx = out_edges[idx - 1]
        end_idx = out_edges[idx]
        start_t = times[start_idx]
        end_t = times[end_idx]
        interval_len = sum(1 for clk_t in clk_edge_times if start_t < clk_t <= end_t)
        intervals.append((start_t, end_t, interval_len))

    pre = [interval for start_t, end_t, interval in intervals if end_t < switch_time]
    post = [interval for start_t, end_t, interval in intervals if start_t >= switch_time]

    pre_ok = len(pre) >= 2 and all(interval == base for interval in pre)
    post_ok = len(post) >= 2 and all(interval == base + 1 for interval in post)
    ok = pre_ok and post_ok
    return ok, f"base={base} pre_count={len(pre)} post_count={len(post)} switch_time_ns={switch_time * 1e9:.3f}"


def check_multimod_divider_ratio_switch(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk_in", "div_out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk_in/div_out"

    times = [r["time"] for r in rows]
    in_edges = rising_edges([r["clk_in"] for r in rows], times)
    out_edges = rising_edges([r["div_out"] for r in rows], times)
    if len(in_edges) < 40 or len(out_edges) < 10:
        return False, f"not_enough_edges in={len(in_edges)} out={len(out_edges)}"

    windows = [
        (10e-9, 90e-9, 4, "pre_div4"),
        (120e-9, 190e-9, 5, "mid_div5"),
        (220e-9, 300e-9, 4, "post_div4"),
    ]
    details: list[str] = []
    for t0, t1, expected_ratio, label in windows:
        win_in = [t for t in in_edges if t0 <= t <= t1]
        win_out = [t for t in out_edges if t0 <= t <= t1]
        if len(win_in) < expected_ratio * 2 or len(win_out) < 2:
            return False, f"{label}_insufficient_edges in={len(win_in)} out={len(win_out)}"
        measured_ratio = len(win_in) / max(len(win_out), 1)
        details.append(f"{label}={measured_ratio:.2f}")
        if abs(measured_ratio - expected_ratio) > 0.35:
            return False, ";".join(details)
    return True, ";".join(details)


def check_bbpd(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"data", "clk", "retimed_data", "up", "down"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing data/clk/retimed_data/up/down"

    data_edges = [i for i in range(1, len(rows)) if rows[i - 1]["data"] < 0.45 <= rows[i]["data"] or rows[i - 1]["data"] > 0.45 >= rows[i]["data"]]
    up_edges = [i for i in range(1, len(rows)) if rows[i - 1]["up"] < 0.45 <= rows[i]["up"]]
    down_edges = [i for i in range(1, len(rows)) if rows[i - 1]["down"] < 0.45 <= rows[i]["down"]]

    if len(data_edges) < 6:
        return False, "not enough data edges"

    overlap = sum(1 for r in rows if r["up"] > 0.45 and r["down"] > 0.45)
    overlap_frac = overlap / max(len(rows), 1)

    edge_trigger_ok = len(up_edges) + len(down_edges) >= max(4, len(data_edges) // 4)
    pulse_presence_ok = len(up_edges) >= 2 and len(down_edges) >= 2
    non_overlap_ok = overlap_frac < 0.02
    ok = edge_trigger_ok and pulse_presence_ok and non_overlap_ok
    return ok, f"data_edges={len(data_edges)} up_edges={len(up_edges)} down_edges={len(down_edges)} overlap_frac={overlap_frac:.4f}"


def check_bbpd_data_edge_alignment(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"clk", "data", "up", "dn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing clk/data/up/dn"

    vth = 0.45
    times = [r["time"] for r in rows]
    up = [r["up"] for r in rows]
    dn = [r["dn"] for r in rows]
    data = [r["data"] for r in rows]

    up_edges = [times[i] for i in range(1, len(rows)) if up[i - 1] <= vth < up[i]]
    dn_edges = [times[i] for i in range(1, len(rows)) if dn[i - 1] <= vth < dn[i]]
    data_edges = [
        times[i]
        for i in range(1, len(rows))
        if ((data[i - 1] <= vth < data[i]) or (data[i - 1] >= vth > data[i]))
    ]

    if len(data_edges) < 6:
        return False, f"too_few_data_edges={len(data_edges)}"
    if len(up_edges) + len(dn_edges) < 6:
        return False, f"too_few_updn_pulses={len(up_edges) + len(dn_edges)}"

    overlap = sum(1 for r in rows if r["up"] > vth and r["dn"] > vth)
    overlap_frac = overlap / max(len(rows), 1)
    if overlap_frac > 0.02:
        return False, f"overlap_frac={overlap_frac:.4f}"

    lead_window_end = 80e-9
    lag_window_start = 90e-9
    up_lead = sum(1 for t in up_edges if t <= lead_window_end)
    dn_lead = sum(1 for t in dn_edges if t <= lead_window_end)
    up_lag = sum(1 for t in up_edges if t >= lag_window_start)
    dn_lag = sum(1 for t in dn_edges if t >= lag_window_start)

    if up_lead < 3 or up_lead <= dn_lead:
        return False, f"lead_window_updn={up_lead}/{dn_lead}"
    if dn_lag < 3 or dn_lag <= up_lag:
        return False, f"lag_window_updn={up_lag}/{dn_lag}"

    return True, (
        f"data_edges={len(data_edges)} "
        f"lead_updn={up_lead}/{dn_lead} "
        f"lag_updn={up_lag}/{dn_lag} "
        f"overlap_frac={overlap_frac:.4f}"
    )


def _find_bus_columns(sample: dict[str, float], base: str) -> dict[int, str]:
    cols: dict[int, str] = {}
    pattern = re.compile(rf"^{re.escape(base)}(?:_|\[)?(\d+)\]?$", re.IGNORECASE)
    for name in sample:
        m = pattern.match(name)
        if m:
            cols[int(m.group(1))] = name
    return cols


def _pick_column(sample: dict[str, float], candidates: list[str]) -> str | None:
    lower_map = {k.lower(): k for k in sample.keys()}
    for name in candidates:
        if name in sample:
            return name
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    return None


def check_bad_bus_output_loop(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty tran.csv"

    sample = rows[0]
    code_cols = _find_bus_columns(sample, "CODE")
    dout_cols = _find_bus_columns(sample, "DOUT")
    bit_indices = [idx for idx in range(4) if idx in code_cols and idx in dout_cols]

    if len(bit_indices) != 4:
        return False, "missing CODE_*/DOUT_* bit columns"

    mismatch = 0
    total = 0
    code_patterns = set()
    dout_patterns = set()
    uniform_rows = 0
    stable_rows = 0
    prev_code_tuple = None
    settle_until = float("-inf")
    settle_s = 0.1e-9

    for row in rows:
        code_vec = []
        dout_vec = []
        for idx in bit_indices:
            code_bit = 1 if row[code_cols[idx]] > 0.45 else 0
            dout_bit = 1 if row[dout_cols[idx]] > 0.45 else 0
            code_vec.append(code_bit)
            dout_vec.append(dout_bit)
        code_tuple = tuple(code_vec)
        dout_tuple = tuple(dout_vec)
        t = row.get("time", 0.0)
        if prev_code_tuple is not None and code_tuple != prev_code_tuple:
            settle_until = max(settle_until, t + settle_s)
        prev_code_tuple = code_tuple

        code_patterns.add(code_tuple)
        dout_patterns.add(dout_tuple)
        if len(set(dout_tuple)) == 1:
            uniform_rows += 1
        if t <= settle_until:
            continue
        stable_rows += 1
        for code_bit, dout_bit in zip(code_tuple, dout_tuple):
            total += 1
            if code_bit != dout_bit:
                mismatch += 1

    mismatch_frac = mismatch / max(total, 1)
    uniform_frac = uniform_rows / max(len(rows), 1)
    ok = (
        mismatch_frac < 0.05
        and len(code_patterns) >= 6
        and len(dout_patterns) >= 6
        and uniform_frac < 0.8
        and stable_rows >= 20
    )
    return ok, (
        f"mismatch_frac={mismatch_frac:.4f} code_patterns={len(code_patterns)} "
        f"dout_patterns={len(dout_patterns)} uniform_frac={uniform_frac:.3f} "
        f"stable_rows={stable_rows}"
    )


def check_missing_transition_outputs(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty tran.csv"

    sample = rows[0]
    vin_col = _pick_column(sample, ["VIN", "vin", "vin_i"])
    flag_col = _pick_column(sample, ["FLAG", "flag", "flag_o", "out_p", "out"])
    if vin_col is None or flag_col is None:
        return False, "missing VIN/FLAG columns"

    vins = [r[vin_col] for r in rows]
    flags = [r[flag_col] for r in rows]
    vmin = min(vins)
    vmax = max(vins)
    if vmax - vmin < 0.2:
        return False, "VIN does not cross threshold range"

    threshold = 0.5 * (vmax + vmin)
    margin = max(0.05 * (vmax - vmin), 0.03)
    crossing_times = [
        rows[i]["time"]
        for i in range(1, len(rows))
        if (vins[i - 1] - threshold) * (vins[i] - threshold) <= 0 and vins[i - 1] != vins[i]
    ]
    settle_s = 0.5e-9
    stable_indices = [
        i
        for i, vin in enumerate(vins)
        if abs(vin - threshold) > margin
        and all(abs(rows[i]["time"] - t_cross) > settle_s for t_cross in crossing_times)
    ]
    if len(stable_indices) < max(10, len(rows) // 4):
        return False, "insufficient stable samples away from threshold"

    mismatch = 0
    for idx in stable_indices:
        expected = vins[idx] > threshold
        observed = flags[idx] > 0.45
        if expected != observed:
            mismatch += 1

    mismatch_frac = mismatch / len(stable_indices)
    flag_span = max(flags) - min(flags)
    high_seen = any(flags[idx] > 0.45 for idx in stable_indices)
    low_seen = any(flags[idx] <= 0.45 for idx in stable_indices)
    ok = mismatch_frac < 0.08 and flag_span > 0.4 and high_seen and low_seen
    return ok, f"mismatch_frac={mismatch_frac:.4f} flag_span={flag_span:.3f} stable_samples={len(stable_indices)}"


def check_dwa_ptr_gen(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "no rows"
    keys = set(rows[0].keys())
    # Accept either bus-integer format (ptr_code/cell_en_code) or individual bits (ptr_0..ptr_15)
    use_codes = {"clk_i", "rst_ni", "cell_en_code", "ptr_code"}.issubset(keys)
    use_bits  = {"clk_i", "rst_ni", "ptr_0", "cell_en_0"}.issubset(keys)
    if not use_codes and not use_bits:
        return False, "missing required columns (need ptr_code/cell_en_code or ptr_0..15/cell_en_0..15)"
    post = [r for r in rows if r["rst_ni"] > 0.45]
    if not post:
        return False, "no post-reset samples"
    if use_codes:
        ptr_codes  = [int(round(r["ptr_code"])) for r in post]
        cell_codes = [int(round(r["cell_en_code"])) for r in post]
    else:
        # Reconstruct integer codes from individual bit columns
        ptr_bits  = [k for k in keys if k.startswith("ptr_") and k[4:].isdigit()]
        cell_bits = [k for k in keys if k.startswith("cell_en_") and k[8:].isdigit()]
        ptr_codes  = [sum(int(r[b] > 0.45) << int(b[4:])  for b in ptr_bits)  for r in post]
        cell_codes = [sum(int(r[b] > 0.45) << int(b[8:]) for b in cell_bits) for r in post]
    ptr_nonzero = all(v > 0 for v in ptr_codes)
    ptr_unique = len(set(ptr_codes))
    cell_active = max(cell_codes) > 0
    ok = ptr_nonzero and cell_active and ptr_unique >= 4
    return ok, f"ptr_unique={ptr_unique} max_cell_code={max(cell_codes)}"


def check_dwa_ptr_gen_no_overlap(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "no rows"

    keys = set(rows[0].keys())
    required = {"time", "clk_i", "rst_ni", "ptr_0", "cell_en_0"}
    if not required.issubset(keys):
        return False, "missing time/clk_i/rst_ni/ptr_0/cell_en_0"

    ptr_cols = indexed_columns(keys, "ptr_")
    cell_cols = indexed_columns(keys, "cell_en_")
    if not ptr_cols or not cell_cols:
        return False, "missing ptr_* or cell_en_* columns"

    times = [r["time"] for r in rows]
    clk_vals = [r["clk_i"] for r in rows]
    rst_vals = [r["rst_ni"] for r in rows]
    edge_times = rising_edges(clk_vals, times)
    if not edge_times:
        return False, "no_clock_edges"

    sample_times = [edge_t + 1.0e-9 for edge_t in edge_times]
    sampled_rows = sample_rows_at_or_after_times(rows, sample_times, rst_key="rst_ni")

    if len(sampled_rows) < 2:
        return False, f"insufficient_post_reset_samples count={len(sampled_rows)}"

    bad_ptr_rows = 0
    cell_counts: list[int] = []
    overlap_count = 0
    prev_active: set[int] | None = None

    for row in sampled_rows:
        ptr_active = {idx for idx, col in enumerate(ptr_cols) if row[col] > 0.45}
        if len(ptr_active) not in (0, 1):
            bad_ptr_rows += 1

        active_cells = {idx for idx, col in enumerate(cell_cols) if row[col] > 0.45}
        cell_counts.append(len(active_cells))

        if prev_active is not None and prev_active & active_cells:
            overlap_count += 1
        prev_active = active_cells

    cell_active = max(cell_counts) > 0
    ok = bad_ptr_rows == 0 and cell_active and overlap_count == 0
    return ok, (
        f"sampled_cycles={len(sampled_rows)} bad_ptr_rows={bad_ptr_rows} "
        f"max_active_cells={max(cell_counts)} overlap_count={overlap_count}"
    )


def check_dwa_wraparound(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "no rows"

    keys = set(rows[0].keys())
    required = {"time", "clk_i", "rst_ni", "ptr_0", "cell_en_0", "code_0"}
    if not required.issubset(keys):
        return False, "missing time/clk_i/rst_ni/ptr_0/cell_en_0/code_0"

    ptr_cols = indexed_columns(keys, "ptr_")
    cell_cols = indexed_columns(keys, "cell_en_")
    code_cols = indexed_columns(keys, "code_")
    if len(ptr_cols) != 16 or len(cell_cols) != 16 or len(code_cols) != 4:
        return False, "expected ptr_0..15, cell_en_0..15, and code_0..3 columns"

    times = [r["time"] for r in rows]
    edge_times = rising_edges([r["clk_i"] for r in rows], times)
    sample_times = [edge_t + 1.0e-9 for edge_t in edge_times]
    sampled_rows = sample_rows_at_or_after_times(rows, sample_times, rst_key="rst_ni")

    if len(sampled_rows) < 5:
        return False, f"insufficient_post_reset_samples count={len(sampled_rows)}"

    expected_ptr = 13
    bad_ptr_rows = 0
    bad_count_rows = 0
    wrap_events = 0
    split_wrap_rows = 0
    prev_ptr = expected_ptr

    for row in sampled_rows:
        code = sum(int(row[col] > 0.45) << int(col[5:]) for col in code_cols)
        expected_ptr = (expected_ptr + code) % 16
        if expected_ptr < prev_ptr:
            wrap_events += 1

        ptr_active = [idx for idx, col in enumerate(ptr_cols) if row[col] > 0.45]
        active_cells = {idx for idx, col in enumerate(cell_cols) if row[col] > 0.45}

        if ptr_active != [expected_ptr]:
            bad_ptr_rows += 1
        if len(active_cells) != code:
            bad_count_rows += 1
        if active_cells and (max(active_cells) - min(active_cells) + 1) > len(active_cells):
            split_wrap_rows += 1

        prev_ptr = expected_ptr

    ok = bad_ptr_rows == 0 and bad_count_rows == 0 and wrap_events >= 2 and split_wrap_rows >= 2
    return ok, (
        f"sampled_cycles={len(sampled_rows)} bad_ptr_rows={bad_ptr_rows} "
        f"bad_count_rows={bad_count_rows} wrap_events={wrap_events} "
        f"split_wrap_rows={split_wrap_rows}"
    )


def check_clk_burst_gen(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"CLK", "RST_N", "CLK_OUT"}.issubset(rows[0]):
        return False, "missing CLK/RST_N/CLK_OUT"
    post = [r for r in rows if r["RST_N"] > 0.45]
    if not post:
        return False, "no post-reset samples"
    clk_out = [r["CLK_OUT"] for r in post]
    times = [r["time"] for r in post]
    hi_frac = sum(1 for v in clk_out if v > 0.45) / len(clk_out)
    edges = rising_edges(clk_out, times)
    ok = 0.05 < hi_frac < 0.4 and len(edges) >= 4
    return ok, f"clk_out_hi_frac={hi_frac:.3f} rising_edges={len(edges)}"


def check_noise_gen(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"vin_i", "vout_o"}.issubset(rows[0]):
        return False, "missing vin_i/vout_o"
    noises = [r["vout_o"] - r["vin_i"] for r in rows]
    mean = sum(noises) / len(noises)
    var = sum((x - mean) ** 2 for x in noises) / len(noises)
    std = var ** 0.5
    ok = std > 0.01 and max(abs(x) for x in noises) > 0.05
    return ok, f"noise_std={std:.4f}"


def check_gain_extraction(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"vinp", "vinn", "vamp_p", "vamp_n"}.issubset(rows[0]):
        return False, "missing vinp/vinn/vamp_p/vamp_n"
    vin_diff = [r["vinp"] - r["vinn"] for r in rows]
    vamp_diff = [r["vamp_p"] - r["vamp_n"] for r in rows]
    mean_in = sum(vin_diff) / len(vin_diff)
    mean_out = sum(vamp_diff) / len(vamp_diff)
    std_in = (sum((x - mean_in) ** 2 for x in vin_diff) / len(vin_diff)) ** 0.5
    std_out = (sum((x - mean_out) ** 2 for x in vamp_diff) / len(vamp_diff)) ** 0.5
    gain = std_out / std_in if std_in > 1e-12 else 0.0
    ok = gain > 4.0 and std_out > std_in
    return ok, f"diff_gain={gain:.2f}"


def check_adpll_lock(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"ref_clk", "fb_clk", "lock", "vctrl_mon"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing ref_clk/fb_clk/lock/vctrl_mon"

    times = [r["time"] for r in rows]
    ref_edges = rising_edges([r["ref_clk"] for r in rows], times)
    fb_edges = rising_edges([r["fb_clk"] for r in rows], times)
    lock_edges = rising_edges([r["lock"] for r in rows], times)

    if len(ref_edges) < 8 or len(fb_edges) < 8:
        return False, f"not_enough_edges ref={len(ref_edges)} fb={len(fb_edges)}"

    t_end = times[-1]
    t_start = t_end * 0.8
    ref_late = [t for t in ref_edges if t_start <= t <= t_end]
    fb_late = [t for t in fb_edges if t_start <= t <= t_end]
    if not ref_late or not fb_late:
        return False, "missing late-window edges"

    ratio = len(fb_late) / max(len(ref_late), 1)
    lock_ok = bool(lock_edges) and lock_edges[0] <= 1.0e-6
    vctrl_vals = [r["vctrl_mon"] for r in rows]
    vctrl_in_range = all(-1e-6 <= v <= 1.2 for v in vctrl_vals)
    freq_ok = 0.95 <= ratio <= 1.05
    ok = freq_ok and lock_ok and vctrl_in_range
    return ok, (
        f"late_edge_ratio={ratio:.3f} "
        f"lock_time={(lock_edges[0] if lock_edges else float('nan')):.3e} "
        f"vctrl_range_ok={vctrl_in_range}"
    )


def edge_frequency_ratio(
    rows: list[dict[str, float]],
    num_signal: str,
    den_signal: str,
    t_start: float,
    t_end: float,
) -> tuple[float, str]:
    window = time_window(rows, t_start, t_end)
    if len(window) < 4 or num_signal not in window[0] or den_signal not in window[0]:
        return float("nan"), "missing_window_or_signals"

    times = [r["time"] for r in window]
    num_edges = rising_edges([r[num_signal] for r in window], times)
    den_edges = rising_edges([r[den_signal] for r in window], times)
    if len(num_edges) < 3 or len(den_edges) < 3:
        return float("nan"), f"not_enough_edges num={len(num_edges)} den={len(den_edges)}"

    num_freq = (len(num_edges) - 1) / max(num_edges[-1] - num_edges[0], 1e-18)
    den_freq = (len(den_edges) - 1) / max(den_edges[-1] - den_edges[0], 1e-18)
    return num_freq / max(den_freq, 1e-18), "ok"


def first_threshold_crossing(rows: list[dict[str, float]], signal: str, threshold: float) -> float:
    if not rows or signal not in rows[0]:
        return float("nan")
    prev = rows[0][signal]
    for row in rows[1:]:
        cur = row[signal]
        if prev < threshold <= cur:
            return row["time"]
        prev = cur
    return float("nan")


def check_adpll_ratio_hop(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"ref_clk", "vout", "lock", "vctrl_mon", "ratio_ctrl"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing ref_clk/vout/lock/vctrl_mon/ratio_ctrl"

    hop_t = first_threshold_crossing(rows, "ratio_ctrl", 5.0)
    if not math.isfinite(hop_t):
        return False, "ratio_hop_not_detected"

    pre_ratio, pre_note = edge_frequency_ratio(rows, "vout", "ref_clk", hop_t - 1.0e-6, hop_t - 2.0e-7)
    post_ratio, post_note = edge_frequency_ratio(rows, "vout", "ref_clk", hop_t + 1.2e-6, hop_t + 2.5e-6)
    if pre_note != "ok":
        return False, f"pre_window_{pre_note}"
    if post_note != "ok":
        return False, f"post_window_{post_note}"

    vth = max(r["lock"] for r in rows) * 0.5 if rows else 0.45
    pre_lock = weighted_logic_high_fraction_window(rows, "lock", vth, hop_t - 4.0e-7, hop_t - 5.0e-8)
    post_lock = weighted_logic_high_fraction_window(rows, "lock", vth, hop_t + 1.8e-6, hop_t + 2.8e-6)
    vctrl_vals = [r["vctrl_mon"] for r in rows]
    vctrl_in_range = all(-1e-6 <= v <= 1.2 for v in vctrl_vals)

    ok = (
        abs(pre_ratio - 4.0) <= 0.25
        and abs(post_ratio - 6.0) <= 0.35
        and pre_lock >= 0.8
        and post_lock >= 0.8
        and vctrl_in_range
    )
    return ok, (
        f"hop_t={hop_t:.3e} "
        f"pre_ratio={pre_ratio:.3f} "
        f"post_ratio={post_ratio:.3f} "
        f"pre_lock={pre_lock:.3f} "
        f"post_lock={post_lock:.3f} "
        f"vctrl_range_ok={vctrl_in_range}"
    )


def check_cppll_tracking(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"ref_clk", "fb_clk", "lock", "vctrl_mon"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing ref_clk/fb_clk/lock/vctrl_mon"

    times = [r["time"] for r in rows]
    ref_edges = rising_edges([r["ref_clk"] for r in rows], times)
    fb_edges = rising_edges([r["fb_clk"] for r in rows], times)
    lock_edges = rising_edges([r["lock"] for r in rows], times)

    if len(ref_edges) < 8 or len(fb_edges) < 8:
        return False, f"not_enough_edges ref={len(ref_edges)} fb={len(fb_edges)}"

    t_end = times[-1]
    t_start = t_end * 0.8
    ref_late = [t for t in ref_edges if t_start <= t <= t_end]
    fb_late = [t for t in fb_edges if t_start <= t <= t_end]
    if len(ref_late) < 4 or len(fb_late) < 4:
        return False, "not_enough_late_edges"

    ref_periods = [b - a for a, b in zip(ref_late, ref_late[1:])]
    fb_periods = [b - a for a, b in zip(fb_late, fb_late[1:])]
    ref_period = sum(ref_periods) / len(ref_periods)
    fb_period = sum(fb_periods) / len(fb_periods)
    if ref_period <= 0.0 or fb_period <= 0.0:
        return False, "non_positive_period"

    freq_ratio = ref_period / fb_period
    fb_jitter = max(fb_periods) - min(fb_periods)
    fb_jitter_frac = fb_jitter / fb_period if fb_period > 0.0 else float("inf")
    vctrl_vals = [r["vctrl_mon"] for r in rows]
    vctrl_min = min(vctrl_vals)
    vctrl_max = max(vctrl_vals)
    vctrl_in_range = all(-1e-6 <= v <= 0.95 for v in vctrl_vals)
    freq_ok = 0.97 <= freq_ratio <= 1.03
    stability_ok = fb_jitter_frac <= 0.10
    ok = freq_ok and stability_ok and vctrl_in_range
    return ok, (
        f"freq_ratio={freq_ratio:.4f} "
        f"fb_jitter_frac={fb_jitter_frac:.4f} "
        f"lock_time={(lock_edges[0] if lock_edges else float('nan')):.3e} "
        f"vctrl_min={vctrl_min:.3f} "
        f"vctrl_max={vctrl_max:.3f}"
    )


def check_sample_hold(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """S&H: output steps at clock edges, held between them."""
    if not rows or not {"in", "clk", "out"}.issubset(rows[0]):
        return False, "missing in/clk/out columns"
    vth = 0.45
    times = [r["time"] for r in rows]
    clk  = [r["clk"]  for r in rows]
    vin  = [r["in"]   for r in rows]
    vout = [r["out"]  for r in rows]
    edge_idx = [i for i in range(1, len(clk)) if clk[i - 1] <= vth < clk[i]]
    if len(edge_idx) < 10:
        return False, f"too_few_clock_edges={len(edge_idx)}"
    # Check hold stability: for 3 consecutive hold windows, skip 2ns after edge, stop 2ns before next
    for i in range(min(3, len(edge_idx) - 1)):
        t_start = times[edge_idx[i]] + 2e-9
        t_end   = times[edge_idx[i + 1]] - 2e-9
        window = [vout[j] for j in range(edge_idx[i], edge_idx[i + 1])
                  if t_start <= times[j] <= t_end]
        if len(window) < 2:
            continue
        jitter = max(window) - min(window)
        if jitter > 0.02:
            return False, f"output_not_held jitter={jitter:.4f}V"
    # Output should track input at edges (settled 2ns after edge)
    mismatches = 0
    for idx in edge_idx[:20]:
        t_settle = times[idx] + 2e-9
        settle_idx = next((j for j in range(idx, len(times)) if times[j] >= t_settle), idx)
        if abs(vout[settle_idx] - vin[idx]) > 0.015:
            mismatches += 1
    if mismatches > 4:
        return False, f"sample_mismatch={mismatches}/20"
    return True, f"edges={len(edge_idx)} hold_ok"


def check_sample_hold_droop(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"vin", "clk", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing vin/clk/vout"

    vth = 0.45
    times = [r["time"] for r in rows]
    clk = [r["clk"] for r in rows]
    vin = [r["vin"] for r in rows]
    vout = [r["vout"] for r in rows]
    edge_idx = [i for i in range(1, len(clk)) if clk[i - 1] <= vth < clk[i]]

    if len(edge_idx) < 6:
        return False, f"too_few_clock_edges={len(edge_idx)}"

    sample_mismatch = 0
    checked_samples = 0
    for i in range(min(6, len(edge_idx) - 1)):
        idx = edge_idx[i]
        t_target = times[idx] + 1.2e-9
        settle_idx = next((j for j in range(idx, len(rows)) if times[j] >= t_target), len(rows) - 1)
        err = abs(vout[settle_idx] - vin[idx])
        checked_samples += 1
        if err > 0.04:
            sample_mismatch += 1
    if checked_samples == 0 or sample_mismatch > 1:
        return False, f"sample_mismatch={sample_mismatch}/{max(checked_samples, 1)}"

    droop_windows = 0
    droop_failures = 0
    for i in range(min(6, len(edge_idx) - 1)):
        start_i = edge_idx[i]
        end_i = edge_idx[i + 1]
        t_start = times[start_i] + 1.5e-9
        t_end = times[end_i] - 1.5e-9
        idxs = [j for j in range(start_i, end_i) if t_start <= times[j] <= t_end]
        if len(idxs) < 6:
            continue
        first = vout[idxs[0]]
        if first < 0.55:
            continue
        last = vout[idxs[-1]]
        droop = first - last
        upward_steps = sum(1 for a, b in zip(idxs[:-1], idxs[1:]) if (vout[b] - vout[a]) > 0.004)
        droop_windows += 1
        if droop < 0.006 or droop > 0.30:
            droop_failures += 1
        if upward_steps > max(1, len(idxs) // 8):
            droop_failures += 1

    if droop_windows < 2:
        return False, f"insufficient_high_hold_windows={droop_windows}"
    if droop_failures > 0:
        return False, f"droop_failures={droop_failures} windows={droop_windows}"

    return True, (
        f"edges={len(edge_idx)} "
        f"sample_mismatch={sample_mismatch}/{checked_samples} "
        f"droop_windows={droop_windows}"
    )


def check_flash_adc_3b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """3-bit flash ADC: all 8 codes present, monotonic with ramp input."""
    if not rows or not {"vin", "clk", "dout2", "dout1", "dout0"}.issubset(rows[0]):
        return False, "missing vin/clk/dout2/dout1/dout0"
    vth = 0.45
    clk = [r["clk"] for r in rows]
    edge_idx = [i for i in range(1, len(clk)) if clk[i - 1] <= vth < clk[i]]
    if len(edge_idx) < 20:
        return False, f"too_few_edges={len(edge_idx)}"
    codes = []
    for idx in edge_idx:
        settle = min(idx + 5, len(rows) - 1)
        c = (int(rows[settle]["dout2"] > vth) << 2 |
             int(rows[settle]["dout1"] > vth) << 1 |
             int(rows[settle]["dout0"] > vth))
        codes.append(c)
    unique = set(codes)
    if len(unique) < 8:
        return False, f"only_{len(unique)}_codes (need 8)"
    # monotonicity: fewer than 5% reversals
    reversals = sum(1 for i in range(1, len(codes)) if codes[i] < codes[i - 1] - 1)
    if reversals > len(codes) * 0.05:
        return False, f"not_monotonic reversals={reversals}"
    return True, f"codes={len(unique)}/8 reversals={reversals}"


def check_serializer_8b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """8-bit P2S: verify 0xA5 bit sequence MSB-first after LOAD."""
    if not rows or not {"load", "clk", "sout"}.issubset(rows[0]):
        return False, "missing load/clk/sout"
    vth = 0.45
    load = [r["load"] for r in rows]
    clk  = [r["clk"]  for r in rows]
    sout = [r["sout"] for r in rows]
    times = [r["time"] for r in rows]

    # find LOAD falling edge
    load_fall = next((i for i in range(1, len(load)) if load[i - 1] > vth > load[i]), None)
    if load_fall is None:
        return False, "LOAD never deasserted"
    expected = [1, 0, 1, 0, 0, 1, 0, 1]  # 0xA5 MSB-first
    load_fall_t = times[load_fall]

    # collect CLK rising edges strictly after LOAD falls
    edges = [
        i for i in range(max(1, load_fall), len(clk))
        if clk[i - 1] <= vth < clk[i] and times[i] > load_fall_t + 1e-15
    ]
    if len(edges) < 7:
        return False, f"only_{len(edges)}_edges_after_load"

    # Sample sout at the middle of the next CLK period (wait for transition to settle)
    # transition() with tedge=100p takes ~100ps to complete, so we need to wait longer
    # CLK period is 5ns, so middle of period is ~2.5ns after edge
    # Find sample index at ~1ns after each edge (enough time for transition)
    edge_bits = []
    for e in edges[:8]:
        edge_t = times[e]
        # Find sample index at edge_t + 1ns (waiting for transition to settle)
        target_t = edge_t + 1e-9
        sample_idx = e
        while sample_idx < len(rows) and times[sample_idx] < target_t:
            sample_idx += 1
        sample_idx = min(sample_idx, len(rows) - 1)
        bit = int(sout[sample_idx] > vth)
        edge_bits.append(bit)

    if len(edge_bits) < 8:
        return False, f"only_{len(edge_bits)}_sampled_bits"
    mismatches = sum(1 for a, b in zip(edge_bits, expected) if a != b)
    if mismatches > 1:
        return False, f"bit_mismatch expected={expected} got={edge_bits}"
    return True, f"0xA5_serialized_ok mode=edge_only mismatches={mismatches}"


def check_vco(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """VCO: output frequency proportional to control voltage."""
    if not rows or not {"tune_voltage", "periodic_out"}.issubset(rows[0]):
        return False, "missing tune_voltage/periodic_out"
    vth = 0.45
    times = [r["time"] for r in rows]
    out = [r["periodic_out"] for r in rows]
    edges = rising_edges(out, times)
    if len(edges) < 50:
        return False, f"too_few_edges={len(edges)}"
    # Check 4 voltage regions: 0.225V, 0.45V, 0.675V, 0.9V
    regions = [0.225, 0.45, 0.675, 0.9]
    expected_f = [10e6 + 90e6*(v/0.9) for v in regions]
    errors = []
    for vctrl, f_exp in zip(regions, expected_f):
        idx = regions.index(vctrl)
        t_start = 2000e-9 * (idx + 1) + 400e-9
        t_end = t_start + 1500e-9
        period_edges = [t for t in edges if t_start < t < t_end]
        if len(period_edges) < 4:
            errors.append(f"vctrl={vctrl:.3f}_too_few_edges={len(period_edges)}")
            continue
        f_meas = (len(period_edges) - 1) / (period_edges[-1] - period_edges[0])
        err = abs(f_meas - f_exp) / f_exp
        if err > 0.3:
            errors.append(f"vctrl={vctrl:.3f}_freq_err={err:.2f}")
    if errors:
        return False, ";".join(errors[:3])
    return True, f"edges={len(edges)}"


def check_charge_pump(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """Charge pump: output steps up/down on lead/lag pulses."""
    if not rows or not {"lead_pulse", "lag_pulse", "pump_out"}.issubset(rows[0]):
        return False, "missing lead_pulse/lag_pulse/pump_out"
    vth = 0.45
    times = [r["time"] for r in rows]
    lead = [r["lead_pulse"] for r in rows]
    lag = [r["lag_pulse"] for r in rows]
    out = [r["pump_out"] for r in rows]
    lead_edges = rising_edges(lead, times)
    lag_edges = rising_edges(lag, times)
    # Check initial value ~0.45
    initial = out[0]
    if abs(initial - 0.45) > 0.1:
        return False, f"bad_initial={initial:.3f}"
    # After lead pulses, pump_out should be higher
    # Find row after last lead edge
    last_lead_t = lead_edges[-1] if lead_edges else 0
    settle_idx = next((i for i, t in enumerate(times) if t >= last_lead_t + 2e-9), len(rows) - 1)
    post_lead = out[settle_idx]
    expected_post_lead = 0.45 + len(lead_edges) * 0.02
    if abs(post_lead - expected_post_lead) > 0.03:
        return False, f"post_lead={post_lead:.3f}_exp={expected_post_lead:.3f}"
    # After lag pulses, should have decreased
    last_lag_t = lag_edges[-1] if lag_edges else 0
    settle_idx2 = next((i for i, t in enumerate(times) if t >= last_lag_t + 2e-9), len(rows) - 1)
    post_lag = out[settle_idx2]
    expected_post_lag = expected_post_lead - len(lag_edges) * 0.02
    if abs(post_lag - expected_post_lag) > 0.03:
        return False, f"post_lag={post_lag:.3f}_exp={expected_post_lag:.3f}"
    return True, f"lead_edges={len(lead_edges)} lag_edges={len(lag_edges)}"


def check_window_comparator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """Window comparator: exactly one output high in each region."""
    if not rows or not {"signal_in", "above_hi", "in_window", "below_lo"}.issubset(rows[0]):
        return False, "missing signal_in/above_hi/in_window/below_lo"
    vth = 0.45
    # Check 5 regions at midpoint times
    checks = [
        (50e-9, "below_lo"),
        (150e-9, "below_lo"),
        (250e-9, "in_window"),
        (350e-9, "above_hi"),
        (450e-9, "above_hi"),
    ]
    failures = []
    for t_target, expected in checks:
        window = [r for r in rows if t_target - 5e-9 <= r["time"] <= t_target + 5e-9]
        if not window:
            failures.append(f"no_samples@{t_target*1e9:.0f}ns")
            continue
        r = window[-1]
        above = r["above_hi"] > vth
        win = r["in_window"] > vth
        below = r["below_lo"] > vth
        count = sum([above, win, below])
        if count != 1:
            failures.append(f"ambiguous@{t_target*1e9:.0f}ns_count={count}")
            continue
        if expected == "below_lo" and not below:
            failures.append(f"exp_below@{t_target*1e9:.0f}ns")
        elif expected == "in_window" and not win:
            failures.append(f"exp_window@{t_target*1e9:.0f}ns")
        elif expected == "above_hi" and not above:
            failures.append(f"exp_above@{t_target*1e9:.0f}ns")
    if failures:
        return False, ";".join(failures[:3])
    return True, "three_region_output_correct"


def check_serializer_frame_alignment(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"clk", "frame", "sout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing clk/frame/sout"

    vth = 0.45
    times = [r["time"] for r in rows]
    clk = [r["clk"] for r in rows]
    frame = [r["frame"] for r in rows]
    sout = [r["sout"] for r in rows]

    clk_edges = [i for i in range(1, len(rows)) if clk[i - 1] <= vth < clk[i]]
    frame_rise = [i for i in range(1, len(rows)) if frame[i - 1] <= vth < frame[i]]
    frame_fall = [i for i in range(1, len(rows)) if frame[i - 1] >= vth > frame[i]]
    if len(frame_rise) < 2:
        return False, f"frame_rises={len(frame_rise)}"
    if len(clk_edges) < 16:
        return False, f"clk_edges={len(clk_edges)}"

    # Estimate bit period from clock edge spacing.
    periods = [times[clk_edges[i]] - times[clk_edges[i - 1]] for i in range(1, min(len(clk_edges), 10))]
    periods = [p for p in periods if p > 0.0]
    if not periods:
        return False, "invalid_clk_period"
    period = sorted(periods)[len(periods) // 2]

    expected_words = [0xA5, 0x3C]
    mismatch_total = 0
    detail_parts: list[str] = []

    for frame_idx, expected_word in enumerate(expected_words):
        t_frame = times[frame_rise[frame_idx]]
        clk_edge_times = [times[idx] for idx in clk_edges]
        near = [i for i, t_edge in enumerate(clk_edge_times) if abs(t_edge - t_frame) <= 0.6 * period]
        if near:
            start_pos = min(near, key=lambda i: abs(clk_edge_times[i] - t_frame))
        else:
            start_pos = next((i for i, t_edge in enumerate(clk_edge_times) if t_edge >= t_frame), None)
            if start_pos is None:
                return False, f"frame{frame_idx}_no_clk_after_frame"
        bit_edges = clk_edge_times[start_pos:start_pos + 8]
        if len(bit_edges) < 8:
            return False, f"frame{frame_idx}_insufficient_bits={len(bit_edges)}"

        expected_bits = [((expected_word >> bit) & 1) for bit in range(7, -1, -1)]
        observed_bits: list[int] = []
        for t_edge in bit_edges:
            t_sample = t_edge + 0.8e-9
            sample_idx = next((i for i, t in enumerate(times) if t >= t_sample), len(rows) - 1)
            observed_bits.append(1 if sout[sample_idx] > vth else 0)
        mismatches = sum(1 for a, b in zip(observed_bits, expected_bits) if a != b)
        mismatch_total += mismatches
        detail_parts.append(f"w{frame_idx}_mm={mismatches}")
        if mismatches > 1:
            return False, f"frame{frame_idx}_bit_mismatch exp={expected_bits} got={observed_bits}"

    # Frame pulse width should be around one bit window.
    pulse_widths: list[float] = []
    for r_idx in frame_rise[:2]:
        fall_idx = next((f for f in frame_fall if f > r_idx), None)
        if fall_idx is None:
            return False, "frame_without_fall_edge"
        pulse_widths.append(times[fall_idx] - times[r_idx])
    if any((w < 0.2 * period or w > 1.6 * period) for w in pulse_widths):
        return False, f"frame_pulse_widths={pulse_widths}"

    return True, (
        f"frame_rises={len(frame_rise)} "
        f"period={period:.3e} "
        f"pulse_w={[round(w / period, 2) for w in pulse_widths]} "
        f"{' '.join(detail_parts)} "
        f"mismatch_total={mismatch_total}"
    )


def check_xor_pd(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"ref", "div", "pd_out"}.issubset(rows[0]):
        return False, "missing ref/div/pd_out"
    vth = max(r["ref"] for r in rows) * 0.5
    pd = [r["pd_out"] for r in rows]
    hi_frac = sum(1 for v in pd if v > vth) / len(pd)
    binary = [1 if v > vth else 0 for v in pd]
    transitions = sum(1 for i in range(1, len(binary)) if binary[i] != binary[i - 1])
    if hi_frac < 0.10:
        return False, f"pd_out_stuck_low hi_frac={hi_frac:.3f}"
    if hi_frac > 0.90:
        return False, f"pd_out_stuck_high hi_frac={hi_frac:.3f}"
    if transitions < 15:
        return False, f"too_few_transitions={transitions}"
    if not (0.30 <= hi_frac <= 0.70):
        return False, f"duty_out_of_range={hi_frac:.3f}"
    return True, f"duty={hi_frac:.3f} transitions={transitions}"


def weighted_logic_high_fraction(rows: list[dict[str, float]], signal: str, threshold: float) -> float:
    if len(rows) < 2:
        return 0.0
    total_dt = rows[-1]["time"] - rows[0]["time"]
    if total_dt <= 0.0:
        return 0.0

    high_dt = 0.0
    for idx in range(1, len(rows)):
        dt = rows[idx]["time"] - rows[idx - 1]["time"]
        if dt <= 0.0:
            continue
        v_mid = 0.5 * (rows[idx - 1][signal] + rows[idx][signal])
        if v_mid > threshold:
            high_dt += dt
    return high_dt / total_dt


def time_window(rows: list[dict[str, float]], t_start: float, t_end: float) -> list[dict[str, float]]:
    return [r for r in rows if t_start <= r["time"] <= t_end]


def weighted_logic_high_fraction_window(
    rows: list[dict[str, float]],
    signal: str,
    threshold: float,
    t_start: float,
    t_end: float,
) -> float:
    return weighted_logic_high_fraction(time_window(rows, t_start, t_end), signal, threshold)


def check_pfd_updn(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"ref", "div", "up", "dn"}.issubset(rows[0]):
        return False, "missing ref/div/up/dn"
    vth = max(r["ref"] for r in rows) * 0.5
    up = [1 if r["up"] > vth else 0 for r in rows]
    dn = [1 if r["dn"] > vth else 0 for r in rows]
    up_frac = weighted_logic_high_fraction(rows, "up", vth)
    dn_frac = weighted_logic_high_fraction(rows, "dn", vth)
    both_hi = [a & b for a, b in zip(up, dn)]
    run_len = 0
    max_run = 0
    for b in both_hi:
        if b:
            run_len += 1
            max_run = max(max_run, run_len)
        else:
            run_len = 0
    up_pulses = sum(1 for i in range(1, len(up)) if up[i - 1] == 0 and up[i] == 1)
    if max_run > 5:
        return False, f"overlap_too_long={max_run}"
    if up_frac < 0.01:
        return False, f"up_never_high up_frac={up_frac:.3f}"
    if up_frac < dn_frac:
        return False, f"up_frac_lt_dn_frac up={up_frac:.3f} dn={dn_frac:.3f}"
    if up_pulses < 10:
        return False, f"too_few_up_pulses={up_pulses}"
    return True, f"up_frac={up_frac:.3f} dn_frac={dn_frac:.3f} up_pulses={up_pulses}"


def check_pfd_deadzone(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"ref", "div", "up", "dn"}.issubset(rows[0]):
        return False, "missing ref/div/up/dn"
    vth = max(r["ref"] for r in rows) * 0.5
    up = [1 if r["up"] > vth else 0 for r in rows]
    dn = [1 if r["dn"] > vth else 0 for r in rows]
    up_frac = weighted_logic_high_fraction(rows, "up", vth)
    dn_frac = weighted_logic_high_fraction(rows, "dn", vth)
    both_hi = [a & b for a, b in zip(up, dn)]

    run_len = 0
    max_run = 0
    for bit in both_hi:
        if bit:
            run_len += 1
            max_run = max(max_run, run_len)
        else:
            run_len = 0

    up_pulses = sum(1 for i in range(1, len(up)) if up[i - 1] == 0 and up[i] == 1)
    if not (0.001 <= up_frac <= 0.03):
        return False, f"up_frac_out_of_range={up_frac:.4f}"
    if dn_frac > 0.002:
        return False, f"dn_frac_too_high={dn_frac:.4f}"
    if max_run > 6:
        return False, f"overlap_too_long={max_run}"
    if up_pulses < 10:
        return False, f"too_few_up_pulses={up_pulses}"
    return True, f"up_frac={up_frac:.4f} dn_frac={dn_frac:.4f} up_pulses={up_pulses}"


def check_pfd_reset_race(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"ref", "div", "up", "dn"}.issubset(rows[0]):
        return False, "missing ref/div/up/dn"

    vth = max(r["ref"] for r in rows) * 0.5
    first = time_window(rows, 20e-9, 120e-9)
    second = time_window(rows, 160e-9, 260e-9)
    if len(first) < 4 or len(second) < 4:
        return False, "insufficient_window_samples"

    up_first = weighted_logic_high_fraction(first, "up", vth)
    dn_first = weighted_logic_high_fraction(first, "dn", vth)
    up_second = weighted_logic_high_fraction(second, "up", vth)
    dn_second = weighted_logic_high_fraction(second, "dn", vth)

    first_times = [r["time"] for r in first]
    second_times = [r["time"] for r in second]
    up_pulses_first = len(rising_edges([r["up"] for r in first], first_times, threshold=vth))
    dn_pulses_second = len(rising_edges([r["dn"] for r in second], second_times, threshold=vth))

    overlap_dt = 0.0
    total_dt = 0.0
    for idx in range(1, len(rows)):
        dt = rows[idx]["time"] - rows[idx - 1]["time"]
        if dt <= 0.0:
            continue
        total_dt += dt
        up_mid = 0.5 * (rows[idx - 1]["up"] + rows[idx]["up"])
        dn_mid = 0.5 * (rows[idx - 1]["dn"] + rows[idx]["dn"])
        if up_mid > vth and dn_mid > vth:
            overlap_dt += dt
    overlap_frac = overlap_dt / max(total_dt, 1e-18)

    ok = (
        0.001 <= up_first <= 0.08
        and dn_first <= 0.01
        and 0.001 <= dn_second <= 0.08
        and up_second <= 0.01
        and up_pulses_first >= 4
        and dn_pulses_second >= 4
        and overlap_frac <= 0.01
    )
    return ok, (
        f"up_first={up_first:.4f} dn_first={dn_first:.4f} "
        f"up_second={up_second:.4f} dn_second={dn_second:.4f} "
        f"up_pulses_first={up_pulses_first} dn_pulses_second={dn_pulses_second} "
        f"overlap_frac={overlap_frac:.4f}"
    )


def check_cppll_freq_step_reacquire(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"ref_clk", "fb_clk", "lock", "vctrl_mon"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing ref_clk/fb_clk/lock/vctrl_mon"

    vth = 0.45
    times = [r["time"] for r in rows]
    ref_edges = rising_edges([r["ref_clk"] for r in rows], times, threshold=vth)
    fb_edges = rising_edges([r["fb_clk"] for r in rows], times, threshold=vth)
    if len(ref_edges) < 12 or len(fb_edges) < 12:
        return False, f"not_enough_edges ref={len(ref_edges)} fb={len(fb_edges)}"

    ref_late = [t for t in ref_edges if 4.5e-6 <= t <= 5.9e-6]
    fb_late = [t for t in fb_edges if 4.5e-6 <= t <= 5.9e-6]
    if len(ref_late) < 4 or len(fb_late) < 4:
        return False, (
            f"not_enough_late_edges ref_late={len(ref_late)} fb_late={len(fb_late)}"
        )

    ref_periods = [b - a for a, b in zip(ref_late, ref_late[1:])]
    fb_periods = [b - a for a, b in zip(fb_late, fb_late[1:])]
    ref_period = sum(ref_periods) / len(ref_periods)
    fb_period = sum(fb_periods) / len(fb_periods)
    if ref_period <= 0.0 or fb_period <= 0.0:
        return False, "non_positive_period"
    freq_ratio = ref_period / fb_period

    lock_edges = rising_edges([r["lock"] for r in rows], times, threshold=vth)
    pre_lock_edges = [t for t in lock_edges if t < 2.0e-6]
    post_lock_edges = [t for t in lock_edges if 2.2e-6 <= t <= 5.9e-6]
    relock_time = post_lock_edges[0] if post_lock_edges else float("nan")

    disturb_low_frac = 1.0 - weighted_logic_high_fraction_window(
        rows, "lock", vth, 2.05e-6, 2.8e-6
    )

    vctrl_vals = [r["vctrl_mon"] for r in rows]
    vctrl_min = min(vctrl_vals)
    vctrl_max = max(vctrl_vals)
    vctrl_in_range = all(-1e-6 <= v <= 0.95 for v in vctrl_vals)

    ok = (
        bool(pre_lock_edges)
        and disturb_low_frac >= 0.25
        and bool(post_lock_edges)
        and 0.97 <= freq_ratio <= 1.03
        and vctrl_in_range
    )
    return ok, (
        f"pre_lock_edges={len(pre_lock_edges)} "
        f"disturb_lock_low_frac={disturb_low_frac:.3f} "
        f"post_lock_edges={len(post_lock_edges)} "
        f"late_freq_ratio={freq_ratio:.4f} "
        f"relock_time={(relock_time if post_lock_edges else float('nan')):.3e} "
        f"vctrl_min={vctrl_min:.3f} "
        f"vctrl_max={vctrl_max:.3f}"
    )


def check_gray_counter_4b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"clk", "rstb", "g3", "g2", "g1", "g0"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing clk/rstb/g3/g2/g1/g0"
    vth = max(r["clk"] for r in rows) * 0.5
    clk = [r["clk"] for r in rows]
    times_ns = [r["time"] * 1e9 for r in rows]
    edge_idx = [i for i in range(1, len(clk)) if clk[i - 1] <= vth < clk[i]]
    codes: list[int] = []
    for idx in edge_idx:
        settle = min(idx + 8, len(rows) - 1)
        code = (
            (1 if rows[settle]["g3"] > vth else 0) << 3
            | (1 if rows[settle]["g2"] > vth else 0) << 2
            | (1 if rows[settle]["g1"] > vth else 0) << 1
            | (1 if rows[settle]["g0"] > vth else 0)
        )
        codes.append(code)
    post_reset = [codes[i] for i, idx in enumerate(edge_idx) if times_ns[idx] > 55.0]
    if len(post_reset) < 20:
        return False, f"not_enough_post_reset_edges={len(post_reset)}"
    bad_transitions = 0
    for a, b in zip(post_reset[:-1], post_reset[1:]):
        if bin(a ^ b).count("1") != 1:
            bad_transitions += 1
    unique_codes = set(post_reset)
    expected_grays = {i ^ (i >> 1) for i in range(16)}
    if bad_transitions > 0:
        return False, f"gray_property_violated bad_transitions={bad_transitions}"
    if not expected_grays.issubset(unique_codes):
        return False, f"missing_gray_codes count={16 - len(expected_grays & unique_codes)}"
    return True, f"unique_codes={len(unique_codes)} bad_transitions={bad_transitions}"


def check_gray_counter_4b_v2(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """Same as check_gray_counter_4b but uses time-based settling (5 ns after edge).

    The v2 perturbation testbenches can have maxstep/tedge combos that make
    the original 8-index settle land on a mid-transition sample. Switching to
    a fixed 5 ns post-edge settle avoids transitional values.
    """
    required = {"clk", "rstb", "g3", "g2", "g1", "g0"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing clk/rstb/g3/g2/g1/g0"
    vth = max(r["clk"] for r in rows) * 0.5
    clk = [r["clk"] for r in rows]
    times = [r["time"] for r in rows]
    times_ns = [t * 1e9 for t in times]
    edge_idx = [i for i in range(1, len(clk)) if clk[i - 1] <= vth < clk[i]]
    codes: list[int] = []
    for idx in edge_idx:
        target_t = times[idx] + 5e-9
        settle = idx
        while settle < len(rows) - 1 and times[settle] < target_t:
            settle += 1
        settle = min(settle, len(rows) - 1)
        code = (
            (1 if rows[settle]["g3"] > vth else 0) << 3
            | (1 if rows[settle]["g2"] > vth else 0) << 2
            | (1 if rows[settle]["g1"] > vth else 0) << 1
            | (1 if rows[settle]["g0"] > vth else 0)
        )
        codes.append(code)
    post_reset = [codes[i] for i, idx in enumerate(edge_idx) if times_ns[idx] > 55.0]
    if len(post_reset) < 20:
        return False, f"not_enough_post_reset_edges={len(post_reset)}"
    bad_transitions = 0
    for a, b in zip(post_reset[:-1], post_reset[1:]):
        if bin(a ^ b).count("1") != 1:
            bad_transitions += 1
    unique_codes = set(post_reset)
    expected_grays = {i ^ (i >> 1) for i in range(16)}
    if bad_transitions > 0:
        return False, f"gray_property_violated bad_transitions={bad_transitions}"
    if not expected_grays.issubset(unique_codes):
        return False, f"missing_gray_codes count={16 - len(expected_grays & unique_codes)}"
    return True, f"all_gray_ok unique_codes={len(unique_codes)}"


def check_gray_counter_one_bit_change(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    sample = rows[0]
    clk_col = _pick_column(sample, ["clk", "CLK"])
    rst_col = _pick_column(sample, ["rst", "RST", "rstb", "RSTB"])
    if clk_col is None or rst_col is None:
        return False, "missing clk/rst"

    g_cols = [_pick_column(sample, [f"g{idx}", f"G{idx}"]) for idx in range(4)]
    if any(col is None for col in g_cols):
        return False, "missing g0..g3"

    threshold = 0.45
    clk = [r[clk_col] for r in rows]
    edge_idx = [i for i in range(1, len(clk)) if clk[i - 1] <= threshold < clk[i]]
    if len(edge_idx) < 20:
        return False, f"not_enough_clk_edges={len(edge_idx)}"

    rst_high_active = any(r[rst_col] > threshold for r in rows[: max(4, len(rows) // 10)])
    post_reset_codes: list[int] = []
    for idx in edge_idx:
        settle = min(idx + 8, len(rows) - 1)
        rst_val = rows[settle][rst_col]
        if (rst_high_active and rst_val > threshold) or ((not rst_high_active) and rst_val < threshold):
            continue
        code = 0
        for bit_idx, col in enumerate(g_cols):
            if rows[settle][col] > threshold:
                code |= 1 << bit_idx
        post_reset_codes.append(code)

    if len(post_reset_codes) < 16:
        return False, f"not_enough_post_reset_codes={len(post_reset_codes)}"

    bad_transitions = sum(1 for a, b in zip(post_reset_codes[:-1], post_reset_codes[1:]) if bin(a ^ b).count("1") != 1)
    unique_codes = set(post_reset_codes)
    expected_grays = {i ^ (i >> 1) for i in range(16)}
    if bad_transitions:
        return False, f"gray_property_violated bad_transitions={bad_transitions}"
    if not expected_grays.issubset(unique_codes):
        return False, f"missing_gray_codes count={16 - len(expected_grays & unique_codes)}"
    return True, f"unique_codes={len(unique_codes)} bad_transitions={bad_transitions}"


def check_prbs7(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """PRBS-7: check serial output has many transitions and ~50% high fraction."""
    if not rows:
        return False, "empty"
    serial_col = next((k for k in rows[0] if k.lower() in {"prbs_out", "serial", "serial_out", "dout", "q_out", "q"}), None)
    if serial_col is None:
        return False, f"missing serial column; keys={list(rows[0].keys())[:8]}"
    post = [r[serial_col] for r in rows if r["time"] > 2e-8]
    if len(post) < 20:
        return False, "too_few_post_init_samples"
    binary = [1 if v > 0.45 else 0 for v in post]
    transitions = sum(1 for i in range(len(binary) - 1) if binary[i] != binary[i + 1])
    hi_frac = sum(binary) / len(binary)
    ok = transitions >= 20 and 0.2 < hi_frac < 0.8
    return ok, f"transitions={transitions} hi_frac={hi_frac:.3f}"


def check_therm2bin(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """Thermometer-to-binary: check all 4 output bits are high in final window (all 15 inputs on)."""
    if not rows:
        return False, "empty"
    b_cols = [k for k in rows[0] if k.lower() in {"b3", "b2", "b1", "b0", "bin_3", "bin_2", "bin_1", "bin_0"}]
    if len(b_cols) < 4:
        return False, f"missing b3..b0; got {list(rows[0].keys())[:12]}"
    b_cols = sorted(
        b_cols,
        key=lambda name: int(re.findall(r"(\d+)$", name)[0]),
    )[:4]
    t_end = rows[-1]["time"]
    late = [r for r in rows if r["time"] > t_end * 0.75]
    if not late:
        return False, "no late-window rows"
    all_high = all(r[c] > 0.45 for r in late for c in b_cols)
    return all_high, f"all_bits_high_final_window={all_high}"


def check_sar_logic(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """10-bit SAR logic: check RDY asserts and DP_DAC bits show activity."""
    if not rows:
        return False, "empty"
    rdy_col = next((k for k in rows[0] if k.lower() in {"rdy", "ready", "eoc", "done"}), None)
    if rdy_col is None:
        return False, f"missing rdy/eoc column; keys={list(rows[0].keys())[:10]}"
    rdy_vals = [r[rdy_col] for r in rows]
    rdy_high = any(v > 0.45 for v in rdy_vals)
    dac_cols = [k for k in rows[0] if re.search(r"dp_dac|dp_n|dp_p|dac_bit|cap", k.lower())]
    dac_activity = False
    for col in dac_cols[:4]:
        vals = [r[col] for r in rows]
        if max(vals) - min(vals) > 0.4:
            dac_activity = True
            break
    ok = rdy_high and dac_activity
    return ok, f"rdy_asserted={rdy_high} dac_activity={dac_activity}"


def check_pipeline_stage(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """1.5-bit MDAC: check VRES is bounded and sub-ADC outputs vary."""
    if not rows:
        return False, "empty"
    vres_col = next((k for k in rows[0] if k.lower() in {"vres", "vout", "residue"}), None)
    d_cols = [k for k in rows[0] if k.lower() in {"d1", "d0", "dout1", "dout0"}]
    if vres_col is None:
        return False, f"missing vres column; keys={list(rows[0].keys())[:10]}"
    vres_vals = [r[vres_col] for r in rows]
    vres_range = max(vres_vals) - min(vres_vals)
    vres_bounded = max(abs(v) for v in vres_vals) < 2.0
    d_active = False
    for col in d_cols:
        vals = [r[col] for r in rows]
        if max(vals) - min(vals) > 0.4:
            d_active = True
            break
    ok = vres_bounded and vres_range > 0.1
    return ok, f"vres_range={vres_range:.3f} bounded={vres_bounded} d_active={d_active}"


def check_sar_12bit(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """12-bit SAR: check EOC/RDY asserts and DAC bits show activity."""
    return check_sar_logic(rows)


def check_segmented_dac(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """Segmented 14-bit DAC: check differential output spans meaningful range."""
    if not rows:
        return False, "empty"
    vop_col = next((k for k in rows[0] if k.lower() in {"vout_p", "iout_p", "voutp"}), None)
    von_col = next((k for k in rows[0] if k.lower() in {"vout_n", "iout_n", "voutn"}), None)
    if vop_col is None or von_col is None:
        vout_col = next((k for k in rows[0] if "vout" in k.lower() or "iout" in k.lower()), None)
        if vout_col is None:
            return False, f"missing vout_p/vout_n; keys={list(rows[0].keys())[:10]}"
        vvals = [r[vout_col] for r in rows]
        ok = max(vvals) - min(vvals) > 0.1
        return ok, f"vout_range={max(vvals)-min(vvals):.3f}"
    diff = [r[vop_col] - r[von_col] for r in rows]
    diff_range = max(diff) - min(diff)
    ok = diff_range > 0.1
    return ok, f"diff_range={diff_range:.3f}"


def check_comparator_offset_search(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "inp", "inn", "outp"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/inp/inn/outp"

    threshold = 0.45
    outp = [r["outp"] for r in rows]
    times = [r["time"] for r in rows]
    rise_t = next((times[idx] for idx in range(1, len(rows)) if outp[idx - 1] < threshold <= outp[idx]), None)
    if rise_t is None:
        return False, "no_output_crossing"

    crossing_row = next((r for r in rows if r["time"] >= rise_t), rows[-1])
    crossing_voltage = crossing_row["inp"]
    low_window = [r["outp"] for r in rows if r["inp"] <= 0.501]
    high_window = [r["outp"] for r in rows if r["inp"] >= 0.509]
    if not low_window or not high_window:
        return False, "insufficient_offset_windows"

    low_frac = sum(1 for v in low_window if v < threshold) / len(low_window)
    high_frac = sum(1 for v in high_window if v > threshold) / len(high_window)
    ok = abs(crossing_voltage - 0.505) <= 0.003 and low_frac > 0.9 and high_frac > 0.9
    return ok, (
        f"crossing_voltage={crossing_voltage:.4f} "
        f"low_frac={low_frac:.3f} "
        f"high_frac={high_frac:.3f}"
    )


def check_cdac_cal(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """CDAC with cal: check differential output varies with control bits."""
    if not rows:
        return False, "empty"
    vdac_cols = [k for k in rows[0] if "vdac" in k.lower() or "vcap" in k.lower() or "vout" in k.lower()]
    if not vdac_cols:
        return False, f"missing vdac columns; keys={list(rows[0].keys())[:10]}"
    for col in vdac_cols[:2]:
        vals = [r[col] for r in rows]
        if max(vals) - min(vals) > 0.05:
            return True, f"vdac_activity col={col} range={max(vals)-min(vals):.3f}"
    return False, f"no vdac activity in {vdac_cols[:4]}"


def check_sc_integrator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    keys = rows[0].keys()
    phi2_col = next((k for k in keys if k.lower() == "phi2"), None)
    vout_col = next((k for k in keys if k.lower() in {"vout", "out"}), None)
    if phi2_col is None or vout_col is None:
        return False, f"missing phi2/vout; keys={list(keys)[:10]}"

    edges = [
        rows[i]["time"]
        for i in range(1, len(rows))
        if rows[i - 1][phi2_col] < 0.45 <= rows[i][phi2_col]
    ]
    if len(edges) < 3:
        return False, f"phi2_edges={len(edges)}"

    samples: list[float] = []
    for t_edge in edges[:5]:
        window = [
            r[vout_col]
            for r in rows
            if t_edge + 0.5e-9 <= r["time"] <= t_edge + 2.0e-9
        ]
        if window:
            samples.append(sum(window) / len(window))
    if len(samples) < 3:
        return False, f"insufficient_vout_samples={len(samples)}"

    monotonic = all(samples[i + 1] >= samples[i] - 2e-3 for i in range(len(samples) - 1))
    total_step = samples[-1] - samples[0]
    ok = monotonic and total_step > 0.05
    return ok, f"monotonic={monotonic} total_step={total_step:.3f}"


def check_bg_cal(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    trim_cols = sorted(
        [k for k in rows[0] if re.fullmatch(r"trim_?[0-5]", k.lower())],
        key=lambda name: int(re.findall(r"(\d+)$", name)[0]),
    )
    settled_col = next((k for k in rows[0] if k.lower() in {"settled", "done", "rdy"}), None)
    if len(trim_cols) < 6 or settled_col is None:
        return False, f"missing trim/settled columns; keys={list(rows[0].keys())[:12]}"

    codes = []
    for row in rows:
        code = 0
        for idx, col in enumerate(trim_cols):
            if row[col] > 0.45:
                code |= 1 << idx
        codes.append(code)

    code_span = max(codes) - min(codes)
    settled_high = any(r[settled_col] > 0.45 for r in rows[int(len(rows) * 0.75):])
    ok = code_span >= 4 and settled_high
    return ok, f"code_span={code_span} settled_high={settled_high}"


def check_multitone(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    out_col = next((k for k in rows[0] if k.lower() in {"out", "vout"}), None)
    if out_col is None:
        return False, f"missing out/vout column; keys={list(rows[0].keys())[:10]}"

    times = [r["time"] for r in rows]
    vals = [r[out_col] for r in rows]

    def interp(t: float) -> float | None:
        if not times:
            return None
        if t <= times[0]:
            return vals[0]
        if t >= times[-1]:
            return vals[-1]
        lo = 0
        hi = len(times) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if times[mid] <= t:
                lo = mid
            else:
                hi = mid
        t0 = times[lo]
        t1 = times[hi]
        if t1 == t0:
            return vals[lo]
        a = (t - t0) / (t1 - t0)
        return vals[lo] + a * (vals[hi] - vals[lo])

    samples = [
        (0.125e-6, 0.2 * math.sin(2 * math.pi * 1e6 * 0.125e-6) + 0.1 * math.sin(2 * math.pi * 2e6 * 0.125e-6) + 0.05 * math.sin(2 * math.pi * 3e6 * 0.125e-6)),
        (0.275e-6, 0.2 * math.sin(2 * math.pi * 1e6 * 0.275e-6) + 0.1 * math.sin(2 * math.pi * 2e6 * 0.275e-6) + 0.05 * math.sin(2 * math.pi * 3e6 * 0.275e-6)),
        (0.410e-6, 0.2 * math.sin(2 * math.pi * 1e6 * 0.410e-6) + 0.1 * math.sin(2 * math.pi * 2e6 * 0.410e-6) + 0.05 * math.sin(2 * math.pi * 3e6 * 0.410e-6)),
    ]
    errs = []
    for t_check, expected in samples:
        measured = interp(t_check)
        if measured is None:
            errs.append(1.0)
            continue
        errs.append(abs(measured - expected))
    max_err = max(errs)
    ok = max_err < 0.03
    return ok, f"max_err={max_err:.4f}"


def check_nrz_prbs(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    outp_col = next((k for k in rows[0] if k.lower() in {"outp", "voutp", "out_p"}), None)
    outn_col = next((k for k in rows[0] if k.lower() in {"outn", "voutn", "out_n"}), None)
    if outp_col is None or outn_col is None:
        return False, f"missing differential outputs; keys={list(rows[0].keys())[:12]}"

    outp = [r[outp_col] for r in rows]
    outn = [r[outn_col] for r in rows]
    transitions = sum(1 for i in range(1, len(outp)) if (outp[i - 1] - 0.45) * (outp[i] - 0.45) < 0)
    complement_err = sum(abs((a + b) - 0.9) for a, b in zip(outp, outn)) / len(outp)
    swing = max(outp) - min(outp)
    ok = transitions >= 8 and complement_err < 0.08 and swing > 0.2
    return ok, f"transitions={transitions} complement_err={complement_err:.4f} swing={swing:.3f}"


def check_mixed_domain_cdac_bug(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    vout_col = next((k for k in rows[0] if k.lower() in {"vout", "out"}), None)
    if vout_col is None:
        return False, f"missing vout column; keys={list(rows[0].keys())[:10]}"

    targets = [
        (17e-9, 0.2),
        (37e-9, 0.5),
        (57e-9, 0.8),
    ]
    errs = []
    for t_check, expected in targets:
        window = [r[vout_col] for r in rows if abs(r["time"] - t_check) <= 1.5e-9]
        if not window:
            errs.append(1.0)
            continue
        measured = sum(window) / len(window)
        errs.append(abs(measured - expected))
    max_err = max(errs)
    ok = max_err < 0.05
    return ok, f"max_err={max_err:.4f}"


def check_spectre_port_discipline(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    required = {"a", "b", "y"}
    keymap = {k.lower(): k for k in rows[0]}
    if not required.issubset(keymap):
        return False, f"missing a/b/y; keys={list(rows[0].keys())[:10]}"

    windows = [
        (10e-9, 0.0, "00"),
        (30e-9, 0.0, "10"),
        (50e-9, 0.0, "01"),
        (70e-9, 0.9, "11"),
    ]
    errs: list[str] = []
    for t_check, expected, label in windows:
        vals = [r[keymap["y"]] for r in rows if abs(r["time"] - t_check) <= 1.5e-9]
        if not vals:
            errs.append(f"{label}_no_samples")
            continue
        measured = sum(vals) / len(vals)
        if abs(measured - expected) > 0.05:
            errs.append(f"{label}_err={abs(measured - expected):.3f}")
    return (not errs), ("ok" if not errs else ";".join(errs))


def check_inverted_comparator_logic_bug(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    required = {"vinp", "vinn", "out_p"}
    if not required.issubset(rows[0]):
        return False, "missing vinp/vinn/out_p"

    windows = [
        (10e-9, 0.0, "low0"),
        (30e-9, 0.9, "high1"),
        (50e-9, 0.0, "low2"),
        (70e-9, 0.9, "high3"),
    ]
    errs: list[str] = []
    for t_check, expected, label in windows:
        vals = [r["out_p"] for r in rows if abs(r["time"] - t_check) <= 1.5e-9]
        if not vals:
            errs.append(f"{label}_no_samples")
            continue
        measured = sum(vals) / len(vals)
        if abs(measured - expected) > 0.08:
            errs.append(f"{label}_err={abs(measured - expected):.3f}")
    return (not errs), ("ok" if not errs else ";".join(errs))


def check_mux_4to1(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"d0", "d1", "d2", "d3", "sel1", "sel0", "y", "time"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing d0/d1/d2/d3/sel1/sel0/y/time"
    windows = [
        (50e-9, 0.1, "sel0"),
        (150e-9, 0.3, "sel1"),
        (250e-9, 0.6, "sel2"),
        (350e-9, 0.8, "sel3"),
    ]
    tol = 20e-3
    failures: list[str] = []
    for t_check, expected, label in windows:
        window = [
            r["y"]
            for r in rows
            if t_check - 10e-9 <= r["time"] <= t_check + 10e-9
        ]
        if not window:
            failures.append(f"{label}_no_samples")
            continue
        measured = sum(window) / len(window)
        if abs(measured - expected) > tol:
            failures.append(f"{label}_err={abs(measured - expected):.4f}")
    if failures:
        return False, ";".join(failures)
    return True, "all_4_select_windows_correct"


def check_above_threshold_startup(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin/out"
    if max(r["vin"] for r in rows) < 0.45:
        return False, "vin_never_above_threshold"
    out_vals = [r["out"] for r in rows]
    out_min = min(out_vals)
    out_max = max(out_vals)
    span = out_max - out_min
    if span < 0.2:
        return False, f"out_not_latched_high span={span:.3f}"
    vth = out_min + 0.5 * span
    first_hi_t = next((r["time"] for r in rows if r["out"] > vth), None)
    if first_hi_t is None:
        return False, "out_never_high"
    late = [r["out"] for r in rows if r["time"] >= rows[-1]["time"] * 0.6]
    late_hi_frac = sum(1 for v in late if v > vth) / max(len(late), 1)
    ok = first_hi_t <= 2e-9 and late_hi_frac > 0.95
    return ok, f"first_hi_t_ns={first_hi_t*1e9:.3f} late_hi_frac={late_hi_frac:.3f}"


def check_bound_step_period_guard(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "guard_out", "phase_out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/guard_out/phase_out"
    g = [r["guard_out"] for r in rows]
    p = [r["phase_out"] for r in rows]
    t = [r["time"] for r in rows]
    gth = 0.5 * (max(g) + min(g))
    guard_hi_frac = weighted_logic_high_fraction(rows, "guard_out", gth)
    if not (0.08 <= guard_hi_frac <= 0.30):
        return False, f"guard_hi_frac_out_of_range={guard_hi_frac:.3f}"
    wraps = sum(1 for i in range(1, len(p)) if p[i] < p[i - 1] - 0.2)
    phase_span = max(p) - min(p)
    guard_rises = len(rising_edges(g, t, threshold=gth))
    ok = wraps >= 3 and phase_span > 0.5 and guard_rises >= 3
    return ok, f"guard_rises={guard_rises} wraps={wraps} phase_span={phase_span:.3f} guard_hi_frac={guard_hi_frac:.3f}"


def check_cross_hysteresis_window(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin/out"
    out_vals = [r["out"] for r in rows]
    lo = min(out_vals)
    hi = max(out_vals)
    span = hi - lo
    if span < 0.3:
        return False, f"out_span_too_small={span:.3f}"
    low1 = [r["out"] for r in rows if r["time"] <= 20e-9]
    high_mid = [r["out"] for r in rows if 35e-9 <= r["time"] <= 55e-9]
    low2 = [r["out"] for r in rows if r["time"] >= 75e-9]
    if not low1 or not high_mid or not low2:
        return False, "insufficient_window_samples"
    m_low1 = sum(low1) / len(low1)
    m_high = sum(high_mid) / len(high_mid)
    m_low2 = sum(low2) / len(low2)
    ok = (m_high - m_low1) > 0.45 * span and (m_high - m_low2) > 0.45 * span
    return ok, f"low1={m_low1:.3f} high={m_high:.3f} low2={m_low2:.3f} span={span:.3f}"


def check_cross_interval_163p333(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"delay_out", "seen_out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing delay_out/seen_out"
    seen_hi = max(r["seen_out"] for r in rows)
    if seen_hi < 0.3:
        return False, f"seen_out_never_high={seen_hi:.3f}"
    tail = [r["delay_out"] for r in rows if r["time"] >= rows[-1]["time"] * 0.7]
    if not tail:
        return False, "no_tail_samples"
    delay_level = sum(tail) / len(tail)
    vdd_est = max(max(r["seen_out"] for r in rows), 1e-6)
    delay_ps = delay_level / vdd_est * 200.0
    ok = 130.0 <= delay_ps <= 190.0
    return ok, f"delay_ps={delay_ps:.3f} seen_hi={seen_hi:.3f}"


def check_cross_sine_precision(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"first_err_out", "max_err_out", "count_out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing first_err_out/max_err_out/count_out"
    vdd_est = max(r["count_out"] for r in rows)
    if vdd_est < 0.2:
        return False, f"count_out_too_low={vdd_est:.3f}"
    count_est = max(r["count_out"] for r in rows) / max(vdd_est, 1e-6) * 3.0
    max_err_ps = max(r["max_err_out"] for r in rows) / max(vdd_est, 1e-6) * 10.0
    ok = count_est >= 2.5 and max_err_ps < 1.0
    return ok, f"count_est={count_est:.2f} max_err_ps={max_err_ps:.4f}"


def check_differential_voltage_output(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "outp", "outn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/outp/outn"
    w0 = [r for r in rows if 5e-9 <= r["time"] <= 15e-9]
    w1 = [r for r in rows if 25e-9 <= r["time"] <= 35e-9]
    w2 = [r for r in rows if 45e-9 <= r["time"] <= 55e-9]
    if not w0 or not w1 or not w2:
        return False, "insufficient_window_samples"
    m0p = sum(r["outp"] for r in w0) / len(w0)
    m1p = sum(r["outp"] for r in w1) / len(w1)
    m2p = sum(r["outp"] for r in w2) / len(w2)
    m0n = sum(r["outn"] for r in w0) / len(w0)
    m1n = sum(r["outn"] for r in w1) / len(w1)
    m2n = sum(r["outn"] for r in w2) / len(w2)
    outn_span = max(abs(m0n - m1n), abs(m1n - m2n), abs(m0n - m2n))
    ok = (m1p - m0p) > 0.25 and abs(m2p - m0p) < 0.12 and outn_span < 0.08
    return ok, f"outp_means=({m0p:.3f},{m1p:.3f},{m2p:.3f}) outn_span={outn_span:.3f}"


def check_final_step_file_metric(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "ref", "metric_out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/ref/metric_out"
    vth = 0.45 if max(r["ref"] for r in rows) < 1.0 else 0.5 * max(r["ref"] for r in rows)
    ref_edges = rising_edges([r["ref"] for r in rows], [r["time"] for r in rows], threshold=vth)
    metric_vals = [r["metric_out"] for r in rows]
    vmax = max(metric_vals)
    if vmax < 0.2:
        return False, f"metric_out_too_low={vmax:.3f}"
    tail = [r["metric_out"] for r in rows if r["time"] >= rows[-1]["time"] * 0.85]
    final_norm = (sum(tail) / len(tail)) / max(vmax, 1e-6) if tail else 0.0
    dips = sum(1 for i in range(1, len(metric_vals)) if metric_vals[i] + 0.03 < metric_vals[i - 1])
    ok = len(ref_edges) >= 4 and final_norm > 0.90 and dips <= 3
    return ok, f"ref_edges={len(ref_edges)} final_norm={final_norm:.3f} metric_dips={dips}"


def check_parameter_type_override(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or "out" not in rows[0]:
        return False, "missing out"
    out_vals = [r["out"] for r in rows]
    vhi = max(out_vals)
    vth = 0.5 * vhi
    times = [r["time"] for r in rows]
    pulses = len(rising_edges(out_vals, times, threshold=vth))
    ok = 3 <= pulses <= 5 and 0.60 <= vhi <= 0.85
    return ok, f"pulses={pulses} peak={vhi:.3f}"


def check_phase_accumulator_timer_wrap(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk_out", "phase_out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk_out/phase_out"
    phase_vals = [r["phase_out"] for r in rows]
    clk_vals = [r["clk_out"] for r in rows]
    times = [r["time"] for r in rows]
    phase_span = max(phase_vals) - min(phase_vals)
    if phase_span < 0.4:
        return False, f"phase_span_too_small={phase_span:.3f}"
    wraps = sum(1 for i in range(1, len(phase_vals)) if phase_vals[i] < phase_vals[i - 1] - 0.2 * phase_span)
    cth = 0.5 * (max(clk_vals) + min(clk_vals))
    clk_rises = len(rising_edges(clk_vals, times, threshold=cth))
    ok = wraps >= 3 and clk_rises >= 3
    return ok, f"wraps={wraps} clk_rises={clk_rises} phase_span={phase_span:.3f}"


def check_simultaneous_event_order(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/out"
    windows = [
        (12e-9, 18e-9),
        (32e-9, 38e-9),
        (52e-9, 58e-9),
        (72e-9, 78e-9),
    ]
    levels: list[float] = []
    for t0, t1 in windows:
        vals = [r["out"] for r in rows if t0 <= r["time"] <= t1]
        if not vals:
            return False, "insufficient_window_samples"
        levels.append(sum(vals) / len(vals))
    monotonic = all(levels[i] <= levels[i + 1] + 0.05 for i in range(len(levels) - 1))
    span = levels[-1] - levels[0]
    ok = monotonic and span > 0.15
    return ok, f"plateau_levels={[round(v,3) for v in levels]} span={span:.3f}"


def check_timer_absolute_grid(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk_out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk_out"
    clk_vals = [r["clk_out"] for r in rows]
    times = [r["time"] for r in rows]
    cth = 0.5 * (max(clk_vals) + min(clk_vals))
    rises = rising_edges(clk_vals, times, threshold=cth)
    if len(rises) < 4:
        return False, f"too_few_rising_edges={len(rises)}"
    targets = [10.1e-9, 30.1e-9, 50.1e-9, 70.1e-9]
    errs = [abs(r - t) for r, t in zip(rises[:4], targets)]
    max_err = max(errs) if errs else float("inf")
    ok = max_err <= 2.0e-9
    return ok, f"rises_ns={[round(v*1e9,3) for v in rises[:4]]} max_err_ns={max_err*1e9:.3f}"


def check_transition_branch_target(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "mode", "clk", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/mode/clk/out"
    w_low0 = [r["out"] for r in rows if 15e-9 <= r["time"] <= 22e-9]
    w_high1 = [r["out"] for r in rows if 35e-9 <= r["time"] <= 42e-9]
    w_high2 = [r["out"] for r in rows if 55e-9 <= r["time"] <= 62e-9]
    w_low3 = [r["out"] for r in rows if 75e-9 <= r["time"] <= 85e-9]
    if not (w_low0 and w_high1 and w_high2 and w_low3):
        return False, "insufficient_window_samples"
    m0 = sum(w_low0) / len(w_low0)
    m1 = sum(w_high1) / len(w_high1)
    m2 = sum(w_high2) / len(w_high2)
    m3 = sum(w_low3) / len(w_low3)
    span = max(m1, m2) - min(m0, m3)
    ok = (m1 - m0) > 0.35 * max(span, 1e-6) and (m2 - m3) > 0.35 * max(span, 1e-6)
    return ok, f"means=({m0:.3f},{m1:.3f},{m2:.3f},{m3:.3f})"


CHECKS = {
    # legacy short IDs (example-level names)
    "adc_dac_ideal_4b": check_adc_dac_ideal_4b,
    "clk_burst_gen": check_clk_burst_gen,
    "clk_div_smoke": check_clk_div,
    "clk_divider": check_clk_divider,
    "comparator_smoke": check_comparator,
    "dac_binary_clk_4b": check_dac_binary_clk_4b,
    "dac_therm_16b": check_dac_therm_16b,
    "digital_basics": check_not_gate,
    "dwa_ptr_gen": check_dwa_ptr_gen,
    "gain_extraction": check_gain_extraction,
    "lfsr": check_lfsr,
    "prbs7": check_prbs7,
    "therm2bin": check_therm2bin,
    "multimod_divider": check_multimod_divider,
    "bbpd": check_bbpd,
    "bad_bus_output_loop": check_bad_bus_output_loop,
    "missing_transition_outputs": check_missing_transition_outputs,
    "noise_gen": check_noise_gen,
    "sar_adc_dac_weighted_8b": check_sar_adc_dac_weighted_8b,
    # formal task IDs (tasks/end-to-end/voltage/)
    "adpll_lock_smoke": check_adpll_lock,
    "adpll_ratio_hop_smoke": check_adpll_ratio_hop,
    "adpll_timer_smoke": check_adpll_lock,
    "above_threshold_startup_smoke": check_above_threshold_startup,
    "and_gate_smoke": check_and_gate,
    "or_gate_smoke": check_or_gate,
    "not_gate_smoke": check_not_gate,
    "dff_rst_smoke": check_dff_rst,
    "bound_step_period_guard_smoke": check_bound_step_period_guard,
    "cross_hysteresis_window_smoke": check_cross_hysteresis_window,
    "cross_interval_163p333_smoke": check_cross_interval_163p333,
    "cross_sine_precision_smoke": check_cross_sine_precision,
    "differential_voltage_output_smoke": check_differential_voltage_output,
    "final_step_file_metric_smoke": check_final_step_file_metric,
    "parameter_type_override_smoke": check_parameter_type_override,
    "phase_accumulator_timer_wrap_smoke": check_phase_accumulator_timer_wrap,
    "simultaneous_event_order_smoke": check_simultaneous_event_order,
    "timer_absolute_grid_smoke": check_timer_absolute_grid,
    "transition_branch_target_smoke": check_transition_branch_target,
    "clk_div_smoke": check_clk_div,
    "cmp_delay_smoke": check_cmp_delay,
    "comparator_hysteresis_smoke": check_cmp_hysteresis,
    "comparator_offset_search_smoke": check_comparator_offset_search,
    "cmp_strongarm_smoke": check_cmp_strongarm,
    "comparator_smoke": check_comparator,
    "cppll_freq_step_reacquire_smoke": check_cppll_freq_step_reacquire,
    "cppll_tracking_smoke": check_cppll_tracking,
    "d2b_4bit_smoke": check_d2b,
    "ramp_gen_smoke": check_ramp_gen,
    "adc_dac_ideal_4b_smoke": check_adc_dac_ideal_4b,
    "clk_burst_gen_smoke": check_clk_burst_gen,
    "dac_binary_clk_4b_smoke": check_dac_binary_clk_4b,
    "dac_therm_16b_smoke": check_dac_therm_16b,
    "digital_basics_smoke": check_not_gate,
    "dwa_ptr_gen_smoke": check_dwa_ptr_gen,
    "dwa_ptr_gen_no_overlap_smoke": check_dwa_ptr_gen_no_overlap,
    "dwa_wraparound_smoke": check_dwa_wraparound,
    "bbpd_data_edge_alignment_smoke": check_bbpd_data_edge_alignment,
    "gain_extraction_smoke": check_gain_extraction,
    "lfsr_smoke": check_lfsr,
    "noise_gen_smoke": check_noise_gen,
    "sar_adc_dac_weighted_8b_smoke": check_sar_adc_dac_weighted_8b,
    "sample_hold_smoke": check_sample_hold,
    "sample_hold_droop_smoke": check_sample_hold_droop,
    "flash_adc_3b_smoke": check_flash_adc_3b,
    "serializer_8b_smoke": check_serializer_8b,
    "serializer_frame_alignment_smoke": check_serializer_frame_alignment,
    "xor_pd_smoke": check_xor_pd,
    "pfd_updn_smoke": check_pfd_updn,
    "pfd_deadzone_smoke": check_pfd_deadzone,
    "pfd_reset_race_smoke": check_pfd_reset_race,
    "gray_counter_one_bit_change_smoke": check_gray_counter_one_bit_change,
    "gray_counter_4b_smoke": check_gray_counter_4b,
    "multimod_divider_ratio_switch_smoke": check_multimod_divider_ratio_switch,
    "mux_4to1_smoke": check_mux_4to1,
    # spec-to-va task IDs
    "clk_divider":    check_clk_divider,
    "prbs7":          check_prbs7,
    "therm2bin":      check_therm2bin,
    "d2b_4bit":       check_d2b,
    "sar_logic":      check_sar_logic,
    "sar_logic_10b":  check_sar_logic,
    "pipeline_stage": check_pipeline_stage,
    "sar_12bit":      check_sar_12bit,
    "segmented_dac":  check_segmented_dac,
    "cdac_cal":       check_cdac_cal,
    "sc_integrator":  check_sc_integrator,
    "bg_cal":         check_bg_cal,
    "adpll_timer":    check_adpll_lock,
    "cppll_timer":    check_cppll_tracking,
    "multitone":      check_multitone,
    "nrz_prbs":       check_nrz_prbs,
    "mixed_domain_cdac_bug": check_mixed_domain_cdac_bug,
    "spectre_port_discipline": check_spectre_port_discipline,
    "strongarm_reset_priority_bug": check_strongarm_reset_priority_bug,
    "wrong_edge_sample_hold_bug": check_sample_hold,
    "inverted_comparator_logic_bug": check_inverted_comparator_logic_bug,
    "swapped_pfd_outputs_bug": check_pfd_updn,
    # benchmark-v2 perturbation tasks
    "gray_counter_4b_p1p2":       check_gray_counter_4b_v2,
    "clk_divider_p2p3p4":         check_clk_div,
    "clk_divider_p4p5p6":         check_clk_div,
    "xor_pd_p2p3p4":              check_xor_pd,
    "dff_rst_p2p5":               check_dff_rst,
    "comparator_p2p3p4":          check_comparator,
    "sample_hold_p2p3p4":         check_sample_hold,
    "lfsr_p2p3p4":                check_lfsr,
    "clk_burst_gen_p2p3p5":       check_clk_burst_gen,
    "pfd_updn_p2p3p4":            check_pfd_updn,
    "flash_adc_3b_p2p3p4":        check_flash_adc_3b,
    # batch 2+3 perturbation tasks
    "mux_4to1_p2p3p4":            check_mux_4to1,
    "pfd_deadzone_p2p3p4":        check_pfd_deadzone,
    "sample_hold_droop_p2p3p4":   check_sample_hold_droop,
    "dac_therm_16b_p2p3p4":       check_dac_therm_16b,
    "noise_gen_p2p3p4":           check_noise_gen,
    "serializer_8b_p2p3p4":       check_serializer_8b,
    # Route B - external architectures
    "vco_p2p3p4":                  check_vco,
    "charge_pump_p2p3p4":          check_charge_pump,
    "window_comparator_p2p3p4":    check_window_comparator,
}


def has_behavior_check(task_id: str) -> bool:
    return task_id in CHECKS


def evaluate_behavior(task_id: str, csv_path: Path) -> tuple[float, list[str]]:
    if task_id not in CHECKS:
        return 0.0, [f"no behavior check implemented for {task_id}"]
    if task_id in {"noise_gen", "noise_gen_smoke", "noise_gen_p2p3p4"}:
        return evaluate_noise_gen_csv(csv_path)
    streaming_result = evaluate_streaming_behavior(task_id, csv_path)
    if streaming_result is not None:
        return streaming_result
    rows = normalize_rows_for_task(task_id, load_csv(csv_path))
    ok, note = CHECKS[task_id](rows)
    return (1.0 if ok else 0.0), [note]


def _behavior_eval_worker(task_id: str, csv_path: str, queue: mp.Queue) -> None:
    """Run checker evaluation in a child process so large CSVs cannot hang scoring."""
    try:
        queue.put(("ok", evaluate_behavior(task_id, Path(csv_path))))
    except Exception as exc:  # pragma: no cover - defensive worker boundary
        queue.put(("error", f"{type(exc).__name__}: {str(exc)[:300]}"))


def evaluate_behavior_with_timeout(
    task_id: str,
    csv_path: Path,
    *,
    timeout_s: int,
) -> tuple[float, list[str]]:
    """Evaluate behavior with a watchdog separate from EVAS simulation timeout.

    `evas simulate` can finish successfully while producing a very large CSV.
    Without a second timeout, Python-side checker parsing can block an entire
    full92 matrix run. Keep this timeout shorter than simulation timeout so one
    pathological waveform becomes a normal task failure instead of a matrix hang.
    """
    eval_timeout_s = max(10, min(60, max(1, timeout_s // 3)))
    ctx = mp.get_context("spawn")
    queue: mp.Queue = ctx.Queue(maxsize=1)
    proc = ctx.Process(
        target=_behavior_eval_worker,
        args=(task_id, str(csv_path), queue),
    )
    proc.start()
    proc.join(eval_timeout_s)
    if proc.is_alive():
        proc.terminate()
        proc.join(5)
        if proc.is_alive():
            proc.kill()
            proc.join(5)
        return 0.0, [f"behavior_eval_timeout>{eval_timeout_s}s"]
    if queue.empty():
        return 0.0, ["behavior_eval_no_result"]
    status, payload = queue.get()
    if status == "ok":
        return payload
    return 0.0, [f"behavior_eval_error={payload}"]


def _duration_to_seconds(value: str, unit: str) -> float:
    number = float(value)
    normalized = unit.lower()
    if normalized == "ms":
        return number / 1000.0
    if normalized in {"us", "µs"}:
        return number / 1_000_000.0
    if normalized == "ns":
        return number / 1_000_000_000.0
    return number


def parse_evas_timing(text: str) -> dict[str, float]:
    timing: dict[str, float] = {}
    tran_match = re.search(
        r"Tran analysis time:\s*CPU\s*=\s*[\d.]+\s*\w+,\s*elapsed\s*=\s*([\d.]+)\s*(ns|us|µs|ms|s)",
        text,
        re.IGNORECASE,
    )
    total_match = re.search(
        r"Total time:\s*CPU\s*=\s*[\d.]+\s*\w+,\s*elapsed\s*=\s*([\d.]+)\s*(ns|us|µs|ms|s)",
        text,
        re.IGNORECASE,
    )
    steps_match = re.search(r"Number of accepted tran steps\s*=\s*([0-9]+)", text)
    if tran_match:
        timing["tran_elapsed_s"] = _duration_to_seconds(tran_match.group(1), tran_match.group(2))
    if total_match:
        timing["total_elapsed_s"] = _duration_to_seconds(total_match.group(1), total_match.group(2))
    if steps_match:
        timing["accepted_tran_steps"] = float(steps_match.group(1))
    return timing


def run_case(
    task_dir: Path,
    dut_path: Path,
    tb_path: Path,
    *,
    output_root: Path | None = None,
    keep_run_dir: bool = False,
    timeout_s: int = 120,
    task_id_override: str | None = None,
) -> dict:
    meta = read_meta(task_dir)
    task_id = task_id_override or meta.get("id") or meta.get("task_id") or task_dir.name
    scoring = set(meta.get("scoring", ["dut_compile", "tb_compile", "sim_correct"]))

    temp_ctx = tempfile.TemporaryDirectory(prefix=f"{task_id}_")
    try:
        run_dir = Path(temp_ctx.name)
        out_dir = output_root.resolve() if output_root else run_dir / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        dut_dst, tb_dst = copy_inputs(run_dir, dut_path, tb_path)
        proc = run_evas(run_dir, tb_dst, out_dir, timeout_s)
        combined = (proc.stdout or "") + "\n" + (proc.stderr or "")

        dut_compile = 1.0 if "Compiled Verilog-A module:" in combined else 0.0
        tb_compile = 1.0 if ("Transient Analysis" in combined or (out_dir / "tran.csv").exists()) else 0.0

        notes = [f"returncode={proc.returncode}"]
        if dut_compile == 0.0:
            notes.append("dut_not_compiled")
        if tb_compile == 0.0:
            notes.append("tb_not_executed")

        csv_path = out_dir / "tran.csv"
        if "sim_correct" in scoring and proc.returncode == 0 and csv_path.exists():
            sim_correct, behavior_notes = evaluate_behavior_with_timeout(
                task_id,
                csv_path,
                timeout_s=timeout_s,
            )
            notes.extend(behavior_notes)
        elif "sim_correct" in scoring:
            sim_correct = 0.0
            notes.append("tran.csv missing")
        else:
            sim_correct = 1.0
            notes.append("sim_correct not required by scoring")

        required_axes: list[tuple[str, float]] = []
        if "dut_compile" in scoring or "syntax" in scoring:
            required_axes.append(("dut_compile", dut_compile))
        if "tb_compile" in scoring or "routing" in scoring or "simulation" in scoring:
            required_axes.append(("tb_compile", tb_compile))
        if "sim_correct" in scoring:
            required_axes.append(("sim_correct", sim_correct))

        if required_axes:
            weighted_total = round(sum(score for _, score in required_axes) / len(required_axes), 4)
        else:
            weighted_total = round((dut_compile + tb_compile + sim_correct) / 3.0, 4)

        if ("dut_compile" in scoring or "syntax" in scoring) and dut_compile < 1.0:
            status = "FAIL_DUT_COMPILE"
        elif ("tb_compile" in scoring or "routing" in scoring or "simulation" in scoring) and tb_compile < 1.0:
            status = "FAIL_TB_COMPILE"
        elif "sim_correct" in scoring and sim_correct < 1.0:
            status = "FAIL_SIM_CORRECTNESS"
        else:
            status = "PASS"

        return {
            "task_id": task_id,
            "status": status,
            "backend_used": "evas",
            "scores": {
                "dut_compile": dut_compile,
                "tb_compile": tb_compile,
                "sim_correct": sim_correct,
                "weighted_total": weighted_total,
            },
            "artifacts": [
                str(dut_dst),
                str(tb_dst),
                str(out_dir / "tran.csv"),
                str(out_dir / "strobe.txt"),
            ],
            "notes": notes,
            "timing": parse_evas_timing(combined),
            "stdout_tail": combined[-4000:],
        }
    finally:
        if not keep_run_dir:
            temp_ctx.cleanup()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("task_dir")
    ap.add_argument("dut")
    ap.add_argument("tb")
    ap.add_argument("--output-root", default=None)
    ap.add_argument("--keep-run-dir", action="store_true")
    ap.add_argument("--timeout-s", type=int, default=120)
    ap.add_argument("--task-id", default=None)
    args = ap.parse_args()

    task_dir = Path(args.task_dir).resolve()
    dut_path = Path(args.dut).resolve()
    tb_path = Path(args.tb).resolve()
    output_root = Path(args.output_root).resolve() if args.output_root else None
    result = run_case(
        task_dir,
        dut_path,
        tb_path,
        output_root=output_root,
        keep_run_dir=args.keep_run_dir,
        timeout_s=args.timeout_s,
        task_id_override=args.task_id,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
