#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from build_repair_prompt import (
    _checker_expectation_bundle,
    _extract_metrics_from_notes,
    _metric_candidate_keys,
    _threshold_spec,
)
from diagnosis_translation import translate_diagnosis
from generate import build_prompt, extract_module_signature, read_meta
from score import ALL_FAMILIES, choose_gold_tb, list_all_task_dirs
from simulate_evas import CHECKS

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _result_path(results_dir: Path, task_id: str) -> Path:
    return results_dir / task_id / "result.json"


def _score(result: dict, axis: str) -> float:
    try:
        return float(result.get("scores", {}).get(axis, 0.0))
    except (TypeError, ValueError):
        return 0.0


def _weighted(result: dict) -> float:
    return _score(result, "weighted_total")


def _resolve_path(raw: str | None) -> Path | None:
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    return path


def _numeric_gap(actual: float, spec: dict) -> float | None:
    target = spec.get("expected")
    tolerance = spec.get("tolerance")
    if isinstance(target, (int, float)) and isinstance(tolerance, (int, float)):
        raw = max(0.0, abs(actual - float(target)) - float(tolerance))
        return raw / max(abs(float(target)), abs(float(tolerance)), 1.0)
    if isinstance(target, str):
        parsed = _threshold_spec(target)
        if not parsed:
            return None
        op, threshold = parsed
        threshold = float(threshold)
        if op == ">=":
            raw = max(0.0, threshold - actual)
        elif op == ">":
            raw = max(0.0, threshold - actual)
        elif op == "<=":
            raw = max(0.0, actual - threshold)
        else:
            raw = max(0.0, actual - threshold)
        return raw / max(abs(threshold), 1.0)
    return None


def metric_gap_score(task_dir: Path, result: dict) -> dict:
    notes = result.get("evas_notes", [])
    metrics = _extract_metrics_from_notes(notes)
    bundle = _checker_expectation_bundle(task_dir)
    expected = bundle.get("expected_conditions", {})
    aliases = bundle.get("metric_aliases", {})

    matched = 0
    violated = 0
    gap_sum = 0.0
    details: list[str] = []
    for metric_name, spec in expected.items():
        keys = _metric_candidate_keys(metric_name, metrics, aliases)
        if not keys:
            continue
        for key in keys:
            value = metrics.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            gap = _numeric_gap(float(value), spec)
            if gap is None:
                continue
            matched += 1
            gap_sum += gap
            if gap > 0:
                violated += 1
                observed = f"{metric_name}={float(value):.4g}"
                if key != metric_name:
                    observed += f" (as {key})"
                details.append(f"{observed}, gap={gap:.4g}")
            break

    return {
        "matched": matched,
        "violated": violated,
        "gap_sum": round(gap_sum, 6),
        "details": details[:5],
    }


def classify_failure(task_id: str, result: dict) -> dict:
    status = result.get("status")
    if status == "PASS":
        return {
            "failure_type": "pass",
            "matched_rule": "PASS",
            "matched_keys": [],
            "diagnosis": "PASS",
        }
    if status == "FAIL_DUT_COMPILE":
        return {
            "failure_type": "dut_compile",
            "matched_rule": "DUT_COMPILE",
            "matched_keys": [],
            "diagnosis": "DUT compile failure",
        }
    if status == "FAIL_TB_COMPILE":
        return {
            "failure_type": "tb_compile",
            "matched_rule": "TB_COMPILE",
            "matched_keys": [],
            "diagnosis": "Testbench compile failure",
        }
    notes = result.get("evas_notes") or []
    for note in notes:
        translated = translate_diagnosis(str(note), task_id=task_id)
        if not translated.get("diagnosis"):
            continue
        return {
            "failure_type": translated.get("failure_type", "unknown"),
            "matched_rule": translated.get("matched_rule", "UNKNOWN"),
            "matched_keys": translated.get("matched_keys", []),
            "diagnosis": translated.get("diagnosis", ""),
        }
    return {
        "failure_type": "unknown",
        "matched_rule": "NO_DIAGNOSIS",
        "matched_keys": [],
        "diagnosis": "No EVAS diagnosis note",
    }


def _generation_meta(generated_root: Path | None, model: str | None, task_id: str) -> dict:
    if not generated_root or not model:
        return {}
    path = generated_root / model / task_id / "sample_0" / "generation_meta.json"
    if not path.exists():
        return {}
    try:
        return _read_json(path)
    except (json.JSONDecodeError, OSError):
        return {}


