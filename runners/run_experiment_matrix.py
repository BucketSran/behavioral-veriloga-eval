#!/usr/bin/env python3
"""
run_experiment_matrix.py - Run the complete experiment matrix for vaEvas benchmark.

Experiment Matrix:
- A (裸LLM): Checker❌, Skill❌, EVAS❌ → absolute baseline
- B (+Checker): Checker✓, Skill❌, EVAS❌ → checker transparency value
- C (+Skill): Checker✓, Skill✓, EVAS❌ → Skill contribution (their work)
- D (+EVAS): Checker✓, Skill❌, EVAS✓ (single-round) → EVAS diagnosis value
- E (+Skill+EVAS): Checker✓, Skill✓, EVAS✓ (single-round) → complete system
- F (+Multi-round EVAS): Checker✓, Skill❌, EVAS✓ (three-round) → current generalized repair condition
- G (+Multi-round EVAS+Skill): Checker✓, Skill✓, EVAS✓ (three-round) → skill-enabled multi-round repair

Usage:
    python3 runners/run_experiment_matrix.py --model kimi-k2.5 --split dev24 --stage all
    python3 runners/run_experiment_matrix.py --model kimi-k2.5 --split dev24 --stage generate --condition B
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Import dev24 task list from run_model_assisted_loop
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

# Experiment conditions mapping
CONDITIONS = {
    "A": {"include_checker": False, "include_skill": False, "repair_mode": None, "repair_include_skill": False},
    "B": {"include_checker": True, "include_skill": False, "repair_mode": None, "repair_include_skill": False},
    "C": {"include_checker": True, "include_skill": True, "repair_mode": None, "repair_include_skill": False},
    "D": {"include_checker": True, "include_skill": False, "repair_mode": "evas-guided-repair-no-skill", "repair_include_skill": False},
    "E": {"include_checker": True, "include_skill": True, "repair_mode": "evas-guided-repair", "repair_include_skill": True},
    "F": {"include_checker": True, "include_skill": False, "repair_mode": "evas-guided-repair-3round", "repair_include_skill": False},
    "G": {"include_checker": True, "include_skill": True, "repair_mode": "evas-guided-repair-3round-skill", "repair_include_skill": True},
}

DATE_TAG = datetime.now().strftime("%Y-%m-%d")


def get_output_dir(condition: str, model: str, split: str) -> Path:
    """Get output directory for a specific condition."""
    model_slug = model.replace("/", "_")
    condition_name = {
        "A": "baseline-raw",
        "B": "baseline-with-checker",
        "C": "baseline-with-checker-skill",
        "D": "repair-with-evas",
        "E": "repair-with-evas-skill",
        "F": "repair-with-evas-3round",
        "G": "repair-with-evas-3round-skill",
    }
    return ROOT / "results" / f"experiment-{condition_name[condition]}-{model_slug}-{split}-{DATE_TAG}"


def get_evas_output_dir(condition: str, model: str, split: str) -> Path:
    """Get EVAS scoring directory scoped by condition to avoid overwrite."""
    model_slug = model.replace("/", "_")
    return ROOT / "results" / f"evas-scoring-condition-{condition}-{model_slug}-{split}-{DATE_TAG}"


def get_task_list(split: str) -> list[str]:
    """Get task IDs for a given split."""
    if split == "dev24":
        return DEV24_TASK_IDS
    elif split == "full86":
        # Import from generate module
        sys.path.insert(0, str(ROOT / "runners"))
        from generate import list_task_dirs
        tasks = list_task_dirs()
        return [task_id for task_id, _ in tasks]
    else:
        raise ValueError(f"unsupported split: {split}")


def sync_baseline_for_repair(*, model: str, baseline_generated_root: Path) -> Path:
    """Mirror condition-B baseline into runners/run_model_assisted_loop expected path."""
    model_slug = model.replace("/", "_")
    src = baseline_generated_root / model_slug
    dst = ROOT / "generated" / model_slug
    if not src.exists():
        raise FileNotFoundError(f"repair baseline source missing: {src}")
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    print(f"[repair-sync] mirrored baseline {src} -> {dst}")
    return dst


def run_baseline(
    *,
    condition: str,
    model: str,
    split: str,
    sample_idx: int,
    temperature: float,
    top_p: float,
    max_tokens: int,
    gen_workers: int,
    force: bool,
    dry_run: bool,
) -> Path:
    """Run baseline generation for conditions A, B, C."""
    config = CONDITIONS[condition]
    output_dir = get_output_dir(condition, model, split)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_slug = model.replace("/", "_")
    generated_root = ROOT / "generated-experiment" / f"condition-{condition}" / model_slug

    task_ids = get_task_list(split)

    # generate.py has no --force flag; when force is requested, clear
    # prior generated artifacts so this run is guaranteed fresh.
    if force and generated_root.exists():
        print(f"[baseline-{condition}] force enabled: removing existing {generated_root}")
        shutil.rmtree(generated_root)

    cmd = [
        "python3", str(ROOT / "runners" / "generate.py"),
        "--model", model,
        "--output-dir", str(generated_root),
        "--sample-idx", str(sample_idx),
        "--temperature", str(temperature),
        "--top-p", str(top_p),
        "--max-tokens", str(max_tokens),
        "--max-workers", str(gen_workers),
    ]

    # Add task IDs
    for task_id in task_ids:
        cmd.extend(["--task", task_id])

    if config["include_checker"]:
        cmd.append("--include-checker")
    if config["include_skill"]:
        cmd.append("--include-skill")
    if dry_run:
        cmd.append("--dry-run")

    print(f"[baseline-{condition}] Running: {' '.join(cmd[:10])}... ({len(task_ids)} tasks)")
    proc = subprocess.run(cmd, cwd=ROOT, text=True)
    if proc.returncode != 0:
        print(f"[baseline-{condition}] ERROR: returncode={proc.returncode}")
        sys.exit(1)

    return generated_root


def run_evas_scoring(
    *,
    condition: str,
    generated_root: Path,
    model: str,
    split: str,
    sample_idx: int,
    temperature: float,
    top_p: float,
    timeout_s: int,
    score_workers: int,
    resume_score: bool,
    score_save_policy: str,
    force: bool,
) -> Path:
    """Run EVAS scoring on generated samples."""
    model_slug = model.replace("/", "_")
    output_root = get_evas_output_dir(condition, model, split)

    # score.py has no --force flag; when force is requested, clear prior
    # scoring outputs so this run starts from a clean result directory.
    if force and output_root.exists():
        print(f"[evas-scoring] force enabled: removing existing {output_root}")
        shutil.rmtree(output_root)

    cmd = [
        "python3", str(ROOT / "runners" / "score.py"),
        "--model", model_slug,
        "--generated-dir", str(generated_root),
        "--output-dir", str(output_root),
        "--sample-idx", str(sample_idx),
        "--temperature", str(temperature),
        "--top-p", str(top_p),
        "--timeout-s", str(timeout_s),
        "--workers", str(score_workers),
        "--save-policy", score_save_policy,
    ]
    if resume_score and not force:
        cmd.append("--resume")

    print(f"[evas-scoring] Running: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=ROOT, text=True)
    if proc.returncode not in (0, 1):
        print(f"[evas-scoring] ERROR: returncode={proc.returncode}")
        sys.exit(1)

    return output_root


def run_repair(
    *,
    condition: str,
    model: str,
    split: str,
    evas_inner_root: Path,
    sample_idx: int,
    temperature: float,
    top_p: float,
    max_tokens: int,
    workers: int,
    force: bool,
    dry_run: bool,
) -> Path:
    """Run repair loop for conditions D, E, F."""
    config = CONDITIONS[condition]
    model_slug = model.replace("/", "_")
    mode = config["repair_mode"]

    if mode is None:
        raise ValueError(f"Condition {condition} does not have a repair mode")

    cmd = [
        "python3", str(ROOT / "runners" / "run_model_assisted_loop.py"),
        "--model", model,
        "--split", split,
        "--mode", mode,
        "--stage", "generate",
        "--sample-idx", str(sample_idx),
        "--temperature", str(temperature),
        "--top-p", str(top_p),
        "--max-tokens", str(max_tokens),
        "--workers", str(workers),
    ]

    if force:
        cmd.append("--force")
    if dry_run:
        cmd.append("--dry-run")

    print(f"[repair-{condition}] Running: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=ROOT, text=True)
    if proc.returncode != 0:
        print(f"[repair-{condition}] ERROR: returncode={proc.returncode}")
        sys.exit(1)

    # run_model_assisted_loop writes to generated-table2-<mode>
    return ROOT / f"generated-table2-{mode}"


def main() -> int:
    global DATE_TAG
    ap = argparse.ArgumentParser(description="Run experiment matrix for vaEvas benchmark.")
    ap.add_argument("--model", required=True, help="Model name, e.g. kimi-k2.5")
    ap.add_argument("--split", choices=["dev24", "full86"], default="dev24")
    ap.add_argument("--condition", choices=["A", "B", "C", "D", "E", "F", "G", "all"], default="all",
                    help="Experiment condition. 'all' runs all conditions A-G.")
    ap.add_argument("--stage", choices=["baseline", "evas-inner", "repair", "all"], default="all")
    ap.add_argument("--sample-idx", type=int, default=0)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--gen-workers", type=int, default=4,
                    help="Parallel generation workers for baseline conditions A/B/C.")
    ap.add_argument("--score-workers", type=int, default=4,
                    help="Parallel EVAS scoring workers. Default: 4.")
    ap.add_argument("--resume-score", action="store_true",
                    help="Reuse matching per-task EVAS scoring results by input/checker fingerprint.")
    ap.add_argument("--score-save-policy", choices=["contract", "debug"], default="contract",
                    help="Save policy for EVAS scoring. Use debug to preserve extra repair observables.")
    ap.add_argument("--timeout-s", type=int, default=180)
    ap.add_argument("--date-tag", default=DATE_TAG,
                    help="Tag used in result directory names. Defaults to today's date.")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    DATE_TAG = args.date_tag

    conditions = ["A", "B", "C", "D", "E", "F", "G"] if args.condition == "all" else [args.condition]

    print(f"[experiment-matrix] model={args.model} split={args.split} conditions={conditions}")
    print(f"[experiment-matrix] Experiment Matrix:")
    for c in conditions:
        config = CONDITIONS[c]
        print(f"  Condition {c}: Checker={config['include_checker']} Skill={config['include_skill']} Repair={config['repair_mode']}")

    # Check API keys
    if not args.dry_run:
        from generate import detect_provider
        provider = detect_provider(args.model)
        key_name = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "bailian": "BAILIAN_API_KEY",
        }.get(provider)
        if key_name and not os.environ.get(key_name):
            print(f"[experiment-matrix] ERROR: {key_name} not set")
            return 1

    # Run experiments
    baseline_generated_dirs: dict[str, Path] = {}
    evas_result_dirs: dict[str, Path] = {}

    for condition in conditions:
        config = CONDITIONS[condition]

        # Baseline conditions A, B, C
        if condition in ("A", "B", "C") and args.stage in ("baseline", "all"):
            generated_root = run_baseline(
                condition=condition,
                model=args.model,
                split=args.split,
                sample_idx=args.sample_idx,
                temperature=args.temperature,
                top_p=args.top_p,
                max_tokens=args.max_tokens,
                gen_workers=args.gen_workers,
                force=args.force,
                dry_run=args.dry_run,
            )
            baseline_generated_dirs[condition] = generated_root

            # Run EVAS scoring for baseline conditions
            if args.stage == "all" and not args.dry_run:
                evas_root = run_evas_scoring(
                    condition=condition,
                    generated_root=generated_root,
                    model=args.model,
                    split=args.split,
                    sample_idx=args.sample_idx,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    timeout_s=args.timeout_s,
                    score_workers=args.score_workers,
                    resume_score=args.resume_score,
                    score_save_policy=args.score_save_policy,
                    force=args.force,
                )
                evas_result_dirs[condition] = evas_root

        # Repair conditions D, E, F, G
        if condition in ("D", "E", "F", "G") and args.stage in ("repair", "all"):
            # For repair, we need EVAS inner results from condition B baseline
            # (condition B has Checker but no Skill, which is the right baseline for repair)
            if "B" not in baseline_generated_dirs:
                print(f"[repair-{condition}] Need baseline B first. Running baseline B...")
                generated_root = run_baseline(
                    condition="B",
                    model=args.model,
                    split=args.split,
                    sample_idx=args.sample_idx,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    max_tokens=args.max_tokens,
                    gen_workers=args.gen_workers,
                    force=args.force,
                    dry_run=args.dry_run,
                )
                baseline_generated_dirs["B"] = generated_root

            if "B" not in evas_result_dirs and not args.dry_run:
                existing_b_evas = get_evas_output_dir("B", args.model, args.split)
                if (
                    not args.force
                    and existing_b_evas.exists()
                    and (existing_b_evas / "model_results.json").exists()
                ):
                    print(f"[repair-{condition}] Reusing existing baseline-B EVAS: {existing_b_evas}")
                    evas_result_dirs["B"] = existing_b_evas
                else:
                    print(f"[repair-{condition}] Running EVAS scoring for baseline B...")
                    evas_root = run_evas_scoring(
                        condition="B",
                        generated_root=baseline_generated_dirs["B"],
                        model=args.model,
                        split=args.split,
                        sample_idx=args.sample_idx,
                        temperature=args.temperature,
                        top_p=args.top_p,
                        timeout_s=args.timeout_s,
                        score_workers=args.score_workers,
                        resume_score=args.resume_score,
                        score_save_policy=args.score_save_policy,
                        force=args.force,
                    )
                    evas_result_dirs["B"] = evas_root

            if not args.dry_run:
                sync_baseline_for_repair(
                    model=args.model,
                    baseline_generated_root=baseline_generated_dirs["B"],
                )

            if not args.dry_run:
                repair_root = run_repair(
                    condition=condition,
                    model=args.model,
                    split=args.split,
                    evas_inner_root=evas_result_dirs["B"],
                    sample_idx=args.sample_idx,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    max_tokens=args.max_tokens,
                    workers=args.gen_workers,
                    force=args.force,
                    dry_run=args.dry_run,
                )
                print(f"[repair-{condition}] Output: {repair_root}")
                if args.stage == "all":
                    repaired_evas_root = run_evas_scoring(
                        condition=condition,
                        generated_root=repair_root,
                        model=args.model,
                        split=args.split,
                        sample_idx=args.sample_idx,
                        temperature=args.temperature,
                        top_p=args.top_p,
                        timeout_s=args.timeout_s,
                        score_workers=args.score_workers,
                        resume_score=args.resume_score,
                        score_save_policy=args.score_save_policy,
                        force=args.force,
                    )
                    print(f"[repair-{condition}] EVAS scoring output: {repaired_evas_root}")

    print(f"[experiment-matrix] Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
