#!/usr/bin/env python3
"""Audit the materialized 1,200-task tri-form release."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RELEASE = PACKAGE_ROOT / "release" / "tri-form-v4-1200-draft"
FORMS = ("dut", "testbench", "bugfix")
MODES = ("G0", "G1", "G2", "G3", "G4", "G5")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file():
            digest.update(item.relative_to(path).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(item.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def public_bundle_hash(task_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(task_dir.rglob("*")):
        if not path.is_file() or "evaluator" in path.parts or path.name == "TASK_RECORD.json":
            continue
        digest.update(path.relative_to(task_dir).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def expected_task_id(form: str, family: str) -> str:
    offsets = {"dut": 0, "testbench": 500, "bugfix": 1000}
    value = offsets[form] + int(family)
    width = 3 if value < 1000 else 4
    return f"v4-{value:0{width}d}"


def audit_task(release: Path, source: Path, row: dict[str, Any], problems: list[str]) -> None:
    task_dir = release / str(row.get("task_dir") or "")
    task_id = str(row.get("task_id") or "")
    form = str(row.get("form") or "")
    family = str(row.get("family_id") or "")
    prefix = f"{task_id or task_dir.name}:"
    if not task_dir.is_dir():
        problems.append(f"{prefix} task directory missing")
        return
    for required in ("TASK_RECORD.json", "instruction.md", "public_contract.json"):
        if not (task_dir / required).is_file():
            problems.append(f"{prefix} missing {required}")
    if problems and not (task_dir / "TASK_RECORD.json").is_file():
        return
    record = read_json(task_dir / "TASK_RECORD.json")
    contract = read_json(task_dir / "public_contract.json")
    if task_id != expected_task_id(form, family):
        problems.append(f"{prefix} ID does not match form/family numbering")
    if record.get("task_id") != task_id or record.get("form") != form or record.get("family_id") != family:
        problems.append(f"{prefix} task record identity mismatch")
    if contract.get("task_id") != task_id or contract.get("form") != form or str(contract.get("family_id")) != family:
        problems.append(f"{prefix} public contract identity mismatch")
    if record.get("public_bundle_sha256") != public_bundle_hash(task_dir):
        problems.append(f"{prefix} public bundle hash mismatch")
    source_task = PACKAGE_ROOT / str(record.get("canonical_dut_source") or "")
    if not source_task.is_dir() or source not in source_task.parents:
        problems.append(f"{prefix} canonical DUT source is invalid")
        return
    spec_path = source_task / "evaluator" / "family_spec.json"
    if not spec_path.is_file() or record.get("family_spec_sha256") != file_sha(spec_path):
        problems.append(f"{prefix} family spec hash mismatch")
        return
    spec = read_json(spec_path)
    artifact_paths = [str(item["path"]) for item in spec["artifact_contract"]["files"]]
    if form == "dut":
        if record.get("candidate_artifacts") != artifact_paths:
            problems.append(f"{prefix} DUT candidate artifacts differ from family spec")
        return
    evaluator = task_dir / "evaluator"
    if not evaluator.is_dir():
        problems.append(f"{prefix} evaluator directory missing")
        return
    derivation = read_json(evaluator / "derivation_manifest.json")
    assignment = derivation.get("negative_assignment") or {}
    suite = assignment.get("testbench_suite") or []
    if len(suite) != 5 or len(set(suite)) != 5:
        problems.append(f"{prefix} testbench suite is not exactly five unique mutations")
    if assignment.get("bugfix_seed") not in suite:
        problems.append(f"{prefix} bugfix seed is not a member of the testbench suite")
    if derivation.get("base_dut", {}).get("family_spec_sha256") != file_sha(spec_path):
        problems.append(f"{prefix} derivation family hash mismatch")
    if form == "testbench":
        if record.get("candidate_artifacts") != ["testbench.scs"] or contract.get("target_artifacts") != ["testbench.scs"]:
            problems.append(f"{prefix} testbench output is not exactly testbench.scs")
        score = read_json(evaluator / "score_policy.json")
        if score.get("candidate_artifacts") != ["testbench.scs"] or score.get("kill_ratio_denominator") != 5:
            problems.append(f"{prefix} testbench score policy mismatch")
        supplied = task_dir / "supplied_dut"
        if tree_sha(supplied) != tree_sha(source_task / "evaluator" / "solution"):
            problems.append(f"{prefix} supplied DUT differs from canonical gold")
        reference = read_json(evaluator / "reference_certificate.json")
        if reference.get("negative_suite_status") != "five_of_five_killed_behaviorally":
            problems.append(f"{prefix} reference testbench is not five-of-five certified")
        public_text = (task_dir / "instruction.md").read_text(encoding="utf-8") + json.dumps(contract)
        if "neg_" in public_text or "mutation_id" in public_text:
            problems.append(f"{prefix} public testbench view leaks negative identity")
    elif form == "bugfix":
        if record.get("candidate_artifacts") != artifact_paths or contract.get("target_artifacts") != artifact_paths:
            problems.append(f"{prefix} bugfix artifact contract mismatch")
        buggy = task_dir / "buggy_bundle"
        buggy_paths = sorted(path.relative_to(buggy).as_posix() for path in buggy.rglob("*.va"))
        if buggy_paths != sorted(artifact_paths):
            problems.append(f"{prefix} buggy bundle file set mismatch")
        if tree_sha(buggy) == tree_sha(source_task / "evaluator" / "solution"):
            problems.append(f"{prefix} buggy bundle is byte-identical to gold")
        public_text = (task_dir / "instruction.md").read_text(encoding="utf-8") + json.dumps(contract)
        forbidden = ("neg_", "faulty file", "root cause", "changed line", "public summary")
        for marker in forbidden:
            if marker.lower() in public_text.lower():
                problems.append(f"{prefix} public bugfix view leaks forbidden marker {marker!r}")
        if re.search(r"\bmutation\b", public_text, re.IGNORECASE):
            problems.append(f"{prefix} public bugfix view leaks forbidden marker 'mutation'")
        selection = derivation.get("selection_evidence") or {}
        if selection.get("selection_status") != "policy_reviewed" or selection.get("triviality_markers"):
            problems.append(f"{prefix} Bugfix seed lacks nontrivial semantic review")


def audit_prompt_records(release: Path, tasks: list[dict[str, Any]], problems: list[str]) -> int:
    path = release / "prompt_modes" / "PROMPT_RECORDS.jsonl"
    if not path.is_file():
        problems.append("prompt record file missing")
        return 0
    seen: dict[str, set[str]] = defaultdict(set)
    count = 0
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            problems.append(f"prompt record line {line_no} is invalid JSON: {exc}")
            continue
        count += 1
        task_id = str(row.get("task_id") or "")
        mode = str(row.get("mode") or "")
        seen[task_id].add(mode)
        expected_cli = mode in {"G2", "G3", "G4", "G5"}
        if row.get("feedback_cli_available") is not expected_cli:
            problems.append(f"{task_id}/{mode}: feedback availability mismatch")
        skills = set((row.get("skill_hashes") or {}).keys())
        if mode in {"G0", "G2"} and skills:
            problems.append(f"{task_id}/{mode}: unexpected skill components")
        if mode == "G1" and len(skills) != 1:
            problems.append(f"{task_id}/{mode}: expected exactly one form skill")
        if mode == "G5" and len(skills) != 3:
            problems.append(f"{task_id}/{mode}: expected form plus feedback skills")
    expected_ids = {str(row["task_id"]) for row in tasks}
    if set(seen) != expected_ids:
        problems.append("prompt record task coverage mismatch")
    for task_id in expected_ids:
        if seen[task_id] != set(MODES):
            problems.append(f"{task_id}: prompt mode coverage mismatch")
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    release = args.release.expanduser().resolve()
    manifest = read_json(release / "MANIFEST.json")
    tasks = read_json(release / "TASK_INDEX.json").get("tasks") or []
    source = PACKAGE_ROOT / str(manifest.get("source_release") or "")
    problems: list[str] = []
    counts = Counter(str(row.get("form") or "") for row in tasks)
    if len(tasks) != 1200 or counts != Counter({form: 400 for form in FORMS}):
        problems.append(f"task counts mismatch: total={len(tasks)} forms={dict(counts)}")
    family_forms: dict[str, set[str]] = defaultdict(set)
    for row in tasks:
        family_forms[str(row.get("family_id") or "")].add(str(row.get("form") or ""))
        audit_task(release, source, row, problems)
    expected_families = {f"{value:03d}" for value in range(1, 401)}
    if set(family_forms) != expected_families:
        problems.append("family coverage is not exactly 001-400")
    for family in expected_families:
        if family_forms[family] != set(FORMS):
            problems.append(f"{family}: missing one or more task forms")
    prompt_count = audit_prompt_records(release, tasks, problems)
    if prompt_count != 7200:
        problems.append(f"prompt record count is {prompt_count}, expected 7200")
    report = {
        "schema_version": "v4-tri-form-release-audit-v1",
        "status": "pass" if not problems else "fail",
        "family_count": len(family_forms),
        "task_count": len(tasks),
        "task_counts": dict(sorted(counts.items())),
        "prompt_record_count": prompt_count,
        "problems": problems,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
