#!/usr/bin/env python3
"""Replay tri-form reference testbenches through Spectre and private checkers.

This is intentionally narrower than the model/API runner: it validates sealed
benchmark reference assets by running each selected testbench-form task's local
``evaluator/reference_tb.scs`` against its public ``public/supplied_dut``
artifacts, then scores the resulting Spectre CSV with the canonical private
checker.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[1]
REPO = PACKAGE.parent
RUNNERS = REPO / "runners"
DEFAULT_RELEASE = PACKAGE / "release" / "benchmarkv4"

for import_dir in (RUNNERS,):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

from run_gold_dual_suite import (  # noqa: E402
    ahdl_includes,
    default_bridge_repo,
    default_remote_cadence_cshrc,
    default_remote_host,
    default_remote_work_root,
    normalize_spectre_backend,
    normalize_spectre_mode,
    run_spectre_case,
)
from simulate_evas import (  # noqa: E402
    CHECKS,
    behavior_side_output_names,
    evaluate_behavior_with_timeout,
    validate_behavior_side_outputs,
)


WARNING_RE = re.compile(r"(?m)^\s*(?:WARNING(?:\s|\()|AHDL\w* warning)[^\n]*$")
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


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def resolve_task_rows(release: Path, requested: list[str]) -> list[dict[str, Any]]:
    rows = list(read_json(release / "TASK_INDEX.json").get("tasks") or [])
    tb_rows = [row for row in rows if row.get("form") == "testbench"]
    if not requested:
        return tb_rows
    by_id = {str(row.get("task_id")): row for row in tb_rows}
    missing = [task_id for task_id in requested if task_id not in by_id]
    if missing:
        raise SystemExit(f"unknown testbench task id(s): {', '.join(missing)}")
    return [by_id[task_id] for task_id in requested]


def checker_task_id(task_dir: Path, task_record: dict[str, Any]) -> str:
    task_eval = task_dir / "evaluator"
    source_task_record = read_json(task_eval / "task_record.json")
    checker_profile = read_json(task_eval / "checker_profile.json")
    source_slug = str(source_task_record.get("source_slug") or "")
    source_name = source_slug.partition("-")[2].replace("-", "_")
    candidates = [
        str(source_task_record.get("checker_task_id") or ""),
        str(checker_profile.get("checker_task_id") or ""),
        str((checker_profile.get("contract") or {}).get("source_task_id") or ""),
        f"v3_{source_slug.replace('-', '_')}" if source_slug else "",
        source_slug,
        source_name,
    ]
    for checker_id in candidates:
        if checker_id in CHECKS:
            return checker_id
    attempted = ", ".join(repr(item) for item in candidates if item)
    raise RuntimeError(f"{task_dir.name}: checker not registered; tried {attempted}")


def include_paths_for_reference_tb(task_dir: Path, tb_path: Path) -> tuple[list[Path], list[str]]:
    supplied_dut = task_dir / "public" / "supplied_dut"
    public_support = task_dir / "public" / "public_support"
    search_dirs = [supplied_dut, public_support, tb_path.parent]
    found: list[Path] = []
    missing: list[str] = []
    for include in ahdl_includes(tb_path):
        include_path = Path(include.replace("\\", "/"))
        candidates: list[Path] = []
        if not include_path.is_absolute() and ".." not in include_path.parts:
            candidates.append(task_dir / include_path)
            candidates.extend(root / include_path.name for root in search_dirs)
        candidates.append((tb_path.parent / include_path).resolve())
        match = next((path for path in candidates if path.exists() and path.is_file()), None)
        if match is None:
            missing.append(include)
            continue
        if match not in found:
            found.append(match)
    return found, missing


def compact_spectre_result(spectre: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(spectre.get("ok")),
        "status": spectre.get("status"),
        "spectre_backend": spectre.get("spectre_backend"),
        "spectre_mode": spectre.get("spectre_mode"),
        "errors": list(spectre.get("errors") or []),
        "warnings": list(spectre.get("warnings") or []),
        "rows": int(spectre.get("rows") or 0),
        "signals_count": len(spectre.get("signals") or []),
        "timing": spectre.get("timing") or {},
        "remote_run_dir": spectre.get("remote_run_dir") or "",
        "csv_path": spectre.get("csv_path") or "",
    }


def run_one(
    *,
    release: Path,
    row: dict[str, Any],
    output_root: Path,
    spectre_backend: str,
    spectre_mode: str,
    timeout_s: int,
    sui_host: str | None,
    sui_work_root: str | None,
    cadence_cshrc: str | None,
    keep_case_dirs: bool,
) -> dict[str, Any]:
    task_id = str(row["task_id"])
    task_dir = release / str(row["task_dir"])
    task_record = read_json(task_dir / "task_record.json")
    tb_path = task_dir / "evaluator" / "reference_tb.scs"
    try:
        checker_id = checker_task_id(task_dir, task_record)
    except RuntimeError as exc:
        return {
            "task_id": task_id,
            "task_dir": str(row["task_dir"]),
            "family_id": task_record.get("family_id"),
            "status": "FAIL_CHECKER",
            "notes": [str(exc)],
        }
    include_paths, missing_includes = include_paths_for_reference_tb(task_dir, tb_path)
    case_dir = output_root / task_id
    if case_dir.exists():
        shutil.rmtree(case_dir)

    base: dict[str, Any] = {
        "task_id": task_id,
        "task_dir": str(row["task_dir"]),
        "family_id": task_record.get("family_id"),
        "checker_task_id": checker_id,
        "reference_tb": str(tb_path),
        "include_paths": [str(path) for path in include_paths],
        "missing_includes": missing_includes,
    }
    if missing_includes:
        return {**base, "status": "FAIL_MISSING_INCLUDE", "notes": missing_includes}

    started = time.perf_counter()
    spectre = run_spectre_case(
        task_id=f"{task_id}:reference_tb",
        tb_path=tb_path,
        include_paths=include_paths,
        output_dir=case_dir,
        bridge_repo=default_bridge_repo(),
        cadence_cshrc=cadence_cshrc,
        timeout_s=timeout_s,
        side_output_files=behavior_side_output_names(checker_id),
        spectre_backend=spectre_backend,
        sui_host=sui_host,
        sui_work_root=sui_work_root,
        spectre_mode=spectre_mode,
    )
    wall_time_s = round(time.perf_counter() - started, 3)
    csv_path = case_dir / "tran_spectre.csv"
    behavior_score = 0.0
    behavior_notes: list[str] = []
    side_output_ok: bool | None = None
    side_output_note = ""
    if spectre.get("ok") and csv_path.exists():
        behavior_score, behavior_notes = evaluate_behavior_with_timeout(
            checker_id,
            csv_path,
            timeout_s=timeout_s,
        )
        side_validation = validate_behavior_side_outputs(checker_id, case_dir, csv_path)
        if side_validation is not None:
            side_output_ok, side_output_note = side_validation
    elif not spectre.get("ok"):
        behavior_notes = ["spectre did not complete successfully"]
    else:
        behavior_notes = ["tran_spectre.csv missing after Spectre run"]

    warning_lines = extract_warning_lines(case_dir, spectre)
    benign_warnings = [line for line in warning_lines if is_benign_warning(line)]
    untriaged_warnings = [line for line in warning_lines if not is_benign_warning(line)]
    if not spectre.get("ok"):
        status = "FAIL_SPECTRE"
    elif behavior_score < 1.0:
        status = "FAIL_BEHAVIOR"
    elif side_output_ok is False:
        status = "FAIL_SIDE_OUTPUT"
    elif untriaged_warnings:
        status = "PASS_WITH_WARNINGS"
    else:
        status = "PASS"

    result = {
        **base,
        "status": status,
        "wall_time_s": wall_time_s,
        "spectre": compact_spectre_result(spectre),
        "behavior_score": behavior_score,
        "behavior_notes": behavior_notes,
        "side_output_ok": side_output_ok,
        "side_output_note": side_output_note,
        "warning_lines": warning_lines,
        "benign_warning_lines": benign_warnings,
        "untriaged_warning_lines": untriaged_warnings,
        "case_dir": str(case_dir) if keep_case_dirs else "",
    }
    if not keep_case_dirs and status == "PASS" and case_dir.exists():
        shutil.rmtree(case_dir)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--task-id", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--timeout-s", type=int, default=600)
    parser.add_argument("--spectre-backend", default="sui-direct")
    parser.add_argument("--spectre-mode", default="ax")
    parser.add_argument("--sui-host", default=default_remote_host("sui-direct"))
    parser.add_argument("--sui-work-root", default=default_remote_work_root("sui-direct"))
    parser.add_argument("--cadence-cshrc", default=default_remote_cadence_cshrc("sui-direct"))
    parser.add_argument("--keep-case-dirs", action="store_true")
    args = parser.parse_args(argv)

    release = args.release.expanduser().resolve()
    output_root = args.work_root.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    backend = normalize_spectre_backend(args.spectre_backend)
    mode = normalize_spectre_mode(args.spectre_mode)
    rows = resolve_task_rows(release, args.task_id)

    results: list[dict[str, Any]] = []
    started_at = now_utc()
    for row in rows:
        result = run_one(
            release=release,
            row=row,
            output_root=output_root,
            spectre_backend=backend,
            spectre_mode=mode,
            timeout_s=args.timeout_s,
            sui_host=args.sui_host,
            sui_work_root=args.sui_work_root,
            cadence_cshrc=args.cadence_cshrc,
            keep_case_dirs=args.keep_case_dirs,
        )
        results.append(result)
        print(
            result["task_id"],
            result["status"],
            f"{result.get('wall_time_s', 0.0):.2f}s",
            f"score={result.get('behavior_score', 0.0)}",
            f"untriaged_warnings={len(result.get('untriaged_warning_lines') or [])}",
            flush=True,
        )

    pass_statuses = {"PASS", "PASS_WITH_WARNINGS"}
    summary = {
        "schema_version": "v4-benchmarkv4-reference-spectre-audit-v1",
        "release": str(release),
        "started_at": started_at,
        "finished_at": now_utc(),
        "spectre_backend": backend,
        "spectre_mode": mode,
        "timeout_s": args.timeout_s,
        "sui_host": args.sui_host or "",
        "sui_work_root": args.sui_work_root or "",
        "task_count": len(results),
        "pass_count": sum(1 for result in results if result.get("status") in pass_statuses),
        "fail_count": sum(1 for result in results if result.get("status") not in pass_statuses),
        "pass_with_warnings_count": sum(1 for result in results if result.get("status") == "PASS_WITH_WARNINGS"),
        "untriaged_warning_count": sum(len(result.get("untriaged_warning_lines") or []) for result in results),
        "results": results,
    }
    write_json(args.output.expanduser().resolve(), summary)
    print(
        json.dumps(
            {
                "task_count": summary["task_count"],
                "pass_count": summary["pass_count"],
                "fail_count": summary["fail_count"],
                "untriaged_warning_count": summary["untriaged_warning_count"],
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0 if summary["fail_count"] == 0 and summary["untriaged_warning_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
