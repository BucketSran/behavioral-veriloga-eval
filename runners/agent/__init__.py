"""vaEvas Agent — closed-loop Verilog-A generation pipeline (merged into runners/).

This subpackage provides the unified closed-loop agent for the vaBench benchmark.
It supersedes the standalone vaEvas-Agent repo and the legacy loop runners
(``runners/evas_loop.py``, ``runners/run_adaptive_repair.py``,
``runners/run_model_assisted_loop.py``).

Public entry points:
    - ``python -m runners.agent run <task_id>`` — run the loop on one task
    - ``python -m runners.agent list`` — discover available tasks
    - ``python -m runners.agent doctor`` — environment readiness checks
    - ``python -m runners.agent config`` — show/edit configuration
    - ``python -m runners.agent init`` — interactive first-time setup
    - ``python -m runners.agent experiment`` — batch A/B experiment across modes
"""
from __future__ import annotations

from .agent import Agent
from .config import (
    AgentConfig,
    LLMConfig,
    LoopConfig,
    OutputConfig,
    PathsConfig,
    SkillsConfig,
    load_config,
    save_config,
)

__all__ = [
    "Agent",
    "AgentConfig",
    "LLMConfig",
    "LoopConfig",
    "OutputConfig",
    "PathsConfig",
    "SkillsConfig",
    "load_config",
    "save_config",
]
