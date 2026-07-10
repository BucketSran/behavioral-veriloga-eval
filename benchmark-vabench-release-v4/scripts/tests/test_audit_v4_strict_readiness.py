from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "audit_v4_strict_readiness.py"
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from evidence_fingerprints import evidence_components  # noqa: E402


def load_module():
    spec = importlib.util.spec_from_file_location("audit_v4_strict_readiness", MODULE_PATH)
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


def bundle_hash(root: Path, rels: list[str]) -> str:
    digest = hashlib.sha256()
    for rel in sorted(rels):
        digest.update(rel.encode())
        digest.update(b"\0")
        digest.update(sha256(root / rel).encode())
        digest.update(b"\0")
    return digest.hexdigest()


def test_public_interface_fragments_are_not_gold_leaks() -> None:
    module = load_module()
    family = {
        "artifact_contract": {
            "files": [
                {
                    "modules": [
                        {
                            "name": "top",
                            "role": "entry",
                            "ports": [{"name": name} for name in ["clk", "rst", "vin", "vout"]],
                        }
                    ]
                }
            ]
        }
    }

    assert module.public_entry_module_declaration("module top(clk, rst, vin, vout);", family)
    assert module.public_entry_module_declaration("rst, vin, vout", family)
    assert not module.public_entry_module_declaration("vin = vin + 1.0;", family)


def write_toolchain(root: Path) -> None:
    write_json(
        root / "TOOLCHAIN_LOCK.json",
        {
            "schema_version": "v4-toolchain-lock-v1",
            "generated_at": "2026-07-10T00:00:00+00:00",
            "status": "valid",
            "evas": {
                "distribution": "evas-sim",
                "implementation_track": "python-rust-hybrid",
                "frontend": "python",
                "runtime": "rust",
                "source_package_version": "0.8.1",
                "runtime_metadata_version": "0.8.1",
                "release_tag": "v0.8.1",
                "git_commit": "e552d152f6be970610dcc58cd27b04b7e53b892f",
                "git_describe": "v0.8.1",
                "dirty": False,
                "release_relation": "exact_release_tag",
                "module_path": "/tmp/evas/__init__.py",
                "requested_engine": "evas-rust",
                "actual_engine": "evas-rust",
                "allow_python_fallback": False,
                "profile": "balanced",
                "rust_core_abi": 20260706,
                "build_sha256": "a" * 64,
                "ahdl_like": {
                    "ruleset_id": "evas-ahdl-like-v0.8.1",
                    "ruleset_sha256": "b" * 64,
                    "spectre_strict": True,
                    "minimum_transition_s": 1e-12,
                },
                "smoke": {
                    "status": "pass",
                    "log_sha256": "c" * 64,
                    "observed_engine": "evas-rust",
                    "observed_profile": "balanced",
                    "python_fallback_observed": False,
                },
            },
            "spectre": {
                "backend": "sui-direct",
                "remote_host": "thu-wei",
                "route": "proxyjump=thu-jin",
                "path": "/cadence/spectre",
                "version": "sub-version fixture",
                "cadence_cshrc": "/home/cadence.cshrc",
                "transport_identity": "sui-direct:ssh:thu-wei:proxyjump=thu-jin",
            },
            "benchmark": {
                "git_commit": "d" * 40,
                "dirty": False,
                "checker_registry_sha256": "e" * 64,
                "harness_generator_sha256": "f" * 64,
                "oracle_runner_sha256": "1" * 64,
                "schema_set_sha256": "2" * 64,
            },
            "runtime": {
                "python_version": "3.12.0",
                "python_executable": "/usr/bin/python3",
                "platform": "fixture",
                "architecture": "arm64",
            },
        },
    )


def write_numbering(root: Path) -> Path:
    path = root / "reports" / "v4_task_family_numbering" / "numbering_plan.json"
    write_json(
        path,
        {
            "schema_version": "v4-task-family-numbering-plan-v1",
            "rows": [
                {
                    "canonical_index": 1,
                    "canonical_dut_id": "001",
                    "canonical_dut_slug": "001-demo",
                    "canonical_testbench_id": "501",
                    "canonical_testbench_slug": "501-demo-testbench",
                    "canonical_bugfix_id": "1001",
                    "canonical_bugfix_slug": "1001-demo-bugfix",
                    "old_dut_slug": "010-demo-source",
                    "category": "demo",
                    "level": "L1",
                    "target_artifacts": ["dut.va"],
                    "source_task_id": "fixture_demo",
                    "title": "Demo",
                }
            ],
        },
    )
    return path


