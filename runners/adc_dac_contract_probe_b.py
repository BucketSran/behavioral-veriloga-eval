#!/usr/bin/env python3
"""Terminal B standalone ADC-DAC semantic probe.

This probe is intentionally B-owned and does not change official scoring or
shared checker semantics. It measures the semantic gaps that the current
generic contract runner cannot yet express directly:

1. decoded ADC code coverage and monotonicity versus vin;
2. DAC reconstruction span and correlation with decoded code;
3. sampled code behavior shortly after clk rising edges.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


BITS_MSB_TO_LSB = ["dout_3", "dout_2", "dout_1", "dout_0"]


def _load_rows(path: Path) -> tuple[list[str], list[dict[str, float]]]:
    rows: list[dict[str, float]] = []
    with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        for raw in reader:
            row: dict[str, float] = {}
            for key, value in raw.items():
                if key is None:
                    continue
                try:
                    row[key] = float(value)
                except (TypeError, ValueError):
                    pass
            rows.append(row)
    return fields, rows


def _span(values: list[float]) -> float | None:
    if not values:
        return None
    return max(values) - min(values)


def _decode(row: dict[str, float], threshold: float) -> int | None:
    if not all(bit in row for bit in BITS_MSB_TO_LSB):
        return None
    code = 0
    for bit in BITS_MSB_TO_LSB:
        code = (code << 1) | int(row[bit] >= threshold)
    return code


def _post_reset_rows(rows: list[dict[str, float]], threshold: float) -> list[dict[str, float]]:
    if not rows or "rst_n" not in rows[0]:
        return rows
    return [row for row in rows if row.get("rst_n", 0.0) >= threshold]


def _rising_edge_indices(rows: list[dict[str, float]], signal: str, threshold: float) -> list[int]:
    edges: list[int] = []
    for idx in range(1, len(rows)):
        if signal not in rows[idx - 1] or signal not in rows[idx]:
            continue
        if rows[idx - 1][signal] < threshold <= rows[idx][signal]:
            edges.append(idx)
    return edges


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    dx = [x - mean_x for x in xs]
    dy = [y - mean_y for y in ys]
    var_x = sum(x * x for x in dx)
    var_y = sum(y * y for y in dy)
    if var_x <= 0.0 or var_y <= 0.0:
        return None
    return sum(x * y for x, y in zip(dx, dy)) / math.sqrt(var_x * var_y)


def analyze(csv_path: Path, threshold: float, sample_offset_rows: int) -> dict:
    fields, rows = _load_rows(csv_path)
    post_rows = _post_reset_rows(rows, threshold)

    decoded_pairs: list[tuple[float, int, float]] = []
    for row in post_rows:
        if "vin" not in row or "vout" not in row:
            continue
        code = _decode(row, threshold)
        if code is None:
            continue
        decoded_pairs.append((row["vin"], code, row["vout"]))

    vins = [item[0] for item in decoded_pairs]
    codes = [item[1] for item in decoded_pairs]
    vouts = [item[2] for item in decoded_pairs]

    monotonic_comparisons = 0
    reversals = 0
    for (prev_vin, prev_code, _prev_vout), (cur_vin, cur_code, _cur_vout) in zip(decoded_pairs, decoded_pairs[1:]):
        if cur_vin <= prev_vin + 1e-12:
            continue
        monotonic_comparisons += 1
        if cur_code + 1 < prev_code:
            reversals += 1
    reversal_fraction = None
    if monotonic_comparisons:
        reversal_fraction = reversals / monotonic_comparisons

    edge_codes: list[int] = []
    clk_edges = _rising_edge_indices(post_rows, "clk", threshold) if post_rows else []
    for edge_idx in clk_edges:
        sample_idx = min(edge_idx + sample_offset_rows, len(post_rows) - 1)
        code = _decode(post_rows[sample_idx], threshold)
        if code is not None:
            edge_codes.append(code)

    unique_codes = len(set(codes))
    unique_edge_codes = len(set(edge_codes))
    vin_span = _span(vins)
    vout_span = _span(vouts)
    code_vin_corr = _pearson([float(v) for v in vins], [float(c) for c in codes])
    vout_code_corr = _pearson([float(c) for c in codes], [float(v) for v in vouts])

    checks = {
        "monotonic_code_vs_input": bool(
            unique_codes >= 14
            and reversal_fraction is not None
            and reversal_fraction <= 0.02
            and (code_vin_corr is None or code_vin_corr >= 0.8)
        ),
        "quantized_reconstruction_span": bool(
            vout_span is not None
            and vout_span >= 0.6
            and unique_codes >= 14
            and (vout_code_corr is None or vout_code_corr >= 0.75)
        ),
        "sampled_code_after_clk_edge": bool(unique_edge_codes >= 10),
    }

    return {
        "probe": "adc_dac_contract_probe_b",
        "csv_path": str(csv_path),
        "required_fields": ["time", "vin", "clk", "rst_n", "vout", *BITS_MSB_TO_LSB],
        "missing_fields": [field for field in ["time", "vin", "clk", "rst_n", "vout", *BITS_MSB_TO_LSB] if field not in fields],
        "threshold": threshold,
        "sample_offset_rows": sample_offset_rows,
        "row_count": len(rows),
        "post_reset_row_count": len(post_rows),
        "metrics": {
            "vin_span": vin_span,
            "vout_span": vout_span,
            "unique_codes": unique_codes,
            "unique_edge_sampled_codes": unique_edge_codes,
            "clk_rising_edges_post_reset": len(clk_edges),
            "monotonic_comparisons": monotonic_comparisons,
            "code_reversals": reversals,
            "code_reversal_fraction": reversal_fraction,
            "code_vin_corr": code_vin_corr,
            "vout_code_corr": vout_code_corr,
            "min_code": min(codes) if codes else None,
            "max_code": max(codes) if codes else None,
            "min_edge_sampled_code": min(edge_codes) if edge_codes else None,
            "max_edge_sampled_code": max(edge_codes) if edge_codes else None
        },
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "diagnostic_hint": (
            "If vin/clk are active but unique_codes or vout_span are low, repair the ADC-DAC chain "
            "as sampled vin -> held integer code -> dout bits -> quantized vout reconstruction."
        )
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--threshold", type=float, default=0.45)
    parser.add_argument("--sample-offset-rows", type=int, default=2)
    args = parser.parse_args()

    report = analyze(args.csv, args.threshold, args.sample_offset_rows)
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
