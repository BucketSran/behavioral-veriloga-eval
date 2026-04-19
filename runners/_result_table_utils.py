#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import json
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[0]
TABLE_PATH = REPO_ROOT / "coordination" / "docs" / "benchmark" / "BENCHMARK_RESULT_TABLE.md"
STATUS_DIR = REPO_ROOT / "coordination" / "status"
PAPER_DIR = REPO_ROOT / "coordination" / "docs" / "paper"

DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")


def strip_ticks(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`"):
        return value[1:-1]
    return value


def parse_markdown_table(block: list[str]) -> list[dict[str, str]]:
    if len(block) < 2:
        return []
    header_line = block[0].strip().strip("|")
    headers = [cell.strip() for cell in header_line.split("|")]
    rows: list[dict[str, str]] = []
    for line in block[2:]:
        line = line.strip()
        if not line.startswith("|"):
            break
        values = [cell.strip() for cell in line.strip("|").split("|")]
        if len(values) < len(headers):
            values.extend([""] * (len(headers) - len(values)))
        rows.append(dict(zip(headers, values)))
    return rows


def load_family_rows(table_path: Path = TABLE_PATH) -> dict[str, list[dict[str, str]]]:
    text = table_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    family_rows: dict[str, list[dict[str, str]]] = {
        "end-to-end": [],
        "spec-to-va": [],
        "bugfix": [],
        "tb-generation": [],
    }
    current_heading = ""
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if line.startswith("## "):
            current_heading = line.strip()
        if line.startswith("| "):
            block = [line]
            idx += 1
            while idx < len(lines) and lines[idx].startswith("|"):
                block.append(lines[idx])
                idx += 1
            rows = parse_markdown_table(block)
            if current_heading == "## Table":
                family_rows["end-to-end"].extend(rows)
            elif current_heading == "## spec-to-va Results":
                family_rows["spec-to-va"].extend(rows)
            elif current_heading == "## bugfix Results":
                family_rows["bugfix"].extend(rows)
            elif current_heading == "## tb-generation Results":
                family_rows["tb-generation"].extend(rows)
            continue
        idx += 1
    return family_rows


def infer_dual_validated(row: dict[str, str]) -> bool:
    parity_status = row.get("parity_status", "").strip("`").strip().lower()
    if parity_status:
        return parity_status == "dual-validated"
    notes = row.get("notes", "").lower()
    return any(token in notes for token in ("dual validation", "dual-suite", "evas+spectre"))


def infer_created_at(row: dict[str, str]) -> str:
    meta = load_task_meta(row)
    created_at = str(meta.get("created_at", "")).strip()
    if DATE_RE.fullmatch(created_at):
        return created_at
    notes = row.get("notes", "")
    match = DATE_RE.search(notes)
    if match:
        return match.group(1)
    return "unknown"


def load_task_meta(row: dict[str, str]) -> dict:
    for key in ("source_path", "task_path"):
        raw_path = strip_ticks(row.get(key, ""))
        if raw_path.startswith("tasks/"):
            meta_path = ROOT / raw_path / "meta.json"
        elif raw_path.startswith("behavioral-veriloga-eval/tasks/"):
            rel = raw_path.split("behavioral-veriloga-eval/", 1)[1]
            meta_path = REPO_ROOT / "behavioral-veriloga-eval" / rel / "meta.json"
        else:
            meta_path = None
        if meta_path and meta_path.exists():
            try:
                return json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
    return {}


def row_category(row: dict[str, str]) -> str:
    category = strip_ticks(row.get("category", ""))
    if category:
        return category
    meta = load_task_meta(row)
    return str(meta.get("category", "unknown")).strip() or "unknown"


def family_stats(rows: list[dict[str, str]], *, family: str) -> dict[str, int]:
    total = len(rows)
    passed = sum(1 for row in rows if row.get("verification_status", "").strip("`") == "passed")
    dual = 0 if family == "spec-to-va" else sum(1 for row in rows if infer_dual_validated(row))
    return {"total": total, "passed": passed, "dual": dual}


def recent_rows(rows: list[dict[str, str]], *, today: date, days: int = 7) -> list[dict[str, str]]:
    recent: list[dict[str, str]] = []
    for row in rows:
        created = infer_created_at(row)
        if created == "unknown":
            continue
        created_date = date.fromisoformat(created)
        if 0 <= (today - created_date).days < days:
            recent.append(row)
    return recent


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter="|", lineterminator="\n")
    writer.writerow([""] + headers + [""])
    writer.writerow([""] + ["---"] * len(headers) + [""])
    for row in rows:
        writer.writerow([""] + row + [""])
    return buf.getvalue()
