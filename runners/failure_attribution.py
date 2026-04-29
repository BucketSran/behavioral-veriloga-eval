#!/usr/bin/env python3
"""Classify scored failures before repair routing.

The first split is intentionally simple:

- functional: simulation produced a trustworthy behavior verdict and the
  circuit behavior failed that verdict.
- validation: the verdict itself is not trustworthy because compile, harness,
  simulator, checker, file, timeout, or scoring issues blocked it.

`repair_owner` refines the second case so the loop can avoid asking the LLM to
change circuit behavior when the checker or scoring pipeline is the real target.
"""
from __future__ import annotations

from typing import Any


def _notes(result: dict[str, Any]) -> list[str]:
    raw = result.get("evas_notes")
    if raw is None:
        raw = result.get("notes", [])
    if isinstance(raw, str):
        return [raw]
    return [str(item) for item in raw]


def _notes_text(result: dict[str, Any]) -> str:
    return "\n".join(_notes(result)).lower()


def _required_axes(result: dict[str, Any]) -> list[str]:
    aliases = {
        "syntax": "dut_compile",
        "routing": "tb_compile",
        "simulation": "sim_correct",
        "behavior": "sim_correct",
    }
    axes: list[str] = []
    for axis in result.get("required_axes", ["dut_compile", "tb_compile", "sim_correct"]):
        mapped = aliases.get(str(axis), str(axis))
        if mapped not in axes:
            axes.append(mapped)
    return axes


def _strict_pass(result: dict[str, Any]) -> bool:
    scores = result.get("scores", {})
    return all(float(scores.get(axis, 0.0)) >= 1.0 for axis in _required_axes(result))


def classify_failure(result: dict[str, Any]) -> dict[str, Any]:
    """Return a stable failure-attribution payload for a scored result."""
    status = str(result.get("status", "UNKNOWN"))
    scores = result.get("scores", {})
    notes_text = _notes_text(result)

    if _strict_pass(result):
        return {
            "domain": "pass",
            "subtype": "pass",
            "repair_owner": "none",
            "confidence": 1.0,
            "reason": "all required score axes pass",
        }

    if status == "PASS":
        return {
            "domain": "validation",
            "subtype": "scoring_schema",
            "repair_owner": "verification_pipeline",
            "confidence": 0.95,
            "reason": "status is PASS but required axes are not all passing",
        }

    if "missing_generated_files" in notes_text or "result_json" in notes_text and "none" in notes_text:
        return {
            "domain": "validation",
            "subtype": "file_artifact",
            "repair_owner": "generation_or_materialization",
            "confidence": 0.95,
            "reason": "required DUT/testbench artifact is missing",
        }

    if "behavior_eval_timeout" in notes_text:
        return {
            "domain": "validation",
            "subtype": "checker_runtime",
            "repair_owner": "verification_pipeline",
            "confidence": 0.95,
            "reason": "Python-side behavior checker timed out before a reliable verdict",
        }

    if "evas_timeout" in notes_text or "timeoutexpired" in notes_text:
        return {
            "domain": "validation",
            "subtype": "simulator_runtime",
            "repair_owner": "ambiguous_runtime",
            "confidence": 0.85,
            "reason": "EVAS simulation timed out before a reliable behavior verdict",
        }

    if "tran.csv missing" in notes_text:
        return {
            "domain": "validation",
            "subtype": "missing_waveform",
            "repair_owner": "verification_pipeline_or_harness",
            "confidence": 0.9,
            "reason": "waveform CSV is missing, so behavior cannot be judged",
        }

    interface_markers = (
        "missing_include=",
        "undefined_module=",
        "primary_dut_uploaded_but_not_referenced_by_tb",
        "no_ahdl_va_include_in_tb",
        "colon_instance_syntax",
        "unsupported_tb_directives",
    )
    if any(marker in notes_text for marker in interface_markers) or status == "FAIL_TB_COMPILE":
        return {
            "domain": "validation",
            "subtype": "interface_or_harness",
            "repair_owner": "candidate_or_harness_interface",
            "confidence": 0.9,
            "reason": "testbench/DUT linkage or harness execution failed before behavior checking",
        }

    syntax_markers = (
        "dut_not_compiled",
        "spectre_strict:verilog_initial_begin",
        "spectre_strict:conditional_transition",
        "spectre_strict:conditional_cross",
        "spectre_strict:genvar_inside_analog",
        "spectre_strict:dynamic_analog_vector_index",
        "spectre_strict:digital_verilog_syntax",
    )
    if any(marker in notes_text for marker in syntax_markers) or status == "FAIL_DUT_COMPILE":
        return {
            "domain": "validation",
            "subtype": "candidate_compile",
            "repair_owner": "llm_candidate_syntax",
            "confidence": 0.9,
            "reason": "candidate failed compile/preflight before behavior could be judged",
        }

    if status == "FAIL_INFRA":
        return {
            "domain": "validation",
            "subtype": "infrastructure",
            "repair_owner": "verification_pipeline",
            "confidence": 0.8,
            "reason": "infrastructure failure blocked a trustworthy behavior verdict",
        }

    sim_required = "sim_correct" in _required_axes(result)
    sim_failed = float(scores.get("sim_correct", 1.0)) < 1.0
    compile_ok = float(scores.get("dut_compile", 0.0)) >= 1.0 and float(scores.get("tb_compile", 0.0)) >= 1.0
    if status == "FAIL_SIM_CORRECTNESS" or (sim_required and sim_failed and compile_ok):
        return {
            "domain": "functional",
            "subtype": "behavior_mismatch",
            "repair_owner": "dut_behavior_or_testbench_behavior",
            "confidence": 0.9,
            "reason": "compile/simulation completed and behavior checker reported a mismatch",
        }

    return {
        "domain": "validation",
        "subtype": "unknown_validation",
        "repair_owner": "manual_triage",
        "confidence": 0.5,
        "reason": "failure does not match a known trustworthy behavior-mismatch pattern",
    }


def attach_failure_attribution(result: dict[str, Any]) -> dict[str, Any]:
    attribution = classify_failure(result)
    result["failure_attribution"] = attribution
    result["failure_domain"] = attribution["domain"]
    result["repair_owner"] = attribution["repair_owner"]
    return result
