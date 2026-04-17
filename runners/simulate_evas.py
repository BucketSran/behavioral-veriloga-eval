#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import tempfile
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


def rising_edges(values: list[float], times: list[float], threshold: float = 0.45) -> list[float]:
    edges: list[float] = []
    for i in range(1, len(values)):
        if values[i - 1] < threshold <= values[i]:
            edges.append(times[i])
    return edges


def decode_bus(rows: list[dict[str, float]], bit_names: list[str], threshold: float = 0.45) -> list[int]:
    decoded: list[int] = []
    for row in rows:
        code = 0
        for bit_name in bit_names:
            bit = 1 if row[bit_name] >= threshold else 0
            m = re.search(r"(\d+)$", bit_name)
            idx = int(m.group(1)) if m else 0
            code |= bit << idx
        decoded.append(code)
    return decoded


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
    dout_bits = [k for k in rows[0] if re.fullmatch(r"DOUT[_\[]?\d+\]?", k)]
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

    for row in rows:
        code_vec = []
        dout_vec = []
        for idx in bit_indices:
            code_bit = 1 if row[code_cols[idx]] > 0.45 else 0
            dout_bit = 1 if row[dout_cols[idx]] > 0.45 else 0
            code_vec.append(code_bit)
            dout_vec.append(dout_bit)
            total += 1
            if code_bit != dout_bit:
                mismatch += 1
        code_tuple = tuple(code_vec)
        dout_tuple = tuple(dout_vec)
        code_patterns.add(code_tuple)
        dout_patterns.add(dout_tuple)
        if len(set(dout_tuple)) == 1:
            uniform_rows += 1

    mismatch_frac = mismatch / max(total, 1)
    uniform_frac = uniform_rows / max(len(rows), 1)
    ok = mismatch_frac < 0.05 and len(code_patterns) >= 6 and len(dout_patterns) >= 6 and uniform_frac < 0.8
    return ok, f"mismatch_frac={mismatch_frac:.4f} code_patterns={len(code_patterns)} dout_patterns={len(dout_patterns)} uniform_frac={uniform_frac:.3f}"


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
    stable_indices = [i for i, vin in enumerate(vins) if abs(vin - threshold) > margin]
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
    # find LOAD falling edge
    load_fall = next((i for i in range(1, len(load)) if load[i - 1] > vth > load[i]), None)
    if load_fall is None:
        return False, "LOAD never deasserted"
    expected = [1, 0, 1, 0, 0, 1, 0, 1]  # 0xA5 MSB-first
    load_fall_t = rows[load_fall]["time"]
    # collect CLK rising edges strictly after LOAD falls
    edges = [
        i for i in range(max(1, load_fall), len(clk))
        if clk[i - 1] <= vth < clk[i] and rows[i]["time"] > load_fall_t + 1e-15
    ]
    if len(edges) < 7:
        return False, f"only_{len(edges)}_edges_after_load"

    edge_bits = [int(sout[min(e + 3, len(sout) - 1)] > vth) for e in edges[:8]]
    if len(edge_bits) < 8:
        return False, f"only_{len(edge_bits)}_sampled_bits"
    mismatches = sum(1 for a, b in zip(edge_bits, expected) if a != b)
    if mismatches > 1:
        return False, f"bit_mismatch expected={expected} got={edge_bits}"
    return True, f"0xA5_serialized_ok mode=edge_only mismatches={mismatches}"


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


def check_pfd_updn(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"ref", "div", "up", "dn"}.issubset(rows[0]):
        return False, "missing ref/div/up/dn"
    vth = max(r["ref"] for r in rows) * 0.5
    up = [1 if r["up"] > vth else 0 for r in rows]
    dn = [1 if r["dn"] > vth else 0 for r in rows]
    up_frac = sum(up) / len(up)
    dn_frac = sum(dn) / len(dn)
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


