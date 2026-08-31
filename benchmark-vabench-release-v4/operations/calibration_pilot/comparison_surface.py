"""Sanitized surface observations for legacy/native workflow comparison.

This module is deliberately read-only. It records model-visible runtime bytes,
provider request fingerprints, and selected container isolation facts without
printing prompts, messages, environment variables, credentials, or hidden judge
content.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
from typing import Any, Mapping


DOCKER_INSPECT_FORMAT = (
    "{{json .Mounts}}\n"
    "{{json .HostConfig.NetworkMode}}\n"
    "{{json .HostConfig.ReadonlyRootfs}}\n"
    "{{json .HostConfig.CapDrop}}\n"
    "{{json .Image}}"
)

_MODEL_VISIBLE_ROOT_FILES = {
    "agent_prompt.txt",
    "direct_prompt.txt",
    "MODEL_ACCESS_POLICY.json",
    "RUNTIME_MANIFEST.json",
}
_FORBIDDEN_COMPONENTS = {
    "evaluator",
    "hidden",
    "private",
    ".private",
    "__private__",
    "solution",
    "trusted_replay_fixtures",
}
_FORBIDDEN_FILENAMES = {
    "score_tb.scs",
    "mutation_catalog.json",
    "certified_faults.json",
    "faults.json",
    "gold.json",
    "checker_private.json",
}


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_public_runtime(runtime: Path) -> dict[str, Any]:
    """Fingerprint the exported model-visible runtime without reading private trees."""
    public_link = runtime / "public"
    if public_link.is_symlink():
        raise ValueError("public/ must not be a symlink")
    root = runtime.resolve()
    if not root.is_dir():
        raise ValueError("public runtime is missing")
    public = _require_child(root, public_link)
    if not public.is_dir():
        raise ValueError("public runtime is missing public/")

    files: dict[str, dict[str, Any]] = {}
    aliases: dict[str, str] = {}
    for item in _iter_model_visible_entries(root, public):
        relative = item.relative_to(root).as_posix()
        _reject_private_looking(relative)
        if item.is_symlink():
            if relative != "public/public":
                raise ValueError(f"model-visible symlink is not allowed: {relative}")
            target = os.readlink(item)
            if target != ".":
                raise ValueError("public/public alias must point to .")
            resolved = item.resolve(strict=True)
            if resolved != public.resolve(strict=True):
                raise ValueError("public/public alias escapes public runtime")
            aliases[relative] = target
            continue
        if item.is_dir():
            continue
        if not item.is_file():
            raise ValueError(f"model-visible entry is not a regular file: {relative}")
        files[relative] = {"bytes": item.stat().st_size, "sha256": file_sha256(item)}

    task_files = _strip_prefix(files, "public/task/")
    submission_files = _strip_prefix(files, "public/submission/")
    tree_payload = {"files": files, "symlinks": aliases}
    public_task_tree = canonical_sha256(task_files) if task_files else None
    initial_submission_tree = (canonical_sha256(submission_files)
                               if (public / "submission").is_dir() else None)
    return {
        "schema_version": "vaevas-comparison-public-runtime-v1",
        "model_visible_files": files,
        "public_task_files": task_files,
        "initial_submission_files": submission_files,
        "public_aliases": aliases,
        "public_task_tree_sha256": public_task_tree,
        "initial_submission_tree_sha256": initial_submission_tree,
        "counts": {
            "model_visible_files": len(files),
            "public_task_files": len(task_files),
            "initial_submission_files": len(submission_files),
            "public_aliases": len(aliases),
        },
        "tree_sha256": canonical_sha256(tree_payload),
    }


def snapshot_request(payload: Mapping[str, Any], *, timeout_s: float) -> dict[str, Any]:
    """Return a request fingerprint with content hashes instead of raw payload text."""
    if not _positive_finite_number(timeout_s):
        raise ValueError("timeout_s must be positive")
    configured_watchdog = payload.get("configured_watchdog_s", payload.get("timeout_s"))
    if configured_watchdog is not None and not _positive_finite_number(configured_watchdog):
        raise ValueError("configured_watchdog_s must be positive")
    max_tokens = payload.get("max_tokens")
    if not _positive_finite_number(max_tokens):
        raise ValueError("max_tokens must be positive")
    messages = [
        {
            "index": index,
            "role": str(message.get("role")),
            "content_sha256": canonical_sha256(message.get("content")),
            "tool_calls_sha256": canonical_sha256(message.get("tool_calls", [])),
            "tool_call_ids": _tool_call_ids(message.get("tool_calls", [])),
        }
        for index, message in enumerate(_list(payload.get("messages"), "messages"))
        if isinstance(message, Mapping)
    ]
    if len(messages) != len(_list(payload.get("messages"), "messages")):
        raise ValueError("messages must be objects")
    tools = [_tool_fingerprint(tool) for tool in _list(payload.get("tools", []), "tools")]
    decoding = {
        key: payload[key]
        for key in ("temperature", "top_p", "presence_penalty", "frequency_penalty", "seed")
        if key in payload
    }
    result: dict[str, Any] = {
        "schema_version": "vaevas-comparison-request-v1",
        "model": payload.get("model"),
        "timeout_s": timeout_s,
        "effective_timeout_s": timeout_s,
        "configured_watchdog_s": configured_watchdog,
        "max_tokens": max_tokens,
        "provider_options": {
            "stream": payload.get("stream"),
            "stream_options_sha256": canonical_sha256(payload.get("stream_options")),
            "thinking_sha256": canonical_sha256(payload.get("thinking")),
            "tool_choice_sha256": canonical_sha256(payload.get("tool_choice")),
        },
        "decoding": decoding,
        "messages": messages,
        "system_messages_sha256": canonical_sha256(
            [row["content_sha256"] for row in messages if row["role"] == "system"]
        ),
        "tools": tools,
        "tools_sha256": canonical_sha256(tools),
        "full_payload_sha256": canonical_sha256(_sanitize_request_payload(payload)),
    }
    result["request_sha256"] = canonical_sha256(result)
    return result


def observe_environment(env: Any) -> dict[str, Any]:
    """Inspect selected Docker isolation fields for a live VaBench environment."""
    if getattr(getattr(env, "config", None), "sandbox_backend", None) != "docker":
        raise ValueError("environment observation requires Docker backend")
    container = getattr(env, "_docker_container", None)
    if not container:
        raise ValueError("Docker environment has not been preflighted")
    docker_command = shlex.split(str(getattr(env, "docker_command", "docker")))
    if not docker_command:
        raise ValueError("docker_command must not be empty")
    inspected = subprocess.check_output(
        [*docker_command, "inspect", "--format", DOCKER_INSPECT_FORMAT, container],
        text=True,
        timeout=30,
    ).splitlines()
    if len(inspected) != 5:
        raise ValueError("Docker inspect returned an unexpected shape")
    mounts, network, read_only, capabilities, image_id = map(json.loads, inspected)
    if not isinstance(mounts, list):
        raise ValueError("Docker inspect mounts must be a list")
    destinations = [
        row.get("Destination")
        for row in mounts
        if isinstance(row, Mapping) and isinstance(row.get("Destination"), str)
    ]
    duplicate_destinations = sorted(
        destination for destination in set(destinations) if destinations.count(destination) > 1
    )
    bindings: dict[str, Mapping[str, Any]] = {}
    for row in mounts:
        if isinstance(row, Mapping) and row.get("Type") == "bind" and row.get("Destination") not in bindings:
            bindings[str(row["Destination"])] = row
    expected = {
        "/workspace/public/task": (_require_child(Path(env.runtime).resolve(), Path(env.runtime) / "public/task"), False),
        "/workspace/public/submission": (
            _require_child(Path(env.runtime).resolve(), Path(env.runtime) / "public/submission"),
            True,
        ),
        "/workspace/work": (_require_child(Path(env.workspace).resolve(), Path(env.work_dir)), True),
    }
    observed_mounts = {
        destination: {
            "source": str(Path(row.get("Source", "")).resolve()),
            "rw": bool(row.get("RW")),
        }
        for destination, row in sorted(bindings.items())
        if destination in expected
    }
    checks = {
        "no_duplicate_mount_destinations": not duplicate_destinations,
        "no_unexpected_mounts": not _unexpected_mounts(mounts, set(expected)),
        "expected_binds": set(bindings) == set(expected)
        and all(
            Path(bindings[destination].get("Source", "")).resolve() == source.resolve()
            and bool(bindings[destination].get("RW")) is writable
            for destination, (source, writable) in expected.items()
        ),
        "network_none": network == "none",
        "read_only_rootfs": read_only is True,
        "capdrop_all": isinstance(capabilities, list) and "ALL" in capabilities,
        "image_id_matches_environment": image_id == getattr(env, "docker_image_id", None),
    }
    trusted = all(checks.values())
    return {
        "schema_version": "vaevas-comparison-environment-v1",
        "sandbox_backend": "docker",
        "container_observed": True,
        "mounts": observed_mounts,
        "network_mode": network,
        "read_only_rootfs": read_only,
        "cap_drop": capabilities,
        "image_id": image_id,
        "declared_image_id": getattr(env, "docker_image_id", None),
        "duplicate_mount_destinations": duplicate_destinations,
        "unexpected_mounts": _unexpected_mounts(mounts, set(expected)),
        "checks": checks,
        "trusted_common_checks": trusted,
    }


def compare_surfaces(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    """Compare common evidence while naming intentionally different prompt/tool surfaces."""
    left_request = _mapping(left.get("request"), "left.request")
    right_request = _mapping(right.get("request"), "right.request")
    configured_watchdog_match = _same_positive(
        left_request.get("configured_watchdog_s"), right_request.get("configured_watchdog_s")
    )
    effective_timeout_within_watchdog = (
        configured_watchdog_match
        and _positive_within(left_request.get("effective_timeout_s"), left_request.get("configured_watchdog_s"))
        and _positive_within(right_request.get("effective_timeout_s"), right_request.get("configured_watchdog_s"))
    )
    matches = {
        "public_snapshot_self_consistent": _public_snapshot_consistent(_mapping(
            left.get("public_runtime"), "left.public_runtime",
        )) and _public_snapshot_consistent(_mapping(right.get("public_runtime"), "right.public_runtime")),
        "request_snapshot_self_consistent": _request_snapshot_consistent(left_request)
        and _request_snapshot_consistent(right_request),
        "public_runtime_tree": _public_snapshot_consistent(_mapping(left.get("public_runtime"), "left.public_runtime"))
        and _public_snapshot_consistent(_mapping(right.get("public_runtime"), "right.public_runtime"))
        and _same_sha(_get(left, "public_runtime", "tree_sha256"), _get(right, "public_runtime", "tree_sha256")),
        "public_task_tree": _public_snapshot_consistent(_mapping(left.get("public_runtime"), "left.public_runtime"))
        and _public_snapshot_consistent(_mapping(right.get("public_runtime"), "right.public_runtime"))
        and _same_sha(_get(left, "public_runtime", "public_task_tree_sha256"),
                      _get(right, "public_runtime", "public_task_tree_sha256")),
        "initial_submission_tree": _public_snapshot_consistent(_mapping(left.get("public_runtime"), "left.public_runtime"))
        and _public_snapshot_consistent(_mapping(right.get("public_runtime"), "right.public_runtime"))
        and _same_sha(_get(left, "public_runtime", "initial_submission_tree_sha256"),
                      _get(right, "public_runtime", "initial_submission_tree_sha256")),
        "trusted_environment": _trusted_environment(_mapping(left.get("environment"), "left.environment"))
        and _trusted_environment(_mapping(right.get("environment"), "right.environment")),
        "image_id": _same_image_id(_get(left, "environment", "image_id"), _get(right, "environment", "image_id")),
        "model": _same_non_empty(left_request.get("model"), right_request.get("model")),
        "decoding": isinstance(left_request.get("decoding"), Mapping)
        and left_request.get("decoding") == right_request.get("decoding"),
        "provider_options": isinstance(left_request.get("provider_options"), Mapping)
        and left_request.get("provider_options") == right_request.get("provider_options"),
        "configured_watchdog_s": configured_watchdog_match,
        "effective_timeout_within_watchdog": effective_timeout_within_watchdog,
        "max_tokens": _same_positive(left_request.get("max_tokens"), right_request.get("max_tokens")),
    }
    permitted: list[str] = []
    if left_request.get("request_sha256") != right_request.get("request_sha256"):
        permitted.append("request")
    if left_request.get("system_messages_sha256") != right_request.get("system_messages_sha256"):
        permitted.append("system_messages")
    if left_request.get("tools_sha256") != right_request.get("tools_sha256"):
        permitted.append("tools")
    return {
        "schema_version": "vaevas-comparison-surface-pair-v1",
        "claim": "surface_comparison_not_pure_parity",
        "matches": matches,
        "permitted_differences": permitted,
        "all_common_checks_match": all(matches.values()),
        "comparison_sha256": canonical_sha256({"matches": matches, "permitted_differences": permitted}),
    }


def _iter_model_visible_entries(root: Path, public: Path) -> list[Path]:
    entries = [root / name for name in sorted(_MODEL_VISIBLE_ROOT_FILES) if (root / name).exists()]
    entries.extend(sorted(public.rglob("*")))
    return entries


def _reject_private_looking(relative: str) -> None:
    path = Path(relative)
    components = {part.lower() for part in path.parts}
    if components & _FORBIDDEN_COMPONENTS or path.name.lower() in _FORBIDDEN_FILENAMES:
        raise ValueError(f"model-visible private-looking entry is not allowed: {relative}")


def _sanitize_request_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in payload.items():
        lower = key.lower()
        if key != "max_tokens" and any(secret in lower for secret in ("api_key", "authorization", "token", "secret", "password")):
            sanitized[key] = {"redacted": True}
        elif key == "messages":
            sanitized[key] = [
                {
                    "message_sha256": canonical_sha256(message),
                    "role": message.get("role"),
                    "content_sha256": canonical_sha256(message.get("content")),
                    "tool_calls_sha256": canonical_sha256(message.get("tool_calls", [])),
                    "tool_call_ids": _tool_call_ids(message.get("tool_calls", [])),
                }
                if isinstance(message, Mapping)
                else {"invalid_message_sha256": canonical_sha256(message)}
                for message in _list(value, "messages")
            ]
        elif key == "tools":
            sanitized[key] = [_tool_fingerprint(tool) for tool in _list(value, "tools")]
        elif key in {"stream_options", "thinking", "tool_choice", "response_format"}:
            sanitized[f"{key}_sha256"] = canonical_sha256(value)
        else:
            sanitized[key] = value
    return sanitized


def _strip_prefix(files: Mapping[str, Any], prefix: str) -> dict[str, Any]:
    return {
        path.removeprefix(prefix): value
        for path, value in files.items()
        if path.startswith(prefix)
    }


def _require_child(root: Path, child: Path) -> Path:
    resolved = child.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("path escapes expected runtime root") from exc
    return resolved


def _list(value: Any, name: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    return value


def _tool_fingerprint(tool: Any) -> dict[str, Any]:
    if not isinstance(tool, Mapping):
        raise ValueError("tools must be objects")
    function = tool.get("function") if isinstance(tool.get("function"), Mapping) else {}
    return {
        "type": tool.get("type"),
        "name": function.get("name"),
        "description_sha256": canonical_sha256(function.get("description")),
        "parameters_sha256": canonical_sha256(function.get("parameters")),
    }


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def _same_sha(left: Any, right: Any) -> bool:
    return isinstance(left, str) and re.fullmatch(r"[0-9a-f]{64}", left) is not None and left == right


def _same_image_id(left: Any, right: Any) -> bool:
    return isinstance(left, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", left) is not None and left == right


def _same_non_empty(left: Any, right: Any) -> bool:
    return isinstance(left, str) and bool(left) and left == right


def _same_positive(left: Any, right: Any) -> bool:
    return _positive_finite_number(left) and left == right


def _positive_within(value: Any, limit: Any) -> bool:
    return _positive_finite_number(value) and _positive_finite_number(limit) and value <= limit


def _unexpected_mounts(mounts: list[Any], expected_bind_destinations: set[str]) -> list[dict[str, Any]]:
    unexpected: list[dict[str, Any]] = []
    for row in mounts:
        if not isinstance(row, Mapping):
            unexpected.append({"type": "invalid", "destination": None})
            continue
        destination = row.get("Destination")
        mount_type = row.get("Type")
        if mount_type == "bind" and destination in expected_bind_destinations:
            continue
        if mount_type == "tmpfs" and destination in {"/tmp"}:
            continue
        unexpected.append({"type": mount_type, "destination": destination})
    return unexpected


def _positive_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0 and value < float("inf")


def _tool_call_ids(tool_calls: Any) -> list[Any]:
    if tool_calls is None:
        return []
    if not isinstance(tool_calls, list):
        return []
    return [call.get("id") for call in tool_calls if isinstance(call, Mapping)]


def _public_snapshot_consistent(snapshot: Mapping[str, Any]) -> bool:
    files = snapshot.get("model_visible_files")
    aliases = snapshot.get("public_aliases")
    task_files = snapshot.get("public_task_files")
    submission_files = snapshot.get("initial_submission_files")
    if not all(isinstance(value, Mapping) for value in (files, aliases, task_files, submission_files)):
        return False
    return (
        snapshot.get("tree_sha256") == canonical_sha256({"files": files, "symlinks": aliases})
        and snapshot.get("public_task_tree_sha256") == canonical_sha256(task_files)
        and snapshot.get("initial_submission_tree_sha256") == canonical_sha256(submission_files)
    )


def _request_snapshot_consistent(snapshot: Mapping[str, Any]) -> bool:
    observed = snapshot.get("request_sha256")
    if not _same_sha(observed, observed):
        return False
    unsigned = dict(snapshot)
    unsigned.pop("request_sha256", None)
    return observed == canonical_sha256(unsigned)


def _trusted_environment(snapshot: Mapping[str, Any]) -> bool:
    required = {
        "no_duplicate_mount_destinations",
        "no_unexpected_mounts",
        "expected_binds",
        "network_none",
        "read_only_rootfs",
        "capdrop_all",
        "image_id_matches_environment",
    }
    checks = snapshot.get("checks")
    return (
        snapshot.get("trusted_common_checks") is True
        and isinstance(checks, Mapping)
        and set(checks) >= required
        and all(checks[key] is True for key in required)
    )


def _get(value: Mapping[str, Any], *path: str) -> Any:
    current: Any = value
    for part in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current
