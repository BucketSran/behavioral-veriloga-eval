#!/usr/bin/env python3
"""Profile fixed native execution scheduling; not model-quality evidence."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import threading
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "benchmark-vabench-release-v4"
CALIBRATION = PACKAGE / "operations" / "calibration_pilot"
for import_root in (ROOT, CALIBRATION, PACKAGE / "runners"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from runners.agent_harness.phase_timing import collect_phases, measure_phase  # noqa: E402


PHASE_SCHEMA = "vaevas-native-execution-profile-v1"
CLAIM_SCOPE = "execution_profile_not_model_quality"
DEFAULT_WORKERS = (1, 2, 4)


@dataclass(frozen=True)
class CellExecutionContext:
    worker_run_id: str
    workers: int
    cell_index: int
    attempt_id: str
    enqueued_at_s: float


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256_bytes(payload)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def file_hashes(root: Path) -> dict[str, str]:
    if not root.is_dir():
        raise ValueError(f"missing file hash root: {root}")
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def parse_worker_counts(value: str) -> tuple[int, ...]:
    try:
        workers = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("workers must be comma-separated integers") from exc
    if not workers or any(count < 1 for count in workers):
        raise argparse.ArgumentTypeError("workers must all be positive")
    if len(set(workers)) != len(workers):
        raise argparse.ArgumentTypeError("workers must not contain duplicates")
    return workers


class _ActiveCells:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.current = 0
        self.peak = 0

    def enter(self) -> None:
        with self._lock:
            self.current += 1
            self.peak = max(self.peak, self.current)

    def exit(self) -> None:
        with self._lock:
            self.current -= 1


def _normalize_result(cell: Mapping[str, Any], result: Mapping[str, Any], attempt_id: str) -> dict[str, Any]:
    cell_id = result.get("cell_id")
    if not isinstance(cell_id, str) or not cell_id:
        raise ValueError("profiled cell result is missing cell_id")
    if cell_id != cell["cell_id"] or result.get("attempt_id") != attempt_id:
        raise ValueError("profiled result identity does not match scheduled cell/attempt")
    submission_files = result.get("submission_files") or {}
    if not isinstance(submission_files, Mapping) or not submission_files:
        raise ValueError(f"profiled cell {cell_id} has invalid submission_files")
    verdict = result.get("verdict") or {}
    if (not isinstance(verdict, Mapping) or not isinstance(verdict.get("judge_status"), str)
            or not verdict["judge_status"] or type(verdict.get("score")) not in (int, float)
            or not math.isfinite(verdict["score"]) or not 0 <= verdict["score"] <= 1):
        raise ValueError(f"profiled cell {cell_id} has invalid verdict")
    digest = result.get("submission_tree_sha256")
    if (not isinstance(digest, str) or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)):
        raise ValueError("profiled submission requires a content digest")
    signature = {
        "submission_files": dict(sorted((str(key), str(value)) for key, value in submission_files.items())),
        "submission_tree_sha256": result.get("submission_tree_sha256"),
        "verdict": {"judge_status": verdict["judge_status"], "score": verdict["score"]},
    }
    return {
        "cell_id": cell_id,
        "expected_cell_id": cell.get("cell_id"),
        "attempt_id": result.get("attempt_id"),
        "status": result.get("status"),
        "signature": signature,
        "signature_sha256": canonical_sha256(signature),
    }


def _run_one(
    *,
    cells: Sequence[Mapping[str, Any]],
    workers: int,
    run_id: str,
    execute_cell: Callable[[dict[str, Any], CellExecutionContext], Mapping[str, Any]],
) -> dict[str, Any]:
    scheduled_at = time.perf_counter()
    enqueued = [time.perf_counter() for _ in cells]
    active = _ActiveCells()
    completed: list[dict[str, Any] | None] = [None] * len(cells)
    errors: list[str] = []

    def execute(index: int, cell: Mapping[str, Any]) -> dict[str, Any]:
        start = time.perf_counter()
        active.enter()
        attempt_id = f"{cell['cell_id']}-attempt-0001"
        context = CellExecutionContext(
            worker_run_id=run_id,
            workers=workers,
            cell_index=index,
            attempt_id=attempt_id,
            enqueued_at_s=enqueued[index],
        )
        try:
            with collect_phases(cell_id=str(cell["cell_id"]), attempt_id=attempt_id) as timing:
                with measure_phase("cell"):
                    result = dict(execute_cell(dict(cell), context))
            normalized = _normalize_result(cell, result, attempt_id)
            return {
                **normalized,
                "queue_delay_s": start - enqueued[index],
                "latency_s": time.perf_counter() - start,
                "phase_timing": timing.to_document(),
            }
        finally:
            active.exit()

    if workers == 1:
        for index, cell in enumerate(cells):
            try:
                completed[index] = execute(index, cell)
            except Exception as exc:  # noqa: BLE001 - preserve accounting in report.
                errors.append(f"{cell.get('cell_id')}: {type(exc).__name__}")
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(execute, index, cell): index for index, cell in enumerate(cells)}
            for future in as_completed(futures):
                index = futures[future]
                try:
                    completed[index] = future.result()
                except Exception as exc:  # noqa: BLE001 - preserve accounting in report.
                    errors.append(f"{cells[index].get('cell_id')}: {type(exc).__name__}")

    elapsed = time.perf_counter() - scheduled_at
    rows = [row for row in completed if row is not None]
    cell_ids = [row["cell_id"] for row in rows]
    duplicates = sorted({cell_id for cell_id in cell_ids if cell_ids.count(cell_id) > 1})
    missing = sorted(str(cell["cell_id"]) for cell in cells if cell["cell_id"] not in cell_ids)
    if duplicates:
        raise ValueError(f"profiled workload produced duplicate cells: {duplicates}")
    if errors:
        raise ValueError("profiled workload failed: " + "; ".join(errors))
    if missing:
        raise ValueError(f"profiled workload missed scheduled cells: {missing}")
    return {
        "run_id": run_id,
        "workers": workers,
        "cell_count": len(cells),
        "terminal_count": len(rows),
        "wall_s": elapsed,
        "throughput_cells_per_s": len(rows) / elapsed if elapsed > 0 else None,
        "latency_s": {
            "min": min((row["latency_s"] for row in rows), default=None),
            "max": max((row["latency_s"] for row in rows), default=None),
            "sum": sum(row["latency_s"] for row in rows),
        },
        "queue_delay_s": {
            "min": min((row["queue_delay_s"] for row in rows), default=None),
            "max": max((row["queue_delay_s"] for row in rows), default=None),
            "sum": sum(row["queue_delay_s"] for row in rows),
        },
        "peak_active_cells": active.peak,
        "resources": {
            "cpu_peak": None,
            "ram_peak_bytes": None,
            "peak_containers": None,
            "note": "Resource counters are not measured by this profiler; peak_active_cells is scheduler concurrency only.",
        },
        "failures": [],
        "cells": rows,
    }


def _compare_runs(runs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    baseline: dict[str, str] | None = None
    mismatches: list[str] = []
    for run in runs:
        signatures = {cell["cell_id"]: cell["signature_sha256"] for cell in run["cells"]}
        if baseline is None:
            baseline = signatures
            continue
        if signatures.keys() != baseline.keys():
            raise ValueError("profiled cell roster differs across workers")
        for cell_id, digest in signatures.items():
            if digest != baseline[cell_id]:
                mismatches.append(f"{cell_id}@workers={run['workers']}")
    if mismatches:
        raise ValueError("profiled submission or verdict differs across workers: " + ", ".join(mismatches))
    return {
        "submission_and_verdict_stable": True,
        "baseline_workers": runs[0]["workers"] if runs else None,
        "compared_worker_counts": [run["workers"] for run in runs],
    }


def profile_workload(
    output_root: Path,
    *,
    cells: Sequence[Mapping[str, Any]],
    worker_counts: Iterable[int] = DEFAULT_WORKERS,
    execute_cell: Callable[[dict[str, Any], CellExecutionContext], Mapping[str, Any]],
    workload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    worker_tuple = tuple(worker_counts)
    if not cells:
        raise ValueError("profile workload requires at least one cell")
    if not worker_tuple or any(worker < 1 for worker in worker_tuple):
        raise ValueError("worker counts must be positive")
    if len(set(worker_tuple)) != len(worker_tuple):
        raise ValueError("worker counts must be unique")
    expected_ids = [cell.get("cell_id") for cell in cells]
    if any(not isinstance(cell_id, str) or not cell_id for cell_id in expected_ids):
        raise ValueError("every profile cell requires a cell_id")
    if len(set(expected_ids)) != len(expected_ids):
        raise ValueError("profile workload schedule contains duplicate cell ids")

    if any(path.is_symlink() for path in (output_root, *output_root.parents)):
        raise ValueError("profile output must not use symlinks")
    output_root.mkdir(parents=True, exist_ok=False)
    started = now()
    runs = []
    for workers in worker_tuple:
        run = _run_one(
            cells=cells,
            workers=workers,
            run_id=f"workers-{workers}",
            execute_cell=execute_cell,
        )
        runs.append(run)
        write_json(output_root / f"workers-{workers}.json", run)
    report = {
        "schema_version": PHASE_SCHEMA,
        "started_at": started,
        "ended_at": now(),
        "claim_scope": CLAIM_SCOPE,
        "workload": {
            "provider": "custom_executor",
            "live_model_calls": None,
            "native_max_attempts": 1,
            "cell_count": len(cells),
            **dict(workload or {}),
        },
        "runs": runs,
        "comparison": _compare_runs(runs),
    }
    write_json(output_root / "native-execution-profile.json", report)
    return report


def fixture_cells(count: int = 4) -> list[dict[str, Any]]:
    return [
        {
            "cell_id": f"fixture-cell-{index:03d}",
            "task_id": "v4-001",
            "family_id": "001",
            "form": "dut",
            "mode": "G2",
            "experimental_arm": "Agentic",
        }
        for index in range(count)
    ]


def fixture_executor(cell: dict[str, Any], context: CellExecutionContext) -> dict[str, Any]:
    with measure_phase("model"):
        time.sleep(0.002)
    with measure_phase("tool"):
        time.sleep(0.001)
    with measure_phase("freeze"):
        pass
    with measure_phase("final_judge"):
        pass
    content = f"// deterministic public profile fixture\n// {cell['task_id']} {cell['cell_id']}\n"
    return {
        "cell_id": cell["cell_id"],
        "attempt_id": context.attempt_id,
        "status": "behavior_failure",
        "submission_files": {"model.va": content},
        "submission_tree_sha256": sha256_text(content),
        "verdict": {"judge_status": "behavior_failure", "score": 0},
    }


def native_docker_cells(family_id: str = "001") -> list[dict[str, Any]]:
    import build_campaign
    from scripts import run_v4_r53_clean_room_smoke as smoke

    campaign = build_campaign.build_campaign(
        smoke.DEFAULT_RELEASE,
        family_ids=[family_id],
        model_provider="deterministic-public-contract-profile",
        model=smoke.DEFAULT_MODEL,
        per_turn_max_tokens=4096,
        repetitions=1,
        three_arm_g0_g2=True,
    )
    cells = [cell for cell in campaign["cells"] if cell["experimental_arm"] == "Agentic"]
    if not cells:
        raise ValueError(f"no Agentic cells found for family {family_id}")
    return cells


def native_docker_executor(
    output_root: Path,
    evas_command: str,
    campaign_file_sha256: str,
) -> Callable[[dict[str, Any], CellExecutionContext], Mapping[str, Any]]:
    from scripts import run_v4_r53_clean_room_smoke as smoke
    from public_validation import public_execution_contract

    def execute(cell: dict[str, Any], context: CellExecutionContext) -> Mapping[str, Any]:
        runtime_root = output_root / context.worker_run_id / "native-runtime"
        args = smoke.parse_args(["--output-root", str(output_root / context.worker_run_id)])
        args.evas_command, identity = smoke.resolve_evas_command(evas_command)
        smoke.configure_runner_args(args, runtime_root, identity)
        args.episode_backend = "native-mini-swe"
        args.native_max_attempts = 1
        args.campaign_file_sha256 = campaign_file_sha256
        contract = smoke.public_contract(smoke.DEFAULT_RELEASE, cell["task_id"])
        public_root = (
            smoke.DEFAULT_RELEASE
            / smoke.task_index_row(smoke.DEFAULT_RELEASE, cell["task_id"])["public_contract"]
        ).parent / "public"
        public_command, _ = public_execution_contract(smoke.read_json(public_root / "evas_runtime.json"))
        client = smoke.client_for_arm(
            cell["experimental_arm"],
            smoke.public_stub_artifacts(contract),
            smoke.DEFAULT_MODEL,
            public_command,
        )
        smoke.run_campaign.run_cell_preserving_failure(cell, args, client)
        row = smoke.score_campaign.read_native_cell(
            runtime_root / cell["cell_id"],
            cell,
            campaign_file_sha256=campaign_file_sha256,
        )
        submission = runtime_root / cell["cell_id"] / "evidence/final_submission"
        hashes = file_hashes(submission)
        manifest = smoke.read_json(runtime_root / cell["cell_id"] / "evidence/native-launcher/manifest.json")
        return {
            "cell_id": cell["cell_id"],
            "attempt_id": manifest["attempt_id"],
            "status": row.get("status", row.get("judge_status")),
            "submission_files": hashes,
            "submission_tree_sha256": canonical_sha256(hashes),
            "verdict": {"judge_status": row.get("judge_status"), "score": row.get("score")},
        }

    return execute


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=parse_worker_counts, default=DEFAULT_WORKERS)
    parser.add_argument("--fixture", action="store_true", help="Use the free deterministic fixture executor.")
    parser.add_argument("--native-docker", action="store_true", help="Run the fixed native Docker/EVAS workload.")
    parser.add_argument("--family-id", default="001")
    parser.add_argument("--fixture-cells", type=int, default=4)
    parser.add_argument("--evas-command", default=str(ROOT / ".venv/bin/evas"))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.fixture == args.native_docker:
        raise SystemExit("select exactly one of --fixture or --native-docker")
    if args.fixture:
        cells = fixture_cells(args.fixture_cells)
        executor = fixture_executor
        workload = {
            "provider": "deterministic_fixture",
            "live_model_calls": 0,
            "execution": "in_process_fixture",
        }
    else:
        cells = native_docker_cells(args.family_id)
        campaign_file_sha256 = canonical_sha256(
            {"profile": "native-docker-fixed-public-stub", "cells": cells}
        )
        executor = native_docker_executor(args.output_root, args.evas_command, campaign_file_sha256)
        workload = {
            "provider": "deterministic_public_contract_stub",
            "live_model_calls": 0,
            "execution": "native_docker_evas",
            "family_id": args.family_id,
            "campaign_file_sha256": campaign_file_sha256,
        }
    report = profile_workload(
        args.output_root,
        cells=cells,
        worker_counts=args.workers,
        execute_cell=executor,
        workload=workload,
    )
    report_path = args.output_root / "native-execution-profile.json"
    print(json.dumps({"report": str(report_path), "report_sha256": sha256_file(report_path)}, sort_keys=True))
    return 0 if report["comparison"]["submission_and_verdict_stable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
