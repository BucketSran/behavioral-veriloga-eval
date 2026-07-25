#!/usr/bin/env python3
"""Run benchmarkv4 testbench references through Rust EVAS as a smoke gate.

This runner stages benchmarkv4 tasks exactly as the release contract expects:
``reference_tb.scs`` sees the supplied DUT under ``./dut/...`` including any
public support files.  Optional mutation runs overlay each score mutation on
top of the same supplied DUT tree and verify that the private checker rejects
the resulting trace behaviorally.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "runners"))

from runners.simulate_evas import (  # noqa: E402
    effective_evas_engine,
    evaluate_behavior_with_timeout,
    evas_module_python,
    evas_source_env,
    parse_evas_performance_counters,
    parse_evas_timing,
    required_trace_signals_for_checker,
    run_evas,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RELEASE = PACKAGE_ROOT / "release" / "benchmarkv4-r51"
REQUIRED_EVAS_ENGINE = "evas2"
REQUIRED_EVAS_VERSION = "0.8.3"
RUST_EVAS_LOG_ENGINE = "evas-rust"
EVAS_VERSION_RE = re.compile(r"^Version\s+(\S+)", re.MULTILINE)
EVAS_BACKEND_RE = re.compile(r"^\s*evas_engine\s*=\s*(\S+)\s*$", re.MULTILINE)


def require_evas2_environment() -> None:
    """Require explicit EVAS2 selection before any evidence is produced."""
    explicit = os.environ.get("EVAS_ENGINE", "").strip().lower()
    default = os.environ.get("VAEVAS_DEFAULT_EVAS_ENGINE", "").strip().lower()
    if explicit != REQUIRED_EVAS_ENGINE or default != REQUIRED_EVAS_ENGINE:
        raise SystemExit(
            "EVAS2 evidence requires explicit EVAS_ENGINE=evas2 and "
            "VAEVAS_DEFAULT_EVAS_ENGINE=evas2"
        )


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe_evas2_runtime(
    *, required_evas_version: str = REQUIRED_EVAS_VERSION
) -> dict[str, str]:
    """Require the pinned EVAS2/Rust runtime before producing evidence."""
    explicit_engine = os.environ.get("EVAS_ENGINE", "").strip().lower()
    explicit_default = os.environ.get("VAEVAS_DEFAULT_EVAS_ENGINE", "").strip().lower()
    if explicit_engine != REQUIRED_EVAS_ENGINE or explicit_default != REQUIRED_EVAS_ENGINE:
        raise SystemExit(
            "EVAS2 evidence requires explicit "
            f"EVAS_ENGINE={REQUIRED_EVAS_ENGINE} and "
            f"VAEVAS_DEFAULT_EVAS_ENGINE={REQUIRED_EVAS_ENGINE}"
        )
    engine = effective_evas_engine()
    if engine != REQUIRED_EVAS_ENGINE:
        raise SystemExit(
            f"EVAS2 evidence requires EVAS_ENGINE={REQUIRED_EVAS_ENGINE!r}; "
            f"effective engine is {engine!r}"
        )
    env = evas_source_env()
    if env is None:
        raise SystemExit("EVAS2 evidence requires the EVAS source checkout")
    source_root = Path(env["PYTHONPATH"].split(os.pathsep, 1)[0]).resolve()
    revision_probe = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if revision_probe.returncode != 0:
        raise SystemExit(
            "EVAS2 evidence requires a Git-traceable EVAS source checkout: "
            f"{revision_probe.stderr.strip()}"
        )
    status_probe = subprocess.run(
        ["git", "-C", str(source_root), "status", "--porcelain"],
        check=False,
        capture_output=True,
        text=True,
    )
    if status_probe.returncode != 0:
        raise SystemExit(
            "EVAS2 evidence could not inspect the EVAS source checkout: "
            f"{status_probe.stderr.strip()}"
        )
    if status_probe.stdout.strip():
        raise SystemExit("EVAS2 evidence requires a clean EVAS source checkout")
    repository_probe = subprocess.run(
        ["git", "-C", str(source_root), "remote", "get-url", "upstream"],
        check=False,
        capture_output=True,
        text=True,
    )
    if repository_probe.returncode != 0:
        repository_probe = subprocess.run(
            ["git", "-C", str(source_root), "remote", "get-url", "origin"],
            check=False,
            capture_output=True,
            text=True,
        )
    if repository_probe.returncode != 0 or not repository_probe.stdout.strip():
        raise SystemExit("EVAS2 evidence requires a Git remote for the EVAS source")
    probe = subprocess.run(
        [
            evas_module_python(),
            "-c",
            (
                "import json, evas; "
                "from evas.simulator.rust_backend import load_optional_rust_backend; "
                "backend = load_optional_rust_backend(); "
                "print(json.dumps({'version': evas.__version__, "
                "'rust_backend_loaded': backend is not None}))"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if probe.returncode != 0:
        raise SystemExit(f"EVAS2 runtime probe failed: {probe.stderr.strip()}")
    try:
        metadata = json.loads(probe.stdout.strip())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"EVAS2 runtime probe returned invalid JSON: {exc}") from exc
    version = str(metadata.get("version") or "")
    if version != required_evas_version:
        raise SystemExit(
            "EVAS2 evidence requires evas-sim "
            f"{required_evas_version}; got {version!r}"
        )
    if metadata.get("rust_backend_loaded") is not True:
        raise SystemExit("EVAS2 Rust backend is unavailable; refusing Python fallback")
    return {
        "evas_engine": REQUIRED_EVAS_ENGINE,
        "evas_engine_used": REQUIRED_EVAS_ENGINE,
        "evas_version": version,
        "evas_backend": "evas-rust",
        "evas_source_repository": repository_probe.stdout.strip(),
        "evas_source_revision": revision_probe.stdout.strip(),
        "evas_source_tree": "clean",
    }


def case_evas2_runtime(output_dir: Path) -> dict[str, Any]:
    """Read the runtime identity emitted by this simulation, without trusting config."""
    log_path = output_dir / "evas.log"
    if not log_path.is_file():
        return {
            "evas_engine": "unknown",
            "evas_engine_used": "unknown",
            "evas_version": "unknown",
            "evas_backend": "unknown",
            "evas_backend_used": "unknown",
            "evas_runtime_valid": False,
            "evas_runtime_notes": ["missing evas.log"],
            "evas_engine_validation": {"valid": False, "notes": ["missing evas.log"]},
        }
    text = log_path.read_text(encoding="utf-8", errors="replace")
    version_match = EVAS_VERSION_RE.search(text)
    backend_match = EVAS_BACKEND_RE.search(text)
    version = version_match.group(1) if version_match else "unknown"
    backend = backend_match.group(1) if backend_match else "unknown"
    valid = version == REQUIRED_EVAS_VERSION and backend == RUST_EVAS_LOG_ENGINE
    notes: list[str] = []
    if version != REQUIRED_EVAS_VERSION:
        notes.append(f"expected EVAS {REQUIRED_EVAS_VERSION}, got {version}")
    if backend != RUST_EVAS_LOG_ENGINE:
        notes.append(f"expected {RUST_EVAS_LOG_ENGINE} backend, got {backend}")
    return {
        "evas_engine": REQUIRED_EVAS_ENGINE if valid else "invalid",
        "evas_engine_used": REQUIRED_EVAS_ENGINE if valid else "invalid",
        "evas_version": version,
        "evas_backend": backend,
        "evas_backend_used": backend,
        "evas_runtime_valid": valid,
        "evas_runtime_notes": notes,
        "evas_engine_validation": {"valid": valid, "notes": notes},
    }


def engine_evidence_from_log(log_path: Path, combined_output: str) -> dict[str, Any]:
    """Compatibility API for the metamorphic/profile evidence runners."""
    configured_engine = effective_evas_engine()
    text = combined_output
    if log_path.is_file():
        text += "\n" + log_path.read_text(encoding="utf-8", errors="replace")
    version_match = EVAS_VERSION_RE.search(text)
    backend_match = EVAS_BACKEND_RE.search(text)
    version = version_match.group(1) if version_match else "unknown"
    backend = backend_match.group(1) if backend_match else "unknown"
    valid = (
        configured_engine == REQUIRED_EVAS_ENGINE
        and version == REQUIRED_EVAS_VERSION
        and backend == RUST_EVAS_LOG_ENGINE
    )
    notes: list[str] = []
    if configured_engine != REQUIRED_EVAS_ENGINE:
        notes.append(f"configured_evas_engine={configured_engine}")
    if version != REQUIRED_EVAS_VERSION:
        notes.append(f"evas_version={version}")
    if backend != RUST_EVAS_LOG_ENGINE:
        notes.append(f"evas_backend={backend}")
    return {
        "evas_engine": configured_engine,
        "evas_engine_used": configured_engine,
        "evas_version": version,
        "evas_backend": backend,
        "evas_backend_used": backend,
        "valid": valid,
        "notes": notes,
    }


def copy_tree(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def task_dir_for_id(release: Path, task_id: str) -> Path:
    index = read_json(release / "TASK_INDEX.json")
    matches = [row for row in index.get("tasks") or [] if row.get("task_id") == task_id]
    if len(matches) != 1:
        raise SystemExit(f"expected one task for {task_id}, found {len(matches)}")
    task_dir = release / str(matches[0]["task_dir"])
    if not task_dir.is_dir():
        raise SystemExit(f"task directory missing for {task_id}: {task_dir}")
    return task_dir


def overlay_mutation(mutation_dir: Path, dut_dir: Path) -> list[str]:
    changed: list[str] = []
    for source in sorted(mutation_dir.rglob("*")):
        if not source.is_file() or source.name == "certification.json":
            continue
        relative = source.relative_to(mutation_dir)
        target = dut_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        changed.append(relative.as_posix())
    return changed


def stage_case(
    *,
    task_dir: Path,
    case_dir: Path,
    mutation_id: str | None,
) -> tuple[Path, list[str]]:
    public_dut = task_dir / "public" / "supplied_dut"
    if not public_dut.is_dir():
        raise SystemExit(f"{task_dir.name}: missing public/supplied_dut")
    dut_dir = case_dir / "dut"
    copy_tree(public_dut, dut_dir)
    changed: list[str] = []
    if mutation_id is not None:
        mutation_dir = task_dir / "evaluator" / "mutation_bundles" / mutation_id
        if not mutation_dir.is_dir():
            raise SystemExit(f"{task_dir.name}: missing mutation bundle {mutation_id}")
        changed = overlay_mutation(mutation_dir, dut_dir)
        if not changed:
            raise SystemExit(f"{task_dir.name}/{mutation_id}: mutation bundle has no source files")
    tb_source = task_dir / "evaluator" / "reference_tb.scs"
    if not tb_source.is_file():
        raise SystemExit(f"{task_dir.name}: missing evaluator/reference_tb.scs")
    tb_target = case_dir / "reference_tb.scs"
    shutil.copy2(tb_source, tb_target)
    return tb_target, changed


def run_one_case(
    *,
    task_dir: Path,
    checker_task_id: str,
    case_id: str,
    mutation_id: str | None,
    output_root: Path,
    timeout_s: int,
) -> dict[str, Any]:
    case_dir = output_root / case_id
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)
    tb_path, changed = stage_case(task_dir=task_dir, case_dir=case_dir, mutation_id=mutation_id)
    case_output = case_dir / "output"
    required_signals = required_trace_signals_for_checker(checker_task_id)
    started = time.perf_counter()
    proc = run_evas(
        case_dir,
        tb_path,
        case_output,
        timeout_s,
        required_trace_signals=required_signals,
    )
    wall_time_s = time.perf_counter() - started
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    csv_path = case_output / "tran.csv"
    case_runtime = case_evas2_runtime(case_output)
    simulator_ok = (
        proc.returncode == 0
        and csv_path.is_file()
        and case_runtime["evas_runtime_valid"] is True
    )
    checker_ok = False
    checker_notes: list[str] = []
    if simulator_ok:
        checker_score, checker_notes = evaluate_behavior_with_timeout(
            checker_task_id,
            csv_path,
            timeout_s=timeout_s,
        )
        checker_ok = bool(checker_score)
    if mutation_id is None:
        if not simulator_ok:
            status = "infrastructure_error"
        else:
            status = "reference_pass" if checker_ok else "reference_fail"
    else:
        status = "mutation_survived" if simulator_ok and checker_ok else (
            "mutation_killed" if simulator_ok else "infrastructure_error"
        )
    return {
        "case_id": case_id,
        "mutation_id": mutation_id,
        "status": status,
        "simulator_ok": simulator_ok,
        "checker_ok": checker_ok,
        "returncode": proc.returncode,
        "changed_artifacts": changed,
        "reference_tb_sha256": file_sha(tb_path),
        "required_trace_signal_count": len(required_signals - {"time"}) if required_signals else 0,
        "checker_notes": checker_notes,
        **case_runtime,
        "timing": parse_evas_timing(combined),
        "performance_counters": parse_evas_performance_counters(combined),
        "wall_time_s": wall_time_s,
        "stdout_tail": combined[-2000:],
    }


def run_task(
    *,
    release: Path,
    task_id: str,
    output_root: Path,
    timeout_s: int,
    include_mutations: bool,
    runtime: dict[str, str],
) -> dict[str, Any]:
    task_dir = task_dir_for_id(release, task_id)
    record = read_json(task_dir / "task_record.json")
    if record.get("form") != "testbench":
        raise SystemExit(f"{task_id}: EVAS reference smoke expects a testbench task")
    checker_task_id = str(record.get("checker_task_id") or "")
    score = read_json(task_dir / "evaluator" / "score_policy.json")
    task_output = output_root / task_id
    task_output.mkdir(parents=True, exist_ok=True)
    cases = [
        run_one_case(
            task_dir=task_dir,
            checker_task_id=checker_task_id,
            case_id="correct",
            mutation_id=None,
            output_root=task_output,
            timeout_s=timeout_s,
        )
    ]
    if include_mutations:
        for mutation_id in score.get("negative_suite_mutation_ids") or []:
            cases.append(
                run_one_case(
                    task_dir=task_dir,
                    checker_task_id=checker_task_id,
                    case_id=str(mutation_id),
                    mutation_id=str(mutation_id),
                    output_root=task_output,
                    timeout_s=timeout_s,
                )
            )
    reference_pass = cases[0]["status"] == "reference_pass"
    mutations_killed = [
        case for case in cases[1:] if case["status"] == "mutation_killed"
    ]
    infrastructure_errors = [case for case in cases if case["status"] == "infrastructure_error"]
    reference_failures = [case for case in cases if case["status"] == "reference_fail"]
    mutation_survivors = [
        case for case in cases[1:] if case["status"] == "mutation_survived"
    ]
    expected_mutation_count = len(cases) - 1
    return {
        "task_id": task_id,
        "task_dir": task_dir.name,
        "family_id": record.get("family_id"),
        "checker_task_id": checker_task_id,
        **runtime,
        "include_mutations": include_mutations,
        "reference_pass": reference_pass,
        "mutation_kill_count": len(mutations_killed),
        "mutation_count": expected_mutation_count,
        "infrastructure_error_count": len(infrastructure_errors),
        "reference_failure_count": len(reference_failures),
        "mutation_survivor_count": len(mutation_survivors),
        "status": "pass"
        if reference_pass
        and len(infrastructure_errors) == 0
        and len(mutation_survivors) == 0
        and len(mutations_killed) == expected_mutation_count
        else "fail",
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--task-id", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--timeout-s", type=int, default=120)
    parser.add_argument("--include-mutations", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--print-full", action="store_true")
    args = parser.parse_args()

    release = args.release.expanduser().resolve()
    output = args.output.expanduser().resolve()
    work_root = args.work_root.expanduser().resolve()
    if work_root.exists():
        if not args.force:
            raise SystemExit(f"work root exists: {work_root}")
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True)
    require_evas2_environment()
    runtime = probe_evas2_runtime()
    results = [
        run_task(
            release=release,
            task_id=task_id,
            output_root=work_root,
            timeout_s=args.timeout_s,
            include_mutations=args.include_mutations,
            runtime=runtime,
        )
        for task_id in args.task_id
    ]
    report = {
        "schema_version": "v4-reference-evas-smoke-v2",
        "release": str(release),
        **runtime,
        "include_mutations": args.include_mutations,
        "task_count": len(results),
        "pass_count": sum(1 for row in results if row["status"] == "pass"),
        "fail_count": sum(1 for row in results if row["status"] != "pass"),
        "reference_failure_count": sum(row["reference_failure_count"] for row in results),
        "infrastructure_error_count": sum(row["infrastructure_error_count"] for row in results),
        "mutation_kill_count": sum(row["mutation_kill_count"] for row in results),
        "mutation_survivor_count": sum(row["mutation_survivor_count"] for row in results),
        "status": "pass" if all(row["status"] == "pass" for row in results) else "fail",
        "results": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.print_full:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            json.dumps(
                {
                    "schema_version": report["schema_version"],
                    "evas_engine": report["evas_engine"],
                    "evas_engine_used": report["evas_engine_used"],
                    "evas_version": report["evas_version"],
                    "evas_backend": report["evas_backend"],
                    "status": report["status"],
                    "task_count": report["task_count"],
                    "pass_count": report["pass_count"],
                    "fail_count": report["fail_count"],
                    "reference_failure_count": report["reference_failure_count"],
                    "infrastructure_error_count": report["infrastructure_error_count"],
                    "mutation_kill_count": report["mutation_kill_count"],
                    "mutation_survivor_count": report["mutation_survivor_count"],
                    "output": str(output),
                    "tasks": [
                        {
                            "task_id": row["task_id"],
                            "evas_engine": row["evas_engine"],
                            "evas_engine_used": row["evas_engine_used"],
                            "evas_version": row["evas_version"],
                            "evas_backend": row["evas_backend"],
                            "status": row["status"],
                            "reference_pass": row["reference_pass"],
                            "mutation_kill_count": row["mutation_kill_count"],
                            "mutation_count": row["mutation_count"],
                            "infrastructure_error_count": row["infrastructure_error_count"],
                            "reference_failure_count": row["reference_failure_count"],
                            "mutation_survivor_count": row["mutation_survivor_count"],
                        }
                        for row in results
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