def _round_result(rounds_root: Path | None, round_num: int, task_id: str) -> dict | None:
    if not rounds_root:
        return None
    path = rounds_root / f"round{round_num}" / task_id / "result.json"
    if not path.exists():
        return None
    try:
        return _read_json(path)
    except (json.JSONDecodeError, OSError):
        return None


def loop_trace(task_id: str, generated_root: Path | None, rounds_root: Path | None, model: str | None) -> dict:
    meta = _generation_meta(generated_root, model, task_id)
    history = list(meta.get("history") or [])
    round_scores = []
    for item in history:
        round_num = item.get("round")
        try:
            round_num = int(round_num)
        except (TypeError, ValueError):
            continue
        round_result = _round_result(rounds_root, round_num, task_id)
        round_scores.append(
            {
                "round": round_num,
                "status": item.get("status") or (round_result or {}).get("status"),
                "progress_label": item.get("progress_label", "-"),
                "weighted_total": item.get("weighted_total")
                if item.get("weighted_total") is not None
                else _weighted(round_result or {}),
            }
        )

    labels = [str(r.get("progress_label", "-")) for r in round_scores]
    weights = [
        float(r["weighted_total"])
        for r in round_scores
        if isinstance(r.get("weighted_total"), (int, float))
    ]
    ever_improved = any(label == "improved" for label in labels)
    if len(weights) >= 2:
        ever_improved = ever_improved or max(weights[1:]) > weights[0]

    return {
        "selected_round": meta.get("selected_round_label") or meta.get("selected_round") or "-",
        "best_status": meta.get("best_status", "-"),
        "round_completed": meta.get("round_completed", "-"),
        "ever_improved": ever_improved,
        "progress_labels": labels,
        "history": round_scores,
    }


def _task_family(task_dir: Path) -> str:
    try:
        rel = task_dir.relative_to(ROOT / "tasks")
        return rel.parts[0] if rel.parts else "-"
    except ValueError:
        return "-"


def next_action(row: dict) -> str:
    failure_type = row.get("failure_type")
    if failure_type == "observability_contract":
        return "fix save/observable contract before behavior repair"
    if failure_type in {"dut_compile", "tb_compile"}:
        return "fix syntax/netlist compile path first"
    if failure_type == "simulation_artifact":
        return "stabilize tran/run artifact before semantic tuning"
    if failure_type == "behavior_semantic" and row.get("matched_metrics", 0):
        return "add metric-specific repair guidance and preserve interface"
    if failure_type == "behavior_semantic":
        return "improve checker-to-repair diagnosis mapping"
    return "inspect raw EVAS notes"


def priority_score(row: dict) -> float:
    if row["new_status"] == "PASS":
        return -1.0
    base = {
        "observability_contract": 100.0,
        "behavior_semantic": 90.0,
        "dut_compile": 80.0,
        "tb_compile": 75.0,
        "simulation_artifact": 60.0,
        "unknown": 40.0,
    }.get(row.get("failure_type"), 50.0)
    if row.get("progress") in {"unchanged", "axis_regressed", "metric_gap_regressed"}:
        base += 10.0
    if row.get("matched_metrics", 0):
        base += 5.0
    return base + min(float(row.get("new_gap") or 0.0), 10.0)


def classify_progress(old: dict, new: dict, old_gap: dict, new_gap: dict) -> str:
    if new.get("status") == "PASS" and old.get("status") != "PASS":
        return "pass_reached"
    if _weighted(new) > _weighted(old):
        return "axis_improved"
    if _weighted(new) < _weighted(old):
        return "axis_regressed"
    old_matched = int(old_gap.get("matched", 0))
    new_matched = int(new_gap.get("matched", 0))
    if old_matched and new_matched:
        if float(new_gap["gap_sum"]) < float(old_gap["gap_sum"]):
            return "metric_gap_improved"
        if float(new_gap["gap_sum"]) > float(old_gap["gap_sum"]):
            return "metric_gap_regressed"
    return "unchanged"


def _module_sigs(gold_dir: Path) -> list[tuple[str, list[str], str]]:
    sigs = []
    seen = set()
    for va in sorted(gold_dir.glob("*.va")):
        sig = extract_module_signature(va)
        if sig and sig[0] not in seen:
            sigs.append((sig[0], sig[1], va.name))
            seen.add(sig[0])
    return sigs


