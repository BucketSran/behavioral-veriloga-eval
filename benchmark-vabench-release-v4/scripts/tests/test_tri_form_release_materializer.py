from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest


PREP = Path(__file__).resolve().parents[2] / "operations" / "tri_form_derivation_prep"
if str(PREP) not in sys.path:
    sys.path.insert(0, str(PREP))
CALIBRATION = Path(__file__).resolve().parents[2] / "operations" / "calibration_pilot"
if str(CALIBRATION) not in sys.path:
    sys.path.insert(0, str(CALIBRATION))
PROVENANCE = (
    Path(__file__).resolve().parents[2]
    / "provenance"
    / "dut-base-v3-exact-five-hash-bound-v2"
)

from materialize_tri_form_release import (  # noqa: E402
    COMPONENT_METADATA,
    DEFAULT_OUTPUTS,
    MODES,
    REFERENCE_TOKENIZER,
    build_bugfix_view,
    build_dut_view,
    build_testbench_view,
    canonical_required_behavior,
    install_skill_snapshots,
    install_prompt_assets,
    iter_public_inputs,
    public_contract_relative_path,
    reference_token_count,
    resolve_testbench_reference,
    render_binding,
    render_bugfix_instruction,
    render_testbench_instruction,
    select_bugfix_seed,
    write_public_contract,
    main as materialize_release,
)
from export_tri_form_runtime import (  # noqa: E402
    build_mode_record,
    install_public,
    main as export_runtime,
    ordered_prompt_components,
    render_prompt,
    task_record as load_task_record,
)
from run_campaign import (  # noqa: E402
    active_tool_schemas,
    list_available_skills,
    read_skill_file,
    skill_tree_sha,
)
from audit_runtime_export import (  # noqa: E402
    ALLOWED_DUT_RUNTIME_SCHEMAS,
    ALLOWED_TESTBENCH_RUNTIME_SCHEMAS,
    main as audit_runtime_export,
    public_text_leaks_authoring_surface,
)
from record_runtime_ingestion_evidence import verified_audit  # noqa: E402
from rebuild_tri_form_release import (  # noqa: E402
    DEFAULT_RELEASES as REBUILD_DEFAULT_RELEASES,
    main as rebuild_release,
)
from audit_tri_form_release import (  # noqa: E402
    RELEASE_SEAL_ARTIFACTS,
    allowed_runtime_schemas,
    audit_release_evidence,
    audit_testbench_reference,
    build_release_seal,
    evidence_artifacts,
    expected_buggy_artifact_hashes,
    file_sha,
    prompt_component_path,
    release_uses_real_skills,
    rust_evas2_runtime,
    valid_git_oid,
)


def test_r51_release_plumbing_preserves_real_skill_and_runtime_contracts() -> None:
    assert DEFAULT_OUTPUTS["r51"].name == "benchmarkv4-r51"
    assert REBUILD_DEFAULT_RELEASES["r51"].name == "benchmarkv4-r51"
    assert release_uses_real_skills("r51") is True
    assert allowed_runtime_schemas("r51", "dut") == {
        "r51-direct-evas-runtime-v2",
        "r51-direct-evas-runtime-v3",
    }
    assert allowed_runtime_schemas("r51", "testbench") == {
        "r51-direct-evas-testbench-suite-v2",
        "r51-direct-evas-testbench-suite-v3",
    }
    assert ALLOWED_DUT_RUNTIME_SCHEMAS["r51"] == {
        "r51-direct-evas-runtime-v2",
        "r51-direct-evas-runtime-v3",
    }
    assert ALLOWED_TESTBENCH_RUNTIME_SCHEMAS["r51"] == {
        "r51-direct-evas-testbench-suite-v2",
        "r51-direct-evas-testbench-suite-v3",
    }


def test_r51_evas_runtime_provenance_requires_a_clean_git_revision() -> None:
    runtime = {
        "evas_engine": "evas2",
        "evas_engine_used": "evas2",
        "evas_version": "0.8.3",
        "evas_backend": "evas-rust",
    }
    assert rust_evas2_runtime(runtime)
    assert not rust_evas2_runtime(runtime, require_source_revision=True)

    runtime.update(
        {
            "evas_source_repository": "https://github.com/Arcadia-1/EVAS.git",
            "evas_source_revision": "a" * 40,
            "evas_source_tree": "clean",
        }
    )
    assert rust_evas2_runtime(runtime, require_source_revision=True)


def write_runtime_skill_manifest(runtime: Path, skill_id: str = "veriloga") -> None:
    skill = runtime / "public" / "skills" / skill_id
    files = [
        {
            "path": item.relative_to(skill).as_posix(),
            "sha256": file_sha(item),
            "bytes": item.stat().st_size,
        }
        for item in sorted(skill.rglob("*"))
        if item.is_file() and not item.is_symlink()
    ]
    (runtime / "public" / "skills" / "SNAPSHOT_MANIFEST.json").write_text(
        json.dumps({
            "schema_version": "v4-runtime-skill-manifest-v1",
            "skills": {
                skill_id: {
                    "skill_file": f"public/skills/{skill_id}/SKILL.md",
                    "tree_sha256": skill_tree_sha(skill),
                    "files": files,
                }
            },
        }) + "\n",
        encoding="utf-8",
    )


def test_git_oid_validation_accepts_sha1_and_sha256() -> None:
    assert valid_git_oid("a" * 40)
    assert valid_git_oid("b" * 64)
    assert not valid_git_oid("c" * 39)
    assert not valid_git_oid("not-a-git-oid")


def test_runtime_schema_compatibility_preserves_frozen_r45_and_requires_r47_v2() -> None:
    assert allowed_runtime_schemas("r45", "dut") == {
        "r45-direct-evas-runtime-v1",
        "r45-direct-evas-runtime-v2",
    }
    assert allowed_runtime_schemas("r45", "testbench") == {
        "r45-direct-evas-testbench-suite-v1",
        "r45-direct-evas-testbench-suite-v2",
    }
    assert allowed_runtime_schemas("r47", "dut") == {
        "r47-direct-evas-runtime-v2",
    }
    assert allowed_runtime_schemas("r47", "testbench") == {
        "r47-direct-evas-testbench-suite-v2",
    }
    assert allowed_runtime_schemas("r48", "dut") == {
        "r48-direct-evas-runtime-v2",
    }
    assert allowed_runtime_schemas("r48", "testbench") == {
        "r48-direct-evas-testbench-suite-v2",
    }
    assert allowed_runtime_schemas("r49", "dut") == {
        "r49-direct-evas-runtime-v2",
    }
    assert allowed_runtime_schemas("r49", "testbench") == {
        "r49-direct-evas-testbench-suite-v2",
    }


def sample_spec() -> dict:
    return {
        "family_id": "001",
        "identity": {"title": "Sample Hold", "category": "sampling", "level": "L1", "difficulty": "D2"},
        "artifact_contract": {"mode": "single_file", "files": [{"path": "dut.va", "modules": [{
            "name": "dut", "role": "entry", "depends_on": [],
            "ports": [{"name": "vin", "direction": "input", "discipline": "electrical", "position": 0}],
            "parameters": [],
        }]}]},
        "testbench_binding": {"source_path_template": "./dut/{artifact_path}", "instances": [{
            "name": "XDUT", "module_ref": "dut", "connections": [{"port_ref": "vin", "net": "vin", "position": 0}],
        }]},
        "properties": [{"id": "P_HOLD", "observable_contract": "hold the sampled value", "required_signals": ["time", "vin"]}],
        "trace_contract": {"required_signals": ["time", "vin"]},
        "modeling_constraints": ["Remain deterministic."],
    }