def write_family(task: Path) -> None:
    write_json(
        task / "family_spec.json",
        {
            "schema_version": "v4-family-spec-v1",
            "family_id": "001",
            "task_ids": {"dut": "v4-001", "testbench": "v4-501", "bugfix": "v4-1001"},
            "identity": {
                "title": "Demo",
                "category": "demo",
                "level": "L1",
                "difficulty": "D1",
                "supported_scope": "voltage-domain transient",
            },
            "artifact_contract": {
                "mode": "single_file",
                "files": [
                    {
                        "path": "dut.va",
                        "modules": [
                            {
                                "name": "dut",
                                "role": "entry",
                                "depends_on": [],
                                "ports": [],
                                "parameters": [],
                            }
                        ],
                    }
                ],
            },
            "testbench_binding": {
                "dut_source_root": "dut",
                "source_path_template": "./dut/{artifact_path}",
                "instances": [
                    {
                        "name": "XDUT",
                        "module_ref": "dut",
                        "connections": [
                            {"port_ref": "in", "net": "in", "position": 0},
                            {"port_ref": "out", "net": "out", "position": 1},
                        ],
                    }
                ],
            },
            "properties": [
                {
                    "id": "P_GAIN",
                    "observable_contract": "gain is correct",
                    "required_signals": ["time", "in", "out"],
                },
                {
                    "id": "P_BUS",
                    "observable_contract": "bus code is correct",
                    "required_signals": ["time", "code[0]", "code[1]"],
                },
                {
                    "id": "P_RESET",
                    "observable_contract": "reset clears output",
                    "required_signals": ["time", "rst", "out"],
                },
            ],
            "trace_contract": {"required_signals": ["time", "in", "out", "code[0]", "code[1]", "rst"]},
            "modeling_constraints": ["Use deterministic behavior."],
        },
    )


def write_gate2_artifacts(task: Path) -> None:
    (task / "instruction.md").write_text(
        "Create the requested Verilog-A module. It may be evaluated with a public testbench.\n",
        encoding="utf-8",
    )
    write_json(
        task / "public_contract.json",
        {
            "schema_version": "v4-public-contract-v1",
            "task_id": "v4_001_demo",
            "task_slug": "010-demo-source",
            "title": "Demo",
            "category": "demo",
            "level": "L1",
            "form": "dut",
            "language": "verilog-a",
            "source_task_id": "fixture_demo",
            "target_artifacts": ["dut.va"],
            "public_observables": ["in", "out", "code0", "code1", "rst"],
            "agent_visible_files": ["instruction.md", "public_contract.json", "test_feedback/run_feedback.py"],
            "canonical_instruction": "instruction.md",
            "status": "gate2_semantic_validated_candidate",
            "gate2_status": "cadence_modeling_ready_candidate",
            "feedback_oracle": {},
            "score_oracle": {},
            "oracle_policy": {},
            "validation_status": {
                "spectre_score_deck": "PASS",
                "untriaged_warning_count": 0,
            },
        },
    )
    checker_path = task / "evaluator" / "checker_profile.json"
    write_json(
        checker_path,
        {
            "schema_version": "v4-checker-profile-v1",
            "access": "private_checker_backend",
            "checker_source_public": False,
            "checker_task_id": "v4_001_demo",
            "contract": {
                "public_contract": "public_contract.json",
                "source_task_id": "fixture_demo",
                "task_id": "v4_001_demo",
            },
            "score_and_feedback_share_checker": True,
            "shared_by": ["test_feedback/public_tb.scs", "evaluator/score_tb.scs"],
            "trace_contract": {"extra_trace_signals": [], "public_observables": ["in", "out", "code0", "code1", "rst"]},
        },
    )
    family_hash = sha256(task / "family_spec.json")
    checker_hash = sha256(checker_path)
    harness = {
        "schema_version": "v4-harness-spec-v1",
        "family_id": "001",
        "task_id": "v4-001",
        "generator": {"name": "render_v4_harness.py", "version": "v4-harness-renderer-v1"},
        "source_contract": {
            "family_spec_sha256": family_hash,
            "checker_profile_sha256": checker_hash,
        },
        "candidate": {"source_root": "./dut", "artifact_paths": ["dut.va"]},
        "deck": {
            "header": ["simulator lang=spectre"],
            "include_templates": ['ahdl_include "{candidate_source_root}/{artifact_path}"'],
            "body_lines": ["XDUT (in out code0 code1 rst) dut"],
            "analyses": ["tran tran stop={stop_time}"],
            "save_signals": ["time", "in", "out", "code[1:0]", "rst"],
        },
        "property_ids": ["P_GAIN", "P_BUS", "P_RESET"],
        "profile_defaults": {
            "feedback": {
                "parameters": {"stop_time": "10n"},
                "simulatorOptions": {"evas_profile": "balanced"},
            },
            "score": {"parameters": {"stop_time": "20n"}, "simulatorOptions": {}},
        },
    }
    harness_path = task / "evaluator" / "harness_spec.json"
    write_json(harness_path, harness)
    harness_hash = sha256(harness_path)
    for profile_name, public_visible in (("feedback", True), ("score", False)):
        write_json(
            task / "evaluator" / "profiles" / f"{profile_name}.json",
            {
                "schema_version": "v4-harness-profile-v1",
                "profile_name": profile_name,
                "harness_spec_sha256": harness_hash,
                "generated_from": {"script": "render_v4_harness.py", "version": "v4-harness-renderer-v1"},
                "property_ids": ["P_GAIN", "P_BUS", "P_RESET"],
                "parameters": {"stop_time": "10n" if profile_name == "feedback" else "20n"},
                "corners": [],
                "deterministic_seed": 0,
                "simulatorOptions": {"evas_profile": "balanced"} if profile_name == "feedback" else {},
                "public_visible": public_visible,
            },
        )
    (task / "solution").mkdir(parents=True)
    (task / "solution" / "dut.va").write_text("module dut(in,out); input in; output out; endmodule\n", encoding="utf-8")


