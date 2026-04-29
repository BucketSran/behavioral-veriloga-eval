#!/usr/bin/env python3
"""Summarize the remaining R26 teacher replay Spectre failures.

The packets are deliberately operational: they separate behavior failures from
Spectre-compatibility/template failures so the next repair pass can apply the
right owner and not ask the LLM to redesign circuits that are already close.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
SPECTRE_ROOT = ROOT / "results" / "r26-teacher-remaining23-spectre-2026-04-29"
LEDGER = ROOT / "docs" / "CLOSEDSET92_COMPLETION_LEDGER.json"
OUT_JSON = SPECTRE_ROOT / "failure_packets.json"
OUT_MD = PROJECT / "coordination" / "status" / "2026-04-29_r26_teacher_remaining10_failure_packets.md"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT.resolve()))
    except Exception:
        return str(path)


def _classify(notes: list[str], log: str) -> list[str]:
    text = "\n".join(notes) + "\n" + log
    labels: list[str] = []
    if "combined_direction_discipline" in text or "invalid port direction" in text:
        labels.append("spectre_port_declaration_style")
    if "malformed_pwl_wave" in text:
        labels.append("malformed_pwl_wave")
    if "embedded_declaration" in text or "VACOMP-1917" in text:
        labels.append("embedded_declaration")
    if "interface_parameter_missing" in text:
        labels.append("interface_parameter_missing")
    if "Unexpected close parenthesis" in text or "syntax error `Unexpected close" in text:
        labels.append("tb_syntax_unexpected_close_parenthesis")
    if "parameter vlow" in text and "exceeds upper bound" in text:
        labels.append("spectre_parameter_range_bound")
    if not labels:
        labels.append("unknown_spectre_compile_or_run")
    return labels


def main() -> int:
    ledger = _read_json(LEDGER)
    rows_by_task = {row["task_id"]: row for row in ledger.get("tasks", [])}
    packets: list[dict[str, Any]] = []
    for result_path in sorted(SPECTRE_ROOT.glob("*/result.json")):
        result = _read_json(result_path)
        if result.get("spectre_pass") is True or result.get("spectre_status") == "PASS":
            continue
        task_id = result.get("task_id") or result_path.parent.name
        log_path = result_path.parent / "bridge_console.log"
        log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
        notes = [str(item) for item in result.get("spectre_notes", [])]
        labels = _classify(notes, log)
        owner = "template_or_pipeline" if any(
            label
            in {
                "spectre_port_declaration_style",
                "malformed_pwl_wave",
                "embedded_declaration",
                "tb_syntax_unexpected_close_parenthesis",
                "interface_parameter_missing",
                "spectre_parameter_range_bound",
            }
            for label in labels
        ) else "manual_triage"
        packets.append(
            {
                "task_id": task_id,
                "mechanism_family": rows_by_task.get(task_id, {}).get("mechanism_family"),
                "spectre_status": result.get("spectre_status"),
                "spectre_scores": result.get("spectre_scores", {}),
                "failure_labels": labels,
                "repair_owner": owner,
                "notes": notes,
                "result_json": _rel(result_path),
                "bridge_log": _rel(log_path),
                "staged_files": sorted(_rel(path) for path in (result_path.parent / "staged").glob("*") if path.is_file()),
                "recommended_action": _recommend(labels),
            }
        )

    summary = {
        "source_root": _rel(SPECTRE_ROOT),
        "total_failures": len(packets),
        "by_label": dict(Counter(label for packet in packets for label in packet["failure_labels"])),
        "by_owner": dict(Counter(packet["repair_owner"] for packet in packets)),
    }
    OUT_JSON.write_text(json.dumps({"summary": summary, "packets": packets}, indent=2), encoding="utf-8")
    OUT_MD.write_text(_markdown(summary, packets), encoding="utf-8")
    print(f"[r26-failure-packets] wrote {OUT_JSON}")
    print(f"[r26-failure-packets] wrote {OUT_MD}")
    print(f"[r26-failure-packets] {summary}")
    return 0


def _recommend(labels: list[str]) -> str:
    if "spectre_port_declaration_style" in labels:
        return "Rewrite Verilog-A port declarations into separate direction and electrical declarations."
    if "tb_syntax_unexpected_close_parenthesis" in labels:
        return "Rewrite the Spectre instance line from multiline named-port style to positional instance syntax."
    if "embedded_declaration" in labels:
        return "Move block-local real declarations to module scope or a labeled analog block supported by Spectre."
    if "spectre_parameter_range_bound" in labels:
        return "Relax or remove incompatible parameter range constraints before hierarchy flattening."
    if "malformed_pwl_wave" in labels:
        return "Normalize bracketed comma/backslash PWL syntax to Spectre-compatible whitespace pairs."
    return "Inspect bridge log and staged files."


def _markdown(summary: dict[str, Any], packets: list[dict[str, Any]]) -> str:
    lines = [
        "# R26 Teacher Replay Remaining Failure Packets",
        "",
        "Date: 2026-04-29",
        "",
        "These packets cover the 10 tasks that still fail after replaying R26 teacher artifacts through real Spectre. They are not treated as behavior failures until Spectre-compatible syntax and runner issues are removed.",
        "",
        "## Summary",
        "",
        f"- Source root: `{summary['source_root']}`",
        f"- Total failures: `{summary['total_failures']}`",
        f"- By label: `{summary['by_label']}`",
        f"- By owner: `{summary['by_owner']}`",
        "",
        "## Packets",
        "",
        "| Task | Mechanism | Labels | Recommended Action |",
        "|---|---|---|---|",
    ]
    for packet in packets:
        labels = ", ".join(f"`{label}`" for label in packet["failure_labels"])
        lines.append(
            f"| `{packet['task_id']}` | `{packet['mechanism_family']}` | {labels} | {packet['recommended_action']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- These failures belong to the teacher-replay completion path, not cold-start A/D/F/G.",
            "- A task should only move from this file into the accepted ledger after EVAS and real Spectre both pass.",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
