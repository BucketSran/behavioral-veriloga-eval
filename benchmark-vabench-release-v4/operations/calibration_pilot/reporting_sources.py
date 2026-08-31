"""Read-only projections of distinct evaluation protocols into viewer records.

Source readers retain scoring authority. Only allowlisted structural fields
are exported; raw reports, prompts, trajectories and diagnostics are not copied.
"""

from collections import Counter
import hashlib
import json
import math
from pathlib import Path


SOURCE_KINDS = ("legacy-native-comparison", "evolution-single", "combined-tools")
_COST_FIELDS = ("model_calls", "tool_calls", "public_validation_calls", "prompt_tokens",
                "completion_tokens", "total_tokens", "reasoning_tokens", "transport_attempts",
                "transport_elapsed_s", "wall_time_s")


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def _pick(value, keys):
    return {key: value[key] for key in keys if key in value}


def _record(identity, *, status, score, group, costs, hashes, details=None):
    if score is not None and (type(score) not in (int, float) or not math.isfinite(score)
                              or not 0 <= score <= 1):
        raise ValueError("invalid source score")
    return {"identity": identity, "report_group": group,
            "status": {"source_status": status}, "actual_score": score,
            "actual_score_eligible": score is not None,
            "actual_score_ineligible_reason": None if score is not None else status,
            "costs": costs, "hashes": hashes, "details": details or {}}


def _legacy(root):
    from run_legacy_native_comparison import read_comparison
    from comparison_results import _pair_score_eligible

    report = read_comparison(root)
    records = []
    for row in report["audit_rows"]:
        identity = _pick(row, ("task_id", "family_id", "form", "backend"))
        identity.update(cell_id=row["comparison_cell_id"], source_cell_id=row["cell_id"])
        records.append(_record(
            identity, status=row["disposition"],
            score=row["score"] if _pair_score_eligible(row) else None,
            group=f"legacy-native-comparison/{row['backend']}",
            costs=_pick(row, ("model_calls", "guard_upper_bound", "elapsed_s", "budget_censored")),
            hashes={"source_report_sha256": _digest(report),
                    **_pick(report, ("manifest_sha256", "budget_sha256"))},
            details=_pick(report, ("score_authority", "evidence_scope", "paid_requests",
                                   "potentially_billable_attempts")),
        ))
    return report, records


def _costs(summary):
    if summary is None:
        return None
    result = {}
    for key in _COST_FIELDS:
        if key not in summary:
            continue
        value = summary[key]
        if isinstance(value, dict):
            result[key] = _pick(value, ("total", "known_subtotal", "unknown_count"))
            values = result[key].values()
        else:
            result[key] = value
            values = [value]
        if any(v is not None and (type(v) not in (int, float) or not math.isfinite(v) or v < 0)
               for v in values):
            raise ValueError("invalid source costs")
    return result


def _evolution_details(final):
    branches = []
    for branch in final.get("branch_evidence", []):
        item = _pick(branch, ("round_index", "branch_id", "model_ref", "started", "status"))
        item["costs"] = _costs(branch.get("costs"))
        # References retain a join to original lineage without exporting raw records.
        item["evidence_hashes"] = {
            name: branch.get("evidence", {}).get(name, {}).get("sha256")
            for name in ("request.json", "result.json", "branch-audit.json")
        }
        branches.append(item)
    return {
        "selected_candidate": _pick(final.get("selected_candidate") or {},
                                    ("candidate_id", "branch_id", "round_index", "candidate_tree_sha256")),
        "denominator": _pick(final.get("denominator") or {},
                             ("scheduled_cells", "scheduled_branches", "observed_branches")),
        "branch_evidence": branches,
        "lineage_scope": "selected_candidate_and_source_branch_hash_references",
    }


def _evolution(root):
    from evolution_batch import validate_terminal_result

    campaign = json.loads((root / "campaign.json").read_bytes())
    cell = campaign["cell"]
    final = validate_terminal_result(root / "run", expected_source_cell_id=campaign["source_cell_id"],
                                     expected_campaign=campaign)
    judgment = final.get("final_judgment") or {}
    identity = _pick(cell, ("cell_id", "task_id", "family_id", "form"))
    identity["backend"] = "evolution"
    identity["source_cell_id"] = campaign["source_cell_id"]
    record = _record(
        identity, status=final["status"], score=judgment.get("score"),
        group="multi_model_round_evolution_selected_candidate",
        costs={"all_branch_costs": _costs(final.get("all_branch_costs")),
               "branch_usage": _costs(final.get("branch_usage"))},
        hashes={"source_report_sha256": _digest(final),
                "campaign_file_sha256": hashlib.sha256((root / "campaign.json").read_bytes()).hexdigest(),
                "score_sidecar_sha256": (final.get("score_sidecar_receipt") or {}).get("sha256")},
        details=_evolution_details(final),
    )
    return final, [record]


