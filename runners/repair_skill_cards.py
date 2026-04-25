#!/usr/bin/env python3
"""Small metric-triggered repair knowledge cards.

This is intentionally not a full RAG system.  Cards are retrieved from EVAS
observable metrics and observation patterns so the repair loop gets only the
domain knowledge relevant to the current failure.
"""
from __future__ import annotations

from observation_repair_policy import classify_observation_pattern, extract_observation_metrics


CARDS = [
    {
        "id": "divider_edge_interval_repair",
        "patterns": {"wrong_event_cadence_or_edge_count"},
        "metrics": {"ratio_code", "interval_hist"},
        "text": [
            "For a programmable divider with ratio N, the checker may measure input rising edges between adjacent output rising edges.",
            "If `interval_hist={K: ...}`, target K is usually `ratio_code=N`.",
            "If K is about 2N, the implementation likely toggles every N input edges, making output rising-to-rising spacing too long.",
            "Repair high/low segment accounting or output rising-edge scheduling; do not change the testbench clock.",
            "For odd N, use floor/ceil segment lengths so adjacent output rising edges stay N input edges apart while duty is approximately balanced.",
        ],
    },
    {
        "id": "state_output_sequence_repair",
        "patterns": {"stuck_or_wrong_digital_sequence"},
        "metrics": {"transitions", "hi_frac"},
        "text": [
            "A stuck digital output usually requires checking both state update and output mapping.",
            "Updating an internal state is insufficient if the observed output is not driven from that state.",
            "If `transitions=0`, prioritize making the output target depend on a state bit that changes after reset.",
            "If `hi_frac` is 0 or 1, the output may be stuck at one polarity; inspect reset, enable gating, and selected output bit.",
            "Keep one source-of-truth state and drive the checker-visible output from it with an unconditional contribution.",
        ],
    },
    {
        "id": "pfd_paired_pulse_repair",
        "patterns": {"missing_or_wrong_pulse_window"},
        "metrics": {"up_first", "dn_first", "up_second", "dn_second", "up_pulses_first", "dn_pulses_second"},
        "text": [
            "A PFD pulse repair is usually paired: REF event, DIV event, and pulse release/clear logic must agree.",
            "REF-leading windows should produce a finite UP pulse; DIV-leading windows should produce a finite DN pulse.",
            "If all UP/DN amplitudes or pulse counts are zero, edge latching or output target assignment is missing.",
            "Avoid `transition()` inside conditional branches; update integer/real targets in conditionals and drive V(UP)/V(DN) unconditionally.",
            "Keep pulses finite and observable, and avoid UP/DN overlap.",
        ],
    },
]


def retrieve_repair_skill_cards(notes: list[str], limit: int = 2) -> list[dict]:
    metrics = extract_observation_metrics(notes)
    pattern = classify_observation_pattern(notes, metrics).get("failure_pattern", "unclassified")
    metric_names = set(metrics)
    scored: list[tuple[int, dict]] = []
    for card in CARDS:
        score = 0
        if pattern in card["patterns"]:
            score += 10
        score += len(metric_names & card["metrics"])
        if score > 0:
            scored.append((score, card))
    return [card for _score, card in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]]


def format_repair_skill_cards(notes: list[str], limit: int = 2) -> list[str]:
    cards = retrieve_repair_skill_cards(notes, limit=limit)
    if not cards:
        return []
    lines = [
        "",
        "Retrieved repair knowledge cards:",
    ]
    for card in cards:
        lines.append(f"- Card `{card['id']}`:")
        lines.extend(f"  - {item}" for item in card["text"])
    return lines
