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
PACKAGE_ROOT = ROOT / "benchmark-vabench-release-v3"
REPORTS_ROOT = PACKAGE_ROOT / "reports"
TASKS_JSON = PACKAGE_ROOT / "TASKS.json"
CHECKS_YAML = PACKAGE_ROOT / "CHECKS.yaml"
REPORT_JSON = REPORTS_ROOT / "layered_certification.json"
REPORT_MD = REPORTS_ROOT / "layered_certification.md"
REPORT_CSV = REPORTS_ROOT / "layered_certification_tasks.csv"
STAGED_BLOCKER_JSON = REPORTS_ROOT / "staged_blocker_matrix.json"
STAGED_BLOCKER_MD = REPORTS_ROOT / "staged_blocker_matrix.md"
STAGED_BLOCKER_CSV = REPORTS_ROOT / "staged_blocker_matrix.csv"
BEHAVIOR_EXTENSION_EVIDENCE_JSON = REPORTS_ROOT / "behavior_certified_extension_task_evidence.json"
EXTENSION_SOP_AUDIT_JSON = REPORTS_ROOT / "extension_sop_audit.json"
STAGED_GOLD_PROBE_JSON = REPORTS_ROOT / "staged_promotion_gold_probe.json"

SPECTRE_DIVERGENT_TASKS = {
    "391-rdist-exponential-jitter": "seeded random exponential sequence differs from Spectre",
    "392-rdist-poisson-count-noise": "seeded random poisson sequence differs from Spectre",
    "393-rdist-normal-offset-dither": "seeded random normal sequence differs from Spectre",
    "396-rdist-erlang-latency": "seeded random erlang sequence differs from Spectre",
    "404-vector-part-select-window": "integer vector part-select behavior differs from Spectre",
    "405-vector-concat-code-build": "integer vector concatenation behavior differs from Spectre",
}


CORE_TIERS = {
    "<none>",
    "formal-candidate",
    "core-formal-candidate",
    "support-formal-candidate",
}

TIER_TO_LAYER = {
    "<none>": (
        "behavioral_event_core",
        "behavior_certified",
        "Inherited original full-300 behavior-certified surface.",
    ),
    "formal-candidate": (
        "behavioral_event_core",
        "behavior_certified",
        "Inherited original full-300 behavior-certified surface.",
    ),
    "core-formal-candidate": (
        "behavioral_event_core",
        "behavior_certified",
        "Inherited original full-300 behavior-certified surface.",
    ),
    "support-formal-candidate": (
        "behavioral_event_support",
        "behavior_certified_support",
        "Inherited original full-300 certified support surface; scoring follows the original denominator policy.",
    ),
    "syntax-extension-candidate": (
        "behavioral_language_extension",
        "compile_supported_candidate",
        "Reference solution compiles with current local EVAS, but behavior checker promotion is still pending.",
    ),
    "ams-mixed-signal-candidate": (
        "ams_mixed_signal_extension",
        "compile_supported_candidate",
        "Verilog-AMS/digital-mixed-signal syntax candidate; not part of the original full-300 behavior claim.",
    ),
    "noise-analysis-candidate": (
        "noise_analysis_extension",
        "compile_supported_candidate",
        "Noise/analysis helper syntax candidate; AC/noise behavior certification is pending.",
    ),
    "cadence-simulator-function-candidate": (
        "cadence_simulator_function_extension",
        "compile_supported_candidate",
        "Cadence simulator helper syntax candidate; behavior certification is pending.",
    ),
    "cadence-derived-data-converter-candidate": (
        "cadence_derived_data_converter_extension",
        "compile_supported_candidate",
        "Cadence-derived data-converter candidate; behavior certification is tracked outside the original full-300 denominator.",
    ),
    "data-converter-replacement-candidate": (
        "data_converter_replacement_candidate",
        "compile_supported_candidate",
        "Materialized data-converter replacement candidate; behavior certification is tracked outside the original full-300 denominator and final counted numbering remains an upstream policy decision.",
    ),
    "behavior-extension-candidate": (
        "behavioral_language_extension",
        "compile_supported_candidate",
        "PLL/clock-timing behavioral extension candidate; behavior certification is tracked outside the original full-300 denominator.",
    ),
    "behavioral-continuous-time-candidate": (
        "behavioral_continuous_time_extension",
        "compile_supported_continuous_time_candidate",
        "Continuous-time operator syntax compiles; dynamic-solver accuracy is not certified.",
    ),
    "behavioral-control-candidate": (
        "behavioral_language_extension",
        "compile_supported_candidate",
        "Integer/vector control behavior candidate; full Spectre-aligned behavior certification is pending.",
    ),
    "kcl-syntax-candidate": (
        "conservative_kcl_syntax_extension",
        "compile_supported_kcl_candidate",
        "KCL/current-contribution syntax compiles; MNA/KCL behavior is not certified.",
    ),
    "conservative-current/KCL-behavior-certified": (
        "conservative_kcl_syntax_extension",
        "behavior_certified_extension",
        "KCL/current-contribution behavior is certified only for the repository's voltage/current trace contract.",
    ),
}


