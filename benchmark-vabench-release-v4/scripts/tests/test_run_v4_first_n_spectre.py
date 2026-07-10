from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT.parent
MODULE_PATH = ROOT / "scripts" / "run_v4_first_n_spectre.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_v4_first_n_spectre", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numbering_row() -> dict:
    return {
        "canonical_index": 1,
        "canonical_dut_id": "001",
        "canonical_dut_slug": "001-demo",
        "canonical_testbench_id": "501",
        "canonical_testbench_slug": "501-demo-testbench",
        "canonical_bugfix_id": "1001",
        "canonical_bugfix_slug": "1001-demo-bugfix",
        "old_dut_slug": "010-demo-source",
        "category": "demo",
        "level": "L2",
        "target_artifacts": ["top.va", "blocks/leaf.va"],
        "source_task_id": "fixture_demo",
        "selection_status": "selected_fixture",
        "title": "Demo System",
    }


def write_numbering_plan(path: Path) -> None:
    write_json(
        path,
        {
            "schema_version": "v4-task-family-numbering-plan-v1",
            "generated_at": "2026-07-10T00:00:00+00:00",
            "policy": {},
            "summary": {"canonical_dut_count": 1},
            "conflicts": [],
            "rows": [numbering_row()],
        },
    )


def write_task(module, tasks_root: Path) -> Path:
    task_dir = tasks_root / "010-demo-source"
    family_path = task_dir / "family_spec.json"
    support_path = task_dir / "public_support" / "helper.va"
    support_path.parent.mkdir(parents=True)
    support_path.write_text("module helper(out); output out; endmodule\n")
    write_json(
        family_path,
        {
            "schema_version": "v4-family-spec-v1",
            "family_id": "001",
            "task_ids": {"dut": "v4-001", "testbench": "v4-501", "bugfix": "v4-1001"},
            "identity": {
                "title": "Demo System",
                "category": "demo",
                "level": "L2",
                "difficulty": "D2",
                "supported_scope": "voltage-domain transient",
            },
            "artifact_contract": {
                "mode": "system_bundle",
                "files": [
                    {"path": "top.va", "modules": []},
                    {"path": "blocks/leaf.va", "modules": []},
                ],
            },
            "support_contract": {
                "visibility": "public_readonly",
                "source_root": "public_support",
                "mount_root": "support",
                "files": [
                    {"path": "helper.va", "sha256": sha256(support_path), "modules": ["helper"]}
                ],
            },
            "testbench_binding": {
                "dut_source_root": "dut",
                "source_path_template": "./dut/{artifact_path}",
                "instances": [],
            },
            "properties": [],
            "trace_contract": {"required_signals": ["time", "out"]},
            "modeling_constraints": [],
        },
    )
    checker_path = task_dir / "evaluator" / "checker_profile.json"
    write_json(
        checker_path,
        {
            "schema_version": "v4-checker-profile-v1",
            "checker_task_id": "fixture_checker",
            "side_effect_contract": {
                "base": "simulator_output_dir",
                "files": [{"path": "metric.out", "validator": "regex", "record_pattern": "ok\\n"}],
            },
        },
    )
    harness = {
        "schema_version": "v4-harness-spec-v1",
        "family_id": "010",
        "task_id": "v4-010",
        "generator": {"name": "render_v4_harness.py", "version": "v4-harness-renderer-v1"},
        "candidate": {"source_root": "./dut", "artifact_paths": ["top.va", "blocks/leaf.va"]},
        "support": {"source_root": "./support", "artifact_paths": ["helper.va"]},
        "deck": {
            "header": ["simulator lang=spectre", "global 0"],
            "include_templates": ['ahdl_include "{candidate_source_root}/{artifact_path}"'],
            "support_include_templates": [
                'ahdl_include "{support_source_root}/{support_artifact_path}"'
            ],
            "body_lines": ["XDUT (out) top"],
            "analyses": ["tran tran stop={stop_time} maxstep={maxstep}"],
            "save_signals": ["out"],
        },
        "property_ids": ["P_DEMO"],
        "profile_defaults": {
            "feedback": {
                "parameters": {"stop_time": "10n", "maxstep": "100p"},
                "simulatorOptions": {},
            },
            "score": {
                "parameters": {"stop_time": "20n", "maxstep": "50p"},
                "simulatorOptions": {"reltol": "1e-4"},
                "deck_overrides": {"body_lines": ["VSCORE marker 0 vsource dc=1"]},
            },
        },
        "source_contract": {
            "family_spec_sha256": sha256(family_path),
            "checker_profile_sha256": sha256(checker_path),
        },
    }
    harness_path = task_dir / "evaluator" / "harness_spec.json"
    write_json(harness_path, harness)
    loaded, harness_hash = module.load_spec(harness_path)
    write_json(
        task_dir / "evaluator" / "profiles" / "score.json",
        module.build_profile(loaded, "score", harness_hash),
    )
    (task_dir / "solution" / "blocks").mkdir(parents=True)
    (task_dir / "solution" / "top.va").write_text("module top(out); output out; endmodule\n")
    (task_dir / "solution" / "blocks" / "leaf.va").write_text(
        "module leaf(out); output out; endmodule\n"
    )
    return task_dir


