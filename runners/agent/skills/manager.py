"""Skill manager — match task IDs to circuit-category knowledge and inject into prompts.

This replaces the triplicated keyword→file maps in runners/generate.py and
runners/build_repair_prompt.py with a single source of truth.
"""
from __future__ import annotations

from pathlib import Path

from .loader import (
    CATEGORY_FILE_MAP,
    KEYWORD_INDEX,
    list_categories,
    load_category_content,
    resolve_skills_root,
)


class SkillManager:
    """Manages veriloga-skills knowledge injection for Agent tasks."""

    def __init__(self, skills_root: Path | str | None = None, max_chars: int = 3000):
        self.max_chars = max_chars

        if skills_root is None:
            skills_root = resolve_skills_root()
        self.skills_root = Path(skills_root) if skills_root else None

        self.categories_dir: Path | None = None
        self._categories: dict[str, Path] = {}
        self._available = False

        if self.skills_root and self.skills_root.exists():
            cat_dir = self.skills_root / "veriloga" / "references" / "categories"
            if cat_dir.exists():
                self.categories_dir = cat_dir
                self._categories = list_categories(cat_dir)
                self._available = len(self._categories) > 0

    @property
    def available(self) -> bool:
        return self._available

    @property
    def category_count(self) -> int:
        return len(self._categories)

    def match(self, task_id: str) -> Path | None:
        if not self._available:
            return None

        task_lower = task_id.lower()
        for keyword, category in KEYWORD_INDEX.items():
            if keyword in task_lower:
                filename = CATEGORY_FILE_MAP.get(category)
                if filename:
                    file_path = self.categories_dir / filename
                    if file_path.exists():
                        return file_path

        for cat_name, cat_path in self._categories.items():
            if cat_name.replace("-", "_") in task_lower:
                return cat_path

        return None

    def load_for_context(self, file_path: Path | None = None, task_id: str | None = None) -> str:
        if file_path is None and task_id is not None:
            file_path = self.match(task_id)
        if file_path is None or not file_path.exists():
            return ""

        content = load_category_content(file_path, max_chars=self.max_chars)
        if not content:
            return ""

        category_name = file_path.stem.replace("-", " ").title()
        return (
            f"\n\n## Circuit-Specific Knowledge: {category_name}\n\n"
            f"{content}\n"
        )

    def build_skill_context(self, task_id: str) -> str:
        return self.load_for_context(task_id=task_id)

    def list_categories(self) -> list[str]:
        return sorted(self._categories.keys())
