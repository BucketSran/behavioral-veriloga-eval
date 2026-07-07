#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "benchmark-vabench-release-v3"
REPORTS_ROOT = PACKAGE_ROOT / "reports"
TASKS_JSON = PACKAGE_ROOT / "TASKS.json"
REPORT_JSON = REPORTS_ROOT / "score_denominator_manifest.json"
REPORT_MD = REPORTS_ROOT / "score_denominator_manifest.md"

CORE_LEVELS = {"L1", "L2", "L3"}
SUPPORT_TIERS = {"support-formal-candidate"}
GOLD_NEGATIVE_REPORTS = [
    REPORTS_ROOT / "verify_001_501_gold_timing.json",
    REPORTS_ROOT / "verify_001_501_negatives.json",
    REPORTS_ROOT / "verify_001_300_replacements_current.json",
    REPORTS_ROOT / "verify_301_505_layered.json",
    REPORTS_ROOT / "verify_502_505_layered.json",
]
LAYERED_CERTIFICATION = REPORTS_ROOT / "layered_certification.json"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_tasks() -> dict[str, Any]:
    payload = read_json(TASKS_JSON)
    defaults = payload.get("defaults", {})
    rows: dict[str, Any] = {}
    for slug, task in payload.get("tasks", {}).items():
        merged = dict(defaults)
        merged.update(task)
        rows[slug] = merged
    return rows


def collect_verification() -> dict[str, dict[str, Any]]:
    rows_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for report_path in GOLD_NEGATIVE_REPORTS:
        payload = read_json(report_path)
        for row in payload.get("rows", []):
            if not isinstance(row, dict):
                continue
            slug = str(row.get("task_slug") or "")
            kind = str(row.get("kind") or "")
            if not slug or kind not in {"gold", "negative"}:
                continue
            variant = str(row.get("variant") or "")
            rows_by_key[(slug, kind, variant)] = row

    evidence: dict[str, dict[str, Any]] = {}
    for row in rows_by_key.values():
        slug = str(row.get("task_slug") or "")
        info = evidence.setdefault(slug, {"gold": [], "negative": []})
        kind = str(row.get("kind") or "")
        info[kind].append(row)
    for slug, info in evidence.items():
        gold_rows = info["gold"]
        negative_rows = info["negative"]
        gold_ok = bool(gold_rows) and all(
            row.get("status") == "PASS" and row.get("meets_expectation") is True
            for row in gold_rows
        )
        negative_ok = len(negative_rows) >= 5 and all(
            row.get("status") != "PASS" and row.get("meets_expectation") is True
            for row in negative_rows
        )
        info["gold_count"] = len(gold_rows)
        info["negative_count"] = len(negative_rows)
        info["gold_verified"] = gold_ok
        info["negative_verified"] = negative_ok
        info["evas_behavior_verified"] = gold_ok and negative_ok
    return evidence


def layered_rows() -> dict[str, dict[str, Any]]:
    payload = read_json(LAYERED_CERTIFICATION)
    rows = payload.get("task_rows", [])
    return {
        str(row.get("task_key")): row
        for row in rows
        if isinstance(row, dict) and row.get("task_key")
    }


def score_surface(level: str, track: str) -> str:
    if track == "core":
        return "v3-standalone-core-task"
    if track == "support":
        return "v3-support-task"
    return f"v3-{level.lower()}-non-core-task"


def task_track(level: str, tier: str) -> str:
    if tier in SUPPORT_TIERS:
        return "support"
    if level in CORE_LEVELS:
        return "core"
    return "language_or_non_core"


def exclusion_reasons(
    level: str,
    tier: str,
    evas_behavior_verified: bool,
    spectre_divergent: bool,
    candidate_score_denominator: bool,
) -> list[str]:
    reasons: list[str] = []
    if level not in CORE_LEVELS:
        reasons.append("non_core_level_excluded")
    if tier in SUPPORT_TIERS:
        reasons.append("support_formal_candidate_excluded_from_core_score")
    if not evas_behavior_verified:
        reasons.append("missing_evas_gold_negative_verification")
    if spectre_divergent:
        reasons.append("spectre_divergent_pending_recalibration")
    if candidate_score_denominator:
        reasons.append("v3_score_policy_not_frozen")
    return reasons


