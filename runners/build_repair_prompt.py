#!/usr/bin/env python3
"""Build matched-budget retry/repair prompts for model-assisted experiments.

The module is intentionally side-effect light: it reads the frozen task prompt,
the previous candidate artifacts, and optionally an EVAS result, then emits a
single prompt.  API keys are never read here.
"""
from __future__ import annotations

import argparse
import json
import re
import textwrap
from pathlib import Path

from generate import build_prompt, read_meta, extract_module_signature
from score import find_tb_file, find_va_file
from diagnosis_translation import translate_diagnosis, format_repair_section
from extract_expected_values import extract_expected_values, format_expected_for_prompt, get_checker_name_for_task

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SKILL_BUNDLE = ROOT / "docs" / "TABLE2_VERILOGA_SKILL_BUNDLE.md"
SKILL_REFS_DIR = ROOT.parent / "veriloga-skills" / "veriloga" / "references" / "categories"
_METRIC_TOKEN_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=([^\s,;]+)")
_NUMERIC_TOKEN_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$", re.IGNORECASE)


def _get_gold_tran_params(task_dir: Path) -> str | None:
    """Read the tran statement from the gold testbench and return it as a string."""
    try:
        gold_dir = task_dir / "gold"
        tbs = sorted(gold_dir.glob("tb*.scs"))
        if not tbs:
            return None
        text = tbs[0].read_text(encoding="utf-8")
        m = re.search(r'\btran\s+\w+\s+(.+)', text)
        return m.group(1).strip() if m else None
    except Exception:
        return None


def _extract_checker_required_columns(task_id: str) -> list[str]:
    """Extract required CSV column names from the checker's issubset call in simulate_evas.py.

    Looks up the checker function name via the CHECKS dict, then finds its issubset call.
    """
    try:
        sim_path = Path(__file__).parent / "simulate_evas.py"
        src = sim_path.read_text(encoding="utf-8")

        # Find what checker function this task_id maps to in CHECKS dict
        checks_match = re.search(
            rf'"{re.escape(task_id)}"\s*:\s*(check_\w+)', src
        )
        if not checks_match:
            return []
        checker_name = checks_match.group(1)

        # Find the function definition and extract its issubset call
        func_match = re.search(rf"def {re.escape(checker_name)}\s*\(", src)
        if not func_match:
            return []
        after_func = src[func_match.start():func_match.start() + 2000]
        issubset_match = re.search(r"not \{([^}]+)\}\.issubset\(rows\[0\]\)", after_func)
        if not issubset_match:
            return []
        return re.findall(r'"([^"]+)"', issubset_match.group(1))
    except Exception:
        return []


def _inject_skill_reference(task_id: str) -> list[str]:
    """根据任务类型，注入 Skill 中对应的电路原理文档片段"""
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
    # 只取原理说明部分，去掉代码示例的详细内容
    lines = content.splitlines()
    filtered_lines = []
    for line in lines:
        filtered_lines.append(line)
        if len(filtered_lines) > 80:  # 限制行数
            break

    filtered_content = "\n".join(filtered_lines)
    if len(filtered_content) > 2500:
        filtered_content = filtered_content[:2500] + "\n... (truncated)"

    return [
        "",
        "# Circuit-Specific Knowledge (from veriloga-skills)",
        "",
        f"Reference: `{matched_ref}`",
        "",
        filtered_content,
    ]


def _inject_check_expectations(task_dir: Path) -> list[str]:
    """直接传完整Checker源码给闭环AI，让它自己分析期望值"""
    # 获取 task_id
    meta_path = task_dir / "meta.json"
    task_id = ""
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            task_id = meta.get("task_id", meta.get("id", task_dir.name))
        except Exception:
            task_id = task_dir.name

    if not task_id:
        task_id = task_dir.name

    # 获取对应的 checker 函数名
    checker_name = get_checker_name_for_task(task_id)

    # 提取完整 checker 源码
    source = _extract_checker_source(checker_name)
    if not source:
        return []

    # 添加电路知识补充
    circuit_context = _get_circuit_context(task_id)

    # 直接传完整源码
    lines = [
        "",
        "# Checker Function (评分标准)",
        "",
        "以下是 evaluate your generated circuit 的 checker 函数源码。",
        "它定义了期望的电路行为（评分标准），不包含具体实现方案。",
        "",
        "请仔细阅读 checker 源码，理解期望的行为条件，然后修复你的代码使其满足这些条件。",
        "",
        "```python",
        source,
        "```",
    ]

    if circuit_context:
        lines.extend(["", "# Circuit Context", "", circuit_context])

    return lines


def _extract_checker_source(checker_name: str) -> Optional[str]:
    """从 simulate_evas.py 提取完整 checker 函数源码"""
    import re
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


def get_checker_name_for_task(task_id: str) -> str:
    """根据 task_id 确定对应的 checker 函数名"""
    # 特殊映射（部分任务名和checker名不一致）
    special_mapping = {
        "digital_basics_smoke": "check_not_gate",
        "adpll_timer": "check_adpll_lock",
        "adpll_timer_smoke": "check_adpll_lock",
    }

    if task_id in special_mapping:
        return special_mapping[task_id]

    # 默认规则：check_<base_task_id>
    base = task_id.replace("_smoke", "")
    return f"check_{base}"


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


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_block(path: Path) -> str:
    suffix = path.suffix.lower()
    lang = "spectre" if suffix == ".scs" else "verilog-a"
    return f"### {path.name}\n\n```{lang}\n{path.read_text(encoding='utf-8', errors='ignore').strip()}\n```"


def _gold_dut_port_order_hints(task_dir: Path, notes: list[str]) -> list[str]:
    gold_dir = task_dir / "gold"
    if not gold_dir.is_dir():
        return []

    for note in notes:
        match = re.search(r"gold_dut_alias=([^;\s]+\.va)->([^;\s]+\.va)", note)
        if not match:
            continue
        gold_va_name = Path(match.group(1)).name
        staged_va_name = Path(match.group(2)).name
        gold_va_path = gold_dir / gold_va_name
        if not gold_va_path.exists():
            continue
        signature = extract_module_signature(gold_va_path)
        if not signature:
            continue
        module_name, ports = signature
        port_list = ", ".join(ports)
        return [
            "",
            "Gold DUT interface contract:",
            f"- EVAS mapped Gold DUT `{gold_va_name}` to testbench include `{staged_va_name}`.",
            f"- Gold DUT module name: `{module_name}`",
            f"- Gold DUT positional port order: `({port_list})`",
            f"- Instantiate exactly as: `XDUT ({port_list}) {module_name}`",
        ]
    return []


