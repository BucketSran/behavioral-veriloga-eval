"""Registry for canonical v4 checker candidates.

The modules in this package are mechanically migrated candidates.  Loading a
checker from this registry proves that the current package can resolve the
checker ID; certification still comes from the benchmark evidence chain.
"""

from __future__ import annotations

import ast
from functools import lru_cache, wraps
from importlib import import_module
from pathlib import Path
import re
from types import ModuleType

from ..api import Checker
from .stimulus_relative import canonical_time_rows


_TASK_MODULE_RE = re.compile(r"task_\d{3}\.py$")
_COMPATIBILITY_CHECKER_MODULES = {
    "v4_074_crossing_metric_writer": "legacy_task_074",
    "v4_091_final_step_file_metric": "legacy_task_091",
}


def _checker_id_from_source(text: str) -> str | None:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None

    constants: dict[str, str] = {}
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        value = statement.value
        for target in statement.targets:
            if not isinstance(target, ast.Name):
                continue
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                constants[target.id] = value.value
                if target.id == "CHECKER_ID":
                    return value.value
            elif target.id == "CHECKER_ID" and isinstance(value, ast.Name):
                return constants.get(value.id)
    return constants.get("CHECKER_ID")


def _discover_checker_modules() -> dict[str, str]:
    modules: dict[str, str] = {}
    for path in sorted(Path(__file__).resolve().parent.glob("task_*.py")):
        if not _TASK_MODULE_RE.fullmatch(path.name):
            continue
        checker_id = _checker_id_from_source(path.read_text(encoding="utf-8"))
        if checker_id is None:
            continue
        modules[checker_id] = path.stem
    return modules


@lru_cache(maxsize=1)
def checker_modules() -> dict[str, str]:
    return _discover_checker_modules()


def published_checker_ids() -> tuple[str, ...]:
    return tuple(sorted(checker_modules()))


def _module_suffix_for_checker_id(checker_id: str) -> str | None:
    return checker_modules().get(checker_id) or _COMPATIBILITY_CHECKER_MODULES.get(
        checker_id
    )


def _validated_checker(module: ModuleType, checker_id: str) -> Checker | None:
    if getattr(module, "CHECKER_ID", None) != checker_id:
        return None
    checker = getattr(module, "CHECKER", None)
    if not callable(checker):
        return None

    @wraps(checker)
    def canonical_checker(rows):
        return checker(canonical_time_rows(rows))

    return canonical_checker


def _validated_streaming_checker(module: ModuleType, checker_id: str) -> Checker | None:
    if getattr(module, "CHECKER_ID", None) != checker_id:
        return None
    checker = getattr(module, "STREAMING_CHECKER", None)
    return checker if callable(checker) else None


@lru_cache(maxsize=None)
def load_checker(checker_id: str) -> Checker | None:
    module_suffix = _module_suffix_for_checker_id(checker_id)
    if module_suffix is None:
        return None
    try:
        module = import_module(f"{__package__}.{module_suffix}")
    except (ImportError, AttributeError):
        return None
    return _validated_checker(module, checker_id)


@lru_cache(maxsize=None)
def load_streaming_checker(checker_id: str) -> Checker | None:
    module_suffix = _module_suffix_for_checker_id(checker_id)
    if module_suffix is None:
        return None
    try:
        module = import_module(f"{__package__}.{module_suffix}")
    except (ImportError, AttributeError):
        return None
    return _validated_streaming_checker(module, checker_id)
