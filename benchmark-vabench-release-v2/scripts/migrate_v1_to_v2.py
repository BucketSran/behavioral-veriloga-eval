#!/usr/bin/env python3
"""Migrate selected vaBench release-v1 task forms into the release-v2 layout.

The migration is intentionally conservative:

- v1 remains the provenance source.
- v2 generated prompts are thin wrappers plus an agent-visible functional spec.
- checker IDs, checker functions, thresholds, and gold answers stay private.
- generated forms default to final_v2_score_enabled=false until fresh v2
  EVAS/Spectre certification is available.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REPRESENTATIVE_TASKS = [
    "CT01_data_converter_models/vbr1_l1_binary_weighted_voltage_dac:dut",
    "CT01_data_converter_models/vbr1_l2_flash_adc_mini_array:e2e",
    "CT02_comparator_and_decision_circuits/vbr1_l1_threshold_comparator:dut",
    "CT02_comparator_and_decision_circuits/vbr1_l2_comparator_measurement_flow:e2e",
    "CT03_sampling_and_analog_memory/vbr1_l1_acquisition_limited_sample_and_hold:bugfix",
    "CT04_baseband_signal_conditioning/vbr1_l1_slew_rate_limiter:dut",
    "CT04_baseband_signal_conditioning/vbr1_l2_amplifier_filter_chain:e2e",
    "CT05_pll_clock_and_timing_systems/vbr1_l1_vco_phase_integrator:dut",
    "CT05_pll_clock_and_timing_systems/vbr1_l1_bang_bang_phase_detector:tb",
    "CT06_calibration_dem_and_control/vbr1_l1_gain_trim_controller:dut",
    "CT06_calibration_dem_and_control/vbr1_l2_complete_calibration_loop:e2e",
    "CT07_bias_reference_power_management/vbr1_l1_ptat_ctat_reference_generator:dut",
    "CT07_bias_reference_power_management/vbr1_l2_ldo_load_step_recovery_flow:e2e",
    "CT08_rf_afe_behavioral_macromodels/vbr1_l1_rf_mixer_downconverter_macro:dut",
    "CT08_rf_afe_behavioral_macromodels/vbr1_l2_agc_receiver_leveling_loop:e2e",
    "SUP01_measurement_instrumentation_flows/vbr1_l1_peak_detector:dut",
    "SUP02_stimulus_and_source_generators/vbr1_l1_lfsr_prbs_generator:bugfix",
    "SUP02_stimulus_and_source_generators/vbr1_l2_programmable_stimulus_sequencer:e2e",
]


FORM_LABELS = {
    "dut": "DUT-generation",
    "tb": "testbench-generation",
    "bugfix": "bugfix",
    "e2e": "end-to-end",
}


@dataclass(frozen=True)
class SourceForm:
    selector: str
    category_dir: str
    entry_id: str
    form: str
    source_dir: Path


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_simulate_evas(repo_root: Path):
    runners_dir = repo_root / "runners"
    sys.path.insert(0, str(runners_dir))
    script_path = runners_dir / "simulate_evas.py"
    spec = importlib.util.spec_from_file_location("simulate_evas", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_selector(selector: str, v1_tasks_root: Path) -> SourceForm:
    if ":" not in selector:
        raise ValueError(f"selector must look like CATEGORY/ENTRY:FORM: {selector}")
    path_part, form = selector.rsplit(":", 1)
    category_dir, entry_id = path_part.split("/", 1)
    source_dir = v1_tasks_root / category_dir / entry_id / "forms" / form
    return SourceForm(
        selector=selector,
        category_dir=category_dir,
        entry_id=entry_id,
        form=form,
        source_dir=source_dir,
    )


def extract_yaml_list_after_key(text: str, key: str) -> list[str]:
    lines = text.splitlines()
    for line_index, line in enumerate(lines):
        if line.strip() != f"{key}:":
            continue
        base_indent = len(line) - len(line.lstrip())
        items: list[str] = []
        for raw in lines[line_index + 1 :]:
            stripped = raw.strip()
            if not stripped:
                continue
            indent = len(raw) - len(raw.lstrip())
            if indent <= base_indent and not stripped.startswith("- "):
                break
            if stripped.startswith("- "):
                items.append(stripped[2:].strip().strip('"').strip("'"))
        return items
    return []


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def normalize_task_id(value: str) -> str:
    return value.replace(":", "_")


def slug_words(value: str) -> list[str]:
    return [word for word in re.split(r"[^A-Za-z0-9]+", value.lower()) if word]


def backticked_values(text: str) -> list[str]:
    return re.findall(r"`([^`]+)`", text)


def prompt_artifact_list(text: str, label: str) -> list[str]:
    for line in text.splitlines():
        if label in line:
            return [
                value
                for value in backticked_values(line)
                if value.endswith((".va", ".scs", ".sp", ".cir"))
            ]
    return []


def sectionize_markdown(text: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_title = ""
    current_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_title or current_lines:
                sections.append((current_title, current_lines))
            current_title = line[3:].strip()
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_title or current_lines:
        sections.append((current_title, current_lines))
    return sections


def clean_public_section(
    lines: list[str],
    forbidden_terms: list[str],
) -> list[str]:
    cleaned: list[str] = []
    for line in lines:
        if line.startswith("# Task:"):
            continue
        if "Hidden evaluator boundary:" in line:
            continue
        if "Visible context:" in line:
            continue
        if any(term and term in line for term in forbidden_terms):
            continue
        line = line.replace("public behavior checks above", "public functional contract")
        line = line.replace("Public Behavior Checks", "Functional Contract")
        cleaned.append(line.rstrip())
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()
    return cleaned


def slim_v1_prompt(
    text: str,
    *,
    task_id: str,
    form: str,
    release_task: dict[str, Any],
    support_files: list[str],
    target_files: list[str],
    public_observables: list[str],
    forbidden_terms: list[str],
) -> str:
    kept_sections: list[str] = []
    drop_titles = {
        "Release Task Contract",
        "Public Behavior Checks",
    }
    for title, lines in sectionize_markdown(text):
        if not title:
            continue
        if title in drop_titles:
            continue
        cleaned = clean_public_section(lines, forbidden_terms)
        if cleaned:
            kept_sections.append("\n".join(cleaned))

    label = FORM_LABELS.get(form, form)
    support_block = "\n".join(f"- `{name}`" for name in support_files) or "- None"
    target_block = "\n".join(f"- `{name}`" for name in target_files)
    observable_block = "\n".join(f"- `{name}`" for name in public_observables) or "- Inherited from the public harness"
    base_function = release_task.get("base_function", release_task.get("release_entry_id", task_id))
    category = release_task.get("category", "")
    level = release_task.get("level", "")

    prelude = f"""# Agent-Visible Spec: {task_id}

