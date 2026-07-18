from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from checker_registry_identity import checker_registry_files, checker_registry_hash


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    _write(repo / "runners" / "simulate_evas.py", "CHECKS = {}\n")
    _write(repo / "runners" / "main120_stable_checks.py", "def register(c): pass\n")
    _write(repo / "runners" / "v4_gate2_checkers_342_349.py", "CHECKS = {}\n")
    _write(repo / "runners" / "checkers" / "v4" / "canonical_201_220.py", "CHECKS = {}\n")
    _write(repo / "runners" / "unrelated_runner.py", "VALUE = 1\n")
    return repo


def test_registry_identity_covers_legacy_and_modular_checker_sources(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    relative = [path.relative_to(repo).as_posix() for path in checker_registry_files(repo)]
    assert relative == [
        "runners/checkers/v4/canonical_201_220.py",
        "runners/main120_stable_checks.py",
        "runners/simulate_evas.py",
        "runners/v4_gate2_checkers_342_349.py",
    ]


def test_registry_identity_changes_only_for_checker_source_tree(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    before = checker_registry_hash(repo)

    _write(repo / "runners" / "unrelated_runner.py", "VALUE = 2\n")
    assert checker_registry_hash(repo) == before

    _write(
        repo / "runners" / "checkers" / "v4" / "canonical_201_220.py",
        "CHECKS = {\"v4_201\": object()}\n",
    )
    assert checker_registry_hash(repo) != before