def write_mutations(root: Path, task: Path) -> None:
    artifacts = ["dut.va"]
    props = ["P_GAIN", "P_BUS", "P_RESET", "P_GAIN", "P_BUS"]
    partitions = ["B", "P", "H", "H", "H"]
    mutations = []
    partition = {"bugfix_seed": [], "testbench_public_feedback": [], "testbench_private_score": []}
    toolchain_hash = sha256(root / "TOOLCHAIN_LOCK.json")
    checker_hash = sha256(task / "evaluator" / "checker_profile.json")
    harness_hash = sha256(task / "evaluator" / "harness_spec.json")
    profile_hash = sha256(task / "evaluator" / "profiles" / "feedback.json")
    gold_hash = bundle_hash(task / "solution", artifacts)
    for index, (prop, part) in enumerate(zip(props, partitions), start=1):
        mutation_id = f"neg_{index:03d}_demo"
        mut_dir = task / "negative_variants" / mutation_id
        mut_dir.mkdir(parents=True)
        (mut_dir / "dut.va").write_text(
            f"module dut(in,out); input in; output out; // mutation {index}\nendmodule\n",
            encoding="utf-8",
        )
        if part == "B":
            partition["bugfix_seed"].append(mutation_id)
        elif part == "P":
            partition["testbench_public_feedback"].append(mutation_id)
        else:
            partition["testbench_private_score"].append(mutation_id)
        write_json(
            mut_dir / "certification.json",
            {
                "schema_version": "v4-negative-certification-v1",
                "family_id": "001",
                "mutation_id": mutation_id,
                "toolchain_lock_sha256": toolchain_hash,
                "inputs": {
                    "mutation_bundle_sha256": bundle_hash(mut_dir, artifacts),
                    "checker_profile_sha256": checker_hash,
                    "harness_spec_sha256": harness_hash,
                    "profile_sha256": profile_hash,
                },
                "evaluators": {
                    "ahdl_like": "pass",
                    "evas": "compile_pass_behavior_fail",
                    "spectre": "compile_pass_behavior_fail",
                },
                "outcome": "killed_behaviorally",
                "diagnostics": {
                    "violated_property_ids": [prop],
                    "expected": "gold behavior",
                    "observed": "mutated behavior",
                    "mismatch_count": 1,
                },
            },
        )
        mutations.append(
            {
                "id": mutation_id,
                "fault_class": f"fault_{(index % 3) + 1}",
                "trigger_condition": "stimulus reaches condition",
                "violated_property_ids": [prop],
                "changed_artifacts": artifacts,
                "artifact_hashes": {"dut.va": sha256(mut_dir / "dut.va")},
                "certification": {
                    "status": "pass",
                    "profile": "feedback",
                    "compile_status": "pass",
                    "simulation_status": "pass",
                    "behavior_status": "killed_behaviorally",
                    "activated_property_ids": [prop],
                    "evidence_path": f"negative_variants/{mutation_id}/certification.json",
                },
            }
        )
    catalog = {
        "schema_version": "v4-mutation-catalog-v1",
        "family_id": "001",
        "gold_bundle_sha256": gold_hash,
        "mutations": mutations,
    }
    write_json(task / "negative_variants" / "manifest.json", catalog)
    write_json(
        task / "evaluator" / "derivation_manifest.json",
        {
            "schema_version": "v4-derivation-manifest-v1",
            "family_id": "001",
            "mutation_catalog_sha256": sha256(task / "negative_variants" / "manifest.json"),
            "mutation_partition": partition,
        },
    )


