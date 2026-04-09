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
    if not rows or not {"vin", "vout", "dout_code", "rst_n"}.issubset(rows[0]):
        return False, "missing vin/vout/dout_code/rst_n"
    post = [r for r in rows if r["rst_n"] > 0.45]
    if not post:
        return False, "no post-reset samples"
    codes = [int(round(r["dout_code"])) for r in post]
    vouts = [r["vout"] for r in post]
    unique_codes = len(set(codes))
    monotonic = all(codes[i] <= codes[i + 1] for i in range(len(codes) - 1))
    span = max(vouts) - min(vouts)
    ok = unique_codes >= 8 and monotonic and span > 0.5
    return ok, f"unique_codes={unique_codes} vout_span={span:.3f}"


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
    if not rows or not {"vin", "vin_sh", "vout", "dout_code", "rst_n"}.issubset(rows[0]):
        return False, "missing vin/vin_sh/vout/dout_code/rst_n"
    post = [r for r in rows if r["rst_n"] > 0.45]
    if not post:
        return False, "no post-reset samples"
    codes = [int(round(r["dout_code"])) for r in post]
    vinsh = [r["vin_sh"] for r in post]
    vouts = [r["vout"] for r in post]
    unique_codes = len(set(codes))
    avg_abs_err = sum(abs(a - b) for a, b in zip(vinsh, vouts)) / len(post)
    ok = unique_codes >= 64 and max(vouts) - min(vouts) > 0.5 and avg_abs_err < 0.12
    return ok, f"unique_codes={unique_codes} avg_abs_err={avg_abs_err:.4f}"


def check_not_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"a", "y"}.issubset(rows[0]):
        return False, "missing a/y"
    good = 0
    for r in rows:
        if (r["a"] > 0.4) != (r["y"] > 0.4):
            good += 1
    frac = good / len(rows)
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
    if not rows or not {"clk_i", "rst_ni", "cell_en_code", "ptr_code"}.issubset(rows[0]):
        return False, "missing clk_i/rst_ni/cell_en_code/ptr_code"
    post = [r for r in rows if r["rst_ni"] > 0.45]
    if not post:
        return False, "no post-reset samples"
    ptr_codes = [int(round(r["ptr_code"])) for r in post]
    cell_codes = [int(round(r["cell_en_code"])) for r in post]
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


CHECKS = {
    "adc_dac_ideal_4b": check_adc_dac_ideal_4b,
    "clk_burst_gen": check_clk_burst_gen,
    "clk_div_smoke": check_clk_div,
    "clk_divider": check_clk_divider,
    "comparator_smoke": check_comparator,
    "dac_binary_clk_4b": check_dac_binary_clk_4b,
    "dac_therm_16b": check_dac_therm_16b,
    "ramp_gen_smoke": check_ramp_gen,
    "d2b_4bit_smoke": check_d2b,
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
    task_id = task_id_override or meta["id"]

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
