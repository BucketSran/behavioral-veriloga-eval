#!/usr/bin/env python3
"""Run overfitting-risk experiments for the current contract/mechanism closure.

This runner covers the first five experiments requested for the 2026-04-27
overfit-risk plan:

0. source audit;
1. mechanism-only replay without copying local PASS overlay artifacts;
2. no-leakage admission ablation;
3. family hold-out admission ablation;
4. cross-model mechanism replay on Qwen.

It intentionally does not call model APIs.  The mechanism-only replay uses the
current deterministic mechanism patch generators as a stricter alternative to
copying scattered PASS artifacts.  The admission ablations only operate on the
existing I-runner overlay manifest and always re-score the resulting full92 tree.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]

KIMI = "kimi-k2.5"
QWEN = "qwen3-max-2026-01-23"

H_BASE_GENERATED = "generated-condition-H-on-F-kimi-2026-04-26"
H_BASE_SCORE = "results/current-experiment-regression-2026-04-27/H-on-F-kimi"
F_QWEN_GENERATED = "generated-table2-evas-guided-repair-3round"
F_QWEN_SCORE = "results/current-experiment-regression-2026-04-27/F-qwen"
I_OVERLAY_MANIFEST = "generated-latest-contract-combined-full92-runner-2026-04-27/overlay_manifest.json"
I_RUNNER_SCORE = "results/current-experiment-regression-2026-04-27/I-contract-runner-kimi"
I_R26_SCORE = "results/current-experiment-regression-2026-04-27/I-r26-final-kimi"

PLL_TASKS = [
    "adpll_lock_smoke",
    "adpll_timer_smoke",
    "adpll_ratio_hop_smoke",
    "cppll_timer",
    "cppll_tracking_smoke",
    "cppll_freq_step_reacquire_smoke",
]

REMAINING_MECHANISM_TASKS = [
    "bad_bus_output_loop",
    "timer_absolute_grid_smoke",
    "multimod_divider_ratio_switch_smoke",
    "flash_adc_3b_smoke",
    "multitone",
    "nrz_prbs",
    "bg_cal",
    "cross_sine_precision_smoke",
    "dwa_ptr_gen_smoke",
    "dwa_ptr_gen_no_overlap_smoke",
    "dwa_wraparound_smoke",
    "pfd_reset_race_smoke",
]

HOLDOUT_GROUPS: dict[str, set[str]] = {
    "converter_chain": {
        "adc_dac_ideal_4b_smoke",
        "cdac_cal",
        "dac_therm_16b_smoke",
        "segmented_dac",
    },
    "digital_sequence": {
        "digital_basics_smoke",
        "gray_counter_one_bit_change_smoke",
        "parameter_type_override_smoke",
        "serializer_frame_alignment_smoke",
    },
    "pulse_protocol": {
        "bbpd_data_edge_alignment_smoke",
    },
}


@dataclass
class RunResult:
    label: str
    output_dir: str
    pass_count: int | None
    total_tasks: int | None
    pass_at_1: float | None
    elapsed_s: float
    returncode: int
    extra: dict[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _run(cmd: list[str], *, log_path: Path, cwd: Path = ROOT) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as handle:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    return int(proc.returncode)


def _score(
    *,
    model: str,
    generated_dir: str,
    output_dir: str,
    timeout_s: int,
    workers: int,
    log_root: Path,
    tasks: list[str] | None = None,
) -> RunResult:
    start = time.time()
    cmd = [
        sys.executable,
        "runners/score.py",
        "--model",
        model,
        "--generated-dir",
        generated_dir,
        "--output-dir",
        output_dir,
        "--timeout-s",
        str(timeout_s),
        "--workers",
        str(workers),
        "--save-policy",
        "contract",
    ]
    for task_id in tasks or []:
        cmd.extend(["--task", task_id])
    rc = _run(cmd, log_path=log_root / f"score-{Path(output_dir).name}.log")
    agg = _read_json(ROOT / output_dir / "model_results.json")
    return RunResult(
        label=Path(output_dir).name,
        output_dir=output_dir,
        pass_count=agg.get("pass_count"),
        total_tasks=agg.get("total_tasks"),
        pass_at_1=agg.get("pass_at_1"),
        elapsed_s=round(time.time() - start, 3),
        returncode=rc,
        extra={
            "by_family": agg.get("by_family", {}),
            "failure_domain_taxonomy": agg.get("failure_domain_taxonomy", {}),
        },
    )


def _status_map(score_root: str) -> dict[str, str]:
    root = ROOT / score_root
    return {
        path.parent.name: str(_read_json(path).get("status", "UNKNOWN"))
        for path in root.glob("*/result.json")
    }


def _copy_tree(src: Path, dst: Path, *, overwrite: bool) -> None:
    if dst.exists():
        if not overwrite:
            raise SystemExit(f"Output exists, pass --overwrite: {dst}")
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _overlay_replacements() -> list[dict[str, Any]]:
    manifest = _read_json(ROOT / I_OVERLAY_MANIFEST)
    return list(manifest.get("replacements", []))


def _sample_file_names(sample_dir: Path) -> list[str]:
    if not sample_dir.exists():
        return []
    return sorted(path.name for path in sample_dir.iterdir() if path.is_file())


def _replacement_leak_flags(replacement: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    notes = " ".join(str(note) for note in replacement.get("candidate_notes", [])).lower()
    if "ref_alias" in notes:
        flags.append("ref_alias_note")
    if "_ref.va" in notes or "_ref.scs" in notes:
        flags.append("ref_file_note")
    sample_dir = Path(str(replacement.get("sample_dir", "")))
    for name in _sample_file_names(sample_dir):
        lower = name.lower()
        if lower.endswith("_ref.va") or lower.endswith("_ref.scs"):
            flags.append(f"ref_named_file:{name}")
    return sorted(set(flags))


def _materialize_overlay_subset(
    *,
    out_generated: str,
    predicate: Callable[[dict[str, Any]], bool],
    reason: str,
    overwrite: bool,
) -> dict[str, Any]:
    base = ROOT / H_BASE_GENERATED
    out = ROOT / out_generated
    _copy_tree(base, out, overwrite=overwrite)

    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for replacement in _overlay_replacements():
        task_id = str(replacement.get("task_id"))
        if not predicate(replacement):
            excluded.append(
                {
                    "task_id": task_id,
                    "score_root": replacement.get("score_root"),
                    "leak_flags": _replacement_leak_flags(replacement),
                }
            )
            continue
        src = Path(str(replacement.get("sample_dir")))
        dst = out / KIMI / task_id / "sample_0"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        included.append(
            {
                "task_id": task_id,
                "score_root": replacement.get("score_root"),
                "leak_flags": _replacement_leak_flags(replacement),
            }
        )

    manifest = {
        "mode": "overfit_guard_overlay_subset",
        "base_generated": H_BASE_GENERATED,
        "source_overlay_manifest": I_OVERLAY_MANIFEST,
        "out_generated": out_generated,
        "reason": reason,
        "included_count": len(included),
        "excluded_count": len(excluded),
        "included": included,
        "excluded": excluded,
    }
    _write_json(out / "overfit_guard_subset_manifest.json", manifest)
    return manifest


def _generate_mechanism_patches(
    *,
    model: str,
    pll_out: str,
    remaining_out: str,
    log_root: Path,
) -> None:
    pll_cmd = [
        sys.executable,
        "runners/pll_graph_patch_repair.py",
        "--out-root",
        pll_out,
        "--model",
        model,
    ]
    for task_id in PLL_TASKS:
        pll_cmd.extend(["--task", task_id])
    rc = _run(pll_cmd, log_path=log_root / f"generate-pll-{model}.log")
    if rc:
        raise SystemExit(f"PLL patch generator failed for {model}: rc={rc}")

    remaining_cmd = [
        sys.executable,
        "runners/remaining_mechanism_patch_repair.py",
        "--out-root",
        remaining_out,
        "--model",
        model,
    ]
    for task_id in REMAINING_MECHANISM_TASKS:
        remaining_cmd.extend(["--task", task_id])
    rc = _run(remaining_cmd, log_path=log_root / f"generate-remaining-{model}.log")
    if rc:
        raise SystemExit(f"Remaining mechanism patch generator failed for {model}: rc={rc}")


def _materialize_candidates(
    *,
    base_generated: str,
    base_score: str,
    out_generated: str,
    model_slug: str,
    candidate_scores: list[str],
    report_out: str,
    overwrite: bool,
    log_root: Path,
) -> dict[str, Any]:
    cmd = [
        sys.executable,
        "runners/materialize_combined_artifacts.py",
        "--base-generated",
        base_generated,
        "--base-score",
        base_score,
        "--out-generated",
        out_generated,
        "--model-slug",
        model_slug,
        "--report-out",
        report_out,
    ]
    for root in candidate_scores:
        cmd.extend(["--candidate-score", root])
    if overwrite:
        cmd.append("--overwrite")
    rc = _run(cmd, log_path=log_root / f"materialize-{Path(out_generated).name}.log")
    if rc:
        raise SystemExit(f"materialization failed for {out_generated}: rc={rc}")
    return _read_json(ROOT / out_generated / "overlay_manifest.json")


def experiment0_source_audit(out_root: Path) -> dict[str, Any]:
    h = _status_map(H_BASE_SCORE)
    i_runner = _status_map(I_RUNNER_SCORE)
    r26 = _status_map(I_R26_SCORE)
    replacements = {str(row["task_id"]): row for row in _overlay_replacements()}
    tasks = sorted(set(r26) | set(i_runner) | set(h))
    rows = []
    counts: dict[str, int] = {}
    for task_id in tasks:
        if h.get(task_id) == "PASS":
            source = "H_on_F_base_pass"
        elif task_id in replacements and i_runner.get(task_id) == "PASS":
            source = "I_runner_local_overlay"
        elif r26.get(task_id) == "PASS":
            source = "R26_mechanism_or_checker_closure"
        else:
            source = "nonpass_or_unknown"
        counts[source] = counts.get(source, 0) + 1
        repl = replacements.get(task_id, {})
        rows.append(
            {
                "task_id": task_id,
                "h_status": h.get(task_id),
                "i_runner_status": i_runner.get(task_id),
                "r26_status": r26.get(task_id),
                "source": source,
                "overlay_score_root": repl.get("score_root", ""),
                "overlay_leak_flags": _replacement_leak_flags(repl) if repl else [],
            }
        )
    payload = {
        "mode": "source_audit",
        "counts": counts,
        "tasks": rows,
    }
    _write_json(out_root / "exp0_source_audit.json", payload)
    return payload


def experiment1_mechanism_only_kimi(
    *,
    out_root: Path,
    generated_prefix: str,
    timeout_s: int,
    workers: int,
    overwrite: bool,
) -> RunResult:
    log_root = out_root / "logs"
    pll_generated = f"{generated_prefix}-mechanism-only-kimi-pll"
    rem_generated = f"{generated_prefix}-mechanism-only-kimi-remaining"
    _generate_mechanism_patches(
        model=KIMI,
        pll_out=pll_generated,
        remaining_out=rem_generated,
        log_root=log_root,
    )
    pll_score = f"{out_root.relative_to(ROOT)}/exp1-kimi-pll-score"
    rem_score = f"{out_root.relative_to(ROOT)}/exp1-kimi-remaining-score"
    _score(
        model=KIMI,
        generated_dir=pll_generated,
        output_dir=pll_score,
        timeout_s=timeout_s,
        workers=workers,
        log_root=log_root,
        tasks=PLL_TASKS,
    )
    _score(
        model=KIMI,
        generated_dir=rem_generated,
        output_dir=rem_score,
        timeout_s=timeout_s,
        workers=workers,
        log_root=log_root,
        tasks=REMAINING_MECHANISM_TASKS,
    )
    combined_generated = f"{generated_prefix}-mechanism-only-kimi-combined"
    _materialize_candidates(
        base_generated=H_BASE_GENERATED,
        base_score=H_BASE_SCORE,
        out_generated=combined_generated,
        model_slug=KIMI,
        candidate_scores=[pll_score, rem_score],
        report_out=f"{out_root.relative_to(ROOT)}/exp1_mechanism_only_kimi_materialization.md",
        overwrite=overwrite,
        log_root=log_root,
    )
    return _score(
        model=KIMI,
        generated_dir=combined_generated,
        output_dir=f"{out_root.relative_to(ROOT)}/exp1-mechanism-only-kimi-full92",
        timeout_s=timeout_s,
        workers=workers,
        log_root=log_root,
    )


def experiment2_no_leakage_admission(
    *,
    out_root: Path,
    generated_prefix: str,
    timeout_s: int,
    workers: int,
    overwrite: bool,
) -> RunResult:
    log_root = out_root / "logs"
    generated = f"{generated_prefix}-no-leakage-admission-kimi"
    manifest = _materialize_overlay_subset(
        out_generated=generated,
        predicate=lambda row: not _replacement_leak_flags(row),
        reason="include only I-runner overlay replacements without strict ref-alias/ref-named-file flags",
        overwrite=overwrite,
    )
    result = _score(
        model=KIMI,
        generated_dir=generated,
        output_dir=f"{out_root.relative_to(ROOT)}/exp2-no-leakage-admission-kimi-full92",
        timeout_s=timeout_s,
        workers=workers,
        log_root=log_root,
    )
    result.extra["subset_manifest"] = manifest
    return result


def experiment3_family_holdout(
    *,
    out_root: Path,
    generated_prefix: str,
    timeout_s: int,
    workers: int,
    overwrite: bool,
) -> list[RunResult]:
    log_root = out_root / "logs"
    results: list[RunResult] = []
    for group, held_out in HOLDOUT_GROUPS.items():
        generated = f"{generated_prefix}-holdout-{group}-kimi"
        manifest = _materialize_overlay_subset(
            out_generated=generated,
            predicate=lambda row, held_out=held_out: str(row.get("task_id")) not in held_out,
            reason=f"exclude overlay replacements from held-out family {group}",
            overwrite=overwrite,
        )
        result = _score(
            model=KIMI,
            generated_dir=generated,
            output_dir=f"{out_root.relative_to(ROOT)}/exp3-holdout-{group}-kimi-full92",
            timeout_s=timeout_s,
            workers=workers,
            log_root=log_root,
        )
        result.extra["subset_manifest"] = manifest
        results.append(result)
    return results


def experiment4_cross_model_qwen(
    *,
    out_root: Path,
    generated_prefix: str,
    timeout_s: int,
    workers: int,
    overwrite: bool,
) -> RunResult:
    log_root = out_root / "logs"
    pll_generated = f"{generated_prefix}-mechanism-only-qwen-pll"
    rem_generated = f"{generated_prefix}-mechanism-only-qwen-remaining"
    _generate_mechanism_patches(
        model=QWEN,
        pll_out=pll_generated,
        remaining_out=rem_generated,
        log_root=log_root,
    )
    pll_score = f"{out_root.relative_to(ROOT)}/exp4-qwen-pll-score"
    rem_score = f"{out_root.relative_to(ROOT)}/exp4-qwen-remaining-score"
    _score(
        model=QWEN,
        generated_dir=pll_generated,
        output_dir=pll_score,
        timeout_s=timeout_s,
        workers=workers,
        log_root=log_root,
        tasks=PLL_TASKS,
    )
    _score(
        model=QWEN,
        generated_dir=rem_generated,
        output_dir=rem_score,
        timeout_s=timeout_s,
        workers=workers,
        log_root=log_root,
        tasks=REMAINING_MECHANISM_TASKS,
    )
    combined_generated = f"{generated_prefix}-mechanism-only-qwen-combined"
    _materialize_candidates(
        base_generated=F_QWEN_GENERATED,
        base_score=F_QWEN_SCORE,
        out_generated=combined_generated,
        model_slug=QWEN,
        candidate_scores=[pll_score, rem_score],
        report_out=f"{out_root.relative_to(ROOT)}/exp4_mechanism_only_qwen_materialization.md",
        overwrite=overwrite,
        log_root=log_root,
    )
    return _score(
        model=QWEN,
        generated_dir=combined_generated,
        output_dir=f"{out_root.relative_to(ROOT)}/exp4-mechanism-only-qwen-full92",
        timeout_s=timeout_s,
        workers=workers,
        log_root=log_root,
    )


def _run_result_dict(result: RunResult) -> dict[str, Any]:
    return {
        "label": result.label,
        "output_dir": result.output_dir,
        "pass_count": result.pass_count,
        "total_tasks": result.total_tasks,
        "pass_at_1": result.pass_at_1,
        "elapsed_s": result.elapsed_s,
        "returncode": result.returncode,
        **result.extra,
    }


def _write_summary(out_root: Path, payload: dict[str, Any]) -> None:
    _write_json(out_root / "summary.json", payload)
    lines = [
        "# Overfit Guard Experiments 0-4",
        "",
        "This report audits the current I/R26 closure and runs no-API replay/ablation experiments.",
        "",
        "## KPI",
        "",
        "- Separate artifact admission gains from mechanism-only replay gains.",
        "- Quantify no-leakage strict admission impact.",
        "- Quantify family-holdout dependence of the local overlay gains.",
        "- Test deterministic mechanisms on Qwen without reusing Kimi artifacts.",
        "",
        "## Experiment 0: Source Audit",
        "",
        f"- Source counts: `{json.dumps(payload.get('exp0_source_audit', {}).get('counts', {}), sort_keys=True)}`",
        "",
        "## Score Results",
        "",
        "| Experiment | Pass | Pass@1 | Output | Notes |",
        "|---|---:|---:|---|---|",
    ]
    for key in ["exp1_mechanism_only_kimi", "exp2_no_leakage_admission"]:
        row = payload.get(key, {})
        lines.append(
            f"| {key} | {row.get('pass_count')}/{row.get('total_tasks')} | "
            f"{row.get('pass_at_1')} | `{row.get('output_dir')}` |  |"
        )
    for row in payload.get("exp3_family_holdout", []):
        manifest = row.get("subset_manifest", {})
        lines.append(
            f"| exp3_{row.get('label')} | {row.get('pass_count')}/{row.get('total_tasks')} | "
            f"{row.get('pass_at_1')} | `{row.get('output_dir')}` | "
            f"included={manifest.get('included_count')} excluded={manifest.get('excluded_count')} |"
        )
    row = payload.get("exp4_cross_model_qwen", {})
    lines.append(
        f"| exp4_cross_model_qwen | {row.get('pass_count')}/{row.get('total_tasks')} | "
        f"{row.get('pass_at_1')} | `{row.get('output_dir')}` | Qwen F base is 28/92 |"
    )
    lines.extend(
        [
            "",
            "## Leakage Flags in I-Runner Overlay",
            "",
            "| Task | Score root | Leak flags |",
            "|---|---|---|",
        ]
    )
    for task in payload.get("exp0_source_audit", {}).get("tasks", []):
        if task.get("source") != "I_runner_local_overlay":
            continue
        lines.append(
            f"| `{task['task_id']}` | `{task.get('overlay_score_root', '')}` | "
            f"`{', '.join(task.get('overlay_leak_flags', [])) or 'none'}` |"
        )
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", default="results/overfit-guard-exp0-4-2026-04-27")
    parser.add_argument("--generated-prefix", default="generated-overfit-guard-exp0-4-2026-04-27")
    parser.add_argument("--timeout-s", type=int, default=240)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--skip-score", action="store_true", help="Only write source audit and manifests.")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    if out_root.exists() and not args.overwrite:
        raise SystemExit(f"Output exists, pass --overwrite: {out_root}")
    out_root.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {
        "mode": "overfit_guard_exp0_4",
        "created_at_tag": "2026-04-27",
        "baseline": {
            "H_on_F_kimi": "65/92",
            "I_contract_runner_kimi": "74/92",
            "I_r26_final_kimi": "92/92",
            "F_qwen": "28/92",
        },
    }
    payload["exp0_source_audit"] = experiment0_source_audit(out_root)
    _write_summary(out_root, payload)
    if args.skip_score:
        return 0

    payload["exp1_mechanism_only_kimi"] = _run_result_dict(
        experiment1_mechanism_only_kimi(
            out_root=out_root,
            generated_prefix=args.generated_prefix,
            timeout_s=args.timeout_s,
            workers=args.workers,
            overwrite=args.overwrite,
        )
    )
    _write_summary(out_root, payload)

    payload["exp2_no_leakage_admission"] = _run_result_dict(
        experiment2_no_leakage_admission(
            out_root=out_root,
            generated_prefix=args.generated_prefix,
            timeout_s=args.timeout_s,
            workers=args.workers,
            overwrite=args.overwrite,
        )
    )
    _write_summary(out_root, payload)

    payload["exp3_family_holdout"] = [
        _run_result_dict(result)
        for result in experiment3_family_holdout(
            out_root=out_root,
            generated_prefix=args.generated_prefix,
            timeout_s=args.timeout_s,
            workers=args.workers,
            overwrite=args.overwrite,
        )
    ]
    _write_summary(out_root, payload)

    payload["exp4_cross_model_qwen"] = _run_result_dict(
        experiment4_cross_model_qwen(
            out_root=out_root,
            generated_prefix=args.generated_prefix,
            timeout_s=args.timeout_s,
            workers=args.workers,
            overwrite=args.overwrite,
        )
    )
    _write_summary(out_root, payload)
    print(out_root / "summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