def sample_source_task(tmp_path: Path, *, independent_reference: bool) -> tuple[Path, dict, dict]:
    source_task = tmp_path / "source" / "001-sample"
    evaluator = source_task / "evaluator"
    (evaluator / "profiles").mkdir(parents=True)
    (evaluator / "solution").mkdir()
    (evaluator / "mutation_bundles").mkdir()
    instruction = source_task / "public" / "task" / "instruction.md"
    instruction.parent.mkdir(parents=True)
    instruction.write_text(
        "# Sample Hold\n\n## Required Behavior\n\n"
        "Capture `vin` on each rising sample edge and hold it until the next edge.\n\n"
        "## Modeling Constraints\n\nRemain deterministic.\n",
        encoding="utf-8",
    )
    spec = sample_spec()
    (evaluator / "family_spec.json").write_text(json.dumps(spec) + "\n", encoding="utf-8")
    (evaluator / "checker_profile.json").write_text(
        '{"checker_task_id":"v4_001_sample"}\n', encoding="utf-8"
    )
    harness = {
        "schema_version": "v4-harness-spec-v1",
        "family_id": "001",
        "task_id": "v4-001",
        "generator": {"name": "render_v4_harness.py", "version": "test"},
        "candidate": {"source_root": "./dut", "artifact_paths": ["dut.va"]},
        "deck": {
            "header": ["simulator lang=spectre", "global 0"],
            "include_templates": ["ahdl_include \"{candidate_source_root}/{artifact_path}\""],
            "body_lines": ["Vstim (vin 0) vsource dc=0.45", "XDUT (vin) dut"],
            "analyses": ["tran tran stop=10n maxstep=100p"],
            "save_signals": ["vin"],
        },
        "property_ids": ["P_HOLD"],
        "profile_defaults": {
            "feedback": {
                "parameters": {}, "corners": ["nominal"], "deterministic_seed": 7,
                "simulatorOptions": {"evas_profile": "balanced", "strict": True},
                "deck_overrides": {},
            },
            "score": {
                "parameters": {}, "corners": ["nominal"], "deterministic_seed": 7,
                "simulatorOptions": {"strict": True}, "deck_overrides": {},
            },
        },
    }
    (evaluator / "harness_spec.json").write_text(json.dumps(harness) + "\n", encoding="utf-8")
    (evaluator / "solution" / "dut.va").write_text("module dut; endmodule\n", encoding="utf-8")
    (evaluator / "score_tb.scs").write_text(
        'ahdl_include "./dut/dut.va"\n', encoding="utf-8"
    )
    if independent_reference:
        (evaluator / "reference_tb.scs").write_text("independent reference deck\n", encoding="utf-8")
    mutation_ids = [f"neg_{index}" for index in range(1, 6)]
    for mutation_id in mutation_ids:
        mutation = evaluator / "mutation_bundles" / mutation_id
        mutation.mkdir()
        (mutation / "dut.va").write_text(
            f"module dut; // {mutation_id}\nendmodule\n", encoding="utf-8"
        )
    (evaluator / "mutation_catalog.json").write_text(
        json.dumps({"mutations": [{"id": mutation_id} for mutation_id in mutation_ids]}) + "\n",
        encoding="utf-8",
    )
    row = {
        "canonical_dut_id": "001",
        "active_mutations": [{"mutation_id": mutation_id} for mutation_id in mutation_ids],
        "hashes": {
            "mutation_catalog_sha256": file_sha(evaluator / "mutation_catalog.json"),
            "task_certification_sha256": "b" * 64,
        },
    }
    seed_review = {"mutation_id": mutation_ids[0]}
    return source_task, row, seed_review


def add_public_evas_runtime(task: Path) -> None:
    (task / "public" / "visible_test.scs").write_text(
        'ahdl_include "../submission/dut.va"\n', encoding="utf-8"
    )
    (task / "public" / "evas_runtime.json").write_text(
        '{"command":"evas simulate public/task/visible_test.scs"}\n', encoding="utf-8"
    )


def test_reference_tb_prefers_explicit_independent_asset(tmp_path: Path) -> None:
    source_task, _, _ = sample_source_task(tmp_path, independent_reference=True)
    path, source_kind = resolve_testbench_reference(source_task)
    assert path == source_task / "evaluator" / "reference_tb.scs"
    assert source_kind == "independent_reference_tb"


@pytest.mark.parametrize("release_revision", ["r45", "r47"])
def test_dut_builder_binds_selected_revision_to_identical_runtime_decks(
    tmp_path: Path, release_revision: str,
) -> None:
    source_task, row, _ = sample_source_task(tmp_path, independent_reference=True)
    output = tmp_path / "release"
    record = build_dut_view(
        output,
        source_task,
        row,
        sample_spec(),
        file_sha(source_task / "evaluator" / "family_spec.json"),
        release_revision=release_revision,
    )
    task = output / record["task_dir"]
    task_record = json.loads((task / "task_record.json").read_text(encoding="utf-8"))
    profile = json.loads(
        (task / "evaluator" / "canonical_test_profile.json").read_text(encoding="utf-8")
    )
    visible = task / "public" / "visible_test.scs"
    trusted = task / "evaluator" / "trusted_replay_test.scs"

    assert visible.read_bytes() == trusted.read_bytes()
    assert profile["test_deck_sha256"] == file_sha(visible)
    assert task_record["release_revision"] == release_revision
    assert task_record["schema_version"].startswith(f"{release_revision}-")
    runtime = json.loads((task / "public" / "evas_runtime.json").read_text(encoding="utf-8"))
    assert runtime["schema_version"].startswith(f"{release_revision}-")
    assert task_record["evaluation_binding"]["profile_sha256"] == file_sha(
        task / "evaluator" / "canonical_test_profile.json"
    )


@pytest.mark.parametrize(
    ("form", "task_dir_name"),
    [
        ("dut", "001-sample"),
        ("testbench", "501-sample-testbench"),
        ("bugfix", "1001-sample-bugfix"),
    ],
)
def test_r51_rdist_solution_uses_portable_v3_runtime_for_every_form(
    tmp_path: Path,
    form: str,
    task_dir_name: str,
) -> None:
    source_task, row, seed_review = sample_source_task(
        tmp_path, independent_reference=True
    )
    (source_task / "evaluator" / "solution" / "dut.va").write_text(
        "module dut; analog V(vin) <+ $rdist_normal(7, 0, 1); endmodule\n",
        encoding="utf-8",
    )
    seed_review.update({
        "selection_status": "policy_reviewed",
        "triviality_markers": [],
    })
    output = tmp_path / "release"
    args = (
        output,
        source_task,
        row,
        sample_spec(),
        "a" * 64,
    )
    if form == "dut":
        build_dut_view(*args, release_revision="r51")
    elif form == "testbench":
        build_testbench_view(
            *args, seed_review, release_revision="r51"
        )
    else:
        build_bugfix_view(
            *args, seed_review, release_revision="r51"
        )

    task = output / "tasks" / task_dir_name
    runtime = json.loads(
        (task / "public" / "evas_runtime.json").read_text(encoding="utf-8")
    )
    contract = json.loads(
        (task / "public_contract.json").read_text(encoding="utf-8")
    )
    command = runtime.get("command") or runtime["candidate_command_template"]

    assert runtime["schema_version"].endswith("-v3")
    assert runtime["compatibility_mode"] == "portable"
    assert "--spectre-strict" not in command
    assert contract["evas"]["compatibility_mode"] == "portable"
    if form != "testbench":
        assert contract["evas"]["command"] == command


@pytest.mark.parametrize(
    ("form", "task_dir_name"),
    [
        ("dut", "001-sample"),
        ("testbench", "501-sample-testbench"),
        ("bugfix", "1001-sample-bugfix"),
    ],
)
def test_r51_non_rdist_solution_retains_strict_v2_runtime(
    tmp_path: Path,
    form: str,
    task_dir_name: str,
) -> None:
    source_task, row, seed_review = sample_source_task(
        tmp_path, independent_reference=True
    )
    seed_review.update({
        "selection_status": "policy_reviewed",
        "triviality_markers": [],
    })
    output = tmp_path / "release"
    args = (
        output,
        source_task,
        row,
        sample_spec(),
        "a" * 64,
    )
    if form == "dut":
        build_dut_view(*args, release_revision="r51")
    elif form == "testbench":
        build_testbench_view(
            *args, seed_review, release_revision="r51"
        )
    else:
        build_bugfix_view(
            *args, seed_review, release_revision="r51"
        )

    task = output / "tasks" / task_dir_name
    runtime = json.loads(
        (task / "public" / "evas_runtime.json").read_text(encoding="utf-8")
    )
    contract = json.loads(
        (task / "public_contract.json").read_text(encoding="utf-8")
    )
    command = runtime.get("command") or runtime["candidate_command_template"]

    assert runtime["schema_version"].endswith("-v2")
    assert "compatibility_mode" not in runtime
    assert "--spectre-strict" in command
    assert "compatibility_mode" not in contract["evas"]
    if form != "testbench":
        assert contract["evas"]["command"] == command


def test_r51_runtime_policy_is_derived_from_solution_not_prompt_text(
    tmp_path: Path,
) -> None:
    source_task, row, _ = sample_source_task(
        tmp_path, independent_reference=True
    )
    instruction = source_task / "public" / "task" / "instruction.md"
    instruction.write_text(
        instruction.read_text(encoding="utf-8")
        + "\nMention `$rdist_normal` only as explanatory prompt text.\n",
        encoding="utf-8",
    )
    output = tmp_path / "release"
    record = build_dut_view(
        output,
        source_task,
        row,
        sample_spec(),
        "a" * 64,
        release_revision="r51",
    )
    runtime = json.loads(
        (
            output
            / record["task_dir"]
            / "public"
            / "evas_runtime.json"
        ).read_text(encoding="utf-8")
    )

    assert runtime["schema_version"] == "r51-direct-evas-runtime-v2"
    assert "--spectre-strict" in runtime["command"]
    assert "compatibility_mode" not in runtime