def write_toolchain_lock(module, path: Path) -> None:
    write_json(
        path,
        {
            "schema_version": "v4-toolchain-lock-v1",
            "generated_at": "2026-07-10T00:00:00+00:00",
            "status": "valid",
            "evas": {},
            "spectre": {
                "backend": "sui-direct",
                "remote_host": "thu-wei",
                "route": "proxyjump=thu-jin",
                "path": "/opt/cadence/bin/spectre",
                "version": "sub-version fixture",
                "cadence_cshrc": "/home/cshrc/.cshrc.cadence.IC618SP201",
                "transport_identity": "sui-direct:ssh:thu-wei:proxyjump=thu-jin",
            },
            "benchmark": {
                "checker_registry_sha256": module.checker_registry_hash(),
                "harness_generator_sha256": sha256(ROOT / "scripts" / "render_v4_harness.py"),
                "oracle_runner_sha256": sha256(ROOT / "runners" / "feedback_oracle.py"),
            },
            "runtime": {},
        },
    )


def test_load_roster_uses_canonical_first_n_order(tmp_path: Path) -> None:
    module = load_module()
    plan = tmp_path / "numbering_plan.json"
    write_numbering_plan(plan)

    rows, plan_hash = module.load_roster(plan, 1)

    assert rows[0]["old_dut_slug"] == "010-demo-source"
    assert rows[0]["canonical_dut_id"] == "001"
    assert plan_hash == sha256(plan)

    broken = json.loads(plan.read_text())
    broken["rows"][0]["canonical_dut_id"] = "009"
    write_json(plan, broken)
    with pytest.raises(module.SidecarError, match="canonical_dut_id"):
        module.load_roster(plan, 1)


def test_source_slug_accepts_legacy_three_and_four_digit_ids() -> None:
    module = load_module()

    assert module.safe_source_slug("010-demo-source") == "010-demo-source"
    assert module.safe_source_slug("1001-differential-pair-gm-limiter") == (
        "1001-differential-pair-gm-limiter"
    )
    with pytest.raises(module.SidecarError, match="unsafe old_dut_slug"):
        module.safe_source_slug("../1001-demo")


def test_warning_extraction_does_not_promote_spectre_notices(tmp_path: Path) -> None:
    module = load_module()
    (tmp_path / "spectre.out").write_text(
        "\n".join(
            [
                "Notice from spectre.",
                "Notice from spectre during topology check.",
                "Warning from spectre during AHDL read-in.",
                "    WARNING (VACOMP-2435): environment setting is obsolete.",
            ]
        )
        + "\n"
    )

    warnings = module.extract_warning_lines(tmp_path, {})

    assert "Notice from spectre." not in warnings
    assert "Notice from spectre during topology check." not in warnings
    assert "Warning from spectre during AHDL read-in." not in warnings
    assert "WARNING (VACOMP-2435): environment setting is obsolete." in warnings


def test_only_evas_profile_sfe_105_is_benign() -> None:
    module = load_module()
    expected = (
        "WARNING (SFE-105): deck.scs 12: `evas_profile' has been ignored because it is not an "
        "option. Correct the name and rerun the simulation."
    )

    assert module.is_benign_warning(expected) is True
    assert module.is_benign_warning(
        "WARNING (SFE-105): deck.scs 12: `reltol' has been ignored because it is not an option."
    ) is False


