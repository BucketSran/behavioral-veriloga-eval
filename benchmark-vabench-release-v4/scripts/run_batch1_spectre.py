#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
TASKS_ROOT = ROOT / "tasks"
REPORT_ROOT = ROOT / "reports" / "v4_replacement_candidate_bank"
DEFAULT_OUTPUT_ROOT = REPORT_ROOT / "spectre_batch1_runs"

RUNNERS_DIR = REPO_ROOT / "runners"
if str(RUNNERS_DIR) not in sys.path:
    sys.path.insert(0, str(RUNNERS_DIR))

from run_gold_dual_suite import (  # noqa: E402
    default_bridge_repo,
    default_remote_cadence_cshrc,
    default_remote_host,
    default_remote_work_root,
    normalize_spectre_backend,
    normalize_spectre_mode,
    run_spectre_case,
)
from simulate_evas import evaluate_behavior_with_timeout  # noqa: E402


SLUGS = [
    "934-nonoverlap-clock-generator",
    "935-pwm-ramp-modulator-front-end",
    "938-periodic-sampler-aperture-metric",
    "941-programmable-frequency-divider",
    "943-level-shifter-enable-rail-tracking",
    "911-ctle-equalizer-macro",
    "912-ffe-transmitter-3tap",
    "947-source-follower-buffer-macro",
    "948-cascode-gain-cell-headroom",
    "956-baseband-offset-gain-trim-macro",
]

