#!/usr/bin/env python3
"""
generate.py — LLM candidate generator for vaEvas benchmark.

Calls an LLM API to generate Verilog-A DUT and/or Spectre testbench files
for one or more benchmark tasks, then saves them in the layout expected by score.py.

Output layout:
  <output-dir>/<model_slug>/<task_id>/sample_<idx>/
    ├── <dut_name>.va            (for spec-to-va, bugfix, end-to-end)
    ├── tb_<name>.scs            (for end-to-end, tb-generation)
    └── generation_meta.json     (model, tokens, finish_reason, timestamp)

Supported providers (auto-detected from model name):
  anthropic  : claude-*  (requires ANTHROPIC_API_KEY)
  openai     : gpt-*, o1*, o3*, o4*  (requires OPENAI_API_KEY)
  bailian    : qwen*, glm*, kimi*, minimax*, MiniMax*
               Uses Anthropic SDK with Alibaba Cloud DashScope endpoint.
               Requires BAILIAN_API_KEY (or set via --bailian-api-key).
               Base URL: https://coding.dashscope.aliyuncs.com/apps/anthropic/v1

Usage:
  cd behavioral-veriloga-eval
  python runners/generate.py --model claude-sonnet-4-6 --task digital_basics_smoke
  python runners/generate.py --model gpt-4o --all --family end-to-end
  python runners/generate.py --model qwen3-coder-plus --all --family end-to-end
  python runners/generate.py --model claude-sonnet-4-6 --task digital_basics_smoke --dry-run
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
ALL_FAMILIES = ("end-to-end", "spec-to-va", "bugfix", "tb-generation")


def family_task_root(family: str) -> Path:
    base = ROOT / "tasks"
    return {
        "end-to-end": base / "end-to-end" / "voltage",
        "spec-to-va": base / "spec-to-va" / "voltage",
        "bugfix": base / "bugfix" / "voltage",
        "tb-generation": base / "tb-generation" / "voltage",
    }[family]


def read_meta(task_dir: Path) -> dict:
    return json.loads((task_dir / "meta.json").read_text(encoding="utf-8"))


def _normalize_port_name(port_item: str) -> str | None:
    item = re.sub(r"\[[^\]]+\]", " ", port_item)
    tokens = [tok for tok in re.split(r"\s+", item.strip()) if tok]
    for token in reversed(tokens):
        if re.fullmatch(r"[A-Za-z_]\w*", token):
            return token
    return None


def extract_module_signature(va_path: Path) -> tuple[str, list[str]] | None:
    text = va_path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"\bmodule\s+(\w+)\s*\((.*?)\)\s*;", text, re.DOTALL)
    if not match:
        return None
    module_name = match.group(1)
    raw_ports = match.group(2)
    ports: list[str] = []
    for item in raw_ports.replace("\n", " ").split(","):
        port_name = _normalize_port_name(item)
        if port_name:
            ports.append(port_name)
    if not ports:
        return None
    return module_name, ports


def _extract_tb_supply_contract(tb_path: Path, ports: list[str]) -> tuple[str, str, str]:
    if len(ports) < 2:
        return "VDD", "VSS", "0.9"

    vdd_node = ports[0]
    vss_node = ports[1]
    vdd_value = "0.9"
    tb_text = tb_path.read_text(encoding="utf-8", errors="ignore")

    def _find_dc(node_name: str) -> str | None:
        pattern = re.compile(
            rf"\b\w+\s*\(\s*{re.escape(node_name)}\s+0\s*\)\s+vsource\b[^\n]*?\bdc\s*=\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))",
            re.IGNORECASE,
        )
        match = pattern.search(tb_text)
        return match.group(1) if match else None

    found_vdd = _find_dc(vdd_node)
    found_vss = _find_dc(vss_node)
    if found_vdd is not None:
        vdd_value = found_vdd
    if found_vss is not None and found_vss not in {"0", "0.0"}:
        vss_node = ports[1]
    return vdd_node, vss_node, vdd_value


_TRAN_RE = re.compile(r"^\s*tran\s+\w+.*$", re.IGNORECASE | re.MULTILINE)
_MAXSTEP_RE = re.compile(r"\bmaxstep\s*=", re.IGNORECASE)
_AHDL_INCLUDE_RE = re.compile(r'ahdl_include\s+"([^"]+\.va)"', re.IGNORECASE)


def gold_include_entries(task_dir: Path, tb_text: str | None = None) -> list[dict[str, str]]:
    """Return verifier include filenames plus the real module declared inside.

    Some verifier files intentionally use a wrapper/reference filename such as
    `and_gate_ref.va` while declaring `module and_gate(...)`.  Public contracts
    must use the declared module name; the include filename is only a staging
    detail for the verifier harness.
    """
    gold_dir = task_dir / "gold"
    if not gold_dir.is_dir():
        return []

    if tb_text is None:
        tbs = sorted(gold_dir.glob("tb_*.scs"))
        if not tbs:
            return []
        tb_text = tbs[0].read_text(encoding="utf-8", errors="ignore")

    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw_path in _AHDL_INCLUDE_RE.findall(tb_text):
        filename = Path(raw_path).name
        stem = Path(filename).stem
        if filename in seen:
            continue
        seen.add(filename)
        module = stem
        va_path = gold_dir / filename
        if va_path.exists():
            signature = extract_module_signature(va_path)
            if signature:
                module = signature[0]
        entries.append({"filename": filename, "stem": stem, "module": module})
    return entries


def _strict_tran_lines(task_dir: Path) -> list[str]:
    """Extract public strict transient statements from the verifier harness.

    The returned lines are testbench-level validation settings, not gold DUT
    implementation details. They are safe to expose as a public contract.
    """
    gold_dir = task_dir / "gold"
    if not gold_dir.is_dir():
        return []

    lines: list[str] = []
    seen: set[str] = set()
    for tb_path in sorted(gold_dir.glob("*.scs")):
        text = tb_path.read_text(encoding="utf-8", errors="ignore")
        for match in _TRAN_RE.finditer(text):
            line = re.sub(r"\s+", " ", match.group(0).strip())
            if line and line not in seen:
                seen.add(line)
                lines.append(line)
    return lines


def _inject_strict_evas_validation_contract(task_dir: Path, family: str) -> list[str]:
    """Inject the final EVAS validation transient contract.

    This is distinct from adaptive quick-check settings. Quick-check maxstep is
    an internal runner acceleration and must not be presented as a task target.
    """
    tran_lines = _strict_tran_lines(task_dir)
    if not tran_lines:
        return []

    prompt_text = (task_dir / "prompt.md").read_text(encoding="utf-8", errors="ignore").lower()
    if "strict evas validation contract" in prompt_text:
        return []

    lines = [
        "",
        "## Strict EVAS Validation Contract (MANDATORY)",
        "",
        "The final EVAS validation uses the following transient analysis setting(s):",
        "",
        "```spectre",
        *tran_lines,
        "```",
        "",
    ]

    any_maxstep = any(_MAXSTEP_RE.search(line) for line in tran_lines)
    if family in ("end-to-end", "tb-generation"):
        lines.extend(
            [
                "If you generate a Spectre testbench, include the transient statement above exactly.",
                "Do not shorten the stop time or use a coarser `maxstep` in the final submitted testbench.",
            ]
        )
    else:
        lines.extend(
            [
                "A fixed reference testbench will validate your DUT using this timing window.",
                "You do not need to output a testbench unless the task explicitly asks for one.",
            ]
        )

    if any_maxstep:
        lines.append(
            "The adaptive runner may use a faster internal quick-check, but the final candidate must pass this strict setting."
        )
    else:
        lines.append(
            "This reference harness does not specify `maxstep`; preserve the shown final validation timing."
        )
    return lines


# ---------------------------------------------------------------------------
# Task discovery
# ---------------------------------------------------------------------------

def list_task_dirs(families: tuple[str, ...] = ALL_FAMILIES,
                   selected: set[str] | None = None) -> list[tuple[str, Path]]:
    result = []
    for family in families:
        root = family_task_root(family)
        if not root.exists():
            continue
        for meta_path in sorted(root.rglob("meta.json")):
            task_dir = meta_path.parent
            if not (task_dir / "prompt.md").exists():
                continue  # no prompt → can't generate
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            task_id = meta.get("task_id") or meta.get("id") or task_dir.name
            if selected and task_id not in selected:
                continue
            # Skip scope-guard tasks
            if meta.get("tier") == "scope-guard":
                continue
            result.append((task_id, task_dir))
    return result


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = textwrap.dedent("""\
    You are an expert Verilog-A behavioral model engineer.
    Your task is to write correct, simulation-ready Verilog-A (.va) modules
    and/or Spectre testbenches (.scs) for analog/mixed-signal circuits.

    Rules:
    1. Use ONLY voltage-domain constructs: V() <+, @(cross()), @(above()),
       @(timer()), @(initial_step), @(final_step), transition(), if/else, for, while.
    2. Do NOT use I() <+, ddt(), idt(), laplace_nd(), or any current-domain operator.
    3. Always include `constants.vams` and `disciplines.vams`.
    4. Output each file as a single fenced code block:
       - Verilog-A files: ```verilog-a ... ``` (or ```verilog ... ```)
       - Spectre testbenches: ```spectre ... ```
    5. Do not include any explanation outside the code blocks.
    6. If multiple files are needed, output them in order: DUT first, then testbench.
    7. Choose module granularity from the task contract, not from circuit size alone.
       If the task specifies one behavioral block with one analog input and digital/analog
       outputs, implement it as one coherent behavioral module even if the real circuit
       could contain many internal subcircuits.
    8. Split into multiple modules only when the task explicitly asks for distinct modeled
       blocks, required includes, or independently named interfaces. When you split, each
       module must have a clear standalone behavior and the top-level testbench must
       exercise every required block through observable signals.
    9. Do not invent hidden submodules just to look realistic; prefer the simplest
       evaluator-visible behavioral abstraction that satisfies the public contract.