def build_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tasks = read_tasks()
    evidence = collect_verification()
    layered = layered_rows()
    entry_rows: list[dict[str, Any]] = []
    form_rows: list[dict[str, Any]] = []
    for slug in sorted(tasks, key=lambda item: int(item.split("-", 1)[0])):
        task = tasks[slug]
        layer = layered.get(slug, {})
        level = str(task.get("level") or "")
        tier = str(task.get("tier") or "<missing>")
        form = str(task.get("form") or "dut")
        track = task_track(level, tier)
        task_evidence = evidence.get(slug, {})
        evas_behavior_verified = bool(task_evidence.get("evas_behavior_verified"))
        spectre_divergent = bool(layer.get("spectre_recalibration_required"))
        candidate_score_denominator = (
            level in CORE_LEVELS
            and tier not in SUPPORT_TIERS
            and evas_behavior_verified
            and not spectre_divergent
        )
        reasons = exclusion_reasons(
            level,
            tier,
            evas_behavior_verified,
            spectre_divergent,
            candidate_score_denominator,
        )
        common = {
            "release_entry_id": slug,
            "level": level,
            "track": track,
            "difficulty": str(task.get("difficulty") or ""),
            "category": str(task.get("category") or ""),
            "base_function": str(task.get("title") or ""),
            "score_surface": score_surface(level, track),
            "manifest": rel(PACKAGE_ROOT / "tasks" / slug / "task.toml"),
            "candidate_score_denominator": candidate_score_denominator,
            "counted_in_score": False,
            "exclusion_reasons": reasons,
            "spectre_parity_status": str(layer.get("spectre_parity_status") or "not_marked_divergent"),
            "spectre_recalibration_required": spectre_divergent,
            "evas_behavior_verified": evas_behavior_verified,
            "gold_verified": bool(task_evidence.get("gold_verified")),
            "negative_verified": bool(task_evidence.get("negative_verified")),
            "negative_count": int(task_evidence.get("negative_count") or 0),
        }
        entry_rows.append({
            **common,
            "required_forms": [form],
            "missing_forms": [],
            "release_blockers": (
                ["spectre_divergent_pending_recalibration"]
                if spectre_divergent
                else []
            ),
            "benchmark_score_enabled": False,
            "certified": evas_behavior_verified and not spectre_divergent,
        })
        form_rows.append({
            **common,
            "task_id": str(task.get("id") or slug),
            "form": form,
            "static": "pass",
            "evas": "pass" if evas_behavior_verified else "pending",
            "spectre": "divergent" if spectre_divergent else "not_frozen",
            "certified": evas_behavior_verified and not spectre_divergent,
            "benchmark_score_enabled": False,
        })
    return entry_rows, form_rows


def reason_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(str(reason) for reason in row.get("exclusion_reasons", []))
    return dict(sorted(counts.items()))


def row_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field) or "") for row in rows).items()))


