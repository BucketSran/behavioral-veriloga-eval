#!/usr/bin/env python3
"""Verify the vaBench evaluator environment contract.

The default mode checks repository source-of-truth files. Use ``--run-evas`` in
the pinned runtime image to attach live package/native-core evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "environment" / "evaluator-contract.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_identity(root: Path, path: Path) -> dict[str, Any]:
    exists = path.is_file()
    payload: dict[str, Any] = {
        "path": path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path),
        "exists": exists,
    }
    if exists:
        payload.update({"sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    return payload


def add_failure(failures: list[dict[str, str]], check: str, detail: str) -> None:
    failures.append({"check": check, "detail": detail})


def repository_identity(root: Path) -> dict[str, Any]:
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=normal"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        ).stdout.splitlines()
        tracked_changes = any(not line.startswith("?? ") for line in status)
        untracked_count = sum(line.startswith("?? ") for line in status)
        return {
            "status": "available",
            "commit": revision,
            "dirty": bool(status),
            "tracked_changes": tracked_changes,
            "untracked_file_count": untracked_count,
        }
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        return {"status": "unavailable", "error": f"{type(exc).__name__}: {exc}"}


def expect_equal(
    failures: list[dict[str, str]],
    check: str,
    observed: Any,
    expected: Any,
) -> None:
    if observed != expected:
        add_failure(failures, check, f"expected {expected!r}, observed {observed!r}")


def verify_source_contract(root: Path, contract_path: Path, contract: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    failures: list[dict[str, str]] = []
    environment = root / "environment"
    dockerfile = environment / "Dockerfile"
    dockerignore = environment / ".dockerignore"
    requirements_in = environment / "requirements.in"
    requirements_lock = environment / "requirements.lock"
    pyproject = root / "pyproject.toml"
    uv_lock = root / "uv.lock"
    public_runtime_workflow = root / ".github" / "workflows" / "public-agent-runtime.yml"
    evaluator_workflow = root / ".github" / "workflows" / "evaluator-closure.yml"

    for name, path in {
        "contract": contract_path,
        "dockerfile": dockerfile,
        "dockerignore": dockerignore,
        "requirements_in": requirements_in,
        "requirements_lock": requirements_lock,
        "pyproject": pyproject,
        "uv_lock": uv_lock,
        "public_runtime_workflow": public_runtime_workflow,
        "evaluator_workflow": evaluator_workflow,
    }.items():
        if not path.is_file():
            add_failure(failures, f"{name}_exists", f"missing {path}")

    if failures:
        return {"files": {}}, failures

    py = contract.get("python", {})
    evas = contract.get("evaluator", {}).get("evas", {})
    boundary = contract.get("runtime_boundary", {})

    docker_text = dockerfile.read_text(encoding="utf-8")
    lock_text = requirements_lock.read_text(encoding="utf-8")
    dockerignore_text = dockerignore.read_text(encoding="utf-8")
    pyproject_text = pyproject.read_text(encoding="utf-8")
    uv_lock_text = uv_lock.read_text(encoding="utf-8")
    public_runtime_workflow_text = public_runtime_workflow.read_text(encoding="utf-8")
    evaluator_workflow_text = evaluator_workflow.read_text(encoding="utf-8")

    expect_equal(failures, "schema_version", contract.get("schema_version"), "vabench-evaluator-environment-contract-v1")
    expect_equal(failures, "python_version", py.get("version"), "3.11.13")
    expect_equal(failures, "evas_package_version", evas.get("package_version"), "0.8.7")
    expect_equal(failures, "evas_engine", evas.get("engine"), "evas-rust")
    expect_equal(failures, "rust_core_abi_version", evas.get("rust_core_abi_version"), 20260718)
    expect_equal(failures, "rust_core_version", evas.get("rust_core_version"), "0.2.4")
    expect_equal(failures, "spectre_required", contract.get("evaluator", {}).get("spectre_required"), False)
    expect_equal(failures, "network_policy", boundary.get("network"), "none")
    expect_equal(failures, "root_filesystem", boundary.get("root_filesystem"), "read-only")

    base_ref = f'{py.get("base_image")}@{py.get("base_image_digest")}'
    if f"FROM {base_ref}" not in docker_text:
        add_failure(failures, "docker_base_image", f"Dockerfile does not pin {base_ref}")
    if "pip install --no-cache-dir --require-hashes" not in docker_text:
        add_failure(failures, "hash_locked_install", "Dockerfile does not use pip --require-hashes")
    for needle in (
        '"package_version"] == "0.8.7"',
        '"engine"] == "evas-rust"',
        '"rust_core_abi_version"] == 20260718',
        '"rust_core_version"] == "0.2.4"',
    ):
        if needle not in docker_text:
            add_failure(failures, "docker_evas_identity", f"missing assertion {needle}")
    if "evas-sim==0.8.7" not in requirements_in.read_text(encoding="utf-8"):
        add_failure(failures, "requirements_in_evas", "requirements.in does not pin evas-sim==0.8.7")
    if "evas-sim==0.8.7 \\" not in lock_text or "--hash=sha256:" not in lock_text:
        add_failure(failures, "requirements_lock_evas", "requirements.lock does not hash-pin evas-sim==0.8.7")
    if "pip-compile with Python 3.11" not in lock_text:
        add_failure(failures, "requirements_lock_python", "requirements.lock was not recorded as Python 3.11")
    if '"evas-sim==0.8.7"' not in pyproject_text:
        add_failure(failures, "project_evas_pin", "pyproject.toml does not pin evas-sim==0.8.7")
    if 'name = "evas-sim"\nversion = "0.8.7"' not in uv_lock_text:
        add_failure(failures, "project_lock_evas", "uv.lock does not resolve evas-sim==0.8.7")
    if "!evaluator-contract.json" not in dockerignore_text:
        add_failure(failures, "dockerignore_contract", ".dockerignore does not include evaluator-contract.json")
    if "scripts/verify_evaluator_environment.py --json" not in public_runtime_workflow_text:
        add_failure(failures, "ci_verifier", "public-agent-runtime CI does not run the environment verifier")
    for needle in (
        "scripts/verify_evaluator_environment.py",
        "scripts/run_v3_clean_room_smoke.py",
        "tests/test_v3_model_eval_claim_gate.py",
    ):
        if needle not in evaluator_workflow_text:
            add_failure(failures, "evaluator_closure_ci", f"evaluator closure CI is missing {needle}")

    mounts = boundary.get("model_mounts", [])
    mount_targets = {item.get("target"): item.get("mode") for item in mounts if isinstance(item, dict)}
    expected_mounts = {
        "/workspace/public/task": "ro",
        "/workspace/public/submission": "rw",
        "/workspace/work": "rw",
        "/workspace/public/skills": "ro",
    }
    if mount_targets != expected_mounts:
        add_failure(failures, "model_mounts", f"expected {expected_mounts!r}, observed {mount_targets!r}")
    forbidden = set(boundary.get("forbidden_model_paths", []))
    if {"/workspace/evaluator", "/opt/benchmark"} - forbidden:
        add_failure(failures, "forbidden_model_paths", "private evaluator paths are not fail-closed")

    return {
        "files": {
            "contract": file_identity(root, contract_path),
            "dockerfile": file_identity(root, dockerfile),
            "requirements_in": file_identity(root, requirements_in),
            "requirements_lock": file_identity(root, requirements_lock),
            "pyproject": file_identity(root, pyproject),
            "uv_lock": file_identity(root, uv_lock),
            "public_runtime_workflow": file_identity(root, public_runtime_workflow),
            "evaluator_workflow": file_identity(root, evaluator_workflow),
        },
        "repository": repository_identity(root),
    }, failures


def verify_live_python(contract: dict[str, Any], required: bool) -> tuple[dict[str, Any], list[dict[str, str]]]:
    failures: list[dict[str, str]] = []
    expected = str(contract.get("python", {}).get("version") or "")
    observed = platform.python_version()
    if required and observed != expected:
        add_failure(
            failures,
            "live_python_version",
            f"expected Python {expected}, observed {observed}",
        )
    return {
        "status": "pass" if not failures else "fail",
        "required_version": expected,
        "observed_version": observed,
        "executable": sys.executable,
    }, failures


def run_evas_version(command: str, timeout_s: int) -> tuple[dict[str, Any] | None, str | None]:
    try:
        completed = subprocess.run(
            [command, "--version", "--format", "json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except FileNotFoundError:
        return None, "evas_command_not_found"
    except subprocess.TimeoutExpired:
        return None, "evas_version_timeout"
    if completed.returncode != 0:
        return None, f"evas_version_failed:{completed.returncode}:{completed.stderr.strip()[:200]}"
    try:
        return json.loads(completed.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"evas_version_invalid_json:{exc}"


def verify_live_evas(
    *,
    contract: dict[str, Any],
    command: str,
    timeout_s: int,
    required: bool,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    failures: list[dict[str, str]] = []
    expected = contract.get("evaluator", {}).get("evas", {})
    observed, error = run_evas_version(command, timeout_s)
    if observed is None:
        status = "fail" if required else "not_checked"
        if required:
            add_failure(failures, "live_evas", error or "unknown_evas_error")
        return {"status": status, "command": command, "error": error}, failures

    for key in (
        "package_name",
        "package_version",
        "engine",
        "rust_core_present",
        "rust_core_loadable",
        "rust_core_abi_version",
        "rust_core_version",
    ):
        expect_equal(failures, f"live_evas_{key}", observed.get(key), expected.get(key))
    return {
        "status": "pass" if not failures else "fail",
        "command": command,
        "observed": observed,
    }, failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument("--json", action="store_true", help="print JSON only")
    parser.add_argument("--run-evas", action="store_true", help="also execute evas --version --format json")
    parser.add_argument("--evas-command", default="evas")
    parser.add_argument("--timeout-s", type=int, default=10)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.repo_root).resolve()
    contract_path = Path(args.contract)
    if not contract_path.is_absolute():
        contract_path = root / contract_path

    failures: list[dict[str, str]] = []
    try:
        contract = read_json(contract_path)
    except (OSError, json.JSONDecodeError) as exc:
        contract = {}
        add_failure(failures, "contract_load", f"{type(exc).__name__}: {exc}")

    source: dict[str, Any] = {"files": {}}
    if contract:
        source, source_failures = verify_source_contract(root, contract_path, contract)
        failures.extend(source_failures)
    if args.run_evas:
        live_python, live_python_failures = verify_live_python(contract, required=True)
        failures.extend(live_python_failures)
        live_evas, live_failures = verify_live_evas(
            contract=contract,
            command=args.evas_command,
            timeout_s=args.timeout_s,
            required=True,
        )
        failures.extend(live_failures)
    else:
        live_python = {
            "status": "not_checked",
            "reason": "pass --run-evas inside the pinned runtime image for formal claim evidence",
        }
        live_evas = {
            "status": "not_checked",
            "command": args.evas_command,
            "reason": "pass --run-evas inside the pinned runtime image for formal claim evidence",
        }

    payload = {
        "schema_version": "vabench-evaluator-environment-verification-v1",
        "status": "pass" if not failures else "fail",
        "contract": file_identity(root, contract_path),
        "source": source,
        "live_python": live_python,
        "live_evas": live_evas,
        "failures": failures,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
