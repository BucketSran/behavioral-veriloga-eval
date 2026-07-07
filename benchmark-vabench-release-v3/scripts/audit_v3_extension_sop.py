#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASKS_ROOT = ROOT / "tasks"
REPORTS_ROOT = ROOT / "reports"
TASKS_JSON = ROOT / "TASKS.json"
CHECKS_YAML = ROOT / "CHECKS.yaml"
REPORT_JSON = REPORTS_ROOT / "extension_sop_audit.json"
REPORT_CSV = REPORTS_ROOT / "extension_sop_audit_tasks.csv"
REPORT_MD = REPORTS_ROOT / "extension_sop_audit.md"

RANGE_GROUPS = [
    (301, 340, "language-semantics voltage-domain candidates"),
    (341, 360, "AMS mixed-signal candidates"),
    (361, 372, "noise and analysis candidates"),
    (373, 434, "task/file/table/random/hierarchy syntax candidates"),
    (435, 458, "manual syntax-completion candidates"),
    (459, 470, "course-material gap-fill candidates"),
    (471, 501, "LRM KCL/continuous-time and Cadence data-converter gap-fill candidates"),
    (502, 505, "post-501 PLL/control extension additions"),
]


def task_number(slug: str) -> int:
    return int(slug.split("-", 1)[0])


def read_tasks() -> dict[str, Any]:
    data = json.loads(TASKS_JSON.read_text(encoding="utf-8"))
    defaults = data.get("defaults", {})
    tasks = {}
    for slug, entry in data.get("tasks", {}).items():
        merged = dict(defaults)
        merged.update(entry)
        tasks[slug] = merged
    return tasks


def read_checks_blocks() -> dict[str, str]:
    checks: dict[str, str] = {}
    current: str | None = None
    lines: list[str] = []
    for line in CHECKS_YAML.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith((" ", "\t")) and line.endswith(": |"):
            if current is not None:
                checks[current] = "\n".join(lines).rstrip() + "\n"
            current = line[:-3]
            lines = []
            continue
        if current is None:
            continue
        lines.append(line[2:] if line.startswith("  ") else line)
    if current is not None:
        checks[current] = "\n".join(lines).rstrip() + "\n"
    return checks


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def negative_count(task_dir: Path) -> int:
    manifest = read_json(task_dir / "negative_variants" / "manifest.json")
    if isinstance(manifest, dict):
        cases = manifest.get("cases")
        if isinstance(cases, list):
            return len(cases)
        variants = manifest.get("variants")
        if isinstance(variants, list):
            return len(variants)
        negative_variants = manifest.get("negative_variants")
        if isinstance(negative_variants, list):
            return len(negative_variants)
    return 0


def negative_manifest_cases(task_dir: Path) -> list[dict[str, Any]]:
    manifest = read_json(task_dir / "negative_variants" / "manifest.json")
    if not isinstance(manifest, dict):
        return []
    for key in ("cases", "negative_cases", "negative_variants", "variants"):
        cases = manifest.get(key)
        if isinstance(cases, list):
            return [case for case in cases if isinstance(case, dict)]
    return []


def negative_case_index(task_dir: Path) -> list[dict[str, Any]]:
    payload = read_json(task_dir / "negative_variants" / "negative_cases.json")
    if isinstance(payload, list):
        return [case for case in payload if isinstance(case, dict)]
    if isinstance(payload, dict):
        cases = payload.get("negative_cases")
        if isinstance(cases, list):
            return [case for case in cases if isinstance(case, dict)]
    return []


def negative_signature(cases: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        str(case.get("id") or ""): sorted(str(file_name) for file_name in case.get("files", []))
        for case in cases
    }


def behavior_contract_complete(task: dict[str, Any], manifest_cases: list[dict[str, Any]]) -> bool:
    required_behavior = task.get("required_behavior")
    visible_tests = task.get("visible_tests")
    hidden_tests = task.get("hidden_tests")
    manifest_negative_ids = task.get("negative_variants")
    expected_negative_ids = [str(case.get("id") or "") for case in manifest_cases]
    return (
        bool(str(task.get("description") or "").strip())
        and isinstance(required_behavior, list)
        and len(required_behavior) >= 2
        and all(str(item).strip() for item in required_behavior)
        and isinstance(visible_tests, list)
        and bool(visible_tests)
        and isinstance(hidden_tests, list)
        and bool(hidden_tests)
        and manifest_negative_ids == expected_negative_ids
    )


