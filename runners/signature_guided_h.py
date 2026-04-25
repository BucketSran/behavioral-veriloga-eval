#!/usr/bin/env python3
"""Signature-guided H-condition EVAS repair prototype.

H is deliberately narrower than the exploratory template runner:

1. Re-score the G artifact with EVAS to obtain concrete failure notes.
2. Classify the failure by diagnostic signature, not by task name.
3. Check the DUT module/interface signature before selecting a reusable
   mechanism template family.
4. Let EVAS rank bounded candidates and keep the best observed candidate.

The task id is still used to find benchmark files and artifacts, but not to
decide which repair template is eligible.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from generate import extract_module_signature
from simulate_evas import run_case
from template_guided_repair import TemplateVariant, clk_divider_variants
from template_guided_smallset import _dff_rst_body, _dwa_ptr_gen_body, _flash_adc_3b_body, _multimod_body, _pfd_body


ROOT = Path(__file__).resolve().parents[1]
ROUND_DIRS = ("sample_0_round3", "sample_0_round2", "sample_0_round1", "sample_0")


@dataclass(frozen=True)
class Candidate:
    name: str
    description: str
    file_name: str
    body: str


@dataclass(frozen=True)
class ResolvedTask:
    task_id: str
    task_dir: Path
    tb_path: Path
    anchor_path: Path
    module_name: str
    ports: tuple[str, ...]


def _json_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fingerprint_tree(root: Path, patterns: tuple[str, ...]) -> list[dict[str, str]]:
    if not root.exists():
        return []
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(root.rglob(pattern))
    items: list[dict[str, str]] = []
    for path in sorted(set(paths)):
        if path.is_file():
            items.append({"path": str(path.relative_to(root)), "sha256": _sha256_file(path)})
    return items


def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name)


def _notes_text(result: dict) -> str:
    notes = result.get("notes") or []
    if isinstance(notes, str):
        return notes
    return "\n".join(str(note) for note in notes)


def _extract_interval_gap(result: dict) -> int | None:
    notes = _notes_text(result)
    ratio_match = re.search(r"\bratio_code=([0-9]+)", notes)
    hist_match = re.search(r"\binterval_hist=\{([^}]*)\}", notes)
    if not ratio_match or not hist_match:
        return None
    ratio = int(ratio_match.group(1))
    keys = [int(key) for key in re.findall(r"([0-9]+)\s*:", hist_match.group(1))]
    if not keys:
        return None
    return min(abs(key - ratio) for key in keys)


def _extract_count_gap(result: dict) -> int | None:
    notes = _notes_text(result)
    base_match = re.search(r"\bbase=([0-9]+)", notes)
    pre_match = re.search(r"\bpre_count=([0-9]+)", notes)
    post_match = re.search(r"\bpost_count=([0-9]+)", notes)
    if not base_match or not pre_match or not post_match:
        return None
    base = int(base_match.group(1))
    pre = int(pre_match.group(1))
    post = int(post_match.group(1))
    return abs(pre - base) + abs(post - (base + 1))


def _extract_code_gap(result: dict) -> int | None:
    notes = _notes_text(result)
    only_match = re.search(r"\bonly_([0-9]+)_codes\s*\(need\s*([0-9]+)\)", notes)
    codes_match = re.search(r"\bcodes=([0-9]+)/([0-9]+)", notes)
    if only_match:
        return int(only_match.group(2)) - int(only_match.group(1))
    if codes_match:
        return int(codes_match.group(2)) - int(codes_match.group(1))
    return None


def _rank(result: dict) -> tuple:
    scores = result.get("scores") or {}
    gaps = [
        gap
        for gap in (
            _extract_interval_gap(result),
            _extract_count_gap(result),
            _extract_code_gap(result),
        )
        if gap is not None
    ]
    gap_rank = 0 if not gaps else -min(gaps)
    return (
        int(result.get("status") == "PASS"),
        float(scores.get("weighted_total", 0.0)),
        gap_rank,
    )


def _run_case_safe(
    task_dir: Path,
    dut_path: Path,
    tb_path: Path,
    output_root: Path,
    timeout_s: int,
    task_id: str,
) -> dict:
    try:
        return run_case(
            task_dir,
            dut_path,
            tb_path,
            output_root=output_root,
            timeout_s=timeout_s,
            task_id_override=task_id,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "task_id": task_id,
            "status": "FAIL_INFRA",
            "backend_used": "evas",
            "scores": {
                "dut_compile": 0.0,
                "tb_compile": 0.0,
                "sim_correct": 0.0,
                "weighted_total": 0.0,
            },
            "artifacts": [str(dut_path), str(tb_path), str(output_root / "tran.csv")],
            "notes": [f"evas_timeout>{timeout_s}s", f"cmd={getattr(exc, 'cmd', '')}"],
            "stdout_tail": "",
        }


def _find_task_dir(task_id: str) -> Path:
    matches = sorted(ROOT.glob(f"tasks/**/{task_id}/meta.json"))
    if not matches:
        raise FileNotFoundError(f"Cannot find task meta.json for {task_id}")
    if len(matches) > 1:
        raise RuntimeError(f"Ambiguous task id {task_id}: {[str(p.parent) for p in matches]}")
    return matches[0].parent


def _find_tb(task_dir: Path) -> Path:
    tbs = sorted((task_dir / "gold").glob("tb_*.scs"))
    if not tbs:
        tbs = sorted((task_dir / "gold").glob("*.scs"))
    if not tbs:
        raise FileNotFoundError(f"Cannot find gold testbench under {task_dir / 'gold'}")
    return tbs[0]


def _anchor_candidates(anchor_root: Path, task_id: str) -> list[Path]:
    task_root = anchor_root / task_id
    candidates: list[Path] = []
    for round_dir in ROUND_DIRS:
        sample_dir = task_root / round_dir
        if sample_dir.is_dir():
            candidates.extend(sorted(sample_dir.glob("*.va")))
    return candidates


def _resolve_task(task_id: str, anchor_root: Path) -> ResolvedTask:
    task_dir = _find_task_dir(task_id)
    tb_path = _find_tb(task_dir)
    for candidate in _anchor_candidates(anchor_root, task_id):
        signature = extract_module_signature(candidate)
        if signature is None:
            continue
        module_name, ports = signature
        return ResolvedTask(
            task_id=task_id,
            task_dir=task_dir,
            tb_path=tb_path,
            anchor_path=candidate,
            module_name=module_name,
            ports=tuple(ports),
        )
    raise FileNotFoundError(f"Cannot find a parseable single-module anchor for {task_id}")


def _classify_failure(result: dict) -> str:
    notes = _notes_text(result)
    if "ratio_code=" in notes and "interval_hist=" in notes:
        return "cadence_ratio_hist"
    if "base=" in notes and "pre_count=" in notes and "post_count=" in notes:
        return "cadence_multimod_counts"
    if "q_mismatch" in notes.lower() or "qb_mismatch" in notes.lower() or "wrong_edge" in notes.lower():
        return "sampled_latch_reset_priority"
    if re.search(r"\bonly_[0-9]+_codes", notes) or "codes=" in notes:
        return "quantizer_code_coverage"
    if "overlap" in notes.lower() or "ptr_" in notes.lower() or "cell_en" in notes.lower():
        return "onehot_no_overlap"
    if "up_frac" in notes.lower() or "dn_frac" in notes.lower() or "pulse" in notes.lower():
        return "pfd_timing_window"
    return "unsupported"


def _has_ports(ports: tuple[str, ...], required: set[str]) -> bool:
    observed = {port.lower() for port in ports}
    return {port.lower() for port in required}.issubset(observed)


def _clk_divider_candidates(file_name: str) -> list[Candidate]:
    variants: list[Candidate] = []
    for variant in clk_divider_variants():
        assert isinstance(variant, TemplateVariant)
        variants.append(
            Candidate(
                name=variant.name,
                description=variant.description,
                file_name=file_name,
                body=variant.body,
            )
        )
    return variants


def _multimod_candidates(file_name: str) -> list[Candidate]:
    return [
        Candidate(
            name="pulse_every_base_or_base_plus_one_reset0",
            description="Pulse on the decoded base count, adding one edge when mod is high.",
            file_name=file_name,
            body=_multimod_body(reset_to_one=False),
        ),
        Candidate(
            name="pulse_every_base_or_base_plus_one_reset1",
            description="Same cadence family with count-after-event phase hypothesis.",
            file_name=file_name,
            body=_multimod_body(reset_to_one=True),
        ),
    ]


def _flash_adc_candidates(file_name: str) -> list[Candidate]:
    return [
        Candidate(
            name="clocked_uniform_3b_quantizer",
            description="Clocked 3-bit quantizer covering all 8 output codes.",
            file_name=file_name,
            body=_flash_adc_3b_body(),
        )
    ]


def _dff_rst_candidates(file_name: str) -> list[Candidate]:
    return [
        Candidate(
            name="posedge_sample_reset_priority",
            description="Clocked DFF with reset priority and complementary Q/QB outputs.",
            file_name=file_name,
            body=_dff_rst_body(),
        )
    ]


def _dwa_candidates(file_name: str, module_name: str) -> list[Candidate]:
    no_overlap = module_name == "dwa_ptr_gen_no_overlap"
    return [
        Candidate(
            name="onehot_pointer_thermometer_no_overlap" if no_overlap else "onehot_pointer_thermometer",
            description="Pointer plus cell-enable skeleton with bounded 16-cell one-hot/thermometer behavior.",
            file_name=file_name,
            body=_dwa_ptr_gen_body(no_overlap=no_overlap),
        )
    ]


def _pfd_candidates(file_name: str) -> list[Candidate]:
    return [
        Candidate(
            name="pfd_immediate_mutual_reset",
            description="REF/DIV edge PFD with immediate mutual reset hypothesis.",
            file_name=file_name,
            body=_pfd_body(clear_mode="immediate"),
        ),
        Candidate(
            name="pfd_delayed_mutual_reset",
            description="REF/DIV edge PFD with short delayed mutual reset hypothesis.",
            file_name=file_name,
            body=_pfd_body(clear_mode="timer_0p5n"),
        ),
    ]


def _eligible_candidates(
    resolved: ResolvedTask,
    failure_signature: str,
) -> tuple[str | None, str, list[Candidate]]:
    ports = resolved.ports
    file_name = resolved.anchor_path.name

    if (
        failure_signature == "cadence_ratio_hist"
        and resolved.module_name == "clk_divider_ref"
        and _has_ports(
            ports,
            {
                "clk_in",
                "rst_n",
                "div_code_0",
                "div_code_1",
                "div_code_2",
                "div_code_3",
                "div_code_4",
                "div_code_5",
                "div_code_6",
                "div_code_7",
                "clk_out",
                "lock",
            },
        )
    ):
        return (
            "counter_cadence_programmable_divider",
            "EVAS reported ratio/interval cadence mismatch and the interface exposes clk_in, rst_n, div_code bits, clk_out, lock.",
            _clk_divider_candidates(file_name),
        )

    if (
        failure_signature == "cadence_multimod_counts"
        and resolved.module_name == "multimod_divider_ref"
        and _has_ports(ports, {"clk_in", "mod", "mod_0", "mod_1", "mod_2", "mod_3", "prescaler_out"})
    ):
        return (
            "counter_cadence_multimod_prescaler",
            "EVAS reported base/pre/post count mismatch and the interface exposes clk_in, mod bits, and prescaler_out.",
            _multimod_candidates(file_name),
        )

    if (
        failure_signature == "quantizer_code_coverage"
        and resolved.module_name == "flash_adc_3b"
        and _has_ports(ports, {"VDD", "VSS", "VIN", "CLK", "DOUT2", "DOUT1", "DOUT0"})
    ):
        return (
            "clocked_quantizer_code_coverage",
            "EVAS reported missing output codes and the interface is a clocked 3-bit ADC.",
            _flash_adc_candidates(file_name),
        )

    if (
        failure_signature == "sampled_latch_reset_priority"
        and resolved.module_name == "dff_rst"
        and _has_ports(ports, {"VDD", "VSS", "D", "CLK", "RST", "Q", "QB"})
    ):
        return (
            "sampled_latch_reset_priority",
            "EVAS reported sampled Q/QB mismatch and the interface exposes D/CLK/RST/Q/QB.",
            _dff_rst_candidates(file_name),
        )

    if (
        failure_signature == "onehot_no_overlap"
        and resolved.module_name in {"dwa_ptr_gen", "dwa_ptr_gen_no_overlap"}
        and _has_ports(ports, {"clk_i", "rst_ni", "ptr_0", "cell_en_0"})
    ):
        return (
            "onehot_thermometer_no_overlap",
            "EVAS reported pointer/cell overlap behavior and the interface exposes DWA pointer/cell enable buses.",
            _dwa_candidates(file_name, resolved.module_name),
        )

    if (
        failure_signature == "pfd_timing_window"
        and resolved.module_name == "pfd_updn"
        and _has_ports(ports, {"VDD", "VSS", "REF", "DIV", "UP", "DN"})
    ):
        return (
            "pfd_pll_timing_window",
            "EVAS reported UP/DN pulse/window behavior and the interface exposes REF/DIV/UP/DN.",
            _pfd_candidates(file_name),
        )

    return None, "No reusable template family matches both failure notes and module/interface signature.", []


def _copy_anchor(resolved: ResolvedTask, generated_root: Path) -> Path:
    baseline_dir = generated_root / resolved.task_id / "baseline"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_path = baseline_dir / resolved.anchor_path.name
    shutil.copy2(resolved.anchor_path, baseline_path)
    return baseline_path


def _h_cache_key(
    *,
    resolved: ResolvedTask,
    timeout_s: int,
    early_stop_pass: bool,
    report_only: bool,
) -> dict:
    return {
        "version": 2,
        "task_id": resolved.task_id,
        "timeout_s": timeout_s,
        "early_stop_pass": early_stop_pass,
        "report_only": report_only,
        "anchor": {
            "path": str(resolved.anchor_path),
            "sha256": _sha256_file(resolved.anchor_path),
        },
        "task_gold": _fingerprint_tree(resolved.task_dir / "gold", ("*.scs", "*.va", "*.csv")),
        "signature_guided_h_py": _sha256_file(Path(__file__).resolve()),
        "simulate_evas_py": _sha256_file((ROOT / "runners" / "simulate_evas.py").resolve()),
        "template_guided_repair_py": _sha256_file((ROOT / "runners" / "template_guided_repair.py").resolve()),
        "template_guided_smallset_py": _sha256_file((ROOT / "runners" / "template_guided_smallset.py").resolve()),
    }


def _load_cached_summary(output_root: Path, task_id: str, expected_key: dict) -> dict | None:
    summary_path = output_root / task_id / "summary.json"
    if not summary_path.exists():
        return None
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if summary.get("_h_cache_key") != expected_key:
        return None
    summary["_cache_hit"] = True
    return summary


def run_task(
    task_id: str,
    anchor_root: Path,
    output_root: Path,
    generated_root: Path,
    timeout_s: int,
    early_stop_pass: bool,
    resume: bool,
    report_only: bool,
) -> dict:
    resolved = _resolve_task(task_id, anchor_root)
    cache_key = _h_cache_key(
        resolved=resolved,
        timeout_s=timeout_s,
        early_stop_pass=early_stop_pass,
        report_only=report_only,
    )
    if resume:
        cached = _load_cached_summary(output_root, task_id, cache_key)
        if cached is not None:
            return cached

    task_output = output_root / task_id
    task_generated = generated_root / task_id
    baseline_path = _copy_anchor(resolved, generated_root)
    baseline_result = _run_case_safe(
        resolved.task_dir,
        baseline_path,
        resolved.tb_path,
        task_output / "baseline",
        timeout_s,
        task_id,
    )
    _json_write(task_output / "baseline/result.json", baseline_result)

    failure_signature = _classify_failure(baseline_result)
    template_family, eligibility_reason, candidates = _eligible_candidates(resolved, failure_signature)
    attempts: list[dict] = []
    best = {
        "variant": "baseline",
        "dut_path": str(baseline_path),
        "result": baseline_result,
        "rank": _rank(baseline_result),
    }

    if report_only:
        candidates = []

    for idx, candidate in enumerate(candidates, start=1):
        variant_name = f"{idx:02d}_{_safe_name(candidate.name)}"
        variant_dir = task_generated / variant_name
        variant_dir.mkdir(parents=True, exist_ok=True)
        dut_path = variant_dir / candidate.file_name
        dut_path.write_text(candidate.body, encoding="utf-8")

        result = _run_case_safe(
            resolved.task_dir,
            dut_path,
            resolved.tb_path,
            task_output / variant_name,
            timeout_s,
            task_id,
        )
        _json_write(task_output / variant_name / "result.json", result)
        rank = _rank(result)
        attempts.append(
            {
                "idx": idx,
                "variant": candidate.name,
                "description": candidate.description,
                "status": result.get("status"),
                "scores": result.get("scores"),
                "notes": result.get("notes"),
                "rank": list(rank),
                "dut_path": str(dut_path),
                "result_path": str(task_output / variant_name / "result.json"),
            }
        )
        print(f"[H] {task_id} {variant_name}: {result.get('status')} rank={rank}")
        if rank > best["rank"]:
            best = {
                "variant": candidate.name,
                "dut_path": str(dut_path),
                "result": result,
                "rank": rank,
            }
        if early_stop_pass and result.get("status") == "PASS":
            break

    summary = {
        "task_id": task_id,
        "task_dir": str(resolved.task_dir),
        "tb_path": str(resolved.tb_path),
        "anchor_path": str(resolved.anchor_path),
        "anchor_signature": {
            "module": resolved.module_name,
            "ports": list(resolved.ports),
        },
        "baseline": {
            "status": baseline_result.get("status"),
            "scores": baseline_result.get("scores"),
            "notes": baseline_result.get("notes"),
            "rank": list(_rank(baseline_result)),
        },
        "failure_signature": failure_signature,
        "template_family": template_family,
        "eligibility_reason": eligibility_reason,
        "report_only": report_only,
        "candidate_count": len(candidates),
        "attempts": attempts,
        "best_variant": best["variant"],
        "best_dut_path": best["dut_path"],
        "best_status": best["result"].get("status"),
        "best_scores": best["result"].get("scores"),
        "best_notes": best["result"].get("notes"),
        "best_rank": list(best["rank"]),
        "rescued": baseline_result.get("status") != "PASS" and best["result"].get("status") == "PASS",
        "_h_cache_key": cache_key,
    }
    _json_write(task_output / "summary.json", summary)
    return summary


def _tasks_from_g_failures(g_result_root: Path) -> list[str]:
    task_ids: list[str] = []
    for result_path in sorted(g_result_root.glob("*/result.json")):
        data = json.loads(result_path.read_text(encoding="utf-8"))
        if data.get("status") != "PASS":
            task_ids.append(result_path.parent.name)
    return task_ids


def run(args: argparse.Namespace) -> dict:
    anchor_root = Path(args.anchor_root).resolve()
    output_root = Path(args.output_root).resolve()
    generated_root = Path(args.generated_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    generated_root.mkdir(parents=True, exist_ok=True)

    if args.tasks:
        task_ids = args.tasks
    else:
        task_ids = _tasks_from_g_failures(Path(args.g_result_root).resolve())

    def _run_one(task_id: str) -> dict:
        try:
            return run_task(
                task_id,
                anchor_root,
                output_root,
                generated_root,
                args.timeout_s,
                early_stop_pass=not args.no_early_stop_pass,
                resume=args.resume,
                report_only=args.report_only,
            )
        except Exception as exc:  # noqa: BLE001 - keep long experiment batches auditable.
            failed_summary = {
                "task_id": task_id,
                "error": type(exc).__name__,
                "message": str(exc),
                "rescued": False,
            }
            _json_write(output_root / task_id / "summary.json", failed_summary)
            return failed_summary

    summaries: list[dict] = []
    worker_count = max(1, min(args.workers, len(task_ids)))
    if worker_count == 1:
        for task_id in task_ids:
            summary = _run_one(task_id)
            summaries.append(summary)
            print(
                f"[H] {task_id}: family={summary.get('template_family')} "
                f"base={summary.get('baseline', {}).get('status')} "
                f"best={summary.get('best_status')} rescued={summary.get('rescued')}"
                f"{' cached' if summary.get('_cache_hit') else ''}"
            )
    else:
        print(f"[H] parallel dispatch with {worker_count} workers")
        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_to_task = {executor.submit(_run_one, task_id): task_id for task_id in task_ids}
            for future in concurrent.futures.as_completed(future_to_task):
                task_id = future_to_task[future]
                summary = future.result()
                summaries.append(summary)
                print(
                    f"[H] {task_id}: family={summary.get('template_family')} "
                    f"base={summary.get('baseline', {}).get('status')} "
                    f"best={summary.get('best_status')} rescued={summary.get('rescued')}"
                    f"{' cached' if summary.get('_cache_hit') else ''}"
                )

    total = len(summaries)
    eligible = sum(1 for item in summaries if item.get("template_family"))
    rescued = sum(1 for item in summaries if item.get("rescued"))
    best_pass = sum(1 for item in summaries if item.get("best_status") == "PASS")
    unsupported = sum(1 for item in summaries if not item.get("template_family"))
    aggregate = {
        "mode": "signature_guided_H",
        "definition": "G + EVAS failure-signature + module/interface-signature gated template search",
        "g_result_root": str(Path(args.g_result_root).resolve()) if args.g_result_root else None,
        "anchor_root": str(anchor_root),
        "output_root": str(output_root),
        "generated_root": str(generated_root),
        "timeout_s": args.timeout_s,
        "workers": worker_count,
        "early_stop_pass": not args.no_early_stop_pass,
        "resume": args.resume,
        "report_only": args.report_only,
        "task_count": total,
        "eligible_count": eligible,
        "rescued_count": rescued,
        "unsupported_count": unsupported,
        "best_pass_count": best_pass,
        "summaries": summaries,
    }
    _json_write(output_root / "summary.json", aggregate)
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser(description="Run signature-guided H-condition EVAS repair.")
    parser.add_argument("--g-result-root", default="results/evas-scoring-condition-G-kimi-k2.5-full86-2026-04-25-overnight-kimi")
    parser.add_argument("--anchor-root", default="generated-table2-evas-guided-repair-3round-skill/kimi-k2.5")
    parser.add_argument("--output-root", default="results/signature-guided-H-kimi-G")
    parser.add_argument("--generated-root", default="generated-signature-guided-H-kimi-G")
    parser.add_argument("--timeout-s", type=int, default=180)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--no-early-stop-pass", action="store_true")
    parser.add_argument("--tasks", nargs="*", help="Optional task ids. Default: all G failures.")
    args = parser.parse_args()
    aggregate = run(args)
    print(
        "[H] summary: "
        f"tasks={aggregate['task_count']} eligible={aggregate['eligible_count']} "
        f"rescued={aggregate['rescued_count']} unsupported={aggregate['unsupported_count']} "
        f"best_pass={aggregate['best_pass_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
