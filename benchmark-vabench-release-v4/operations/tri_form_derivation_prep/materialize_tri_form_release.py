#!/usr/bin/env python3
"""Materialize the standalone benchmarkv4 task package.

The frozen exact-five DUT release is the only family source.  The generated
benchmarkv4 package keeps each task self-contained for running and scoring:
solver-visible inputs live under ``public/`` and local scoring assets live
under ``evaluator/``.  Source/provenance evidence stays in the release build
pipeline instead of being replicated into every task directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable

from source_certification_binding import inspect_source_certification_reuse
from score_denominator_registry import (
    load_family_rows,
    load_registry_metadata,
    score_denominator_registry_sha256,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
PREP_ROOT = Path(__file__).resolve().parent
SCRIPTS_ROOT = PACKAGE_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from render_r45_canonical_test import (  # noqa: E402
    REUSE_POLICY as CANONICAL_TEST_REUSE_POLICY,
    bind_deployed_test_deck,
    build_canonical_test,
)
DEFAULT_SOURCE = PACKAGE_ROOT / "provenance" / "dut-base-v3-exact-five-hash-bound-v2"
DEFAULT_OUTPUTS = {
    "r44": PACKAGE_ROOT / "release" / "benchmarkv4",
    "r45": PACKAGE_ROOT / "release" / "benchmarkv4-r45",
    "r47": PACKAGE_ROOT / "release" / "benchmarkv4-r47",
    "r48": PACKAGE_ROOT / "release" / "benchmarkv4-r48",
    "r49": PACKAGE_ROOT / "release" / "benchmarkv4-r49",
    "r50": PACKAGE_ROOT / "release" / "benchmarkv4-r50",
    "r51": PACKAGE_ROOT / "release" / "benchmarkv4-r51",
}
PROMPT_ASSETS = PREP_ROOT / "prompt_assets"
NEXT_RUNTIME_TRANSPORT_WRAPPER_REVISIONS = frozenset({"r52"})
NEXT_RUNTIME_TRANSPORT_WRAPPER = (
    PROMPT_ASSETS / "wrappers" / "direct_wrapper_runtime_transport.md"
)
SKILLS_ROOT = PACKAGE_ROOT.parent / "skills"
SKILL_IDS = ("veriloga", "vabench-feedback")
REAL_SKILL_REVISIONS = frozenset({"r50", "r51"})
REAL_SKILL_MODES = {
    "G0": {"process": "direct_one_shot", "skills": [], "evas_cli": False},
    "G1": {"process": "direct_one_shot", "skills": ["veriloga"], "evas_cli": False},
    "G2": {"process": "agentic", "skills": [], "evas_cli": True},
    "G3": {"process": "agentic", "skills": ["veriloga"], "evas_cli": True},
    "G4": {"process": "agentic", "skills": ["vabench-feedback"], "evas_cli": True},
    "G5": {"process": "agentic", "skills": ["veriloga", "vabench-feedback"], "evas_cli": True},
}
LEGACY_MODES = {
    "G0": {"process": "direct_one_shot", "form_skill": False, "evas_guide": False, "evas_cli": False},
    "G1": {"process": "direct_one_shot", "form_skill": True, "evas_guide": False, "evas_cli": False},
    "G2": {"process": "agentic", "form_skill": False, "evas_guide": False, "evas_cli": True},
    "G3": {"process": "agentic", "form_skill": True, "evas_guide": False, "evas_cli": True},
    "G4": {"process": "agentic", "form_skill": False, "evas_guide": True, "evas_cli": True},
    "G5": {"process": "agentic", "form_skill": True, "evas_guide": True, "evas_cli": True},
}
# The active comparison contract is the real-skill registry introduced in r50.
# The legacy registry remains available only to reproduce sealed pre-r50 releases.
MODES = REAL_SKILL_MODES
FORM_SKILLS = {
    "dut": "dut_modeling.md",
    "testbench": "testbench_verification.md",
    "bugfix": "bugfix_diagnosis.md",
}
EVAS_GUIDES = {
    "dut": "evas_dut.md",
    "testbench": "evas_testbench.md",
    "bugfix": "evas_bugfix.md",
}
EVAS_CORE = "evas_core.md"
MATERIALIZED_ARTIFACTS = (
    "TASK_INDEX.json",
    "prompt_modes/modes.json",
    "prompt_modes/manifest.json",
)
PUBLIC_MATERIALIZED_ARTIFACTS = MATERIALIZED_ARTIFACTS
REAL_SKILL_MATERIALIZED_ARTIFACTS = (*MATERIALIZED_ARTIFACTS, "skills/SNAPSHOT_MANIFEST.json")
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
}
LEGACY_COMPONENT_METADATA = {
    **COMPONENT_METADATA,
    "dut_modeling.md": {"stable_id": "component.form.dut", "kind": "form_skill", "applicable_forms": ["dut"]},
    "testbench_verification.md": {"stable_id": "component.form.testbench", "kind": "form_skill", "applicable_forms": ["testbench"]},
    "bugfix_diagnosis.md": {"stable_id": "component.form.bugfix", "kind": "form_skill", "applicable_forms": ["bugfix"]},
    "evas_core.md": {"stable_id": "component.evas.core", "kind": "evas_guide", "applicable_forms": ["dut", "testbench", "bugfix"]},
    "evas_dut.md": {"stable_id": "component.evas.dut", "kind": "evas_guide", "applicable_forms": ["dut"]},
    "evas_testbench.md": {"stable_id": "component.evas.testbench", "kind": "evas_guide", "applicable_forms": ["testbench"]},
    "evas_bugfix.md": {"stable_id": "component.evas.bugfix", "kind": "evas_guide", "applicable_forms": ["bugfix"]},
}
COMPONENT_SUBDIR_BY_KIND = {
    "wrapper": "wrappers",
    "form_skill": "form_skills",
    "evas_guide": "evas_guides",
}
SKILL_SOURCES = {
    "veriloga": {
        "type": "vendored_runtime_subset",
        "path": "skills/veriloga",
        "upstream_repository": "https://github.com/Arcadia-1/veriloga-skills",
        "upstream_commit": "bf3ee9f5c20bbefccc36f1cd58af9a48032a6ca5",
        "upstream_pull_request": "https://github.com/Arcadia-1/veriloga-skills/pull/17",
        "included_paths": ["SKILL.md", "agents/**", "assets/**", "references/**"],
    },
    "vabench-feedback": {
        "type": "in_repository",
        "path": "skills/vabench-feedback",
    },
}
STANDALONE_EVALUATOR_COMMON = (
    "family_spec.json",
    "checker_profile.json",
    "harness_spec.json",
    "score_tb.scs",
)
INDEPENDENT_REFERENCE_TB = "independent_reference_tb"
LEGACY_SCORE_TB_FALLBACK = "legacy_score_tb_fallback"
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


def resolve_testbench_reference(source_task: Path) -> tuple[Path, str]:
    """Resolve the canonical TB-form gold without masking legacy fallback."""
    evaluator = source_task / "evaluator"
    independent = evaluator / "reference_tb.scs"
    if independent.is_file():
        return independent, INDEPENDENT_REFERENCE_TB
    legacy = evaluator / "score_tb.scs"
    if legacy.is_file():
        return legacy, LEGACY_SCORE_TB_FALLBACK
    raise SystemExit(f"{source_task.name}: missing evaluator/reference_tb.scs and evaluator/score_tb.scs")


def materialized_testbench_reference(source_task: Path, reference: Path) -> str:
    """Render the reference deck against the public supplied-DUT mount."""

    text = reference.read_text(encoding="utf-8")
    if (source_task / "public" / "task" / "public_support").is_dir():
        text = text.replace(
            'ahdl_include "./support/',
            'ahdl_include "./dut/support/',
        )
    return text


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


def materialized_artifacts_for_revision(revision: str) -> tuple[str, ...]:
    return (
        REAL_SKILL_MATERIALIZED_ARTIFACTS
        if revision in REAL_SKILL_REVISIONS
        else MATERIALIZED_ARTIFACTS
    )


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


def render_parameter_evaluation_policy(spec: dict[str, Any]) -> str:
    policy = spec.get("evaluation_parameter_policy") or {}
    statement = str(policy.get("statement") or "").strip()
    return f"\n{statement}\n" if statement else ""


def render_binding(spec: dict[str, Any]) -> str:
    binding = spec.get("testbench_binding") or {}
    source_template = str(binding.get("source_path_template") or "./dut/{artifact_path}")
    include_paths = [
        source_template.format(artifact_path=file_record["path"])
        for file_record in (spec.get("artifact_contract") or {}).get("files") or []
    ]
    include_label = "Include path" if len(include_paths) == 1 else "Include paths"
    lines = [
        "The submitted `testbench.scs` must use the supplied DUT through this public binding:",
        "",
        f"- {include_label}: {', '.join(f'`{path}`' for path in include_paths)}",
    ]
    for instance in binding.get("instances") or []:
        connections = sorted(instance.get("connections") or [], key=lambda item: int(item.get("position", 0)))
        ordered_nets = instance.get("ordered_nets")
        nets = (
            " ".join(str(item) for item in ordered_nets)
            if ordered_nets
            else " ".join(str(item["net"]) for item in connections)
        )
        overrides = instance.get("parameter_overrides") or {}
        parameters = " ".join(f"{name}={overrides[name]}" for name in sorted(overrides))
        suffix = f" {parameters}" if parameters else ""
        lines.append(f"- DUT instance: `{instance['name']} ({nets}) {instance['module_ref']}{suffix}`")
    required_traces = [
        str(signal)
        for signal in (spec.get("trace_contract") or {}).get("required_signals") or []
        if str(signal) != "time"
    ]
    lines.extend([
        f"- Required saved public traces: {', '.join(f'`{signal}`' for signal in required_traces)}",
        "- Use one bounded transient analysis with a finite positive stop time.",
        "",
        "You must design the stimulus yourself. Save traces as bare public signal names",
        "(for example `clk`, not suffixed or hierarchical forms such as `clk:V` or",
        "`XDUT.clk`). Do not redefine the DUT, drive DUT output nets, save",
        "hierarchical/private nodes, or use checker/gold/internal files.",
    ])
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


def neutralize_testbench_authoring_directives(text: str) -> str:
    """Keep canonical behavior while removing DUT-form submission directions."""
    substitutions = (
        r"\bThis task asks for\b.*?\bnot\s+(?:a\s+)?Spectre\s+testbench\.\s*",
        r"\bThis is a measurement-helper DUT task,\s*"
        r"not a Spectre testbench-generation task\.\s*",
        r"\bReturn only the Verilog-A source file `[^`]+`\.\s*",
        r"\bBoth\s+files\s+are\s+scored\s+DUT\s+source\s+artifacts;.*?"
        r"\breturning\s+the\s+bundle\.\s*",
        r"\bOnly `[^`]+` is graded as the candidate implementation\.\s*",
        r"\bDo not generate a Spectre `?\.scs`? file despite the historical "
        r"`_tb` filename\.\s*",
    )
    for pattern in substitutions:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    text = re.sub(
        r"^Implement (?P<article>an?) ",
        r"The supplied DUT is \g<article> ",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"(?m)^Implement ",
        "The supplied DUT implements ",
        text,
    )
    text = re.sub(
        r"(?m)^Implement:\s*$",
        "The supplied DUT provides:",
        text,
    )
    text = re.sub(
        r"\bThat support source is not the candidate implementation,\s*"
        r"but\s+the fractional-N model\b",
        "The supplied DUT",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\bThe module\b", "The supplied DUT", text)
    text = re.sub(r"\bthe module\b", "the supplied DUT", text)
    text = re.sub(r"\bthis module\b", "the supplied DUT", text)
    text = re.sub(r"\byour module\b", "the supplied DUT", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def canonical_required_behavior(source_task: Path, form: str) -> str:
    instruction = source_task / "public" / "task" / "instruction.md"
    if not instruction.is_file():
        return ""
    text = sanitize_instruction_text(instruction.read_text(encoding="utf-8"), form)
    match = re.search(
        r"(?ms)^## Required Behavior\s*\n(?P<body>.*?)(?=^##\s|\Z)",
        text,
    )
    if not match:
        return ""
    behavior = match.group("body").strip()
    if form == "testbench":
        behavior = neutralize_testbench_authoring_directives(behavior)
    return behavior


def render_canonical_behavior(value: str) -> str:
    if not value:
        return ""
    return (
        "\nThe following canonical public behavior is normative for this derived form:\n\n"
        f"{value}\n"
    )


def render_testbench_instruction(
    spec: dict[str, Any],
    *,
    support_artifacts: list[str] | None = None,
    canonical_behavior: str = "",
) -> str:
    title = task_title(spec)
    support_clause = ""
    if support_artifacts:
        support_clause = (
            "- Include the supplied read-only support files only from\n"
            "  `./dut/support/...`; do not reference `./support/...` or undeclared paths.\n"
        )
    return f"""# {title} Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `{title}` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

