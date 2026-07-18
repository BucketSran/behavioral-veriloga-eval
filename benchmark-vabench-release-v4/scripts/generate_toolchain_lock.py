#!/usr/bin/env python3
"""Generate the v4 toolchain lock from the environment that will run it."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from checker_registry_identity import (
    checker_registry_files as _checker_registry_files,
    checker_registry_hash as _checker_registry_hash,
    tree_hash,
)
from evidence_fingerprints import evas_runtime_component_identity


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
WORKSPACE = REPO.parent
SCHEMA = ROOT / "schemas" / "toolchain_lock.schema.json"
OUTPUT = ROOT / "TOOLCHAIN_LOCK.json"
EXPECTED_EVAS_COMMIT = "e552d152f6be970610dcc58cd27b04b7e53b892f"
EXPECTED_EVAS_TAG = "v0.8.1"
EXPECTED_EVAS_VERSION = "0.8.1"
EXPECTED_RUST_ABI = 20260711
DEFAULT_EVAS_ROOT = WORKSPACE / ".runtime" / "evas-v0.8.1"
DEFAULT_EVAS_PYTHON = DEFAULT_EVAS_ROOT / ".venv312" / "bin" / "python"
DEFAULT_SPECTRE_HOST = "thu-sui"
DEFAULT_CADENCE_CSHRC = "/home/cshrc/.cshrc.cadence.IC618SP201"


def run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or "").strip()
        raise RuntimeError(f"command failed: {command!r}\n{details}") from exc
    return completed.stdout.strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def checker_registry_files() -> list[Path]:
    return _checker_registry_files(REPO)


def checker_registry_hash() -> str:
    return _checker_registry_hash(REPO)


def benchmark_component_hashes() -> dict[str, str]:
    return {
        "checker_registry_sha256": checker_registry_hash(),
        "harness_generator_sha256": sha256_file(ROOT / "scripts" / "render_v4_harness.py"),
        "oracle_runner_sha256": sha256_file(ROOT / "runners" / "feedback_oracle.py"),
    }


def git_value(root: Path, *args: str) -> str:
    return run(["git", "-C", str(root), *args])


def git_dirty(root: Path) -> bool:
    return bool(git_value(root, "status", "--porcelain", "--untracked-files=no"))


def inspect_evas(evas_python: Path, evas_root: Path) -> dict[str, Any]:
    script = r"""
import hashlib, importlib.metadata, json, os, platform, sys
import evas
from evas.netlist.runner import _configured_evas_engine
from evas.simulator.rust_backend import default_rust_core_library_path, load_rust_backend
p = default_rust_core_library_path()
b = load_rust_backend()
print(json.dumps({
  "runtime_metadata_version": importlib.metadata.version("evas-sim"),
  "module_path": str(evas.__file__),
  "actual_engine": _configured_evas_engine({}),
  "rust_core_abi": b.abi_version,
  "build_path": str(p),
  "build_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
  "python_version": platform.python_version(),
  "python_executable": sys.executable,
  "platform": platform.platform(),
  "architecture": platform.machine(),
}))
"""
    env = os.environ.copy()
    env["EVAS_ENGINE"] = "evas-rust"
    data = json.loads(run([str(evas_python), "-c", script], cwd=evas_root, env=env))
    git_commit = git_value(evas_root, "rev-parse", "HEAD")
    try:
        run(
            ["git", "-C", str(evas_root), "merge-base", "--is-ancestor", EXPECTED_EVAS_COMMIT, git_commit]
        )
        release_base_is_ancestor = True
    except RuntimeError:
        release_base_is_ancestor = False
    patch_commit_count = int(
        git_value(evas_root, "rev-list", "--count", f"{EXPECTED_EVAS_COMMIT}..{git_commit}")
    )
    data.update(
        {
            "git_commit": git_commit,
            "git_describe": git_value(evas_root, "describe", "--tags", "--always", "--dirty"),
            "dirty": git_dirty(evas_root),
            "release_base_commit": EXPECTED_EVAS_COMMIT,
            "release_base_is_ancestor": release_base_is_ancestor,
            "patch_commit_count": patch_commit_count,
            "release_relation": (
                "exact_release_tag" if git_commit == EXPECTED_EVAS_COMMIT
                else "patched_release_descendant"
            ),
        }
    )
    return data


def run_evas_smoke(evas_python: Path, evas_root: Path) -> dict[str, Any]:
    va_text = """`include \"constants.vams\"\n`include \"disciplines.vams\"\nmodule v4_lock_smoke(in, out);\n  input in; output out; electrical in, out;\n  analog V(out) <+ transition(2.0 * V(in), 0.0, 1p);\nendmodule\n"""
    scs_text = """simulator lang=spectre\nglobal 0\nahdl_include \"v4_lock_smoke.va\"\nVIN (vin 0) vsource dc=0.25\nXDUT (vin vout) v4_lock_smoke\nsimulatorOptions options evas_engine=evas-rust evas_profile=balanced\ntran tran stop=2n maxstep=0.1n\nsave vin:2e vout:2e\n"""
    with tempfile.TemporaryDirectory(prefix="v4_toolchain_smoke_") as raw_dir:
        work = Path(raw_dir)
        (work / "v4_lock_smoke.va").write_text(va_text, encoding="utf-8")
        deck = work / "smoke.scs"
        deck.write_text(scs_text, encoding="utf-8")
        log_path = work / "evas.log"
        output_dir = work / "output"
        env = os.environ.copy()
        env["EVAS_ENGINE"] = "evas-rust"
        run(
            [
                str(evas_python),
                "-m",
                "evas.cli",
                "simulate",
                str(deck),
                "--engine",
                "evas-rust",
                "--ahdllint",
                "--spectre-strict",
                "-log",
                str(log_path),
                "-o",
                str(output_dir),
            ],
            cwd=evas_root,
            env=env,
        )
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        observed_engine = "evas-rust" if "evas_engine = evas-rust" in log_text else "unknown"
        observed_profile = "balanced" if "evas_profile = balanced" in log_text else "unknown"
        fallback_observed = "evas_engine = python" in log_text
        if observed_engine != "evas-rust" or observed_profile != "balanced" or fallback_observed:
            raise RuntimeError("EVAS smoke did not observe the locked engine/profile")
        return {
            "status": "pass",
            "log_sha256": sha256_bytes(log_text.encode("utf-8")),
            "observed_engine": observed_engine,
            "observed_profile": observed_profile,
            "python_fallback_observed": fallback_observed,
        }


