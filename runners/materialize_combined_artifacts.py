#!/usr/bin/env python3
"""Materialize a combined generated tree from independently passing repairs.

This runner turns one-off overlay experiments into a reproducible artifact:

1. copy a base generated tree, usually a full92 condition such as H-on-F;
2. scan candidate score roots for task-level PASS results;
3. replace only base tasks that are not already Pass@1, unless requested;
4. copy the candidate's scored sample directory into the output tree;
5. write an auditable overlay manifest and a short Markdown report.

It does not score anything and does not call a model. Run ``score.py`` on the
materialized output tree to verify the combined full benchmark result.
"""
from __future__ import annotations

import argparse
import glob
import json
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Candidate:
    task_id: str
    score_root: Path
    result_path: Path
    sample_dir: Path
    result: dict
    reason: str = ""


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _normalized_required_axes(required_axes: list[str]) -> list[str]:
    aliases = {
        "syntax": "dut_compile",
        "routing": "tb_compile",
        "simulation": "sim_correct",
        "behavior": "sim_correct",
    }
    normalized: list[str] = []
    for axis in required_axes:
        mapped = aliases.get(axis, axis)
        if mapped not in normalized:
            normalized.append(mapped)
    return normalized


def _task_pass(result: dict) -> bool:
    scores = result.get("scores", {})
    required = _normalized_required_axes(
        result.get("required_axes", ["dut_compile", "tb_compile", "sim_correct"])
    )
    return all(float(scores.get(axis, 0.0)) >= 1.0 for axis in required)


def _result_status(result: dict) -> str:
    return str(result.get("status", ""))


def _base_results(base_score: Path) -> dict[str, dict]:
    results: dict[str, dict] = {}
    for path in sorted(base_score.glob("*/result.json")):
        try:
            results[path.parent.name] = _read_json(path)
        except Exception:
            continue
    return results


def _model_slug(base_generated: Path, requested: str) -> str:
    if requested:
        return requested
    model_dirs = sorted(path.name for path in base_generated.iterdir() if path.is_dir())
    if len(model_dirs) == 1:
        return model_dirs[0]
    if "kimi-k2.5" in model_dirs:
        return "kimi-k2.5"
    raise SystemExit(
        "Could not infer model slug from base generated tree. "
        "Pass --model-slug explicitly."
    )


def _candidate_roots(explicit: list[str], patterns: list[str]) -> list[Path]:
    roots: list[Path] = []
    for raw in explicit:
        roots.append(Path(raw))
    for pattern in patterns:
        for match in sorted(glob.glob(pattern)):
            roots.append(Path(match))
    deduped: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        resolved = str(root.resolve())
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(root)
    return deduped


def _sample_dir_from_result(result: dict) -> Path | None:
    artifacts = result.get("artifacts", {})
    for key in ("dut_path", "tb_path"):
        raw = artifacts.get(key)
        if raw:
            path = Path(raw)
            if path.exists():
                return path.parent
    return None


def _sample_complete(sample_dir: Path) -> tuple[bool, str]:
    if not sample_dir.exists():
        return False, "sample_dir_missing"
    if not any(sample_dir.glob("*.va")):
        return False, "missing_va"
    return True, "ok"


def _scan_candidates(candidate_roots: list[Path]) -> tuple[dict[str, Candidate], list[dict]]:
    selected: dict[str, Candidate] = {}
    rejected: list[dict] = []

    for root in candidate_roots:
        if not root.exists():
            rejected.append({"score_root": str(root), "reason": "score_root_missing"})
            continue
        for result_path in sorted(root.glob("*/result.json")):
            task_id = result_path.parent.name
            try:
                result = _read_json(result_path)
            except Exception as exc:
                rejected.append(
                    {
                        "task_id": task_id,
                        "score_root": str(root),
                        "result_path": str(result_path),
                        "reason": f"result_json_unreadable:{exc}",
                    }
                )
                continue
            if _result_status(result) != "PASS" or not _task_pass(result):
                rejected.append(
                    {
                        "task_id": task_id,
                        "score_root": str(root),
                        "result_path": str(result_path),
                        "reason": "not_pass",
                        "status": _result_status(result),
                        "scores": result.get("scores", {}),
                    }
                )
                continue
            sample_dir = _sample_dir_from_result(result)
            if sample_dir is None:
                rejected.append(
                    {
                        "task_id": task_id,
                        "score_root": str(root),
                        "result_path": str(result_path),
                        "reason": "missing_artifact_sample_path",
                    }
                )
                continue
            ok, reason = _sample_complete(sample_dir)
            if not ok:
                rejected.append(
                    {
                        "task_id": task_id,
                        "score_root": str(root),
                        "result_path": str(result_path),
                        "sample_dir": str(sample_dir),
                        "reason": reason,
                    }
                )
                continue

            candidate = Candidate(
                task_id=task_id,
                score_root=root,
                result_path=result_path,
                sample_dir=sample_dir,
                result=result,
                reason="candidate_pass",
            )
            current = selected.get(task_id)
            if current is None or result_path.stat().st_mtime >= current.result_path.stat().st_mtime:
                selected[task_id] = candidate

    return selected, rejected


def _copy_base(base_generated: Path, out_generated: Path, *, overwrite: bool, dry_run: bool) -> None:
    if out_generated.exists():
        if not overwrite:
            raise SystemExit(f"Output generated tree exists; pass --overwrite: {out_generated}")
        if not dry_run:
            shutil.rmtree(out_generated)
    if not dry_run:
        shutil.copytree(base_generated, out_generated)


