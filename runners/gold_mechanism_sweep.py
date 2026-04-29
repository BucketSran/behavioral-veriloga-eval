#!/usr/bin/env python3
"""Run non-mutating gold parameter sweeps to distill mechanism knowledge."""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shutil
import sys
from pathlib import Path

from simulate_evas import rising_edges, run_case

ROOT = Path(__file__).resolve().parents[1]


def _task_dir(task_id: str) -> Path:
    for meta_path in sorted((ROOT / "tasks").rglob("meta.json")):
        task_dir = meta_path.parent
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if (meta.get("task_id") or meta.get("id") or task_dir.name) == task_id:
            return task_dir
    raise SystemExit(f"task not found: {task_id}")


def _read_csv(path: Path) -> list[dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, float]] = []
        for row in reader:
            parsed: dict[str, float] = {}
            for key, value in row.items():
                try:
                    parsed[key] = float(value)
                except (TypeError, ValueError):
                    parsed[key] = float("nan")
            rows.append(parsed)
        return rows


def _first_rising(times: list[float], values: list[float], threshold: float = 0.45) -> float:
    edges = rising_edges(values, times, threshold=threshold)
    return edges[0] if edges else float("nan")


def _high_fraction(rows: list[dict[str, float]], signal: str, threshold: float = 0.45) -> float:
    if not rows or signal not in rows[0] or len(rows) < 2:
        return 0.0
    high_dt = 0.0
    total_dt = 0.0
    for prev, cur in zip(rows, rows[1:]):
        dt = cur["time"] - prev["time"]
        if dt <= 0:
            continue
        total_dt += dt
        if 0.5 * (prev[signal] + cur[signal]) > threshold:
            high_dt += dt
    return high_dt / max(total_dt, 1e-18)


def _edge_metrics(rows: list[dict[str, float]]) -> dict:
    if not rows or not {"time", "ref_clk", "fb_clk", "lock", "vctrl_mon"}.issubset(rows[0]):
        return {"metrics_error": "missing required columns"}
    times = [row["time"] for row in rows]
    ref_edges = rising_edges([row["ref_clk"] for row in rows], times, threshold=0.45)
    fb_edges = rising_edges([row["fb_clk"] for row in rows], times, threshold=0.45)
    lock_edges = rising_edges([row["lock"] for row in rows], times, threshold=0.45)
    t_end = times[-1]
    t_start = 0.8 * t_end
    ref_late = [t for t in ref_edges if t_start <= t <= t_end]
    fb_late = [t for t in fb_edges if t_start <= t <= t_end]
    late_edge_ratio = len(fb_late) / max(len(ref_late), 1)
    vctrl = [row["vctrl_mon"] for row in rows]
    return {
        "ref_edges": len(ref_edges),
        "fb_edges": len(fb_edges),
        "lock_edges": len(lock_edges),
        "ref_late_edges": len(ref_late),
        "fb_late_edges": len(fb_late),
        "late_edge_ratio_count": late_edge_ratio,
        "lock_time": lock_edges[0] if lock_edges else float("nan"),
        "lock_high_fraction": _high_fraction(rows, "lock"),
        "vctrl_min": min(vctrl),
        "vctrl_max": max(vctrl),
        "vctrl_span": max(vctrl) - min(vctrl),
    }


def _code_from_bits(row: dict[str, float], prefix: str, width: int, threshold: float = 0.45) -> int | None:
    code = 0
    seen = False
    for bit in range(width):
        candidates = [f"{prefix}{bit}", f"{prefix}_{bit}"]
        signal = next((name for name in candidates if name in row), None)
        if signal is None:
            continue
        seen = True
        if row.get(signal, 0.0) > threshold:
            code |= 1 << bit
    return code if seen else None


