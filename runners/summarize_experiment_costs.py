#!/usr/bin/env python3
"""Summarize generation token/time costs and optional validation outcomes."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _normalized_required_axes(required_axes: list[str] | None = None) -> list[str]:
    aliases = {
        "syntax": "dut_compile",
        "routing": "tb_compile",
        "simulation": "sim_correct",
        "behavior": "sim_correct",
    }
    axes = required_axes or ["dut_compile", "tb_compile", "sim_correct"]
    normalized: list[str] = []
    for axis in axes:
        mapped = aliases.get(axis, axis)
        if mapped not in normalized:
            normalized.append(mapped)
    return normalized or ["dut_compile", "tb_compile", "sim_correct"]


def _strict_result_status(data: dict[str, Any]) -> str:
    """Normalize legacy-axis PASS labels before table aggregation."""
    raw_status = str(data.get("status", ""))
    scores = data.get("scores") or {}
    axes = _normalized_required_axes(data.get("required_axes"))
    if raw_status == "FAIL_INFRA":
        return raw_status
    if "dut_compile" in axes and _num(scores.get("dut_compile")) < 1.0:
        return "FAIL_DUT_COMPILE"
    if "tb_compile" in axes and _num(scores.get("tb_compile")) < 1.0:
        return "FAIL_TB_COMPILE"
    if "sim_correct" in axes and _num(scores.get("sim_correct")) < 1.0:
        return "FAIL_SIM_CORRECTNESS"
    return "PASS" if raw_status else ""


def _load_bench_meta(bench_dir: Path | None) -> dict[str, dict[str, Any]]:
    if bench_dir is None:
        return {}
    task_root = bench_dir / "tasks"
    metas: dict[str, dict[str, Any]] = {}
    for meta_path in sorted(task_root.glob("*/meta.json")):
        meta = _read_json(meta_path)
        task_id = meta.get("task_id") or meta_path.parent.name
        metas[task_id] = meta
    return metas


def _sample_index(sample_name: str) -> int | None:
    if not sample_name.startswith("sample_"):
        return None
    try:
        return int(sample_name.split("_", 1)[1])
    except ValueError:
        return None


def _collect_generation_rows(
    generated_dir: Path,
    bench_meta: dict[str, dict[str, Any]],
    sample_idx: int | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for meta_path in sorted(generated_dir.glob("*/*/sample_*/generation_meta.json")):
        sample = _sample_index(meta_path.parent.name)
        if sample_idx is not None and sample != sample_idx:
            continue
        meta = _read_json(meta_path)
        task_id = meta.get("task_id") or meta_path.parent.parent.name
        task_meta = bench_meta.get(task_id, {})
        model_slug = meta.get("model_slug") or meta_path.parents[2].name
        model = meta.get("model") or model_slug
        input_tokens = int(_num(meta.get("input_tokens")))
        output_tokens = int(_num(meta.get("output_tokens")))
        row = {
            "model": model,
            "model_slug": model_slug,
            "task_id": task_id,
            "sample_idx": sample,
            "status": meta.get("status", ""),
            "finish_reason": meta.get("finish_reason", ""),
            "family": meta.get("family") or task_meta.get("family", ""),
            "source_collection": meta.get("source_collection") or task_meta.get("source_collection", ""),
            "task_form": meta.get("task_form") or task_meta.get("task_form", ""),
            "core_function": meta.get("core_function") or task_meta.get("core_function") or task_meta.get("category", ""),
            "benchmark_split": meta.get("benchmark_split") or task_meta.get("benchmark_split", ""),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "api_elapsed_s": round(_num(meta.get("api_elapsed_s")), 3),
            "task_elapsed_s": round(_num(meta.get("task_elapsed_s")), 3),
            "api_call_count": int(_num(meta.get("api_call_count"))),
            "generated_at": meta.get("generated_at", ""),
            "meta_path": str(meta_path),
        }
        rows.append(row)
    return rows


def _collect_result_maps(result_dirs: list[Path]) -> dict[str, dict[str, str]]:
    """Return task_id -> backend_label -> status."""
    status_by_task: dict[str, dict[str, str]] = defaultdict(dict)
    for result_dir in result_dirs:
        label = result_dir.name
        for path in sorted(result_dir.glob("*/evas_result.json")):
            data = _read_json(path)
            task_id = data.get("task_id") or path.parent.name
            status_by_task[task_id][label] = _strict_result_status(data)
            status_by_task[task_id][f"{label}:backend"] = "evas"
        for path in sorted(result_dir.glob("*/spectre_result.json")):
            data = _read_json(path)
            task_id = data.get("task_id") or path.parent.name
            status_by_task[task_id][label] = _strict_result_status(data)
            status_by_task[task_id][f"{label}:backend"] = "spectre"
    return status_by_task


def _attach_results(rows: list[dict[str, Any]], result_dirs: list[Path]) -> list[str]:
    status_by_task = _collect_result_maps(result_dirs)
    labels = sorted({label for per_task in status_by_task.values() for label in per_task if not label.endswith(":backend")})
    for row in rows:
        per_task = status_by_task.get(row["task_id"], {})
        for label in labels:
            row[f"result:{label}"] = per_task.get(label, "")
    return labels


def _aggregate(rows: list[dict[str, Any]], group_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = tuple(row.get(k, "") for k in group_keys)
        buckets[key].append(row)
    output: list[dict[str, Any]] = []
    for key, items in sorted(buckets.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        total_input = sum(int(item["input_tokens"]) for item in items)
        total_output = sum(int(item["output_tokens"]) for item in items)
        total_tokens = total_input + total_output
        api_elapsed = sum(float(item["api_elapsed_s"]) for item in items)
        task_elapsed = sum(float(item["task_elapsed_s"]) for item in items)
        generated = sum(1 for item in items if item.get("status") == "generated")
        api_error = sum(1 for item in items if item.get("status") == "api_error")
        no_code = sum(1 for item in items if item.get("status") == "no_code_extracted")
        row = {
            "group": "+".join(group_keys) if group_keys else "overall",
            "tasks": len(items),
            "generated": generated,
            "api_error": api_error,
            "no_code_extracted": no_code,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_tokens,
            "avg_tokens_per_task": round(total_tokens / max(len(items), 1), 2),
            "api_elapsed_s": round(api_elapsed, 3),
            "avg_api_elapsed_s_per_task": round(api_elapsed / max(len(items), 1), 3),
            "task_elapsed_s": round(task_elapsed, 3),
            "avg_task_elapsed_s_per_task": round(task_elapsed / max(len(items), 1), 3),
            "api_call_count": sum(int(item["api_call_count"]) for item in items),
        }
        for name, value in zip(group_keys, key):
            row[name] = value
        result_cols = sorted(k for k in items[0] if k.startswith("result:")) if items else []
        for col in result_cols:
            pass_count = sum(1 for item in items if item.get(col) == "PASS")
            seen_count = sum(1 for item in items if item.get(col))
            if seen_count:
                row[f"{col}:pass_count"] = pass_count
                row[f"{col}:seen_count"] = seen_count
                row[f"{col}:pass_rate"] = round(pass_count / seen_count, 4)
        output.append(row)
    return output


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_markdown(path: Path, aggregate_rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    result_cols = sorted(
        {
            key
            for row in aggregate_rows
            for key in row
            if key.startswith("result:") and key.endswith((":pass_count", ":seen_count", ":pass_rate"))
        }
    )
    preferred = [
        "group",
        "model",
        "source_collection",
        "task_form",
        "core_function",
        "tasks",
        "generated",
        "api_error",
        "no_code_extracted",
        "total_input_tokens",
        "total_output_tokens",
        "total_tokens",
        "avg_tokens_per_task",
        "api_elapsed_s",
        "avg_api_elapsed_s_per_task",
    ] + result_cols
    lines = ["# Experiment Cost Summary", ""]
    for group in ("overall", "model", "source_collection", "task_form", "source_collection+task_form"):
        items = [row for row in aggregate_rows if row.get("group") == group]
        if not items:
            continue
        cols = [col for col in preferred if any(col in row for row in items)]
        lines.extend([f"## {group}", "", "| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"])
        for row in items:
            lines.append("| " + " | ".join(str(row.get(col, "")) for col in cols) + " |")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-dir", required=True, help="Generated root containing <model>/<task>/sample_N/.")
    parser.add_argument("--bench-dir", default="", help="Optional benchmark root for task metadata enrichment.")
    parser.add_argument("--result-dir", action="append", default=[], help="Optional validation result root to attach statuses.")
    parser.add_argument("--sample-idx", type=int, default=0, help="Sample index to summarize. Use -1 for all samples.")
    parser.add_argument("--output-prefix", default="", help="Output prefix for .json/.rows.csv/.groups.csv/.md files.")
    args = parser.parse_args()

    generated_dir = Path(args.generated_dir)
    if not generated_dir.is_absolute():
        generated_dir = ROOT / generated_dir
    bench_dir = Path(args.bench_dir) if args.bench_dir else None
    if bench_dir is not None and not bench_dir.is_absolute():
        bench_dir = ROOT / bench_dir
    result_dirs = [Path(p) if Path(p).is_absolute() else ROOT / p for p in args.result_dir]
    sample_idx = None if args.sample_idx < 0 else args.sample_idx
    output_prefix = Path(args.output_prefix) if args.output_prefix else generated_dir / "cost_summary"
    if not output_prefix.is_absolute():
        output_prefix = ROOT / output_prefix

    rows = _collect_generation_rows(generated_dir, _load_bench_meta(bench_dir), sample_idx)
    result_labels = _attach_results(rows, result_dirs)
    aggregate_rows: list[dict[str, Any]] = []
    for keys in [
        (),
        ("model",),
        ("source_collection",),
        ("task_form",),
        ("source_collection", "task_form"),
        ("core_function",),
        ("model", "source_collection", "task_form"),
    ]:
        aggregate_rows.extend(_aggregate(rows, keys))

    payload = {
        "generated_dir": str(generated_dir),
        "bench_dir": str(bench_dir) if bench_dir else None,
        "sample_idx": sample_idx,
        "result_labels": result_labels,
        "rows": rows,
        "aggregates": aggregate_rows,
    }
    json_path = output_prefix.with_suffix(".json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_csv(output_prefix.with_suffix(".rows.csv"), rows)
    _write_csv(output_prefix.with_suffix(".groups.csv"), aggregate_rows)
    _write_markdown(output_prefix.with_suffix(".md"), aggregate_rows)
    print(f"[cost-summary] rows={len(rows)} groups={len(aggregate_rows)}")
    print(f"[cost-summary] wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
