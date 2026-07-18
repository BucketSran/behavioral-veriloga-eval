#!/usr/bin/env python3
"""Canonical identity for the checker registry source tree."""
from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path


def tree_hash(paths: Iterable[Path], *, base: Path) -> str:
    """Hash a deterministic set of source files relative to *base*."""
    digest = hashlib.sha256()
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(item for item in path.rglob("*.py") if item.is_file())
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(path)
    for path in sorted(set(files)):
        try:
            relative = path.relative_to(base)
        except ValueError:
            relative = Path(path.name)
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def checker_registry_files(repo: Path) -> list[Path]:
    """Return every Python source file that can define or register a checker."""
    runners = repo / "runners"
    files = [
        runners / "simulate_evas.py",
        runners / "main120_stable_checks.py",
    ]
    files.extend(sorted(runners.glob("v4_*checkers*.py")))
    checker_package = runners / "checkers"
    if checker_package.is_dir():
        files.extend(sorted(checker_package.rglob("*.py")))
    return sorted({path for path in files if path.is_file()})


def checker_registry_hash(repo: Path) -> str:
    """Return the canonical checker registry source-tree identity."""
    return tree_hash(checker_registry_files(repo), base=repo)