""")


def build_prompt(
    task_dir: Path,
    include_checker: bool = False,
    include_skill: bool = False,
    include_public_contract: bool = True,
) -> str:
    """Read prompt.md and optionally include buggy DUT for bugfix tasks.

    Args:
        task_dir: Path to the task directory
        include_checker: If True, inject checker source code (condition B)
        include_skill: If True, inject Skill circuit knowledge (condition C)
        include_public_contract: If True, inject evaluator-aligned public
            behavioral indicators without exposing gold implementation details.
    """
    prompt_md = (task_dir / "prompt.md").read_text(encoding="utf-8")
    raw_has_public_eval_contract = "public evaluation contract (non-gold)" in prompt_md.lower()
    meta = read_meta(task_dir)
    family = meta.get("family", "end-to-end")
    task_id = meta.get("task_id") or meta.get("id") or task_dir.name

    # For bugfix tasks, append the buggy DUT source code
    if family == "bugfix":
        buggy_dir = task_dir / "buggy"
        if buggy_dir.is_dir():
            buggy_vas = sorted(buggy_dir.glob("*.va"))
            if buggy_vas:
                buggy_code = buggy_vas[0].read_text(encoding="utf-8")
                dut_name = buggy_vas[0].name
                prompt_md += f"\n\n## Buggy DUT ({dut_name})\n\n```verilog-a\n{buggy_code}\n```\n"

    gold_include_entries_list: list[dict[str, str]] = []
    gold_tb_text = ""
    if family in ("spec-to-va", "bugfix", "end-to-end"):
        gold_dir = task_dir / "gold"
        if gold_dir.is_dir():
            tbs = sorted(gold_dir.glob("tb_*.scs"))
            if tbs:
                gold_tb_text = tbs[0].read_text(encoding="utf-8", errors="ignore")
                gold_include_entries_list = gold_include_entries(task_dir, gold_tb_text)

    if family == "end-to-end":
        prompt_md += """
## End-To-End Output Contract (MANDATORY)

You MUST return both deliverables:
1. DUT Verilog-A code block: ```verilog-a ... ```
2. Spectre testbench code block: ```spectre ... ```

Do not return DUT-only output for this task.

## Hierarchical Modeling Policy (MANDATORY)