One-shot {label} task for `{base_function}`.

## Agent-Visible Input

{support_block}

## Required Output

{target_block}

## Public Task Summary

- Level: `{level}`
- Category: {category}
- Domain: `{release_task.get("domain", "voltage")}`
- Form: `{form}`

## Public Observables

Saved signal names are part of the public contract: use actual top-level Spectre
nets connected to the DUT; do not rely on instance-qualified aliases.

{observable_block}

If `time` is present, it is the implicit transient waveform axis.
"""

    body = "\n\n".join(kept_sections)
    modeling = """## Modeling Constraints

Keep the implementation in the public voltage-domain behavioral Verilog-A task
scope. Do not emit hidden checker logic, private thresholds, private sample
windows, gold answers, current-domain device models, transistor-level circuits,
or AC/noise analysis assumptions unless they are explicitly part of the public
task contract.
"""
    pieces = [prelude.strip()]
    if body.strip():
        pieces.append(body.strip())
    pieces.append(modeling.strip())
    return "\n\n".join(pieces) + "\n"


def target_and_support_files(
    source_dir: Path,
    release_task: dict[str, Any],
    meta: dict[str, Any],
    prompt_text: str,
) -> tuple[list[Path], list[Path]]:
    gold_paths = []
    for raw in release_task.get("artifacts", {}).get("gold", []):
        path = Path(raw)
        gold_paths.append(path if path.is_absolute() else source_dir.parents[5] / path)
    if not gold_paths:
        gold_paths = sorted((source_dir / "gold").glob("*"))

    target_names = set(prompt_artifact_list(prompt_text, "Target artifact(s):"))
    if not target_names:
        form = source_dir.name
        gold_names = {path.name for path in gold_paths}
        if form == "e2e":
            target_names = set(gold_names)
        elif form == "tb":
            target_names = {name for name in gold_names if name.endswith((".scs", ".sp", ".cir"))}
        elif form == "bugfix":
            fixed = {name for name in gold_names if "fixed" in name}
            target_names = fixed or {"dut_fixed.va"} & gold_names
        elif form == "dut":
            target_names = {name for name in gold_names if name.endswith(".va") and not name.startswith("tb_")}
        else:
            target_names = set(meta.get("artifacts", []))

    targets: list[Path] = []
    support: list[Path] = []
    for path in gold_paths:
        if path.name in target_names:
            targets.append(path)
        else:
            support.append(path)
    missing_targets = sorted(name for name in target_names if name not in {path.name for path in targets})
    if missing_targets:
        raise FileNotFoundError(f"missing target gold artifact(s) in {source_dir}: {missing_targets}")
    return sorted(targets), sorted(support)


def copy_files(paths: list[Path], dst_dir: Path) -> list[str]:
    dst_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for path in paths:
        dst = dst_dir / path.name
        shutil.copy2(path, dst)
        copied.append(path.name)
    return copied


def build_agent_prompt(task_id: str, form: str, target_files: list[str]) -> str:
    target_text = ", ".join(f"`{name}`" for name in target_files)
    if form == "dut":
        action = f"Implement only {target_text}"
    elif form == "tb":
        action = f"Generate only {target_text}"
    elif form == "bugfix":
        action = f"Repair only {target_text}"
    else:
        action = f"Generate exactly {target_text}"
    return f"# Task: {task_id}\n\n{action}, following `public/agent_visible_spec.md`.\n"


def build_agent_visible_files(
    task_id: str,
    support_files: list[str],
    target_files: list[str],
    hidden_gold: list[str],
    forbidden_terms: list[str],
    public_anchor_terms: list[str],
) -> dict[str, Any]:
    hidden = [
        {
            "path": "task_release_card.json",
            "reason": "private task metadata and provenance",
        },
        {
            "path": "private/invisible_checker_config.yaml",
            "reason": "agent-invisible checker IDs, thresholds, sample windows, and expected outcomes",
        },
        {
            "path": "private/invisible_spec_checker_map.json",
            "reason": "agent-invisible public-spec to private-checker map and leak audit terms",
        },
    ]
    hidden.extend(
        {
            "path": f"private/gold/{name}",
            "reason": "gold answer",
        }
        for name in hidden_gold
    )
    anchors = [
        {
            "id": "target_artifacts",
            "all_of": target_files,
        },
        {
            "id": "public_task_summary",
            "all_of": ["Public Task Summary", "Domain"],
        },
    ]
    if public_anchor_terms:
        anchors.append(
            {
                "id": "public_observables",
                "all_of": public_anchor_terms[:8],
            }
        )
    return {
        "schema_version": "vabench-release-v2",
        "task_id": task_id,
        "agent_prompt": "agent_prompt.md",
        "agent_visible_spec": "public/agent_visible_spec.md",
        "agent_visible": {
            "prompt": "agent_prompt.md",
            "support_files": [
                {
                    "alias": name,
                    "source_path": f"public/support/{name}",
                    "render": True,
                    "writable_by_agent": False,
                }
                for name in support_files
            ],
            "target_files": target_files,
            "spec": "public/agent_visible_spec.md",
        },
        "agent_hidden": hidden,
        "render_policy": {
            "render_agent_visible_contract_only": True,
            "render_agent_prompt_only": False,
            "render_support_files_only_if_listed": True,
            "support_files_must_live_under_public_support": True,
            "never_render_checker_files": True,
            "never_render_private_directory": True,
            "never_render_gold_fixed_artifacts": True,
            "generic_runner_rules_allowed": True,
            "never_render_task_release_card": True,
        },
        "leak_audit": {
            "forbidden_phrases": sorted(set(forbidden_terms)),
            "allowed_public_concepts": [
                "agent-visible functional behavior and interfaces",
                "public support files listed in agent_visible_files.json",
                "generic voltage-domain Verilog-A and Spectre syntax rules",
            ],
        },
        "contract_audit": {
            "required_public_anchors": anchors,
        },
    }


def build_checker_config(
    *,
    task_id: str,
    checker_task_id: str,
    checker_function: str,
    v1_checks_text: str,
) -> str:
    return (
        'schema_version: "vabench-release-v2-checks"\n'
        f"task_id: {yaml_quote(task_id)}\n"
        "checker:\n"
        f"  task_id: {yaml_quote(checker_task_id)}\n"
        f"  function: {yaml_quote(checker_function)}\n"
        '  source: "runners/simulate_evas.py"\n'
        "# The remaining fields are inherited from release-v1 and remain private\n"
        "# evaluator configuration until human review and fresh v2 dual rerun.\n"
        f"{v1_checks_text.rstrip()}\n"
    )


def build_spec_checker_map(
    *,
    task_id: str,
    source_aliases: list[str],
    checker_function: str,
    behavior_checks: list[str],
    base_function: str,
    target_files: list[str],
) -> dict[str, Any]:
    public_anchor_terms = ["Required Output", "Public Task Summary"]
    for word in slug_words(base_function)[:3]:
        public_anchor_terms.append(word)
    if target_files:
        public_anchor_terms.append(target_files[0])

    links = []
    for check_id in behavior_checks or ["sim_correct"]:
        links.append(
            {
                "id": f"public_contract_supports_{check_id}",
                "public_requirement": (
                    "The agent-visible functional specification and public support "
                    "artifacts define the observable behavior without exposing checker internals."
                ),
                "public_anchor_terms": public_anchor_terms,
                "checker_config_ids": [check_id],
                "checker_functions": [checker_function],
                "private_policy_terms": [
                    check_id,
                    checker_function,
                    "private checker configuration",
                ],
            }
        )

    return {
        "schema_version": "vabench-release-v2-invisible-spec-checker-map",
        "task_id": task_id,
        "source_agent_visible_spec": "public/agent_visible_spec.md",
        "source_invisible_checker_config": "private/invisible_checker_config.yaml",
        "source_checker": {
            "file": "runners/simulate_evas.py",
            "task_aliases": source_aliases,
        },
        "auditor": {
            "forbidden_public_terms": sorted(set([checker_function, *behavior_checks])),
        },
        "requirement_links": links,
    }


def build_task_release_card(
    *,
    task_id: str,
    release_task: dict[str, Any],
    source_selector: str,
    source_dir: Path,
    target_files: list[str],
    support_files: list[str],
    checker_task_id: str,
    checker_function: str,
    behavior_checks: list[str],
) -> dict[str, Any]:
    evidence = release_task.get("certification", {}).get("evidence")
    return {
        **{k: v for k, v in release_task.items() if k not in {"benchmark", "artifacts", "certification", "counts"}},
        "benchmark": "vabench-release-v2",
        "schema_version": "vabench-release-v2",
        "artifacts": {
            "agent_prompt": "agent_prompt.md",
            "agent_visible_spec": "public/agent_visible_spec.md",
            "agent_visible_files": "agent_visible_files.json",
            "public_support": [f"public/support/{name}" for name in support_files],
            "invisible_checker_config": "private/invisible_checker_config.yaml",
            "private_gold": [f"private/gold/{name}" for name in target_files],
            "invisible_spec_checker_map": "private/invisible_spec_checker_map.json",
        },
        "migration": {
            "source_benchmark": "vabench-release-v1",
            "source_selector": source_selector,
            "source_task": str(source_dir / "release_task.json"),
            "source_v1_evidence": evidence,
            "runtime_depends_on_v1": False,
            "status": "auto_migrated_needs_human_prompt_review",
            "notes": [
                "Generated by benchmark-vabench-release-v2/scripts/migrate_v1_to_v2.py.",
                "Public prompt was slimmed from v1 to remove checker IDs and private evaluator language.",
                "Fresh v2 EVAS/Spectre dual certification is still required before scoring.",
            ],
        },
        "certification": {
            "prompt_boundary": "pending_audit",
            "static": "inherited_from_v1_pending_fresh_v2_rerun",
            "evas": "inherited_from_v1_pending_fresh_v2_rerun",
            "spectre": "inherited_from_v1_pending_fresh_v2_rerun",
            "fresh_v2_evidence": "pending",
        },
        "counts": {
            "benchmark_score_candidate": bool(release_task.get("counts", {}).get("benchmark_score")),
            "final_v2_score_enabled": False,
            "requires_fresh_v2_dual_certification": True,
        },
        "visibility": "internal_only",
        "source_v1_task_id": release_task.get("id"),
        "agent_visible": {
            "source_of_truth": "agent_visible_files.json",
        },
        "private_evaluator_assets": {
            "gold": [f"private/gold/{name}" for name in target_files],
            "checker_config": "private/invisible_checker_config.yaml",
            "spec_checker_map": "private/invisible_spec_checker_map.json",
        },
        "provenance": {
            "source_v1_release_task": str(source_dir / "release_task.json"),
            "source_v1_dual_evidence": evidence,
            "runtime_required": False,
        },
        "private_diagnostics": {
            "checker_task_id": checker_task_id,
            "checker_function": checker_function,
            "private_sample_policy": "Inherited from the executable runner checker and private checker config.",
            "gold_expectation": "Private gold artifacts are stored under private/gold and must not be rendered to agents.",
        },
        "private_checker_contract": {
            "policy": "behavior_first",
            "checker_ids": behavior_checks,
            "public_behavior_envelope": "Defined by public/agent_visible_spec.md and public support artifacts.",
            "implementation_constraints": "Do not require private variable names or a fixed implementation template unless explicitly configured.",
            "source_of_truth": "private/invisible_checker_config.yaml",
            "spec_checker_map": "private/invisible_spec_checker_map.json",
        },
        "directive": "This release task card is private benchmark/evaluator metadata. Do not render it into agent prompts.",
    }


def migrate_one(
    source: SourceForm,
    *,
    repo_root: Path,
    v2_tasks_root: Path,
    simulate_evas,
    overwrite: bool,
    dry_run: bool,
) -> dict[str, Any]:
    source_dir = source.source_dir
    if not source_dir.exists():
        raise FileNotFoundError(f"missing source form: {source_dir}")
    release_task = load_json(source_dir / "release_task.json")
    meta = load_json(source_dir / "meta.json")
    v1_prompt = (source_dir / "prompt.md").read_text(encoding="utf-8")
    v1_checks_text = (source_dir / "checks.yaml").read_text(encoding="utf-8")
    behavior_checks = meta.get("behavior_checks") or extract_yaml_list_after_key(v1_checks_text, "checks")
    public_observables = extract_yaml_list_after_key(v1_checks_text, "public_observables")

    task_id = str(release_task.get("id") or f"{source.entry_id}:{source.form}")
    checker_task_id = simulate_evas.resolve_checker_task_id(meta, task_id, form=source.form)
    checker = simulate_evas.CHECKS.get(checker_task_id)
    if checker is None:
        raise RuntimeError(f"no runner checker for {source.selector}: {checker_task_id}")
    checker_function = checker.__name__

    target_paths, support_paths = target_and_support_files(source_dir, release_task, meta, v1_prompt)
    target_files = [path.name for path in target_paths]
    support_files = [path.name for path in support_paths]
    target_dir = v2_tasks_root / source.category_dir / source.entry_id / "forms" / source.form
    if target_dir.exists() and not overwrite:
        return {
            "selector": source.selector,
            "task_id": task_id,
            "status": "SKIP_EXISTS",
            "target_dir": str(target_dir),
        }

    source_aliases = sorted(
        {
            checker_task_id,
            normalize_task_id(task_id),
            task_id,
            source.entry_id,
            f"{source.entry_id}_{source.form}",
            f"{source.entry_id}:{source.form}",
            str(meta.get("id", "")),
            str(meta.get("task_id", "")),
        }
        - {""}
    )
    forbidden_terms = sorted(set([checker_function, checker_task_id, *behavior_checks]))
    public_anchor_terms = [term for term in public_observables if term != "time"]

    if dry_run:
        return {
            "selector": source.selector,
            "task_id": task_id,
            "status": "DRY_RUN",
            "target_dir": str(target_dir),
            "checker_task_id": checker_task_id,
            "checker_function": checker_function,
            "target_files": target_files,
            "support_files": support_files,
        }

    if target_dir.exists():
        shutil.rmtree(target_dir)
    (target_dir / "public" / "support").mkdir(parents=True, exist_ok=True)
    (target_dir / "private" / "gold").mkdir(parents=True, exist_ok=True)

    copied_gold = copy_files(target_paths, target_dir / "private" / "gold")
    copied_support = copy_files(support_paths, target_dir / "public" / "support")

    (target_dir / "agent_prompt.md").write_text(
        build_agent_prompt(task_id, source.form, target_files),
        encoding="utf-8",
    )
    (target_dir / "public" / "agent_visible_spec.md").write_text(
        slim_v1_prompt(
            v1_prompt,
            task_id=task_id,
            form=source.form,
            release_task=release_task,
            support_files=copied_support,
            target_files=copied_gold,
            public_observables=public_observables,
            forbidden_terms=forbidden_terms,
        ),
        encoding="utf-8",
    )
    write_json(
        target_dir / "agent_visible_files.json",
        build_agent_visible_files(
            task_id,
            copied_support,
            copied_gold,
            copied_gold,
            forbidden_terms,
            public_anchor_terms,
        ),
    )
    (target_dir / "private" / "invisible_checker_config.yaml").write_text(
        build_checker_config(
            task_id=task_id,
            checker_task_id=checker_task_id,
            checker_function=checker_function,
            v1_checks_text=v1_checks_text,
        ),
        encoding="utf-8",
    )
    write_json(
        target_dir / "private" / "invisible_spec_checker_map.json",
        build_spec_checker_map(
            task_id=task_id,
            source_aliases=source_aliases,
            checker_function=checker_function,
            behavior_checks=behavior_checks,
            base_function=str(release_task.get("base_function", source.entry_id)),
            target_files=copied_gold,
        ),
    )
    write_json(
        target_dir / "task_release_card.json",
        build_task_release_card(
            task_id=task_id,
            release_task=release_task,
            source_selector=source.selector,
            source_dir=source_dir,
            target_files=copied_gold,
            support_files=copied_support,
            checker_task_id=checker_task_id,
            checker_function=checker_function,
            behavior_checks=behavior_checks,
        ),
    )

    return {
        "selector": source.selector,
        "task_id": task_id,
        "status": "MIGRATED",
        "target_dir": str(target_dir),
        "checker_task_id": checker_task_id,
        "checker_function": checker_function,
        "target_files": copied_gold,
        "support_files": copied_support,
        "source_evidence": release_task.get("certification", {}).get("evidence"),
    }


def task_selectors_from_args(args: argparse.Namespace) -> list[str]:
    selectors: list[str] = []
    if args.representative_batch:
        selectors.extend(DEFAULT_REPRESENTATIVE_TASKS)
    selectors.extend(args.task or [])
    if args.tasks_file:
        selectors.extend(
            line.strip()
            for line in args.tasks_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
    if args.limit is not None:
        selectors = selectors[: args.limit]
    seen: set[str] = set()
    unique: list[str] = []
    for selector in selectors:
        if selector in seen:
            continue
        seen.add(selector)
        unique.append(selector)
    return unique


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_script())
    parser.add_argument("--v1-root", type=Path, default=None)
    parser.add_argument("--v2-root", type=Path, default=None)
    parser.add_argument("--task", action="append", help="Task selector CATEGORY/ENTRY:FORM")
    parser.add_argument("--tasks-file", type=Path)
    parser.add_argument("--representative-batch", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-id", default=None)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    v1_root = (args.v1_root or repo_root / "benchmark-vabench-release-v1").resolve()
    v2_root = (args.v2_root or repo_root / "benchmark-vabench-release-v2").resolve()
    v1_tasks_root = v1_root / "tasks"
    v2_tasks_root = v2_root / "tasks"
    selectors = task_selectors_from_args(args)
    if not selectors:
        parser.error("no tasks selected; use --representative-batch, --task, or --tasks-file")

    simulate_evas = load_simulate_evas(repo_root)
    results: list[dict[str, Any]] = []
    for selector in selectors:
        source = parse_selector(selector, v1_tasks_root)
        results.append(
            migrate_one(
                source,
                repo_root=repo_root,
                v2_tasks_root=v2_tasks_root,
                simulate_evas=simulate_evas,
                overwrite=args.overwrite,
                dry_run=args.dry_run,
            )
        )

    batch_id = args.batch_id or datetime.now(timezone.utc).strftime("v1-to-v2-batch-%Y%m%dT%H%M%SZ")
    summary = {
        "schema_version": "vabench-release-v2-migration-batch",
        "batch_id": batch_id,
        "source": "benchmark-vabench-release-v1",
        "target": "benchmark-vabench-release-v2",
        "dry_run": args.dry_run,
        "selector_count": len(selectors),
        "status_counts": {
            status: sum(1 for item in results if item["status"] == status)
            for status in sorted({item["status"] for item in results})
        },
        "results": results,
        "claim_boundary": (
            "Auto-migrated forms are structure-ready v2 candidates only; they "
            "require human prompt review and fresh v2 EVAS/Spectre certification "
            "before final scoring."
        ),
    }
    if not args.dry_run:
        provenance_dir = v2_root / "provenance"
        provenance_dir.mkdir(parents=True, exist_ok=True)
        write_json(provenance_dir / f"{batch_id}.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
