from __future__ import annotations

import json
import sys
from pathlib import Path


PREP = Path(__file__).resolve().parents[2] / "operations" / "tri_form_derivation_prep"
if str(PREP) not in sys.path:
    sys.path.insert(0, str(PREP))

from materialize_tri_form_release import (  # noqa: E402
    COMPONENT_METADATA,
    MODES,
    REFERENCE_TOKENIZER,
    install_prompt_assets,
    iter_public_inputs,
    negative_assignment,
    public_contract_relative_path,
    reference_token_count,
    render_bugfix_instruction,
    render_testbench_instruction,
    select_bugfix_seed,
    write_public_contract,
)
from export_tri_form_runtime import install_public, ordered_prompt_components, render_prompt  # noqa: E402
from record_runtime_ingestion_evidence import verified_audit  # noqa: E402
from audit_tri_form_release import (  # noqa: E402
    RELEASE_SEAL_ARTIFACTS,
    build_release_seal,
    expected_buggy_artifact_hashes,
    file_sha,
    mutation_certification_hashes,
)


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


def test_mode_matrix_is_two_direct_plus_four_agentic() -> None:
    assert [name for name, row in MODES.items() if row["process"] == "direct_one_shot"] == ["G0", "G1"]
    assert [name for name, row in MODES.items() if row["feedback_cli"]] == ["G2", "G3", "G4", "G5"]


def test_bugfix_instruction_does_not_localize_fault() -> None:
    text = render_bugfix_instruction(sample_spec()).lower()
    for forbidden in ("mutation", "faulty file", "root cause", "changed line", "baseline result"):
        assert forbidden not in text


def test_testbench_instruction_has_one_candidate_and_five_anonymous_negatives() -> None:
    text = render_testbench_instruction(sample_spec())
    assert "`testbench.scs`" in text
    assert "five anonymous semantic negative DUTs" in text
    assert "hidden" not in text.lower()


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


def test_testbench_and_bugfix_share_one_selected_negative_assignment() -> None:
    row = {
        "bugfix_seed": "neg_001_force_zero",
        "active_mutations": [
            {"mutation_id": "neg_001_force_zero"},
            {"mutation_id": "neg_002_wrong_edge"},
        ],
    }
    selected = {"mutation_id": "neg_002_wrong_edge"}
    assert negative_assignment(row, selected) == {
        "bugfix_seed": "neg_002_wrong_edge",
        "testbench_suite": ["neg_001_force_zero", "neg_002_wrong_edge"],
    }


def test_prompt_components_have_pinned_reference_tokenizer_metadata() -> None:
    assert REFERENCE_TOKENIZER["id"] == "vabench_utf8_lexeme"
    assert set(COMPONENT_METADATA) == {
        "direct_wrapper.md",
        "agentic_wrapper.md",
        "dut_modeling.md",
        "testbench_verification.md",
        "bugfix_diagnosis.md",
        "feedback_dut.md",
        "feedback_testbench.md",
        "feedback_bugfix.md",
    }
    assert reference_token_count("one two; three") == 4


