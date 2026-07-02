"""R0 prompt assembly for the agent.

Scope reduction vs the standalone vaEvas-Agent: this module now ONLY builds the
Round 0 system + task prompts. The R1+ repair prompts are delegated to
``runners/build_repair_prompt.py`` via ``runners/agent/prompt_modes.py`` —
that file carries the rich metric-gap / DWA / layered-repair knowledge that
the standalone agent's pipeline.py lacked.

Kept here (because R0 needs them and they're also reused by agent.py's
task-context builder):
  - build_system_prompt(skill_context, extra_rules)
  - build_task_prompt(task_dir, ...)
  - _resolve_gold_path, _read_meta, _read_prompt_md  (gold/meta/prompt discovery)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .system import SYSTEM_PROMPT


# ─── System prompt ───────────────────────────────────────────

def build_system_prompt(
    skill_context: str = "",
    extra_rules: list[str] | None = None,
) -> str:
    """Build the system prompt with optional skill context appended."""
    prompt = SYSTEM_PROMPT
    if skill_context:
        prompt += skill_context
    if extra_rules:
        prompt += "\n\n" + "\n".join(extra_rules)
    return prompt


# ─── Task prompt (Round 0: generation) ───────────────────────

def build_task_prompt(
    task_dir: Path,
    *,
    skill_context: str = "",
) -> str:
    """Build the user prompt for initial generation (Round 0).

    NOTE: For closed-loop modes the R0 prompt is actually built by
    ``prompt_modes.build_round0_prompt`` (which calls build_skill_only_prompt).
    This function is retained for callers that want a richer inline R0 prompt
    with contract injection (e.g. the `list` command's preview, or tests).
    """
    meta = _read_meta(task_dir)
    task_id = meta.get("task_id") or meta.get("id") or task_dir.name
    family = meta.get("family", "end-to-end")
    prompt_md = _read_prompt_md(task_dir)

    if family == "bugfix":
        buggy_code = _read_buggy_dut(task_dir)
        if buggy_code:
            prompt_md += f"\n\n## Buggy DUT\n\n```verilog-a\n{buggy_code}\n```\n"

    if family == "end-to-end":
        prompt_md += (
            "\n\n## End-To-End Output Contract (MANDATORY)\n\n"
            "You MUST return both deliverables:\n"
            "1. DUT Verilog-A code block: ```verilog-a ... ```\n"
            "2. Spectre testbench code block: ```spectre ... ```\n\n"
            "Do not return DUT-only output for this task.\n"
        )

    gold_dir = _resolve_gold_path(task_dir)
    if gold_dir and family in ("spec-to-va", "bugfix", "end-to-end"):
        gold_tb = _find_gold_tb(gold_dir, task_dir)
        if gold_tb:
            try:
                gold_tb_text = gold_tb.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                gold_tb_text = ""
            if gold_tb_text:
                prompt_md += _inject_evas_validation_contract(gold_tb_text)
                prompt_md += _inject_module_name_contract(family, gold_tb_text, task_id)

    if family in ("spec-to-va", "bugfix", "end-to-end"):
        prompt_md += _VA_SYNTAX_RULES

    if skill_context:
        prompt_md += skill_context

    return prompt_md


# ─── Inline injection helpers ────────────────────────────────

_VA_SYNTAX_RULES = """
## Verilog-A Syntax Rules (MANDATORY)

Your code must be pure Verilog-A, not digital Verilog. Spectre VACOMP will reject:
1. `reg`, `wire`, `logic` — use `electrical` for signals, `integer` for state.
2. Packed bit-select like `sig[3] = ...` on scalar integers.
3. `always @(...)` — use `analog begin` with `@(cross(...))`.
4. `initial begin` — use `@(initial_step)` inside `analog`.
5. Bit literals like `7'b0000001` — use integer constants.
6. Multiple `<+` to the same node adds contributions, not overwrites.
"""


def _inject_evas_validation_contract(gold_tb_text: str) -> str:
    tran_match = re.search(r'^\s*tran\s+\w+.*$', gold_tb_text, re.MULTILINE | re.IGNORECASE)
    if not tran_match:
        return ""
    tran_line = re.sub(r'\s+', ' ', tran_match.group(0).strip())
    return f"""
## Strict EVAS Validation Contract (MANDATORY)

The final EVAS validation uses this transient setting:
```spectre
{tran_line}
```
A fixed reference testbench will validate your DUT using this timing window.
Do not shorten the stop time or use a coarser maxstep.
"""


def _inject_module_name_contract(family: str, gold_tb_text: str, task_id: str) -> str:
    include_match = re.search(r'ahdl_include\s+"([^"]+\.va)"', gold_tb_text)
    if not include_match:
        return ""
    include_file = include_match.group(1)
    include_stem = Path(include_file).stem
    expected_mod = include_stem
    if family == "bugfix":
        xdut_match = re.search(r'\bXDUT\s+\([^)]+\)\s+(\w+)', gold_tb_text)
        if xdut_match:
            expected_mod = xdut_match.group(1)
    lines = [
        "",
        "## Module Name Contract",
        f"Your module **MUST** be named exactly **`{expected_mod}`**.",
        f"- Your file will be included as `ahdl_include \"{include_file}\"`",
        f"- Your module declaration MUST be: `module {expected_mod}(...);`",
    ]
    if expected_mod != task_id:
        lines.append(f"- Do **not** use `{task_id}` — the correct name is `{expected_mod}`.")
    return "\n".join(lines)


# ─── Utility helpers (shared with agent.py) ──────────────────

def _read_meta(task_dir: Path) -> dict:
    meta_path = task_dir / "meta.json"
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {}


def _resolve_gold_path(task_dir: Path) -> Path | None:
    """Resolve the gold/ directory, walking up for hidden/ variants.

    For v3 tasks, falls back to solution/.
    """
    candidate = task_dir / "gold"
    if candidate.exists():
        return candidate
    sol = task_dir / "solution"
    if sol.is_dir():
        return sol
    for parent in task_dir.parents:
        candidate = parent / "gold"
        if candidate.exists():
            return candidate
        if (parent / ".git").exists() or (parent / "schemas").exists():
            break
    return None


def _read_prompt_md(task_dir: Path) -> str:
    """Read prompt.md, falling back to instruction.md (v3) or parent dirs."""
    prompt_path = task_dir / "prompt.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    instruction_path = task_dir / "instruction.md"
    if instruction_path.exists():
        return instruction_path.read_text(encoding="utf-8")
    for parent in task_dir.parents:
        candidate = parent / "prompt.md"
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
        if (parent / ".git").exists() or (parent / "schemas").exists():
            break
    return ""


def _read_buggy_dut(task_dir: Path) -> str | None:
    buggy_dir = task_dir / "buggy"
    if not buggy_dir.exists():
        return None
    va_files = sorted(buggy_dir.glob("*.va"))
    if va_files:
        return va_files[0].read_text(encoding="utf-8", errors="ignore")
    return None


def _find_gold_tb(gold_dir: Path, task_dir: Path | None = None) -> Path | None:
    preferred = sorted(gold_dir.glob("tb*_ref.scs"))
    if preferred:
        return preferred[0]
    fallback = sorted(gold_dir.glob("tb*.scs"))
    if fallback:
        return fallback[0]
    if task_dir is None:
        return None
    parent_gold = _resolve_gold_path(task_dir.parent) if task_dir.parent != task_dir else None
    if parent_gold and parent_gold != gold_dir:
        return _find_gold_tb(parent_gold, task_dir.parent)
    return None
