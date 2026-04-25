#!/usr/bin/env python3
"""Run Table 2/3 matched-budget generic retry and EVAS-assisted loops.

This runner deliberately reads API credentials only from environment variables
handled by the provider-specific generator helpers.  Do not pass keys as CLI
arguments; doing so would leak them into shell history and experiment logs.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from build_repair_prompt import (
    DEFAULT_SKILL_BUNDLE,
    build_evas_assisted_prompt,
    build_evas_guided_repair_prompt,
    build_generic_retry_prompt,
    build_skill_only_prompt,
    load_skill_bundle,
    metric_gap_summary,
)
from diagnosis_translation import translate_diagnosis
from generate import (
    call_model,
    detect_provider,
    extract_code_blocks,
    extract_module_signature,
    infer_module_name,
    infer_tb_name,
    list_task_dirs,
    read_meta,
)
from score import build_model_results, find_generated_dir, score_one_task

ROOT = Path(__file__).resolve().parents[1]
DATE_TAG = "2026-04-20"
PHASE_A_MODELS = ["qwen3-max-2026-01-23", "kimi-k2.5"]
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

DEV24_TASK_IDS = [
    "digital_basics_smoke",
    "lfsr_smoke",
    "gray_counter_4b_smoke",
    "mux_4to1_smoke",
    "cmp_delay_smoke",
    "comparator_hysteresis_smoke",
    "sample_hold_smoke",
    "dac_binary_clk_4b_smoke",
    "adpll_ratio_hop_smoke",
    "cppll_freq_step_reacquire_smoke",
    "pfd_reset_race_smoke",
    "bbpd_data_edge_alignment_smoke",
    "sc_integrator",
    "prbs7",
    "clk_divider",
    "adpll_timer",
    "multimod_divider",
    "inverted_comparator_logic_bug",
    "strongarm_reset_priority_bug",
    "wrong_edge_sample_hold_bug",
    "sample_hold_aperture_tb",
    "nrz_prbs_jitter_tb",
    "comparator_offset_tb",
    "dco_gain_step_tb",
]

MODE_TO_OUTPUT = {
    "raw-generic-retry": "generated-table2-generic-retry",
    "evas-assisted": "generated-table2-evas-assisted",
    "evas-guided-repair": "generated-table2-evas-guided-repair",
    "evas-guided-repair-no-skill": "generated-table2-evas-guided-repair-no-skill",
    "evas-guided-repair-3round": "generated-table2-evas-guided-repair-3round",
    "evas-guided-repair-3round-skill": "generated-table2-evas-guided-repair-3round-skill",
    "skill-only": "generated-table2-skill-only",
    "skill-evas-informed": "generated-table2-skill-evas-informed",
}

_METRIC_TOKEN_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=([^\s,;]+)")
_NUMERIC_TOKEN_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$", re.IGNORECASE)


def _json_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _classify_repair_layer(result: dict) -> str:
    """Route failures to the narrowest editable layer for optional F/G repair."""
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
    if any(marker in notes for marker in _OBSERVABLE_NOTE_MARKERS):
        return "observable"
    if result.get("status") == "FAIL_SIM_CORRECTNESS":
        return "behavior"
    return "infra"


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


def _declared_modules(paths: list[Path]) -> set[str]:
    modules: set[str] = set()
    for path in paths:
        signature = extract_module_signature(path)
        if signature:
            modules.add(signature[0])
    return modules


def _protected_dut_modules(task_dir: Path, dst_sample: Path) -> set[str]:
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


def _freeze_gold_harness(task_dir: Path, dst_sample: Path) -> list[str]:
    """Use gold verifier harness while preserving generated DUT modules."""
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


def _looks_like_settling_repair(result: dict, sample_dir: Path) -> bool:
    notes = " ".join(str(note) for note in result.get("evas_notes", [])).lower()
    if not any(marker in notes for marker in ("gray_property_violated", "bad_transitions", "q_mismatch", "qb_mismatch")):
        return False
    for va_path in sorted(sample_dir.glob("*.va"))[:4]:
        text = va_path.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"parameter\s+real\s+(?:t(?:edge|rise|fall|d)|tr|tf)\s*=", text):
            return True
    return False


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


def _json_read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _model_slug(model: str) -> str:
    return model.replace("/", "_")


def _provider_key_name(model: str) -> str:
    provider = detect_provider(model)
    if provider == "anthropic":
        return "ANTHROPIC_API_KEY"
    if provider == "openai":
        return "OPENAI_API_KEY"
    if provider == "bailian":
        return "BAILIAN_API_KEY"
    raise ValueError(f"unknown provider: {provider}")


def _ensure_key_available(models: list[str]) -> tuple[bool, list[str]]:
    missing: list[str] = []
    for model in models:
        key_name = _provider_key_name(model)
        if not os.environ.get(key_name):
            missing.append(f"{model}:{key_name}")
    return not missing, missing


def _is_transient_api_error(exc: Exception) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    return any(
        token in text
        for token in (
            "ratelimit",
            "rate limit",
            "too many requests",
            "timeout",
            "api connection",
            "temporarily unavailable",
            "429",
            "500",
            "502",
            "503",
            "504",
        )
    )


def _call_model_with_retries(
    model: str,
    prompt: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    *,
    attempts: int = 4,
) -> tuple[str, dict]:
    """Retry transient provider failures so matrix rows are not lost to rate limits."""
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return call_model(model, prompt, temperature, top_p, max_tokens)
        except Exception as exc:
            last_exc = exc
            if attempt >= attempts or not _is_transient_api_error(exc):
                raise
            delay_s = min(90, 8 * (2 ** (attempt - 1)))
            print(
                f"api_retry {type(exc).__name__} attempt={attempt}/{attempts} "
                f"sleep={delay_s}s ... ",
                end="",
                flush=True,
            )
            time.sleep(delay_s)
    assert last_exc is not None
    raise last_exc


def _task_list(split: str, selected_tasks: set[str] | None = None) -> list[tuple[str, Path]]:
    if split == "dev24":
        selected = set(DEV24_TASK_IDS)
        if selected_tasks is not None:
            selected &= selected_tasks
        tasks = list_task_dirs(selected=selected)
        found = {task_id for task_id, _ in tasks}
        missing = sorted(selected - found)
        if missing:
            raise RuntimeError(f"dev24 task ids missing from benchmark tree: {missing}")
        order = {task_id: i for i, task_id in enumerate(DEV24_TASK_IDS)}
        return sorted(tasks, key=lambda item: order[item[0]])
    if split == "full86":
        return list_task_dirs(selected=selected_tasks)
    raise ValueError(f"unsupported split: {split}")


def _copy_previous_artifacts(src: Path, dst: Path) -> list[str]:
    copied: list[str] = []
    dst.mkdir(parents=True, exist_ok=True)
    for path in sorted(src.glob("*")):
        if path.is_file() and path.suffix.lower() in {".va", ".scs"}:
            out = dst / f"previous_{path.name}"
            shutil.copy2(path, out)
            copied.append(str(out))
    return copied


def _save_generated_response(
    *,
    response_text: str,
    sample_dir: Path,
    family: str,
    task_dir: Path | None = None,
) -> list[str]:
    import re as _re
    blocks = extract_code_blocks(response_text)
    saved_files: list[str] = []

    if family in ("spec-to-va", "bugfix", "end-to-end") and blocks["va"]:
        if family == "bugfix" and task_dir is not None:
            # For bugfix tasks: always save one file as <ahdl_include_stem>.va.
            # Pick the block whose module name matches the gold XDUT instantiation;
            # fall back to first block. Never rename the module.
            _bugfix_save_stem: str | None = None
            _xdut_mod: str | None = None
            _gold_dir = task_dir / "gold"
            if _gold_dir.is_dir():
                _tbs = sorted(_gold_dir.glob("tb_*.scs"))
                if _tbs:
                    _tb_text = _tbs[0].read_text(encoding="utf-8", errors="ignore")
                    _m_inc = _re.search(r'ahdl_include\s+"([^"]+\.va)"', _tb_text)
                    if _m_inc:
                        _bugfix_save_stem = Path(_m_inc.group(1)).stem
                    _m_xdut = _re.search(r'\bXDUT\s+\([^)]+\)\s+(\w+)', _tb_text)
                    if _m_xdut:
                        _xdut_mod = _m_xdut.group(1)
            if _bugfix_save_stem:
                best_block = blocks["va"][0]
                for _blk in blocks["va"]:
                    if _xdut_mod and infer_module_name(_blk) == _xdut_mod:
                        best_block = _blk
                        break
                va_path = sample_dir / f"{_bugfix_save_stem}.va"
                va_path.write_text(best_block, encoding="utf-8")
                saved_files.append(str(va_path))
            else:
                # No gold TB found; fall back to saving all blocks by module name
                for va_code in blocks["va"]:
                    va_path = sample_dir / f"{infer_module_name(va_code)}.va"
                    va_path.write_text(va_code, encoding="utf-8")
                    saved_files.append(str(va_path))
        else:
            for va_code in blocks["va"]:
                va_path = sample_dir / f"{infer_module_name(va_code)}.va"
                va_path.write_text(va_code, encoding="utf-8")
                saved_files.append(str(va_path))

    if family in ("end-to-end", "tb-generation") and blocks["scs"]:
        scs_code = blocks["scs"][0]
        scs_path = sample_dir / f"{infer_tb_name(scs_code)}.scs"
        scs_path.write_text(scs_code, encoding="utf-8")
        saved_files.append(str(scs_path))

    return saved_files


def _baseline_sample_dir(model: str, task_id: str, sample_idx: int) -> Path | None:
    return find_generated_dir(ROOT / "generated", _model_slug(model), task_id, sample_idx)


def _mode_sample_dir(mode: str, model: str, task_id: str, sample_idx: int) -> Path | None:
    generated_root = ROOT / MODE_TO_OUTPUT[mode]
    return find_generated_dir(generated_root, _model_slug(model), task_id, sample_idx)


def _result_path(output_root: Path, task_id: str) -> Path:
    return output_root / task_id / "result.json"


def _round_label(round_idx: int) -> str:
    return "baseline" if round_idx <= 0 else f"R{round_idx}"


def _parse_metric_token(token: str) -> float | bool | str:
    cleaned = token.strip().strip("`")
    lowered = cleaned.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if _NUMERIC_TOKEN_RE.match(cleaned):
        try:
            return float(cleaned)
        except ValueError:
            pass
    return cleaned


def _extract_metrics_from_notes(notes: list[str]) -> dict[str, float | bool | str]:
    metrics: dict[str, float | bool | str] = {}
    for note in notes:
        for key, raw_value in _METRIC_TOKEN_RE.findall(note):
            metrics[key] = _parse_metric_token(raw_value)
    return metrics


def _hash_paths(paths: list[Path]) -> str:
    if not paths:
        return ""
    hasher = hashlib.sha1()
    for path in sorted(paths):
        hasher.update(path.name.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(path.read_bytes())
        hasher.update(b"\0")
    return hasher.hexdigest()[:12]


def _sample_signature(sample_dir: Path) -> dict[str, str]:
    va_paths = sorted(sample_dir.glob("*.va"))
    scs_paths = sorted(sample_dir.glob("*.scs"))
    return {
        "va_hash": _hash_paths(va_paths),
        "tb_hash": _hash_paths(scs_paths),
        "artifact_hash": _hash_paths(va_paths + scs_paths),
    }


def _result_rank(result: dict) -> tuple[float, float, float, float, int]:
    scores = result.get("scores", {})
    return (
        float(scores.get("weighted_total", 0.0)),
        float(scores.get("sim_correct", 0.0)),
        float(scores.get("tb_compile", 0.0)),
        float(scores.get("dut_compile", 0.0)),
        int(result.get("status") == "PASS"),
    )


def _compare_results(candidate: dict, reference: dict) -> int:
    candidate_rank = (
        1 if candidate.get("status") == "PASS" else 0,
        *_result_rank(candidate),
    )
    reference_rank = (
        1 if reference.get("status") == "PASS" else 0,
        *_result_rank(reference),
    )
    if candidate_rank > reference_rank:
        return 1
    if candidate_rank < reference_rank:
        return -1
    return 0


def _missing_observable_signal(notes: list[str]) -> bool:
    for note in notes:
        lowered = note.lower()
        if lowered.startswith("missing ") or "missing_" in lowered:
            return True
    return False


def _shared_numeric_metric_names(
    left: dict[str, float | bool | str],
    right: dict[str, float | bool | str],
) -> tuple[list[str], list[str]]:
    changed: list[str] = []
    unchanged: list[str] = []
    shared = sorted(set(left) & set(right))
    for key in shared:
        left_value = left[key]
        right_value = right[key]
        if not isinstance(left_value, (int, float)) or not isinstance(right_value, (int, float)):
            continue
        tolerance = max(1e-9, 1e-6 * max(abs(float(left_value)), abs(float(right_value)), 1.0))
        if abs(float(left_value) - float(right_value)) <= tolerance:
            unchanged.append(key)
        else:
            changed.append(key)
    return changed, unchanged


def _failure_class(result: dict) -> str:
    status = result.get("status", "FAIL_OTHER")
    if status == "PASS":
        return "pass"
    if status == "FAIL_DUT_COMPILE":
        return "dut_compile"
    if status == "FAIL_TB_COMPILE":
        return "tb_compile"
    if status == "FAIL_SIM_CORRECTNESS":
        return "behavior"
    if status == "FAIL_INFRA":
        return "infra"
    return "other"


def _failure_subtype(task_id: str, result: dict) -> str:
    status = result.get("status", "FAIL_OTHER")
    if status == "PASS":
        return "pass"
    if status == "FAIL_DUT_COMPILE":
        return "dut_compile"
    if status == "FAIL_TB_COMPILE":
        return "tb_compile"
    if status == "FAIL_INFRA":
        return "infra"
    for note in result.get("evas_notes", []):
        translation = translate_diagnosis(str(note), task_id=task_id)
        if translation.get("diagnosis"):
            return translation.get("failure_type", "behavior_semantic")
    if status == "FAIL_SIM_CORRECTNESS":
        return "behavior_semantic"
    return "other"


def _failure_subtype_rank(subtype: str) -> int:
    # Higher is better when weighted scores tie. A semantic failure usually
    # means compile/run/observability is working and the loop can optimize
    # measured behavior. Infra/contract failures are less informative.
    return {
        "pass": 6,
        "behavior_semantic": 5,
        "observability_contract": 4,
        "simulation_artifact": 3,
        "tb_compile": 2,
        "dut_compile": 1,
        "infra": 0,
        "other": 0,
    }.get(subtype, 0)


def _has_evas_note(state: dict, token: str) -> bool:
    return any(token in str(note) for note in state.get("evas_notes", []))


def _compile_stage_rank(state: dict) -> int:
    """Rank how far a candidate progressed through the compile/sim pipeline.

    The weighted score is still the main reported metric, but the repair loop
    should not keep a known DUT-compile failure when a later candidate has
    already passed strict Verilog-A preflight and reached the EVAS runtime.
    """
    status = state.get("status", "FAIL_OTHER")
    if status == "PASS":
        return 5
    if status == "FAIL_SIM_CORRECTNESS":
        return 4
    if status == "FAIL_INFRA" and _has_evas_note(state, "spectre_strict:preflight_pass"):
        return 3
    if status == "FAIL_TB_COMPILE":
        return 2
    if status == "FAIL_DUT_COMPILE":
        return 1
    return 0


def _build_loop_state(
    *,
    round_idx: int,
    sample_dir: Path,
    result: dict,
    task_id: str,
    task_dir: Path,
) -> dict:
    notes = list(result.get("evas_notes", []))
    gap = metric_gap_summary(task_dir, result)
    return {
        "round": round_idx,
        "sample_dir": str(sample_dir),
        "status": result.get("status", "FAIL_OTHER"),
        "scores": dict(result.get("scores", {})),
        "evas_notes": notes,
        "metrics": _extract_metrics_from_notes(notes),
        "failure_class": _failure_class(result),
        "failure_subtype": _failure_subtype(task_id, result),
        "metric_gap": gap,
        "signature": _sample_signature(sample_dir),
    }


def _loop_state_rank(state: dict) -> tuple:
    scores = state.get("scores", {})
    gap = state.get("metric_gap", {})
    gap_sum = float(gap.get("gap_sum", 0.0))
    matched = int(gap.get("matched", 0))
    violated = int(gap.get("violated", 0))
    return (
        int(state.get("status") == "PASS"),
        _compile_stage_rank(state),
        float(scores.get("weighted_total", 0.0)),
        float(scores.get("sim_correct", 0.0)),
        float(scores.get("tb_compile", 0.0)),
        float(scores.get("dut_compile", 0.0)),
        _failure_subtype_rank(str(state.get("failure_subtype", "other"))),
        matched,
        -violated,
        -gap_sum,
    )


def _compare_loop_states(candidate_state: dict, reference_state: dict) -> int:
    candidate_rank = _loop_state_rank(candidate_state)
    reference_rank = _loop_state_rank(reference_state)
    if candidate_rank > reference_rank:
        return 1
    if candidate_rank < reference_rank:
        return -1
    return 0


def _classify_loop_transition(reference_state: dict, candidate_state: dict) -> tuple[str, str]:
    ranking = _compare_loop_states(candidate_state, reference_state)
    ref_scores = reference_state.get("scores", {})
    cand_scores = candidate_state.get("scores", {})
    ref_total = float(ref_scores.get("weighted_total", 0.0))
    cand_total = float(cand_scores.get("weighted_total", 0.0))

    ref_sig = reference_state.get("signature", {})
    cand_sig = candidate_state.get("signature", {})
    changed_metrics, unchanged_metrics = _shared_numeric_metric_names(
        reference_state.get("metrics", {}),
        candidate_state.get("metrics", {}),
    )
    same_artifacts = cand_sig.get("artifact_hash") == ref_sig.get("artifact_hash")
    same_behavior = bool(unchanged_metrics) and not changed_metrics
    tb_only_change = (
        cand_sig.get("tb_hash") != ref_sig.get("tb_hash")
        and cand_sig.get("va_hash") == ref_sig.get("va_hash")
    )
    toggled_missing_observable = (
        _missing_observable_signal(reference_state.get("evas_notes", []))
        != _missing_observable_signal(candidate_state.get("evas_notes", []))
    )

    ref_gap = reference_state.get("metric_gap", {})
    cand_gap = candidate_state.get("metric_gap", {})
    ref_gap_sum = float(ref_gap.get("gap_sum", 0.0))
    cand_gap_sum = float(cand_gap.get("gap_sum", 0.0))

    if ranking > 0:
        label = "improved"
        if cand_total > ref_total:
            summary = (
                f"EVAS score improved from {ref_total:.3f} to {cand_total:.3f}; "
                "preserve the repaired parts and focus only on the remaining failure."
            )
        elif cand_gap.get("matched", 0) and cand_gap_sum < ref_gap_sum:
            summary = (
                f"Weighted score stayed at {cand_total:.3f}, but checker metric gap improved "
                f"from {ref_gap_sum:.4g} to {cand_gap_sum:.4g}; preserve this closer candidate."
            )
        else:
            summary = (
                f"Weighted score stayed at {cand_total:.3f}, but EVAS failure quality improved; "
                "preserve this candidate and continue with a smaller targeted edit."
            )
    elif ranking < 0:
        if tb_only_change and toggled_missing_observable:
            label = "oscillating"
            summary = (
                "The latest edit changed the testbench/interface failure surface without "
                "improving EVAS. Continue from the best-so-far candidate instead of this round."
            )
        else:
            label = "regressed"
            summary = (
                f"EVAS score regressed from {ref_total:.3f} to {cand_total:.3f}; "
                "roll back to the best-so-far candidate and avoid repeating the last edit direction."
            )
    elif same_artifacts:
        label = "stalled"
        summary = "This round produced the same artifact set as the reference candidate."
    elif same_behavior:
        label = "stalled"
        summary = (
            "Code changed, but the shared EVAS measurements did not move. "
            "Try a different repair mechanism instead of a cosmetic rewrite."
        )
    elif tb_only_change and toggled_missing_observable:
        label = "oscillating"
        summary = (
            "The loop is toggling between interface/observability failures. "
            "Freeze naming/save structure and fix the remaining semantic bug from the best-so-far candidate."
        )
    else:
        label = "lateral"
        summary = (
            f"EVAS score stayed at {cand_total:.3f}, but the failure surface changed. "
            "Use the best-so-far candidate as the anchor and make a more targeted edit."
        )

    if changed_metrics:
        preview = ", ".join(changed_metrics[:3])
        summary = f"{summary} Changed metrics: {preview}."
    return label, summary


def score_baseline_evas(
    *,
    model: str,
    split: str,
    tasks: list[tuple[str, Path]],
    generated_root: Path,
    result_tag: str | None,
    sample_idx: int,
    temperature: float,
    top_p: float,
    timeout_s: int,
    force: bool,
) -> Path:
    model_slug = _model_slug(model)
    if result_tag:
        out_root = ROOT / "results" / f"model-assisted-evas-inner-{result_tag}-{model_slug}-{split}-{DATE_TAG}"
        source_tag = f"{result_tag}_inner_evas"
        log_tag = result_tag
    else:
        out_root = ROOT / "results" / f"model-assisted-evas-inner-{model_slug}-{split}-{DATE_TAG}"
        source_tag = "raw_one_shot_inner_evas"
        log_tag = "raw"
    results: list[dict] = []
    out_root.mkdir(parents=True, exist_ok=True)

    for task_id, task_dir in tasks:
        existing = _result_path(out_root, task_id)
        if existing.exists() and not force:
            results.append(_json_read(existing))
            continue
        sample_dir = find_generated_dir(generated_root, model_slug, task_id, sample_idx)
        if sample_dir is None:
            print(f"[evas-inner:{log_tag}] SKIP {model_slug}/{task_id}: missing sample")
            continue
        print(f"[evas-inner:{log_tag}] {model_slug}/{task_id} ... ", end="", flush=True)
        result = score_one_task(
            task_id,
            task_dir,
            sample_dir,
            out_root,
            model=model_slug,
            sample_idx=sample_idx,
            temperature=temperature,
            top_p=top_p,
            timeout_s=timeout_s,
        )
        print(result.get("status", "unknown"))
        results.append(result)

    aggregate = build_model_results(model_slug, results, temperature, top_p)
    aggregate.update({"split": split, "source": source_tag})
    _json_write(out_root / "model_results.json", aggregate)
    return out_root


def generate_mode(
    *,
    mode: str,
    model: str,
    split: str,
    tasks: list[tuple[str, Path]],
    sample_idx: int,
    temperature: float,
    top_p: float,
    max_tokens: int,
    force: bool,
    dry_run: bool,
    workers: int,
    evas_inner_root: Path | None,
    skill_bundle_text: str | None,
    skill_bundle_path: Path | None,
) -> Path:
    model_slug = _model_slug(model)
    generated_root = ROOT / MODE_TO_OUTPUT[mode]
    generated_model_root = generated_root / model_slug
    generated_model_root.mkdir(parents=True, exist_ok=True)

    def _process_task(task_id: str, task_dir: Path) -> None:
        meta = read_meta(task_dir)
        family = meta.get("family", "end-to-end")
        baseline_dir: Path | None
        sample_dir = generated_model_root / task_id / f"sample_{sample_idx}"
        meta_path = sample_dir / "generation_meta.json"

        if mode in ("raw-generic-retry", "evas-assisted", "evas-guided-repair", "evas-guided-repair-no-skill"):
            baseline_dir = _baseline_sample_dir(model, task_id, sample_idx)
            if baseline_dir is None:
                print(f"[generate:{mode}] SKIP {model_slug}/{task_id}: missing raw sample")
                return
        elif mode == "skill-evas-informed":
            baseline_dir = _mode_sample_dir("skill-only", model, task_id, sample_idx)
            if baseline_dir is None:
                print(f"[generate:{mode}] SKIP {model_slug}/{task_id}: missing skill-only sample")
                return
        else:
            baseline_dir = None
        if meta_path.exists() and not force:
            old = _json_read(meta_path)
            old_status = old.get("status", "unknown")
            if dry_run and old.get("status") != "dry_run":
                print(f"[generate:{mode}] REUSE {model_slug}/{task_id}: {old.get('status', 'unknown')} (skip dry-run overwrite)")
                return
            if not dry_run and old_status not in ("dry_run", "api_error"):
                print(f"[generate:{mode}] REUSE {model_slug}/{task_id}: {old_status}")
                return
            if not dry_run and old_status == "api_error":
                print(f"[generate:{mode}] RETRY {model_slug}/{task_id}: previous api_error")

        if mode == "raw-generic-retry":
            assert baseline_dir is not None
            prompt = build_generic_retry_prompt(task_dir, baseline_dir)
            prompt_source = "generic_retry_without_validator_feedback"
            evas_result_path = None
        elif mode == "evas-assisted":
            if evas_inner_root is None:
                raise RuntimeError("evas-assisted generation requires EVAS inner results")
            evas_result_path = evas_inner_root / task_id / "result.json"
            if not evas_result_path.exists():
                print(f"[generate:{mode}] SKIP {model_slug}/{task_id}: missing EVAS result")
                return
            assert baseline_dir is not None
            prompt = build_evas_assisted_prompt(task_dir, baseline_dir, _json_read(evas_result_path))
            prompt_source = "evas_targeted_repair"
        elif mode == "evas-guided-repair":
            if evas_inner_root is None:
                raise RuntimeError("evas-guided-repair generation requires EVAS inner results")
            evas_result_path = evas_inner_root / task_id / "result.json"
            if not evas_result_path.exists():
                print(f"[generate:{mode}] SKIP {model_slug}/{task_id}: missing EVAS result")
                return
            assert baseline_dir is not None
            prompt = build_evas_guided_repair_prompt(task_dir, baseline_dir, _json_read(evas_result_path), include_skill=True)
            prompt_source = "evas_guided_targeted_repair_with_skill"
        elif mode == "evas-guided-repair-no-skill":
            # Experiment condition D: Checker + EVAS only (no Skill)
            if evas_inner_root is None:
                raise RuntimeError("evas-guided-repair-no-skill generation requires EVAS inner results")
            evas_result_path = evas_inner_root / task_id / "result.json"
            if not evas_result_path.exists():
                print(f"[generate:{mode}] SKIP {model_slug}/{task_id}: missing EVAS result")
                return
            assert baseline_dir is not None
            prompt = build_evas_guided_repair_prompt(task_dir, baseline_dir, _json_read(evas_result_path), include_skill=False)
            prompt_source = "evas_guided_targeted_repair_no_skill"
        elif mode == "skill-only":
            if not skill_bundle_text:
                raise RuntimeError("skill-only generation requires a skill bundle")
            evas_result_path = None
            prompt = build_skill_only_prompt(task_dir, skill_bundle_text=skill_bundle_text)
            prompt_source = "skill_only_prompt_bundle"
        elif mode == "skill-evas-informed":
            if evas_inner_root is None and dry_run:
                print(f"[generate:{mode}] SKIP {model_slug}/{task_id}: dry-run has no skill EVAS inner results")
                return
            if evas_inner_root is None:
                raise RuntimeError("skill-evas-informed generation requires skill EVAS inner results")
            if not skill_bundle_text:
                raise RuntimeError("skill-evas-informed generation requires a skill bundle")
            evas_result_path = evas_inner_root / task_id / "result.json"
            if not evas_result_path.exists():
                print(f"[generate:{mode}] SKIP {model_slug}/{task_id}: missing skill EVAS result")
                return
            assert baseline_dir is not None
            prompt = build_evas_assisted_prompt(
                task_dir,
                baseline_dir,
                _json_read(evas_result_path),
                skill_bundle_text=skill_bundle_text,
            )
            prompt_source = "skill_plus_evas_targeted_repair"
        else:
            raise ValueError(f"unsupported mode: {mode}")

        sample_dir.mkdir(parents=True, exist_ok=True)
        (sample_dir / "repair_prompt.md").write_text(prompt, encoding="utf-8")

        base_meta = {
            "model": model,
            "model_slug": model_slug,
            "task_id": task_id,
            "family": family,
            "sample_idx": sample_idx,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "prompt_source": prompt_source,
            "baseline_sample_dir": str(baseline_dir) if baseline_dir else None,
            "evas_result_path": str(evas_result_path) if evas_result_path else None,
            "skill_bundle_path": str(skill_bundle_path) if skill_bundle_text and skill_bundle_path else None,
        }

        if dry_run:
            _json_write(meta_path, {**base_meta, "status": "dry_run", "saved_files": []})
            print(f"[generate:{mode}] DRY {model_slug}/{task_id}")
            return

        print(f"[generate:{mode}] CALL {model_slug}/{task_id} ... ", end="", flush=True)
        try:
            response_text, usage = _call_model_with_retries(model, prompt, temperature, top_p, max_tokens)
            (sample_dir / "raw_response.txt").write_text(response_text, encoding="utf-8")
            saved_files = _save_generated_response(
                response_text=response_text,
                sample_dir=sample_dir,
                family=family,
                task_dir=task_dir,
            )
            status = "generated" if saved_files else "no_code_extracted"
            _json_write(meta_path, {
                **base_meta,
                "status": status,
                "saved_files": saved_files,
                "raw_response_length": len(response_text),
                **usage,
            })
            print(status)
        except Exception as exc:  # API/provider failures are experiment facts.
            _json_write(meta_path, {
                **base_meta,
                "status": "api_error",
                "error": str(exc)[:600],
                "input_tokens": 0,
                "output_tokens": 0,
            })
            print(f"api_error: {type(exc).__name__}")

    if workers > 1 and len(tasks) > 1:
        worker_count = min(workers, len(tasks))
        print(f"[generate:{mode}] parallel dispatch with {worker_count} workers")
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [executor.submit(_process_task, task_id, task_dir) for task_id, task_dir in tasks]
            for fut in as_completed(futures):
                fut.result()
    else:
        for task_id, task_dir in tasks:
            _process_task(task_id, task_dir)

    return generated_root


def generate_multi_round_repair(
    *,
    model: str,
    split: str,
    tasks: list[tuple[str, Path]],
    sample_idx: int,
    temperature: float,
    top_p: float,
    max_tokens: int,
    force: bool,
    dry_run: bool,
    evas_inner_root: Path,
    workers: int = 1,
    n_rounds: int = 3,
    include_skill: bool = False,
    timeout_s: int = 180,
    layered_only_repair: bool = False,
) -> Path:
    """Multi-round EVAS-guided repair (condition F).

    For each task that fails at baseline (B), run up to n_rounds repair calls.
    Each round feeds the previous round's EVAS result + history into the next
    repair prompt using the existing history parameter of build_evas_guided_repair_prompt.
    Stops early if a round produces PASS.
    The final sample_dir contains the best-so-far artifacts selected by EVAS.
    """
    model_slug = _model_slug(model)
    mode_name = "evas-guided-repair-3round-skill" if include_skill else "evas-guided-repair-3round"
    generated_root = ROOT / MODE_TO_OUTPUT[mode_name]
    generated_model_root = generated_root / model_slug
    generated_model_root.mkdir(parents=True, exist_ok=True)

    round_results_root = ROOT / "results" / f"experiment-condition-F-rounds-{model_slug}-{split}"
    round_results_root.mkdir(parents=True, exist_ok=True)

    if workers > 1 and len(tasks) > 1:
        worker_count = min(workers, len(tasks))
        print(f"[multi-repair] parallel dispatch with {worker_count} workers")
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(
                    generate_multi_round_repair,
                    model=model,
                    split=split,
                    tasks=[(task_id, task_dir)],
                    sample_idx=sample_idx,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    force=force,
                    dry_run=dry_run,
                    evas_inner_root=evas_inner_root,
                    workers=1,
                    n_rounds=n_rounds,
                    include_skill=include_skill,
                    timeout_s=timeout_s,
                    layered_only_repair=layered_only_repair,
                )
                for task_id, task_dir in tasks
            ]
            for fut in as_completed(futures):
                fut.result()
        return generated_root

    for task_id, task_dir in tasks:
        meta = read_meta(task_dir)
        family = meta.get("family", "end-to-end")

        final_sample_dir = generated_model_root / task_id / f"sample_{sample_idx}"
        final_meta_path = final_sample_dir / "generation_meta.json"

        if final_meta_path.exists() and not force:
            old = _json_read(final_meta_path)
            if old.get("status") not in ("dry_run",):
                print(f"[multi-repair] REUSE {model_slug}/{task_id}: round {old.get('round_completed', '?')}")
                continue

        baseline_evas_path = evas_inner_root / task_id / "result.json"
        if not baseline_evas_path.exists():
            print(f"[multi-repair] SKIP {task_id}: no B baseline EVAS result")
            continue
        baseline_evas_result = _json_read(baseline_evas_path)

        baseline_dir = _baseline_sample_dir(model, task_id, sample_idx)
        if baseline_dir is None:
            print(f"[multi-repair] SKIP {task_id}: no B baseline sample")
            continue

        if baseline_evas_result.get("status") == "PASS":
            print(f"[multi-repair] BASELINE_PASS {task_id}: reuse baseline sample")
            if dry_run:
                final_sample_dir.mkdir(parents=True, exist_ok=True)
                _json_write(final_meta_path, {
                    "model": model,
                    "model_slug": model_slug,
                    "task_id": task_id,
                    "family": family,
                    "sample_idx": sample_idx,
                    "mode": mode_name,
                    "status": "dry_run",
                    "round_completed": 0,
                    "selected_round": 0,
                    "selected_round_label": "baseline",
                    "best_status": "PASS",
                    "best_scores": baseline_evas_result.get("scores", {}),
                    "best_sample_dir": str(baseline_dir),
                    "history": [],
                })
            else:
                final_sample_dir.mkdir(parents=True, exist_ok=True)
                for f in sorted(baseline_dir.glob("*")):
                    if f.is_file():
                        shutil.copy2(f, final_sample_dir / f.name)
                baseline_meta: dict = {}
                baseline_meta_path = baseline_dir / "generation_meta.json"
                if baseline_meta_path.exists():
                    baseline_meta = _json_read(baseline_meta_path)
                _json_write(final_meta_path, {
                    **baseline_meta,
                    "model": model,
                    "model_slug": model_slug,
                    "task_id": task_id,
                    "family": family,
                    "sample_idx": sample_idx,
                    "mode": mode_name,
                    "round_completed": 0,
                    "selected_round": 0,
                    "selected_round_label": "baseline",
                    "best_status": "PASS",
                    "best_scores": baseline_evas_result.get("scores", {}),
                    "best_sample_dir": str(baseline_dir),
                    "history": [],
                })
            continue

        best_evas_result = baseline_evas_result
        best_sample_dir = baseline_dir
        best_state = _build_loop_state(
            round_idx=0,
            sample_dir=baseline_dir,
            result=baseline_evas_result,
            task_id=task_id,
            task_dir=task_dir,
        )
        history: list[dict] = []
        round_completed = 0

        for round_idx in range(1, n_rounds + 1):
            loop_context = {
                "attempt_round": round_idx,
                "repair_from_round": best_state.get("round", 0),
                "repair_from_label": _round_label(int(best_state.get("round", 0))),
                "best_round": best_state.get("round", 0),
                "best_status": best_state.get("status"),
                "best_scores": best_state.get("scores", {}),
                "best_metric_gap": best_state.get("metric_gap", {}),
                "best_failure_subtype": best_state.get("failure_subtype"),
                "last_transition": history[-1].get("progress_label") if history else None,
                "last_transition_summary": history[-1].get("progress_summary") if history else None,
            }
            prompt = build_evas_guided_repair_prompt(
                task_dir,
                best_sample_dir,
                best_evas_result,
                history=history,
                include_skill=include_skill,
                loop_context=loop_context,
            )
            repair_layer = _classify_repair_layer(best_evas_result) if layered_only_repair else ""
            if layered_only_repair:
                prompt += _layer_policy_section(repair_layer, task_dir)
            round_sample_dir = generated_model_root / task_id / f"sample_{sample_idx}_round{round_idx}"
            round_sample_dir.mkdir(parents=True, exist_ok=True)
            (round_sample_dir / "repair_prompt.md").write_text(prompt, encoding="utf-8")

            base_meta = {
                "model": model,
                "model_slug": model_slug,
                "task_id": task_id,
                "family": family,
                "sample_idx": sample_idx,
                "temperature": temperature,  # base temperature (may be overridden in round 2+)
                "top_p": top_p,
                "max_tokens": max_tokens,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "mode": mode_name,
                "round": round_idx,
            }
            round_meta_path = round_sample_dir / "generation_meta.json"

            if dry_run:
                _json_write(round_meta_path, {**base_meta, "status": "dry_run", "saved_files": []})
                print(f"[multi-repair] DRY {task_id} round {round_idx}")
                round_completed = round_idx
                break

            print(f"[multi-repair] CALL {model_slug}/{task_id} round {round_idx} ... ", end="", flush=True)
            try:
                # Use higher temperature for round 2+ to avoid identical outputs when
                # diagnosis is unchanged (T=0 would produce same code as previous round)
                round_temp = temperature if round_idx == 1 else max(temperature, 0.3)
                response_text, usage = _call_model_with_retries(model, prompt, round_temp, top_p, max_tokens)
                (round_sample_dir / "raw_response.txt").write_text(response_text, encoding="utf-8")
                saved_files = _save_generated_response(
                    response_text=response_text,
                    sample_dir=round_sample_dir,
                    family=family,
                    task_dir=task_dir,
                )
                frozen_duts: list[str] = []
                frozen_harness: list[str] = []
                freeze_exception = ""
                if layered_only_repair and saved_files:
                    if repair_layer == "observable":
                        frozen_duts = _freeze_veriloga_from(best_sample_dir, round_sample_dir)
                    elif repair_layer == "behavior":
                        if _looks_like_settling_repair(best_evas_result, best_sample_dir):
                            freeze_exception = "settling_repair_allows_tb_transition_override"
                        else:
                            frozen_harness = _freeze_gold_harness(task_dir, round_sample_dir)
                status = "generated" if saved_files else "no_code_extracted"
                _json_write(round_meta_path, {**base_meta, "status": status, "saved_files": saved_files,
                                              "actual_temperature": round_temp,
                                              "layered_only_repair": layered_only_repair,
                                              "repair_layer": repair_layer,
                                              "freeze_exception": freeze_exception,
                                              "frozen_dut_from_best": frozen_duts,
                                              "frozen_gold_harness": frozen_harness,
                                              "raw_response_length": len(response_text), **usage})
                print(status)
            except Exception as exc:
                _json_write(round_meta_path, {**base_meta, "status": "api_error", "error": str(exc)[:600],
                                              "input_tokens": 0, "output_tokens": 0})
                print(f"api_error: {type(exc).__name__}")
                break

            if not saved_files:
                break

            try:
                round_evas_result = score_one_task(
                    task_id, task_dir, round_sample_dir,
                    round_results_root / f"round{round_idx}",
                    model=model_slug,
                    sample_idx=sample_idx,
                    temperature=temperature,
                    top_p=top_p,
                    timeout_s=timeout_s,
                )
            except Exception as score_exc:
                print(f"score_error: {type(score_exc).__name__}")
                round_evas_result = {
                    "task_id": task_id, "status": "FAIL_INFRA",
                    "scores": {"dut_compile": 0.0, "tb_compile": 0.0, "sim_correct": 0.0, "weighted_total": 0.0},
                    "evas_notes": [f"score_exception: {str(score_exc)[:200]}"],
                }
            print(f"  → {round_evas_result.get('status')}")

            round_completed = round_idx
            previous_best_state = best_state
            round_state = _build_loop_state(
                round_idx=round_idx,
                sample_dir=round_sample_dir,
                result=round_evas_result,
                task_id=task_id,
                task_dir=task_dir,
            )
            progress_label, progress_summary = _classify_loop_transition(previous_best_state, round_state)
            round_state.update({
                "compared_to_round": previous_best_state.get("round", 0),
                "progress_label": progress_label,
                "progress_summary": progress_summary,
            })
            history.append(round_state)

            if _compare_loop_states(round_state, best_state) > 0:
                best_evas_result = round_evas_result
                best_sample_dir = round_sample_dir
                best_state = round_state

            if round_evas_result.get("status") == "PASS":
                break

        # Copy best-so-far artifacts to final sample dir
        if round_completed > 0 and not dry_run:
            selected_source_dir = best_sample_dir
            if selected_source_dir.exists():
                final_sample_dir.mkdir(parents=True, exist_ok=True)
                for f in sorted(selected_source_dir.glob("*")):
                    if f.is_file():
                        shutil.copy2(f, final_sample_dir / f.name)
                selected_meta: dict = {}
                selected_meta_path = selected_source_dir / "generation_meta.json"
                if selected_meta_path.exists():
                    selected_meta = _json_read(selected_meta_path)
                _json_write(final_meta_path, {
                    **selected_meta,
                    "model": model,
                    "model_slug": model_slug,
                    "task_id": task_id,
                    "family": family,
                    "sample_idx": sample_idx,
                    "mode": mode_name,
                    "round_completed": round_completed,
                    "selected_round": best_state.get("round", 0),
                    "selected_round_label": _round_label(int(best_state.get("round", 0))),
                    "best_status": best_state.get("status"),
                    "best_scores": best_state.get("scores", {}),
                    "best_sample_dir": str(selected_source_dir),
                    "history": [
                        {
                            "round": entry.get("round"),
                            "status": entry.get("status"),
                            "progress_label": entry.get("progress_label"),
                            "progress_summary": entry.get("progress_summary"),
                            "weighted_total": entry.get("scores", {}).get("weighted_total"),
                            "failure_subtype": entry.get("failure_subtype"),
                            "metric_gap": entry.get("metric_gap", {}),
                        }
                        for entry in history
                    ],
                })

    return generated_root


def run_spectre_final(
    *,
    mode: str,
    model: str,
    split: str,
    tasks: list[tuple[str, Path]],
    sample_idx: int,
    temperature: float,
    top_p: float,
    timeout_s: int,
) -> int:
    model_slug = _model_slug(model)
    generated_root = ROOT / MODE_TO_OUTPUT[mode]
    output_root = ROOT / "results" / f"model-spectre-eval-{model_slug}-table2-{mode}-{split}-{DATE_TAG}"
    cmd = [
        str(ROOT / "scripts" / "run_with_bridge.sh"),
        "python3",
        "runners/score_spectre_generated.py",
        "--model",
        model_slug,
        "--generated-dir",
        str(generated_root),
        "--output-dir",
        str(output_root),
        "--sample-idx",
        str(sample_idx),
        "--temperature",
        str(temperature),
        "--top-p",
        str(top_p),
        "--timeout-s",
        str(timeout_s),
    ]
    for task_id, _ in tasks:
        cmd.extend(["--task", task_id])

    print(f"[spectre:{mode}] {model_slug}/{split} -> {output_root}")
    proc = subprocess.run(cmd, cwd=ROOT, text=True)
    if proc.returncode not in (0, 1):
        print(f"[spectre:{mode}] BLOCKED returncode={proc.returncode}")
    return proc.returncode


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run Table 2/3 model-assisted benchmark loops.")
    ap.add_argument("--model", action="append", default=[], help="Model name. Repeatable. Default: phase-A models.")
    ap.add_argument("--split", choices=["dev24", "full86"], default="dev24")
    ap.add_argument("--task", action="append", default=[], help="Optional task id filter. Repeatable.")
    ap.add_argument(
        "--mode",
        choices=[
            "raw-generic-retry",
            "evas-assisted",
            "evas-guided-repair",
            "evas-guided-repair-no-skill",
            "evas-guided-repair-3round",
            "evas-guided-repair-3round-skill",
            "skill-only",
            "skill-evas-informed",
            "both",
            "mainline",
        ],
        default="both",
        help="Mode: evas-guided-repair-3round (F) or evas-guided-repair-3round-skill (G)",
    )
    ap.add_argument("--stage", choices=["plan", "evas-inner", "generate", "spectre-final", "all"], default="plan")
    ap.add_argument("--sample-idx", type=int, default=0)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--workers", type=int, default=4,
                    help="Parallel workers for single-round generate modes. Default: 4")
    ap.add_argument("--timeout-s", type=int, default=180)
    ap.add_argument("--spectre-timeout-s", type=int, default=240)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="Do not call model APIs; write prompt/meta placeholders.")
    ap.add_argument("--skill-bundle", default=str(DEFAULT_SKILL_BUNDLE), help="Frozen skill bundle path.")
    ap.add_argument(
        "--layered-only-repair",
        action="store_true",
        help=(
            "For multi-round F/G repair, route each failure to the narrowest layer: "
            "observable repairs preserve DUT files, and behavior repairs use the verifier harness."
        ),
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    models = args.model or PHASE_A_MODELS
    if args.mode == "both":
        modes = ["raw-generic-retry", "evas-assisted"]
    elif args.mode == "mainline":
        modes = ["raw-generic-retry", "evas-assisted", "evas-guided-repair", "evas-guided-repair-no-skill", "skill-only", "skill-evas-informed"]
    else:
        modes = [args.mode]
    selected_tasks = set(args.task) if args.task else None
    tasks = _task_list(args.split, selected_tasks=selected_tasks)
    skill_bundle_text = None
    skill_bundle_path = Path(args.skill_bundle) if args.skill_bundle else None
    if any(mode in {"skill-only", "skill-evas-informed"} for mode in modes):
        if skill_bundle_path is None or not skill_bundle_path.exists():
            raise RuntimeError("skill mode requested but --skill-bundle does not exist")
        skill_bundle_text = load_skill_bundle(skill_bundle_path)

    print(f"[model-assisted] split={args.split} tasks={len(tasks)} models={len(models)} modes={','.join(modes)} stage={args.stage}")
    for task_id, _ in tasks:
        print(f"  task: {task_id}")

    if args.stage == "plan":
        return 0

    if args.stage in ("generate", "all") and not args.dry_run:
        ok, missing = _ensure_key_available(models)
        if not ok:
            print("[model-assisted] BLOCKED: required API key environment variables are missing.")
            for item in missing:
                print(f"  missing: {item}")
            print("[model-assisted] Set keys in your local shell, e.g. export BAILIAN_API_KEY='<token>', then rerun.")
            return 2

    final_return = 0
    for model in models:
        raw_evas_inner_root: Path | None = None
        skill_evas_inner_root: Path | None = None
        if args.stage in ("evas-inner", "generate", "all") and any(mode in {"evas-assisted", "evas-guided-repair", "evas-guided-repair-no-skill", "evas-guided-repair-3round", "evas-guided-repair-3round-skill"} for mode in modes):
            raw_evas_inner_root = score_baseline_evas(
                model=model,
                split=args.split,
                tasks=tasks,
                generated_root=ROOT / "generated",
                result_tag=None,
                sample_idx=args.sample_idx,
                temperature=args.temperature,
                top_p=args.top_p,
                timeout_s=args.timeout_s,
                force=args.force,
            )

        if args.stage in ("generate", "all"):
            if "skill-only" in modes or "skill-evas-informed" in modes:
                generate_mode(
                    mode="skill-only",
                    model=model,
                    split=args.split,
                    tasks=tasks,
                    sample_idx=args.sample_idx,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    max_tokens=args.max_tokens,
                    force=args.force,
                    dry_run=args.dry_run,
                    workers=args.workers,
                    evas_inner_root=None,
                    skill_bundle_text=skill_bundle_text,
                    skill_bundle_path=skill_bundle_path,
                )
            if "skill-evas-informed" in modes and not args.dry_run:
                skill_evas_inner_root = score_baseline_evas(
                    model=model,
                    split=args.split,
                    tasks=tasks,
                    generated_root=ROOT / MODE_TO_OUTPUT["skill-only"],
                    result_tag="skill",
                    sample_idx=args.sample_idx,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    timeout_s=args.timeout_s,
                    force=args.force,
                )
            for mode in modes:
                if mode == "skill-only":
                    continue
                if mode in {"evas-guided-repair-3round", "evas-guided-repair-3round-skill"}:
                    if raw_evas_inner_root is None:
                        print(f"[model-assisted] SKIP {mode}: no B baseline EVAS results")
                        continue
                    generate_multi_round_repair(
                        model=model,
                        split=args.split,
                        tasks=tasks,
                        sample_idx=args.sample_idx,
                        temperature=args.temperature,
                        top_p=args.top_p,
                        max_tokens=args.max_tokens,
                        force=args.force,
                        dry_run=args.dry_run,
                        evas_inner_root=raw_evas_inner_root,
                        workers=args.workers,
                        n_rounds=3,
                        include_skill=(mode == "evas-guided-repair-3round-skill"),
                        timeout_s=args.timeout_s,
                        layered_only_repair=args.layered_only_repair,
                    )
                    continue
                generate_mode(
                    mode=mode,
                    model=model,
                    split=args.split,
                    tasks=tasks,
                    sample_idx=args.sample_idx,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    max_tokens=args.max_tokens,
                    force=args.force,
                    dry_run=args.dry_run,
                    workers=args.workers,
                    evas_inner_root=raw_evas_inner_root if mode in {"evas-assisted", "evas-guided-repair", "evas-guided-repair-no-skill"} else skill_evas_inner_root,
                    skill_bundle_text=skill_bundle_text,
                    skill_bundle_path=skill_bundle_path,
                )

        if args.stage in ("spectre-final", "all") and not args.dry_run:
            for mode in modes:
                rc = run_spectre_final(
                    mode=mode,
                    model=model,
                    split=args.split,
                    tasks=tasks,
                    sample_idx=args.sample_idx,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    timeout_s=args.spectre_timeout_s,
                )
                if rc not in (0, 1):
                    final_return = rc

    return final_return


if __name__ == "__main__":
    raise SystemExit(main())