def write_evidence(root: Path, numbering: Path, *, status: str = "PASS", toolchain_hash: str | None = None) -> None:
    task = root / "tasks" / "010-demo-source"
    toolchain_hash = toolchain_hash or sha256(root / "TOOLCHAIN_LOCK.json")
    audit = load_module()
    checker = json.loads((task / "evaluator" / "checker_profile.json").read_text(encoding="utf-8"))
    checker_task_id = str(checker["checker_task_id"])
    oracle = audit.checker_fingerprints(
        checker_task_id,
        checker,
        audit.CHECKS.get(checker_task_id),
    )
    oracle["oracle_runner_sha256"] = audit.benchmark_component_hashes()[
        "oracle_runner_sha256"
    ]
    backend = audit.backend_fingerprints(
        json.loads((root / "TOOLCHAIN_LOCK.json").read_text(encoding="utf-8")),
        spectre_mode="reference",
    )
    components = evidence_components(
        task_inputs={},
        oracle=oracle,
        backend=backend,
        release_snapshot_sha256=toolchain_hash,
    )
    harness = json.loads(
        (task / "evaluator" / "harness_spec.json").read_text(encoding="utf-8")
    )
    score_profile = json.loads(
        (task / "evaluator" / "profiles" / "score.json").read_text(encoding="utf-8")
    )
    deck_sha256 = hashlib.sha256(
        audit.render_scs(harness, score_profile).encode("utf-8")
    ).hexdigest()
    write_json(
        root / "reports" / "tri_form_first120" / "local_evas_evidence.json",
        {
            "generated_at": "2026-07-10T00:00:00+00:00",
            "records": [
                {
                    "family_id": "001",
                    "slug": "010-demo-source",
                    "profile": profile,
                    "status": "pass",
                    "returncode": 0,
                    "diagnostics": f"{profile.upper()}_PASS",
                    "timed_out": False,
                    "duration_s": 1.0,
                }
                for profile in ("feedback", "score")
            ],
        },
    )
    write_json(
        root / "reports" / "first_n_spectre" / "first1.json",
        {
            "schema_version": "v4-first-n-spectre-evidence-v2",
            "evidence_policy": "v4-dependency-scoped-evidence-v2",
            "generated_at": "2026-07-10T00:00:00+00:00",
            "status": "pass" if status == "PASS" else "partial_failure",
            "dry_run": False,
            "numbering_plan": {
                "path": str(numbering),
                "sha256": sha256(numbering),
                "schema_version": "v4-task-family-numbering-plan-v1",
                "selection_mode": "first_n",
                "requested_first_n": 1,
                "requested_task_ids": [],
                "selected_rows": 1,
            },
            "toolchain_lock": {
                "path": str(root / "TOOLCHAIN_LOCK.json"),
                "sha256": toolchain_hash,
                "schema_version": "v4-toolchain-lock-v1",
                "status": "valid",
            },
            "execution": {
                "script": "scripts/run_v4_first_n_spectre.py",
                "script_sha256": "3" * 64,
                "runner_api": "runners.run_gold_dual_suite.run_spectre_case",
                "host": "thu-wei",
                "backend": "sui-direct",
                "mode": "reference",
                "route": "proxyjump=thu-jin",
                "timeout_s": 1,
                "sui_work_root": "/tmp",
                "case_root": "/tmp/case",
                "output_path": "/tmp/out.json",
                "keep_case_dirs": False,
                "fail_fast": False,
                "cache_enabled": False,
                "refresh_cache": False,
                "local_cache_root": "/tmp/cache",
                "remote_cache_root": "",
                "started_at": "2026-07-10T00:00:00+00:00",
                "finished_at": "2026-07-10T00:00:01+00:00",
                "argv": ["run"],
            },
            "summary": {
                "requested_rows": 1,
                "selected_rows": 1,
                "materialized_rows": 1,
                "executed_rows": 1,
                "cache_hit_rows": 0,
                "passed_rows": 1 if status == "PASS" else 0,
                "failed_rows": 0 if status == "PASS" else 1,
                "spectre_ok_rows": 1 if status == "PASS" else 0,
                "behavior_pass_rows": 1 if status == "PASS" else 0,
                "side_effect_required_rows": 0,
                "side_effect_pass_rows": 0,
                "warning_count": 0,
                "untriaged_warning_count": 0,
                "total_wall_time_s": 1.0,
                "status_counts": {status: 1},
                "all_pass": status == "PASS",
            },
            "rows": [
                {
                    "canonical_id": "001",
                    "canonical_slug": "001-demo",
                    "source_slug": "010-demo-source",
                    "task_id": "v4-001",
                    "title": "Demo",
                    "category": "demo",
                    "level": "L1",
                    "status": status,
                    "component_fingerprints": components,
                    "materialization": {
                        "status": "complete",
                        "case_dir": "/tmp/case",
                        "retained": False,
                        "deck_path": "/tmp/case/score.scs",
                        "artifact_paths": ["dut.va"],
                        "notes": [],
                    },
                    "hashes": {
                        "deck_sha256": deck_sha256,
                        "harness_spec_sha256": sha256(task / "evaluator" / "harness_spec.json"),
                        "score_profile_sha256": sha256(task / "evaluator" / "profiles" / "score.json"),
                        "family_spec_sha256": sha256(task / "family_spec.json"),
                        "gold_bundle_sha256": bundle_hash(task / "solution", ["dut.va"]),
                        "gold_artifacts": [{"path": "dut.va", "sha256": sha256(task / "solution" / "dut.va")}],
                        "public_support_bundle_sha256": hashlib.sha256(b"").hexdigest(),
                        "public_support_artifacts": [],
                        "checker_sha256": "5" * 64,
                        "checker_profile_sha256": sha256(task / "evaluator" / "checker_profile.json"),
                        "checker_registry_sha256": "6" * 64,
                        "toolchain_lock_sha256": toolchain_hash,
                    },
                    "spectre_identity": {
                        "backend": "sui-direct",
                        "mode": "reference",
                        "host": "thu-wei",
                        "route": "proxyjump=thu-jin",
                        "path": "/cadence/spectre",
                        "version": "sub-version fixture",
                        "cadence_cshrc": "/home/cadence.cshrc",
                        "transport_identity": "sui-direct:ssh:thu-wei:proxyjump=thu-jin",
                        "verification": "remote_probe_match",
                    },
                    "spectre": {
                        "ran": True,
                        "ok": status == "PASS",
                        "rows": 3,
                        "signals": ["time", "in", "out", "code[1:0]", "rst"],
                        "errors": [],
                        "warnings": [],
                        "benign_warnings": [],
                        "untriaged_warnings": [],
                        "remote_run_dir": "/tmp/remote",
                        "timing": {},
                        "wall_time_s": 1.0,
                    },
                    "behavior": {"ran": True, "score": 1.0 if status == "PASS" else 0.0, "notes": []},
                    "side_effect": {"required": False, "expected_files": [], "ran": True, "pass": True, "notes": []},
                    "cache": {
                        "key": "",
                        "profile": "score",
                        "inputs": {},
                        "hit": False,
                        "source": "none",
                        "cacheable": False,
                        "local_entry": "",
                        "remote_entry": "",
                        "notes": [],
                    },
                }
            ],
        },
    )


