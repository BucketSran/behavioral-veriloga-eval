#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import subprocess
from pathlib import Path

from run_gold_suite import (
    ahdl_includes,
    benchmark_root,
    choose_gold_tb,
    list_gold_task_dirs,
    read_meta,
)
from simulate_evas import evaluate_behavior


def project_root() -> Path:
    return benchmark_root().parents[1]


def default_bridge_repo() -> Path:
    return project_root() / "iccad" / "virtuoso-bridge-lite"


def load_csv_rows(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed: dict[str, float] = {}
            for key, value in row.items():
                if key is None or value is None or value == "":
                    continue
                parsed[key] = float(value)
            rows.append(parsed)
    return rows


def interp_at(rows: list[dict[str, float]], sig: str, t: float) -> float:
    if t <= rows[0]["time"]:
        return rows[0].get(sig, 0.0)
    if t >= rows[-1]["time"]:
        return rows[-1].get(sig, 0.0)

    lo = 0
    hi = len(rows) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if rows[mid]["time"] <= t:
            lo = mid
        else:
            hi = mid

    t0 = rows[lo]["time"]
    t1 = rows[hi]["time"]
    y0 = rows[lo].get(sig, 0.0)
    y1 = rows[hi].get(sig, 0.0)
    if t1 == t0:
        return y0
    a = (t - t0) / (t1 - t0)
    return y0 + a * (y1 - y0)


def compare_waveforms(
    evas_csv: Path,
    spectre_csv: Path,
    sample_n: int = 1200,
) -> dict:
    evas_rows = load_csv_rows(evas_csv)
    spectre_rows = load_csv_rows(spectre_csv)
    if not evas_rows or not spectre_rows:
        return {
            "status": "blocked",
            "reason": "empty waveform rows",
        }

    common_signals = sorted((set(evas_rows[0]) & set(spectre_rows[0])) - {"time"})
    if not common_signals:
        return {
            "status": "blocked",
            "reason": "no common saved signals",
        }

    common_start = max(evas_rows[0]["time"], spectre_rows[0]["time"])
    common_end = min(evas_rows[-1]["time"], spectre_rows[-1]["time"])
    if common_end <= common_start:
        return {
            "status": "blocked",
            "reason": "no overlapping time window",
        }

    per_signal: dict[str, dict[str, float]] = {}
    nrmse_values: list[float] = []
    rmse_values: list[float] = []
    max_abs_values: list[float] = []

    dt = (common_end - common_start) / max(sample_n - 1, 1)
    max_lag_samples = max(0, int(round(1e-9 / max(dt, 1e-15))))

    def infer_digital(vals: list[float]) -> tuple[bool, float, float]:
        if not vals:
            return False, 0.0, 0.0
        lo = min(vals)
        hi = max(vals)
        span = hi - lo
        if span < 1e-6:
            return False, lo, hi
        # Relaxed tolerance: accept values within 30% of span from rails
        # This handles clock signals with transition region samples
        tol = max(0.15 * span, 0.05)
        near = sum(1 for v in vals if abs(v - lo) <= tol or abs(v - hi) <= tol)
        return (near / len(vals)) >= 0.95, lo, hi

    for sig in common_signals:
        ev_vals: list[float] = []
        sp_vals: list[float] = []
        merged_vals: list[float] = []
        for idx in range(sample_n):
            t = common_start + (common_end - common_start) * idx / max(sample_n - 1, 1)
            ev = interp_at(evas_rows, sig, t)
            sp = interp_at(spectre_rows, sig, t)
            ev_vals.append(ev)
            sp_vals.append(sp)
            merged_vals.append(ev)
            merged_vals.append(sp)

        digital_ev, ev_lo, ev_hi = infer_digital(ev_vals)
        digital_sp, sp_lo, sp_hi = infer_digital(sp_vals)
        is_digital = digital_ev and digital_sp

        if is_digital:
            ev_thr = 0.5 * (ev_lo + ev_hi)
            sp_thr = 0.5 * (sp_lo + sp_hi)
            ev_bits = [1 if v >= ev_thr else 0 for v in ev_vals]
            sp_bits = [1 if v >= sp_thr else 0 for v in sp_vals]

            best_lag = 0
            best_mismatch = 1.0
            for lag in range(-max_lag_samples, max_lag_samples + 1):
                if lag < 0:
                    xa = ev_bits[-lag:]
                    xb = sp_bits[: sample_n + lag]
                elif lag > 0:
                    xa = ev_bits[: sample_n - lag]
                    xb = sp_bits[lag:]
                else:
                    xa = ev_bits
                    xb = sp_bits

                if not xa or not xb:
                    continue
                mismatches = sum(1 for a, b in zip(xa, xb) if a != b)
                mismatch = mismatches / len(xa)
                if mismatch < best_mismatch:
                    best_mismatch = mismatch
                    best_lag = lag

            span = max(merged_vals) - min(merged_vals)
            # For digital-like signals, treat mismatch ratio as normalized error.
            nrmse = best_mismatch
            rmse = math.sqrt(best_mismatch) * max(span, 1.0)
            max_abs = float(max(span, 1.0)) if best_mismatch > 0 else 0.0
            per_signal[sig] = {
                "rmse_v": rmse,
                "max_abs_v": max_abs,
                "span_v": span,
                "nrmse": nrmse,
                "kind": "digital",
                "best_lag_samples": best_lag,
                "best_lag_s": best_lag * dt,
                "mismatch_ratio": best_mismatch,
            }
        else:
            diffs = [a - b for a, b in zip(ev_vals, sp_vals)]
            mse = sum(d * d for d in diffs) / len(diffs)
            rmse = math.sqrt(mse)
            max_abs = max(abs(d) for d in diffs)
            span = max(merged_vals) - min(merged_vals)
            nrmse = rmse / max(span, 1e-6)
            per_signal[sig] = {
                "rmse_v": rmse,
                "max_abs_v": max_abs,
                "span_v": span,
                "nrmse": nrmse,
                "kind": "analog",
            }

        nrmse_values.append(nrmse)
        rmse_values.append(rmse)
        max_abs_values.append(max_abs)

    sorted_nrmse = sorted(nrmse_values)
    p95_idx = min(len(sorted_nrmse) - 1, max(0, math.ceil(0.95 * len(sorted_nrmse)) - 1))
    max_nrmse = max(sorted_nrmse)
    p95_nrmse = sorted_nrmse[p95_idx]
    max_rmse = max(rmse_values)
    max_abs = max(max_abs_values)
    mean_nrmse = sum(sorted_nrmse) / len(sorted_nrmse)

    passed = (p95_nrmse <= 0.14 and max_nrmse <= 0.22) or (
        max_rmse <= 0.05 and max_abs <= 0.30
    ) or (mean_nrmse <= 0.08 and max_nrmse <= 0.25)

    return {
        "status": "passed" if passed else "needs_review",
        "common_window_s": [common_start, common_end],
        "signals_compared": len(common_signals),
        "samples": sample_n,
        "max_rmse_v": max_rmse,
        "max_abs_v": max_abs,
        "mean_nrmse": mean_nrmse,
        "p95_nrmse": p95_nrmse,
        "max_nrmse": max_nrmse,
        "per_signal": per_signal,
    }


def run_cmd(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None, timeout_s: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )


def run_spectre_case(
    *,
    task_id: str,
    tb_path: Path,
    include_paths: list[Path],
    output_dir: Path,
    bridge_repo: Path,
    cadence_cshrc: str | None,
    timeout_s: int,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    bridge_py = bridge_repo / ".venv" / "bin" / "python"
    result_json = output_dir / "spectre_result.json"
    csv_path = output_dir / "tran_spectre.csv"

    payload = {
        "bridge_repo": str(bridge_repo.resolve()),
        "tb_path": str(tb_path.resolve()),
        "include_paths": [str(p.resolve()) for p in include_paths],
        "output_dir": str(output_dir.resolve()),
        "result_json": str(result_json.resolve()),
        "csv_path": str(csv_path.resolve()),
        "cadence_cshrc": cadence_cshrc or "",
    }

    inline = (
        "import csv, json, os\n"
        "from pathlib import Path\n"
        "from dotenv import load_dotenv\n"
        "payload = json.loads(" + repr(json.dumps(payload)) + ")\n"
        "bridge_repo = Path(payload['bridge_repo'])\n"
        "load_dotenv(bridge_repo / '.env')\n"
        "if payload['cadence_cshrc']:\n"
        "    os.environ['VB_CADENCE_CSHRC'] = payload['cadence_cshrc']\n"
        "from virtuoso_bridge.spectre.runner import SpectreSimulator, spectre_mode_args\n"
        "tb = Path(payload['tb_path'])\n"
        "out = Path(payload['output_dir'])\n"
        "out.mkdir(parents=True, exist_ok=True)\n"
        "sim = SpectreSimulator.from_env(spectre_args=spectre_mode_args('ax'), work_dir=out, output_format='psfascii')\n"
        "res = sim.run_simulation(tb, {'include_files': payload['include_paths']})\n"
        "keys = sorted(res.data.keys())\n"
        "if 'time' in keys:\n"
        "    keys = ['time'] + [k for k in keys if k != 'time']\n"
        "nrows = max((len(v) for v in res.data.values()), default=0)\n"
        "csv_path = Path(payload['csv_path'])\n"
        "with csv_path.open('w', newline='') as f:\n"
        "    writer = csv.writer(f)\n"
        "    writer.writerow(keys)\n"
        "    for i in range(nrows):\n"
        "        writer.writerow([(res.data.get(k, [])[i] if i < len(res.data.get(k, [])) else '') for k in keys])\n"
        "summary = {\n"
        "    'status': res.status.value,\n"
        "    'ok': bool(res.ok),\n"
        "    'errors': list(res.errors),\n"
        "    'warnings': list(res.warnings),\n"
        "    'signals': keys,\n"
        "    'rows': nrows,\n"
        "    'csv_path': str(csv_path),\n"
        "}\n"
        "Path(payload['result_json']).write_text(json.dumps(summary, indent=2), encoding='utf-8')\n"
        "print(json.dumps(summary, indent=2))\n"
    )

    env = os.environ.copy()
    py_path = str(bridge_repo)
    if env.get("PYTHONPATH"):
        py_path = py_path + os.pathsep + env["PYTHONPATH"]
    env["PYTHONPATH"] = py_path

    proc = run_cmd(
        [str(bridge_py), "-c", inline],
        cwd=bridge_repo,
        env=env,
        timeout_s=max(timeout_s, 600),
    )

    if not result_json.exists():
        return {
            "status": "blocked",
            "ok": False,
            "notes": ["spectre_result.json missing"],
            "stdout_tail": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-4000:],
        }

    result = json.loads(result_json.read_text(encoding="utf-8"))
    result["stdout_tail"] = ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-4000:]
    if proc.returncode != 0 and result.get("status") != "success":
        result["status"] = "error"
        result["ok"] = False
    return result