def test_pre_r51_rdist_solution_retains_sealed_strict_v2_runtime(
    tmp_path: Path,
) -> None:
    source_task, row, _ = sample_source_task(
        tmp_path, independent_reference=True
    )
    (source_task / "evaluator" / "solution" / "dut.va").write_text(
        "module dut; analog V(vin) <+ $rdist_normal(7, 0, 1); endmodule\n",
        encoding="utf-8",
    )
    output = tmp_path / "release"
    record = build_dut_view(
        output,
        source_task,
        row,
        sample_spec(),
        "a" * 64,
        release_revision="r50",
    )
    runtime = json.loads(
        (
            output
            / record["task_dir"]
            / "public"
            / "evas_runtime.json"
        ).read_text(encoding="utf-8")
    )

    assert runtime["schema_version"] == "r50-direct-evas-runtime-v2"
    assert "--spectre-strict" in runtime["command"]
    assert "compatibility_mode" not in runtime


def test_runtime_export_rejects_tampered_canonical_deck(tmp_path: Path) -> None:
    source_task, row, _ = sample_source_task(tmp_path, independent_reference=True)
    release = tmp_path / "release"
    record = build_dut_view(
        release, source_task, row, sample_spec(), file_sha(source_task / "evaluator" / "family_spec.json")
    )
    (release / "TASK_INDEX.json").write_text(
        json.dumps({"tasks": [record]}) + "\n", encoding="utf-8"
    )
    task = release / record["task_dir"]
    (task / "evaluator" / "trusted_replay_test.scs").write_text(
        "tampered\n", encoding="utf-8"
    )

    with pytest.raises(SystemExit, match="decks differ"):
        load_task_record(release, "v4-001")


def test_reference_tb_legacy_fallback_is_explicit(tmp_path: Path) -> None:
    source_task, _, _ = sample_source_task(tmp_path, independent_reference=False)
    path, source_kind = resolve_testbench_reference(source_task)
    assert path == source_task / "evaluator" / "score_tb.scs"
    assert source_kind == "legacy_score_tb_fallback"


def test_testbench_builder_records_reference_hash_and_source_kind(tmp_path: Path) -> None:
    source_task, row, seed_review = sample_source_task(tmp_path, independent_reference=True)
    output = tmp_path / "release"
    build_testbench_view(output, source_task, row, sample_spec(), "a" * 64, seed_review)
    evaluator = output / "tasks" / "501-sample-testbench" / "evaluator"
    score = json.loads((evaluator / "score_policy.json").read_text(encoding="utf-8"))
    assert (evaluator / "reference_tb.scs").read_text(encoding="utf-8") == "independent reference deck\n"
    assert score["reference_tb_sha256"] == file_sha(source_task / "evaluator" / "reference_tb.scs")
    assert score["reference_tb_source_kind"] == "independent_reference_tb"
    task = output / "tasks" / "501-sample-testbench"
    assert not (task / "public" / "visible_test.scs").exists()
    assert not (task / "evaluator" / "trusted_replay_test.scs").exists()
    assert (task / "public" / "evas_runtime.json").read_bytes() == (
        task / "evaluator" / "trusted_replay_suite.json"
    ).read_bytes()
    assert file_sha(task / "public" / "evas_runtime.json") == json.loads(
        (task / "task_record.json").read_text(encoding="utf-8")
    )["evaluation_binding"]["public_suite_sha256"]
    assert sorted(
        path.name for path in (task / "public" / "visible_fixtures").iterdir()
    ) == ["mutation_01", "mutation_02", "mutation_03", "mutation_04", "mutation_05", "reference"]
    suite = json.loads((task / "public" / "evas_runtime.json").read_text(encoding="utf-8"))
    command = suite["candidate_command_template"]
    assert "/tmp/vabench-visible/runs/{case}" in command
    assert "/tmp/vabench-visible/evas-output/{case}" in command
    assert "public/submission/runs" not in command
    assert "public/submission/evas-output" not in command
    contract = json.loads((task / "public_contract.json").read_text(encoding="utf-8"))
    assert "feedback" not in contract
    assert contract["evas"]["visible_and_final_suite"] == "identical_reference_plus_five_mutations"


def test_testbench_builder_mounts_reference_support_below_dut(tmp_path: Path) -> None:
    source_task, row, seed_review = sample_source_task(tmp_path, independent_reference=True)
    support = source_task / "public" / "task" / "public_support"
    support.mkdir(parents=True)
    (support / "helper.va").write_text("module helper; endmodule\n", encoding="utf-8")
    reference = source_task / "evaluator" / "reference_tb.scs"
    reference.write_text('ahdl_include "./support/helper.va"\n', encoding="utf-8")

    output = tmp_path / "release"
    build_testbench_view(output, source_task, row, sample_spec(), "a" * 64, seed_review)
    task = output / "tasks" / "501-sample-testbench"
    materialized = task / "evaluator" / "reference_tb.scs"
    score = json.loads((task / "evaluator" / "score_policy.json").read_text(encoding="utf-8"))

    assert materialized.read_text(encoding="utf-8") == 'ahdl_include "./dut/support/helper.va"\n'
    assert (task / "public" / "supplied_dut" / "support" / "helper.va").is_file()
    assert score["reference_tb_sha256"] == file_sha(materialized)


def test_testbench_builder_marks_legacy_score_deck_fallback(tmp_path: Path) -> None:
    source_task, row, seed_review = sample_source_task(tmp_path, independent_reference=False)
    output = tmp_path / "release"
    build_testbench_view(output, source_task, row, sample_spec(), "a" * 64, seed_review)
    evaluator = output / "tasks" / "501-sample-testbench" / "evaluator"
    score = json.loads((evaluator / "score_policy.json").read_text(encoding="utf-8"))
    assert (evaluator / "reference_tb.scs").read_text(encoding="utf-8") == 'ahdl_include "./dut/dut.va"\n'
    assert score["reference_tb_sha256"] == file_sha(source_task / "evaluator" / "score_tb.scs")
    assert "reference_tb_source_kind" not in score


def test_audit_rejects_false_independent_reference_claim(tmp_path: Path) -> None:
    source_task, _, _ = sample_source_task(tmp_path, independent_reference=False)
    evaluator = tmp_path / "release-evaluator"
    evaluator.mkdir()
    reference = source_task / "evaluator" / "score_tb.scs"
    (evaluator / "reference_tb.scs").write_bytes(reference.read_bytes())
    score = {
        "reference_tb_sha256": file_sha(reference),
        "reference_tb_source_kind": "independent_reference_tb",
    }
    problems: list[str] = []
    source_kind = audit_testbench_reference(evaluator, source_task, score, "v4-501:", problems)
    assert source_kind == "legacy_score_tb_fallback"
    assert any("source kind mismatch" in problem for problem in problems)


def test_mode_matrix_is_two_direct_plus_four_agentic() -> None:
    assert [name for name, row in MODES.items() if row["process"] == "direct_one_shot"] == ["G0", "G1"]
    assert [name for name, row in MODES.items() if row["evas_cli"]] == ["G2", "G3", "G4", "G5"]


def test_bugfix_instruction_does_not_localize_fault() -> None:
    text = render_bugfix_instruction(sample_spec()).lower()
    for forbidden in ("mutation", "faulty file", "root cause", "changed line", "baseline result"):
        assert forbidden not in text


def test_derived_instructions_preserve_canonical_required_behavior(tmp_path: Path) -> None:
    source_task, _, _ = sample_source_task(tmp_path, independent_reference=True)
    behavior = canonical_required_behavior(source_task, "bugfix")

    assert behavior == "Capture `vin` on each rising sample edge and hold it until the next edge."
    assert behavior in render_bugfix_instruction(sample_spec(), canonical_behavior=behavior)
    assert behavior in render_testbench_instruction(sample_spec(), canonical_behavior=behavior)


@pytest.mark.parametrize(
    ("source_slug", "semantic_marker"),
    [
        ("081-adpll-ratio-hop-timer", "models an ADPLL timing loop"),
        ("084-bbpd-data-edge-alignment", "bang-bang phase detector front end"),
        ("088-cppll-tracking-reacquire-timer", "Use `ref_clk` as the reference timing input."),
        ("089-edge-crossing-interval-timer", "measures the interval"),
        ("090-dither-adder", "standalone differential dither injection block"),
        ("092-fixed-gain-amplifier", "standalone fixed-gain differential amplifier"),
        ("098-reference-step-clock", "checks the generated `CLK` waveform"),
        ("101-settling-time-measurement", "Use a 1 ns timer update"),
        ("105-single-shot-pulse", "voltage-domain one-shot pulse generator"),
        ("108-crossing-pulse-detector", "emits a fixed-width pulse"),
        ("302-fractional-n-divider-accumulator-flow", "fractional accumulator"),
    ],
)
def test_testbench_canonical_behavior_removes_dut_authoring_directives(
    source_slug: str,
    semantic_marker: str,
) -> None:
    behavior = canonical_required_behavior(PROVENANCE / source_slug, "testbench")

    assert semantic_marker in behavior
    assert not re.search(
        r"(?is)"
        r"not\s+(?:a\s+)?Spectre\s+testbench|"
        r"testbench-generation task|"
        r"Return only the Verilog-A source|"
        r"graded as the candidate implementation|"
        r"Both\s+files\s+are\s+scored\s+DUT\s+source\s+artifacts|"
        r"Do not generate a Spectre `?\.scs`? file|"
        r"^Implement\s",
        behavior,
    )