Choose the module boundary from the public task contract:
- If the task asks for a single behavioral component, keep it as one coherent module even if a transistor-level implementation would contain many internal blocks.
- If the task asks for multiple named blocks/modules, implement those blocks separately and connect them in one top-level testbench.
- For split designs, each generated module must have a clear local contract and the testbench must exercise the integrated behavior through the required public observables.
- Do not add extra hidden submodules unless they are necessary to satisfy a named task interface or required include.
"""

    strict_tran_contract = [] if raw_has_public_eval_contract else _inject_strict_evas_validation_contract(task_dir, family)
    if strict_tran_contract:
        prompt_md += "\n\n" + "\n".join(strict_tran_contract)

    # For spec-to-va / bugfix / end-to-end tasks, inject contract information
    # from the gold testbench. For end-to-end multi-module tasks, inject a
    # multi-module contract instead of forcing a single module name.
    if family in ("spec-to-va", "bugfix", "end-to-end") and gold_include_entries_list:
        if family == "bugfix":
            first_entry = gold_include_entries_list[0]
            expected_mod = first_entry["module"]
            m_xdut = re.search(r'\bXDUT\s+\([^)]+\)\s+(\w+)', gold_tb_text)
            if m_xdut:
                expected_mod = m_xdut.group(1)
            prompt_md += (
                "\n\n## Module Name Contract\n\n"
                f"Your module **MUST** be named exactly **`{expected_mod}`**.\n"
                f"- Your file will be included as `ahdl_include \"{first_entry['filename']}\"`\n"
                f"- Your module declaration MUST be: `module {expected_mod}(...);`\n"
            )
        elif family == "spec-to-va" or (family == "end-to-end" and len(gold_include_entries_list) == 1):
            first_entry = gold_include_entries_list[0]
            expected_mod = first_entry["module"]
            prompt_md += (
                "\n\n## Module Name Contract\n\n"
                f"Your module **MUST** be named exactly **`{expected_mod}`**.\n"
                f"- The verifier may include it from `ahdl_include \"{first_entry['filename']}\"`\n"
                f"- Your module declaration MUST be: `module {expected_mod}(...);`\n"
                + (f"- Do **not** use `{task_id}` — the correct name is `{expected_mod}`.\n"
                   if expected_mod != task_id else "")
            )
        elif family == "end-to-end":
            include_list = "\n".join(
                f"- `{entry['filename']}` must contain module `{entry['module']}`"
                for entry in gold_include_entries_list
            )
            prompt_md += (
                "\n\n## Multi-Module Contract\n\n"
                "This task expects multiple Verilog-A modules. Do NOT collapse them into one file.\n"
                "Generate one module per required include:\n"
                f"{include_list}\n"
            )

    # Inject Verilog-A mandatory syntax rules for DUT generation.
    # Models often emit digital Verilog syntax (reg, always @, packed bit-select)
    # which Spectre VACOMP rejects.
    if family in ("spec-to-va", "bugfix", "end-to-end"):
        prompt_md += """
## Verilog-A Syntax Rules (MANDATORY)

Your code must be **pure Verilog-A**, not digital Verilog. Spectre VACOMP will reject:
1. `reg`, `wire`, `logic` — use `electrical` for signals, `integer` for state variables.
2. Packed bit-select like `sig[3] = ...` on scalar integers. If you need multi-bit ports, declare `electrical [N:0] sig` and iterate with `@(initial_step)` or analog block, NOT `always @`.
3. `always @(...) block` — Verilog-A uses `analog begin ... end` with `@(cross(...))` for edge detection.
4. `initial begin` — Verilog-A uses `@(initial_step)` inside `analog`.
5. Bit literals like `7'b0000001` — use integer constants with `transition()`.
6. Assignments in `always` — Verilog-A analog assignments use `V(out) <+ expr` or `I(out) <+ expr`.