def run_dual_case(
    *,
    task_dir: Path,
    output_root: Path,
    bridge_repo: Path,
    cadence_cshrc: str | None,
    timeout_s: int,
) -> dict:
    gold_dir = task_dir / "gold"
    meta = read_meta(task_dir)
    task_id = meta.get("task_id", task_dir.name)

    tb_path = choose_gold_tb(gold_dir)
    if tb_path is None:
        return {
            "task_id": task_id,
            "status": "FAIL_INFRA",
            "notes": ["no gold testbench found"],
        }

    includes = ahdl_includes(tb_path)
    if not includes:
        return {
            "task_id": task_id,
            "status": "FAIL_INFRA",
            "notes": [f"no ahdl_include found in {tb_path.name}"],
        }

    include_paths = [gold_dir / name for name in includes]
    missing = [str(path.name) for path in include_paths if not path.exists()]
    if missing:
        return {
            "task_id": task_id,
            "status": "FAIL_INFRA",
            "notes": [f"missing included files: {', '.join(missing)}"],
        }

    case_root = output_root / task_id
    evas_root = case_root / "evas"
    spectre_root = case_root / "spectre"
    primary_dut = include_paths[0]

    from run_gold_suite import run_gold_case

    evas_result = run_gold_case(task_dir, output_root, timeout_s)
    evas_csv = evas_root / "tran.csv"
    if not evas_csv.exists():
        evas_csv = case_root / "tran.csv"

    spectre_result = run_spectre_case(
        task_id=task_id,
        tb_path=tb_path,
        include_paths=include_paths,
        output_dir=spectre_root,
        bridge_repo=bridge_repo,
        cadence_cshrc=cadence_cshrc,
        timeout_s=timeout_s,
    )

    notes = [
        f"gold_tb={tb_path.name}",
        f"gold_primary_dut={primary_dut.name}",
    ]

    spectre_csv = spectre_root / "tran_spectre.csv"
    if spectre_result.get("ok") and spectre_csv.exists():
        spectre_sim_correct, spectre_behavior_notes = evaluate_behavior(task_id, spectre_csv)
        notes.extend(f"spectre:{note}" for note in spectre_behavior_notes)
    else:
        spectre_sim_correct = 0.0
        notes.append("spectre:tran_spectre.csv missing or run failed")
        spectre_behavior_notes = []

    if evas_result["status"] == "PASS" and spectre_sim_correct == 1.0 and spectre_csv.exists() and evas_csv.exists():
        parity = compare_waveforms(evas_csv, spectre_csv)
    else:
        parity = {
            "status": "blocked",
            "reason": "prerequisites not met for waveform comparison",
        }

    if evas_result["status"] != "PASS":
        status = "FAIL_EVAS"
    elif not spectre_result.get("ok"):
        status = "FAIL_SPECTRE"
    elif spectre_sim_correct < 1.0:
        status = "FAIL_SPECTRE_BEHAVIOR"
    elif parity.get("status") != "passed":
        status = "FAIL_PARITY"
    else:
        status = "PASS"

    return {
        "task_id": task_id,
        "status": status,
        "gold_dir": str(gold_dir),
        "gold_tb": str(tb_path),
        "gold_includes": includes,
        "evas": evas_result,
        "spectre": {
            **spectre_result,
            "behavior_score": spectre_sim_correct,
            "behavior_notes": spectre_behavior_notes,
        },
        "parity": parity,
        "notes": notes,
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run EVAS + Spectre dual validation on gold end-to-end tasks.")
    ap.add_argument(
        "--output-root",
        default="results/gold-dual-suite",
        help="Output directory relative to benchmark root unless absolute.",
    )
    ap.add_argument("--timeout-s", type=int, default=240)
    ap.add_argument(
        "--task",
        action="append",
        default=[],
        help="Restrict to one or more task IDs with gold assets.",
    )
    ap.add_argument(
        "--bridge-repo",
        default=str(default_bridge_repo()),
        help="Path to virtuoso-bridge-lite repository.",
    )
    ap.add_argument(
        "--cadence-cshrc",
        default=os.environ.get("VB_CADENCE_CSHRC", ""),
        help="Remote Cadence cshrc path used to expose spectre on PATH.",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    bridge_repo = Path(args.bridge_repo).resolve()
    if not bridge_repo.exists():
        print(json.dumps({"status": "blocked", "reason": f"bridge repo not found: {bridge_repo}"}, indent=2))
        return 2

    out_root = Path(args.output_root)
    if not out_root.is_absolute():
        out_root = benchmark_root() / out_root
    out_root.mkdir(parents=True, exist_ok=True)

    selected = set(args.task) if args.task else None
    results = [
        run_dual_case(
            task_dir=task_dir,
            output_root=out_root,
            bridge_repo=bridge_repo,
            cadence_cshrc=args.cadence_cshrc or None,
            timeout_s=args.timeout_s,
        )
        for task_dir in list_gold_task_dirs(selected)
    ]

    summary = {
        "tasks_total": len(results),
        "pass_count": sum(1 for r in results if r["status"] == "PASS"),
        "fail_count": sum(1 for r in results if r["status"] != "PASS"),
        "task_ids": [r["task_id"] for r in results],
        "bridge_repo": str(bridge_repo),
        "cadence_cshrc": args.cadence_cshrc or "",
        "results": results,
    }
    (out_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if summary["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