def _materialize(
    *,
    base_generated: Path,
    base_score: Path,
    out_generated: Path,
    model_slug: str,
    candidates: dict[str, Candidate],
    rejected: list[dict],
    allow_replace_pass: bool,
    overwrite: bool,
    dry_run: bool,
) -> dict:
    base = _base_results(base_score)
    if not base:
        raise SystemExit(f"No per-task result.json files found under base score: {base_score}")

    _copy_base(base_generated, out_generated, overwrite=overwrite, dry_run=dry_run)

    replacements: list[dict] = []
    skipped: list[dict] = []
    for task_id, candidate in sorted(candidates.items()):
        base_result = base.get(task_id)
        if base_result is None:
            skipped.append(
                {
                    "task_id": task_id,
                    "score_root": str(candidate.score_root),
                    "reason": "task_not_in_base_score",
                }
            )
            continue
        base_pass = _task_pass(base_result)
        if base_pass and not allow_replace_pass:
            skipped.append(
                {
                    "task_id": task_id,
                    "score_root": str(candidate.score_root),
                    "reason": "base_already_pass",
                }
            )
            continue

        dst = out_generated / model_slug / task_id / "sample_0"
        base_task_dir = base_generated / model_slug / task_id
        if not dst.parent.exists() and not (dry_run and base_task_dir.exists()):
            skipped.append(
                {
                    "task_id": task_id,
                    "score_root": str(candidate.score_root),
                    "reason": "task_not_in_base_generated_tree",
                    "destination": str(dst),
                }
            )
            continue
        if not dry_run:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(candidate.sample_dir, dst)
        replacements.append(
            {
                "task_id": task_id,
                "base_status": _result_status(base_result),
                "base_scores": base_result.get("scores", {}),
                "score_root": str(candidate.score_root),
                "result_path": str(candidate.result_path),
                "sample_dir": str(candidate.sample_dir),
                "destination": str(dst),
                "candidate_status": _result_status(candidate.result),
                "candidate_scores": candidate.result.get("scores", {}),
                "candidate_notes": candidate.result.get("evas_notes", [])[:12],
            }
        )

    manifest = {
        "version": 1,
        "base_generated": str(base_generated),
        "base_score": str(base_score),
        "output_generated": str(out_generated),
        "model_slug": model_slug,
        "allow_replace_pass": allow_replace_pass,
        "dry_run": dry_run,
        "base_tasks": len(base),
        "base_pass_count": sum(1 for result in base.values() if _task_pass(result)),
        "candidate_pass_tasks": len(candidates),
        "replacement_count": len(replacements),
        "replacements": replacements,
        "skipped": skipped,
        "rejected": rejected,
    }
    if not dry_run:
        _write_json(out_generated / "overlay_manifest.json", manifest)
    return manifest


def _write_report(path: Path, manifest: dict) -> None:
    lines = [
        "# Combined Artifact Materialization Report",
        "",
        "## Summary",
        "",
        f"- Base generated: `{manifest['base_generated']}`",
        f"- Base score: `{manifest['base_score']}`",
        f"- Output generated: `{manifest['output_generated']}`",
        f"- Base Pass@1 count: `{manifest['base_pass_count']}/{manifest['base_tasks']}`",
        f"- Candidate pass tasks: `{manifest['candidate_pass_tasks']}`",
        f"- Replacements: `{manifest['replacement_count']}`",
        "",
        "## Replacements",
        "",
        "| Task | Base | Candidate root | Notes |",
        "|---|---|---|---|",
    ]
    for item in manifest.get("replacements", []):
        notes = "; ".join(str(note) for note in item.get("candidate_notes", [])[-3:])
        lines.append(
            f"| `{item['task_id']}` | `{item['base_status']}` | "
            f"`{item['score_root']}` | {notes} |"
        )
    lines.extend(
        [
            "",
            "## Skipped",
            "",
            "| Task | Reason |",
            "|---|---|",
        ]
    )
    for item in manifest.get("skipped", []):
        lines.append(f"| `{item.get('task_id', '-')}` | `{item.get('reason', '-')}` |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-generated", required=True)
    parser.add_argument("--base-score", required=True)
    parser.add_argument("--out-generated", required=True)
    parser.add_argument("--model-slug", default="")
    parser.add_argument("--candidate-score", action="append", default=[])
    parser.add_argument(
        "--candidate-score-glob",
        action="append",
        default=[],
        help="Glob for candidate score roots, e.g. 'results/*final-score'.",
    )
    parser.add_argument("--allow-replace-pass", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report-out", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_generated = Path(args.base_generated)
    base_score = Path(args.base_score)
    out_generated = Path(args.out_generated)
    model_slug = _model_slug(base_generated, args.model_slug)
    candidate_roots = _candidate_roots(args.candidate_score, args.candidate_score_glob)
    if not candidate_roots:
        raise SystemExit("No candidate score roots supplied")

    candidates, rejected = _scan_candidates(candidate_roots)
    manifest = _materialize(
        base_generated=base_generated,
        base_score=base_score,
        out_generated=out_generated,
        model_slug=model_slug,
        candidates=candidates,
        rejected=rejected,
        allow_replace_pass=args.allow_replace_pass,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )
    report_out = Path(args.report_out) if args.report_out else out_generated / "overlay_report.md"
    if not args.dry_run:
        _write_report(report_out, manifest)
    print(
        json.dumps(
            {
                "base_tasks": manifest["base_tasks"],
                "base_pass_count": manifest["base_pass_count"],
                "candidate_pass_tasks": manifest["candidate_pass_tasks"],
                "replacement_count": manifest["replacement_count"],
                "output_generated": str(out_generated),
                "manifest": str(out_generated / "overlay_manifest.json"),
                "report": str(report_out),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
