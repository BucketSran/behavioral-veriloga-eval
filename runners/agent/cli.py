"""CLI entry point for ``python -m runners.agent``.

Subcommands: run, list, config, doctor, init, experiment.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .agent import Agent
from .config import AgentConfig, load_config, save_config
from .display import dim, green, red, yellow
from .doctor import Doctor, DoctorConfig
from .skills.manager import SkillManager


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="runners.agent",
        description="vaEvas Agent — closed-loop Verilog-A generation pipeline",
    )
    sub = parser.add_subparsers(dest="command")

    # ── run ──
    p_run = sub.add_parser("run", help="Run the closed loop for a task")
    p_run.add_argument("task_id", help="Task ID (e.g., digital_basics_smoke)")
    p_run.add_argument("--task-root", default=None, help="Root directory of tasks")
    p_run.add_argument("--model", default=None, help="LLM model override")
    p_run.add_argument("--provider", choices=["anthropic", "openai",
                         "anthropic-compatible", "openai-compatible"], default=None)
    p_run.add_argument("--base-url", default=None, help="Custom LLM endpoint URL")
    p_run.add_argument("--max-rounds", type=int, default=None)
    p_run.add_argument("--mode", default=None,
                       choices=["guided-repair", "generic-retry", "evas-assisted",
                                "skill-only", "skill-evas-informed"],
                       help="Prompt strategy (default: guided-repair)")
    p_run.add_argument("--layered", action="store_true",
                       help="Enable layered repair policy (run_adaptive_repair-style)")
    p_run.add_argument("--no-skill", action="store_true", help="Disable skill injection")
    p_run.add_argument("--output-dir", default=None)
    p_run.add_argument("--force", action="store_true",
                       help="Ignore existing final_result.json and re-run")
    p_run.add_argument("--skip-doctor", action="store_true", help="Skip environment check")
    p_run.set_defaults(func=cmd_run)

    # ── list ──
    p_list = sub.add_parser("list", help="List available tasks")
    p_list.add_argument("--family", default=None, help="Filter by family")
    p_list.add_argument("--task-root", default=None)
    p_list.set_defaults(func=cmd_list)

    # ── config ──
    p_config = sub.add_parser("config", help="Show or update configuration")
    p_config.add_argument("--set-model", default=None)
    p_config.add_argument("--set-provider", choices=["anthropic", "openai",
                          "anthropic-compatible", "openai-compatible"], default=None)
    p_config.add_argument("--set-base-url", default=None)
    p_config.add_argument("--set-mode", default=None,
                          choices=["guided-repair", "generic-retry", "evas-assisted",
                                   "skill-only", "skill-evas-informed"])
    p_config.add_argument("--layered", dest="layered", action="store_true", default=None)
    p_config.add_argument("--no-layered", dest="layered", action="store_false")
    p_config.add_argument("--show", action="store_true")
    p_config.set_defaults(func=cmd_config)

    # ── doctor ──
    p_doctor = sub.add_parser("doctor", help="Check environment readiness")
    p_doctor.add_argument("--fix", action="store_true")
    p_doctor.set_defaults(func=cmd_doctor)

    # ── init ──
    p_init = sub.add_parser("init", help="Interactive first-time setup")
    p_init.set_defaults(func=cmd_init)

    # ── experiment ──
    p_exp = sub.add_parser("experiment", help="Batch A/B experiment across modes")
    p_exp.add_argument("--presets", default="all",
                       help="Comma-separated preset names, or 'all'")
    p_exp.add_argument("--tasks", required=True,
                       help="Comma-separated task IDs to run")
    p_exp.add_argument("--task-root", default=None)
    p_exp.add_argument("--output-dir", default="./output/experiments")
    p_exp.add_argument("--workers", type=int, default=1)
    p_exp.add_argument("--force", action="store_true")
    p_exp.add_argument("--skip-doctor", action="store_true")
    p_exp.set_defaults(func=cmd_experiment)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    args.func(args)


# ─── Command implementations ─────────────────────────────────

def cmd_run(args) -> None:
    config = load_config()
    if args.model:
        config.llm.model = args.model
    if args.provider:
        config.llm.provider = args.provider
    if args.base_url:
        config.llm.base_url = args.base_url
    if args.max_rounds:
        config.loop.max_rounds = args.max_rounds
    if args.mode:
        config.loop.prompt_mode = args.mode
    if args.layered:
        config.loop.layered_repair = True
    if args.no_skill:
        config.skills.enabled = False
    if args.output_dir:
        config.output.dir = args.output_dir

    if not args.skip_doctor:
        dr = Doctor(_make_doctor_config(config))
        if dr.run(auto_fix=False) != 0:
            print(yellow("\nRun 'python -m runners.agent doctor --fix' to auto-repair, "
                        "or add --skip-doctor to skip.\n"))
            sys.exit(1)

    task_dir = _find_task_dir(args.task_id, args.task_root, config)
    if task_dir is None:
        print(red(f"Task '{args.task_id}' not found. Use 'list' to see available tasks."))
        sys.exit(1)

    agent = Agent(config)
    # The loop controller reads force from its run() kwargs; we set it on the agent
    # via a closure since Agent.run doesn't expose force directly. For simplicity,
    # we pass it through the config project_root (not ideal) — instead, re-invoke
    # the loop with force when needed. Here we just run normally; force is handled
    # by deleting prior results.
    if args.force:
        task_results = config.resolve_path(config.output.dir) / args.task_id
        if task_results.exists():
            import shutil
            shutil.rmtree(task_results)

    history = agent.run(args.task_id, task_dir)
    last = history[-1] if history else None
    sys.exit(0 if (last and last.status == "PASS") else 1)


def cmd_list(args) -> None:
    config = load_config()
    root = _resolve_eval_root(args.task_root, config)
    if root is None or not root.exists():
        print(red("Task root not found. Set behavioral-veriloga-eval path in config."))
        sys.exit(1)
    tasks = _scan_all_tasks(root)
    family_filter = args.family
    by_prefix: dict[str, list[dict]] = {}
    for t in tasks:
        if family_filter and t["family"] != family_filter:
            continue
        prefix = t["prefix"] or "(root)"
        by_prefix.setdefault(prefix, []).append(t)
    for prefix in sorted(by_prefix):
        group = by_prefix[prefix]
        print(f"\n{bold(prefix)}/  ({len(group)} tasks)")
        for t in sorted(group, key=lambda x: x["task_id"]):
            icon = "gold" if t["has_gold"] else ("chk" if t["has_checks"] else "inc")
            line = (f"  {t['task_id']:<40s} {t['family']:<16s} "
                    f"{t['category']:<20s} {t['difficulty']:<8s} {icon}")
            print(dim(line) if sys.stdout.isatty() else line)
    print(f"\nTotal: {len(tasks)} tasks across {len(by_prefix)} directories")


def cmd_config(args) -> None:
    config_path = _default_config_path()
    if args.show or not any([args.set_model, args.set_provider,
                             args.set_base_url, args.set_mode, args.layered is not None]):
        _print_config(load_config(config_path))
        return
    config = load_config(config_path)
    if args.set_model:
        config.llm.model = args.set_model
    if args.set_provider:
        config.llm.provider = args.set_provider
    if args.set_base_url:
        config.llm.base_url = args.set_base_url
    if args.set_mode:
        config.loop.prompt_mode = args.set_mode
    if args.layered is not None:
        config.loop.layered_repair = args.layered
    save_config(config, config_path)
    print(green(f"Config saved to {config_path}"))
    _print_config(config)


def cmd_doctor(args) -> None:
    config = load_config()
    dr = Doctor(_make_doctor_config(config))
    sys.exit(dr.run(auto_fix=args.fix))


def cmd_init(args) -> None:
    print(f"\n{bold('vaEvas Agent — First-Time Setup')}")
    print(dim("─" * 50))
    providers = {
        "1": ("anthropic", "Anthropic (Claude) — api.anthropic.com"),
        "2": ("openai", "OpenAI (GPT/o-series) — api.openai.com"),
        "3": ("anthropic-compatible", "Anthropic-compatible (DeepSeek, self-hosted, proxies)"),
        "4": ("openai-compatible", "OpenAI-compatible (Azure, vLLM, ollama, local)"),
    }
    print(f"\n{bold('Step 1: Choose LLM Provider')}")
    for key, (_, desc) in providers.items():
        print(f"  [{key}] {desc}")
    choice = _prompt("Select [1-4]", default="1", choices=list(providers.keys()))
    provider, _ = providers[choice]
    defaults = {"anthropic": "claude-sonnet-4-6", "openai": "gpt-4o",
                "anthropic-compatible": "deepseek-v4-flash", "openai-compatible": "gpt-4o"}
    print(f"\n{bold('Step 2: Model Name')}")
    print(f"  Press Enter for default: {defaults[provider]}")
    model = _prompt("Model name", default=defaults[provider])
    key_env = "ANTHROPIC_API_KEY" if "anthropic" in provider else "OPENAI_API_KEY"
    print(f"\n{bold('Step 3: API Key')}")
    print(f"  Will be saved to .env as {key_env}")
    api_key = _prompt(f"{key_env} (Enter to skip)", default="", allow_empty=True)
    if api_key:
        _write_env(key_env, api_key)
    base_url = ""
    if "compatible" in provider:
        print(f"\n{bold('Step 4: Base URL')}")
        base_url = _prompt("Base URL", default="", allow_empty=True)
    print(f"\n{bold('Step 5: Write Configuration')}")
    config_path = _default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = load_config(config_path)
    config.llm.provider = provider
    config.llm.model = model
    if base_url:
        config.llm.base_url = base_url
    save_config(config, config_path)
    print(green(f"  Saved: {config_path}"))
    print(f"\n{bold('Step 6: Environment Check')}")
    if api_key:
        os.environ[key_env] = api_key
    if base_url:
        os.environ["ANTHROPIC_BASE_URL"] = base_url
    dr = Doctor(_make_doctor_config(config))
    dr.run(auto_fix=True)
    print(f"\n{green('Try:')} python -m runners.agent list")


def cmd_experiment(args) -> None:
    from .experiment import run_experiment, PRESETS
    config = load_config()
    if not args.skip_doctor:
        dr = Doctor(_make_doctor_config(config))
        if dr.run(auto_fix=False) != 0:
            sys.exit(1)
    presets = args.presets.split(",")
    if "all" in presets:
        presets = list(PRESETS.keys())
    task_ids = [t.strip() for t in args.tasks.split(",") if t.strip()]
    tasks = []
    for tid in task_ids:
        td = _find_task_dir(tid, args.task_root, config)
        if td is None:
            print(red(f"Task '{tid}' not found, skipping."))
            continue
        tasks.append((tid, td))
    if not tasks:
        print(red("No valid tasks."))
        sys.exit(1)
    output_root = config.resolve_path(args.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    summary = run_experiment(
        config, presets, tasks,
        output_root=output_root, workers=args.workers, force=args.force,
    )
    print(f"\n{bold('Experiment summary')}: {output_root / 'experiment_summary.json'}")
    for name, stats in summary["presets"].items():
        print(f"  {name:<32s} pass_rate={stats['pass_rate']:.3f} "
              f"({stats['passed']}/{stats['total_tasks']}) avg_rounds={stats['avg_rounds']}")


# ─── Helpers ─────────────────────────────────────────────────

def _default_config_path() -> Path:
    return Path(__file__).resolve().parent / "config" / "default.json"


def _prompt(text: str, default: str = "", choices: list[str] | None = None,
            allow_empty: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    if choices:
        suffix += f" ({'/'.join(choices)})"
    while True:
        try:
            val = input(f"  {text}{suffix}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); sys.exit(0)
        if not val and default:
            return default
        if not val and allow_empty:
            return ""
        if not val:
            print(red("  Please enter a value")); continue
        if choices and val not in choices:
            print(red(f"  Invalid choice. Options: {', '.join(choices)}")); continue
        return val


def _write_env(key: str, value: str) -> None:
    env_path = Path(".env")
    lines: list[str] = []
    found = False
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines(keepends=True):
            if line.strip().startswith(f"{key}=") or line.strip().startswith(f"# {key}="):
                lines.append(f"{key}={value}\n"); found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"{key}={value}\n")
    env_path.write_text("".join(lines), encoding="utf-8")
    print(green(f"  Saved {key} to .env"))


def _find_task_dir(task_id: str, task_root_override: str | None, config: AgentConfig) -> Path | None:
    root = _resolve_eval_root(task_root_override, config)
    if root is None:
        return None
    for meta_path in sorted(root.rglob("meta.json")):
        task_dir = meta_path.parent
        resolved = _resolve_task_dir(task_dir, root)
        if resolved is None:
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            tid = meta.get("task_id") or meta.get("id") or task_dir.name
        except Exception:
            tid = task_dir.name
        if tid == task_id:
            return resolved
    for toml_path in sorted(root.rglob("task.toml")):
        task_dir = toml_path.parent
        resolved = _resolve_v3_task_dir(task_dir)
        if resolved is None:
            continue
        tid = _read_v3_task_id(toml_path, task_dir.name)
        if tid == task_id:
            return resolved
    return None


def _read_v3_task_id(toml_path: Path, fallback: str) -> str:
    try:
        for line in toml_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line.startswith(("id", "name")) and "=" in line:
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return val
    except (OSError, UnicodeDecodeError):
        pass
    return fallback


def _resolve_v3_task_dir(task_dir: Path) -> Path | None:
    if (task_dir / "solution").is_dir() or (task_dir / "test_harness" / "checks.yaml").exists():
        return task_dir
    return None


def _resolve_task_dir(task_dir: Path, root: Path) -> Path | None:
    if not ((task_dir / "gold").is_dir() or (task_dir / "checks.yaml").exists()):
        return None
    if (task_dir / "prompt.md").exists() and (task_dir / "gold").is_dir():
        return task_dir
    for parent in task_dir.parents:
        if parent == root:
            break
        if (parent / "prompt.md").exists() and (parent / "gold").is_dir():
            return parent
    return task_dir


def _resolve_eval_root(override: str | None, config: AgentConfig) -> Path | None:
    if override:
        p = Path(override).resolve()
        return p if p.exists() else None
    eval_path = config.resolve_path(config.paths.behavioral_eval)
    if eval_path.exists():
        return eval_path
    candidates = [
        Path.cwd() / ".." / "behavioral-veriloga-eval",
        Path.cwd() / "behavioral-veriloga-eval",
        Path(__file__).resolve().parent.parent.parent,  # runners/agent → repo root
    ]
    for c in candidates:
        if c.resolve().exists():
            return c.resolve()
    return None


def _scan_all_tasks(root: Path) -> list[dict]:
    tasks = []
    seen: set[str] = set()
    for meta_path in sorted(root.rglob("meta.json")):
        task_dir = meta_path.parent
        resolved = _resolve_task_dir(task_dir, root)
        if resolved is None:
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        tid = meta.get("task_id") or meta.get("id") or task_dir.name
        if tid in seen:
            continue
        seen.add(tid)
        rel = resolved.relative_to(root)
        prefix = str(rel.parent) if rel.parent != Path(".") else ""
        tasks.append({
            "task_id": tid,
            "family": meta.get("family", "unknown"),
            "category": meta.get("category", "unknown"),
            "difficulty": meta.get("difficulty", "?"),
            "has_gold": (resolved / "gold").is_dir(),
            "has_checks": (resolved / "checks.yaml").exists(),
            "prefix": prefix,
        })
    return tasks


def _make_doctor_config(config: AgentConfig) -> DoctorConfig:
    return DoctorConfig(
        veriloga_skills_path=config.resolve_path(config.paths.veriloga_skills),
        behavioral_eval_path=config.resolve_path(config.paths.behavioral_eval),
        config_path=_default_config_path(),
    )


def _print_config(config: AgentConfig) -> None:
    print(f"\n{bold('LLM Configuration')}")
    print(f"  provider:    {config.llm.provider}")
    print(f"  model:       {config.llm.model}")
    print(f"  temperature: {config.llm.temperature} (repair: {config.llm.repair_temperature})")
    print(f"  base_url:    {config.llm.base_url or '(default)'}")
    print(f"\n{bold('Loop Configuration')}")
    print(f"  max_rounds:     {config.loop.max_rounds}")
    print(f"  prompt_mode:    {config.loop.prompt_mode}")
    print(f"  include_skill:  {config.loop.include_skill}")
    print(f"  layered_repair: {config.loop.layered_repair}")
    print(f"\n{bold('Skills')}")
    print(f"  enabled:    {config.skills.enabled}")
    mgr = SkillManager(skills_root=config.resolve_path(config.paths.veriloga_skills))
    print(f"  available:  {mgr.category_count} categories" if mgr.available else "  available:  no")
    print(f"\n{bold('Paths')}")
    print(f"  skills: {config.resolve_path(config.paths.veriloga_skills)}")
    print(f"  eval:   {config.resolve_path(config.paths.behavioral_eval)}")
    print(f"  output: {config.resolve_path(config.output.dir)}")
    print()


def bold(text: str) -> str:
    return f"\033[1m{text}\033[0m" if sys.stdout.isatty() else text