def _artifact_contract(family: str) -> str:
    if family in ("spec-to-va", "bugfix"):
        return (
            "Return exactly one complete Verilog-A DUT file in a fenced "
            "`verilog-a` code block. Do not return a testbench."
        )
    if family == "tb-generation":
        return (
            "Return exactly one complete Spectre testbench in a fenced "
            "`spectre` code block. Do not return a DUT."
        )
    return (
        "Return the complete DUT artifact set required by the task: one or "
        "more Verilog-A DUT files in separate `verilog-a` code blocks as "
        "needed, followed by exactly one complete Spectre testbench in a "
        "`spectre` code block. Do not omit an unchanged file."
    )


def _end_to_end_shape_guidance(task_prompt: str, family: str) -> str:
    if family != "end-to-end":
        return ""
    guidance = [
        "End-to-end shape requirements:",
        "- The final answer may contain multiple `verilog-a` code blocks if the task asks for multiple modules.",
        "- Output exactly one complete top-level `spectre` testbench block.",
        "- Do not concatenate several standalone mini-testbenches into one `.scs` file.",
        "- Put shared directives such as `simulator`, `global`, `save`, and `tran` in the single final testbench, not repeated per sub-block.",
        "- Every `ahdl_include` used by the testbench must correspond to a DUT file you emitted in this same answer.",
    ]
    lowered = task_prompt.lower()
    if "separate modules" in lowered or "implement four" in lowered or "implement two" in lowered:
        guidance.extend([
            "- This task explicitly asks for multiple DUT modules.",
            "- Emit one complete `verilog-a` block per requested module before the single `spectre` block.",
        ])
    return "\n".join(guidance)


def load_skill_bundle(path: Path | None = None) -> str:
    bundle_path = path or DEFAULT_SKILL_BUNDLE
    return bundle_path.read_text(encoding="utf-8").strip()


def _skill_section(skill_bundle_text: str | None) -> str:
    if not skill_bundle_text:
        return ""
    return textwrap.dedent(f"""\
        # Frozen Skill Bundle

        {skill_bundle_text.strip()}
    """).strip()


def _candidate_sections(sample_dir: Path) -> list[str]:
    sections: list[str] = []
    for va_path in sorted(sample_dir.glob("*.va")):
        sections.append(_file_block(va_path))
    tb_path = find_tb_file(sample_dir)
    if tb_path:
        sections.append(_file_block(tb_path))
    if not sections:
        sections.append("No previous candidate files were found.")
    return sections


def _score_summary(evas_result: dict) -> str:
    scores = evas_result.get("scores", {})
    # Include both evas_notes and spectre_notes (for Spectre backend results)
    notes = evas_result.get("evas_notes") or evas_result.get("notes") or []
    spectre_notes = evas_result.get("spectre_notes", [])
    all_notes = notes + [n for n in spectre_notes if n not in notes]
    note_text = "\n".join(f"- {note}" for note in all_notes[:20]) or "- <none>"
    required = ", ".join(evas_result.get("required_axes", [])) or "<unknown>"

    # Add structure diagnosis summary
    diag = evas_result.get("structure_diagnosis")
    diag_text = ""
    if diag:
        mismatch = diag.get("mismatch_detail", [])
        if mismatch:
            diag_text = "\n\nStructure mismatch:\n" + "\n".join(f"- {d}" for d in mismatch)

    return textwrap.dedent(f"""\
        EVAS status: {evas_result.get("status", "<unknown>")}
        Required axes: {required}
        Scores:
        - dut_compile: {scores.get("dut_compile", "<missing>")}
        - tb_compile: {scores.get("tb_compile", "<missing>")}
        - sim_correct: {scores.get("sim_correct", "<missing>")}
        - weighted_total: {scores.get("weighted_total", "<missing>")}

        EVAS notes:
        {note_text}{diag_text}
    """)


def _parse_metric_token(token: str) -> float | bool | str:
    cleaned = token.strip().strip("`")
    lowered = cleaned.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if _NUMERIC_TOKEN_RE.match(cleaned):
        try:
            return float(cleaned)
        except ValueError:
            pass
    return cleaned


def _extract_metrics_from_notes(notes: list[str]) -> dict[str, float | bool | str]:
    metrics: dict[str, float | bool | str] = {}
    for note in notes:
        for key, raw_value in _METRIC_TOKEN_RE.findall(note):
            metrics[key] = _parse_metric_token(raw_value)
    return metrics


def _format_scalar(value: float | bool | str) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (int, float)):
        return f"{float(value):.4g}"
    return str(value)


def _checker_expectation_bundle(task_dir: Path) -> dict:
    meta = read_meta(task_dir)
    task_id = meta.get("task_id", meta.get("id", task_dir.name))
    checker_name = get_checker_name_for_task(task_id)
    extracted = extract_expected_values(checker_name)
    if extracted.get("error"):
        return {"checker_name": checker_name, "expected_conditions": {}, "semantic_hints": []}
    return {
        "checker_name": checker_name,
        "expected_conditions": extracted.get("expected_conditions", {}),
        "semantic_hints": extracted.get("semantic_hints", []),
        "formatted_lines": format_expected_for_prompt(extracted),
    }


def _threshold_spec(spec: str) -> tuple[str, float] | None:
    match = re.match(r"^(>=|<=|>|<)\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)$", spec.strip(), re.IGNORECASE)
    if not match:
        return None
    try:
        return match.group(1), float(match.group(2))
    except ValueError:
        return None