{render_interface(spec)}

Stable public Spectre binding:

{render_binding(spec)}

## Public Parameter Contract

{render_parameters(spec)}
{render_parameter_evaluation_policy(spec)}

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

{render_properties(spec, 'exercise and make observable:')}

Use any deterministic stimulus layout that makes every required public behavior
observable. Exact event counts, absolute event times, sample density, and
reference-deck ordering are not part of the contract unless stated explicitly
above.

{render_canonical_behavior(canonical_behavior)}

The required trace names are: {', '.join(f'`{x}`' for x in (spec.get('trace_contract') or {}).get('required_signals') or [])}.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
{support_clause}- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
"""


def render_bugfix_instruction(
    spec: dict[str, Any],
    *,
    canonical_behavior: str = "",
) -> str:
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
{render_parameter_evaluation_policy(spec)}

## Required Behavior

The repaired bundle must satisfy every public property:

{render_properties(spec, 'restore:')}

{render_canonical_behavior(canonical_behavior)}

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
    return f"tasks/{task_dir.name}/public_contract.json"


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


def copy_public_support(source_task: Path, destination: Path) -> list[str]:
    """Copy public read-only support artifacts under ``support/``.

    Testbench candidates see these files below the same mounted ``./dut`` root
    as the supplied DUT, so a public support file ``foo.va`` is included as
    ``ahdl_include "./dut/support/foo.va"``.  The support files are not target
    artifacts and are not editable candidate outputs.
    """
    source_root = source_task / "public" / "task" / "public_support"
    if not source_root.is_dir():
        return []

    copied: list[str] = []
    for source in sorted(source_root.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(source_root)
        target_rel = Path("support") / relative
        target = destination / target_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(target_rel.as_posix())
    return copied


def uses_portable_rdist_runtime(
    source_task: Path,
    spec: dict[str, Any],
    release_revision: str,
) -> bool:
    """Select the r51 EVAS extension mode from the canonical DUT sources."""

    if release_revision != "r51":
        return False
    for file_record in (spec.get("artifact_contract") or {}).get("files") or []:
        source = source_task / "evaluator" / "solution" / str(file_record["path"])
        if source.is_file() and re.search(
            r"\$rdist_[A-Za-z_][A-Za-z0-9_]*\b",
            source.read_text(encoding="utf-8"),
        ):
            return True
    return False


def direct_evas_command(*, portable_rdist: bool) -> str:
    command = (
        "evas simulate public/task/visible_test.scs "
        "-o /tmp/vabench-visible/evas-output"
    )
    return command if portable_rdist else f"{command} --spectre-strict"


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
    source_task_slug: str, checker_task_id: str, candidate_artifacts: list[str],
    public_contract: str, public_contract_sha: str, public_bundle_sha: str,
    evaluation_binding: dict[str, Any],
    release_revision: str = "r45",
) -> dict[str, Any]:
    return {
        "schema_version": f"{release_revision}-benchmarkv4-task-record-v1",
        "release_revision": release_revision,
        "task_id": task_id,
        "form": form,
        "family_id": family_id,
        "task_dir": directory,
        "public_contract": public_contract,
        "public_contract_sha256": public_contract_sha,
        "candidate_artifacts": candidate_artifacts,
        "family_spec_sha256": spec_sha,
        "canonical_dut_source_slug": source_task_slug,
        "checker_task_id": checker_task_id,
        "public_bundle_sha256": public_bundle_sha,
        "evaluation_binding": evaluation_binding,
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
    copy_public_support(source_task, evaluator / "solution")
    if include_negative_suite:
        shutil.copy2(source_eval / "mutation_catalog.json", evaluator / "mutation_catalog.json")
        copy_tree_skipping(
            source_eval / "mutation_bundles",
            evaluator / "mutation_bundles",
            excluded_names={"certification.json"},
        )


def render_visible_dut_test(canonical_deck: str) -> str:
    """Bind the canonical deck to the agent's writable submission directory."""
    text = canonical_deck
    text = text.replace('ahdl_include "./dut/', 'ahdl_include "../submission/')
    text = text.replace('ahdl_include "./support/', 'ahdl_include "./public_support/')
    return text