**Correct Verilog-A template:**
```verilog-a
module NAME (ports);
    electrical ports;
    integer state;   // NOT reg
    analog begin
        @(initial_step) state = 0;   // NOT initial begin
        @(cross(V(clk) - vth, 1))    // NOT always @(posedge clk)
            state = state + 1;
        V(out) <+ transition(state * vstep, 0, 1n);
    end
endmodule
```
"""

    # For tb-generation tasks, inject the Gold VA interface as hard constraints.
    # The model must use: exact module names, exact port order, correct supply voltage.
    if family == "tb-generation":
        gold_dir = task_dir / "gold"
        if gold_dir.is_dir():
            gold_vas = sorted(gold_dir.glob("*.va"))
            gold_tbs = sorted(gold_dir.glob("tb_*.scs"))
            gold_tb = gold_tbs[0] if gold_tbs else None
            dut_entries: list[str] = []
            for gva in gold_vas:
                signature = extract_module_signature(gva)
                if not signature:
                    continue
                mod, port_names = signature
                ports = ", ".join(port_names)
                vdd_node, vss_node, vdd_v = (
                    _extract_tb_supply_contract(gold_tb, port_names)
                    if gold_tb is not None
                    else ("VDD", "VSS", "0.9")
                )
                dut_entries.append(
                    f"**DUT: `{mod}`** (`{gva.name}`)\n"
                    f"- Port order (positional): `({ports})`\n"
                    f"- Supply: `Vvdd ({vdd_node} 0) vsource dc={vdd_v}` and `Vvss ({vss_node} 0) vsource dc=0`\n"
                    f"- Include line (place LAST): `ahdl_include \"{gva.name}\"`\n"
                    f"- Instantiation: `XDUT ({ports}) {mod}`"
                )
            if dut_entries:
                prompt_md += (
                    "\n\n## DUT Contract — MUST follow exactly\n\n"
                    "The Gold DUT Verilog-A file(s) are provided. "
                    "Use ONLY the information below — do NOT invent module names, port names, or supply voltages.\n\n"
                    + "\n\n".join(dut_entries)
                    + "\n\n"
                    "## Testbench Structure Rules\n\n"
                    "Write a minimal Spectre testbench. Do NOT add elements beyond what is needed:\n"
                    "- Use only `vsource` elements (type=pulse or type=pwl). No `vcvs`, `ccvs`, `resistor`, `capacitor` unless the task explicitly requires them.\n"
                    "- Use a single `tran` analysis only. No `dc` sweep, no `ac` analysis.\n"
                    "- `save` only the signal names listed in the task, using plain names (no `XDUT:signal` colon syntax).\n"
                    "- `ahdl_include` must be the LAST line.\n"
                    "- Add `global 0` on the second line after `simulator lang=spectre`.\n"
                )

    # Public behavioral contract: expose must-satisfy evaluator indicators as
    # task-level contract, without exposing checker source or gold design code.
    if include_public_contract:
        public_contract_lines = _inject_public_behavior_contract(task_id)
        if public_contract_lines:
            prompt_md += "\n\n" + "\n".join(public_contract_lines)
        observable_contract_lines = [] if raw_has_public_eval_contract else _inject_observable_csv_contract(task_id)
        if observable_contract_lines:
            prompt_md += "\n\n" + "\n".join(observable_contract_lines)

    # === Experiment Matrix: Inject Checker source (Condition B) ===
    if include_checker:
        checker_lines = _inject_checker_source(task_dir, task_id)
        if checker_lines:
            prompt_md += "\n\n" + "\n".join(checker_lines)

    # === Experiment Matrix: Inject Skill circuit knowledge (Condition C) ===
    if include_skill:
        skill_lines = _inject_skill_knowledge(task_id)
        if skill_lines:
            prompt_md += "\n\n" + "\n".join(skill_lines)

    return prompt_md


def _inject_checker_source(task_dir: Path, task_id: str) -> list[str]:
    """Inject checker source code for experiment condition B."""
    # Import from extract_expected_values module
    from extract_expected_values import get_checker_name_for_task

    checker_name = get_checker_name_for_task(task_id)
    source = _extract_checker_source(checker_name)
    if not source:
        return []

    circuit_context = _get_circuit_context(task_id)

    lines = [
        "",
        "# Checker Function (评分标准)",
        "",
        "以下是 evaluate your generated circuit 的 checker 函数源码。",
        "它定义了期望的电路行为（评分标准），不包含具体实现方案。",
        "",
        "请仔细阅读 checker 源码，理解期望的行为条件，然后生成满足这些条件的代码。",
        "",
        "```python",
        source,
        "```",
    ]

    if circuit_context:
        lines.extend(["", "# Circuit Context", "", circuit_context])

    return lines


def _inject_public_behavior_contract(task_id: str) -> list[str]:
    """Inject non-leaking evaluator-aligned behavioral indicators."""
    try:
        from extract_expected_values import extract_expected_values, get_checker_name_for_task
    except Exception:
        return []

    checker_name = get_checker_name_for_task(task_id)
    extracted = extract_expected_values(checker_name)
    expected = extracted.get("expected_conditions", {})
    semantic_hints = extracted.get("semantic_hints", [])

    if not expected and not semantic_hints:
        return []

    lines = [
        "",
        "## Public Behavioral Contract (Evaluator-Aligned)",
        "",
        "The following indicators are part of the public behavior contract for this task.",
        "They define what must be satisfied at evaluation time, without revealing any gold implementation.",
        "",
    ]

    skipped_metrics = {
        "v",
        "i",
        "j",
        "k",
        "x",
        "y",
        "z",
        "a",
        "b",
        "t",
    }

    def _is_contract_worthy(metric: str, description: str) -> bool:
        name = metric.strip().lower()
        desc = description.strip().lower()
        if not name or name in skipped_metrics:
            return False
        # Filter out checker internal validity guards that are not behavioral
        # targets for synthesis/repair.
        if re.search(r"should be [≤<] 0\.0(?:\s|$)", description):
            return False
        if "should be > 0.0" in description and ("period" in name or "dt" in name):
            return False
        if "not enough" in desc or "missing" in desc:
            return False
        return True

    contract_lines: list[str] = []
    for metric, info in list(expected.items())[:14]:
        desc = str(info.get("description", "")).strip()
        if not _is_contract_worthy(metric, desc):
            continue
        if desc:
            contract_lines.append(f"- `{metric}`: {desc}")
            continue
        expected_val = info.get("expected")
        tolerance = info.get("tolerance")
        if tolerance is not None:
            contract_lines.append(f"- `{metric}` should stay near `{expected_val}` with bounded tolerance.")
        else:
            contract_lines.append(f"- `{metric}` must satisfy `{expected_val}`.")

    if contract_lines:
        lines.extend(contract_lines[:10])

    curated_hints: list[str] = []
    for hint in semantic_hints:
        lowered = hint.lower()
        if "required signals" in lowered:
            curated_hints.append(hint)
        elif any(
            token in lowered
            for token in (
                "frequency",
                "ratio",
                "lock",
                "overlap",
                "reset",
                "delay",
                "monotonic",
            )
        ):
            curated_hints.append(hint)
    curated_hints = curated_hints[:4]
    if curated_hints:
        lines.extend(["", "Additional evaluator-facing constraints:"])
        for hint in curated_hints:
            lines.append(f"- {hint}")

    return lines


def _observable_columns_from_checker(task_id: str) -> list[str]:
    """Return public CSV column names required by the evaluator checker.

    This exposes only observable signal names, not the gold implementation.
    """
    try:
        from extract_expected_values import get_checker_name_for_task
    except Exception:
        return []

    source = _extract_checker_source(get_checker_name_for_task(task_id))
    if not source:
        return []

    columns: list[str] = []
    for required_body in re.findall(r"required\s*=\s*\{([^}]+)\}", source, flags=re.DOTALL):
        columns.extend(re.findall(r'"([^"]+)"', required_body))
    for literal_body in re.findall(r"not\s+\{([^}]+)\}\.issubset", source, flags=re.DOTALL):
        columns.extend(re.findall(r'"([^"]+)"', literal_body))

    expanded: list[str] = []
    seen: set[str] = set()

    def add(name: str) -> None:
        if name and name not in seen:
            seen.add(name)
            expanded.append(name)

    for col in columns:
        if col == "ptr_0":
            for idx in range(16):
                add(f"ptr_{idx}")
        elif col == "cell_en_0":
            for idx in range(16):
                add(f"cell_en_{idx}")
        elif col == "code_0":
            for idx in range(4):
                add(f"code_{idx}")
        else:
            add(col)

    return expanded


def _inject_observable_csv_contract(task_id: str) -> list[str]:
    columns = _observable_columns_from_checker(task_id)
    if not columns:
        return []

    lines = [
        "",
        "## Observable CSV Contract (MANDATORY)",
        "",
        "The EVAS checker reads `tran.csv` by exact column names. Your testbench must make these public waveform columns observable:",
        "",
    ]
    for chunk_start in range(0, len(columns), 8):
        chunk = columns[chunk_start : chunk_start + 8]
        lines.append("- `" + "`, `".join(chunk) + "`")
    lines.extend(
        [
            "",
            "Rules:",
            "- Use plain scalar save names exactly as listed above; do not rely on hierarchical names or instance-qualified names.",
            "- If the DUT uses vector ports internally, connect or save each bit so the CSV exposes the scalar names above.",
            "- For DWA-style buses, the checker expects `ptr_0..ptr_15`, `cell_en_0..cell_en_15`, and when applicable `code_0..code_3`; do not rely only on `ptr_o[0]`, `cell_en_o[0]`, or `code_i[0]` CSV headers.",
        ]
    )
    return lines


def _extract_checker_source(checker_name: str) -> str | None:
    """从 simulate_evas.py 提取完整 checker 函数源码"""
    simulate_evas_path = ROOT / "runners" / "simulate_evas.py"

    if not simulate_evas_path.exists():
        return None

    content = simulate_evas_path.read_text(encoding="utf-8")

    # 匹配函数定义到下一个 def 或文件结束
    pattern = rf"^(def {checker_name}\([^)]*\).*?)(?=\ndef [a-z_]|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)

    if not match:
        return None

    source = match.group(1).strip()

    # 限制长度（避免过长）
    if len(source) > 3000:
        source = source[:3000] + "\n... (truncated)"

    return source


def _get_circuit_context(task_id: str) -> str:
    """根据 task_id 关键词提供简短的电路上下文"""
    task_lower = task_id.lower()

    if "pll" in task_lower or "adpll" in task_lower or "cppll" in task_lower:
        return """