def _metric_gap_line(name: str, actual: float | bool | str, spec: dict) -> tuple[bool, str] | None:
    if not isinstance(actual, (int, float)):
        return None
    actual_value = float(actual)
    target = spec.get("expected")
    tolerance = spec.get("tolerance")
    if isinstance(target, (int, float)) and isinstance(tolerance, (int, float)):
        target_value = float(target)
        tolerance_value = float(tolerance)
        deviation = abs(actual_value - target_value)
        ok = deviation <= tolerance_value
        detail = (
            f"`{name}` expected {target_value:.4g} +/- {tolerance_value:.4g}, "
            f"actual {actual_value:.4g} -> {'OK' if ok else f'ERROR (off by {deviation:.4g})'}"
        )
        return ok, detail
    if isinstance(target, str):
        parsed = _threshold_spec(target)
        if not parsed:
            return None
        op, threshold = parsed
        if op == ">=":
            ok = actual_value >= threshold
        elif op == "<=":
            ok = actual_value <= threshold
        elif op == ">":
            ok = actual_value > threshold
        else:
            ok = actual_value < threshold
        gap = abs(actual_value - threshold)
        detail = (
            f"`{name}` expected {target}, actual {actual_value:.4g} -> "
            f"{'OK' if ok else f'ERROR (gap {gap:.4g})'}"
        )
        return ok, detail
    return None


def _expected_vs_actual_lines(
    metrics: dict[str, float | bool | str],
    expected_conditions: dict,
) -> tuple[list[str], list[str]]:
    already_good: list[str] = []
    remaining_gaps: list[str] = []
    for metric_name, spec in expected_conditions.items():
        if metric_name not in metrics:
            continue
        comparison = _metric_gap_line(metric_name, metrics[metric_name], spec)
        if comparison is None:
            continue
        ok, detail = comparison
        if ok:
            already_good.append(f"- {detail}")
        else:
            remaining_gaps.append(f"- {detail}")
    return already_good, remaining_gaps


def _loop_state_section(
    task_dir: Path,
    evas_result: dict,
    history: list[dict],
    loop_context: dict | None,
) -> str:
    if not history and not loop_context:
        return ""

    bundle = _checker_expectation_bundle(task_dir)
    metrics = _extract_metrics_from_notes(evas_result.get("evas_notes", []))
    expected_conditions = bundle.get("expected_conditions", {})
    already_good, remaining_gaps = _expected_vs_actual_lines(metrics, expected_conditions)

    lines = ["# EVAS Loop State", ""]
    if loop_context:
        anchor = loop_context.get("repair_from_label", "baseline")
        best_status = loop_context.get("best_status", "<unknown>")
        best_scores = loop_context.get("best_scores", {})
        lines.append(
            f"- Start this round from the best-so-far candidate: `{anchor}` "
            f"(status={best_status}, weighted_total={float(best_scores.get('weighted_total', 0.0)):.3f})."
        )
        last_transition = loop_context.get("last_transition_summary")
        if last_transition:
            lines.append(f"- Last loop diagnosis: {last_transition}")

        transition_policy = loop_context.get("last_transition")
        if transition_policy == "regressed":
            lines.extend([
                "- Policy for this round: continue from the best-so-far candidate, not from the latest regressed edit.",
                "- Preserve the EVAS behaviors that were already working before the regression.",
            ])
        elif transition_policy == "stalled":
            lines.extend([
                "- Policy for this round: the previous edit did not move EVAS; use a different repair mechanism.",
                "- Avoid cosmetic rewrites that preserve the same failing measurements.",
            ])
        elif transition_policy == "oscillating":
            lines.extend([
                "- Policy for this round: stop toggling interface/testbench details.",
                "- Keep the working file contract fixed and repair the remaining semantic bug from the best-so-far candidate.",
            ])
        elif transition_policy == "improved":
            lines.extend([
                "- Policy for this round: preserve the behavior that improved in the best-so-far candidate.",
                "- Change only the remaining failing logic exposed by EVAS.",
            ])

    if bundle.get("formatted_lines"):
        lines.extend(["", "# Checker Targets"])
        lines.extend(bundle["formatted_lines"])

    if already_good:
        lines.extend(["", "Metrics already consistent with the checker:"])
        lines.extend(already_good[:5])
        lines.append("- Do NOT modify the logic responsible for the metrics above unless EVAS proves they regressed.")

    if remaining_gaps:
        lines.extend(["", "Metrics still failing against the checker:"])
        lines.extend(remaining_gaps[:6])
        lines.append("- Focus the next edit on the failing metrics above; treat them as the EVAS optimization target.")

    semantic_hints = bundle.get("semantic_hints", [])
    if semantic_hints and not remaining_gaps:
        lines.extend(["", "Checker hints still relevant for this repair:"])
        for hint in semantic_hints[:4]:
            lines.append(f"- {hint}")

    return "\n".join(lines)