def write_fixture(root: Path) -> Path:
    write_toolchain(root)
    numbering = write_numbering(root)
    task = root / "tasks" / "010-demo-source"
    write_family(task)
    write_gate2_artifacts(task)
    write_mutations(root, task)
    write_evidence(root, numbering)
    return numbering


def issue_codes(record: dict, gate: str) -> set[str]:
    return {item["code"] for item in record[gate]["issues"]}


def issue_categories(record: dict, gate: str) -> set[str]:
    return {item["category"] for item in record[gate]["issues"]}


def test_ready_fixture_passes_gate2_and_gate3_with_bus_trace_normalization(tmp_path: Path) -> None:
    module = load_module()
    numbering = write_fixture(tmp_path)

    report = module.audit_release(root=tmp_path, numbering_plan_path=numbering, canonical_first=1)

    record = report["records"][0]
    assert record["gate2"]["ready"] is True
    assert record["gate3"]["ready"] is True
    assert "testbench" not in issue_codes(record, "gate2")


def test_spectre_evidence_selection_prefers_current_gold_bundle_over_newer_report(tmp_path: Path) -> None:
    module = load_module()
    numbering = write_fixture(tmp_path)
    current = json.loads((tmp_path / "reports" / "first_n_spectre" / "first1.json").read_text(encoding="utf-8"))
    stale = json.loads(json.dumps(current))
    stale["generated_at"] = "2026-07-11T00:00:00+00:00"
    stale["rows"][0]["hashes"]["gold_bundle_sha256"] = "0" * 64
    stale["rows"][0]["spectre"]["untriaged_warnings"] = ["stale warning"]
    write_json(tmp_path / "reports" / "first_n_spectre" / "newer_stale_gold.json", stale)

    report = module.audit_release(root=tmp_path, numbering_plan_path=numbering, canonical_first=1)

    record = report["records"][0]
    assert record["gate2"]["ready"] is True
    assert "spectre_untriaged_warnings" not in issue_codes(record, "gate2")


