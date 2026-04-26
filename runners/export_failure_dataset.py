#!/usr/bin/env python3
"""Export current formal failures as a repair-oriented dataset.

The normal score output is optimized for Pass@1 accounting.  For H2-style
layered repair we need a second view: which failures look like DUT behavior,
generated-testbench stimulus, harness/observable/runtime, scoring-contract
aliasing, or mixed/complex-system issues.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _notes(result: dict[str, Any]) -> list[str]:
    raw = result.get("evas_notes") or result.get("notes") or []
    if isinstance(raw, str):
        return [raw]
    return [str(item) for item in raw]


def _notes_text(result: dict[str, Any]) -> str:
    return "\n".join(_notes(result))


def _rel(path: str | None) -> str:
    if not path:
        return ""
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT))
    except Exception:
        return path


def _strict_pass_at_1(result: dict[str, Any]) -> bool:
    scores = result.get("scores") or {}
    required = result.get("required_axes") or ["dut_compile", "tb_compile", "sim_correct"]
    return all(float(scores.get(axis, 0.0)) >= 1.0 for axis in required)


def _has_legacy_axis_alias_failure(result: dict[str, Any]) -> bool:
    if result.get("status") != "PASS":
        return False
    scores = result.get("scores") or {}
    if not all(float(scores.get(axis, 0.0)) >= 1.0 for axis in ("dut_compile", "tb_compile", "sim_correct")):
        return False
    required = set(result.get("required_axes") or [])
    legacy_axes = {"syntax", "routing", "simulation", "behavior"}
    return bool(required & legacy_axes)


def _first_matching_note(result: dict[str, Any], patterns: list[str]) -> str:
    text = _notes_text(result)
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return match.group(0)
    notes = _notes(result)
    return notes[-1] if notes else ""


def _classify(result: dict[str, Any]) -> dict[str, str]:
    status = str(result.get("status") or "")
    scores = result.get("scores") or {}
    text = _notes_text(result)
    low = text.lower()

    if _has_legacy_axis_alias_failure(result):
        return {
            "suspected_layer": "scoring_contract",
            "repair_scope": "score-axis-alias-only",
            "mechanism_family": "scoring_axis_alias",
            "failure_signature": "status_PASS_but_required_axes_use_legacy_names",
            "confidence": "high",
        }

    if "missing_generated_files: testbench.scs" in low:
        return {
            "suspected_layer": "harness_artifact",
            "repair_scope": "tb-or-artifact-only",
            "mechanism_family": "missing_generated_testbench",
            "failure_signature": "missing_generated_files:testbench.scs",
            "confidence": "high",
        }

    if float(scores.get("dut_compile", 1.0)) < 1.0 or status == "FAIL_DUT_COMPILE":
        return {
            "suspected_layer": "dut",
            "repair_scope": "dut-only",
            "mechanism_family": "dut_compile",
            "failure_signature": _first_matching_note(result, [r"FAIL_DUT_COMPILE", r"spectre_strict:[^\n]+"]),
            "confidence": "high",
        }

    if float(scores.get("tb_compile", 1.0)) < 1.0 or status == "FAIL_TB_COMPILE":
        return {
            "suspected_layer": "tb_or_harness",
            "repair_scope": "tb-or-harness-only",
            "mechanism_family": "tb_compile",
            "failure_signature": _first_matching_note(result, [r"FAIL_TB_COMPILE", r"spectre_strict:[^\n]+"]),
            "confidence": "high",
        }

    if "tran.csv missing" in low or "returncode=1" in low:
        return {
            "suspected_layer": "harness_runtime",
            "repair_scope": "harness-first",
            "mechanism_family": "csv_missing_or_runtime",
            "failure_signature": _first_matching_note(result, [r"tran\.csv missing", r"returncode=1"]),
            "confidence": "medium",
        }

    if "behavior_eval_timeout" in low:
        return {
            "suspected_layer": "checker_runtime_or_complex_behavior",
            "repair_scope": "diagnose-before-repair",
            "mechanism_family": "checker_timeout",
            "failure_signature": _first_matching_note(result, [r"behavior_eval_timeout>[^\n]+"]),
            "confidence": "medium",
        }

    # Generated input/stimulus is likely not exercising the circuit.  These
    # signatures need a TB/gold-harness cross-check before blaming the DUT.
    if re.search(r"\btoo_few_(?:rising_)?edges=0\b", low) or re.search(r"\bnot_enough_clk_edges=0\b", low):
        return {
            "suspected_layer": "tb_stimulus_or_observable",
            "repair_scope": "tb-first-then-dut",
            "mechanism_family": "missing_clock_or_edge_stimulus",
            "failure_signature": _first_matching_note(
                result,
                [r"too_few_(?:rising_)?edges=0", r"not_enough_clk_edges=0"],
            ),
            "confidence": "medium",
        }

    if "too_few_data_edges=0" in low or "insufficient_post_reset_samples count=0" in low:
        return {
            "suspected_layer": "tb_stimulus_or_observable",
            "repair_scope": "tb-first-then-dut",
            "mechanism_family": "missing_data_or_reset_window",
            "failure_signature": _first_matching_note(
                result,
                [r"too_few_data_edges=0", r"insufficient_post_reset_samples count=0"],
            ),
            "confidence": "medium",
        }

    if re.search(r"\bnot_enough_edges\b", low) or "freq_ratio=" in low or "lock_time=nan" in low or "pre_lock" in low:
        return {
            "suspected_layer": "dut_or_complex_system",
            "repair_scope": "submodule-or-loop-local-repair",
            "mechanism_family": "pll_clock_ratio_lock",
            "failure_signature": _first_matching_note(
                result,
                [r"not_enough_edges[^\n]*", r"freq_ratio=[^\n]*", r"pre_lock[^\n]*"],
            ),
            "confidence": "medium",
        }

    if (
        re.search(r"\bunique_codes=\d+", low)
        or re.search(r"\bonly_\d+_codes", low)
        or "code_span=" in low
        or "no vdac activity" in low
        or "max_vout=" in low
        or "diff_range=0.000" in low
    ):
        return {
            "suspected_layer": "dut",
            "repair_scope": "dut-only",
            "mechanism_family": "adc_dac_code_or_output_coverage",
            "failure_signature": _first_matching_note(
                result,
                [
                    r"unique_codes=[^\n]+",
                    r"only_\d+_codes[^\n]+",
                    r"code_span=[^\n]+",
                    r"no vdac activity[^\n]+",
                    r"max_vout=[^\n]+",
                    r"diff_range=0\.000",
                ],
            ),
            "confidence": "medium",
        }

    if "transitions=0" in low or "clk_edges=" in low or "pulses=0" in low:
        return {
            "suspected_layer": "dut",
            "repair_scope": "dut-only",
            "mechanism_family": "sequence_frame_or_pulse_generation",
            "failure_signature": _first_matching_note(result, [r"transitions=0[^\n]*", r"clk_edges=[^\n]*", r"pulses=0[^\n]*"]),
            "confidence": "medium",
        }

    if "count_out_too_low" in low:
        return {
            "suspected_layer": "dut",
            "repair_scope": "dut-only",
            "mechanism_family": "analog_event_crossing",
            "failure_signature": _first_matching_note(result, [r"count_out_too_low=[^\n]+"]),
            "confidence": "medium",
        }

    return {
        "suspected_layer": "unknown_or_mixed",
        "repair_scope": "diagnose-before-repair",
        "mechanism_family": "unsupported",
        "failure_signature": _first_matching_note(result, [r"[^\n]+$"]),
        "confidence": "low",
    }


def collect_failures(result_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    all_results = sorted(result_root.glob("*/result.json"))
    for result_path in all_results:
        result = _load_json(result_path)
        strict_pass = _strict_pass_at_1(result)
        if strict_pass:
            continue
        artifacts = result.get("artifacts") or {}
        classification = _classify(result)
        row = {
            "task_id": result.get("task_id") or result_path.parent.name,
            "benchmark_family": result.get("family", ""),
            "category": result.get("category", ""),
            "status": result.get("status", ""),
            "weighted_total": (result.get("scores") or {}).get("weighted_total"),
            "dut_compile": (result.get("scores") or {}).get("dut_compile"),
            "tb_compile": (result.get("scores") or {}).get("tb_compile"),
            "sim_correct": (result.get("scores") or {}).get("sim_correct"),
            "required_axes": ",".join(result.get("required_axes") or []),
            "status_pass_but_axis_alias": _has_legacy_axis_alias_failure(result),
            "suspected_layer": classification["suspected_layer"],
            "repair_scope": classification["repair_scope"],
            "mechanism_family": classification["mechanism_family"],
            "failure_signature": classification["failure_signature"],
            "confidence": classification["confidence"],
            "result_json": _rel(str(result_path)),
            "dut_path": _rel(artifacts.get("dut_path")),
            "tb_path": _rel(artifacts.get("tb_path")),
            "notes": " ; ".join(_notes(result)),
        }
        rows.append(row)

    summary = {
        "source_result_root": _rel(str(result_root)),
        "total_result_count": len(all_results),
        "failure_count": len(rows),
        "status_counts": dict(Counter(row["status"] for row in rows)),
        "suspected_layer_counts": dict(Counter(row["suspected_layer"] for row in rows)),
        "repair_scope_counts": dict(Counter(row["repair_scope"] for row in rows)),
        "mechanism_family_counts": dict(Counter(row["mechanism_family"] for row in rows)),
    }
    return rows, summary


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fields = [
        "task_id",
        "benchmark_family",
        "category",
        "status",
        "weighted_total",
        "dut_compile",
        "tb_compile",
        "sim_correct",
        "required_axes",
        "status_pass_but_axis_alias",
        "suspected_layer",
        "repair_scope",
        "mechanism_family",
        "failure_signature",
        "confidence",
        "result_json",
        "dut_path",
        "tb_path",
        "notes",
    ]
    with (output_dir / "failures.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (output_dir / "failures.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Current Failure Dataset",
        "",
        f"Source result root: `{summary['source_result_root']}`",
        "",
        "## Summary",
        "",
        f"- Total result count: `{summary['total_result_count']}`",
        f"- Pass@1 failure count: `{summary['failure_count']}`",
        "",
        "### Suspected Layer Counts",
        "",
        "| suspected_layer | count |",
        "|---|---:|",
    ]
    for key, count in sorted(summary["suspected_layer_counts"].items()):
        lines.append(f"| `{key}` | {count} |")
    lines.extend(["", "### Repair Scope Counts", "", "| repair_scope | count |", "|---|---:|"])
    for key, count in sorted(summary["repair_scope_counts"].items()):
        lines.append(f"| `{key}` | {count} |")
    lines.extend(["", "## Failed Tasks", "", "| task | layer | mechanism | signature | scope |", "|---|---|---|---|---|"])
    for row in rows:
        signature = str(row["failure_signature"]).replace("|", "\\|")[:120]
        lines.append(
            f"| `{row['task_id']}` | `{row['suspected_layer']}` | `{row['mechanism_family']}` | {signature} | `{row['repair_scope']}` |"
        )
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export formal failures as a layered-repair dataset.")
    parser.add_argument("--result-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    rows, summary = collect_failures(Path(args.result_root).resolve())
    write_outputs(rows, summary, Path(args.output_dir))
    print(f"[failure-dataset] wrote {args.output_dir}")
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
