#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORTS = ROOT / "benchmark-vabench-release-v3" / "reports"
DEFAULT_TASKS_JSON = ROOT / "benchmark-vabench-release-v3" / "TASKS.json"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def row_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("task_slug") or ""),
        str(row.get("kind") or ""),
        str(row.get("variant") or ""),
    )


def scrub_note(note: Any) -> str:
    text = str(note)
    if not text.startswith("checker_config="):
        return text
    marker = "benchmark-vabench-release-v3/"
    if marker in text:
        return f"checker_config={text[text.index(marker):]}"
    return text


def scrub_row(row: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(row)
    cleaned.pop("stdout_tail", None)
    cleaned.pop("artifacts", None)
    notes = cleaned.get("notes")
    if isinstance(notes, list):
        cleaned["notes"] = [scrub_note(note) for note in notes]
    return cleaned


def read_current_tasks(path: Path) -> set[str]:
    payload = read_json(path)
    tasks = payload.get("tasks", {})
    return {str(slug) for slug in tasks} if isinstance(tasks, dict) else set()


def build_payload(inputs: list[Path], scope: str, current_tasks: set[str] | None = None) -> dict[str, Any]:
    rows_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    skipped_tasks: list[str] = []
    source_reports: list[dict[str, Any]] = []
    source_wall_s = 0.0
    slow_threshold = 20.0

    for path in inputs:
        payload = read_json(path)
        summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
        source_reports.append({
            "path": rel(path),
            "summary": summary,
        })
        try:
            source_wall_s += float(summary.get("wall_s") or 0.0)
        except (TypeError, ValueError):
            pass
        if "slow_gold_threshold_s" in summary:
            try:
                slow_threshold = float(summary["slow_gold_threshold_s"])
            except (TypeError, ValueError):
                pass
        for task in payload.get("skipped_tasks", []):
            skipped_tasks.append(str(task))
        for row in payload.get("rows", []):
            if isinstance(row, dict):
                slug = str(row.get("task_slug") or "")
                if current_tasks is not None and slug not in current_tasks:
                    continue
                rows_by_key[row_key(row)] = scrub_row(row)

    rows = sorted(rows_by_key.values(), key=row_key)
    gold_rows = [row for row in rows if row.get("kind") == "gold"]
    negative_rows = [row for row in rows if row.get("kind") == "negative"]
    gold_timings = [
        {
            "task_slug": row.get("task_slug"),
            "task_id": row.get("task_id"),
            "case_id": row.get("case_id"),
            "status": row.get("status"),
            "wall_s": row.get("wall_s", 0.0),
        }
        for row in gold_rows
    ]
    gold_wall_times = []
    for row in gold_timings:
        try:
            gold_wall_times.append(float(row.get("wall_s") or 0.0))
        except (TypeError, ValueError):
            gold_wall_times.append(0.0)
    slow_cases = [
        row for row in gold_timings
        if float(row.get("wall_s") or 0.0) > slow_threshold
    ]
    summary = {
        "scope": scope,
        "cases_total": len(rows),
        "gold_total": len(gold_rows),
        "gold_pass": sum(row.get("status") == "PASS" for row in gold_rows),
        "gold_fail": sum(row.get("status") != "PASS" for row in gold_rows),
        "negative_total": len(negative_rows),
        "negative_rejected": sum(row.get("status") != "PASS" for row in negative_rows),
        "negative_accepted": sum(row.get("status") == "PASS" for row in negative_rows),
        "expectation_pass": sum(row.get("meets_expectation") is True for row in rows),
        "expectation_fail": sum(row.get("meets_expectation") is not True for row in rows),
        "skipped_staged_tasks": len(set(skipped_tasks)),
        "gold_wall_s_total": round(sum(gold_wall_times), 6),
        "gold_wall_s_max": round(max(gold_wall_times), 6) if gold_wall_times else 0.0,
        "slow_gold_threshold_s": slow_threshold,
        "slow_gold_count": len(slow_cases),
        "wall_s": round(source_wall_s, 6),
    }
    return {
        "summary": summary,
        "source_reports": source_reports,
        "rows": rows,
        "skipped_tasks": sorted(set(skipped_tasks)),
        "gold_timings": sorted(gold_timings, key=lambda row: str(row.get("task_slug") or "")),
        "slow_gold_cases": sorted(slow_cases, key=lambda row: float(row.get("wall_s") or 0.0), reverse=True),
    }


def write_markdown(payload: dict[str, Any], out: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# v3 Layered Verification Merge",
        "",
        "## Summary",
        "",
    ]
    for key in (
        "scope",
        "cases_total",
        "gold_total",
        "gold_pass",
        "gold_fail",
        "negative_total",
        "negative_rejected",
        "negative_accepted",
        "expectation_pass",
        "expectation_fail",
        "skipped_staged_tasks",
        "gold_wall_s_total",
        "gold_wall_s_max",
        "slow_gold_count",
        "wall_s",
    ):
        lines.append(f"- `{key}`: {summary[key]}")
    lines.extend([
        "",
        "## Source Reports",
        "",
        "| Report | Cases | Gold pass | Negative rejected | Expectation fail |",
        "| --- | ---: | ---: | ---: | ---: |",
    ])
    for source in payload["source_reports"]:
        source_summary = source.get("summary", {})
        lines.append(
            f"| `{source['path']}` | {source_summary.get('cases_total', '')} | "
            f"{source_summary.get('gold_pass', '')} | "
            f"{source_summary.get('negative_rejected', '')} | "
            f"{source_summary.get('expectation_fail', '')} |"
        )
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge v3 layered verification reports.")
    parser.add_argument(
        "--input",
        action="append",
        type=Path,
        required=True,
        help="Input verification JSON. May be supplied more than once.",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--md-out", type=Path, default=None)
    parser.add_argument("--scope", default="301-505")
    parser.add_argument(
        "--filter-current-tasks",
        action="store_true",
        help="Drop rows whose task_slug is not present in the current v3 TASKS.json.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    current_tasks = read_current_tasks(DEFAULT_TASKS_JSON) if args.filter_current_tasks else None
    payload = build_payload(args.input, args.scope, current_tasks=current_tasks)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        write_markdown(payload, args.md_out)
    summary = payload["summary"]
    print(
        "merged layered verification: cases={cases}; gold={gold}/{gold_total}; "
        "negatives={negative}/{negative_total}; expectation_fail={fail}".format(
            cases=summary["cases_total"],
            gold=summary["gold_pass"],
            gold_total=summary["gold_total"],
            negative=summary["negative_rejected"],
            negative_total=summary["negative_total"],
            fail=summary["expectation_fail"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