def canonical_profile_for_task(source_task: Path) -> tuple[dict[str, Any], str]:
    spec_path = source_task / "evaluator" / "harness_spec.json"
    return build_canonical_test(read_json(spec_path), file_sha(spec_path))


def install_visible_dut_runtime(
    task_dir: Path,
    source_task: Path,
    *,
    release_revision: str = "r45",
    portable_rdist: bool = False,
) -> dict[str, Any]:
    public = task_dir / "public"
    evaluator = task_dir / "evaluator"
    profile, canonical_deck = canonical_profile_for_task(source_task)
    visible = public / "visible_test.scs"
    visible_text = render_visible_dut_test(canonical_deck)
    write_text(visible, visible_text)
    shutil.copy2(visible, evaluator / "trusted_replay_test.scs")
    profile = bind_deployed_test_deck(profile, visible_text)
    profile_path = evaluator / "canonical_test_profile.json"
    write_json(profile_path, profile)
    runtime = {
        "schema_version": (
            f"{release_revision}-direct-evas-runtime-"
            f"{'v3' if portable_rdist else 'v2'}"
        ),
        "command": direct_evas_command(portable_rdist=portable_rdist),
        "working_directory": "runtime_package_root",
        "candidate_root": "public/submission",
        "test": "visible_test.scs",
        "trusted_replay": "byte_identical_visible_test",
        "visible_test_sha256": file_sha(visible),
    }
    if portable_rdist:
        runtime["compatibility_mode"] = "portable"
    write_json(public / "evas_runtime.json", runtime)
    return {
        "kind": "canonical_test_deck",
        "profile": "evaluator/canonical_test_profile.json",
        "profile_sha256": file_sha(profile_path),
        "canonical_semantics_sha256": profile["canonical_semantics_sha256"],
        "public_test": "public/visible_test.scs",
        "trusted_replay_test": "evaluator/trusted_replay_test.scs",
        "test_deck_sha256": file_sha(visible),
        "reuse_policy": CANONICAL_TEST_REUSE_POLICY,
    }


