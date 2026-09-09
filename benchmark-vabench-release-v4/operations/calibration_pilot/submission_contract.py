"""Declared candidate paths, output transport schema and pre-freeze checks.

Both generation and scoring consume this contract; it does not launch agents
or execute a judge. Existing run_campaign imports remain compatibility exports.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

PUBLIC_INCLUDE_RE = re.compile(
    r"\b(?:ahdl_include|include)\s+[\"']([^\"']+)[\"']", re.IGNORECASE
)


def safe_relative(raw: str) -> Path:
    path = Path(raw.replace("\\", "/"))
    if not path.parts or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe relative path: {raw!r}")
    return path


def expected_candidate_artifacts(runtime: Path) -> list[str]:
    policy_path = runtime / "evaluator" / "score_policy.json"
    if not policy_path.is_file():
        return []
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    return [safe_relative(str(item)).as_posix() for item in policy.get("candidate_artifacts") or []]


def submit_artifacts_tool_schema(runtime: Path) -> dict[str, Any]:
    expected = expected_candidate_artifacts(runtime)
    if not expected:
        raise ValueError("submit_artifacts requires declared candidate artifacts")
    return {
        "type": "function",
        "function": {
            "name": "submit_artifacts",
            "description": (
                "Submit the complete final candidate bundle. This output-only "
                "transport returns no execution or checker feedback."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "artifacts": {
                        "type": "object",
                        "properties": {
                            path: {"type": "string", "minLength": 1}
                            for path in expected
                        },
                        "required": expected,
                        "additionalProperties": False,
                    }
                },
                "required": ["artifacts"],
                "additionalProperties": False,
            },
        },
    }


def submission_source_diagnostics(runtime: Path) -> list[str]:
    """Reject candidate filesystem/include escapes before trusted execution."""
    submission = runtime / "public" / "submission"
    expected = set(expected_candidate_artifacts(runtime))
    diagnostics: list[str] = []
    if not submission.is_dir():
        return diagnostics
    for path in sorted(submission.rglob("*")):
        relative = path.relative_to(submission).as_posix()
        if path.is_symlink():
            diagnostics.append(f"symlink_not_allowed:{relative}")
            continue
        if not path.is_file() or path.suffix.lower() not in {".va", ".scs"}:
            continue
        if path.stat().st_size > 1_000_000:
            diagnostics.append(f"source_too_large:{relative}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            diagnostics.append(f"source_not_utf8:{relative}")
            continue
        uncommented = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        uncommented = "\n".join(
            line.split("//", 1)[0] for line in uncommented.splitlines()
        )
        for raw in PUBLIC_INCLUDE_RE.findall(uncommented):
            normalized = raw.replace("\\", "/")
            include = Path(normalized)
            if normalized in {"constants.vams", "disciplines.vams"}:
                continue
            if (
                path.name == "testbench.scs"
                and not include.is_absolute()
                and ".." not in include.parts
                and include.parts
                and include.parts[0] == "dut"
            ):
                continue
            if include.is_absolute() or ".." in include.parts:
                diagnostics.append(f"unsafe_source_include:{relative}:{raw}")
                continue
            try:
                target = safe_relative((Path(relative).parent / include).as_posix()).as_posix()
            except ValueError:
                diagnostics.append(f"unsafe_source_include:{relative}:{raw}")
                continue
            if target not in expected:
                diagnostics.append(f"undeclared_source_include:{relative}:{raw}")
    return diagnostics


def submission_artifact_gate(runtime: Path) -> dict[str, Any]:
    expected = expected_candidate_artifacts(runtime)
    expected_set = set(expected)
    submission = runtime / "public" / "submission"
    diagnostics: list[str] = []
    actual: set[str] = set()
    allowed_directories: set[str] = set()
    for raw in expected:
        parent = Path(raw).parent
        while parent != Path("."):
            allowed_directories.add(parent.as_posix())
            parent = parent.parent

    if not expected:
        diagnostics.append("missing_candidate_artifact_contract")
    if len(expected_set) != len(expected):
        diagnostics.append("duplicate_candidate_artifact_contract")
    if not submission.is_dir():
        diagnostics.append("missing_submission_directory")
    else:
        for path in sorted(submission.rglob("*")):
            relative = path.relative_to(submission).as_posix()
            if path.is_symlink():
                diagnostics.append(f"symlink_not_allowed:{relative}")
            elif path.is_file():
                actual.add(relative)
            elif path.is_dir():
                if relative not in allowed_directories:
                    diagnostics.append(f"undeclared_directory:{relative}")
            else:
                diagnostics.append(f"non_regular_artifact:{relative}")

    diagnostics.extend(
        f"missing_artifact_path:{relative}" for relative in sorted(expected_set - actual)
    )
    diagnostics.extend(
        f"undeclared_artifact_path:{relative}" for relative in sorted(actual - expected_set)
    )
    diagnostics.extend(
        diagnostic
        for diagnostic in submission_source_diagnostics(runtime)
        if diagnostic not in diagnostics
    )
    passed = not diagnostics
    artifacts = {
        relative: hashlib.sha256((submission / relative).read_bytes()).hexdigest()
        for relative in expected
        if passed
    }
    return {
        "schema_version": "v4-submission-artifact-gate-v1",
        "passed": passed,
        "expected_artifacts": expected,
        "observed_artifacts": sorted(actual),
        "artifact_sha256": artifacts,
        "diagnostics": diagnostics,
    }
