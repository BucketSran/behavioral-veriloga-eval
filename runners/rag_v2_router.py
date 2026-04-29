#!/usr/bin/env python3
"""Prototype RAG-v2 router for closed-set 92 residual failures.

The router is intentionally inspectable.  It does not admit artifacts by
itself; it emits a JSON decision packet with query rewrite, candidate nodes,
slot coverage, negative-constraint checks, and recommended admission action.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from run_circuit_mechanism_rag_audit import build_knowledge_base, retrieve


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
LEDGER = ROOT / "docs" / "CLOSEDSET92_COMPLETION_LEDGER.json"
ARTIFACT_STORE = ROOT / "docs" / "VERIFIED_ARTIFACT_STORE.json"
TEMPLATE_STORE = ROOT / "docs" / "CLOSEDSET_CIRCUIT_TEMPLATES.json"
DEFAULT_OUT = ROOT / "results" / "rag-v2-router-audit-2026-04-29"
STATUS_MD = PROJECT / "coordination" / "status" / "2026-04-29_rag_upgrade_notes.md"


MECHANISM_TERMS: dict[str, dict[str, list[str]]] = {
    "dwa_rotating_pointer_window": {
        "required": ["clock", "code", "cell_outputs"],
        "positive": ["dwa", "pointer", "active cells", "unit cells", "window", "wrap", "overlap"],
        "negative": ["binary weighted dac", "not thermometer"],
    },
    "converter_quantize_reconstruct_or_decode": {
        "required": ["analog_input", "code_outputs", "analog_output", "width"],
        "positive": ["adc", "dac", "quantize", "reconstruct", "code", "vout", "sar", "binary"],
        "negative": ["not thermometer", "not unary", "arbitrary ordering"],
    },
    "pll_feedback_cadence": {
        "required": ["ref_clk", "feedback_or_divider", "output_or_lock", "ratio_or_frequency"],
        "positive": ["pll", "ref", "feedback", "divider", "lock", "ratio", "dco", "vctrl", "frequency"],
        "negative": ["independent free running", "no feedback"],
    },
    "phase_detector_pulse_relation": {
        "required": ["edge_a", "edge_b", "up_or_dn", "pulse_width"],
        "positive": ["pfd", "bbpd", "ref", "div", "up", "dn", "pulse", "phase", "edge"],
        "negative": ["generic pulse only", "single edge stream"],
    },
    "counter_or_divider_sequence": {
        "required": ["clock", "ratio_or_state", "output"],
        "positive": ["divider", "counter", "ratio", "edge", "toggle", "clock"],
        "negative": ["gray one bit"] ,
    },
    "lfsr_prbs_sequence": {
        "required": ["clock", "state", "output"],
        "positive": ["lfsr", "prbs", "xor", "feedback", "sequence"],
        "negative": ["counter"],
    },
    "comparator_threshold_hysteresis": {
        "required": ["input", "threshold", "output"],
        "positive": ["comparator", "threshold", "hysteresis", "cross", "vinp", "vinn"],
        "negative": ["oscillator"],
    },
    "sample_hold_track_latch": {
        "required": ["input", "sample_control", "output"],
        "positive": ["sample", "hold", "track", "droop", "aperture"],
        "negative": ["continuous buffer"],
    },
    "calibration_search_settle": {
        "required": ["code_or_trim", "metric", "settled_or_done"],
        "positive": ["calibration", "trim", "search", "settled", "done", "metric"],
        "negative": ["static code only"],
    },
    "serializer_frame_sequence": {
        "required": ["clock", "parallel_or_data", "serial_output", "frame"],
        "positive": ["serializer", "frame", "alignment", "bit", "sequence"],
        "negative": ["parallel only"],
    },
    "generic_voltage_behavior": {
        "required": ["input_or_time", "output"],
        "positive": ["ramp", "voltage", "time", "step", "grid"],
        "negative": [],
    },
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _rel(path: Path | str | None) -> str | None:
    if not path:
        return None
    try:
        return str(Path(path).resolve().relative_to(PROJECT.resolve()))
    except Exception:
        return str(path)


def _task_prompt(row: dict[str, Any]) -> str:
    task_dir = PROJECT / str(row.get("task_dir", ""))
    prompt = task_dir / "prompt.md"
    if prompt.exists():
        return prompt.read_text(encoding="utf-8", errors="ignore")
    return ""


def _negative_constraints(text: str, mechanism: str) -> list[str]:
    low = text.lower()
    out: list[str] = []
    if "not thermometer" in low or "not a thermometer" in low or "binary-weighted" in low:
        out.append("forbid_thermometer_unless_explicit_unit_cell")
    if "not gray" in low or ("binary counter" in low and "may flip multiple" in low):
        out.append("forbid_gray_counter")
    if "arbitrary" in low and ("ordering" in low or "monotonic" in low):
        out.append("forbid_monotonic_order_assumption")
    if mechanism == "pll_feedback_cadence" and "divider" in low and "lock" not in low and "feedback" not in low:
        out.append("prefer_standalone_divider_over_pll")
    return out


def _rewrite_query(row: dict[str, Any], prompt: str) -> tuple[str, str, list[str]]:
    mechanism = row["mechanism_family"]
    terms = MECHANISM_TERMS.get(mechanism, {})
    notes = " ".join(row.get("current_notes", []))
    positive = ", ".join(terms.get("positive", [])[:8])
    rewritten = (
        f"mechanism={mechanism}; task={row['task_id']}; family={row['family']}; "
        f"category={row.get('category','')}; desired_behavior={positive}; "
        f"failure_status={row['current_status']}; failure_notes={notes}"
    )
    hyde = (
        f"Ideal mechanism for {row['task_id']}: implement {mechanism} with shared internal state, "
        f"bind public ports and parameters, avoid Spectre-incompatible conditional transition contributions, "
        f"and satisfy the checker metrics implied by: {notes[:500]}"
    )
    negatives = _negative_constraints(f"{prompt}\n{notes}", mechanism)
    return rewritten, hyde, negatives


def _slot_coverage(row: dict[str, Any], prompt: str, hyde: str) -> dict[str, Any]:
    mechanism = row["mechanism_family"]
    required = MECHANISM_TERMS.get(mechanism, {}).get("required", [])
    hay = f"{row['task_id']} {row.get('category','')} {prompt} {hyde} {' '.join(row.get('current_notes', []))}".lower()
    synonyms = {
        "clock": ["clk", "clock", "edge"],
        "code": ["code", "din", "input", "bits"],
        "cell_outputs": ["cell", "unit", "enable", "out", "sel"],
        "analog_input": ["vin", "input", "analog", "stimulus", "sense"],
        "code_outputs": ["code", "bit", "b0", "b1", "output"],
        "analog_output": ["vout", "recon", "reconstruct", "analog output"],
        "width": ["bit", "width", "4b", "8b", "12bit", "16b"],
        "ref_clk": ["ref", "reference"],
        "feedback_or_divider": ["feedback", "fb", "div", "divider"],
        "output_or_lock": ["lock", "out", "output", "clk"],
        "ratio_or_frequency": ["ratio", "frequency", "freq", "period", "divide"],
        "edge_a": ["ref", "data", "input", "edge"],
        "edge_b": ["div", "feedback", "clock", "edge"],
        "up_or_dn": ["up", "dn", "bbpd", "phase"],
        "pulse_width": ["pulse", "width", "deadzone", "reset"],
        "ratio_or_state": ["ratio", "count", "state", "divide"],
        "output": ["out", "output", "y", "vout"],
        "state": ["state", "lfsr", "seed", "register"],
        "input": ["input", "vin", "in", "sense"],
        "threshold": ["threshold", "vth", "hysteresis", "cross"],
        "sample_control": ["sample", "hold", "clk", "control"],
        "code_or_trim": ["code", "trim", "cal", "search"],
        "metric": ["metric", "error", "offset", "measure"],
        "settled_or_done": ["settled", "done", "lock"],
        "parallel_or_data": ["parallel", "data", "frame", "byte"],
        "serial_output": ["serial", "out", "tx"],
        "frame": ["frame", "alignment", "word"],
        "input_or_time": ["input", "time", "ramp", "step"],
    }
    bound: list[str] = []
    missing: list[str] = []
    for slot in required:
        terms = synonyms.get(slot, [slot])
        if any(term in hay for term in terms):
            bound.append(slot)
        else:
            missing.append(slot)
    score = round(len(bound) / max(len(required), 1), 3)
    return {
        "score": score,
        "required_bound": bound,
        "missing_required": missing,
        "ambiguous": [],
    }


def _candidate_from_artifact(row: dict[str, Any], artifacts_by_task: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for artifact in artifacts_by_task.get(row["task_id"], []):
        source = artifact.get("source_kind")
        if source not in {"R26_verified", "condition-G", "I_repair"}:
            continue
        # Same-task artifacts are the strongest closed-set candidate even when
        # they still need real Spectre confirmation.  Keep the risk visible,
        # but route them before generic text templates.
        provenance = 1.25 if artifact.get("spectre_pass") is not True else 1.50
        decision = "exact_replay_requires_spectre" if source == "R26_verified" else "exact_replay_candidate"
        out.append(
            {
                "node_id": artifact["artifact_id"],
                "source_kind": "verified_or_teacher_artifact",
                "mechanism_label": artifact.get("mechanism_label"),
                "raw_score": provenance,
                "rerank_score": provenance,
                "slot_coverage": {"score": 1.0, "required_bound": ["same_task"], "missing_required": [], "ambiguous": []},
                "negative_constraints": {"violated": False, "matched_rules": [], "blocked_mechanisms": []},
                "verified_provenance": {
                    "confidence": provenance,
                    "source_rank": source,
                    "evas_pass": artifact.get("evas_pass"),
                    "spectre_pass": artifact.get("spectre_pass"),
                    "artifact_root": artifact.get("source_root"),
                    "validation_root": artifact.get("validation_root"),
                },
                "decision": decision,
                "reasons": ["same_task_artifact", f"source={source}"],
                "risks": [] if artifact.get("spectre_pass") is True else ["needs_real_spectre_confirmation"],
            }
        )
    return out


def _rerank_node(row: dict[str, Any], item: dict[str, Any], slot: dict[str, Any], negatives: list[str]) -> dict[str, Any]:
    node_id = str(item.get("node_id"))
    kind = str(item.get("kind"))
    mechanism = row["mechanism_family"]
    text = f"{node_id} {item.get('title','')}".lower()
    negative_violation = False
    blocked: list[str] = []
    if "forbid_thermometer_unless_explicit_unit_cell" in negatives and "thermometer" in text and "dwa" not in text:
        negative_violation = True
        blocked.append("thermometer")
    if "forbid_gray_counter" in negatives and "gray" in text:
        negative_violation = True
        blocked.append("gray")
    source_conf = {
        "mechanism_skeleton": 0.65,
        "r26_template": 0.70,
        "repair_card": 0.55,
        "prompt_template": 0.35,
        "veriloga_skill": 0.20,
    }.get(kind, 0.2)
    mech_match = 1.0 if any(part in text for part in mechanism.split("_")[:2]) else 0.5
    score = 0.30 * mech_match + 0.25 * slot["score"] + 0.20 * source_conf + 0.15 * min(float(item.get("score", 0.0)) / 20.0, 1.0) + 0.10
    if negative_violation:
        score -= 1.0
    return {
        "node_id": node_id,
        "source_kind": kind,
        "mechanism_label": mechanism,
        "raw_score": item.get("score"),
        "rerank_score": round(score, 4),
        "slot_coverage": slot,
        "negative_constraints": {
            "violated": negative_violation,
            "matched_rules": negatives,
            "blocked_mechanisms": blocked,
        },
        "verified_provenance": {
            "confidence": source_conf,
            "source_rank": kind,
            "source_path": item.get("source"),
        },
        "decision": "blocked_by_negative_constraint" if negative_violation else "use_for_materializer_or_prompt",
        "reasons": ["retrieved_by_rag_v0", f"kind={kind}"],
        "risks": ["low_slot_coverage"] if slot["score"] < 0.7 else [],
    }


def route(row: dict[str, Any], nodes: list[Any], artifacts_by_task: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    prompt = _task_prompt(row)
    rewritten, hyde, negatives = _rewrite_query(row, prompt)
    slot = _slot_coverage(row, prompt, hyde)
    query = "\n".join([prompt, rewritten, hyde, "negative_constraints " + " ".join(negatives)])
    raw = retrieve(nodes, query, top_k=12)
    candidates = _candidate_from_artifact(row, artifacts_by_task)
    candidates.extend(_rerank_node(row, item, slot, negatives) for item in raw)
    candidates.sort(key=lambda item: (-float(item.get("rerank_score", 0.0)), str(item.get("node_id"))))
    selected = candidates[0] if candidates else None
    action = "no_knowledge_coverage"
    if selected:
        if selected["source_kind"] == "verified_or_teacher_artifact":
            action = "exact_replay" if selected["verified_provenance"].get("spectre_pass") is True else "exact_replay_then_spectre"
        elif slot["score"] >= 0.7 and not selected["negative_constraints"]["violated"]:
            action = "slot_materializer"
        else:
            action = "rag_llm_repair_or_failure_packet"
    return {
        "task_id": row["task_id"],
        "query": {
            "rewritten_query": rewritten,
            "hyde_hypothesis": hyde,
            "functional_ir": {
                "mechanism_candidates": [row["mechanism_family"]],
                "positive_constraints": MECHANISM_TERMS.get(row["mechanism_family"], {}).get("positive", []),
                "negative_constraints": negatives,
                "failure_signature": row.get("current_notes", []),
            },
        },
        "candidates": candidates[:8],
        "admission": {
            "action": action,
            "min_slot_coverage_required": 0.7,
            "selected_node_id": selected.get("node_id") if selected else None,
            "slot_coverage": slot["score"],
            "stop_reason": None if selected else "no_candidates",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--only-failures", action="store_true", default=True)
    args = ap.parse_args()

    ledger = _read_json(LEDGER)
    store = _read_json(ARTIFACT_STORE)
    artifacts_by_task: dict[str, list[dict[str, Any]]] = {}
    for artifact in store.get("artifacts", []):
        artifacts_by_task.setdefault(str(artifact.get("task_id")), []).append(artifact)

    rows = ledger.get("tasks", [])
    if args.only_failures:
        rows = [row for row in rows if row.get("current_status") != "PASS"]

    nodes = build_knowledge_base(include_skills=False)
    routed = [route(row, nodes, artifacts_by_task) for row in rows]
    out_root = Path(args.output_dir)
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    out_root.mkdir(parents=True, exist_ok=True)
    result = {
        "version": "rag-v2-router-prototype-v0",
        "scope": "closed-set residual failures" if args.only_failures else "all tasks",
        "total": len(routed),
        "action_counts": dict(Counter(item["admission"]["action"] for item in routed)),
        "routes": routed,
    }
    (out_root / "router_results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (STATUS_MD).write_text(_markdown(result), encoding="utf-8")
    print(f"[rag-v2-router] wrote {out_root / 'router_results.json'}")
    print(f"[rag-v2-router] wrote {STATUS_MD}")
    print(f"[rag-v2-router] actions {result['action_counts']}")
    return 0


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# RAG-v2 Router Notes",
        "",
        "Date: 2026-04-29",
        "",
        "This is an inspectable router prototype for the current closed-set residual failures. It does not admit artifacts by itself.",
        "",
        f"- Scope: `{result['scope']}`",
        f"- Total routed tasks: `{result['total']}`",
        f"- Action counts: `{result['action_counts']}`",
        "",
        "## Routes",
        "",
        "| Task | Action | Selected | Slot Coverage | Top Risks |",
        "|---|---|---|---:|---|",
    ]
    for item in result["routes"]:
        cand = item["candidates"][0] if item["candidates"] else {}
        risks = ", ".join(cand.get("risks", []))
        lines.append(
            f"| `{item['task_id']}` | `{item['admission']['action']}` | "
            f"`{item['admission']['selected_node_id']}` | {item['admission']['slot_coverage']:.3f} | {risks} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `exact_replay_then_spectre` means a same-task R26/teacher artifact exists but needs real Spectre confirmation before strict admission.",
            "- `slot_materializer` means the router found enough slot coverage for a deterministic or semi-deterministic materializer attempt.",
            "- Low slot coverage should stop broad LLM repair and produce a failure packet.",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