def negative_descriptions_task_specific(
    title: str,
    manifest_cases: list[dict[str, Any]],
    indexed_cases: list[dict[str, Any]],
) -> bool:
    indexed_by_id = {str(case.get("id") or ""): case for case in indexed_cases}
    if len(indexed_by_id) != len(manifest_cases):
        return False
    for case in manifest_cases:
        case_id = str(case.get("id") or "")
        description = str(case.get("description") or "")
        indexed = indexed_by_id.get(case_id, {})
        why_wrong = str(indexed.get("why_wrong") or indexed.get("description") or "")
        if not description.startswith(f"{title}: "):
            return False
        if description != why_wrong:
            return False
    return True


def has_scs_feature(text: str, feature: str) -> bool:
    if feature == "include":
        return "ahdl_include" in text or "include " in text
    if feature == "instance":
        return re.search(r"(?m)^\s*X\w+\s*\(", text) is not None
    if feature == "source":
        return "vsource" in text or "isource" in text
    if feature == "save":
        return re.search(r"(?m)^\s*save\b", text) is not None
    return False


def audit_task(slug: str, task: dict[str, Any], checks: dict[str, str]) -> dict[str, Any]:
    task_dir = TASKS_ROOT / slug
    target = list(task.get("target", []))
    target_name = target[0] if target else ""
    instruction_path = task_dir / "instruction.md"
    instruction = instruction_path.read_text(encoding="utf-8", errors="ignore") if instruction_path.exists() else ""
    solution_files = sorted((task_dir / "solution").glob("*"))
    starter_files = sorted((task_dir / "starter").glob("*"))
    visible_scs = sorted((task_dir / "test_visible").glob("**/*.scs"))
    hidden_scs = sorted((task_dir / "test_hidden").glob("**/*.scs"))
    visible_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in visible_scs)
    hidden_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in hidden_scs)
    visible_hidden_distinct = bool(visible_text and hidden_text and visible_text != hidden_text)
    check_text = checks.get(slug, "")

    issues: list[str] = []
    warnings: list[str] = []

    if not instruction_path.exists():
        issues.append("missing_instruction")
    if not target_name:
        issues.append("missing_target")
    if target_name and not (task_dir / "solution" / target_name).exists():
        issues.append("target_missing_from_solution")
    if target_name and not (task_dir / "starter" / target_name).exists():
        issues.append("target_missing_from_starter")
    if not solution_files:
        issues.append("missing_solution_files")
    if not starter_files:
        issues.append("missing_starter_files")
    if not visible_scs:
        issues.append("missing_visible_scs")
    if not hidden_scs:
        issues.append("missing_hidden_scs")

    for label, text in (("visible", visible_text), ("hidden", hidden_text)):
        if not text:
            continue
        missing = [name for name in ("include", "instance", "source", "save") if not has_scs_feature(text, name)]
        if missing:
            issues.append(f"{label}_scs_not_executable:{','.join(missing)}")

    manifest_cases = negative_manifest_cases(task_dir)
    indexed_cases = negative_case_index(task_dir)
    neg_count = len(manifest_cases)
    if neg_count < 5:
        issues.append(f"negative_count_lt5:{neg_count}")
    contract_complete = behavior_contract_complete(task, manifest_cases)
    negative_cases_aligned = negative_signature(indexed_cases) == negative_signature(manifest_cases)
    negative_descriptions_specific = negative_descriptions_task_specific(
        str(task.get("title") or ""),
        manifest_cases,
        indexed_cases,
    )
    if not contract_complete:
        issues.append("manifest_behavior_contract_incomplete")
    if not negative_cases_aligned:
        issues.append("negative_cases_index_mismatch")
    if not negative_descriptions_specific:
        issues.append("negative_descriptions_not_task_specific")

    generic_prompt_markers = [
        "checks the language feature named by this task",
        "deterministic voltage-domain stimulus",
        "Use voltage-coded logic with `vth = 0.45` V and high outputs near `0.9` V.",
    ]
    if all(marker in instruction for marker in generic_prompt_markers):
        issues.append("generic_prompt_template")
    if "Required Behavior" not in instruction:
        issues.append("missing_required_behavior_section")
    if "syntax:" in check_text and "sim_correct:" not in check_text:
        issues.append("checker_syntax_only_no_behavior_score")
    if "compile_supported" in str(task.get("certification_scope", "")):
        warnings.append("compile_scope_only")
    if str(task.get("tier", "")).endswith("candidate"):
        warnings.append("candidate_tier_not_score_ready")
    if visible_text and hidden_text and not visible_hidden_distinct:
        warnings.append("visible_hidden_identical")

    usable_scene = not any(issue in issues for issue in ("missing_instruction", "missing_target"))
    reasonable_task = (
        "generic_prompt_template" not in issues
        and "missing_required_behavior_section" not in issues
        and contract_complete
    )
    complete_tests = not any("scs_not_executable" in issue or issue.startswith("missing_") for issue in issues)
    fair_eval = (
        "checker_syntax_only_no_behavior_score" not in issues
        and neg_count >= 5
        and negative_cases_aligned
        and negative_descriptions_specific
    )
    sop_ready = usable_scene and reasonable_task and complete_tests and fair_eval

    return {
        "task": slug,
        "number": task_number(slug),
        "title": task.get("title", ""),
        "tier": task.get("tier", ""),
        "certification_scope": task.get("certification_scope", ""),
        "syntax_focus": task.get("syntax_focus", ""),
        "target": target_name,
        "solution_file_count": len(solution_files),
        "starter_file_count": len(starter_files),
        "visible_scs_count": len(visible_scs),
        "hidden_scs_count": len(hidden_scs),
        "visible_hidden_distinct": visible_hidden_distinct,
        "negative_count": neg_count,
        "behavior_contract_complete": contract_complete,
        "negative_cases_aligned": negative_cases_aligned,
        "negative_descriptions_task_specific": negative_descriptions_specific,
        "usable_scene": usable_scene,
        "reasonable_task": reasonable_task,
        "complete_tests": complete_tests,
        "fair_eval": fair_eval,
        "sop_ready": sop_ready,
        "issues": issues,
        "warnings": warnings,
    }


