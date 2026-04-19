#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from _result_table_utils import STATUS_DIR, TABLE_PATH, family_stats, load_family_rows, markdown_table, recent_rows, strip_ticks


def render_summary(today: date) -> str:
    families = load_family_rows(TABLE_PATH)
    all_rows = [row for rows in families.values() for row in rows]

    total_tasks = sum(len(rows) for rows in families.values())
    total_passed = sum(family_stats(rows, family=family)["passed"] for family, rows in families.items())
    total_dual = sum(family_stats(rows, family=family)["dual"] for family, rows in families.items())

    family_rows: list[list[str]] = []
    for family in ("end-to-end", "spec-to-va", "bugfix", "tb-generation"):
        stats = family_stats(families[family], family=family)
        family_rows.append([family, str(stats["total"]), str(stats["passed"]), str(stats["dual"])])

    recent = recent_rows(all_rows, today=today, days=7)
    recent_lines = []
    for row in recent:
        case_id = strip_ticks(row.get("case_name", "") or row.get("task_name", "") or row.get("id", "unknown"))
        status = strip_ticks(row.get("verification_status", "unknown"))
        recent_lines.append(f"- `{case_id}`: `{status}`")
    if not recent_lines:
        recent_lines.append("- none")

    lines = [
        f"# Weekly Summary — {today.isoformat()}",
        "",
        "## 总体状态",
        f"- 总任务数：{total_tasks}",
        f"- 已验证（EVAS passed）：{total_passed}",
        f"- Dual validated：{total_dual}",
        "",
        "## 各 family 明细",
        markdown_table(["family", "total", "evas_passed", "dual_validated"], family_rows).rstrip(),
        "",
        "## 本周新增",
        *recent_lines,
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a weekly benchmark summary from BENCHMARK_RESULT_TABLE.md.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Summary date in YYYY-MM-DD.")
    parser.add_argument(
        "--output",
        default="",
        help="Optional explicit output path. Defaults to coordination/status/summary_<date>.md.",
    )
    args = parser.parse_args()

    today = date.fromisoformat(args.date)
    output_path = Path(args.output) if args.output else STATUS_DIR / f"summary_{today.isoformat()}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = render_summary(today)
    output_path.write_text(content, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
