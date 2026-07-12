#!/usr/bin/env python3
"""Record hash-bound evidence from audited tri-form runtime export samples."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def tree_sha(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file():
            digest.update(item.relative_to(path).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(item.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


AUDITOR = Path(__file__).resolve().with_name("audit_runtime_export.py")


def verified_audit(run: Path) -> tuple[dict, Path]:
    audit_path = run / "evidence" / "runtime_export_audit.json"
    if not audit_path.is_file():
        raise SystemExit(f"missing runtime export audit: {audit_path}")
    stored = read_json(audit_path)
    if (
        stored.get("schema_version") != "v4-runtime-export-audit-v1"
        or stored.get("status") != "pass"
        or stored.get("problems") != []
    ):
        raise SystemExit(f"stored runtime export audit is not a valid pass: {audit_path}")
    completed = subprocess.run(
        [sys.executable, str(AUDITOR), "--run", str(run)],
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise SystemExit(f"fresh runtime export audit failed for {run}: {completed.stdout}{completed.stderr}")
    try:
        fresh = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"fresh runtime export audit emitted invalid JSON for {run}: {exc}") from exc
    if fresh != stored:
        raise SystemExit(f"stored runtime export audit does not match a fresh auditor run: {audit_path}")
    return stored, audit_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for raw in args.run:
        run = raw.expanduser().resolve()
        attempt = read_json(run / "evidence" / "attempt_record.json")
        access = read_json(run / "MODEL_ACCESS_POLICY.json")
        audit, audit_path = verified_audit(run)
        rows.append({
            "task_id": attempt["task_id"],
            "family_id": attempt["family_id"],
            "form": attempt["form"],
            "mode": attempt["mode"],
            "runtime_tree_sha256": tree_sha(run),
            "public_bundle_sha256": attempt["public_bundle_sha256"],
            "evaluator_bundle_sha256": attempt["evaluator_bundle_sha256"],
            "model_mounts": access["mounts"],
            "evaluator_mounted": access["evaluator_mounted"],
            "network": access["network"],
            "audit_status": audit["status"],
            "audit_report_sha256": file_sha(audit_path),
            "audit_summary": audit,
            "auditor_sha256": file_sha(AUDITOR),
        })
    rows.sort(key=lambda row: (row["form"], row["mode"]))
    payload = {
        "schema_version": "v4-runtime-ingestion-evidence-v1",
        "status": "pass" if rows and all(row["audit_status"] == "pass" for row in rows) else "fail",
        "scope": "one direct DUT, one agentic Testbench, and one fully-skilled agentic Bugfix export",
        "runner": "operations/tri_form_derivation_prep/export_tri_form_runtime.py",
        "access_auditor": "operations/tri_form_derivation_prep/audit_runtime_export.py",
        "sample_count": len(rows),
        "samples": rows,
        "claim_boundary": "proves record ingestion and bundle isolation; does not claim model execution or final score",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