def _save_signals(tb_path: Path | None) -> list[str]:
    if not tb_path or not tb_path.exists():
        return []
    text = tb_path.read_text(encoding="utf-8", errors="ignore")
    logical_lines: list[str] = []
    current = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if current:
            current += " " + line.rstrip("\\").strip()
        else:
            current = line.rstrip("\\").strip()
        if not line.endswith("\\"):
            logical_lines.append(current)
            current = ""
    if current:
        logical_lines.append(current)

    signals: list[str] = []
    seen = set()
    for line in logical_lines:
        if not line.lower().startswith("save "):
            continue
        for token in line.split()[1:]:
            if token.lower() == "all":
                continue
            match = re.match(r"v\s*\(\s*([^)]+)\s*\)", token, re.IGNORECASE)
            signal = match.group(1) if match else token
            signal = signal.strip()
            if signal and signal not in seen:
                signals.append(signal)
                seen.add(signal)
    return signals


def _tran_lines(tb_path: Path | None) -> list[str]:
    if not tb_path or not tb_path.exists():
        return []
    lines = []
    for line in tb_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if re.search(r"\btran\b", line):
            lines.append(line.strip())
    return lines


def _prompt_mentions(text: str, items: list[str]) -> list[str]:
    found = []
    lowered = text.lower()
    for item in items:
        if item and item.lower() in lowered:
            found.append(item)
    return sorted(set(found))


def _compact(items: list[str], limit: int = 4) -> str:
    if not items:
        return "-"
    shown = items[:limit]
    suffix = f" (+{len(items) - limit})" if len(items) > limit else ""
    return ", ".join(shown) + suffix


def contract_row(task_id: str, task_dir: Path) -> dict:
    prompt_text = (task_dir / "prompt.md").read_text(encoding="utf-8", errors="ignore")
    actual_prompt = build_prompt(task_dir, include_checker=True, include_skill=False)
    gold_dir = task_dir / "gold"
    gold_tb = choose_gold_tb(gold_dir)
    modules = _module_sigs(gold_dir)
    module_names = [m for m, _, _ in modules]
    port_tokens = [p for _, ports, _ in modules for p in ports]
    save_tokens = _save_signals(gold_tb)
    tran = _tran_lines(gold_tb)
    checker = CHECKS.get(task_id)
    checker_name = checker.__name__ if checker else "-"

    original_mentions = {
        "module": _prompt_mentions(prompt_text, module_names),
        "ports": _prompt_mentions(prompt_text, port_tokens),
        "save": _prompt_mentions(prompt_text, save_tokens),
        "tran": [line for line in tran if line in prompt_text],
        "checker": [checker_name] if checker_name in prompt_text else [],
    }
    actual_mentions = {
        "module": _prompt_mentions(actual_prompt, module_names),
        "ports": _prompt_mentions(actual_prompt, port_tokens),
        "save": _prompt_mentions(actual_prompt, save_tokens),
        "tran": [line for line in tran if line in actual_prompt],
        "checker": [checker_name] if checker_name in actual_prompt else [],
    }

    risk = []
    if module_names and not original_mentions["module"]:
        risk.append("original_prompt_missing_exact_module")
    if save_tokens and len(original_mentions["save"]) < len(save_tokens):
        risk.append("original_prompt_partial_save_contract")
    if tran and not original_mentions["tran"]:
        risk.append("original_prompt_missing_exact_tran")
    if checker_name != "-" and not original_mentions["checker"]:
        risk.append("original_prompt_no_checker_source")

    return {
        "task": task_id,
        "gold_modules": _compact(module_names),
        "gold_ports": _compact(port_tokens, 6),
        "gold_save": _compact(save_tokens, 6),
        "gold_tran": _compact(tran, 2),
        "checker": checker_name,
        "original_prompt_mentions": (
            f"module:{len(original_mentions['module'])}/{len(module_names)}; "
            f"ports:{len(original_mentions['ports'])}/{len(set(port_tokens))}; "
            f"save:{len(original_mentions['save'])}/{len(set(save_tokens))}; "
            f"tran:{len(original_mentions['tran'])}/{len(tran)}; "
            f"checker:{len(original_mentions['checker'])}/1"
        ),
        "actual_prompt_mentions": (
            f"module:{len(actual_mentions['module'])}/{len(module_names)}; "
            f"ports:{len(actual_mentions['ports'])}/{len(set(port_tokens))}; "
            f"save:{len(actual_mentions['save'])}/{len(set(save_tokens))}; "
            f"tran:{len(actual_mentions['tran'])}/{len(tran)}; "
            f"checker:{len(actual_mentions['checker'])}/1"
        ),
        "risk": _compact(risk, 4),
    }