def install_visible_testbench_runtime(
    task_dir: Path,
    source_task: Path,
    spec: dict[str, Any],
    mutation_ids: list[str],
    *,
    release_revision: str = "r45",
    portable_rdist: bool = False,
) -> dict[str, Any]:
    public = task_dir / "public"
    evaluator = task_dir / "evaluator"
    fixtures = public / "visible_fixtures"
    reference_dut = fixtures / "reference" / "dut"
    copy_solution(source_task, reference_dut, spec)
    copy_public_support(source_task, reference_dut)

    cases = [{"case": "reference", "dut_root": "visible_fixtures/reference/dut"}]
    for index, mutation_id in enumerate(mutation_ids, start=1):
        case = f"mutation_{index:02d}"
        dut_root = fixtures / case / "dut"
        artifact_paths = copy_solution(source_task, dut_root, spec)
        copy_public_support(source_task, dut_root)
        overlay_mutation(source_task, mutation_id, dut_root, artifact_paths)
        cases.append({"case": case, "dut_root": f"visible_fixtures/{case}/dut"})

    suite = {
        "schema_version": (
            f"{release_revision}-direct-evas-testbench-suite-"
            f"{'v3' if portable_rdist else 'v2'}"
        ),
        "candidate": "public/submission/testbench.scs",
        "candidate_dut_binding": "./dut",
        "cases": cases,
        "fixture_policy": "read_only_and_identical_for_visible_and_final_replay",
        "working_directory": "runtime_package_root",
        "candidate_command_template": (
            "rm -rf /tmp/vabench-visible/runs/{case} "
            "/tmp/vabench-visible/evas-output/{case} && "
            "mkdir -p /tmp/vabench-visible/runs/{case} && "
            "cp public/submission/testbench.scs "
            "/tmp/vabench-visible/runs/{case}/testbench.scs && "
            "ln -sfn \"$(pwd)/public/task/{dut_root}\" "
            "/tmp/vabench-visible/runs/{case}/dut && "
            "evas simulate /tmp/vabench-visible/runs/{case}/testbench.scs "
            f"-o /tmp/vabench-visible/evas-output/{{case}}"
            f"{'' if portable_rdist else ' --spectre-strict'}"
        ),
        "fixture_tree_sha256": tree_sha(fixtures),
    }
    if portable_rdist:
        suite["compatibility_mode"] = "portable"
    write_json(public / "evas_runtime.json", suite)
    shutil.copy2(public / "evas_runtime.json", evaluator / "trusted_replay_suite.json")
    copy_tree(fixtures, evaluator / "trusted_replay_fixtures")
    return {
        "kind": "public_testbench_suite",
        "public_suite": "public/evas_runtime.json",
        "public_suite_sha256": file_sha(public / "evas_runtime.json"),
        "public_fixture_tree": "public/visible_fixtures",
        "public_fixture_tree_sha256": tree_sha(fixtures),
        "trusted_replay_suite": "evaluator/trusted_replay_suite.json",
        "trusted_replay_fixture_tree": "evaluator/trusted_replay_fixtures",
        "reuse_policy": "public_and_trusted_replay_suite_same_bytes",
    }


