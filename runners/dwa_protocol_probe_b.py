#!/usr/bin/env python3
"""Terminal B standalone DWA protocol probe.

This probe does not change official scoring. It checks a protocol gap that can
be missed by activity-only contracts: whether consecutive post-reset DWA
selection windows reuse enabled cells.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


CELL_BITS = [f"cell_en_{idx}" for idx in range(16)]
PTR_BITS = [f"ptr_{idx}" for idx in range(16)]


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


def _rising_edge_indices(rows: list[dict[str, float]], signal: str, threshold: float) -> list[int]:
    edges: list[int] = []
    for idx in range(1, len(rows)):
        if signal not in rows[idx - 1] or signal not in rows[idx]:
            continue
        if rows[idx - 1][signal] < threshold <= rows[idx][signal]:
            edges.append(idx)
    return edges


def _active_set(row: dict[str, float], bits: list[str], threshold: float) -> set[int]:
    return {idx for idx, bit in enumerate(bits) if row.get(bit, 0.0) >= threshold}


def analyze(csv_path: Path, threshold: float, sample_offset_rows: int) -> dict:
    fields, rows = _load_rows(csv_path)
    missing = [
        field
        for field in ["time", "clk_i", "rst_ni", *CELL_BITS, *PTR_BITS]
        if field not in fields
    ]

    sampled: list[dict] = []
    for edge_idx in _rising_edge_indices(rows, "clk_i", threshold):
        sample_idx = min(edge_idx + sample_offset_rows, len(rows) - 1)
        row = rows[sample_idx]
        if row.get("rst_ni", 0.0) < threshold:
            continue
        cell_set = _active_set(row, CELL_BITS, threshold)
        ptr_set = _active_set(row, PTR_BITS, threshold)
        sampled.append(
            {
                "idx": sample_idx,
                "time": row.get("time", 0.0),
                "cell_set": sorted(cell_set),
                "ptr_set": sorted(ptr_set),
                "cell_active_count": len(cell_set),
                "ptr_active_count": len(ptr_set),
            }
        )

    overlap_count = 0
    overlap_examples: list[dict] = []
    for prev, cur in zip(sampled, sampled[1:]):
        overlap = sorted(set(prev["cell_set"]) & set(cur["cell_set"]))
        if overlap:
            overlap_count += 1
            if len(overlap_examples) < 5:
                overlap_examples.append(
                    {
                        "prev_time": prev["time"],
                        "cur_time": cur["time"],
                        "overlap": overlap,
                        "prev_cell_set": prev["cell_set"],
                        "cur_cell_set": cur["cell_set"],
                    }
                )

    bad_ptr_rows = [
        item
        for item in sampled
        if item["ptr_active_count"] not in {0, 1}
    ]
    active_rows = [item for item in sampled if item["cell_active_count"] > 0]
    max_active = max((item["cell_active_count"] for item in sampled), default=0)
    min_active_nonzero = min((item["cell_active_count"] for item in active_rows), default=0)

    checks = {
        "post_reset_samples_present": len(sampled) >= 8,
        "cell_activity_present": len(active_rows) >= 4,
        "ptr_onehot_or_reset": not bad_ptr_rows,
        "consecutive_no_overlap": overlap_count == 0 and len(sampled) >= 2,
    }

    return {
        "probe": "dwa_protocol_probe_b",
        "csv_path": str(csv_path),
        "missing_fields": missing,
        "threshold": threshold,
        "sample_offset_rows": sample_offset_rows,
        "metrics": {
            "sampled_cycles": len(sampled),
            "active_rows": len(active_rows),
            "max_active_cells": max_active,
            "min_active_cells_nonzero": min_active_nonzero,
            "bad_ptr_rows": len(bad_ptr_rows),
            "overlap_count": overlap_count,
        },
        "overlap_examples": overlap_examples,
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "diagnostic_hint": "DWA must keep cell_en active and pointer one-hot, while preventing overlap between consecutive selected cell sets.",
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