def _targeted_repair_skill(task_dir: Path, evas_result: dict, include_skill: bool = True) -> str:
    meta = read_meta(task_dir)
    family = meta.get("family", "end-to-end")
    task_prompt = build_prompt(task_dir)
    task_id = meta.get("task_id", meta.get("id", ""))
    status = evas_result.get("status", "FAIL_OTHER")
    # Include both evas_notes and spectre_notes (for Spectre backend results)
    notes = evas_result.get("evas_notes") or evas_result.get("notes") or []
    spectre_notes = evas_result.get("spectre_notes", [])
    notes = notes + [n for n in spectre_notes if n not in notes]

    lines = [
        "# EVAS-Guided Repair Skill",
        "",
        "Use only the repair rules relevant to the reported EVAS failure.",
        "Keep the original task contract fixed while repairing the candidate.",
    ]

    if family == "end-to-end":
        tran_params = _get_gold_tran_params(task_dir)
        tran_hint = (
            f"- **Use exactly this tran statement (from the reference design): `tran tran {tran_params}`**"
            if tran_params else
            "- Use a single `tran` analysis: stop time 5u~20u for PLL/slow circuits, 100n~2u for digital; maxstep at least 1n."
        )
        lines.extend([
            "",
            "End-to-end repair contract:",
            "- Return the full DUT artifact set required by the task plus exactly one top-level Spectre testbench.",
            "- Do not split the answer into several independent testbenches.",
            "- **DUT-TB filename consistency (critical):** The `ahdl_include` path in the TB must exactly match",
            "  the filename of your generated DUT. The DUT file is saved as `<module_name>.va` where",
            "  `<module_name>` is the identifier after the `module` keyword in your Verilog-A file.",
            "  Example: if your DUT declares `module lfsr(...)`, the file is `lfsr.va` and the TB must have",
            "  `ahdl_include \"lfsr.va\"` — not `./lfsr31_v.va` or any other name.",
            tran_hint,
            "- **NEVER set maxstep smaller than 1n** unless the gold reference uses a smaller value — tiny maxstep causes simulation timeout.",
            "- Do not use bare `errpreset=conservative` without an explicit `maxstep`.",
        ])

    if status == "FAIL_DUT_COMPILE":
        lines.extend([
            "",
            "Targeted DUT repair rules:",
            "- Preserve the exact module name expected by the task and any referenced testbench include.",
            "- **Port order convention: VDD/VSS first, then signal ports.**",
            "  - Example NOT gate: `module not_gate (inout VDD, inout VSS, input A, output Y);`",
            "  - Example DFF: `module dff_rst (inout VDD, inout VSS, input D, input CLK, input RST, output Q, output QB);`",
            "- Preserve port order exactly; do not silently reorder or rename interface pins.",
            "- **Do NOT re-declare ports after ANSI-style header.**",
            "  - Wrong: `module foo (input A, output Y); electrical A, Y;`",
            "  - Correct: `module foo (input electrical A, output electrical Y);`",
            "- Use voltage-domain Verilog-A only: `V() <+`, `transition`, `cross`, `timer`, `initial_step`.",
            "- Do not use `I()`, `ddt`, `idt`, `idtmod`, `laplace_*`, or plain Verilog `initial begin`.",
            "- Keep declarations at module scope and use `electrical` on signal ports.",
            "- For power rails, use `inout`, not plain `input`.",
            "- Prefer the smallest interface-preserving repair that resolves compile/linkage issues.",
            "",
            "## Verilog-A Mandatory Syntax Rules (Spectre VACOMP strict)",
            "",
            "These rules come from a curated library of 1,638 real Verilog-A designs.",
            "Violating any rule causes Spectre VACOMP to reject the file.",
            "",
            "**Rule 1 — Signal types: use `electrical`, never `reg`/`wire`/`logic`**",
            "- All ports and internal nets must use `electrical` (or `integer`/`real` for scalars).",
            "- `reg` does not exist in Verilog-A. Replace every `reg` with `integer`.",
            "  ```",
            "  // WRONG (SystemVerilog):  reg cnt_reg; reg lock;",
            "  // CORRECT (Verilog-A):   integer cnt_reg; integer lock;",
            "  ```",
            "",
            "**Rule 2 — No packed bit-select on `integer` variables**",
            "- Verilog-A has no packed arrays on scalar integers.",
            "- `x[0] = 1` is invalid when `x` is declared as `integer`.",
            "- To read individual bits from an electrical bus, unroll port-by-port:",
            "  ```",
            "  // WRONG:  div_val[0] = (V(d[0]) > vth) ? 1 : 0;",
            "  // CORRECT: integer b; div_val = 0;",
            "  //   if (V(d[0]) > vth) div_val = div_val + 1;",
            "  //   if (V(d[1]) > vth) div_val = div_val + 2;",
            "  //   if (V(d[2]) > vth) div_val = div_val + 4;",
            "  ```",
            "",
            "**Rule 3 — Edge detection: use `@(cross())`, not `always @`**",
            "- Rising edge: `@(cross(V(clk) - vth, +1))`",
            "- Falling edge: `@(cross(V(clk) - vth, -1))`",
            "- `always @(posedge clk)` does not exist in Verilog-A.",
            "",
            "**Rule 4 — All declarations at module scope, before `analog begin`**",
            "- `integer`, `real`, `parameter`, `genvar` must come before `analog begin`.",
            "",
            "**Rule 5 — Outputs use `transition()` with a discrete target variable**",
            "  ```",
            "  real out_target;",
            "  out_target = state ? vh : vl;",
            "  V(out_o) <+ transition(out_target, 0, tr, tf);",
            "  ```",
            "",
            "**Rule 6 — Initialize state in `@(initial_step)`**",
            "  ```",
            "  @(initial_step) begin",
            "      cnt = 0; state = 0; lock = 0;",
            "  end",
            "  ```",
        ])
    elif status == "FAIL_TB_COMPILE":
        lines.extend([
            "",
            "Targeted testbench repair rules:",
            "- Write a single top-level Spectre testbench, not several stitched mini-netlists.",
            "- Use `simulator lang=spectre` when the file uses Spectre directives such as `ahdl_include`, `save`, and `tran`.",
            "- Do not place `ahdl_include` or `save` in a spice-language section.",
            "- **Do NOT use colon-instance syntax in save statements** (e.g., `and_dut:A` is invalid).",
            "- Use plain signal names in save statements: `save a b y` not `save X1:A X1:B X1:Y`.",
            "- Match DUT instance module names and port order exactly to the emitted DUT modules.",
            "- Keep the save list aligned with the task-required observables.",
            "- Use a single `tran` statement: `tran tran stop=200n maxstep=5n`.",
            "- Use only `vsource` elements for stimulus (type=pulse or type=pwl). Do NOT use `vcvs`, `ccvs`, `capacitor`, or `resistor` unless the task explicitly requires them.",
            "- Write a single `tran` analysis. Do NOT add `dc` sweep or `ac` analysis.",
            "- In `save` statements, use plain signal names only: `save clk vin vout`. Do NOT use `XDUT:signal` colon syntax.",
            "- Add `global 0` on the line after `simulator lang=spectre`.",
            "- `ahdl_include` must be the absolute LAST line in the netlist.",
        ])
        lines.extend(_gold_dut_port_order_hints(task_dir, notes))
    elif status == "FAIL_SIM_CORRECTNESS":
        lines.extend([
            "",
            "Targeted behavioral repair rules:",
            "- Preserve interface and testbench structure; focus on semantics rather than broad rewrites.",
            "- Check threshold choice, edge direction, reset priority, initialization, and output complement rules.",
            "- Ensure the testbench stimulates and saves every signal required by the checker.",
            "- If the DUT is edge-driven, prefer explicit `@(cross(..., dir))` with correct direction.",
            "- If the output uses `transition`, drive a target variable continuously rather than embedding unstable expressions.",
            "- **For multi-module tasks, use module prefix in signal names**:",
            "  - NOT gate signals: `not_a`, `not_y` (or `a`, `y` if single module)",
            "  - AND gate signals: `and_a`, `and_b`, `and_y`",
            "  - DFF signals: `dff_d`, `dff_clk`, `dff_q`, `dff_qb`",
            "- **Instance syntax: use positional port order, not named ports**:",
            "  - Correct: `I_not (vdd vss a y) not_gate`",
            "  - Wrong: `I_not not_gate A=a VDD=vdd VSS=vss Y=y` (named port syntax may not work)",
        ])
    elif status == "FAIL_INFRA":
        # Parse what's actually missing from the notes
        missing_files: list[str] = []
        for note in notes:
            if note.startswith("missing_generated_files:"):
                files_str = note[len("missing_generated_files:"):].strip()
                missing_files.extend([f.strip() for f in files_str.split(",") if f.strip()])

        if missing_files:
            missing_list = ", ".join(f"`{f}`" for f in missing_files)
            lines.extend([
                "",
                f"FAIL_INFRA: EVAS could not evaluate your submission because the following required files were not generated: {missing_list}",
                "",
                "Required action:",
            ])
            if any(f.endswith(".scs") for f in missing_files):
                lines.extend([
                    "- **You must generate a complete Spectre testbench** (`.scs` file) in addition to the DUT.",
                    "- The testbench must include `ahdl_include` for your DUT, stimulus sources, save directives, and a `tran` analysis.",
                    "- Both your DUT Verilog-A file(s) and the testbench must be present in this response.",
                    "- Do not return only the DUT — the testbench is required to evaluate correctness.",
                ])
            if any(f.endswith(".va") for f in missing_files):
                lines.extend([
                    f"- **You must generate the missing DUT Verilog-A file(s)**: {missing_list}",
                    "- Ensure the module name and port list exactly match what the testbench expects.",
                ])
        else:
            lines.extend([
                "",
                "FAIL_INFRA: EVAS could not evaluate your submission due to missing or unreadable artifacts.",
                "- Ensure you return ALL required files: DUT Verilog-A file(s) and Spectre testbench (if required by the task).",
                "- Each code block must be complete and syntactically correct so EVAS can extract it.",
                "- Do not truncate code blocks or mix multiple files into one block.",
            ])
    else:
        lines.extend([
            "",
            "Generic repair rules:",
            "- Preserve artifact shape and interface contract first.",
            "- Repair malformed code blocks, missing files, or obvious compatibility problems before changing behavior.",
        ])

    # Compile-related hints (keep existing)
    note_hints: list[str] = []
    for note in notes:
        if "undefined_module=" in note:
            import re as _re
            # undefined_module = what the TB is searching for (the NEEDED name)
            # available_modules = what the LLM provided (the WRONG name it used)
            _m_needed = _re.search(r"undefined_module=([^;]+)", note)
            _m_provided = _re.search(r"available_modules=([^;\s]+)", note)
            _needed = _m_needed.group(1).split(",")[0].strip() if _m_needed else None
            _provided = _m_provided.group(1).split(",")[0].strip() if _m_provided else None
            if _needed and _provided and _needed != _provided:
                note_hints.extend([
                    f"- **CRITICAL MODULE NAME ERROR.** Your code declares `module {_provided}` but the testbench expects `module {_needed}`.",
                    f"- **The ONLY fix required: change the single line `module {_provided}(` to `module {_needed}(`. Do not alter any other code.**",
                    f"- **Do NOT output a file named `{_needed}.va`. Output exactly one `verilog-a` code block containing `module {_needed}(...)`.**",
                ])
            else:
                note_hints.append("- EVAS saw an undefined module mismatch: make the declared module name exactly match what the testbench instantiates.")
        if "colon_instance_syntax_lines=" in note:
            note_hints.extend([
                "- **CRITICAL: Colon-instance syntax detected**. Spectre rejects this pattern.",
                "- Replace `save X1:A X1:B X1:Y` with plain signal names: `save a b y`.",
            ])
        if "conditional_transition=" in note:
            note_hints.extend([
                "- **CRITICAL: Conditional transition pattern detected**. Spectre rejects this.",
                "- Use: `target = condition ? high : low; V(out) <+ transition(target, ...);`",
            ])
        if "no_ahdl_va_include_in_tb" in note:
            note_hints.append("- The current testbench does not properly include the DUT: add explicit `ahdl_include` lines.")
        if note.startswith("missing ") or "missing_" in note:
            # Try to inject exact checker-required column names for end-to-end tasks
            required_cols = _extract_checker_required_columns(task_id) if family == "end-to-end" else []
            if required_cols:
                save_stmt = " ".join(required_cols)
                note_hints.extend([
                    f"- **CRITICAL: Checker expects these exact lowercase column names in tran.csv: `{save_stmt}`**",
                    f"- Your testbench `save` statement must use exactly: `save {save_stmt}`",
                    "- Do NOT use uppercase (e.g. `DIN3`, `AOUT`) — the checker uses case-sensitive string matching.",
                ])
            else:
                note_hints.append("- EVAS reported missing required observables or files.")
        if "digital_verilog_syntax" in note:
            issue = note.split("digital_verilog_syntax=")[-1].split(" in ")[0] if "digital_verilog_syntax=" in note else note
            if "sv_param_header" in issue:
                note_hints.extend([
                    "- **CRITICAL: SystemVerilog parameterized header detected** (`module foo #(...)`). Spectre VACOMP rejects this.",
                    "- Fix: declare parameters inside the module body with `parameter real/integer name = value;`",
                    "- Correct: `module foo(port_a, port_b); parameter integer div = 4;`",
                ])
            if "digital_reg_decl" in issue:
                note_hints.extend([
                    "- **CRITICAL: `reg` keyword detected**. Verilog-A has no `reg` type — Spectre VACOMP rejects it.",
                    "- Fix: replace every `reg` variable with `integer` (for counters/flags/state) or `real` (for analog values).",
                    "  - Before: `reg clk_out_reg; reg lock_reg;`",
                    "  - After:  `integer clk_out_reg; integer lock_reg;`",
                ])
            if "digital_always_block" in issue:
                note_hints.extend([
                    "- **CRITICAL: `always @(` block detected**. Verilog-A uses `analog begin` with `@(cross(...))` events.",
                    "- Fix: replace `always @(posedge clk)` with `@(cross(V(clk) - vth, +1))` inside `analog begin`.",
                ])
            if "packed_bit_select" in issue:
                note_hints.extend([
                    "- **CRITICAL: bit-select indexing `var[N]` detected** (e.g. `div_val[0] = ...`). Verilog-A does not support packed bit arrays on `integer` variables.",
                    "- Fix: do NOT index an integer with `[N]`. Read individual bits by testing membership or using helper integers:",
                    "  - Before: `div_val[0] = (V(d[0]) > vth) ? 1 : 0;`",
                    "  - After:  `integer b0; b0 = (V(d[0]) > vth) ? 1 : 0; div_val = div_val | b0;`",
                    "  - Or unroll: `div_val = 0; if (V(d[0])>vth) div_val=div_val+1; if (V(d[1])>vth) div_val=div_val+2; ...`",
                ])
            if "shift_operator" in issue:
                note_hints.extend([
                    "- **CRITICAL: shift operator `<<` or `>>` on a `reg` variable**. These are invalid Verilog-A.",
                    "- Fix: replace `reg` with `integer`; `<<`/`>>` on `integer` is valid Verilog-A.",
                    "  - Before: `reg [7:0] cnt; cnt >> 1`",
                    "  - After:  `integer cnt; cnt / 2`  (or keep `>>` once `reg` is gone)",
                ])

        # generated_include: TB includes a specific file — check DUT consistency
        if note.startswith("generated_include=") and family == "end-to-end":
            import re as _re
            inc_match = _re.search(r"generated_include=(.+)", note)
            inc_file = inc_match.group(1).strip() if inc_match else None
            if inc_file:
                note_hints.extend([
                    f"- **DUT-TB include mismatch risk.** Your previous TB used `ahdl_include \"{inc_file}\"`.",
                    "- The Spectre scorer checks that this filename matches the actual generated DUT file.",
                    "- **The DUT file is saved as `<module_name>.va`.** If your DUT module is `lfsr`, the file is `lfsr.va`.",
                    f"- Ensure your new TB uses `ahdl_include \"<your_module_name>.va\"` — not `{inc_file}` unless that exactly matches your module name.",
                ])

        # evas_compile_errors: surface raw EVAS compile lines to the LLM
        if note.startswith("evas_compile_errors:"):
            error_text = note[len("evas_compile_errors:"):].strip()
            note_hints.extend([
                "- **EVAS reported the following compile error(s):**",
                *[f"  `{line.strip()}`" for line in error_text.split("|") if line.strip()],
                "- Fix the syntax or declaration issue indicated above before addressing anything else.",
            ])

    # === NEW: Automated diagnosis translation ===
    # Translate behavioral diagnostic messages into specific repair suggestions
    diagnosis_sections: list[str] = []
    csv_signal_lines: list[str] = []
    for note in notes:
        # Collect CSV signal summary lines separately
        if note.startswith("csv_signal:"):
            csv_signal_lines.append(note[len("csv_signal:"):].strip())
            continue
        # Skip compile-related notes (already handled above)
        if any(kw in note for kw in ["undefined_module", "colon_instance", "conditional_transition", "no_ahdl", "spectre_strict", "evas_compile_errors"]):
            continue
        # Use diagnosis translation system
        translation = translate_diagnosis(note, task_id)
        if translation["diagnosis"]:
            section = f"\n### Diagnostic: `{note}`\n\n{format_repair_section(translation)}"
            diagnosis_sections.append(section)

        # Behavioral correctness hints are now handled by diagnosis_translation system
        # (see DIAGNOSIS_RULES in diagnosis_translation.py)

    if note_hints:
        deduped: list[str] = []
        seen = set()
        for item in note_hints:
            if item not in seen:
                deduped.append(item)
                seen.add(item)
        lines.extend(["", "Compile-related repair hints:"])
        lines.extend(deduped)

    # Add diagnosis-translated sections
    if diagnosis_sections:
        lines.extend(["", "# Behavioral Diagnosis Analysis", "", "Below are specific diagnostic findings from EVAS simulation and their repair suggestions:"])
        lines.extend(diagnosis_sections)

    # Add CSV signal waveform summary when sim_correct failed
    if csv_signal_lines:
        lines.extend([
            "",
            "# Observed Waveform Summary (from EVAS tran.csv)",
            "",
            "The following signal statistics were measured from the simulation output.",
            "Use these to understand what the circuit actually produced and identify the functional bug:",
            "",
        ])
        for sig_line in csv_signal_lines:
            lines.append(f"- {sig_line}")
        lines.extend([
            "",
            "Compare these values against the expected behaviour described in the task to identify",
            "which signal is incorrect and what the root cause is (wrong threshold, missing edge, wrong polarity, etc.).",
        ])

    # Parse structure_diagnosis for additional repair hints
    diag = evas_result.get("structure_diagnosis")
    if diag:
        missing_modules = diag.get("missing_modules", [])
        extra_modules = diag.get("extra_modules", [])
        missing_signals = diag.get("missing_signals", [])
        extra_signals = diag.get("extra_signals", [])

        if missing_modules:
            expected = ", ".join(missing_modules)
            actual = ", ".join(extra_modules) or "<none>"
            lines.extend([
                "",
                "Module mismatch:",
                f"- Expected modules (from gold testbench): {expected}",
                f"- Your generated modules: {actual}",
                "- Align your ahdl_include directives and module names with the gold testbench structure.",
            ])

        if missing_signals:
            expected_sig = ", ".join(missing_signals)
            actual_sig = ", ".join(extra_signals[:10]) or "<different names>"
            lines.extend([
                "",
                "**Signal naming mismatch**:",
                f"- Expected save signals (from gold testbench): {expected_sig}",
                f"- Your CSV columns: {actual_sig}",
                "- **Fix: Rename your signals in the save statement to match expected names exactly.**",
                "- Example: If gold expects `not_a`, change `a_not` or `not_dut:A` to `not_a`.",
            ])

    shape_text = _end_to_end_shape_guidance(task_prompt, family)
    if shape_text:
        lines.extend(["", shape_text])

    # Inject Skill circuit-specific knowledge ONLY for behavioral errors (condition E)
    # Do NOT inject for FAIL_INFRA (missing files) — prioritize file generation first
    # Condition D: include_skill=False → no Skill injection
    if include_skill and status in ("FAIL_SIM_CORRECTNESS", "FAIL_DUT_COMPILE", "FAIL_TB_COMPILE"):
        skill_ref_lines = _inject_skill_reference(task_id)
        if skill_ref_lines:
            lines.extend(skill_ref_lines)

    # Inject checks.yaml expected behavior (Checker source) for behavioral errors
    # This is always included for both conditions D and E (Checker is fixed)
    if status == "FAIL_SIM_CORRECTNESS":
        check_lines = _inject_check_expectations(task_dir)
        if check_lines:
            lines.extend(check_lines)

    return "\n".join(lines)


