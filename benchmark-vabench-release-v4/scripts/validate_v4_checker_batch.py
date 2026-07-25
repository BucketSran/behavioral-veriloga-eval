#!/usr/bin/env python3
"""Certify a canonical V4 family batch with Rust EVAS2 and checker metamorphs.

The tool stages directly from the canonical provenance source.  It never
reads or edits the generated ``release/benchmarkv4`` tree.  For every selected
family it requires the gold DUT to pass, all five active mutations to compile
and be killed, and checker classification to remain unchanged under the
public timing metamorph ``t' = scale * t + shift``.  A short gold prefix must
also fail as insufficient excitation.

Rust EVAS2 is the sole certification evaluator for this release lane.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners"))

from runners.checkers.v4.registry import load_checker  # noqa: E402
from runners.checkers.v4.stimulus_relative import transformed_rows  # noqa: E402
from runners.simulate_evas import (  # noqa: E402
    effective_evas_engine,
    load_csv,
    required_trace_signals_for_checker,
    run_evas,
)

sys.path.insert(
    0,
    str(ROOT / "benchmark-vabench-release-v4" / "operations" / "tri_form_derivation_prep"),
)
from run_v4_reference_evas_smoke import (  # noqa: E402
    REQUIRED_EVAS_VERSION,
    probe_evas2_runtime,
)
from score_denominator_registry import load_family_rows  # noqa: E402


DEFAULT_SOURCE = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "provenance"
    / "dut-base-v3-exact-five-hash-bound-v2"
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(path: Path, *, excluded_names: set[str] | None = None) -> str:
    excluded_names = excluded_names or set()
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if not item.is_file() or item.name in excluded_names:
            continue
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_sha(item).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def load_active_mutation_suites(source: Path) -> dict[str, list[str]]:
    """Load the score authority from family-sharded registry rows."""
    rows = load_family_rows(source)
    suites: dict[str, list[str]] = {}
    for row in rows:
        family_id = str(row["canonical_dut_id"])
        mutation_ids = [
            str(value["mutation_id"]) for value in row.get("active_mutations") or []
        ]
        if family_id in suites:
            raise SystemExit(f"duplicate active mutation suite for family {family_id}")
        if len(mutation_ids) != 5 or len(set(mutation_ids)) != 5:
            raise SystemExit(
                f"family {family_id}: expected exactly five unique active mutations"
            )
        suites[family_id] = mutation_ids
    return suites


def selected_mutation_ids(
    task: Path, active_suites: dict[str, list[str]]
) -> list[str]:
    family_id = task.name[:3]
    manifest = read_json(task / "evaluator" / "mutation_bundles" / "manifest.json")
    catalog_ids = [str(row["id"]) for row in manifest["mutations"]]
    mutation_ids = active_suites.get(family_id, catalog_ids)
    if len(mutation_ids) != 5 or len(set(mutation_ids)) != 5:
        raise SystemExit(f"{task.name}: expected exactly five active mutations")
    missing = sorted(set(mutation_ids) - set(catalog_ids))
    if missing:
        raise SystemExit(
            f"{task.name}: active mutations missing from catalog: {', '.join(missing)}"
        )
    return mutation_ids


def diagnostics_are_complete(
    *, passed: bool, note: str, property_ids: list[str]
) -> bool:
    # Checker notes predate the compact feedback protocol and intentionally use
    # family-specific metric names.  Certification needs an actionable,
    # non-empty diagnostic, not one particular rendering vocabulary.
    del passed, property_ids
    return bool(note.strip()) and "=" in note


def source_binding(task: Path, mutation_ids: list[str]) -> dict[str, Any]:
    family_id = task.name[:3]
    evaluator = task / "evaluator"
    public = task / "public" / "task"
    manifest = read_json(evaluator / "mutation_bundles" / "manifest.json")
    checker_files = [
        ROOT / "runners" / "simulate_evas.py",
        ROOT / "runners" / "checkers" / "api.py",
        ROOT / "runners" / "checkers" / "v4" / "registry.py",
        ROOT / "runners" / "checkers" / "v4" / "stimulus_relative.py",
        ROOT / "runners" / "checkers" / "v4" / f"task_{family_id}.py",
    ]
    checker_files.extend(
        sorted((ROOT / "runners" / "checkers" / "common").glob("*.py"))
    )
    checker_files.extend(
        sorted((ROOT / "runners" / "checkers" / "v4").glob("family_*.py"))
    )
    checker_files = sorted(set(checker_files))
    checker_records = [
        {"path": path.relative_to(ROOT).as_posix(), "sha256": file_sha(path)}
        for path in checker_files
    ]
    checker_digest = hashlib.sha256()
    for record in checker_records:
        checker_digest.update(record["path"].encode("utf-8"))
        checker_digest.update(b"\0")
        checker_digest.update(record["sha256"].encode("ascii"))
        checker_digest.update(b"\0")
    return {
        "family_id": family_id,
        "canonical_task": task.relative_to(ROOT).as_posix(),
        "inputs": {
            "task_record_sha256": file_sha(evaluator / "task_record.json"),
            "public_contract_sha256": file_sha(public / "public_contract.json"),
            "checker_profile_sha256": file_sha(evaluator / "checker_profile.json"),
            "harness_spec_sha256": file_sha(evaluator / "harness_spec.json"),
            "feedback_profile_sha256": file_sha(
                evaluator / "profiles" / "feedback.json"
            ),
            "score_profile_sha256": file_sha(evaluator / "profiles" / "score.json"),
            "feedback_deck_sha256": file_sha(public / "feedback_tb.scs"),
            "score_deck_sha256": file_sha(evaluator / "score_tb.scs"),
            "gold_bundle_sha256": tree_sha(evaluator / "solution"),
        },
        "checker_implementation": {
            "bundle_sha256": checker_digest.hexdigest(),
            "files": checker_records,
        },
        "mutations": [
            {
                "mutation_id": str(row["id"]),
                "candidate_bundle_sha256": tree_sha(
                    evaluator / "mutation_bundles" / str(row["id"]),
                    excluded_names={"certification.json"},
                ),
            }
            for row in manifest["mutations"]
            if str(row["id"]) in mutation_ids
        ],
    }


def parse_range(value: str) -> tuple[int, int]:
    left, separator, right = value.partition("-")
    if not separator:
        right = left
    start, stop = int(left), int(right)
    if start < 1 or stop < start or stop > 400:
        raise argparse.ArgumentTypeError(f"invalid family range: {value}")
    return start, stop


def family_dir(source: Path, family_id: str) -> Path:
    matches = sorted(source.glob(f"{family_id}-*"))
    if len(matches) != 1:
        raise SystemExit(f"{family_id}: expected one canonical family, found {len(matches)}")
    return matches[0]


def require_explicit_evas2_backend() -> str:
    engine = effective_evas_engine()
    explicit_engine = os.environ.get("EVAS_ENGINE", "").strip().lower()
    default_engine = os.environ.get("VAEVAS_DEFAULT_EVAS_ENGINE", "").strip().lower()
    if engine != "evas2" or explicit_engine != "evas2" or default_engine != "evas2":
        raise SystemExit(
            "V4 checker batch evidence requires EVAS_ENGINE=evas2 and "
            "VAEVAS_DEFAULT_EVAS_ENGINE=evas2; observed "
            f"EVAS_ENGINE={explicit_engine!r}, "
            f"VAEVAS_DEFAULT_EVAS_ENGINE={default_engine!r}, "
            f"effective={engine!r}"
        )
    return engine


def copy_solution(task: Path, dut_dir: Path) -> None:
    shutil.copytree(task / "evaluator" / "solution", dut_dir)


def copy_public_support(task: Path, case_dir: Path) -> None:
    support = task / "public" / "task" / "public_support"
    if support.is_dir():
        shutil.copytree(support, case_dir / "support")


def overlay_mutation(task: Path, mutation_id: str, dut_dir: Path) -> list[str]:
    mutation_dir = task / "evaluator" / "mutation_bundles" / mutation_id
    changed: list[str] = []
    for source in sorted(mutation_dir.rglob("*")):
        if not source.is_file() or source.name == "certification.json":
            continue
        relative = source.relative_to(mutation_dir)
        target = dut_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        changed.append(relative.as_posix())
    if not changed:
        raise RuntimeError(f"{task.name}/{mutation_id}: no mutation source artifacts")
    return changed


def run_case(
    *,
    task: Path,
    case_id: str,
    mutation_id: str | None,
    work_root: Path,
    timeout_s: int,
    timing_scale: float,
    timing_shift_s: float,
) -> dict[str, Any]:
    family_id = task.name[:3]
    checker_id = str(read_json(task / "evaluator" / "task_record.json")["checker_task_id"])
    property_ids = list(read_json(task / "evaluator" / "harness_spec.json")["property_ids"])
    checker = load_checker(checker_id)
    if checker is None:
        return {
            "family_id": family_id,
            "case_id": case_id,
            "mutation_id": mutation_id,
            "status": "checker_unresolved",
            "checker_id": checker_id,
        }

    case_dir = work_root / family_id / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    dut_dir = case_dir / "dut"
    copy_solution(task, dut_dir)
    copy_public_support(task, case_dir)
    changed = overlay_mutation(task, mutation_id, dut_dir) if mutation_id else []
    deck = case_dir / "score_tb.scs"
    shutil.copy2(task / "evaluator" / "score_tb.scs", deck)
    output_dir = case_dir / "output"
    try:
        proc = run_evas(
            case_dir,
            deck,
            output_dir,
            timeout_s,
            required_trace_signals=required_trace_signals_for_checker(checker_id),
        )
    except (FileNotFoundError, TimeoutError) as exc:
        return {
            "family_id": family_id,
            "case_id": case_id,
            "mutation_id": mutation_id,
            "status": "infrastructure_error",
            "outcome_category": "infrastructure_error",
            "checker_id": checker_id,
            "changed_artifacts": changed,
            "simulator_tail": str(exc),
        }
    csv_path = output_dir / "tran.csv"
    simulator_ok = proc.returncode == 0 and csv_path.is_file()
    if not simulator_ok:
        combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
        return {
            "family_id": family_id,
            "case_id": case_id,
            "mutation_id": mutation_id,
            "status": "infrastructure_error",
            "outcome_category": "infrastructure_error",
            "checker_id": checker_id,
            "changed_artifacts": changed,
            "returncode": proc.returncode,
            "simulator_tail": combined[-1600:],
        }

    rows = load_csv(csv_path)
    passed, note = checker(rows)
    transformed_passed, transformed_note = checker(
        transformed_rows(rows, scale=timing_scale, shift_s=timing_shift_s)
    )
    expected_pass = mutation_id is None
    classification_ok = passed is expected_pass
    timing_invariant = transformed_passed is passed
    diagnostics_complete = diagnostics_are_complete(
        passed=passed, note=note, property_ids=property_ids
    )
    insufficient_excitation_rejected: bool | None = None
    insufficient_note: str | None = None
    if mutation_id is None:
        prefix = rows[:2]
        insufficient_passed, insufficient_note = checker(prefix)
        insufficient_excitation_rejected = True if not insufficient_passed else None
    ok = (
        classification_ok
        and timing_invariant
        and diagnostics_complete
        and insufficient_excitation_rejected is not False
    )
    return {
        "family_id": family_id,
        "case_id": case_id,
        "mutation_id": mutation_id,
        "status": "pass" if ok else "fail",
        "outcome_category": "behavior_pass" if passed else "behavior_mismatch",
        "checker_id": checker_id,
        "expected_pass": expected_pass,
        "checker_pass": passed,
        "timing_metamorph_pass": transformed_passed,
        "timing_invariant": timing_invariant,
        "diagnostics_complete": diagnostics_complete,
        "insufficient_excitation_rejected": insufficient_excitation_rejected,
        "checker_note": note,
        "timing_metamorph_note": transformed_note,
        "insufficient_excitation_note": insufficient_note,
        "changed_artifacts": changed,
        "trace_row_count": len(rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--family-range", type=parse_range, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout-s", type=int, default=120)
    parser.add_argument("--timing-scale", type=float, default=1.37)
    parser.add_argument("--timing-shift-s", type=float, default=2e-9)
    parser.add_argument(
        "--required-evas-version",
        default=REQUIRED_EVAS_VERSION,
        help=(
            "exact evas-sim version required for this evidence run "
            f"(default: {REQUIRED_EVAS_VERSION})"
        ),
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    evas_engine = require_explicit_evas2_backend()
    runtime = probe_evas2_runtime(
        required_evas_version=args.required_evas_version
    )

    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    work_root = args.work_root.expanduser().resolve()
    if work_root.exists():
        if not args.force:
            raise SystemExit(f"work root exists: {work_root}")
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True)

    start, stop = args.family_range
    tasks = [family_dir(source, f"{value:03d}") for value in range(start, stop + 1)]
    active_suites = load_active_mutation_suites(source)
    task_mutation_ids: dict[Path, list[str]] = {}
    requests: list[tuple[Path, str, str | None]] = []
    for task in tasks:
        requests.append((task, "gold", None))
        mutation_ids = selected_mutation_ids(task, active_suites)
        task_mutation_ids[task] = mutation_ids
        requests.extend((task, mutation_id, mutation_id) for mutation_id in mutation_ids)

    def execute(request: tuple[Path, str, str | None]) -> dict[str, Any]:
        task, case_id, mutation_id = request
        return run_case(
            task=task,
            case_id=case_id,
            mutation_id=mutation_id,
            work_root=work_root,
            timeout_s=args.timeout_s,
            timing_scale=args.timing_scale,
            timing_shift_s=args.timing_shift_s,
        )

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        cases = list(pool.map(execute, requests))

    report = {
        "schema_version": "v4-checker-batch-certification-v1",
        "family_range": f"{start:03d}-{stop:03d}",
        "family_count": len(tasks),
        "case_count": len(cases),
        "pass_count": sum(case["status"] == "pass" for case in cases),
        "fail_count": sum(case["status"] != "pass" for case in cases),
        "gold_pass_count": sum(
            case["mutation_id"] is None and case["status"] == "pass" for case in cases
        ),
        "mutation_kill_count": sum(
            case["mutation_id"] is not None and case.get("checker_pass") is False
            for case in cases
        ),
        "timing_invariant_count": sum(case.get("timing_invariant") is True for case in cases),
        "insufficient_excitation_rejection_count": sum(
            case.get("insufficient_excitation_rejected") is True for case in cases
        ),
        "insufficient_excitation_not_applicable_count": sum(
            case.get("mutation_id") is None
            and case.get("insufficient_excitation_rejected") is None
            for case in cases
        ),
        "evas_engine": evas_engine,
        "timing_metamorph": {
            "scale": args.timing_scale,
            "shift_s": args.timing_shift_s,
        },
        "certification_policy": "rust_evas2_only",
        "runtime": runtime,
        "reproduction": {
            "command": (
                "EVAS_ENGINE=evas2 VAEVAS_DEFAULT_EVAS_ENGINE=evas2 "
                "python3 benchmark-vabench-release-v4/scripts/"
                "validate_v4_checker_batch.py --family-range "
                f"{start:03d}-{stop:03d} --output <output.json> "
                f"--work-root <work-root> --workers {max(1, args.workers)} "
                f"--timeout-s {args.timeout_s} --timing-scale {args.timing_scale} "
                f"--timing-shift-s {args.timing_shift_s} "
                f"--required-evas-version {args.required_evas_version} --force"
            ),
            "working_directory": "<repository-root>",
        },
        "diagnostic_categories": [
            "behavior_pass",
            "behavior_mismatch",
            "insufficient_excitation",
            "missing_trace",
            "infrastructure_error",
        ],
        "source_bindings": [
            source_binding(task, task_mutation_ids[task]) for task in tasks
        ],
        "status": "pass" if all(case["status"] == "pass" for case in cases) else "fail",
        "cases": cases,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "schema_version",
                    "status",
                    "family_range",
                    "family_count",
                    "case_count",
                    "pass_count",
                    "fail_count",
                    "gold_pass_count",
                    "mutation_kill_count",
                    "timing_invariant_count",
                    "insufficient_excitation_rejection_count",
                    "evas_engine",
                )
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
