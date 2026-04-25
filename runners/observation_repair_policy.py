#!/usr/bin/env python3
"""Circuit-agnostic EVAS observation repair policy.

This module intentionally classifies failures from observable EVAS notes and
metrics rather than task names.  The goal is to steer repair toward generic
mechanisms such as stuck outputs, wrong event cadence, missing pulses, or low
code coverage without overfitting to specific benchmark circuits.
"""
from __future__ import annotations

import re
from typing import Any

_METRIC_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)=([^\s,;]+)")
_NUMERIC_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$", re.IGNORECASE)


def _parse_value(raw: str) -> float | str:
    token = raw.strip().strip("`")
    if _NUMERIC_RE.match(token):
        try:
            return float(token)
        except ValueError:
            pass
    return token


def extract_observation_metrics(notes: list[str]) -> dict[str, float | str]:
    metrics: dict[str, float | str] = {}
    for note in notes:
        for key, raw in _METRIC_RE.findall(str(note)):
            metrics[key] = _parse_value(raw)
    return metrics


def _num(metrics: dict[str, float | str], key: str) -> float | None:
    value = metrics.get(key)
    return float(value) if isinstance(value, (int, float)) else None


def _has_any(metrics: dict[str, float | str], *keys: str) -> bool:
    return any(key in metrics for key in keys)


def classify_observation_pattern(notes: list[str], metrics: dict[str, float | str] | None = None) -> dict[str, Any]:
    """Classify an EVAS failure by observable symptom, not circuit name."""
    metrics = metrics or extract_observation_metrics(notes)
    joined = "\n".join(str(note) for note in notes)
    lowered = joined.lower()
    evidence: list[str] = []

    def add_metric(key: str) -> None:
        if key in metrics:
            evidence.append(f"{key}={metrics[key]}")

    if "tran.csv missing" in lowered or _num(metrics, "returncode") == 1.0:
        add_metric("returncode")
        return {
            "failure_pattern": "runtime_or_observable_artifact_loss",
            "likely_regions": ["include_or_filename", "instance_wiring", "ground_supply", "tran_save_setup"],
            "patch_goal": "restore a runnable artifact that produces tran.csv before changing behavior",
            "evidence": evidence or ["tran.csv missing"],
        }

    if "behavior_eval_timeout" in lowered:
        add_metric("returncode")
        return {
            "failure_pattern": "checker_timeout_or_pathological_waveform",
            "likely_regions": ["event_rate", "feedback_loop", "output_assignment", "save_scope"],
            "patch_goal": "remove excessive toggling or pathological waveform structure while preserving public columns",
            "evidence": evidence or ["behavior_eval_timeout"],
        }

    pulse_keys = (
        "up_first",
        "dn_first",
        "up_second",
        "dn_second",
        "up_pulses_first",
        "dn_pulses_second",
        "overlap_frac",
        "too_few_updn_pulses",
    )
    if _has_any(metrics, *pulse_keys) or "too_few_updn_pulses" in lowered:
        for key in pulse_keys:
            add_metric(key)
        return {
            "failure_pattern": "missing_or_wrong_pulse_window",
            "likely_regions": ["edge_order_latch", "pulse_state", "release_timer", "mutual_exclusion"],
            "patch_goal": "generate finite observable pulses in the expected windows without overlap",
            "evidence": evidence,
        }

    cadence_keys = (
        "ref",
        "fb",
        "num",
        "den",
        "in_edges",
        "out_edges",
        "freq_ratio",
        "late_edge_ratio",
        "pre_lock_edges",
        "post_lock_edges",
        "period_match",
        "base",
        "pre_count",
        "post_count",
    )
    if _has_any(metrics, *cadence_keys) or "not_enough_edges" in lowered:
        for key in cadence_keys:
            add_metric(key)
        return {
            "failure_pattern": "wrong_event_cadence_or_edge_count",
            "likely_regions": ["clock_cross_event", "counter_terminal_count", "timer_next_event", "toggle_condition"],
            "patch_goal": "make edge count, frequency ratio, or event cadence match the observed stimulus window",
            "evidence": evidence,
        }

    code_keys = (
        "unique_codes",
        "vout_span",
        "code_span",
        "avg_abs_err",
        "settled_high",
        "max_vout",
        "levels",
        "codes",
    )
    unique_codes = _num(metrics, "unique_codes")
    vout_span = _num(metrics, "vout_span")
    code_span = _num(metrics, "code_span")
    if (
        _has_any(metrics, *code_keys)
        or "only_" in lowered and "codes" in lowered
        or unique_codes is not None and unique_codes <= 1.0
        or vout_span is not None and vout_span <= 0.0
        or code_span is not None and code_span <= 0.0
    ):
        for key in code_keys:
            add_metric(key)
        return {
            "failure_pattern": "low_code_coverage_or_stuck_code_path",
            "likely_regions": ["sample_to_code", "threshold_or_quantizer", "bit_encode_decode", "analog_output_scale"],
            "patch_goal": "make one source-of-truth code change over the stimulus range and drive all outputs from it",
            "evidence": evidence,
        }

    sequence_keys = (
        "transitions",
        "hi_frac",
        "complement_err",
        "invert_match_frac",
        "mismatch_frac",
        "bad_transitions",
        "mismatches",
    )
    transitions = _num(metrics, "transitions")
    hi_frac = _num(metrics, "hi_frac")
    if (
        _has_any(metrics, *sequence_keys)
        or transitions is not None and transitions <= 0.0
        or hi_frac is not None and hi_frac <= 0.0
        or "bit_mismatch" in lowered
        or "dynamic monotonic code check" in lowered
    ):
        for key in sequence_keys:
            add_metric(key)
        return {
            "failure_pattern": "stuck_or_wrong_digital_sequence",
            "likely_regions": ["reset_release", "clock_event", "state_update", "bit_order", "output_target_assignment"],
            "patch_goal": "make state update after reset and drive the expected bit/sequence polarity without changing the interface",
            "evidence": evidence or ["sequence mismatch"],
        }

    analog_keys = ("span", "range", "low1", "high", "low2", "means", "output_mean_delta")
    if _has_any(metrics, *analog_keys):
        for key in analog_keys:
            add_metric(key)
        return {
            "failure_pattern": "wrong_analog_range_or_threshold_window",
            "likely_regions": ["threshold_condition", "output_scale", "window_state", "transition_target"],
            "patch_goal": "adjust threshold/window/output target logic so measured ranges match the stimulus windows",
            "evidence": evidence,
        }

    return {
        "failure_pattern": "unclassified_behavior_mismatch",
        "likely_regions": ["reset_release", "event_trigger", "state_update", "output_assignment"],
        "patch_goal": "make the smallest behavior-only change that moves the reported EVAS metric",
        "evidence": evidence or notes[:3],
    }


