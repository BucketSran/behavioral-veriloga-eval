#!/usr/bin/env python3
"""Materialize the immutable V4 experiment-result protocol."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any


SCHEMA_VERSION = "vabench-experiment-result-v2"
FAILURE_TAXONOMY_SCHEMA_VERSION = "vabench-failure-taxonomy-v1"
FAILURE_CLASSES = {
    "invalid",
    "compile",
    "runtime",
    "functional",
    "mutation_survival",
    "property",
    "timeout",
    "resource_exhaustion",
    "behavior_unspecified",
    "infrastructure",
}
FAILURE_STAGES = {
    "not_run",
    "completed",
    "model_execution",
    "artifact_gate",
    "compilation",
    "simulation",
    "functional_check",
    "mutation_check",
    "property_check",
    "behavior_check",
    "infrastructure",
    "not_scored",
}
FAILURE_RESPONSIBILITIES = {
    "none",
    "candidate",
    "model",
    "system",
    "undetermined",
}
FAILURE_TAXONOMY_FIELDS = {
    "schema_version",
    "primary_class",
    "secondary_classes",
    "stage",
    "responsibility",
    "retryable",
    "case_ids",
    "property_ids",
    "mutation_ids",
}
REPLAY_FAILURE_CLASSES = {
    "not_run": {None},
    "passed": {None},
    "compile_failure": {"compile"},
    "runtime_failure": {"runtime", "timeout"},
    "behavior_failure": {
        "functional",
        "mutation_survival",
        "property",
        "behavior_unspecified",
    },
    "infrastructure_failure": {"infrastructure"},
}
REPLAY_FAILURE_STAGES = {
    ("not_run", None): {"not_run"},
    ("passed", None): {"completed"},
    ("compile_failure", "compile"): {"compilation"},
    ("runtime_failure", "runtime"): {"simulation"},
    ("runtime_failure", "timeout"): {"simulation"},
    ("behavior_failure", "functional"): {"functional_check", "behavior_check"},
    ("behavior_failure", "mutation_survival"): {"mutation_check"},
    ("behavior_failure", "property"): {"property_check"},
    ("behavior_failure", "behavior_unspecified"): {"behavior_check"},
    ("infrastructure_failure", "infrastructure"): {"infrastructure"},
}
REPLAY_FAILURE_RESPONSIBILITIES = {
    "not_run": {"none"},
    "passed": {"none"},
    "compile_failure": {"candidate"},
    "runtime_failure": {"candidate"},
    "behavior_failure": {"candidate"},
    "infrastructure_failure": {"system", "undetermined"},
}
REPLAY_STATUSES = {
    "passed",
    "compile_failure",
    "runtime_failure",
    "behavior_failure",
    "infrastructure_failure",
}


def validate_adapter_failure_taxonomy(status: str, value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("failure_taxonomy must be an object")
    unknown = set(value) - FAILURE_TAXONOMY_FIELDS
    if unknown:
        raise ValueError(f"unknown failure_taxonomy fields: {sorted(unknown)}")
    schema_version = value.get("schema_version")
    if schema_version not in {None, FAILURE_TAXONOMY_SCHEMA_VERSION}:
        raise ValueError("unsupported failure_taxonomy schema_version")
    primary_class = value.get("primary_class")
    if primary_class not in REPLAY_FAILURE_CLASSES[status]:
        raise ValueError("failure class is incompatible with replay status")
    stage = value.get("stage")
    if stage is not None and stage not in FAILURE_STAGES:
        raise ValueError("unknown failure stage")
    if (
        stage is not None
        and stage not in REPLAY_FAILURE_STAGES[(status, primary_class)]
    ):
        raise ValueError("failure stage is incompatible with replay status")
    responsibility = value.get("responsibility")
    if responsibility is not None and responsibility not in FAILURE_RESPONSIBILITIES:
        raise ValueError("unknown failure responsibility")
    if (
        responsibility is not None
        and responsibility not in REPLAY_FAILURE_RESPONSIBILITIES[status]
    ):
        raise ValueError("failure responsibility is incompatible with replay status")
    if "retryable" in value and not isinstance(value["retryable"], bool):
        raise ValueError("retryable must be boolean")
    if status != "infrastructure_failure" and value.get("retryable") is True:
        raise ValueError("candidate and completed outcomes cannot be retryable")
    for field in (
        "secondary_classes",
        "case_ids",
        "property_ids",
        "mutation_ids",
    ):
        items = value.get(field, [])
        if not isinstance(items, list) or not all(
            isinstance(item, str) and item for item in items
        ):
            raise ValueError(f"{field} must contain non-empty strings")
        if len(items) != len(set(items)):
            raise ValueError(f"{field} must not contain duplicates")
    secondary = value.get("secondary_classes", [])
    if any(item not in FAILURE_CLASSES for item in secondary):
        raise ValueError("unknown secondary failure class")
    if primary_class in secondary:
        raise ValueError("primary failure class cannot also be secondary")


def normalize_failure_taxonomy(
    value: dict[str, Any],
    *,
    primary_class: str | None,
    stage: str,
    responsibility: str,
    retryable: bool,
) -> dict[str, Any]:
    return {
        "schema_version": FAILURE_TAXONOMY_SCHEMA_VERSION,
        "primary_class": value.get("primary_class", primary_class),
        "secondary_classes": list(value.get("secondary_classes") or []),
        "stage": value.get("stage", stage),
        "responsibility": value.get("responsibility", responsibility),
        "retryable": bool(value.get("retryable", retryable)),
        "case_ids": list(value.get("case_ids") or []),
        "property_ids": list(value.get("property_ids") or []),
        "mutation_ids": list(value.get("mutation_ids") or []),
    }


def replay_failure_taxonomy(
    status: str,
    command: dict[str, Any] | None,
    adapter_result: dict[str, Any] | None,
) -> dict[str, Any]:
    defaults: dict[str, tuple[str | None, str, str, bool]] = {
        "not_run": (None, "not_run", "none", False),
        "passed": (None, "completed", "none", False),
        "compile_failure": ("compile", "compilation", "candidate", False),
        "runtime_failure": ("runtime", "simulation", "candidate", False),
        "behavior_failure": (
            "behavior_unspecified",
            "behavior_check",
            "candidate",
            False,
        ),
        "infrastructure_failure": (
            "infrastructure",
            "infrastructure",
            "system",
            True,
        ),
    }
    primary_class, stage, responsibility, retryable = defaults[status]
    if command and command.get("execution_status") == "timeout":
        primary_class = "timeout"
        stage = "simulation"
    raw = dict((adapter_result or {}).get("failure_taxonomy") or {})
    return normalize_failure_taxonomy(
        raw,
        primary_class=primary_class,
        stage=stage,
        responsibility=responsibility,
        retryable=retryable,
    )


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def raw_model_final_output(messages: list[dict[str, Any]]) -> dict[str, Any]:
    message = next(
        (item for item in reversed(messages) if item.get("role") == "assistant"),
        None,
    )
    if message is None:
        return {"available": False, "sha256": None, "message": None}
    preserved = dict(message)
    return {
        "available": True,
        "sha256": canonical_sha256(preserved),
        "message": preserved,
    }


def snapshot_submission(runtime: Path, artifact_gate: dict[str, Any]) -> dict[str, Any]:
    expected = list(artifact_gate.get("expected_artifacts") or [])
    if not artifact_gate.get("passed"):
        return {
            "status": "no_submission",
            "artifacts": [],
            "tree_sha256": None,
            "diagnostics": list(artifact_gate.get("diagnostics") or []),
        }

    source_root = runtime / "public" / "submission"
    snapshot_root = runtime / "evidence" / "final_submission"
    artifacts: list[dict[str, Any]] = []
    # Canonicalize artifact order so an unchanged multi-file submission is
    # idempotent even when the score policy lists targets non-lexicographically.
    for relative in sorted(expected):
        source = source_root / relative
        data = source.read_bytes()
        artifacts.append({
            "path": relative,
            "snapshot_path": f"evidence/final_submission/{relative}",
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    frozen = {
        "status": "available",
        "artifacts": artifacts,
        "tree_sha256": canonical_sha256(
            [{"path": row["path"], "sha256": row["sha256"]} for row in artifacts]
        ),
        "diagnostics": [],
        "immutable": True,
    }
    if snapshot_root.exists():
        observed_files = sorted(
            path.relative_to(snapshot_root).as_posix()
            for path in snapshot_root.rglob("*")
            if path.is_file() and not path.is_symlink()
        )
        observed = []
        for relative in observed_files:
            data = (snapshot_root / relative).read_bytes()
            observed.append(
                {
                    "path": relative,
                    "snapshot_path": f"evidence/final_submission/{relative}",
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
        if observed != artifacts:
            raise ValueError(
                "frozen submission does not match the current gated submission"
            )
        return frozen

    evidence_root = snapshot_root.parent
    evidence_root.mkdir(parents=True, exist_ok=True)
    staging_root = Path(
        tempfile.mkdtemp(prefix=".final_submission-", dir=evidence_root)
    )
    try:
        for row in artifacts:
            source = source_root / row["path"]
            target = staging_root / row["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
            target.chmod(0o444)
        staging_root.rename(snapshot_root)
        for directory in sorted(
            (path for path in snapshot_root.rglob("*") if path.is_dir()),
            reverse=True,
        ):
            directory.chmod(0o555)
        snapshot_root.chmod(0o555)
    except Exception:
        shutil.rmtree(staging_root, ignore_errors=True)
        raise
    return frozen


def hash_test_tree(evaluator_dir: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    if evaluator_dir.is_dir():
        for path in sorted(evaluator_dir.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(evaluator_dir).as_posix()
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            data = path.read_bytes()
            files.append({
                "path": relative,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            })
    return {
        "file_count": len(files),
        "tree_sha256": canonical_sha256(
            [{"path": row["path"], "sha256": row["sha256"]} for row in files]
        ),
        "files": files,
    }


def evas_identity(command: list[str], timeout_s: int = 10) -> dict[str, Any]:
    resolved = shutil.which(command[0]) if command else None
    executable_sha256 = None
    if resolved:
        try:
            executable_sha256 = hashlib.sha256(Path(resolved).read_bytes()).hexdigest()
        except OSError:
            executable_sha256 = None
    try:
        completed = subprocess.run(
            [*command, "--version"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "available": False,
            "command": command,
            "resolved_executable": resolved,
            "executable_sha256": executable_sha256,
            "version_output": None,
            "sha256": None,
            "error_type": type(exc).__name__,
            "error": str(exc)[:1000],
        }
    version_output = (completed.stdout or completed.stderr).strip()
    available = completed.returncode == 0 and bool(version_output)
    return {
        "available": available,
        "command": command,
        "resolved_executable": resolved,
        "executable_sha256": executable_sha256,
        "returncode": completed.returncode,
        "version_output": version_output or None,
        "sha256": (
            hashlib.sha256(version_output.encode("utf-8")).hexdigest()
            if version_output else None
        ),
    }


def trusted_replay(
    command: dict[str, Any] | None,
    adapter_result: dict[str, Any] | None,
    test_manifest: dict[str, Any],
    identity: dict[str, Any],
    submission_tree_sha256: str | None = None,
) -> dict[str, Any]:
    taxonomy_adapter_result: dict[str, Any] | None = None
    if command is None:
        status = "not_run"
        diagnostics: list[str] = []
    elif command.get("execution_status") == "timeout":
        status = "runtime_failure"
        diagnostics = ["trusted_replay_timeout"]
    elif command.get("execution_status") != "completed":
        status = "infrastructure_failure"
        diagnostics = ["trusted_replay_did_not_execute"]
    elif adapter_result is not None:
        status = str(adapter_result.get("status") or "")
        if status not in REPLAY_STATUSES:
            status = "infrastructure_failure"
            diagnostics = ["invalid_trusted_replay_status"]
        else:
            diagnostics = list(adapter_result.get("diagnostics") or [])
            if "failure_taxonomy" in adapter_result:
                try:
                    validate_adapter_failure_taxonomy(
                        status, adapter_result["failure_taxonomy"]
                    )
                except ValueError:
                    status = "infrastructure_failure"
                    diagnostics.append("invalid_failure_taxonomy")
                else:
                    taxonomy_adapter_result = adapter_result
            else:
                taxonomy_adapter_result = adapter_result
    else:
        status = "infrastructure_failure"
        diagnostics = ["missing_structured_trusted_replay_result"]
    return {
        "status": status,
        "executed": command is not None,
        "test_manifest": test_manifest,
        "submission_tree_sha256": submission_tree_sha256,
        "evas_identity": identity,
        "command": command,
        "adapter_result": adapter_result,
        "diagnostics": diagnostics,
        "failure_taxonomy": replay_failure_taxonomy(
            status, command, taxonomy_adapter_result
        ),
    }


def normalize_trusted_replay_watchdog(replay: dict[str, Any]) -> None:
    """The outer judge watchdog is infrastructure, not candidate runtime."""
    command = replay.get("command")
    if not isinstance(command, dict) or command.get("execution_status") != "timeout":
        return
    replay["status"] = "infrastructure_failure"
    replay["diagnostics"] = ["trusted_replay_watchdog_timeout"]
    replay["failure_taxonomy"] = {
        "schema_version": "vabench-failure-taxonomy-v1",
        "primary_class": "infrastructure",
        "secondary_classes": ["timeout"],
        "stage": "infrastructure",
        "responsibility": "system",
        "retryable": True,
        "case_ids": [], "property_ids": [], "mutation_ids": [],
    }


def terminal_outcome(
    model_status: str,
    submission: dict[str, Any],
    replay: dict[str, Any],
) -> str:
    if model_status == "agent_resource_exhausted":
        return "agent_resource_exhausted"
    if model_status in {"provider_failure", "runner_failure"}:
        return "infrastructure_failure"
    if model_status == "agent_timeout" and submission.get("status") != "available":
        return "agent_timeout"
    if submission.get("status") != "available":
        return "no_submission"
    replay_status = str(replay.get("status") or "not_run")
    if replay_status in REPLAY_STATUSES:
        return replay_status
    return "not_scored"


def terminal_failure_taxonomy(
    model_status: str,
    submission: dict[str, Any],
    replay: dict[str, Any],
) -> dict[str, Any]:
    if model_status == "agent_resource_exhausted":
        return normalize_failure_taxonomy(
            {},
            primary_class="resource_exhaustion",
            stage="model_execution",
            responsibility="model",
            retryable=False,
        )
    if model_status in {"provider_failure", "runner_failure"}:
        return normalize_failure_taxonomy(
            {},
            primary_class="infrastructure",
            stage="model_execution",
            responsibility="system",
            retryable=True,
        )
    if model_status == "agent_timeout" and submission.get("status") != "available":
        return normalize_failure_taxonomy(
            {},
            primary_class="timeout",
            stage="model_execution",
            responsibility="model",
            retryable=False,
        )
    if submission.get("status") != "available":
        return normalize_failure_taxonomy(
            {},
            primary_class="invalid",
            stage="artifact_gate",
            responsibility="candidate",
            retryable=False,
        )
    replay_status = str(replay.get("status") or "not_run")
    existing = replay.get("failure_taxonomy")
    if isinstance(existing, dict):
        return dict(existing)
    if replay_status in REPLAY_STATUSES or replay_status == "not_run":
        return replay_failure_taxonomy(replay_status, replay.get("command"), None)
    return normalize_failure_taxonomy(
        {},
        primary_class=None,
        stage="not_scored",
        responsibility="none",
        retryable=False,
    )


def build_experiment_result(
    *,
    cell: dict[str, Any],
    model_status: str,
    messages: list[dict[str, Any]],
    artifact_gate: dict[str, Any],
    runtime: Path,
    replay: dict[str, Any],
    final_submission: dict[str, Any] | None = None,
) -> dict[str, Any]:
    submission = final_submission or snapshot_submission(runtime, artifact_gate)
    outcome = terminal_outcome(model_status, submission, replay)
    failure_taxonomy = terminal_failure_taxonomy(model_status, submission, replay)
    scored = outcome in {
        "passed",
        "compile_failure",
        "runtime_failure",
        "behavior_failure",
    }
    score = 1.0 if outcome == "passed" else 0.0 if scored else None
    return {
        "schema_version": SCHEMA_VERSION,
        "recorded_at": now(),
        "cell_id": str(cell.get("cell_id") or ""),
        "task_id": str(cell.get("task_id") or ""),
        "mode": str(cell.get("mode") or ""),
        "model_execution": {
            "status": model_status,
            "raw_final_output": raw_model_final_output(messages),
        },
        "final_submission": submission,
        "final_trusted_replay": replay,
        "outcome": outcome,
        "failure_taxonomy": failure_taxonomy,
        "score_eligible": scored,
        "score": score,
    }
