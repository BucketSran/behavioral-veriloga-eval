#!/usr/bin/env python3
"""Mechanical region-replacement EVAS repair prototype."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from generate import call_model, extract_code_blocks, extract_module_signature
from observation_repair_policy import classify_observation_pattern, extract_observation_metrics
from patch_region_locator import PatchRegion, locate_patch_regions, replace_region
from repair_skill_cards import format_repair_skill_cards
from run_adaptive_repair import (
    _concrete_diagnostics,
    _copy_sample,
    _failure_subtype,
    _json_write,
    _load_env_file,
    _progress_rank,
    _score_quick,
    _task_lookup,
)
from run_model_assisted_loop import _model_slug


def _module_signatures(sample_dir: Path) -> dict[str, list[str]]:
    signatures: dict[str, list[str]] = {}
    for va_path in sorted(sample_dir.glob("*.va")):
        signature = extract_module_signature(va_path)
        if signature:
            name, ports = signature
            signatures[name] = ports
    return signatures


def _parse_replacement(response_text: str) -> str | None:
    blocks = extract_code_blocks(response_text)
    if blocks["va"]:
        return blocks["va"][0].strip()
    generic = re.search(r"```\s*\n(.*?)```", response_text, flags=re.DOTALL)
    if generic:
        return generic.group(1).strip()
    return None


def _parse_replacements(response_text: str, expected_count: int) -> list[str] | None:
    blocks = extract_code_blocks(response_text)
    replacements = [block.strip() for block in blocks["va"]]
    if not replacements:
        replacements = [
            match.group(1).strip()
            for match in re.finditer(r"```\s*\n(.*?)```", response_text, flags=re.DOTALL)
        ]
    if not replacements and expected_count == 1:
        single = _parse_replacement(response_text)
        replacements = [single] if single else []
    if len(replacements) < expected_count:
        return None
    return replacements[:expected_count]


def _static_patch_guard(anchor_sample: Path, candidate_sample: Path, replacements: list[str]) -> dict:
    reasons: list[str] = []
    joined_replacements = "\n".join(replacements)
    if re.search(r"\bmodule\b|\bendmodule\b", joined_replacements):
        reasons.append("replacement_contains_module_boundary")
    for idx, replacement in enumerate(replacements, start=1):
        if replacement.count("begin") < replacement.count("end") - 2:
            reasons.append(f"suspicious_unbalanced_begin_end_block_{idx}")

    anchor_modules = _module_signatures(anchor_sample)
    candidate_modules = _module_signatures(candidate_sample)
    if candidate_modules != anchor_modules:
        reasons.append(f"module_signatures_changed={candidate_modules}!={anchor_modules}")

    return {
        "passed": not reasons,
        "reasons": reasons,
        "anchor_modules": anchor_modules,
        "candidate_modules": candidate_modules,
    }


def _regions_overlap(left: PatchRegion, right: PatchRegion) -> bool:
    if left.file_path != right.file_path:
        return False
    return not (left.end_line < right.start_line or right.end_line < left.start_line)


def _select_patch_regions(regions: list[PatchRegion], count: int) -> list[PatchRegion]:
    selected: list[PatchRegion] = []
    for region in regions:
        if any(_regions_overlap(region, existing) for existing in selected):
            continue
        selected.append(region)
        if len(selected) >= count:
            break
    return selected


def _extract_cadence_closeness(result: dict) -> dict:
    joined = "\n".join(str(note) for note in result.get("evas_notes", []))
    ratio_match = re.search(r"\bratio_code=([0-9]+)", joined)
    hist_match = re.search(r"\binterval_hist=\{([^}]*)\}", joined)
    if not ratio_match or not hist_match:
        return {}
    ratio = int(ratio_match.group(1))
    keys = [int(key) for key in re.findall(r"([0-9]+)\s*:", hist_match.group(1))]
    if not keys:
        return {}
    gaps = [abs(key - ratio) for key in keys]
    return {
        "target": ratio,
        "measured_keys": keys,
        "min_abs_gap": min(gaps),
        "mean_abs_gap": sum(gaps) / len(gaps),
    }


def _metric_value(result: dict, key: str) -> float | None:
    metrics = extract_observation_metrics([str(note) for note in result.get("evas_notes", [])])
    value = metrics.get(key)
    return float(value) if isinstance(value, (int, float)) else None


def _extract_sequence_closeness(result: dict) -> dict:
    transitions = _metric_value(result, "transitions")
    hi_frac = _metric_value(result, "hi_frac")
    if transitions is None and hi_frac is None:
        return {}
    transition_score = min(transitions or 0.0, 4.0)
    balance_gap = abs((hi_frac if hi_frac is not None else 0.0) - 0.5)
    return {
        "transitions": transitions,
        "hi_frac": hi_frac,
        "transition_score": transition_score,
        "balance_gap": balance_gap,
    }


def _extract_pulse_closeness(result: dict) -> dict:
    keys = ("up_first", "dn_first", "up_second", "dn_second", "up_pulses_first", "dn_pulses_second")
    values = {key: _metric_value(result, key) for key in keys}
    if all(value is None for value in values.values()):
        return {}
    amplitude_sum = sum(value or 0.0 for key, value in values.items() if not key.endswith("pulses_first") and not key.endswith("pulses_second"))
    pulse_count = sum(value or 0.0 for key, value in values.items() if key.endswith("pulses_first") or key.endswith("pulses_second"))
    overlap = _metric_value(result, "overlap_frac") or 0.0
    return {
        "amplitude_sum": amplitude_sum,
        "pulse_count": pulse_count,
        "overlap_frac": overlap,
    }


def _fitness_rank(task_id: str, result: dict) -> tuple:
    base = _progress_rank(task_id, result)
    cadence = _extract_cadence_closeness(result)
    if cadence:
        # Smaller gap is better.  Keep this after the coarse compile/TB/phase
        # rank so closeness never beats a solved compile/runtime layer.
        return (
            *base,
            -float(cadence["min_abs_gap"]),
            -float(cadence["mean_abs_gap"]),
        )
    sequence = _extract_sequence_closeness(result)
    if sequence:
        return (
            *base,
            float(sequence["transition_score"]),
            -float(sequence["balance_gap"]),
        )
    pulse = _extract_pulse_closeness(result)
    if pulse:
        return (
            *base,
            float(pulse["pulse_count"]),
            float(pulse["amplitude_sum"]),
            -float(pulse["overlap_frac"]),
        )
    return (*base, -9999.0, -9999.0)


def _closeness_summary(result: dict) -> dict:
    return {
        "cadence": _extract_cadence_closeness(result),
        "sequence": _extract_sequence_closeness(result),
        "pulse": _extract_pulse_closeness(result),
    }


def _candidate_strategy(pattern: str, candidate_idx: int) -> list[str]:
    """Return generic diversity guidance selected by observation pattern."""
    idx = max(candidate_idx, 1)
    if pattern == "wrong_event_cadence_or_edge_count":
        strategies = [
            "Try a terminal-count correction: off-by-one, threshold, or reset of the event counter.",
            "Try an edge-interval correction: make measured intervals match the reported target ratio rather than changing the stimulus.",
            "Try a phase/accounting correction: preserve output toggling but change when count increments, clears, or lock is asserted.",
            "Try an odd/even segment correction: handle floor/ceil timing without changing ports or the testbench.",
        ]
    elif pattern == "missing_or_wrong_pulse_window":
        strategies = [
            "Try a latch-first correction: assert the pulse immediately on the relevant edge and clear opposing state safely.",
            "Try a release-timer correction: ensure the pulse remains finite and observable long enough for the checker.",
            "Try a mutual-exclusion correction: prevent overlap while still producing both requested pulse windows.",
            "Try a threshold/edge-order correction: make the edge detector match the public stimulus polarity.",
        ]
    elif pattern == "stuck_or_wrong_digital_sequence":
        strategies = [
            "Try a reset-release correction: ensure state leaves reset and is not reloaded in the checker window.",
            "Try a state-update correction: update the source-of-truth state exactly once per valid event.",
            "Try an output-mapping correction: keep the state but drive the observed output polarity/bit from the right state bit.",
            "Try an enable/clock-gating correction: avoid silently suppressing valid post-reset events.",
        ]
    elif pattern == "low_code_coverage_or_stuck_code_path":
        strategies = [
            "Try a sample-to-code correction: make the internal code vary with the observed input.",
            "Try a bit-drive correction: keep one source-of-truth code and drive all visible bits from it.",
            "Try an analog-output correction: drive vout from the same changing code path.",
            "Try a threshold/range correction: use thresholds that cover the public stimulus span.",
        ]
    else:
        strategies = [
            "Try the smallest reset or initialization correction.",
            "Try the smallest event trigger or state-update correction.",
            "Try the smallest output target or threshold correction.",
            "Try a different local mechanism than previous failed candidates.",
        ]
    return [strategies[(idx - 1) % len(strategies)]]


def _build_patch_prompt(
    task_id: str,
    regions: list[PatchRegion],
    evas_result: dict,
    history: list[dict],
    *,
    candidate_idx: int,
    candidates_per_round: int,
    candidate_attempts: list[dict],
) -> str:
    primary_region = regions[0]
    notes = [str(note) for note in evas_result.get("evas_notes", [])]
    metrics = extract_observation_metrics(notes)
    policy = classify_observation_pattern(notes, metrics)
    evidence = policy.get("evidence") or notes[:6]

    pattern = str(policy.get("failure_pattern", "unclassified"))
    lines = [
            "You are repairing a Verilog-A candidate by replacing one or more localized regions.",
            "",
            f"You must output exactly `{len(regions)}` fenced `verilog` code block(s), one replacement per selected region, in the same order.",
            "Do not output a full module. Do not include `module` or `endmodule` in any block.",
            "Preserve all module names, ports, file names, testbench behavior, save names, and transient setup.",
            "The replacement must be syntactically valid Verilog-A/Spectre AHDL.",
            "",
            f"Task: `{task_id}`",
            f"Primary file: `{primary_region.file_path.name}`",
            f"Failure pattern: `{pattern}`",
            f"Patch goal: {policy.get('patch_goal', 'move the reported EVAS metric')}",
            f"Candidate: `{candidate_idx}` of `{candidates_per_round}`",
            "",
            "EVAS evidence:",
            *[f"- `{item}`" for item in evidence[:8]],
    ]
    lines.extend(format_repair_skill_cards(notes, limit=2))
    if pattern == "wrong_event_cadence_or_edge_count":
        lines.extend(
            [
                "",
                "Cadence metric interpretation:",
                "- If EVAS reports `ratio_code=N` and `interval_hist={K: ...}`, the histogram key `K` is the measured number of input rising edges between adjacent output rising edges.",
                "- The target is `K == N`. If `K > N`, the output is too slow; if `K < N`, the output is too fast.",
                "- Repair the local counter/toggle/phase accounting so the measured interval moves toward the target ratio.",
            ]
        )
    lines.extend(
        [
            "",
            "Candidate diversity instruction:",
            *[f"- {item}" for item in _candidate_strategy(pattern, candidate_idx)],
            "- This candidate should use a different local mechanism than other candidates in this round.",
            "",
            "Selected regions to replace:",
        ]
    )
    for idx, region in enumerate(regions, start=1):
        lines.extend(
            [
                "",
                f"## Region {idx}",
                f"- File: `{region.file_path.name}`",
                f"- Lines: `{region.start_line}-{region.end_line}`",
                f"- Kind: `{region.kind}`",
                f"- Locator reason: `{region.reason}`",
                "```verilog",
                region.text,
                "```",
            ]
        )
    if history:
        lines.extend(
            [
                "",
                "Previous localized patch attempts that did not improve EVAS:",
            ]
        )
        for item in history[-4:]:
            patch_notes = item.get("evas_notes", [])[:4]
            selected = item.get("selected_regions") or [item.get("selected_region", {})]
            selected_text = ",".join(
                f"{region.get('file')}:{region.get('start_line')}-{region.get('end_line')}"
                for region in selected
            )
            lines.append(
                f"- Round {item.get('round')}: status={item.get('status')} "
                f"regions={selected_text}"
            )
            for note in patch_notes:
                lines.append(f"  - `{note}`")
        lines.extend(
            [
                "",
                "Do not repeat the same mechanism as failed attempts. Make a different local edit that targets the remaining EVAS metric.",
            ]
        )
    if candidate_attempts:
        lines.extend(
            [
                "",
                "Earlier candidates in this same round already failed; do not repeat them:",
            ]
        )
        for item in candidate_attempts[-4:]:
            lines.append(f"- Candidate {item.get('candidate_idx')}: status={item.get('status')}")
            for note in item.get("evas_notes", [])[:3]:
                lines.append(f"  - `{note}`")

    lines.extend(
        [
            "",
            "Return only the replacement region:",
        ]
    )
    return "\n".join(lines)


def _load_initial_result(args: argparse.Namespace, task_id: str, task_dir: Path, sample_dir: Path, output_root: Path, model_slug: str) -> dict:
    if args.initial_result_root:
        path = Path(args.initial_result_root) / task_id / "result.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return _score_quick(
        task_id=task_id,
        task_dir=task_dir,
        sample_dir=sample_dir,
        output_root=output_root / "round0",
        model_slug=model_slug,
        sample_idx=args.sample_idx,
        timeout_s=args.timeout_s,
        quick_maxstep=args.quick_maxstep,
    )


def run_task(args: argparse.Namespace, task_id: str, task_dir: Path) -> dict:
    model_slug = _model_slug(args.model)
    source_sample = Path(args.source_generated_dir) / model_slug / task_id / f"sample_{args.sample_idx}"
    if not source_sample.is_dir():
        raise SystemExit(f"Missing source sample: {source_sample}")

    output_root = Path(args.output_root)
    generated_task_root = Path(args.generated_root) / model_slug / task_id
    generated_task_root.mkdir(parents=True, exist_ok=True)

    best_sample = source_sample
    best_result = _load_initial_result(args, task_id, task_dir, source_sample, output_root, model_slug)
    best_rank = _fitness_rank(task_id, best_result)
    history: list[dict] = []
    print(f"[mechanical] {task_id} R0 {best_result.get('status')} rank={best_rank}")

    for round_idx in range(1, args.max_rounds + 1):
        if best_result.get("status") == "PASS":
            break

        regions = locate_patch_regions(best_sample, best_result, limit=args.region_limit)
        if not regions:
            print(f"[mechanical] {task_id} no_region")
            break
        selected_regions = _select_patch_regions(regions, args.regions_per_patch)
        if not selected_regions:
            print(f"[mechanical] {task_id} no_non_overlapping_region")
            break
        round_attempts: list[dict] = []
        best_candidate: dict | None = None

        for candidate_idx in range(1, args.candidates_per_round + 1):
            prompt = _build_patch_prompt(
                task_id,
                selected_regions,
                best_result,
                history,
                candidate_idx=candidate_idx,
                candidates_per_round=args.candidates_per_round,
                candidate_attempts=round_attempts,
            )
            round_dir = generated_task_root / f"mechanical_round{round_idx}_cand{candidate_idx}"
            _copy_sample(best_sample, round_dir)
            (round_dir / "patch_prompt.md").write_text(prompt, encoding="utf-8")
            (round_dir / "selected_region.json").write_text(
                json.dumps(
                    [
                        {
                            "file": region.file_path.name,
                            "start_line": region.start_line,
                            "end_line": region.end_line,
                            "kind": region.kind,
                            "score": region.score,
                            "reason": region.reason,
                        }
                        for region in selected_regions
                    ],
                    indent=2,
                ),
                encoding="utf-8",
            )

            print(
                f"[mechanical] CALL {model_slug}/{task_id} R{round_idx}C{candidate_idx} "
                f"{','.join(f'{region.file_path.name}:{region.start_line}-{region.end_line}' for region in selected_regions)} ... ",
                end="",
                flush=True,
            )
            response_text, usage = call_model(
                args.model,
                prompt,
                args.temperature if candidate_idx == 1 and round_idx == 1 else max(args.temperature, 0.35),
                args.top_p,
                args.max_tokens,
            )
            (round_dir / "raw_response.txt").write_text(response_text, encoding="utf-8")
            replacements = _parse_replacements(response_text, len(selected_regions))
            if not replacements:
                result = json.loads(json.dumps(best_result))
                result.setdefault("evas_notes", [])
                result["evas_notes"] = ["mechanical_patch_no_replacement_block", *result["evas_notes"]]
                guard = {"passed": False, "reasons": ["no_replacement_block"]}
                _json_write(output_root / f"round{round_idx}_cand{candidate_idx}" / task_id / "result.json", result)
                print("no_replacement")
            else:
                # Apply bottom-up within each file so earlier replacements do
                # not shift later line numbers.
                apply_items = sorted(
                    zip(selected_regions, replacements),
                    key=lambda item: (str(item[0].file_path), item[0].start_line),
                    reverse=True,
                )
                for region, replacement in apply_items:
                    target_file = round_dir / region.file_path.name
                    round_region = PatchRegion(
                        file_path=target_file,
                        start_line=region.start_line,
                        end_line=region.end_line,
                        kind=region.kind,
                        score=region.score,
                        reason=region.reason,
                        text=region.text,
                    )
                    replace_region(target_file, round_region, replacement)
                guard = _static_patch_guard(best_sample, round_dir, replacements)
                _json_write(
                    round_dir / "generation_meta.json",
                    {
                        "model": args.model,
                        "model_slug": model_slug,
                        "task_id": task_id,
                        "mode": "mechanical-region-patch-v1",
                        "round": round_idx,
                        "candidate_idx": candidate_idx,
                        "candidates_per_round": args.candidates_per_round,
                        "selected_regions": [
                            {
                                "file": region.file_path.name,
                                "start_line": region.start_line,
                                "end_line": region.end_line,
                                "kind": region.kind,
                                "score": region.score,
                                "reason": region.reason,
                            }
                            for region in selected_regions
                        ],
                        "static_guard": guard,
                        "replacement_lines": [len(replacement.splitlines()) for replacement in replacements],
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        **usage,
                    },
                )
                if not guard["passed"]:
                    result = json.loads(json.dumps(best_result))
                    result.setdefault("evas_notes", [])
                    result["evas_notes"] = ["mechanical_patch_guard_rejected=" + ";".join(guard["reasons"]), *result["evas_notes"]]
                    _json_write(output_root / f"round{round_idx}_cand{candidate_idx}" / task_id / "result.json", result)
                    print("guard_reject")
                else:
                    print("guard_pass")
                    result = _score_quick(
                        task_id=task_id,
                        task_dir=task_dir,
                        sample_dir=round_dir,
                        output_root=output_root / f"round{round_idx}_cand{candidate_idx}",
                        model_slug=model_slug,
                        sample_idx=args.sample_idx,
                        timeout_s=args.timeout_s,
                        quick_maxstep=args.quick_maxstep,
                    )

            rank = _fitness_rank(task_id, result)
            attempt = {
                "round": round_idx,
                "candidate_idx": candidate_idx,
                "sample_dir": str(round_dir),
                "status": result.get("status"),
                "scores": result.get("scores", {}),
                "evas_notes": result.get("evas_notes", []),
                "concrete_diagnostics": _concrete_diagnostics(result),
                "failure_subtype": _failure_subtype(result),
                "selected_regions": [
                    {
                        "file": region.file_path.name,
                        "start_line": region.start_line,
                        "end_line": region.end_line,
                        "kind": region.kind,
                        "score": region.score,
                        "reason": region.reason,
                    }
                    for region in selected_regions
                ],
                "guard": guard,
                "rank": list(rank),
                "closeness": _closeness_summary(result),
                "progress_label": "improved" if rank > best_rank else "stalled",
            }
            round_attempts.append(attempt)
            print(f"[mechanical] {task_id} R{round_idx}C{candidate_idx} {result.get('status')} rank={rank}")
            candidate_record = {"result": result, "rank": rank, "sample_dir": round_dir, "attempt": attempt}
            if best_candidate is None or rank > best_candidate["rank"]:
                best_candidate = candidate_record
            if result.get("status") == "PASS":
                break

        if best_candidate is None:
            break
        result = best_candidate["result"]
        rank = best_candidate["rank"]
        improved = rank > best_rank
        print(
            f"[mechanical] {task_id} R{round_idx} select C{best_candidate['attempt']['candidate_idx']} "
            f"{result.get('status')} improved={improved} rank={rank}"
        )
        history.append(
            {
                "round": round_idx,
                "status": result.get("status"),
                "scores": result.get("scores", {}),
                "evas_notes": result.get("evas_notes", []),
                "concrete_diagnostics": _concrete_diagnostics(result),
                "failure_subtype": _failure_subtype(result),
                "selected_regions": best_candidate["attempt"]["selected_regions"],
                "selected_candidate_idx": best_candidate["attempt"]["candidate_idx"],
                "candidate_attempts": round_attempts,
                "progress_label": "improved" if improved else "stalled",
            }
        )
        if improved:
            best_sample = best_candidate["sample_dir"]
            best_result = result
            best_rank = rank
        if result.get("status") == "PASS":
            break

    final_dir = Path(args.generated_root) / model_slug / task_id / f"sample_{args.sample_idx}"
    _copy_sample(best_sample, final_dir)
    _json_write(
        final_dir / "generation_meta.json",
        {
            "model": args.model,
            "model_slug": model_slug,
            "task_id": task_id,
            "mode": "mechanical-region-patch-v1",
            "selected_sample": str(best_sample),
            "best_status": best_result.get("status"),
            "best_scores": best_result.get("scores", {}),
            "history": history,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    _json_write(output_root / "best" / task_id / "result.json", best_result)
    return best_result


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run mechanical localized region replacement repair.")
    ap.add_argument("--model", default="kimi-k2.5")
    ap.add_argument("--task", action="append", default=[])
    ap.add_argument("--source-generated-dir", required=True)
    ap.add_argument("--initial-result-root", default="")
    ap.add_argument("--generated-root", default="generated-mechanical-patch-repair")
    ap.add_argument("--output-root", default="results/mechanical-patch-repair-2026-04-26")
    ap.add_argument("--sample-idx", type=int, default=0)
    ap.add_argument("--max-rounds", type=int, default=1)
    ap.add_argument("--candidates-per-round", type=int, default=1,
                    help="Generate and EVAS-score this many alternative snippets for the same localized region.")
    ap.add_argument("--regions-per-patch", type=int, default=1,
                    help="Replace up to this many non-overlapping localized regions per candidate.")
    ap.add_argument("--region-limit", type=int, default=5)
    ap.add_argument("--timeout-s", type=int, default=60)
    ap.add_argument("--quick-maxstep", default="1n")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--env-file", default=".env.table2")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    _load_env_file(Path(args.env_file))
    if not args.task:
        raise SystemExit("At least one --task is required.")
    tasks = _task_lookup(args.task)
    results = [run_task(args, task_id, task_dir) for task_id, task_dir in tasks]
    summary = {
        "model": args.model,
        "mode": "mechanical-region-patch-v1",
        "candidates_per_round": args.candidates_per_round,
        "tasks": len(results),
        "pass_count": sum(1 for result in results if result.get("status") == "PASS"),
        "results": [
            {
                "task_id": result.get("task_id"),
                "status": result.get("status"),
                "scores": result.get("scores", {}),
                "notes": result.get("evas_notes", [])[:8],
            }
            for result in results
        ],
    }
    _json_write(Path(args.output_root) / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
