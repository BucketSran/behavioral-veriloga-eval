#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from _result_table_utils import PAPER_DIR, TABLE_PATH, family_stats, load_family_rows, markdown_table, infer_dual_validated, row_category


def pct(numer: int, denom: int) -> str:
    if denom <= 0:
        return "0.0%"
    return f"{100.0 * numer / denom:.1f}%"


def build_outputs(today: date) -> tuple[str, dict]:
    families = load_family_rows(TABLE_PATH)
    all_rows = [row for rows in families.values() for row in rows]

    family_table_rows: list[list[str]] = []
    family_json: dict[str, dict[str, int]] = {}
    total_tasks = 0
    total_passed = 0
    total_dual = 0
    for family in ("end-to-end", "spec-to-va", "bugfix", "tb-generation"):
        stats = family_stats(families[family], family=family)
        family_json[family] = stats
        total_tasks += stats["total"]
        total_passed += stats["passed"]
        total_dual += stats["dual"]
        family_table_rows.append(
            [
                family,
                str(stats["total"]),
                f"{stats['passed']} ({pct(stats['passed'], stats['total'])})",
                str(stats["dual"]),
            ]
        )
    family_table_rows.append(
        [
            "**Total**",
            f"**{total_tasks}**",
            f"**{total_passed} ({pct(total_passed, total_tasks)})**",
            f"**{total_dual}**",
        ]
    )

    category_counts: dict[str, int] = {}
    dual_by_category: dict[str, int] = {}
    for row in all_rows:
        category = row_category(row)
        category_counts[category] = category_counts.get(category, 0) + 1
        family = "end-to-end"
        for fam, rows in families.items():
            if row in rows:
                family = fam
                break
        if family != "spec-to-va" and infer_dual_validated(row):
            dual_by_category[category] = dual_by_category.get(category, 0) + 1

    category_rows = [
        [category, str(category_counts[category]), str(dual_by_category.get(category, 0))]
        for category in sorted(category_counts)
    ]

    markdown = "\n".join(
        [
            f"# Paper Stats — {today.isoformat()}",
            "",
            "## Family Distribution",
            markdown_table(["Task Family", "# Tasks", "EVAS Passed", "Dual-Validated"], family_table_rows).rstrip(),
            "",
            "## Category Distribution",
            markdown_table(["Category", "# Tasks", "Dual-Validated"], category_rows).rstrip(),
            "",
        ]
    )
    payload = {
        "total_tasks": total_tasks,
        "families": family_json,
        "categories": category_counts,
        "dual_validated_by_category": dual_by_category,
        "dual_validated_total": total_dual,
        "generated_at": today.isoformat(),
    }
    return markdown, payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate paper-ready benchmark statistics.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Generation date in YYYY-MM-DD.")
    parser.add_argument("--markdown-output", default="", help="Optional explicit PAPER_STATS.md path.")
    parser.add_argument("--json-output", default="", help="Optional explicit paper_stats.json path.")
    args = parser.parse_args()

    today = date.fromisoformat(args.date)
    markdown_path = Path(args.markdown_output) if args.markdown_output else PAPER_DIR / "PAPER_STATS.md"
    json_path = Path(args.json_output) if args.json_output else PAPER_DIR / "paper_stats.json"
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    markdown, payload = build_outputs(today)
    markdown_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(markdown_path)
    print(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
