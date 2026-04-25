#!/usr/bin/env python3
"""Adaptive EVAS repair pilot.

This runner is intentionally small and experimental. It tests whether EVAS
feedback can drive a fast repair loop without committing to a fixed round count.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from build_repair_prompt import build_evas_guided_repair_prompt, metric_gap_summary
from generate import call_model, extract_module_signature, list_task_dirs, read_meta
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
    "conditional_cross=",
    "conditional_transition=",
    "digital_verilog_syntax=",
    "genvar_inside_analog=",
    "undefined_module=",
    "colon_instance_syntax_lines=",
    "evas_compile_errors:",
    "missing dout_code",
    "missing dout_0..7",
    "bit_mismatch",
    "only_",
    "unique_codes=",
    "up_first=",
    "dn_first=",
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
    return base


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
            if quick_maxstep:
                updated = re.sub(r"\bmaxstep\s*=\s*0\.[0-9]+n\b", f"maxstep={quick_maxstep}", line)
                if updated != line:
                    edits.append(f"relaxed maxstep in {tb.name}: {line.strip()} -> {updated.strip()}")
                    line = updated
            new_lines.append(line)
        if new_lines != lines:
            tb.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return edits


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
    if edits:
        result.setdefault("evas_notes", []).insert(0, "quick_sanitize=" + ";".join(edits))
        _json_write(output_root / task_id / "result.json", result)
    return result


def _task_lookup(task_ids: list[str]) -> list[tuple[str, Path]]:
    selected = set(task_ids)
    tasks = [(tid, path) for tid, path in list_task_dirs(selected=selected)]
    found = {tid for tid, _ in tasks}
    missing = sorted(selected - found)
    if missing:
        raise SystemExit(f"Missing task ids: {', '.join(missing)}")
    return tasks


def run_task(args: argparse.Namespace, task_id: str, task_dir: Path) -> dict:
    model_slug = _model_slug(args.model)
    out_root = Path(args.output_root)
    gen_root = Path(args.generated_root) / model_slug / task_id
    gen_root.mkdir(parents=True, exist_ok=True)

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
        result_path = Path(result_root) / task_id / "result.json" if result_root else None
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
        rank = _progress_rank(task_id, result)
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
    best_rank = _progress_rank(task_id, best_result)
    best_layer = _classify_repair_layer(best_result)
    anchor_sample = best_sample
    anchor_result = best_result
    history: list[dict] = []
    no_progress = 0

    print(f"[adaptive] {task_id} R0 {best_result.get('status')} layer={best_layer} rank={best_rank}")

    for round_idx in range(1, args.max_rounds + 1):
        if best_result.get("status") == "PASS":
            break
        layer = _classify_repair_layer(anchor_result)
        prompt = build_evas_guided_repair_prompt(
            task_dir,
            anchor_sample,
            anchor_result,
            history=history,
            include_skill=True,
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
        elif args.freeze_gold_harness_on_behavior and anchor_result.get("status") == "FAIL_SIM_CORRECTNESS":
            prompt += _layer_policy_section("behavior", task_dir)
        sample_dir = gen_root / f"adaptive_round{round_idx}"
        sample_dir.mkdir(parents=True, exist_ok=True)
        (sample_dir / "repair_prompt.md").write_text(prompt, encoding="utf-8")

        print(f"[adaptive] CALL {model_slug}/{task_id} R{round_idx} ... ", end="", flush=True)
        response_text, usage = call_model(
            args.model,
            prompt,
            args.temperature if round_idx == 1 else max(args.temperature, 0.2),
            args.top_p,
            args.max_tokens,
        )
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
        if args.layered_only_repair:
            if layer == "observable":
                frozen_duts = _freeze_veriloga_from(anchor_sample, sample_dir)
            elif layer == "behavior":
                frozen_harness = _freeze_gold_harness(task_dir, sample_dir)
        elif anchor_result.get("status") == "FAIL_SIM_CORRECTNESS":
            if args.freeze_gold_harness_on_behavior:
                frozen_harness = _freeze_gold_harness(task_dir, sample_dir)
            elif args.freeze_tb_on_behavior:
                frozen_tbs = _freeze_testbench_from(best_sample, sample_dir)
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
                "repair_layer": layer,
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
        rank = _progress_rank(task_id, result)
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
                "metric_gap": metric_gap_summary(task_dir, result),
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
        if result.get("status") == "PASS" or no_progress >= args.patience:
            break

    final_dir = Path(args.generated_root) / model_slug / task_id / f"sample_{args.sample_idx}"
    _copy_sample(best_sample, final_dir)
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
    ap.add_argument("--task", action="append", default=[])
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
    ap.add_argument("--freeze-tb-on-behavior", action="store_true",
                    help="For behavior failures, keep the best-so-far testbench and only evaluate generated DUT changes.")
    ap.add_argument("--freeze-gold-harness-on-behavior", action="store_true",
                    help="For behavior failures, use benchmark gold stimulus/save harness while preserving generated DUT code.")
    ap.add_argument("--layered-only-repair", action="store_true",
                    help="Automatically route compile/observable/behavior failures to the narrowest editable layer.")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    _load_env_file(Path(args.env_file))
    tasks = _task_lookup(args.task or DEFAULT_TASKS)
    results = []
    for task_id, task_dir in tasks:
        results.append(run_task(args, task_id, task_dir))
    summary = {
        "model": args.model,
        "tasks": len(results),
        "pass_count": sum(1 for r in results if r.get("status") == "PASS"),
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
