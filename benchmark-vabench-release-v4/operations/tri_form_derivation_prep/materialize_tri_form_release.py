#!/usr/bin/env python3
"""Materialize the standalone benchmarkv4 task package.

The frozen exact-five DUT release is the only family source.  The generated
benchmarkv4 package keeps each task self-contained: solver-visible inputs live
under ``public/``, local scoring assets under ``evaluator/``, and hash-bound
audit provenance under ``provenance/``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any, Iterable


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
PREP_ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = PACKAGE_ROOT / "provenance" / "dut-base-v3-exact-five-hash-bound-v2"
DEFAULT_OUTPUT = PACKAGE_ROOT / "release" / "benchmarkv4"
PROMPT_ASSETS = PREP_ROOT / "prompt_assets"
MODES = {
    "G0": {"process": "direct_one_shot", "form_skill": False, "feedback_guide": False, "feedback_cli": False},
    "G1": {"process": "direct_one_shot", "form_skill": True, "feedback_guide": False, "feedback_cli": False},
    "G2": {"process": "agentic", "form_skill": False, "feedback_guide": False, "feedback_cli": True},
    "G3": {"process": "agentic", "form_skill": True, "feedback_guide": False, "feedback_cli": True},
    "G4": {"process": "agentic", "form_skill": False, "feedback_guide": True, "feedback_cli": True},
    "G5": {"process": "agentic", "form_skill": True, "feedback_guide": True, "feedback_cli": True},
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
PUBLIC_MATERIALIZED_ARTIFACTS = MATERIALIZED_ARTIFACTS
WRAPPERS_BY_PROCESS = {
    "direct_one_shot": "direct_wrapper.md",
    "agentic": "agentic_wrapper.md",
}
REFERENCE_TOKENIZER = {
    "id": "vabench_utf8_lexeme",
    "version": "1.0.0",
    "algorithm": "Unicode word runs and individual non-whitespace punctuation marks",
}
COMPONENT_METADATA = {
    "direct_wrapper.md": {"stable_id": "component.wrapper.direct_one_shot", "kind": "wrapper", "applicable_forms": ["dut", "testbench", "bugfix"]},
    "agentic_wrapper.md": {"stable_id": "component.wrapper.agentic", "kind": "wrapper", "applicable_forms": ["dut", "testbench", "bugfix"]},
    "dut_modeling.md": {"stable_id": "component.form.dut", "kind": "form_skill", "applicable_forms": ["dut"]},
    "testbench_verification.md": {"stable_id": "component.form.testbench", "kind": "form_skill", "applicable_forms": ["testbench"]},
    "bugfix_diagnosis.md": {"stable_id": "component.form.bugfix", "kind": "form_skill", "applicable_forms": ["bugfix"]},
    "feedback_dut.md": {"stable_id": "component.feedback.dut", "kind": "feedback_guide", "applicable_forms": ["dut"]},
    "feedback_testbench.md": {"stable_id": "component.feedback.testbench", "kind": "feedback_guide", "applicable_forms": ["testbench"]},
    "feedback_bugfix.md": {"stable_id": "component.feedback.bugfix", "kind": "feedback_guide", "applicable_forms": ["bugfix"]},
}
COMPONENT_SUBDIR_BY_KIND = {
    "wrapper": "wrappers",
    "form_skill": "form_skills",
    "feedback_guide": "feedback_guides",
}
STANDALONE_EVALUATOR_COMMON = (
    "task_record.json",
    "family_spec.json",
    "checker_profile.json",
    "harness_spec.json",
    "score_tb.scs",
)
TASK_RECORD_FILENAME = "task_record.json"
TRIVIAL_FAULT_CLASSES = {
    "zero_stub_output",
    "holds_clock_output_low",
    "constant_stub_output",
}
TRIVIAL_ID_MARKERS = {"force_zero", "stuck_zero", "constant_zero"}
SEMANTIC_MARKERS = {
    "async": 5, "asynchronous": 5, "edge": 5, "reset": 5, "hold": 5,
    "timing": 5, "delay": 4, "state": 5, "sequence": 5, "calibration": 4,
    "hysteresis": 4, "slew": 4, "settling": 4, "polarity": 4, "direction": 4,
    "gain": 3, "clipping": 3, "saturation": 3, "rail": 3, "weight": 3,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical_sha(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha_bytes(payload.encode("utf-8"))


def reference_token_count(text: str) -> int:
    return len(re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE))


def component_fingerprint(component_id: str, path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    tokenizer_id = f"{REFERENCE_TOKENIZER['id']}@{REFERENCE_TOKENIZER['version']}"
    return {
        "id": component_id,
        "sha256": file_sha(path),
        "bytes": path.stat().st_size,
        "token_counts": {tokenizer_id: reference_token_count(text)},
    }


def tree_sha(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file():
            digest.update(item.relative_to(path).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(item.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def materialized_artifact_hashes(output: Path, artifacts: Iterable[str]) -> dict[str, str]:
    return {relative: file_sha(output / relative) for relative in artifacts}


def negative_assignment(row: dict[str, Any], seed_review: dict[str, Any]) -> dict[str, Any]:
    return {
        "bugfix_seed": seed_review["mutation_id"],
        "testbench_suite": [str(item["mutation_id"]) for item in row["active_mutations"]],
    }


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def task_title(spec: dict[str, Any]) -> str:
    return str((spec.get("identity") or {}).get("title") or f"Family {spec['family_id']}")


def render_interface(spec: dict[str, Any]) -> str:
    blocks: list[str] = []
    for file_record in (spec.get("artifact_contract") or {}).get("files") or []:
        blocks.append(f"- Artifact `{file_record['path']}`:")
        for module in file_record.get("modules") or []:
            role = str(module.get("role") or "module")
            blocks.append(f"  - Module `{module['name']}` ({role})")
            ports = sorted(module.get("ports") or [], key=lambda item: int(item.get("position", 0)))
            for port in ports:
                blocks.append(
                    f"    - position {port['position']}: `{port['name']}` "
                    f"({port['direction']}, {port['discipline']})"
                )
    return "\n".join(blocks) or "- Use the interface declared in the public contract metadata."


def render_parameters(spec: dict[str, Any]) -> str:
    lines: list[str] = []
    for file_record in (spec.get("artifact_contract") or {}).get("files") or []:
        for module in file_record.get("modules") or []:
            for parameter in module.get("parameters") or []:
                units = f" {parameter['units']}" if parameter.get("units") else ""
                lines.append(
                    f"- `{module['name']}.{parameter['name']}` defaults to "
                    f"`{parameter.get('default')}`{units}; valid range: "
                    f"{parameter.get('valid_range', 'as declared')}; "
                    f"{parameter.get('override_behavior', 'honor public overrides')}."
                )
    return "\n".join(lines) or "- No public parameter is declared."


def render_properties(spec: dict[str, Any], verb: str) -> str:
    lines = []
    for prop in spec.get("properties") or []:
        signals = ", ".join(f"`{value}`" for value in prop.get("required_signals") or [])
        lines.append(f"- `{prop['id']}`: {verb} {prop['observable_contract']} Required traces: {signals}.")
    return "\n".join(lines)


def render_binding(spec: dict[str, Any]) -> str:
    binding = spec.get("testbench_binding") or {}
    lines = [f"- DUT sources use `{binding.get('source_path_template', './dut/{artifact_path}')}`."]
    for instance in binding.get("instances") or []:
        connections = sorted(instance.get("connections") or [], key=lambda item: int(item.get("position", 0)))
        ports = ", ".join(f"{item['port_ref']}={item['net']}" for item in connections)
        lines.append(
            f"- Instantiate `{instance['module_ref']}` as `{instance['name']}` with ordered public binding: {ports}."
        )
    return "\n".join(lines)


def render_constraints(spec: dict[str, Any]) -> str:
    lines = [f"- {value}" for value in spec.get("modeling_constraints") or []]
    return "\n".join(lines) or "- Keep behavior deterministic and within the declared voltage-domain scope."


def sanitize_instruction_text(text: str, form: str) -> str:
    """Remove evaluation-surface wording from canonical prompt text."""
    if form != "testbench":
        text = text.replace(
            "Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. "
            "The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, "
            "transient stop time, or validation sample window into the DUT unless that behavior is part of the "
            "public circuit contract.",
            "Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. "
            "Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT "
            "unless that behavior is part of the public circuit contract.",
        )
        text = text.replace("visible testbench", "validation scenario")
        text = text.replace("Visible testbench", "Validation scenario")
        text = text.replace("a Spectre testbench", "a testbench")
        text = text.replace("a the simulator example harness", "the validation harness")
    return text


def render_testbench_instruction(spec: dict[str, Any]) -> str:
    title = task_title(spec)
    return f"""# {title} Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `{title}` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

