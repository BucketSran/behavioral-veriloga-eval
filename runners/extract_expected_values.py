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

# simulate_evas.py 路径
SIMULATE_EVAS_PATH = Path(__file__).parent / "simulate_evas.py"


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


def parse_expected_conditions(source: str) -> dict:
    """解析 checker 源码中的期望值条件"""
    expected = {}

    # 常见条件模式
    patterns = [
        # abs(value - expected) <= tolerance
        (r"abs\((\w+)\s*-\s*([\d.]+)\)\s*<=\s*([\d.]+)",
         lambda m: {
             m.group(1): {
                 "expected": float(m.group(2)),
                 "tolerance": float(m.group(3)),
                 "description": f"{m.group(1)} should be ≈ {m.group(2)} (tolerance ±{m.group(3)})"
             }
         }),

        # abs(value - expected) < tolerance
        (r"abs\((\w+)\s*-\s*([\d.]+)\)\s*<\s*([\d.]+)",
         lambda m: {
             m.group(1): {
                 "expected": float(m.group(2)),
                 "tolerance": float(m.group(3)),
                 "description": f"{m.group(1)} should be ≈ {m.group(2)} (tolerance ±{m.group(3)})"
             }
         }),

        # value >= threshold
        (r"(\w+)\s*>=\s*([\d.]+)",
         lambda m: {
             m.group(1): {
                 "expected": f">= {m.group(2)}",
                 "description": f"{m.group(1)} should be ≥ {m.group(2)}"
             }
         }),

        # value > threshold
        (r"(\w+)\s*>\s*([\d.]+)",
         lambda m: {
             m.group(1): {
                 "expected": f"> {m.group(2)}",
                 "description": f"{m.group(1)} should be > {m.group(2)}"
             }
         }),

        # value <= threshold
        (r"(\w+)\s*<=\s*([\d.]+)",
         lambda m: {
             m.group(1): {
                 "expected": f"<= {m.group(2)}",
                 "description": f"{m.group(1)} should be ≤ {m.group(2)}"
             }
         }),

        # value < threshold
        (r"(\w+)\s*<\s*([\d.]+)",
         lambda m: {
             m.group(1): {
                 "expected": f"< {m.group(2)}",
                 "description": f"{m.group(1)} should be < {m.group(2)}"
             }
         }),

        # value == expected (rare in checkers)
        (r"(\w+)\s*==\s*([\d.]+)",
         lambda m: {
             m.group(1): {
                 "expected": float(m.group(2)),
                 "tolerance": 0,
                 "description": f"{m.group(1)} should be exactly {m.group(2)}"
             }
         }),
    ]

    # 提取所有条件
    for pattern, handler in patterns:
        for match in re.finditer(pattern, source):
            try:
                result = handler(match)
                for key, value in result.items():
                    # 避免覆盖已存在的更精确条件
                    if key not in expected:
                        expected[key] = value
            except (ValueError, AttributeError):
                continue

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
    """根据 task_id 确定对应的 checker 函数名"""
    # CHECKS 映射规则（从 simulate_evas.py）
    # 大多数 checker 名为 check_<base_task_id>

    base = task_id.replace("_smoke", "")

    # 特殊映射
    special_mapping = {
        "clk_divider": "check_clk_divider",
        "multimod_divider": "check_multimod_divider",
        "adpll_timer": "check_adpll_lock",
        "cppll_freq_step_reacquire": "check_cppll_freq_step_reacquire",
        "bbpd_data_edge_alignment": "check_bbpd_data_edge_alignment",
        "prbs7": "check_prbs7",
        "sc_integrator": "check_sc_integrator",
        "digital_basics": "check_not_gate",
        "strongarm_reset_priority_bug": "check_strongarm_reset_priority_bug",
        "inverted_comparator_logic_bug": "check_inverted_comparator_logic_bug",
        "wrong_edge_sample_hold_bug": "check_wrong_edge_sample_hold_bug",
    }

    if base in special_mapping:
        return special_mapping[base]

    # 默认规则
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