#!/usr/bin/env python3
"""Audit LEGO-style functional skill retrieval on benchmark-v2 tasks."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from lego_skill_library import retrieve_lego_skills


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "benchmark-v2" / "manifests" / "v2-small.json"
DEFAULT_OUT = ROOT / "results" / "lego-skill-audit-v2-small-2026-04-29"


EXPECTED_SKILLS: dict[str, tuple[str, ...]] = {
    "adc_dac_quantize_reconstruct": ("adc_dac_quantize_reconstruct",),
    "adc_dac_quantize_reconstruct_plus_calibration": (
        "adc_dac_quantize_reconstruct",
        "calibration_search_settle",
    ),
    "binary_weighted_dac": ("dac_decode_binary_thermometer",),
    "binary_weighted_dac_with_segment_guard": (
        "dac_decode_binary_thermometer",
        "transition_glitch_guard",
    ),
    "dwa_rotating_pointer_window": ("dwa_pointer_window",),
    "dwa_plus_segmented_dac": ("dwa_pointer_window", "transition_glitch_guard"),
    "pfd_updn_reset_race": ("pfd_edge_pulse_window",),
    "pfd_plus_lock_detector": ("pfd_edge_pulse_window", "pll_feedback_cadence"),
    "divider_counter_ratio": ("divider_counter_ratio",),
    "binary_counter_ratio": ("divider_counter_ratio",),
    "divider_plus_event_feedback": ("divider_counter_ratio", "pfd_edge_pulse_window"),
    "sample_hold_discrete_update": ("sample_hold_track_latch",),
    "sample_hold_plus_calibration": ("sample_hold_track_latch", "calibration_search_settle"),
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _task_path(task_id: str) -> Path:
    return ROOT / "benchmark-v2" / "tasks" / task_id


def _row(task: dict[str, Any], *, top_k: int, use_meta_family: bool, use_meta_slots: bool) -> dict[str, Any]:
    task_id = str(task["task_id"])
    task_dir = _task_path(task_id)
    prompt = (task_dir / "prompt.md").read_text(encoding="utf-8")
    meta_path = task_dir / "meta.json"
    meta = _read_json(meta_path) if meta_path.exists() else {}
    result = retrieve_lego_skills(
        prompt,
        meta=meta,
        top_k=top_k,
        use_meta_family=use_meta_family,
        use_meta_slots=use_meta_slots,
    )
    expected_ordered = tuple(EXPECTED_SKILLS.get(str(task.get("mechanism_family", "")), ()))
    expected = set(expected_ordered)
    got = [str(item["skill_id"]) for item in result["skills"]]
    got_top3 = set(got[:3])
    got_topk = set(got[:top_k])
    return {
        "task_id": task_id,
        "mechanism_family": task.get("mechanism_family"),
        "perturbation_level": task.get("perturbation_level"),
        "expected_skill_all": list(expected_ordered),
        "top_skills": result["skills"],
        "functional_ir": result["functional_ir"],
        "top1_hit": bool(expected_ordered and got[:1] and got[0] == expected_ordered[0]),
        "top3_hit": bool(expected and expected <= got_top3),
        "topk_hit": bool(expected and expected <= got_topk),
        "top3_any_hit": bool(any(skill_id in expected for skill_id in got[:3])),
    }


def _summary(rows: list[dict[str, Any]], *, top_k: int) -> dict[str, Any]:
    total = len(rows)
    by_level: dict[str, Counter] = defaultdict(Counter)
    by_family: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        for bucket in (by_level[str(row.get("perturbation_level"))], by_family[str(row.get("mechanism_family"))]):
            bucket["total"] += 1
            bucket["top1"] += int(row["top1_hit"])
            bucket["top3"] += int(row["top3_hit"])
            bucket["topk"] += int(row["topk_hit"])
    return {
        "total": total,
        "top1": sum(int(row["top1_hit"]) for row in rows),
        "top3": sum(int(row["top3_hit"]) for row in rows),
        "topk": sum(int(row["topk_hit"]) for row in rows),
        "top_k": top_k,
        "top1_rate": round(sum(int(row["top1_hit"]) for row in rows) / total, 4) if total else 0.0,
        "top3_rate": round(sum(int(row["top3_hit"]) for row in rows) / total, 4) if total else 0.0,
        "topk_rate": round(sum(int(row["topk_hit"]) for row in rows) / total, 4) if total else 0.0,
        "miss_top3": [row["task_id"] for row in rows if not row["top3_hit"]],
        "by_perturbation": _counter_table(by_level),
        "by_family": _counter_table(by_family),
    }


def _counter_table(data: dict[str, Counter]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for key, counter in sorted(data.items()):
        total = int(counter["total"])
        out[key] = {
            "total": total,
            "top1": int(counter["top1"]),
            "top3": int(counter["top3"]),
            "topk": int(counter["topk"]),
            "top1_rate": round(counter["top1"] / total, 4) if total else 0.0,
            "top3_rate": round(counter["top3"] / total, 4) if total else 0.0,
            "topk_rate": round(counter["topk"] / total, 4) if total else 0.0,
        }
    return out


def _markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# LEGO Skill Retrieval Audit",
        "",
        "This audit checks whether benchmark-v2 perturbation prompts retrieve the expected type-level mechanism skill set. For composition prompts, Top-3/Top-k requires all expected LEGO blocks to be retrieved. It is retrieval evidence only; it does not claim LLM repair pass rate.",
        "",
        "## Setup",
        "",
        f"- Manifest: `{payload['manifest']}`",
        f"- Use task id / manifest family for routing: `{payload['use_meta_family']}`",
        f"- Use meta checker spec for slot binding: `{payload['use_meta_slots']}`",
        f"- Top-k: `{summary['top_k']}`",
        "",
        "## Summary",
        "",
        f"- Top-1 primary skill: `{summary['top1']}/{summary['total']}` (`{summary['top1_rate']:.4f}`)",
        f"- Top-3 full skill-set recall: `{summary['top3']}/{summary['total']}` (`{summary['top3_rate']:.4f}`)",
        f"- Top-{summary['top_k']} full skill-set recall: `{summary['topk']}/{summary['total']}` (`{summary['topk_rate']:.4f}`)",
        f"- Top-3 misses: `{', '.join(summary['miss_top3']) or 'none'}`",
        "",
        "## Rows",
        "",
        "| Task | Family | Perturbation | Expected Skill Set | Top-1 Primary | Top-3 All | Retrieved |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for row in payload["rows"]:
        top_ids = [str(item["skill_id"]) for item in row["top_skills"][:4]]
        lines.append(
            f"| `{row['task_id']}` | `{row['mechanism_family']}` | `{row['perturbation_level']}` | "
            f"`{', '.join(row['expected_skill_all'])}` | `{int(row['top1_hit'])}` | `{int(row['top3_hit'])}` | "
            f"`{', '.join(top_ids)}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A prompt-only hit means the router can recover the type-level mechanism from functional language, aliases, negative constraints, and public interface shape.",
            "- A miss should become either a new LEGO skill concept rule or a benchmark prompt-quality issue, not a task-id special case.",
            "- The next stage is to inject the selected skill packets into adaptive EVAS repair, then run final Spectre validation on EVAS-passing candidates.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    ap.add_argument("--output-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--top-k", type=int, default=4)
    ap.add_argument("--use-meta-family", action="store_true", help="allow manifest mechanism family as an oracle; off by default")
    ap.add_argument("--use-meta-slots", action="store_true", help="use public meta checker spec to improve slot binding")
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    manifest = _read_json(manifest_path)
    rows = [
        _row(
            task,
            top_k=args.top_k,
            use_meta_family=args.use_meta_family,
            use_meta_slots=args.use_meta_slots,
        )
        for task in manifest.get("tasks", [])
    ]
    payload = {
        "version": "lego-skill-audit-v1",
        "manifest": str(manifest_path),
        "use_meta_family": bool(args.use_meta_family),
        "use_meta_slots": bool(args.use_meta_slots),
        "summary": _summary(rows, top_k=args.top_k),
        "rows": rows,
    }

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "lego_skill_audit.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out / "summary.md").write_text(_markdown(payload), encoding="utf-8")
    print(f"[lego-audit] wrote {out / 'lego_skill_audit.json'}")
    print(f"[lego-audit] wrote {out / 'summary.md'}")
    print(
        "[lego-audit] "
        f"top1={payload['summary']['top1']}/{payload['summary']['total']} "
        f"top3={payload['summary']['top3']}/{payload['summary']['total']} "
        f"miss_top3={payload['summary']['miss_top3']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
