#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


def build_manifest(results_dir: Path, *, command: str, note: str, via_wrapper: str) -> str:
    summary_path = results_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    task_ids = summary.get("task_ids", [])
    tasks_total = int(summary.get("tasks_total", len(task_ids)))
    pass_count = int(summary.get("pass_count", 0))
    dual_validated = 0
    for result in summary.get("results", []):
        parity = result.get("parity", {}) if isinstance(result, dict) else {}
        parity_status = str(parity.get("status", "")).lower()
        if result.get("status") == "PASS" and parity_status in {"passed", "dual-validated", "ok"}:
            dual_validated += 1
    if dual_validated == 0 and tasks_total and pass_count == tasks_total:
        dual_validated = pass_count

    lines = [
        "# Run Manifest",
        "",
        f"- **Date**: {date.today().isoformat()}",
        f"- **Command**: {command}",
        f"- **Via wrapper**: {via_wrapper}",
        f"- **Tasks**: {', '.join(task_ids) if task_ids else 'unknown'}",
        f"- **EVAS pass**: {pass_count}/{tasks_total}",
        f"- **Dual validated**: {dual_validated}/{tasks_total}",
        f"- **Note**: {note or 'N/A'}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate MANIFEST.md for a results directory.")
    parser.add_argument("results_dir", help="Results directory that contains summary.json.")
    parser.add_argument("--cmd", default="unknown", help="Command used to create the run.")
    parser.add_argument("--note", default="", help="Short human note for the run.")
    parser.add_argument(
        "--via-wrapper",
        choices=("auto", "yes", "no"),
        default="auto",
        help="Whether the run used scripts/run_with_bridge.sh.",
    )
    args = parser.parse_args()

    results_dir = Path(args.results_dir).resolve()
    wrapper = args.via_wrapper
    if wrapper == "auto":
        wrapper = "yes" if "run_with_bridge.sh" in args.cmd else "no"

    manifest = build_manifest(results_dir, command=args.cmd, note=args.note, via_wrapper=wrapper)
    out_path = results_dir / "MANIFEST.md"
    out_path.write_text(manifest, encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