def build_generic_retry_prompt(
    task_dir: Path,
    sample_dir: Path,
    *,
    skill_bundle_text: str | None = None,
) -> str:
    """Build a no-diagnostics retry prompt.

    This is the matched-budget control: it gives the model one extra chance and
    the previous files, but no EVAS failure attribution or validation notes.
    """
    meta = read_meta(task_dir)
    family = meta.get("family", "end-to-end")
    original_prompt = build_prompt(task_dir)
    candidate_text = "\n\n".join(_candidate_sections(sample_dir))
    skill_text = _skill_section(skill_bundle_text)
    shape_text = _end_to_end_shape_guidance(original_prompt, family)
    return textwrap.dedent(f"""\
        You are doing a generic second attempt for the same benchmark task.

        Important fairness rule:
        - You may inspect the previous candidate files below.
        - You are NOT given simulator diagnostics or validator feedback.
        - Produce a complete replacement answer that follows the original task.

        Artifact contract:
        {_artifact_contract(family)}

        Output rules:
        - Output code blocks only.
        - Do not include explanations outside code blocks.
        - Preserve required module names, port order, parameters, and observable names from the original task.
        - Use EVAS/Spectre-compatible voltage-domain Verilog-A only.
        - Do not use current-domain operators such as I(), ddt(), idt(), or laplace_*.
        - Avoid Verilog initial blocks; initialize inside analog @(initial_step).
        - Keep transition() contributions continuous rather than inside conditional begin/end branches.
        {shape_text}

        {skill_text}

        # Original Task Prompt

        {original_prompt.strip()}

        # Previous Candidate Files

        {candidate_text}
    """).strip() + "\n"


