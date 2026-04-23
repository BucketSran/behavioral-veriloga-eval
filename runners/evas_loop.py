#!/usr/bin/env python3
"""
evas_loop.py — EVAs closed-loop VA generation pipeline.

For each task in the 24-task end-to-end subset, iteratively generates
Verilog-A with an LLM, scores with EVAs, and re-prompts with structured
feedback until EVAs passes or max_rounds is reached.

Experimental design:
  Baseline (no feedback):  runners/generate.py + runners/score.py (existing)
  Closed loop (this file): each round feeds EVAs errors back to the LLM

The baseline does NOT receive any EVAs feedback — it is a pure one-shot
generation. This script is for the closed-loop condition only.

Round 0 uses the frozen Verilog-A skill bundle as a prior (build_skill_only_prompt).
Round 1+ uses dynamic targeted repair skill + EVAs diagnostics (build_evas_guided_repair_prompt).

Output layout:
  <gen-root>/<model_slug>/<task_id>/round_<N>/sample_0/
    ├── <module>.va
    ├── tb_<name>.scs
    └── generation_meta.json

  <results-root>/<task_id>/
    ├── round_<N>_result.json    EVAs result for each round
    └── final_result.json        first passing round, or last round

  <results-root>/loop_summary.json   aggregate stats across all tasks

Usage:
  cd behavioral-veriloga-eval
  python runners/evas_loop.py --model qwen3-max-2026-01-23 --max-rounds 8
  python runners/evas_loop.py --model kimi-k2.5 --task flash_adc_3b_smoke
  python runners/evas_loop.py --model qwen3-max-2026-01-23 --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup: runners/ is the CWD when this script is called from project root
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate as _gen
import score as _score
from build_repair_prompt import (
    build_evas_guided_repair_prompt,
    build_skill_only_prompt,
    load_skill_bundle,
    DEFAULT_SKILL_BUNDLE,
)
from simulate_evas import run_case


# ---------------------------------------------------------------------------
# 24-task subset (verified+passed end-to-end, balanced by category/difficulty)
# ---------------------------------------------------------------------------

LOOP_TASKS_24: list[str] = [
    # digital-logic (4): easy×2, medium×1, hard×1
    "digital_basics_smoke",
    "gray_counter_4b_smoke",
    "gray_counter_one_bit_change_smoke",
    "serializer_frame_alignment_smoke",
    # stimulus (3): easy×2, medium×1
    "clk_burst_gen_smoke",
    "timer_absolute_grid_smoke",
    "bound_step_period_guard_smoke",
    # data-converter (4): easy×2, medium×2
    "flash_adc_3b_smoke",
    "dac_binary_clk_4b_smoke",
    "adc_dac_ideal_4b_smoke",
    "dwa_wraparound_smoke",
    # comparator (4): easy×1, medium×3
    "cross_hysteresis_window_smoke",
    "cmp_delay_smoke",
    "comparator_hysteresis_smoke",
    "cmp_strongarm_smoke",
    # phase-detector (3): easy×1, medium×1, hard×1
    "xor_pd_smoke",
    "pfd_updn_smoke",
    "bbpd_data_edge_alignment_smoke",
    # pll-closed-loop (2): medium×1, hard×1
    "cppll_freq_step_reacquire_smoke",
    "adpll_ratio_hop_smoke",
    # sample-hold (2): easy×1, medium×1
    "sample_hold_smoke",
    "sample_hold_droop_smoke",
    # pll (1): hard×1
    "multimod_divider_ratio_switch_smoke",
    # calibration (1): medium×1
    "dwa_ptr_gen_smoke",
]
assert len(LOOP_TASKS_24) == 24


TASK_ROOT = ROOT / "tasks" / "end-to-end" / "voltage"


# ---------------------------------------------------------------------------
# File finders that skip dry-run placeholder files
# ---------------------------------------------------------------------------

def _find_va_file(sample_dir: Path) -> Path | None:
    """Return the first real .va file, skipping _dryrn placeholders."""
    vas = [p for p in sorted(sample_dir.glob("*.va")) if "_dryrn" not in p.name]
    return vas[0] if vas else None


def _find_tb_file(sample_dir: Path) -> Path | None:
    """Return the first real .scs testbench, skipping _dryrn placeholders."""
    preferred = [p for p in sorted(sample_dir.glob("tb_*.scs")) if "_dryrn" not in p.name]
    if preferred:
        return preferred[0]
    fallbacks = [p for p in sorted(sample_dir.glob("*.scs")) if "_dryrn" not in p.name]
    return fallbacks[0] if fallbacks else None


# ---------------------------------------------------------------------------
# stdout_tail → augmented notes for compile failures
# ---------------------------------------------------------------------------

def _augment_notes_with_stdout(evas_result: dict) -> dict:
    """For compile failures, prepend key error lines from stdout_tail into evas_notes."""
    status = evas_result.get("status", "")
    stdout_tail = evas_result.get("stdout_tail", "")
    if status not in ("FAIL_DUT_COMPILE", "FAIL_TB_COMPILE") or not stdout_tail:
        return evas_result

    lines = stdout_tail.splitlines()
    error_lines: list[str] = []
    for i, line in enumerate(lines):
        if any(kw in line for kw in ("Error", "error", "ParseError", "SyntaxError",
                                      "Traceback", "Exception", "FAILED", "fatal",
                                      "Warning", "warning")):
            start = max(0, i - 1)
            end = min(len(lines), i + 3)
            error_lines.extend(lines[start:end])
            if len(error_lines) >= 25:
                break

    if error_lines:
        deduped = list(dict.fromkeys(error_lines))
        compile_note = "compile_log: " + " | ".join(deduped[:20])
        existing = list(evas_result.get("evas_notes", []))
        return {**evas_result, "evas_notes": [compile_note] + existing}
    return evas_result


# ---------------------------------------------------------------------------
# Per-round generation
# ---------------------------------------------------------------------------

def generate_round(
    task_id: str,
    task_dir: Path,
    sample_dir: Path,
    *,
    model: str,
    round_idx: int,
    temperature: float,
    top_p: float,
    max_tokens: int,
    dry_run: bool,
    prompt_text: str,
) -> dict:
    """Generate DUT + TB for one round. Returns generation_meta dict."""
    sample_dir.mkdir(parents=True, exist_ok=True)

    gen_meta_base = {
        "model": model,
        "task_id": task_id,
        "round": round_idx,
        "temperature": temperature,
        "top_p": top_p,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "with_feedback": round_idx > 0,
    }

    if dry_run:
        placeholder_va = (
            '`include "constants.vams"\n`include "disciplines.vams"\n\n'
            f"// DRY-RUN placeholder for {task_id} round {round_idx}\n"
            f"module {task_id}_dryrn(out);\n"
            "    output electrical out;\n"
            "    analog V(out) <+ 0.0;\n"
            "endmodule\n"
        )
        placeholder_scs = (
            "simulator lang=spectre\nglobal 0\n"
            f"// DRY-RUN placeholder testbench for {task_id}\n"
            f"I1 (0 out) {task_id}_dryrn\n"
            "tran tran stop=10n\n"
            f'ahdl_include "./{task_id}_dryrn.va"\n'
        )
        (sample_dir / f"{task_id}_dryrn.va").write_text(placeholder_va)
        (sample_dir / f"tb_{task_id}_dryrn.scs").write_text(placeholder_scs)
        gen_meta = {**gen_meta_base, "status": "dry_run", "input_tokens": 0, "output_tokens": 0}
        (sample_dir / "generation_meta.json").write_text(json.dumps(gen_meta, indent=2))
        return gen_meta

    try:
        response_text, usage = _gen.call_model(model, prompt_text, temperature, top_p, max_tokens)
    except Exception as exc:
        gen_meta = {**gen_meta_base, "status": "api_error", "error": str(exc)[:400],
                    "input_tokens": 0, "output_tokens": 0}
        (sample_dir / "generation_meta.json").write_text(json.dumps(gen_meta, indent=2))
        return gen_meta

    blocks = _gen.extract_code_blocks(response_text)
    saved_files: list[str] = []

    for va_code in blocks["va"]:
        module_name = _gen.infer_module_name(va_code)
        va_path = sample_dir / f"{module_name}.va"
        va_path.write_text(va_code, encoding="utf-8")
        saved_files.append(str(va_path))

    if blocks["scs"]:
        scs_code = blocks["scs"][0]
        tb_name = _gen.infer_tb_name(scs_code)
        scs_path = sample_dir / f"{tb_name}.scs"
        scs_path.write_text(scs_code, encoding="utf-8")
        saved_files.append(str(scs_path))

    gen_meta = {
        **gen_meta_base,
        "status": "generated" if saved_files else "no_code_extracted",
        "saved_files": saved_files,
        **usage,
    }
    (sample_dir / "generation_meta.json").write_text(json.dumps(gen_meta, indent=2))
    if not saved_files:
        print(f"    WARNING: no code blocks extracted for {task_id} round {round_idx}")
    return gen_meta


# ---------------------------------------------------------------------------
# Per-round scoring (returns full EVAs result including stdout_tail)
# ---------------------------------------------------------------------------

def score_for_loop(
    task_id: str,
    task_dir: Path,
    sample_dir: Path,
    *,
    timeout_s: int = 180,
) -> dict:
    """Score a generated candidate and return full result including stdout_tail."""
    meta = _score.read_meta(task_dir)
    family = meta.get("family", "end-to-end")
    required_axes: list[str] = meta.get("scoring", ["dut_compile", "tb_compile", "sim_correct"])
    gold_dir = task_dir / "gold"

    # Use dryrn-filtered finders to avoid stale placeholder files
    dut_path = _find_va_file(sample_dir)
    tb_path = _find_tb_file(sample_dir)
    gold_tb = _score.choose_gold_tb(gold_dir)

    if dut_path is None or not dut_path.exists():
        return {"status": "FAIL_INFRA", "scores": _zero_scores(required_axes),
                "evas_notes": ["missing_dut_va"], "stdout_tail": ""}
    if tb_path is None or not tb_path.exists():
        return {"status": "FAIL_INFRA", "scores": _zero_scores(required_axes),
                "evas_notes": ["missing_tb_scs"], "stdout_tail": ""}

    # Extract gold structure for structure diagnosis
    gold_structure = None
    if gold_tb and gold_tb.exists():
        gold_structure = _score.tb_structure(gold_tb)

    with tempfile.TemporaryDirectory(prefix=f"loop_{task_id}_") as tmp:
        tmp_path = Path(tmp)
        tmp_dut, tmp_tb, staging_notes = _score.stage_candidate_case(
            family=family,
            gold_dir=gold_dir,
            sample_dir=sample_dir,
            dut_path=dut_path,
            tb_path=tb_path,
            stage_dir=tmp_path,
            auxiliary_gold_vas=[],
        )

        strict_status, strict_scores, strict_notes = _score.spectre_strict_preflight(
            family=family,
            required_axes=required_axes,
            staged_tb=tmp_tb,
            staged_va_paths=sorted(tmp_path.rglob("*.va")),
        )
        if strict_status is not None and strict_scores is not None:
            return {
                "status": strict_status,
                "scores": strict_scores,
                "evas_notes": staging_notes + strict_notes,
                "stdout_tail": "",
                "structure_diagnosis": None,
            }

        out_dir = tmp_path / "evas_out"
        out_dir.mkdir()
        try:
            raw = run_case(
                task_dir, tmp_dut, tmp_tb,
                output_root=out_dir,
                timeout_s=timeout_s,
                task_id_override=task_id,
                gold_structure=gold_structure,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "FAIL_INFRA",
                "scores": _zero_scores(required_axes),
                "evas_notes": staging_notes + strict_notes + ["evas_timeout"],
                "stdout_tail": "",
                "structure_diagnosis": None,
            }

    return {
        "status": raw["status"],
        "scores": raw["scores"],
        "evas_notes": staging_notes + strict_notes + raw.get("notes", []),
        "stdout_tail": raw.get("stdout_tail", ""),
        "structure_diagnosis": raw.get("structure_diagnosis"),
    }


def _zero_scores(required_axes: list[str]) -> dict:
    scores = {"dut_compile": 0.0, "tb_compile": 0.0, "sim_correct": 0.0}
    axes = [a for a in required_axes if a in scores]
    scores["weighted_total"] = 0.0 if axes else 0.0
    return scores


def _task_pass(result: dict) -> bool:
    scores = result.get("scores", {})
    required = ["dut_compile", "tb_compile", "sim_correct"]
    return all(scores.get(ax, 0.0) >= 1.0 for ax in required)


# ---------------------------------------------------------------------------
# Per-task loop
# ---------------------------------------------------------------------------

def run_task_loop(
    task_id: str,
    *,
    model: str,
    model_slug: str,
    gen_root: Path,
    results_root: Path,
    max_rounds: int,
    temperature: float,
    top_p: float,
    max_tokens: int,
    dry_run: bool,
    timeout_s: int,
    skill_bundle_text: str,
    force: bool = False,
) -> dict:
    """Run the full EVAs closed loop for one task. Returns final_result dict."""
    task_dir = TASK_ROOT / task_id
    if not task_dir.exists():
        return {"task_id": task_id, "status": "FAIL_INFRA", "error": "task_dir_not_found",
                "passed_round": None, "total_rounds": 0}

    task_results_dir = results_root / task_id
    task_results_dir.mkdir(parents=True, exist_ok=True)

    # Resume: find the last completed round
    start_round = 0
    prev_evas_result: dict = {}
    prev_sample_dir: Path | None = None
    last_result: dict = {}
    passed_round: int | None = None
    # Accumulated history: prevents model from oscillating back to previously fixed errors
    round_history: list[dict] = []

    if not force:
        # Check if final_result.json already exists
        final_path = task_results_dir / "final_result.json"
        if final_path.exists():
            final = json.loads(final_path.read_text(encoding="utf-8"))
            print(f"    [resume] final_result.json exists, skipping")
            return final

        # Find the last completed round
        for r in range(max_rounds):
            rpath = task_results_dir / f"round_{r}_result.json"
            if rpath.exists():
                rdata = json.loads(rpath.read_text(encoding="utf-8"))
                last_result = rdata
                prev_status = rdata.get("status", "FAIL_OTHER")
                round_history.append({"round": r, "evas_notes": rdata.get("evas_notes", [])})
                if _task_pass(rdata):
                    passed_round = r
                    break
                # Load prev_evas_result for repair prompt
                prev_sample_dir = gen_root / model_slug / task_id / f"round_{r}" / "sample_0"
                prev_evas_result = {
                    "status": prev_status,
                    "scores": rdata.get("scores", {}),
                    "evas_notes": rdata.get("evas_notes", []),
                    "stdout_tail": "",  # not persisted; will be re-scored if needed
                }
                start_round = r + 1

        if passed_round is not None:
            final_result = {
                **last_result,
                "passed_round": passed_round,
                "total_rounds_run": passed_round + 1,
                "max_rounds": max_rounds,
            }
            (task_results_dir / "final_result.json").write_text(
                json.dumps(final_result, indent=2), encoding="utf-8"
            )
            return final_result

    for round_idx in range(start_round, max_rounds):
        sample_dir = gen_root / model_slug / task_id / f"round_{round_idx}" / "sample_0"

        # Build prompt
        if round_idx == 0:
            prompt_text = build_skill_only_prompt(task_dir, skill_bundle_text=skill_bundle_text)
        else:
            # Augment prev evas_result with stdout_tail error lines, pass full history
            augmented = _augment_notes_with_stdout(prev_evas_result)
            prompt_text = build_evas_guided_repair_prompt(
                task_dir, prev_sample_dir, augmented,
                history=round_history,
            )

        # Generate
        gen_meta = generate_round(
            task_id, task_dir, sample_dir,
            model=model,
            round_idx=round_idx,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            dry_run=dry_run,
            prompt_text=prompt_text,
        )

        if gen_meta.get("status") == "api_error":
            round_result = {
                "task_id": task_id, "round": round_idx,
                "status": "FAIL_INFRA", "scores": _zero_scores(["dut_compile", "tb_compile", "sim_correct"]),
                "evas_notes": [f"api_error: {gen_meta.get('error','')}"],
                "generation_meta": gen_meta,
            }
            evas_result: dict = {"status": "FAIL_INFRA", "scores": round_result["scores"],
                                 "evas_notes": round_result["evas_notes"], "stdout_tail": ""}
        else:
            evas_result = score_for_loop(task_id, task_dir, sample_dir, timeout_s=timeout_s)
            round_result = {
                "task_id": task_id,
                "round": round_idx,
                "status": evas_result["status"],
                "scores": evas_result["scores"],
                "evas_notes": evas_result["evas_notes"],
                "generation_meta": gen_meta,
                "structure_diagnosis": evas_result.get("structure_diagnosis"),
            }

        # Save round result (stdout_tail omitted to keep JSON clean)
        round_path = task_results_dir / f"round_{round_idx}_result.json"
        round_path.write_text(json.dumps(round_result, indent=2), encoding="utf-8")

        # Update state for next iteration
        prev_sample_dir = sample_dir
        prev_evas_result = evas_result
        last_result = round_result
        round_history.append({"round": round_idx, "evas_notes": evas_result.get("evas_notes", [])})

        status_str = round_result["status"]
        wt = round_result["scores"].get("weighted_total", 0.0)
        print(f"    round {round_idx}: {status_str}  weighted={wt:.3f}")

        if _task_pass(round_result):
            passed_round = round_idx
            break

    final_result = {
        **last_result,
        "passed_round": passed_round,
        "total_rounds_run": (passed_round if passed_round is not None else max_rounds - 1) + 1,
        "max_rounds": max_rounds,
    }
    (task_results_dir / "final_result.json").write_text(
        json.dumps(final_result, indent=2), encoding="utf-8"
    )
    return final_result


# ---------------------------------------------------------------------------
# Aggregate summary
# ---------------------------------------------------------------------------

def build_loop_summary(model_slug: str, task_results: list[dict],
                       temperature: float, top_p: float) -> dict:
    total = len(task_results)
    if total == 0:
        return {"model": model_slug, "total": 0, "pass_rate": 0.0}

    n_pass = sum(1 for r in task_results if r.get("passed_round") is not None)
    pass_rounds = [r["passed_round"] for r in task_results if r.get("passed_round") is not None]
    avg_rounds_to_pass = round(sum(pass_rounds) / len(pass_rounds), 2) if pass_rounds else None

    fail_taxonomy: dict[str, int] = {}
    for r in task_results:
        if r.get("passed_round") is None:
            label = r.get("status", "FAIL_OTHER")
            fail_taxonomy[label] = fail_taxonomy.get(label, 0) + 1

    return {
        "model": model_slug,
        "temperature": temperature,
        "top_p": top_p,
        "total_tasks": total,
        "pass_count": n_pass,
        "pass_rate": round(n_pass / total, 4),
        "avg_rounds_to_pass": avg_rounds_to_pass,
        "pass_by_round": {
            str(r): sum(1 for t in task_results if t.get("passed_round") == r)
            for r in sorted(set(pass_rounds))
        },
        "fail_taxonomy_final_round": fail_taxonomy,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="EVAs closed-loop VA generation pipeline for the 24-task end-to-end subset."
    )
    ap.add_argument("--model", required=True,
                    help="Model name, e.g. qwen3-max-2026-01-23 or kimi-k2.5")
    ap.add_argument("--max-rounds", type=int, default=8,
                    help="Maximum EVAs feedback rounds per task. Default: 8")
    ap.add_argument("--task", nargs='*', default=[],
                    help="Run only these task_ids (space-separated). Default: all 24.")
    ap.add_argument("--workers", type=int, default=4,
                    help="Number of parallel workers. Default: 4")
    ap.add_argument("--gen-root", default="generated-loop",
                    help="Root for generated files. Default: generated-loop/")
    ap.add_argument("--results-root", default="",
                    help="Root for results. Default: results/evas-loop-<model>/")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--timeout-s", type=int, default=180,
                    help="EVAS simulation timeout per round (seconds). Default: 180")
    ap.add_argument("--dry-run", action="store_true",
                    help="Write placeholder files without calling any API.")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite existing round results (default: resume from last completed round).")
    ap.add_argument("--skill-bundle", default="",
                    help="Path to Verilog-A skill bundle markdown. Default: docs/TABLE2_VERILOGA_SKILL_BUNDLE.md")
    ap.add_argument("--bailian-api-key", default="",
                    help="Bailian/DashScope API key. Overrides BAILIAN_API_KEY env var.")
    args = ap.parse_args()

    model_slug = args.model.replace("/", "_")

    # Validate API key
    if not args.dry_run:
        try:
            provider = _gen.detect_provider(args.model)
        except ValueError as e:
            print(f"[evas_loop] ERROR: {e}")
            return 1
        if provider == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
            print("[evas_loop] ERROR: ANTHROPIC_API_KEY not set.")
            return 1
        elif provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
            print("[evas_loop] ERROR: OPENAI_API_KEY not set.")
            return 1
        elif provider == "bailian":
            key = args.bailian_api_key or os.environ.get("BAILIAN_API_KEY", "")
            if not key:
                print("[evas_loop] ERROR: BAILIAN_API_KEY not set.")
                return 1
            _gen._bailian_api_key_override = key

    # Load skill bundle
    skill_bundle_path = Path(args.skill_bundle) if args.skill_bundle else DEFAULT_SKILL_BUNDLE
    skill_bundle_text = load_skill_bundle(skill_bundle_path)
    print(f"[evas_loop] skill bundle: {skill_bundle_path.name} ({len(skill_bundle_text)} chars)")

    gen_root = Path(args.gen_root)
    if not gen_root.is_absolute():
        gen_root = ROOT / gen_root

    results_root = (
        Path(args.results_root) if args.results_root
        else ROOT / "results" / f"evas-loop-{model_slug}"
    )
    if not results_root.is_absolute():
        results_root = ROOT / results_root
    results_root.mkdir(parents=True, exist_ok=True)

    # Task selection
    selected = set(args.task) if args.task else set(LOOP_TASKS_24)
    task_ids = [t for t in LOOP_TASKS_24 if t in selected]
    if args.task:
        for t in args.task:
            if t not in task_ids:
                task_ids.append(t)

    print(f"[evas_loop] model={args.model}  tasks={len(task_ids)}"
          f"  max_rounds={args.max_rounds}  temp={args.temperature}"
          f"  workers={args.workers}  force={args.force}  dry_run={args.dry_run}")

    all_results: list[dict] = []
    results_lock = []

    def run_single_task(task_id: str) -> tuple[str, dict]:
        """Run single task and return (task_id, result)."""
        result = run_task_loop(
            task_id,
            model=args.model,
            model_slug=model_slug,
            gen_root=gen_root,
            results_root=results_root,
            max_rounds=args.max_rounds,
            temperature=args.temperature,
            top_p=args.top_p,
            max_tokens=args.max_tokens,
            dry_run=args.dry_run,
            timeout_s=args.timeout_s,
            skill_bundle_text=skill_bundle_text,
            force=args.force,
        )
        return task_id, result

    if args.workers > 1 and len(task_ids) > 1:
        # Parallel execution
        print(f"[evas_loop] Running {len(task_ids)} tasks with {args.workers} workers...")
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(run_single_task, tid): tid for tid in task_ids}
            for future in as_completed(futures):
                task_id, final = future.result()
                passed = final.get("passed_round")
                status_line = (f"PASS at round {passed}" if passed is not None
                               else f"FAIL after {final.get('total_rounds_run', '?')} rounds")
                print(f"  [{task_id}] → {status_line}")
                all_results.append(final)
    else:
        # Sequential execution
        for task_id in task_ids:
            print(f"  [{task_id}]")
            final = run_task_loop(
                task_id,
                model=args.model,
                model_slug=model_slug,
                gen_root=gen_root,
                results_root=results_root,
                max_rounds=args.max_rounds,
                temperature=args.temperature,
                top_p=args.top_p,
                max_tokens=args.max_tokens,
                dry_run=args.dry_run,
                timeout_s=args.timeout_s,
                skill_bundle_text=skill_bundle_text,
                force=args.force,
            )
            passed = final.get("passed_round")
            status_line = (f"PASS at round {passed}" if passed is not None
                           else f"FAIL after {final.get('total_rounds_run', '?')} rounds")
            print(f"  → {status_line}")
            all_results.append(final)

    summary = build_loop_summary(model_slug, all_results, args.temperature, args.top_p)
    summary_path = results_root / "loop_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\n[evas_loop] {model_slug}  tasks={summary['total_tasks']}"
          f"  pass_rate={summary['pass_rate']:.3f}"
          f"  ({summary['pass_count']}/{summary['total_tasks']})")
    if summary.get("avg_rounds_to_pass") is not None:
        print(f"  avg rounds to pass: {summary['avg_rounds_to_pass']}")
    print(f"  pass by round: {summary.get('pass_by_round', {})}")
    print(f"\n  → {results_root}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
