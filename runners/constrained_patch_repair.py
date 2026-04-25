#!/usr/bin/env python3
"""EVAS-guided constrained patch repair prototype.

This runner is a small literature-guided alternative to whole-file repair.  It
still asks an LLM to produce complete code blocks because the project extractors
are file-oriented, but it adds two important controls before spending EVAS time:

1. A localized-patch protocol in the prompt.
2. A static guard that rejects layer/interface regressions before simulation.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from build_repair_prompt import build_evas_guided_repair_prompt, metric_gap_summary
from generate import call_model, extract_module_signature, read_meta
from observation_repair_policy import classify_observation_pattern, extract_observation_metrics
from run_adaptive_repair import (
    _classify_repair_layer,
    _concrete_diagnostics,
    _copy_sample,
    _failure_subtype,
    _freeze_gold_harness,
    _json_write,
    _load_env_file,
    _progress_rank,
    _score_quick,
    _task_lookup,
)
from run_model_assisted_loop import _model_slug, _save_generated_response


ROOT = Path(__file__).resolve().parents[1]


def _module_signatures(sample_dir: Path) -> dict[str, list[str]]:
    signatures: dict[str, list[str]] = {}
    for va_path in sorted(sample_dir.glob("*.va")):
        signature = extract_module_signature(va_path)
        if signature:
            name, ports = signature
            signatures[name] = ports
    return signatures


def _file_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _changed_lines(anchor_sample: Path, candidate_sample: Path) -> int:
    changed = 0
    for candidate in sorted(candidate_sample.glob("*.va")):
        anchor = anchor_sample / candidate.name
        if not anchor.exists():
            changed += len(candidate.read_text(encoding="utf-8", errors="ignore").splitlines())
            continue
        diff = difflib.unified_diff(
            _file_text(anchor).splitlines(),
            _file_text(candidate).splitlines(),
            lineterm="",
        )
        changed += sum(1 for line in diff if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))
    return changed


def _saved_relative_files(saved_files: list[str], sample_dir: Path) -> list[str]:
    rels: list[str] = []
    for raw in saved_files:
        path = Path(raw)
        try:
            rels.append(str(path.relative_to(sample_dir)))
        except ValueError:
            rels.append(path.name)
    return sorted(rels)


def _prune_behavior_extra_veriloga(anchor_sample: Path, candidate_sample: Path) -> list[str]:
    """Remove harness/helper Verilog-A files that are not part of the anchor DUT.

    The scorer treats generated samples as file-oriented artifacts.  In
    spec-to-VA tasks an extra gold helper `.va` can be sorted before the repaired
    DUT file and accidentally become the staged DUT.  For behavior-only repair,
    only the anchor DUT modules should remain editable/evaluable.
    """
    anchor_modules = _module_signatures(anchor_sample)
    if not anchor_modules:
        return []
    removed: list[str] = []
    for va_path in sorted(candidate_sample.glob("*.va")):
        signature = extract_module_signature(va_path)
        module_name = signature[0] if signature else va_path.stem
        if module_name in anchor_modules:
            continue
        va_path.unlink()
        removed.append(va_path.name)
    return removed


def _build_constrained_section(
    *,
    task_id: str,
    anchor_sample: Path,
    evas_result: dict,
    layer: str,
    max_changed_lines: int,
) -> str:
    notes = [str(note) for note in evas_result.get("evas_notes", [])]
    metrics = extract_observation_metrics(notes)
    policy = classify_observation_pattern(notes, metrics)
    signatures = _module_signatures(anchor_sample)
    signature_lines = [
        f"- `{name}({', '.join(ports)})`" for name, ports in sorted(signatures.items())
    ] or ["- No existing module signature was detected; preserve the task prompt signature exactly."]
    evidence = policy.get("evidence") or notes[:4]

    return "\n".join(
        [
            "",
            "# Constrained Localized Patch Protocol",
            "",
            "This repair must follow a localized patch workflow, not a full redesign.",
            "",
            f"- Task: `{task_id}`",
            f"- Current repair layer: `{layer}`",
            f"- Observation pattern: `{policy.get('failure_pattern', 'unclassified')}`",
            f"- Patch goal: {policy.get('patch_goal', 'make the smallest metric-moving edit')}",
            f"- Maximum intended Verilog-A changed lines: `{max_changed_lines}`",
            "",
            "Observable evidence:",
            *[f"- `{item}`" for item in evidence[:8]],
            "",
            "Module signatures that must remain valid:",
            *signature_lines,
            "",
            "Before editing, internally choose exactly one patch target region:",
            "- reset release / initialization",
            "- clock or cross event block",
            "- timer scheduling block",
            "- state update / counter terminal condition",
            "- bit mapping / output target assignment",
            "- threshold or analog output scale",
            "- interface/harness/save/tran only if EVAS evidence says CSV/runtime is broken",
            "",
            "Output rules:",
            "- Do not introduce a new top-level module name.",
            "- Do not rename existing ports or change their order.",
            "- Do not add an unrelated helper module for a behavior-only failure.",
            "- Do not edit the Spectre testbench for a behavior-only failure.",
            "- If you cannot repair locally, keep the existing interface and make the smallest behavior edit anyway.",
            "- Return only complete code blocks for files that truly need this local patch.",
        ]
    )


def _guard_candidate(
    *,
    task_id: str,
    anchor_sample: Path,
    candidate_sample: Path,
    saved_files: list[str],
    layer: str,
    max_changed_lines: int,
) -> dict:
    anchor_modules = _module_signatures(anchor_sample)
    candidate_modules = _module_signatures(candidate_sample)
    saved_rel = _saved_relative_files(saved_files, candidate_sample)
    reasons: list[str] = []

    if layer == "behavior":
        for module_name, ports in anchor_modules.items():
            if module_name not in candidate_modules:
                reasons.append(f"missing_anchor_module={module_name}")
                continue
            if candidate_modules[module_name] != ports:
                reasons.append(
                    f"port_signature_changed={module_name}:"
                    f"{candidate_modules[module_name]} != {ports}"
                )
        for saved in saved_rel:
            if not saved.endswith(".va"):
                continue
            signature = extract_module_signature(candidate_sample / saved)
            if not signature:
                reasons.append(f"saved_va_without_module_signature={saved}")
                continue
            module_name, _ports = signature
            if anchor_modules and module_name not in anchor_modules:
                reasons.append(f"new_behavior_module={module_name}")
        for module_name in candidate_modules:
            if anchor_modules and module_name not in anchor_modules:
                reasons.append(f"extra_behavior_module_after_harness_freeze={module_name}")

    if layer in {"observable", "runtime_interface", "compile_tb"}:
        if not sorted(candidate_sample.glob("*.scs")):
            reasons.append("no_spectre_testbench_after_repair")

    if not sorted(candidate_sample.glob("*.va")):
        reasons.append("no_veriloga_file_after_repair")

    changed = _changed_lines(anchor_sample, candidate_sample)
    if layer == "behavior" and changed > max_changed_lines:
        reasons.append(f"broad_va_rewrite_changed_lines={changed}>{max_changed_lines}")

    return {
        "passed": not reasons,
        "reasons": reasons,
        "layer": layer,
        "changed_va_lines": changed,
        "anchor_modules": anchor_modules,
        "candidate_modules": candidate_modules,
        "saved_files": saved_rel,
    }


def _guard_reject_result(task_id: str, anchor_result: dict, guard: dict) -> dict:
    result = json.loads(json.dumps(anchor_result))
    result["task_id"] = task_id
    result["status"] = anchor_result.get("status", "FAIL_SIM_CORRECTNESS")
    result.setdefault("evas_notes", [])
    result["evas_notes"] = [
        "constrained_patch_guard_rejected=" + ";".join(guard.get("reasons", [])),
        *result["evas_notes"],
    ]
    result["constrained_patch_guard"] = guard
    return result


def _load_result_or_score(
    *,
    args: argparse.Namespace,
    task_id: str,
    task_dir: Path,
    sample_dir: Path,
    out_root: Path,
    model_slug: str,
) -> dict:
    result_path = Path(args.initial_result_root) / task_id / "result.json" if args.initial_result_root else None
    if result_path and result_path.exists():
        return json.loads(result_path.read_text(encoding="utf-8"))
    return _score_quick(
        task_id=task_id,
        task_dir=task_dir,
        sample_dir=sample_dir,
        output_root=out_root / "round0",
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

    out_root = Path(args.output_root)
    gen_root = Path(args.generated_root) / model_slug / task_id
    gen_root.mkdir(parents=True, exist_ok=True)

    best_sample = source_sample
    best_result = _load_result_or_score(
        args=args,
        task_id=task_id,
        task_dir=task_dir,
        sample_dir=source_sample,
        out_root=out_root,
        model_slug=model_slug,
    )
    best_rank = _progress_rank(task_id, best_result)
    history: list[dict] = []

    print(f"[constrained] {task_id} R0 {best_result.get('status')} rank={best_rank}")

    for round_idx in range(1, args.max_rounds + 1):
        if best_result.get("status") == "PASS":
            break

        layer = _classify_repair_layer(best_result)
        prompt = build_evas_guided_repair_prompt(
            task_dir,
            best_sample,
            best_result,
            history=history,
            include_skill=args.include_skill,
            loop_context={
                "attempt_round": round_idx,
                "best_round": history[-1]["round"] if history else 0,
                "best_status": best_result.get("status"),
                "best_scores": best_result.get("scores", {}),
                "best_metric_gap": metric_gap_summary(task_dir, best_result),
                "best_failure_subtype": _failure_subtype(best_result),
            },
        )
        prompt += _build_constrained_section(
            task_id=task_id,
            anchor_sample=best_sample,
            evas_result=best_result,
            layer=layer,
            max_changed_lines=args.max_changed_lines,
        )

        sample_dir = gen_root / f"constrained_round{round_idx}"
        sample_dir.mkdir(parents=True, exist_ok=True)
        (sample_dir / "repair_prompt.md").write_text(prompt, encoding="utf-8")

        print(f"[constrained] CALL {model_slug}/{task_id} R{round_idx} ... ", end="", flush=True)
        response_text, usage = call_model(
            args.model,
            prompt,
            args.temperature if round_idx == 1 else max(args.temperature, 0.2),
            args.top_p,
            args.max_tokens,
        )
        (sample_dir / "raw_response.txt").write_text(response_text, encoding="utf-8")
        saved_files = _save_generated_response(
            response_text=response_text,
            sample_dir=sample_dir,
            family=read_meta(task_dir).get("family", "end-to-end"),
            task_dir=task_dir,
        )
        frozen_harness: list[str] = []
        pruned_veriloga: list[str] = []
        if layer == "behavior" and saved_files:
            frozen_harness = _freeze_gold_harness(task_dir, sample_dir)
            pruned_veriloga = _prune_behavior_extra_veriloga(best_sample, sample_dir)

        guard = _guard_candidate(
            task_id=task_id,
            anchor_sample=best_sample,
            candidate_sample=sample_dir,
            saved_files=saved_files,
            layer=layer,
            max_changed_lines=args.max_changed_lines,
        )
        _json_write(
            sample_dir / "generation_meta.json",
            {
                "model": args.model,
                "model_slug": model_slug,
                "task_id": task_id,
                "mode": "constrained-patch-repair-v1",
                "round": round_idx,
                "status": "generated" if saved_files else "no_code_extracted",
                "saved_files": saved_files,
                "frozen_gold_harness": frozen_harness,
                "pruned_behavior_veriloga": pruned_veriloga,
                "repair_layer": layer,
                "constrained_patch_guard": guard,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                **usage,
            },
        )
        print("guard_pass" if guard["passed"] else "guard_reject")

        if not saved_files:
            break

        if guard["passed"]:
            result = _score_quick(
                task_id=task_id,
                task_dir=task_dir,
                sample_dir=sample_dir,
                output_root=out_root / f"round{round_idx}",
                model_slug=model_slug,
                sample_idx=args.sample_idx,
                timeout_s=args.timeout_s,
                quick_maxstep=args.quick_maxstep,
            )
        else:
            result = _guard_reject_result(task_id, best_result, guard)
            _json_write(out_root / f"round{round_idx}" / task_id / "result.json", result)

        rank = _progress_rank(task_id, result)
        improved = rank > best_rank
        print(f"[constrained] {task_id} R{round_idx} {result.get('status')} improved={improved} rank={rank}")
        history.append(
            {
                "round": round_idx,
                "status": result.get("status"),
                "repair_layer": layer,
                "scores": result.get("scores", {}),
                "evas_notes": result.get("evas_notes", []),
                "concrete_diagnostics": _concrete_diagnostics(result),
                "metric_gap": metric_gap_summary(task_dir, result),
                "failure_subtype": _failure_subtype(result),
                "guard": guard,
                "progress_label": "improved" if improved else "stalled",
            }
        )
        if improved:
            best_sample = sample_dir
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
            "mode": "constrained-patch-repair-v1",
            "selected_sample": str(best_sample),
            "best_status": best_result.get("status"),
            "best_scores": best_result.get("scores", {}),
            "history": history,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    _json_write(out_root / "best" / task_id / "result.json", best_result)
    return best_result


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run constrained localized EVAS patch repair.")
    ap.add_argument("--model", default="kimi-k2.5")
    ap.add_argument("--task", action="append", default=[])
    ap.add_argument("--source-generated-dir", required=True)
    ap.add_argument("--initial-result-root", default="")
    ap.add_argument("--generated-root", default="generated-constrained-patch-repair")
    ap.add_argument("--output-root", default="results/constrained-patch-repair-2026-04-26")
    ap.add_argument("--sample-idx", type=int, default=0)
    ap.add_argument("--max-rounds", type=int, default=1)
    ap.add_argument("--timeout-s", type=int, default=60)
    ap.add_argument("--quick-maxstep", default="1n")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--max-changed-lines", type=int, default=160)
    ap.add_argument("--include-skill", action="store_true")
    ap.add_argument("--env-file", default=".env.table2")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    _load_env_file(Path(args.env_file))
    if not args.task:
        raise SystemExit("At least one --task is required for constrained repair.")
    tasks = _task_lookup(args.task)
    results = [run_task(args, task_id, task_dir) for task_id, task_dir in tasks]
    summary = {
        "model": args.model,
        "mode": "constrained-patch-repair-v1",
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