def test_all_testbench_canonical_behavior_is_form_neutral() -> None:
    forbidden = re.compile(
        r"not\s+(?:a\s+)?Spectre\s+testbench|"
        r"testbench-generation task|"
        r"Return only the Verilog-A source|"
        r"graded as the candidate implementation|"
        r"Both\s+files\s+are\s+scored\s+DUT\s+source\s+artifacts|"
        r"Do not generate a Spectre `?\.scs`? file|"
        r"^Implement(?:\s|:)",
        flags=re.IGNORECASE | re.DOTALL | re.MULTILINE,
    )
    problems = []
    for source_task in sorted(PROVENANCE.iterdir()):
        if not source_task.is_dir():
            continue
        behavior = canonical_required_behavior(source_task, "testbench")
        if match := forbidden.search(behavior):
            problems.append(f"{source_task.name}: {match.group(0)!r}")

    assert problems == []


def test_testbench_instruction_has_one_candidate_and_five_anonymous_negatives() -> None:
    text = render_testbench_instruction(sample_spec())
    assert "`testbench.scs`" in text
    assert "five anonymous semantic negative DUTs" in text
    assert "hidden" not in text.lower()
    assert "- Include path: `./dut/dut.va`" in text
    assert "- DUT instance: `XDUT (vin) dut`" in text
    assert "- Required saved public traces: `vin`" in text
    assert "one bounded transient analysis with a finite positive stop time" in text
    assert "Do not redefine the DUT, drive DUT output nets" in text
    assert "Exact event counts, absolute event times, sample density" in text
    assert "reference-deck ordering are not part of the contract" in text


def test_family_064_uses_default_parameter_policy_without_override_property() -> None:
    source = PROVENANCE / "064-edge-delay-line-with-deglitch"
    spec = json.loads(
        (source / "evaluator" / "family_spec.json").read_text(encoding="utf-8")
    )
    instruction = (source / "public" / "task" / "instruction.md").read_text(
        encoding="utf-8"
    )
    rendered = render_testbench_instruction(
        spec,
        canonical_behavior=canonical_required_behavior(source, "testbench"),
    )

    property_ids = {item["id"] for item in spec["properties"]}
    assert "P_PARAMETER_OVERRIDE" not in property_ids
    assert "Scored evaluation\nuses these published default values" in instruction
    assert "alternative parameter overrides are outside" in instruction
    assert "P_PARAMETER_OVERRIDE" not in rendered
    assert "alternative parameter overrides are outside" in rendered


def test_testbench_instruction_renders_multi_file_instances_and_parameter_overrides() -> None:
    spec = sample_spec()
    spec["artifact_contract"]["files"].append({
        "path": "helper.va",
        "modules": [],
    })
    spec["testbench_binding"]["instances"].append({
        "name": "XHELP",
        "module_ref": "helper",
        "connections": [
            {"port_ref": "out", "net": "observed", "position": 1},
            {"port_ref": "in", "net": "vin", "position": 0},
        ],
        "parameter_overrides": {"width": 4, "gain": 2},
    })

    text = render_testbench_instruction(spec)
    assert "- Include paths: `./dut/dut.va`, `./dut/helper.va`" in text
    assert "- DUT instance: `XHELP (vin observed) helper gain=2 width=4`" in text


def test_binding_renderer_exposes_declared_instance_parameter_overrides() -> None:
    spec = sample_spec()
    spec["testbench_binding"]["instances"][0]["parameter_overrides"] = {"ctrl": 42}
    text = render_binding(spec)
    assert "- DUT instance: `XDUT (vin) dut ctrl=42`" in text


def test_seed_policy_prefers_temporal_semantic_fault_over_force_zero() -> None:
    row = {
        "bugfix_seed": "neg_001_force_zero",
        "active_mutations": [
            {"mutation_id": "neg_001_force_zero", "fault_class": "stuck_zero", "trigger_condition": "all time", "violated_property_ids": ["P_OUT"]},
            {"mutation_id": "neg_002_wrong_edge", "fault_class": "wrong_sampling_edge", "trigger_condition": "falling edge after reset", "violated_property_ids": ["P_EDGE", "P_HOLD"]},
        ],
    }
    selected = select_bugfix_seed(row)
    assert selected["mutation_id"] == "neg_002_wrong_edge"
    assert not selected["triviality_markers"]


def test_release_artifact_set_omits_task_local_provenance_indexes() -> None:
    assert "BUGFIX_SEED_REVIEW.json" not in RELEASE_SEAL_ARTIFACTS
    assert all("provenance" not in artifact for artifact in RELEASE_SEAL_ARTIFACTS)


def test_prompt_components_have_pinned_reference_tokenizer_metadata() -> None:
    assert REFERENCE_TOKENIZER["id"] == "vabench_utf8_lexeme"
    assert set(COMPONENT_METADATA) == {
        "direct_wrapper.md",
        "agentic_wrapper.md",
    }
    assert reference_token_count("one two; three") == 4


def test_facility_veriloga_skill_is_tool_independent_and_probe_only() -> None:
    root = Path(__file__).resolve().parents[3] / "skills" / "veriloga"
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ).lower()
    for forbidden in (
        "evas", "spectre", "openvaf", "ngspice", "cadence", "virtuoso",
        "vabench", "behavioral-veriloga-eval", ".scs", "testbench",
    ):
        assert forbidden not in text
    examples = {
        path.name for path in (root / "assets" / "examples").glob("*.va")
    }
    assert examples == {
        "branch_access_probe.va",
        "cross_logging_probe.va",
        "declaration_parameter_probe.va",
        "minimal_zero_probe.va",
        "transition_syntax_probe.va",
        "vector_genvar_zero_probe.va",
    }
    assert not list(root.rglob("*.scs"))
    assert not list(root.rglob("*.py"))


def test_feedback_skill_is_a_routed_public_evas_workflow() -> None:
    root = Path(__file__).resolve().parents[3] / "skills" / "vabench-feedback"
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    assert "name: vabench-feedback" in skill
    assert "public/task/evas_runtime.json" in skill
    assert "private evaluator remain the final judge" in skill
    assert "references/runtime-contract.md" in skill
    assert "references/form-workflows.md" in skill
    assert "references/diagnosis.md" in skill
    assert re.search(r"v4-\d{3,4}", skill, flags=re.IGNORECASE) is None


def test_feedback_skill_name_is_not_confused_with_legacy_feedback_cli() -> None:
    assert public_text_leaks_authoring_surface("# vaBench Feedback") is False
    assert public_text_leaks_authoring_surface("vabench feedback run --task v4-001") is True
    assert public_text_leaks_authoring_surface("vabench feedback capabilities") is True


