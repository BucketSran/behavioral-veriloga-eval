#!/usr/bin/env python3
"""Validate benchmark-v2 draft gold tasks with EVAS and real Spectre."""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from score import build_model_results, spectre_strict_preflight
from simulate_evas import parse_evas_log_diagnostics, parse_evas_runtime_error, parse_evas_timing, run_evas
from spectre_validate_baseline import (
    DEFAULT_ENV,
    _copy_flat_spectre_input,
    _include_files_for,
    _import_bridge,
    _load_env,
    _write_spectre_csv,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCH = ROOT / "benchmark-v2"
BENCH = DEFAULT_BENCH
TASK_ROOT = BENCH / "tasks"
BENCH_FAMILY = "benchmark-v2"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _task_dirs(selected: set[str] | None = None) -> list[Path]:
    dirs = []
    for meta_path in sorted(TASK_ROOT.glob("*/meta.json")):
        task_dir = meta_path.parent
        meta = _read_json(meta_path)
        task_id = meta.get("task_id", task_dir.name)
        if selected and task_id not in selected:
            continue
        dirs.append(task_dir)
    return dirs


def _choose_tb(stage_dir: Path) -> Path | None:
    for pattern in ("tb_ref.scs", "tb*_ref.scs", "tb*.scs", "*.scs"):
        matches = sorted(stage_dir.glob(pattern))
        if matches:
            return matches[0]
    return None


def _ahdl_includes(tb_path: Path) -> list[str]:
    text = tb_path.read_text(encoding="utf-8", errors="ignore")
    return re.findall(r'^\s*ahdl_include\s+"([^"]+)"', text, flags=re.MULTILINE)


def _stage_gold(task_dir: Path, stage_dir: Path) -> tuple[Path, Path]:
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True)
    gold = task_dir / "gold"
    for src in gold.iterdir():
        if src.is_file():
            shutil.copy2(src, stage_dir / src.name)
    tb = _choose_tb(stage_dir)
    if tb is None:
        return stage_dir / "dut.va", stage_dir / "tb_ref.scs"
    includes = _ahdl_includes(tb)
    if includes and (stage_dir / includes[0]).exists():
        return stage_dir / includes[0], tb
    vas = sorted(stage_dir.glob("*.va"))
    dut = vas[0] if vas else stage_dir / "dut.va"
    return dut, tb


def _stage_candidate(
    task_dir: Path,
    stage_dir: Path,
    *,
    candidate_root: Path | None,
    model: str,
    sample_idx: int,
) -> tuple[Path, Path]:
    if candidate_root is None:
        return _stage_gold(task_dir, stage_dir)
    sample_dir = candidate_root / model / task_dir.name / f"sample_{sample_idx}"
    if not sample_dir.is_dir():
        raise FileNotFoundError(f"missing candidate sample: {sample_dir}")
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True)
    for src in sample_dir.iterdir():
        if src.is_file() and src.suffix.lower() in {".va", ".scs", ".csv", ".txt", ".json"}:
            shutil.copy2(src, stage_dir / src.name)
    dut = stage_dir / "dut.va"
    tb = stage_dir / "tb_ref.scs"
    if not tb.exists():
        tbs = sorted(stage_dir.glob("*.scs"))
        if tbs:
            tb = tbs[0]
    if not dut.exists():
        vas = sorted(stage_dir.glob("*.va"))
        if vas:
            dut = vas[0]
    return dut, tb


