#!/usr/bin/env python3
"""Batch-run behavior contracts against a scored result root.

This is a diagnostic helper. It does not change scoring semantics, generated
artifacts, or task files. It reads generated ``contracts.json`` files, runs each
contract set against the corresponding ``tran.csv`` from a score root, and
writes per-task reports plus a compact summary.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from contract_check import run_contracts


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _prompt_templates(contract_path: Path) -> list[str]:
    try:
        spec = json.loads(contract_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return list(spec.get("source", {}).get("prompt_checker_templates", []))


def _contract_count(contract_path: Path) -> int:
    try:
        spec = json.loads(contract_path.read_text(encoding="utf-8"))
    except Exception:
        return 0
    return len(spec.get("contracts", []))


def _task_ids(contract_root: Path, selected: list[str]) -> list[str]:
    if selected:
        return sorted(set(selected))
    return sorted(path.parent.name for path in contract_root.glob("*/contracts.json"))


def build_reports(contract_root: Path, score_root: Path, out_root: Path, selected: list[str]) -> dict:
    rows: list[dict] = []
    for task_id in _task_ids(contract_root, selected):
        contract_path = contract_root / task_id / "contracts.json"
        csv_path = score_root / task_id / "tran.csv"
        task_out = out_root / task_id
        if not contract_path.exists():
            report = {
                "task_id": task_id,
                "status": "MISSING_CONTRACT",
                "advisory_status": "PASS",
                "failed_hard_contracts": [],
                "failed_advisory_contracts": [],
                "contract_results": [],
                "contract_path": str(contract_path),
                "csv_path": str(csv_path),
            }
        elif not csv_path.exists():
            try:
                spec = json.loads(contract_path.read_text(encoding="utf-8"))
            except Exception:
                spec = {}
            source = spec.get("source", {}) if isinstance(spec.get("source", {}), dict) else {}
            report = {
                "task_id": task_id,
                "status": "MISSING_CSV",
                "advisory_status": "PASS",
                "source": source,
                "prompt_functional_ir": source.get("prompt_functional_ir", {}),
                "prompt_functional_claims": source.get("prompt_functional_claims", []),
                "prompt_checker_templates": source.get("prompt_checker_templates", []),
                "prompt_checker_signal_sources": source.get("prompt_checker_signal_sources", {}),
                "failed_hard_contracts": ["runtime_csv_missing"],
                "failed_advisory_contracts": [],
                "contract_results": [
                    {
                        "name": "runtime_csv_missing",
                        "type": "runtime_csv_exists",
                        "severity": "hard",
                        "passed": False,
                        "diagnostic_hint": "No transient CSV was available for contract checking.",
                        "repair_family": "runtime-interface-minimal-harness",
                    }
                ],
                "contract_path": str(contract_path),
                "csv_path": str(csv_path),
            }
        else:
            report = run_contracts(contract_path, csv_path)
        _write_json(task_out / "contract_report.json", report)
        rows.append(
            {
                "task_id": task_id,
                "status": report.get("status"),
                "advisory_status": report.get("advisory_status"),
                "failed_hard_contracts": report.get("failed_hard_contracts", []),
                "failed_advisory_contracts": report.get("failed_advisory_contracts", []),
                "passed_hard_contracts": report.get("passed_hard_contracts", []),
                "prompt_checker_templates": _prompt_templates(contract_path),
                "contract_count": _contract_count(contract_path),
            }
        )

    payload = {
        "contract_root": str(contract_root),
        "score_root": str(score_root),
        "total_tasks": len(rows),
        "pass_count": sum(1 for row in rows if row.get("status") == "PASS"),
        "missing_csv_count": sum(1 for row in rows if row.get("status") == "MISSING_CSV"),
        "missing_contract_count": sum(1 for row in rows if row.get("status") == "MISSING_CONTRACT"),
        "advisory_warn_count": sum(1 for row in rows if row.get("advisory_status") == "WARN_CONTRACT"),
        "tasks": rows,
    }
    _write_json(out_root / "summary.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-root", type=Path, required=True)
    parser.add_argument("--score-root", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--task", action="append", default=[])
    args = parser.parse_args()
    summary = build_reports(args.contract_root, args.score_root, args.out_root, args.task)
    print(
        f"checked {summary['total_tasks']} contract sets; "
        f"pass={summary['pass_count']} missing_csv={summary['missing_csv_count']} "
        f"missing_contract={summary['missing_contract_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
