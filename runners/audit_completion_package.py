#!/usr/bin/env python3
"""Audit the VAEVAS completion package.

This script does not rerun every simulation.  It verifies that every closed-set
task has an accepted provenance entry and that the referenced evidence roots
exist.  It is the fast reproducibility gate before expensive EVAS/Spectre
replays.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
MANIFEST = ROOT / "docs" / "COMPLETION_PACKAGE_MANIFEST.json"
LEDGER = ROOT / "docs" / "CLOSEDSET92_COMPLETION_LEDGER.json"
ARTIFACT_STORE = ROOT / "docs" / "VERIFIED_ARTIFACT_STORE.json"
OUT_JSON = ROOT / "results" / "completion-package-audit-2026-04-29" / "summary.json"
OUT_MD = PROJECT / "coordination" / "status" / "2026-04-29_completion_package_audit.md"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT.resolve()))
    except Exception:
        return str(path)


def _exists(rel_or_abs: str | None) -> bool:
    if not rel_or_abs:
        return False
    path = Path(rel_or_abs)
    if not path.is_absolute():
        path = PROJECT / path
    return path.exists()


def _main() -> int:
    manifest = _read_json(MANIFEST)
    ledger = _read_json(LEDGER)
    store = _read_json(ARTIFACT_STORE)
    tasks = ledger.get("tasks", [])
    failures: list[dict[str, Any]] = []
    role_counts = Counter(task.get("result_role") for task in tasks)
    claim_counts = Counter(task.get("claim_allowed") for task in tasks)

    for task in tasks:
        task_failures: list[str] = []
        if task.get("current_status") != "PASS":
            task_failures.append("not_pass")
        if not task.get("result_role"):
            task_failures.append("missing_result_role")
        if not task.get("claim_allowed"):
            task_failures.append("missing_claim_allowed")
        if task.get("claim_allowed") not in {
            "strict_baseline_closed_set_anchor",
            "closed_set_completion_not_cold_start",
        }:
            task_failures.append("unexpected_claim_label")
        validation_root = task.get("validation_root")
        if task.get("source_kind") in {"R26_teacher_replay", "R26_teacher_spectrefix", "I_repair"} and not _exists(validation_root):
            task_failures.append("missing_validation_root")
        if task_failures:
            failures.append({"task_id": task.get("task_id"), "issues": task_failures})

    required_files = (
        manifest.get("closed_set_assets", [])
        + manifest.get("reusable_knowledge_assets", [])
        + manifest.get("runners", [])
    )
    missing_files = []
    for rel in required_files:
        if not (ROOT / rel).exists():
            missing_files.append(rel)

    artifact_claims = Counter(item.get("claim_allowed") for item in store.get("artifacts", []))
    summary = {
        "manifest": _rel(MANIFEST),
        "ledger": _rel(LEDGER),
        "artifact_store": _rel(ARTIFACT_STORE),
        "total_tasks": len(tasks),
        "accepted_pass": sum(1 for task in tasks if task.get("current_status") == "PASS"),
        "role_counts": dict(role_counts),
        "claim_counts": dict(claim_counts),
        "artifact_claim_counts": dict(artifact_claims),
        "missing_package_files": missing_files,
        "task_failures": failures,
        "package_audit_pass": len(tasks) == 92 and not failures and not missing_files,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    OUT_MD.write_text(_markdown(summary), encoding="utf-8")
    print(f"[completion-package-audit] pass={summary['package_audit_pass']} accepted={summary['accepted_pass']}/{summary['total_tasks']}")
    print(f"[completion-package-audit] wrote {OUT_JSON}")
    print(f"[completion-package-audit] wrote {OUT_MD}")
    return 0 if summary["package_audit_pass"] else 2


def _markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Completion Package Audit",
        "",
        "Date: 2026-04-29",
        "",
        f"- Package audit pass: `{summary['package_audit_pass']}`",
        f"- Accepted closed-set tasks: `{summary['accepted_pass']}/{summary['total_tasks']}`",
        f"- Role counts: `{summary['role_counts']}`",
        f"- Claim counts: `{summary['claim_counts']}`",
        f"- Artifact claim counts: `{summary['artifact_claim_counts']}`",
        "",
        "## Claim Boundary",
        "",
        "- `strict_baseline_closed_set_anchor` entries can support the A/D/F/G same-baseline result line.",
        "- `closed_set_completion_not_cold_start` entries can support the completion-package result, not cold-start claims.",
        "- `teacher_dataset_not_cold_start` entries are teacher data unless independently admitted by EVAS + Spectre.",
        "",
        "## Missing Package Files",
        "",
    ]
    if summary["missing_package_files"]:
        lines.extend(f"- `{item}`" for item in summary["missing_package_files"])
    else:
        lines.append("- None")
    lines.extend(["", "## Task Issues", ""])
    if summary["task_failures"]:
        for failure in summary["task_failures"]:
            lines.append(f"- `{failure['task_id']}`: {', '.join(failure['issues'])}")
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(_main())
