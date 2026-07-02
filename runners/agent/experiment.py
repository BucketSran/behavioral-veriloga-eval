"""Batch A/B experiment runner — absorbs ``run_model_assisted_loop``'s
orchestration (the ~1400 lines of per-mode boilerplate collapse to one loop).

Runs the agent across multiple config presets (mode × include_skill ×
max_rounds × layered_repair) over a set of tasks, isolating each preset's
output and producing a comparison summary.

The 8 legacy modes map to presets like:
    skill-only                → {prompt_mode: skill-only}
    raw-generic-retry         → {prompt_mode: generic-retry}
    evas-assisted             → {prompt_mode: evas-assisted, include_skill: false}
    skill-evas-informed       → {prompt_mode: skill-evas-informed}
    evas-guided-repair        → {prompt_mode: guided-repair, include_skill: true, max_rounds: 8}
    evas-guided-repair-no-skill → {prompt_mode: guided-repair, include_skill: false, max_rounds: 8}
    evas-guided-repair-3round → {prompt_mode: guided-repair, include_skill: false, max_rounds: 3}
    evas-guided-repair-3round-skill → {prompt_mode: guided-repair, include_skill: true, max_rounds: 3}
"""
from __future__ import annotations

import copy
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from .agent import Agent
from .config import AgentConfig


# ─── Named presets (the 8 legacy modes) ───────────────────────

PRESETS: dict[str, dict] = {
    "skill-only":                  {"prompt_mode": "skill-only"},
    "raw-generic-retry":           {"prompt_mode": "generic-retry"},
    "evas-assisted":               {"prompt_mode": "evas-assisted", "include_skill": False},
    "skill-evas-informed":         {"prompt_mode": "skill-evas-informed"},
    "evas-guided-repair":          {"prompt_mode": "guided-repair", "include_skill": True,  "max_rounds": 8},
    "evas-guided-repair-no-skill": {"prompt_mode": "guided-repair", "include_skill": False, "max_rounds": 8},
    "evas-guided-repair-3round":   {"prompt_mode": "guided-repair", "include_skill": False, "max_rounds": 3},
    "evas-guided-repair-3round-skill": {"prompt_mode": "guided-repair", "include_skill": True, "max_rounds": 3},
}


@dataclass
class ExperimentResult:
    preset_name: str
    task_id: str
    passed: bool
    rounds: int
    final_status: str
    final_scores: dict = field(default_factory=dict)


def run_experiment(
    base_config: AgentConfig,
    preset_names: list[str],
    tasks: list[tuple[str, Path]],
    *,
    output_root: Path,
    workers: int = 1,
    force: bool = False,
) -> dict:
    """Run every preset × task combination and produce a comparison summary.

    Args:
        base_config: Starting config; each preset overrides loop fields.
        preset_names: Keys into PRESETS (or "all").
        tasks: List of (task_id, task_dir).
        output_root: Where to write per-preset outputs.
        workers: Parallel workers (ThreadPoolExecutor).
        force: Re-run even if final_result.json exists.

    Returns a summary dict with per-preset pass rates, suitable for
    serialization to <output_root>/experiment_summary.json.
    """
    if preset_names == ["all"]:
        preset_names = list(PRESETS.keys())

    results: list[ExperimentResult] = []

    def _run_one(preset_name: str, task_id: str, task_dir: Path) -> ExperimentResult:
        cfg = copy.deepcopy(base_config)
        override = PRESETS[preset_name]
        for k, v in override.items():
            setattr(cfg.loop, k, v)
        # Isolate output per preset.
        cfg.output.dir = str(output_root / preset_name)
        # Disable the run-time doctor (we check once at the start).
        agent = Agent(cfg)
        history = agent.run(task_id, task_dir)
        last = history[-1] if history else None
        return ExperimentResult(
            preset_name=preset_name,
            task_id=task_id,
            passed=bool(last and last.status == "PASS"),
            rounds=len(history),
            final_status=last.status if last else "NO_HISTORY",
            final_scores=last.scores if last else {},
        )

    if workers > 1 and len(preset_names) * len(tasks) > 1:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(_run_one, pn, tid, td): (pn, tid)
                for pn in preset_names for (tid, td) in tasks
            }
            for fut in as_completed(futures):
                try:
                    results.append(fut.result())
                except Exception as e:
                    pn, tid = futures[fut]
                    results.append(ExperimentResult(pn, tid, False, 0, f"ERROR: {e}"))
    else:
        for pn in preset_names:
            for (tid, td) in tasks:
                results.append(_run_one(pn, tid, td))

    summary = _build_summary(results, preset_names)
    (output_root / "experiment_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


def _build_summary(results: list[ExperimentResult], preset_names: list[str]) -> dict:
    by_preset: dict[str, list[ExperimentResult]] = {p: [] for p in preset_names}
    for r in results:
        by_preset.setdefault(r.preset_name, []).append(r)

    summary = {"presets": {}}
    for name, rs in by_preset.items():
        total = len(rs)
        passed = sum(1 for r in rs if r.passed)
        summary["presets"][name] = {
            "total_tasks": total,
            "passed": passed,
            "pass_rate": round(passed / total, 4) if total else 0.0,
            "avg_rounds": round(sum(r.rounds for r in rs) / total, 2) if total else 0,
            "per_task": [
                {"task_id": r.task_id, "passed": r.passed, "rounds": r.rounds,
                 "status": r.final_status}
                for r in rs
            ],
        }
    return summary