def _load_checker(task_dir: Path):
    checker_path = task_dir / "checker.py"
    spec = importlib.util.spec_from_file_location(f"{task_dir.name}_checker", checker_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _run_checker(task_dir: Path, csv_path: Path) -> tuple[float, list[str], dict[str, Any]]:
    try:
        result = _load_checker(task_dir).check_csv(csv_path)
    except Exception as exc:  # noqa: BLE001 - checker boundary
        return 0.0, [f"checker_exception={type(exc).__name__}: {str(exc)[:300]}"], {}
    ok = bool(result.get("pass"))
    notes = [str(item) for item in result.get("notes", [])]
    return (1.0 if ok else 0.0), notes, result


def _status(scores: dict[str, float], required_axes: list[str] | None = None) -> str:
    axes = required_axes or ["dut_compile", "tb_compile", "sim_correct"]
    if "dut_compile" in axes and scores.get("dut_compile", 0.0) < 1.0:
        return "FAIL_DUT_COMPILE"
    if "tb_compile" in axes and scores.get("tb_compile", 0.0) < 1.0:
        return "FAIL_TB_COMPILE"
    if "sim_correct" in axes and scores.get("sim_correct", 0.0) < 1.0:
        return "FAIL_SIM_CORRECTNESS"
    return "PASS"


def _weighted(scores: dict[str, float], required_axes: list[str] | None = None) -> float:
    axes = required_axes or ["dut_compile", "tb_compile", "sim_correct"]
    return round(sum(scores.get(axis, 0.0) for axis in axes) / len(axes), 4)


def validate_evas(
    task_dir: Path,
    case_out: Path,
    timeout_s: int,
    *,
    candidate_root: Path | None = None,
    model: str = "",
    sample_idx: int = 0,
) -> dict[str, Any]:
    meta = _read_json(task_dir / "meta.json")
    task_id = meta["task_id"]
    required_axes = meta.get("scoring", ["dut_compile", "tb_compile", "sim_correct"])
    stage_dir = case_out / "staged"
    _dut, tb = _stage_candidate(task_dir, stage_dir, candidate_root=candidate_root, model=model, sample_idx=sample_idx)
    output_dir = case_out / "evas_output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    proc = run_evas(stage_dir, tb, output_dir, timeout_s)
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    (case_out / "evas_console.log").write_text(combined, encoding="utf-8")
    csv_path = output_dir / "tran.csv"
    scores = {
        "dut_compile": 1.0 if "Compiled Verilog-A module:" in combined else 0.0,
        "tb_compile": 1.0 if ("Transient Analysis" in combined or csv_path.exists()) else 0.0,
        "sim_correct": 0.0,
    }
    notes = [f"returncode={proc.returncode}"]
    runtime = parse_evas_runtime_error(combined)
    if runtime:
        notes.append("evas_runtime_error=" + runtime)
    notes.extend(parse_evas_log_diagnostics(combined))
    checker_result = {}
    if "sim_correct" not in required_axes:
        scores["sim_correct"] = 1.0
        notes.append("sim_correct_not_required")
    elif proc.returncode == 0 and csv_path.exists():
        sim_score, checker_notes, checker_result = _run_checker(task_dir, csv_path)
        scores["sim_correct"] = sim_score
        notes.extend(checker_notes)
    else:
        notes.append("tran.csv missing")
    scores["weighted_total"] = _weighted(scores, required_axes)
    result = {
        "task_id": task_id,
        "backend": "evas",
        "source": "candidate" if candidate_root else "gold",
        "status": _status(scores, required_axes),
        "scores": scores,
        "notes": notes,
        "checker_result": checker_result,
        "timing": parse_evas_timing(combined),
        "artifacts": {
            "staged_dir": str(stage_dir),
            "tb": str(tb),
            "tran_csv": str(csv_path) if csv_path.exists() else None,
        },
    }
    (case_out / "evas_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def validate_spectre(
    task_dir: Path,
    case_out: Path,
    sim,
    timeout_s: int,
    spectre_mode: str,
    *,
    candidate_root: Path | None = None,
    model: str = "",
    sample_idx: int = 0,
) -> dict[str, Any]:
    meta = _read_json(task_dir / "meta.json")
    task_id = meta["task_id"]
    required_axes = meta.get("scoring", ["dut_compile", "tb_compile", "sim_correct"])
    stage_dir = case_out / "staged"
    _dut, tb = _stage_candidate(task_dir, stage_dir, candidate_root=candidate_root, model=model, sample_idx=sample_idx)
    strict_status, strict_scores, strict_notes = spectre_strict_preflight(
        family=meta.get("family", BENCH_FAMILY),
        required_axes=required_axes,
        staged_tb=tb,
        staged_va_paths=sorted(stage_dir.glob("*.va")),
    )
    input_dir = case_out / "spectre_input"
    netlist = _copy_flat_spectre_input(stage_dir, tb, input_dir)
    include_files = _include_files_for(netlist)
    spectre_dir = case_out / "spectre"
    if spectre_dir.exists():
        shutil.rmtree(spectre_dir)
    spectre_dir.mkdir(parents=True)
    sim._work_dir = spectre_dir

    notes = list(strict_notes)
    checker_result = {}
    try:
        bridge_console = io.StringIO()
        with contextlib.redirect_stdout(bridge_console), contextlib.redirect_stderr(bridge_console):
            spectre_result = sim.run_simulation(netlist, {"include_files": include_files})
        (case_out / "bridge_console.log").write_text(bridge_console.getvalue(), encoding="utf-8")
        returncode = spectre_result.metadata.get("returncode")
        csv_path = case_out / "tran.csv"
        csv_ok, csv_note = _write_spectre_csv(spectre_result.data or {}, csv_path)
        notes.append(csv_note)
        scores = {
            "dut_compile": 1.0 if returncode == 0 else 0.0,
            "tb_compile": 1.0 if returncode == 0 and csv_ok else 0.0,
            "sim_correct": 0.0,
        }
        if "sim_correct" not in required_axes:
            scores["sim_correct"] = 1.0
            notes.append("sim_correct_not_required")
        elif returncode == 0 and csv_ok:
            sim_score, checker_notes, checker_result = _run_checker(task_dir, csv_path)
            scores["sim_correct"] = sim_score
            notes.extend(checker_notes)
        elif returncode != 0:
            notes.append(f"spectre_returncode={returncode}")
        else:
            notes.append("spectre_tran_csv_missing")
        command = spectre_result.metadata.get("spectre_command", "")
        remote_match = re.search(r"(/tmp/virtuoso_bridge_[^/]+/virtuoso_bridge_spectre/[0-9a-f]+)/", command)
        extra = {
            "spectre_returncode": returncode,
            "spectre_execution_status": getattr(spectre_result.status, "value", str(spectre_result.status)),
            "spectre_errors": spectre_result.errors,
            "spectre_warnings": spectre_result.warnings[:20],
            "spectre_remote_dir": remote_match.group(1) + "/" if remote_match else None,
            "spectre_command": command,
        }
    except Exception as exc:  # noqa: BLE001
        scores = {"dut_compile": 0.0, "tb_compile": 0.0, "sim_correct": 0.0}
        notes.append(f"spectre_exception={type(exc).__name__}: {str(exc)[:300]}")
        extra = {}

    scores["weighted_total"] = _weighted(scores, required_axes)
    result = {
        "task_id": task_id,
        "backend": "spectre",
        "source": "candidate" if candidate_root else "gold",
        "spectre_mode": spectre_mode,
        "status": _status(scores, required_axes),
        "scores": scores,
        "notes": notes,
        "checker_result": checker_result,
        "strict_preflight_status": strict_status,
        "strict_preflight_scores": strict_scores,
        "artifacts": {"staged_dir": str(stage_dir), "tb": str(tb), "tran_csv": str(case_out / "tran.csv")},
        **extra,
    }
    (case_out / "spectre_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def _aggregate(results: list[dict[str, Any]], backend: str) -> dict[str, Any]:
    model_like = [
        {
            "task_id": r["task_id"],
            "family": BENCH_FAMILY,
            "required_axes": ["dut_compile", "tb_compile", "sim_correct"],
            "scores": r.get("scores", {}),
            "status": r.get("status", "FAIL_INFRA"),
        }
        for r in results
    ]
    aggregate = build_model_results(f"{BENCH_FAMILY}-gold-{backend}", model_like, 0.0, 1.0)
    aggregate["backend"] = backend
    aggregate["pass_tasks"] = [r["task_id"] for r in results if r.get("status") == "PASS"]
    aggregate["fail_tasks"] = [
        {"task_id": r["task_id"], "status": r.get("status"), "notes": r.get("notes", [])[-5:]}
        for r in results
        if r.get("status") != "PASS"
    ]
    return aggregate


def main() -> int:
    global BENCH, TASK_ROOT, BENCH_FAMILY

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--backend", choices=["evas", "spectre", "both"], default="both")
    ap.add_argument("--bench-dir", default=str(DEFAULT_BENCH), help="Benchmark root containing tasks/ and common_checker.py.")
    ap.add_argument("--family", default="benchmark-v2", help="Family label used in aggregate result files.")
    ap.add_argument("--output-dir", default="results/benchmark-v2-gold-validation-2026-04-29")
    ap.add_argument("--candidate-dir", default="", help="Optional generated-root to validate instead of benchmark-v2 gold.")
    ap.add_argument("--model", default="completion-package-v0", help="Model slug under --candidate-dir.")
    ap.add_argument("--sample-idx", type=int, default=0)
    ap.add_argument("--task", action="append", default=[])
    ap.add_argument("--timeout-s", type=int, default=180)
    ap.add_argument("--env", default=str(DEFAULT_ENV))
    ap.add_argument("--profile", default="ci")
    ap.add_argument("--spectre-mode", default="spectre", choices=["spectre", "aps", "x", "cx", "ax", "mx", "lx", "vx"])
    ap.add_argument("--keep-remote-files", action="store_true")
    args = ap.parse_args()

    BENCH = Path(args.bench_dir)
    if not BENCH.is_absolute():
        BENCH = ROOT / BENCH
    TASK_ROOT = BENCH / "tasks"
    BENCH_FAMILY = args.family

    out_root = Path(args.output_dir)
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    out_root.mkdir(parents=True, exist_ok=True)
    candidate_root = Path(args.candidate_dir) if args.candidate_dir else None
    if candidate_root and not candidate_root.is_absolute():
        candidate_root = ROOT / candidate_root
    model_slug = args.model.replace("/", "_")
    selected = set(args.task) if args.task else None
    tasks = _task_dirs(selected)
    if not tasks:
        print("[benchmark-v2-validate] no tasks selected")
        return 1

    sim = None
    if args.backend in {"spectre", "both"}:
        _load_env(Path(args.env))
        SpectreSimulator, spectre_mode_args = _import_bridge()
        sim = SpectreSimulator(
            spectre_args=spectre_mode_args(args.spectre_mode),
            timeout=args.timeout_s,
            work_dir=out_root / "_spectre_runs",
            output_format="psfascii",
            keep_remote_files=args.keep_remote_files,
            remote=True,
            profile=args.profile,
        )

    evas_results: list[dict[str, Any]] = []
    spectre_results: list[dict[str, Any]] = []
    for idx, task_dir in enumerate(tasks, start=1):
        task_id = _read_json(task_dir / "meta.json")["task_id"]
        print(f"[benchmark-v2-validate] {idx}/{len(tasks)} {task_id}", flush=True)
        case_out = out_root / task_id
        case_out.mkdir(parents=True, exist_ok=True)
        if args.backend in {"evas", "both"}:
            evas_results.append(
                validate_evas(
                    task_dir,
                    case_out,
                    args.timeout_s,
                    candidate_root=candidate_root,
                    model=model_slug,
                    sample_idx=args.sample_idx,
                )
            )
        if args.backend in {"spectre", "both"}:
            assert sim is not None
            spectre_results.append(
                validate_spectre(
                    task_dir,
                    case_out,
                    sim,
                    args.timeout_s,
                    args.spectre_mode,
                    candidate_root=candidate_root,
                    model=model_slug,
                    sample_idx=args.sample_idx,
                )
            )

    summary: dict[str, Any] = {
        "total_tasks": len(tasks),
        "backend": args.backend,
        "source": "candidate" if candidate_root else "gold",
        "candidate_root": str(candidate_root) if candidate_root else None,
        "model": model_slug if candidate_root else None,
    }
    if evas_results:
        summary["evas"] = _aggregate(evas_results, "evas")
        (out_root / "evas_model_results.json").write_text(json.dumps(summary["evas"], indent=2), encoding="utf-8")
    if spectre_results:
        summary["spectre"] = _aggregate(spectre_results, "spectre")
        (out_root / "spectre_model_results.json").write_text(json.dumps(summary["spectre"], indent=2), encoding="utf-8")
    if evas_results and spectre_results:
        e_by_task = {r["task_id"]: r for r in evas_results}
        s_by_task = {r["task_id"]: r for r in spectre_results}
        mismatches = []
        for task_id in sorted(e_by_task):
            if (e_by_task[task_id]["status"] == "PASS") != (s_by_task[task_id]["status"] == "PASS"):
                mismatches.append(
                    {
                        "task_id": task_id,
                        "evas_status": e_by_task[task_id]["status"],
                        "spectre_status": s_by_task[task_id]["status"],
                        "evas_notes": e_by_task[task_id].get("notes", [])[-5:],
                        "spectre_notes": s_by_task[task_id].get("notes", [])[-5:],
                    }
                )
        summary["pass_mismatches"] = mismatches
    (out_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[benchmark-v2-validate] wrote {out_root}")
    if "evas" in summary:
        print(f"[benchmark-v2-validate] EVAS {summary['evas']['pass_count']}/{summary['evas']['total_tasks']}")
    if "spectre" in summary:
        print(f"[benchmark-v2-validate] Spectre {summary['spectre']['pass_count']}/{summary['spectre']['total_tasks']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
