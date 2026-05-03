#!/usr/bin/env python3
"""Adaptive EVAS repair pilot.

This runner is intentionally small and experimental. It tests whether EVAS
feedback can drive a fast repair loop without committing to a fixed round count.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path

from build_repair_prompt import build_evas_guided_repair_prompt, metric_gap_summary
from compile_skill_library import render_compile_skill_guidance, select_compile_skills
from compile_vector_unroll_guard import apply_vector_unroll_guard
from generate import (
    build_enhancement_payload,
    build_prompt,
    call_model,
    extract_module_signature,
    list_bench_task_dirs,
    list_task_dirs,
    read_meta,
)
from interface_parameter_guard import check_interface_parameters, format_issue_notes
from run_model_assisted_loop import _model_slug, _save_generated_response
from score import find_generated_dir, score_one_task

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASKS = ["dwa_ptr_gen_no_overlap_smoke", "dwa_wraparound_smoke"]

_METRIC_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)=([^\s,;]+)")
_OBSERVABLE_NOTE_MARKERS = (
    "missing ",
    "tran.csv missing",
    "insufficient_post_reset_samples",
    "too_few_edges",
    "too_few_clock_edges",
    "too_few_rising_edges",
    "seen_out_never_high",
)
_MAIN_MODULE_PATTERNS = [
    re.compile(r"Main module name:\s*`([^`]+)`", re.IGNORECASE),
    re.compile(r"Module name:\s*`([^`]+)`", re.IGNORECASE),
    re.compile(r"module named\s*`([^`]+)`", re.IGNORECASE),
]
_CONCRETE_DIAGNOSTIC_MARKERS = (
    "dynamic_analog_vector_index=",
    "interface_parameter_missing=",
    "conditional_cross=",
    "conditional_transition=",
    "digital_verilog_syntax=",
    "genvar_inside_analog=",
    "embedded_declaration=",
    "unsupported_tb_directives=",
    "evas_log_diagnostic=",
    "undefined_module=",
    "colon_instance_syntax_lines=",
    "nonincreasing_pwl_time=",
    "uncontinued_multiline_instance=",
    "evas_runtime_error=",
    "evas_compile_errors:",
    "missing dout_code",
    "missing dout_0..7",
    "bit_mismatch",
    "only_",
    "unique_codes=",
    "up_first=",
    "dn_first=",
)
_SYNTAX_ZERO_STRICT_MARKERS = (
    "dynamic_analog_vector_index=",
    "interface_parameter_missing=",
    "conditional_cross=",
    "conditional_transition=",
    "digital_verilog_syntax=",
    "genvar_inside_analog=",
    "embedded_declaration=",
    "unsupported_tb_directives=",
    "evas_log_diagnostic=",
    "undefined_module=",
    "colon_instance_syntax_lines=",
    "nonincreasing_pwl_time=",
    "uncontinued_multiline_instance=",
    "spectre_strict_preflight",
    "strict_preflight",
)
_SYNTAX_ZERO_RUNTIME_MARKERS = (
    "tran.csv missing",
    "tb_not_executed",
    "returncode=1",
    "evas_timeout",
    "evas_runtime_error",
    "timeout",
)


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def _json_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _parse_value(raw: str) -> float | str:
    try:
        return float(raw)
    except ValueError:
        return raw


def _extract_metrics(result: dict) -> dict[str, float | str]:
    metrics: dict[str, float | str] = {}
    for note in result.get("evas_notes", []):
        for key, raw in _METRIC_RE.findall(str(note)):
            metrics[key] = _parse_value(raw)
    return metrics


def _concrete_diagnostics(result: dict) -> list[str]:
    diagnostics: list[str] = []
    seen: set[str] = set()
    for raw in result.get("evas_notes", []):
        note = str(raw).strip()
        lowered = note.lower()
        if not any(marker in lowered for marker in _CONCRETE_DIAGNOSTIC_MARKERS):
            continue
        if note in seen:
            continue
        seen.add(note)
        diagnostics.append(note)
    return diagnostics[:10]


def _failure_subtype(result: dict) -> str:
    status = str(result.get("status", ""))
    if status == "PASS":
        return "pass"
    if status == "FAIL_DUT_COMPILE":
        return "dut_compile"
    if status == "FAIL_TB_COMPILE":
        return "tb_compile"
    notes = " ".join(str(note) for note in result.get("evas_notes", [])).lower()
    if "tran.csv missing" in notes or "tb_not_executed" in notes:
        return "simulation_artifact"
    if any(marker in notes for marker in _OBSERVABLE_NOTE_MARKERS):
        return "observability_contract"
    if status == "FAIL_SIM_CORRECTNESS":
        return "behavior_semantic"
    return "infra"


def _metric_float(metrics: dict[str, float | str], key: str, default: float = 0.0) -> float:
    value = metrics.get(key, default)
    return float(value) if isinstance(value, (int, float)) else default


def _metric_bool(metrics: dict[str, float | str], key: str) -> int:
    value = metrics.get(key)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value != 0)
    if isinstance(value, str):
        return int(value.strip().lower() in {"1", "true", "yes", "ok"})
    return 0


def _failure_phase_score(result: dict) -> int:
    """Reward useful failure-surface progress even when weighted score ties.

    EVAS repair often moves from "checker cannot read CSV columns" to
    "checker reads columns and reports a behavior metric" without changing the
    coarse weighted score.  That is real progress and should be kept as the
    next anchor candidate.
    """
    status = result.get("status")
    if status == "PASS":
        return 6
    notes = " ".join(str(note) for note in result.get("evas_notes", [])).lower()
    if status == "FAIL_SIM_CORRECTNESS":
        if "tran.csv missing" in notes or "tb_not_executed" in notes:
            return 2
        if "missing " in notes or "missing_" in notes:
            return 3
        if any(marker in notes for marker in _OBSERVABLE_NOTE_MARKERS):
            return 4
        return 5
    if status == "FAIL_TB_COMPILE":
        return 1
    if status == "FAIL_DUT_COMPILE":
        return 0
    return 0


def _syntax_blocker_count(result: dict) -> int:
    """Count compile/runtime blockers so partial syntax cleanup can be ranked.

    Several G repairs stay in the same coarse FAIL_DUT_COMPILE bucket after
    removing one error and exposing the next.  A lower blocker count is still
    progress and should not be discarded immediately.
    """
    notes = " ".join(str(note) for note in result.get("evas_notes", [])).lower()
    markers = (
        "digital_verilog_syntax=",
        "embedded_declaration=",
        "conditional_transition=",
        "conditional_cross=",
        "dynamic_analog_vector_index=",
        "genvar_inside_analog=",
        "unsupported_tb_directives=",
        "undefined_module=",
        "colon_instance_syntax_lines=",
        "evas_log_diagnostic=error:",
        "evas_runtime_error=",
        "dut_not_compiled",
        "tb_not_executed",
        "tran.csv missing",
    )
    return sum(notes.count(marker) for marker in markers)


def _classify_repair_layer(result: dict) -> str:
    """Route failures to the narrowest editable layer.

    The layer controls what the next repair round is allowed to change:
    compile/interface, observable harness, or DUT behavior.
    """
    if result.get("status") == "PASS":
        return "done"

    scores = result.get("scores", {})
    dut_compile = float(scores.get("dut_compile", 0.0))
    tb_compile = float(scores.get("tb_compile", 0.0))
    notes = " ".join(str(note) for note in result.get("evas_notes", [])).lower()

    if dut_compile < 1.0:
        return "compile_dut"
    if tb_compile < 1.0:
        return "compile_tb"
    if "tran.csv missing" in notes or "returncode=1" in notes or "tb_not_executed" in notes:
        return "runtime_interface"
    if any(marker in notes for marker in _OBSERVABLE_NOTE_MARKERS):
        return "observable"
    if result.get("status") == "FAIL_SIM_CORRECTNESS":
        return "behavior"
    return "infra"


def _progress_rank(task_id: str, result: dict) -> tuple:
    scores = result.get("scores", {})
    metrics = _extract_metrics(result)
    status = result.get("status", "FAIL")
    base = (
        int(status == "PASS"),
        float(scores.get("weighted_total", 0.0)),
        float(scores.get("dut_compile", 0.0)),
        float(scores.get("tb_compile", 0.0)),
        _failure_phase_score(result),
        -_syntax_blocker_count(result),
    )
    if "no_overlap" in task_id:
        return (
            *base,
            int(_metric_float(metrics, "max_active_cells") > 0),
            -_metric_float(metrics, "bad_ptr_rows", 99.0),
            -_metric_float(metrics, "overlap_count", 99.0),
            _metric_float(metrics, "max_active_cells"),
        )
    if "wraparound" in task_id:
        return (
            *base,
            -_metric_float(metrics, "bad_ptr_rows", 99.0),
            -_metric_float(metrics, "bad_count_rows", 99.0),
            min(_metric_float(metrics, "wrap_events"), 2.0),
            min(_metric_float(metrics, "split_wrap_rows"), 2.0),
        )
    if "pll" in task_id or "adpll" in task_id or "cppll" in task_id:
        late_ratio = _metric_float(metrics, "late_edge_ratio", 0.0)
        freq_ratio = _metric_float(metrics, "freq_ratio", 0.0)
        pre_ratio = _metric_float(metrics, "pre_ratio", 0.0)
        post_ratio = _metric_float(metrics, "post_ratio", 0.0)
        edge_progress = max(
            min(late_ratio, 1.0),
            1.0 if _metric_float(metrics, "fb", 0.0) > 0 else 0.0,
        )
        ratio_progress = max(
            1.0 - min(abs(late_ratio - 1.0), 1.0) if late_ratio else 0.0,
            1.0 - min(abs(freq_ratio - 1.0), 1.0) if freq_ratio else 0.0,
            1.0 - min(abs(pre_ratio - post_ratio), 1.0) if pre_ratio and post_ratio else 0.0,
        )
        return (
            *base,
            edge_progress,
            ratio_progress,
            _metric_bool(metrics, "vctrl_range_ok"),
            _metric_float(metrics, "pre_lock", 0.0),
            _metric_float(metrics, "post_lock", 0.0),
        )
    return base


def _compile_closure_rank(task_id: str, result: dict) -> tuple:
    """Rank candidates for official G compile-gate closure.

    This deliberately avoids behavior metric-gap information.  A candidate
    wins once the syntax/interface/runtime/observable gate is clear; after that
    behavior correctness is only reported by final scoring, not optimized here.
    """
    scores = result.get("scores", {})
    gate_state = _syntax_zero_gate_state(result)
    return (
        int(gate_state["cleared"]),
        float(scores.get("dut_compile", 0.0)),
        float(scores.get("tb_compile", 0.0)),
        _failure_phase_score(result),
        -len(gate_state["issues"]),
        -_syntax_blocker_count(result),
        int(result.get("status") == "PASS"),
        float(scores.get("weighted_total", 0.0)),
        task_id,
    )


def _result_rank(task_id: str, result: dict, *, compile_only_closure: bool = False) -> tuple:
    if compile_only_closure:
        return _compile_closure_rank(task_id, result)
    return _progress_rank(task_id, result)


def _copy_sample(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for path in sorted(src.glob("*")):
        if path.is_file():
            shutil.copy2(path, dst / path.name)


def _sanitize_quick_tb(sample_dir: Path, quick_maxstep: str) -> list[str]:
    """Remove heavy save directives that are unnecessary for checker columns."""
    edits: list[str] = []
    for tb in sample_dir.glob("*.scs"):
        lines = tb.read_text(encoding="utf-8", errors="ignore").splitlines()
        new_lines: list[str] = []
        for line in lines:
            stripped = line.strip().lower()
            if "saveahdlvars=all" in stripped:
                edits.append(f"removed saveahdlvars=all from {tb.name}")
                continue
            if "save=all" in stripped or "currents=all" in stripped:
                edits.append(f"removed broad save option from {tb.name}")
                continue
            updated_quotes = re.sub(r"=\s*'([^']+)'", r"=\1", line)
            if updated_quotes != line:
                edits.append(f"removed single-quoted parameter expression in {tb.name}: {line.strip()} -> {updated_quotes.strip()}")
                line = updated_quotes
            if quick_maxstep:
                updated = re.sub(r"\bmaxstep\s*=\s*0\.[0-9]+n\b", f"maxstep={quick_maxstep}", line)
                if updated != line:
                    edits.append(f"relaxed maxstep in {tb.name}: {line.strip()} -> {updated.strip()}")
                    line = updated
            new_lines.append(line)
        if new_lines != lines:
            tb.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return edits


def _materialize_syntax_zero_sanitizers(sample_dir: Path) -> list[str]:
    """Apply deterministic, syntax-only normalizations to the final sample.

    These edits do not encode task behavior.  They materialize the same public
    Spectre syntax cleanup used by the quick checker so the final sample is not
    scored differently from the accepted candidate.
    """
    edits: list[str] = []
    for tb in sample_dir.glob("*.scs"):
        text = tb.read_text(encoding="utf-8", errors="ignore")
        updated = re.sub(r"=\s*'([^']+)'", r"=\1", text)
        if updated != text:
            edits.append(f"removed_single_quoted_param_expr:{tb.name}")
            tb.write_text(updated, encoding="utf-8")
    return edits


def _first_file(path: Path, pattern: str) -> Path | None:
    matches = sorted(path.glob(pattern))
    return matches[0] if matches else None


def _interface_guard_fail_result(
    *,
    task_id: str,
    task_dir: Path,
    sample_dir: Path,
    output_root: Path,
    model_slug: str,
    sample_idx: int,
    notes: list[str],
) -> dict:
    meta = read_meta(task_dir)
    family = meta.get("family", "end-to-end")
    category = meta.get("category", "unknown")
    required_axes: list[str] = meta.get("scoring", ["dut_compile", "tb_compile", "sim_correct"])
    scores = {"dut_compile": 0.0, "tb_compile": 0.0, "sim_correct": 0.0, "weighted_total": 0.0}
    gen_meta_path = sample_dir / "generation_meta.json"
    gen_meta: dict = {}
    if gen_meta_path.exists():
        try:
            gen_meta = json.loads(gen_meta_path.read_text(encoding="utf-8"))
        except Exception:
            gen_meta = {}
    dut_path = _first_file(sample_dir, "*.va")
    tb_path = _first_file(sample_dir, "*.scs")
    result = {
        "model": model_slug,
        "task_id": task_id,
        "family": family,
        "category": category,
        "sample_idx": sample_idx,
        "temperature": 0.0,
        "top_p": 1.0,
        "status": "FAIL_INFRA",
        "scores": scores,
        "required_axes": required_axes,
        "artifacts": {
            "dut_path": str(dut_path) if dut_path else None,
            "tb_path": str(tb_path) if tb_path else None,
            "result_json": str(output_root / task_id / "result.json"),
        },
        "generation_meta": gen_meta,
        "evas_notes": notes,
        "evas_timing": {},
    }
    _json_write(output_root / task_id / "result.json", result)
    return result


def _freeze_testbench_from(src_sample: Path, dst_sample: Path) -> list[str]:
    src_tbs = sorted(src_sample.glob("*.scs"))
    if not src_tbs:
        return []
    for existing in dst_sample.glob("*.scs"):
        existing.unlink()
    copied: list[str] = []
    for src in src_tbs:
        dst = dst_sample / src.name
        shutil.copy2(src, dst)
        copied.append(src.name)
    return copied


def _freeze_veriloga_from(src_sample: Path, dst_sample: Path) -> list[str]:
    src_vas = sorted(src_sample.glob("*.va"))
    if not src_vas:
        return []
    for existing in dst_sample.glob("*.va"):
        existing.unlink()
    copied: list[str] = []
    for src in src_vas:
        dst = dst_sample / src.name
        shutil.copy2(src, dst)
        copied.append(src.name)
    return copied


def _main_module_name(task_dir: Path) -> str | None:
    prompt = task_dir.joinpath("prompt.md").read_text(encoding="utf-8", errors="ignore")
    for pattern in _MAIN_MODULE_PATTERNS:
        match = pattern.search(prompt)
        if match:
            return match.group(1).strip()
    return None


def _protected_dut_modules(task_dir: Path, dst_sample: Path) -> set[str]:
    """Return generated DUT modules that gold harness freeze must not overwrite.

    Gold harness directories often contain Verilog-A stimulus/helper modules in
    addition to the reference DUT.  During behavior-only repair we want the
    verifier harness and helpers, but we must preserve the candidate's DUT.
    Protect explicitly named DUT modules from the prompt; fall back to candidate
    modules only when no prompt contract can be inferred.
    """
    prompt = task_dir.joinpath("prompt.md").read_text(encoding="utf-8", errors="ignore")
    protected: set[str] = set()

    main_module = _main_module_name(task_dir)
    if main_module:
        protected.add(main_module)

    for match in re.finditer(
        r"\bmodules?\s+named\s+((?:`[^`]+`(?:\s*(?:,|and)\s*)?)+)",
        prompt,
        flags=re.IGNORECASE,
    ):
        protected.update(re.findall(r"`([^`]+)`", match.group(1)))

    for match in re.finditer(
        r"\b(?:ADC|DAC|DUT|main)\s+module\s+`([^`]+)`",
        prompt,
        flags=re.IGNORECASE,
    ):
        protected.add(match.group(1))

    if protected:
        return protected
    return _declared_modules(sorted(dst_sample.glob("*.va")))


def _declared_modules(paths: list[Path]) -> set[str]:
    modules: set[str] = set()
    for path in paths:
        signature = extract_module_signature(path)
        if signature:
            modules.add(signature[0])
    return modules


def _freeze_gold_harness(task_dir: Path, dst_sample: Path) -> list[str]:
    """Use the benchmark verifier harness while preserving generated DUT code.

    This is not copying the gold DUT. We copy Spectre testbenches and helper
    stimulus modules, but skip the Verilog-A file whose stem matches the task's
    main DUT module. That lets the loop evaluate only the repaired DUT behavior.
    """
    gold_dir = task_dir / "gold"
    if not gold_dir.exists():
        return []
    protected_modules = _protected_dut_modules(task_dir, dst_sample)
    copied: list[str] = []

    for existing in dst_sample.glob("*.scs"):
        existing.unlink()

    for src in sorted(gold_dir.glob("*.scs")):
        shutil.copy2(src, dst_sample / src.name)
        copied.append(src.name)

    for src in sorted(gold_dir.glob("*.va")):
        signature = extract_module_signature(src)
        gold_module = signature[0] if signature else src.stem
        if gold_module in protected_modules:
            continue
        shutil.copy2(src, dst_sample / src.name)
        copied.append(src.name)
    return copied


def _gold_harness_parameter_names(task_dir: Path) -> list[str]:
    names: set[str] = set()
    for tb in sorted((task_dir / "gold").glob("*.scs")):
        text = tb.read_text(encoding="utf-8", errors="ignore")
        for name in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=", text):
            if name not in {"type", "val0", "val1", "period", "delay", "rise", "fall", "width", "wave", "stop", "maxstep"}:
                names.add(name)
    return sorted(names)


def _layer_policy_section(layer: str, task_dir: Path) -> str:
    if layer == "compile_dut":
        return (
            "\n\n# Layered Only-Repair Policy: DUT Compile\n"
            "The current failure is in DUT compile/interface. Change only the Verilog-A DUT files needed to compile. "
            "Preserve the testbench stimulus, save statements, tran setup, module intent, and behavior policy unless "
            "a compile error directly requires an interface adjustment.\n"
        )
    if layer == "compile_tb":
        return (
            "\n\n# Layered Only-Repair Policy: Testbench Compile\n"
            "The current failure is in testbench compile/interface. Change only the Spectre testbench wiring, includes, "
            "instances, parameters, save statements, or tran setup needed to compile. Preserve DUT Verilog-A behavior.\n"
        )
    if layer == "observable":
        return (
            "\n\n# Layered Only-Repair Policy: Observable Harness\n"
            "The current failure is an observable/stimulus problem, not a DUT behavior problem. The runner will preserve "
            "the existing Verilog-A DUT files and evaluate only your repaired Spectre testbench/harness. Focus on reset "
            "release, transient stop, required save names, include paths, and stimulus coverage. Do not redesign DUT logic.\n"
        )
    if layer == "runtime_interface":
        return (
            "\n\n# Layered Only-Repair Policy: Runtime Interface/Harness\n"
            "The current failure is `returncode=1`, `tran.csv missing`, or equivalent runtime artifact loss after strict "
            "preflight. This is usually a coupled DUT/TB interface problem. Repair the smallest consistent set of "
            "Verilog-A module declarations, file names, ahdl_include lines, Spectre instance node lists, reset/enable "
            "sources, and save/tran setup needed to produce a stable `tran.csv`. Do not tune semantic constants until "
            "the waveform CSV exists.\n"
        )
    if layer == "behavior":
        harness_params = _gold_harness_parameter_names(task_dir)
        param_text = ", ".join(f"`{name}`" for name in harness_params) if harness_params else "the verifier parameters"
        return (
            "\n\n# Layered Only-Repair Policy: DUT Behavior\n"
            "The current failure is behavior correctness. The runner will use the benchmark verifier harness for stimulus "
            "and saved observables, so repair the DUT behavior only. Do not spend tokens redesigning the Spectre testbench. "
            "Preserve the required DUT module name and ports exactly.\n"
            f"The DUT must accept these verifier parameters if present in the harness: {param_text}. "
            "Use the verifier supply parameter (for example `vdd`) for output HIGH and verifier initialization parameters "
            "for reset state when those names are present.\n"
        )
    return (
        "\n\n# Layered Only-Repair Policy: Infrastructure\n"
        "The failure is not yet classified as compile, observable, or behavior. Make the smallest change needed to expose "
        "a concrete EVAS diagnostic, and do not rewrite working layers.\n"
    )


def _syntax_zero_gate_state(result: dict) -> dict:
    layer = _classify_repair_layer(result)
    scores = result.get("scores", {})
    status = result.get("status")
    notes = " ".join(str(note) for note in result.get("evas_notes", [])).lower()
    issues: list[str] = []

    if float(scores.get("dut_compile", 0.0)) < 1.0:
        issues.append("dut_compile_not_zero")
    if float(scores.get("tb_compile", 0.0)) < 1.0:
        issues.append("tb_compile_not_zero")
    for marker in _SYNTAX_ZERO_RUNTIME_MARKERS:
        if marker in notes:
            issues.append(f"runtime_artifact:{marker}")
    for marker in _SYNTAX_ZERO_STRICT_MARKERS:
        if marker in notes:
            issues.append(f"strict_preflight:{marker}")
    if any(marker in notes for marker in _OBSERVABLE_NOTE_MARKERS):
        issues.append("observable_surface_not_zero")
    if status == "FAIL_INFRA" and not issues:
        issues.append("infra_unclassified")

    return {
        "layer": layer,
        "cleared": status == "PASS" or (layer == "behavior" and not issues),
        "issues": issues[:12],
    }


def _syntax_zero_gate_policy_section(layer: str, result: dict) -> str:
    state = _syntax_zero_gate_state(result)
    issues = ", ".join(state["issues"]) if state["issues"] else "none"
    notes = " ".join(str(note) for note in result.get("evas_notes", [])).lower()
    if state["cleared"]:
        return (
            "\n\n# Syntax-Zero Gate (Condition G): Cleared\n"
            "The compile/interface/runtime/observable gate is currently clear, so this round may repair behavior. "
            "Keep the working module names, ports, ahdl_include lines, saved signals, transient setup, and CSV-producing "
            "testbench structure stable while changing only the DUT behavior needed by the EVAS metric gap.\n"
        )

    if layer == "compile_dut":
        target = (
            "Fix Verilog-A legality and DUT interface first: module declaration, ports, disciplines, parameters, "
            "analog block syntax, and Spectre-compatible constructs."
        )
    elif layer == "compile_tb":
        target = (
            "Fix the Spectre testbench first: ahdl_include, instance node order, file names, parameter names, "
            "stimulus sources, save directives, and tran statement."
        )
    elif layer == "runtime_interface":
        target = (
            "Fix the runtime artifact path first: the simulation must execute and produce the required waveform CSV "
            "with the expected saved columns."
        )
    elif layer == "observable":
        target = (
            "Fix observability first: reset/stimulus coverage, saved signal names, transient duration, and required "
            "columns. Do not redesign the DUT behavior while the checker cannot observe the intended surface."
        )
    else:
        target = (
            "Expose a stable compile/runtime/observable diagnostic first, then repair only that failing surface."
        )

    strong_templates: list[str] = []
    if "integer_function_cast" in notes or "integer(...)" in notes:
        strong_templates.extend([
            "- `integer(...)` is not a Verilog-A cast. Remove every `integer(expr)` occurrence. Use declared `integer` variables and integer arithmetic assignments instead.",
            "- If a real-to-integer conversion is needed, assign the expression to an `integer` state variable directly and avoid function-style casts in the source text.",
        ])
    if "embedded_declaration=" in notes:
        strong_templates.extend([
            "- Move every `integer`, `real`, `parameter`, and `genvar` declaration out of `analog begin`, `if`, `case`, event, and loop bodies. Declarations must live at module scope before `analog begin`.",
            "- Do not introduce replacement local declarations while editing; reuse module-scope temporaries.",
        ])
    if "conditional_transition=" in notes or "transition() contribution is inside" in notes:
        strong_templates.extend([
            "- Replace conditional `transition()` contributions with held target variables: update `real out_target` inside events/branches, then drive `V(out) <+ transition(out_target, 0, tr, tf);` exactly once and unconditionally.",
            "- No `transition()` may appear inside `if`, `else`, `case`, `for`, `while`, or event branches whose execution can skip the contribution.",
            "- For many outputs, use a generic multi-output target-buffer pattern: declare `real out0_t, out1_t, ...` or `real out_t[0:N-1]` at module scope; update those targets inside event/condition code; drive all electrical outputs once at analog top level.",
            "- A loop around `transition()` is legal only when the loop variable is a module-scope `genvar`. A loop with `integer i` is runtime control flow and must not contain `V(out[i]) <+ transition(...)`.",
            "- If there are fewer than about 32 public outputs, prefer explicit unrolled contributions for the compile-clean repair: `V(out_0) <+ transition(out0_t, 0, tr, tf);`, `V(out_1) <+ transition(out1_t, 0, tr, tf);`, and so on.",
        ])
    if "conditional_cross=" in notes or "@(cross" in notes and "conditional" in notes:
        strong_templates.extend([
            "- `@(cross(...))` event statements must not be nested inside runtime `if`, `else`, `case`, `for`, or `while` branches. Declare each cross event unconditionally at analog top level.",
            "- To keep conditional behavior, move the condition inside the event body: `@(cross(expr,+1)) begin if (enable_or_mode) state = ...; end`.",
            "- For hysteresis, use separate unconditional rising and falling cross events, each with its fixed threshold expression, and gate only the state update inside the event body.",
        ])
    if "dynamic_analog_vector_index=" in notes:
        strong_templates.extend([
            "- Runtime integer indices inside `V(bus[i])` are not allowed. Replace each offending access with fixed-index code, for example `V(bus[0])`, `V(bus[1])`, ... through the required width.",
            "- For output buses, prefer explicit unrolled contributions for this repair. Do not use `V(out[i])` with `integer i` inside an analog loop.",
            "- If the testbench connects scalar nodes such as `d15 d14 ... d0`, declare scalar ports such as `din_15, din_14, ...` instead of one vector port, then unroll every `V(din_k)` access explicitly.",
        ])
    if "unsupported_tb_directives=" in notes or "single_quote" in notes:
        strong_templates.extend([
            "- Spectre testbenches must not use shell-style single-quoted directives or strings. Replace single quotes with Spectre-compatible double-quoted paths/strings or plain numeric tokens.",
            "- Keep the testbench in `simulator lang=spectre` and preserve `ahdl_include`, instance, `save`, and `tran` structure while fixing only the illegal directive syntax.",
        ])
    if "model " in notes and " not found" in notes:
        strong_templates.extend([
            "- If EVAS reports `Model ... not found`, make the instance model name exactly match the `module` identifier in the generated Verilog-A file and make `ahdl_include` point to that file.",
        ])
    if "undefined_module=" in notes:
        strong_templates.extend([
            "- If EVAS reports `undefined_module=<name>`, the generated Verilog-A must declare `module <name>(...)` or the Spectre instance must use the actual declared module name. Do not leave a filename/module-name mismatch.",
            "- For bugfix/spec-to-VA tasks, preserve the exact DUT module name requested by the public prompt and verifier harness; helper modules may be included only in addition to that DUT module.",
        ])
    if "instance_port_count_mismatch=" in notes:
        strong_templates.extend([
            "- If an instance has more scalar nodes than the module port list, rewrite the Verilog-A module port list to the same scalar ports used by the Spectre instance, in the same order.",
            "- Do not rely on Verilog-A vector ports when the Spectre testbench uses scalar node names; unroll the ports and contributions explicitly.",
        ])
    if "sourced_port_voltage_drive=" in notes:
        strong_templates.extend([
            "- Do not connect a DUT supply or input port directly to literal `0` in the instance when strict preflight flags it. Use a named node such as `vss` and drive it with `Vss (vss 0) vsource dc=0`.",
            "- Keep output ports on unsourced nodes; only stimulus/supply nodes should be driven by `vsource` elements.",
        ])
    if "cannot find va file" in notes:
        strong_templates.extend([
            "- If EVAS reports `Cannot find VA file`, make the `ahdl_include` filename exactly match a generated `.va` artifact in the same sample directory.",
        ])
    if "invalid source" in notes or "failed to parse" in notes:
        strong_templates.extend([
            "- If EVAS reports an invalid source or parse error, repair only the Spectre netlist syntax first; do not change DUT behavior until the testbench parses and runs.",
        ])
    if "nonincreasing_pwl_time=" in notes:
        strong_templates.extend([
            "- Spectre PWL time entries must be strictly increasing. Do not encode an ideal step with duplicate timestamps such as `4n ... 4n ...`.",
            "- Replace every duplicate-time PWL step with a tiny finite transition window that preserves intent, for example hold until `3.99n` and change at `4n`, or use adjacent times separated by the task's maxstep scale.",
        ])
    if "uncontinued_multiline_instance=" in notes:
        strong_templates.extend([
            "- Spectre does not join bare multi-line instance node lists. Put the entire instance on one line, or end every continued instance line with `\\`.",
            "- Do not split `XDUT (...) model` across lines without explicit continuation; otherwise later node names are parsed as new undefined instances.",
        ])
    if "tran.csv missing" in notes or "tb_not_executed" in notes:
        strong_templates.extend([
            "- `tran.csv missing` means the run did not reach a usable transient waveform. First ensure the TB has one valid `tran` statement, all included VA modules compile, all instances reference existing modules, and the `save` list names real nodes.",
        ])
    if "missing_generated_files" in notes or "testbench.scs" in notes:
        strong_templates.extend([
            "- End-to-end and testbench-generation tasks must output a complete fenced `spectre` testbench block as well as any required Verilog-A block. A Verilog-A-only response is not acceptable for compile closure.",
            "- If the prompt is long, output a minimal compile-clean testbench: `simulator lang=spectre`, needed `ahdl_include` lines, supplies/stimulus, one `XDUT` instance, required `save` nodes, and one `tran` statement.",
        ])

    template_text = ""
    if strong_templates:
        deduped: list[str] = []
        seen: set[str] = set()
        for item in strong_templates:
            if item in seen:
                continue
            seen.add(item)
            deduped.append(item)
        template_text = (
            "\nMandatory signature-specific compile-clean templates:\n"
            + "\n".join(deduped[:12])
            + "\n"
        )

    return (
        "\n\n# Syntax-Zero Gate (Condition G)\n"
        f"Current gate layer: `{layer}`. Gate issues: {issues}.\n"
        f"{target}\n"
        f"{template_text}"
        "This round is not allowed to tune semantic constants, gains, ratios, thresholds, lock criteria, quantization "
        "policy, or state-machine behavior unless the change is directly required to clear the gate. The acceptance "
        "target for this round is zero syntax/interface/runtime/observable errors; behavior optimization starts only "
        "after DUT compile, TB compile, strict preflight, simulation execution, and required observables are stable.\n"
    )


def _compile_closure_gate_cleared(result: dict) -> bool:
    return bool(_syntax_zero_gate_state(result).get("cleared"))


def _file_block(path: Path) -> str:
    lang = "spectre" if path.suffix.lower() == ".scs" else "verilog-a"
    text = path.read_text(encoding="utf-8", errors="ignore").rstrip()
    return f"# File: {path.name}\n```{lang}\n{text}\n```"


def _candidate_sections(sample_dir: Path) -> list[str]:
    sections: list[str] = []
    for va_path in sorted(sample_dir.glob("*.va")):
        sections.append(_file_block(va_path))
    for tb_path in sorted(sample_dir.glob("*.scs")):
        sections.append(_file_block(tb_path))
    if not sections:
        sections.append("No previous candidate files were found.")
    return sections


def _compile_gate_score_summary(result: dict) -> str:
    scores = result.get("scores", {})
    notes = result.get("evas_notes") or result.get("notes") or []
    spectre_notes = result.get("spectre_notes", [])
    all_notes = [str(note) for note in notes]
    all_notes.extend(str(note) for note in spectre_notes if note not in notes)
    note_text = "\n".join(f"- {note}" for note in all_notes[:24]) or "- <none>"
    diagnostics = "\n".join(f"- {note}" for note in _concrete_diagnostics(result)) or "- <none>"
    gate_state = _syntax_zero_gate_state(result)
    issues = "\n".join(f"- {issue}" for issue in gate_state["issues"]) or "- <none>"
    return textwrap.dedent(
        f"""\
        Current validator status: {result.get("status", "<unknown>")}
        Current gate layer: {gate_state["layer"]}
        Gate cleared: {gate_state["cleared"]}

        Scores:
        - dut_compile: {scores.get("dut_compile", "<missing>")}
        - tb_compile: {scores.get("tb_compile", "<missing>")}
        - sim_correct: {scores.get("sim_correct", "<missing>")}
        - weighted_total: {scores.get("weighted_total", "<missing>")}

        Gate issues:
        {issues}

        Concrete compile/interface/runtime diagnostics:
        {diagnostics}

        Validator notes:
        {note_text}
        """
    ).strip()


def _compile_history_section(history: list[dict]) -> str:
    if not history:
        return "No previous compile-closure repair rounds."
    lines = ["Previous compile-closure rounds:"]
    for item in history[-4:]:
        diagnostics = item.get("concrete_diagnostics") or item.get("evas_notes") or []
        diag_text = "; ".join(str(note) for note in diagnostics[:4]) or "<none>"
        lines.append(
            f"- R{item.get('round')}: status={item.get('status')} "
            f"layer={item.get('result_layer')} progress={item.get('progress_label')} diagnostics={diag_text}"
        )
    return "\n".join(lines)


def _compile_skill_guidance_section(result: dict, *, enabled: bool) -> str:
    if not enabled:
        return "# Routed Compile Skills\nCompile skill guidance disabled for this run."
    notes = [str(note) for note in (result.get("evas_notes") or result.get("notes") or [])]
    notes.extend(_concrete_diagnostics(result))
    selected = select_compile_skills(notes)
    if not selected:
        return "# Routed Compile Skills\nNo compile skills matched the current validator notes."
    skill_ids = [skill.id for skill in selected]
    guidance = render_compile_skill_guidance(skill_ids)
    return (
        "# Routed Compile Skills\n"
        f"Selected compile skills: {', '.join(skill_ids)}\n\n"
        f"{guidance.strip()}"
    )


def _compile_only_closure_prompt(
    *,
    task_dir: Path,
    sample_dir: Path,
    result: dict,
    history: list[dict],
    round_idx: int,
    public_spec_mode: str,
    include_mechanism: bool,
    include_compile_skills: bool,
) -> str:
    """Build official-G compile-closure prompt without behavior checker leakage."""
    meta = read_meta(task_dir)
    family = meta.get("family", "end-to-end")
    original_prompt = build_prompt(
        task_dir,
        include_checker=False,
        include_skill=False,
        public_spec_mode=public_spec_mode,
        enhancement_mode="none",
    )
    mechanism_payload = build_enhancement_payload(task_dir, "mechanism") if include_mechanism else {"text": ""}
    condition_label = (
        "official Condition G compile-closure step"
        if include_mechanism
        else "Condition C compile-closure ablation step"
    )
    allowed_guidance = (
        "the public Condition G mechanism guidance, "
        if include_mechanism
        else ""
    )
    candidate_text = "\n\n".join(_candidate_sections(sample_dir))
    layer = _classify_repair_layer(result)
    gate_policy = _syntax_zero_gate_policy_section(layer, result)
    score_text = _compile_gate_score_summary(result)
    history_text = _compile_history_section(history)
    compile_skill_text = _compile_skill_guidance_section(result, enabled=include_compile_skills)

    return textwrap.dedent(
        f"""\
        You are running the {condition_label} for the vaEVAS ADFGI benchmark.

        Scope:
        - This is a compile/interface/runtime/observable gate repair, not a behavior-optimization round.
        - Use only the public task prompt/spec, {allowed_guidance}the current candidate files, and validator compile/runtime notes.
        - Do not use gold code, checker source, hidden expected values, private thresholds, or behavior metric-gap targets.
        - Do not tune semantic constants, gains, ratios, thresholds, quantization policy, lock criteria, or state-machine behavior unless the edit is directly required to clear the compile/interface/runtime/observable gate.
        - Once the candidate reaches a behavior-only failure or PASS, the runner stops instead of asking you to repair behavior.

        Artifact contract:
        - Task family: `{family}`.
        - Preserve required module names, port order, parameters, filenames, include relationships, saved observables, and public waveform-column names from the task.
        - Output complete replacement code blocks only.
        - Do not include explanations outside code blocks.
        - Use fenced `verilog-a` blocks for Verilog-A files and fenced `spectre` blocks for Spectre testbenches.
        - Prefer the smallest compile-clean edit; copy unchanged code exactly when possible.
        - While fixing the current failure, do not revert any fix that resolved a prior round's failure.

        Attempt round: {round_idx}

        # Current Gate Feedback

        {score_text}

        {gate_policy.strip()}

        # Compile-Closure History

        {history_text}

        {compile_skill_text}

        # Public Condition G Mechanism Guidance

        {mechanism_payload.get("text", "").strip() or "Mechanism guidance disabled for this run."}

        # Original Public Task Prompt

        {original_prompt.strip()}

        # Current Candidate Files

        {candidate_text}
        """
    ).strip() + "\n"


def _score_quick(
    *,
    task_id: str,
    task_dir: Path,
    sample_dir: Path,
    output_root: Path,
    model_slug: str,
    sample_idx: int,
    timeout_s: int,
    quick_maxstep: str,
) -> dict:
    quick_sample = output_root / "_quick_samples" / task_id / sample_dir.name
    _copy_sample(sample_dir, quick_sample)
    edits = _sanitize_quick_tb(quick_sample, quick_maxstep)
    guard_issues = check_interface_parameters(quick_sample)
    result = score_one_task(
        task_id,
        task_dir,
        quick_sample,
        output_root,
        model=model_slug,
        sample_idx=sample_idx,
        temperature=0.0,
        top_p=1.0,
        timeout_s=timeout_s,
    )
    if guard_issues:
        # Spectre normally treats extra/unknown Verilog-A instance parameters as
        # warnings.  Do not let this older guard mask real compile blockers such
        # as integer casts, dynamic analog vector indices, or conditional
        # transition contributions.
        result.setdefault("evas_notes", []).extend(
            ["interface_parameter_guard=warning", *format_issue_notes(guard_issues)]
        )
    if edits:
        result.setdefault("evas_notes", []).insert(0, "quick_sanitize=" + ";".join(edits))
    if edits or guard_issues:
        _json_write(output_root / task_id / "result.json", result)
    return result


def _task_lookup(task_ids: list[str], bench_dir: str = "") -> list[tuple[str, Path]]:
    selected = set(task_ids)
    if bench_dir:
        bench_path = Path(bench_dir)
        if not bench_path.is_absolute():
            bench_path = ROOT / bench_path
        tasks = [(tid, path) for tid, path in list_bench_task_dirs(bench_path, selected=selected)]
    else:
        tasks = [(tid, path) for tid, path in list_task_dirs(selected=selected)]
    found = {tid for tid, _ in tasks}
    missing = sorted(selected - found)
    if missing:
        raise SystemExit(f"Missing task ids: {', '.join(missing)}")
    return tasks


def _existing_result_path(result_root: str, task_id: str) -> Path | None:
    if not result_root:
        return None
    task_root = Path(result_root) / task_id
    for filename in ("result.json", "evas_result.json"):
        candidate = task_root / filename
        if candidate.exists():
            return candidate
    return None


def run_task(args: argparse.Namespace, task_id: str, task_dir: Path) -> dict:
    model_slug = _model_slug(args.model)
    out_root = Path(args.output_root)
    gen_root = Path(args.generated_root) / model_slug / task_id
    gen_root.mkdir(parents=True, exist_ok=True)
    final_dir = Path(args.generated_root) / model_slug / task_id / f"sample_{args.sample_idx}"
    best_result_path = out_root / "best" / task_id / "result.json"

    if args.resume and best_result_path.exists() and final_dir.exists():
        result = json.loads(best_result_path.read_text(encoding="utf-8"))
        print(f"[adaptive] {task_id} resume best={best_result_path} status={result.get('status')}")
        return result

    candidate_generated_dirs = [args.source_generated_dir, *args.candidate_generated_dir]
    candidate_result_roots = [args.initial_result_root, *args.candidate_result_root]
    while len(candidate_result_roots) < len(candidate_generated_dirs):
        candidate_result_roots.append("")

    initial_candidates: list[dict] = []
    for idx, (generated_dir, result_root) in enumerate(zip(candidate_generated_dirs, candidate_result_roots)):
        source_sample = find_generated_dir(Path(generated_dir), model_slug, task_id, args.sample_idx)
        if source_sample is None:
            if idx == 0:
                raise SystemExit(f"Missing source sample for {model_slug}/{task_id}")
            continue
        result_path = _existing_result_path(result_root, task_id)
        if result_path and result_path.exists():
            result = json.loads(result_path.read_text(encoding="utf-8"))
            print(f"[adaptive] {task_id} R0 candidate{idx} reuse_result={result_path}")
        else:
            result = _score_quick(
                task_id=task_id,
                task_dir=task_dir,
                sample_dir=source_sample,
                output_root=out_root / f"round0_candidate{idx}",
                model_slug=model_slug,
                sample_idx=args.sample_idx,
                timeout_s=args.timeout_s,
                quick_maxstep=args.quick_maxstep,
            )
        rank = _result_rank(task_id, result, compile_only_closure=args.compile_only_closure)
        initial_candidates.append(
            {
                "idx": idx,
                "generated_dir": generated_dir,
                "result_root": result_root,
                "sample": source_sample,
                "result": result,
                "rank": rank,
            }
        )
        print(f"[adaptive] {task_id} R0 candidate{idx} {result.get('status')} rank={rank}")

    if not initial_candidates:
        raise SystemExit(f"Missing source samples for {model_slug}/{task_id}")

    selected_candidate = max(initial_candidates, key=lambda item: item["rank"])
    best_sample = selected_candidate["sample"]
    best_result = selected_candidate["result"]
    best_rank = _result_rank(task_id, best_result, compile_only_closure=args.compile_only_closure)
    best_layer = _classify_repair_layer(best_result)
    anchor_sample = best_sample
    anchor_result = best_result
    history: list[dict] = []
    no_progress = 0

    print(f"[adaptive] {task_id} R0 {best_result.get('status')} layer={best_layer} rank={best_rank}")

    for round_idx in range(1, args.max_rounds + 1):
        if best_result.get("status") == "PASS":
            break
        if args.compile_only_closure and _compile_closure_gate_cleared(best_result):
            print(f"[adaptive] {task_id} compile-closure gate clear; stop before behavior repair")
            break
        round_start = time.perf_counter()
        layer = _classify_repair_layer(anchor_result)
        if args.compile_only_closure:
            prompt = _compile_only_closure_prompt(
                task_dir=task_dir,
                sample_dir=anchor_sample,
                result=anchor_result,
                history=history,
                round_idx=round_idx,
                public_spec_mode=args.repair_public_spec_mode,
                include_mechanism=not args.no_repair_skill,
                include_compile_skills=args.compile_skill_guidance,
            )
        else:
            prompt = build_evas_guided_repair_prompt(
                task_dir,
                anchor_sample,
                anchor_result,
                history=history,
                include_skill=not args.no_repair_skill,
                include_contract_diagnosis=not args.disable_contract_diagnosis,
                public_spec_mode=args.repair_public_spec_mode,
                loop_context={
                    "attempt_round": round_idx,
                    "best_round": history[-1]["round"] if history else 0,
                    "best_status": best_result.get("status"),
                    "best_scores": best_result.get("scores", {}),
                    "best_metric_gap": metric_gap_summary(task_dir, best_result),
                    "best_failure_subtype": _failure_subtype(best_result),
                },
            )
            if args.layered_only_repair:
                prompt += _layer_policy_section(layer, task_dir)
            if args.syntax_zero_gate:
                prompt += _syntax_zero_gate_policy_section(layer, anchor_result)
            elif args.freeze_gold_harness_on_behavior and anchor_result.get("status") == "FAIL_SIM_CORRECTNESS":
                prompt += _layer_policy_section("behavior", task_dir)
        sample_dir = gen_root / f"adaptive_round{round_idx}"
        sample_dir.mkdir(parents=True, exist_ok=True)
        (sample_dir / "repair_prompt.md").write_text(prompt, encoding="utf-8")

        print(f"[adaptive] CALL {model_slug}/{task_id} R{round_idx} ... ", end="", flush=True)
        api_start = time.perf_counter()
        response_text, usage = call_model(
            args.model,
            prompt,
            args.temperature if round_idx == 1 else max(args.temperature, 0.2),
            args.top_p,
            args.max_tokens,
        )
        api_elapsed_s = time.perf_counter() - api_start
        (sample_dir / "raw_response.txt").write_text(response_text, encoding="utf-8")
        saved = _save_generated_response(
            response_text=response_text,
            sample_dir=sample_dir,
            family=read_meta(task_dir).get("family", "end-to-end"),
            task_dir=task_dir,
        )
        frozen_tbs: list[str] = []
        frozen_duts: list[str] = []
        frozen_harness: list[str] = []
        syntax_gate_state = (
            _syntax_zero_gate_state(anchor_result)
            if args.syntax_zero_gate or args.compile_only_closure
            else {}
        )
        if args.layered_only_repair:
            if layer == "observable":
                frozen_duts = _freeze_veriloga_from(anchor_sample, sample_dir)
            elif layer == "behavior":
                frozen_harness = _freeze_gold_harness(task_dir, sample_dir)
        elif args.syntax_zero_gate or args.compile_only_closure:
            if layer in {"compile_tb", "observable"}:
                frozen_duts = _freeze_veriloga_from(anchor_sample, sample_dir)
        elif anchor_result.get("status") == "FAIL_SIM_CORRECTNESS":
            if args.freeze_gold_harness_on_behavior:
                frozen_harness = _freeze_gold_harness(task_dir, sample_dir)
            elif args.freeze_tb_on_behavior:
                frozen_tbs = _freeze_testbench_from(best_sample, sample_dir)
        vector_unroll_guard_edits = (
            apply_vector_unroll_guard(sample_dir, notes=anchor_result.get("evas_notes", []))
            if args.compile_only_closure
            else []
        )
        _json_write(
            sample_dir / "generation_meta.json",
            {
                "model": args.model,
                "model_slug": model_slug,
                "task_id": task_id,
                "mode": "adaptive-evas-repair-v0",
                "round": round_idx,
                "status": "generated" if saved else "no_code_extracted",
                "saved_files": saved,
                "frozen_testbench_from_best": frozen_tbs,
                "frozen_dut_from_anchor": frozen_duts,
                "frozen_gold_harness": frozen_harness,
                "vector_unroll_guard_edits": vector_unroll_guard_edits,
                "repair_layer": layer,
                "syntax_zero_gate": bool(args.syntax_zero_gate),
                "compile_only_closure": bool(args.compile_only_closure),
                "compile_skill_guidance": bool(args.compile_skill_guidance),
                "syntax_zero_gate_state": syntax_gate_state,
                "api_elapsed_s": round(api_elapsed_s, 3),
                "api_call_count": 1,
                "task_elapsed_s": round(time.perf_counter() - round_start, 3),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                **usage,
            },
        )
        print("generated" if saved else "no_code")
        if not saved:
            break

        result = _score_quick(
            task_id=task_id,
            task_dir=task_dir,
            sample_dir=sample_dir,
            output_root=out_root / f"round{round_idx}",
            model_slug=model_slug,
            sample_idx=args.sample_idx,
            timeout_s=args.timeout_s,
            quick_maxstep=args.quick_maxstep,
        )
        rank = _result_rank(task_id, result, compile_only_closure=args.compile_only_closure)
        result_layer = _classify_repair_layer(result)
        improved = rank > best_rank
        print(
            f"[adaptive] {task_id} R{round_idx} {result.get('status')} "
            f"layer={result_layer} improved={improved} rank={rank}"
        )

        history.append(
            {
                "round": round_idx,
                "status": result.get("status"),
                "repair_layer": layer,
                "result_layer": result_layer,
                "scores": result.get("scores", {}),
                "evas_notes": result.get("evas_notes", []),
                "concrete_diagnostics": _concrete_diagnostics(result),
                "metric_gap": {} if args.compile_only_closure else metric_gap_summary(task_dir, result),
                "failure_subtype": _failure_subtype(result),
                "metrics": _extract_metrics(result),
                "progress_label": "improved" if improved else "stalled",
                "progress_summary": "Adaptive quick-check improved rank." if improved else "No quick-check progress.",
            }
        )
        if improved:
            best_sample = sample_dir
            best_result = result
            best_rank = rank
            best_layer = result_layer
            anchor_sample = sample_dir
            anchor_result = result
            anchor_policy = "latest_improved_candidate"
            no_progress = 0
        else:
            no_progress += 1
            # Do not let a stalled or regressed candidate become the next base.
            # The next LLM call should repair the best EVAS surface we have
            # actually observed, not compound errors from a worse rewrite.
            anchor_sample = best_sample
            anchor_result = best_result
            anchor_policy = "best_so_far_after_stall"
        history[-1]["next_anchor_policy"] = anchor_policy
        if (
            result.get("status") == "PASS"
            or (args.compile_only_closure and _compile_closure_gate_cleared(best_result))
            or no_progress >= args.patience
        ):
            break

    _copy_sample(best_sample, final_dir)
    materialized_syntax_edits = (
        _materialize_syntax_zero_sanitizers(final_dir) if args.syntax_zero_gate or args.compile_only_closure else []
    )
    materialized_vector_unroll_edits = (
        apply_vector_unroll_guard(final_dir, notes=best_result.get("evas_notes", []))
        if args.compile_only_closure
        else []
    )
    _json_write(
        final_dir / "generation_meta.json",
        {
            "model": args.model,
            "model_slug": model_slug,
            "task_id": task_id,
            "mode": "adaptive-evas-repair-v0",
            "selected_sample": str(best_sample),
            "best_status": best_result.get("status"),
            "best_layer": best_layer,
            "best_scores": best_result.get("scores", {}),
            "best_metrics": _extract_metrics(best_result),
            "syntax_zero_gate": bool(args.syntax_zero_gate),
            "compile_only_closure": bool(args.compile_only_closure),
            "compile_skill_guidance": bool(args.compile_skill_guidance),
            "compile_closure_gate_state": _syntax_zero_gate_state(best_result),
            "materialized_syntax_edits": materialized_syntax_edits,
            "materialized_vector_unroll_edits": materialized_vector_unroll_edits,
            "initial_candidates": [
                {
                    "idx": item["idx"],
                    "generated_dir": item["generated_dir"],
                    "result_root": item["result_root"],
                    "sample": str(item["sample"]),
                    "status": item["result"].get("status"),
                    "scores": item["result"].get("scores", {}),
                    "rank": list(item["rank"]),
                }
                for item in initial_candidates
            ],
            "history": history,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    _json_write(out_root / "best" / task_id / "result.json", best_result)
    return best_result


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Adaptive EVAS repair pilot runner.")
    ap.add_argument("--model", default="kimi-k2.5")
    ap.add_argument("--all", action="store_true", help="Run all benchmark tasks instead of the small default pilot set.")
    ap.add_argument("--task", action="append", default=[])
    ap.add_argument(
        "--bench-dir",
        default="",
        help="Optional benchmark root containing tasks/. Use for benchmark-balanced repair runs.",
    )
    ap.add_argument("--workers", type=int, default=1, help="Task-level parallel workers. Use 1 for serial mode.")
    ap.add_argument("--resume", action="store_true", help="Skip tasks that already have a best result and final sample.")
    ap.add_argument("--source-generated-dir", default="generated-table2-evas-guided-repair-3round-skill")
    ap.add_argument("--initial-result-root", default="",
                    help="Optional existing EVAS result root used as round-0 feedback to avoid re-scoring slow baselines.")
    ap.add_argument("--candidate-generated-dir", action="append", default=[],
                    help="Additional generated roots to consider as round-0 candidates before repair.")
    ap.add_argument("--candidate-result-root", action="append", default=[],
                    help="Optional result roots paired with --candidate-generated-dir entries.")
    ap.add_argument("--generated-root", default="generated-adaptive-evas-repair")
    ap.add_argument("--output-root", default="results/adaptive-evas-repair-dwa-pilot-2026-04-24")
    ap.add_argument("--sample-idx", type=int, default=0)
    ap.add_argument("--max-rounds", type=int, default=2)
    ap.add_argument("--patience", type=int, default=1)
    ap.add_argument("--timeout-s", type=int, default=60)
    ap.add_argument("--quick-maxstep", default="1n",
                    help="Optional maxstep used only for adaptive quick checks; set empty to preserve generated TB.")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--env-file", default=".env.table2")
    ap.add_argument(
        "--repair-public-spec-mode",
        choices=["prompt-only", "spectre-strict-v3", "legacy-extracted"],
        default="legacy-extracted",
        help="Prompt/spec mode used when reconstructing the original task inside repair prompts.",
    )
    ap.add_argument(
        "--no-repair-skill",
        action="store_true",
        help="Disable repair skill/circuit-knowledge injection for clean EVAS-only F experiments.",
    )
    ap.add_argument(
        "--disable-contract-diagnosis",
        action="store_true",
        help="Disable task-local behavior contract diagnosis for clean EVAS-only F experiments.",
    )
    ap.add_argument("--freeze-tb-on-behavior", action="store_true",
                    help="For behavior failures, keep the best-so-far testbench and only evaluate generated DUT changes.")
    ap.add_argument("--freeze-gold-harness-on-behavior", action="store_true",
                    help="For behavior failures, use benchmark gold stimulus/save harness while preserving generated DUT code.")
    ap.add_argument("--layered-only-repair", action="store_true",
                    help="Automatically route compile/observable/behavior failures to the narrowest editable layer.")
    ap.add_argument(
        "--syntax-zero-gate",
        action="store_true",
        help=(
            "Condition G: repair compile/interface/runtime/strict-preflight/observable errors before behavior tuning, "
            "and preserve working layers where possible."
        ),
    )
    ap.add_argument(
        "--compile-only-closure",
        action="store_true",
        help=(
            "Official Condition G mode: use mechanism guidance plus validator gate notes to close "
            "compile/interface/runtime/observable errors, then stop before behavior repair."
        ),
    )
    ap.add_argument(
        "--compile-skill-guidance",
        action="store_true",
        help=(
            "Route current compile diagnostics through runners/compile_skills and inject the matched "
            "skill guidance into compile-only LLM repair prompts. Use for C-SKILL style ablations."
        ),
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    _load_env_file(Path(args.env_file))
    tasks = _task_lookup([] if args.all else (args.task or DEFAULT_TASKS), args.bench_dir)
    results = []

    def _runner_exception_result(task_id: str, task_dir: Path, exc: BaseException) -> dict:
        meta = read_meta(task_dir)
        result = {
            "model": args.model,
            "task_id": task_id,
            "family": meta.get("family", "unknown"),
            "category": meta.get("category", "unknown"),
            "status": "FAIL_INFRA",
            "scores": {"dut_compile": 0.0, "tb_compile": 0.0, "sim_correct": 0.0, "weighted_total": 0.0},
            "required_axes": meta.get("scoring", ["dut_compile", "tb_compile", "sim_correct"]),
            "evas_notes": [f"adaptive_runner_exception={type(exc).__name__}: {exc}"],
        }
        _json_write(Path(args.output_root) / "best" / task_id / "result.json", result)
        return result

    worker_count = max(1, min(args.workers, len(tasks)))
    if worker_count == 1:
        for task_id, task_dir in tasks:
            results.append(run_task(args, task_id, task_dir))
    else:
        print(f"[adaptive] parallel task-level repair with {worker_count} workers")
        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_map = {
                executor.submit(run_task, args, task_id, task_dir): (task_id, task_dir)
                for task_id, task_dir in tasks
            }
            for future in concurrent.futures.as_completed(future_map):
                task_id, task_dir = future_map[future]
                try:
                    results.append(future.result())
                except BaseException as exc:
                    print(f"[adaptive] {task_id} runner exception: {type(exc).__name__}: {exc}")
                    results.append(_runner_exception_result(task_id, task_dir, exc))
    summary = {
        "model": args.model,
        "tasks": len(results),
        "pass_count": sum(1 for r in results if r.get("status") == "PASS"),
        "workers": worker_count,
        "condition_flags": {
            "syntax_zero_gate": bool(args.syntax_zero_gate),
            "compile_only_closure": bool(args.compile_only_closure),
            "layered_only_repair": bool(args.layered_only_repair),
            "repair_public_spec_mode": args.repair_public_spec_mode,
            "no_repair_skill": bool(args.no_repair_skill),
            "disable_contract_diagnosis": bool(args.disable_contract_diagnosis),
            "bench_dir": args.bench_dir,
        },
        "results": [
            {
                "task_id": r.get("task_id"),
                "status": r.get("status"),
                "scores": r.get("scores", {}),
                "metrics": _extract_metrics(r),
                "notes": r.get("evas_notes", []),
            }
            for r in results
        ],
    }
    _json_write(Path(args.output_root) / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
