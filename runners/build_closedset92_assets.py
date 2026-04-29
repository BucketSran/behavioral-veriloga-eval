#!/usr/bin/env python3
"""Build closed-set 92 ledger and teacher artifact stores.

This script is intentionally provenance-first.  It summarizes the current
strict A/D/F/G/H/I lineage and the older R26 92/92 teacher artifacts without
claiming that teacher/replay artifacts are cold-start generations.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent

G_EVAS = ROOT / "results" / "condition-G-targeted-materialized-spectre-aligned-kimi-evas-2026-04-28"
G_SPECTRE = ROOT / "results" / "condition-G-targeted-materialized-spectre-aligned-kimi-spectre-combined-2026-04-28"
I27_EVAS = ROOT / "results" / "condition-I-Full-on-Hv2-finalG27-kimi-evas-after-realliteralfix-full27-2026-04-29"
I4_SPECTRE = ROOT / "results" / "condition-I-Full-on-Hv2-finalG27-kimi-spectre-pass4-after-realliteralfix-2026-04-29"
R26_EVAS = ROOT / "results" / "latest-system-score-r26-dwa-pfd-axisfix-admission-2026-04-27"
R26_GEN = ROOT / "generated-r26-dwa-pfd-combined-admission-2026-04-27"
R26_REMAINING23_SPECTRE = ROOT / "results" / "r26-teacher-remaining23-spectre-2026-04-29"
R26_SPECTREFIX_GEN = ROOT / "generated-r26-teacher-spectrefix-remaining10-2026-04-29"
R26_SPECTREFIX_EVAS = ROOT / "results" / "r26-teacher-spectrefix-remaining10-evas-2026-04-29-r2"
R26_SPECTREFIX_SPECTRE = ROOT / "results" / "r26-teacher-spectrefix-remaining10-spectre-2026-04-29-r2"
R26_TEMPLATES = ROOT / "results" / "gold-r26-template-generalization-2026-04-29" / "gold_r26_mechanism_templates.json"

LEDGER_JSON = ROOT / "docs" / "CLOSEDSET92_COMPLETION_LEDGER.json"
ARTIFACT_STORE = ROOT / "docs" / "VERIFIED_ARTIFACT_STORE.json"
TEMPLATE_STORE = ROOT / "docs" / "CLOSEDSET_CIRCUIT_TEMPLATES.json"
STATUS_MD = PROJECT / "coordination" / "status" / "2026-04-29_closedset92_completion_ledger.md"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _maybe_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return _read_json(path)
    except Exception:
        return None


def _rel(path: str | Path | None) -> str | None:
    if not path:
        return None
    try:
        return str(Path(path).resolve().relative_to(PROJECT.resolve()))
    except Exception:
        return str(path)


def _sha256(path: Path | None) -> str | None:
    if path is None or not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _task_pass(result: dict[str, Any] | None) -> bool:
    if not result:
        return False
    scores = result.get("scores") or result.get("spectre_scores") or {}
    if result.get("status") == "PASS" or result.get("spectre_status") == "PASS":
        return True
    required = result.get("required_axes") or ["dut_compile", "tb_compile", "sim_correct"]
    return all(float(scores.get(axis, 0.0)) >= 1.0 for axis in required)


def _all_tasks() -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for meta_path in sorted((ROOT / "tasks").rglob("meta.json")):
        task_dir = meta_path.parent
        if not (task_dir / "gold").is_dir():
            continue
        meta = _read_json(meta_path)
        if meta.get("tier") == "scope-guard":
            continue
        task_id = meta.get("task_id") or meta.get("id") or task_dir.name
        prompt_path = task_dir / "prompt.md"
        gold_tb = _choose_gold_tb(task_dir / "gold")
        tasks.append(
            {
                "task_id": task_id,
                "family": meta.get("family", "unknown"),
                "category": meta.get("category", ""),
                "task_dir": _rel(task_dir),
                "prompt_hash": _sha256(prompt_path),
                "checker_hash": _sha256(task_dir / "checker.py"),
                "gold_tb_hash": _sha256(gold_tb),
            }
        )
    return tasks


def _choose_gold_tb(gold_dir: Path) -> Path | None:
    preferred = sorted(gold_dir.glob("tb*_ref.scs"))
    if preferred:
        return preferred[0]
    fallback = sorted(gold_dir.glob("tb*.scs"))
    return fallback[0] if fallback else None


def _result(root: Path, task_id: str) -> dict[str, Any] | None:
    return _maybe_json(root / task_id / "result.json")


def _spectre_pass_tasks(root: Path) -> set[str]:
    out: set[str] = set()
    for result_path in root.glob("*/result.json"):
        data = _maybe_json(result_path)
        if not data:
            continue
        if data.get("spectre_pass") is True or data.get("spectre_status") == "PASS":
            out.add(str(data.get("task_id") or result_path.parent.name))
    return out


def _mechanism_family(task: dict[str, Any]) -> str:
    text = f"{task['task_id']} {task.get('category','')} {task.get('family','')}".lower()
    if "dwa" in text:
        return "dwa_rotating_pointer_window"
    if "pll" in text or "dco" in text or "adpll" in text or "cppll" in text:
        return "pll_feedback_cadence"
    if "pfd" in text or "bbpd" in text or "phase" in text:
        return "phase_detector_pulse_relation"
    if "adc" in text or "dac" in text or "cdac" in text or "sar" in text or "d2b" in text:
        return "converter_quantize_reconstruct_or_decode"
    if "comparator" in text or "cmp" in text or "threshold" in text or "hysteresis" in text:
        return "comparator_threshold_hysteresis"
    if "sample_hold" in text or "sample-hold" in text:
        return "sample_hold_track_latch"
    if "divider" in text or "clk_div" in text or "counter" in text:
        return "counter_or_divider_sequence"
    if "prbs" in text or "lfsr" in text:
        return "lfsr_prbs_sequence"
    if "serializer" in text:
        return "serializer_frame_sequence"
    if "cal" in text or "trim" in text:
        return "calibration_search_settle"
    return "generic_voltage_behavior"


def _main_notes(result: dict[str, Any] | None, limit: int = 5) -> list[str]:
    if not result:
        return []
    notes = result.get("notes") or result.get("spectre_notes") or []
    meta = result.get("generation_meta") or {}
    if not notes and isinstance(meta, dict):
        history = meta.get("history") or []
        if history:
            notes = history[-1].get("evas_notes", [])
    return [str(item) for item in notes[-limit:]]


def build_ledger() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    i_spectre_pass = _spectre_pass_tasks(I4_SPECTRE)
    r26_replay_spectre_pass = _spectre_pass_tasks(R26_REMAINING23_SPECTRE)
    r26_spectrefix_pass = _spectre_pass_tasks(R26_SPECTREFIX_SPECTRE)
    g_spectre_summary = _maybe_json(G_SPECTRE / "spectre_model_results.json") or {}
    rows: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []

    for task in _all_tasks():
        task_id = task["task_id"]
        mechanism = _mechanism_family(task)
        g = _result(G_EVAS, task_id)
        i = _result(I27_EVAS, task_id)
        r26 = _result(R26_EVAS, task_id)
        r26fix = _result(R26_SPECTREFIX_EVAS, task_id)

        accepted = None
        accepted_role = None
        source_kind = None
        validation_root = None
        spectre_status = None
        admission_method = None
        claim_allowed = None

        if i and _task_pass(i) and task_id in i_spectre_pass:
            accepted = i
            accepted_role = "closed_set_continuation"
            source_kind = "I_repair"
            validation_root = _rel(I4_SPECTRE)
            spectre_status = "PASS"
            admission_method = "LLM_repair_with_cards"
            claim_allowed = "closed_set_completion_not_cold_start"
        elif g and _task_pass(g):
            accepted = g
            accepted_role = "same_baseline_G_anchor"
            source_kind = "condition-G"
            validation_root = _rel(G_SPECTRE)
            spectre_status = "PASS_BY_COMPOSED_SUMMARY" if g_spectre_summary else None
            admission_method = "fresh_or_targeted_materialized_generation"
            claim_allowed = "strict_baseline_closed_set_anchor"
        elif r26 and _task_pass(r26) and task_id in r26_replay_spectre_pass:
            accepted = r26
            accepted_role = "closed_set_teacher_replay_spectre_confirmed"
            source_kind = "R26_teacher_replay"
            validation_root = _rel(R26_REMAINING23_SPECTRE)
            spectre_status = "PASS"
            admission_method = "exact_replay_then_spectre"
            claim_allowed = "closed_set_completion_not_cold_start"
        elif r26fix and _task_pass(r26fix) and task_id in r26_spectrefix_pass:
            accepted = r26fix
            accepted_role = "closed_set_teacher_template_spectre_fixed"
            source_kind = "R26_teacher_spectrefix"
            validation_root = _rel(R26_SPECTREFIX_SPECTRE)
            spectre_status = "PASS"
            admission_method = "template_spectre_fix_then_evas_and_spectre"
            claim_allowed = "closed_set_completion_not_cold_start"

        latest = i if i is not None else g
        latest_status = latest.get("status") if latest else "MISSING"
        if accepted:
            current_status = "PASS"
            current_scores = accepted.get("scores", {})
            current_notes = _main_notes(accepted)
            current_artifacts = accepted.get("artifacts", {})
        else:
            current_status = latest_status
            current_scores = latest.get("scores", {}) if latest else {}
            current_notes = _main_notes(latest)
            current_artifacts = latest.get("artifacts", {}) if latest else {}
            accepted_role = "remaining_failure"
            source_kind = "final_G27_failure" if i else "condition-G_failure"
            admission_method = "not_admitted"
            claim_allowed = "failure_analysis_only"

        row = {
            **task,
            "mechanism_family": mechanism,
            "current_status": current_status,
            "current_scores": current_scores,
            "current_notes": current_notes,
            "current_artifacts": {key: _rel(value) for key, value in current_artifacts.items()},
            "result_role": accepted_role,
            "source_kind": source_kind,
            "admission_method": admission_method,
            "validation_root": validation_root,
            "spectre_status": spectre_status,
            "claim_allowed": claim_allowed,
            "g_status": g.get("status") if g else None,
            "i_status": i.get("status") if i else None,
            "r26_teacher_status": r26.get("status") if r26 else None,
            "r26_teacher_result": _rel(R26_EVAS / task_id / "result.json") if r26 else None,
            "r26_spectrefix_status": r26fix.get("status") if r26fix else None,
        }
        rows.append(row)

        if accepted:
            artifacts.append(_artifact_entry(row, accepted, mechanism, validation_root, spectre_status))

        if r26 and _task_pass(r26):
            artifacts.append(_teacher_artifact_entry(task, r26, mechanism))

    summary = {
        "total_tasks": len(rows),
        "current_closed_set_pass": sum(1 for row in rows if row["current_status"] == "PASS"),
        "current_status_counts": dict(Counter(row["current_status"] for row in rows)),
        "result_role_counts": dict(Counter(row["result_role"] for row in rows)),
        "mechanism_counts": dict(Counter(row["mechanism_family"] for row in rows)),
        "r26_teacher_pass": sum(1 for row in rows if row["r26_teacher_status"] == "PASS"),
        "roots": {
            "g_evas": _rel(G_EVAS),
            "g_spectre": _rel(G_SPECTRE),
            "i27_evas": _rel(I27_EVAS),
            "i4_spectre": _rel(I4_SPECTRE),
            "r26_evas": _rel(R26_EVAS),
            "r26_generated": _rel(R26_GEN),
            "r26_remaining23_spectre": _rel(R26_REMAINING23_SPECTRE),
            "r26_spectrefix_generated": _rel(R26_SPECTREFIX_GEN),
            "r26_spectrefix_evas": _rel(R26_SPECTREFIX_EVAS),
            "r26_spectrefix_spectre": _rel(R26_SPECTREFIX_SPECTRE),
        },
    }
    return rows, artifacts, summary


def _artifact_entry(
    row: dict[str, Any],
    result: dict[str, Any],
    mechanism: str,
    validation_root: str | None,
    spectre_status: str | None,
) -> dict[str, Any]:
    artifacts = result.get("artifacts", {})
    dut_path = Path(artifacts.get("dut_path", "")) if artifacts.get("dut_path") else None
    tb_path = Path(artifacts.get("tb_path", "")) if artifacts.get("tb_path") else None
    return {
        "artifact_id": f"{row['task_id']}::{row['source_kind']}::{row['admission_method']}",
        "task_id": row["task_id"],
        "mechanism_label": mechanism,
        "source_kind": row["source_kind"],
        "source_root": row.get("validation_root") or row.get("result_role"),
        "result_json": row["current_artifacts"].get("result_json"),
        "dut_paths": [_rel(dut_path)] if dut_path else [],
        "tb_paths": [_rel(tb_path)] if tb_path else [],
        "dut_hashes": [_sha256(dut_path)] if dut_path else [],
        "tb_hashes": [_sha256(tb_path)] if tb_path else [],
        "evas_pass": True,
        "spectre_pass": True if spectre_status and str(spectre_status).startswith("PASS") else None,
        "spectre_status": spectre_status,
        "validation_root": validation_root,
        "reuse_scope": "exact_task_or_same_interface_replay",
        "claim_allowed": row["claim_allowed"],
        "forbidden_claims": ["cold_start"],
        "prompt_hash": row.get("prompt_hash"),
        "checker_hash": row.get("checker_hash"),
        "notes": row.get("current_notes", []),
    }


def _teacher_artifact_entry(task: dict[str, Any], result: dict[str, Any], mechanism: str) -> dict[str, Any]:
    artifacts = result.get("artifacts", {})
    dut_path = Path(artifacts.get("dut_path", "")) if artifacts.get("dut_path") else None
    tb_path = Path(artifacts.get("tb_path", "")) if artifacts.get("tb_path") else None
    return {
        "artifact_id": f"{task['task_id']}::R26_teacher",
        "task_id": task["task_id"],
        "mechanism_label": mechanism,
        "source_kind": "R26_verified",
        "source_root": _rel(R26_EVAS),
        "generated_root": _rel(R26_GEN),
        "result_json": _rel(R26_EVAS / task["task_id"] / "result.json"),
        "dut_paths": [_rel(dut_path)] if dut_path else [],
        "tb_paths": [_rel(tb_path)] if tb_path else [],
        "dut_hashes": [_sha256(dut_path)] if dut_path else [],
        "tb_hashes": [_sha256(tb_path)] if tb_path else [],
        "evas_pass": True,
        "spectre_pass": None,
        "spectre_status": "NOT_VALIDATED_IN_THIS_STORE",
        "validation_root": _rel(R26_EVAS),
        "reuse_scope": "teacher_only_until_spectre_confirmed",
        "claim_allowed": "teacher_dataset_not_cold_start",
        "forbidden_claims": ["cold_start", "strict_spectre_pass_without_validation"],
        "prompt_hash": task.get("prompt_hash"),
        "checker_hash": task.get("checker_hash"),
        "generation_meta": result.get("generation_meta", {}),
    }


def build_templates(rows: list[dict[str, Any]], artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    teacher_by_task = {art["task_id"]: art for art in artifacts if art["source_kind"] == "R26_verified"}
    for row in rows:
        if row["task_id"] in teacher_by_task:
            grouped[row["mechanism_family"]].append(teacher_by_task[row["task_id"]])

    templates: list[dict[str, Any]] = []
    r26_templates = _maybe_json(R26_TEMPLATES) or {}
    r26_by_family = defaultdict(list)
    for template in r26_templates.get("templates", []):
        r26_by_family[str(template.get("family", ""))].append(template)

    for mechanism, entries in sorted(grouped.items()):
        templates.append(
            {
                "template_id": f"closedset::{mechanism}",
                "mechanism_label": mechanism,
                "source": "R26/closed-set teacher artifacts",
                "source_tasks": sorted({entry["task_id"] for entry in entries}),
                "example_artifacts": entries[:5],
                "r26_template_refs": r26_by_family.get(mechanism, []),
                "reuse_scope": "closed_set_teacher_or_slot_bound_after_review",
                "claim_allowed": "closed_set_template_not_cold_start",
                "required_review_before_generalization": [
                    "slot_binding",
                    "negative_constraint_check",
                    "EVAS validation",
                    "Spectre validation",
                ],
            }
        )
    return {
        "version": "closedset-circuit-templates-v0",
        "purpose": "Concrete closed-set teacher templates and artifact examples distilled from R26/92PASS lineage. These are not cold-start evidence.",
        "templates": templates,
    }


def write_outputs(rows: list[dict[str, Any]], artifacts: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    LEDGER_JSON.write_text(json.dumps({"summary": summary, "tasks": rows}, indent=2), encoding="utf-8")
    ARTIFACT_STORE.write_text(
        json.dumps(
            {
                "version": "verified-artifact-store-v0",
                "purpose": "Closed-set artifact/provenance store. Entries derived from gold/R26/history are forbidden as cold-start claims.",
                "summary": {
                    "entries": len(artifacts),
                    "by_source_kind": dict(Counter(art["source_kind"] for art in artifacts)),
                    "by_claim_allowed": dict(Counter(art["claim_allowed"] for art in artifacts)),
                },
                "artifacts": artifacts,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    TEMPLATE_STORE.write_text(json.dumps(build_templates(rows, artifacts), indent=2), encoding="utf-8")
    STATUS_MD.write_text(_markdown(rows, artifacts, summary), encoding="utf-8")


def _markdown(rows: list[dict[str, Any]], artifacts: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    remaining = [row for row in rows if row["current_status"] != "PASS"]
    by_mech = Counter(row["mechanism_family"] for row in remaining)
    role_counts = Counter(row["result_role"] for row in rows)
    g_anchor = role_counts.get("same_baseline_G_anchor", 0)
    hi_continuations = role_counts.get("closed_set_continuation", 0)
    r26_spectre_replay = role_counts.get("closed_set_teacher_replay_spectre_confirmed", 0)
    r26_spectre_fix = role_counts.get("closed_set_teacher_template_spectre_fixed", 0)
    lines = [
        "# Closed-Set 92 Completion Ledger",
        "",
        "Date: 2026-04-29",
        "",
        "## Claim Boundary",
        "",
        "- A/D/F/G remain the strict same-baseline result line.",
        f"- G is the current strict anchor at `{g_anchor}/92`.",
        f"- H/I add `{hi_continuations}` Spectre-confirmed closed-set continuations.",
        f"- R26 teacher replay adds `{r26_spectre_replay}` real-Spectre-confirmed closed-set continuations.",
        f"- R26 teacher template/syntax repair adds `{r26_spectre_fix}` real-Spectre-confirmed closed-set continuations.",
        f"- The current closed-set accepted result is therefore `{summary['current_closed_set_pass']}/92`, but the R26 replay portion is not cold-start evidence.",
        "- R26/92PASS artifacts are teacher/replay material. They are useful for closed-set completion and template distillation, but must not be reported as fresh LLM generation.",
        "",
        "## Summary",
        "",
        f"- Total tasks: `{summary['total_tasks']}`",
        f"- Current closed-set accepted PASS: `{summary['current_closed_set_pass']}/{summary['total_tasks']}`",
        f"- R26 teacher EVAS PASS: `{summary['r26_teacher_pass']}/{summary['total_tasks']}`",
        f"- Current status counts: `{summary['current_status_counts']}`",
        f"- Result role counts: `{summary['result_role_counts']}`",
        "",
        "## Output Files",
        "",
        f"- Ledger JSON: `{_rel(LEDGER_JSON)}`",
        f"- Artifact store: `{_rel(ARTIFACT_STORE)}`",
        f"- Closed-set templates: `{_rel(TEMPLATE_STORE)}`",
        "",
        "## Remaining Failures By Mechanism",
        "",
        "| Mechanism | Count |",
        "|---|---:|",
    ]
    for mechanism, count in sorted(by_mech.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{mechanism}` | {count} |")

    lines.extend(
        [
            "",
            "## Remaining Failure Tasks",
            "",
            "| Task | Family | Mechanism | Status | Notes | R26 Teacher | Next Action |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for row in sorted(remaining, key=lambda r: (r["mechanism_family"], r["task_id"])):
        notes = "; ".join(row.get("current_notes", [])[:3]).replace("|", "\\|")
        next_action = _next_action(row)
        lines.append(
            f"| `{row['task_id']}` | `{row['family']}` | `{row['mechanism_family']}` | "
            f"`{row['current_status']}` | {notes} | `{row['r26_teacher_status']}` | {next_action} |"
        )
    lines.extend(
        [
            "",
            "## Provenance Notes",
            "",
            "- `VERIFIED_ARTIFACT_STORE.json` contains both strict accepted artifacts and R26 teacher artifacts; check `claim_allowed` and `forbidden_claims` before using an entry in a paper table.",
        "- R26 entries are marked `teacher_dataset_not_cold_start` and `spectre_pass=null` unless independently validated.",
        "- R26 replay entries marked `closed_set_completion_not_cold_start` have real Spectre confirmation, but their provenance is still teacher replay.",
        "- R26 spectrefix entries are also not cold-start; they combine teacher artifacts with explicit Spectre-compatibility templates.",
        "- G entries marked `PASS_BY_COMPOSED_SUMMARY` inherit the combined Spectre summary rather than per-task result JSON.",
        ]
    )
    return "\n".join(lines) + "\n"


def _next_action(row: dict[str, Any]) -> str:
    if row["current_status"] == "FAIL_TB_COMPILE":
        return "RAG route to concrete syntax/interface template; retry materializer before LLM."
    if row["mechanism_family"] in {"pll_feedback_cadence", "phase_detector_pulse_relation"}:
        return "Use system-relation template with slot binding; require EVAS then Spectre."
    if row["mechanism_family"] == "converter_quantize_reconstruct_or_decode":
        return "Use converter concrete template; bind width/reference/code outputs."
    if row["mechanism_family"] == "dwa_rotating_pointer_window":
        return "Use DWA pointer/window concrete template; enforce unconditional transition."
    return "Run RAG-v2 router; write failure packet if slot coverage < 0.7."


def main() -> int:
    rows, artifacts, summary = build_ledger()
    write_outputs(rows, artifacts, summary)
    print(f"[closedset92] wrote {LEDGER_JSON}")
    print(f"[closedset92] wrote {ARTIFACT_STORE}")
    print(f"[closedset92] wrote {TEMPLATE_STORE}")
    print(f"[closedset92] wrote {STATUS_MD}")
    print(f"[closedset92] current PASS {summary['current_closed_set_pass']}/{summary['total_tasks']}; R26 teacher {summary['r26_teacher_pass']}/{summary['total_tasks']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
