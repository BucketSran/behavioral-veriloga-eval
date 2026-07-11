#!/usr/bin/env python3
"""Build a hash-bound exact-five scoring view over a certified DUT release."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / "operations" / "tri_form_derivation_prep"
DEFAULT_BASE = ROOT / "release" / "dut-base-v3-catalog-certified"
DEFAULT_OUTPUT = ROOT / "release" / "dut-base-v3-exact-five-hash-bound-v2"


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
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def mutation_semantics(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "mutation_id": str(item["id"]),
        "fault_class": str(item.get("fault_class") or "unspecified"),
        "trigger_condition": str(item.get("trigger_condition") or "unspecified"),
        "violated_property_ids": sorted(str(value) for value in item.get("violated_property_ids") or []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-release", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--active-index", type=Path, default=PREP / "ACTIVE_MUTATION_SUITE_INDEX.json")
    parser.add_argument("--archive-index", type=Path, default=PREP / "EXCLUDED_MUTATION_ARCHIVE_INDEX.json")
    parser.add_argument("--overfive-review", type=Path, default=PREP / "OVERFIVE_REVIEW.json")
    parser.add_argument("--semantic-decisions", type=Path, required=True)
    args = parser.parse_args()

    base = args.base_release.resolve()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"output already exists: {output}")
    active_path = args.active_index.resolve()
    archive_path = args.archive_index.resolve()
    review_path = args.overfive_review.resolve()
    decision_path = args.semantic_decisions.resolve()
    active = read_json(active_path)
    archive = read_json(archive_path)
    review = read_json(review_path)
    decisions = read_json(decision_path)
    base_manifest = read_json(base / "score_denominator_manifest.json")

    active_by_family = {str(row["family_id"]): row for row in active.get("families") or []}
    archive_by_family = {str(row["family_id"]): row for row in archive.get("families") or []}
    review_by_family = {str(row["family_id"]): row for row in review.get("families") or []}
    decision_by_family = {str(row["family_id"]): row for row in decisions.get("families") or []}
    expected_ids = [f"{value:03d}" for value in range(1, 401)]
    if sorted(active_by_family) != expected_ids:
        raise SystemExit("active index must cover canonical families 001-400 exactly")
    if sorted(decision_by_family) != sorted(archive_by_family):
        raise SystemExit("semantic decisions must cover exactly the archived over-five families")

    shutil.copytree(base, output, copy_function=shutil.copy2)
    task_rows = []
    archive_rows = []
    semantic_rows = []
    total_catalog = 0
    total_active = 0
    for base_row in base_manifest.get("tasks") or []:
        family = str(base_row["canonical_dut_id"])
        release_dir = output / str(base_row["release_dir"])
        evaluator = release_dir / "evaluator"
        catalog_path = evaluator / "mutation_catalog.json"
        catalog = read_json(catalog_path)
        catalog_by_id = {str(item["id"]): item for item in catalog.get("mutations") or []}
        synchronized_active_ids = [str(value) for value in active_by_family[family]["testbench_suite"]]
        decision = decision_by_family.get(family)
        active_ids = [
            str(value) for value in (
                decision["active_mutation_ids"] if decision is not None else synchronized_active_ids
            )
        ]
        if len(active_ids) != 5 or len(set(active_ids)) != 5:
            raise SystemExit(f"{family}: active suite is not exactly five unique mutations")
        if not set(active_ids) <= set(catalog_by_id):
            raise SystemExit(f"{family}: active suite references mutations outside the catalog")
        excluded_ids = sorted(set(catalog_by_id) - set(active_ids))
        expected_excluded = sorted(
            str(value) for value in (
                decision["excluded_mutation_ids"] if decision is not None else []
            )
        )
        if excluded_ids != expected_excluded:
            raise SystemExit(f"{family}: archive and active suite do not partition the catalog")
        bugfix_seed = str(active_by_family[family]["bugfix_seed"])
        if bugfix_seed not in active_ids:
            raise SystemExit(f"{family}: bugfix seed is not part of the exact-five suite")

        active_mutations = []
        for mutation_id in active_ids:
            item = catalog_by_id[mutation_id]
            cert_rel = str((item.get("certification") or {}).get("evidence_path") or "")
            cert = release_dir / "evaluator" / "mutation_bundles" / mutation_id / "certification.json"
            bundle = release_dir / "evaluator" / "mutation_bundles" / mutation_id
            if not cert.is_file():
                raise SystemExit(f"{family}/{mutation_id}: missing catalog certification")
            status = item.get("certification") or {}
            if not (
                status.get("status") == "pass"
                and status.get("compile_status") == "pass"
                and status.get("simulation_status") == "pass"
                and status.get("behavior_status") == "killed_behaviorally"
            ):
                raise SystemExit(f"{family}/{mutation_id}: catalog certification is incomplete")
            active_mutations.append({
                **mutation_semantics(item),
                "certification_path": f"evaluator/mutation_bundles/{mutation_id}/certification.json",
                "source_catalog_certification_path": cert_rel,
                "certification_sha256": file_sha(cert),
                "mutation_bundle_sha256": tree_sha(bundle),
            })

        task_rows.append({
            "canonical_dut_id": family,
            "release_dir": base_row["release_dir"],
            "bugfix_seed": bugfix_seed,
            "active_mutation_count": 5,
            "active_mutations": active_mutations,
            "hashes": {
                "task_record_sha256": file_sha(evaluator / "task_record.json"),
                "task_certification_sha256": file_sha(evaluator / "certification.json"),
                "mutation_catalog_sha256": file_sha(catalog_path),
                "score_deck_sha256": file_sha(evaluator / "score_tb.scs"),
            },
        })
        total_catalog += len(catalog_by_id)
        total_active += len(active_ids)

        if excluded_ids:
            if decision is None:
                raise SystemExit(f"{family}: over-five catalog has no semantic decision")
            decision = {
                **decision,
                "synchronized_proposal": {
                    "active_mutation_ids": synchronized_active_ids,
                    "excluded_mutation_ids": sorted(
                        str(value["id"])
                        for value in (archive_by_family.get(family) or {}).get("excluded_mutations") or []
                    ),
                },
            }
            semantic_rows.append(decision)
            for mutation_id in excluded_ids:
                item = catalog_by_id[mutation_id]
                cert = release_dir / "evaluator" / "mutation_bundles" / mutation_id / "certification.json"
                archive_rows.append({
                    "family_id": family,
                    **mutation_semantics(item),
                    "archive_reason": str(decision["exclusion_reasons"][mutation_id]),
                    "certification_path": f"evaluator/mutation_bundles/{mutation_id}/certification.json",
                    "certification_sha256": file_sha(cert),
                    "mutation_bundle_sha256": tree_sha(cert.parent),
                    "status": "provenance_only",
                })

    if len(task_rows) != 400 or total_active != 2000 or total_catalog != 2051 or len(archive_rows) != 51:
        raise SystemExit(
            f"invalid totals tasks={len(task_rows)} active={total_active} catalog={total_catalog} archive={len(archive_rows)}"
        )
    selection_inputs = output / "selection_inputs"
    selection_inputs.mkdir()
    copied_inputs = {
        "base_release_score_denominator_manifest.json": base / "score_denominator_manifest.json",
        "ACTIVE_MUTATION_SUITE_INDEX.json": active_path,
        "EXCLUDED_MUTATION_ARCHIVE_INDEX.json": archive_path,
        "OVERFIVE_REVIEW.json": review_path,
        "SEMANTIC_SELECTION_DECISIONS.json": decision_path,
    }
    for name, source in copied_inputs.items():
        shutil.copy2(source, selection_inputs / name)
    inputs = {
        name: file_sha(selection_inputs / name)
        for name in sorted(copied_inputs)
    }
    denominator = {
        "schema_version": "v4-canonical-dut-exact-five-denominator-v1",
        "release_kind": "canonical_dut_base_exact_five",
        "canonical_range": ["001", "400"],
        "counted_task_count": 400,
        "active_mutation_count": 2000,
        "active_mutations_per_family": 5,
        "catalog_certified_mutation_count": 2051,
        "provenance_only_mutation_count": 51,
        "simulation_rerun_count": 0,
        "evidence_policy": "hash_reuse_from_catalog_certified_dut_base",
        "input_hashes": inputs,
        "tasks": task_rows,
    }
    denominator["content_sha256"] = canonical_sha(denominator)
    archive_manifest = {
        "schema_version": "v4-canonical-dut-provenance-archive-v1",
        "policy": "Certified mutations excluded from the exact-five scored suite remain immutable provenance-only evidence.",
        "mutation_count": len(archive_rows),
        "input_hashes": inputs,
        "mutations": archive_rows,
    }
    archive_manifest["content_sha256"] = canonical_sha(archive_manifest)
    semantic_manifest = {
        "schema_version": "v4-exact-five-semantic-selection-v1",
        "reviewed_family_count": len(semantic_rows),
        "policy": "Select by distinct observable fault semantics, property coverage, and trigger coverage; never by mutation ID order alone.",
        "families": sorted(semantic_rows, key=lambda row: row["family_id"]),
        "supplemental_exact_five_reviews": decisions.get("supplemental_exact_five_reviews") or [],
    }
    semantic_manifest["content_sha256"] = canonical_sha(semantic_manifest)
    write_json(output / "score_denominator_manifest.json", denominator)
    write_json(output / "provenance_only_mutation_archive.json", archive_manifest)
    write_json(output / "semantic_selection_review.json", semantic_manifest)
    print(json.dumps({
        "status": "PASS", "task_count": 400, "active_mutation_count": 2000,
        "archive_mutation_count": 51, "output": str(output),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
