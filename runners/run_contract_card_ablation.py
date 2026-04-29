#!/usr/bin/env python3
"""Run and summarize contract-guided repair-card ablations.

This runner is an orchestration layer only. It does not change scoring or
checker semantics. It wires together:

1. adaptive repair with v7 behavior contracts and optional repair cards;
2. independent `score.py`;
3. final contract-vector checking;
4. a compact markdown comparison report.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import shlex
import subprocess
import sys
from pathlib import Path

from contract_check import run_contracts
from contract_repair_cards import select_contract_repair_cards
from generate import list_task_dirs, read_meta
from run_model_assisted_loop import _model_slug

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASKS = [
    "adc_dac_ideal_4b_smoke",
    "bg_cal",
    "cdac_cal",
    "segmented_dac",
    "dac_therm_16b_smoke",
]
DEFAULT_CONTRACT_ROOT = "results/generated-behavior-contracts-H-on-F-stable-2026-04-26-v7"
DEFAULT_SOURCE_GENERATED = "generated-condition-H-on-F-kimi-2026-04-26"
DEFAULT_INITIAL_RESULT = "results/latest-system-score-condition-H-on-F-kimi-2026-04-26-stable"
DEFAULT_COMPARE_RESULT = "results/adaptive-assertion-guided-v6-highconf-kimi-2026-04-26-final-score"


def _json_read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _task_dirs(task_ids: list[str]) -> dict[str, Path]:
    selected = set(task_ids)
    found = {task_id: task_dir for task_id, task_dir in list_task_dirs(selected=selected)}
    missing = sorted(selected - set(found))
    if missing:
        raise SystemExit(f"Missing task ids: {', '.join(missing)}")
    return found


def _command_text(cmd: list[str], env_delta: dict[str, str] | None = None) -> str:
    prefix = ""
    if env_delta:
        prefix = " ".join(f"{key}={shlex.quote(value)}" for key, value in sorted(env_delta.items())) + " "
    return prefix + " ".join(shlex.quote(part) for part in cmd)


def _run(
    cmd: list[str],
    *,
    env_delta: dict[str, str] | None = None,
    dry_run: bool = False,
    wall_timeout_s: int = 0,
) -> None:
    print(_command_text(cmd, env_delta))
    if dry_run:
        return
    env = os.environ.copy()
    if env_delta:
        env.update(env_delta)
    proc = subprocess.Popen(cmd, cwd=ROOT, env=env, start_new_session=True)
    try:
        proc.wait(timeout=wall_timeout_s or None)
    except subprocess.TimeoutExpired as exc:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
        raise SystemExit(
            f"Command exceeded wall timeout ({wall_timeout_s}s): {_command_text(cmd, env_delta)}"
        ) from exc
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, cmd)


def _result(root: Path, task_id: str) -> dict:
    path = root / task_id / "result.json"
    return _json_read(path) if path.exists() else {"status": "MISSING", "scores": {}}


def _weighted(result: dict) -> str:
    value = result.get("scores", {}).get("weighted_total")
    return "" if value is None else str(value)


def _prompt_card_ids(generated_root: Path, model_slug: str, task_id: str) -> list[str]:
    prompt = generated_root / model_slug / task_id / "adaptive_round1" / "repair_prompt.md"
    if not prompt.exists():
        return []
    return re.findall(r"Card `([^`]+)`", prompt.read_text(encoding="utf-8", errors="ignore"))


def _contract_checks(
    *,
    tasks: list[str],
    task_dirs: dict[str, Path],
    contract_root: Path,
    score_root: Path,
    contract_check_root: Path,
    model_slug: str,
    generated_root: Path,
    card_limit: int,
) -> dict:
    rows: list[dict] = []
    for task_id in tasks:
        report = run_contracts(contract_root / task_id / "contracts.json", score_root / task_id / "tran.csv")
        task_out = contract_check_root / task_id
        task_out.mkdir(parents=True, exist_ok=True)
        _json_write(task_out / "contract_report.json", report)
        meta = read_meta(task_dirs[task_id])
        selected_cards = select_contract_repair_cards(
            report,
            task_id=task_id,
            category=meta.get("category", ""),
            limit=card_limit,
        )
        rows.append(
            {
                "task_id": task_id,
                "contract_status": report.get("status"),
                "advisory_status": report.get("advisory_status"),
                "failed_hard_contracts": report.get("failed_hard_contracts", []),
                "failed_advisory_contracts": report.get("failed_advisory_contracts", []),
                "selected_card_ids_from_final_contracts": [card["id"] for card in selected_cards],
                "prompt_card_ids": _prompt_card_ids(generated_root, model_slug, task_id),
            }
        )
    payload = {
        "total_tasks": len(rows),
        "pass_count": sum(1 for row in rows if row["contract_status"] == "PASS"),
        "advisory_warn_count": sum(1 for row in rows if row.get("advisory_status") == "WARN_CONTRACT"),
        "tasks": rows,
    }
    _json_write(contract_check_root / "summary.json", payload)
    return payload


def _load_model_summary(score_root: Path) -> dict:
    path = score_root / "model_results.json"
    return _json_read(path) if path.exists() else {}


def _write_report(
    *,
    report_path: Path,
    args: argparse.Namespace,
    tasks: list[str],
    generated_root: Path,
    output_root: Path,
    score_root: Path,
    contract_check_root: Path,
    baseline_root: Path,
    compare_root: Path,
    contract_summary: dict,
) -> None:
    model_summary = _load_model_summary(score_root)
    contract_rows = {row["task_id"]: row for row in contract_summary.get("tasks", [])}
    lines = [
        f"# Contract Card Ablation Report: {args.tag}",
        "",
        "## Configuration",
        "",
        f"- Model: `{args.model}`",
        f"- Tasks: `{len(tasks)}`",
        f"- Contract root: `{args.contract_root}`",
        f"- Repair cards enabled: `{not args.no_cards}`",
        f"- Relaxed card selector: `{args.relaxed_card_selector}`",
        f"- Card limit: `{args.card_limit}`",
        f"- Repair wall timeout: `{args.repair_wall_timeout_s}`",
        f"- Generated root: `{generated_root}`",
        f"- Adaptive output root: `{output_root}`",
        f"- Score root: `{score_root}`",
        f"- Contract check root: `{contract_check_root}`",
        "",
        "## Score Summary",
        "",
        f"- Pass@1: `{model_summary.get('pass_at_1', 'NA')}`",
        f"- Pass count: `{model_summary.get('pass_count', 'NA')}/{model_summary.get('total_tasks', len(tasks))}`",
        f"- Contract PASS: `{contract_summary.get('pass_count', 'NA')}/{contract_summary.get('total_tasks', len(tasks))}`",
        "",
        "## Comparison",
        "",
        "| Task | Baseline | Compare root | This run | Weighted | Prompt cards | Final hard failures |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for task_id in tasks:
        baseline = _result(baseline_root, task_id)
        compare = _result(compare_root, task_id)
        current = _result(score_root, task_id)
        row = contract_rows.get(task_id, {})
        cards = ", ".join(f"`{card}`" for card in row.get("prompt_card_ids", []))
        hard = ", ".join(f"`{name}`" for name in row.get("failed_hard_contracts", []))
        lines.append(
            f"| `{task_id}` | {baseline.get('status')} | {compare.get('status')} | "
            f"{current.get('status')} | {_weighted(current)} | {cards} | {hard} |"
        )

    lines.extend([
        "",
        "## Commands",
        "",
        "Adaptive repair and scoring commands are printed by the runner during execution. Re-run with `--dry-run` to reproduce them without API calls.",
        "",
    ])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _guard_paths(paths: list[Path], *, overwrite: bool) -> None:
    if overwrite:
        return
    existing = [path for path in paths if path.exists()]
    if existing:
        raise SystemExit(
            "Refusing to overwrite existing paths without --overwrite:\n"
            + "\n".join(f"- {path}" for path in existing)
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="Experiment tag used for default output roots.")
    parser.add_argument("--model", default="kimi-k2.5")
    parser.add_argument("--task", action="append", default=[], help="Task id. Repeat for multiple tasks.")
    parser.add_argument("--tasks", nargs="+", default=[], help="Task ids as a space-separated list.")
    parser.add_argument("--contract-root", default=DEFAULT_CONTRACT_ROOT)
    parser.add_argument("--source-generated-dir", default=DEFAULT_SOURCE_GENERATED)
    parser.add_argument("--initial-result-root", default=DEFAULT_INITIAL_RESULT)
    parser.add_argument("--compare-result-root", default=DEFAULT_COMPARE_RESULT)
    parser.add_argument("--generated-root", default="")
    parser.add_argument("--output-root", default="")
    parser.add_argument("--score-root", default="")
    parser.add_argument("--contract-check-root", default="")
    parser.add_argument("--report-out", default="")
    parser.add_argument("--max-rounds", type=int, default=1)
    parser.add_argument("--patience", type=int, default=1)
    parser.add_argument("--timeout-s", type=int, default=90)
    parser.add_argument(
        "--repair-wall-timeout-s",
        type=int,
        default=1800,
        help="Outer wall-clock timeout for adaptive repair. Use 0 to disable.",
    )
    parser.add_argument("--quick-maxstep", default="1n")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--sample-idx", type=int, default=0)
    parser.add_argument("--card-limit", type=int, default=2)
    parser.add_argument("--cards-path", default="")
    parser.add_argument("--no-cards", action="store_true", help="Disable repair-card env flag for a contracts-only ablation.")
    parser.add_argument(
        "--relaxed-card-selector",
        action="store_true",
        help="Allow semantic/prompt-template evidence to select repair cards when functional claims or CSV contracts are incomplete.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report-only", action="store_true", help="Skip repair and score; only run contract checks and write report.")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting generated result roots created by this runner.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tasks = args.task + args.tasks or DEFAULT_TASKS
    task_dirs = _task_dirs(tasks)
    model_slug = _model_slug(args.model)

    generated_root = Path(args.generated_root or f"generated-adaptive-contract-cards-{args.tag}")
    output_root = Path(args.output_root or f"results/adaptive-contract-cards-{args.tag}")
    score_root = Path(args.score_root or f"results/adaptive-contract-cards-{args.tag}-final-score")
    contract_check_root = Path(args.contract_check_root or f"results/adaptive-contract-cards-{args.tag}-final-contract-check-v7")
    report_path = Path(args.report_out or f"results/CONTRACT_CARD_ABLATION_{args.tag}.md")
    contract_root = Path(args.contract_root)
    baseline_root = Path(args.initial_result_root)
    compare_root = Path(args.compare_result_root)

    if not args.report_only:
        _guard_paths([generated_root, output_root, score_root, contract_check_root, report_path], overwrite=args.overwrite)
    elif not score_root.exists():
        raise SystemExit(f"--report-only requires existing score root: {score_root}")

    env_delta = {
        "VAEVAS_CONTRACT_ROOT": str(contract_root),
        "VAEVAS_REPAIR_CARD_LIMIT": str(args.card_limit),
    }
    if args.cards_path:
        env_delta["VAEVAS_REPAIR_CARDS_PATH"] = args.cards_path
    if not args.no_cards:
        env_delta["VAEVAS_ENABLE_REPAIR_CARDS"] = "1"
    if args.relaxed_card_selector:
        env_delta["VAEVAS_RELAXED_CARD_SELECTOR"] = "1"

    adaptive_cmd = [
        sys.executable,
        "runners/run_adaptive_repair.py",
        "--model",
        args.model,
    ]
    for task_id in tasks:
        adaptive_cmd.extend(["--task", task_id])
    adaptive_cmd.extend(
        [
            "--source-generated-dir",
            args.source_generated_dir,
            "--initial-result-root",
            args.initial_result_root,
            "--generated-root",
            str(generated_root),
            "--output-root",
            str(output_root),
            "--max-rounds",
            str(args.max_rounds),
            "--patience",
            str(args.patience),
            "--timeout-s",
            str(args.timeout_s),
            "--quick-maxstep",
            args.quick_maxstep,
            "--sample-idx",
            str(args.sample_idx),
            "--layered-only-repair",
        ]
    )

    score_cmd = [
        sys.executable,
        "runners/score.py",
        "--model",
        args.model,
        "--generated-dir",
        str(generated_root),
        "--output-dir",
        str(score_root),
    ]
    for task_id in tasks:
        score_cmd.extend(["--task", task_id])
    score_cmd.extend(["--timeout-s", str(args.timeout_s), "--workers", str(args.workers)])

    if not args.report_only:
        _run(
            adaptive_cmd,
            env_delta=env_delta,
            dry_run=args.dry_run,
            wall_timeout_s=args.repair_wall_timeout_s,
        )
        _run(score_cmd, dry_run=args.dry_run)
    else:
        print("[ablation] report-only mode: skipping adaptive repair and independent score")

    if args.dry_run:
        print(f"[ablation] would write contract check root: {contract_check_root}")
        print(f"[ablation] would write report: {report_path}")
        return 0

    contract_summary = _contract_checks(
        tasks=tasks,
        task_dirs=task_dirs,
        contract_root=contract_root,
        score_root=score_root,
        contract_check_root=contract_check_root,
        model_slug=model_slug,
        generated_root=generated_root,
        card_limit=args.card_limit,
    )
    _write_report(
        report_path=report_path,
        args=args,
        tasks=tasks,
        generated_root=generated_root,
        output_root=output_root,
        score_root=score_root,
        contract_check_root=contract_check_root,
        baseline_root=baseline_root,
        compare_root=compare_root,
        contract_summary=contract_summary,
    )
    print(f"[ablation] report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
