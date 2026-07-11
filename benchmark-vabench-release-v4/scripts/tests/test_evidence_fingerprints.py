from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "evidence_fingerprints.py"


def load_module():
    spec = importlib.util.spec_from_file_location("evidence_fingerprints", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def toolchain() -> dict:
    return {
        "evas": {
            "distribution": "evas-sim",
            "implementation_track": "python-rust-hybrid",
            "frontend": "python",
            "runtime": "rust",
            "source_package_version": "0.8.1",
            "runtime_metadata_version": "0.8.1",
            "git_commit": "1" * 40,
            "requested_engine": "evas-rust",
            "actual_engine": "evas-rust",
            "allow_python_fallback": False,
            "profile": "balanced",
            "rust_core_abi": 20260706,
            "build_sha256": "2" * 64,
            "ahdl_like": {
                "ruleset_id": "evas-ahdl-like-v0.8.1",
                "ruleset_sha256": "3" * 64,
                "spectre_strict": True,
                "minimum_transition_s": 1e-15,
            },
        },
        "spectre": {
            "backend": "sui-direct",
            "remote_host": "thu-wei",
            "route": "proxyjump=thu-jin",
            "path": "/cadence/spectre",
            "version": "spectre fixture",
            "cadence_cshrc": "/home/cadence.cshrc",
            "transport_identity": "sui-direct:ssh:thu-wei:proxyjump=thu-jin",
        },
        "benchmark": {
            "checker_registry_sha256": "4" * 64,
            "harness_generator_sha256": "5" * 64,
            "oracle_runner_sha256": "6" * 64,
            "schema_set_sha256": "7" * 64,
        },
        "runtime": {"python_version": "3.12"},
    }


def test_backend_fingerprints_ignore_unrelated_release_components() -> None:
    module = load_module()
    original = toolchain()
    changed = copy.deepcopy(original)
    changed["benchmark"]["checker_registry_sha256"] = "8" * 64
    changed["benchmark"]["schema_set_sha256"] = "9" * 64
    changed["runtime"]["python_version"] = "3.13"

    assert module.backend_fingerprints(original, spectre_mode="ax") == module.backend_fingerprints(
        changed, spectre_mode="ax"
    )


def test_backend_fingerprints_ignore_provenance_only_git_commit() -> None:
    module = load_module()
    original = toolchain()
    changed = copy.deepcopy(original)
    changed["evas"]["git_commit"] = "f" * 40

    assert module.backend_fingerprints(original, spectre_mode="ax") == module.backend_fingerprints(
        changed, spectre_mode="ax"
    )


def test_evas_and_spectre_backend_fingerprints_invalidate_independently() -> None:
    module = load_module()
    original = toolchain()

    evas_changed = copy.deepcopy(original)
    evas_changed["evas"]["build_sha256"] = "a" * 64
    before = module.backend_fingerprints(original, spectre_mode="ax")
    after_evas = module.backend_fingerprints(evas_changed, spectre_mode="ax")
    assert before["evas_sha256"] != after_evas["evas_sha256"]
    assert before["spectre_sha256"] == after_evas["spectre_sha256"]

    spectre_changed = copy.deepcopy(original)
    spectre_changed["spectre"]["version"] = "spectre newer"
    after_spectre = module.backend_fingerprints(spectre_changed, spectre_mode="ax")
    assert before["evas_sha256"] == after_spectre["evas_sha256"]
    assert before["spectre_sha256"] != after_spectre["spectre_sha256"]


def test_frontend_and_runtime_identity_invalidate_only_evas_evidence() -> None:
    module = load_module()
    original = toolchain()
    standalone = copy.deepcopy(original)
    standalone["evas"]["implementation_track"] = "standalone-rust"
    standalone["evas"]["frontend"] = "rust"

    before = module.backend_fingerprints(original, spectre_mode="ax")
    after = module.backend_fingerprints(standalone, spectre_mode="ax")

    assert before["evas_sha256"] != after["evas_sha256"]
    assert before["ahdl_like_sha256"] == after["ahdl_like_sha256"]
    assert before["spectre_sha256"] == after["spectre_sha256"]


def test_runtime_components_invalidate_only_the_evas_backend_identity() -> None:
    module = load_module()
    original = toolchain()
    before = module.backend_fingerprints(original, spectre_mode="ax")
    after = module.backend_fingerprints(
        original,
        spectre_mode="ax",
        evas_runtime_identity={
            "netlist_runner_sha256": "runner-v2",
            "spectre_parser_sha256": "parser-v2",
            "rust_runtime_sha256": "rust-v1",
        },
    )

    assert before["evas_sha256"] != after["evas_sha256"]
    assert before["ahdl_like_sha256"] == after["ahdl_like_sha256"]
    assert before["spectre_sha256"] == after["spectre_sha256"]


def test_standalone_rust_component_identity_tracks_binary_and_sources(tmp_path: Path) -> None:
    module = load_module()
    root = tmp_path / "evas"
    rust_root = root / "evas" / "rust_core"
    (rust_root / "src").mkdir(parents=True)
    (rust_root / "Cargo.toml").write_text("[package]\nname='demo'\n", encoding="utf-8")
    (rust_root / "Cargo.lock").write_text("version = 3\n", encoding="utf-8")
    source = rust_root / "src" / "lib.rs"
    source.write_text("pub fn demo() {}\n", encoding="utf-8")
    binary = rust_root / "target" / "release" / "evas_rust_frontend"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"binary-v1")

    before = module.standalone_rust_component_identity(root, binary)
    source.write_text("pub fn demo() { let _ = 1; }\n", encoding="utf-8")
    after_source = module.standalone_rust_component_identity(root, binary)
    binary.write_bytes(b"binary-v2")
    after_binary = module.standalone_rust_component_identity(root, binary)

    assert before["rust_source_tree_sha256"] != after_source["rust_source_tree_sha256"]
    assert after_source["rust_frontend_sha256"] != after_binary["rust_frontend_sha256"]


