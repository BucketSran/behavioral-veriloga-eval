from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"
LEGACY_SAVE_QUALIFIER = re.compile(r"\b[A-Za-z_]\w*:(?:[0-9][A-Za-z0-9]*|d|f)\b")


def test_gold_testbenches_do_not_use_legacy_save_qualifiers() -> None:
    offenders: list[str] = []

    for tb_path in sorted(TASKS_DIR.rglob("tb_*.scs")):
        in_save = False
        for lineno, raw_line in enumerate(tb_path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw_line.strip()
            if line.startswith("save "):
                in_save = True
            if in_save and LEGACY_SAVE_QUALIFIER.search(raw_line):
                offenders.append(f"{tb_path.relative_to(ROOT)}:{lineno}: {raw_line.strip()}")
            if in_save and not raw_line.rstrip().endswith("\\"):
                in_save = False

    assert not offenders, "Legacy Spectre save qualifiers remain:\n" + "\n".join(offenders)
