#!/usr/bin/env python3
"""Cross-check vaEvas scored candidates with remote Cadence Spectre.

This runner intentionally reuses the normal `score.py` staging path so the
candidate being sent to Spectre is the same contract-pruned artifact that EVAS
scores.  It then converts Spectre PSF-ASCII data to `tran.csv` and runs the
same behavior checkers used by EVAS scoring.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import os
import re
import shutil
import sys
from pathlib import Path

from score import (
    _normalized_required_axes,
    _task_pass,
    ahdl_includes,
    all_save_signals,
    build_model_results,
    choose_gold_tb,
    find_generated_dir,
    find_tb_file,
    find_va_file,
    list_all_task_dirs,
    read_meta,
    spectre_strict_preflight,
    stage_candidate_case,
)
from simulate_evas import evaluate_behavior_with_timeout


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_SRC = Path("/Users/bucketsran/Documents/TsingProject/iccad/virtuoso-bridge-lite-ci/src")
DEFAULT_ENV = Path("/Users/bucketsran/Documents/TsingProject/iccad/virtuoso-bridge-lite-ci/.env")


def _load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _import_bridge():
    if str(BRIDGE_SRC) not in sys.path:
        sys.path.insert(0, str(BRIDGE_SRC))
    from virtuoso_bridge.spectre.runner import SpectreSimulator, spectre_mode_args

    return SpectreSimulator, spectre_mode_args


def _copy_flat_spectre_input(staged_dir: Path, staged_tb: Path, input_dir: Path) -> Path:
    """Create a flat Spectre input dir compatible with bridge uploads."""
    if input_dir.exists():
        shutil.rmtree(input_dir)
    input_dir.mkdir(parents=True)

    for src in staged_dir.rglob("*"):
        if not src.is_file() or "_candidate_original" in src.parts:
            continue
        dst = input_dir / src.name
        if src.resolve() == staged_tb.resolve():
            continue
        if dst.exists():
            # Keep first file on basename collision; staged benchmark inputs are
            # expected to be unique for Spectre includes.
            continue
        shutil.copy2(src, dst)

    tb_dst = input_dir / staged_tb.name
    text = staged_tb.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(
        r'(^\s*ahdl_include\s+")([^"]+)(")',
        lambda m: f"{m.group(1)}{Path(m.group(2)).name}{m.group(3)}",
        text,
        flags=re.MULTILINE,
    )
    tb_dst.write_text(text, encoding="utf-8")
    return tb_dst


def _include_files_for(netlist: Path) -> list[Path]:
    include_names = ahdl_includes(netlist)
    files: list[Path] = []
    for name in include_names:
        path = netlist.parent / Path(name).name
        if path.exists():
            files.append(path)
    # Upload any extra flat VA/SCS support files as well; Spectre will ignore
    # files that are not included, while this prevents missing secondary AHDL.
    for path in sorted(netlist.parent.glob("*")):
        if path == netlist or not path.is_file():
            continue
        if path.suffix.lower() in {".va", ".scs", ".csv", ".txt"} and path not in files:
            files.append(path)
    return files


def _write_spectre_csv(data: dict, csv_path: Path) -> tuple[bool, str]:
    if not data or "time" not in data:
        return False, "spectre_data_missing_time"
    keys = [key for key, value in data.items() if isinstance(value, list)]
    if "time" not in keys:
        keys.insert(0, "time")
    else:
        keys = ["time"] + [key for key in keys if key != "time"]
    lengths = [len(data.get(key, [])) for key in keys]
    n_rows = min(lengths) if lengths else 0
    if n_rows <= 0:
        return False, "spectre_data_empty"

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for idx in range(n_rows):
            writer.writerow({key: data[key][idx] for key in keys})
    return True, f"spectre_csv_rows={n_rows} cols={len(keys)}"


def _stage_task(
    *,
    task_id: str,
    task_dir: Path,
    sample_dir: Path,
    stage_dir: Path,
    save_policy: str,
) -> tuple[dict | None, Path | None, Path | None, list[str]]:
    meta = read_meta(task_dir)
    family = meta.get("family", "end-to-end")
    required_axes: list[str] = meta.get("scoring", ["dut_compile", "tb_compile", "sim_correct"])
    gold_dir = task_dir / "gold"

    gen_meta_path = sample_dir / "generation_meta.json"
    gen_meta: dict = {}
    if gen_meta_path.exists():
        try:
            gen_meta = json.loads(gen_meta_path.read_text(encoding="utf-8"))
        except Exception:
            gen_meta = {}
    if gen_meta.get("dry_run") or gen_meta.get("status") == "dry_run":
        return None, None, None, ["dry_run_generation"]
    placeholder_files = sorted(
        p.name
        for p in sample_dir.glob("*placeholder*")
        if p.is_file() and p.suffix.lower() in {".va", ".scs"}
    )
    if placeholder_files:
        return None, None, None, [f"placeholder_artifacts={','.join(placeholder_files[:4])}"]

    generated_va = find_va_file(sample_dir)
    generated_tb = find_tb_file(sample_dir)
    gold_tb = choose_gold_tb(gold_dir)
    auxiliary_gold_vas: list[Path] = []
    contract_save_signals = all_save_signals(gold_tb) if gold_tb and gold_tb.exists() else None

    if family in ("spec-to-va", "bugfix"):
        dut_path = generated_va
        tb_path = gold_tb
    elif family == "tb-generation":
        gold_vas = sorted(gold_dir.glob("*.va"))
        dut_path = gold_vas[0] if gold_vas else None
        tb_path = generated_tb
        auxiliary_gold_vas = gold_vas
    else:
        dut_path = generated_va
        tb_path = generated_tb

    missing = []
    if dut_path is None or not dut_path.exists():
        missing.append("dut.va")
    if tb_path is None or not tb_path.exists():
        missing.append("testbench.scs")
    if missing:
        return None, None, None, [f"missing_generated_files={','.join(missing)}"]

    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True)
    dut, tb, notes = stage_candidate_case(
        family=family,
        gold_dir=gold_dir,
        sample_dir=sample_dir,
        dut_path=dut_path,
        tb_path=tb_path,
        stage_dir=stage_dir,
        auxiliary_gold_vas=auxiliary_gold_vas,
        save_policy=save_policy,
        required_axes=required_axes,
        contract_save_signals=contract_save_signals,
    )
    return meta, dut, tb, notes


def _scores_from_spectre(
    *,
    task_id: str,
    required_axes: list[str],
    returncode: int | None,
    csv_path: Path | None,
    timeout_s: int,
) -> tuple[str, dict[str, float], list[str]]:
    notes: list[str] = []
    if returncode != 0:
        scores = {"dut_compile": 0.0, "tb_compile": 0.0, "sim_correct": 0.0}
        status = "FAIL_SPECTRE_RUN"
    else:
        scores = {"dut_compile": 1.0, "tb_compile": 1.0, "sim_correct": 1.0}
        status = "PASS"
        if "sim_correct" in _normalized_required_axes(required_axes):
            if csv_path and csv_path.exists():
                sim_correct, behavior_notes = evaluate_behavior_with_timeout(
                    task_id,
                    csv_path,
                    timeout_s=timeout_s,
                )
                scores["sim_correct"] = sim_correct
                notes.extend(behavior_notes)
                if sim_correct < 1.0:
                    status = "FAIL_SIM_CORRECTNESS"
            else:
                scores["sim_correct"] = 0.0
                notes.append("spectre_tran_csv_missing")
                status = "FAIL_SIM_CORRECTNESS"

    required = _normalized_required_axes(required_axes)
    axes = [axis for axis in required if axis in {"dut_compile", "tb_compile", "sim_correct"}]
    if not axes:
        axes = ["dut_compile", "tb_compile", "sim_correct"]
    scores["weighted_total"] = round(sum(scores.get(axis, 0.0) for axis in axes) / len(axes), 4)
    return status, scores, notes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="kimi-k2.5")
    ap.add_argument("--generated-dir", default="generated-clean-A-promptonly-kimi-2026-04-27-r3-genericprompt")
    ap.add_argument("--evas-results-dir", default="results/clean-A-r3-spectre-strict-v3-full92-2026-04-28")
    ap.add_argument("--output-dir", default="results/baselineA-spectre-validation-v3-full92-2026-04-28")
    ap.add_argument("--env", default=str(DEFAULT_ENV))
    ap.add_argument("--profile", default="ci")
    ap.add_argument("--task", action="append", default=[])
    ap.add_argument("--family", action="append", default=[])
    ap.add_argument("--sample-idx", type=int, default=0)
    ap.add_argument("--timeout-s", type=int, default=180)
    ap.add_argument(
        "--spectre-mode",
        choices=["spectre", "aps", "x", "cx", "ax", "mx", "lx", "vx"],
        default="spectre",
        help=(
            "Remote Spectre mode. Use 'spectre' for strict final validation that "
            "preserves netlist tran options such as maxstep; Spectre X presets "
            "such as 'ax' may override those options."
        ),
    )
    ap.add_argument("--save-policy", choices=["contract", "debug"], default="contract")
    ap.add_argument("--keep-remote-files", action="store_true")
    args = ap.parse_args()

    _load_env(Path(args.env))
    SpectreSimulator, spectre_mode_args = _import_bridge()

    generated_root = Path(args.generated_dir)
    if not generated_root.is_absolute():
        generated_root = ROOT / generated_root
    evas_root = Path(args.evas_results_dir)
    if not evas_root.is_absolute():
        evas_root = ROOT / evas_root
    out_root = Path(args.output_dir)
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    out_root.mkdir(parents=True, exist_ok=True)

    selected = set(args.task) if args.task else None
    families = tuple(args.family) if args.family else ("end-to-end", "spec-to-va", "bugfix", "tb-generation")
    task_list = list_all_task_dirs(families=families, selected=selected)
    if not task_list:
        print("[spectre-validate] no tasks selected")
        return 1

    sim = SpectreSimulator(
        spectre_args=spectre_mode_args(args.spectre_mode),
        timeout=args.timeout_s,
        work_dir=out_root / "_spectre_runs",
        output_format="psfascii",
        keep_remote_files=args.keep_remote_files,
        remote=True,
        profile=args.profile,
    )

    results: list[dict] = []
    model_slug = args.model.replace("/", "_")
    for index, (task_id, task_dir) in enumerate(task_list, start=1):
        print(f"[spectre-validate] {index}/{len(task_list)} {task_id}", flush=True)
        sample_dir = find_generated_dir(generated_root, model_slug, task_id, args.sample_idx)
        evas_result_path = evas_root / task_id / "result.json"
        evas_result = json.loads(evas_result_path.read_text(encoding="utf-8")) if evas_result_path.exists() else {}
        meta = read_meta(task_dir)
        required_axes: list[str] = meta.get("scoring", ["dut_compile", "tb_compile", "sim_correct"])

        case_out = out_root / task_id
        stage_dir = case_out / "staged"
        case_out.mkdir(parents=True, exist_ok=True)
        result: dict = {
            "task_id": task_id,
            "family": meta.get("family", "unknown"),
            "required_axes": required_axes,
            "evas_status": evas_result.get("status"),
            "evas_scores": evas_result.get("scores", {}),
            "evas_pass": _task_pass(evas_result) if evas_result else None,
            "spectre_mode": args.spectre_mode,
        }

        if sample_dir is None:
            result.update(
                {
                    "spectre_status": "NOT_RUN",
                    "spectre_scores": {"dut_compile": 0.0, "tb_compile": 0.0, "sim_correct": 0.0, "weighted_total": 0.0},
                    "spectre_notes": ["missing_generated_sample"],
                }
            )
            (case_out / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
            results.append(result)
            continue

        staged_meta, _staged_dut, staged_tb, staging_notes = _stage_task(
            task_id=task_id,
            task_dir=task_dir,
            sample_dir=sample_dir,
            stage_dir=stage_dir,
            save_policy=args.save_policy,
        )
        if staged_meta is None or staged_tb is None:
            result.update(
                {
                    "spectre_status": "NOT_RUN",
                    "spectre_scores": {"dut_compile": 0.0, "tb_compile": 0.0, "sim_correct": 0.0, "weighted_total": 0.0},
                    "spectre_notes": staging_notes,
                }
            )
            result["spectre_pass"] = False
            result["pass_match"] = result["evas_pass"] == result["spectre_pass"]
            (case_out / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
            results.append(result)
            continue

        strict_status, strict_scores, strict_notes = spectre_strict_preflight(
            family=meta.get("family", "unknown"),
            required_axes=required_axes,
            staged_tb=staged_tb,
            staged_va_paths=sorted(stage_dir.rglob("*.va")),
        )

        input_dir = case_out / "spectre_input"
        netlist = _copy_flat_spectre_input(stage_dir, staged_tb, input_dir)
        include_files = _include_files_for(netlist)
        spectre_dir = case_out / "spectre"
        if spectre_dir.exists():
            shutil.rmtree(spectre_dir)
        spectre_dir.mkdir(parents=True)
        sim._work_dir = spectre_dir  # per-task local raw/log isolation

        run_notes = list(staging_notes) + list(strict_notes)
        try:
            bridge_console = io.StringIO()
            with contextlib.redirect_stdout(bridge_console), contextlib.redirect_stderr(bridge_console):
                spectre_result = sim.run_simulation(netlist, {"include_files": include_files})
            (case_out / "bridge_console.log").write_text(bridge_console.getvalue(), encoding="utf-8")
            returncode = spectre_result.metadata.get("returncode")
            data = spectre_result.data or {}
            csv_path = case_out / "tran.csv"
            csv_ok, csv_note = _write_spectre_csv(data, csv_path)
            run_notes.append(csv_note)
            if not csv_ok:
                csv_path = None
            status, scores, behavior_notes = _scores_from_spectre(
                task_id=task_id,
                required_axes=required_axes,
                returncode=returncode,
                csv_path=csv_path,
                timeout_s=args.timeout_s,
            )
            run_notes.extend(behavior_notes)
            spectre_command = spectre_result.metadata.get("spectre_command", "")
            remote_match = re.search(r"(/tmp/virtuoso_bridge_[^/]+/virtuoso_bridge_spectre/[0-9a-f]+)/", spectre_command)
            result.update(
                {
                    "spectre_status": status,
                    "spectre_scores": scores,
                    "spectre_returncode": returncode,
                    "spectre_execution_status": getattr(spectre_result.status, "value", str(spectre_result.status)),
                    "spectre_errors": spectre_result.errors,
                    "spectre_warnings": spectre_result.warnings[:20],
                    "spectre_output_dir": spectre_result.metadata.get("output_dir"),
                    "spectre_log": str(spectre_dir / "spectre.out"),
                    "spectre_remote_dir": remote_match.group(1) + "/" if remote_match else None,
                    "spectre_command": spectre_command,
                    "spectre_mode": args.spectre_mode,
                    "strict_preflight_status": strict_status,
                    "strict_preflight_scores": strict_scores,
                    "spectre_notes": run_notes,
                }
            )
        except Exception as exc:  # noqa: BLE001 - boundary around remote EDA invocation
            result.update(
                {
                    "spectre_status": "FAIL_INFRA",
                    "spectre_scores": {"dut_compile": 0.0, "tb_compile": 0.0, "sim_correct": 0.0, "weighted_total": 0.0},
                    "spectre_exception": f"{type(exc).__name__}: {exc}",
                    "strict_preflight_status": strict_status,
                    "strict_preflight_scores": strict_scores,
                    "spectre_notes": run_notes,
                }
            )

        result["spectre_pass"] = all(
            result.get("spectre_scores", {}).get(axis, 0.0) >= 1.0
            for axis in _normalized_required_axes(required_axes)
        )
        result["pass_match"] = result["evas_pass"] == result["spectre_pass"]
        result["status_match"] = result.get("evas_status") == result.get("spectre_status")
        (case_out / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        results.append(result)

    aggregate = build_model_results(args.model, [
        {
            "task_id": r["task_id"],
            "family": r.get("family", "unknown"),
            "required_axes": r.get("required_axes", []),
            "scores": r.get("spectre_scores", {}),
            "status": r.get("spectre_status", "FAIL_INFRA"),
        }
        for r in results
    ], 0.0, 1.0)
    comparisons = {
        "total_tasks": len(results),
        "spectre_mode": args.spectre_mode,
        "pass_match_count": sum(1 for r in results if r.get("pass_match")),
        "pass_mismatches": [
            {
                "task_id": r["task_id"],
                "family": r.get("family"),
                "evas_status": r.get("evas_status"),
                "evas_pass": r.get("evas_pass"),
                "spectre_status": r.get("spectre_status"),
                "spectre_pass": r.get("spectre_pass"),
                "spectre_returncode": r.get("spectre_returncode"),
                "spectre_notes": r.get("spectre_notes", [])[-5:],
            }
            for r in results
            if not r.get("pass_match")
        ],
        "spectre_aggregate": aggregate,
    }
    (out_root / "spectre_model_results.json").write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
    (out_root / "comparison.json").write_text(json.dumps(comparisons, indent=2), encoding="utf-8")
    print(
        f"[spectre-validate] Spectre Pass@1={aggregate['pass_count']}/{aggregate['total_tasks']} "
        f"({aggregate['pass_at_1']:.4f}); pass matches={comparisons['pass_match_count']}/{len(results)}"
    )
    if comparisons["pass_mismatches"]:
        print("[spectre-validate] mismatches:")
        for item in comparisons["pass_mismatches"]:
            print(
                f"  - {item['task_id']}: EVAS {item['evas_status']} pass={item['evas_pass']} "
                f"vs Spectre {item['spectre_status']} pass={item['spectre_pass']}"
            )
    print(f"[spectre-validate] wrote {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
