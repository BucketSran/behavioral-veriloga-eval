"""Prompt-mode dispatcher — maps config ``loop.prompt_mode`` to the right
``build_repair_prompt.py`` builder function.

This absorbs the 8 modes of the legacy ``run_model_assisted_loop.py`` into a
single knob. The 8 modes were always just combinations of 3 variables:

    prompt_mode × include_skill × max_rounds (+ optional layered_repair)

mode → builder mapping:
    guided-repair       → build_evas_guided_repair_prompt  (default)
    generic-retry       → build_generic_retry_prompt       (no EVAS feedback)
    evas-assisted       → build_evas_assisted_prompt
    skill-only          → build_skill_only_prompt           (R0 only, no repair loop)
    skill-evas-informed → build_evas_assisted_prompt + skill bundle

For modes that are "single-shot" (generic-retry, skill-only), the loop runs
exactly 1 round and skips the R1+ repair path entirely.
"""
from __future__ import annotations

from pathlib import Path


SINGLE_SHOT_MODES = {"generic-retry", "skill-only"}
"""Modes that run exactly 1 round (no R1+ repair loop)."""


def build_round0_prompt(
    mode: str,
    task_dir: Path,
    *,
    skill_bundle_text: str = "",
    include_skill: bool = True,
) -> str:
    """Build the Round 0 generation prompt for the given mode.

    For closed-loop modes (guided-repair, evas-assisted, skill-evas-informed),
    Round 0 still uses ``build_skill_only_prompt`` because there is no EVAS
    feedback yet. For generic-retry, Round 0 uses build_generic_retry_prompt.
    """
    # Import lazily so this module is importable even if build_repair_prompt
    # has heavy top-level imports the caller doesn't need.
    from build_repair_prompt import (
        build_skill_only_prompt,
        build_generic_retry_prompt,
    )

    if mode == "generic-retry":
        return build_generic_retry_prompt(task_dir, task_dir)  # baseline_dir ~ task_dir
    # All other modes use skill-only for Round 0.
    bundle = skill_bundle_text if include_skill else ""
    return build_skill_only_prompt(task_dir, skill_bundle_text=bundle)


def build_repair_prompt_for_mode(
    mode: str,
    task_dir: Path,
    sample_dir: Path,
    evas_result: dict,
    *,
    history: list[dict] | None = None,
    include_skill: bool = True,
    skill_bundle_text: str = "",
    loop_context: dict | None = None,
) -> str:
    """Build the R1+ repair prompt for the given mode.

    For single-shot modes this is never called (the loop stops after R0).
    """
    from build_repair_prompt import (
        build_evas_guided_repair_prompt,
        build_evas_assisted_prompt,
    )

    if mode in ("guided-repair",):
        return build_evas_guided_repair_prompt(
            task_dir, sample_dir, evas_result,
            history=history, include_skill=include_skill,
            loop_context=loop_context,
        )
    if mode in ("evas-assisted", "skill-evas-informed"):
        bundle = skill_bundle_text if mode == "skill-evas-informed" else None
        return build_evas_assisted_prompt(
            task_dir, sample_dir, evas_result,
            skill_bundle_text=bundle,
        )
    # generic-retry and skill-only are single-shot; no R1+ prompt.
    return ""