def test_component_comparison_reports_only_precise_stale_paths() -> None:
    module = load_module()
    expected = {
        "task_inputs": {"deck_sha256": "a" * 64},
        "oracle": {"checker_implementation_sha256": "b" * 64},
        "backend": {"spectre_sha256": "c" * 64},
    }
    observed = copy.deepcopy(expected)
    observed["oracle"]["checker_implementation_sha256"] = "d" * 64

    assert module.component_mismatches(expected, observed) == [
        "oracle.checker_implementation_sha256"
    ]


def test_checker_only_change_reuses_complete_trace() -> None:
    module = load_module()
    expected = {
        "task_inputs": {"deck_sha256": "a" * 64},
        "oracle": {"checker_implementation_sha256": "b" * 64},
        "backend": {"spectre_sha256": "c" * 64},
    }
    observed = copy.deepcopy(expected)
    observed["oracle"]["checker_implementation_sha256"] = "d" * 64

    decision = module.reuse_decision(
        expected,
        observed,
        backend="spectre",
        raw_trace_available=True,
        available_trace_signals=("time", "out"),
        required_trace_signals=("time", "out"),
    )
    assert decision["action"] == "re_evaluate_checker"
    assert decision["state"] == "carried_forward"


def test_checker_change_without_required_signal_reruns_only_affected_backend() -> None:
    module = load_module()
    expected = {
        "task_inputs": {"deck_sha256": "a" * 64},
        "oracle": {"checker_implementation_sha256": "b" * 64},
        "backend": {"evas_sha256": "c" * 64},
    }
    observed = copy.deepcopy(expected)
    observed["oracle"]["checker_implementation_sha256"] = "d" * 64
    decision = module.reuse_decision(
        expected,
        observed,
        backend="evas",
        raw_trace_available=True,
        available_trace_signals=("time",),
        required_trace_signals=("time", "out"),
    )
    assert decision["action"] == "rerun_evas"
    assert decision["missing_trace_signals"] == ["out"]


def test_harness_change_invalidates_only_selected_task_profile_backend() -> None:
    module = load_module()
    expected = {
        "task_inputs": {"harness_spec_sha256": "a" * 64},
        "oracle": {},
        "backend": {"spectre_sha256": "b" * 64, "evas_sha256": "c" * 64},
    }
    observed = copy.deepcopy(expected)
    observed["task_inputs"]["harness_spec_sha256"] = "d" * 64
    decision = module.reuse_decision(
        expected,
        observed,
        backend="spectre",
        raw_trace_available=True,
    )
    assert decision["action"] == "rerun_spectre"
    assert decision["reasons"] == ["task_inputs.harness_spec_sha256"]


def test_other_backend_and_release_snapshot_changes_are_ignored() -> None:
    module = load_module()
    expected = {
        "task_inputs": {"deck_sha256": "a" * 64},
        "oracle": {},
        "backend": {"spectre_sha256": "b" * 64, "evas_sha256": "c" * 64},
        "assembly": {"release_snapshot_sha256": "d" * 64},
    }
    observed = copy.deepcopy(expected)
    observed["backend"]["evas_sha256"] = "e" * 64
    observed["assembly"]["release_snapshot_sha256"] = "f" * 64
    decision = module.reuse_decision(
        expected,
        observed,
        backend="spectre",
        raw_trace_available=True,
    )
    assert decision["action"] == "reuse"
    assert decision["state"] == "carried_forward"
    assert decision["ignored_mismatches"] == [
        "assembly.release_snapshot_sha256",
        "backend.evas_sha256",
    ]