def build_report() -> dict[str, Any]:
    entry_rows, form_rows = build_rows()
    candidate_entries = [row for row in entry_rows if row["candidate_score_denominator"]]
    candidate_forms = [row for row in form_rows if row["candidate_score_denominator"]]
    spectre_divergent_rows = [row for row in entry_rows if row["spectre_recalibration_required"]]
    summary = {
        "planned_entry_count": len(entry_rows),
        "release_form_count": len(form_rows),
        "track_entry_counts": row_counts(entry_rows, "track"),
        "track_form_counts": row_counts(form_rows, "track"),
        "difficulty_entry_counts": row_counts(entry_rows, "difficulty"),
        "difficulty_form_counts": row_counts(form_rows, "difficulty"),
        "core_entry_count": sum(row["track"] == "core" for row in entry_rows),
        "support_entry_count": sum(row["track"] == "support" for row in entry_rows),
        "non_core_entry_count": sum(row["track"] == "language_or_non_core" for row in entry_rows),
        "core_form_count": sum(row["track"] == "core" for row in form_rows),
        "support_form_count": sum(row["track"] == "support" for row in form_rows),
        "non_core_form_count": sum(row["track"] == "language_or_non_core" for row in form_rows),
        "evas_behavior_verified_entry_count": sum(row["evas_behavior_verified"] for row in entry_rows),
        "evas_behavior_verified_form_count": sum(row["evas_behavior_verified"] for row in form_rows),
        "candidate_score_entry_count": len(candidate_entries),
        "candidate_score_form_count": len(candidate_forms),
        "benchmark_score_enabled_entry_count": 0,
        "benchmark_score_enabled_form_count": 0,
        "scored_entry_count": 0,
        "scored_form_count": 0,
        "core_scored_entry_count": 0,
        "core_scored_form_count": 0,
        "support_scored_entry_count": 0,
        "support_scored_form_count": 0,
        "spectre_divergent_entry_count": len(spectre_divergent_rows),
        "spectre_divergent_tasks": [row["release_entry_id"] for row in spectre_divergent_rows],
        "entry_exclusion_reason_counts": reason_counts(entry_rows),
        "form_exclusion_reason_counts": reason_counts(form_rows),
    }
    return {
        "date": date.today().isoformat(),
        "release": "benchmark-vabench-release-v3",
        "status": "candidate_denominator_identified_not_frozen",
        "summary": summary,
        "claim_rule": {
            "source_of_truth": rel(REPORT_JSON),
            "denominator_policy": (
                "candidate_score_denominator=true marks current v3 standalone core L1/L2/L3 tasks "
                "with EVAS gold+negative evidence, excluding support-formal, SX/NA language rows, "
                "and retained spectre-divergent rows. counted_in_score remains false until the v3 "
                "score policy is explicitly frozen."
            ),
            "score_claim_allowed": False,
            "score_claim_blockers": [
                "v3_score_policy_not_frozen",
                "spectre_divergent_rows_require_recalibration_before_full_spectre_claim",
            ],
        },
        "entry_rows": entry_rows,
        "form_rows": form_rows,
        "evidence_sources": {
            "task_manifest": rel(TASKS_JSON),
            "layered_certification": rel(LAYERED_CERTIFICATION),
            "gold_negative_reports": [rel(path) for path in GOLD_NEGATIVE_REPORTS],
        },
    }


def write_markdown(report: dict[str, Any]) -> None:
    summary = report["summary"]
    lines = [
        "# vaBench v3 Score Denominator Manifest",
        "",
        f"Date: {report['date']}",
        "",
        "This manifest identifies the current v3 candidate score denominator without",
        "freezing a formal paper score claim.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| status | `{report['status']}` |",
        f"| planned entries | {summary['planned_entry_count']} |",
        f"| release forms | {summary['release_form_count']} |",
        f"| core entries | {summary['core_entry_count']} |",
        f"| support entries | {summary['support_entry_count']} |",
        f"| non-core entries | {summary['non_core_entry_count']} |",
        f"| EVAS behavior-verified entries | {summary['evas_behavior_verified_entry_count']} |",
        f"| candidate score entries | {summary['candidate_score_entry_count']} |",
        f"| candidate score forms | {summary['candidate_score_form_count']} |",
        f"| counted entries | {summary['scored_entry_count']} |",
        f"| counted forms | {summary['scored_form_count']} |",
        f"| spectre-divergent rows | {summary['spectre_divergent_entry_count']} |",
        "",
        "## Claim Rule",
        "",
        report["claim_rule"]["denominator_policy"],
        "",
        "## Spectre-Divergent Rows",
        "",
    ]
    for task in summary["spectre_divergent_tasks"]:
        lines.append(f"- `{task}`")
    lines.extend(["", "## Entry Exclusion Reasons", ""])
    for key, value in summary["entry_exclusion_reason_counts"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Candidate Score Rows", ""])
    for row in report["entry_rows"]:
        if row["candidate_score_denominator"]:
            lines.append(f"- `{row['release_entry_id']}`")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    report = build_report()
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report)
    summary = report["summary"]
    print(
        "wrote v3 score denominator manifest: candidates={candidates}; counted={counted}; "
        "spectre_divergent={divergent}".format(
            candidates=summary["candidate_score_entry_count"],
            counted=summary["scored_entry_count"],
            divergent=summary["spectre_divergent_entry_count"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
