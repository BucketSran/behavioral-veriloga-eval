#!/usr/bin/env python3
"""Run the current vaEvas regression matrix and write an auditable summary.

The script intentionally re-scores existing generated artifacts with the
current checker/attribution pipeline.  It does not call model APIs.  This keeps
the experiment focused on whether the latest contracts, mechanism patches,
streaming checkers, and failure attribution change the measured outcome.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Experiment:
    condition: str
    model: str
    generated_dir: str
    label: str
    note: str = ""


EXPERIMENTS: tuple[Experiment, ...] = (
    Experiment(
        condition="A",
        model="kimi-k2.5",
        generated_dir="generated-experiment/condition-A/kimi-k2.5",
        label="A-kimi",
        note="baseline prompt, Kimi",
    ),
    Experiment(
        condition="A",
        model="qwen3-max-2026-01-23",
        generated_dir="generated-experiment/condition-A/qwen3-max-2026-01-23",
        label="A-qwen",
        note="baseline prompt, Qwen",
    ),
    Experiment(
        condition="B",
        model="kimi-k2.5",
        generated_dir="generated-experiment/condition-B/kimi-k2.5",
        label="B-kimi",
        note="prompt-only/skill condition, Kimi",
    ),
    Experiment(
        condition="B",
        model="qwen3-max-2026-01-23",
        generated_dir="generated-experiment/condition-B/qwen3-max-2026-01-23",
        label="B-qwen",
        note="prompt-only/skill condition, Qwen",
    ),
    Experiment(
        condition="C",
        model="kimi-k2.5",
        generated_dir="generated-experiment/condition-C/kimi-k2.5",
        label="C-kimi",
        note="prompt+skill generation condition, Kimi",
    ),
    Experiment(
        condition="C",
        model="qwen3-max-2026-01-23",
        generated_dir="generated-experiment/condition-C/qwen3-max-2026-01-23",
        label="C-qwen",
        note="prompt+skill generation condition, Qwen",
    ),
    Experiment(
        condition="D",
        model="kimi-k2.5",
        generated_dir="generated-table2-evas-guided-repair-no-skill",
        label="D-kimi",
        note="EVAS-guided repair without skill, Kimi",
    ),
    Experiment(
        condition="D",
        model="qwen3-max-2026-01-23",
        generated_dir="generated-table2-evas-guided-repair-no-skill",
        label="D-qwen",
        note="EVAS-guided repair without skill, Qwen",
    ),
    Experiment(
        condition="E",
        model="kimi-k2.5",
        generated_dir="generated-table2-evas-guided-repair",
        label="E-kimi",
        note="EVAS-guided repair with skill, Kimi",
    ),
    Experiment(
        condition="E",
        model="qwen3-max-2026-01-23",
        generated_dir="generated-table2-evas-guided-repair",
        label="E-qwen",
        note="EVAS-guided repair with skill, Qwen",
    ),
    Experiment(
        condition="F",
        model="kimi-k2.5",
        generated_dir="generated-table2-evas-guided-repair-3round",
        label="F-kimi",
        note="three-round EVAS repair, Kimi",
    ),
    Experiment(
        condition="F",
        model="qwen3-max-2026-01-23",
        generated_dir="generated-table2-evas-guided-repair-3round",
        label="F-qwen",
        note="three-round EVAS repair, Qwen",
    ),
    Experiment(
        condition="G",
        model="kimi-k2.5",
        generated_dir="generated-table2-evas-guided-repair-3round-skill",
        label="G-kimi",
        note="three-round EVAS repair with skill, Kimi; generated set may be incomplete",
    ),
    Experiment(
        condition="G",
        model="qwen3-max-2026-01-23",
        generated_dir="generated-table2-evas-guided-repair-3round-skill",
        label="G-qwen",
        note="three-round EVAS repair with skill, Qwen; generated set may be incomplete",
    ),
    Experiment(
        condition="H",
        model="kimi-k2.5",
        generated_dir="generated-condition-H-on-F-kimi-2026-04-26",
        label="H-on-F-kimi",
        note="signature/contract-guided repair overlay on F, Kimi",
    ),
    Experiment(
        condition="H",
        model="kimi-k2.5",
        generated_dir="generated-condition-H-on-G-kimi-2026-04-26",
        label="H-on-G-kimi",
        note="signature/contract-guided repair overlay on G, Kimi",
    ),
    Experiment(
        condition="I",
        model="kimi-k2.5",
        generated_dir="generated-latest-contract-combined-full92-runner-2026-04-27",
        label="I-contract-runner-kimi",
        note="formal materialization runner before R26 final admission, Kimi",
    ),
    Experiment(
        condition="I",
        model="kimi-k2.5",
        generated_dir="generated-r26-dwa-pfd-combined-admission-2026-04-27",
        label="I-r26-final-kimi",
        note="R26 final combined admission set, Kimi",
    ),
)


def _model_dir_name(model: str) -> str:
    return model.replace("/", "_")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _generated_sample_count(generated_dir: Path, model: str) -> int:
    root = generated_dir / _model_dir_name(model)
    if not root.exists():
        return 0
    return sum(1 for _ in root.glob("*/sample_0"))


def _run_command(cmd: list[str], cwd: Path, stdout_path: Path) -> int:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    with stdout_path.open("w", encoding="utf-8") as handle:
        process = subprocess.run(
            cmd,
            cwd=str(cwd),
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    return int(process.returncode)


def _summarize_experiment(
    experiment: Experiment,
    out_dir: Path,
    generated_abs: Path,
    score_returncode: int | None,
    triage_returncode: int | None,
    elapsed_s: float | None,
) -> dict[str, Any]:
    aggregate = _read_json(out_dir / "model_results.json")
    triage = _read_json(out_dir / "failure_attribution_report.json")
    generated_count = _generated_sample_count(generated_abs, experiment.model)

    total = aggregate.get("total_tasks")
    passed = aggregate.get("pass_count")
    pass_at_1 = aggregate.get("pass_at_1")
    return {
        "label": experiment.label,
        "condition": experiment.condition,
        "model": experiment.model,
        "generated_dir": experiment.generated_dir,
        "generated_sample_count": generated_count,
        "note": experiment.note,
        "output_dir": str(out_dir.relative_to(ROOT)),
        "score_returncode": score_returncode,
        "triage_returncode": triage_returncode,
        "elapsed_s": elapsed_s,
        "total_tasks": total,
        "pass_count": passed,
        "pass_at_1": pass_at_1,
        "by_family": aggregate.get("by_family", {}),
        "failure_domain_taxonomy": aggregate.get("failure_domain_taxonomy", {}),
        "repair_owner_taxonomy": aggregate.get("repair_owner_taxonomy", {}),
        "strict_pass_count": triage.get("strict_status_counts", {}).get("STRICT_PASS"),
        "strict_nonpass_count": triage.get("strict_status_counts", {}).get("STRICT_NONPASS"),
        "contract_family_counts": triage.get("contract_family_counts", {}),
        "failure_count": triage.get("failure_count"),
    }


def _write_summary(out_root: Path, rows: list[dict[str, Any]]) -> None:
    out_root.mkdir(parents=True, exist_ok=True)
    summary_json = out_root / "summary.json"
    summary_json.write_text(json.dumps({"experiments": rows}, indent=2), encoding="utf-8")

    lines = [
        "# Current vaEvas Regression",
        "",
        "This report re-scores existing generated artifacts with the current checker, contract, streaming, and failure-attribution pipeline.",
        "",
        "| label | model | generated | samples | pass | Pass@1 | strict pass | failure domains | notes |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        total = row.get("total_tasks")
        passed = row.get("pass_count")
        pass_text = "n/a" if total is None or passed is None else f"{passed}/{total}"
        pass_at_1 = row.get("pass_at_1")
        pass_at_text = "n/a" if pass_at_1 is None else f"{float(pass_at_1):.3f}"
        strict = row.get("strict_pass_count")
        strict_nonpass = row.get("strict_nonpass_count")
        strict_text = "n/a" if strict is None else f"{strict}/{(strict or 0) + (strict_nonpass or 0)}"
        domains = row.get("failure_domain_taxonomy") or {}
        domain_text = ", ".join(f"{k}:{v}" for k, v in sorted(domains.items())) or "n/a"
        lines.append(
            "| {label} | {model} | `{generated_dir}` | {samples} | {pass_text} | {pass_at_text} | {strict_text} | {domains} | {note} |".format(
                label=row.get("label", ""),
                model=row.get("model", ""),
                generated_dir=row.get("generated_dir", ""),
                samples=row.get("generated_sample_count", 0),
                pass_text=pass_text,
                pass_at_text=pass_at_text,
                strict_text=strict_text,
                domains=domain_text,
                note=(row.get("note") or "").replace("|", "/"),
            )
        )

    lines.extend(
        [
            "",
            "## Per-Condition Detail",
            "",
        ]
    )
    for row in rows:
        lines.extend(
            [
                f"### {row.get('label')}",
                "",
                f"- output: `{row.get('output_dir')}`",
                f"- score_returncode: `{row.get('score_returncode')}`",
                f"- triage_returncode: `{row.get('triage_returncode')}`",
                f"- elapsed_s: `{row.get('elapsed_s')}`",
                f"- by_family: `{json.dumps(row.get('by_family', {}), sort_keys=True)}`",
                f"- repair_owner_taxonomy: `{json.dumps(row.get('repair_owner_taxonomy', {}), sort_keys=True)}`",
                f"- contract_family_counts: `{json.dumps(row.get('contract_family_counts', {}), sort_keys=True)}`",
                "",
            ]
        )
    (out_root / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def run_experiment(
    experiment: Experiment,
    out_root: Path,
    timeout_s: int,
    workers: int,
    resume: bool,
    save_policy: str,
    skip_existing: bool,
) -> dict[str, Any]:
    generated_abs = ROOT / experiment.generated_dir
    out_dir = out_root / experiment.label
    model_results = out_dir / "model_results.json"
    triage_json = out_dir / "failure_attribution_report.json"

    aggregate = _read_json(model_results)
    triage = _read_json(triage_json)
    triage_is_current = (
        bool(triage)
        and int(triage.get("total_tasks", -1)) == int(aggregate.get("total_tasks", -2))
        and int(triage.get("total_tasks", 0)) > 0
    )

    if skip_existing and model_results.exists() and triage_is_current:
        return _summarize_experiment(
            experiment=experiment,
            out_dir=out_dir,
            generated_abs=generated_abs,
            score_returncode=0,
            triage_returncode=0,
            elapsed_s=0.0,
        )

    start = time.time()
    score_rc: int | None = 0
    if not (skip_existing and model_results.exists()):
        score_cmd = [
            sys.executable,
            "runners/score.py",
            "--model",
            experiment.model,
            "--generated-dir",
            experiment.generated_dir,
            "--output-dir",
            str(out_dir.relative_to(ROOT)),
            "--timeout-s",
            str(timeout_s),
            "--workers",
            str(workers),
            "--save-policy",
            save_policy,
        ]
        if resume:
            score_cmd.append("--resume")
        score_rc = _run_command(score_cmd, cwd=ROOT, stdout_path=out_dir / "score.stdout.log")

    triage_rc: int | None = None
    if model_results.exists():
        triage_cmd = [
            sys.executable,
            "runners/behavior_contract_triage.py",
            "--result-root",
            str(out_dir),
            "--json-out",
            str(triage_json),
            "--md-out",
            str(out_dir / "failure_attribution_report.md"),
        ]
        triage_rc = _run_command(triage_cmd, cwd=ROOT, stdout_path=out_dir / "triage.stdout.log")

    elapsed = round(time.time() - start, 3)
    return _summarize_experiment(
        experiment=experiment,
        out_dir=out_dir,
        generated_abs=generated_abs,
        score_returncode=score_rc,
        triage_returncode=triage_rc,
        elapsed_s=elapsed,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-root",
        default="results/current-experiment-regression-2026-04-27",
        help="Output root under behavioral-veriloga-eval.",
    )
    parser.add_argument("--only", action="append", default=[], help="Run only labels or conditions. Repeatable.")
    parser.add_argument("--timeout-s", type=int, default=240)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--save-policy", choices=["contract", "debug"], default="contract")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    out_root.mkdir(parents=True, exist_ok=True)

    selectors = set(args.only)
    selected = [
        exp for exp in EXPERIMENTS
        if not selectors or exp.label in selectors or exp.condition in selectors
    ]
    rows: list[dict[str, Any]] = []
    for index, experiment in enumerate(selected, 1):
        print(f"[regression] {index}/{len(selected)} {experiment.label}: {experiment.note}", flush=True)
        row = run_experiment(
            experiment=experiment,
            out_root=out_root,
            timeout_s=args.timeout_s,
            workers=args.workers,
            resume=args.resume,
            save_policy=args.save_policy,
            skip_existing=args.skip_existing,
        )
        rows.append(row)
        _write_summary(out_root, rows)
        total = row.get("total_tasks")
        passed = row.get("pass_count")
        print(
            f"[regression] {experiment.label} done: pass={passed}/{total} "
            f"score_rc={row.get('score_returncode')} triage_rc={row.get('triage_returncode')}",
            flush=True,
        )

    _write_summary(out_root, rows)
    print(f"[regression] summary: {out_root / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
