#!/usr/bin/env python3
"""Summarize EVAS runtime bottlenecks from a scoring result directory."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def _notes_text(result: dict) -> str:
    notes = result.get("evas_notes") or result.get("notes") or []
    if isinstance(notes, str):
        return notes
    return " | ".join(str(note) for note in notes)


def _classify(row: dict) -> str:
    notes = row["notes"].lower()
    if row["status"] in {"FAIL_DUT_COMPILE", "FAIL_TB_COMPILE"}:
        return "compile_or_preflight"
    if "behavior_eval_timeout" in notes:
        return "checker_timeout"
    if "evas_timeout" in notes:
        return "evas_timeout"
    if "tran.csv missing" in notes:
        return "missing_csv"
    if row["csv_mb"] >= 50:
        return "large_csv"
    if (row["steps"] or 0) >= 250_000:
        return "many_steps"
    return "normal"


def collect(result_root: Path) -> list[dict]:
    rows: list[dict] = []
    for result_path in sorted(result_root.glob("*/result.json")):
        result = json.loads(result_path.read_text(encoding="utf-8"))
        timing = result.get("evas_timing") or result.get("timing") or {}
        csv_path = result_path.parent / "tran.csv"
        csv_mb = csv_path.stat().st_size / (1024 * 1024) if csv_path.exists() else 0.0
        row = {
            "task_id": result_path.parent.name,
            "status": result.get("status"),
            "family": result.get("family", ""),
            "total_elapsed_s": timing.get("total_elapsed_s"),
            "tran_elapsed_s": timing.get("tran_elapsed_s"),
            "accepted_tran_steps": timing.get("accepted_tran_steps"),
            "csv_mb": csv_mb,
            "notes": _notes_text(result),
        }
        row["class"] = _classify(
            {
                "status": row["status"],
                "notes": row["notes"],
                "csv_mb": csv_mb,
                "steps": row["accepted_tran_steps"],
            }
        )
        rows.append(row)
    return rows


def summarize(rows: list[dict]) -> dict:
    timed = [row for row in rows if row["total_elapsed_s"] is not None]
    totals = sorted(float(row["total_elapsed_s"]) for row in timed)
    by_class: dict[str, int] = {}
    for row in rows:
        by_class[row["class"]] = by_class.get(row["class"], 0) + 1
    return {
        "task_count": len(rows),
        "timed_count": len(timed),
        "total_elapsed_sum_s": round(sum(totals), 3) if totals else 0.0,
        "median_elapsed_s": round(statistics.median(totals), 3) if totals else None,
        "p90_elapsed_s": round(totals[int(0.9 * (len(totals) - 1))], 3) if totals else None,
        "p95_elapsed_s": round(totals[int(0.95 * (len(totals) - 1))], 3) if totals else None,
        "max_elapsed_s": round(max(totals), 3) if totals else None,
        "by_class": by_class,
    }


def write_markdown(path: Path, result_root: Path, rows: list[dict], summary: dict, limit: int) -> None:
    top = sorted(
        rows,
        key=lambda row: float(row["total_elapsed_s"] or -1.0),
        reverse=True,
    )[:limit]
    lines = [
        f"# Slow Task Report: `{result_root}`",
        "",
        "## Summary",
        "",
        f"- tasks: {summary['task_count']}",
        f"- timed tasks: {summary['timed_count']}",
        f"- total EVAS elapsed sum: {summary['total_elapsed_sum_s']} s",
        f"- median: {summary['median_elapsed_s']} s",
        f"- p90: {summary['p90_elapsed_s']} s",
        f"- p95: {summary['p95_elapsed_s']} s",
        f"- max: {summary['max_elapsed_s']} s",
        f"- classes: `{summary['by_class']}`",
        "",
        "## Slowest Tasks",
        "",
        "| task | class | status | total s | tran s | steps | CSV MB | notes |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in top:
        notes = row["notes"].replace("|", "\\|")[:180]
        lines.append(
            "| {task_id} | {klass} | {status} | {total} | {tran} | {steps} | {csv:.1f} | {notes} |".format(
                task_id=row["task_id"],
                klass=row["class"],
                status=row["status"],
                total="" if row["total_elapsed_s"] is None else f"{float(row['total_elapsed_s']):.3f}",
                tran="" if row["tran_elapsed_s"] is None else f"{float(row['tran_elapsed_s']):.3f}",
                steps="" if row["accepted_tran_steps"] is None else f"{int(row['accepted_tran_steps'])}",
                csv=row["csv_mb"],
                notes=notes,
            )
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a slow-task report from EVAS scoring results.")
    parser.add_argument("result_root")
    parser.add_argument("--output-md", default="")
    parser.add_argument("--output-json", default="")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()

    result_root = Path(args.result_root).resolve()
    rows = collect(result_root)
    summary = summarize(rows)
    payload = {
        "result_root": str(result_root),
        "summary": summary,
        "rows": rows,
    }

    output_json = Path(args.output_json) if args.output_json else result_root / "slow_task_report.json"
    output_md = Path(args.output_md) if args.output_md else result_root / "slow_task_report.md"
    output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    write_markdown(output_md, result_root, rows, summary, args.limit)
    print(f"[slow-report] wrote {output_md}")
    print(f"[slow-report] wrote {output_json}")
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
