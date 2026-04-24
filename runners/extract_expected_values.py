#!/usr/bin/env python3
"""
自动从 checker 函数源码中提取期望值条件。

用法:
    from extract_expected_values import extract_expected_values

    expected = extract_expected_values("check_adpll_ratio_hop")
    # 返回: {"pre_ratio": {"expected": 4.0, "tolerance": 0.25}, ...}
"""
import re
from pathlib import Path
from typing import Optional
from functools import lru_cache

# simulate_evas.py 路径
SIMULATE_EVAS_PATH = Path(__file__).parent / "simulate_evas.py"

# Task-specific metric alias map (checker variable -> EVAS note metric key).
# This is model-agnostic and only bridges naming-contract gaps between checker
# internals and emitted diagnostics.
TASK_METRIC_ALIASES: dict[str, dict[str, list[str]]] = {
    "cppll_timer": {
        "ratio": ["freq_ratio"],
        "ratio_err": ["freq_ratio"],
    },
    "cppll_tracking_smoke": {
        "ratio": ["freq_ratio"],
        "ratio_err": ["freq_ratio"],
    },
    "cppll_freq_step_reacquire_smoke": {
        "pre_ratio": ["freq_ratio"],
        "post_ratio": ["freq_ratio"],
        "pre_lock": ["final_lock_high"],
        "post_lock": ["final_lock_high"],
    },
    "adpll_lock_smoke": {
        "freq_ratio": ["freq_ratio", "late_edge_ratio"],
        "vctrl_span": ["vctrl_range_ok", "vctrl_min", "vctrl_max"],
    },
    "adpll_timer": {
        "freq_ratio": ["freq_ratio", "late_edge_ratio"],
        "vctrl_span": ["vctrl_range_ok", "vctrl_min", "vctrl_max"],
    },
    "adpll_timer_smoke": {
        "freq_ratio": ["freq_ratio", "late_edge_ratio"],
        "vctrl_span": ["vctrl_range_ok", "vctrl_min", "vctrl_max"],
    },
    "comparator_hysteresis_smoke": {
        "rise_t": ["rise_t_out_of_range"],
        "fall_t": ["fall_t_out_of_range"],
    },
    "gray_counter_4b_smoke": {
        "bad_transitions": ["bad_transitions"],
    },
    "multimod_divider": {
        "base": ["base", "pre_count", "post_count"],
    },
}


def metric_aliases_for_task(task_id: str) -> dict[str, list[str]]:
    """Return metric alias mapping for a task (checker var -> EVAS metric keys)."""
    aliases = TASK_METRIC_ALIASES.get(task_id, {})
    if aliases:
        return aliases
    # Fallback to base task id (strip smoke suffix).
    base = task_id.replace("_smoke", "")
    return TASK_METRIC_ALIASES.get(base, {})


def extract_checker_source(checker_name: str) -> Optional[str]:
    """从 simulate_evas.py 提取指定 checker 函数的源码"""
    if not SIMULATE_EVAS_PATH.exists():
        return None

    content = SIMULATE_EVAS_PATH.read_text(encoding="utf-8")

    # 匹配函数定义到下一个 def 或文件结束
    pattern = rf"def {checker_name}\([^)]*\).*?(?=\ndef |\Z)"
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return None

    return match.group(0)


@lru_cache(maxsize=1)
def _load_checks_mapping() -> dict[str, str]:
    """Parse CHECKS mapping from simulate_evas.py as task_id -> checker function name."""
    if not SIMULATE_EVAS_PATH.exists():
        return {}
    content = SIMULATE_EVAS_PATH.read_text(encoding="utf-8")
    mapping: dict[str, str] = {}
    for task_id, checker_name in re.findall(r'"([^"]+)"\s*:\s*(check_[A-Za-z0-9_]+)', content):
        mapping[task_id] = checker_name
    return mapping


_NUM_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?"
_OP_TEXT = {
    ">": ">",
    ">=": "≥",
    "<": "<",
    "<=": "≤",
    "==": "exactly",
}
_INVERT_OP = {
    ">": "<=",
    ">=": "<",
    "<": ">=",
    "<=": ">",
}


