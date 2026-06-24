#!/usr/bin/env python3
"""Build vaBench release v2 package-level indexes and evaluator metadata."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_config(root: Path, config_path: Path | None) -> dict:
    path = config_path or (root / "config" / "release_config.json")
    if not path.exists():
        raise FileNotFoundError(f"missing v2 release config: {path}")
    config = load_json(path)
    config["_config_path"] = path
    return config


def rel(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def forbidden_terms(agent_manifest: dict, spec_checker_map: dict) -> list[str]:
    terms: list[str] = []
    terms.extend(agent_manifest.get("leak_audit", {}).get("forbidden_phrases", []))
    terms.extend(spec_checker_map.get("auditor", {}).get("forbidden_public_terms", []))
    for link in spec_checker_map.get("requirement_links", []):
        terms.extend(link.get("private_policy_terms", []))
    return sorted({term for term in terms if term})


def output_path(root: Path, config: dict, key: str) -> Path:
    return root / config["outputs"][key]


def prompt_boundary_statuses(root: Path, config: dict) -> dict[str, str]:
    report_path = output_path(root, config, "prompt_boundary_audit")
    if not report_path.exists():
        return {}
    report = load_json(report_path)
    statuses: dict[str, str] = {}
    for item in report.get("results", []):
        task_id = item.get("task_id")
        if not task_id:
            continue
        statuses[task_id] = "pass" if item.get("status") == "PASS" else "fail"
    return statuses


def task_card_paths(root: Path, config: dict) -> list[Path]:
    discovery = config.get("task_discovery", {})
    globs = discovery.get("task_card_globs") or ["tasks/**/task_release_card.json"]
    paths: set[Path] = set()
    for pattern in globs:
        paths.update(root.glob(pattern))
    return sorted(paths)


def artifact_path(artifacts: dict, *keys: str, default: str) -> str:
    for key in keys:
        value = artifacts.get(key)
        if value:
            return value
    return default


def manifest_prompt_path(manifest: dict) -> str:
    return manifest.get("agent_prompt", "agent_prompt.md")


def manifest_spec_path(manifest: dict) -> str:
    return manifest.get("agent_visible_spec", "public/agent_visible_spec.md")


def task_form_rows(root: Path, repo_root: Path, config: dict, prompt_statuses: dict[str, str]) -> list[dict]:
    rows = []
    for release_task_path in task_card_paths(root, config):
        release_task = load_json(release_task_path)
        form_dir = release_task_path.parent
        artifacts = release_task["artifacts"]
        manifest_path = form_dir / artifact_path(
            artifacts,
            "agent_visible_files",
            default="agent_visible_files.json",
        )
        agent_manifest = load_json(manifest_path)
        spec_checker_map_path_raw = artifact_path(
            artifacts,
            "invisible_spec_checker_map",
            default="private/invisible_spec_checker_map.json",
        )
        spec_checker_map_path = form_dir / spec_checker_map_path_raw
        spec_checker_map = (
            load_json(spec_checker_map_path)
            if spec_checker_map_path.exists()
            else {"requirement_links": []}
        )
        counts = release_task.get("counts", {})
        certification = release_task.get("certification", {})
        provenance = release_task.get("provenance", {})
        agent_prompt = rel(
            form_dir
            / artifact_path(
                artifacts,
                "agent_prompt",
                default=manifest_prompt_path(agent_manifest),
            ),
            repo_root,
        )
        agent_visible_spec = rel(
            form_dir
            / artifact_path(
                artifacts,
                "agent_visible_spec",
                default=manifest_spec_path(agent_manifest),
            ),
            repo_root,
        )
        agent_visible_files = rel(manifest_path, repo_root)
        invisible_checker_config = rel(
            form_dir
            / artifact_path(
                artifacts,
                "invisible_checker_config",
                default="private/invisible_checker_config.yaml",
            ),
            repo_root,
        )
        invisible_spec_checker_map = rel(spec_checker_map_path, repo_root)
        prompt_boundary = prompt_statuses.get(
            release_task["id"],
            certification.get("prompt_boundary", "unknown"),
        )
        rows.append(
            {
                "task_id": release_task["id"],
                "release_entry_id": release_task["release_entry_id"],
                "form": release_task["family"],
                "level": release_task["level"],
                "track": release_task.get("track", ""),
                "difficulty": release_task.get("difficulty", ""),
                "category": release_task.get("category", ""),
                "base_function": release_task.get("base_function", ""),
                "score_surface": release_task.get("score_surface", ""),
                "release_task_manifest": rel(release_task_path, repo_root),
                "agent_prompt": agent_prompt,
                "agent_visible_spec": agent_visible_spec,
                "agent_visible_files": agent_visible_files,
                "public_support": [
                    rel(form_dir / path, repo_root) for path in map(Path, artifacts.get("public_support", []))
                ],
                "invisible_checker_config": invisible_checker_config,
                "invisible_spec_checker_map": invisible_spec_checker_map,
                "private_gold": [
                    rel(form_dir / path, repo_root) for path in map(Path, artifacts.get("private_gold", []))
                ],
                "prompt_boundary": prompt_boundary,
                "static": certification.get("static", "unknown"),
                "evas": certification.get("evas", "unknown"),
                "spectre": certification.get("spectre", "unknown"),
                "benchmark_score_candidate": bool(counts.get("benchmark_score_candidate", False)),
                "final_v2_score_enabled": bool(counts.get("final_v2_score_enabled", False)),
                "requires_fresh_v2_dual_certification": bool(
                    counts.get("requires_fresh_v2_dual_certification", True)
                ),
                "source_v1_release_task": provenance.get(
                    "source_v1_release_task",
                    release_task.get("migration", {}).get("source_task", ""),
                ),
                "forbidden_phrase_count": len(forbidden_terms(agent_manifest, spec_checker_map)),
                "requirement_link_count": len(spec_checker_map.get("requirement_links", [])),
            }
        )
    return rows


def entry_rows(forms: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in forms:
        grouped[row["release_entry_id"]].append(row)

    entries = []
    for entry_id, group in sorted(grouped.items()):
        first = group[0]
        final_score_enabled = all(row["final_v2_score_enabled"] for row in group)
        requires_fresh = any(row["requires_fresh_v2_dual_certification"] for row in group)
        entries.append(
            {
                "release_entry_id": entry_id,
                "level": first["level"],
                "track": first["track"],
                "difficulty": first["difficulty"],
                "category": first["category"],
                "base_function": first["base_function"],
                "forms": sorted(row["form"] for row in group),
                "form_count": len(group),
                "prompt_boundary": "pass" if all(row["prompt_boundary"] == "pass" for row in group) else "pending",
                "benchmark_score_candidate": any(row["benchmark_score_candidate"] for row in group),
                "final_v2_score_enabled": final_score_enabled,
                "requires_fresh_v2_dual_certification": requires_fresh,
                "counted_in_score": final_score_enabled and not requires_fresh,
            }
        )
    return entries


def summary(entries: list[dict], forms: list[dict]) -> dict:
    track_entry_counts = Counter(row["track"] for row in entries)
    track_form_counts = Counter(row["track"] for row in forms)
    difficulty_entry_counts = Counter(row["difficulty"] for row in entries)
    difficulty_form_counts = Counter(row["difficulty"] for row in forms)
    return {
        "entry_count": len(entries),
        "form_count": len(forms),
        "track_entry_counts": dict(sorted(track_entry_counts.items())),
        "track_form_counts": dict(sorted(track_form_counts.items())),
        "difficulty_entry_counts": dict(sorted(difficulty_entry_counts.items())),
        "difficulty_form_counts": dict(sorted(difficulty_form_counts.items())),
        "prompt_boundary_pass_form_count": sum(row["prompt_boundary"] == "pass" for row in forms),
        "spec_checker_map_form_count": sum(row["requirement_link_count"] > 0 for row in forms),
        "requirement_link_count": sum(row["requirement_link_count"] for row in forms),
        "score_candidate_entry_count": sum(row["benchmark_score_candidate"] for row in entries),
        "score_candidate_form_count": sum(row["benchmark_score_candidate"] for row in forms),
        "final_score_enabled_entry_count": sum(row["final_v2_score_enabled"] for row in entries),
        "final_score_enabled_form_count": sum(row["final_v2_score_enabled"] for row in forms),
        "fresh_dual_certification_pending_entry_count": sum(
            row["requires_fresh_v2_dual_certification"] for row in entries
        ),
        "fresh_dual_certification_pending_form_count": sum(
            row["requires_fresh_v2_dual_certification"] for row in forms
        ),
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_manifest_csv(path: Path, forms: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "task_id",
        "release_entry_id",
        "form",
        "level",
        "track",
        "difficulty",
        "category",
        "base_function",
        "prompt_boundary",
        "benchmark_score_candidate",
        "final_v2_score_enabled",
        "requires_fresh_v2_dual_certification",
        "release_task_manifest",
        "agent_prompt",
        "agent_visible_spec",
        "agent_visible_files",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in forms:
            writer.writerow({field: row[field] for field in fields})


def write_manifest_md(path: Path, generated_date: str, manifest: dict) -> None:
    summary_payload = manifest["summary"]
    lines = [
        "# vaBench Release v2 Package Manifest",
        "",
        f"Date: {generated_date}",
        "",
        "This manifest indexes migrated v2 task forms. It is package metadata,",
        "not fresh EVAS/Spectre certification evidence.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| entries | `{summary_payload['entry_count']}` |",
        f"| forms | `{summary_payload['form_count']}` |",
        f"| prompt-boundary pass forms | `{summary_payload['prompt_boundary_pass_form_count']}` |",
        f"| spec-checker map forms | `{summary_payload['spec_checker_map_form_count']}` |",
        f"| public/private requirement links | `{summary_payload['requirement_link_count']}` |",
        f"| score candidate forms | `{summary_payload['score_candidate_form_count']}` |",
        f"| final score-enabled forms | `{summary_payload['final_score_enabled_form_count']}` |",
        f"| fresh dual-certification pending forms | `{summary_payload['fresh_dual_certification_pending_form_count']}` |",
        "",
        "## Claim Boundary",
        "",
        "- v2 score claims remain disabled until fresh v2 EVAS/Spectre certification is available.",
        "- Agent prompts must be rendered from `agent_visible_files.json`, not from private evaluator files.",
        "- `task_release_card.json`, `private/*`, and gold assets must never be agent-visible.",
        "",
        "## Forms",
        "",
        "| Task | Form | Prompt Boundary | Score Enabled | Fresh Dual Pending |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in manifest["forms"]:
        lines.append(
            f"| `{row['task_id']}` | `{row['form']}` | `{row['prompt_boundary']}` | "
            f"`{row['final_v2_score_enabled']}` | `{row['requires_fresh_v2_dual_certification']}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def score_denominator(
    generated_date: str,
    root: Path,
    repo_root: Path,
    config: dict,
    entries: list[dict],
    forms: list[dict],
) -> dict:
    score_policy = config["score_policy"]
    form_rows = []
    for row in forms:
        exclusion_reasons = []
        if not row["final_v2_score_enabled"]:
            exclusion_reasons.append("fresh_v2_dual_certification_pending")
        form_rows.append(
            {
                "task_id": row["task_id"],
                "release_entry_id": row["release_entry_id"],
                "form": row["form"],
                "level": row["level"],
                "track": row["track"],
                "difficulty": row["difficulty"],
                "category": row["category"],
                "base_function": row["base_function"],
                "manifest": row["release_task_manifest"],
                "benchmark_score_candidate": row["benchmark_score_candidate"],
                "final_v2_score_enabled": row["final_v2_score_enabled"],
                "counted_in_score": row["final_v2_score_enabled"],
                "exclusion_reasons": exclusion_reasons,
            }
        )
    return {
        "date": generated_date,
        "release": config["release"],
        "status": score_policy["status"],
        "summary": {
            "entry_count": len(entries),
            "form_count": len(forms),
            "score_candidate_entry_count": sum(row["benchmark_score_candidate"] for row in entries),
            "score_candidate_form_count": sum(row["benchmark_score_candidate"] for row in forms),
            "counted_entry_count": sum(row["counted_in_score"] for row in entries),
            "counted_form_count": sum(row["counted_in_score"] for row in form_rows),
        },
        "claim_rule": {
            "source_of_truth": rel(output_path(root, config, "score_denominator"), repo_root),
            "score_claim_allowed": bool(score_policy["score_claim_allowed"]),
            "denominator_policy": score_policy["denominator_policy"],
        },
        "entry_rows": entries,
        "form_rows": form_rows,
    }


def evaluator_contract(generated_date: str, root: Path, repo_root: Path, config: dict, manifest: dict) -> dict:
    outputs = config["outputs"]
    schemas = config["schemas"]
    prompt_protocol = config["prompt_protocol"]
    score_policy = config["score_policy"]
    return {
        "date": generated_date,
        "release": config["release"],
        "status": config["status"],
        "contract_version": config["contract_version"],
        "inputs": {
            "release_config": rel(Path(config["_config_path"]), repo_root),
            "package_manifest": rel(root / outputs["package_manifest_json"], repo_root),
            "score_denominator": rel(root / outputs["score_denominator"], repo_root),
            "prompt_boundary_audit": rel(root / outputs["prompt_boundary_audit"], repo_root),
            "spec_checker_map_audit": rel(root / outputs["spec_checker_map_audit"], repo_root),
        },
        "schemas": {
            "agent_visible_files": rel(root / schemas["agent_visible_files"], repo_root),
            "task_release_card": rel(root / schemas["task_release_card"], repo_root),
            "invisible_spec_checker_map": rel(root / schemas["invisible_spec_checker_map"], repo_root),
        },
        "task_selection": {
            "source_of_truth": rel(root / outputs["score_denominator"], repo_root),
            "package_entry_count": manifest["summary"]["entry_count"],
            "package_form_count": manifest["summary"]["form_count"],
            "score_enabled": bool(score_policy["score_claim_allowed"]),
            "selection_rule": "Rows enter v2 scores only after prompt-boundary audit and fresh EVAS/Spectre certification.",
        },
        "prompt_protocol": {
            "agent_visible_source": prompt_protocol.get("agent_visible_source", ""),
            "agent_visible_spec_filename": prompt_protocol.get(
                "agent_visible_spec_filename",
                "public/agent_visible_spec.md",
            ),
            "agent_prompt_filename": prompt_protocol.get("agent_prompt_filename", "agent_prompt.md"),
            "public_support_dir": prompt_protocol["public_support_dir"],
            "private_dir": prompt_protocol["private_dir"],
            "hidden_sources": prompt_protocol["hidden_sources"],
            "renderer": rel(root / "scripts" / "render_agent_prompt.py", repo_root),
            "audit": rel(root / "scripts" / "audit_prompt_boundaries.py", repo_root),
            "spec_checker_map_audit": rel(root / "scripts" / "audit_spec_checker_map.py", repo_root),
        },
        "evaluation_protocol": config.get("evaluation_protocol", {}),
        "backend_roles": config["backend_roles"],
        "replaceability": config.get("replaceability", {}),
        "claim_gate": {
            "score_claim_allowed": bool(score_policy["score_claim_allowed"]),
            "blocking_reason": score_policy["score_claim_blocking_reason"],
        },
    }


def write_evaluator_md(path: Path, generated_date: str, evaluator: dict) -> None:
    lines = [
        "# vaBench Release v2 Evaluator Contract",
        "",
        f"Date: {generated_date}",
        "",
        f"Status: `{evaluator['status']}`",
        "",
        "## Prompt Protocol",
        "",
        f"- Agent-visible source: `{evaluator['prompt_protocol']['agent_visible_source']}`",
        f"- Agent-visible spec filename: `{evaluator['prompt_protocol']['agent_visible_spec_filename']}`",
        f"- Agent prompt filename: `{evaluator['prompt_protocol']['agent_prompt_filename']}`",
        "- Hidden sources:",
        *[f"  - `{item}`" for item in evaluator["prompt_protocol"]["hidden_sources"]],
        f"- Spec-checker map audit: `{evaluator['prompt_protocol']['spec_checker_map_audit']}`",
        "",
        "## Evaluation Protocol",
        "",
        f"- primary_track: `{evaluator.get('evaluation_protocol', {}).get('primary_track', 'unspecified')}`",
        f"- feedback_track: `{evaluator.get('evaluation_protocol', {}).get('feedback_track', 'unspecified')}`",
        f"- score_mixing_policy: {evaluator.get('evaluation_protocol', {}).get('score_mixing_policy', 'unspecified')}",
        "",
        "## Claim Gate",
        "",
        f"- score_claim_allowed: `{evaluator['claim_gate']['score_claim_allowed']}`",
        f"- blocking_reason: {evaluator['claim_gate']['blocking_reason']}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="benchmark-vabench-release-v2 root directory",
    )
    parser.add_argument("--config", type=Path, help="optional v2 release_config.json path")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()

    root = args.root
    repo_root = root.resolve().parent
    config = load_config(root, args.config)
    forms = task_form_rows(root, repo_root, config, prompt_boundary_statuses(root, config))
    entries = entry_rows(forms)
    package_manifest = {
        "date": args.date,
        "release": config["release"],
        "status": config["status"],
        "release_config": rel(Path(config["_config_path"]), repo_root),
        "package_root": rel(root, repo_root),
        "summary": summary(entries, forms),
        "entries": entries,
        "forms": forms,
    }

    write_json(output_path(root, config, "package_manifest_json"), package_manifest)
    write_manifest_csv(output_path(root, config, "package_manifest_csv"), forms)
    write_manifest_md(output_path(root, config, "package_manifest_md"), args.date, package_manifest)

    denominator = score_denominator(args.date, root, repo_root, config, entries, forms)
    write_json(output_path(root, config, "score_denominator"), denominator)

    evaluator = evaluator_contract(args.date, root, repo_root, config, package_manifest)
    write_json(output_path(root, config, "evaluator_json"), evaluator)
    write_evaluator_md(output_path(root, config, "evaluator_md"), args.date, evaluator)

    print(
        json.dumps(
            {
                "release": config["release"],
                "status": "PASS",
                "entry_count": len(entries),
                "form_count": len(forms),
                "config": rel(Path(config["_config_path"]), repo_root),
                "outputs": [
                    rel(output_path(root, config, "package_manifest_json"), repo_root),
                    rel(output_path(root, config, "package_manifest_csv"), repo_root),
                    rel(output_path(root, config, "package_manifest_md"), repo_root),
                    rel(output_path(root, config, "evaluator_json"), repo_root),
                    rel(output_path(root, config, "evaluator_md"), repo_root),
                    rel(output_path(root, config, "score_denominator"), repo_root),
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