def evaluator_checker_task_id(evaluator: Path) -> str:
    checker_profile = read_json(evaluator / "checker_profile.json")
    return str(checker_profile.get("checker_task_id") or "")


def build_dut_view(
    output: Path,
    source_task: Path,
    row: dict[str, Any],
    spec: dict[str, Any],
    spec_sha: str,
    *,
    release_revision: str = "r45",
) -> dict[str, Any]:
    family = str(row["canonical_dut_id"])
    portable_rdist = uses_portable_rdist_runtime(
        source_task, spec, release_revision
    )
    task_dir = output / "tasks" / source_task.name
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
        "evas": {
            "available_in_modes": ["G2", "G3", "G4", "G5"],
            "command": direct_evas_command(portable_rdist=portable_rdist),
            "visible_and_final_test": "identical",
        },
    })
    if portable_rdist:
        contract["evas"]["compatibility_mode"] = "portable"
    public_contract = write_public_contract(output, task_dir, contract)
    public_contract_sha = file_sha(output / public_contract)
    evaluator = task_dir / "evaluator"
    materialize_standalone_evaluator(source_task, evaluator, include_negative_suite=False)
    write_json(evaluator / "score_policy.json", {
        "schema_version": "v4-dut-score-policy-v1",
        "task_id": f"v4-{family}",
        "candidate_artifacts": contract["target_artifacts"],
        "full_contract_pass_required": True,
        "certification_evaluator": "rust_evas2",
        "materialized_checker_profile": "evaluator/checker_profile.json",
        "checker_profile_sha256": file_sha(evaluator / "checker_profile.json"),
        "gold_solution_tree_sha256": tree_sha(evaluator / "solution"),
        "gold_dut_certification_sha256": row["hashes"]["task_certification_sha256"],
    })
    evaluation_binding = install_visible_dut_runtime(
        task_dir,
        source_task,
        release_revision=release_revision,
        portable_rdist=portable_rdist,
    )
    bundle_sha = public_bundle_hash(task_dir)
    write_task_record(task_dir, common_task_record(
        task_id=f"v4-{family}", form="dut", family_id=family,
        directory=rel(task_dir, output), spec_sha=spec_sha,
        source_task_slug=source_task.name,
        checker_task_id=evaluator_checker_task_id(evaluator),
        candidate_artifacts=contract["target_artifacts"], public_contract=public_contract,
        public_contract_sha=public_contract_sha,
        public_bundle_sha=bundle_sha,
        evaluation_binding=evaluation_binding,
        release_revision=release_revision,
    ))
    return {
        "task_id": f"v4-{family}",
        "form": "dut",
        "family_id": family,
        "task_dir": rel(task_dir, output),
        "public_contract": public_contract,
        "public_contract_sha256": public_contract_sha,
    }


