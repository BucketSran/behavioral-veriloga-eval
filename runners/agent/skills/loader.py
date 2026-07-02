"""Skill loader — scans veriloga-skills categories and loads reference markdown.

Path resolution no longer hardcodes ``~/Desktop/WorkSpace/...``. The caller
(the Agent / SkillManager) supplies ``skills_root`` from config; if none is
supplied, we fall back to a path relative to the agent package.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class SkillRef:
    name: str
    path: Path
    category: str
    source: str


# ─── Keyword → category mapping ──────────────────────────────

KEYWORD_INDEX: dict[str, str] = {
    # PLL / Clock
    "pll": "pll-clock",
    "adpll": "pll-clock",
    "cppll": "pll-clock",
    "pfd": "pll-clock",
    "vco": "pll-clock",
    "lock": "pll-clock",
    "bbpd": "pll-clock",
    # DAC
    "dac": "dac",
    "dwa": "dac",
    "therm": "dac",
    "binary_clk": "dac",
    # ADC / SAR
    "adc": "adc-sar",
    "sar": "adc-sar",
    "flash_adc": "adc-sar",
    # Comparator
    "comparator": "comparator",
    "cmp": "comparator",
    "strongarm": "comparator",
    "hysteresis": "comparator",
    "offset": "comparator",
    # Digital Logic
    "mux": "digital-logic",
    "divider": "digital-logic",
    "clk_div": "digital-logic",
    "counter": "digital-logic",
    "lfsr": "digital-logic",
    "prbs": "digital-logic",
    "gray": "digital-logic",
    "digital": "digital-logic",
    "gate": "digital-logic",
    "dff": "digital-logic",
    "flip": "digital-logic",
    "d2b": "digital-logic",
    # Sample & Hold
    "sample_hold": "sample-hold",
    "sample": "sample-hold",
    "aperture": "sample-hold",
    # Amplifier / Filter
    "gain": "amplifier-filter",
    "filter": "amplifier-filter",
    "lpf": "amplifier-filter",
    "amplifier": "amplifier-filter",
    # Signal Source
    "noise": "signal-source",
    "ramp": "signal-source",
    "burst": "signal-source",
    "pulse": "signal-source",
    "sine": "signal-source",
    # Measurement
    "extraction": "measurement-helpers",
    # Calibration
    "calibration": "calibration",
    # Power / Switch
    "switch": "power-switch",
    "power": "power-switch",
    # Passive
    "passive": "passive-model",
    "rlc": "passive-model",
    # Testbench
    "tb_generation": "testbench-spectre",
    "testbench": "testbench-spectre",
}


CATEGORY_FILE_MAP: dict[str, str] = {
    "adc-sar": "adc-sar.md",
    "amplifier-filter": "amplifier-filter.md",
    "calibration": "calibration.md",
    "comparator": "comparator.md",
    "dac": "dac.md",
    "digital-logic": "digital-logic.md",
    "measurement-helpers": "measurement-helpers.md",
    "passive-model": "passive-model.md",
    "pll-clock": "pll-clock.md",
    "power-switch": "power-switch.md",
    "sample-hold": "sample-hold.md",
    "signal-source": "signal-source.md",
    "testbench-spectre": "testbench-spectre.md",
}


def resolve_skills_root(config_skills_path: str | None = None) -> Path | None:
    """Resolve the veriloga-skills root directory.

    Search order:
      1. config_skills_path (explicit, from AgentConfig)
      2. ``../../veriloga-skills`` relative to this file (runners/agent → repo root)
      3. ``../../../veriloga-skills`` (one more level up)
    """
    candidates: list[Path] = []

    if config_skills_path:
        candidates.append(Path(config_skills_path).resolve())

    pkg_root = Path(__file__).resolve().parent.parent.parent  # runners/
    repo_root = pkg_root.parent                                # behavioral-veriloga-eval/
    candidates.append((repo_root.parent / "veriloga-skills").resolve())
    candidates.append((repo_root / ".." / "veriloga-skills").resolve())

    for c in candidates:
        try:
            if c.exists() and c.is_dir():
                return c
        except (OSError, PermissionError):
            continue
    return None


def list_categories(categories_dir: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    if not categories_dir.exists():
        return result
    for md_file in sorted(categories_dir.glob("*.md")):
        result[md_file.stem] = md_file
    return result


def load_category_content(file_path: Path, max_chars: int = 3000) -> str:
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return ""

    if len(text) <= max_chars:
        return text.strip()

    truncated = text[:max_chars]
    last_break = max(truncated.rfind("\n\n"), truncated.rfind("\n## "))
    if last_break > max_chars // 2:
        truncated = text[:last_break]
    return truncated.strip() + "\n\n... (truncated)"
