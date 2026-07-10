#!/usr/bin/env python3
"""Run canonical first-N v4 DUT golds through the unified score harness on Spectre."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
TASKS_ROOT = ROOT / "tasks"
NUMBERING_PLAN = ROOT / "reports" / "v4_task_family_numbering" / "numbering_plan.json"
TOOLCHAIN_LOCK = ROOT / "TOOLCHAIN_LOCK.json"
DEFAULT_EVIDENCE = ROOT / "reports" / "first_n_spectre" / "evidence.json"
DEFAULT_LOCAL_CACHE_ROOT = ROOT / "reports" / "first_n_spectre" / "cache"
DEFAULT_REMOTE_CACHE_ROOT = "vaevas-v4-spectre-cache"
ALLOWED_HOSTS = {"thu-wei", "thu-sui"}
CACHEABLE_STATUSES = {"PASS", "PASS_WITH_WARNINGS", "FAIL_BEHAVIOR", "FAIL_SIDE_EFFECT"}
SIMULATION_CACHE_INPUT_KEYS = (
    "task_id",
    "profile",
    "backend",
    "backend_sha256",
    "deck_sha256",
    "candidate_bundle_sha256",
    "public_support_bundle_sha256",
    "harness_spec_sha256",
    "profile_sha256",
    "spectre_mode",
)
SOURCE_SLUG_RE = re.compile(r"^[0-9]{3,4}-[A-Za-z0-9_.-]+$")
SPECTRE_INFRASTRUCTURE_OUTPUTS = {Path("spectre.out")}

RUNNERS_DIR = REPO_ROOT / "runners"
V4_RUNNERS_DIR = ROOT / "runners"
SCRIPTS_DIR = ROOT / "scripts"
for import_dir in (RUNNERS_DIR, V4_RUNNERS_DIR, SCRIPTS_DIR):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

from feedback_oracle import _validate_side_effect_contract  # noqa: E402
from evidence_fingerprints import (  # noqa: E402
    backend_fingerprints,
    checker_fingerprints,
    evidence_components,
    simulation_cache_inputs,
    task_input_fingerprints,
)
from generate_toolchain_lock import (  # noqa: E402
    benchmark_component_hashes,
    checker_registry_hash,
    inspect_spectre,
    inspect_ssh_route,
)
from render_v4_harness import build_profile, load_spec, render_scs  # noqa: E402
from run_batch1_spectre import extract_warning_lines, is_benign_warning  # noqa: E402
from run_gold_dual_suite import (  # noqa: E402
    default_bridge_repo,
    default_remote_work_root,
    normalize_spectre_mode,
    run_ssh_bytes,
    run_spectre_case,
    safe_extract_tar_bytes,
    tar_input_files,
)
from simulate_evas import CHECKS, evaluate_behavior_with_timeout  # noqa: E402


class SidecarError(RuntimeError):
    """Raised when an input violates the reproducible sidecar contract."""


@dataclass(frozen=True)
class MaterializedCase:
    canonical_id: str
    canonical_slug: str
    source_slug: str
    task_id: str
    title: str
    category: str
    level: str
    case_dir: Path
    deck_path: Path
    include_paths: tuple[Path, ...]
    checker_task_id: str
    checker_profile: dict[str, Any]
    side_output_files: tuple[str, ...]
    hashes: dict[str, Any]
    component_fingerprints: dict[str, Any]


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SidecarError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SidecarError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SidecarError(f"expected JSON object: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aggregate_hash(entries: Iterable[tuple[str, str]]) -> str:
    digest = hashlib.sha256()
    for relative, file_hash in sorted(entries):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def safe_relative_path(raw: str, *, label: str, suffix: str | None = None) -> Path:
    path = Path(raw.replace("\\", "/"))
    if not path.parts or path.is_absolute() or ".." in path.parts:
        raise SidecarError(f"unsafe {label} path: {raw!r}")
    if suffix is not None and path.suffix != suffix:
        raise SidecarError(f"{label} path must end with {suffix}: {raw!r}")
    return path


def safe_source_slug(raw: str) -> str:
    if not SOURCE_SLUG_RE.fullmatch(raw) or Path(raw).name != raw:
        raise SidecarError(f"unsafe old_dut_slug: {raw!r}")
    return raw


def safe_remote_cache_root(raw: str) -> str:
    path = PurePosixPath(raw)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise SidecarError(
            "--remote-cache-root must be a safe path relative to the remote home directory"
        )
    return path.as_posix()


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def validate_output_boundaries(
    *, tasks_root: Path, case_root: Path | None, evidence_output: Path, local_cache_root: Path
) -> None:
    protected = [
        tasks_root,
        ROOT / "tasks",
        ROOT / "operations",
        ROOT / "formal_tasks",
        ROOT / "formal_derivatives",
    ]
    for label, candidate in (
        ("case root", case_root),
        ("evidence output", evidence_output),
        ("local cache root", local_cache_root),
    ):
        if candidate is None:
            continue
        if any(is_within(candidate, root) for root in protected):
            raise SidecarError(f"{label} may not be inside a protected benchmark directory: {candidate}")


def normalize_canonical_ids(task_ids: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for raw in task_ids:
        text = str(raw)
        if not text.isdigit() or not 1 <= int(text) <= 400:
            raise SidecarError(f"--task must contain canonical ids in 001..400, observed {raw!r}")
        canonical_id = f"{int(text):03d}"
        if canonical_id in normalized:
            raise SidecarError(f"duplicate canonical task id: {canonical_id}")
        normalized.append(canonical_id)
    if not normalized:
        raise SidecarError("--task requires at least one canonical id")
    return normalized


def load_roster(
    numbering_plan_path: Path,
    first_n: int | None = None,
    *,
    task_ids: Iterable[str] | None = None,
) -> tuple[list[dict[str, Any]], str]:
    if (first_n is None) == (task_ids is None):
        raise SidecarError("select exactly one of --first-n or --task")
    if first_n is not None and not 1 <= first_n <= 400:
        raise SidecarError(f"--first-n must be in 1..400, observed {first_n}")
    plan = read_json(numbering_plan_path)
    if plan.get("schema_version") != "v4-task-family-numbering-plan-v1":
        raise SidecarError("unsupported numbering plan schema")
    rows = list(plan.get("rows") or [])
    for expected_index, row in enumerate(rows, start=1):
        expected_id = f"{expected_index:03d}"
        if row.get("canonical_index") != expected_index:
            raise SidecarError(
                f"numbering plan row {expected_index} has canonical_index={row.get('canonical_index')!r}"
            )
        if row.get("canonical_dut_id") != expected_id:
            raise SidecarError(
                f"numbering plan row {expected_index} has canonical_dut_id={row.get('canonical_dut_id')!r}"
            )
        safe_source_slug(str(row.get("old_dut_slug") or ""))
    if first_n is not None:
        if len(rows) < first_n:
            raise SidecarError(f"numbering plan has {len(rows)} rows, cannot select first {first_n}")
        selected = rows[:first_n]
    else:
        requested = normalize_canonical_ids(task_ids or [])
        by_id = {str(row["canonical_dut_id"]): row for row in rows}
        missing = [task_id for task_id in requested if task_id not in by_id]
        if missing:
            raise SidecarError(f"canonical task ids absent from numbering plan: {', '.join(missing)}")
        selected = [by_id[task_id] for task_id in requested]
    return selected, sha256_file(numbering_plan_path)


def load_toolchain(toolchain_lock_path: Path, host: str) -> tuple[dict[str, Any], str]:
    if host not in ALLOWED_HOSTS:
        raise SidecarError(f"unsupported Spectre host: {host}")
    lock = read_json(toolchain_lock_path)
    if lock.get("schema_version") != "v4-toolchain-lock-v1" or lock.get("status") != "valid":
        raise SidecarError("toolchain lock is not a valid v4 lock")
    spectre = lock.get("spectre") or {}
    if spectre.get("backend") != "sui-direct":
        raise SidecarError("first-N Spectre sidecar requires toolchain backend sui-direct")
    if spectre.get("remote_host") != host:
        raise SidecarError(
            f"toolchain host mismatch: lock={spectre.get('remote_host')!r}, requested={host!r}"
        )
    for key in ("route", "path", "version", "cadence_cshrc", "transport_identity"):
        if not str(spectre.get(key) or ""):
            raise SidecarError(f"toolchain lock lacks spectre.{key}")
    return lock, sha256_file(toolchain_lock_path)


def _declared_artifacts(family_spec: dict[str, Any]) -> list[Path]:
    files = ((family_spec.get("artifact_contract") or {}).get("files") or [])
    artifacts = [
        safe_relative_path(str(item.get("path") or ""), label="family artifact", suffix=".va")
        for item in files
    ]
    if not artifacts:
        raise SidecarError("family_spec declares no Verilog-A artifacts")
    if len(set(artifacts)) != len(artifacts):
        raise SidecarError("family_spec contains duplicate artifact paths")
    return artifacts


def _declared_support(
    family_spec: dict[str, Any], harness_spec: dict[str, Any]
) -> list[dict[str, Any]]:
    contract = family_spec.get("support_contract") or {}
    records = list(contract.get("files") or [])
    family_paths = [
        safe_relative_path(str(item.get("path") or ""), label="family support", suffix=".va")
        for item in records
    ]
    harness_support = harness_spec.get("support") or {}
    harness_paths = [
        safe_relative_path(str(item), label="harness support", suffix=".va")
        for item in harness_support.get("artifact_paths") or []
    ]
    if not records and not harness_paths:
        return []
    if contract.get("visibility") != "public_readonly":
        raise SidecarError("family support visibility must be public_readonly")
    if contract.get("source_root") != "public_support" or contract.get("mount_root") != "support":
        raise SidecarError("family support roots must be public_support -> support")
    if harness_support.get("source_root") != "./support":
        raise SidecarError("harness support source_root must be ./support")
    if family_paths != harness_paths:
        raise SidecarError(
            f"harness support {harness_paths!r} does not match family support {family_paths!r}"
        )
    if len(set(family_paths)) != len(family_paths):
        raise SidecarError("family_spec contains duplicate support paths")
    return records


def _side_output_files(checker_profile: dict[str, Any]) -> tuple[str, ...]:
    files = ((checker_profile.get("side_effect_contract") or {}).get("files") or [])
    paths = [
        safe_relative_path(str(item.get("path") or ""), label="side-effect output").as_posix()
        for item in files
    ]
    if len(set(paths)) != len(paths):
        raise SidecarError("checker profile contains duplicate side-effect output paths")
    return tuple(paths)


def validate_spectre_side_effect_contract(
    checker_profile: dict[str, Any], csv_path: Path, output_dir: Path
) -> tuple[bool, list[str]]:
    """Validate candidate files without treating Spectre-owned logs as DUT output."""
    contract = checker_profile.get("side_effect_contract") or {}
    exclusive_suffix = str(contract.get("exclusive_suffix") or "")
    profile = checker_profile
    if exclusive_suffix:
        profile = {
            **checker_profile,
            "side_effect_contract": {
                **contract,
                "exclusive_suffix": "",
            },
        }
    ok, notes = _validate_side_effect_contract(profile, csv_path, output_dir)
    if not exclusive_suffix:
        return ok, notes

    expected_paths = {Path(item) for item in _side_output_files(checker_profile)}
    observed_paths = {
        path.relative_to(output_dir)
        for path in output_dir.rglob(f"*{exclusive_suffix}")
        if path.is_file()
    }
    extra = sorted(
        path.as_posix()
        for path in observed_paths - expected_paths - SPECTRE_INFRASTRUCTURE_OUTPUTS
    )
    if extra:
        ok = False
        notes.append(f"side_effect_unexpected_files={','.join(extra)}")
    return ok, notes


def _verify_locked_components(toolchain_lock: dict[str, Any]) -> None:
    benchmark = toolchain_lock.get("benchmark") or {}
    required = (
        "checker_registry_sha256",
        "harness_generator_sha256",
        "oracle_runner_sha256",
    )
    missing = [key for key in required if not benchmark.get(key)]
    if missing:
        raise SidecarError(
            "toolchain release snapshot lacks required provenance: "
            + ", ".join(missing)
        )


def materialize_case(
    row: dict[str, Any],
    *,
    tasks_root: Path,
    case_dir: Path,
    toolchain_sha256: str,
    backend_hashes: dict[str, str] | None = None,
) -> MaterializedCase:
    canonical_id = str(row["canonical_dut_id"])
    source_slug = safe_source_slug(str(row["old_dut_slug"]))
    task_dir = (tasks_root / source_slug).resolve()
    if task_dir.parent != tasks_root.resolve():
        raise SidecarError(f"{source_slug}: resolved task path escapes tasks root")
    family_path = task_dir / "family_spec.json"
    harness_path = task_dir / "evaluator" / "harness_spec.json"
    checker_path = task_dir / "evaluator" / "checker_profile.json"
    family_spec = read_json(family_path)
    harness_spec, harness_sha256 = load_spec(harness_path)
    checker_profile = read_json(checker_path)
    family_sha256 = sha256_file(family_path)
    checker_profile_sha256 = sha256_file(checker_path)

    expected_task_id = f"v4-{canonical_id}"
    if family_spec.get("family_id") != canonical_id:
        raise SidecarError(
            f"{source_slug}: family_id={family_spec.get('family_id')!r}, expected {canonical_id!r}"
        )
    if (family_spec.get("task_ids") or {}).get("dut") != expected_task_id:
        raise SidecarError(f"{source_slug}: family_spec DUT id does not match {expected_task_id}")
    source_id = source_slug.split("-", 1)[0]
    if not source_id.isdigit():
        raise SidecarError(f"{source_slug}: source slug does not begin with a numeric id")
    harness_identity = (str(harness_spec.get("family_id") or ""), str(harness_spec.get("task_id") or ""))
    allowed_harness_identities = {
        (canonical_id, f"v4-{canonical_id}"),
        (source_id, f"v4-{source_id}"),
    }
    if harness_identity not in allowed_harness_identities:
        raise SidecarError(
            f"{source_slug}: harness identity {harness_identity!r} matches neither canonical "
            f"v4-{canonical_id} nor source v4-{source_id}"
        )
    source_contract = harness_spec.get("source_contract") or {}
    if source_contract.get("family_spec_sha256") != family_sha256:
        raise SidecarError(f"{source_slug}: harness source_contract has stale family_spec hash")
    if source_contract.get("checker_profile_sha256") != checker_profile_sha256:
        raise SidecarError(f"{source_slug}: harness source_contract has stale checker_profile hash")

    artifacts = _declared_artifacts(family_spec)
    harness_artifacts = [
        safe_relative_path(str(item), label="harness artifact", suffix=".va")
        for item in (harness_spec.get("candidate") or {}).get("artifact_paths") or []
    ]
    if harness_artifacts != artifacts:
        raise SidecarError(
            f"{source_slug}: harness artifacts {harness_artifacts!r} do not match family artifacts {artifacts!r}"
        )
    support_records = _declared_support(family_spec, harness_spec)

    profile = build_profile(harness_spec, "score", harness_sha256)
    recorded_profile_path = task_dir / "evaluator" / "profiles" / "score.json"
    recorded_profile = read_json(recorded_profile_path)
    if recorded_profile != profile:
        raise SidecarError(f"{source_slug}: stored score profile is stale relative to harness_spec")

    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)
    dut_dir = case_dir / "dut"
    artifact_hashes: list[dict[str, str]] = []
    support_hashes: list[dict[str, str]] = []
    include_paths: list[Path] = []
    for artifact in artifacts:
        source = task_dir / "solution" / artifact
        if not source.is_file():
            raise SidecarError(f"{source_slug}: missing declared gold artifact solution/{artifact}")
        if source.is_symlink():
            raise SidecarError(f"{source_slug}: gold artifact may not be a symlink: {artifact}")
        destination = dut_dir / artifact
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        source_hash = sha256_file(source)
        if sha256_file(destination) != source_hash:
            raise SidecarError(f"{source_slug}: copied artifact hash mismatch: {artifact}")
        artifact_hashes.append({"path": artifact.as_posix(), "sha256": source_hash})
        include_paths.append(destination)

    for item in support_records:
        support = safe_relative_path(
            str(item.get("path") or ""), label="public support", suffix=".va"
        )
        source = task_dir / "public_support" / support
        if not source.is_file() or source.is_symlink():
            raise SidecarError(f"{source_slug}: missing declared public support artifact {support}")
        source_hash = sha256_file(source)
        if source_hash != item.get("sha256"):
            raise SidecarError(
                f"{source_slug}: public support hash mismatch for {support}: "
                f"declared={item.get('sha256')} observed={source_hash}"
            )
        destination = case_dir / "support" / support
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if sha256_file(destination) != source_hash:
            raise SidecarError(f"{source_slug}: copied support hash mismatch: {support}")
        support_hashes.append({"path": support.as_posix(), "sha256": source_hash})
        include_paths.append(destination)

    deck_path = case_dir / "score.scs"
    deck_path.write_text(render_scs(harness_spec, profile), encoding="utf-8")
    checker_registry_sha256 = checker_registry_hash()
    gold_sha256 = aggregate_hash(
        (str(item["path"]), str(item["sha256"])) for item in artifact_hashes
    )
    support_sha256 = aggregate_hash(
        (str(item["path"]), str(item["sha256"])) for item in support_hashes
    )
    checker_task_id = str(checker_profile.get("checker_task_id") or "")
    if not checker_task_id:
        raise SidecarError(f"{source_slug}: checker_profile lacks checker_task_id")
    oracle_hashes = checker_fingerprints(
        checker_task_id,
        checker_profile,
        CHECKS.get(checker_task_id),
    )
    oracle_hashes["oracle_runner_sha256"] = benchmark_component_hashes()[
        "oracle_runner_sha256"
    ]
    checker_sha256 = aggregate_hash(
        [
            ("checker_profile", oracle_hashes["checker_profile_sha256"]),
            ("checker_binding", oracle_hashes["checker_binding_sha256"]),
            ("checker_implementation", oracle_hashes["checker_implementation_sha256"]),
        ]
    )
    hashes = {
        "deck_sha256": sha256_file(deck_path),
        "harness_spec_sha256": harness_sha256,
        "score_profile_sha256": sha256_file(recorded_profile_path),
        "family_spec_sha256": family_sha256,
        "gold_bundle_sha256": gold_sha256,
        "gold_artifacts": artifact_hashes,
        "public_support_bundle_sha256": support_sha256,
        "public_support_artifacts": support_hashes,
        "checker_sha256": checker_sha256,
        "checker_profile_sha256": checker_profile_sha256,
        "checker_registry_sha256": checker_registry_sha256,
        "toolchain_lock_sha256": toolchain_sha256,
        **(backend_hashes or {}),
    }
    components = evidence_components(
        task_inputs=task_input_fingerprints(family_spec=family_spec, hashes=hashes),
        oracle=oracle_hashes,
        backend=backend_hashes or {},
        release_snapshot_sha256=toolchain_sha256,
    )

    return MaterializedCase(
        canonical_id=canonical_id,
        canonical_slug=str(row["canonical_dut_slug"]),
        source_slug=source_slug,
        task_id=expected_task_id,
        title=str((family_spec.get("identity") or {}).get("title") or row.get("title") or ""),
        category=str((family_spec.get("identity") or {}).get("category") or row.get("category") or ""),
        level=str((family_spec.get("identity") or {}).get("level") or row.get("level") or ""),
        case_dir=case_dir,
        deck_path=deck_path,
        include_paths=tuple(include_paths),
        checker_task_id=checker_task_id,
        checker_profile=checker_profile,
        side_output_files=_side_output_files(checker_profile),
        hashes=hashes,
        component_fingerprints=components,
    )


def cache_inputs(case: MaterializedCase, *, mode: str) -> dict[str, str]:
    return simulation_cache_inputs(
        task_id=case.task_id,
        profile="score",
        backend="spectre",
        backend_sha256=str(case.hashes.get("spectre_sha256") or case.hashes.get("spectre_backend_sha256") or ""),
        hashes=case.hashes,
        spectre_mode=mode,
    )


def cache_key(case: MaterializedCase, *, mode: str) -> str:
    encoded = json.dumps(
        cache_inputs(case, mode=mode), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def cache_entry_path(root: Path, case: MaterializedCase, key: str) -> Path:
    return root / case.canonical_id / "score" / key


def legacy_cache_task_root(root: Path, case: MaterializedCase) -> Path:
    return root / case.canonical_id / "score"


def cache_metadata(
    case: MaterializedCase,
    *,
    mode: str,
    key: str,
    local_entry: Path,
    remote_root: str,
    hit: bool,
    source: str,
    cacheable: bool,
) -> dict[str, Any]:
    return {
        "key": key,
        "profile": "score",
        "inputs": cache_inputs(case, mode=mode),
        "hit": hit,
        "source": source,
        "cacheable": cacheable,
        "local_entry": str(local_entry),
        "remote_entry": (
            f"$HOME/{remote_root}/{case.canonical_id}/score/{key}"
            if remote_root
            else ""
        ),
        "notes": [],
    }


def refresh_cached_derived_evidence(
    row: dict[str, Any],
    *,
    checker_profile: dict[str, Any],
    side_output_files: tuple[str, ...],
    local_entry: Path,
    checker_task_id: str = "",
    timeout_s: int = 30,
) -> None:
    """Recompute policy-derived fields from immutable cached simulator outputs."""
    output_dir = local_entry / "spectre"
    csv_path = output_dir / "tran_spectre.csv"
    result_path = output_dir / "spectre_result.json"
    if not csv_path.is_file():
        row["cache"]["notes"].append("cached_raw_trace_missing; derived evidence unchanged")
        return

    spectre_result = read_json(result_path) if result_path.is_file() else {"warnings": []}
    warnings = extract_warning_lines(output_dir, spectre_result)
    benign = [line for line in warnings if is_benign_warning(line)]
    untriaged = [line for line in warnings if not is_benign_warning(line)]
    row["spectre"]["warnings"] = warnings
    row["spectre"]["benign_warnings"] = benign
    row["spectre"]["untriaged_warnings"] = untriaged

    effective_checker_task_id = checker_task_id or str(
        checker_profile.get("checker_task_id") or ""
    )
    if effective_checker_task_id:
        score, behavior_notes = evaluate_behavior_with_timeout(
            effective_checker_task_id,
            csv_path,
            timeout_s=timeout_s,
            checks_config=checker_profile,
        )
        row["behavior"] = {
            "ran": True,
            "score": float(score),
            "notes": [str(item) for item in behavior_notes],
        }
    else:
        score = float((row.get("behavior") or {}).get("score") or 0.0)

    side_ok, side_notes = validate_spectre_side_effect_contract(
        checker_profile, csv_path, output_dir
    )
    row["side_effect"] = {
        "required": bool(side_output_files),
        "expected_files": list(side_output_files),
        "ran": True,
        "pass": bool(side_ok),
        "notes": [str(item) for item in side_notes],
    }
    if float(score) < 1.0:
        row["status"] = "FAIL_BEHAVIOR"
    elif not side_ok:
        row["status"] = "FAIL_SIDE_EFFECT"
    elif untriaged:
        row["status"] = "PASS_WITH_WARNINGS"
    else:
        row["status"] = "PASS"
    row["cache"]["notes"].append(
        "behavior, warning, and side-effect evidence rederived from cached raw outputs"
    )


def load_local_cache(
    case: MaterializedCase,
    *,
    mode: str,
    key: str,
    local_entry: Path,
    remote_root: str,
    source: str,
    timeout_s: int,
) -> dict[str, Any] | None:
    manifest_path = local_entry / "cache_manifest.json"
    evidence_path = local_entry / "row_evidence.json"
    if not manifest_path.is_file() or not evidence_path.is_file():
        return None
    try:
        manifest = read_json(manifest_path)
        row = read_json(evidence_path)
    except SidecarError:
        return None
    expected_inputs = cache_inputs(case, mode=mode)
    if (
        manifest.get("schema_version") != "v4-spectre-cache-entry-v1"
        or manifest.get("cache_key") != key
        or manifest.get("inputs") != expected_inputs
        or manifest.get("row_status") not in CACHEABLE_STATUSES
        or row.get("status") != manifest.get("row_status")
    ):
        return None
    row["cache"] = cache_metadata(
        case,
        mode=mode,
        key=key,
        local_entry=local_entry,
        remote_root=remote_root,
        hit=True,
        source=source,
        cacheable=True,
    )
    migrated_from = manifest.get("migrated_from")
    if isinstance(migrated_from, dict):
        source_entry = str(migrated_from.get("entry") or "")
        source_key = str(migrated_from.get("cache_key") or "")
        row["cache"]["notes"].append(
            f"migrated_from_legacy_cache entry={source_entry} cache_key={source_key}"
        )
    row["materialization"]["case_dir"] = str(local_entry)
    row["materialization"]["deck_path"] = str(local_entry / "score.scs")
    row["materialization"]["retained"] = True
    old_snapshot = ((row.get("component_fingerprints") or {}).get("assembly") or {}).get(
        "release_snapshot_sha256"
    ) or (row.get("hashes") or {}).get("toolchain_lock_sha256")
    row["component_fingerprints"] = json.loads(json.dumps(case.component_fingerprints))
    row["component_fingerprints"]["state"] = "carried_forward"
    row["component_fingerprints"]["assembly"][
        "carried_from_release_snapshot_sha256"
    ] = old_snapshot
    refresh_cached_derived_evidence(
        row,
        checker_profile=case.checker_profile,
        side_output_files=case.side_output_files,
        local_entry=local_entry,
        checker_task_id=case.checker_task_id,
        timeout_s=timeout_s,
    )
    return row


def _legacy_cache_created_at(entry: Path, manifest: dict[str, Any]) -> tuple[float, str]:
    raw_created = str(manifest.get("created_at") or "")
    try:
        normalized = raw_created.replace("Z", "+00:00")
        timestamp = datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        try:
            timestamp = (entry / "cache_manifest.json").stat().st_mtime
        except OSError:
            timestamp = 0.0
    return timestamp, entry.as_posix()


def _legacy_observed_inputs(row: dict[str, Any], manifest: dict[str, Any]) -> dict[str, str]:
    for candidate in (
        manifest.get("inputs"),
        (row.get("cache") or {}).get("inputs"),
    ):
        if isinstance(candidate, dict):
            return {str(key): str(value) for key, value in candidate.items()}
    hashes = row.get("hashes") or {}
    identity = row.get("spectre_identity") or {}
    return {
        "task_id": str(row.get("task_id") or ""),
        "profile": "score",
        "backend": "spectre",
        "backend_sha256": str(
            hashes.get("spectre_sha256")
            or hashes.get("spectre_backend_sha256")
            or ""
        ),
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
        "spectre_mode": str(identity.get("mode") or ""),
    }


def _legacy_cache_matches_current_simulation(
    case: MaterializedCase,
    *,
    mode: str,
    row: dict[str, Any],
    manifest: dict[str, Any],
) -> bool:
    expected = cache_inputs(case, mode=mode)
    observed = _legacy_observed_inputs(row, manifest)
    for key in SIMULATION_CACHE_INPUT_KEYS:
        if observed.get(key) != expected.get(key):
            return False
    return True


def migrate_legacy_local_cache(
    case: MaterializedCase,
    *,
    mode: str,
    key: str,
    legacy_root: Path,
    local_entry: Path,
) -> bool:
    """Promote the newest matching legacy per-task score cache entry to the current key."""
    if local_entry.exists():
        return False
    task_root = legacy_cache_task_root(legacy_root, case)
    if not task_root.is_dir():
        return False
    candidates: list[tuple[float, str, Path, dict[str, Any], dict[str, Any]]] = []
    for entry in task_root.iterdir():
        if not entry.is_dir() or entry.resolve() == local_entry.resolve():
            continue
        manifest_path = entry / "cache_manifest.json"
        evidence_path = entry / "row_evidence.json"
        raw_trace_path = entry / "spectre" / "tran_spectre.csv"
        if not manifest_path.is_file() or not evidence_path.is_file() or not raw_trace_path.is_file():
            continue
        try:
            manifest = read_json(manifest_path)
            row = read_json(evidence_path)
        except SidecarError:
            continue
        status = str(manifest.get("row_status") or row.get("status") or "")
        if status not in CACHEABLE_STATUSES or row.get("status") != status:
            continue
        if not _legacy_cache_matches_current_simulation(
            case, mode=mode, row=row, manifest=manifest
        ):
            continue
        created_at, path_token = _legacy_cache_created_at(entry, manifest)
        candidates.append((created_at, path_token, entry, manifest, row))
    if not candidates:
        return False

    _, _, source_entry, source_manifest, source_row = sorted(
        candidates, key=lambda item: (-item[0], item[1])
    )[0]
    local_entry.parent.mkdir(parents=True, exist_ok=True)
    staging = local_entry.parent / f".legacy-{key}-{os.getpid()}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(source_entry, staging)
    write_json(
        staging / "cache_manifest.json",
        {
            "schema_version": "v4-spectre-cache-entry-v1",
            "cache_key": key,
            "created_at": now_utc(),
            "canonical_id": case.canonical_id,
            "task_id": case.task_id,
            "profile": "score",
            "inputs": cache_inputs(case, mode=mode),
            "row_status": source_row["status"],
            "migrated_from": {
                "entry": str(source_entry),
                "cache_key": str(source_manifest.get("cache_key") or source_entry.name),
                "created_at": str(source_manifest.get("created_at") or ""),
                "schema_version": str(source_manifest.get("schema_version") or ""),
            },
        },
    )
    if local_entry.exists():
        shutil.rmtree(local_entry)
    os.replace(staging, local_entry)
    return True


def persist_local_cache(
    case: MaterializedCase,
    record: dict[str, Any],
    *,
    mode: str,
    key: str,
    local_entry: Path,
    remote_root: str,
) -> None:
    local_entry.parent.mkdir(parents=True, exist_ok=True)
    staging = local_entry.parent / f".tmp-{key}-{os.getpid()}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(case.case_dir, staging)
    stored_record = json.loads(json.dumps(record))
    stored_record["cache"] = cache_metadata(
        case,
        mode=mode,
        key=key,
        local_entry=local_entry,
        remote_root=remote_root,
        hit=False,
        source="none",
        cacheable=True,
    )
    stored_record["materialization"]["case_dir"] = "."
    stored_record["materialization"]["deck_path"] = "score.scs"
    stored_record["materialization"]["retained"] = True
    write_json(staging / "row_evidence.json", stored_record)
    write_json(
        staging / "cache_manifest.json",
        {
            "schema_version": "v4-spectre-cache-entry-v1",
            "cache_key": key,
            "created_at": now_utc(),
            "canonical_id": case.canonical_id,
            "task_id": case.task_id,
            "profile": "score",
            "inputs": cache_inputs(case, mode=mode),
            "row_status": record["status"],
        },
    )
    if local_entry.exists():
        shutil.rmtree(local_entry)
    os.replace(staging, local_entry)


def fetch_remote_cache(
    *,
    host: str,
    remote_root: str,
    case: MaterializedCase,
    key: str,
    local_entry: Path,
    timeout_s: int,
    ssh_runner: Callable[..., Any] = run_ssh_bytes,
) -> bool:
    root = safe_remote_cache_root(remote_root)
    relative = f"{case.canonical_id}/score/{key}"
    script = (
        "set -euo pipefail; "
        f"entry=\"$HOME\"/{shlex.quote(root)}/{shlex.quote(relative)}; "
        "test -f \"$entry/cache_manifest.json\" || exit 44; "
        "tar -C \"$entry\" -czf - ."
    )
    completed = ssh_runner(host, script, timeout_s=timeout_s)
    if completed.returncode == 44:
        return False
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace")
        raise SidecarError(f"remote cache fetch failed: {stderr[-1000:]}")
    staging = local_entry.parent / f".remote-{key}-{os.getpid()}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    safe_extract_tar_bytes(completed.stdout, staging)
    if local_entry.exists():
        shutil.rmtree(local_entry)
    os.replace(staging, local_entry)
    return True


def persist_remote_cache(
    *,
    host: str,
    remote_root: str,
    case: MaterializedCase,
    key: str,
    local_entry: Path,
    timeout_s: int,
    refresh: bool,
    ssh_runner: Callable[..., Any] = run_ssh_bytes,
) -> None:
    root = safe_remote_cache_root(remote_root)
    relative = f"{case.canonical_id}/score/{key}"
    files = [path for path in local_entry.rglob("*") if path.is_file()]
    payload = tar_input_files(files, local_entry)
    refresh_command = "rm -rf \"$entry\"; " if refresh else ""
    script = (
        "set -euo pipefail; "
        f"root=\"$HOME\"/{shlex.quote(root)}; "
        f"entry=\"$root\"/{shlex.quote(relative)}; "
        f"tmp=\"$root/.tmp-{case.canonical_id}-{key}-{os.getpid()}\"; "
        "mkdir -p \"$(dirname \"$entry\")\"; rm -rf \"$tmp\"; mkdir -p \"$tmp\"; "
        "tar -xzf - -C \"$tmp\"; "
        + refresh_command
        + "if [ -e \"$entry\" ]; then rm -rf \"$tmp\"; else mv \"$tmp\" \"$entry\"; fi"
    )
    completed = ssh_runner(host, script, timeout_s=timeout_s, input_data=payload)
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace")
        raise SidecarError(f"remote cache persist failed: {stderr[-1000:]}")


def _identity(
    toolchain_lock: dict[str, Any], *, host: str, mode: str, verification: str
) -> dict[str, str]:
    spectre = toolchain_lock["spectre"]
    return {
        "backend": "sui-direct",
        "mode": mode,
        "host": host,
        "route": str(spectre["route"]),
        "path": str(spectre["path"]),
        "version": str(spectre["version"]),
        "cadence_cshrc": str(spectre["cadence_cshrc"]),
        "transport_identity": str(spectre["transport_identity"]),
        "verification": verification,
    }


def probe_remote_identity(
    toolchain_lock: dict[str, Any], *, host: str, mode: str
) -> dict[str, str]:
    locked = toolchain_lock["spectre"]
    observed_spectre = inspect_spectre(host, str(locked["cadence_cshrc"]))
    observed_route = inspect_ssh_route(host)
    expected = {
        "path": str(locked["path"]),
        "version": str(locked["version"]),
        "route": str(locked["route"]),
        "transport_identity": str(locked["transport_identity"]),
    }
    observed = {**observed_spectre, **observed_route}
    mismatches = [
        f"{key}: lock={value!r} remote={observed.get(key)!r}"
        for key, value in expected.items()
        if observed.get(key) != value
    ]
    if mismatches:
        raise SidecarError("remote Spectre identity differs from toolchain lock: " + "; ".join(mismatches))
    return _identity(toolchain_lock, host=host, mode=mode, verification="remote_probe_match")


def _base_record(case: MaterializedCase, identity: dict[str, str], *, retained: bool) -> dict[str, Any]:
    return {
        "canonical_id": case.canonical_id,
        "canonical_slug": case.canonical_slug,
        "source_slug": case.source_slug,
        "task_id": case.task_id,
        "title": case.title,
        "category": case.category,
        "level": case.level,
        "status": "DRY_RUN",
        "materialization": {
            "status": "complete",
            "case_dir": str(case.case_dir),
            "retained": retained,
            "deck_path": str(case.deck_path),
            "artifact_paths": [item["path"] for item in case.hashes["gold_artifacts"]],
            "notes": [],
        },
        "hashes": case.hashes,
        "component_fingerprints": case.component_fingerprints,
        "spectre_identity": identity,
        "spectre": {
            "ran": False,
            "ok": None,
            "rows": 0,
            "signals": [],
            "errors": [],
            "warnings": [],
            "benign_warnings": [],
            "untriaged_warnings": [],
            "remote_run_dir": "",
            "timing": {},
            "wall_time_s": 0.0,
        },
        "behavior": {"ran": False, "score": None, "notes": []},
        "side_effect": {
            "required": bool(case.side_output_files),
            "expected_files": list(case.side_output_files),
            "ran": False,
            "pass": None,
            "notes": [],
        },
        "cache": {},
    }


def run_materialized_case(
    case: MaterializedCase,
    *,
    toolchain_lock: dict[str, Any],
    host: str,
    mode: str,
    timeout_s: int,
    sui_work_root: str | None,
    keep_case_dir: bool,
    runner: Callable[..., dict[str, Any]] = run_spectre_case,
) -> dict[str, Any]:
    identity = _identity(
        toolchain_lock, host=host, mode=mode, verification="remote_probe_match"
    )
    record = _base_record(case, identity, retained=keep_case_dir)
    output_dir = case.case_dir / "spectre"
    started = time.perf_counter()
    result = runner(
        task_id=f"{case.task_id}:score:gold",
        tb_path=case.deck_path,
        include_paths=list(case.include_paths),
        output_dir=output_dir,
        bridge_repo=default_bridge_repo(),
        cadence_cshrc=identity["cadence_cshrc"],
        timeout_s=timeout_s,
        side_output_files=case.side_output_files,
        spectre_backend="sui-direct",
        sui_host=host,
        sui_work_root=sui_work_root,
        spectre_mode=mode,
    )
    wall_time_s = round(time.perf_counter() - started, 6)
    csv_path = output_dir / "tran_spectre.csv"
    warnings = extract_warning_lines(output_dir, result)
    benign = [line for line in warnings if is_benign_warning(line)]
    untriaged = [line for line in warnings if not is_benign_warning(line)]
    record["spectre"] = {
        "ran": True,
        "ok": bool(result.get("ok")),
        "rows": int(result.get("rows") or 0),
        "signals": [str(item) for item in result.get("signals") or []],
        "errors": [str(item) for item in result.get("errors") or []],
        "warnings": warnings,
        "benign_warnings": benign,
        "untriaged_warnings": untriaged,
        "remote_run_dir": str(result.get("remote_run_dir") or ""),
        "timing": dict(result.get("timing") or {}),
        "wall_time_s": wall_time_s,
    }

    if result.get("ok") and csv_path.is_file():
        score, notes = evaluate_behavior_with_timeout(
            case.checker_task_id,
            csv_path,
            timeout_s=timeout_s,
            checks_config=case.checker_profile,
        )
        record["behavior"] = {
            "ran": True,
            "score": float(score),
            "notes": [str(item) for item in notes],
        }
        side_ok, side_notes = validate_spectre_side_effect_contract(
            case.checker_profile, csv_path, output_dir
        )
        record["side_effect"] = {
            "required": bool(case.side_output_files),
            "expected_files": list(case.side_output_files),
            "ran": True,
            "pass": bool(side_ok),
            "notes": [str(item) for item in side_notes],
        }
        if score < 1.0:
            record["status"] = "FAIL_BEHAVIOR"
        elif not side_ok:
            record["status"] = "FAIL_SIDE_EFFECT"
        elif untriaged:
            record["status"] = "PASS_WITH_WARNINGS"
        else:
            record["status"] = "PASS"
    else:
        record["status"] = "FAIL_SPECTRE"
        record["behavior"]["notes"] = [
            "Spectre did not produce a successful tran_spectre.csv"
        ]
    return record


def failure_record(
    row: dict[str, Any],
    *,
    toolchain_sha256: str,
    identity: dict[str, str],
    error: Exception,
) -> dict[str, Any]:
    canonical_id = str(row.get("canonical_dut_id") or "")
    source_slug = str(row.get("old_dut_slug") or "")
    return {
        "canonical_id": canonical_id,
        "canonical_slug": str(row.get("canonical_dut_slug") or ""),
        "source_slug": source_slug,
        "task_id": f"v4-{canonical_id}",
        "title": str(row.get("title") or ""),
        "category": str(row.get("category") or ""),
        "level": str(row.get("level") or ""),
        "status": "FAIL_RUNNER",
        "materialization": {
            "status": "fail",
            "case_dir": "",
            "retained": False,
            "deck_path": "",
            "artifact_paths": [],
            "notes": [f"{type(error).__name__}: {str(error)[:1000]}"],
        },
        "hashes": {
            "deck_sha256": "",
            "harness_spec_sha256": "",
            "score_profile_sha256": "",
            "family_spec_sha256": "",
            "gold_bundle_sha256": "",
            "gold_artifacts": [],
            "public_support_bundle_sha256": "",
            "public_support_artifacts": [],
            "checker_sha256": "",
            "checker_profile_sha256": "",
            "checker_registry_sha256": "",
            "toolchain_lock_sha256": toolchain_sha256,
        },
        "spectre_identity": identity,
        "spectre": {
            "ran": False,
            "ok": None,
            "rows": 0,
            "signals": [],
            "errors": [f"{type(error).__name__}: {str(error)[:1000]}"],
            "warnings": [],
            "benign_warnings": [],
            "untriaged_warnings": [],
            "remote_run_dir": "",
            "timing": {},
            "wall_time_s": 0.0,
        },
        "behavior": {"ran": False, "score": None, "notes": []},
        "side_effect": {
            "required": False,
            "expected_files": [],
            "ran": False,
            "pass": None,
            "notes": [],
        },
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


def summarize(
    rows: list[dict[str, Any]], *, dry_run: bool, requested_rows: int
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    total = len(rows)
    materialized = sum(1 for row in rows if row["materialization"]["status"] == "complete")
    behavior_pass = sum(
        1 for row in rows if row["behavior"]["score"] is not None and row["behavior"]["score"] >= 1.0
    )
    side_effect_pass = sum(
        1
        for row in rows
        if row["side_effect"]["required"] and row["side_effect"]["pass"] is True
    )
    return {
        "requested_rows": requested_rows,
        "selected_rows": total,
        "materialized_rows": materialized,
        "executed_rows": sum(
            1 for row in rows if row["spectre"]["ran"] and not row.get("cache", {}).get("hit")
        ),
        "cache_hit_rows": sum(1 for row in rows if row.get("cache", {}).get("hit")),
        "passed_rows": sum(1 for row in rows if row["status"] == "PASS"),
        "failed_rows": sum(1 for row in rows if row["status"].startswith("FAIL")),
        "spectre_ok_rows": sum(1 for row in rows if row["spectre"]["ok"] is True),
        "behavior_pass_rows": behavior_pass,
        "side_effect_required_rows": sum(1 for row in rows if row["side_effect"]["required"]),
        "side_effect_pass_rows": side_effect_pass,
        "warning_count": sum(len(row["spectre"]["warnings"]) for row in rows),
        "untriaged_warning_count": sum(
            len(row["spectre"]["untriaged_warnings"]) for row in rows
        ),
        "total_wall_time_s": round(
            sum(
                row["spectre"]["wall_time_s"]
                for row in rows
                if not row.get("cache", {}).get("hit")
            ),
            6,
        ),
        "status_counts": status_counts,
        "all_pass": bool(total) and (
            materialized == total if dry_run else all(row["status"] == "PASS" for row in rows)
        ),
    }


def execute(
    *,
    first_n: int | None,
    task_ids: Iterable[str] | None = None,
    numbering_plan_path: Path,
    tasks_root: Path,
    toolchain_lock_path: Path,
    evidence_output: Path,
    host: str,
    mode: str,
    timeout_s: int,
    case_root: Path | None,
    keep_case_dirs: bool,
    dry_run: bool,
    fail_fast: bool,
    sui_work_root: str | None,
    cache_enabled: bool = False,
    refresh_cache: bool = False,
    local_cache_root: Path = DEFAULT_LOCAL_CACHE_ROOT,
    legacy_cache_root: Path | None = None,
    remote_cache_root: str = "",
    cache_ssh_runner: Callable[..., Any] = run_ssh_bytes,
    runner: Callable[..., dict[str, Any]] = run_spectre_case,
    identity_probe: Callable[..., dict[str, str]] = probe_remote_identity,
) -> dict[str, Any]:
    started_at = now_utc()
    mode = normalize_spectre_mode(mode)
    roster, numbering_sha256 = load_roster(
        numbering_plan_path, first_n, task_ids=task_ids
    )
    requested_rows = first_n if first_n is not None else len(roster)
    local_cache_root = local_cache_root.resolve()
    legacy_cache_root = legacy_cache_root.resolve() if legacy_cache_root else None
    validate_output_boundaries(
        tasks_root=tasks_root,
        case_root=case_root,
        evidence_output=evidence_output,
        local_cache_root=local_cache_root,
    )
    if cache_enabled and remote_cache_root:
        remote_cache_root = safe_remote_cache_root(remote_cache_root)
    toolchain, toolchain_sha256 = load_toolchain(toolchain_lock_path, host)
    _verify_locked_components(toolchain)
    identity = (
        _identity(toolchain, host=host, mode=mode, verification="not_probed_dry_run")
        if dry_run
        else identity_probe(toolchain, host=host, mode=mode)
    )
    backend_hashes = backend_fingerprints(
        toolchain,
        spectre_mode=mode,
        spectre_identity=identity,
    )
    effective_work_root = case_root or Path(tempfile.mkdtemp(prefix="v4_first_n_spectre_"))
    created_root = case_root is None
    effective_work_root.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    try:
        for row in roster:
            canonical_id = str(row["canonical_dut_id"])
            case_dir = effective_work_root / f"{canonical_id}-{row['old_dut_slug']}"
            try:
                case = materialize_case(
                    row,
                    tasks_root=tasks_root,
                    case_dir=case_dir,
                    toolchain_sha256=toolchain_sha256,
                    backend_hashes=backend_hashes,
                )
                if dry_run:
                    record = _base_record(case, identity, retained=keep_case_dirs)
                    key = cache_key(case, mode=mode)
                    record["cache"] = cache_metadata(
                        case,
                        mode=mode,
                        key=key,
                        local_entry=cache_entry_path(local_cache_root, case, key),
                        remote_root=remote_cache_root,
                        hit=False,
                        source="none",
                        cacheable=False,
                    )
                else:
                    key = cache_key(case, mode=mode)
                    local_entry = cache_entry_path(local_cache_root, case, key)
                    record = None
                    if cache_enabled and not refresh_cache:
                        record = load_local_cache(
                            case,
                            mode=mode,
                            key=key,
                            local_entry=local_entry,
                            remote_root=remote_cache_root,
                            source="local",
                            timeout_s=timeout_s,
                        )
                        if record is None and legacy_cache_root is not None:
                            if migrate_legacy_local_cache(
                                case,
                                mode=mode,
                                key=key,
                                legacy_root=legacy_cache_root,
                                local_entry=local_entry,
                            ):
                                record = load_local_cache(
                                    case,
                                    mode=mode,
                                    key=key,
                                    local_entry=local_entry,
                                    remote_root=remote_cache_root,
                                    source="local",
                                    timeout_s=timeout_s,
                                )
                        if record is None and remote_cache_root:
                            if fetch_remote_cache(
                                host=host,
                                remote_root=remote_cache_root,
                                case=case,
                                key=key,
                                local_entry=local_entry,
                                timeout_s=timeout_s,
                                ssh_runner=cache_ssh_runner,
                            ):
                                record = load_local_cache(
                                    case,
                                    mode=mode,
                                    key=key,
                                    local_entry=local_entry,
                                    remote_root=remote_cache_root,
                                    source="remote",
                                    timeout_s=timeout_s,
                                )
                    if record is None:
                        record = run_materialized_case(
                            case,
                            toolchain_lock=toolchain,
                            host=host,
                            mode=mode,
                            timeout_s=timeout_s,
                            sui_work_root=sui_work_root,
                            keep_case_dir=keep_case_dirs,
                            runner=runner,
                        )
                        cacheable = cache_enabled and record["status"] in CACHEABLE_STATUSES
                        if cacheable:
                            persist_local_cache(
                                case,
                                record,
                                mode=mode,
                                key=key,
                                local_entry=local_entry,
                                remote_root=remote_cache_root,
                            )
                            if remote_cache_root:
                                persist_remote_cache(
                                    host=host,
                                    remote_root=remote_cache_root,
                                    case=case,
                                    key=key,
                                    local_entry=local_entry,
                                    timeout_s=timeout_s,
                                    refresh=refresh_cache,
                                    ssh_runner=cache_ssh_runner,
                                )
                        record["cache"] = cache_metadata(
                            case,
                            mode=mode,
                            key=key,
                            local_entry=local_entry,
                            remote_root=remote_cache_root,
                            hit=False,
                            source="none",
                            cacheable=cacheable,
                        )
            except Exception as exc:
                record = failure_record(
                    row,
                    toolchain_sha256=toolchain_sha256,
                    identity=identity,
                    error=exc,
                )
            records.append(record)
            print(
                json.dumps(
                    {
                        "canonical_id": record["canonical_id"],
                        "source_slug": record["source_slug"],
                        "status": record["status"],
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            if not keep_case_dirs and case_dir.exists():
                shutil.rmtree(case_dir)
            if record["status"].startswith("FAIL") and fail_fast:
                break
    finally:
        if created_root and not keep_case_dirs and effective_work_root.exists():
            shutil.rmtree(effective_work_root)

    summary = summarize(records, dry_run=dry_run, requested_rows=requested_rows)
    if dry_run and summary["all_pass"]:
        status = "dry_run_materialized"
    elif not dry_run and summary["all_pass"]:
        status = "pass"
    elif not dry_run and summary["passed_rows"]:
        status = "partial_failure"
    else:
        status = "fail"
    payload = {
        "schema_version": "v4-first-n-spectre-evidence-v2",
        "evidence_policy": "v4-dependency-scoped-evidence-v2",
        "generated_at": now_utc(),
        "status": status,
        "dry_run": dry_run,
        "numbering_plan": {
            "path": str(numbering_plan_path),
            "sha256": numbering_sha256,
            "schema_version": "v4-task-family-numbering-plan-v1",
            "selection_mode": "first_n" if first_n is not None else "task_ids",
            "requested_first_n": first_n,
            "requested_task_ids": normalize_canonical_ids(task_ids or []) if task_ids is not None else [],
            "selected_rows": len(roster),
        },
        "toolchain_lock": {
            "path": str(toolchain_lock_path),
            "sha256": toolchain_sha256,
            "schema_version": "v4-toolchain-lock-v1",
            "status": "valid",
        },
        "execution": {
            "script": "scripts/run_v4_first_n_spectre.py",
            "script_sha256": sha256_file(Path(__file__)),
            "runner_api": "runners.run_gold_dual_suite.run_spectre_case",
            "host": host,
            "backend": "sui-direct",
            "mode": mode,
            "route": identity["route"],
            "timeout_s": timeout_s,
            "sui_work_root": sui_work_root or default_remote_work_root("sui-direct"),
            "case_root": str(effective_work_root),
            "output_path": str(evidence_output),
            "keep_case_dirs": keep_case_dirs,
            "fail_fast": fail_fast,
            "cache_enabled": cache_enabled,
            "refresh_cache": refresh_cache,
            "local_cache_root": str(local_cache_root),
            "remote_cache_root": remote_cache_root,
            "started_at": started_at,
            "finished_at": now_utc(),
            "argv": list(sys.argv),
        },
        "summary": summary,
        "rows": records,
    }
    write_json(evidence_output, payload)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--first-n", type=int)
    selection.add_argument("--task", dest="task_ids", action="append")
    parser.add_argument("--numbering-plan", type=Path, default=NUMBERING_PLAN)
    parser.add_argument("--tasks-root", type=Path, default=TASKS_ROOT)
    parser.add_argument("--toolchain-lock", type=Path, default=TOOLCHAIN_LOCK)
    parser.add_argument("--evidence-output", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--host", choices=sorted(ALLOWED_HOSTS), default="thu-wei")
    parser.add_argument("--mode", default=os.environ.get("VAEVAS_SPECTRE_MODE", "ax"))
    parser.add_argument("--timeout-s", type=int, default=300)
    parser.add_argument("--case-root", type=Path)
    parser.add_argument("--keep-case-dirs", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--sui-work-root")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--refresh-cache", action="store_true")
    parser.add_argument("--local-cache-root", type=Path, default=DEFAULT_LOCAL_CACHE_ROOT)
    parser.add_argument("--legacy-cache-root", type=Path)
    parser.add_argument("--remote-cache-root", default=DEFAULT_REMOTE_CACHE_ROOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = execute(
            first_n=args.first_n,
            task_ids=args.task_ids,
            numbering_plan_path=args.numbering_plan.resolve(),
            tasks_root=args.tasks_root.resolve(),
            toolchain_lock_path=args.toolchain_lock.resolve(),
            evidence_output=args.evidence_output.resolve(),
            host=args.host,
            mode=args.mode,
            timeout_s=args.timeout_s,
            case_root=args.case_root.resolve() if args.case_root else None,
            keep_case_dirs=args.keep_case_dirs,
            dry_run=args.dry_run,
            fail_fast=args.fail_fast,
            sui_work_root=args.sui_work_root,
            cache_enabled=not args.no_cache,
            refresh_cache=args.refresh_cache,
            local_cache_root=args.local_cache_root,
            legacy_cache_root=args.legacy_cache_root,
            remote_cache_root=args.remote_cache_root,
        )
    except SidecarError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if payload["status"] in {"pass", "dry_run_materialized"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