def _adc_roundtrip_metrics(rows: list[dict[str, float]], *, width: int = 8) -> dict:
    if not rows:
        return {"metrics_error": "empty csv"}
    fields = set(rows[0])
    input_signal = "vin_sh" if "vin_sh" in fields else ("vin" if "vin" in fields else "")
    output_signal = "vout" if "vout" in fields else ("aout" if "aout" in fields else "")
    codes: list[int] = []
    errors: list[float] = []
    input_values: list[float] = []
    output_values: list[float] = []
    for row in rows:
        code = _code_from_bits(row, "dout", width)
        if code is not None:
            codes.append(code)
        if input_signal and output_signal and input_signal in row and output_signal in row:
            input_values.append(row[input_signal])
            output_values.append(row[output_signal])
            errors.append(abs(row[input_signal] - row[output_signal]))
    metrics: dict[str, float | int | str] = {}
    if codes:
        metrics["unique_codes"] = len(set(codes))
        metrics["min_code"] = min(codes)
        metrics["max_code"] = max(codes)
    if errors:
        metrics["input_signal"] = input_signal
        metrics["output_signal"] = output_signal
        metrics["avg_abs_error"] = sum(errors) / len(errors)
        metrics["max_abs_error"] = max(errors)
        metrics["input_span"] = max(input_values) - min(input_values)
        metrics["output_span"] = max(output_values) - min(output_values)
    if "clks" in fields or "clk" in fields:
        clock = "clks" if "clks" in fields else "clk"
        times = [row["time"] for row in rows if "time" in row]
        values = [row[clock] for row in rows if clock in row]
        metrics["clock_edges"] = len(rising_edges(values, times, threshold=0.45)) if len(times) == len(values) else 0
    return metrics


def _parse_note_metrics(notes: list[str]) -> dict:
    metrics: dict[str, float | str | bool] = {}
    for note in notes:
        for key, raw in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)=([^\s,;]+)", note):
            if raw == "True":
                metrics[key] = True
            elif raw == "False":
                metrics[key] = False
            else:
                try:
                    metrics[key] = float(raw)
                except ValueError:
                    metrics[key] = raw
    return metrics


def _format_value(value: object) -> str:
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return f"{value:.6g}"
    return str(value)


def _patch_instance_parameters(text: str, params: dict[str, object]) -> str:
    patched = text
    for name, value in params.items():
        replacement = f"{name}={_format_value(value)}"
        pattern = rf"\b{name}\s*=\s*[^\\\s]+"
        patched, count = re.subn(pattern, replacement, patched)
        if count == 0:
            raise ValueError(f"parameter not found in testbench: {name}")
    return patched


def _adpll_lock_cases() -> list[dict]:
    base = {
        "div_ratio": 8,
        "f_center": 760e6,
        "freq_step_hz": 5e6,
        "f_min": 500e6,
        "f_max": 1.2e9,
        "code_min": 0,
        "code_max": 63,
        "code_center": 32,
        "code_init": 40,
        "tedge": "1n",
        "lock_tol": "12n",
        "lock_count_target": 4,
    }

    def case(name: str, **updates: object) -> dict:
        params = dict(base)
        params.update(updates)
        return {"case_id": name, "params": params}

    return [
        case("base"),
        case("div_ratio_6", div_ratio=6),
        case("div_ratio_10", div_ratio=10),
        case("f_center_0p85", f_center=646e6),
        case("f_center_1p15", f_center=874e6),
        case("freq_step_2e6", freq_step_hz=2e6),
        case("freq_step_10e6", freq_step_hz=10e6),
        case("code_init_center", code_init=32),
        case("code_init_low", code_init=24),
        case("code_init_high", code_init=52),
        case("lock_tol_tight", lock_tol="4n"),
        case("lock_tol_loose", lock_tol="24n"),
        case("lock_count_2", lock_count_target=2),
        case("lock_count_8", lock_count_target=8),
        case("matched_div6_fcenter", div_ratio=6, f_center=560e6),
        case("matched_div10_fcenter", div_ratio=10, f_center=960e6),
    ]


def _sar_adc_roundtrip_cases() -> list[dict]:
    def case(name: str, **params: object) -> dict:
        return {"case_id": name, "params": params}

    return [
        case("fin_50k", fin=50e3),
        case("fin_100k_base", fin=100e3),
        case("fin_200k", fin=200e3),
        case("fin_500k", fin=500e3),
        case("fin_1m", fin=1.0e6),
    ]