PLL (Phase-Locked Loop) basics:
- Lock condition: fb_clk frequency ≈ ref_clk frequency, phase aligned
- VCTRL (control voltage) should settle to a stable value
- Divider ratio: output_freq = vco_freq / divider_ratio
"""
    elif "pfd" in task_lower:
        return """
PFD (Phase-Frequency Detector) basics:
- UP pulse when ref leads fb (early)
- DN pulse when ref lags fb (late)
- UP/DN should NOT overlap when locked
"""
    elif "mux" in task_lower:
        return """
MUX (Multiplexer) basics:
- SEL signal selects which input passes to output
- SEL=00→d0, SEL=01→d1, SEL=10→d2, SEL=11→d3 (for 4-to-1)
"""
    elif "bbpd" in task_lower:
        return """
BBPD (Bang-Bang Phase Detector) basics:
- Used for clock/data recovery
- UP when data edge leads clock, DN when lags
"""
    elif "dac" in task_lower:
        return """
DAC (Digital-to-Analog) basics:
- Binary-weighted: each bit has different weight (1, 2, 4, 8...)
- Monotonic: increasing code → increasing output
"""
    elif "comparator" in task_lower or "cmp" in task_lower:
        return """
Comparator basics:
- Output HIGH when vinp > vinn (or threshold)
- Hysteresis: two thresholds (rising +vhys/2, falling -vhys/2)
"""
    elif "divider" in task_lower or "clk_div" in task_lower:
        return """
Clock Divider basics:
- Output frequency = input frequency / division_ratio
- Counter increments on each clock, output toggles at threshold
"""
    elif "sample_hold" in task_lower or "sample" in task_lower:
        return """