def test_prompt_assets_keep_wrappers_and_snapshot_real_skills(tmp_path: Path) -> None:
    records = install_prompt_assets(tmp_path)
    manifest = json.loads((tmp_path / "prompt_modes" / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["wrappers"]) == {"direct_wrapper.md", "agentic_wrapper.md"}
    assert "form_skills" not in manifest
    assert "evas_guides" not in manifest
    assert set(manifest["components"]) == set(manifest["wrappers"])
    assert set(manifest["skill_snapshots"]) == {"veriloga", "vabench-feedback"}
    assert (tmp_path / "prompt_modes" / "wrappers" / "direct_wrapper.md").is_file()
    assert (tmp_path / "prompt_modes" / "wrappers" / "agentic_wrapper.md").is_file()
    assert not (tmp_path / "prompt_modes" / "form_skills").exists()
    assert not (tmp_path / "prompt_modes" / "evas_guides").exists()
    assert not (tmp_path / "prompt_modes" / "skills").exists()
    assert (tmp_path / "skills" / "veriloga" / "SKILL.md").is_file()
    assert (tmp_path / "skills" / "vabench-feedback" / "SKILL.md").is_file()
    skill_manifest = json.loads((tmp_path / "skills" / "SNAPSHOT_MANIFEST.json").read_text(encoding="utf-8"))
    assert skill_manifest["mode_skill_matrix"]["G1"] == ["veriloga"]
    assert skill_manifest["mode_skill_matrix"]["G4"] == ["vabench-feedback"]
    veriloga_source = skill_manifest["skills"]["veriloga"]["source"]
    assert veriloga_source["upstream_commit"] == (
        "bf3ee9f5c20bbefccc36f1cd58af9a48032a6ca5"
    )
    assert veriloga_source["upstream_pull_request"].endswith("/pull/17")
    assert all(
        not Path(record["source_path"]).is_absolute()
        for skill in skill_manifest["skills"].values()
        for record in skill["files"]
    )
    assert records["direct_wrapper.md"]["kind"] == "wrapper"


def test_materializer_rejects_a_symlinked_skill_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_root = tmp_path / "skill-sources"
    outside = tmp_path / "outside-veriloga"
    outside.mkdir()
    (outside / "SKILL.md").write_text("---\nname: veriloga\n---\n", encoding="utf-8")
    source_root.mkdir()
    (source_root / "veriloga").symlink_to(outside, target_is_directory=True)
    monkeypatch.setitem(
        install_skill_snapshots.__globals__, "SKILLS_ROOT", source_root
    )

    with pytest.raises(SystemExit, match="skill source contains symlink"):
        install_skill_snapshots(tmp_path / "release")


def test_pre_r50_prompt_assets_remain_reproducible_as_legacy_inline_components(
    tmp_path: Path,
) -> None:
    install_prompt_assets(tmp_path, "r49")
    manifest = json.loads(
        (tmp_path / "prompt_modes" / "manifest.json").read_text(encoding="utf-8")
    )
    modes = json.loads(
        (tmp_path / "prompt_modes" / "modes.json").read_text(encoding="utf-8")
    )["modes"]
    assert set(manifest["form_skills"]) == {
        "dut_modeling.md", "testbench_verification.md", "bugfix_diagnosis.md",
    }
    assert set(manifest["evas_guides"]) == {
        "evas_core.md", "evas_dut.md", "evas_testbench.md", "evas_bugfix.md",
    }
    assert not (tmp_path / "skills").exists()
    assert modes["G1"]["form_skill"] is True
    assert "skills" not in modes["G1"]


def test_direct_wrapper_defines_unambiguous_artifact_protocol(tmp_path: Path) -> None:
    install_prompt_assets(tmp_path)
    wrapper = (tmp_path / "prompt_modes" / "wrappers" / "direct_wrapper.md").read_text(encoding="utf-8")

    assert '`<<<VABENCH_ARTIFACT path="`' in wrapper
    assert "exact declared relative artifact" in wrapper
    assert "exactly three `>` characters" in wrapper
    assert "`<<<END_VABENCH_ARTIFACT>>>`" in wrapper
    assert "Only `VABENCH_ARTIFACT` is a valid submission marker" in wrapper
    assert "Do not wrap the artifact body in Markdown code fences" in wrapper
    assert "Do not include explanatory prose" in wrapper


def test_agentic_wrapper_discloses_evas_spectre_portability_boundary(
    tmp_path: Path,
) -> None:
    install_prompt_assets(tmp_path)
    wrapper_path = tmp_path / "prompt_modes" / "wrappers" / "agentic_wrapper.md"
    wrapper = wrapper_path.read_text(encoding="utf-8")
    manifest = json.loads(
        (tmp_path / "prompt_modes" / "manifest.json").read_text(encoding="utf-8")
    )
    record = manifest["wrappers"]["agentic_wrapper.md"]

    assert "The visible closed loop runs on EVAS" in wrapper
    assert "does not invoke Cadence Spectre" in wrapper
    assert "adaptive time-step placement" in wrapper
    assert all(event in wrapper for event in ("`timer`", "`cross`", "`transition`"))
    assert "handling of `$bound_step`" in wrapper
    assert "diagnostics for invalid models" in wrapper
    assert "portable Verilog-A semantics" in wrapper
    assert "raw output-row density" in wrapper
    assert "public EVAS loop only" in wrapper
    assert record["sha256"] == file_sha(wrapper_path)
    assert record["bytes"] == len(wrapper_path.read_bytes())
    assert record == manifest["components"]["agentic_wrapper.md"]


def test_runtime_prompt_components_follow_explicit_order_with_wrapper_last() -> None:
    mode_record = {
        "component_order": [
            "instruction",
            "agentic_wrapper.md",
        ],
        "prompt_component_hashes": {
            "agentic_wrapper.md": "d" * 64,
        },
    }
    assert ordered_prompt_components(mode_record) == ["agentic_wrapper.md"]


def test_render_prompt_announces_skills_without_inlining_body(tmp_path: Path) -> None:
    release = tmp_path / "release"
    task = tmp_path / "task"
    path = release / "prompt_modes" / "wrappers" / "agentic_wrapper.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("agentic wrapper\n", encoding="utf-8")
    (task / "public").mkdir(parents=True)
    (task / "public" / "instruction.md").write_text("repair task\n", encoding="utf-8")
    mode_record = {
        "mode": "G5",
        "component_order": [
            "instruction",
            "agentic_wrapper.md",
        ],
        "available_skills": {
            "veriloga": {
                "path": "public/skills/veriloga",
                "skill_file": "public/skills/veriloga/SKILL.md",
                "tree_sha256": "a" * 64,
            },
        },
        "prompt_component_hashes": {
            "agentic_wrapper.md": "d" * 64,
        },
    }
    rendered = render_prompt(
        release,
        task,
        {"form": "bugfix"},
        mode_record,
        inline_artifacts=False,
    )
    assert '<<<VABENCH_SKILL_AVAILABILITY>>>' in rendered
    assert "public/skills/veriloga/SKILL.md" in rendered
    assert '<<<VABENCH_COMPONENT id="agentic_wrapper.md">>>' in rendered
    assert "---\nname:" not in rendered
    assert "Use this skill" not in rendered
    assert "VABENCH_PUBLIC_CONTRACT" not in rendered
    assert rendered.strip().endswith("<<<END_VABENCH_COMPONENT>>>")


def test_derived_prompt_plan_hash_binds_non_visible_public_contract(tmp_path: Path) -> None:
    release = tmp_path / "release"
    install_prompt_assets(release)
    task = release / "tasks" / "1001-sample-bugfix"
    (task / "public" / "buggy_bundle").mkdir(parents=True)
    (task / "public" / "instruction.md").write_text("Repair the bundle.\n", encoding="utf-8")
    (task / "public" / "buggy_bundle" / "dut.va").write_text("module dut; endmodule\n", encoding="utf-8")
    (task / "public_contract.json").write_text('{"task_id":"v4-1001"}\n', encoding="utf-8")
    record = {
        "task_id": "v4-1001",
        "family_id": "001",
        "form": "bugfix",
        "public_contract_sha256": file_sha(task / "public_contract.json"),
    }
    plan = build_mode_record(release, task, record, "G5")
    assert plan["public_contract_sha256"] == file_sha(task / "public_contract.json")
    assert plan["component_order"][-1:] == ["agentic_wrapper.md"]
    assert set(plan["available_skills"]) == {"veriloga", "vabench-feedback"}
    assert set(plan["public_input_hashes"]) == {
        "public/instruction.md", "public/buggy_bundle/dut.va",
    }


def test_prompt_inputs_exclude_contract_json_from_model_surface(tmp_path: Path) -> None:
    task = tmp_path / "task"
    (task / "public").mkdir(parents=True)
    (task / "public" / "instruction.md").write_text("instruction.md\n", encoding="utf-8")
    (task / "public_contract.json").write_text("public_contract.json\n", encoding="utf-8")
    assert [path.name for path in iter_public_inputs(task, "dut", "G0")] == ["instruction.md"]
    assert [path.name for path in iter_public_inputs(task, "dut", "G1")] == ["instruction.md"]
    assert [path.name for path in iter_public_inputs(task, "dut", "G2")] == ["instruction.md"]


def test_public_contracts_live_in_task_directories(tmp_path: Path) -> None:
    output = tmp_path / "release"
    task = output / "tasks" / "001-sample"
    task.mkdir(parents=True)
    assert public_contract_relative_path(task) == "tasks/001-sample/public_contract.json"
    relative = write_public_contract(output, task, {"task_id": "v4-001", "form": "dut"})
    assert relative == "tasks/001-sample/public_contract.json"
    assert (output / relative).is_file()
    assert (task / "public_contract.json").is_file()


def test_agentic_bugfix_export_seeds_editable_submission(tmp_path: Path) -> None:
    task = tmp_path / "task"
    (task / "public" / "buggy_bundle").mkdir(parents=True)
    (task / "public" / "buggy_bundle" / "a.va").write_text("module a; endmodule\n", encoding="utf-8")
    (task / "public" / "instruction.md").write_text("Repair the bundle.\n", encoding="utf-8")
    add_public_evas_runtime(task)
    public = tmp_path / "public"
    (public / "submission").mkdir(parents=True)
    install_public(task, public, "bugfix", "G2")
    assert (public / "submission" / "a.va").read_bytes() == (task / "public" / "buggy_bundle" / "a.va").read_bytes()
    assert (public / "task" / "buggy_bundle" / "a.va").is_file()
    assert (public / "task" / "visible_test.scs").is_file()
    assert (public / "evas_manifest.json").is_file()
    assert not (public / "tool_manifest.json").exists()


def test_export_omits_public_contract_mount(tmp_path: Path) -> None:
    task = tmp_path / "task"
    (task / "public").mkdir(parents=True)
    (task / "public" / "instruction.md").write_text("Build the DUT.\n", encoding="utf-8")
    add_public_evas_runtime(task)
    for mode in ("G0", "G2"):
        public = tmp_path / f"public-{mode}"
        (public / "submission").mkdir(parents=True)
        install_public(task, public, "dut", mode)
        assert (public / "task" / "instruction.md").is_file()
        assert not (public / "task" / "public_contract.json").exists()


def test_export_mounts_declared_public_readonly_support(tmp_path: Path) -> None:
    task = tmp_path / "task"
    support = task / "evaluator" / "solution" / "support"
    support.mkdir(parents=True)
    helper = support / "helper.va"
    helper.write_text("module helper; endmodule\n", encoding="utf-8")
    (task / "evaluator" / "family_spec.json").write_text(json.dumps({
        "support_contract": {
            "visibility": "public_readonly",
            "source_root": "public_support",
            "mount_root": "support",
            "files": [{"path": "helper.va", "sha256": file_sha(helper), "modules": ["helper"]}],
        }
    }) + "\n", encoding="utf-8")
    (task / "public").mkdir(parents=True)
    (task / "public" / "instruction.md").write_text("Build the DUT.\n", encoding="utf-8")
    add_public_evas_runtime(task)
    public = tmp_path / "runtime-public"
    (public / "submission").mkdir(parents=True)
    install_public(task, public, "dut", "G2")
    assert (public / "task" / "public_support" / "helper.va").read_bytes() == helper.read_bytes()


@pytest.mark.parametrize("release_revision", ["r45", "r47"])
def test_g5_testbench_runtime_exports_direct_evas_visible_suite(
    tmp_path: Path,
    monkeypatch,
    release_revision: str,
) -> None:
    source_task, row, seed_review = sample_source_task(tmp_path, independent_reference=True)
    release = tmp_path / "release"
    task_record = build_testbench_view(
        release,
        source_task,
        row,
        sample_spec(),
        "a" * 64,
        seed_review,
        release_revision=release_revision,
    )
    install_prompt_assets(release, release_revision)
    (release / "TASK_INDEX.json").write_text(
        json.dumps({"tasks": [task_record]}) + "\n", encoding="utf-8"
    )
    runtime = tmp_path / "runtime"
    monkeypatch.setattr(sys, "argv", [
        "export_tri_form_runtime.py",
        "--release", str(release),
        "--task", "v4-501",
        "--mode", "G5",
        "--output", str(runtime),
        "--working-token-budget", "4096",
    ])
    assert export_runtime() == 0
    monkeypatch.setattr(sys, "argv", [
        "audit_runtime_export.py", "--run", str(runtime),
    ])
    assert audit_runtime_export() == 0
    assert not (runtime / "public" / "task" / "visible_test.scs").exists()
    assert (runtime / "public" / "task" / "evas_runtime.json").read_bytes() == (
        runtime / "evaluator" / "trusted_replay_suite.json"
    ).read_bytes()
    suite = json.loads(
        (runtime / "public" / "task" / "evas_runtime.json").read_text(encoding="utf-8")
    )
    assert [case["case"] for case in suite["cases"]] == [
        "reference", "mutation_01", "mutation_02", "mutation_03", "mutation_04", "mutation_05",
    ]
    assert "public/submission/runs" not in suite["candidate_command_template"]
    assert "/tmp/vabench-visible/runs/{case}" in suite["candidate_command_template"]


def test_g1_dut_runtime_audit_does_not_require_agentic_visible_mount(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_task, row, _ = sample_source_task(tmp_path, independent_reference=True)
    release = tmp_path / "release"
    task_record = build_dut_view(
        release, source_task, row, sample_spec(), "a" * 64, release_revision="r50"
    )
    install_prompt_assets(release)
    (release / "TASK_INDEX.json").write_text(
        json.dumps({"tasks": [task_record]}) + "\n", encoding="utf-8"
    )
    runtime = tmp_path / "runtime"
    monkeypatch.setattr(sys, "argv", [
        "export_tri_form_runtime.py",
        "--release", str(release),
        "--task", "v4-001",
        "--mode", "G1",
        "--output", str(runtime),
        "--working-token-budget", "4096",
    ])
    assert export_runtime() == 0
    assert not (runtime / "public" / "task" / "visible_test.scs").exists()
    policy = json.loads((runtime / "MODEL_ACCESS_POLICY.json").read_text(encoding="utf-8"))
    assert policy["mounts"] == []
    assert policy["provider_tools"] == ["list_skills", "read_skill"]
    assert set(policy["available_skills"]) == {"veriloga"}
    assert (runtime / "public" / "skills" / "veriloga" / "SKILL.md").is_file()
    monkeypatch.setattr(sys, "argv", [
        "audit_runtime_export.py", "--run", str(runtime),
    ])
    assert audit_runtime_export() == 0


def test_g2_runtime_has_no_skill_surface(tmp_path: Path, monkeypatch) -> None:
    source_task, row, _ = sample_source_task(tmp_path, independent_reference=True)
    release = tmp_path / "release"
    task_record = build_dut_view(
        release, source_task, row, sample_spec(), "a" * 64, release_revision="r50"
    )
    install_prompt_assets(release)
    (release / "TASK_INDEX.json").write_text(json.dumps({"tasks": [task_record]}) + "\n", encoding="utf-8")
    runtime = tmp_path / "runtime"
    monkeypatch.setattr(sys, "argv", [
        "export_tri_form_runtime.py",
        "--release", str(release),
        "--task", "v4-001",
        "--mode", "G2",
        "--output", str(runtime),
        "--working-token-budget", "4096",
    ])
    assert export_runtime() == 0
    policy = json.loads((runtime / "MODEL_ACCESS_POLICY.json").read_text(encoding="utf-8"))
    assert policy["mounts"] == ["public/task:ro", "public/submission:rw", "public/work:rw"]
    assert policy["provider_tools"] == []
    assert policy["available_skills"] == {}
    assert not (runtime / "public" / "skills").exists()


@pytest.mark.parametrize(
    ("mode", "expected_skills", "expected_mounts"),
    [
        ("G0", set(), []),
        ("G1", {"veriloga"}, []),
        ("G2", set(), ["public/task:ro", "public/submission:rw", "public/work:rw"]),
        (
            "G3",
            {"veriloga"},
            [
                "public/task:ro",
                "public/submission:rw",
                "public/work:rw",
                "public/skills:ro",
            ],
        ),
        (
            "G4",
            {"vabench-feedback"},
            [
                "public/task:ro",
                "public/submission:rw",
                "public/work:rw",
                "public/skills:ro",
            ],
        ),
        (
            "G5",
            {"veriloga", "vabench-feedback"},
            [
                "public/task:ro",
                "public/submission:rw",
                "public/work:rw",
                "public/skills:ro",
            ],
        ),
    ],
)
def test_r50_mode_matrix_exports_only_declared_real_skills(
    tmp_path: Path,
    monkeypatch,
    mode: str,
    expected_skills: set[str],
    expected_mounts: list[str],
) -> None:
    source_task, row, _ = sample_source_task(tmp_path, independent_reference=True)
    release = tmp_path / "release"
    task_record = build_dut_view(
        release, source_task, row, sample_spec(), "a" * 64, release_revision="r50"
    )
    install_prompt_assets(release)
    (release / "TASK_INDEX.json").write_text(
        json.dumps({"tasks": [task_record]}) + "\n", encoding="utf-8"
    )
    runtime = tmp_path / "runtime"
    monkeypatch.setattr(sys, "argv", [
        "export_tri_form_runtime.py",
        "--release", str(release),
        "--task", "v4-001",
        "--mode", mode,
        "--output", str(runtime),
        "--working-token-budget", "4096",
    ])

    assert export_runtime() == 0
    policy = json.loads(
        (runtime / "MODEL_ACCESS_POLICY.json").read_text(encoding="utf-8")
    )
    assert policy["schema_version"] == "r50-real-skills-model-access-policy-v1"
    assert policy["mounts"] == expected_mounts
    assert set(policy["available_skills"]) == expected_skills
    assert policy["provider_tools"] == (
        ["list_skills", "read_skill"] if expected_skills else []
    )
    active_tools = active_tool_schemas(runtime, mode)
    active_tool_names = [
        tool["function"]["name"] for tool in (active_tools or [])
    ]
    assert active_tool_names == (
        (["list_files", "read_file", "write_file", "run_evas", "finalize"]
         if mode in {"G2", "G3", "G4", "G5"} else [])
        + (["list_skills", "read_skill"] if expected_skills else [])
    )
    skills_root = runtime / "public" / "skills"
    observed_skills = {
        path.name
        for path in skills_root.iterdir()
        if path.is_dir()
    } if skills_root.is_dir() else set()
    assert observed_skills == expected_skills
    prompt_name = "agent_prompt.txt" if mode in {"G2", "G3", "G4", "G5"} else "direct_prompt.txt"
    prompt = (runtime / prompt_name).read_text(encoding="utf-8")
    assert ("<<<VABENCH_SKILL_AVAILABILITY>>>" in prompt) is bool(expected_skills)
    assert "---\nname: veriloga" not in prompt
    assert "---\nname: vabench-feedback" not in prompt
    if mode in {"G2", "G3", "G4", "G5"}:
        assert "The visible closed loop runs on EVAS" in prompt
        assert "does not invoke Cadence Spectre" in prompt
        assert "raw output-row density" in prompt
    else:
        assert "The visible closed loop runs on EVAS" not in prompt
    monkeypatch.setattr(sys, "argv", [
        "audit_runtime_export.py", "--run", str(runtime),
    ])
    assert audit_runtime_export() == 0


def test_export_rejects_a_noncanonical_release_skill_path(tmp_path: Path) -> None:
    source_task, row, _ = sample_source_task(tmp_path, independent_reference=True)
    release = tmp_path / "release"
    task_record = build_dut_view(
        release, source_task, row, sample_spec(), "a" * 64, release_revision="r50"
    )
    install_prompt_assets(release)
    manifest_path = release / "skills" / "SNAPSHOT_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["skills"]["veriloga"]["path"] = "../outside/veriloga"
    manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    task = next((release / "tasks").iterdir())

    with pytest.raises(SystemExit, match="path is not canonical"):
        build_mode_record(release, task, task_record, "G1")


def test_runner_rejects_a_skill_manifest_in_a_skill_free_mode(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    skill = runtime / "public" / "skills" / "veriloga"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: veriloga\n---\n", encoding="utf-8")
    write_runtime_skill_manifest(runtime)
    (runtime / "MODEL_ACCESS_POLICY.json").write_text(
        json.dumps({"mode": "G0", "provider_tools": [], "available_skills": {}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="provider-tool policy disagree"):
        active_tool_schemas(runtime, "G0")


def test_runtime_audit_rejects_an_undeclared_skills_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_task, row, _ = sample_source_task(tmp_path, independent_reference=True)
    release = tmp_path / "release"
    task_record = build_dut_view(
        release, source_task, row, sample_spec(), "a" * 64, release_revision="r50"
    )
    install_prompt_assets(release)
    (release / "TASK_INDEX.json").write_text(
        json.dumps({"tasks": [task_record]}) + "\n", encoding="utf-8"
    )
    runtime = tmp_path / "runtime"
    monkeypatch.setattr(sys, "argv", [
        "export_tri_form_runtime.py",
        "--release", str(release),
        "--task", "v4-001",
        "--mode", "G0",
        "--output", str(runtime),
        "--working-token-budget", "4096",
    ])
    assert export_runtime() == 0
    (runtime / "public" / "skills").mkdir()
    monkeypatch.setattr(sys, "argv", [
        "audit_runtime_export.py", "--run", str(runtime),
    ])

    assert audit_runtime_export() == 1


def test_skill_lookup_rejects_a_symlinked_skills_root(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    (runtime / "public").mkdir(parents=True)
    outside = tmp_path / "outside-skills"
    outside.mkdir()
    (runtime / "public" / "skills").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="skills root is a symlink"):
        list_available_skills(runtime)


def test_skill_lookup_is_confined_and_cached(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    skill = runtime / "public" / "skills" / "veriloga"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: veriloga\n---\n# Skill\n", encoding="utf-8")
    (skill / "assets").mkdir()
    (skill / "assets" / "probe.va").write_text(
        "module probe; analog begin end endmodule\n", encoding="utf-8"
    )
    write_runtime_skill_manifest(runtime)

    listed = list_available_skills(runtime)["skills"]
    assert set(listed) == {"veriloga"}
    assert {record["path"] for record in listed["veriloga"]["files"]} == {
        "SKILL.md", "assets/probe.va",
    }
    first = read_skill_file(runtime, "veriloga", "SKILL.md")
    assert "# Skill" in first
    assert "module probe" in read_skill_file(runtime, "veriloga", "assets/probe.va")
    second = read_skill_file(runtime, "veriloga", "SKILL.md")
    assert json.loads(second)["status"] == "already_provided_in_this_episode"
    with pytest.raises(ValueError, match="unsafe relative path"):
        read_skill_file(runtime, "veriloga", "../secret.md")
    with pytest.raises(ValueError, match="not available"):
        read_skill_file(runtime, "missing", "SKILL.md")
    events = [
        json.loads(line)
        for line in (runtime / "evidence" / "skill_lookup_events.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert [event["cached"] for event in events] == [False, False, True]


def test_skill_lookup_rejects_symlink(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    skill = runtime / "public" / "skills" / "veriloga"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: veriloga\n---\n", encoding="utf-8")
    outside = tmp_path / "outside.md"
    outside.write_text("secret\n", encoding="utf-8")
    (skill / "leak.md").symlink_to(outside)
    write_runtime_skill_manifest(runtime)
    with pytest.raises(ValueError, match="contains a symlink"):
        read_skill_file(runtime, "veriloga", "leak.md")


def test_skill_lookup_rejects_snapshot_tampering(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    skill = runtime / "public" / "skills" / "veriloga"
    skill.mkdir(parents=True)
    source = skill / "SKILL.md"
    source.write_text("---\nname: veriloga\n---\n# Skill\n", encoding="utf-8")
    write_runtime_skill_manifest(runtime)
    source.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ValueError, match="tree hash mismatch"):
        list_available_skills(runtime)


def test_runtime_evidence_rejects_handwritten_pass_report(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "runtime_export_audit.json").write_text(
        '{"schema_version":"wrong","status":"pass","problems":[]}\n',
        encoding="utf-8",
    )
    try:
        verified_audit(tmp_path)
    except SystemExit as exc:
        assert "not a valid pass" in str(exc)
    else:
        raise AssertionError("handwritten pass report was accepted")


def test_bugfix_bundle_hashes_include_unchanged_gold_artifacts(tmp_path: Path) -> None:
    solution = tmp_path / "solution"
    solution.mkdir()
    (solution / "changed.va").write_text("gold changed\n", encoding="utf-8")
    (solution / "unchanged.va").write_text("gold unchanged\n", encoding="utf-8")
    mutated_hash = "c" * 64
    assert expected_buggy_artifact_hashes(
        ["changed.va", "unchanged.va"],
        {"changed.va": mutated_hash},
        solution,
    ) == {
        "changed.va": mutated_hash,
        "unchanged.va": file_sha(solution / "unchanged.va"),
    }


def test_release_seal_binds_transitive_release_and_reused_certifications(tmp_path: Path) -> None:
    for relative in RELEASE_SEAL_ARTIFACTS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"artifact": relative}) + "\n", encoding="utf-8")
    reuse = {
        "policy": "source_denominator_hash_bound",
        "source_dut_gold_certification_count": 400,
        "source_negative_certification_count": 2000,
        "evaluators": ["rust_evas2"],
        "simulation_rerun_required_for_materialization": False,
    }
    seal = build_release_seal(tmp_path, "a" * 64, reuse)
    assert seal["release_status"] == "r44_immutable_rust_evas2_certified"
    assert seal["release_revision"] == "r44"
    assert seal["immutable"] is True
    assert seal["certification_reuse"] == reuse
    assert set(seal["artifact_sha256"]) == set(RELEASE_SEAL_ARTIFACTS)


@pytest.mark.parametrize("release_revision", ["r45", "r47"])
def test_post_r44_release_seal_has_independent_revision_identity(
    tmp_path: Path, release_revision: str,
) -> None:
    for relative in RELEASE_SEAL_ARTIFACTS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"artifact": relative}) + "\n", encoding="utf-8")
    reuse = {"simulation_rerun_required_for_materialization": False}

    seal = build_release_seal(
        tmp_path,
        "a" * 64,
        reuse,
        release_revision=release_revision,
    )

    assert seal["release_revision"] == release_revision
    assert seal["release_status"] == f"{release_revision}_immutable_rust_evas2_certified"
    assert seal["simulation_claim"].startswith("fresh full400")


def test_r45_evidence_never_falls_back_to_r44(tmp_path: Path) -> None:
    for relative in evidence_artifacts("r44"):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
    problems: list[str] = []

    hashes = audit_release_evidence("r45", problems, package_root=tmp_path)

    assert hashes == {}
    assert len(problems) == 6
    assert all("r45" in problem for problem in problems)
    assert not any("r44" in problem for problem in problems)


def test_r45_evidence_rejects_a_copied_r44_artifact(tmp_path: Path) -> None:
    filename = "PROFILE_PARITY.json"
    for revision in ("r44", "r45"):
        path = tmp_path / "evidence" / revision / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"status":"pass"}\n', encoding="utf-8")
    problems: list[str] = []

    audit_release_evidence("r45", problems, package_root=tmp_path)

    assert any("byte-identical to r44 evidence" in problem for problem in problems)


def test_r47_evidence_rejects_a_copied_r45_artifact(tmp_path: Path) -> None:
    filename = "PROFILE_PARITY.json"
    for revision in ("r45", "r47"):
        path = tmp_path / "evidence" / revision / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"status":"pass"}\n', encoding="utf-8")
    problems: list[str] = []

    audit_release_evidence("r47", problems, package_root=tmp_path)

    assert any("byte-identical to r45 evidence" in problem for problem in problems)


def write_valid_r47_evidence(tmp_path: Path) -> tuple[Path, str]:
    release = tmp_path / "release" / "benchmarkv4-r47"
    release.mkdir(parents=True)
    (release / "MANIFEST.json").write_text('{"release_revision":"r47"}\n', encoding="utf-8")
    source_sha = "a" * 64
    source_definition_sha = "d" * 64
    manifest_sha = file_sha(release / "MANIFEST.json")
    runtime = {
        "evas_engine": "evas2",
        "evas_engine_used": "evas2",
        "evas_version": "0.8.3",
        "evas_backend": "evas-rust",
    }
    payloads = {
        "RUST_EVAS2_CERTIFICATION.json": {
            "schema_version": "v4-r47-rust-evas2-certification-report-v2",
            "status": "pass",
            "release_candidate": "r47",
            "certification_policy": "rust_evas2_only",
            "source_certification_definition_sha256": source_definition_sha,
            "runtime": runtime,
            "input_report_sha256": [{"name": "raw.json", "sha256": "b" * 64}],
            "summary": {
                "family_count": 400,
                "gold_pass_count": 400,
                "negative_case_count": 2000,
                "mutation_kill_count": 2000,
                "insufficient_excitation_rejection_count": 400,
                "insufficient_excitation_not_applicable_count": 0,
            },
        },
        "STIMULUS_METAMORPHIC.json": {
            "schema_version": "v4-r47-stimulus-metamorphic-compact-v1",
            "status": "pass",
            "release": "release/benchmarkv4-r47",
            "release_revision": "r47",
            "certification_policy": "rust_evas2_only",
            "source_score_denominator_registry_sha256": source_sha,
            "release_manifest_sha256": manifest_sha,
            "input_report_sha256": "c" * 64,
            **runtime,
            "summary": {
                "task_count": 400,
                "affine_gold_pass_count": 400,
                "affine_mutation_kill_count": 2000,
                "affine_infrastructure_error_count": 0,
                "insufficient_excitation_rejection_count": 400,
                "insufficient_excitation_not_applicable_count": 0,
            },
        },
        "PROFILE_PARITY.json": {
            "schema_version": "v4-profile-parity-evas2-smoke-v1",
            "status": "pass",
            "release": "release/benchmarkv4-r47",
            "release_revision": "r47",
            "source_score_denominator_registry_sha256": source_sha,
            "release_manifest_sha256": manifest_sha,
            "evas_engine": "evas2",
            "evas_engine_used": "evas2",
            "evas_version": "0.8.3",
            "evas_backend_required": "evas-rust",
            "runtime": runtime,
            "task_count": 1200,
            "pass_count": 1200,
            "fail_count": 0,
        },
    }
    for filename, payload in payloads.items():
        path = tmp_path / "evidence" / "r47" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return release, source_sha


def test_r47_evidence_requires_strict_provenance_bindings(tmp_path: Path) -> None:
    release, source_sha = write_valid_r47_evidence(tmp_path)
    problems: list[str] = []

    audit_release_evidence(
        "r47",
        problems,
        package_root=tmp_path,
        release=release,
        source_registry_sha256=source_sha,
        source_definition_sha256="d" * 64,
    )

    assert problems == []


def test_r47_evidence_rejects_relabelled_payload_without_source_binding(tmp_path: Path) -> None:
    release, source_sha = write_valid_r47_evidence(tmp_path)
    profile = tmp_path / "evidence" / "r47" / "PROFILE_PARITY.json"
    payload = json.loads(profile.read_text(encoding="utf-8"))
    payload.pop("source_score_denominator_registry_sha256")
    profile.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    problems: list[str] = []

    audit_release_evidence(
        "r47",
        problems,
        package_root=tmp_path,
        release=release,
        source_registry_sha256=source_sha,
    )

    assert "r47 profile evidence source registry binding mismatch" in problems


def test_materializer_has_distinct_revision_default_outputs() -> None:
    assert DEFAULT_OUTPUTS["r47"].name == "benchmarkv4-r47"
    assert DEFAULT_OUTPUTS["r47"] != DEFAULT_OUTPUTS["r45"]
    assert DEFAULT_OUTPUTS["r48"].name == "benchmarkv4-r48"
    assert DEFAULT_OUTPUTS["r48"] != DEFAULT_OUTPUTS["r47"]
    assert DEFAULT_OUTPUTS["r49"].name == "benchmarkv4-r49"
    assert DEFAULT_OUTPUTS["r49"] != DEFAULT_OUTPUTS["r48"]


def test_prompt_component_path_supports_immutable_r44_feedback_assets(tmp_path: Path) -> None:
    assert prompt_component_path(tmp_path, "feedback_core.md") == (
        tmp_path / "prompt_modes" / "feedback_guides" / "feedback_core.md"
    )
    assert prompt_component_path(tmp_path, "feedback_dut.md") == (
        tmp_path / "prompt_modes" / "feedback_guides" / "feedback_dut.md"
    )


def test_materializer_refuses_to_rebuild_immutable_r44(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", [
        "materialize_tri_form_release.py",
        "--release-revision",
        "r44",
    ])
    try:
        materialize_release()
    except SystemExit as exc:
        assert "r44 is immutable" in str(exc)
    else:
        raise AssertionError("immutable r44 materialization was accepted")