def _combined(root):
    from run_combined_tools import read_combined

    report = read_combined(root)
    if report["terminal"] != 1 or report["disposition"] == "incomplete_evidence":
        raise ValueError("combined source requires complete terminal evidence")
    manifest = json.loads((root / "combined-manifest.json").read_bytes())
    identity = _pick(manifest["source_cell"], ("cell_id", "task_id", "family_id", "form"))
    identity["backend"] = report["backend"]
    details = {"combined_acceptance_passed": report["combined_acceptance_passed"],
               "score_authority": "development_only",
               **_pick(report, ("evidence_scope", "paid_requests"))}
    if report["backend"] == "evolution" and report["disposition"] == "completed":
        _, evolution_records = _evolution(root)
        details.update(evolution_records[0]["details"])
    # Only structural counters from the already verified feature-use report.
    features = (report.get("feature_use") or {}).get("features", {})
    details["feature_use"] = {
        name: {**_pick(features.get(name, {}), ("attempted", "succeeded", "feedback_exposed_requests")),
               "incomplete_count": len(features.get(name, {}).get("incomplete", []))}
        for name in ("offline_docs", "public_waveform")
    }
    budget = report.get("cost") or {}
    safe_budget = _pick(budget, ("currency", "guard_upper_bound", "model_calls",
                                  "transport_reservations", "censored"))
    safe_budget["per_branch"] = [
        _pick(branch, ("branch_id", "model_calls", "transport_reservations", "guard_upper_bound"))
        for branch in budget.get("per_branch", [])
    ]
    record = _record(
        identity, status=report["disposition"], score=report["score"],
        group=f"combined-tools/{report['backend']}",
        costs={"budget": safe_budget,
               "all_branch_costs": _costs(report.get("all_branch_costs"))},
        hashes={"source_report_sha256": _digest(report), "manifest_sha256": report["manifest_sha256"]},
        details=details,
    )
    return report, [record]


def read_reporting_ledger(source_kind: str, root: Path) -> dict:
    """Read an existing protocol root; no execution or adoption of partial data."""
    if any(path.is_symlink() for path in (root, *root.parents)) or not root.is_dir():
        raise ValueError("source root must be a real directory without symlinks")
    readers = {"legacy-native-comparison": _legacy, "evolution-single": _evolution,
               "combined-tools": _combined}
    if source_kind not in readers:
        raise ValueError("unsupported reporting source kind")
    for path in root.rglob("*"):
        # Production creates this relative self-alias for legacy public paths.
        # It cannot escape its parent; source readers still verify runtime hashes.
        public_alias = (path.name == "public" and path.parent.name == "public"
                        and path.is_symlink() and str(path.readlink()) == ".")
        if path.is_symlink() and not public_alias:
            raise ValueError("source evidence must not use symlinks")
    report, records = readers[source_kind](root)
    identities = [row["identity"]["cell_id"] for row in records]
    if not records or len(set(identities)) != len(identities):
        raise ValueError("reporting records must be nonempty and unique")
    arms = {}
    for row in records:
        group = arms.setdefault(row["report_group"], {
            "planned": 0, "observed": 0, "score_eligible": 0, "passed": 0,
            "pass_rate": None, "ineligible_reasons": Counter(),
        })
        group["planned"] += 1
        group["observed"] += 1
        group["score_eligible"] += row["actual_score_eligible"]
        group["passed"] += row["actual_score"] == 1
        if not row["actual_score_eligible"]:
            group["ineligible_reasons"][row["actual_score_ineligible_reason"]] += 1
    for group in arms.values():
        if group["score_eligible"]:
            group["pass_rate"] = group["passed"] / group["score_eligible"]
        group["ineligible_reasons"] = dict(group["ineligible_reasons"])
    ledger = {
        "schema_version": "vaevas-multipath-report-ledger-v1",
        "source_kind": source_kind, "source_report_sha256": _digest(report),
        "execution_performed": False, "single_trajectory_pooling_allowed": False,
        "claim_scope": "result_interoperability_only",
        "denominator": {"scheduled_cells": len(records), "observed_rows": len(records),
                        "eligible_actual_score_cells": sum(r["actual_score_eligible"] for r in records)},
        "paired_summary": {"arms": arms}, "records": records,
    }
    ledger["ledger_sha256"] = _digest(ledger)
    return ledger