def _condition_info(var: str, op: str, value: str, *, source_kind: str) -> dict:
    if op == "==":
        return {
            "expected": float(value),
            "tolerance": 0,
            "description": f"{var} should be exactly {value}",
            "source_kind": source_kind,
        }
    return {
        "expected": f"{op} {value}",
        "description": f"{var} should be {_OP_TEXT.get(op, op)} {value}",
        "source_kind": source_kind,
    }


def _add_condition(expected: dict, var: str, op: str, value: str, *, source_kind: str) -> None:
    if var not in expected:
        expected[var] = _condition_info(var, op, value, source_kind=source_kind)


def _parse_simple_comparisons(expr: str, *, invert: bool, source_kind: str) -> dict:
    """Parse numeric checker predicates into public contract conditions.

    Checker code often expresses failures as `if metric > threshold: return False`.
    In that case the public contract is the inverse (`metric <= threshold`).
    """
    found: dict = {}
    text = expr.strip()

    # abs(metric - target) <= tolerance
    abs_pat = rf"abs\((\w+)\s*-\s*({_NUM_RE})\)\s*(<=|<)\s*({_NUM_RE})"
    for m in re.finditer(abs_pat, text):
        if invert:
            continue
        var, target, _op, tol = m.groups()
        found[var] = {
            "expected": float(target),
            "tolerance": float(tol),
            "description": f"{var} should be ≈ {target} (tolerance ±{tol})",
            "source_kind": source_kind,
        }

    # lower <= metric <= upper
    chain_pat = rf"({_NUM_RE})\s*(<=|<)\s*(\w+)\s*(<=|<)\s*({_NUM_RE})"
    for m in re.finditer(chain_pat, text):
        if invert:
            continue
        lower, lop, var, uop, upper = m.groups()
        found[var] = {
            "expected": f"{lower} {lop} x {uop} {upper}",
            "description": f"{var} should be between {lower} and {upper}",
            "source_kind": source_kind,
        }

    comparisons = [
        (rf"\b(\w+)\s*(>=|<=|>|<|==)\s*({_NUM_RE})", False),
        (rf"({_NUM_RE})\s*(>=|<=|>|<|==)\s*(\w+)", True),
    ]
    for pattern, number_first in comparisons:
        for m in re.finditer(pattern, text):
            if number_first:
                value, op, var = m.groups()
                op = {">": "<", ">=": "<=", "<": ">", "<=": ">=", "==": "=="}[op]
            else:
                var, op, value = m.groups()
            if var in found:
                continue
            if invert:
                op = _INVERT_OP.get(op)
                if op is None:
                    continue
            found[var] = _condition_info(var, op, value, source_kind=source_kind)

    return found


def _line_returns_false_soon(lines: list[str], start_idx: int) -> bool:
    for lookahead in lines[start_idx + 1 : start_idx + 5]:
        stripped = lookahead.strip()
        if not stripped:
            continue
        if "return False" in stripped:
            return True
        # Stop once another peer-level control statement begins.
        if stripped.startswith(("if ", "elif ", "else:", "ok =", "return True")):
            return False
    return False


def parse_expected_conditions(source: str) -> dict:
    """Parse public behavior targets from checker source.

    Conditions that immediately lead to `return False` are inverted before being
    exposed, so the prompt receives the pass criterion rather than the fail guard.
    """
    expected: dict = {}
    lines = source.splitlines()

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith(("if ", "elif ")):
            continue
        if not _line_returns_false_soon(lines, idx):
            continue
        condition = stripped.split(":", 1)[0]
        condition = re.sub(r"^(?:if|elif)\s+", "", condition)
        for var, info in _parse_simple_comparisons(
            condition, invert=True, source_kind="inverted_fail_guard"
        ).items():
            if var not in expected:
                expected[var] = info

    # Direct pass expressions such as `ok = wraps >= 3 and clk_rises >= 3`.
    ok_blocks = re.findall(r"\bok\s*=\s*(.*?)(?=\n\s*return\s+ok\b)", source, flags=re.DOTALL)
    for block in ok_blocks:
        for var, info in _parse_simple_comparisons(
            block, invert=False, source_kind="pass_expression"
        ).items():
            if var not in expected:
                expected[var] = info

    # Named pass predicates later composed into `ok`, e.g.
    # `freq_ok = 0.97 <= freq_ratio <= 1.03`.
    for line in lines:
        stripped = line.strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*(?:_ok|_in_range)\s*=", stripped):
            continue
        rhs = stripped.split("=", 1)[1]
        for var, info in _parse_simple_comparisons(
            rhs, invert=False, source_kind="pass_predicate"
        ).items():
            if var not in expected:
                expected[var] = info

    return expected