def build_testbench_view(
    output: Path,
    source_task: Path,
    row: dict[str, Any],
    spec: dict[str, Any],
    spec_sha: str,
    seed_review: dict[str, Any],
    *,
    release_revision: str = "r45",
) -> dict[str, Any]:
    family = str(row["canonical_dut_id"])
    portable_rdist = uses_portable_rdist_runtime(
        source_task, spec, release_revision
    )
    task_num = 500 + int(family)
    slug = source_task.name.split("-", 1)[1]
    task_dir = output / "tasks" / f"{task_num:03d}-{slug}-testbench"
    task_dir.mkdir(parents=True)
    public = task_dir / "public"
    public.mkdir()
    supplied = public / "supplied_dut"
    artifacts = copy_solution(source_task, supplied, spec)
    support_artifacts = copy_public_support(source_task, supplied)
    write_text(
        public / "instruction.md",
        render_testbench_instruction(
            spec,
            support_artifacts=support_artifacts,
            canonical_behavior=canonical_required_behavior(source_task, "testbench"),
        ),
    )
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
        "evas": {
            "available_in_modes": ["G2", "G3", "G4", "G5"],
            "runtime_contract": "public/task/evas_runtime.json",
            "visible_and_final_suite": "identical_reference_plus_five_mutations",
        },
        "security_summary": [
            "only declared ./dut source bindings are allowed",
            "DUT redefinition, direct output drive, private hierarchical probes, arbitrary file access, and unbounded analyses are rejected",
        ],
    })
    if portable_rdist:
        contract["evas"]["compatibility_mode"] = "portable"
    if support_artifacts:
        contract["supplied_support_artifacts"] = [
            f"supplied_dut/{path}" for path in support_artifacts
        ]
    public_contract = write_public_contract(output, task_dir, contract)
    public_contract_sha = file_sha(output / public_contract)
    evaluator = task_dir / "evaluator"
    materialize_standalone_evaluator(source_task, evaluator, include_negative_suite=True)
    reference_tb, reference_tb_source_kind = resolve_testbench_reference(source_task)
    reference_target = evaluator / "reference_tb.scs"
    write_text(reference_target, materialized_testbench_reference(source_task, reference_tb))
    suite = [str(item["mutation_id"]) for item in row["active_mutations"]]
    score_policy = {
        "schema_version": "v4-testbench-score-policy-v1",
        "task_id": f"v4-{task_num:03d}",
        "candidate_artifacts": ["testbench.scs"],
        "reference_gate": "all applicable public properties pass on supplied correct DUT",
        "negative_outcomes": ["killed_behaviorally", "survived", "invalid_run"],
        "full_credit": "reference_gate and five_of_five_killed_behaviorally",
        "kill_ratio_denominator": 5,
        "certification_evaluator": "rust_evas2",
        "materialized_checker_profile": "evaluator/checker_profile.json",
        "checker_profile_sha256": file_sha(evaluator / "checker_profile.json"),
        "reference_tb_sha256": file_sha(reference_target),
        "mutation_catalog_sha256": row["hashes"]["mutation_catalog_sha256"],
        "negative_suite_mutation_ids": suite,
        "bugfix_seed_mutation_id": seed_review["mutation_id"],
    }
    if support_artifacts:
        score_policy["read_only_support_artifacts"] = support_artifacts
    if reference_tb_source_kind == "independent_reference_tb":
        score_policy["reference_tb_source_kind"] = reference_tb_source_kind
    write_json(evaluator / "score_policy.json", score_policy)
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
    evaluation_binding = install_visible_testbench_runtime(
        task_dir,
        source_task,
        spec,
        suite,
        release_revision=release_revision,
        portable_rdist=portable_rdist,
    )
    bundle_sha = public_bundle_hash(task_dir)
    write_task_record(task_dir, common_task_record(
        task_id=f"v4-{task_num:03d}", form="testbench", family_id=family,
        directory=rel(task_dir, output), spec_sha=spec_sha,
        source_task_slug=source_task.name,
        checker_task_id=evaluator_checker_task_id(evaluator),
        candidate_artifacts=["testbench.scs"],
        public_contract=public_contract,
        public_contract_sha=public_contract_sha,
        public_bundle_sha=bundle_sha,
        evaluation_binding=evaluation_binding,
        release_revision=release_revision,
    ))
    return {
        "task_id": f"v4-{task_num:03d}",
        "form": "testbench",
        "family_id": family,
        "task_dir": rel(task_dir, output),
        "public_contract": public_contract,
        "public_contract_sha256": public_contract_sha,
    }


def build_bugfix_view(
    output: Path,
    source_task: Path,
    row: dict[str, Any],
    spec: dict[str, Any],
    spec_sha: str,
    seed_review: dict[str, Any],
    *,
    release_revision: str = "r45",
) -> dict[str, Any]:
    family = str(row["canonical_dut_id"])
    portable_rdist = uses_portable_rdist_runtime(
        source_task, spec, release_revision
    )
    task_num = 1000 + int(family)
    slug = source_task.name.split("-", 1)[1]
    task_dir = output / "tasks" / f"{task_num:04d}-{slug}-bugfix"
    task_dir.mkdir(parents=True)
    public = task_dir / "public"
    public.mkdir()
    write_text(
        public / "instruction.md",
        render_bugfix_instruction(
            spec,
            canonical_behavior=canonical_required_behavior(source_task, "bugfix"),
        ),
    )
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
        "evas": {
            "available_in_modes": ["G2", "G3", "G4", "G5"],
            "command": direct_evas_command(portable_rdist=portable_rdist),
            "visible_and_final_test": "identical",
        },
    })
    if portable_rdist:
        contract["evas"]["compatibility_mode"] = "portable"
    public_contract = write_public_contract(output, task_dir, contract)
    public_contract_sha = file_sha(output / public_contract)
    evaluator = task_dir / "evaluator"
    materialize_standalone_evaluator(source_task, evaluator, include_negative_suite=False)
    write_json(evaluator / "score_policy.json", {
        "schema_version": "v4-bugfix-score-policy-v1",
        "task_id": f"v4-{task_num}",
        "candidate_artifacts": artifacts,
        "artifact_mode": spec["artifact_contract"]["mode"],
        "full_contract_pass_required": True,
        "certification_evaluator": "rust_evas2",
        "materialized_checker_profile": "evaluator/checker_profile.json",
        "checker_profile_sha256": file_sha(evaluator / "checker_profile.json"),
        "gold_solution_tree_sha256": tree_sha(evaluator / "solution"),
        "mutation_catalog_sha256": row["hashes"]["mutation_catalog_sha256"],
        "bugfix_seed_mutation_id": seed_review["mutation_id"],
        "bugfix_seed_selection_status": seed_review["selection_status"],
        "bugfix_seed_triviality_markers": seed_review["triviality_markers"],
        "buggy_bundle_sha256": tree_sha(buggy),
        "changed_artifacts": changed,
        "gold_dut_certification_sha256": row["hashes"]["task_certification_sha256"],
    })
    evaluation_binding = install_visible_dut_runtime(
        task_dir,
        source_task,
        release_revision=release_revision,
        portable_rdist=portable_rdist,
    )
    bundle_sha = public_bundle_hash(task_dir)
    write_task_record(task_dir, common_task_record(
        task_id=f"v4-{task_num}", form="bugfix", family_id=family,
        directory=rel(task_dir, output), spec_sha=spec_sha,
        source_task_slug=source_task.name,
        checker_task_id=evaluator_checker_task_id(evaluator),
        candidate_artifacts=artifacts,
        public_contract=public_contract,
        public_contract_sha=public_contract_sha,
        public_bundle_sha=bundle_sha,
        evaluation_binding=evaluation_binding,
        release_revision=release_revision,
    ))
    return {
        "task_id": f"v4-{task_num}",
        "form": "bugfix",
        "family_id": family,
        "task_dir": rel(task_dir, output),
        "public_contract": public_contract,
        "public_contract_sha256": public_contract_sha,
    }