def check_clk_divider(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """Programmable clock divider: check output/input edge ratio ≈ div_ratio and LOCK asserts."""
    if not rows or "clk_in" not in rows[0] or "clk_out" not in rows[0]:
        return False, "missing clk_in/clk_out"
    times = [r["time"] for r in rows]
    in_edges  = rising_edges([r["clk_in"]  for r in rows], times)
    out_edges = rising_edges([r["clk_out"] for r in rows], times)
    if len(in_edges) < 6 or len(out_edges) < 2:
        return False, f"not_enough_edges in={len(in_edges)} out={len(out_edges)}"
    ratio = len(in_edges) / max(len(out_edges), 1)
    lock_ok = True
    if "lock" in rows[0]:
        t_end = times[-1]
        lock_late = [r["lock"] for r in rows if r["time"] > t_end * 0.5]
        lock_ok = bool(lock_late) and any(v > 0.45 for v in lock_late)
    ok = 2.0 <= ratio <= 8.0 and lock_ok
    return ok, f"edge_ratio={ratio:.2f} lock_ok={lock_ok}"


def check_prbs7(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """PRBS-7: check serial output has many transitions and ~50% high fraction."""
    if not rows:
        return False, "empty"
    serial_col = next((k for k in rows[0] if k.lower() in {"prbs_out", "serial", "dout", "q_out", "q"}), None)
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
    b_cols = [k for k in rows[0] if k.lower() in {"b3", "b2", "b1", "b0"}]
    if len(b_cols) < 4:
        return False, f"missing b3..b0; got {list(rows[0].keys())[:12]}"
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
    "clk_div_smoke": check_clk_div,
    "comparator_smoke": check_comparator,
    "d2b_4bit_smoke": check_d2b,
    "ramp_gen_smoke": check_ramp_gen,
    "adc_dac_ideal_4b_smoke": check_adc_dac_ideal_4b,
    "clk_burst_gen_smoke": check_clk_burst_gen,
    "dac_binary_clk_4b_smoke": check_dac_binary_clk_4b,
    "dac_therm_16b_smoke": check_dac_therm_16b,
    "digital_basics_smoke": check_not_gate,
    "dwa_ptr_gen_smoke": check_dwa_ptr_gen,
    "gain_extraction_smoke": check_gain_extraction,
    "lfsr_smoke": check_lfsr,
    "noise_gen_smoke": check_noise_gen,
    "sar_adc_dac_weighted_8b_smoke": check_sar_adc_dac_weighted_8b,
    "sample_hold_smoke": check_sample_hold,
    "flash_adc_3b_smoke": check_flash_adc_3b,
    "serializer_8b_smoke": check_serializer_8b,
    "xor_pd_smoke": check_xor_pd,
    "pfd_updn_smoke": check_pfd_updn,
    "gray_counter_4b_smoke": check_gray_counter_4b,
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
}


def has_behavior_check(task_id: str) -> bool:
    return task_id in CHECKS


def evaluate_behavior(task_id: str, csv_path: Path) -> tuple[float, list[str]]:
    if task_id not in CHECKS:
        return 0.0, [f"no behavior check implemented for {task_id}"]
    rows = load_csv(csv_path)
    ok, note = CHECKS[task_id](rows)
    return (1.0 if ok else 0.0), [note]


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

    temp_ctx = tempfile.TemporaryDirectory(prefix=f"{task_id}_")
    run_dir = Path(temp_ctx.name)
    out_dir = output_root.resolve() if output_root else run_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
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
        if proc.returncode == 0 and csv_path.exists():
            sim_correct, behavior_notes = evaluate_behavior(task_id, csv_path)
            notes.extend(behavior_notes)
        else:
            sim_correct = 0.0
            notes.append("tran.csv missing")

        weighted_total = round((dut_compile + tb_compile + sim_correct) / 3.0, 4)

        if dut_compile < 1.0:
            status = "FAIL_DUT_COMPILE"
        elif tb_compile < 1.0:
            status = "FAIL_TB_COMPILE"
        elif sim_correct < 1.0:
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