def write_csv(rows: list[dict[str, Any]]) -> None:
    fields = [
        "task",
        "number",
        "title",
        "tier",
        "target",
        "visible_hidden_distinct",
        "negative_count",
        "behavior_contract_complete",
        "negative_cases_aligned",
        "negative_descriptions_task_specific",
        "usable_scene",
        "reasonable_task",
        "complete_tests",
        "fair_eval",
        "sop_ready",
        "issues",
        "warnings",
    ]
    with REPORT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["issues"] = ";".join(row["issues"])
            out["warnings"] = ";".join(row["warnings"])
            writer.writerow({field: out.get(field, "") for field in fields})


def write_md(report: dict[str, Any]) -> None:
    summary = report["summary"]
    start_number = report["summary"]["min_task_number"]
    end_number = report["summary"]["max_task_number"]
    lines = [
        "# v3 Extension SOP Audit",
        "",
        f"Date: {report['date']}",
        "",
        "## Summary",
        "",
        f"- Audited extension tasks: **{summary['task_count']}**",
        f"- SOP-ready tasks: **{summary['sop_ready_count']}**",
        f"- Tasks with executable visible+hidden SCS evidence: **{summary['complete_tests_count']}**",
        f"- Tasks with behavior checker evidence: **{summary['fair_eval_count']}**",
        f"- Tasks with complete manifest behavior contracts: **{summary['behavior_contract_complete_count']}**",
        f"- Tasks with aligned negative case indexes: **{summary['negative_cases_aligned_count']}**",
        f"- Tasks with task-specific negative descriptions: **{summary['negative_descriptions_task_specific_count']}**",
        f"- Tasks with distinct visible/hidden SCS stimuli: **{summary['visible_hidden_distinct_count']}**",
        f"- Tasks with identical visible/hidden SCS stimuli: **{summary['visible_hidden_identical_count']}**",
        f"- SOP-ready tasks with identical visible/hidden SCS stimuli: **{summary['sop_ready_visible_hidden_identical_count']}**",
        f"- Staged tasks with identical visible/hidden SCS stimuli: **{summary['staged_visible_hidden_identical_count']}**",
        "",
        "## Issue Counts",
        "",
    ]
    for issue, count in summary["issue_counts"].items():
        lines.append(f"- `{issue}`: {count}")
    lines.extend([
        "",
        "## Warning Counts",
        "",
    ])
    for warning, count in summary["warning_counts"].items():
        lines.append(f"- `{warning}`: {count}")
    lines.extend([
        "",
        "## Range Summary",
        "",
        "| Range | Description | Tasks | Ready | Executable Tests | Behavior Eval | Contracts | Neg Index | Neg Desc | Distinct V/H | Top Issues |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ])
    for row in report["range_summary"]:
        top_issues = "<br>".join(f"`{issue}`: {count}" for issue, count in row["top_issues"])
        lines.append(
            f"| `{row['range']}` | {row['description']} | {row['task_count']} | "
            f"{row['sop_ready_count']} | {row['complete_tests_count']} | "
            f"{row['fair_eval_count']} | {row['behavior_contract_complete_count']} | "
            f"{row['negative_cases_aligned_count']} | {row['negative_descriptions_task_specific_count']} | "
            f"{row['visible_hidden_distinct_count']} | {top_issues} |"
        )
    lines.extend([
        "",
        "## Highest Severity Finding",
        "",
        f"Tasks {start_number:03d}-{end_number:03d} are staging-layer benchmark tasks outside the original "
        "full-300 denominator. Under the SOP they must retain concrete public "
        "behavior prompts, executable visible and hidden tests, repository "
        "behavior checkers, and five behavior-rejected negative variants.",
        "",
        "## Per-Task Rows",
        "",
        "| Task | Tier | Ready | Issues |",
        "| --- | --- | --- | --- |",
    ])
    for row in report["tasks"]:
        issues = "<br>".join(f"`{issue}`" for issue in row["issues"]) or "-"
        lines.append(f"| `{row['task']}` | `{row['tier']}` | {row['sop_ready']} | {issues} |")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    tasks = read_tasks()
    checks = read_checks_blocks()
    rows = [
        audit_task(slug, tasks[slug], checks)
        for slug in sorted(tasks, key=task_number)
        if task_number(slug) >= 301
    ]
    issue_counts = dict(sorted(Counter(issue for row in rows for issue in row["issues"]).items()))
    warning_counts = dict(sorted(Counter(warning for row in rows for warning in row["warnings"]).items()))
    min_task_number = min((row["number"] for row in rows), default=301)
    max_task_number = max((row["number"] for row in rows), default=300)
    range_summary = []
    for start, end, description in RANGE_GROUPS:
        group_rows = [row for row in rows if start <= row["number"] <= end]
        group_issues = Counter(issue for row in group_rows for issue in row["issues"])
        range_summary.append({
            "range": f"{start}-{end}",
            "description": description,
            "task_count": len(group_rows),
            "sop_ready_count": sum(row["sop_ready"] for row in group_rows),
            "complete_tests_count": sum(row["complete_tests"] for row in group_rows),
            "fair_eval_count": sum(row["fair_eval"] for row in group_rows),
            "behavior_contract_complete_count": sum(row["behavior_contract_complete"] for row in group_rows),
            "negative_cases_aligned_count": sum(row["negative_cases_aligned"] for row in group_rows),
            "negative_descriptions_task_specific_count": sum(
                row["negative_descriptions_task_specific"] for row in group_rows
            ),
            "visible_hidden_distinct_count": sum(row["visible_hidden_distinct"] for row in group_rows),
            "top_issues": group_issues.most_common(5),
        })
    report = {
        "date": date.today().isoformat(),
        "scope": f"benchmark-vabench-release-v3 tasks {min_task_number:03d}-{max_task_number:03d}",
        "standard": "behavioral-veriloga-vela/SOP.md visible/hidden task standard and four quality criteria",
        "summary": {
            "task_count": len(rows),
            "min_task_number": min_task_number,
            "max_task_number": max_task_number,
            "sop_ready_count": sum(row["sop_ready"] for row in rows),
            "complete_tests_count": sum(row["complete_tests"] for row in rows),
            "fair_eval_count": sum(row["fair_eval"] for row in rows),
            "behavior_contract_complete_count": sum(row["behavior_contract_complete"] for row in rows),
            "negative_cases_aligned_count": sum(row["negative_cases_aligned"] for row in rows),
            "negative_descriptions_task_specific_count": sum(
                row["negative_descriptions_task_specific"] for row in rows
            ),
            "visible_hidden_distinct_count": sum(row["visible_hidden_distinct"] for row in rows),
            "visible_hidden_identical_count": sum(
                row["visible_scs_count"] > 0
                and row["hidden_scs_count"] > 0
                and not row["visible_hidden_distinct"]
                for row in rows
            ),
            "sop_ready_visible_hidden_identical_count": sum(
                row["sop_ready"]
                and row["visible_scs_count"] > 0
                and row["hidden_scs_count"] > 0
                and not row["visible_hidden_distinct"]
                for row in rows
            ),
            "staged_visible_hidden_identical_count": sum(
                not row["sop_ready"]
                and row["visible_scs_count"] > 0
                and row["hidden_scs_count"] > 0
                and not row["visible_hidden_distinct"]
                for row in rows
            ),
            "issue_counts": issue_counts,
            "warning_counts": warning_counts,
        },
        "range_summary": range_summary,
        "tasks": rows,
    }
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(rows)
    write_md(report)
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
