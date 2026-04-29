#!/usr/bin/env python3
"""Triage behavior failures into contract and repair-template families.

This script is intentionally diagnostic.  It does not change generated
artifacts and does not call an LLM.  It reads a scored result directory,
groups non-passing tasks by EVAS notes, and emits a repair-oriented report.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from failure_attribution import classify_failure

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class FamilyRule:
    family: str
    contract_templates: tuple[str, ...]
    repair_template: str
    summary: str
    patterns: tuple[str, ...]


RULES: tuple[FamilyRule, ...] = (
    FamilyRule(
        family="runtime_or_timeout",
        contract_templates=("runtime_csv_exists", "checker_runtime_budget"),
        repair_template="runtime-interface-minimal-harness",
        summary="Simulation completed poorly or checker timed out before a useful behavior verdict.",
        patterns=("behavior_eval_timeout", "tran.csv missing", "returncode=1"),
    ),
    FamilyRule(
        family="missing_edges_or_clock_activity",
        contract_templates=("edge_count", "clock_activity", "reset_release_activity"),
        repair_template="clock-event-generator-or-reset-release",
        summary="Expected clock/output events are absent or far too sparse.",
        patterns=(
            "not_enough_edges",
            "too_few_edges",
            "not_enough_clk_edges",
            "too_few_rising_edges",
            "too_few_data_edges",
            "count_out_too_low",
            "clk_edges=",
            "pulses=0",
            "transitions=0",
        ),
    ),
    FamilyRule(
        family="pll_or_ratio_tracking",
        contract_templates=("frequency_ratio", "lock_window", "reacquire_window", "edge_interval"),
        repair_template="pll-dco-counter-feedback-loop",
        summary="Frequency ratio, lock, or relock metrics are wrong after transient execution.",
        patterns=("freq_ratio=", "late_freq_ratio=", "pre_ratio=", "post_ratio=", "lock_time=nan", "post_lock=0"),
    ),
    FamilyRule(
        family="code_coverage_or_quantizer",
        contract_templates=("code_coverage", "monotonic_code", "bit_mapping", "sample_clock_alignment"),
        repair_template="clocked-quantizer-code-update",
        summary="ADC/DAC/digital code output is stuck, incomplete, or not spanning expected codes.",
        patterns=("unique_codes=", "only_", "codes=", "code_span=", "diff_range=0.000", "vout_span=0.000"),
    ),
    FamilyRule(
        family="analog_output_stuck",
        contract_templates=("output_span", "activity_after_stimulus", "settled_level_window"),
        repair_template="drive-output-target-and-transition",
        summary="Analog output appears stuck even though inputs or decoded activity exist.",
        patterns=("max_vout=0.000", "no vdac activity", "peak=0.000", "vctrl_min=0.500 vctrl_max=0.500"),
    ),
    FamilyRule(
        family="dwa_or_onehot_overlap",
        contract_templates=("onehot_no_overlap", "pointer_wrap", "thermometer_count", "post_reset_samples"),
        repair_template="dwa-pointer-thermometer-mask",
        summary="DWA pointer/cell-enable behavior lacks samples, wraps incorrectly, or overlaps.",
        patterns=("ptr_", "cell_en", "overlap", "insufficient_post_reset_samples", "bad_ptr_rows"),
    ),
    FamilyRule(
        family="pulse_window_or_pfd",
        contract_templates=("pulse_width", "pulse_order", "mutual_reset_window", "deadzone_response"),
        repair_template="pfd-latched-pulse-delayed-clear",
        summary="PFD/BBPD pulse timing, ordering, or reset window is likely wrong.",
        patterns=("up_frac", "dn_frac", "pulse", "deadzone", "pfd"),
    ),
)


GENERIC_FAMILY = FamilyRule(
    family="unclassified_behavior",
    contract_templates=("task_specific_behavior_contract",),
    repair_template="manual-contract-extraction-needed",
    summary="No high-confidence generic family matched; inspect checker and task prompt.",
    patterns=(),
)


COMPILE_INTERFACE_FAMILY = FamilyRule(
    family="compile_interface",
    contract_templates=("spectre_strict_syntax", "interface_preservation"),
    repair_template="compile-interface-syntax-first",
    summary="Candidate violates Spectre-friendly Verilog-A/Spectre syntax or interface rules.",
    patterns=(),
)


COUNTER_CADENCE_FAMILY = FamilyRule(
    family="counter_cadence_or_timer_grid",
    contract_templates=("counter_cadence", "edge_interval", "timer_window"),
    repair_template="counter-cadence-off-by-one",
    summary="Counter, divider, or timer cadence is wrong.",
    patterns=(),
)


ADC_DAC_FAMILY = FamilyRule(
    family="adc_dac_code_or_output_coverage",
    contract_templates=("code_coverage", "monotonic_code", "output_span", "calibration_settling"),
    repair_template="clocked-quantizer-code-update",
    summary="Converter code/output coverage, reconstruction, or calibration behavior is wrong.",
    patterns=(),
)


PLL_FAMILY = FamilyRule(
    family="pll_clock_ratio_lock",
    contract_templates=("frequency_ratio", "lock_window", "edge_interval"),
    repair_template="pll-dco-counter-feedback-loop",
    summary="PLL/clock feedback ratio, cadence, or lock behavior is wrong.",
    patterns=(),
)


PULSE_FAMILY = FamilyRule(
    family="pulse_or_edge_protocol",
    contract_templates=("pulse_width", "pulse_order", "non_overlap"),
    repair_template="pfd-latched-pulse-delayed-clear",
    summary="PFD/BBPD pulse timing, ordering, or reset protocol is wrong.",
    patterns=(),
)


SEQUENCE_FAMILY = FamilyRule(
    family="sequence_frame_or_pulse_generation",
    contract_templates=("sequence_alignment", "transition_count", "frame_alignment"),
    repair_template="sequence-frame-alignment",
    summary="Sequence, PRBS/LFSR, Gray counter, or serialized frame behavior is wrong.",
    patterns=(),
)


DWA_FAMILY = FamilyRule(
    family="dwa_or_onehot_overlap",
    contract_templates=("onehot_no_overlap", "pointer_wrap", "thermometer_count", "post_reset_samples"),
    repair_template="dwa-pointer-thermometer-mask",
    summary="DWA pointer/cell-enable behavior lacks samples, wraps incorrectly, or overlaps.",
    patterns=(),
)


ANALOG_WINDOW_FAMILY = FamilyRule(
    family="analog_or_logic_window_behavior",
    contract_templates=("output_span", "window_fraction", "equation_accuracy"),
    repair_template="analog-window-or-truth-table-repair",
    summary="Analog equation, threshold window, or simple logic-window behavior is wrong.",
    patterns=(),
)


def _strict_task_pass(result: dict) -> bool:
    scores = result.get("scores", {})
    aliases = {
        "syntax": "dut_compile",
        "routing": "tb_compile",
        "simulation": "sim_correct",
        "behavior": "sim_correct",
    }
    required = []
    for axis in result.get("required_axes", ["dut_compile", "tb_compile", "sim_correct"]):
        mapped = aliases.get(str(axis), str(axis))
        if mapped not in required:
            required.append(mapped)
    return all(float(scores.get(axis, 0.0)) >= 1.0 for axis in required)


def _notes(result: dict) -> list[str]:
    raw = result.get("evas_notes")
    if raw is None:
        raw = result.get("notes", [])
    if isinstance(raw, str):
        return [raw]
    return [str(item) for item in raw]


def _notes_text(result: dict) -> str:
    return "\n".join(_notes(result)).lower()


def _has_any(text: str, patterns: Iterable[str]) -> bool:
    return any(pattern.lower() in text for pattern in patterns)


def _task_prompt_text(task_id: str) -> str:
    matches = sorted(ROOT.glob(f"tasks/**/{task_id}/prompt.md"))
    if not matches:
        return ""
    try:
        return matches[0].read_text(encoding="utf-8").lower()
    except Exception:
        return ""


def _infer_blocking_rule(result: dict) -> FamilyRule | None:
    """Return the first repair layer that must be fixed before semantic tuning."""
    text = _notes_text(result)
    status = str(result.get("status", ""))
    if _has_any(
        text,
        (
            "spectre_strict:embedded_declaration",
            "spectre_strict:conditional_cross",
            "spectre_strict:conditional_transition",
            "spectre_strict:reversed_source_syntax",
            "spectre_strict:zero_pulse_edge",
        ),
    ):
        return COMPILE_INTERFACE_FAMILY
    if _has_any(text, ("tran.csv missing", "tb_not_executed", "returncode=1")):
        return RULES[0]
    if _has_any(text, ("behavior_eval_timeout", "evas_timeout")):
        return RULES[0]
    if status in {"FAIL_DUT_COMPILE", "FAIL_TB_COMPILE"} and _has_any(text, ("spectre_strict:", "dut_not_compiled")):
        return COMPILE_INTERFACE_FAMILY
    return None


def _infer_semantic_rule(result: dict) -> FamilyRule:
    """Map EVAS notes plus public prompt semantics to the mechanism card family."""
    note_text = _notes_text(result)
    task_id = str(result.get("task_id", "")).lower()
    prompt_text = _task_prompt_text(task_id)
    semantic_text = f"{task_id}\n{prompt_text}\n{note_text}"

    # PFD/BBPD should win over generic "overlap" or one-hot wording.
    if _has_any(
        semantic_text,
        (
            "pfd",
            "phase frequency detector",
            "bbpd",
            "bang-bang phase detector",
            "too_few_updn_pulses",
            "up_frac",
            "dn_frac",
            "deadzone",
            "dead zone",
        ),
    ):
        return PULSE_FAMILY

    if _has_any(
        semantic_text,
        (
            "pll",
            "phase-locked loop",
            "phase locked loop",
            "lock_time=nan",
            "late_edge_ratio=",
            "freq_ratio=",
            "late_freq_ratio=",
            "pre_ratio=",
            "post_ratio=",
            "vctrl_",
        ),
    ):
        return PLL_FAMILY

    if _has_any(
        semantic_text,
        (
            "ratio_code=",
            "interval_hist=",
            "period_match=",
            "phase_span_too_small",
            "code_start=",
            "code_end=",
            "counter",
            "divider",
            "timer",
        ),
    ):
        return COUNTER_CADENCE_FAMILY

    if _has_any(
        semantic_text,
        (
            "adc",
            "dac",
            "quantiz",
            "unique_codes=",
            "only_",
            "code_span=",
            "vout_span=0",
            "diff_range=0.000",
            "edge_sampled_levels=0",
            "aout_span=0",
            "max_vout=0.000",
            "no vdac activity",
            "settled_high=false",
        ),
    ):
        return ADC_DAC_FAMILY

    if _has_any(semantic_text, ("dwa", "ptr_", "cell_en", "bad_ptr_rows", "wraparound", "wrap around")):
        return DWA_FAMILY

    if _has_any(
        semantic_text,
        (
            "transitions=",
            "complement_err=",
            "serializer",
            "sequence",
            "frame",
            "prbs",
            "lfsr",
            "gray",
        ),
    ):
        return SEQUENCE_FAMILY

    if _has_any(
        semantic_text,
        (
            "max_err=",
            "low1=",
            "window_fracs",
            "all_bits_high_final_window=false",
            "means=(",
            "truth",
            "hysteresis",
            "threshold",
            "gain",
        ),
    ):
        return ANALOG_WINDOW_FAMILY

    return GENERIC_FAMILY


def _match_rule(result: dict) -> FamilyRule:
    return _infer_blocking_rule(result) or _infer_semantic_rule(result)


def _rule_payload(rule: FamilyRule | None) -> dict[str, object]:
    if rule is None:
        return {
            "family": "",
            "contract_templates": [],
            "repair_template": "",
            "summary": "",
        }
    return {
        "family": rule.family,
        "contract_templates": list(rule.contract_templates),
        "repair_template": rule.repair_template,
        "summary": rule.summary,
    }


def _extract_metrics(notes: Iterable[str]) -> dict[str, str]:
    metrics: dict[str, str] = {}
    for note in notes:
        for key, value in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)=([^\s,;]+)", note):
            metrics[key] = value
    return metrics


def _task_meta(task_id: str) -> dict:
    matches = sorted(ROOT.glob(f"tasks/**/{task_id}/meta.json"))
    if not matches:
        return {}
    try:
        return json.loads(matches[0].read_text(encoding="utf-8"))
    except Exception:
        return {}


def _result_items(result_root: Path) -> list[tuple[str, Path, dict]]:
    items: list[tuple[str, Path, dict]] = []
    for path in sorted(result_root.glob("*/result.json")):
        try:
            result = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        task_id = result.get("task_id") or path.parent.name
        items.append((str(task_id), path, result))
    return items


def build_report(result_root: Path) -> dict:
    items = _result_items(result_root)
    failures: list[dict] = []
    family_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    repair_owner_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    strict_status_counts: Counter[str] = Counter()
    template_counts: Counter[str] = Counter()

    for task_id, path, result in items:
        attribution = result.get("failure_attribution") or classify_failure(result)
        domain_counts[str(attribution.get("domain", "unknown"))] += 1
        repair_owner_counts[str(attribution.get("repair_owner", "unknown"))] += 1
        status = str(result.get("status", "UNKNOWN"))
        status_counts[status] += 1
        strict_pass = _strict_task_pass(result)
        strict_status_counts["STRICT_PASS" if strict_pass else "STRICT_NONPASS"] += 1
        if strict_pass:
            continue
        if status == "PASS":
            rule = FamilyRule(
                family="scoring_contract_mismatch",
                contract_templates=("required_axis_alignment",),
                repair_template="scoring-schema-reconcile",
                summary="Task status is PASS but required_axes do not align with current score keys.",
                patterns=(),
            )
            blocking_rule = rule
            semantic_rule = None
        else:
            blocking_rule = _infer_blocking_rule(result)
            semantic_rule = _infer_semantic_rule(result)
            rule = blocking_rule or semantic_rule
        notes = _notes(result)
        metrics = _extract_metrics(notes)
        meta = _task_meta(task_id)
        family_counts[rule.family] += 1
        template_counts[rule.repair_template] += 1
        failures.append(
            {
                "task_id": task_id,
                "family": meta.get("family", ""),
                "category": meta.get("category", ""),
                "status": status,
                "strict_pass": strict_pass,
                "required_axes": result.get("required_axes", ["dut_compile", "tb_compile", "sim_correct"]),
                "scores": result.get("scores", {}),
                "failure_attribution": attribution,
                "contract_family": rule.family,
                "contract_templates": list(rule.contract_templates),
                "repair_template": rule.repair_template,
                "blocking_family": _rule_payload(blocking_rule),
                "semantic_family": _rule_payload(semantic_rule),
                "summary": rule.summary,
                "key_metrics": metrics,
                "notes": notes[:8],
                "result_path": str(path),
            }
        )

    return {
        "result_root": str(result_root),
        "total_tasks": len(items),
        "status_counts": dict(status_counts),
        "strict_status_counts": dict(strict_status_counts),
        "failure_domain_counts": dict(domain_counts),
        "repair_owner_counts": dict(repair_owner_counts),
        "failure_count": len(failures),
        "contract_family_counts": dict(family_counts),
        "repair_template_counts": dict(template_counts),
        "failures": failures,
    }


def write_markdown(report: dict, path: Path) -> None:
    lines: list[str] = []
    lines.append("# Behavior Contract Triage Report")
    lines.append("")
    lines.append(f"Result root: `{report['result_root']}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total tasks: `{report['total_tasks']}`")
    lines.append(f"- Non-pass tasks: `{report['failure_count']}`")
    lines.append("")
    lines.append("### Status Counts")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|---|---:|")
    for status, count in sorted(report["status_counts"].items()):
        lines.append(f"| `{status}` | {count} |")
    lines.append("")
    lines.append("### Strict Pass@1 Counts")
    lines.append("")
    lines.append("| Strict status | Count |")
    lines.append("|---|---:|")
    for status, count in sorted(report["strict_status_counts"].items()):
        lines.append(f"| `{status}` | {count} |")
    lines.append("")
    lines.append("### Failure Domains")
    lines.append("")
    lines.append("| Domain | Count |")
    lines.append("|---|---:|")
    for domain, count in sorted(report["failure_domain_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{domain}` | {count} |")
    lines.append("")
    lines.append("### Repair Owners")
    lines.append("")
    lines.append("| Repair owner | Count |")
    lines.append("|---|---:|")
    for owner, count in sorted(report["repair_owner_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{owner}` | {count} |")
    lines.append("")
    lines.append("### Contract Families")
    lines.append("")
    lines.append("| Contract family | Count |")
    lines.append("|---|---:|")
    for family, count in sorted(report["contract_family_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{family}` | {count} |")
    lines.append("")
    lines.append("### Repair Templates")
    lines.append("")
    lines.append("| Repair template | Count |")
    lines.append("|---|---:|")
    for template, count in sorted(report["repair_template_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{template}` | {count} |")
    semantic_counts: Counter[str] = Counter(
        item.get("semantic_family", {}).get("family", "") for item in report["failures"]
    )
    semantic_counts.pop("", None)
    if semantic_counts:
        lines.append("")
        lines.append("### Semantic Families")
        lines.append("")
        lines.append("| Semantic family | Count |")
        lines.append("|---|---:|")
        for family, count in sorted(semantic_counts.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"| `{family}` | {count} |")
    lines.append("")
    lines.append("## Failure Worklist")
    lines.append("")
    lines.append("| Task | Status | Domain | Repair owner | Blocking family | Semantic family | Repair template | Key metrics / first note |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for item in report["failures"]:
        metrics = ", ".join(f"{key}={value}" for key, value in list(item["key_metrics"].items())[:5])
        first_note = item["notes"][0] if item["notes"] else ""
        detail = metrics or first_note
        detail = detail.replace("|", "\\|")
        attribution = item.get("failure_attribution", {})
        blocking_family = item.get("blocking_family", {}).get("family", "") or item["contract_family"]
        semantic_family = item.get("semantic_family", {}).get("family", "")
        lines.append(
            f"| `{item['task_id']}` | `{item['status']}` | `{attribution.get('domain', 'unknown')}` | "
            f"`{attribution.get('repair_owner', 'unknown')}` | `{blocking_family}` | `{semantic_family}` | "
            f"`{item['repair_template']}` | {detail} |"
        )
    lines.append("")
    lines.append("## Next Experiment Cut")
    lines.append("")
    lines.append("Start with one or two tasks from each high-count family, write explicit `contracts.yaml`, then feed only a diagnostic summary into the repair prompt.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--result-root",
        type=Path,
        required=True,
        help="Directory containing per-task result.json files.",
    )
    parser.add_argument("--json-out", type=Path, help="Optional JSON report output path.")
    parser.add_argument("--md-out", type=Path, help="Optional Markdown report output path.")
    args = parser.parse_args()

    report = build_report(args.result_root)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.md_out:
        write_markdown(report, args.md_out)
    if not args.json_out and not args.md_out:
        print(json.dumps(report, indent=2))
    else:
        print(
            f"triaged {report['failure_count']} failures from {report['total_tasks']} tasks; "
            f"families={report['contract_family_counts']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