def prompt_component_subdir(
    component_id: str, metadata: dict[str, dict[str, Any]] | None = None
) -> str:
    kind = (metadata or COMPONENT_METADATA)[component_id]["kind"]
    return COMPONENT_SUBDIR_BY_KIND[kind]


def skill_file_records(skill_id: str, release_skill_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in sorted(release_skill_root.rglob("*")):
        if not item.is_file():
            continue
        if item.is_symlink():
            raise SystemExit(f"skill snapshot contains symlink: {item}")
        relative = item.relative_to(release_skill_root).as_posix()
        records.append({
            "path": relative,
            "sha256": file_sha(item),
            "bytes": item.stat().st_size,
            "source_path": (Path("skills") / skill_id / relative).as_posix(),
        })
    return records


def install_skill_snapshots(output: Path) -> dict[str, dict[str, Any]]:
    skills: dict[str, dict[str, Any]] = {}
    release_skills = output / "skills"
    for skill_id in SKILL_IDS:
        source = SKILLS_ROOT / skill_id
        if not (source / "SKILL.md").is_file():
            raise SystemExit(f"missing real skill package: {source}")
        if source.is_symlink() or any(item.is_symlink() for item in source.rglob("*")):
            raise SystemExit(f"skill source contains symlink: {source}")
        destination = release_skills / skill_id
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination, symlinks=False)
        files = skill_file_records(skill_id, destination)
        skills[skill_id] = {
            "id": skill_id,
            "path": rel(destination, output),
            "skill_file": f"skills/{skill_id}/SKILL.md",
            "tree_sha256": tree_sha(destination),
            "files": files,
            "source": SKILL_SOURCES[skill_id],
            "license": {"status": "not_declared_in_source_repository", "spdx": None},
        }
    write_json(release_skills / "SNAPSHOT_MANIFEST.json", {
        "schema_version": "v4-real-skill-snapshot-manifest-v1",
        "skills": skills,
        "mode_skill_matrix": {
            mode: list(policy.get("skills") or [])
            for mode, policy in MODES.items()
        },
    })
    return skills