def read_tasks() -> dict[str, Any]:
    return json.loads(TASKS_JSON.read_text(encoding="utf-8"))["tasks"]


def task_number(key: str) -> int:
    return int(key.split("-", 1)[0])


def extension_bounds(tasks: dict[str, Any]) -> tuple[int, int]:
    extension_numbers = [task_number(key) for key in tasks if task_number(key) > 300]
    if not extension_numbers:
        return 301, 300
    return min(extension_numbers), max(extension_numbers)


def verify_layered_json(tasks: dict[str, Any] | None = None) -> Path:
    if tasks is None:
        tasks = read_tasks()
    start, end = extension_bounds(tasks)
    return REPORTS_ROOT / f"verify_{start:03d}_{end:03d}_layered.json"


def read_sop_ready_extension_tasks() -> set[str]:
    if not EXTENSION_SOP_AUDIT_JSON.exists():
        return set()
    try:
        audit = json.loads(EXTENSION_SOP_AUDIT_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    ready: set[str] = set()
    for row in audit.get("tasks", []):
        if isinstance(row, dict) and row.get("sop_ready") is True:
            task_key = str(row.get("task") or "").strip()
            if task_key:
                ready.add(task_key)
    return ready


def read_sop_audit() -> dict[str, Any]:
    if not EXTENSION_SOP_AUDIT_JSON.exists():
        return {}
    try:
        return json.loads(EXTENSION_SOP_AUDIT_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def read_layered_verification_summary() -> dict[str, Any]:
    verify_json = verify_layered_json()
    if not verify_json.exists():
        return {}
    try:
        payload = json.loads(verify_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    summary = payload.get("summary")
    return summary if isinstance(summary, dict) else {}


def read_layered_verification_payload() -> dict[str, Any]:
    verify_json = verify_layered_json()
    if not verify_json.exists():
        return {}
    try:
        payload = json.loads(verify_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def read_behavior_verified_extension_tasks() -> set[str]:
    payload = read_layered_verification_payload()
    rows = payload.get("rows", []) if isinstance(payload, dict) else []
    gold_by_task: dict[str, dict[str, Any]] = {}
    negative_by_task: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        task = str(row.get("task_slug") or "")
        if not task:
            continue
        if row.get("kind") == "gold":
            gold_by_task[task] = row
        elif row.get("kind") == "negative":
            negative_by_task.setdefault(task, []).append(row)
    ready: set[str] = set()
    for task, gold in gold_by_task.items():
        negatives = negative_by_task.get(task, [])
        gold_ok = gold.get("status") == "PASS" and gold.get("meets_expectation") is True
        negatives_ok = (
            len(negatives) >= 5
            and all(row.get("status") != "PASS" for row in negatives)
            and all(row.get("meets_expectation") is True for row in negatives)
        )
        if gold_ok and negatives_ok:
            ready.add(task)
    return ready


def read_staged_gold_probe() -> dict[str, Any]:
    if not STAGED_GOLD_PROBE_JSON.exists():
        return {}
    try:
        payload = json.loads(STAGED_GOLD_PROBE_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def read_checks_issue_urls() -> dict[str, list[str]]:
    if not CHECKS_YAML.exists():
        return {}
    issue_pattern = re.compile(r"https://github\.com/Arcadia-1/EVAS/issues/\d+")
    issue_urls: dict[str, list[str]] = {}
    current_key: str | None = None
    current_lines: list[str] = []
    for line in CHECKS_YAML.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line and not line.startswith((" ", "\t")) and line.endswith(": |"):
            if current_key is not None:
                urls = sorted(set(issue_pattern.findall("\n".join(current_lines))))
                if urls:
                    issue_urls[current_key] = urls
            current_key = line.split(":", 1)[0]
            current_lines = []
            continue
        if current_key is not None:
            current_lines.append(line)
    if current_key is not None:
        urls = sorted(set(issue_pattern.findall("\n".join(current_lines))))
        if urls:
            issue_urls[current_key] = urls
    return issue_urls


def classify_task(
    key: str,
    task: dict[str, Any],
    behavior_ready_extension_tasks: set[str],
    checks_issue_urls: dict[str, list[str]],
) -> dict[str, Any]:
    tier = str(task.get("tier") or "<none>")
    if tier not in TIER_TO_LAYER:
        raise ValueError(f"unknown tier for {key}: {tier}")
    semantic_layer, certification_level, claim_boundary = TIER_TO_LAYER[tier]
    number = task_number(key)
    in_original_full_300 = number <= 300
    extension_candidate = number > 300
    behavior_ready_extension = extension_candidate and key in behavior_ready_extension_tasks
    spectre_divergent = key in SPECTRE_DIVERGENT_TASKS
    if behavior_ready_extension:
        certification_level = "behavior_certified_extension"
        claim_boundary = (
            "Extension task has SOP-ready behavior evidence: executable visible/hidden tests, "
            "repository behavior checker, and five rejected negative variants. It remains outside "
            "the original full-300 denominator."
        )
    if spectre_divergent:
        certification_level = (
            "behavior_certified_extension_spectre_divergent"
            if behavior_ready_extension
            else "spectre_divergent_candidate"
        )
        claim_boundary = (
            "EVAS/checker behavior evidence exists, but the 2026-07-04 Spectre-parity audit records "
            f"a retained-row behavior mismatch: {SPECTRE_DIVERGENT_TASKS[key]}. Recalibrate the "
            "gold/checker contract against Spectre before full Spectre-certified or scored claims."
        )
    return {
        "task_key": key,
        "task_number": number,
        "task_id": task.get("id", ""),
        "title": task.get("title", ""),
        "form": task.get("form", ""),
        "category": task.get("category", ""),
        "tier": tier,
        "semantic_layer": semantic_layer,
        "certification_level": certification_level,
        "in_original_full_300": in_original_full_300,
        "extension_candidate": extension_candidate,
        "behavior_certified": certification_level.startswith("behavior_certified"),
        "score_claim": (
            "excluded_spectre_divergent_pending_recalibration"
            if spectre_divergent
            else
            "original_full_300_policy"
            if in_original_full_300
            else "extension_behavior_certified_outside_original_300"
            if behavior_ready_extension
            else "excluded_until_behavior_promotion"
        ),
        "claim_boundary": claim_boundary,
        "spectre_parity_status": "spectre_divergent" if spectre_divergent else "not_marked_divergent",
        "spectre_recalibration_required": spectre_divergent,
        "spectre_divergence_reason": SPECTRE_DIVERGENT_TASKS.get(key, ""),
        "blocking_issue_urls": ";".join(checks_issue_urls.get(key, [])),
        "target": ";".join(task.get("target", [])),
        "syntax_focus": task.get("syntax_focus", ""),
        "certification_scope": task.get("certification_scope", "original_full_300_claim"),
    }


def counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row[key]) for row in rows).items()))


def promotion_command_for(blocked_rows: list[dict[str, Any]]) -> str:
    numbers = sorted(int(row["task_number"]) for row in blocked_rows)
    if not numbers:
        return ""
    task_filter = ",".join(f"{number:03d}" for number in numbers)
    return (
        "PYTHONPATH=runners VAEVAS_DEFAULT_EVAS_ENGINE=python "
        "VAEVAS_EVAS_PERSISTENT_WORKER=0 PATH=\"$PWD/.venv-evas/bin:$PATH\" "
        ".venv-evas/bin/python scripts/run_v3_gold_negative_verification.py "
        f"--start {numbers[0]} --end {numbers[-1]} --tasks {task_filter} "
        "--include-staged --timeout 120 --jobs 1 "
        f"--out benchmark-vabench-release-v3/reports/verify_issue_{numbers[0]}_{numbers[-1]}.json"
    )


def task_promotion_command_for(row: dict[str, Any]) -> str:
    number = int(row["task_number"])
    task_filter = f"{number:03d}"
    return (
        "PYTHONPATH=runners VAEVAS_DEFAULT_EVAS_ENGINE=python "
        "VAEVAS_EVAS_PERSISTENT_WORKER=0 PATH=\"$PWD/.venv-evas/bin:$PATH\" "
        ".venv-evas/bin/python scripts/run_v3_gold_negative_verification.py "
        f"--start {number} --end {number} --tasks {task_filter} "
        "--include-staged --timeout 120 --jobs 1 "
        f"--out benchmark-vabench-release-v3/reports/verify_task_{number:03d}.json"
    )


def task_promotion_acceptance_for(row: dict[str, Any]) -> str:
    return (
        f"Promote `{row['task_key']}` only after adding repository sim_correct evidence, then require "
        "1/1 gold PASS, 5/5 negative variants rejected, and zero expectation_fail in the per-task report."
    )


def promotion_acceptance_for(blocked_rows: list[dict[str, Any]]) -> str:
    task_count = len(blocked_rows)
    negative_count = task_count * 5
    return (
        f"After EVAS support lands, promote the listed {task_count} task(s) by adding sim_correct "
        "behavior contracts/checkers if missing, then require "
        f"{task_count}/{task_count} gold PASS, {negative_count}/{negative_count} negative variants rejected, "
        "and zero expectation_fail in the verification report."
    )


def build_completion_audit(
    summary: dict[str, Any],
    sop_audit: dict[str, Any],
    verification_summary: dict[str, Any],
    blocking_issues: list[dict[str, Any]],
) -> dict[str, Any]:
    sop_summary = sop_audit.get("summary", {}) if isinstance(sop_audit, dict) else {}
    issue_counts = sop_summary.get("issue_counts", {}) if isinstance(sop_summary, dict) else {}
    staged_count = summary["compile_supported_candidate_count"]
    expected_extension_count = summary["task_count"] - summary["original_full_300_count"]
    extension_start = summary["original_full_300_count"] + 1
    extension_end = summary["task_count"]
    verify_report_label = f"verify_{extension_start:03d}_{extension_end:03d}_layered"
    verification_ok = (
        verification_summary.get("gold_pass") == summary["behavior_certified_extension_count"]
        and verification_summary.get("gold_fail") == 0
        and verification_summary.get("negative_accepted") == 0
        and verification_summary.get("expectation_fail") == 0
    )
    fair_eval_ok = (
        summary["behavior_certified_extension_count"] == expected_extension_count
        and staged_count == 0
    )
    staged_issue_ok = (
        staged_count == 0
        or (
            sum(issue["task_count"] for issue in blocking_issues) == staged_count
            and all(issue.get("promotion_command") and issue.get("promotion_acceptance") for issue in blocking_issues)
        )
    )
    spectre_divergent_count = int(summary.get("spectre_divergent_count", 0) or 0)
    requirements = [
        {
            "requirement": f"Scope covers all v3 extension tasks {extension_start:03d}-{extension_end:03d}.",
            "status": (
                "satisfied"
                if summary["extension_candidate_count"] == expected_extension_count
                else "not_satisfied"
            ),
            "evidence": f"layered_certification summary reports extension_candidate_count={summary['extension_candidate_count']}.",
        },
        {
            "requirement": "Each extension task has a clear prompt and required behavior section.",
            "status": "satisfied" if issue_counts.get("missing_required_behavior_section", 0) == 0 else "not_satisfied",
            "evidence": "extension_sop_audit has no missing_required_behavior_section issue.",
        },
        {
            "requirement": "Each extension task has executable visible and hidden test evidence.",
            "status": (
                "satisfied"
                if sop_summary.get("complete_tests_count") == expected_extension_count
                else "not_satisfied"
            ),
            "evidence": f"extension_sop_audit complete_tests_count={sop_summary.get('complete_tests_count')}.",
        },
        {
            "requirement": "Each extension task has five useful negative variants.",
            "status": "satisfied" if not any(str(key).startswith("negative_count_lt5") for key in issue_counts) else "not_satisfied",
            "evidence": "extension_sop_audit reports no negative_count_lt5 issues.",
        },
        {
            "requirement": "Each extension task has repository behavior checker evidence and can be scored fairly.",
            "status": "satisfied" if fair_eval_ok else "partial",
            "evidence": (
                f"{summary['behavior_certified_extension_count']} extension tasks are behavior-certified; "
                f"{staged_count} remain excluded_until_behavior_promotion."
            ),
            "gap": "" if fair_eval_ok else (
                "The remaining staged rows are blocked by EVAS support issues or missing "
                "behavior-checker evidence; staged_promotion_gold_probe records the current "
                "per-task blocker."
            ),
        },
        {
            "requirement": "Behavior-certified extension tasks pass gold verification and reject all negative variants.",
            "status": "satisfied" if verification_ok else "not_satisfied",
            "evidence": (
                f"{verify_report_label}: gold_pass={verification_summary.get('gold_pass')}, "
                f"gold_fail={verification_summary.get('gold_fail')}, "
                f"negative_rejected={verification_summary.get('negative_rejected')}, "
                f"negative_accepted={verification_summary.get('negative_accepted')}, "
                f"expectation_fail={verification_summary.get('expectation_fail')}."
            ),
        },
        {
            "requirement": "Every staged task has a concrete EVAS issue and promotion checklist.",
            "status": "satisfied" if staged_issue_ok else "not_satisfied",
            "evidence": (
                "No staged tasks remain; no EVAS promotion blockers are required."
                if staged_count == 0
                else (
                    f"{len(blocking_issues)} blocking issues cover "
                    f"{sum(issue['task_count'] for issue in blocking_issues)} staged tasks; "
                    "staged_promotion_gold_probe records "
                    f"{staged_count}/{staged_count} staged gold cases still failing the current promotion gate."
                )
            ),
        },
        {
            "requirement": "No retained default row is marked spectre-divergent for a full Spectre-certified claim.",
            "status": "satisfied" if spectre_divergent_count == 0 else "not_satisfied",
            "evidence": (
                "No spectre-divergent retained rows are listed."
                if spectre_divergent_count == 0
                else f"{spectre_divergent_count} retained row(s) require Spectre recalibration."
            ),
            "gap": "" if spectre_divergent_count == 0 else (
                "Recalibrate the affected gold/checker contracts against Spectre before enabling a full "
                "Spectre-certified or formal score-denominator claim."
            ),
        },
    ]
    is_complete = all(item["status"] == "satisfied" for item in requirements)
    return {
        "status": "complete" if is_complete else "partial_external_blocked",
        "is_complete": is_complete,
        "reason": (
            f"All {expected_extension_count} extension tasks have behavior checker evidence, "
            "gold verification, and five rejected negative variants."
            if is_complete
            else (
                f"The full {extension_start:03d}-{extension_end:03d} objective is not complete because "
                f"{staged_count} extension tasks still lack "
                "behavior checker evidence and are excluded until EVAS support issues are resolved."
            )
        ),
        "requirements": requirements,
    }


def build_report() -> dict[str, Any]:
    tasks = read_tasks()
    extension_start, extension_end = extension_bounds(tasks)
    sop_audit = read_sop_audit()
    behavior_ready_extension_tasks = (
        read_sop_ready_extension_tasks()
        | read_behavior_verified_extension_tasks()
    )
    verification_summary = read_layered_verification_summary()
    checks_issue_urls = read_checks_issue_urls()
    rows = [
        classify_task(key, tasks[key], behavior_ready_extension_tasks, checks_issue_urls)
        for key in sorted(tasks, key=task_number)
    ]
    extension_rows = [row for row in rows if row["extension_candidate"]]
    behavior_rows = [row for row in rows if row["behavior_certified"]]
    compile_rows = [
        row for row in rows
        if str(row["certification_level"]).startswith("compile_supported")
    ]
    summary = {
        "task_count": len(rows),
        "original_full_300_count": sum(row["in_original_full_300"] for row in rows),
        "extension_candidate_count": len(extension_rows),
        "behavior_certified_count": len(behavior_rows),
        "behavior_certified_extension_count": sum(
            row["extension_candidate"] and row["behavior_certified"] for row in rows
        ),
        "compile_supported_candidate_count": len(compile_rows),
        "unsupported_candidate_count": sum(row["tier"] == "evas-unsupported-candidate" for row in rows),
        "tier_counts": counter(rows, "tier"),
        "semantic_layer_counts": counter(rows, "semantic_layer"),
        "certification_level_counts": counter(rows, "certification_level"),
        "score_claim_counts": counter(rows, "score_claim"),
        "spectre_parity_status_counts": counter(rows, "spectre_parity_status"),
        "spectre_divergent_count": sum(row["spectre_recalibration_required"] for row in rows),
        "spectre_divergent_tasks": [
            row["task_key"]
            for row in rows
            if row["spectre_recalibration_required"]
        ],
        "blocking_issue_counts": dict(sorted(Counter(
            issue_url
            for row in rows
            if row["score_claim"] == "excluded_until_behavior_promotion"
            for issue_url in str(row["blocking_issue_urls"]).split(";")
            if issue_url
        ).items())),
    }
    blocking_issues = []
    for issue_url, count in summary["blocking_issue_counts"].items():
        blocked_rows = [
            row for row in rows
            if issue_url in str(row["blocking_issue_urls"]).split(";")
            and row["score_claim"] == "excluded_until_behavior_promotion"
        ]
        blocking_issues.append({
            "issue_url": issue_url,
            "task_count": count,
            "semantic_layers": counter(blocked_rows, "semantic_layer"),
            "promotion_command": promotion_command_for(blocked_rows),
            "promotion_acceptance": promotion_acceptance_for(blocked_rows),
            "tasks": [
                {
                    "task_key": row["task_key"],
                    "task_id": row["task_id"],
                    "title": row["title"],
                    "tier": row["tier"],
                    "semantic_layer": row["semantic_layer"],
                    "target": row["target"],
                }
                for row in blocked_rows
            ],
        })
    return {
        "date": date.today().isoformat(),
        "release": "benchmark-vabench-release-v3",
        "status": (
            "layered_complete"
            if summary["compile_supported_candidate_count"] == 0
            and summary["spectre_divergent_count"] == 0
            else "layered_partial_spectre_divergent"
            if summary["spectre_divergent_count"]
            else "layered_partial"
        ),
        "summary": summary,
        "layers": [
            {
                "semantic_layer": layer,
                "task_count": count,
                "certification_levels": counter(
                    [row for row in rows if row["semantic_layer"] == layer],
                    "certification_level",
                ),
            }
            for layer, count in summary["semantic_layer_counts"].items()
        ],
        "blocking_issues": blocking_issues,
        "completion_audit": build_completion_audit(
            summary,
            sop_audit,
            verification_summary,
            blocking_issues,
        ),
        "claim_boundary": [
            "Only tasks 001-300 are part of the original behavior-certified full-300 claim.",
            f"Tasks {extension_start:03d}-{extension_end:03d} are behavior-certified extension rows outside the original full-300 denominator.",
            "Rows marked spectre-divergent are excluded from full Spectre-certified and score-denominator claims until recalibrated.",
            "Continuous-time rows certify the repository's finite-difference/stateful behavioral response, not a general analog solver accuracy claim.",
            "KCL/current rows certify observable branch-current contribution behavior, not unknown-node MNA/KCL solving.",
            "AMS, noise/analysis, Cadence-helper, Cadence-derived data-converter, and table-model extension rows are certified only for their layer-specific transient/checker contracts.",
        ],
        "evidence_sources": {
            "task_manifest": "benchmark-vabench-release-v3/TASKS.json",
            "checker_manifest": "benchmark-vabench-release-v3/CHECKS.yaml",
            "extension_sop_audit": "benchmark-vabench-release-v3/reports/extension_sop_audit.json",
            "behavior_certified_extension_task_evidence": "benchmark-vabench-release-v3/reports/behavior_certified_extension_task_evidence.json",
            "language_extension_notes": "benchmark-vabench-release-v3/LANGUAGE_EXTENSION.md",
            "core_behavior_evidence": "benchmark-vabench-release-v1/reports/benchmark_overview.json",
            "staged_gold_probe": "benchmark-vabench-release-v3/reports/staged_promotion_gold_probe.json",
            "staged_gold_probe_summary": "benchmark-vabench-release-v3/reports/staged_promotion_gold_probe.md",
            "staged_blocker_matrix": "benchmark-vabench-release-v3/reports/staged_blocker_matrix.json",
            "staged_blocker_matrix_summary": "benchmark-vabench-release-v3/reports/staged_blocker_matrix.md",
            "latest_compile_probe": "local EVAS compile/verification probes cover the current staging rows and their five negative variants per task.",
        },
        "task_rows": rows,
    }


def write_csv(rows: list[dict[str, Any]]) -> None:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    fields = [
        "task_key",
        "task_number",
        "task_id",
        "title",
        "tier",
        "semantic_layer",
        "certification_level",
        "behavior_certified",
        "score_claim",
        "spectre_parity_status",
        "spectre_recalibration_required",
        "spectre_divergence_reason",
        "claim_boundary",
        "blocking_issue_urls",
        "target",
    ]
    with REPORT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def build_staged_blocker_matrix(report: dict[str, Any]) -> dict[str, Any]:
    probe = read_staged_gold_probe()
    probe_rows = {
        str(row.get("task_slug")): row
        for row in probe.get("rows", [])
        if isinstance(row, dict) and row.get("task_slug")
    }
    issue_commands = {
        issue["issue_url"]: {
            "promotion_command": issue.get("promotion_command", ""),
            "promotion_acceptance": issue.get("promotion_acceptance", ""),
        }
        for issue in report["blocking_issues"]
    }
    rows: list[dict[str, Any]] = []
    for task in report["task_rows"]:
        if task["score_claim"] != "excluded_until_behavior_promotion":
            continue
        issue_urls = [
            issue_url
            for issue_url in str(task.get("blocking_issue_urls", "")).split(";")
            if issue_url
        ]
        probe_row = probe_rows.get(task["task_key"], {})
        rows.append({
            "task_key": task["task_key"],
            "task_id": task["task_id"],
            "title": task["title"],
            "tier": task["tier"],
            "semantic_layer": task["semantic_layer"],
            "target": task["target"],
            "issue_urls": issue_urls,
            "probe_status": probe_row.get("status", ""),
            "failure_summary": probe_row.get("failure_summary", ""),
            "task_promotion_command": task_promotion_command_for(task),
            "task_promotion_acceptance": task_promotion_acceptance_for(task),
            "promotion_commands": [
                issue_commands.get(issue_url, {}).get("promotion_command", "")
                for issue_url in issue_urls
            ],
            "promotion_acceptance": [
                issue_commands.get(issue_url, {}).get("promotion_acceptance", "")
                for issue_url in issue_urls
            ],
        })
    missing_issue = [row["task_key"] for row in rows if not row["issue_urls"]]
    missing_probe = [row["task_key"] for row in rows if not row["failure_summary"]]
    return {
        "date": report["date"],
        "release": report["release"],
        "summary": {
            "staged_task_count": len(rows),
            "missing_issue_count": len(missing_issue),
            "missing_failure_summary_count": len(missing_probe),
            "issue_count": len({issue_url for row in rows for issue_url in row["issue_urls"]}),
            "semantic_layer_counts": dict(sorted(Counter(row["semantic_layer"] for row in rows).items())),
        },
        "missing_issue_tasks": missing_issue,
        "missing_failure_summary_tasks": missing_probe,
        "tasks": rows,
    }


def write_staged_blocker_csv(matrix: dict[str, Any]) -> None:
    fields = [
        "task_key",
        "task_id",
        "title",
        "tier",
        "semantic_layer",
        "target",
        "issue_urls",
        "probe_status",
        "failure_summary",
        "task_promotion_command",
        "task_promotion_acceptance",
    ]
    with STAGED_BLOCKER_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in matrix["tasks"]:
            writer.writerow({
                "task_key": row["task_key"],
                "task_id": row["task_id"],
                "title": row["title"],
                "tier": row["tier"],
                "semantic_layer": row["semantic_layer"],
                "target": row["target"],
                "issue_urls": ";".join(row["issue_urls"]),
                "probe_status": row["probe_status"],
                "failure_summary": row["failure_summary"],
                "task_promotion_command": row["task_promotion_command"],
                "task_promotion_acceptance": row["task_promotion_acceptance"],
            })


def write_staged_blocker_md(matrix: dict[str, Any]) -> None:
    summary = matrix["summary"]
    lines = [
        "# v3 Staged Blocker Matrix",
        "",
        f"Date: {matrix['date']}",
        "",
        "## Summary",
        "",
        f"- Staged tasks: **{summary['staged_task_count']}**",
        f"- Distinct blocking issues: **{summary['issue_count']}**",
        f"- Missing issue links: **{summary['missing_issue_count']}**",
        f"- Missing failure summaries: **{summary['missing_failure_summary_count']}**",
        "",
        "## Tasks",
        "",
        "| Task | Layer | Issue | Probe status | Failure summary | Per-task promotion command |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in matrix["tasks"]:
        issues = "<br>".join(row["issue_urls"])
        summary_text = str(row["failure_summary"]).replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| `{row['task_key']}` | `{row['semantic_layer']}` | {issues} | "
            f"`{row['probe_status']}` | {summary_text} | `{row['task_promotion_command']}` |"
        )
    lines.append("")
    STAGED_BLOCKER_MD.write_text("\n".join(lines), encoding="utf-8")


def write_staged_blocker_matrix(report: dict[str, Any]) -> None:
    matrix = build_staged_blocker_matrix(report)
    STAGED_BLOCKER_JSON.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_staged_blocker_csv(matrix)
    write_staged_blocker_md(matrix)


def write_behavior_extension_evidence(report: dict[str, Any]) -> None:
    verification = {}
    verify_json = verify_layered_json()
    if verify_json.exists():
        try:
            verification = json.loads(verify_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            verification = {}
    rows = verification.get("rows", []) if isinstance(verification, dict) else []
    gold_by_task = {
        str(row.get("task_slug")): row
        for row in rows
        if isinstance(row, dict) and row.get("kind") == "gold"
    }
    negative_statuses_by_task: dict[str, dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("kind") != "negative":
            continue
        task = str(row.get("task_slug") or "")
        variant = str(row.get("variant") or "")
        if task and variant:
            negative_statuses_by_task.setdefault(task, {})[variant] = str(row.get("status") or "")

    behavior_extension_rows = [
        row for row in report["task_rows"]
        if row["extension_candidate"] and row["behavior_certified"]
    ]
    task_rows: list[dict[str, Any]] = []
    for task in behavior_extension_rows:
        task_key = task["task_key"]
        gold = gold_by_task.get(task_key, {})
        negative_statuses = negative_statuses_by_task.get(task_key, {})
        negative_rejected = {
            variant: status
            for variant, status in negative_statuses.items()
            if status == "FAIL_SIM_CORRECTNESS"
        }
        task_rows.append({
            "task": task_key,
            "checker_task_id": gold.get("checker_task_id"),
            "gold_status": gold.get("status"),
            "gold_meets_expectation": gold.get("meets_expectation"),
            "negative_count": len(negative_statuses),
            "negative_statuses": negative_statuses,
            "negative_behavior_rejected_count": len(negative_rejected),
            "all_negatives_behavior_rejected": len(negative_statuses) == 5 and len(negative_rejected) == 5,
        })

    payload = {
        "summary": {
            "source_report": str(verify_json.relative_to(ROOT)),
            "task_count": len(task_rows),
            "gold_pass_count": sum(row["gold_status"] == "PASS" for row in task_rows),
            "negative_total": sum(row["negative_count"] for row in task_rows),
            "negative_behavior_rejected_total": sum(
                row["negative_behavior_rejected_count"] for row in task_rows
            ),
            "all_tasks_have_five_behavior_rejected_negatives": all(
                row["all_negatives_behavior_rejected"] for row in task_rows
            ),
        },
        "tasks": task_rows,
    }
    BEHAVIOR_EXTENSION_EVIDENCE_JSON.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_md(report: dict[str, Any]) -> None:
    summary = report["summary"]
    lines = [
        "# vaBench v3 Layered Certification",
        "",
        f"Date: {report['date']}",
        "",
        "## Headline",
        "",
        f"- Total tasks: **{summary['task_count']}**",
        f"- Original behavior-certified full-300 surface: **{summary['original_full_300_count']}**",
        f"- Extension candidates: **{summary['extension_candidate_count']}**",
        f"- Behavior-certified extension rows: **{summary['behavior_certified_extension_count']}**",
        f"- Compile-supported candidate rows: **{summary['compile_supported_candidate_count']}**",
        f"- Unsupported candidate rows: **{summary['unsupported_candidate_count']}**",
        f"- Spectre-divergent retained rows: **{summary['spectre_divergent_count']}**",
        "",
        "## Semantic Layers",
        "",
        "| Layer | Tasks | Certification levels |",
        "| --- | ---: | --- |",
    ]
    for layer in report["layers"]:
        levels = ", ".join(
            f"{name}: {count}"
            for name, count in layer["certification_levels"].items()
        )
        lines.append(f"| `{layer['semantic_layer']}` | {layer['task_count']} | {levels} |")
    lines.extend([
        "",
        "## Blocking Issues",
        "",
        "| EVAS issue | Blocked tasks | Semantic layers | Promotion acceptance |",
        "| --- | ---: | --- | --- |",
    ])
    for issue in report["blocking_issues"]:
        layers = ", ".join(
            f"{name}: {count}"
            for name, count in issue["semantic_layers"].items()
        )
        lines.append(
            f"| {issue['issue_url']} | {issue['task_count']} | {layers} | "
            f"{issue['promotion_acceptance']} |"
        )
    lines.extend([
        "",
        "## Spectre-Divergent Rows",
        "",
        "| Task | Reason |",
        "| --- | --- |",
    ])
    divergent_rows = [
        row for row in report["task_rows"]
        if row["spectre_recalibration_required"]
    ]
    if divergent_rows:
        for row in divergent_rows:
            reason = str(row["spectre_divergence_reason"]).replace("|", "\\|")
            lines.append(f"| `{row['task_key']}` | {reason} |")
    else:
        lines.append("| - | - |")
    lines.extend([
        "",
        "## Completion Audit",
        "",
        f"- Status: `{report['completion_audit']['status']}`",
        f"- Complete: `{str(report['completion_audit']['is_complete']).lower()}`",
        f"- Reason: {report['completion_audit']['reason']}",
        "",
        "| Requirement | Status | Evidence | Gap |",
        "| --- | --- | --- | --- |",
    ])
    for item in report["completion_audit"]["requirements"]:
        lines.append(
            f"| {item['requirement']} | `{item['status']}` | {item.get('evidence', '')} | {item.get('gap', '')} |"
        )
    lines.extend([
        "",
        "## Claim Boundary",
        "",
    ])
    lines.extend(f"- {item}" for item in report["claim_boundary"])
    lines.extend([
        "",
        "## Evidence Sources",
        "",
        "| Evidence | Path / note |",
        "| --- | --- |",
    ])
    for key, value in report["evidence_sources"].items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    report = build_report()
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(report["task_rows"])
    write_md(report)
    write_behavior_extension_evidence(report)
    write_staged_blocker_matrix(report)
    print(f"wrote {REPORT_JSON.relative_to(ROOT)}")
    print(f"wrote {REPORT_CSV.relative_to(ROOT)}")
    print(f"wrote {REPORT_MD.relative_to(ROOT)}")
    print(f"wrote {BEHAVIOR_EXTENSION_EVIDENCE_JSON.relative_to(ROOT)}")
    print(f"wrote {STAGED_BLOCKER_JSON.relative_to(ROOT)}")
    print(f"wrote {STAGED_BLOCKER_CSV.relative_to(ROOT)}")
    print(f"wrote {STAGED_BLOCKER_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
