#!/usr/bin/env python3
"""Classify EVAS failures into mechanism-level H-template families."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


FAMILY_ORDER = [
    "counter_cadence/off-by-one",
    "sampled_latch/reset_priority",
    "quantizer/code_coverage",
    "onehot/thermometer/no-overlap",
    "frame/sequence_alignment",
    "PFD/PLL timing_window",
    "multi-module interface sanity",
    "compile/preflight",
    "unsupported/behavior_other",
    "pass",
]


def notes_text(result: dict) -> str:
    notes = result.get("evas_notes") or result.get("notes") or []
    if isinstance(notes, str):
        return notes
    return "\n".join(str(note) for note in notes)


def classify(result: dict) -> tuple[str, str]:
    status = result.get("status", "")
    notes = notes_text(result)
    lowered = notes.lower()
    if status == "PASS":
        return "pass", "already_pass"
    strict_failure = "spectre_strict:" in lowered and "spectre_strict:preflight_pass" not in lowered
    if status in {"FAIL_DUT_COMPILE", "FAIL_TB_COMPILE"} or strict_failure:
        return "compile/preflight", "compile_or_spectre_strict"
    if "tran.csv missing" in lowered or "missing_generated" in lowered or "module" in lowered and "missing" in lowered:
        return "multi-module interface sanity", "missing_csv_or_missing_generated_artifact"
    if "ratio_code=" in notes and "interval_hist=" in notes:
        return "counter_cadence/off-by-one", "ratio_interval_hist"
    if "base=" in notes and "pre_count=" in notes and "post_count=" in notes:
        return "counter_cadence/off-by-one", "base_pre_post_count"
    if "q_mismatch" in lowered or "wrong_edge" in lowered or "sample" in lowered and "mismatch" in lowered:
        return "sampled_latch/reset_priority", "sample_or_q_mismatch"
    if re.search(r"only_[0-9]+_codes", lowered) or "codes=" in lowered or "unique_codes" in lowered:
        return "quantizer/code_coverage", "code_coverage_or_unique_codes"
    if "reversal" in lowered or "monotonic" in lowered:
        return "quantizer/code_coverage", "monotonic_or_reversal"
    if "overlap" in lowered or "ptr_" in lowered or "cell_en" in lowered or "therm" in lowered:
        return "onehot/thermometer/no-overlap", "onehot_overlap_or_pointer"
    if "frame" in lowered or "sequence" in lowered or "prbs" in lowered or "lfsr" in lowered:
        return "frame/sequence_alignment", "frame_or_sequence"
    if (
        "up_frac" in lowered
        or "dn_frac" in lowered
        or "pulse" in lowered
        or "lock" in lowered
        or "freq_ratio" in lowered
        or "reacquire" in lowered
        or "phase" in lowered
    ):
        return "PFD/PLL timing_window", "pulse_phase_lock_window"
    if "behavior_eval_timeout" in lowered:
        return "unsupported/behavior_other", "checker_timeout_no_specific_signature"
    return "unsupported/behavior_other", "no_supported_signature"


def collect(result_root: Path) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(result_root.glob("*/result.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        family, reason = classify(result)
        timing = result.get("evas_timing") or {}
        rows.append(
            {
                "task_id": path.parent.name,
                "status": result.get("status"),
                "benchmark_family": result.get("family", ""),
                "h_family": family,
                "reason": reason,
                "total_elapsed_s": timing.get("total_elapsed_s"),
                "notes": notes_text(result),
            }
        )
    return rows


def write_markdown(path: Path, result_root: Path, rows: list[dict]) -> None:
    counts = {family: 0 for family in FAMILY_ORDER}
    for row in rows:
        counts[row["h_family"]] = counts.get(row["h_family"], 0) + 1
    lines = [
        f"# H Failure Taxonomy: `{result_root}`",
        "",
        "## Counts",
        "",
        "| family | count |",
        "|---|---:|",
    ]
    for family in FAMILY_ORDER:
        if counts.get(family, 0):
            lines.append(f"| `{family}` | {counts[family]} |")
    lines.extend(["", "## Failed Tasks", "", "| task | H family | reason | status | notes |", "|---|---|---|---|---|"])
    for row in rows:
        if row["h_family"] == "pass":
            continue
        notes = row["notes"].replace("|", "\\|")[:180]
        lines.append(
            f"| `{row['task_id']}` | `{row['h_family']}` | `{row['reason']}` | `{row['status']}` | {notes} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify result failures into H mechanism families.")
    parser.add_argument("result_root")
    parser.add_argument("--output-md", default="")
    parser.add_argument("--output-json", default="")
    args = parser.parse_args()

    result_root = Path(args.result_root).resolve()
    rows = collect(result_root)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["h_family"]] = counts.get(row["h_family"], 0) + 1
    payload = {"result_root": str(result_root), "counts": counts, "rows": rows}
    output_json = Path(args.output_json) if args.output_json else result_root / "h_failure_taxonomy.json"
    output_md = Path(args.output_md) if args.output_md else result_root / "h_failure_taxonomy.md"
    output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    write_markdown(output_md, result_root, rows)
    print(f"[h-taxonomy] wrote {output_md}")
    print(f"[h-taxonomy] wrote {output_json}")
    print(json.dumps(counts, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