def build_skill_only_prompt(
    task_dir: Path,
    *,
    skill_bundle_text: str,
) -> str:
    meta = read_meta(task_dir)
    family = meta.get("family", "end-to-end")
    original_prompt = build_prompt(task_dir)
    skill_text = _skill_section(skill_bundle_text)
    shape_text = _end_to_end_shape_guidance(original_prompt, family)
    return textwrap.dedent(f"""\
        You are generating a benchmark candidate using a frozen Verilog-A skill bundle.

        Artifact contract:
        {_artifact_contract(family)}

        Output rules:
        - Output code blocks only.
        - Do not include explanations outside code blocks.
        - Preserve required module names, port order, parameters, and observable names from the original task.
        - Follow the frozen skill bundle strictly.
        {shape_text}

        {skill_text}

        # Original Task Prompt

        {original_prompt.strip()}
    """).strip() + "\n"


def build_evas_assisted_prompt(
    task_dir: Path,
    sample_dir: Path,
    evas_result: dict,
    *,
    skill_bundle_text: str | None = None,
) -> str:
    """Build a targeted repair prompt using EVAS status, scores, and notes."""
    meta = read_meta(task_dir)
    family = meta.get("family", "end-to-end")
    original_prompt = build_prompt(task_dir)
    candidate_text = "\n\n".join(_candidate_sections(sample_dir))
    score_text = _score_summary(evas_result)
    skill_text = _skill_section(skill_bundle_text)
    shape_text = _end_to_end_shape_guidance(original_prompt, family)
    status = evas_result.get("status", "FAIL_OTHER")

    if status == "FAIL_DUT_COMPILE":
        focus = (
            "Focus first on Verilog-A DUT syntax, module/interface mismatch, "
            "unsupported AHDL constructs, and banned operators."
        )
    elif status == "FAIL_TB_COMPILE":
        focus = (
            "Focus first on Spectre testbench syntax, ahdl_include paths, DUT "
            "instance name/port order, stimulus sources, save directives, and "
            "observable naming."
        )
    elif status == "FAIL_SIM_CORRECTNESS":
        focus = (
            "Focus first on behavioral semantics. Decide whether the mismatch is "
            "DUT logic, stimulus inadequacy, missing saved observables, reset/"
            "bring-up sequencing, or timing thresholds."
        )
    else:
        focus = (
            "Focus first on missing files, malformed code blocks, infrastructure "
            "compatibility, and preserving the required artifact contract."
        )

    return textwrap.dedent(f"""\
        You are repairing a generated Verilog-A/Spectre benchmark candidate using EVAS validator feedback.

        Repair focus:
        {focus}

        Artifact contract:
        {_artifact_contract(family)}

        Output rules:
        - Output complete replacement code blocks only.
        - Do not include explanations outside code blocks.
        - Preserve required module names, port order, parameters, and observable names from the original task.
        - Use EVAS/Spectre-compatible voltage-domain Verilog-A only.
        - Do not use current-domain operators such as I(), ddt(), idt(), or laplace_*.
        - Avoid Verilog initial blocks; initialize inside analog @(initial_step).
        - Keep transition() contributions continuous rather than inside conditional begin/end branches.
        - Prefer the smallest semantic change that addresses the validator failure.
        {shape_text}

        {skill_text}

        # EVAS Result

        {score_text.strip()}

        # Original Task Prompt

        {original_prompt.strip()}

        # Current Candidate Files

        {candidate_text}
    """).strip() + "\n"