def install_prompt_assets(
    output: Path, release_revision: str = "r50"
) -> dict[str, dict[str, Any]]:
    real_skills = release_revision in REAL_SKILL_REVISIONS
    component_metadata = COMPONENT_METADATA if real_skills else LEGACY_COMPONENT_METADATA
    modes = REAL_SKILL_MODES if real_skills else LEGACY_MODES
    records: dict[str, dict[str, Any]] = {}
    wrappers: dict[str, dict[str, Any]] = {}
    form_skills: dict[str, dict[str, Any]] = {}
    evas_guides: dict[str, dict[str, Any]] = {}
    sources = {source.name: source for source in sorted(PROMPT_ASSETS.rglob("*.md"))}
    missing_sources = sorted(set(component_metadata) - set(sources))
    if missing_sources:
        raise SystemExit(f"prompt component source(s) missing: {missing_sources}")
    for component_id in component_metadata:
        source = (
            NEXT_RUNTIME_TRANSPORT_WRAPPER
            if (
                component_id == "direct_wrapper.md"
                and release_revision in NEXT_RUNTIME_TRANSPORT_WRAPPER_REVISIONS
            )
            else sources[component_id]
        )
        destination = (
            output
            / "prompt_modes"
            / prompt_component_subdir(component_id, component_metadata)
            / component_id
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        metadata = component_metadata[component_id]
        fingerprint = component_fingerprint(component_id, destination)
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
        records[component_id] = record
        if metadata["kind"] == "wrapper":
            wrappers[component_id] = record
        elif metadata["kind"] == "form_skill":
            form_skills[component_id] = record
        elif metadata["kind"] == "evas_guide":
            evas_guides[component_id] = record
        else:
            raise SystemExit(f"unknown prompt component kind: {metadata['kind']}")
    manifest = {
        "schema_version": "v4-prompt-component-manifest-v1",
        "reference_tokenizer": REFERENCE_TOKENIZER,
        "components": records,
        "wrappers": wrappers,
    }
    if real_skills:
        skills = install_skill_snapshots(output)
        manifest.update({
            "skills_manifest": "skills/SNAPSHOT_MANIFEST.json",
            "skill_snapshots": {
                skill_id: {
                    "path": record["path"],
                    "skill_file": record["skill_file"],
                    "tree_sha256": record["tree_sha256"],
                }
                for skill_id, record in skills.items()
            },
        })
    else:
        manifest.update({
            "form_skills": form_skills,
            "evas_guides": evas_guides,
        })
    write_json(output / "prompt_modes" / "manifest.json", manifest)
    write_json(output / "prompt_modes" / "modes.json", {
        "schema_version": "v4-prompt-mode-registry-v1",
        "modes": modes,
        "composition_order": (
            [
                "canonical_instruction_and_inline_artifacts",
                "real_skill_lookup_when_enabled",
                "mode_wrapper_response_protocol",
            ]
            if real_skills
            else [
                "canonical_instruction_and_inline_artifacts",
                "form_skill",
                "evas_guide",
                "mode_wrapper_response_protocol",
            ]
        ),
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
    parser.add_argument(
        "--release-revision",
        choices=tuple(DEFAULT_OUTPUTS),
        required=True,
        help="release contract to materialize; revisions never share an output tree",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    revision = str(args.release_revision)
    if revision == "r44":
        raise SystemExit(
            "r44 is immutable; audit the tracked release instead of rebuilding it"
        )
    output = (args.output or DEFAULT_OUTPUTS[revision]).expanduser().resolve()
    if (
        output == DEFAULT_OUTPUTS[revision].resolve()
        and (output / "RELEASE_SEAL.json").is_file()
    ):
        raise SystemExit(
            f"{revision} is immutable; materialize it only to an explicit comparison output"
        )
    if output.exists():
        if not args.force:
            raise SystemExit(f"output exists; pass --force to replace it: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)

    denominator_metadata = load_registry_metadata(source)
    rows = load_family_rows(source)
    if len(rows) != 400:
        raise SystemExit("source release must contain exactly 400 canonical DUT rows")
    source_rows = {str(row["canonical_dut_id"]): row for row in rows}
    certification_reuse, _ = inspect_source_certification_reuse(source, source_rows)
    source_registry_sha = score_denominator_registry_sha256(source)
    task_rows: list[dict[str, Any]] = []
    for row in rows:
        family = str(row["canonical_dut_id"])
        source_task = source / str(row["release_dir"])
        spec_path = source_task / "evaluator" / "family_spec.json"
        spec = read_json(spec_path)
        if str(spec.get("family_id")) != family:
            raise SystemExit(f"{source_task.name}: family spec ID mismatch")
        spec_sha = file_sha(spec_path)
        seed_review = select_bugfix_seed(row)
        task_rows.extend([
            build_dut_view(
                output,
                source_task,
                row,
                spec,
                spec_sha,
                release_revision=revision,
            ),
            build_testbench_view(
                output,
                source_task,
                row,
                spec,
                spec_sha,
                seed_review,
                release_revision=revision,
            ),
            build_bugfix_view(
                output,
                source_task,
                row,
                spec,
                spec_sha,
                seed_review,
                release_revision=revision,
            ),
        ])

    task_rows.sort(key=lambda item: int(str(item["task_id"]).split("-", 1)[1]))
    install_prompt_assets(output, revision)
    write_json(
        output / "TASK_INDEX.json",
        {
            "schema_version": f"{revision}-benchmarkv4-task-index-v1",
            "tasks": task_rows,
        },
    )
    counts = {form: sum(item["form"] == form for item in task_rows) for form in ("dut", "testbench", "bugfix")}
    rerun_required = bool(certification_reuse["simulation_rerun_required_for_materialization"])
    manifest = {
        "schema_version": f"{revision}-benchmarkv4-release-manifest-v1",
        "release_revision": revision,
        "release_status": (
            "materialized_certification_refresh_required"
            if rerun_required
            else f"{revision}_materialized_rust_evas2_audit_pending"
        ),
        "family_count": 400,
        "task_count": len(task_rows),
        "task_counts": counts,
        "source_release_label": source.name,
        "source_score_denominator_registry_sha256": source_registry_sha,
        "source_active_mutation_count": denominator_metadata.get("active_mutation_count"),
        "active_mutations_per_family": denominator_metadata.get("active_mutations_per_family"),
        "certification_evaluator": "rust_evas2",
        "simulation_rerun_count_for_materialization": 0,
        "simulation_rerun_required_for_materialization": rerun_required,
        "certification_reuse": certification_reuse,
        "prompt_record_count": len(task_rows) * len(MODES),
        "release_surface": "benchmarkv4_package",
        "public_surface": {
            "tasks": "tasks",
            "prompt_modes": "prompt_modes",
            "task_index": "TASK_INDEX.json",
            **({"skills": "skills"} if revision in REAL_SKILL_REVISIONS else {}),
        },
        "package_layout": {
            "task_public_inputs": "tasks/<task>/public",
            "task_evaluator_assets": "tasks/<task>/evaluator",
            "task_contract": "tasks/<task>/public_contract.json",
            "task_form": "tasks/<task>/task_record.json:form",
        },
        "tasks_index": "TASK_INDEX.json",
        "materialized_artifact_sha256": materialized_artifact_hashes(
            output, materialized_artifacts_for_revision(revision)
        ),
    }
    write_json(output / "MANIFEST.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