def test_side_effect_exclusivity_ignores_only_spectre_owned_log(tmp_path: Path) -> None:
    module = load_module()
    output = tmp_path / "output"
    output.mkdir()
    trace = output / "tran_spectre.csv"
    trace.write_text("time,out\n0,0\n1e-9,1\n")
    (output / "metric.out").write_text("ok\n")
    (output / "spectre.out").write_text("Spectre log\n")
    profile = {
        "side_effect_contract": {
            "exclusive_suffix": ".out",
            "files": [
                {
                    "path": "metric.out",
                    "validator": "regex",
                    "record_pattern": "ok\\n",
                }
            ],
        }
    }

    ok, notes = module.validate_spectre_side_effect_contract(profile, trace, output)

    assert ok is True
    assert not any("side_effect_unexpected_files" in note for note in notes)

    (output / "candidate-extra.out").write_text("unexpected\n")
    ok, notes = module.validate_spectre_side_effect_contract(profile, trace, output)

    assert ok is False
    assert "side_effect_unexpected_files=candidate-extra.out" in notes


def test_cached_evidence_is_rederived_from_raw_spectre_outputs(tmp_path: Path) -> None:
    module = load_module()
    entry = tmp_path / "cache-entry"
    output = entry / "spectre"
    output.mkdir(parents=True)
    (output / "tran_spectre.csv").write_text("time,out\n0,0\n1e-9,1\n")
    (output / "metric.out").write_text("ok\n")
    (output / "spectre.out").write_text(
        "Notice from spectre.\n"
        "WARNING (VACOMP-2435): environment setting is obsolete.\n"
    )
    write_json(output / "spectre_result.json", {"warnings": []})
    profile = {
        "side_effect_contract": {
            "exclusive_suffix": ".out",
            "files": [
                {
                    "path": "metric.out",
                    "validator": "regex",
                    "record_pattern": "ok\\n",
                }
            ],
        }
    }
    row = {
        "status": "PASS_WITH_WARNINGS",
        "behavior": {"score": 1.0},
        "spectre": {
            "warnings": ["Notice from spectre."],
            "benign_warnings": [],
            "untriaged_warnings": ["Notice from spectre."],
        },
        "side_effect": {},
        "cache": {"notes": []},
    }

    module.refresh_cached_derived_evidence(
        row,
        checker_profile=profile,
        side_output_files=("metric.out",),
        local_entry=entry,
    )

    assert row["status"] == "PASS"
    assert row["spectre"]["warnings"] == [
        "WARNING (VACOMP-2435): environment setting is obsolete."
    ]
    assert row["spectre"]["untriaged_warnings"] == []
    assert row["side_effect"]["pass"] is True


def test_materialization_preserves_all_declared_artifact_subdirectories(tmp_path: Path) -> None:
    module = load_module()
    tasks_root = tmp_path / "tasks"
    write_task(module, tasks_root)

    first = module.materialize_case(
        numbering_row(),
        tasks_root=tasks_root,
        case_dir=tmp_path / "case-a",
        toolchain_sha256="f" * 64,
    )
    second = module.materialize_case(
        numbering_row(),
        tasks_root=tasks_root,
        case_dir=tmp_path / "case-b",
        toolchain_sha256="f" * 64,
    )

    assert (first.case_dir / "dut" / "top.va").is_file()
    assert (first.case_dir / "dut" / "blocks" / "leaf.va").is_file()
    assert (first.case_dir / "support" / "helper.va").is_file()
    assert [item["path"] for item in first.hashes["gold_artifacts"]] == [
        "top.va",
        "blocks/leaf.va",
    ]
    assert first.hashes == second.hashes
    deck = first.deck_path.read_text(encoding="utf-8")
    assert 'ahdl_include "./dut/top.va"' in deck
    assert 'ahdl_include "./dut/blocks/leaf.va"' in deck
    assert 'ahdl_include "./support/helper.va"' in deck
    assert "VSCORE marker" in deck
    assert first.side_output_files == ("metric.out",)