def test_release_snapshot_hash_change_does_not_request_spectre_rerun(tmp_path: Path) -> None:
    module = load_module()
    numbering = write_fixture(tmp_path)
    evidence_path = tmp_path / "reports" / "first_n_spectre" / "first1.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence["toolchain_lock"]["sha256"] = "f" * 64
    evidence["rows"][0]["hashes"]["toolchain_lock_sha256"] = "f" * 64
    write_json(evidence_path, evidence)

    report = module.audit_release(root=tmp_path, numbering_plan_path=numbering, canonical_first=1)

    record = report["records"][0]
    assert "spectre_toolchain_hash_stale" not in issue_codes(record, "gate2")
    assert "spectre_toolchain_lock_sha256_mismatch" not in issue_codes(record, "gate2")


def test_spectre_evidence_rejects_stale_rendered_deck(tmp_path: Path) -> None:
    module = load_module()
    numbering = write_fixture(tmp_path)
    evidence_path = tmp_path / "reports" / "first_n_spectre" / "first1.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence["rows"][0]["hashes"]["deck_sha256"] = "0" * 64
    write_json(evidence_path, evidence)

    payload = module.audit_release(
        root=tmp_path, numbering_plan_path=numbering, canonical_first=1
    )
    record = payload["records"][0]

    assert "spectre_deck_sha256_mismatch" in issue_codes(record, "gate2")


def test_numbering_snapshot_change_does_not_hide_task_evidence(tmp_path: Path) -> None:
    module = load_module()
    numbering = write_fixture(tmp_path)
    evidence_path = tmp_path / "reports" / "first_n_spectre" / "first1.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence["numbering_plan"]["sha256"] = "0" * 64
    write_json(evidence_path, evidence)

    report = module.audit_release(root=tmp_path, numbering_plan_path=numbering, canonical_first=1)
    record = report["records"][0]
    assert "spectre_evidence_missing" not in issue_codes(record, "gate2")
    assert record["gate2"]["ready"] is True


def test_legacy_v1_keeps_backend_reusable_but_requires_checker_revalidation(tmp_path: Path) -> None:
    module = load_module()
    numbering = write_fixture(tmp_path)
    evidence_path = tmp_path / "reports" / "first_n_spectre" / "first1.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence["schema_version"] = "v4-first-n-spectre-evidence-v1"
    evidence.pop("evidence_policy")
    evidence["rows"][0].pop("component_fingerprints")
    write_json(evidence_path, evidence)

    report = module.audit_release(root=tmp_path, numbering_plan_path=numbering, canonical_first=1)
    record = report["records"][0]
    assert "spectre_backend_component_stale" not in issue_codes(record, "gate2")
    assert "spectre_checker_component_unproven" in issue_codes(record, "gate2")
    assert record["gate2"]["ready"] is False


