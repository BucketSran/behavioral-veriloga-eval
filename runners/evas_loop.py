#!/usr/bin/env python3
"""evas_loop.py — compatibility shim that delegates to ``runners/agent/``.

This file preserves the original ``python runners/evas_loop.py`` CLI and its
output layout. The actual loop now runs through the unified agent
(``runners/agent/``), which absorbs evas_loop's parallel batch execution,
resume-from-disk, and per-round JSON results.

Behavioral compatibility:
  - Same CLI flags as the original (--model, --max-rounds, --task, --workers,
    --gen-root, --results-root, --temperature, --top-p, --max-tokens,
    --timeout-s, --dry-run, --force, --skill-bundle, --bailian-api-key).
  - Same output files:
      <gen-root>/<model_slug>/<task_id>/round_<N>/sample_0/*.va,*.scs
      <results-root>/<task_id>/round_<N>_result.json
      <results-root>/<task_id>/final_result.json
      <results-root>/loop_summary.json   (same schema as build_loop_summary)
  - The 24-task default subset (LOOP_TASKS_24) is honored when --task is omitted.
  - Sequential vs parallel (--workers>1) is honored.

What is delegated to the agent:
  - LLM calls (4 provider modes + retry, instead of the old 3-provider inline)
  - EVAS scoring (score.score_one_task, same as before)
  - R1+ repair prompts (runners/build_repair_prompt.build_evas_guided_repair_prompt)

For new work prefer ``python -m runners.agent run`` / ``experiment`` directly.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

warnings.warn(
    "runners/evas_loop.py is a compatibility shim around runners/agent/. "
    "For new work use 'python -m runners.agent run' / 'experiment'.",
    DeprecationWarning,
    stacklevel=2,
)

# Make runners/ importable (flat style) so 'from agent...' and 'from score...'
# both resolve. This file lives in runners/.
_RUNNERS = Path(__file__).resolve().parent
_ROOT = _RUNNERS.parent
if str(_RUNNERS) not in sys.path:
    sys.path.insert(0, str(_RUNNERS))

from agent import agent as _agent_mod      # noqa: E402
from agent import config as _config_mod    # noqa: E402
import generate as _gen                     # noqa: E402  (for detect_provider / bailian key)


# ---------------------------------------------------------------------------
# The 24-task subset — kept verbatim from the original for default selection.
# ---------------------------------------------------------------------------

LOOP_TASKS_24: list[str] = [
    # digital-logic (4)
    "digital_basics_smoke",
    "gray_counter_4b_smoke",
    "gray_counter_one_bit_change_smoke",
    "serializer_frame_alignment_smoke",
    # stimulus (3)
    "clk_burst_gen_smoke",
    "timer_absolute_grid_smoke",
    "bound_step_period_guard_smoke",
    # data-converter (4)
    "flash_adc_3b_smoke",
    "dac_binary_clk_4b_smoke",
    "adc_dac_ideal_4b_smoke",
    "dwa_wraparound_smoke",
    # comparator (4)
    "cross_hysteresis_window_smoke",
    "cmp_delay_smoke",
    "comparator_hysteresis_smoke",
    "cmp_strongarm_smoke",
    # phase-detector (3)
    "xor_pd_smoke",
    "pfd_updn_smoke",
    "bbpd_data_edge_alignment_smoke",
    # pll-closed-loop (2)
    "cppll_freq_step_reacquire_smoke",
    "adpll_ratio_hop_smoke",
    # sample-hold (2)
    "sample_hold_smoke",
    "sample_hold_droop_smoke",
    # pll (1)
    "multimod_divider_ratio_switch_smoke",
    # calibration (1)
    "dwa_ptr_gen_smoke",
]

# Where v1 end-to-end tasks live (used to resolve task IDs → task dirs).
TASK_ROOT = _ROOT / "tasks" / "end-to-end" / "voltage"


# ---------------------------------------------------------------------------
# Provider bridging: map the old model-name → provider detection onto the
# agent's 4-mode LLMConfig.
# ---------------------------------------------------------------------------

def _provider_for_model(model: str, bailian_key: str = "") -> tuple[str, str]:
    """Return (agent provider, api_key_env) for a legacy model name."""
    try:
        legacy = _gen.detect_provider(model)
    except ValueError:
        legacy = "anthropic"
    if legacy == "bailian":
        # DashScope/Bailian speaks the Anthropic Messages API at a fixed base_url.
        if bailian_key:
            os.environ["BAILIAN_API_KEY"] = bailian_key
        return ("anthropic-compatible", "BAILIAN_API_KEY")
    if legacy == "openai":
        return ("openai", "OPENAI_API_KEY")
    return ("anthropic", "ANTHROPIC_API_KEY")


# ---------------------------------------------------------------------------
# Task discovery — tries the legacy v1 path first, then falls back to the
# broader v1+v3 scan used by the agent CLI.
# ---------------------------------------------------------------------------

def _resolve_task_dir(task_id: str) -> Path | None:
    """Locate a task directory by ID across v1 (meta.json) and v3 (task.toml + release).

    Order:
      1. Legacy exact path: tasks/end-to-end/voltage/<task_id>/
      2. v3 release exact path: benchmark-vabench-release-v3/tasks/<task_id>/
         (handles the common "NNN-slug" naming where the dir name IS the task id)
      3. Broad recursive scan via the agent CLI (meta.json + task.toml).
    """
    legacy = TASK_ROOT / task_id
    if legacy.is_dir() and ((legacy / "gold").is_dir()
                            or (legacy / "meta.json").exists()):
        return legacy
    # v3 release: dir name matches task_id exactly (e.g. "001-bang-bang-phase-detector").
    v3_release = _ROOT / "benchmark-vabench-release-v3" / "tasks" / task_id
    if v3_release.is_dir() and ((v3_release / "solution").is_dir()
                                or (v3_release / "instruction.md").exists()):
        return v3_release
    # Broad scan (delegates to agent CLI's discovery helpers).
    try:
        from agent.cli import _find_task_dir
        config = _config_mod.load_config()
        found = _find_task_dir(task_id, None, config)
        if found is not None:
            return found
    except Exception:
        pass
    return None





# ---------------------------------------------------------------------------
# Per-task execution: build a one-shot AgentConfig, run, and return a
# final_result dict shaped like the original run_task_loop output.
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
    """Run the agent loop for one task; return a legacy-shaped final_result dict."""
    # Dry-run short-circuits before any task-dir lookup — its whole point is to
    # not require a real task or any API call.
    if dry_run:
        return _dry_run_task(task_id, model_slug, gen_root, results_root, max_rounds)

    task_dir = _resolve_task_dir(task_id)
    if task_dir is None:
        return {"task_id": task_id, "status": "FAIL_INFRA",
                "error": "task_dir_not_found", "passed_round": None,
                "total_rounds": 0, "scores": {}, "evas_notes": []}

    provider, key_env = _provider_for_model(model)
    config = _config_mod.load_config()
    config.llm.provider = provider
    config.llm.model = model
    config.llm.temperature = temperature
    config.llm.repair_temperature = temperature
    config.llm.top_p = top_p
    config.llm.max_tokens = max_tokens
    config.llm.timeout = timeout_s
    if key_env:
        config.llm.api_key_env = key_env
    config.loop.max_rounds = max_rounds
    config.loop.prompt_mode = "guided-repair"
    config.loop.include_skill = True
    config.loop.layered_repair = False
    # Honor --skill-bundle: if a bundle text was provided, write it to a temp
    # file under gen_root and point the agent's bundle_override_path at it.
    if skill_bundle_text and skill_bundle_text.strip():
        bundle_dir = gen_root / "_skill_bundles"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        bundle_file = bundle_dir / f"{task_id}_bundle.md"
        bundle_file.write_text(skill_bundle_text, encoding="utf-8")
        config.skills.bundle_override_path = str(bundle_file)

    # The agent writes to <output.dir>/<model_slug>/<task_id>/... and
    # <output.dir>/<task_id>/round_N_result.json. Point output.dir at gen_root so
    # the <model_slug>/<task_id>/ tree lands under gen_root.
    config.output.dir = str(gen_root)

    # Re-run the agent, writing results under results_root/<task_id>/.
    # The agent's LoopController writes round_N_result.json + final_result.json
    # under <output.dir>/<task_id>/. We override by post-moving.
    agent = _agent_mod.Agent(config)
    if force:
        task_results = Path(config.output.dir) / task_id
        if task_results.exists():
            import shutil
            shutil.rmtree(task_results)

    # Suppress the agent's rich header prints during shim use; the shim prints
    # its own progress lines to match the original output style.
    try:
        history = agent.run(task_id, task_dir)
    except Exception as e:
        return {"task_id": task_id, "status": "FAIL_INFRA",
                "error": str(e)[:400], "passed_round": None,
                "total_rounds": 0, "scores": {}, "evas_notes": []}

    # Move/ensure the per-task result dir matches the legacy layout
    # (<results_root>/<task_id>/...). The agent wrote to <gen_root>/<task_id>/.
    src_results = gen_root / task_id
    dst_results = results_root / task_id
    dst_results.mkdir(parents=True, exist_ok=True)
    for fname in ("final_result.json",):
        s = src_results / fname
        d = dst_results / fname
        if s.exists():
            d.write_text(s.read_text(encoding="utf-8"), encoding="utf-8")
    # Copy every round_N_result.json across.
    for rp in sorted(src_results.glob("round_*_result.json")):
        (dst_results / rp.name).write_text(rp.read_text(encoding="utf-8"), encoding="utf-8")

    # Load the final_result.json the agent wrote and reshape to legacy schema.
    final_path = dst_results / "final_result.json"
    if final_path.exists():
        final = json.loads(final_path.read_text(encoding="utf-8"))
    else:
        last = history[-1] if history else None
        final = {
            "task_id": task_id,
            "status": last.status if last else "FAIL_INFRA",
            "scores": last.scores if last else {},
            "evas_notes": last.evas_notes if last else [],
            "passed_round": None,
            "total_rounds_run": len(history),
            "max_rounds": max_rounds,
        }
    final.setdefault("task_id", task_id)
    final.setdefault("max_rounds", max_rounds)
    # total_rounds_run: original counted rounds as 1-indexed.
    if "total_rounds_run" not in final:
        final["total_rounds_run"] = len(history)
    return final


def _dry_run_task(task_id: str, model_slug: str, gen_root: Path,
                  results_root: Path, max_rounds: int) -> dict:
    """Write placeholder .va/.scs files without calling any API (legacy --dry-run)."""
    sample_dir = gen_root / model_slug / task_id / "round_0" / "sample_0"
    sample_dir.mkdir(parents=True, exist_ok=True)
    placeholder_va = (
        '`include "constants.vams"\n`include "disciplines.vams"\n\n'
        f"// DRY-RUN placeholder for {task_id}\n"
        f"module {task_id}_dryrn(out);\n"
        "    output electrical out;\n"
        "    analog V(out) <+ 0.0;\n"
        "endmodule\n"
    )
    placeholder_scs = (
        "simulator lang=spectre\nglobal 0\n"
        f"I1 (0 out) {task_id}_dryrn\n"
        "tran tran stop=10n\n"
        f'ahdl_include "./{task_id}_dryrn.va"\n'
    )
    (sample_dir / f"{task_id}_dryrn.va").write_text(placeholder_va)
    (sample_dir / f"tb_{task_id}_dryrn.scs").write_text(placeholder_scs)
    final = {
        "task_id": task_id, "status": "dry_run", "scores": {},
        "evas_notes": ["dry_run placeholder"], "passed_round": None,
        "total_rounds_run": 1, "max_rounds": max_rounds,
    }
    task_results = results_root / task_id
    task_results.mkdir(parents=True, exist_ok=True)
    (task_results / "final_result.json").write_text(
        json.dumps(final, indent=2), encoding="utf-8")
    return final


# ---------------------------------------------------------------------------
# Aggregate summary — verbatim schema from the original build_loop_summary.
# ---------------------------------------------------------------------------

def build_loop_summary(model_slug: str, task_results: list[dict],
                       temperature: float, top_p: float) -> dict:
    total = len(task_results)
    if total == 0:
        return {"model": model_slug, "total": 0, "pass_rate": 0.0}
    n_pass = sum(1 for r in task_results if r.get("passed_round") is not None)
    pass_rounds = [r["passed_round"] for r in task_results
                   if r.get("passed_round") is not None]
    avg_rounds_to_pass = (round(sum(pass_rounds) / len(pass_rounds), 2)
                          if pass_rounds else None)
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
# Convenience re-exports for any code importing the original module's helpers.
# ---------------------------------------------------------------------------

def generate_round(*args, **kwargs):  # pragma: no cover - thin wrapper
    """Deprecated; generation is now internal to the agent loop."""
    raise NotImplementedError(
        "generate_round is no longer public — generation runs inside the agent. "
        "Use runners.agent.Agent.run() or the evas_loop CLI."
    )


def score_for_loop(*args, **kwargs):  # pragma: no cover - thin wrapper
    """Deprecated; scoring is now internal to the agent loop."""
    raise NotImplementedError(
        "score_for_loop is no longer public — scoring runs inside the agent."
    )


# ---------------------------------------------------------------------------
# Main — CLI surface identical to the original.
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="EVAs closed-loop VA generation pipeline (delegates to runners/agent)."
    )
    ap.add_argument("--model", required=True,
                    help="Model name, e.g. qwen3-max-2026-01-23 or kimi-k2.5")
    ap.add_argument("--max-rounds", type=int, default=8)
    ap.add_argument("--task", nargs="*", default=[],
                    help="Run only these task_ids. Default: all 24.")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--gen-root", default="generated-loop")
    ap.add_argument("--results-root", default="")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--timeout-s", type=int, default=180)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--skill-bundle", default="",
                    help="Path to Verilog-A skill bundle markdown. Default: "
                         "docs/TABLE2_VERILOGA_SKILL_BUNDLE.md")
    ap.add_argument("--bailian-api-key", default="")
    args = ap.parse_args()

    model_slug = args.model.replace("/", "_")

    # Load skill bundle (honored — injected via config.skills.bundle_override_path).
    skill_bundle_text = ""
    if args.skill_bundle:
        sb_path = Path(args.skill_bundle)
        if not sb_path.is_absolute():
            sb_path = _ROOT / sb_path
        if sb_path.exists():
            skill_bundle_text = sb_path.read_text(encoding="utf-8")
            print(f"[evas_loop] skill bundle: {sb_path.name} "
                  f"({len(skill_bundle_text)} chars)")
        else:
            print(f"[evas_loop] WARNING: skill bundle not found at {sb_path}")

    # Validate API key (same contract as the original).
    if not args.dry_run:
        provider, key_env = _provider_for_model(args.model, args.bailian_api_key)
        if key_env and not os.environ.get(key_env):
            print(f"[evas_loop] ERROR: {key_env} not set.")
            return 1

    gen_root = Path(args.gen_root)
    if not gen_root.is_absolute():
        gen_root = _ROOT / gen_root
    gen_root.mkdir(parents=True, exist_ok=True)

    results_root = (Path(args.results_root) if args.results_root
                    else _ROOT / "results" / f"evas-loop-{model_slug}")
    if not results_root.is_absolute():
        results_root = _ROOT / results_root
    results_root.mkdir(parents=True, exist_ok=True)

    # Task selection — same logic as original.
    selected = set(args.task) if args.task else set(LOOP_TASKS_24)
    task_ids = [t for t in LOOP_TASKS_24 if t in selected]
    if args.task:
        for t in args.task:
            if t not in task_ids:
                task_ids.append(t)

    print(f"[evas_loop] model={args.model}  tasks={len(task_ids)}"
          f"  max_rounds={args.max_rounds}  temp={args.temperature}"
          f"  workers={args.workers}  force={args.force}  dry_run={args.dry_run}")
    print("[evas_loop] (delegating to runners/agent/)")

    def run_single_task(task_id: str) -> tuple[str, dict]:
        result = run_task_loop(
            task_id, model=args.model, model_slug=model_slug,
            gen_root=gen_root, results_root=results_root,
            max_rounds=args.max_rounds, temperature=args.temperature,
            top_p=args.top_p, max_tokens=args.max_tokens,
            dry_run=args.dry_run, timeout_s=args.timeout_s,
            skill_bundle_text=skill_bundle_text, force=args.force,
        )
        return task_id, result

    all_results: list[dict] = []
    if args.workers > 1 and len(task_ids) > 1:
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
        for task_id in task_ids:
            print(f"  [{task_id}]")
            _, final = run_single_task(task_id)
            passed = final.get("passed_round")
            status_line = (f"PASS at round {passed}" if passed is not None
                           else f"FAIL after {final.get('total_rounds_run', '?')} rounds")
            print(f"  → {status_line}")
            all_results.append(final)

    summary = build_loop_summary(model_slug, all_results,
                                 args.temperature, args.top_p)
    (results_root / "loop_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

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