def test_execute_dry_run_materializes_and_writes_evidence_without_network(tmp_path: Path) -> None:
    module = load_module()
    tasks_root = tmp_path / "tasks"
    write_task(module, tasks_root)
    plan = tmp_path / "numbering_plan.json"
    lock = tmp_path / "TOOLCHAIN_LOCK.json"
    evidence = tmp_path / "evidence.json"
    write_numbering_plan(plan)
    write_toolchain_lock(module, lock)

    def network_must_not_run(**_kwargs):
        raise AssertionError("dry-run attempted to call Spectre")

    payload = module.execute(
        first_n=1,
        numbering_plan_path=plan,
        tasks_root=tasks_root,
        toolchain_lock_path=lock,
        evidence_output=evidence,
        host="thu-wei",
        mode="ax",
        timeout_s=30,
        case_root=tmp_path / "cases",
        keep_case_dirs=True,
        dry_run=True,
        fail_fast=False,
        sui_work_root=None,
        runner=network_must_not_run,
    )

    assert payload["status"] == "dry_run_materialized"
    assert payload["summary"]["materialized_rows"] == 1
    assert payload["rows"][0]["status"] == "DRY_RUN"
    assert payload["rows"][0]["spectre"]["ran"] is False
    assert payload["rows"][0]["hashes"]["toolchain_lock_sha256"] == sha256(lock)
    assert json.loads(evidence.read_text(encoding="utf-8")) == payload
    assert (tmp_path / "cases" / "001-010-demo-source" / "dut" / "blocks" / "leaf.va").is_file()
    schema = json.loads(
        (ROOT / "schemas" / "first_n_spectre_evidence.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(payload)


def test_toolchain_host_must_match_requested_host(tmp_path: Path) -> None:
    module = load_module()
    lock = tmp_path / "TOOLCHAIN_LOCK.json"
    write_toolchain_lock(module, lock)

    with pytest.raises(module.SidecarError, match="toolchain host mismatch"):
        module.load_toolchain(lock, "thu-sui")


def test_execute_uses_runner_checker_and_side_effect_contract_without_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_module()
    tasks_root = tmp_path / "tasks"
    write_task(module, tasks_root)
    plan = tmp_path / "numbering_plan.json"
    lock = tmp_path / "TOOLCHAIN_LOCK.json"
    evidence = tmp_path / "evidence.json"
    write_numbering_plan(plan)
    write_toolchain_lock(module, lock)
    observed: dict = {}

    def fake_runner(**kwargs):
        observed.update(kwargs)
        output_dir = Path(kwargs["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "tran_spectre.csv").write_text("time,out\n0,0\n1e-9,1\n")
        (output_dir / "metric.out").write_text("ok\n")
        return {
            "ok": True,
            "rows": 2,
            "signals": ["time", "out"],
            "errors": [],
            "warnings": [],
            "remote_run_dir": "/remote/fixture",
            "timing": {"tran_elapsed_s": 0.01},
        }

    monkeypatch.setattr(
        module,
        "evaluate_behavior_with_timeout",
        lambda *_args, **_kwargs: (1.0, ["fixture checker pass"]),
    )
    payload = module.execute(
        first_n=1,
        numbering_plan_path=plan,
        tasks_root=tasks_root,
        toolchain_lock_path=lock,
        evidence_output=evidence,
        host="thu-wei",
        mode="ax",
        timeout_s=30,
        case_root=tmp_path / "cases",
        keep_case_dirs=True,
        dry_run=False,
        fail_fast=False,
        sui_work_root=None,
        runner=fake_runner,
        identity_probe=lambda lock, *, host, mode: module._identity(
            lock, host=host, mode=mode, verification="remote_probe_match"
        ),
    )

    assert observed["spectre_backend"] == "sui-direct"
    assert observed["sui_host"] == "thu-wei"
    assert observed["side_output_files"] == ("metric.out",)
    assert [path.relative_to(observed["tb_path"].parent).as_posix() for path in observed["include_paths"]] == [
        "dut/top.va",
        "dut/blocks/leaf.va",
        "support/helper.va",
    ]
    assert payload["status"] == "pass"
    assert payload["rows"][0]["behavior"]["score"] == 1.0
    assert payload["rows"][0]["side_effect"]["pass"] is True
    schema = json.loads(
        (ROOT / "schemas" / "first_n_spectre_evidence.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(payload)


def test_cache_key_covers_every_reusable_result_input(tmp_path: Path) -> None:
    module = load_module()
    tasks_root = tmp_path / "tasks"
    write_task(module, tasks_root)
    case = module.materialize_case(
        numbering_row(),
        tasks_root=tasks_root,
        case_dir=tmp_path / "case",
        toolchain_sha256="a" * 64,
    )
    baseline = module.cache_key(case, mode="ax")

    cache_to_hash = {
        "deck_sha256": "deck_sha256",
        "candidate_bundle_sha256": "gold_bundle_sha256",
        "public_support_bundle_sha256": "public_support_bundle_sha256",
        "harness_spec_sha256": "harness_spec_sha256",
        "profile_sha256": "score_profile_sha256",
        "backend_sha256": "spectre_sha256",
    }
    for cache_field, hash_field in cache_to_hash.items():
        assert cache_field in module.cache_inputs(case, mode="ax")
        changed = replace(case, hashes={**case.hashes, hash_field: "f" * 64})
        assert module.cache_key(changed, mode="ax") != baseline
    assert module.cache_key(case, mode="cx") != baseline


def test_spectre_simulation_cache_key_ignores_oracle_and_release_snapshot_changes(
    tmp_path: Path,
) -> None:
    module = load_module()
    tasks_root = tmp_path / "tasks"
    write_task(module, tasks_root)
    case = module.materialize_case(
        numbering_row(),
        tasks_root=tasks_root,
        case_dir=tmp_path / "case",
        toolchain_sha256="a" * 64,
    )
    case = replace(
        case,
        hashes={**case.hashes, "spectre_backend_sha256": "b" * 64},
    )
    baseline = module.cache_key(case, mode="ax")

    unrelated = replace(
        case,
        hashes={
            **case.hashes,
            "toolchain_lock_sha256": "c" * 64,
            "checker_sha256": "d" * 64,
            "checker_profile_sha256": "e" * 64,
            "checker_registry_sha256": "f" * 64,
        },
    )
    assert module.cache_key(unrelated, mode="ax") == baseline

    backend_changed = replace(
        case,
        hashes={**case.hashes, "spectre_backend_sha256": "0" * 64},
    )
    assert module.cache_key(backend_changed, mode="ax") != baseline


def write_legacy_spectre_cache_entry(
    module,
    case,
    entry: Path,
    *,
    mode: str = "ax",
    input_overrides: dict[str, str] | None = None,
    created_at: str = "2026-07-10T01:00:00+00:00",
    historical_v1_inputs: bool = False,
) -> None:
    identity = {
        "backend": "sui-direct",
        "mode": mode,
        "host": "thu-wei",
        "route": "proxyjump=thu-jin",
        "path": "/opt/cadence/bin/spectre",
        "version": "sub-version fixture",
        "cadence_cshrc": "/home/cshrc/.cshrc.cadence.IC618SP201",
        "transport_identity": "sui-direct:ssh:thu-wei:proxyjump=thu-jin",
        "verification": "remote_probe_match",
    }
    shutil_source = case.case_dir
    entry.parent.mkdir(parents=True, exist_ok=True)
    if entry.exists():
        shutil.rmtree(entry)
    shutil.copytree(shutil_source, entry)
    output = entry / "spectre"
    output.mkdir(parents=True, exist_ok=True)
    (output / "tran_spectre.csv").write_text("time,out\n0,0\n1e-9,1\n")
    (output / "metric.out").write_text("ok\n")
    row = module._base_record(case, identity, retained=True)
    row["status"] = "PASS"
    row["spectre"] = {
        "ran": True,
        "ok": True,
        "rows": 2,
        "signals": ["time", "out"],
        "errors": [],
        "warnings": [],
        "benign_warnings": [],
        "untriaged_warnings": [],
        "remote_run_dir": "/remote/legacy",
        "timing": {"tran_elapsed_s": 0.01},
        "wall_time_s": 0.02,
    }
    row["behavior"] = {"ran": True, "score": 0.0, "notes": ["legacy checker failed"]}
    row["side_effect"] = {
        "required": True,
        "expected_files": ["metric.out"],
        "ran": True,
        "pass": True,
        "notes": [],
    }
    inputs = module.cache_inputs(case, mode=mode)
    if historical_v1_inputs:
        inputs = {
            "task_id": inputs["task_id"],
            "profile": inputs["profile"],
            "deck_sha256": inputs["deck_sha256"],
            "gold_bundle_sha256": inputs["candidate_bundle_sha256"],
            "public_support_bundle_sha256": inputs["public_support_bundle_sha256"],
            "harness_spec_sha256": inputs["harness_spec_sha256"],
            "score_profile_sha256": inputs["profile_sha256"],
            "spectre_mode": inputs["spectre_mode"],
        }
    inputs.update(input_overrides or {})
    inputs["checker_sha256"] = "legacy-checker-only-field"
    row["cache"] = {
        "key": entry.name,
        "profile": "score",
        "inputs": inputs,
        "hit": False,
        "source": "none",
        "cacheable": True,
        "local_entry": str(entry),
        "remote_entry": "",
        "notes": [],
    }
    write_json(entry / "row_evidence.json", row)
    write_json(
        entry / "cache_manifest.json",
        {
            "schema_version": "legacy-v4-spectre-cache-entry-with-checker-v1",
            "cache_key": entry.name,
            "created_at": created_at,
            "canonical_id": case.canonical_id,
            "task_id": case.task_id,
            "profile": "score",
            "inputs": inputs,
            "row_status": "PASS",
        },
    )


def test_legacy_cache_migration_reuses_raw_trace_after_checker_only_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_module()
    tasks_root = tmp_path / "tasks"
    write_task(module, tasks_root)
    case = module.materialize_case(
        numbering_row(),
        tasks_root=tasks_root,
        case_dir=tmp_path / "case",
        toolchain_sha256="a" * 64,
        backend_hashes={"spectre_sha256": "b" * 64},
    )
    current = replace(case, hashes={**case.hashes, "checker_sha256": "c" * 64})
    key = module.cache_key(current, mode="ax")
    legacy_root = tmp_path / "legacy"
    legacy_entry = legacy_root / "001" / "score" / ("1" * 64)
    local_entry = tmp_path / "cache" / "001" / "score" / key
    write_legacy_spectre_cache_entry(
        module, case, legacy_entry, historical_v1_inputs=True
    )
    monkeypatch.setattr(
        module,
        "evaluate_behavior_with_timeout",
        lambda *_args, **_kwargs: (1.0, ["current checker pass"]),
    )

    migrated = module.migrate_legacy_local_cache(
        current,
        mode="ax",
        key=key,
        legacy_root=legacy_root,
        local_entry=local_entry,
    )
    record = module.load_local_cache(
        current,
        mode="ax",
        key=key,
        local_entry=local_entry,
        remote_root="",
        source="local",
        timeout_s=30,
    )

    assert migrated is True
    assert record is not None
    assert record["status"] == "PASS"
    assert record["behavior"]["notes"] == ["current checker pass"]
    assert record["cache"]["hit"] is True
    assert any("migrated_from_legacy_cache" in note for note in record["cache"]["notes"])
    manifest = json.loads((local_entry / "cache_manifest.json").read_text(encoding="utf-8"))
    assert manifest["cache_key"] == key
    assert manifest["migrated_from"]["cache_key"] == "1" * 64


@pytest.mark.parametrize(
    "field,hash_field",
    [
        ("deck_sha256", "deck_sha256"),
        ("candidate_bundle_sha256", "gold_bundle_sha256"),
        ("backend_sha256", "spectre_sha256"),
    ],
)
def test_legacy_cache_migration_rejects_simulation_input_mismatch(
    tmp_path: Path, field: str, hash_field: str
) -> None:
    module = load_module()
    tasks_root = tmp_path / "tasks"
    write_task(module, tasks_root)
    case = module.materialize_case(
        numbering_row(),
        tasks_root=tasks_root,
        case_dir=tmp_path / f"case-{field}",
        toolchain_sha256="a" * 64,
        backend_hashes={"spectre_sha256": "b" * 64},
    )
    key = module.cache_key(case, mode="ax")
    legacy_root = tmp_path / f"legacy-{field}"
    legacy_entry = legacy_root / "001" / "score" / ("2" * 64)
    local_entry = tmp_path / f"cache-{field}" / "001" / "score" / key
    write_legacy_spectre_cache_entry(
        module,
        case,
        legacy_entry,
        input_overrides={field: "f" * 64},
    )

    migrated = module.migrate_legacy_local_cache(
        case,
        mode="ax",
        key=key,
        legacy_root=legacy_root,
        local_entry=local_entry,
    )

    assert migrated is False
    assert not local_entry.exists()
    assert module.cache_inputs(case, mode="ax")[field] == case.hashes[hash_field]


def test_release_snapshot_does_not_freeze_current_benchmark_code() -> None:
    module = load_module()
    module._verify_locked_components(
        {
            "benchmark": {
                "checker_registry_sha256": "1" * 64,
                "harness_generator_sha256": "2" * 64,
                "oracle_runner_sha256": "3" * 64,
            }
        }
    )


def test_execute_reuses_valid_local_cache_without_running_spectre(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_module()
    tasks_root = tmp_path / "tasks"
    write_task(module, tasks_root)
    plan = tmp_path / "numbering_plan.json"
    lock = tmp_path / "TOOLCHAIN_LOCK.json"
    write_numbering_plan(plan)
    write_toolchain_lock(module, lock)
    cache_root = tmp_path / "cache"

    def fake_runner(**kwargs):
        output_dir = Path(kwargs["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "tran_spectre.csv").write_text("time,out\n0,0\n1e-9,1\n")
        (output_dir / "metric.out").write_text("ok\n")
        return {
            "ok": True,
            "rows": 2,
            "signals": ["time", "out"],
            "errors": [],
            "warnings": [],
            "remote_run_dir": "/remote/fixture",
            "timing": {"tran_elapsed_s": 0.01},
        }

    monkeypatch.setattr(
        module,
        "evaluate_behavior_with_timeout",
        lambda *_args, **_kwargs: (1.0, ["fixture checker pass"]),
    )
    common = {
        "first_n": 1,
        "numbering_plan_path": plan,
        "tasks_root": tasks_root,
        "toolchain_lock_path": lock,
        "host": "thu-wei",
        "mode": "ax",
        "timeout_s": 30,
        "keep_case_dirs": False,
        "dry_run": False,
        "fail_fast": False,
        "sui_work_root": None,
        "cache_enabled": True,
        "local_cache_root": cache_root,
        "identity_probe": lambda lock, *, host, mode: module._identity(
            lock, host=host, mode=mode, verification="remote_probe_match"
        ),
    }
    first = module.execute(
        **common,
        evidence_output=tmp_path / "first.json",
        case_root=tmp_path / "cases-first",
        runner=fake_runner,
    )
    assert first["summary"]["executed_rows"] == 1
    assert first["summary"]["cache_hit_rows"] == 0

    second = module.execute(
        **common,
        evidence_output=tmp_path / "second.json",
        case_root=tmp_path / "cases-second",
        runner=lambda **_kwargs: pytest.fail("cache hit attempted Spectre execution"),
    )
    assert second["summary"]["executed_rows"] == 0
    assert second["summary"]["cache_hit_rows"] == 1
    assert second["rows"][0]["cache"]["source"] == "local"


def test_dry_run_records_materialization_failure_as_schema_valid_evidence(tmp_path: Path) -> None:
    module = load_module()
    tasks_root = tmp_path / "tasks"
    task_dir = write_task(module, tasks_root)
    plan = tmp_path / "numbering_plan.json"
    lock = tmp_path / "TOOLCHAIN_LOCK.json"
    evidence = tmp_path / "evidence.json"
    write_numbering_plan(plan)
    write_toolchain_lock(module, lock)
    profile_path = task_dir / "evaluator" / "profiles" / "score.json"
    stale = json.loads(profile_path.read_text(encoding="utf-8"))
    stale["deterministic_seed"] = 99
    write_json(profile_path, stale)

    payload = module.execute(
        first_n=1,
        numbering_plan_path=plan,
        tasks_root=tasks_root,
        toolchain_lock_path=lock,
        evidence_output=evidence,
        host="thu-wei",
        mode="ax",
        timeout_s=30,
        case_root=tmp_path / "cases",
        keep_case_dirs=False,
        dry_run=True,
        fail_fast=False,
        sui_work_root=None,
        runner=lambda **_kwargs: pytest.fail("dry-run attempted network runner"),
    )

    assert payload["status"] == "fail"
    assert payload["rows"][0]["status"] == "FAIL_RUNNER"
    assert "stored score profile is stale" in payload["rows"][0]["materialization"]["notes"][0]
    schema = json.loads(
        (ROOT / "schemas" / "first_n_spectre_evidence.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(payload)
