from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"
COMMENT_RE = re.compile(r"//.*$")


def _strip_comment(line: str) -> str:
    return COMMENT_RE.sub("", line)


def _lint_pwl_file(path: Path) -> list[str]:
    offenders: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    waiting_wave = False
    in_wave = False
    wave_tokens: list[str] = []
    wave_start_lineno = 0
    wave_start_line = ""

    def start_wave(raw_line: str, lineno: int) -> None:
        nonlocal in_wave, wave_start_lineno, wave_start_line, wave_tokens
        in_wave = True
        wave_start_lineno = lineno
        wave_start_line = raw_line.strip()
        wave_tokens = []

    def add_wave_tokens(fragment: str) -> None:
        cleaned = _strip_comment(fragment).replace("\\", " ").replace("[", " ").replace("]", " ")
        wave_tokens.extend(token for token in cleaned.split() if token)

    def finish_wave(path: Path) -> None:
        if len(wave_tokens) % 2 != 0:
            offenders.append(
                f"{path.relative_to(ROOT)}:{wave_start_lineno}: odd number of PWL tokens in `{wave_start_line}`"
            )

    for lineno, raw_line in enumerate(lines, start=1):
        line = _strip_comment(raw_line)
        stripped = line.strip()
        ends_with_continuation = raw_line.rstrip().endswith("\\")

        if waiting_wave and "wave=[" in line:
            waiting_wave = False
            start_wave(raw_line, lineno)
            if "]" not in line and not ends_with_continuation:
                offenders.append(
                    f"{path.relative_to(ROOT)}:{lineno}: multi-line PWL must use explicit continuation `\\`"
                )
            add_wave_tokens(line.split("wave=[", 1)[1])
            if "]" in line:
                in_wave = False
                finish_wave(path)
            continue

        if "type=pwl" in line:
            if "wave=[" in line:
                start_wave(raw_line, lineno)
                if "]" not in line and not ends_with_continuation:
                    offenders.append(
                        f"{path.relative_to(ROOT)}:{lineno}: multi-line PWL must use explicit continuation `\\`"
                    )
                add_wave_tokens(line.split("wave=[", 1)[1])
                if "]" in line:
                    in_wave = False
                    finish_wave(path)
                continue
            waiting_wave = ends_with_continuation

        if in_wave:
            if "]" not in line and stripped and not ends_with_continuation:
                offenders.append(
                    f"{path.relative_to(ROOT)}:{lineno}: continued PWL lines must end with `\\` until `]` closes"
                )
            add_wave_tokens(line)
            if "]" in line:
                in_wave = False
                finish_wave(path)

    return offenders


def test_gold_testbenches_use_spectre_safe_pwl_format() -> None:
    offenders: list[str] = []

    for tb_path in sorted(TASKS_DIR.rglob("tb_*.scs")):
        offenders.extend(_lint_pwl_file(tb_path))

    assert not offenders, "Unsafe or malformed PWL sources remain:\n" + "\n".join(offenders)
