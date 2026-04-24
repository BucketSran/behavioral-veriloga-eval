#!/usr/bin/env python3
"""Analyze recurring EVAS diagnostics to prioritize generic repair templates.

This script is evidence-gathering only: it scans existing `results/**/result.json`
files and does not call any model or simulator.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


TEMPLATE_DEFS = [
    {
        "id": "analog_bus_safe_template",
        "title": "Analog bus safe Verilog-A template",
        "patterns": [
            r"dynamic_analog_vector_index=",
            r"genvar_inside_analog=",
        ],
        "template": "Fixed-index bus reads plus real target arrays and module-scope genvar output contributions.",
    },
    {
        "id": "conditional_event_contribution_template",
        "title": "Conditional cross/transition structure template",
        "patterns": [
            r"conditional_cross=",
            r"conditional_transition=",
        ],
        "template": "Top-level cross events and unconditional transition contributions driven by target variables.",
    },
    {
        "id": "digital_verilog_to_veriloga_template",
        "title": "Digital-Verilog to Verilog-A syntax template",
        "patterns": [
            r"digital_verilog_syntax=",
            r"packed_bit_select",
            r"digital_reg_decl",
            r"digital_always_block",
            r"sv_param_header",
            r"shift_operator",
        ],
        "template": "Replace reg/wire/always/packed integer bit indexing with integer state and analog cross events.",
    },
    {
        "id": "module_file_interface_template",
        "title": "Module/file/include interface template",
        "patterns": [
            r"undefined_module=",
            r"missing_include=",
            r"missing_generated_files:",
            r"generated_dut_alias=",
            r"primary_dut_uploaded_but_not_referenced_by_tb",
        ],
        "template": "Align module declaration, saved filename, ahdl_include path, and testbench instantiation.",
    },
    {
        "id": "observable_scalar_alias_template",
        "title": "Observable scalar CSV alias/save template",
        "patterns": [
            r"^missing ",
            r"missing_",
            r"missing dout_code",
            r"missing dout_0\.\.7",
            r"missing vin/",
            r"missing .*ptr_0",
            r"missing .*cell_en_0",
            r"normalized_tb_save_tokens",
            r"colon_instance_syntax_lines=",
        ],
        "template": "Expose checker-required waveform columns as plain scalar nodes and save names.",
    },
    {
        "id": "simulation_artifact_runtime_template",
        "title": "Simulation artifact/runtime template",
        "patterns": [
            r"tran\.csv missing",
            r"tb_not_executed",
            r"dut_not_compiled",
            r"evas_timeout",
            r"returncode=1",
        ],
        "template": "Recover runnable netlist: complete includes, valid tran, realistic maxstep, and raw compile diagnostics.",
    },
    {
        "id": "adc_sar_code_coverage_template",
        "title": "ADC/SAR code coverage template",
        "patterns": [
            r"unique_codes=",
            r"only_\d+_codes",
            r"vout_span=0",
            r"avg_abs_err=",
            r"too_few_edges=",
        ],
        "template": "Monotonic quantizer/code path, full input coverage, clocked updates, and DAC output span.",
    },
    {
        "id": "serializer_phase_order_template",
        "title": "Serializer bit order/phase template",
        "patterns": [
            r"bit_mismatch",
            r"only_\d+_edges_after_load",
            r"only_\d+_sampled_bits",
            r"frame_rises=",
        ],
        "template": "Capture word at load, choose MSB/LSB order from EVAS expected sequence, align first bit phase.",
    },
    {
        "id": "pfd_bbpd_pulse_window_template",
        "title": "PFD/BBPD pulse-window template",
        "patterns": [
            r"up_first=",
            r"dn_first=",
            r"up_second=",
            r"dn_second=",
            r"overlap_frac=",
            r"lead_window_updn",
        ],
        "template": "Edge-order latch, finite UP/DN pulse windows, non-overlap reset, window-local behavior.",
    },
    {
        "id": "pll_edge_ratio_timing_template",
        "title": "PLL/clock edge-ratio timing template",
        "patterns": [
            r"freq_ratio=",
            r"late_edge_ratio=",
            r"not_enough_edges",
            r"lock_time=",
            r"vctrl_",
            r"ratio_hop",
            r"relock_time=",
        ],
        "template": "Divider/DCO edge cadence, measured lock criteria, and stable ratio windows.",
    },
    {
        "id": "gray_counter_template",
        "title": "Gray counter state/output template",
        "patterns": [
            r"gray_property_violated",
            r"bad_transitions=",
            r"missing_gray_codes",
        ],
        "template": "Binary counter state plus Gray transform, one update per clock edge, fixed bit outputs.",
    },
    {
        "id": "mux_selection_template",
        "title": "MUX select mapping template",
        "patterns": [
            r"sel0_err",
            r"sel1_err",
            r"sel2_err",
            r"sel3_err",
            r"all_4_select_windows",
        ],
        "template": "Truth-table-driven select decode with stable output window per select code.",
    },
    {
        "id": "dac_level_count_template",
        "title": "DAC level/count coverage template",
        "patterns": [
            r"levels=",
            r"aout_span=",
            r"max_ones=",
            r"max_vout=",
        ],
        "template": "Decode all input bits/thermometer cells and map count/code to monotonic analog output.",
    },
    {
        "id": "sample_hold_timing_template",
        "title": "Sample-hold edge/droop timing template",
        "patterns": [
            r"too_few_clock_edges",
            r"sample_mismatch",
            r"droop_failures",
            r"droop_windows",
        ],
        "template": "Sample on correct aperture edge, hold target state, and apply droop only during hold windows.",
    },
]

COMPILED_PATTERNS = [
    (entry, [re.compile(pattern, re.IGNORECASE) for pattern in entry["patterns"]])
    for entry in TEMPLATE_DEFS
]


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _notes(result: dict) -> list[str]:
    values: list[str] = []
    for key in ("evas_notes", "notes", "spectre_notes"):
        raw = result.get(key) or []
        if isinstance(raw, list):
            values.extend(str(item) for item in raw)
    return values


def _task_id_from_result(path: Path, result: dict) -> str:
    task_id = str(result.get("task_id") or "").strip()
    if task_id:
        return task_id
    if path.parent.name:
        return path.parent.name
    return "<unknown>"


def _run_id_from_result(path: Path) -> str:
    try:
        rel = path.relative_to(ROOT / "results")
    except ValueError:
        return str(path.parent)
    parts = rel.parts
    if len(parts) >= 3 and parts[-1] == "result.json":
        return "/".join(parts[:-2])
    return "/".join(parts[:-1])


def _match_templates(note: str) -> list[dict]:
    matches = []
    for entry, patterns in COMPILED_PATTERNS:
        if any(pattern.search(note) for pattern in patterns):
            matches.append(entry)
    return matches


def _status_bucket(status: str) -> str:
    if status == "PASS":
        return "pass"
    if status == "FAIL_DUT_COMPILE":
        return "dut_compile"
    if status == "FAIL_TB_COMPILE":
        return "tb_compile"
    if status == "FAIL_SIM_CORRECTNESS":
        return "sim_correctness"
    if status == "FAIL_INFRA":
        return "infra"
    return status.lower() or "unknown"


def analyze(results_root: Path) -> dict:
    template_rows = {
        entry["id"]: {
            "id": entry["id"],
            "title": entry["title"],
            "template": entry["template"],
            "occurrences": 0,
            "result_entries": set(),
            "tasks": set(),
            "runs": set(),
            "statuses": Counter(),
            "examples": [],
        }
        for entry in TEMPLATE_DEFS
    }
    status_counts = Counter()
    total_results = 0
    failed_results = 0
    unmatched_failed: list[dict] = []
    task_status = defaultdict(Counter)

    for path in sorted(results_root.rglob("result.json")):
        result = _read_json(path)
        if not isinstance(result, dict):
            continue
        total_results += 1
        status = str(result.get("status") or "UNKNOWN")
        status_counts[status] += 1
        task_id = _task_id_from_result(path, result)
        run_id = _run_id_from_result(path)
        task_status[task_id][status] += 1
        if status == "PASS":
            continue
        failed_results += 1

        matched_any = False
        for note in _notes(result):
            matched = _match_templates(note)
            if not matched:
                continue
            matched_any = True
            for entry in matched:
                row = template_rows[entry["id"]]
                row["occurrences"] += 1
                row["result_entries"].add(str(path.relative_to(ROOT)))
                row["tasks"].add(task_id)
                row["runs"].add(run_id)
                row["statuses"][_status_bucket(status)] += 1
                if len(row["examples"]) < 5:
                    row["examples"].append(
                        {
                            "task_id": task_id,
                            "status": status,
                            "run_id": run_id,
                            "note": note[:500],
                        }
                    )
        if not matched_any and len(unmatched_failed) < 50:
            notes = _notes(result)
            unmatched_failed.append(
                {
                    "task_id": task_id,
                    "status": status,
                    "run_id": run_id,
                    "notes": notes[:5],
                }
            )

    rows = []
    for row in template_rows.values():
        rows.append(
            {
                "id": row["id"],
                "title": row["title"],
                "template": row["template"],
                "occurrences": row["occurrences"],
                "result_entry_count": len(row["result_entries"]),
                "task_count": len(row["tasks"]),
                "run_count": len(row["runs"]),
                "statuses": dict(row["statuses"]),
                "top_tasks": [task for task, _ in Counter({t: 1 for t in row["tasks"]}).most_common(12)],
                "tasks": sorted(row["tasks"]),
                "examples": row["examples"],
            }
        )
    rows.sort(key=lambda item: (item["task_count"], item["result_entry_count"], item["occurrences"]), reverse=True)

    return {
        "results_root": str(results_root),
        "total_result_json": total_results,
        "failed_result_json": failed_results,
        "status_counts": dict(status_counts),
        "template_rows": rows,
        "unmatched_failed_examples": unmatched_failed,
    }


def _md_table(rows: list[dict]) -> str:
    lines = [
        "| Rank | Template Need | Occurrences | Result entries | Tasks | Dominant statuses | Proposed generic template |",
        "| ---: | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for idx, row in enumerate(rows, start=1):
        statuses = ", ".join(f"{k}:{v}" for k, v in sorted(row["statuses"].items())) or "-"
        lines.append(
            f"| {idx} | `{row['id']}`<br>{row['title']} | {row['occurrences']} | "
            f"{row['result_entry_count']} | {row['task_count']} | {statuses} | {row['template']} |"
        )
    return "\n".join(lines)


def _md_examples(rows: list[dict]) -> str:
    sections: list[str] = []
    for row in rows:
        if not row["examples"]:
            continue
        sections.extend([f"### `{row['id']}`", ""])
        sections.append(f"Template: {row['template']}")
        sections.append("")
        sections.append("Examples:")
        for ex in row["examples"]:
            sections.append(
                f"- `{ex['task_id']}` ({ex['status']}, `{ex['run_id']}`): `{ex['note']}`"
            )
        sections.append("")
    return "\n".join(sections)


def write_report(summary: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_ready = {
        **summary,
        "template_rows": summary["template_rows"],
    }
    (out_dir / "repair_template_needs.json").write_text(json.dumps(json_ready, indent=2), encoding="utf-8")

    rows = summary["template_rows"]
    md = [
        "# Repair Template Needs From Existing EVAS Results",
        "",
        "Date: 2026-04-25",
        "",
        "Scope: existing `results/**/result.json` only. No model or simulator calls.",
        "",
        "Goal: prioritize generic repair templates from recurring EVAS diagnostic classes, not task-specific gold implementations.",
        "",
        "## Summary",
        "",
        f"- Result files scanned: `{summary['total_result_json']}`",
        f"- Non-PASS result files: `{summary['failed_result_json']}`",
        "- Status counts: "
        + ", ".join(f"`{k}={v}`" for k, v in sorted(summary["status_counts"].items())),
        "",
        "## Ranked Template Needs",
        "",
        _md_table(rows),
        "",
        "## Recommended Implementation Order",
        "",
    ]
    recommended = [
        row for row in rows
        if row["task_count"] > 0 and row["id"] not in {"simulation_artifact_runtime_template"}
    ][:5]
    for idx, row in enumerate(recommended, start=1):
        md.append(f"{idx}. `{row['id']}`: {row['template']}")
    md.extend(
        [
            "",
            "Rationale:",
            "",
            "- Prefer templates that affect many distinct tasks rather than many repeated runs of one task.",
            "- Prefer compile/observable templates first because they unblock downstream behavioral EVAS feedback.",
            "- Treat `simulation_artifact_runtime_template` as a diagnostic-retention and raw-log surfacing problem, not a standalone behavior template.",
            "",
            "## Examples",
            "",
            _md_examples(rows[:8]),
        ]
    )
    if summary["unmatched_failed_examples"]:
        md.extend(["", "## Unmatched Failed Examples", ""])
        for ex in summary["unmatched_failed_examples"][:20]:
            note_preview = " | ".join(str(note)[:180] for note in ex["notes"])
            md.append(f"- `{ex['task_id']}` ({ex['status']}, `{ex['run_id']}`): `{note_preview}`")
    (out_dir / "REPAIR_TEMPLATE_NEEDS.md").write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyze recurring EVAS diagnostics for generic repair templates.")
    ap.add_argument("--results-root", default="results")
    ap.add_argument("--output-dir", default="results/repair-template-needs-2026-04-25")
    args = ap.parse_args()

    results_root = Path(args.results_root)
    if not results_root.is_absolute():
        results_root = ROOT / results_root
    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir

    summary = analyze(results_root)
    write_report(summary, out_dir)
    print(
        f"[repair-template-needs] scanned={summary['total_result_json']} "
        f"failed={summary['failed_result_json']} output={out_dir}"
    )
    for row in summary["template_rows"][:8]:
        print(
            f"  {row['id']}: tasks={row['task_count']} "
            f"results={row['result_entry_count']} occurrences={row['occurrences']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
