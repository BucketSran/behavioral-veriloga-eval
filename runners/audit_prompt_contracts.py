#!/usr/bin/env python3
"""Audit raw task prompts against public benchmark contracts.

This audit intentionally does not require prompts to copy gold testbenches.
It flags only likely contract drift:

- P0: clear contradiction/corruption that can make the benchmark unfair.
- P1: underspecified wording that may cause observable failures.
- P2: acceptable concise prompt, or no actionable issue found.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from generate import ROOT, gold_include_entries, list_task_dirs, read_meta


TIME_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:fs|ps|p|ns|n|us|u|ms|s)\b", re.IGNORECASE)
TRAN_RE = re.compile(r"^\s*tran\s+\w+.*$", re.IGNORECASE | re.MULTILINE)
INCLUDE_RE = re.compile(r'ahdl_include\s+"(?:\./)?([^"]+)\.va"', re.IGNORECASE)
MODULE_NAMED_RE = re.compile(r"(?:module named|module name|named)\s+`([^`]+)`", re.IGNORECASE)

BAD_TEXT_PATTERNS = (
    re.compile(r"electrical-", re.IGNORECASE),
    re.compile(r"(?:\[[0-9]+:0\]\s+\w+[^A-Za-z0-9_]+){4,}", re.IGNORECASE),
)

GOLD_LINE_PATTERNS = (
    re.compile(r"^\s*V\w+\s*\(", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*I\w+\s*\(", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*X\w+\s*\(", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*ahdl_include\s+", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*tran\s+tran\s+", re.IGNORECASE | re.MULTILINE),
)


def _gold_tbs(task_dir: Path) -> list[Path]:
    gold = task_dir / "gold"
    if not gold.exists():
        return []
    return sorted(gold.glob("*.scs"))


def _gold_includes(task_dir: Path) -> list[str]:
    return [entry["stem"] for entry in _gold_entries(task_dir)]


def _gold_entries(task_dir: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for tb in _gold_tbs(task_dir):
        text = tb.read_text(encoding="utf-8", errors="ignore")
        for entry in gold_include_entries(task_dir, text):
            if entry["filename"] not in seen:
                seen.add(entry["filename"])
                entries.append(entry)
    return entries


def _gold_modules(task_dir: Path) -> list[str]:
    modules: list[str] = []
    seen: set[str] = set()
    for entry in _gold_entries(task_dir):
        module = entry["module"]
        if module not in seen:
            seen.add(module)
            modules.append(module)
    return modules


def _gold_tran(task_dir: Path) -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()
    for tb in _gold_tbs(task_dir):
        for match in TRAN_RE.finditer(tb.read_text(encoding="utf-8", errors="ignore")):
            line = re.sub(r"\s+", " ", match.group(0).strip())
            if line not in seen:
                seen.add(line)
                lines.append(line)
    return lines


def _raw_module_names(prompt: str) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for match in MODULE_NAMED_RE.finditer(prompt):
        name = match.group(1).strip()
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return names


def _gold_like_line_count(prompt: str) -> int:
    return sum(len(pattern.findall(prompt)) for pattern in GOLD_LINE_PATTERNS)


def _has_conflicting_primary_module(raw_names: list[str], gold_modules: list[str], family: str) -> bool:
    if not raw_names or not gold_modules:
        return False
    if family == "end-to-end":
        # Multi-module end-to-end prompts can name only the main module.
        return raw_names[0] not in gold_modules
    if family in {"spec-to-va", "bugfix"}:
        return raw_names[0] not in gold_modules
    return False


def _requires_gain_estimator(prompt_l: str) -> bool:
    if "gain_estimator" not in prompt_l:
        return False
    if re.search(r"\bdo\s+not\s+create\s+(?:a\s+)?`?gain_estimator`?", prompt_l):
        return False
    return bool(
        re.search(
            r"\b(?:create|generate|implement|return|write|module\s+named|module\s+name|named)\s+(?:a\s+)?`?gain_estimator`?",
            prompt_l,
        )
    )


def _audit_one(task_id: str, task_dir: Path) -> dict:
    meta = read_meta(task_dir)
    family = meta.get("family", task_dir.parts[-4] if len(task_dir.parts) >= 4 else "")
    prompt = (task_dir / "prompt.md").read_text(encoding="utf-8", errors="ignore")
    prompt_l = prompt.lower()
    gold_includes = _gold_includes(task_dir)
    gold_modules = _gold_modules(task_dir)
    gold_tran = _gold_tran(task_dir)
    raw_names = _raw_module_names(prompt)

    issues: list[str] = []
    p0 = False
    p1 = False

    for pattern in BAD_TEXT_PATTERNS:
        if pattern.search(prompt):
            issues.append("corrupted_or_duplicated_prompt_text")
            p0 = True
            break

    if _has_conflicting_primary_module(raw_names, gold_modules, family):
        issues.append(f"primary_module_name_not_in_gold_modules:{raw_names[0]} vs {','.join(gold_modules)}")
        p0 = True

    if _requires_gain_estimator(prompt_l) and "gain_estimator" not in gold_modules:
        issues.append("mentions_gain_estimator_not_in_gold_harness")
        p0 = True

    if "500 mhz" in prompt_l and any("sar_adc_dac_weighted_8b" in inc for inc in gold_includes):
        issues.append("sampling_frequency_conflicts_with_gold_scale")
        p0 = True

    if "50us" in prompt_l or "50 µs" in prompt_l:
        if any("cmp_hysteresis" in inc for inc in gold_includes):
            issues.append("comparator_hysteresis_time_scale_conflict")
            p0 = True

    if family in {"end-to-end", "tb-generation"}:
        if "save" not in prompt_l and "observable" not in prompt_l and "csv" not in prompt_l:
            issues.append("no_raw_observable_or_save_contract")
            p1 = True
        if "testbench" not in prompt_l and family == "end-to-end":
            issues.append("end_to_end_prompt_does_not_request_testbench")
            p1 = True

    if gold_tran and not any(word in prompt_l for word in ("transient", "tran", "run for", "runs for", "simulation")):
        issues.append("raw_prompt_missing_simulation_window_hint")
        p1 = True

    gold_like_count = _gold_like_line_count(prompt)
    if gold_like_count >= 6:
        issues.append(f"raw_prompt_may_copy_gold_harness_lines:{gold_like_count}")
        p1 = True

    # Raw prompt can be concise: strict timing/observable details are injected at build_prompt time.
    priority = "P0" if p0 else "P1" if p1 else "P2"
    return {
        "task_id": task_id,
        "family": family,
        "relative_path": str(task_dir.relative_to(ROOT / "tasks")),
        "priority": priority,
        "issues": issues,
        "raw_module_names": raw_names,
        "gold_includes": gold_includes,
        "gold_modules": gold_modules,
        "gold_tran": gold_tran,
    }


def _md_table(rows: list[dict]) -> str:
    lines = [
        "| Priority | Task | Family | Issues | Gold includes | Gold modules | Gold tran |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        issues = "<br>".join(row["issues"]) if row["issues"] else "none"
        includes = ", ".join(row["gold_includes"]) if row["gold_includes"] else "-"
        modules = ", ".join(row["gold_modules"]) if row["gold_modules"] else "-"
        tran = "<br>".join(row["gold_tran"]) if row["gold_tran"] else "-"
        lines.append(
            f"| {row['priority']} | `{row['task_id']}` | {row['family']} | {issues} | {includes} | {modules} | {tran} |"
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit raw prompts for public contract drift.")
    ap.add_argument("--output-dir", default="results/prompt-contract-audit-2026-04-25")
    args = ap.parse_args()

    rows = [_audit_one(task_id, task_dir) for task_id, task_dir in list_task_dirs()]
    rows.sort(key=lambda row: ({"P0": 0, "P1": 1, "P2": 2}[row["priority"]], row["task_id"]))

    counts = {priority: sum(1 for row in rows if row["priority"] == priority) for priority in ("P0", "P1", "P2")}
    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "task_count": len(rows),
        "counts": counts,
        "rows": rows,
    }
    (out_dir / "prompt_contract_audit.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md = [
        "# Prompt Contract Audit",
        "",
        "Date: 2026-04-25",
        "",
        "This audit classifies raw `prompt.md` files, not the runtime prompt after `build_prompt()` injection.",
        "",
        "Priority meanings:",
        "",
        "- `P0`: clear contradiction/corruption; should be fixed before broad experiments.",
        "- `P1`: underspecified or potentially fragile; fix when it appears in failing sets.",
        "- `P2`: acceptable concise prompt or no actionable issue found.",
        "",
        "## Summary",
        "",
        f"- Tasks audited: `{len(rows)}`",
        f"- P0: `{counts['P0']}`",
        f"- P1: `{counts['P1']}`",
        f"- P2: `{counts['P2']}`",
        "",
        "## Findings",
        "",
        _md_table(rows),
        "",
    ]
    (out_dir / "PROMPT_CONTRACT_AUDIT.md").write_text("\n".join(md), encoding="utf-8")

    print(f"[prompt-audit] tasks={len(rows)} P0={counts['P0']} P1={counts['P1']} P2={counts['P2']}")
    print(f"[prompt-audit] output={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
