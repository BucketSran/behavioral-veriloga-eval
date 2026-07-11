#!/usr/bin/env python3
"""Content-addressed identities for reusable vaBench v4 evidence."""
from __future__ import annotations

import hashlib
import inspect
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


POLICY_ID = "v4-dependency-scoped-evidence-v2"


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _python_tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def evas_runtime_component_identity(evas_root: Path) -> dict[str, str]:
    binary_candidates = (
        evas_root / "evas" / "rust_core" / "target" / "release" / "libevas_rust_core.dylib",
        evas_root / "evas" / "rust_core" / "target" / "release" / "libevas_rust_core.so",
    )
    binary = next((path for path in binary_candidates if path.is_file()), None)
    if binary is None:
        raise FileNotFoundError(f"missing frozen EVAS Rust runtime under {evas_root}")
    component_paths = {
        "netlist_runner_sha256": evas_root / "evas" / "netlist" / "runner.py",
        "spectre_parser_sha256": evas_root / "evas" / "netlist" / "spectre_parser.py",
        "rust_runtime_sha256": binary,
    }
    components = {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in component_paths.items()
    }
    components["python_package_sha256"] = _python_tree_sha256(evas_root / "evas")
    return components


def standalone_rust_component_identity(
    evas_root: Path, rust_frontend: Path
) -> dict[str, str]:
    rust_root = evas_root / "evas" / "rust_core"
    source_paths = [rust_root / "Cargo.toml", rust_root / "Cargo.lock"]
    source_paths.extend(sorted((rust_root / "src").rglob("*.rs")))
    missing = [path for path in source_paths[:2] if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing standalone Rust EVAS source inputs: {missing}")
    if not rust_frontend.is_file():
        raise FileNotFoundError(f"missing standalone Rust EVAS executable: {rust_frontend}")
    digest = hashlib.sha256()
    for path in source_paths:
        digest.update(path.relative_to(rust_root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return {
        "rust_frontend_sha256": hashlib.sha256(rust_frontend.read_bytes()).hexdigest(),
        "rust_source_tree_sha256": digest.hexdigest(),
    }


def _selected(mapping: Mapping[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {key: mapping.get(key) for key in keys}


def backend_fingerprints(
    toolchain: Mapping[str, Any],
    *,
    spectre_mode: str,
    spectre_identity: Mapping[str, Any] | None = None,
    evas_runtime_identity: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    evas = toolchain.get("evas") or {}
    ahdl = evas.get("ahdl_like") or {}
    spectre = spectre_identity or toolchain.get("spectre") or {}
    ahdl_payload = _selected(
        ahdl,
        ("ruleset_id", "ruleset_sha256", "spectre_strict", "minimum_transition_s"),
    )
    evas_payload = _selected(
        evas,
        (
            "distribution",
            "implementation_track",
            "frontend",
            "runtime",
            "source_package_version",
            "runtime_metadata_version",
            "requested_engine",
            "actual_engine",
            "allow_python_fallback",
            "profile",
            "rust_core_abi",
            "build_sha256",
        ),
    )
    runtime_identity = evas_runtime_identity or evas.get("runtime_components") or {}
    if runtime_identity:
        evas_payload["runtime_components"] = dict(sorted(runtime_identity.items()))
    spectre_payload = {
        **_selected(
            spectre,
            (
                "backend",
                "route",
                "path",
                "version",
                "cadence_cshrc",
                "transport_identity",
            ),
        ),
        "host": spectre.get("host") or spectre.get("remote_host"),
        "mode": spectre_mode,
    }
    return {
        "ahdl_like_sha256": canonical_sha256(ahdl_payload),
        "evas_sha256": canonical_sha256(evas_payload),
        "spectre_sha256": canonical_sha256(spectre_payload),
    }


def checker_fingerprints(
    checker_task_id: str,
    checker_profile: Mapping[str, Any],
    checker: Callable[..., Any] | None,
) -> dict[str, str]:
    if checker is None:
        callable_module = "unresolved"
        callable_name = checker_task_id
        source = ""
    else:
        callable_module = str(getattr(checker, "__module__", ""))
        callable_name = str(
            getattr(checker, "__qualname__", getattr(checker, "__name__", ""))
        )
        try:
            source = inspect.getsource(checker)
        except (OSError, TypeError):
            code = getattr(checker, "__code__", None)
            source = repr(
                (
                    getattr(code, "co_code", b""),
                    getattr(code, "co_consts", ()),
                    getattr(code, "co_names", ()),
                )
            )
    binding = {
        "checker_task_id": checker_task_id,
        "callable_module": callable_module,
        "callable_name": callable_name,
    }
    diagnostic_policy = {
        "diagnostics": checker_profile.get("diagnostics") or {},
        "side_effect_contract": checker_profile.get("side_effect_contract") or {},
    }
    return {
        "checker_profile_sha256": canonical_sha256(checker_profile),
        "checker_binding_sha256": canonical_sha256(binding),
        "checker_implementation_sha256": canonical_sha256(
            {**binding, "source": source}
        ),
        "diagnostic_policy_sha256": canonical_sha256(diagnostic_policy),
    }


def task_input_fingerprints(
    *,
    family_spec: Mapping[str, Any],
    hashes: Mapping[str, Any],
) -> dict[str, str]:
    names = (
        "family_spec_sha256",
        "candidate_bundle_sha256",
        "gold_bundle_sha256",
        "mutation_bundle_sha256",
        "public_support_bundle_sha256",
        "harness_spec_sha256",
        "profile_sha256",
        "score_profile_sha256",
        "deck_sha256",
    )
    values = {
        name: str(hashes[name])
        for name in names
        if isinstance(hashes.get(name), str) and hashes.get(name)
    }
    values["trace_contract_sha256"] = canonical_sha256(
        family_spec.get("trace_contract") or {}
    )
    values["property_contract_sha256"] = canonical_sha256(
        family_spec.get("properties") or []
    )
    return values


def evidence_components(
    *,
    task_inputs: Mapping[str, str],
    oracle: Mapping[str, str],
    backend: Mapping[str, str],
    release_snapshot_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": "v4-evidence-components-v2",
        "policy_id": POLICY_ID,
        "state": "fresh",
        "task_inputs": dict(sorted(task_inputs.items())),
        "oracle": dict(sorted(oracle.items())),
        "backend": dict(sorted(backend.items())),
        "assembly": {
            "policy_sha256": canonical_sha256({"policy_id": POLICY_ID}),
            "release_snapshot_sha256": release_snapshot_sha256,
        },
    }


def _flatten(prefix: str, value: Any, output: dict[str, Any]) -> None:
    if isinstance(value, Mapping):
        for key in sorted(value):
            child = f"{prefix}.{key}" if prefix else str(key)
            _flatten(child, value[key], output)
    else:
        output[prefix] = value


def component_mismatches(
    expected: Mapping[str, Any], observed: Mapping[str, Any]
) -> list[str]:
    expected_flat: dict[str, Any] = {}
    observed_flat: dict[str, Any] = {}
    _flatten("", expected, expected_flat)
    _flatten("", observed, observed_flat)
    return sorted(
        path
        for path, expected_value in expected_flat.items()
        if observed_flat.get(path) != expected_value
    )


def reuse_decision(
    expected: Mapping[str, Any],
    observed: Mapping[str, Any],
    *,
    backend: str,
    raw_trace_available: bool,
    available_trace_signals: tuple[str, ...] = (),
    required_trace_signals: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Explain the narrowest legal action for one backend evidence record."""
    all_mismatches = component_mismatches(expected, observed)
    relevant_backend = f"backend.{backend}_sha256"
    simulation_mismatches = [
        path
        for path in all_mismatches
        if path.startswith("task_inputs.") or path == relevant_backend
    ]
    oracle_mismatches = [
        path for path in all_mismatches if path.startswith("oracle.")
    ]
    ignored = [
        path
        for path in all_mismatches
        if path not in simulation_mismatches and path not in oracle_mismatches
    ]
    missing_signals = sorted(set(required_trace_signals) - set(available_trace_signals))
    if simulation_mismatches:
        action = f"rerun_{backend}"
        state = "stale_component"
        reasons = simulation_mismatches
    elif oracle_mismatches and raw_trace_available and not missing_signals:
        action = "re_evaluate_checker"
        state = "carried_forward"
        reasons = oracle_mismatches
    elif oracle_mismatches:
        action = f"rerun_{backend}"
        state = "blocked_missing_raw_evidence"
        reasons = oracle_mismatches + [
            f"missing_trace_signal.{signal}" for signal in missing_signals
        ]
        if not raw_trace_available:
            reasons.append("raw_trace_missing")
    else:
        action = "reuse"
        state = "carried_forward" if all_mismatches else "fresh"
        reasons = []
    return {
        "backend": backend,
        "state": state,
        "action": action,
        "reasons": sorted(set(reasons)),
        "ignored_mismatches": sorted(ignored),
        "raw_trace_available": raw_trace_available,
        "missing_trace_signals": missing_signals,
    }


def simulation_cache_inputs(
    *,
    task_id: str,
    profile: str,
    backend: str,
    backend_sha256: str,
    hashes: Mapping[str, Any],
    source_slug: str = "",
    mutation_id: str = "",
    spectre_mode: str = "",
) -> dict[str, str]:
    payload = {
        "task_id": task_id,
        "profile": profile,
        "backend": backend,
        "backend_sha256": backend_sha256,
        "deck_sha256": str(hashes.get("deck_sha256") or ""),
        "candidate_bundle_sha256": str(
            hashes.get("candidate_bundle_sha256")
            or hashes.get("gold_bundle_sha256")
            or ""
        ),
        "public_support_bundle_sha256": str(
            hashes.get("public_support_bundle_sha256") or ""
        ),
        "harness_spec_sha256": str(hashes.get("harness_spec_sha256") or ""),
        "profile_sha256": str(
            hashes.get("profile_sha256")
            or hashes.get("score_profile_sha256")
            or ""
        ),
    }
    if source_slug:
        payload["source_slug"] = source_slug
    if mutation_id:
        payload["mutation_id"] = mutation_id
    if backend == "spectre":
        payload["spectre_mode"] = spectre_mode
    return payload