def _write_markdown(out_path: Path, summary: dict) -> None:
    lines = [
        f"# Gold Mechanism Sweep: {summary['task_id']}",
        "",
        "## Summary",
        "",
        f"- Cases: `{len(summary['cases'])}`",
        f"- Passes: `{sum(1 for case in summary['cases'] if case['status'] == 'PASS')}`",
        "",
        "## Cases",
        "",
        "| Case | Status | late ratio | lock time | lock frac | vctrl span | note |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for case in summary["cases"]:
        m = case.get("metrics", {})
        note = "; ".join(str(item) for item in case.get("notes", [])[-2:])
        lines.append(
            "| {case_id} | {status} | {ratio} | {lock_time} | {lock_frac} | {vspan} | {note} |".format(
                case_id=case["case_id"],
                status=case["status"],
                ratio=_format_value(m.get("late_edge_ratio", m.get("late_edge_ratio_count", ""))),
                lock_time=_format_value(m.get("lock_time", "")),
                lock_frac=_format_value(m.get("lock_high_fraction", "")),
                vspan=_format_value(m.get("vctrl_span", "")),
                note=note.replace("|", "/"),
            )
        )

    lines.extend([
        "",
        "## Distilled Mechanism Notes",
        "",
        *[f"- {item}" for item in summary.get("distilled_notes", [])],
        "",
    ])
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _write_adc_markdown(out_path: Path, summary: dict) -> None:
    lines = [
        f"# Gold Mechanism Sweep: {summary['task_id']}",
        "",
        "## Summary",
        "",
        f"- Cases: `{len(summary['cases'])}`",
        f"- Passes: `{sum(1 for case in summary['cases'] if case['status'] == 'PASS')}`",
        "",
        "## Cases",
        "",
        "| Case | Status | unique codes | avg abs err | max abs err | input span | output span | note |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for case in summary["cases"]:
        m = case.get("metrics", {})
        note = "; ".join(str(item) for item in case.get("notes", [])[-2:])
        lines.append(
            "| {case_id} | {status} | {codes} | {avg_err} | {max_err} | {in_span} | {out_span} | {note} |".format(
                case_id=case["case_id"],
                status=case["status"],
                codes=_format_value(m.get("unique_codes", "")),
                avg_err=_format_value(m.get("avg_abs_error", "")),
                max_err=_format_value(m.get("max_abs_error", "")),
                in_span=_format_value(m.get("input_span", "")),
                out_span=_format_value(m.get("output_span", "")),
                note=note.replace("|", "/"),
            )
        )

    lines.extend([
        "",
        "## Distilled Mechanism Notes",
        "",
        *[f"- {item}" for item in summary.get("distilled_notes", [])],
        "",
    ])
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _distill_adpll_lock(cases: list[dict]) -> list[str]:
    notes = [
        "The gold ADPLL uses the public verifier parameters as the stable interface; parameter names are part of the executable contract.",
        "The feedback clock is derived from the DCO path, not from an independent reference-derived timer.",
        "The useful cadence relation is approximately `f_dco ~= 2 * div_ratio * f_ref` because `fb_clk` is a divided/toggled output and rising edges occur every full feedback period.",
        "Lock is based on repeated small ref/fb phase error observations, not just on the control code being near its center.",
        "A moving `vctrl_mon` is necessary evidence of loop activity, but it does not by itself imply lock.",
    ]
    passing = [case for case in cases if case.get("status") == "PASS"]
    if passing:
        fastest = min(
            passing,
            key=lambda case: case.get("metrics", {}).get("lock_time", float("inf"))
            if math.isfinite(case.get("metrics", {}).get("lock_time", float("nan")))
            else float("inf"),
        )
        notes.append(
            f"Fastest passing case in this sweep is `{fastest['case_id']}` with lock_time={_format_value(fastest['metrics'].get('lock_time'))}."
        )
    ratio_bad = [
        case for case in cases
        if case.get("metrics", {}).get("late_edge_ratio") is not None
        and isinstance(case["metrics"].get("late_edge_ratio"), float)
        and abs(case["metrics"]["late_edge_ratio"] - 1.0) > 0.05
    ]
    if ratio_bad:
        notes.append(
            "Perturbations that move the late edge ratio outside roughly `0.95..1.05` fail even when the waveform still has plenty of feedback edges."
        )
    return notes


def _distill_sar_adc_roundtrip(cases: list[dict]) -> list[str]:
    notes = [
        "Treat an ADC round trip as a chain: sample clock -> sampled input -> quantizer code -> DAC reconstruction -> optional ready/calibration evidence.",
        "A PASS case needs both enough code coverage and a small reconstruction error; seeing only a changing clock or only a changing output is not sufficient.",
        "The SAR ADC and DAC must agree on bit order, voltage reference, and threshold. A mismatch in any of those shows up as large reconstruction error even when the code bus toggles.",
        "Input frequency is a contract dimension: if the input moves too fast relative to the sample/update cadence, reconstruction can lag or lose code coverage.",
    ]
    passing = [case for case in cases if case.get("status") == "PASS"]
    failing = [case for case in cases if case.get("status") != "PASS"]
    if passing:
        worst_pass = max(passing, key=lambda case: case.get("params", {}).get("fin", 0.0))
        notes.append(
            f"Highest passing sine input in this sweep is `{worst_pass['case_id']}` at fin={_format_value(worst_pass['params'].get('fin'))}."
        )
    if failing:
        first_fail = min(failing, key=lambda case: case.get("params", {}).get("fin", float("inf")))
        notes.append(
            f"First failing sine input in this sweep is `{first_fail['case_id']}` at fin={_format_value(first_fail['params'].get('fin'))}; use its metrics as the speed/coverage warning boundary."
        )
    return notes


def run_adpll_lock(args: argparse.Namespace) -> dict:
    task_id = "adpll_lock_smoke"
    task_dir = _task_dir(task_id)
    gold_dir = task_dir / "gold"
    gold_dut = gold_dir / "adpll_va_idtmod.va"
    gold_tb = gold_dir / "tb_adpll_lock_ref.scs"
    if not gold_dut.exists() or not gold_tb.exists():
        raise SystemExit("missing adpll_lock_smoke gold files")

    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    tb_text = gold_tb.read_text(encoding="utf-8")

    results: list[dict] = []
    for entry in _adpll_lock_cases():
        case_id = entry["case_id"]
        params = entry["params"]
        case_dir = out_root / case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        dut_copy = case_dir / gold_dut.name
        tb_copy = case_dir / gold_tb.name
        shutil.copy2(gold_dut, dut_copy)
        tb_copy.write_text(_patch_instance_parameters(tb_text, params), encoding="utf-8")

        sim_out = case_dir / "evas"
        try:
            result = run_case(
                task_dir,
                dut_copy,
                tb_copy,
                output_root=sim_out,
                keep_run_dir=False,
                timeout_s=args.timeout_s,
                task_id_override=task_id,
            )
        except Exception as exc:
            result = {
                "status": "ERROR",
                "scores": {},
                "notes": [f"{type(exc).__name__}: {exc}"],
            }
        csv_path = sim_out / "tran.csv"
        metrics = {}
        if csv_path.exists():
            metrics.update(_edge_metrics(_read_csv(csv_path)))
        note_metrics = _parse_note_metrics(result.get("notes", []))
        metrics.update(note_metrics)

        case_result = {
            "case_id": case_id,
            "params": params,
            "status": result.get("status"),
            "scores": result.get("scores", {}),
            "notes": result.get("notes", []),
            "metrics": metrics,
            "artifacts": {
                "dut": str(dut_copy),
                "tb": str(tb_copy),
                "csv": str(csv_path),
                "case_dir": str(case_dir),
            },
        }
        (case_dir / "result.json").write_text(json.dumps(case_result, indent=2), encoding="utf-8")
        results.append(case_result)
        print(
            f"[{case_id}] {case_result['status']} "
            f"late_ratio={_format_value(metrics.get('late_edge_ratio', metrics.get('late_edge_ratio_count', '')))} "
            f"lock_time={_format_value(metrics.get('lock_time', ''))}"
        )

    summary = {
        "task_id": task_id,
        "out_root": str(out_root),
        "cases": results,
        "distilled_notes": _distill_adpll_lock(results),
    }
    (out_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_markdown(out_root / "summary.md", summary)
    return summary


def run_sar_adc_roundtrip(args: argparse.Namespace) -> dict:
    task_id = "sar_adc_dac_weighted_8b_smoke"
    task_dir = _task_dir(task_id)
    gold_dir = task_dir / "gold"
    gold_dut = gold_dir / "sar_adc_weighted_8b.va"
    gold_tb = gold_dir / "tb_sar_adc_dac_weighted_8b_ref.scs"
    if not gold_dut.exists() or not gold_tb.exists():
        raise SystemExit("missing sar_adc_dac_weighted_8b_smoke gold files")

    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    tb_text = gold_tb.read_text(encoding="utf-8")

    results: list[dict] = []
    for entry in _sar_adc_roundtrip_cases():
        case_id = entry["case_id"]
        params = entry["params"]
        case_dir = out_root / case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        case_json = case_dir / "result.json"
        if case_json.exists():
            case_result = json.loads(case_json.read_text(encoding="utf-8"))
            results.append(case_result)
            print(f"[{case_id}] {case_result['status']} cached")
            continue
        for src in gold_dir.iterdir():
            if src.is_file():
                shutil.copy2(src, case_dir / src.name)
        tb_copy = case_dir / gold_tb.name
        tb_copy.write_text(_patch_instance_parameters(tb_text, params), encoding="utf-8")
        dut_copy = case_dir / gold_dut.name

        sim_out = case_dir / "evas"
        try:
            result = run_case(
                task_dir,
                dut_copy,
                tb_copy,
                output_root=sim_out,
                keep_run_dir=False,
                timeout_s=args.timeout_s,
                task_id_override=task_id,
            )
        except Exception as exc:
            result = {
                "status": "ERROR",
                "scores": {},
                "notes": [f"{type(exc).__name__}: {exc}"],
            }
        csv_path = sim_out / "tran.csv"
        metrics = {}
        if csv_path.exists():
            metrics.update(_adc_roundtrip_metrics(_read_csv(csv_path), width=8))
        note_metrics = _parse_note_metrics(result.get("notes", []))
        metrics.update(note_metrics)

        case_result = {
            "case_id": case_id,
            "params": params,
            "status": result.get("status"),
            "scores": result.get("scores", {}),
            "notes": result.get("notes", []),
            "metrics": metrics,
            "artifacts": {
                "dut": str(dut_copy),
                "tb": str(tb_copy),
                "csv": str(csv_path),
                "case_dir": str(case_dir),
            },
        }
        (case_dir / "result.json").write_text(json.dumps(case_result, indent=2), encoding="utf-8")
        results.append(case_result)
        print(
            f"[{case_id}] {case_result['status']} "
            f"codes={_format_value(metrics.get('unique_codes', ''))} "
            f"avg_err={_format_value(metrics.get('avg_abs_error', ''))}"
        )

    summary = {
        "task_id": task_id,
        "out_root": str(out_root),
        "cases": results,
        "distilled_notes": _distill_sar_adc_roundtrip(results),
    }
    (out_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_adc_markdown(out_root / "summary.md", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default="adpll_lock_smoke", choices=["adpll_lock_smoke", "sar_adc_dac_weighted_8b_smoke"])
    parser.add_argument("--out-root", default="results/gold-mechanism-sweep-adpll-lock-2026-04-27")
    parser.add_argument("--timeout-s", type=int, default=90)
    args = parser.parse_args()

    if args.task == "adpll_lock_smoke":
        run_adpll_lock(args)
        return 0
    if args.task == "sar_adc_dac_weighted_8b_smoke":
        run_sar_adc_roundtrip(args)
        return 0
    raise SystemExit(f"unsupported task: {args.task}")


if __name__ == "__main__":
    raise SystemExit(main())
