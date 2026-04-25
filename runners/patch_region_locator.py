#!/usr/bin/env python3
"""Locate small Verilog-A repair regions from EVAS observation patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from generate import extract_module_signature
from observation_repair_policy import classify_observation_pattern, extract_observation_metrics


@dataclass(frozen=True)
class PatchRegion:
    file_path: Path
    start_line: int
    end_line: int
    kind: str
    score: int
    reason: str
    text: str


def _strip_comment(line: str) -> str:
    return line.split("//", 1)[0]


def _token_count(line: str, token: str) -> int:
    return len(re.findall(rf"\b{re.escape(token)}\b", _strip_comment(line)))


def _find_block(lines: list[str], start_idx: int) -> tuple[int, int] | None:
    """Return 0-based inclusive line range for the begin/end block at start."""
    begin_idx: int | None = None
    depth = 0
    for idx in range(start_idx, min(len(lines), start_idx + 8)):
        depth += _token_count(lines[idx], "begin")
        if _token_count(lines[idx], "begin") and begin_idx is None:
            begin_idx = idx
            break
    if begin_idx is None:
        return None

    depth = 0
    for idx in range(begin_idx, len(lines)):
        depth += _token_count(lines[idx], "begin")
        depth -= _token_count(lines[idx], "end")
        if depth <= 0:
            return start_idx, idx
    return None


def _find_analog_block(lines: list[str]) -> tuple[int, int] | None:
    for idx, line in enumerate(lines):
        if re.search(r"\banalog\s+begin\b", _strip_comment(line)):
            return _find_block(lines, idx)
    return None


def _find_output_assignment_regions(lines: list[str]) -> list[tuple[int, int]]:
    regions: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for idx, line in enumerate(lines):
        stripped_line = _strip_comment(line)
        if "<+" not in stripped_line or "V(" not in stripped_line:
            continue
        start = max(0, idx - 8)
        for prev in range(idx - 1, max(-1, idx - 9), -1):
            stripped = _strip_comment(lines[prev]).strip()
            if re.search(r"@\s*\(", stripped) or re.search(r"\banalog\s+begin\b", stripped):
                start = prev + 1
                break
        end = idx
        for nxt in range(idx + 1, min(len(lines), idx + 5)):
            stripped = _strip_comment(lines[nxt]).strip()
            if "<+" in stripped and "V(" in stripped:
                end = nxt
                continue
            break
        region = (start, end)
        if region not in seen:
            seen.add(region)
            regions.append(region)
    return regions


def _region_text(lines: list[str], start: int, end: int) -> str:
    return "\n".join(lines[start : end + 1])


def _score_region(pattern: str, kind: str, text: str, filename: str) -> tuple[int, str]:
    lowered = text.lower()
    score = 0
    reasons: list[str] = []

    if kind == "event_block":
        score += 20
        reasons.append("event block")
    elif kind == "timer_block":
        score += 18
        reasons.append("timer block")
    elif kind == "analog_block":
        score += 5
        reasons.append("analog fallback")
        # Use the whole analog block only when no tighter event/timer block is
        # plausible. This keeps the repair mechanically local.
        score -= 20
    elif kind == "output_assignment":
        score += 16
        reasons.append("output assignment")

    if pattern == "wrong_event_cadence_or_edge_count":
        for token in ("counter", "count", "toggle", "div", "ratio", "period", "lock"):
            if token in lowered or token in filename.lower():
                score += 8
                reasons.append(token)
    elif pattern == "missing_or_wrong_pulse_window":
        for token in ("up", "dn", "pulse", "release", "ref", "div", "edge"):
            if token in lowered or token in filename.lower():
                score += 8
                reasons.append(token)
        if kind == "output_assignment":
            score += 5
            reasons.append("pulse output")
    elif pattern == "stuck_or_wrong_digital_sequence":
        for token in ("state", "lfsr", "shift", "clk", "rst", "transition", "dpn", "out"):
            if token in lowered or token in filename.lower():
                score += 8
                reasons.append(token)
        if kind == "output_assignment":
            score += 12
            reasons.append("sequence output")
    elif pattern == "low_code_coverage_or_stuck_code_path":
        for token in ("code", "sample", "threshold", "quant", "dac", "dout", "vout", "vin"):
            if token in lowered or token in filename.lower():
                score += 8
                reasons.append(token)
    elif pattern == "wrong_analog_range_or_threshold_window":
        for token in ("threshold", "window", "scale", "transition", "vout", "span"):
            if token in lowered or token in filename.lower():
                score += 8
                reasons.append(token)
    else:
        for token in ("reset", "rst", "cross", "state", "output", "transition"):
            if token in lowered:
                score += 5
                reasons.append(token)

    # Prefer reasonably small regions over whole analog blocks when tied.
    line_count = text.count("\n") + 1
    if line_count <= 80:
        score += 6
    if line_count > 180:
        score -= 20
        reasons.append("large")

    return score, ", ".join(reasons[:8])


def locate_patch_regions(sample_dir: Path, evas_result: dict, limit: int = 5) -> list[PatchRegion]:
    notes = [str(note) for note in evas_result.get("evas_notes", [])]
    metrics = extract_observation_metrics(notes)
    pattern = classify_observation_pattern(notes, metrics).get("failure_pattern", "unclassified")

    regions: list[PatchRegion] = []
    for va_path in sorted(sample_dir.glob("*.va")):
        if not extract_module_signature(va_path):
            continue
        lines = va_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        seen: set[tuple[int, int]] = set()

        for idx, line in enumerate(lines):
            stripped = _strip_comment(line)
            kind = ""
            if re.search(r"@\s*\(\s*cross\s*\(", stripped):
                kind = "event_block"
            elif re.search(r"@\s*\(\s*timer\s*\(", stripped):
                kind = "timer_block"
            if not kind:
                continue
            block = _find_block(lines, idx)
            if not block or block in seen:
                continue
            seen.add(block)
            start, end = block
            text = _region_text(lines, start, end)
            score, reason = _score_region(str(pattern), kind, text, va_path.name)
            regions.append(
                PatchRegion(
                    file_path=va_path,
                    start_line=start + 1,
                    end_line=end + 1,
                    kind=kind,
                    score=score,
                    reason=reason,
                    text=text,
                )
            )

        analog = _find_analog_block(lines)
        if analog and analog not in seen:
            start, end = analog
            text = _region_text(lines, start, end)
            score, reason = _score_region(str(pattern), "analog_block", text, va_path.name)
            regions.append(
                PatchRegion(
                    file_path=va_path,
                    start_line=start + 1,
                    end_line=end + 1,
                    kind="analog_block",
                    score=score,
                    reason=reason,
                    text=text,
                )
            )

        for output_region in _find_output_assignment_regions(lines):
            if output_region in seen:
                continue
            start, end = output_region
            text = _region_text(lines, start, end)
            score, reason = _score_region(str(pattern), "output_assignment", text, va_path.name)
            regions.append(
                PatchRegion(
                    file_path=va_path,
                    start_line=start + 1,
                    end_line=end + 1,
                    kind="output_assignment",
                    score=score,
                    reason=reason,
                    text=text,
                )
            )

    return sorted(regions, key=lambda region: region.score, reverse=True)[:limit]


def replace_region(file_path: Path, region: PatchRegion, replacement: str) -> None:
    lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    replacement_lines = replacement.strip("\n").splitlines()
    start = region.start_line - 1
    end = region.end_line
    updated = lines[:start] + replacement_lines + lines[end:]
    file_path.write_text("\n".join(updated) + "\n", encoding="utf-8")
