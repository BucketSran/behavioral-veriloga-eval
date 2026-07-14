#!/usr/bin/env python3
"""Audit the standalone 1,200-task benchmarkv4 release package."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RELEASE = PACKAGE_ROOT / "release" / "benchmarkv4"
DEFAULT_SOURCE = PACKAGE_ROOT / "provenance" / "dut-base-v3-exact-five-hash-bound-v2"
FORMS = ("dut", "testbench", "bugfix")
MODES = ("G0", "G1", "G2", "G3", "G4", "G5")
DIRECT_MODES = {"G0", "G1"}
AGENTIC_MODES = {"G2", "G3", "G4", "G5"}
WRAPPERS_BY_MODE = {
    "G0": "direct_wrapper.md",
    "G1": "direct_wrapper.md",
    "G2": "agentic_wrapper.md",
    "G3": "agentic_wrapper.md",
    "G4": "agentic_wrapper.md",
    "G5": "agentic_wrapper.md",
}
FORM_SKILLS = {
    "dut": "dut_modeling.md",
    "testbench": "testbench_verification.md",
    "bugfix": "bugfix_diagnosis.md",
}
FEEDBACK_GUIDES = {
    "dut": "feedback_dut.md",
    "testbench": "feedback_testbench.md",
    "bugfix": "feedback_bugfix.md",
}
MATERIALIZED_ARTIFACTS = (
    "TASK_INDEX.json",
    "BUGFIX_SEED_REVIEW.json",
    "prompt_modes/modes.json",
    "prompt_modes/manifest.json",
)
RELEASE_SEAL_ARTIFACTS = (
    "MANIFEST.json",
    *MATERIALIZED_ARTIFACTS,
)
STANDALONE_EVALUATOR_COMMON = (
    "task_record.json",
    "family_spec.json",
    "checker_profile.json",
    "harness_spec.json",
    "score_tb.scs",
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def tree_sha(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file():
            digest.update(item.relative_to(path).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(item.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def tree_sha_skipping(path: Path, *, excluded_names: set[str]) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file() and item.name not in excluded_names:
            digest.update(item.relative_to(path).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(item.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def public_bundle_hash(task_dir: Path) -> str:
    public = task_dir / "public"
    digest = hashlib.sha256()
    for path in sorted(public.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(public).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def prompt_component_path(release: Path, component_id: str) -> Path:
    if component_id.endswith("_wrapper.md"):
        subdir = "wrappers"
    elif component_id in set(FORM_SKILLS.values()):
        subdir = "form_skills"
    elif component_id in set(FEEDBACK_GUIDES.values()):
        subdir = "feedback_guides"
    else:
        raise SystemExit(f"unknown prompt component: {component_id}")
    return release / "prompt_modes" / subdir / component_id


def build_release_seal(
    release: Path,
    source_manifest_sha256: str,
    certification_reuse: dict[str, Any],
) -> dict[str, Any]:
    artifact_hashes = {}
    for relative in RELEASE_SEAL_ARTIFACTS:
        path = release / relative
        if not path.is_file():
            raise SystemExit(f"cannot seal release; missing artifact: {relative}")
        artifact_hashes[relative] = file_sha(path)
    return {
        "schema_version": "v4-benchmarkv4-release-seal-v1",
        "release_status": "gate3_hash_bound_certification_reused",
        "source_score_denominator_manifest_sha256": source_manifest_sha256,
        "artifact_sha256": artifact_hashes,
        "certification_reuse": certification_reuse,
        "simulation_claim": "canonical DUT gold and exact-five negative EVAS/Spectre certifications reused by hash",
    }


def expected_task_id(form: str, family: str) -> str:
    offsets = {"dut": 0, "testbench": 500, "bugfix": 1000}
    value = offsets[form] + int(family)
    width = 3 if value < 1000 else 4
    return f"v4-{value:0{width}d}"


def mutation_certification_hashes(active_mutations: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(item.get("mutation_id") or ""): str(item.get("certification_sha256") or "")
        for item in active_mutations
    }


def expected_buggy_artifact_hashes(
    artifact_paths: list[str],
    changed_hashes: dict[str, str],
    solution: Path,
) -> dict[str, str]:
    return {
        artifact: changed_hashes.get(artifact, file_sha(solution / artifact))
        for artifact in artifact_paths
    }


def audit_source_certifications(
    source: Path,
    source_rows: dict[str, dict[str, Any]],
    problems: list[str],
) -> dict[str, Any]:
    gold_count = 0
    negative_count = 0
    for family, row in sorted(source_rows.items()):
        source_task = source / str(row.get("release_dir") or "")
        task_cert_path = source_task / "evaluator" / "certification.json"
        expected_task_sha = str((row.get("hashes") or {}).get("task_certification_sha256") or "")
        if not task_cert_path.is_file() or file_sha(task_cert_path) != expected_task_sha:
            problems.append(f"{family}: source gold certification hash mismatch")
        else:
            certification = read_json(task_cert_path)
            evaluators = certification.get("evaluators") or {}
            if certification.get("status") != "gate2_pass":
                problems.append(f"{family}: source gold certification is not gate2_pass")
            for evaluator_name in ("evas", "spectre"):
                if (evaluators.get(evaluator_name) or {}).get("status") != "pass":
                    problems.append(f"{family}: source gold lacks {evaluator_name} PASS")
            gold_count += 1
        for mutation in row.get("active_mutations") or []:
            mutation_id = str(mutation.get("mutation_id") or "")
            cert_path = source_task / str(mutation.get("certification_path") or "")
            expected_sha = str(mutation.get("certification_sha256") or "")
            if not cert_path.is_file() or file_sha(cert_path) != expected_sha:
                problems.append(f"{family}/{mutation_id}: source negative certification hash mismatch")
                continue
            certification = read_json(cert_path)
            evaluators = certification.get("evaluators") or {}
            if certification.get("outcome") != "killed_behaviorally":
                problems.append(f"{family}/{mutation_id}: source negative was not killed behaviorally")
            for evaluator_name in ("evas", "spectre"):
                if evaluators.get(evaluator_name) != "compile_pass_behavior_fail":
                    problems.append(f"{family}/{mutation_id}: source negative lacks {evaluator_name} behavioral kill")
            negative_count += 1
    return {
        "policy": "source_denominator_hash_bound",
        "source_dut_gold_certification_count": gold_count,
        "source_negative_certification_count": negative_count,
        "evaluators": ["evas", "spectre"],
        "simulation_rerun_required_for_materialization": False,
    }


def audit_standalone_evaluator(
    task_dir: Path,
    source_task: Path,
    form: str,
    prefix: str,
    problems: list[str],
) -> Path | None:
    evaluator = task_dir / "evaluator"
    source_eval = source_task / "evaluator"
    if not evaluator.is_dir():
        problems.append(f"{prefix} evaluator directory missing")
        return None
    for name in STANDALONE_EVALUATOR_COMMON:
        local = evaluator / name
        source = source_eval / name
        if not local.is_file():
            problems.append(f"{prefix} standalone evaluator missing {name}")
        elif not source.is_file() or file_sha(local) != file_sha(source):
            problems.append(f"{prefix} standalone evaluator {name} differs from canonical source")
    for directory in ("profiles", "solution"):
        local = evaluator / directory
        source = source_eval / directory
        if not local.is_dir():
            problems.append(f"{prefix} standalone evaluator missing {directory}/")
        elif tree_sha(local) != tree_sha(source):
            problems.append(f"{prefix} standalone evaluator {directory}/ differs from canonical source")
    if form == "testbench":
        local_catalog = evaluator / "mutation_catalog.json"
        source_catalog = source_eval / "mutation_catalog.json"
        if not local_catalog.is_file():
            problems.append(f"{prefix} standalone testbench evaluator missing mutation_catalog.json")
        elif file_sha(local_catalog) != file_sha(source_catalog):
            problems.append(f"{prefix} standalone testbench evaluator mutation_catalog.json differs from canonical source")
        local_mutations = evaluator / "mutation_bundles"
        source_mutations = source_eval / "mutation_bundles"
        if not local_mutations.is_dir():
            problems.append(f"{prefix} standalone testbench evaluator missing mutation_bundles/")
        elif tree_sha(local_mutations) != tree_sha_skipping(source_mutations, excluded_names={"certification.json"}):
            problems.append(f"{prefix} standalone testbench evaluator mutation_bundles/ scoring files differ from canonical source")
        if list(local_mutations.rglob("certification.json")):
            problems.append(f"{prefix} standalone testbench evaluator should not copy negative certification files")
    score_policy = evaluator / "score_policy.json"
    if not score_policy.is_file():
        problems.append(f"{prefix} evaluator missing score_policy.json")
    else:
        score = read_json(score_policy)
        if "source_checker_profile" in score:
            problems.append(f"{prefix} score policy keeps external source_checker_profile reference")
        if score.get("materialized_checker_profile") != "evaluator/checker_profile.json":
            problems.append(f"{prefix} score policy does not point at materialized checker_profile.json")
        if score.get("checker_profile_sha256") != file_sha(evaluator / "checker_profile.json"):
            problems.append(f"{prefix} score policy checker_profile hash mismatch")
    return evaluator


def source_task_for_family(source: Path, source_rows: dict[str, dict[str, Any]], family: str) -> Path | None:
    row = source_rows.get(family)
    if row is None:
        return None
    return source / str(row.get("release_dir") or "")


def audit_task(
    release: Path,
    source: Path,
    source_manifest_sha: str,
    source_rows: dict[str, dict[str, Any]],
    row: dict[str, Any],
    problems: list[str],
) -> None:
    task_dir = release / str(row.get("task_dir") or "")
    task_id = str(row.get("task_id") or "")
    form = str(row.get("form") or "")
    family = str(row.get("family_id") or "")
    prefix = f"{task_id or task_dir.name}:"
    if not task_dir.is_dir():
        problems.append(f"{prefix} task directory missing")
        return
    for required in ("task_record.json", "public/instruction.md", "public_contract.json", "evaluator", "provenance"):
        if not (task_dir / required).exists():
            problems.append(f"{prefix} missing {required}")
    if problems and not (task_dir / "task_record.json").is_file():
        return
    record = read_json(task_dir / "task_record.json")
    contract = read_json(task_dir / "public_contract.json")
    expected_contract = rel(task_dir / "public_contract.json", release)
    if row.get("public_contract") != expected_contract or record.get("public_contract") != expected_contract:
        problems.append(f"{prefix} public contract path is not task-local")
    if record.get("canonical_dut_source"):
        problems.append(f"{prefix} task record keeps external canonical_dut_source path")
    if task_id != expected_task_id(form, family):
        problems.append(f"{prefix} ID does not match form/family numbering")
    if record.get("task_id") != task_id or record.get("form") != form or record.get("family_id") != family:
        problems.append(f"{prefix} task record identity mismatch")
    if contract.get("task_id") != task_id or contract.get("form") != form or str(contract.get("family_id")) != family:
        problems.append(f"{prefix} public contract identity mismatch")
    if record.get("public_bundle_sha256") != public_bundle_hash(task_dir):
        problems.append(f"{prefix} public bundle hash mismatch")
    source_row = source_rows.get(family)
    source_task = source_task_for_family(source, source_rows, family)
    if source_row is None or source_task is None or not source_task.is_dir():
        problems.append(f"{prefix} canonical denominator row missing")
        return
    if record.get("canonical_dut_source_slug") != source_task.name:
        problems.append(f"{prefix} source slug does not match denominator row")
    spec_path = source_task / "evaluator" / "family_spec.json"
    if not spec_path.is_file() or record.get("family_spec_sha256") != file_sha(spec_path):
        problems.append(f"{prefix} family spec hash mismatch")
        return
    spec = read_json(spec_path)
    artifact_paths = [str(item["path"]) for item in spec["artifact_contract"]["files"]]
    instruction_text = (task_dir / "public" / "instruction.md").read_text(encoding="utf-8")
    for marker in ("test_visible", "Public visible tests", "hidden evaluator", "Vela"):
        if marker in instruction_text:
            problems.append(f"{prefix} instruction leaks run/evaluator marker {marker!r}")
    if form != "testbench" and "visible testbench" in instruction_text.lower():
        problems.append(f"{prefix} non-testbench instruction leaks visible testbench wording")
    evaluator = audit_standalone_evaluator(task_dir, source_task, form, prefix, problems)
    if evaluator is None:
        return
    provenance = task_dir / "provenance"
    for required in ("source_task_record.json", "source_derivation_manifest.json"):
        if not (provenance / required).is_file():
            problems.append(f"{prefix} missing provenance/{required}")
    if form == "dut":
        if record.get("candidate_artifacts") != artifact_paths:
            problems.append(f"{prefix} DUT candidate artifacts differ from family spec")
        gold_reference = read_json(provenance / "gold_reference.json")
        if "source_solution" in gold_reference:
            problems.append(f"{prefix} DUT gold reference keeps external source_solution reference")
        if gold_reference.get("materialized_solution") != "evaluator/solution":
            problems.append(f"{prefix} DUT gold reference does not point to materialized solution")
        if gold_reference.get("solution_tree_sha256") != tree_sha(evaluator / "solution"):
            problems.append(f"{prefix} DUT gold solution hash mismatch")
        return
    derivation_path = provenance / "derivation_manifest.json"
    if not derivation_path.is_file():
        problems.append(f"{prefix} missing provenance/derivation_manifest.json")
        return
    derivation = read_json(derivation_path)
    assignment = derivation.get("negative_assignment") or {}
    suite = assignment.get("testbench_suite") or []
    if len(suite) != 5 or len(set(suite)) != 5:
        problems.append(f"{prefix} testbench suite is not exactly five unique mutations")
    active_mutations = source_row.get("active_mutations") or []
    expected_suite = [str(item.get("mutation_id") or "") for item in active_mutations]
    if suite != expected_suite:
        problems.append(f"{prefix} testbench suite differs from the exact-five denominator")
    if assignment.get("bugfix_seed") not in suite:
        problems.append(f"{prefix} bugfix seed is not a member of the testbench suite")
    base_dut = derivation.get("base_dut") or {}
    expected_base = {
        "canonical_task_id": f"v4-{family}",
        "canonical_task_slug": source_task.name,
        "family_spec_sha256": file_sha(spec_path),
        "mutation_catalog_sha256": file_sha(source_task / "evaluator" / "mutation_catalog.json"),
        "source_release_manifest_sha256": source_manifest_sha,
    }
    for field, expected in expected_base.items():
        if base_dut.get(field) != expected:
            problems.append(f"{prefix} derivation base hash mismatch for {field}")
    if form == "testbench":
        if record.get("candidate_artifacts") != ["testbench.scs"] or contract.get("target_artifacts") != ["testbench.scs"]:
            problems.append(f"{prefix} testbench output is not exactly testbench.scs")
        score = read_json(evaluator / "score_policy.json")
        if score.get("candidate_artifacts") != ["testbench.scs"] or score.get("kill_ratio_denominator") != 5:
            problems.append(f"{prefix} testbench score policy mismatch")
        supplied = task_dir / "public" / "supplied_dut"
        if tree_sha(supplied) != tree_sha(source_task / "evaluator" / "solution"):
            problems.append(f"{prefix} supplied DUT differs from canonical gold")
        reference = read_json(provenance / "reference_certificate.json")
        score_tb = source_task / "evaluator" / "score_tb.scs"
        score_tb_sha = file_sha(score_tb)
        if file_sha(evaluator / "reference_tb.scs") != score_tb_sha:
            problems.append(f"{prefix} reference testbench differs from the canonical score deck")
        if reference.get("reference_tb_sha256") != score_tb_sha:
            problems.append(f"{prefix} reference testbench certificate hash mismatch")
        if reference.get("mutation_certification_sha256") != mutation_certification_hashes(active_mutations):
            problems.append(f"{prefix} mutation certification hash map differs from the denominator")
        if reference.get("negative_suite_status") != "five_of_five_killed_behaviorally":
            problems.append(f"{prefix} reference testbench is not five-of-five certified")
        public_text = instruction_text + json.dumps(contract)
        if "neg_" in public_text or "mutation_id" in public_text:
            problems.append(f"{prefix} public testbench view leaks negative identity")
    elif form == "bugfix":
        if record.get("candidate_artifacts") != artifact_paths or contract.get("target_artifacts") != artifact_paths:
            problems.append(f"{prefix} bugfix artifact contract mismatch")
        buggy = task_dir / "public" / "buggy_bundle"
        buggy_paths = sorted(path.relative_to(buggy).as_posix() for path in buggy.rglob("*.va"))
        if buggy_paths != sorted(artifact_paths):
            problems.append(f"{prefix} buggy bundle file set mismatch")
        seed_id = str(assignment.get("bugfix_seed") or "")
        mutation_catalog = read_json(source_task / "evaluator" / "mutation_catalog.json")
        mutation_rows = {str(item.get("id") or ""): item for item in mutation_catalog.get("mutations") or []}
        seed_catalog = mutation_rows.get(seed_id)
        if seed_catalog is None:
            problems.append(f"{prefix} bugfix seed is missing from the canonical mutation catalog")
        else:
            expected_hashes = expected_buggy_artifact_hashes(
                artifact_paths,
                seed_catalog.get("artifact_hashes") or {},
                source_task / "evaluator" / "solution",
            )
            actual_hashes = {
                path.relative_to(buggy).as_posix(): file_sha(path)
                for path in buggy.rglob("*.va")
            }
            if actual_hashes != expected_hashes:
                problems.append(f"{prefix} buggy bundle differs from the selected canonical mutation")
        if tree_sha(buggy) == tree_sha(source_task / "evaluator" / "solution"):
            problems.append(f"{prefix} buggy bundle is byte-identical to gold")
        private_materialization = derivation.get("private_materialization") or {}
        if private_materialization.get("buggy_bundle_sha256") != tree_sha(buggy):
            problems.append(f"{prefix} buggy bundle hash mismatch")
        gold_reference = read_json(provenance / "gold_repair_reference.json")
        if "source_solution" in gold_reference:
            problems.append(f"{prefix} gold repair reference keeps external source_solution reference")
        if gold_reference.get("materialized_solution") != "evaluator/solution":
            problems.append(f"{prefix} gold repair reference does not point to materialized solution")
        if gold_reference.get("solution_tree_sha256") != tree_sha(evaluator / "solution"):
            problems.append(f"{prefix} gold repair solution hash mismatch")
        if gold_reference.get("gold_dut_certification_sha256") != (
            source_row.get("hashes") or {}
        ).get("task_certification_sha256"):
            problems.append(f"{prefix} gold DUT certification hash mismatch")
        public_text = instruction_text + json.dumps(contract)
        forbidden = ("neg_", "faulty file", "root cause", "changed line", "public summary")
        for marker in forbidden:
            if marker.lower() in public_text.lower():
                problems.append(f"{prefix} public bugfix view leaks forbidden marker {marker!r}")
        if re.search(r"\bmutation\b", public_text, re.IGNORECASE):
            problems.append(f"{prefix} public bugfix view leaks forbidden marker 'mutation'")
        selection = derivation.get("selection_evidence") or {}
        if selection.get("selection_status") != "policy_reviewed" or selection.get("triviality_markers"):
            problems.append(f"{prefix} bugfix seed lacks nontrivial semantic review")


def iter_prompt_public_inputs(task_dir: Path, form: str) -> list[Path]:
    public = task_dir / "public"
    inputs = [public / "instruction.md"]
    if form == "testbench":
        inputs.extend(sorted((public / "supplied_dut").rglob("*.va")))
    elif form == "bugfix":
        inputs.extend(sorted((public / "buggy_bundle").rglob("*.va")))
    return inputs


def audit_prompt_components(release: Path, tasks: list[dict[str, Any]], problems: list[str]) -> int:
    if (release / "prompt_modes" / "PROMPT_RECORDS.jsonl").exists():
        problems.append("release should not include prompt_modes/PROMPT_RECORDS.jsonl")
    component_manifest = read_json(release / "prompt_modes" / "manifest.json")
    mode_manifest = read_json(release / "prompt_modes" / "modes.json")
    wrapper_records = component_manifest.get("wrappers") or {}
    form_skill_records = component_manifest.get("form_skills") or {}
    feedback_guide_records = component_manifest.get("feedback_guides") or {}
    component_records = component_manifest.get("components") or {
        **wrapper_records,
        **form_skill_records,
        **feedback_guide_records,
    }
    tokenizer = component_manifest.get("reference_tokenizer") or {}
    tokenizer_key = f"{tokenizer.get('id')}@{tokenizer.get('version')}"
    required_wrappers = set(WRAPPERS_BY_MODE.values())
    required_form_skills = set(FORM_SKILLS.values())
    required_feedback_guides = set(FEEDBACK_GUIDES.values())
    if set(wrapper_records) != required_wrappers:
        problems.append("component manifest wrapper set mismatch")
    if set(form_skill_records) != required_form_skills:
        problems.append("component manifest form-skill set mismatch")
    if set(feedback_guide_records) != required_feedback_guides:
        problems.append("component manifest feedback-guide set mismatch")
    if set(component_records) != required_wrappers | required_form_skills | required_feedback_guides:
        problems.append("component manifest component set mismatch")
    if (release / "prompt_modes" / "skills").exists():
        problems.append("legacy prompt_modes/skills/ directory should not be present")
    for name, component in component_records.items():
        for field in ("stable_id", "semantic_version", "applicable_forms", "sha256", "bytes", "license", "provenance", "token_counts"):
            if field not in component:
                problems.append(f"component manifest {name}: missing {field}")
        if tokenizer_key not in (component.get("token_counts") or {}):
            problems.append(f"component manifest {name}: missing reference-tokenizer count")
        expected_path = prompt_component_path(release, name)
        if component.get("path") != expected_path.relative_to(release).as_posix():
            problems.append(f"component manifest {name}: path does not match component kind")
        if expected_path.is_file() and component.get("sha256") != file_sha(expected_path):
            problems.append(f"component manifest {name}: sha256 mismatch")
    mode_records = mode_manifest.get("modes") or {}
    if set(mode_records) != set(MODES):
        problems.append("prompt mode registry does not define exactly G0-G5")
    count = 0
    for task in tasks:
        task_id = str(task.get("task_id") or "")
        form = str(task.get("form") or "")
        task_dir = release / str(task.get("task_dir") or "")
        for mode in MODES:
            count += 1
            policy = mode_records.get(mode) or {}
            expected_cli = mode in AGENTIC_MODES
            if bool(policy.get("feedback_cli")) is not expected_cli:
                problems.append(f"{task_id}/{mode}: feedback availability mismatch")
            public_inputs = iter_prompt_public_inputs(task_dir, form)
            for item in public_inputs:
                if not item.is_file():
                    problems.append(f"{task_id}/{mode}: prompt public input missing: {item.relative_to(task_dir)}")
            expected_components: list[str] = []
            if mode in {"G1", "G3", "G5"}:
                expected_components.append(FORM_SKILLS.get(form, ""))
            if mode in {"G4", "G5"}:
                expected_components.append(FEEDBACK_GUIDES.get(form, ""))
            expected_components.append(WRAPPERS_BY_MODE.get(mode, ""))
            for name in expected_components:
                component = component_records.get(name) or {}
                if component.get("sha256") != file_sha(prompt_component_path(release, name)):
                    problems.append(f"{task_id}/{mode}: prompt component hash mismatch for {name}")
            if mode in DIRECT_MODES:
                direct_text_parts = [item.read_text(encoding="utf-8", errors="replace") for item in public_inputs if item.is_file()]
                direct_text_parts.extend(
                    prompt_component_path(release, name).read_text(encoding="utf-8", errors="replace")
                    for name in expected_components
                    if name in component_records
                )
                direct_text = "\n".join(direct_text_parts)
                for marker in (
                    "Feedback tools",
                    "feedback CLI",
                    "public/submission",
                    "agentic mode",
                    "mounted public task inputs",
                ):
                    if marker.lower() in direct_text.lower():
                        problems.append(f"{task_id}/{mode}: direct prompt leaks {marker!r}")
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seal-output", type=Path)
    args = parser.parse_args()
    release = args.release.expanduser().resolve()
    source = args.source.expanduser().resolve()
    manifest = read_json(release / "MANIFEST.json")
    tasks = read_json(release / "TASK_INDEX.json").get("tasks") or []
    problems: list[str] = []
    if (release / "private_evaluator").exists():
        problems.append("top-level private_evaluator/ should not exist in standalone benchmarkv4")
    if (release / "public_contracts").exists():
        problems.append("top-level public_contracts/ should not exist in standalone benchmarkv4")
    source_manifest_path = source / "score_denominator_manifest.json"
    if not source_manifest_path.is_file():
        raise SystemExit(f"source denominator missing: {source_manifest_path}")
    source_manifest = read_json(source_manifest_path)
    source_manifest_sha = file_sha(source_manifest_path)
    source_rows = {
        str(item.get("canonical_dut_id") or ""): item
        for item in source_manifest.get("tasks") or []
    }
    expected_materialized_hashes = {
        relative: file_sha(release / relative)
        for relative in MATERIALIZED_ARTIFACTS
        if (release / relative).is_file()
    }
    if set(expected_materialized_hashes) != set(MATERIALIZED_ARTIFACTS):
        problems.append("one or more materialized release artifacts are missing")
    if manifest.get("materialized_artifact_sha256") != expected_materialized_hashes:
        problems.append("materialized artifact hash binding mismatch")
    if manifest.get("source_release") or manifest.get("private_evaluator"):
        problems.append("manifest keeps legacy external source/private evaluator path")
    if manifest.get("source_release_label") != source.name:
        problems.append("manifest source release label mismatch")
    if manifest.get("source_score_denominator_manifest_sha256") != source_manifest_sha:
        problems.append("manifest source denominator hash mismatch")
    certification_reuse = audit_source_certifications(source, source_rows, problems)
    counts = Counter(str(row.get("form") or "") for row in tasks)
    if len(tasks) != 1200 or counts != Counter({form: 400 for form in FORMS}):
        problems.append(f"task counts mismatch: total={len(tasks)} forms={dict(counts)}")
    family_forms: dict[str, set[str]] = defaultdict(set)
    for row in tasks:
        family_forms[str(row.get("family_id") or "")].add(str(row.get("form") or ""))
        audit_task(release, source, source_manifest_sha, source_rows, row, problems)
    expected_families = {f"{value:03d}" for value in range(1, 401)}
    if set(family_forms) != expected_families:
        problems.append("family coverage is not exactly 001-400")
    for family in expected_families:
        if family_forms[family] != set(FORMS):
            problems.append(f"{family}: missing one or more task forms")
    task_by_family_form = {
        (str(row.get("family_id") or ""), str(row.get("form") or "")): release / str(row.get("task_dir") or "")
        for row in tasks
    }
    for family in sorted(expected_families):
        testbench_dir = task_by_family_form.get((family, "testbench"))
        bugfix_dir = task_by_family_form.get((family, "bugfix"))
        if testbench_dir is None or bugfix_dir is None:
            continue
        testbench_seed = (
            read_json(testbench_dir / "provenance" / "derivation_manifest.json").get("negative_assignment") or {}
        ).get("bugfix_seed")
        bugfix_seed = (
            read_json(bugfix_dir / "provenance" / "derivation_manifest.json").get("negative_assignment") or {}
        ).get("bugfix_seed")
        if testbench_seed != bugfix_seed:
            problems.append(f"{family}: cross-form bugfix seed mismatch: testbench={testbench_seed} bugfix={bugfix_seed}")
    prompt_count = audit_prompt_components(release, tasks, problems)
    if prompt_count != 7200:
        problems.append(f"prompt record count is {prompt_count}, expected 7200")
    report = {
        "schema_version": "v4-benchmarkv4-release-audit-v1",
        "status": "pass" if not problems else "fail",
        "family_count": len(family_forms),
        "task_count": len(tasks),
        "task_counts": dict(sorted(counts.items())),
        "prompt_record_count": prompt_count,
        "certification_reuse": certification_reuse,
        "input_hashes": {
            "source_score_denominator_manifest_sha256": source_manifest_sha,
            "manifest_sha256": file_sha(release / "MANIFEST.json"),
            **expected_materialized_hashes,
        },
        "problems": problems,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.seal_output:
        if problems:
            raise SystemExit("cannot seal release while audit problems remain")
        if not args.output:
            raise SystemExit("--seal-output requires --output so the audit report can be hash-bound")
        seal = build_release_seal(release, source_manifest_sha, certification_reuse)
        args.seal_output.parent.mkdir(parents=True, exist_ok=True)
        args.seal_output.write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