{render_interface(spec)}

Stable evaluator binding:

{render_binding(spec)}

## Public Parameter Contract

{render_parameters(spec)}

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

{render_properties(spec, 'exercise and make observable:')}

The required trace names are: {', '.join(f'`{x}`' for x in (spec.get('trace_contract') or {}).get('required_signals') or [])}.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
"""


def render_bugfix_instruction(spec: dict[str, Any]) -> str:
    title = task_title(spec)
    paths = [str(item["path"]) for item in (spec.get("artifact_contract") or {}).get("files") or []]
    return f"""# {title} Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

{render_interface(spec)}

## Public Parameter Contract

{render_parameters(spec)}

## Required Behavior

The repaired bundle must satisfy every public property:

{render_properties(spec, 'restore:')}

## Modeling Constraints

{render_constraints(spec)}
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: {', '.join(f'`{path}`' for path in paths)}.
Every supplied `.va` file is editable; do not add or omit files.
"""


def public_semantics(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "family_id": spec["family_id"],
        "identity": spec["identity"],
        "artifact_contract": spec["artifact_contract"],
        "testbench_binding": spec["testbench_binding"],
        "properties": spec["properties"],
        "trace_contract": spec["trace_contract"],
        "modeling_constraints": spec.get("modeling_constraints") or [],
    }


def public_contract_relative_path(task_dir: Path) -> str:
    form = task_dir.parent.name
    return f"tasks/{form}/{task_dir.name}/public_contract.json"


def write_public_contract(output: Path, task_dir: Path, contract: dict[str, Any]) -> str:
    target = task_dir / "public_contract.json"
    relative = rel(target, output)
    write_json(target, contract)
    return relative


def mutation_score(item: dict[str, Any], preferred: bool) -> tuple[int, str]:
    mutation_id = str(item["mutation_id"])
    fault_class = str(item.get("fault_class") or "")
    trigger = str(item.get("trigger_condition") or "")
    text = f"{mutation_id} {fault_class} {trigger}".lower()
    score = 3 * len(item.get("violated_property_ids") or []) + min(len(trigger.split()), 8)
    for marker, weight in SEMANTIC_MARKERS.items():
        if marker in text:
            score += weight
    trivial = []
    if fault_class.lower() in TRIVIAL_FAULT_CLASSES:
        trivial.append(fault_class.lower())
    trivial.extend(marker for marker in TRIVIAL_ID_MARKERS if marker in mutation_id.lower())
    trivial = sorted(set(trivial))
    score -= 24 * len(trivial)
    if preferred:
        score += 2
    return score, ",".join(trivial)


def select_bugfix_seed(row: dict[str, Any]) -> dict[str, Any]:
    preferred = str(row.get("bugfix_seed") or "")
    ranked = []
    for item in row["active_mutations"]:
        score, markers = mutation_score(item, str(item["mutation_id"]) == preferred)
        ranked.append((score, str(item["mutation_id"]), markers, item))
    ranked.sort(key=lambda value: (-value[0], value[1]))
    score, mutation_id, markers, item = ranked[0]
    return {
        "mutation_id": mutation_id,
        "selection_policy": "semantic_fault_complexity_v1",
        "selection_status": "policy_reviewed",
        "source_preferred_seed": preferred,
        "source_preferred_seed_preserved": mutation_id == preferred,
        "semantic_score": score,
        "triviality_markers": markers.split(",") if markers else [],
        "rationale": (
            f"Select fault class {item.get('fault_class')} under trigger "
            f"'{item.get('trigger_condition')}' because it exercises "
            f"{', '.join(item.get('violated_property_ids') or [])} as one compile-pass semantic defect."
        ),
    }


def copy_solution(source_task: Path, destination: Path, spec: dict[str, Any]) -> list[str]:
    paths = [str(item["path"]) for item in spec["artifact_contract"]["files"]]
    for artifact in paths:
        source = source_task / "evaluator" / "solution" / artifact
        if not source.is_file():
            raise SystemExit(f"{source_task.name}: missing solution artifact {artifact}")
        target = destination / artifact
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return paths


def overlay_mutation(source_task: Path, mutation_id: str, destination: Path, artifact_paths: list[str]) -> list[str]:
    mutation_dir = source_task / "evaluator" / "mutation_bundles" / mutation_id
    candidates = sorted(mutation_dir.rglob("*.va"))
    if not candidates:
        raise SystemExit(f"{source_task.name}/{mutation_id}: mutation bundle has no Verilog-A source")
    changed: list[str] = []
    by_name = {Path(path).name: path for path in artifact_paths}
    for source in candidates:
        relative = source.relative_to(mutation_dir).as_posix()
        if relative in artifact_paths:
            target_rel = relative
        elif source.name in by_name:
            target_rel = by_name[source.name]
        elif len(artifact_paths) == 1:
            target_rel = artifact_paths[0]
        else:
            raise SystemExit(f"{source_task.name}/{mutation_id}: cannot map {relative} into DUT bundle")
        target = destination / target_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        changed.append(target_rel)
    return sorted(set(changed))


def common_task_record(
    *, task_id: str, form: str, family_id: str, directory: str, spec_sha: str,
    source_task_slug: str, candidate_artifacts: list[str], public_contract: str, public_bundle_sha: str,
) -> dict[str, Any]:
    return {
        "schema_version": "v4-benchmarkv4-task-record-v1",
        "task_id": task_id,
        "form": form,
        "family_id": family_id,
        "task_dir": directory,
        "public_contract": public_contract,
        "candidate_artifacts": candidate_artifacts,
        "family_spec_sha256": spec_sha,
        "canonical_dut_source_slug": source_task_slug,
        "public_bundle_sha256": public_bundle_sha,
        "scored": True,
        "modes": list(MODES),
    }


def public_bundle_hash(task_dir: Path) -> str:
    public = task_dir / "public"
    included = [path for path in sorted(public.rglob("*")) if path.is_file()]
    digest = hashlib.sha256()
    for path in included:
        digest.update(path.relative_to(public).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def write_task_record(task_dir: Path, record: dict[str, Any]) -> None:
    write_json(task_dir / TASK_RECORD_FILENAME, record)


def copy_tree(source: Path, target: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True)


def copy_tree_skipping(source: Path, target: Path, *, excluded_names: set[str]) -> None:
    for item in sorted(source.rglob("*")):
        if not item.is_file() or item.name in excluded_names:
            continue
        destination = target / item.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, destination)


def materialize_standalone_evaluator(source_task: Path, evaluator: Path, *, include_negative_suite: bool) -> None:
    """Copy local scoring assets into a benchmarkv4 task evaluator directory."""
    source_eval = source_task / "evaluator"
    evaluator.mkdir(parents=True, exist_ok=True)
    for name in STANDALONE_EVALUATOR_COMMON:
        shutil.copy2(source_eval / name, evaluator / name)
    copy_tree(source_eval / "profiles", evaluator / "profiles")
    copy_tree(source_eval / "solution", evaluator / "solution")
    if include_negative_suite:
        shutil.copy2(source_eval / "mutation_catalog.json", evaluator / "mutation_catalog.json")
        copy_tree_skipping(
            source_eval / "mutation_bundles",
            evaluator / "mutation_bundles",
            excluded_names={"certification.json"},
        )


def build_dut_view(
    output: Path,
    source_task: Path,
    row: dict[str, Any],
    spec: dict[str, Any],
    spec_sha: str,
) -> dict[str, Any]:
    family = str(row["canonical_dut_id"])
    task_dir = output / "tasks" / "dut" / source_task.name
    task_dir.mkdir(parents=True)
    public = task_dir / "public"
    public.mkdir()
    write_text(
        public / "instruction.md",
        sanitize_instruction_text(
            (source_task / "public" / "task" / "instruction.md").read_text(encoding="utf-8"),
            "dut",
        ),
    )
    contract = public_semantics(spec)
    contract.update({
        "schema_version": "v4-benchmarkv4-public-contract-v1",
        "task_id": f"v4-{family}",
        "form": "dut",
        "target_artifacts": [str(item["path"]) for item in spec["artifact_contract"]["files"]],
        "feedback": {"available_in_modes": ["G2", "G3", "G4", "G5"], "command": "vabench feedback run"},
    })
    public_contract = write_public_contract(output, task_dir, contract)
    evaluator = task_dir / "evaluator"
    materialize_standalone_evaluator(source_task, evaluator, include_negative_suite=False)
    provenance = task_dir / "provenance"
    provenance.mkdir()
    shutil.copy2(source_task / "evaluator" / "task_record.json", provenance / "source_task_record.json")
    shutil.copy2(source_task / "evaluator" / "derivation_manifest.json", provenance / "source_derivation_manifest.json")
    write_json(evaluator / "score_policy.json", {
        "schema_version": "v4-dut-score-policy-v1",
        "task_id": f"v4-{family}",
        "candidate_artifacts": contract["target_artifacts"],
        "full_contract_pass_required": True,
        "spectre_final_judge": True,
        "materialized_checker_profile": "evaluator/checker_profile.json",
        "checker_profile_sha256": file_sha(evaluator / "checker_profile.json"),
    })
    write_json(provenance / "gold_reference.json", {
        "schema_version": "v4-gold-reference-v1",
        "materialized_solution": "evaluator/solution",
        "solution_tree_sha256": tree_sha(evaluator / "solution"),
        "gold_dut_certification_sha256": row["hashes"]["task_certification_sha256"],
        "simulation_rerun_required_for_materialization": False,
    })
    bundle_sha = public_bundle_hash(task_dir)
    write_task_record(task_dir, common_task_record(
        task_id=f"v4-{family}", form="dut", family_id=family,
        directory=rel(task_dir, output), spec_sha=spec_sha,
        source_task_slug=source_task.name,
        candidate_artifacts=contract["target_artifacts"], public_contract=public_contract,
        public_bundle_sha=bundle_sha,
    ))
    return {
        "task_id": f"v4-{family}",
        "form": "dut",
        "family_id": family,
        "task_dir": rel(task_dir, output),
        "public_contract": public_contract,
    }


def build_testbench_view(
    output: Path,
    source_task: Path,
    row: dict[str, Any],
    spec: dict[str, Any],
    spec_sha: str,
    source_manifest_sha: str,
    seed_review: dict[str, Any],
) -> dict[str, Any]:
    family = str(row["canonical_dut_id"])
    task_num = 500 + int(family)
    slug = source_task.name.split("-", 1)[1]
    task_dir = output / "tasks" / "testbench" / f"{task_num:03d}-{slug}-testbench"
    task_dir.mkdir(parents=True)
    public = task_dir / "public"
    public.mkdir()
    write_text(public / "instruction.md", render_testbench_instruction(spec))
    supplied = public / "supplied_dut"
    artifacts = copy_solution(source_task, supplied, spec)
    contract = public_semantics(spec)
    contract.update({
        "schema_version": "v4-benchmarkv4-public-contract-v1",
        "task_id": f"v4-{task_num:03d}",
        "form": "testbench",
        "target_artifacts": ["testbench.scs"],
        "supplied_dut_artifacts": [f"supplied_dut/{path}" for path in artifacts],
        "evaluation_summary": {
            "reference_cases": 1,
            "anonymous_negative_cases": 5,
            "full_credit": "valid candidate and reference pass and all five negatives killed behaviorally",
        },
        "feedback": {"available_in_modes": ["G2", "G3", "G4", "G5"], "command": "vabench feedback run"},
        "security_summary": [
            "only declared ./dut source bindings are allowed",
            "DUT redefinition, direct output drive, private hierarchical probes, arbitrary file access, and unbounded analyses are rejected",
        ],
    })
    public_contract = write_public_contract(output, task_dir, contract)
    evaluator = task_dir / "evaluator"
    materialize_standalone_evaluator(source_task, evaluator, include_negative_suite=True)
    provenance = task_dir / "provenance"
    provenance.mkdir()
    shutil.copy2(source_task / "evaluator" / "task_record.json", provenance / "source_task_record.json")
    shutil.copy2(source_task / "evaluator" / "derivation_manifest.json", provenance / "source_derivation_manifest.json")
    suite = [str(item["mutation_id"]) for item in row["active_mutations"]]
    derivation = {
        "schema_version": "v4-derivation-manifest-v2",
        "family_id": family,
        "base_dut": {
            "canonical_task_id": f"v4-{family}",
            "canonical_task_slug": source_task.name,
            "family_spec_sha256": spec_sha,
            "source_release_manifest_sha256": source_manifest_sha,
            "mutation_catalog_sha256": row["hashes"]["mutation_catalog_sha256"],
            "canonical_score_tb_sha256": row["hashes"]["score_deck_sha256"],
        },
        "negative_assignment": negative_assignment(row, seed_review),
    }
    write_json(evaluator / "score_policy.json", {
        "schema_version": "v4-testbench-score-policy-v1",
        "task_id": f"v4-{task_num:03d}",
        "candidate_artifacts": ["testbench.scs"],
        "reference_gate": "all applicable public properties pass on supplied correct DUT",
        "negative_outcomes": ["killed_behaviorally", "survived", "invalid_run"],
        "full_credit": "reference_gate and five_of_five_killed_behaviorally",
        "kill_ratio_denominator": 5,
        "spectre_final_judge": True,
        "materialized_checker_profile": "evaluator/checker_profile.json",
        "checker_profile_sha256": file_sha(evaluator / "checker_profile.json"),
    })
    write_json(evaluator / "testbench_security_policy.json", {
        "schema_version": "v4-testbench-security-policy-v1",
        "candidate_artifacts": ["testbench.scs"],
        "allowed_dut_root": "./dut",
        "forbid": [
            "undeclared_include", "absolute_path", "path_traversal", "process_execution", "network_access",
            "dut_redefinition", "direct_dut_output_drive", "private_hierarchical_probe", "unbounded_resource_use",
        ],
        "require": ["declared_dut_binding", "transient_analysis", "all_required_public_traces"],
    })
    shutil.copy2(source_task / "evaluator" / "score_tb.scs", evaluator / "reference_tb.scs")
    write_json(provenance / "derivation_manifest.json", derivation)
    write_json(provenance / "reference_certificate.json", {
        "schema_version": "v4-reference-testbench-certificate-v1",
        "evidence_source": "canonical_score_profile_hash_reuse",
        "reference_tb_sha256": file_sha(evaluator / "reference_tb.scs"),
        "correct_dut_status": "pass",
        "negative_suite_status": "five_of_five_killed_behaviorally",
        "mutation_certification_sha256": {item["mutation_id"]: item["certification_sha256"] for item in row["active_mutations"]},
        "simulation_rerun_required_for_materialization": False,
    })
    bundle_sha = public_bundle_hash(task_dir)
    write_task_record(task_dir, common_task_record(
        task_id=f"v4-{task_num:03d}", form="testbench", family_id=family,
        directory=rel(task_dir, output), spec_sha=spec_sha,
        source_task_slug=source_task.name, candidate_artifacts=["testbench.scs"],
        public_contract=public_contract,
        public_bundle_sha=bundle_sha,
    ))
    return {
        "task_id": f"v4-{task_num:03d}",
        "form": "testbench",
        "family_id": family,
        "task_dir": rel(task_dir, output),
        "public_contract": public_contract,
    }


def build_bugfix_view(
    output: Path,
    source_task: Path,
    row: dict[str, Any],
    spec: dict[str, Any],
    spec_sha: str,
    source_manifest_sha: str,
    seed_review: dict[str, Any],
) -> dict[str, Any]:
    family = str(row["canonical_dut_id"])
    task_num = 1000 + int(family)
    slug = source_task.name.split("-", 1)[1]
    task_dir = output / "tasks" / "bugfix" / f"{task_num:04d}-{slug}-bugfix"
    task_dir.mkdir(parents=True)
    public = task_dir / "public"
    public.mkdir()
    write_text(public / "instruction.md", render_bugfix_instruction(spec))
    buggy = public / "buggy_bundle"
    artifacts = copy_solution(source_task, buggy, spec)
    changed = overlay_mutation(source_task, seed_review["mutation_id"], buggy, artifacts)
    contract = public_semantics(spec)
    contract.update({
        "schema_version": "v4-benchmarkv4-public-contract-v1",
        "task_id": f"v4-{task_num}",
        "form": "bugfix",
        "target_artifacts": artifacts,
        "buggy_input_artifacts": [f"buggy_bundle/{path}" for path in artifacts],
        "editable_scope": "complete_declared_verilog_a_bundle",
        "problem_statement": "the supplied system violates the public contract",
        "feedback": {"available_in_modes": ["G2", "G3", "G4", "G5"], "command": "vabench feedback run"},
    })
    public_contract = write_public_contract(output, task_dir, contract)
    evaluator = task_dir / "evaluator"
    materialize_standalone_evaluator(source_task, evaluator, include_negative_suite=False)
    provenance = task_dir / "provenance"
    provenance.mkdir()
    shutil.copy2(source_task / "evaluator" / "task_record.json", provenance / "source_task_record.json")
    shutil.copy2(source_task / "evaluator" / "derivation_manifest.json", provenance / "source_derivation_manifest.json")
    write_json(evaluator / "score_policy.json", {
        "schema_version": "v4-bugfix-score-policy-v1",
        "task_id": f"v4-{task_num}",
        "candidate_artifacts": artifacts,
        "artifact_mode": spec["artifact_contract"]["mode"],
        "full_contract_pass_required": True,
        "spectre_final_judge": True,
        "materialized_checker_profile": "evaluator/checker_profile.json",
        "checker_profile_sha256": file_sha(evaluator / "checker_profile.json"),
        "gold_solution_tree_sha256": tree_sha(evaluator / "solution"),
    })
    write_json(provenance / "derivation_manifest.json", {
        "schema_version": "v4-derivation-manifest-v2",
        "family_id": family,
        "base_dut": {
            "canonical_task_id": f"v4-{family}",
            "canonical_task_slug": source_task.name,
            "family_spec_sha256": spec_sha,
            "source_release_manifest_sha256": source_manifest_sha,
            "mutation_catalog_sha256": row["hashes"]["mutation_catalog_sha256"],
        },
        "negative_assignment": negative_assignment(row, seed_review),
        "selection_evidence": seed_review,
        "private_materialization": {
            "changed_artifacts": changed,
            "buggy_bundle_sha256": tree_sha(buggy),
        },
    })
    write_json(provenance / "gold_repair_reference.json", {
        "schema_version": "v4-gold-repair-reference-v1",
        "materialized_solution": "evaluator/solution",
        "solution_tree_sha256": tree_sha(evaluator / "solution"),
        "gold_dut_certification_sha256": row["hashes"]["task_certification_sha256"],
        "simulation_rerun_required_for_materialization": False,
    })
    bundle_sha = public_bundle_hash(task_dir)
    write_task_record(task_dir, common_task_record(
        task_id=f"v4-{task_num}", form="bugfix", family_id=family,
        directory=rel(task_dir, output), spec_sha=spec_sha,
        source_task_slug=source_task.name, candidate_artifacts=artifacts,
        public_contract=public_contract,
        public_bundle_sha=bundle_sha,
    ))
    return {
        "task_id": f"v4-{task_num}",
        "form": "bugfix",
        "family_id": family,
        "task_dir": rel(task_dir, output),
        "public_contract": public_contract,
    }


def prompt_component_subdir(component_id: str) -> str:
    kind = COMPONENT_METADATA[component_id]["kind"]
    return COMPONENT_SUBDIR_BY_KIND[kind]


def install_prompt_assets(output: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    wrappers: dict[str, dict[str, Any]] = {}
    form_skills: dict[str, dict[str, Any]] = {}
    feedback_guides: dict[str, dict[str, Any]] = {}
    for source in sorted(PROMPT_ASSETS.rglob("*.md")):
        if source.name not in COMPONENT_METADATA:
            raise SystemExit(f"prompt component lacks metadata: {source.name}")
        destination = output / "prompt_modes" / prompt_component_subdir(source.name) / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        metadata = COMPONENT_METADATA[source.name]
        fingerprint = component_fingerprint(source.name, destination)
        record = {
            "path": rel(destination, output),
            **fingerprint,
            "stable_id": metadata["stable_id"],
            "kind": metadata["kind"],
            "semantic_version": "1.0.0",
            "applicable_forms": metadata["applicable_forms"],
            "license": {"status": "repository_license_pending", "spdx": None},
            "provenance": {"type": "project_authored", "source": "V4_TRI_FORM_BENCHMARK_REQUIREMENTS.md"},
        }
        records[source.name] = record
        if metadata["kind"] == "wrapper":
            wrappers[source.name] = record
        elif metadata["kind"] == "form_skill":
            form_skills[source.name] = record
        elif metadata["kind"] == "feedback_guide":
            feedback_guides[source.name] = record
        else:
            raise SystemExit(f"unknown prompt component kind: {metadata['kind']}")
    write_json(output / "prompt_modes" / "manifest.json", {
        "schema_version": "v4-prompt-component-manifest-v1",
        "reference_tokenizer": REFERENCE_TOKENIZER,
        "components": records,
        "wrappers": wrappers,
        "form_skills": form_skills,
        "feedback_guides": feedback_guides,
    })
    write_json(output / "prompt_modes" / "modes.json", {
        "schema_version": "v4-prompt-mode-registry-v1",
        "modes": MODES,
        "composition_order": [
            "canonical_instruction_and_inline_artifacts",
            "form_skill",
            "feedback_guide",
            "mode_wrapper_response_protocol",
        ],
        "working_token_budget": "runner_supplied_same_ceiling_within_comparison_stratum",
        "wall_time_policy": "safety_limit_not_ability_budget",
    })
    return records


def iter_public_inputs(task_dir: Path, form: str, mode: str | None = None) -> Iterable[Path]:
    public = task_dir / "public"
    yield public / "instruction.md"
    if form == "testbench":
        yield from sorted((public / "supplied_dut").rglob("*.va"))
    elif form == "bugfix":
        yield from sorted((public / "buggy_bundle").rglob("*.va"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if output.exists():
        if not args.force:
            raise SystemExit(f"output exists; pass --force to replace it: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)

    denominator_path = source / "score_denominator_manifest.json"
    denominator = read_json(denominator_path)
    rows = denominator.get("tasks") or []
    if len(rows) != 400:
        raise SystemExit("source release must contain exactly 400 canonical DUT rows")
    source_manifest_sha = file_sha(denominator_path)
    task_rows: list[dict[str, Any]] = []
    seed_rows: list[dict[str, Any]] = []
    for row in rows:
        family = str(row["canonical_dut_id"])
        source_task = source / str(row["release_dir"])
        spec_path = source_task / "evaluator" / "family_spec.json"
        spec = read_json(spec_path)
        if str(spec.get("family_id")) != family:
            raise SystemExit(f"{source_task.name}: family spec ID mismatch")
        spec_sha = file_sha(spec_path)
        seed_review = select_bugfix_seed(row)
        seed_rows.append({"family_id": family, **seed_review})
        task_rows.extend([
            build_dut_view(output, source_task, row, spec, spec_sha),
            build_testbench_view(output, source_task, row, spec, spec_sha, source_manifest_sha, seed_review),
            build_bugfix_view(output, source_task, row, spec, spec_sha, source_manifest_sha, seed_review),
        ])

    task_rows.sort(key=lambda item: (item["form"], int(item["family_id"])))
    install_prompt_assets(output)
    write_json(output / "BUGFIX_SEED_REVIEW.json", {
        "schema_version": "v4-bugfix-seed-review-v1",
        "selection_policy": "semantic_fault_complexity_v1",
        "families": seed_rows,
    })
    write_json(output / "TASK_INDEX.json", {"schema_version": "v4-benchmarkv4-task-index-v1", "tasks": task_rows})
    counts = {form: sum(item["form"] == form for item in task_rows) for form in ("dut", "testbench", "bugfix")}
    manifest = {
        "schema_version": "v4-benchmarkv4-release-manifest-v1",
        "release_status": "materialized_hash_bound_certification_reuse_audit_pending",
        "family_count": 400,
        "task_count": len(task_rows),
        "task_counts": counts,
        "source_release_label": source.name,
        "source_score_denominator_manifest_sha256": source_manifest_sha,
        "source_active_mutation_count": denominator.get("active_mutation_count"),
        "active_mutations_per_family": denominator.get("active_mutations_per_family"),
        "spectre_final_judge": True,
        "simulation_rerun_count_for_materialization": 0,
        "certification_reuse": {
            "policy": "source_denominator_hash_bound",
            "source_dut_gold_certification_count": 400,
            "source_negative_certification_count": 2000,
            "simulation_rerun_required_for_materialization": False,
        },
        "prompt_record_count": len(task_rows) * len(MODES),
        "release_surface": "benchmarkv4_package",
        "public_surface": {
            "tasks": "tasks",
            "prompt_modes": "prompt_modes",
            "task_index": "TASK_INDEX.json",
        },
        "package_layout": {
            "task_public_inputs": "tasks/<form>/<task>/public",
            "task_evaluator_assets": "tasks/<form>/<task>/evaluator",
            "task_provenance": "tasks/<form>/<task>/provenance",
            "task_contract": "tasks/<form>/<task>/public_contract.json",
        },
        "tasks_index": "TASK_INDEX.json",
        "materialized_artifact_sha256": materialized_artifact_hashes(output, MATERIALIZED_ARTIFACTS),
    }
    write_json(output / "MANIFEST.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