def build_observation_policy_section(notes: list[str]) -> list[str]:
    metrics = extract_observation_metrics(notes)
    policy = classify_observation_pattern(notes, metrics)
    evidence = policy.get("evidence") or []
    likely_regions = policy.get("likely_regions") or []

    lines = [
        "",
        "# Observation-Driven Repair Policy",
        "",
        "This section is selected only from EVAS observable notes and metrics, not from circuit names.",
        "",
        f"- Failure pattern: `{policy['failure_pattern']}`",
        f"- Patch goal: {policy['patch_goal']}",
    ]
    if evidence:
        lines.append("- Evidence:")
        lines.extend(f"  - `{item}`" for item in evidence[:8])
    if likely_regions:
        lines.append("- Likely code regions to inspect first:")
        lines.extend(f"  - `{item}`" for item in likely_regions[:8])

    lines.extend([
        "",
        "Universal patch boundary:",
        "- Do not change module names, port order, filenames, testbench includes, save names, or tran setup.",
        "- Do not add hierarchy or rename public nodes while fixing a behavior metric.",
        "- Preserve any metric that is already observable and compile-clean.",
        "- Prefer changing one internal mechanism: reset release, event trigger, state update, timer/counter condition, bit mapping, threshold, or output target.",
        "- If a proposed edit requires broad rewiring, reject it and make a smaller local behavior edit instead.",
    ])

    pattern = policy["failure_pattern"]
    if pattern == "stuck_or_wrong_digital_sequence":
        lines.extend([
            "",
            "Generic repair recipe:",
            "- Check that reset deasserts and stays deasserted in the checker window.",
            "- Check that the clock/event crossing direction matches the stimulus.",
            "- Use one integer state as the source of truth and update it exactly once per valid event.",
            "- Drive outputs from that state with unconditional transition targets.",
            "- If polarity or complement metrics are exactly wrong, flip the output target assignment instead of rewriting the whole state machine.",
        ])
    elif pattern == "wrong_event_cadence_or_edge_count":
        lines.extend([
            "",
            "Generic repair recipe:",
            "- Keep the existing observable clock/output columns and stimulus.",
            "- Inspect the event trigger, counter terminal count, timer next-event update, and toggle condition.",
            "- If input edges exist but output edge count is wrong, fix the counter/toggle condition, not the testbench.",
            "- If output edges are absent, ensure the event block schedules future events and is not held in reset.",
        ])
    elif pattern == "missing_or_wrong_pulse_window":
        lines.extend([
            "",
            "Generic repair recipe:",
            "- Latch which event arrived first, assert a finite pulse target, and release it with a timer or bounded state.",
            "- Keep pulse generation window-local; avoid pulses that never assert, never clear, or overlap.",
            "- If pulses are absent, fix event detection/state latching; if pulses are too wide or overlap, fix release timing.",
        ])
    elif pattern == "low_code_coverage_or_stuck_code_path":
        lines.extend([
            "",
            "Generic repair recipe:",
            "- Keep one integer code as the source of truth.",
            "- Drive all bit outputs and analog outputs from the same code.",
            "- Ensure reset does not hold the code constant during the conversion/measurement window.",
            "- Adjust quantization, clipping, bit order, or output scale without changing public wiring.",
        ])
    elif pattern == "wrong_analog_range_or_threshold_window":
        lines.extend([
            "",
            "Generic repair recipe:",
            "- Preserve stimulus and saved columns.",
            "- Inspect threshold comparisons, hysteresis/window state, output scale, and transition targets.",
            "- Change the smallest threshold/window/output target expression that can move the measured range.",
        ])
    elif pattern == "checker_timeout_or_pathological_waveform":
        lines.extend([
            "",
            "Generic repair recipe:",
            "- Remove uncontrolled oscillation or extremely dense event generation.",
            "- Keep outputs event-bounded and transition-driven from discrete targets.",
            "- Save only public checker columns; avoid adding internal high-activity nodes.",
        ])
    elif pattern == "runtime_or_observable_artifact_loss":
        lines.extend([
            "",
            "Generic repair recipe:",
            "- Restore runnable artifacts first: filenames, include lines, instance node counts, ground/supply consistency, and save/tran setup.",
            "- Do not tune behavior constants until EVAS produces `tran.csv` and behavior metrics.",
        ])

    return lines
