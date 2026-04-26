#!/usr/bin/env python3
"""Materialize condition-H formal artifacts.

The signature-guided H runner validates repaired DUTs with the benchmark
gold/reference harness.  To measure formal end-to-end impact, this script
creates a normal generated-artifact tree:

1. copy the selected best round from a base condition such as F or G;
2. replace only the DUT file for H strict rescues;
3. keep the base generated testbench/harness intact;
4. score the resulting tree with ``score.py``.

This keeps H's DUT-side evidence separate from full formal scoring while making
the transfer test reproducible.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from score import ALL_FAMILIES, list_all_task_dirs, read_meta


ROOT = Path(__file__).resolve().parents[1]


def _json_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _base_result_path(base_score_root: Path, model: str, task_id: str) -> Path | None:
    candidates = [
        base_score_root / model / task_id / "result.json",
        base_score_root / task_id / "result.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _selected_round(base_score_root: Path, model: str, task_id: str) -> str:
    result_path = _base_result_path(base_score_root, model, task_id)
    if result_path is None:
        return "sample_0"
    try:
        return str(_load_json(result_path).get("round") or "sample_0")
    except Exception:
        return "sample_0"


def _h_summary_path(h_summary_root: Path, task_id: str) -> Path:
    return h_summary_root / task_id / "summary.json"


def _load_h_summary(h_summary_root: Path, task_id: str) -> dict | None:
    path = _h_summary_path(h_summary_root, task_id)
    if not path.exists():
        return None
    try:
        return _load_json(path)
    except Exception:
        return None


def _should_apply_h(summary: dict | None, policy: str) -> bool:
    if not summary:
        return False
    if policy == "rescued":
        return bool(summary.get("rescued")) and summary.get("best_status") == "PASS"
    if policy == "best-pass":
        return summary.get("best_status") == "PASS" and summary.get("best_variant") != "baseline"
    raise ValueError(f"unknown policy: {policy}")


def _copy_sample_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _replace_dut(sample_dir: Path, best_dut_path: Path) -> Path:
    target = sample_dir / best_dut_path.name
    if not target.exists():
        va_files = sorted(sample_dir.glob("*.va"))
        if len(va_files) == 1:
            target = va_files[0]
        else:
            target = sample_dir / best_dut_path.name
    shutil.copy2(best_dut_path, target)
    return target


_TIME_UNITS = {
    "f": 1e-15,
    "p": 1e-12,
    "n": 1e-9,
    "u": 1e-6,
    "m": 1e-3,
    "": 1.0,
}


def _parse_time_s(token: str) -> float | None:
    match = re.fullmatch(r"\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)\s*([fpnum]?)s?\s*", token, re.I)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2).lower()
    return value * _TIME_UNITS.get(unit, 1.0)


def _format_time_s(value_s: float) -> str:
    for suffix, scale in (("u", 1e-6), ("n", 1e-9), ("p", 1e-12)):
        scaled = value_s / scale
        if 1 <= scaled < 1000:
            return f"{scaled:.6g}{suffix}"
    return f"{value_s:.6g}"


def _extract_assignment(text: str, key: str) -> str | None:
    match = re.search(rf"\b{re.escape(key)}\s*=\s*([^\s\]]+)", text, flags=re.I)
    return match.group(1) if match else None


def _merge_alter_vsource_lines(text: str) -> tuple[str, list[str]]:
    """Inline simple Spectre ``alter`` source-waveform statements.

    Several LLM-generated testbenches create a DC vsource and later write
    ``alter SRC type=pwl`` or ``alter SRC type=pulse``.  EVAS currently treats
    the original DC source as the effective stimulus, so the checker observes a
    flat CSV.  This rewrite is intentionally narrow: it only rewrites source
    instances that already exist in the same testbench and removes the matched
    alter lines.
    """
    lines = text.splitlines()
    alter_params: dict[str, str] = {}
    rewritten: list[str] = []
    repairs: list[str] = []

    for line in lines:
        match = re.match(r"\s*alter\s+([A-Za-z_][\w.]*)\s+(.+?)\s*$", line, flags=re.I)
        if match:
            alter_params[match.group(1)] = match.group(2).strip()
        else:
            rewritten.append(line)

    if not alter_params:
        return text, repairs

    final_lines: list[str] = []
    consumed: set[str] = set()
    for line in rewritten:
        match = re.match(r"^(\s*)([A-Za-z_][\w.]*)\s+(.+?\bvsource\b)(.*)$", line, flags=re.I)
        if not match:
            final_lines.append(line)
            continue
        indent, source_name, prefix, tail = match.groups()
        params = alter_params.get(source_name)
        if not params:
            final_lines.append(line)
            continue
        final_lines.append(f"{indent}{source_name} {prefix} {params}")
        consumed.add(source_name)
        repairs.append(f"inline_alter_source={source_name}")

    for source_name in sorted(set(alter_params) - consumed):
        repairs.append(f"unmatched_alter_source={source_name}")

    return "\n".join(final_lines) + ("\n" if text.endswith("\n") else ""), repairs


def _ensure_pulse_edge_budget(text: str, min_pulse_edges: int) -> tuple[str, list[str]]:
    """Extend short pulse-driven simulations enough for edge-count checkers."""
    if min_pulse_edges <= 0:
        return text, []
    period_tokens = re.findall(r"\bperiod\s*=\s*([^\s\]]+)", text, flags=re.I)
    periods = [value for value in (_parse_time_s(token) for token in period_tokens) if value and value > 0]
    if not periods:
        return text, []
    period_s = min(periods)

    stop_match = re.search(r"(?m)^(\s*tran\s+\S+.*?\bstop\s*=\s*)([^\s]+)(.*)$", text, flags=re.I)
    if not stop_match:
        return text, []
    old_stop_s = _parse_time_s(stop_match.group(2))
    if old_stop_s is None:
        return text, []

    required_stop_s = period_s * (min_pulse_edges + 1)
    if old_stop_s >= required_stop_s:
        return text, []

    new_stop = _format_time_s(required_stop_s)
    updated = (
        text[: stop_match.start()]
        + f"{stop_match.group(1)}{new_stop}{stop_match.group(3)}"
        + text[stop_match.end() :]
    )
    return updated, [f"extend_tran_stop={stop_match.group(2)}->{new_stop}"]


def _rewrite_verilog_style_instances(text: str) -> tuple[str, list[str]]:
    """Rewrite simple ``module inst (...)`` lines into Spectre instance syntax."""
    modules = {
        Path(match).stem
        for match in re.findall(r'(?m)^\s*ahdl_include\s+"([^"]+\.va)"', text, flags=re.I)
    }
    if not modules:
        return text, []

    repairs: list[str] = []
    updated_lines: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^(\s*)([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*\(([^)]*)\)(.*)$", line)
        if not match or match.group(2) not in modules:
            updated_lines.append(line)
            continue
        indent, module_name, inst_name, nodes, tail = match.groups()
        updated_lines.append(f"{indent}{inst_name} ({nodes.strip()}) {module_name}{tail}")
        repairs.append(f"rewrite_instance_syntax={module_name}:{inst_name}")

    return "\n".join(updated_lines) + ("\n" if text.endswith("\n") else ""), repairs


def _needs_edge_budget_repair(notes_text: str) -> bool:
    lowered = notes_text.lower()
    return any(
        key in lowered
        for key in (
            "too_few_edges",
            "too_few_rising_edges",
            "too_few_data_edges",
            "not_enough_clk_edges",
            "insufficient_post_reset_samples",
            "clk_edges=",
        )
    )


def _repair_generated_tb(sample_dir: Path, min_pulse_edges: int, notes_text: str) -> list[str]:
    tb_files = sorted(sample_dir.glob("tb_*.scs")) or sorted(sample_dir.glob("*.scs"))
    if not tb_files:
        return ["tb_repair_skipped=no_testbench"]
    if len(tb_files) > 1:
        return [f"tb_repair_skipped=ambiguous_testbench:{','.join(path.name for path in tb_files)}"]

    tb_path = tb_files[0]
    original = tb_path.read_text(encoding="utf-8", errors="ignore")
    updated, repairs = _merge_alter_vsource_lines(original)
    updated, instance_repairs = _rewrite_verilog_style_instances(updated)
    repairs.extend(instance_repairs)
    if _needs_edge_budget_repair(notes_text):
        updated, edge_repairs = _ensure_pulse_edge_budget(updated, min_pulse_edges)
        repairs.extend(edge_repairs)
    if updated != original:
        tb_path.write_text(updated, encoding="utf-8")
    return repairs


def materialize_task(
    *,
    task_id: str,
    task_dir: Path,
    model: str,
    base_generated_root: Path,
    base_score_root: Path,
    h_summary_root: Path,
    output_generated_root: Path,
    apply_policy: str,
    tb_repair_scope: str,
    min_pulse_edges: int,
) -> dict:
    round_name = _selected_round(base_score_root, model, task_id)
    src_sample = base_generated_root / model / task_id / round_name
    dst_sample = output_generated_root / model / task_id / "sample_0"
    meta = read_meta(task_dir)

    record: dict = {
        "task_id": task_id,
        "family": meta.get("family", "unknown"),
        "base_round": round_name,
        "base_sample_dir": str(src_sample),
        "output_sample_dir": str(dst_sample),
        "h_applied": False,
        "h_reason": "not_eligible_or_not_rescued",
        "tb_repairs": [],
    }
    base_result = _load_json(_base_result_path(base_score_root, model, task_id)) if _base_result_path(base_score_root, model, task_id) else {}
    base_notes = base_result.get("evas_notes") or base_result.get("notes") or []
    if isinstance(base_notes, str):
        base_notes_text = base_notes
    else:
        base_notes_text = "\n".join(str(note) for note in base_notes)

    if not src_sample.is_dir():
        record["h_reason"] = "missing_base_sample"
        dst_sample.mkdir(parents=True, exist_ok=True)
        _json_write(dst_sample / "h_materialization.json", record)
        return record

    _copy_sample_tree(src_sample, dst_sample)

    summary = _load_h_summary(h_summary_root, task_id)
    if _should_apply_h(summary, apply_policy):
        best_dut = Path(str(summary.get("best_dut_path", "")))
        if best_dut.exists():
            replaced = _replace_dut(dst_sample, best_dut)
            record.update(
                {
                    "h_applied": True,
                    "h_reason": "strict_rescue_applied" if summary.get("rescued") else "best_pass_applied",
                    "h_template_family": summary.get("template_family"),
                    "h_failure_signature": summary.get("failure_signature"),
                    "h_best_variant": summary.get("best_variant"),
                    "h_best_dut_path": str(best_dut),
                    "replaced_dut_path": str(replaced),
                }
            )
        else:
            record["h_reason"] = "missing_h_best_dut"

    should_repair_tb = tb_repair_scope == "all" or (tb_repair_scope == "h-applied" and record["h_applied"])
    if should_repair_tb:
        record["tb_repairs"] = _repair_generated_tb(dst_sample, min_pulse_edges, base_notes_text)

    _json_write(dst_sample / "h_materialization.json", record)
    return record


def run(args: argparse.Namespace) -> dict:
    model = args.model
    base_generated_root = Path(args.base_generated_root).resolve()
    base_score_root = Path(args.base_score_root).resolve()
    h_summary_root = Path(args.h_summary_root).resolve()
    output_generated_root = Path(args.output_generated_root).resolve()

    selected = set(args.task or [])
    families = tuple(args.family) if args.family else ALL_FAMILIES
    task_items = list_all_task_dirs(families=families, selected=selected or None)

    records = [
        materialize_task(
            task_id=task_id,
            task_dir=task_dir,
            model=model,
            base_generated_root=base_generated_root,
            base_score_root=base_score_root,
            h_summary_root=h_summary_root,
            output_generated_root=output_generated_root,
            apply_policy=args.apply_policy,
            tb_repair_scope=args.tb_repair_scope,
            min_pulse_edges=args.min_pulse_edges,
        )
        for task_id, task_dir in task_items
    ]

    aggregate = {
        "mode": "condition_H_formal_materialization",
        "definition": "base best-round artifacts plus H repaired DUT replacements",
        "model": model,
        "base_generated_root": str(base_generated_root),
        "base_score_root": str(base_score_root),
        "h_summary_root": str(h_summary_root),
        "output_generated_root": str(output_generated_root),
        "apply_policy": args.apply_policy,
        "tb_repair_scope": args.tb_repair_scope,
        "min_pulse_edges": args.min_pulse_edges,
        "task_count": len(records),
        "h_applied_count": sum(1 for record in records if record.get("h_applied")),
        "tb_repaired_count": sum(
            1
            for record in records
            if any(
                not str(item).startswith(("tb_repair_skipped=", "unmatched_alter_source="))
                for item in record.get("tb_repairs", [])
            )
        ),
        "h_applied_tasks": [record["task_id"] for record in records if record.get("h_applied")],
        "records": records,
    }
    _json_write(output_generated_root / model / "condition_h_materialization.json", aggregate)
    print(
        f"[materialize-H] tasks={aggregate['task_count']} "
        f"h_applied={aggregate['h_applied_count']} -> {output_generated_root / model}"
    )
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize condition-H formal generated artifacts.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-generated-root", required=True)
    parser.add_argument("--base-score-root", required=True)
    parser.add_argument("--h-summary-root", required=True)
    parser.add_argument("--output-generated-root", required=True)
    parser.add_argument("--apply-policy", choices=("rescued", "best-pass"), default="rescued")
    parser.add_argument(
        "--tb-repair-scope",
        choices=("none", "h-applied", "all"),
        default="none",
        help="Optionally apply safe generated-testbench stimulus repair for H2-style transfer tests.",
    )
    parser.add_argument(
        "--min-pulse-edges",
        type=int,
        default=24,
        help="Minimum pulse periods to preserve when extending short transient analyses.",
    )
    parser.add_argument("--task", action="append")
    parser.add_argument("--family", action="append", choices=ALL_FAMILIES)
    args = parser.parse_args()
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
