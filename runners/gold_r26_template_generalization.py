#!/usr/bin/env python3
"""Build and test parameterized mechanism variants distilled from R26 artifacts.

This is not a cold-start LLM score.  It is a teacher-data audit:

Gold/R26 pass artifact -> type-level parameterized variant -> EVAS check.

The goal is to identify which historical closure patterns are reusable as
mechanism templates, and which ones are just task-specific admissions.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from simulate_evas import run_case


REPO_ROOT = Path(__file__).resolve().parents[2]
BENCH_ROOT = Path(__file__).resolve().parents[1]
R26_ROOT = BENCH_ROOT / "generated-r26-dwa-pfd-combined-admission-2026-04-27" / "kimi-k2.5"


PatchFn = Callable[[Path], None]


@dataclass(frozen=True)
class Variant:
    name: str
    params: dict[str, object]
    patch: PatchFn


@dataclass(frozen=True)
class TemplateCase:
    template_id: str
    family: str
    source_task: str
    task_dir: Path
    sample_dir: Path
    dut_file: str
    tb_file: str
    mechanism_summary: str
    source_kind: str = "r26_verified_artifact"
    variants: list[Variant] = field(default_factory=list)


def _rewrite(path: Path, fn: Callable[[str], str]) -> None:
    old = path.read_text(encoding="utf-8")
    new = fn(old)
    path.write_text(new, encoding="utf-8")


def _sub_once(text: str, pattern: str, replacement: str) -> str:
    new, n = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if n != 1:
        raise RuntimeError(f"expected one match for {pattern!r}, got {n}")
    return new


def _fmt_ns(seconds: float) -> str:
    return f"{seconds * 1e9:g}n"


def patch_adpll(*, ref_period_s: float, div_ratio: int, stop_s: float = 5e-6) -> PatchFn:
    period = _fmt_ns(ref_period_s)
    width = _fmt_ns(ref_period_s / 2.0)
    stop = f"{stop_s * 1e6:g}u"

    def _patch(stage: Path) -> None:
        va = stage / "adpll_timer_ref.va"
        tb = stage / "tb_adpll_timer_ref.scs"
        _rewrite(
            va,
            lambda s: _sub_once(
                s,
                r"ref_period_nom\s*=\s*[^;]+;",
                f"ref_period_nom = {period};",
            ),
        )
        def tb_patch(s: str) -> str:
            s = _sub_once(
                s,
                r"period=[^ \\\n]+ width=[^ \\\n]+",
                f"period={period} width={width}",
            )
            s = re.sub(r"div_ratio=\d+", f"div_ratio={div_ratio}", s, count=1)
            s = _sub_once(s, r"tran tran stop=[^ ]+ maxstep=[^\n]+", f"tran tran stop={stop} maxstep=5n")
            return s
        _rewrite(tb, tb_patch)

    return _patch


def patch_dwa_code(code: int) -> PatchFn:
    if not 0 <= code <= 15:
        raise ValueError("DWA code must be 0..15")
    bits = [(code >> i) & 1 for i in range(4)]

    def _patch(stage: Path) -> None:
        tb = stage / "tb_dwa_ptr_gen.scs"
        def tb_patch(s: str) -> str:
            for idx, bit in enumerate(bits):
                val = "0.9" if bit else "0.0"
                s = re.sub(
                    rf"Vcode{idx} \(code_{idx} 0\) vsource dc=[^\n]+",
                    f"Vcode{idx} (code_{idx} 0) vsource dc={val}",
                    s,
                    count=1,
                )
            return s
        _rewrite(tb, tb_patch)

    return _patch


def patch_pfd(*, pulse_width_s: float = 0.5e-9, vdd: float = 0.9) -> PatchFn:
    pulse = _fmt_ns(pulse_width_s)

    def _patch(stage: Path) -> None:
        tb = stage / "tb_pfd_reset_race.scs"
        def tb_patch(s: str) -> str:
            s = re.sub(r"VDD \(vdd 0\) vsource dc=[^\n]+", f"VDD (vdd 0) vsource dc={vdd:g}", s, count=1)
            s = re.sub(r"val1=0\.9", f"val1={vdd:g}", s)
            s = re.sub(r"XDUT \(vdd vss ref div up dn\) pfd_updn", f"XDUT (vdd vss ref div up dn) pfd_updn pulse_width={pulse}", s, count=1)
            return s
        _rewrite(tb, tb_patch)

    return _patch


def patch_adc_dac(*, vdd: float = 0.9, ramp_stop_s: float = 50e-9) -> PatchFn:
    ramp_stop = _fmt_ns(ramp_stop_s)

    def _patch(stage: Path) -> None:
        tb = stage / "tb_adc_dac_ideal_4b_ref.scs"
        def tb_patch(s: str) -> str:
            s = s.replace('ahdl_include "adc_ideal_4b_ref.va"', 'ahdl_include "adc_ideal_4b.va"')
            s = s.replace('ahdl_include "dac_ideal_4b_ref.va"', 'ahdl_include "dac_ideal_4b.va"')
            s = re.sub(r"parameters vdd=[^ ]+", f"parameters vdd={vdd:g}", s, count=1)
            s = re.sub(r"Vvin \(vin 0\) vsource type=pwl wave=\[0 0\s+[^ ]+\s+[^\]]+\]", f"Vvin (vin 0) vsource type=pwl wave=[0 0  {ramp_stop} vdd]", s, count=1)
            s = re.sub(r"tran tran stop=[^ ]+ maxstep=", f"tran tran stop={ramp_stop} maxstep=", s, count=1)
            return s
        _rewrite(tb, tb_patch)

    return _patch


def _case_defs() -> list[TemplateCase]:
    return [
        TemplateCase(
            template_id="pll_feedback_cadence_lock",
            family="pll-clock",
            source_task="adpll_timer_smoke",
            task_dir=BENCH_ROOT / "tasks/end-to-end/voltage/adpll_timer_smoke",
            sample_dir=R26_ROOT / "adpll_timer_smoke/sample_0",
            dut_file="adpll_timer_ref.va",
            tb_file="tb_adpll_timer_ref.scs",
            mechanism_summary="Keep ref/fb cadence matched through DCO timer plus divider; assert lock only after visible reference edges.",
            variants=[
                Variant("base_20n_div8", {"ref_period_s": 20e-9, "div_ratio": 8}, patch_adpll(ref_period_s=20e-9, div_ratio=8)),
                Variant("fast_ref_16n_div8", {"ref_period_s": 16e-9, "div_ratio": 8}, patch_adpll(ref_period_s=16e-9, div_ratio=8, stop_s=4e-6)),
                Variant("slow_ref_25n_div8", {"ref_period_s": 25e-9, "div_ratio": 8}, patch_adpll(ref_period_s=25e-9, div_ratio=8, stop_s=6.25e-6)),
                Variant("base_ref_div6", {"ref_period_s": 20e-9, "div_ratio": 6}, patch_adpll(ref_period_s=20e-9, div_ratio=6)),
            ],
        ),
        TemplateCase(
            template_id="dwa_rotating_pointer_window",
            family="dwa",
            source_task="dwa_ptr_gen_smoke",
            task_dir=BENCH_ROOT / "tasks/end-to-end/voltage/dwa_ptr_gen_smoke",
            sample_dir=R26_ROOT / "dwa_ptr_gen_smoke/sample_0",
            dut_file="dwa_ptr_gen.va",
            tb_file="tb_dwa_ptr_gen.scs",
            mechanism_summary="Decode 4-bit code, advance pointer modulo 16, and drive held one-hot pointer plus active-cell window outside conditionals.",
            variants=[
                Variant("code1", {"code": 1}, patch_dwa_code(1)),
                Variant("code3", {"code": 3}, patch_dwa_code(3)),
                Variant("code5", {"code": 5}, patch_dwa_code(5)),
                Variant("code7", {"code": 7}, patch_dwa_code(7)),
            ],
        ),
        TemplateCase(
            template_id="pfd_mutual_exclusion_pulse_windows",
            family="pfd-bbpd",
            source_task="pfd_reset_race_smoke",
            task_dir=BENCH_ROOT / "tasks/end-to-end/voltage/pfd_reset_race_smoke",
            sample_dir=R26_ROOT / "pfd_reset_race_smoke/sample_0",
            dut_file="pfd_updn.va",
            tb_file="tb_pfd_reset_race.scs",
            mechanism_summary="Generate separated UP and DN pulse windows with no overlap and parameterized pulse width.",
            variants=[
                Variant("pulse_0p3n", {"pulse_width_s": 0.3e-9}, patch_pfd(pulse_width_s=0.3e-9)),
                Variant("pulse_0p5n", {"pulse_width_s": 0.5e-9}, patch_pfd(pulse_width_s=0.5e-9)),
                Variant("pulse_0p7n", {"pulse_width_s": 0.7e-9}, patch_pfd(pulse_width_s=0.7e-9)),
            ],
        ),
        TemplateCase(
            template_id="adc_dac_quantize_reconstruct",
            family="converter",
            source_task="adc_dac_ideal_4b_smoke",
            task_dir=BENCH_ROOT / "tasks/end-to-end/voltage/adc_dac_ideal_4b_smoke",
            sample_dir=R26_ROOT / "adc_dac_ideal_4b_smoke/sample_0",
            dut_file="adc_ideal_4b.va",
            tb_file="tb_adc_dac_ideal_4b_ref.scs",
            mechanism_summary="Quantize input ramp into 4-bit monotonic code and reconstruct a monotonic DAC output with sufficient span.",
            variants=[
                Variant("vdd0p8_ramp50n", {"vdd": 0.8, "ramp_stop_s": 50e-9}, patch_adc_dac(vdd=0.8, ramp_stop_s=50e-9)),
                Variant("vdd0p9_ramp80n", {"vdd": 0.9, "ramp_stop_s": 80e-9}, patch_adc_dac(vdd=0.9, ramp_stop_s=80e-9)),
                Variant("vdd1p2_ramp50n", {"vdd": 1.2, "ramp_stop_s": 50e-9}, patch_adc_dac(vdd=1.2, ramp_stop_s=50e-9)),
            ],
        ),
    ]


def run_variant(case: TemplateCase, variant: Variant, out_root: Path, *, timeout_s: int, overwrite: bool) -> dict:
    stage = out_root / "staged" / case.template_id / variant.name
    result_dir = out_root / "runs" / case.template_id / variant.name
    if stage.exists():
        if not overwrite:
            raise FileExistsError(stage)
        shutil.rmtree(stage)
    if result_dir.exists() and overwrite:
        shutil.rmtree(result_dir)
    stage.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(case.sample_dir, stage)
    variant.patch(stage)
    result_dir.mkdir(parents=True, exist_ok=True)
    result = run_case(
        case.task_dir,
        stage / case.dut_file,
        stage / case.tb_file,
        output_root=result_dir,
        keep_run_dir=False,
        timeout_s=timeout_s,
        task_id_override=case.source_task,
    )
    result_path = result_dir / "result.json"
    result_path.write_text(json.dumps(result, indent=2, allow_nan=True), encoding="utf-8")
    return {
        "template_id": case.template_id,
        "family": case.family,
        "source_task": case.source_task,
        "variant": variant.name,
        "params": variant.params,
        "status": result["status"],
        "scores": result["scores"],
        "notes": result["notes"],
        "stage_dir": str(stage.relative_to(BENCH_ROOT)),
        "result_json": str(result_path.relative_to(BENCH_ROOT)),
    }


def write_template_dataset(cases: list[TemplateCase], out_root: Path) -> Path:
    dataset = {
        "version": 1,
        "purpose": "gold/R26 verified artifact to parameterized mechanism template audit",
        "source_root": str(R26_ROOT.relative_to(BENCH_ROOT)),
        "templates": [
            {
                "template_id": c.template_id,
                "family": c.family,
                "source_task": c.source_task,
                "source_kind": c.source_kind,
                "mechanism_summary": c.mechanism_summary,
                "variant_count": len(c.variants),
                "variant_params": [{"name": v.name, "params": v.params} for v in c.variants],
            }
            for c in cases
        ],
    }
    path = out_root / "gold_r26_mechanism_templates.json"
    path.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
    return path


def write_markdown(summary: dict, out_root: Path) -> Path:
    lines = [
        "# Gold/R26 Template Generalization",
        "",
        "This is a teacher-data audit, not a cold-start LLM score.",
        "",
        f"- Total variants: `{summary['total_variants']}`",
        f"- PASS variants: `{summary['pass_variants']}`",
        "",
        "| Template | Family | Source task | Variants | PASS |",
        "|---|---|---|---:|---:|",
    ]
    for row in summary["by_template"]:
        lines.append(
            f"| `{row['template_id']}` | `{row['family']}` | `{row['source_task']}` | "
            f"{row['variants']} | {row['pass']} |"
        )
    lines.extend(["", "## Variant Detail", "", "| Template | Variant | Params | Status | Notes |", "|---|---|---|---|---|"])
    for row in summary["results"]:
        notes = "; ".join(row.get("notes", []))
        lines.append(
            f"| `{row['template_id']}` | `{row['variant']}` | `{json.dumps(row['params'])}` | "
            f"`{row['status']}` | {notes[:220]} |"
        )
    path = out_root / "summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", default="results/gold-r26-template-generalization-2026-04-29")
    ap.add_argument("--timeout-s", type=int, default=180)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--template", action="append", help="Limit to template_id; repeatable.")
    args = ap.parse_args()

    out_root = (BENCH_ROOT / args.output_root).resolve()
    if out_root.exists() and args.overwrite:
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    selected = set(args.template or [])
    cases = [c for c in _case_defs() if not selected or c.template_id in selected]
    if selected and len(cases) != len(selected):
        known = {c.template_id for c in _case_defs()}
        missing = sorted(selected - known)
        raise SystemExit(f"unknown template(s): {missing}; known={sorted(known)}")

    template_dataset = write_template_dataset(cases, out_root)
    results = []
    for case in cases:
        for variant in case.variants:
            print(f"[generalization] {case.template_id}/{variant.name} ...", flush=True)
            results.append(run_variant(case, variant, out_root, timeout_s=args.timeout_s, overwrite=args.overwrite))

    by_template = []
    for case in cases:
        rows = [r for r in results if r["template_id"] == case.template_id]
        by_template.append({
            "template_id": case.template_id,
            "family": case.family,
            "source_task": case.source_task,
            "variants": len(rows),
            "pass": sum(1 for r in rows if r["status"] == "PASS"),
        })
    summary = {
        "template_dataset": str(template_dataset.relative_to(BENCH_ROOT)),
        "total_variants": len(results),
        "pass_variants": sum(1 for r in results if r["status"] == "PASS"),
        "by_template": by_template,
        "results": results,
    }
    (out_root / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=True), encoding="utf-8")
    md_path = write_markdown(summary, out_root)
    print(json.dumps({
        "output_root": str(out_root.relative_to(BENCH_ROOT)),
        "summary_json": str((out_root / "summary.json").relative_to(BENCH_ROOT)),
        "summary_md": str(md_path.relative_to(BENCH_ROOT)),
        "pass": f"{summary['pass_variants']}/{summary['total_variants']}",
    }, indent=2))


if __name__ == "__main__":
    main()