def _history_section(history: list[dict], current_status: str = "FAIL") -> str:
    if not history:
        return ""

    lines = ["# Previous Repair Attempts", ""]
    lines.append("Use the summaries below to continue the search from the best-so-far candidate instead of repeating failed edits.")
    lines.append("")

    status_history = [(entry.get("round", "?"), entry.get("status", "?")) for entry in history]
    status_str = " → ".join(f"R{round_idx}:{status}" for round_idx, status in status_history)
    lines.append(f"**Status progression**: {status_str} → R{len(history)+1}:{current_status} (target: PASS)")
    lines.append("")

    for entry in history[-3:]:
        round_idx = entry.get("round", "?")
        scores = entry.get("scores", {})
        compared_to = entry.get("compared_to_round", 0)
        progress_label = entry.get("progress_label", "unknown")
        lines.append(
            f"- R{round_idx} vs `{('baseline' if compared_to == 0 else f'R{compared_to}')}`: "
            f"status={entry.get('status', '?')}, "
            f"weighted_total={float(scores.get('weighted_total', 0.0)):.3f}, "
            f"sim_correct={float(scores.get('sim_correct', 0.0)):.3f}, "
            f"loop_state={progress_label}"
        )
        progress_summary = entry.get("progress_summary")
        if progress_summary:
            lines.append(f"  {progress_summary}")

        metrics = entry.get("metrics", {})
        if metrics:
            preview_items = []
            for key in sorted(metrics)[:4]:
                preview_items.append(f"{key}={_format_scalar(metrics[key])}")
            if preview_items:
                lines.append(f"  Metrics snapshot: {', '.join(preview_items)}")

    return "\n".join(lines)