def inspect_spectre(host: str, cadence_cshrc: str) -> dict[str, str]:
    # Some Spectre releases print a valid `-W` version banner but return a
    # non-zero status. Keep the identity probe strict about parseable output,
    # not that release-specific exit convention.
    remote = f"csh -fc 'source {cadence_cshrc}; which spectre; spectre -W; true'"
    completed: subprocess.CompletedProcess[str] | None = None
    last_error = ""
    for attempt in range(3):
        try:
            completed = subprocess.run(
                ["ssh", host, remote],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            break
        except subprocess.CalledProcessError as exc:
            last_error = (exc.stdout or "").strip()
            if attempt == 2:
                raise RuntimeError(
                    f"Spectre identity probe failed after 3 attempts for {host}: {last_error}"
                ) from exc
            time.sleep(attempt + 1)
    assert completed is not None
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) < 2:
        raise RuntimeError(f"cannot parse Spectre identity from {lines!r}")
    path = next((line for line in lines if line.startswith("/")), "")
    version = next((line for line in lines if "sub-version" in line.lower()), "")
    if not path or not version:
        raise RuntimeError(f"cannot parse Spectre path/version from {lines!r}")
    return {"path": path, "version": version}


def inspect_ssh_route(host: str) -> dict[str, str]:
    output = run(["ssh", "-G", host])
    values: dict[str, str] = {}
    for line in output.splitlines():
        key, _, value = line.partition(" ")
        if key in {"hostname", "proxyjump"} and value.strip():
            values[key] = value.strip()
    proxyjump = values.get("proxyjump", "")
    if proxyjump and proxyjump.lower() != "none":
        route = f"proxyjump={proxyjump}"
        identity = f"sui-direct:ssh:{host}:proxyjump={proxyjump}"
    else:
        route = "direct"
        identity = f"sui-direct:ssh:{host}"
    return {"route": route, "transport_identity": identity}