def test_public_leak_check_targets_mutation_ids_not_generic_testbench_word(tmp_path: Path) -> None:
    module = load_module()
    numbering = write_fixture(tmp_path)
    instruction = tmp_path / "tasks" / "010-demo-source" / "instruction.md"
    instruction.write_text("The public testbench may be used. Do not copy neg_003_demo behavior.\n", encoding="utf-8")

    report = module.audit_release(root=tmp_path, numbering_plan_path=numbering, canonical_first=1)

    record = report["records"][0]
    assert "public_surface_private_leak" in issue_codes(record, "gate2")
    leak_messages = [item["message"] for item in record["gate2"]["issues"] if item["code"] == "public_surface_private_leak"]
    assert any("mutation_id:neg_003_demo" in message for message in leak_messages)
    assert not any("testbench" in message for message in leak_messages)


def test_missing_evidence_is_separate_from_behavioral_failure(tmp_path: Path) -> None:
    module = load_module()
    numbering = write_fixture(tmp_path)
    (tmp_path / "reports" / "first_n_spectre" / "first1.json").unlink()

    missing_report = module.audit_release(root=tmp_path, numbering_plan_path=numbering, canonical_first=1)
    missing_record = missing_report["records"][0]
    assert "spectre_evidence_missing" in issue_codes(missing_record, "gate2")
    assert "missing_evidence" in issue_categories(missing_record, "gate2")
    assert "behavioral_failure" not in [
        item["category"]
        for item in missing_record["gate2"]["issues"]
        if item["code"] == "spectre_evidence_missing"
    ]

    write_evidence(tmp_path, numbering, status="FAIL_BEHAVIOR")
    failure_report = module.audit_release(root=tmp_path, numbering_plan_path=numbering, canonical_first=1)
    failure_record = failure_report["records"][0]
    assert "spectre_behavior_failure" in issue_codes(failure_record, "gate2")
    assert "behavioral_failure" in issue_categories(failure_record, "gate2")


def test_gate3_reports_partition_and_property_coverage(tmp_path: Path) -> None:
    module = load_module()
    numbering = write_fixture(tmp_path)
    catalog_path = tmp_path / "tasks" / "010-demo-source" / "negative_variants" / "manifest.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["mutations"] = catalog["mutations"][:4]
    catalog["mutations"][0]["violated_property_ids"] = ["P_GAIN"]
    catalog["mutations"][1]["violated_property_ids"] = ["P_GAIN"]
    catalog["mutations"][2]["violated_property_ids"] = ["P_GAIN"]
    catalog["mutations"][3]["violated_property_ids"] = ["P_GAIN"]
    write_json(catalog_path, catalog)
    derivation_path = tmp_path / "tasks" / "010-demo-source" / "evaluator" / "derivation_manifest.json"
    derivation = json.loads(derivation_path.read_text(encoding="utf-8"))
    derivation["mutation_catalog_sha256"] = sha256(catalog_path)
    derivation["mutation_partition"]["testbench_public_feedback"] = []
    derivation["mutation_partition"]["testbench_private_score"] = ["neg_003_demo", "neg_004_demo", "neg_005_demo"]
    write_json(derivation_path, derivation)

    report = module.audit_release(root=tmp_path, numbering_plan_path=numbering, canonical_first=1)

    record = report["records"][0]
    assert record["gate3"]["ready"] is False
    assert "mutation_partition_not_total" in issue_codes(record, "gate3")
    assert "mutation_partition_count_insufficient" in issue_codes(record, "gate3")
    assert "mutation_diversity_insufficient" in issue_codes(record, "gate3")
    assert "mutation_property_coverage_incomplete" in issue_codes(record, "gate3")


def test_cli_writes_requested_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_module()
    numbering = write_fixture(tmp_path)
    output = tmp_path / "out" / "audit.json"
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "audit_v4_strict_readiness.py",
            "--canonical-first",
            "1",
            "--output",
            str(output),
        ],
    )

    assert module.main() == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["scope"]["canonical_first"] == 1
    assert payload["summary"]["gate2"]["ready_count"] == 1