def test_prompt_assets_split_wrappers_form_skills_and_feedback_guides(tmp_path: Path) -> None:
    records = install_prompt_assets(tmp_path)
    manifest = json.loads((tmp_path / "prompt_modes" / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["wrappers"]) == {"direct_wrapper.md", "agentic_wrapper.md"}
    assert set(manifest["form_skills"]) == {"dut_modeling.md", "testbench_verification.md", "bugfix_diagnosis.md"}
    assert set(manifest["feedback_guides"]) == {"feedback_dut.md", "feedback_testbench.md", "feedback_bugfix.md"}
    assert set(manifest["components"]) == set(manifest["wrappers"]) | set(manifest["form_skills"]) | set(manifest["feedback_guides"])
    assert (tmp_path / "prompt_modes" / "wrappers" / "direct_wrapper.md").is_file()
    assert (tmp_path / "prompt_modes" / "wrappers" / "agentic_wrapper.md").is_file()
    assert (tmp_path / "prompt_modes" / "form_skills" / "dut_modeling.md").is_file()
    assert (tmp_path / "prompt_modes" / "feedback_guides" / "feedback_dut.md").is_file()
    assert not (tmp_path / "prompt_modes" / "skills").exists()
    assert records["direct_wrapper.md"]["kind"] == "wrapper"
    assert records["dut_modeling.md"]["kind"] == "form_skill"
    assert records["feedback_dut.md"]["kind"] == "feedback_guide"


def test_runtime_prompt_components_follow_explicit_order_with_wrapper_last() -> None:
    mode_record = {
        "component_order": [
            "instruction",
            "bugfix_diagnosis.md",
            "feedback_bugfix.md",
            "agentic_wrapper.md",
        ],
        "prompt_component_hashes": {
            "bugfix_diagnosis.md": "a" * 64,
            "feedback_bugfix.md": "b" * 64,
            "agentic_wrapper.md": "d" * 64,
        },
    }
    assert ordered_prompt_components(mode_record) == [
        "bugfix_diagnosis.md",
        "feedback_bugfix.md",
        "agentic_wrapper.md",
    ]


def test_render_prompt_places_guides_before_wrapper_without_public_contract_inline(tmp_path: Path) -> None:
    release = tmp_path / "release"
    task = tmp_path / "task"
    for subdir, name, text in [
        ("form_skills", "bugfix_diagnosis.md", "bugfix skill\n"),
        ("feedback_guides", "feedback_bugfix.md", "feedback bugfix\n"),
        ("wrappers", "agentic_wrapper.md", "agentic wrapper\n"),
    ]:
        path = release / "prompt_modes" / subdir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (task / "public").mkdir(parents=True)
    (task / "public" / "instruction.md").write_text("repair task\n", encoding="utf-8")
    mode_record = {
        "mode": "G5",
        "component_order": [
            "instruction",
            "bugfix_diagnosis.md",
            "feedback_bugfix.md",
            "agentic_wrapper.md",
        ],
        "prompt_component_hashes": {
            "bugfix_diagnosis.md": "a" * 64,
            "feedback_bugfix.md": "b" * 64,
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
    markers = [
        '<<<VABENCH_COMPONENT id="bugfix_diagnosis.md">>>',
        '<<<VABENCH_COMPONENT id="feedback_bugfix.md">>>',
        '<<<VABENCH_COMPONENT id="agentic_wrapper.md">>>',
    ]
    positions = [rendered.index(marker) for marker in markers]
    assert positions == sorted(positions)
    assert "VABENCH_PUBLIC_CONTRACT" not in rendered
    assert rendered.strip().endswith("<<<END_VABENCH_COMPONENT>>>")


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
    task = output / "tasks" / "dut" / "001-sample"
    task.mkdir(parents=True)
    assert public_contract_relative_path(task) == "tasks/dut/001-sample/public_contract.json"
    relative = write_public_contract(output, task, {"task_id": "v4-001", "form": "dut"})
    assert relative == "tasks/dut/001-sample/public_contract.json"
    assert (output / relative).is_file()
    assert (task / "public_contract.json").is_file()


def test_agentic_bugfix_export_seeds_editable_submission(tmp_path: Path) -> None:
    task = tmp_path / "task"
    (task / "public" / "buggy_bundle").mkdir(parents=True)
    (task / "public" / "buggy_bundle" / "a.va").write_text("module a; endmodule\n", encoding="utf-8")
    (task / "public" / "instruction.md").write_text("Repair the bundle.\n", encoding="utf-8")
    public = tmp_path / "public"
    (public / "submission").mkdir(parents=True)
    install_public(task, public, "bugfix", "G2")
    assert (public / "submission" / "a.va").read_bytes() == (task / "public" / "buggy_bundle" / "a.va").read_bytes()
    assert (public / "task" / "buggy_bundle" / "a.va").is_file()


def test_export_omits_public_contract_mount(tmp_path: Path) -> None:
    task = tmp_path / "task"
    (task / "public").mkdir(parents=True)
    (task / "public" / "instruction.md").write_text("Build the DUT.\n", encoding="utf-8")
    for mode in ("G0", "G2"):
        public = tmp_path / f"public-{mode}"
        (public / "submission").mkdir(parents=True)
        install_public(task, public, "dut", mode)
        assert (public / "task" / "instruction.md").is_file()
        assert not (public / "task" / "public_contract.json").exists()


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


def test_reference_certification_hashes_are_bound_to_exact_five_rows() -> None:
    rows = [
        {"mutation_id": "m1", "certification_sha256": "a" * 64},
        {"mutation_id": "m2", "certification_sha256": "b" * 64},
    ]
    assert mutation_certification_hashes(rows) == {
        "m1": "a" * 64,
        "m2": "b" * 64,
    }


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
        "evaluators": ["evas", "spectre"],
        "simulation_rerun_required_for_materialization": False,
    }
    seal = build_release_seal(tmp_path, "a" * 64, reuse)
    assert seal["release_status"] == "gate3_hash_bound_certification_reused"
    assert seal["certification_reuse"] == reuse
    assert set(seal["artifact_sha256"]) == set(RELEASE_SEAL_ARTIFACTS)
