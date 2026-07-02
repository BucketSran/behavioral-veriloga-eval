"""Agent configuration — dataclass + JSON loader.

Merged from vaEvas-Agent. Changes vs the standalone repo:
  - Config format switched from YAML to JSON (stdlib only — avoids adding
    a pyyaml dependency to a repo that previously had none).
  - Added ``loop.prompt_mode``, ``loop.include_skill``, ``loop.layered_repair``
    to express the 8 experimental modes of the legacy ``run_model_assisted_loop``
    as plain config knobs (no separate runner needed).
  - The ``.env`` auto-load at import time is removed (the runners repo does not
    use .env; callers can invoke ``load_env_file`` explicitly if desired).
  - ``load_config`` resolves the package default as ``<package>/config/default.json``.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict, fields, is_dataclass
from pathlib import Path
from typing import Literal


def load_env_file(path: Path | str | None = None) -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ (if key not set).

    Optional utility — the agent no longer calls this at import time.
    """
    if path is None:
        env_var = os.environ.get("VAEVAS_ENV")
        if env_var:
            path = Path(env_var)
        else:
            path = Path(".env")
    if not isinstance(path, Path):
        path = Path(path)
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


# ─── Dataclasses ─────────────────────────────────────────────


@dataclass
class LLMConfig:
    provider: Literal["anthropic", "openai", "anthropic-compatible", "openai-compatible"] = "anthropic"
    model: str = "claude-sonnet-4-6"
    temperature: float = 0.0
    repair_temperature: float = 0.3
    max_tokens: int = 4096
    top_p: float = 1.0
    timeout: int = 120
    base_url: str = ""
    api_key_env: str = ""


@dataclass
class PathsConfig:
    # Relative to project_root (= runners/agent/, so ../.. = repo root).
    veriloga_skills: str = "../../../veriloga-skills"
    behavioral_eval: str = "../.."


@dataclass
class LoopConfig:
    max_rounds: int = 8
    stall_limit: int = 2
    regress_limit: int = 2
    prompt_mode: Literal[
        "guided-repair",
        "generic-retry",
        "evas-assisted",
        "skill-only",
        "skill-evas-informed",
    ] = "guided-repair"
    include_skill: bool = True
    layered_repair: bool = False


@dataclass
class SkillsConfig:
    enabled: bool = True
    max_chars: int = 3000
    categories_dir: str = "../../../veriloga-skills/veriloga/references/categories"
    # Optional override: if set, the contents of this markdown file are injected
    # into the prompt as a skill bundle IN ADDITION to (or instead of) the
    # keyword-matched category reference. Mirrors the legacy evas_loop
    # --skill-bundle flag. Empty string = use keyword matching only.
    bundle_override_path: str = ""


@dataclass
class OutputConfig:
    dir: str = "./output"
    save_artifacts: bool = True
    save_prompts: bool = True


@dataclass
class AgentConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    loop: LoopConfig = field(default_factory=LoopConfig)
    skills: SkillsConfig = field(default_factory=SkillsConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    project_root: Path = field(default_factory=Path.cwd)

    def resolve_path(self, raw: str) -> Path:
        expanded = os.path.expandvars(os.path.expanduser(raw))
        p = Path(expanded)
        if p.is_absolute():
            return p
        return (self.project_root / p).resolve()


_NESTED_TYPES: dict[str, type] = {
    "llm": LLMConfig,
    "paths": PathsConfig,
    "loop": LoopConfig,
    "skills": SkillsConfig,
    "output": OutputConfig,
}


def _dict_to_dataclass(data: dict, klass):
    known = {f.name for f in fields(klass)}
    kwargs = {}
    for k, v in data.items():
        if k not in known:
            continue
        nested_type = _NESTED_TYPES.get(k)
        if isinstance(v, dict) and nested_type is not None:
            kwargs[k] = _dict_to_dataclass(v, nested_type)
        else:
            kwargs[k] = v
    return klass(**kwargs)


def load_config(config_path: Path | str | None = None) -> AgentConfig:
    """Load configuration from JSON file, with sensible defaults.

    Search order for *config_path*:
      1. explicit argument
      2. ``VAEVAS_AGENT_CONFIG`` env var
      3. ``<package>/config/default.json``
      4. bare ``AgentConfig()`` defaults
    """
    if config_path is None:
        env_path = os.environ.get("VAEVAS_AGENT_CONFIG")
        if env_path:
            config_path = Path(env_path)
        else:
            package_default = Path(__file__).resolve().parent / "config" / "default.json"
            if package_default.exists():
                config_path = package_default
            else:
                return AgentConfig()

    config_path = Path(config_path)
    if not config_path.exists():
        return AgentConfig()

    with open(config_path, encoding="utf-8") as f:
        raw = json.load(f) or {}

    config = _dict_to_dataclass(raw, AgentConfig)
    config.project_root = config_path.parent.parent.resolve()
    return config


def save_config(config: AgentConfig, config_path: Path | str) -> None:
    """Save configuration to JSON file."""
    raw = {}
    for f in fields(AgentConfig):
        val = getattr(config, f.name)
        if is_dataclass(val):
            raw[f.name] = asdict(val)
        else:
            raw[f.name] = val
    raw.pop("project_root", None)
    with open(config_path, "w", encoding="utf-8") as fh:
        json.dump(raw, fh, indent=2, ensure_ascii=False)