def extract_semantic_hints(source: str) -> list[str]:
    """从 checker 源码中提取语义提示"""
    hints = []

    # 检查返回的 note 字串中的关键信息
    note_pattern = r'return\s+\w+,\s*f"[^"]*"|return\s+\w+,\s*"([^"]*)"'
    for match in re.finditer(note_pattern, source):
        note_content = match.group(1) or match.group(0)
        if note_content:
            # 提取有用的诊断关键词
            keywords = ["missing", "lock", "monotonic", "overlap", "reset", "delay", "frequency", "ratio"]
            for kw in keywords:
                if kw in note_content.lower() and kw not in " ".join(hints).lower():
                    hints.append(f"Checker checks: {kw}")

    # 从 required 集合提取信号要求
    required_pattern = r'required\s*=\s*\{([^}]+)\}'
    for match in re.finditer(required_pattern, source):
        signals = match.group(1)
        if signals:
            hints.append(f"Required signals: {signals.strip()}")

    return hints


def extract_expected_values(checker_name: str) -> dict:
    """从 checker 函数提取期望值和语义提示"""
    source = extract_checker_source(checker_name)
    if not source:
        return {"error": f"Checker {checker_name} not found"}

    expected = parse_expected_conditions(source)
    hints = extract_semantic_hints(source)

    return {
        "checker": checker_name,
        "expected_conditions": expected,
        "semantic_hints": hints,
        "source_preview": source[:500] if len(source) > 500 else source,
    }


def format_expected_for_prompt(extracted: dict) -> list[str]:
    """将提取结果格式化为 prompt 片段"""
    lines = []

    expected = extracted.get("expected_conditions", {})
    if expected:
        lines.append("")
        lines.append("# Expected Behavior (extracted from checker)")
        lines.append("")
        lines.append("The checker verifies the following conditions:")
        for var, info in expected.items():
            desc = info.get("description", f"{var} condition")
            lines.append(f"- {desc}")

    hints = extracted.get("semantic_hints", [])
    if hints:
        lines.append("")
        lines.append("Checker requirements:")
        for hint in hints[:5]:
            lines.append(f"- {hint}")

    return lines


def get_checker_name_for_task(task_id: str) -> str:
    """Resolve checker function name directly from simulate_evas.CHECKS mapping."""
    checks = _load_checks_mapping()
    if task_id in checks:
        return checks[task_id]
    base = task_id.replace("_smoke", "")
    if base in checks:
        return checks[base]
    smoke_id = f"{base}_smoke"
    if smoke_id in checks:
        return checks[smoke_id]
    return f"check_{base}"


# 测试
if __name__ == "__main__":
    test_checkers = [
        "check_adpll_ratio_hop",
        "check_mux_4to1",
        "check_cmp_delay",
        "check_dac_binary_clk_4b",
        "check_bbpd_data_edge_alignment",
        "check_cppll_freq_step_reacquire",
    ]

    for checker in test_checkers:
        print(f"\n{'='*60}")
        print(f"Checker: {checker}")
        print("="*60)

        result = extract_expected_values(checker)

        print("\nExpected conditions:")
        for var, info in result.get("expected_conditions", {}).items():
            print(f"  {var}: {info.get('description', info)}")

        print("\nSemantic hints:")
        for hint in result.get("semantic_hints", []):
            print(f"  {hint}")

        print("\nFormatted for prompt:")
        for line in format_expected_for_prompt(result):
            print(line)