def _markdown_table(rows: list[dict], columns: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        vals = [str(row.get(col, "-")).replace("\n", " ").replace("|", "\\|") for col in columns]
        lines.append("| " + " | ".join(vals) + " |")
    return lines


def build_report(args: argparse.Namespace) -> tuple[dict, str]:
    old_dir = _resolve_path(args.old_results)
    new_dir = _resolve_path(args.new_results)
    generated_root = _resolve_path(args.generated_root)
    rounds_root = _resolve_path(args.rounds_root)
    assert old_dir is not None
    assert new_dir is not None

    tasks = sorted(p.parent.name for p in new_dir.glob("*/result.json"))
    task_dirs = {
        task_id: task_dir
        for task_id, task_dir in list_all_task_dirs(families=ALL_FAMILIES, selected=set(tasks))
    }

    per_task = []
    for task_id in tasks:
        if task_id not in task_dirs:
            continue
        old = _read_json(_result_path(old_dir, task_id))
        new = _read_json(_result_path(new_dir, task_id))
        task_dir = task_dirs[task_id]
        old_gap = metric_gap_score(task_dir, old)
        new_gap = metric_gap_score(task_dir, new)
        failure = classify_failure(task_id, new)
        trace = loop_trace(task_id, generated_root, rounds_root, args.model)
        per_task.append(
            {
                "task": task_id,
                "family": _task_family(task_dir),
                "old_status": old.get("status"),
                "new_status": new.get("status"),
                "old_total": _weighted(old),
                "new_total": _weighted(new),
                "old_axes": f"{_score(old, 'dut_compile'):.0f}/{_score(old, 'tb_compile'):.0f}/{_score(old, 'sim_correct'):.0f}",
                "new_axes": f"{_score(new, 'dut_compile'):.0f}/{_score(new, 'tb_compile'):.0f}/{_score(new, 'sim_correct'):.0f}",
                "old_gap": old_gap["gap_sum"],
                "new_gap": new_gap["gap_sum"],
                "matched_metrics": new_gap["matched"],
                "progress": classify_progress(old, new, old_gap, new_gap),
                "failure_type": failure["failure_type"],
                "matched_rule": failure["matched_rule"],
                "selected_round": trace["selected_round"],
                "best_status": trace["best_status"],
                "round_completed": trace["round_completed"],
                "ever_improved": trace["ever_improved"],
                "loop_progress_labels": ",".join(trace["progress_labels"]) or "-",
                "loop_history": trace["history"],
                "new_gap_details": "; ".join(new_gap["details"]) or "-",
            }
        )

    priority_rows = [
        {
            "task": row["task"],
            "family": row["family"],
            "status": row["new_status"],
            "failure_type": row["failure_type"],
            "matched_rule": row["matched_rule"],
            "new_total": row["new_total"],
            "new_gap": row["new_gap"],
            "matched_metrics": row["matched_metrics"],
            "progress": row["progress"],
            "selected_round": row["selected_round"],
            "ever_improved": row["ever_improved"],
            "priority_score": round(priority_score(row), 4),
            "next_action": next_action(row),
        }
        for row in per_task
        if row["new_status"] != "PASS"
    ]
    priority_rows.sort(key=lambda r: (-float(r["priority_score"]), r["task"]))

    summary = {
        "task_count": len(per_task),
        "old_status": dict(Counter(r["old_status"] for r in per_task)),
        "new_status": dict(Counter(r["new_status"] for r in per_task)),
        "progress": dict(Counter(r["progress"] for r in per_task)),
        "failure_type": dict(Counter(r["failure_type"] for r in per_task)),
        "matched_rule": dict(Counter(r["matched_rule"] for r in per_task)),
        "family": dict(Counter(r["family"] for r in per_task)),
        "selected_round": dict(Counter(str(r["selected_round"]) for r in per_task)),
        "ever_improved": sum(1 for r in per_task if r["ever_improved"]),
        "loop_progress_labels": dict(
            Counter(
                label
                for row in per_task
                for label in str(row["loop_progress_labels"]).split(",")
                if label and label != "-"
            )
        ),
        "old_pass": sum(1 for r in per_task if r["old_status"] == "PASS"),
        "new_pass": sum(1 for r in per_task if r["new_status"] == "PASS"),
        "old_avg_weighted": round(sum(r["old_total"] for r in per_task) / max(len(per_task), 1), 6),
        "new_avg_weighted": round(sum(r["new_total"] for r in per_task) / max(len(per_task), 1), 6),
        "old_axis_sums": {
            "dut_compile": sum(_score(_read_json(_result_path(old_dir, r["task"])), "dut_compile") for r in per_task),
            "tb_compile": sum(_score(_read_json(_result_path(old_dir, r["task"])), "tb_compile") for r in per_task),
            "sim_correct": sum(_score(_read_json(_result_path(old_dir, r["task"])), "sim_correct") for r in per_task),
        },
        "new_axis_sums": {
            "dut_compile": sum(_score(_read_json(_result_path(new_dir, r["task"])), "dut_compile") for r in per_task),
            "tb_compile": sum(_score(_read_json(_result_path(new_dir, r["task"])), "tb_compile") for r in per_task),
            "sim_correct": sum(_score(_read_json(_result_path(new_dir, r["task"])), "sim_correct") for r in per_task),
        },
    }

    contract_rows = [contract_row(task_id, task_dirs[task_id]) for task_id in tasks if task_id in task_dirs]
    contract_risks = Counter()
    for row in contract_rows:
        risk = row["risk"]
        if risk == "-":
            contract_risks["none"] += 1
        else:
            for item in [part.strip() for part in risk.split(",") if part.strip()]:
                contract_risks[item] += 1
    summary["contract_risk"] = dict(contract_risks)
    report = {
        "old_results": str(old_dir),
        "new_results": str(new_dir),
        "generated_root": str(generated_root) if generated_root else "",
        "rounds_root": str(rounds_root) if rounds_root else "",
        "model": args.model or "",
        "summary": summary,
        "per_task": per_task,
        "repair_priority_queue": priority_rows,
        "gold_prompt_contract": contract_rows,
    }

    md = [
        "# Hard34 Closeness Report",
        "",
        "## Summary",
        "",
        f"- Tasks: {summary['task_count']}",
        f"- PASS: {summary['old_pass']} -> {summary['new_pass']}",
        f"- Avg weighted_total: {summary['old_avg_weighted']:.4f} -> {summary['new_avg_weighted']:.4f}",
        f"- Progress classes: {summary['progress']}",
        f"- Failure types: {summary['failure_type']}",
        f"- Selected rounds: {summary['selected_round']}",
        f"- Ever improved in loop: {summary['ever_improved']}/{summary['task_count']}",
        f"- Contract risks: {summary['contract_risk']}",
        f"- Old status: {summary['old_status']}",
        f"- New status: {summary['new_status']}",
        "",
        "## Repair Priority Queue",
        "",
    ]
    md.extend(
        _markdown_table(
            priority_rows[:25],
            [
                "task",
                "family",
                "status",
                "failure_type",
                "matched_rule",
                "new_total",
                "new_gap",
                "matched_metrics",
                "progress",
                "selected_round",
                "ever_improved",
                "priority_score",
                "next_action",
            ],
        )
    )
    md.extend(
        [
            "",
            "## Per-Task Closeness",
            "",
        ]
    )
    md.extend(
        _markdown_table(
            per_task,
            [
                "task",
                "family",
                "old_status",
                "new_status",
                "old_total",
                "new_total",
                "old_axes",
                "new_axes",
                "old_gap",
                "new_gap",
                "matched_metrics",
                "progress",
                "failure_type",
                "matched_rule",
                "selected_round",
                "ever_improved",
            ],
        )
    )
    md.extend(["", "## Gold Prompt Contract Table", ""])
    md.extend(
        _markdown_table(
            contract_rows,
            [
                "task",
                "gold_modules",
                "gold_ports",
                "gold_save",
                "gold_tran",
                "checker",
                "original_prompt_mentions",
                "actual_prompt_mentions",
                "risk",
            ],
        )
    )
    return report, "\n".join(md) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare old/new EVAS results with closeness metrics.")
    ap.add_argument("--old-results", required=True)
    ap.add_argument("--new-results", required=True)
    ap.add_argument("--generated-root", default="")
    ap.add_argument("--rounds-root", default="")
    ap.add_argument("--model", default="")
    ap.add_argument("--output-dir", default="")
    ap.add_argument("--prefix", default="hard34-closeness")
    args = ap.parse_args()

    report, markdown = build_report(args)
    out_dir = Path(args.output_dir) if args.output_dir else ROOT / "results" / args.prefix
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{args.prefix}.json"
    md_path = out_dir / f"{args.prefix}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")

    summary = report["summary"]
    print(f"[closeness] tasks={summary['task_count']} pass={summary['old_pass']}->{summary['new_pass']}")
    print(f"[closeness] weighted={summary['old_avg_weighted']:.4f}->{summary['new_avg_weighted']:.4f}")
    print(f"[closeness] json={json_path}")
    print(f"[closeness] md={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