def verify_evas(identity: dict[str, Any]) -> None:
    expected = {
        "runtime_metadata_version": EXPECTED_EVAS_VERSION,
        "actual_engine": "evas-rust",
        "rust_core_abi": EXPECTED_RUST_ABI,
        "dirty": False,
        "release_base_commit": EXPECTED_EVAS_COMMIT,
        "release_base_is_ancestor": True,
    }
    mismatches = [
        f"{key}: expected {value!r}, observed {identity.get(key)!r}"
        for key, value in expected.items()
        if identity.get(key) != value
    ]
    relation = identity.get("release_relation")
    patch_count = identity.get("patch_commit_count")
    describe = str(identity.get("git_describe") or "")
    if identity.get("git_commit") == EXPECTED_EVAS_COMMIT:
        if relation != "exact_release_tag" or patch_count != 0 or describe != EXPECTED_EVAS_TAG:
            mismatches.append(
                "exact release identity requires exact_release_tag, zero patches, and git_describe=v0.8.1"
            )
    elif relation != "patched_release_descendant" or not isinstance(patch_count, int) or patch_count < 1:
        mismatches.append(
            "patched EVAS identity requires patched_release_descendant and patch_commit_count>=1"
        )
    if not (describe == EXPECTED_EVAS_TAG or describe.startswith(f"{EXPECTED_EVAS_TAG}-")):
        mismatches.append(f"git_describe must be rooted at {EXPECTED_EVAS_TAG}, observed {describe!r}")
    if mismatches:
        raise RuntimeError("EVAS identity mismatch:\n  " + "\n  ".join(mismatches))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evas-root", type=Path, default=DEFAULT_EVAS_ROOT)
    parser.add_argument("--evas-python", type=Path, default=DEFAULT_EVAS_PYTHON)
    parser.add_argument("--spectre-host", default=DEFAULT_SPECTRE_HOST)
    parser.add_argument("--cadence-cshrc", default=DEFAULT_CADENCE_CSHRC)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evas_root = args.evas_root.resolve()
    evas_python = args.evas_python.expanduser().absolute()
    if not evas_python.is_file():
        raise SystemExit(f"EVAS Python not found: {evas_python}")

    evas = inspect_evas(evas_python, evas_root)
    verify_evas(evas)
    runtime_components = evas_runtime_component_identity(evas_root)
    smoke = run_evas_smoke(evas_python, evas_root)
    spectre = inspect_spectre(args.spectre_host, args.cadence_cshrc)
    ssh_route = inspect_ssh_route(args.spectre_host)

    ahdl_rules = [evas_root / "evas" / "compiler" / "linter.py"]
    schema_files = sorted((ROOT / "schemas").glob("*.schema.json"))

    payload = {
        "schema_version": "v4-toolchain-lock-v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "valid",
        "evas": {
            "distribution": "evas-sim",
            "implementation_track": "python-rust-hybrid",
            "frontend": "python",
            "runtime": "rust",
            "source_package_version": EXPECTED_EVAS_VERSION,
            "runtime_metadata_version": evas["runtime_metadata_version"],
            "release_tag": EXPECTED_EVAS_TAG,
            "release_base_commit": evas["release_base_commit"],
            "patch_commit_count": evas["patch_commit_count"],
            "git_commit": evas["git_commit"],
            "git_describe": evas["git_describe"],
            "dirty": evas["dirty"],
            "release_relation": evas["release_relation"],
            "module_path": evas["module_path"],
            "requested_engine": "evas-rust",
            "actual_engine": evas["actual_engine"],
            "allow_python_fallback": False,
            "profile": "balanced",
            "rust_core_abi": evas["rust_core_abi"],
            "build_sha256": evas["build_sha256"],
            "runtime_components": runtime_components,
            "ahdl_like": {
                "ruleset_id": "evas-ahdl-like-v0.8.1",
                "ruleset_sha256": tree_hash(ahdl_rules, base=evas_root),
                "spectre_strict": True,
                "minimum_transition_s": 1e-12,
            },
            "smoke": smoke,
        },
        "spectre": {
            "backend": "sui-direct",
            "remote_host": args.spectre_host,
            "route": ssh_route["route"],
            "path": spectre["path"],
            "version": spectre["version"],
            "cadence_cshrc": args.cadence_cshrc,
            "transport_identity": ssh_route["transport_identity"],
        },
        "benchmark": {
            "git_commit": git_value(REPO, "rev-parse", "HEAD"),
            "dirty": git_dirty(REPO),
            **benchmark_component_hashes(),
            "schema_set_sha256": tree_hash(schema_files, base=ROOT),
        },
        "runtime": {
            "python_version": evas["python_version"],
            "python_executable": evas["python_executable"],
            "platform": evas["platform"],
            "architecture": evas["architecture"],
        },
    }
    errors = sorted(Draft202012Validator(json.loads(SCHEMA.read_text())).iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        for error in errors:
            print(f"schema error at {list(error.path)}: {error.message}")
        return 1
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "sha256": sha256_file(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
