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

Usage:
    python3 runners/run_experiment_matrix.py --model kimi-k2.5 --split dev24 --stage all
    python3 runners/run_experiment_matrix.py --model kimi-k2.5 --split dev24 --stage generate --condition B
"""
from __future__ import annotations

import argparse
import json
import os
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
}

DATE_TAG = "2026-04-22"


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
    }
    return ROOT / "results" / f"experiment-{condition_name[condition]}-{model_slug}-{split}-{DATE_TAG}"


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


def run_baseline(
    *,
    condition: str,
    model: str,
    split: str,
    sample_idx: int,
    temperature: float,
    top_p: float,
    max_tokens: int,
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

    cmd = [
        "python3", str(ROOT / "runners" / "generate.py"),
        "--model", model,
        "--output-dir", str(generated_root),
        "--sample-idx", str(sample_idx),
        "--temperature", str(temperature),
        "--top-p", str(top_p),
        "--max-tokens", str(max_tokens),
    ]

    # Add task IDs
    for task_id in task_ids:
        cmd.extend(["--task", task_id])

    if config["include_checker"]:
        cmd.append("--include-checker")
    if config["include_skill"]:
        cmd.append("--include-skill")
    if force:
        cmd.append("--force")
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
    generated_root: Path,
    model: str,
    split: str,
    sample_idx: int,
    temperature: float,
    top_p: float,
    timeout_s: int,
    force: bool,
) -> Path:
    """Run EVAS scoring on generated samples."""
    model_slug = model.replace("/", "_")
    output_root = ROOT / "results" / f"evas-scoring-{model_slug}-{split}-{DATE_TAG}"

    cmd = [
        "python3", str(ROOT / "runners" / "score.py"),
        "--model", model_slug,
        "--generated-dir", str(generated_root),
        "--output-dir", str(output_root),
        "--sample-idx", str(sample_idx),
        "--temperature", str(temperature),
        "--top-p", str(top_p),
        "--timeout-s", str(timeout_s),
    ]

    if force:
        cmd.append("--force")

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

    # Return the generated output directory
    return ROOT / "generated-table2" / f"{mode}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Run experiment matrix for vaEvas benchmark.")
    ap.add_argument("--model", required=True, help="Model name, e.g. kimi-k2.5")
    ap.add_argument("--split", choices=["dev24", "full86"], default="dev24")
    ap.add_argument("--condition", choices=["A", "B", "C", "D", "E", "F", "all"], default="all",
                    help="Experiment condition. 'all' runs all conditions A-F.")
    ap.add_argument("--stage", choices=["baseline", "evas-inner", "repair", "all"], default="all")
    ap.add_argument("--sample-idx", type=int, default=0)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--timeout-s", type=int, default=180)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conditions = ["A", "B", "C", "D", "E", "F"] if args.condition == "all" else [args.condition]

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
                force=args.force,
                dry_run=args.dry_run,
            )
            baseline_generated_dirs[condition] = generated_root

            # Run EVAS scoring for baseline conditions
            if args.stage == "all" and not args.dry_run:
                evas_root = run_evas_scoring(
                    generated_root=generated_root,
                    model=args.model,
                    split=args.split,
                    sample_idx=args.sample_idx,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    timeout_s=args.timeout_s,
                    force=args.force,
                )
                evas_result_dirs[condition] = evas_root

        # Repair conditions D, E, F
        if condition in ("D", "E", "F") and args.stage in ("repair", "all"):
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
                    force=args.force,
                    dry_run=args.dry_run,
                )
                baseline_generated_dirs["B"] = generated_root

            if "B" not in evas_result_dirs and not args.dry_run:
                print(f"[repair-{condition}] Running EVAS scoring for baseline B...")
                evas_root = run_evas_scoring(
                    generated_root=baseline_generated_dirs["B"],
                    model=args.model,
                    split=args.split,
                    sample_idx=args.sample_idx,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    timeout_s=args.timeout_s,
                    force=args.force,
                )
                evas_result_dirs["B"] = evas_root

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
                    force=args.force,
                    dry_run=args.dry_run,
                )
                print(f"[repair-{condition}] Output: {repair_root}")

    print(f"[experiment-matrix] Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