@pytest.mark.parametrize("release_revision", ["r45", "r47"])
def test_materializer_refuses_to_replace_a_sealed_tracked_release(
    tmp_path: Path,
    monkeypatch,
    release_revision: str,
) -> None:
    release = tmp_path / f"benchmarkv4-{release_revision}"
    release.mkdir()
    (release / "RELEASE_SEAL.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setitem(DEFAULT_OUTPUTS, release_revision, release)
    monkeypatch.setattr(sys, "argv", [
        "materialize_tri_form_release.py",
        "--release-revision",
        release_revision,
    ])
    try:
        materialize_release()
    except SystemExit as exc:
        assert f"{release_revision} is immutable" in str(exc)
    else:
        raise AssertionError(f"tracked immutable {release_revision} materialization was accepted")


@pytest.mark.parametrize("release_revision", ["r45", "r47"])
def test_rebuilder_refuses_to_replace_a_sealed_tracked_release(
    tmp_path: Path,
    monkeypatch,
    release_revision: str,
) -> None:
    release = tmp_path / f"benchmarkv4-{release_revision}"
    release.mkdir()
    (release / "RELEASE_SEAL.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setitem(REBUILD_DEFAULT_RELEASES, release_revision, release)
    monkeypatch.setattr(sys, "argv", [
        "rebuild_tri_form_release.py",
        "--release-revision",
        release_revision,
    ])
    try:
        rebuild_release()
    except SystemExit as exc:
        assert f"{release_revision} is immutable" in str(exc)
    else:
        raise AssertionError(f"tracked immutable {release_revision} rebuild was accepted")


def test_release_seal_refuses_to_claim_stale_certifications(tmp_path: Path) -> None:
    for relative in RELEASE_SEAL_ARTIFACTS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"artifact": relative}) + "\n", encoding="utf-8")
    reuse = {
        "policy": "source_transitive_input_hash_bound",
        "source_dut_gold_certification_count": 399,
        "source_negative_certification_count": 1995,
        "evaluators": ["rust_evas2"],
        "simulation_rerun_required_for_materialization": True,
        "stale_certification_family_ids": ["398"],
    }
    certification_problems = ["398: source negative certification is stale"]

    seal = build_release_seal(
        tmp_path,
        "a" * 64,
        reuse,
        certification_problems,
    )

    assert seal["release_status"] == "materialized_certification_refresh_required"
    assert seal["simulation_claim"].startswith("none;")
    assert seal["certification_problem_count"] == 1
    assert seal["certification_problems"] == certification_problems