WARNING_RE = re.compile(
    r"(?m)^\s*(?:WARNING(?:\s|\()|AHDL\w* warning)[^\n]*$"
)
BENIGN_WARNING_PATTERNS = (
    re.compile(r"^remote_ahdlcmi_cache_prepare_failed rc=75$"),
    re.compile(r"^WARNING \(VACOMP-2435\):"),
    re.compile(r"^WARNING \(SPECTRE-592\):"),
    re.compile(
        r"^WARNING \(SFE-105\): .*`evas_profile' has been ignored because it is not an option\."
    ),
    re.compile(r"^spectre completes with 0 errors, [0-9]+ warnings?, and [0-9]+ notices?\.$"),
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slug_output_dir(output_root: Path, slug: str) -> Path:
    return output_root / slug


def task_include_paths(task_dir: Path, public_contract: dict[str, Any]) -> list[Path]:
    solution_dir = task_dir / "solution"
    expected = [solution_dir / str(name) for name in public_contract.get("target_artifacts") or []]
    extras = sorted(path for path in solution_dir.glob("*.va") if path not in expected)
    include_paths = [*expected, *extras]
    missing = [path for path in expected if not path.exists()]
    if missing:
        names = ", ".join(path.name for path in missing)
        raise FileNotFoundError(f"{task_dir.name}: missing solution artifact(s): {names}")
    return include_paths


def extract_warning_lines(case_dir: Path, spectre_result: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for item in spectre_result.get("warnings") or []:
        text = str(item).strip()
        if text:
            warnings.append(text)
    log_path = case_dir / "spectre.out"
    if log_path.exists():
        text = log_path.read_text(encoding="utf-8", errors="replace")
        for match in WARNING_RE.finditer(text):
            line = re.sub(r"\s+", " ", match.group(0).strip())
            if line and line not in warnings:
                warnings.append(line)
    return warnings[:50]


def is_benign_warning(line: str) -> bool:
    return any(pattern.search(line) for pattern in BENIGN_WARNING_PATTERNS)


def run_one_case(
    *,
    slug: str,
    output_root: Path,
    spectre_backend: str,
    spectre_mode: str,
    timeout_s: int,
    sui_host: str | None,
    sui_work_root: str | None,
    cadence_cshrc: str | None,
) -> dict[str, Any]:
    task_dir = TASKS_ROOT / slug
    public_contract = read_json(task_dir / "public_contract.json")
    checker_profile = read_json(task_dir / "evaluator" / "checker_profile.json")
    checker_task_id = str(checker_profile.get("checker_task_id") or public_contract["task_id"])
    task_id = str(public_contract["task_id"])
    tb_path = task_dir / "evaluator" / "score_tb.scs"
    include_paths = task_include_paths(task_dir, public_contract)
    case_dir = slug_output_dir(output_root, slug)
    if case_dir.exists():
        shutil.rmtree(case_dir)

    start = time.perf_counter()
    spectre_result = run_spectre_case(
        task_id=f"{task_id}:score:gold",
        tb_path=tb_path,
        include_paths=include_paths,
        output_dir=case_dir,
        bridge_repo=default_bridge_repo(),
        cadence_cshrc=cadence_cshrc,
        timeout_s=timeout_s,
        side_output_files=(),
        spectre_backend=spectre_backend,
        sui_host=sui_host,
        sui_work_root=sui_work_root,
        spectre_mode=spectre_mode,
    )
    wall_time_s = round(time.perf_counter() - start, 3)

    csv_path = case_dir / "tran_spectre.csv"
    behavior_score = 0.0
    behavior_notes: list[str] = []
    if spectre_result.get("ok") and csv_path.exists():
        behavior_score, behavior_notes = evaluate_behavior_with_timeout(
            checker_task_id,
            csv_path,
            timeout_s=timeout_s,
            checks_config=checker_profile,
        )
    elif not spectre_result.get("ok"):
        behavior_notes = ["spectre did not complete successfully"]
    else:
        behavior_notes = ["tran_spectre.csv missing after Spectre run"]

    warning_lines = extract_warning_lines(case_dir, spectre_result)
    untriaged_warning_lines = [line for line in warning_lines if not is_benign_warning(line)]
    benign_warning_lines = [line for line in warning_lines if is_benign_warning(line)]
    if not spectre_result.get("ok"):
        status = "FAIL_SPECTRE"
        ahdl_warning_status = "blocked"
    elif behavior_score < 1.0:
        status = "FAIL_BEHAVIOR"
        ahdl_warning_status = "needs_review" if untriaged_warning_lines else "pass"
    elif untriaged_warning_lines:
        status = "PASS_WITH_WARNINGS"
        ahdl_warning_status = "needs_review"
    else:
        status = "PASS"
        ahdl_warning_status = "pass_benign_environment_warnings" if warning_lines else "pass"

    return {
        "slug": slug,
        "task_id": task_id,
        "checker_task_id": checker_task_id,
        "title": public_contract.get("title", ""),
        "category": public_contract.get("category", ""),
        "top_module": public_contract.get("top_module", ""),
        "score_tb": str(tb_path.relative_to(ROOT)),
        "include_paths": [str(path.relative_to(task_dir)) for path in include_paths],
        "case_dir": str(case_dir),
        "csv_path": str(csv_path) if csv_path.exists() else "",
        "status": status,
        "spectre_ok": bool(spectre_result.get("ok")),
        "spectre_backend": spectre_result.get("spectre_backend", spectre_backend),
        "spectre_mode": spectre_result.get("spectre_mode", spectre_mode),
        "spectre_rows": int(spectre_result.get("rows") or 0),
        "spectre_signal_count": len(spectre_result.get("signals") or []),
        "spectre_errors": list(spectre_result.get("errors") or []),
        "spectre_warning_lines": warning_lines,
        "benign_warning_lines": benign_warning_lines,
        "untriaged_warning_lines": untriaged_warning_lines,
        "ahdl_warning_status": ahdl_warning_status,
        "behavior_score": behavior_score,
        "behavior_notes": behavior_notes,
        "wall_time_s": wall_time_s,
        "remote_run_dir": spectre_result.get("remote_run_dir", ""),
        "timing": spectre_result.get("timing", {}),
        "stdout_tail": spectre_result.get("stdout_tail", "")[-2000:],
    }


def summarize(records: list[dict[str, Any]], *, spectre_backend: str, spectre_mode: str) -> dict[str, Any]:
    pass_count = sum(1 for record in records if record["status"] == "PASS")
    pass_with_warnings = sum(1 for record in records if record["status"] == "PASS_WITH_WARNINGS")
    spectre_fail = sum(1 for record in records if record["status"] == "FAIL_SPECTRE")
    behavior_fail = sum(1 for record in records if record["status"] == "FAIL_BEHAVIOR")
    total = len(records)
    all_spectre_ok = all(record["spectre_ok"] for record in records) if records else False
    all_behavior_ok = all(record["behavior_score"] >= 1.0 for record in records) if records else False
    warning_count = sum(len(record["spectre_warning_lines"]) for record in records)
    untriaged_warning_count = sum(len(record.get("untriaged_warning_lines") or []) for record in records)
    return {
        "total": total,
        "pass": pass_count,
        "pass_with_warnings": pass_with_warnings,
        "fail_spectre": spectre_fail,
        "fail_behavior": behavior_fail,
        "all_spectre_ok": all_spectre_ok,
        "all_behavior_ok": all_behavior_ok,
        "warning_count": warning_count,
        "untriaged_warning_count": untriaged_warning_count,
        "spectre_backend": spectre_backend,
        "spectre_mode": spectre_mode,
        "batch_status": (
            "spectre_behavior_pass"
            if total and pass_count == total
            else "spectre_behavior_pass_with_warning_triage"
            if total and pass_count + pass_with_warnings == total
            else "spectre_rework_needed"
        ),
    }


def write_markdown(evidence: dict[str, Any]) -> None:
    summary = evidence["summary"]
    rows = []
    for record in evidence["records"]:
        note = "; ".join(str(item) for item in record.get("behavior_notes") or [])[:120]
        rows.append(
            "| {slug} | {status} | {spectre_ok} | {rows} | {score:.1f} | {untriaged}/{warnings} | {note} |".format(
                slug=record["slug"],
                status=record["status"],
                spectre_ok="yes" if record["spectre_ok"] else "no",
                rows=record["spectre_rows"],
                score=float(record["behavior_score"]),
                warnings=len(record["spectre_warning_lines"]),
                untriaged=len(record.get("untriaged_warning_lines") or []),
                note=note.replace("|", "\\|"),
            )
        )

    text = f"""# v4 Replacement Candidate Bank: Batch 1 Spectre Evidence

Generated: {evidence['generated_at']}

## Summary

- Backend: `{summary['spectre_backend']}` / mode `{summary['spectre_mode']}`.
- Tasks: {summary['total']}.
- Spectre and behavior PASS: {summary['pass']}/{summary['total']}.
- PASS with warning triage: {summary['pass_with_warnings']}/{summary['total']}.
- Spectre failures: {summary['fail_spectre']}; behavior failures after Spectre: {summary['fail_behavior']}.
- AHDL/Spectre warning lines captured: {summary['warning_count']}.
- Untriaged warning lines: {summary['untriaged_warning_count']}.
- Batch status: `{summary['batch_status']}`.

## Per-task Results

| Task | Status | Spectre OK | Rows | Behavior | Untriaged/All Warnings | Note |
| --- | --- | --- | ---: | ---: | ---: | --- |
{chr(10).join(rows)}

## Interpretation

`PASS` means the private score deck ran on the selected remote Spectre backend,
`tran_spectre.csv` was parsed, and the same behavior checker accepted the
Spectre waveform. `PASS_WITH_WARNINGS` keeps the behavioral pass but still
requires AHDL/Spectre warning triage before final admission. Any FAIL row
requires task or harness rework before it can be promoted.
"""
    (REPORT_ROOT / "batch1_spectre_report.md").write_text(text, encoding="utf-8")


def sync_candidate_status(evidence: dict[str, Any]) -> None:
    summary = evidence["summary"]
    if summary["batch_status"] == "spectre_behavior_pass":
        status = "replacement_candidate_evas_spectre_validated"
    elif summary["batch_status"] == "spectre_behavior_pass_with_warning_triage":
        status = "replacement_candidate_spectre_warning_triage_needed"
    else:
        status = "replacement_candidate_spectre_rework_needed"

    records_by_slug = {record["slug"]: record for record in evidence["records"]}
    evidence_rel = "reports/v4_replacement_candidate_bank/batch1_spectre_evidence.json"
    validation_rel = "reports/v4_replacement_candidate_bank/batch1_validation_evidence.json"
    validation_path = REPORT_ROOT / "batch1_validation_evidence.json"
    validation = read_json(validation_path) if validation_path.exists() else {}

    tasks_path = ROOT / "TASKS.json"
    if tasks_path.exists():
        data = read_json(tasks_path)
        for slug, record in records_by_slug.items():
            if slug in data.get("tasks", {}):
                data["tasks"][slug]["status"] = status if record["status"] == "PASS" else record["status"].lower()
                data["tasks"][slug]["validation_evidence"] = validation_rel
                data["tasks"][slug]["spectre_evidence"] = evidence_rel
        write_json(tasks_path, data)

    manifest_path = REPORT_ROOT / "batch1_manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        manifest["status"] = status
        manifest["spectre_evidence"] = evidence_rel
        for slug, record in records_by_slug.items():
            if slug in manifest.get("candidates", {}):
                manifest["candidates"][slug]["status"] = status if record["status"] == "PASS" else record["status"].lower()
                manifest["candidates"][slug]["validation_evidence"] = validation_rel
                manifest["candidates"][slug]["spectre_evidence"] = evidence_rel
                manifest["candidates"][slug]["spectre_status"] = record["status"]
                manifest["candidates"][slug]["ahdl_warning_status"] = record.get("ahdl_warning_status", "")
        write_json(manifest_path, manifest)

    gold_by_task: dict[str, int] = {slug: 0 for slug in records_by_slug}
    for record in (validation.get("gold_oracles") or {}).get("records") or []:
        if record.get("pass") and record.get("slug") in gold_by_task:
            gold_by_task[str(record["slug"])] += 1
    negative_by_task = (validation.get("negative_oracles") or {}).get("by_task") or {}
    marker = "\n## Current Validation Evidence\n"
    for slug, record in records_by_slug.items():
        audit_path = TASKS_ROOT / slug / "AUDIT.md"
        if not audit_path.exists():
            continue
        base = audit_path.read_text(encoding="utf-8").split(marker, 1)[0].rstrip()
        neg_bucket = negative_by_task.get(slug, {})
        row_status = status if record["status"] == "PASS" else record["status"].lower()
        current = f"""{marker}
- Status: `{row_status}`.
- EVAS evidence: `{validation_rel}`.
- Spectre evidence: `{evidence_rel}`.
- EVAS gold oracle runs: {gold_by_task.get(slug, 0)}/2 feedback/score runs passed.
- EVAS negative certification: {neg_bucket.get('ok', 0)}/{neg_bucket.get('total', 0)} negatives failed behaviorally.
- Spectre score deck: `{record['status']}` with {record['spectre_rows']} parsed rows.
- Spectre behavior checker: {record['behavior_score']:.1f}.
- AHDL warning triage: `{record.get('ahdl_warning_status', '')}` ({len(record.get('untriaged_warning_lines') or [])} untriaged / {len(record.get('spectre_warning_lines') or [])} total captured lines).

This task remains a replacement-bank candidate until final human duplicate
review and denominator admission are performed.
"""
        audit_path.write_text(base + "\n" + current, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slugs", nargs="*", default=SLUGS)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--spectre-backend",
        default=os.environ.get("VAEVAS_SPECTRE_BACKEND", "sui-direct"),
        help="Spectre backend: bridge, labctl, or sui-direct.",
    )
    parser.add_argument("--spectre-mode", default=os.environ.get("VAEVAS_SPECTRE_MODE", "ax"))
    parser.add_argument("--timeout-s", type=int, default=300)
    parser.add_argument("--sui-host", default=None)
    parser.add_argument("--sui-work-root", default=None)
    parser.add_argument("--cadence-cshrc", default=None)
    parser.add_argument("--keep-going", action="store_true", default=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    backend = normalize_spectre_backend(args.spectre_backend)
    mode = normalize_spectre_mode(args.spectre_mode)
    sui_host = args.sui_host or default_remote_host(backend) or None
    sui_work_root = args.sui_work_root or default_remote_work_root(backend) or None
    cadence_cshrc = args.cadence_cshrc or default_remote_cadence_cshrc(backend) or None

    records: list[dict[str, Any]] = []
    for slug in args.slugs:
        try:
            record = run_one_case(
                slug=slug,
                output_root=args.output_root,
                spectre_backend=backend,
                spectre_mode=mode,
                timeout_s=args.timeout_s,
                sui_host=sui_host,
                sui_work_root=sui_work_root,
                cadence_cshrc=cadence_cshrc,
            )
        except Exception as exc:  # pragma: no cover - field evidence path
            record = {
                "slug": slug,
                "status": "FAIL_RUNNER",
                "spectre_ok": False,
                "spectre_rows": 0,
                "behavior_score": 0.0,
                "behavior_notes": [f"runner_exception={type(exc).__name__}: {str(exc)[:300]}"],
                "spectre_errors": [],
                "spectre_warning_lines": [],
                "ahdl_warning_status": "blocked",
            }
        records.append(record)
        print(
            json.dumps(
                {
                    "slug": record["slug"],
                    "status": record["status"],
                    "spectre_ok": record["spectre_ok"],
                    "rows": record["spectre_rows"],
                    "behavior_score": record["behavior_score"],
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if not args.keep_going and record["status"].startswith("FAIL"):
            break

    evidence = {
        "schema_version": "v4-replacement-bank-batch1-spectre-v1",
        "generated_at": now_utc(),
        "command": {
            "spectre_backend": backend,
            "spectre_mode": mode,
            "timeout_s": args.timeout_s,
            "sui_host": sui_host,
            "sui_work_root": sui_work_root,
            "cadence_cshrc": cadence_cshrc,
            "output_root": str(args.output_root),
        },
        "summary": summarize(records, spectre_backend=backend, spectre_mode=mode),
        "records": records,
    }
    write_json(REPORT_ROOT / "batch1_spectre_evidence.json", evidence)
    write_markdown(evidence)
    sync_candidate_status(evidence)
    print(json.dumps(evidence["summary"], indent=2, sort_keys=True))
    return 0 if evidence["summary"]["batch_status"] == "spectre_behavior_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
