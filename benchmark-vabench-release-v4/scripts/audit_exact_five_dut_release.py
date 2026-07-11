#!/usr/bin/env python3
"""Audit exact-five DUT denominator counts, hashes, and catalog certification."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file():
            digest.update(item.relative_to(path).as_posix().encode())
            digest.update(b"\0")
            digest.update(file_sha(item).encode())
            digest.update(b"\0")
    return digest.hexdigest()


def canonical_sha(value: Any) -> str:
    value = dict(value)
    value.pop("content_sha256", None)
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    release = args.release.resolve()
    denominator = read_json(release / "score_denominator_manifest.json")
    archive = read_json(release / "provenance_only_mutation_archive.json")
    review = read_json(release / "semantic_selection_review.json")
    problems: list[str] = []
    rows = denominator.get("tasks") or []
    selection_inputs = release / "selection_inputs"
    for name, expected in (denominator.get("input_hashes") or {}).items():
        path = selection_inputs / name
        if not path.is_file() or file_sha(path) != expected:
            problems.append(f"selection input hash mismatch: {name}")
    if len(rows) != 400 or denominator.get("counted_task_count") != 400:
        problems.append("denominator does not contain exactly 400 tasks")
    ids = [str(row.get("canonical_dut_id") or "") for row in rows]
    if ids != [f"{value:03d}" for value in range(1, 401)]:
        problems.append("canonical task IDs are not exactly 001-400")
    active_pairs: set[tuple[str, str]] = set()
    catalog_pairs: set[tuple[str, str]] = set()
    release_dir_by_family = {str(row["canonical_dut_id"]): str(row["release_dir"]) for row in rows}
    for row in rows:
        family = str(row["canonical_dut_id"])
        evaluator = release / str(row["release_dir"]) / "evaluator"
        mutations = row.get("active_mutations") or []
        if len(mutations) != 5 or row.get("active_mutation_count") != 5:
            problems.append(f"{family}: active mutation count is not exactly five")
        if row.get("bugfix_seed") not in {item.get("mutation_id") for item in mutations}:
            problems.append(f"{family}: bugfix seed is outside the active suite")
        expected_hashes = {
            "task_record_sha256": file_sha(evaluator / "task_record.json"),
            "task_certification_sha256": file_sha(evaluator / "certification.json"),
            "mutation_catalog_sha256": file_sha(evaluator / "mutation_catalog.json"),
            "score_deck_sha256": file_sha(evaluator / "score_tb.scs"),
        }
        if row.get("hashes") != expected_hashes:
            problems.append(f"{family}: task-level hash binding mismatch")
        catalog = read_json(evaluator / "mutation_catalog.json")
        catalog_by_id = {str(item["id"]): item for item in catalog.get("mutations") or []}
        catalog_pairs.update((family, mutation_id) for mutation_id in catalog_by_id)
        for item in mutations:
            mutation_id = str(item["mutation_id"])
            active_pairs.add((family, mutation_id))
            source = catalog_by_id.get(mutation_id) or {}
            status = source.get("certification") or {}
            if not (
                status.get("status") == "pass"
                and status.get("compile_status") == "pass"
                and status.get("simulation_status") == "pass"
                and status.get("behavior_status") == "killed_behaviorally"
            ):
                problems.append(f"{family}/{mutation_id}: active catalog certification is incomplete")
            bundle = evaluator / "mutation_bundles" / mutation_id
            cert = bundle / "certification.json"
            if item.get("certification_path") != f"evaluator/mutation_bundles/{mutation_id}/certification.json":
                problems.append(f"{family}/{mutation_id}: release certification path mismatch")
            if not cert.is_file() or item.get("certification_sha256") != file_sha(cert):
                problems.append(f"{family}/{mutation_id}: certification hash mismatch")
            if item.get("mutation_bundle_sha256") != tree_sha(bundle):
                problems.append(f"{family}/{mutation_id}: mutation bundle hash mismatch")
    if len(active_pairs) != 2000 or denominator.get("active_mutation_count") != 2000:
        problems.append("active mutation denominator is not exactly 2000")
    archived = archive.get("mutations") or []
    archived_pairs = {(str(row["family_id"]), str(row["mutation_id"])) for row in archived}
    if len(archived_pairs) != 51 or archive.get("mutation_count") != 51:
        problems.append("provenance archive does not contain exactly 51 unique mutations")
    if active_pairs & archived_pairs:
        problems.append("active and provenance-only mutation sets overlap")
    if active_pairs | archived_pairs != catalog_pairs or len(catalog_pairs) != 2051:
        problems.append("active and provenance-only sets do not exactly partition the 2051-entry catalog")
    for row in archived:
        family = str(row["family_id"])
        mutation_id = str(row["mutation_id"])
        evaluator = release / release_dir_by_family[family] / "evaluator"
        bundle = evaluator / "mutation_bundles" / mutation_id
        cert = bundle / "certification.json"
        if row.get("certification_path") != f"evaluator/mutation_bundles/{mutation_id}/certification.json":
            problems.append(f"{family}/{mutation_id}: archived release certification path mismatch")
        catalog = read_json(evaluator / "mutation_catalog.json")
        source = next((item for item in catalog.get("mutations") or [] if str(item["id"]) == mutation_id), {})
        status = source.get("certification") or {}
        if not (
            status.get("status") == "pass"
            and status.get("compile_status") == "pass"
            and status.get("simulation_status") == "pass"
            and status.get("behavior_status") == "killed_behaviorally"
        ):
            problems.append(f"{family}/{mutation_id}: archived catalog certification is incomplete")
        if not cert.is_file() or row.get("certification_sha256") != file_sha(cert):
            problems.append(f"{family}/{mutation_id}: archived certification hash mismatch")
        if row.get("mutation_bundle_sha256") != tree_sha(bundle):
            problems.append(f"{family}/{mutation_id}: archived mutation bundle hash mismatch")
    if review.get("reviewed_family_count") != 36 or len(review.get("families") or []) != 36:
        problems.append("semantic review does not cover exactly 36 over-five families")
    supplemental = review.get("supplemental_exact_five_reviews") or []
    if {str(row.get("family_id")) for row in supplemental} != {"092", "098"}:
        problems.append("supplemental duplicate-semantic review does not cover 092 and 098")
    if any(not str(row.get("status") or "").startswith("approved_") for row in supplemental):
        problems.append("supplemental duplicate-semantic review contains an unresolved finding")
    for name, payload in (
        ("denominator", denominator), ("archive", archive), ("semantic review", review)
    ):
        if payload.get("content_sha256") != canonical_sha(payload):
            problems.append(f"{name} content hash mismatch")
    summary = {
        "status": "PASS" if not problems else "FAIL",
        "task_count": len(rows),
        "active_mutation_count": len(active_pairs),
        "archived_mutation_count": len(archived_pairs),
        "problem_count": len(problems),
        "problems": problems,
    }
    if args.output:
        args.output.resolve().write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
