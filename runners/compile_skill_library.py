#!/usr/bin/env python3
"""Compile-skill registry and routing helpers.

The registry makes compile repair capabilities explicit and auditable.  A skill
can provide prompt guidance, judge triggers, and an optional deterministic fixer
action.  The same skill ids can therefore be used in LLM repair prompts and in
post-generation guard passes.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SKILL_ROOT = ROOT / "compile_skills"
REGISTRY_PATH = SKILL_ROOT / "registry.json"


@dataclass(frozen=True)
class CompileSkill:
    id: str
    version: str
    description: str
    triggers: tuple[str, ...]
    guidance_file: str
    fixer: str | None
    judge: str
    safe_autofix: bool

    @property
    def guidance_path(self) -> Path:
        return SKILL_ROOT / self.id / self.guidance_file


def load_compile_skills(registry_path: Path = REGISTRY_PATH) -> list[CompileSkill]:
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    skills: list[CompileSkill] = []
    for item in data.get("skills", []):
        skills.append(
            CompileSkill(
                id=str(item["id"]),
                version=str(item.get("version", "0.1")),
                description=str(item.get("description", "")),
                triggers=tuple(str(trigger).lower() for trigger in item.get("triggers", [])),
                guidance_file=str(item.get("guidance_file", "SKILL.md")),
                fixer=item.get("fixer"),
                judge=str(item.get("judge", "spectre_strict_preflight")),
                safe_autofix=bool(item.get("safe_autofix", False)),
            )
        )
    return skills


def select_compile_skills(notes: list[str] | None, *, registry_path: Path = REGISTRY_PATH) -> list[CompileSkill]:
    joined = " ".join(str(note).lower() for note in notes or [])
    selected: list[CompileSkill] = []
    for skill in load_compile_skills(registry_path):
        if any(trigger in joined for trigger in skill.triggers):
            selected.append(skill)
    return selected


def render_compile_skill_guidance(skill_ids: list[str] | None = None) -> str:
    skills = load_compile_skills()
    wanted = set(skill_ids or [])
    chunks: list[str] = []
    for skill in skills:
        if wanted and skill.id not in wanted:
            continue
        path = skill.guidance_path
        if not path.exists():
            continue
        chunks.append(path.read_text(encoding="utf-8").strip())
    return "\n\n".join(chunk for chunk in chunks if chunk)


def skill_summary(skill: CompileSkill) -> dict[str, object]:
    return {
        "id": skill.id,
        "version": skill.version,
        "description": skill.description,
        "fixer": skill.fixer,
        "judge": skill.judge,
        "safe_autofix": skill.safe_autofix,
    }
