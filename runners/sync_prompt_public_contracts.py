#!/usr/bin/env python3
"""Append public evaluator contracts to raw task prompts.

The generated runtime prompt already injects several contracts, but raw
`prompt.md` files should also disclose evaluator-facing constraints that affect
fairness: final transient settings, observable CSV names, and generic
reset/enable/clock window rules.  This script intentionally does not copy gold
implementation code or exact DUT internals.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from generate import ROOT, list_task_dirs, read_meta
from generate import _observable_columns_from_checker, _strict_tran_lines


MARKER = "## Public Evaluation Contract (Non-Gold)"

SAVE_RE = re.compile(r"^\s*save\s+(.+)$", re.IGNORECASE | re.MULTILINE)
SOURCE_RE = re.compile(r"^\s*[VI]\w*\s+\(([^)\s]+)\s+0\)\s+\w+source\b", re.IGNORECASE | re.MULTILINE)

RESET_NAMES = ("rst", "reset", "rstb", "rst_n", "reset_n", "rst_ni", "RST", "RSTB", "RST_N")
ENABLE_NAMES = ("en", "enable", "EN", "ENABLE")
CLOCK_NAMES = ("clk", "clock", "CLK", "CLOCK", "ref_clk", "dco_clk", "fb_clk")


def _gold_tbs(task_dir: Path) -> list[Path]:
    gold_dir = task_dir / "gold"
    if not gold_dir.is_dir():
        return []
    return sorted(gold_dir.glob("*.scs"))


def _gold_tb_text(task_dir: Path) -> str:
    chunks: list[str] = []
    for tb_path in _gold_tbs(task_dir):
        chunks.append(tb_path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks)


def _save_columns_from_gold(task_dir: Path) -> list[str]:
    text = _gold_tb_text(task_dir)
    columns: list[str] = []
    seen: set[str] = set()
    for match in SAVE_RE.finditer(text):
        body = match.group(1).strip()
        if body.lower().startswith(("all", "none")):
            continue
        for token in re.split(r"\s+", body):
            token = token.strip()
            if not token:
                continue
            token = re.sub(r"^v\(([^)]+)\)$", r"\1", token, flags=re.IGNORECASE)
            token = token.split(":")[-1].split(".")[-1]
            if token and token not in seen:
                seen.add(token)
                columns.append(token)
    return columns


def _mentioned_names(prompt: str, gold_tb: str, names: tuple[str, ...]) -> list[str]:
    haystack = prompt + "\n" + gold_tb
    found: list[str] = []
    seen: set[str] = set()
    for name in names:
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", haystack):
            lname = name.lower()
            if lname not in seen:
                seen.add(lname)
                found.append(name)
    return found


def _source_nodes(gold_tb: str) -> list[str]:
    nodes: list[str] = []
    seen: set[str] = set()
    for match in SOURCE_RE.finditer(gold_tb):
        node = match.group(1).strip()
        if node and node not in seen:
            seen.add(node)
            nodes.append(node)
    return nodes


def _chunked(items: list[str], size: int = 8) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _build_contract(task_id: str, task_dir: Path) -> str:
    meta = read_meta(task_dir)
    family = meta.get("family", "unknown")
    prompt = (task_dir / "prompt.md").read_text(encoding="utf-8", errors="ignore")
    gold_tb = _gold_tb_text(task_dir)

    columns = _observable_columns_from_checker(task_id)
    if not columns:
        columns = _save_columns_from_gold(task_dir)

    tran_lines = _strict_tran_lines(task_dir)
    reset_names = _mentioned_names(prompt, gold_tb, RESET_NAMES)
    enable_names = _mentioned_names(prompt, gold_tb, ENABLE_NAMES)
    clock_names = _mentioned_names(prompt, gold_tb, CLOCK_NAMES)
    source_nodes = _source_nodes(gold_tb)

    lines: list[str] = [
        "",
        MARKER,
        "",
        "This section states evaluator-facing constraints that must be visible to the generated artifact.",
        "It does not prescribe the internal implementation or reveal a gold solution.",
        "",
    ]

    if tran_lines:
        lines.extend(["Final EVAS transient setting:"])
        lines.append("")
        lines.append("```spectre")
        lines.extend(tran_lines)
        lines.append("```")
        lines.append("")

    if columns:
        lines.extend(
            [
                "Required public waveform columns in `tran.csv`:",
                "",
            ]
        )
        for chunk in _chunked(columns):
            lines.append("- `" + "`, `".join(chunk) + "`")
        lines.extend(
            [
                "",
                "Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.",
                "",
            ]
        )

    if family in {"end-to-end", "tb-generation"}:
        timing_lines: list[str] = []
        if reset_names:
            names = "`, `".join(reset_names)
            timing_lines.append(
                f"- Reset-like input(s) `{names}` must be asserted only for startup/explicit reset checks, then deasserted early enough and kept deasserted through the post-reset checking window."
            )
            timing_lines.append(
                "- For active-low resets such as `rstb`, `rst_n`, or `rst_ni`, avoid a finite-width pulse that returns the reset node low after release; use a waveform that remains high during checking."
            )
        if enable_names:
            names = "`, `".join(enable_names)
            timing_lines.append(
                f"- Enable-like input(s) `{names}` must be in the enabled state during the post-reset checking window unless the task explicitly asks for disabled intervals."
            )
        if clock_names:
            names = "`, `".join(clock_names[:6])
            timing_lines.append(
                f"- Clock-like input(s) `{names}` must provide enough valid edges after reset/enable for the checker to sample settled outputs."
            )
            timing_lines.append(
                "- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions."
            )
        if source_nodes:
            timing_lines.append(
                "- Public stimulus nodes used by the reference harness include: `"
                + "`, `".join(source_nodes[:12])
                + "`."
            )

        if timing_lines:
            lines.extend(["Timing/checking-window contract:", ""])
            lines.extend(timing_lines)
            lines.append("")

    if family in {"spec-to-va", "bugfix"}:
        lines.extend(
            [
                "The evaluator may use a fixed reference testbench with the timing and observable names above.",
                "Generate the requested DUT/fix so it behaves correctly under that public validation window.",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Append public evaluator contracts to task prompts.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--task", action="append", default=[])
    args = ap.parse_args()

    selected = set(args.task) if args.task else None
    changed: list[str] = []
    skipped: list[str] = []
    for task_id, task_dir in list_task_dirs(selected=selected):
        prompt_path = task_dir / "prompt.md"
        text = prompt_path.read_text(encoding="utf-8")
        if MARKER in text:
            skipped.append(task_id)
            continue
        contract = _build_contract(task_id, task_dir)
        changed.append(task_id)
        if not args.dry_run:
            prompt_path.write_text(text.rstrip() + "\n\n" + contract, encoding="utf-8")

    print(f"[prompt-contract-sync] changed={len(changed)} skipped={len(skipped)} dry_run={args.dry_run}")
    if changed:
        print("[prompt-contract-sync] changed tasks:")
        for task_id in changed:
            print(f"  - {task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