def build_evas_guided_repair_prompt(
    task_dir: Path,
    sample_dir: Path,
    evas_result: dict,
    *,
    history: list[dict] | None = None,
    include_skill: bool = True,
    loop_context: dict | None = None,
) -> str:
    """Build a targeted repair prompt.

    Args:
        history: list of previous round result dicts (each has 'round', 'evas_notes').
                 When provided, accumulated constraints are included to prevent oscillation.
        include_skill: If True, inject Skill circuit knowledge (Experiment condition E).
                       If False, only Checker + EVAS diagnosis (Experiment condition D).
    """
    meta = read_meta(task_dir)
    family = meta.get("family", "end-to-end")
    original_prompt = build_prompt(task_dir)
    candidate_text = "\n\n".join(_candidate_sections(sample_dir))
    score_text = _score_summary(evas_result)
    targeted_skill_text = _targeted_repair_skill(task_dir, evas_result, include_skill=include_skill)
    loop_state_text = _loop_state_section(task_dir, evas_result, history or [], loop_context)
    history_text = _history_section(history or [], current_status=evas_result.get("status", "FAIL"))

    skill_label = "Checker + EVAS + Skill" if include_skill else "Checker + EVAS only"

    return textwrap.dedent(f"""\
        You are repairing a generated Verilog-A/Spectre benchmark candidate using EVAS validator feedback and a targeted repair skill ({skill_label}).

        Artifact contract:
        {_artifact_contract(family)}

        Output rules:
        - Output complete replacement code blocks only.
        - Do not include explanations outside code blocks.
        - Preserve required module names, port order, parameters, and observable names from the original task.
        - Apply the targeted repair skill below instead of doing a broad rewrite.
        - Prefer the smallest change that resolves the EVAS-reported failure.
        - While fixing the current failure, do NOT revert any fix that resolved a prior round's failure.

        {targeted_skill_text}

        # EVAS Result

        {score_text.strip()}

        {loop_state_text}

        {history_text}

        # Original Task Prompt

        {original_prompt.strip()}

        # Current Candidate Files

        {candidate_text}
    """).strip() + "\n"


def build_prompt_from_paths(
    *,
    mode: str,
    task_dir: Path,
    sample_dir: Path,
    evas_result_path: Path | None,
    skill_bundle_path: Path | None,
) -> str:
    skill_bundle_text = load_skill_bundle(skill_bundle_path) if skill_bundle_path else None
    if mode == "generic-retry":
        return build_generic_retry_prompt(task_dir, sample_dir, skill_bundle_text=skill_bundle_text)
    if mode == "skill-only":
        if not skill_bundle_text:
            raise ValueError("skill-only prompt requires --skill-bundle")
        return build_skill_only_prompt(task_dir, skill_bundle_text=skill_bundle_text)
    if mode == "skill-evas-informed":
        if not evas_result_path:
            raise ValueError("skill-evas-informed prompt requires --evas-result")
        if not skill_bundle_text:
            raise ValueError("skill-evas-informed prompt requires --skill-bundle")
        return build_evas_assisted_prompt(
            task_dir,
            sample_dir,
            _read_json(evas_result_path),
            skill_bundle_text=skill_bundle_text,
        )
    if mode == "evas-guided-repair":
        if not evas_result_path:
            raise ValueError("evas-guided-repair prompt requires --evas-result")
        return build_evas_guided_repair_prompt(task_dir, sample_dir, _read_json(evas_result_path), include_skill=True)
    if mode == "evas-guided-repair-no-skill":
        # Experiment condition D: Checker + EVAS only (no Skill)
        if not evas_result_path:
            raise ValueError("evas-guided-repair-no-skill prompt requires --evas-result")
        return build_evas_guided_repair_prompt(task_dir, sample_dir, _read_json(evas_result_path), include_skill=False)
    if not evas_result_path:
        raise ValueError("evas-assisted prompt requires --evas-result")
    return build_evas_assisted_prompt(
        task_dir,
        sample_dir,
        _read_json(evas_result_path),
        skill_bundle_text=skill_bundle_text,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Build prompts for mainline retry / skill / EVAS-assisted modes.")
    ap.add_argument(
        "--mode",
        choices=["generic-retry", "evas-assisted", "skill-only", "skill-evas-informed", "evas-guided-repair", "evas-guided-repair-no-skill"],
        required=True,
        help="Mode: evas-guided-repair (condition E: +Skill) or evas-guided-repair-no-skill (condition D: no Skill)",
    )
    ap.add_argument("--task-dir", required=True)
    ap.add_argument("--sample-dir", required=True)
    ap.add_argument("--evas-result", default="")
    ap.add_argument("--skill-bundle", default="")
    ap.add_argument("--output", default="", help="Write prompt to this file. Defaults to stdout.")
    args = ap.parse_args()

    prompt = build_prompt_from_paths(
        mode=args.mode,
        task_dir=Path(args.task_dir),
        sample_dir=Path(args.sample_dir),
        evas_result_path=Path(args.evas_result) if args.evas_result else None,
        skill_bundle_path=Path(args.skill_bundle) if args.skill_bundle else None,
    )
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(prompt, encoding="utf-8")
        print(out)
    else:
        print(prompt, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