Sample-Hold basics:
- sample=HIGH: output tracks input
- sample=LOW: output holds last value
"""

    return ""


def _inject_skill_knowledge(task_id: str) -> list[str]:
    """Inject Skill circuit-specific knowledge for experiment condition C."""
    SKILL_REFS_DIR = ROOT.parent / "veriloga-skills" / "veriloga" / "references" / "categories"

    if not SKILL_REFS_DIR.exists():
        return []

    # 根据任务 ID 选择参考文档
    ref_mapping = {
        "pll": "pll-clock.md",
        "adpll": "pll-clock.md",
        "cppll": "pll-clock.md",
        "pfd": "pll-clock.md",
        "vco": "pll-clock.md",
        "mux": "digital-logic.md",
        "divider": "digital-logic.md",
        "clk_divider": "digital-logic.md",
        "counter": "digital-logic.md",
        "lfsr": "digital-logic.md",
        "prbs": "digital-logic.md",
        "digital": "digital-logic.md",
        "gate": "digital-logic.md",
        "dff": "digital-logic.md",
        "flip": "digital-logic.md",
        "dac": "dac.md",
        "dwa": "dac.md",
        "adc": "adc-sar.md",
        "sar": "adc-sar.md",
        "comparator": "comparator.md",
        "cmp": "comparator.md",
        "strongarm": "comparator.md",
        "hysteresis": "comparator.md",
        "sample_hold": "sample-hold.md",
        "sample": "sample-hold.md",
        "sampler": "sample-hold.md",
        "bbpd": "pll-clock.md",
        "filter": "amplifier-filter.md",
        "lpf": "amplifier-filter.md",
    }

    task_lower = task_id.lower()
    matched_ref = None
    for key, ref_file in ref_mapping.items():
        if key in task_lower:
            matched_ref = ref_file
            break

    if not matched_ref:
        return []

    ref_path = SKILL_REFS_DIR / matched_ref
    if not ref_path.exists():
        return []

    # 读取文档，截取前 3000 字符（避免过长）
    content = ref_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    filtered_lines = []
    for line in lines:
        filtered_lines.append(line)
        if len(filtered_lines) > 130:  # keep Spectre-safe patterns and DWA notes visible
            break

    filtered_content = "\n".join(filtered_lines)
    if len(filtered_content) > 4000:
        filtered_content = filtered_content[:4000] + "\n... (truncated)"

    return [
        "",
        "# Circuit-Specific Knowledge (from veriloga-skills)",
        "",
        f"Reference: `{matched_ref}`",
        "",
        "## Mandatory EVAS+Spectre Compile Contract",
        "",
        "- Treat the following skill notes as hard compile constraints.",
        "- Do not use runtime analog bus indexing such as `integer i; V(bus[i])`.",
        "- Use fixed bit indices for small input buses and `genvar` loops for output bus contributions.",
        "- Declare `genvar` at module scope before `analog begin`; never declare it inside `analog begin`.",
        "- Keep `@(cross(...))` as a top-level event statement; put reset/enable logic inside the event body.",
        "- Keep `transition()` contributions unconditional; compute target values first.",
        "",
        filtered_content,
    ]


# ---------------------------------------------------------------------------
# Code extraction from LLM response
# ---------------------------------------------------------------------------

# Match fenced code blocks with common Verilog-A and Spectre language tags
_VA_PATTERN = re.compile(
    r"```(?:verilog-a|verilog|va)\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)
_SCS_PATTERN = re.compile(
    r"```(?:spectre|scs|spice)\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)


def extract_code_blocks(response_text: str) -> dict[str, list[str]]:
    """Extract code blocks from LLM response. Returns {'va': [...], 'scs': [...]}."""
    va_blocks = [m.group(1).strip() for m in _VA_PATTERN.finditer(response_text)]
    scs_blocks = [m.group(1).strip() for m in _SCS_PATTERN.finditer(response_text)]
    return {"va": va_blocks, "scs": scs_blocks}


def infer_module_name(va_code: str) -> str:
    """Extract the module name from a Verilog-A code block."""
    m = re.search(r"\bmodule\s+(\w+)", va_code)
    return m.group(1) if m else "generated_module"


def infer_tb_name(scs_code: str) -> str:
    """Extract a testbench name from a Spectre code block (Cell name comment)."""
    m = re.search(r"Cell name:\s*(\S+)", scs_code)
    if m:
        return m.group(1)
    # Fallback: look for a recognizable tb_ name
    m = re.search(r"(tb_\w+)", scs_code)
    return m.group(1) if m else "tb_generated"


# ---------------------------------------------------------------------------
# LLM provider dispatch
# ---------------------------------------------------------------------------

# The Anthropic Python SDK appends /v1/messages to base_url, so omit /v1 here.
# Full constructed URL: https://coding.dashscope.aliyuncs.com/apps/anthropic/v1/messages
_BAILIAN_BASE_URL = "https://coding.dashscope.aliyuncs.com/apps/anthropic"
_BAILIAN_MODEL_PREFIXES = ("qwen", "glm", "kimi", "minimax")


def detect_provider(model: str) -> str:
    model_lower = model.lower()
    if model_lower.startswith("claude"):
        return "anthropic"
    if any(model_lower.startswith(p) for p in ("gpt-", "o1", "o3", "o4", "text-")):
        return "openai"
    if any(model_lower.startswith(p) for p in _BAILIAN_MODEL_PREFIXES):
        return "bailian"
    raise ValueError(
        f"Cannot auto-detect provider for model '{model}'. "
        "Model name should start with 'claude' (Anthropic), 'gpt-/o1/o3/o4' (OpenAI), "
        "or 'qwen/glm/kimi/minimax' (Bailian/DashScope)."
    )


def call_anthropic(model: str, system: str, user: str,
                   temperature: float, max_tokens: int) -> tuple[str, dict]:
    """Call Anthropic API. Returns (response_text, usage_dict)."""
    try:
        import anthropic  # type: ignore
    except ImportError:
        sys.exit("[generate] ERROR: 'anthropic' package not installed. Run: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("[generate] ERROR: ANTHROPIC_API_KEY not set.")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = message.content[0].text if message.content else ""
    usage = {
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
        "finish_reason": message.stop_reason,
    }
    return text, usage


def call_openai(model: str, system: str, user: str,
                temperature: float, max_tokens: int) -> tuple[str, dict]:
    """Call OpenAI API. Returns (response_text, usage_dict)."""
    try:
        import openai  # type: ignore
    except ImportError:
        sys.exit("[generate] ERROR: 'openai' package not installed. Run: pip install openai")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("[generate] ERROR: OPENAI_API_KEY not set.")

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    text = response.choices[0].message.content or ""
    usage_obj = response.usage
    usage = {
        "input_tokens": usage_obj.prompt_tokens if usage_obj else 0,
        "output_tokens": usage_obj.completion_tokens if usage_obj else 0,
        "finish_reason": response.choices[0].finish_reason,
    }
    return text, usage


def call_bailian(model: str, system: str, user: str,
                 temperature: float, max_tokens: int,
                 api_key: str | None = None) -> tuple[str, dict]:
    """Call Alibaba Cloud Bailian API via Anthropic SDK with custom base_url."""
    try:
        import anthropic  # type: ignore
    except ImportError:
        sys.exit("[generate] ERROR: 'anthropic' package not installed. Run: pip install anthropic")

    key = api_key or os.environ.get("BAILIAN_API_KEY")
    if not key:
        sys.exit("[generate] ERROR: BAILIAN_API_KEY not set and --bailian-api-key not provided.")

    client = anthropic.Anthropic(api_key=key, base_url=_BAILIAN_BASE_URL,
                                  timeout=300.0)  # 5-minute timeout per task
    # Bailian supports temperature only when > 0; clamp to avoid API rejection at exactly 0
    actual_temp = max(temperature, 0.0)
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=actual_temp,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    # Some models (e.g. glm-5) return a ThinkingBlock before the TextBlock;
    # iterate to find the first block with a .text attribute.
    text = ""
    for block in message.content:
        if hasattr(block, "text"):
            text = block.text
            break
    usage = {
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
        "finish_reason": message.stop_reason,
    }
    return text, usage


# Global override for Bailian API key (set by main() from --bailian-api-key arg)
_bailian_api_key_override: str | None = None


def call_model(model: str, prompt: str, temperature: float,
               top_p: float, max_tokens: int) -> tuple[str, dict]:
    provider = detect_provider(model)
    if provider == "anthropic":
        return call_anthropic(model, SYSTEM_PROMPT, prompt, temperature, max_tokens)
    elif provider == "openai":
        return call_openai(model, SYSTEM_PROMPT, prompt, temperature, max_tokens)
    elif provider == "bailian":
        return call_bailian(model, SYSTEM_PROMPT, prompt, temperature, max_tokens,
                            api_key=_bailian_api_key_override)
    raise ValueError(f"Unknown provider: {provider}")


# ---------------------------------------------------------------------------
# Per-task generation
# ---------------------------------------------------------------------------

def generate_one_task(
    task_id: str,
    task_dir: Path,
    output_root: Path,
    *,
    model: str,
    model_slug: str,
    sample_idx: int,
    temperature: float,
    top_p: float,
    max_tokens: int,
    dry_run: bool,
    include_checker: bool = False,
    include_skill: bool = False,
) -> dict:
    """Generate candidate(s) for one task. Returns generation_meta dict.

    Args:
        include_checker: If True, inject checker source code (experiment condition B)
        include_skill: If True, inject Skill circuit knowledge (experiment condition C)
    """
    meta = read_meta(task_dir)
    family = meta.get("family", "end-to-end")

    sample_dir = output_root / model_slug / task_id / f"sample_{sample_idx}"
    sample_dir.mkdir(parents=True, exist_ok=True)

    # Skip if already successfully generated (allows resuming interrupted runs)
    existing_meta_path = sample_dir / "generation_meta.json"
    if existing_meta_path.exists() and not dry_run:
        try:
            existing = json.loads(existing_meta_path.read_text(encoding="utf-8"))
            if existing.get("status") in ("generated", "no_code_extracted", "dry_run", "api_error"):
                return existing
        except Exception:
            pass

    prompt_text = build_prompt(task_dir, include_checker=include_checker, include_skill=include_skill)
    gen_meta_base = {
        "model": model,
        "model_slug": model_slug,
        "task_id": task_id,
        "family": family,
        "sample_idx": sample_idx,
        "temperature": temperature,
        "top_p": top_p,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "include_checker": include_checker,
        "include_skill": include_skill,
    }

    if dry_run:
        # Write placeholder files so score.py can be tested without real API calls
        placeholder_va = (
            "`include \"constants.vams\"\n`include \"disciplines.vams\"\n\n"
            f"// DRY-RUN placeholder for {task_id}\n"
            f"module {task_id}_placeholder(out);\n"
            "    output electrical out;\n"
            "    analog V(out) <+ 0.0;\n"
            "endmodule\n"
        )
        placeholder_scs = (
            "simulator lang=spectre\nglobal 0\n"
            f"// DRY-RUN placeholder testbench for {task_id}\n"
            f"I1 (0 out) {task_id}_placeholder\n"
            "tran tran stop=10n\n"
            f"ahdl_include \"./{task_id}_placeholder.va\"\n"
        )
        if family in ("spec-to-va", "bugfix", "end-to-end"):
            (sample_dir / f"{task_id}_placeholder.va").write_text(placeholder_va)
        if family in ("end-to-end", "tb-generation"):
            (sample_dir / f"tb_{task_id}_placeholder.scs").write_text(placeholder_scs)
        gen_meta = {**gen_meta_base, "status": "dry_run", "input_tokens": 0, "output_tokens": 0}
        (sample_dir / "generation_meta.json").write_text(json.dumps(gen_meta, indent=2))
        return gen_meta

    # Real LLM call
    try:
        response_text, usage = call_model(model, prompt_text, temperature, top_p, max_tokens)
    except Exception as exc:
        gen_meta = {
            **gen_meta_base,
            "status": "api_error",
            "error": str(exc)[:400],
            "input_tokens": 0,
            "output_tokens": 0,
        }
        (sample_dir / "generation_meta.json").write_text(json.dumps(gen_meta, indent=2))
        return gen_meta

    blocks = extract_code_blocks(response_text)

    va_blocks = blocks["va"]
    scs_blocks = blocks["scs"]

    # Determine module-name contract for this task.
    # - bugfix: file stem follows ahdl_include, module name follows XDUT
    # - spec-to-va: force single module name from ahdl_include
    # - end-to-end: force single module name only when gold tb includes one VA;
    #   for multi-module tasks, do not force-rename to one module.
    _expected_mod_name: str | None = None
    _bugfix_save_stem: str | None = None  # bugfix only: stem to save the .va as
    _force_single_module_name = False
    if family in ("spec-to-va", "bugfix", "end-to-end"):
        _gold_dir = task_dir / "gold"
        if _gold_dir.is_dir():
            _tbs = sorted(_gold_dir.glob("tb_*.scs"))
            if _tbs:
                _tb_text = _tbs[0].read_text(encoding="utf-8", errors="ignore")
                _entries = gold_include_entries(task_dir, _tb_text)
                if _entries:
                    if family == "bugfix":
                        # File must be saved as the ahdl_include name (e.g. dut_fixed.va).
                        _bugfix_save_stem = _entries[0]["stem"]
                        # Module inside must match XDUT (may differ from file stem).
                        _m_xdut = re.search(r'\bXDUT\s+\([^)]+\)\s+(\w+)', _tb_text)
                        _expected_mod_name = _m_xdut.group(1) if _m_xdut else _entries[0]["module"]
                    elif family == "spec-to-va":
                        _expected_mod_name = _entries[0]["module"]
                        _force_single_module_name = True
                    elif family == "end-to-end" and len(_entries) == 1:
                        _expected_mod_name = _entries[0]["module"]
                        _force_single_module_name = True

    saved_files = []
    if family in ("spec-to-va", "bugfix", "end-to-end") and va_blocks:
        if family == "bugfix" and _bugfix_save_stem is not None:
            # For bugfix tasks: save exactly one file as <ahdl_include_stem>.va.
            # Pick the block whose inferred module name matches _expected_mod_name
            # (the XDUT name), falling back to the first block if none match.
            # Never rename the module — score.py stages the file by copy, so the
            # module name inside must already be correct.
            best_block = va_blocks[0]
            for _blk in va_blocks:
                if _expected_mod_name and infer_module_name(_blk) == _expected_mod_name:
                    best_block = _blk
                    break
            va_path = sample_dir / f"{_bugfix_save_stem}.va"
            va_path.write_text(best_block, encoding="utf-8")
            saved_files.append(str(va_path))
        else:
            for va_code in va_blocks:
                module_name = infer_module_name(va_code)
                # Post-process: if the gold TB expects a specific module name and the
                # model used a different one, rename it in both the source text and the
                # output filename so that ahdl_include always finds the right module.
                if _force_single_module_name and _expected_mod_name and module_name != _expected_mod_name:
                    va_code = re.sub(
                        r'\bmodule\s+' + re.escape(module_name) + r'\b',
                        f'module {_expected_mod_name}',
                        va_code,
                    )
                    module_name = _expected_mod_name
                va_path = sample_dir / f"{module_name}.va"
                va_path.write_text(va_code, encoding="utf-8")
                saved_files.append(str(va_path))

    if family in ("end-to-end", "tb-generation") and scs_blocks:
        scs_code = scs_blocks[0]
        tb_name = infer_tb_name(scs_code)
        scs_path = sample_dir / f"{tb_name}.scs"
        scs_path.write_text(scs_code, encoding="utf-8")
        saved_files.append(str(scs_path))

    gen_meta = {
        **gen_meta_base,
        "status": "generated" if saved_files else "no_code_extracted",
        "saved_files": saved_files,
        "raw_response_length": len(response_text),
        **usage,
    }
    (sample_dir / "generation_meta.json").write_text(json.dumps(gen_meta, indent=2))

    if not saved_files:
        print(f"  WARNING: no code blocks extracted for {task_id}")

    return gen_meta


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate Verilog-A candidates for vaEvas benchmark tasks using an LLM."
    )
    ap.add_argument("--model", required=True,
                    help="Model name, e.g. claude-sonnet-4-6 or gpt-4o")
    ap.add_argument("--output-dir", default="generated",
                    help="Root output directory. Default: generated/")
    ap.add_argument("--task", action="append", default=[],
                    help="Generate only these task_ids (repeatable). Omit for all.")
    ap.add_argument("--family", action="append", choices=list(ALL_FAMILIES),
                    help="Limit to these families. Omit for all.")
    ap.add_argument("--sample-idx", type=int, default=0,
                    help="Sample index (0 = deterministic Pass@1). Default: 0")
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="Sampling temperature. Default: 0.0 (deterministic)")
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=4096,
                    help="Max output tokens per task. Default: 4096")
    ap.add_argument("--dry-run", action="store_true",
                    help="Write placeholder files without calling any API.")
    ap.add_argument("--bailian-api-key", default="",
                    help="Bailian/DashScope API key. Overrides BAILIAN_API_KEY env var.")
    ap.add_argument("--include-checker", action="store_true",
                    help="Inject checker source code (Experiment condition B: +Checker)")
    ap.add_argument("--include-skill", action="store_true",
                    help="Inject Skill circuit knowledge (Experiment condition C: +Skill)")
    ap.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Max parallel generation workers. Use 1 to force serial mode.",
    )
    args = ap.parse_args()

    model_slug = args.model.replace("/", "_")
    out_root = Path(args.output_dir)
    if not out_root.is_absolute():
        out_root = ROOT / out_root

    # Validate provider + API key before starting (unless dry-run)
    if not args.dry_run:
        try:
            provider = detect_provider(args.model)
        except ValueError as e:
            print(f"[generate] ERROR: {e}")
            return 1
        if provider == "anthropic":
            if not os.environ.get("ANTHROPIC_API_KEY"):
                print("[generate] ERROR: ANTHROPIC_API_KEY is not set.")
                return 1
        elif provider == "openai":
            if not os.environ.get("OPENAI_API_KEY"):
                print("[generate] ERROR: OPENAI_API_KEY is not set.")
                return 1
        elif provider == "bailian":
            key = args.bailian_api_key or os.environ.get("BAILIAN_API_KEY", "")
            if not key:
                print("[generate] ERROR: BAILIAN_API_KEY is not set and --bailian-api-key not provided.")
                return 1
            # Store for use by call_model()
            global _bailian_api_key_override
            _bailian_api_key_override = key

    families = tuple(args.family) if args.family else ALL_FAMILIES
    selected = set(args.task) if args.task else None
    task_list = list_task_dirs(families=families, selected=selected)

    if not task_list:
        print("[generate] No tasks found.")
        return 1

    print(f"[generate] model={args.model}  tasks={len(task_list)}"
          f"  temp={args.temperature}  sample={args.sample_idx}"
          f"  checker={args.include_checker}  skill={args.include_skill}"
          f"  dry_run={args.dry_run}  workers={args.max_workers}")

    total_input_tokens = 0
    total_output_tokens = 0

    if args.max_workers <= 1:
        for task_id, task_dir in task_list:
            print(f"  {task_id} ...", end=" ", flush=True)
            gen_meta = generate_one_task(
                task_id, task_dir, out_root,
                model=args.model,
                model_slug=model_slug,
                sample_idx=args.sample_idx,
                temperature=args.temperature,
                top_p=args.top_p,
                max_tokens=args.max_tokens,
                dry_run=args.dry_run,
                include_checker=args.include_checker,
                include_skill=args.include_skill,
            )
            status = gen_meta.get("status", "?")
            out_tok = int(gen_meta.get("output_tokens", 0) or 0)
            total_input_tokens += int(gen_meta.get("input_tokens", 0) or 0)
            total_output_tokens += out_tok
            suffix = f"  ERROR: {gen_meta.get('error','')[:80]}" if status == "api_error" else ""
            print(f"{status}  ({out_tok} out_tokens){suffix}")
    else:
        worker_count = min(args.max_workers, len(task_list))
        print(f"[generate] parallel dispatch with {worker_count} workers")

        def _run_one(item: tuple[str, Path]) -> tuple[str, dict]:
            task_id, task_dir = item
            gen_meta = generate_one_task(
                task_id, task_dir, out_root,
                model=args.model,
                model_slug=model_slug,
                sample_idx=args.sample_idx,
                temperature=args.temperature,
                top_p=args.top_p,
                max_tokens=args.max_tokens,
                dry_run=args.dry_run,
                include_checker=args.include_checker,
                include_skill=args.include_skill,
            )
            return task_id, gen_meta

        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as ex:
            futs = [ex.submit(_run_one, item) for item in task_list]
            for fut in concurrent.futures.as_completed(futs):
                task_id, gen_meta = fut.result()
                status = gen_meta.get("status", "?")
                out_tok = int(gen_meta.get("output_tokens", 0) or 0)
                total_input_tokens += int(gen_meta.get("input_tokens", 0) or 0)
                total_output_tokens += out_tok
                suffix = f"  ERROR: {gen_meta.get('error','')[:80]}" if status == "api_error" else ""
                print(f"  {task_id} ... {status}  ({out_tok} out_tokens){suffix}")

    print(f"\n[generate] done  total_in={total_input_tokens}  total_out={total_output_tokens}")
    print(f"  output: {out_root / model_slug}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
