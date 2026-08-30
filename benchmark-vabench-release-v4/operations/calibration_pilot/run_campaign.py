#!/usr/bin/env python3
"""Run selected v4 calibration cells through an OpenAI-compatible endpoint."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from typing import Any


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[1]
REPO = PACKAGE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import result_protocol as RESULT_PROTOCOL  # noqa: E402
from experiment_policy import (  # noqa: E402
    experiment_policy_sha256,
    load_experiment_policy,
)
from mini_swe_vabench import (  # noqa: E402
    CANDIDATE_TREE_SCHEMA_VERSION,
    DEFAULT_DOCKER_IMAGE,
    DEFAULT_NO_EVAS_DOCKER_IMAGE,
    MINI_SWE_SCAFFOLD_ID,
    default_sandbox_backend,
    run_mini_swe_episode,
)

EXPORTER = PACKAGE / "operations" / "tri_form_derivation_prep" / "export_tri_form_runtime.py"
DEFAULT_RELEASE = PACKAGE / "release" / "benchmarkv4-r53"
DEFAULT_BASE_URL = "https://www.cun.ai/v1"
DEFAULT_API_KEY_ENV = "VAEVAS_API_KEY"
DEFAULT_SETUP_TIMEOUT_S = 1800
DEFAULT_REQUEST_TIMEOUT_S = 1800
DEFAULT_TOOL_TIMEOUT_S = 1800
DEFAULT_JUDGE_TIMEOUT_S = 1800
DEFAULT_MINI_SWE_PREFLIGHT_TIMEOUT_S = 60
DEFAULT_MINI_SWE_PREFLIGHT_ATTEMPTS = 2
DEFAULT_MINI_SWE_STARTUP_WORKERS = 8
DIRECT_PARSER_VERSION = "v4-exact-artifact-envelope-parser-v1"
DIRECT_DUT_RUNTIME_SCHEMAS = {
    "r45-direct-evas-runtime-v1",
    "r45-direct-evas-runtime-v2",
    "r47-direct-evas-runtime-v2",
    "r48-direct-evas-runtime-v2",
    "r49-direct-evas-runtime-v2",
    "r50-direct-evas-runtime-v2",
    "r51-direct-evas-runtime-v2",
    "r51-direct-evas-runtime-v3",
    "r52-direct-evas-runtime-v2",
    "r52-direct-evas-runtime-v3",
}
DIRECT_TESTBENCH_RUNTIME_SCHEMAS = {
    "r45-direct-evas-testbench-suite-v1",
    "r45-direct-evas-testbench-suite-v2",
    "r47-direct-evas-testbench-suite-v2",
    "r48-direct-evas-testbench-suite-v2",
    "r49-direct-evas-testbench-suite-v2",
    "r50-direct-evas-testbench-suite-v2",
    "r51-direct-evas-testbench-suite-v2",
    "r51-direct-evas-testbench-suite-v3",
    "r52-direct-evas-testbench-reference-v1",
}
ARTIFACT_RE = re.compile(
    r'(?m)^<<<VABENCH_ARTIFACT path="([^"\r\n]+)">>>\r?\n'
    r'(.*?)'
    r'\r?\n<<<END_VABENCH_ARTIFACT>>>(?=\r?$)',
    re.DOTALL,
)
RELAXED_ARTIFACT_RE = re.compile(
    r'<<<VABENCH_ARTIFACT\s+path="([^"]+)">{2,3}\s*(.*?)\s*<<<END_VABENCH_ARTIFACT>{2,3}',
    re.DOTALL,
)
INPUT_ARTIFACT_RE = re.compile(
    r'<<<VABENCH_INPUT_ARTIFACT\s+path="([^"]+)">{2,3}\s*(.*?)\s*<<<END_VABENCH_ARTIFACT>{2,3}',
    re.DOTALL,
)
FILENAME_ARTIFACT_RE = re.compile(
    r"<<<\s*([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.(?:va|scs))\s*>>>\s*(.*?)\s*<<<END_VABENCH_ARTIFACT>{2,3}",
    re.DOTALL | re.IGNORECASE,
)
FENCED_BLOCK_RE = re.compile(
    r"```(?:verilog-a|veriloga|verilog|spectre|scs)?\s*(.*?)```",
    re.DOTALL | re.IGNORECASE,
)
FILENAME_TOKEN_RE = re.compile(
    r"(?<![\w./-])([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.(?:va|scs))(?![\w./-])",
    re.IGNORECASE,
)
AGENTIC = {"G2", "G3", "G4", "G5"}
NATIVE_MINI_SWE_ARM_CONTRACT = {
    "OneShot": ("G0", False),
    "Agent-No-EVAS": ("G2", False),
    "Agentic": ("G2", True),
}
MAX_ONESHOT_TRANSPORT_FAILURES = 2
RESUMABLE_TERMINAL_STATUSES = {
    "submitted",
    "submitted_at_budget",
    "workspace_ready",
    "invalid_submission",
    "budget_exhausted",
    "agent_timeout",
    "agent_resource_exhausted",
    "context_window_exceeded",
}
ARTIFACT_READY_STATUSES = {"submitted", "submitted_at_budget", "workspace_ready"}
FEEDBACK_SIGNAL_PREFIXES = (
    "FEEDBACK_",
    "reference:",
    "negative_",
    "security:",
    "ERROR:",
    "WARNING:",
    "Traceback",
)
PROMPT_EMBEDDED_TASK_FILES = {
    "task/instruction.md",
    "task/solver_contract.json",
    "task/public_contract.json",
}
PUBLIC_INCLUDE_RE = re.compile(
    r"\b(?:ahdl_include|include)\s+[\"']([^\"']+)[\"']", re.IGNORECASE
)
PUBLIC_ESCAPE_RE = re.compile(
    r"\b(?:shell|system|exec|spawn|unix|socket|tcp|udp|https?|ftp|curl|wget|ocean|skill|ipcBeginProcess)\b",
    re.IGNORECASE,
)
AGENTIC_COMPONENT_START = '<<<VABENCH_COMPONENT id="agentic_wrapper.md">>>'
AGENTIC_COMPONENT_END = "<<<END_VABENCH_COMPONENT>>>"
NO_EVAS_AGENTIC_WRAPPER = """\
# vaBench Agent-No-EVAS Submission Contract

Inspect the mounted public task inputs and write only the final candidate
artifacts under `public/submission/`. Preserve exact file names, module names,
ports, parameters, and required artifact paths.

EVAS execution is not available in this experimental arm. No public simulator
diagnostics or waveforms are provided. Reason from the public specification and
task files, then run `vabench-submit` after the declared artifacts are complete.
The final private Spectre judge is outside the model-visible workspace.
"""
ONESHOT_TRANSPORT_INSTRUCTION = """\
Complete the task in the user message without changing its requested behavior.
For final delivery, call `submit_artifacts` exactly once with the complete text
of every artifact named by the function schema. Do not add undeclared paths.
This function is only an output transport: it does not execute the candidate,
reveal diagnostics, or provide checker feedback.
"""


class ProviderRequestTimeout(TimeoutError):
    """One provider request exhausted its infrastructure timeout."""


class ProviderContextWindowExceeded(RuntimeError):
    """Provider rejected the turn because the conversation exceeded context."""


class ProviderAPIError(RuntimeError):
    """Provider returned a structured API error that is not transport failure."""


class ProviderTransportError(RuntimeError):
    """Transport failed before a provider response could be decoded."""


class RuntimeExportError(RuntimeError):
    """The isolated public runtime could not be materialized for a cell."""


class SandboxStartupError(RuntimeError):
    """Typed transient preflight failure, before any model or final call."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_prepared_native_mini_swe(**kwargs: Any) -> Any:
    """Lazy native launcher import so legacy campaign startup stays unchanged."""
    from run_native_mini_swe import run_prepared_native_mini_swe as launch

    return launch(**kwargs)


def validate_native_mini_swe_cell(cell: dict[str, Any]) -> None:
    if cell.get("form") not in {"dut", "bugfix", "testbench"}:
        raise ValueError("native-mini-swe supports DUT/bugfix/Testbench cells only")
    arm = cell.get("experimental_arm")
    if arm not in NATIVE_MINI_SWE_ARM_CONTRACT:
        raise ValueError("native-mini-swe requires a supported experimental arm")
    expected_mode, expected_feedback = NATIVE_MINI_SWE_ARM_CONTRACT[arm]
    if (
        cell.get("mode") != expected_mode
        or cell.get("base_mode") != expected_mode
        or cell.get("executable_feedback") is not expected_feedback
    ):
        raise ValueError("native-mini-swe experimental arm contract mismatch")


def write_native_dispatch_result(
    runtime: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    path = runtime / "evidence/native-dispatch/result.json"
    if path.exists() or path.is_symlink() or path.parent.is_symlink():
        raise RuntimeError("native dispatch result already exists")
    document = {
        "schema_version": "v4-native-dispatch-result-v1",
        "backend": "native-mini-swe",
        **payload,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return document


def summarize_public_agent_images(results: list[dict[str, Any]]) -> dict[str, Any]:
    image_ids_by_arm: dict[str, set[str]] = {}
    for row in results:
        scaffold = row.get("agent_scaffold")
        if not isinstance(scaffold, dict):
            continue
        image_id = scaffold.get("docker_image_id")
        if not image_id:
            continue
        arm = str((row.get("cell") or {}).get("experimental_arm") or "standard")
        image_ids_by_arm.setdefault(arm, set()).add(str(image_id))
    serialized = {
        arm: sorted(image_ids)
        for arm, image_ids in sorted(image_ids_by_arm.items())
    }
    return {
        "observed_image_ids": sorted(
            {image_id for image_ids in serialized.values() for image_id in image_ids}
        ),
        "observed_image_ids_by_arm": serialized,
        "identity_consistent": all(
            len(image_ids) <= 1 for image_ids in serialized.values()
        ),
    }


def resolve_pinned_evas_identity(command: str) -> dict[str, Any]:
    argv = shlex.split(command)
    if not argv or not Path(argv[0]).is_absolute():
        raise SystemExit("--evas-command must start with an absolute executable path")
    identity = RESULT_PROTOCOL.evas_identity(argv)
    if not identity.get("available"):
        raise SystemExit(
            "configured EVAS is unavailable or has no version identity: "
            f"{identity.get('error') or identity.get('version_output') or command}"
        )
    return identity


def validate_pinned_evas_identity(
    command: str, expected: dict[str, Any] | None
) -> dict[str, Any]:
    if not isinstance(expected, dict) or not expected.get("available"):
        raise SystemExit("campaign is missing its pinned EVAS identity")
    observed = resolve_pinned_evas_identity(command)
    fields = (
        "command",
        "resolved_executable",
        "executable_sha256",
        "version_output",
        "sha256",
    )
    mismatches = [
        field for field in fields if observed.get(field) != expected.get(field)
    ]
    if mismatches:
        raise SystemExit("EVAS identity mismatch: " + ", ".join(mismatches))
    return observed


def file_digest_summary(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def read_tool_delivery_cache(runtime: Path) -> set[str]:
    path = runtime / "evidence" / "tool_delivery_cache.json"
    if not path.is_file():
        return set()
    try:
        payload = read_json(path)
    except (OSError, json.JSONDecodeError):
        return set()
    return {str(item) for item in payload.get("full_read_files") or []}


def write_tool_delivery_cache(runtime: Path, delivered: set[str]) -> None:
    write_json(runtime / "evidence" / "tool_delivery_cache.json", {
        "schema_version": "v4-tool-delivery-cache-v1",
        "full_read_files": sorted(delivered),
    })


def reference_tokens(text: str) -> int:
    return len(re.findall(r"[\w]+|[^\s\w]", text, flags=re.UNICODE))


def provider_output_usage(
    usage: dict[str, Any] | None,
    visible_text: str,
    *,
    reasoning_text: str = "",
    tool_text: str = "",
) -> dict[str, Any]:
    usage = usage or {}
    completion = usage.get("completion_tokens")
    details = usage.get("completion_tokens_details") or {}
    reasoning = details.get("reasoning_tokens", usage.get("reasoning_tokens", 0))
    if isinstance(completion, int) and completion >= 0:
        reasoning_tokens = int(reasoning) if isinstance(reasoning, int) else 0
        return {
            "output_tokens": completion,
            "reasoning_tokens": reasoning_tokens,
            "visible_tokens": max(0, completion - reasoning_tokens),
            "source": "provider_usage",
        }
    visible_estimate = reference_tokens(visible_text + tool_text)
    reasoning_estimate = reference_tokens(reasoning_text)
    return {
        "output_tokens": visible_estimate + reasoning_estimate,
        "reasoning_tokens": reasoning_estimate,
        "visible_tokens": visible_estimate,
        "source": "reference_estimate",
    }


def provider_response_metadata(response: dict[str, Any]) -> dict[str, Any]:
    """Keep stable audit fields without persisting the full provider response."""
    return {
        "response_id": response.get("id"),
        "model": response.get("model"),
        "created": response.get("created"),
        "system_fingerprint": response.get("system_fingerprint"),
    }


def model_event_hit_limit(event: dict[str, Any]) -> bool:
    if event.get("finish_reason") == "length":
        return True
    requested = event.get("requested_max_tokens")
    generated = event.get("provider_output_tokens")
    return (
        isinstance(requested, int)
        and requested > 0
        and isinstance(generated, int)
        and generated >= requested
    )


def summarize_evas_invocations(invocations: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = [str(row.get("status") or "unknown") for row in invocations]
    candidate_tree_hash_call_counts: dict[str, int] = {}
    modified_rerun_count = 0
    unchanged_repeat_count = 0
    previous_hash: str | None = None
    for row in invocations:
        raw_hash = row.get("candidate_tree_sha256")
        candidate_hash = raw_hash if isinstance(raw_hash, str) and raw_hash else None
        if candidate_hash is None:
            previous_hash = None
            continue
        candidate_tree_hash_call_counts[candidate_hash] = (
            candidate_tree_hash_call_counts.get(candidate_hash, 0) + 1
        )
        if previous_hash is not None:
            if candidate_hash == previous_hash:
                unchanged_repeat_count += 1
            else:
                modified_rerun_count += 1
        previous_hash = candidate_hash
    return {
        "schema_version": "v4-direct-evas-usage-v2",
        "calls_executed": len(invocations),
        "calls_succeeded": statuses.count("succeeded"),
        "calls_failed": statuses.count("failed"),
        "calls_timed_out": statuses.count("timed_out"),
        "calls_interrupted": statuses.count("interrupted"),
        "last_status": statuses[-1] if statuses else None,
        "candidate_tree_schema_version": CANDIDATE_TREE_SCHEMA_VERSION,
        "calls_with_candidate_tree_hash": sum(
            candidate_tree_hash_call_counts.values()
        ),
        "unique_candidate_tree_hashes": list(
            candidate_tree_hash_call_counts
        ),
        "candidate_tree_hash_call_counts": candidate_tree_hash_call_counts,
        "modified_rerun_count": modified_rerun_count,
        "unchanged_repeat_count": unchanged_repeat_count,
    }


def evas_invocation_incidents(invocations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    incidents: list[dict[str, Any]] = []
    for row in invocations:
        status = str(row.get("status") or "unknown")
        if status == "succeeded":
            continue
        incidents.append(
            {
                "phase": "tool",
                "component": "evas",
                "category": (
                    "evas_command_timeout"
                    if status == "timed_out"
                    else "evas_command_interrupted"
                    if status == "interrupted"
                    else "evas_command_failure"
                ),
                "responsibility": "candidate_or_model",
                "retryable": True,
                "invocation_id": row.get("invocation_id"),
                "returncode": row.get("returncode"),
            }
        )
    return incidents


def classify_execution_exception(exc: Exception) -> dict[str, Any]:
    error_type = type(exc).__name__
    message = str(exc).lower()
    if isinstance(exc, SandboxStartupError):
        return {
            "status": "infrastructure_failure", "termination_reason": "sandbox_startup",
            "model_status": "runner_failure",
            "incident": {
                "category": "sandbox_startup", "component": "sandbox",
                "error_type": error_type, "phase": "setup",
                "responsibility": "infrastructure", "retryable": True,
            },
        }
    if isinstance(exc, RuntimeExportError):
        return {
            "status": "infrastructure_failure",
            "termination_reason": "runtime_export_failure",
            "model_status": "runner_failure",
            "incident": {
                "category": "runtime_export_failure",
                "component": "runner",
                "error_type": error_type,
                "phase": "setup",
                "responsibility": "infrastructure",
                "retryable": True,
            },
        }
    if isinstance(exc, ProviderRequestTimeout):
        return {
            "status": "provider_timeout",
            "termination_reason": "provider_request_timeout",
            "model_status": "provider_failure",
            "incident": {
                "category": "provider_request_timeout",
                "component": "provider",
                "error_type": error_type,
                "phase": "model",
                "responsibility": "infrastructure",
                "retryable": True,
            },
        }
    if isinstance(exc, ProviderAPIError) or (
        isinstance(exc, RuntimeError) and "provider" in message
    ):
        return {
            "status": "provider_error",
            "termination_reason": "provider_api_error",
            "model_status": "provider_failure",
            "incident": {
                "category": "provider_api_error",
                "component": "provider",
                "error_type": error_type,
                "phase": "model",
                "responsibility": "infrastructure",
                "retryable": True,
            },
        }
    if "sandbox" in message:
        category, component = "sandbox_failure", "sandbox"
    elif "evas" in message:
        category, component = "evas_infrastructure_failure", "evas"
    elif isinstance(exc, subprocess.TimeoutExpired):
        category, component = "runner_subprocess_timeout", "runner"
    else:
        category, component = "runner_failure", "runner"
    return {
        "status": "infrastructure_failure" if category != "runner_failure" else "runner_error",
        "termination_reason": category,
        "model_status": "runner_failure",
        "incident": {
            "category": category,
            "component": component,
            "error_type": error_type,
            "phase": "setup" if component in {"sandbox", "evas"} else "runner",
            "responsibility": "infrastructure" if component != "runner" else "runner",
            "retryable": isinstance(exc, subprocess.TimeoutExpired),
        },
    }


def provider_error_is_context_window(error: Any) -> bool:
    text = json.dumps(error, sort_keys=True) if isinstance(error, dict) else str(error)
    lowered = text.lower()
    markers = (
        "contextwindowexceeded",
        "context window",
        "context length",
        "maximum context",
        "max context",
        "too many tokens",
        "tokens exceed",
        "input is too long",
        "prompt is too long",
    )
    return any(marker in lowered for marker in markers)


def pending_tool_calls(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return uncheckpointed calls from the most recent assistant tool turn."""
    assistant_index = next(
        (
            index
            for index in range(len(messages) - 1, -1, -1)
            if messages[index].get("role") == "assistant"
        ),
        None,
    )
    if assistant_index is None:
        return []
    calls = list(messages[assistant_index].get("tool_calls") or [])
    handled = {
        str(message.get("tool_call_id"))
        for message in messages[assistant_index + 1:]
        if message.get("role") == "tool"
    }
    return [call for call in calls if str(call.get("id")) not in handled]


def cell_per_turn_max_tokens(cell: dict[str, Any]) -> int:
    value = cell.get("per_turn_max_tokens", cell.get("max_output_tokens", cell.get("max_working_tokens")))
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"invalid per-turn output-token cap for {cell.get('cell_id')}: {value!r}")
    return value


def cell_output_budget(cell: dict[str, Any]) -> int:
    """Backward-compatible alias for historical budget-reuse tooling."""
    return cell_per_turn_max_tokens(cell)


def validate_campaign_cells(cells: list[dict[str, Any]], release: Path) -> None:
    mode_specs = read_json(release / "prompt_modes" / "modes.json")["modes"]
    task_rows = read_json(release / "TASK_INDEX.json")["tasks"]
    tasks = {str(row["task_id"]): row for row in task_rows}
    seen: set[str] = set()
    arm_contract = {
        "OneShot": ("G0", False),
        "Agent-No-EVAS": ("G2", False),
        "Agentic": ("G2", True),
    }
    for cell in cells:
        cell_id = str(cell.get("cell_id") or "")
        if not re.fullmatch(
            r"v4-[0-9]{3,4}-G[0-5]-r[0-9]{2,}(?:-(?:oneshot|noevas|agentic))?",
            cell_id,
        ):
            raise ValueError(f"invalid campaign cell_id: {cell_id!r}")
        if cell_id in seen:
            raise ValueError(f"duplicate campaign cell_id: {cell_id}")
        seen.add(cell_id)

        mode = str(cell.get("mode") or "")
        if mode not in mode_specs:
            raise ValueError(f"unknown campaign mode for {cell_id}: {mode!r}")
        expected_process = str(mode_specs[mode]["process"])
        if cell.get("process") != expected_process:
            raise ValueError(f"campaign process mismatch for {cell_id}")
        arm = cell.get("experimental_arm")
        if arm is not None:
            if arm not in arm_contract:
                raise ValueError(f"unknown experimental arm for {cell_id}: {arm!r}")
            expected_mode, expected_feedback = arm_contract[arm]
            if mode != expected_mode or cell.get("base_mode") != expected_mode:
                raise ValueError(f"experimental arm mode mismatch for {cell_id}")
            if cell.get("executable_feedback") is not expected_feedback:
                raise ValueError(
                    f"experimental arm executable-feedback mismatch for {cell_id}"
                )

        task_id = str(cell.get("task_id") or "")
        task = tasks.get(task_id)
        if task is None:
            raise ValueError(f"unknown campaign task for {cell_id}: {task_id!r}")
        if str(cell.get("family_id")) != str(task["family_id"]):
            raise ValueError(f"campaign family mismatch for {cell_id}")
        if str(cell.get("form")) != str(task["form"]):
            raise ValueError(f"campaign form mismatch for {cell_id}")
        cell_per_turn_max_tokens(cell)


def safe_relative(raw: str) -> Path:
    path = Path(raw.replace("\\", "/"))
    if not path.parts or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe relative path: {raw!r}")
    return path


def submission_relative(raw: str) -> Path:
    """Normalize the public path spellings exposed by the agent prompt and tools."""
    path = safe_relative(raw)
    if path.parts[:2] == ("public", "submission"):
        path = Path(*path.parts[2:])
    elif path.parts[0] == "submission":
        path = Path(*path.parts[1:])
    if not path.parts:
        raise ValueError(f"submission path names no artifact: {raw!r}")
    return path


def load_key(path: str | None, env_name: str) -> str:
    value = os.environ.get(env_name, "").strip()
    if value:
        return value
    if path:
        value = Path(path).expanduser().read_text(encoding="utf-8").strip()
        if value:
            return value
    raise SystemExit(f"missing credential: set {env_name} or use --api-key-file")


class OpenAICompatible:
    supports_transport_capture = True

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str,
        timeout_s: int,
        temperature: float,
        stream: bool = False,
    ):
        self.endpoint = base_url.rstrip("/")
        if not self.endpoint.endswith("/chat/completions"):
            self.endpoint += "/chat/completions" if self.endpoint.endswith("/v1") else "/v1/chat/completions"
        self.model = model
        self.api_key = api_key
        self.timeout_s = timeout_s
        self.temperature = temperature
        self.stream = stream

    def _redact(self, text: str) -> str:
        return text.replace(self.api_key, "<redacted-provider-credential>") if self.api_key else text

    def complete(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        tools: list[dict[str, Any]] | None,
        *,
        timeout_s: float | None = None,
        transport_observer=None,
    ) -> dict[str, Any]:
        effective_timeout_s = max(0.1, float(timeout_s or self.timeout_s))
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": self.temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        if self.stream:
            payload["stream"] = True
            capture_options = ({"transport_observer": transport_observer}
                               if transport_observer is not None else {})
            return self._complete_stream(payload, timeout_s=effective_timeout_s,
                                         **capture_options)
        completed = None
        deadline = time.monotonic() + effective_timeout_s
        for attempt in range(1, 4):
            attempt_timeout_s = max(0.1, deadline - time.monotonic())
            with tempfile.TemporaryDirectory(prefix="v4_provider_") as td:
                root = Path(td)
                payload_path = root / "payload.json"
                header_path = root / "headers.txt"
                payload_path.write_text(json.dumps(payload), encoding="utf-8")
                header_path.write_text(
                    f"Authorization: Bearer {self.api_key}\nContent-Type: application/json\n",
                    encoding="utf-8",
                )
                header_path.chmod(0o600)
                completed = self._capture_transport(lambda: subprocess.run(
                    [
                        "curl", "-sS", "--max-time", f"{attempt_timeout_s:.3f}",
                        self.endpoint, "-H", f"@{header_path}",
                        "--data-binary", f"@{payload_path}",
                    ],
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=attempt_timeout_s + 0.5, check=False,
                ), attempt=attempt, observer=transport_observer)
            if completed.returncode == 0:
                break
            if attempt < 3 and time.monotonic() < deadline:
                time.sleep(min(2 * attempt, max(0.0, deadline - time.monotonic())))
            if time.monotonic() >= deadline:
                break
        assert completed is not None
        if completed.returncode == 28:
            raise ProviderRequestTimeout(
                f"provider request exceeded {self.timeout_s}s after 3 attempts"
            )
        if completed.returncode != 0:
            raise ProviderTransportError(
                f"provider transport failed after 3 attempts rc={completed.returncode}: "
                f"{self._redact(completed.stderr[-2000:])}"
            )
        try:
            response = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "provider returned non-JSON response "
                f"status=transport_ok stdout_len={len(completed.stdout)} "
                f"stderr_len={len(completed.stderr)} "
                f"stdout_tail={self._redact(completed.stdout[-2000:])!r} "
                f"stderr_tail={self._redact(completed.stderr[-2000:])!r}"
            ) from exc
        if response.get("error"):
            if provider_error_is_context_window(response["error"]):
                raise ProviderContextWindowExceeded(
                    f"provider context window exceeded: {self._redact(json.dumps(response['error'])[:2000])}"
                )
            error = self._redact(json.dumps(response["error"])[:2000])
            raise ProviderAPIError(f"provider error: {error}")
        return response

    def _capture_transport(self, execute, *, attempt: int, observer):
        """Opt-in private decoded transport capture; never retain auth headers."""
        if observer is None:
            return execute()
        started = time.monotonic()

        def captured(value):
            if isinstance(value, bytes):
                value = value.decode("utf-8", errors="replace")
            text = self._redact(value or "")
            raw = text.encode("utf-8")
            limit = 64 * 1024
            retained = raw if len(raw) <= limit else raw[:limit // 2] + raw[-limit // 2:]
            return {
                "encoding": "utf8_redacted_decoded_transport",
                "text": retained.decode("utf-8", errors="replace"),
                "bytes_sha256": hashlib.sha256(raw).hexdigest(),
                "total_bytes": len(raw), "retained_bytes": len(retained),
                "truncated_bytes": len(raw) - len(retained),
            }

        try:
            completed = execute()
        except Exception as exc:
            observer({
                "transport_attempt": attempt, "returncode": None,
                "error_type": type(exc).__name__, "capture_complete": False,
                "elapsed_s": time.monotonic() - started,
                "stdout": captured(getattr(exc, "stdout", None)),
                "stderr": captured(getattr(exc, "stderr", None)),
            })
            raise
        observer({
            "transport_attempt": attempt, "returncode": completed.returncode,
            "error_type": None, "capture_complete": True,
            "elapsed_s": time.monotonic() - started,
            "stdout": captured(completed.stdout), "stderr": captured(completed.stderr),
        })
        return completed

    def _curl_payload(self, payload: dict[str, Any], *, timeout_s: float) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="v4_provider_") as td:
            root = Path(td)
            payload_path = root / "payload.json"
            header_path = root / "headers.txt"
            payload_path.write_text(json.dumps(payload), encoding="utf-8")
            header_path.write_text(
                f"Authorization: Bearer {self.api_key}\nContent-Type: application/json\n",
                encoding="utf-8",
            )
            header_path.chmod(0o600)
            return subprocess.run(
                [
                    "curl", "-sS", "--no-buffer", "--max-time", f"{timeout_s:.3f}",
                    self.endpoint, "-H", f"@{header_path}",
                    "--data-binary", f"@{payload_path}",
                ],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=timeout_s + 0.5, check=False,
            )

    def _complete_stream(self, payload: dict[str, Any], *, timeout_s: float,
                         transport_observer=None) -> dict[str, Any]:
        completed = None
        deadline = time.monotonic() + timeout_s
        for attempt in range(1, 4):
            attempt_timeout_s = max(0.1, deadline - time.monotonic())
            completed = self._capture_transport(
                lambda: self._curl_payload(payload, timeout_s=attempt_timeout_s),
                attempt=attempt, observer=transport_observer,
            )
            if completed.returncode == 0:
                break
            if attempt < 3 and time.monotonic() < deadline:
                time.sleep(min(2 * attempt, max(0.0, deadline - time.monotonic())))
            if time.monotonic() >= deadline:
                break
        assert completed is not None
        if completed.returncode == 28:
            raise ProviderRequestTimeout(
                f"provider streaming request exceeded {self.timeout_s}s after 3 attempts"
            )
        if completed.returncode != 0:
            raise ProviderTransportError(
                f"provider streaming transport failed after 3 attempts rc={completed.returncode}: "
                f"{self._redact(completed.stderr[-2000:])}"
            )
        try:
            return parse_openai_sse_response(completed.stdout, completed.stderr)
        except RuntimeError as exc:
            raise RuntimeError(self._redact(str(exc))) from None


def parse_openai_sse_response(stdout: str, stderr: str = "") -> dict[str, Any]:
    content_parts: list[str] = []
    reasoning_parts: list[str] = []
    tool_calls_by_index: dict[int, dict[str, Any]] = {}
    finish_reason = None
    usage = None
    metadata: dict[str, Any] = {"object": "chat.completion"}
    chunk_count = 0
    for raw in stdout.splitlines():
        line = raw.strip()
        if not line or line.startswith(":"):
            continue
        if not line.startswith("data:"):
            continue
        data = line.removeprefix("data:").strip()
        if data == "[DONE]":
            continue
        try:
            chunk = json.loads(data)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "provider returned malformed streaming JSON "
                f"stdout_len={len(stdout)} stderr_len={len(stderr)} "
                f"line_tail={line[-1000:]!r} stderr_tail={stderr[-2000:]!r}"
            ) from exc
        chunk_count += 1
        if chunk.get("error"):
            if provider_error_is_context_window(chunk["error"]):
                raise ProviderContextWindowExceeded(
                    f"provider context window exceeded: {json.dumps(chunk['error'])[:2000]}"
                )
            raise ProviderAPIError(f"provider streaming error: {json.dumps(chunk['error'])[:2000]}")
        for key in ("id", "model", "created", "system_fingerprint"):
            if chunk.get(key) is not None:
                metadata[key] = chunk.get(key)
        if chunk.get("usage") is not None:
            usage = chunk.get("usage")
        choices = chunk.get("choices") or []
        if not choices:
            continue
        choice = choices[0]
        if choice.get("finish_reason") is not None:
            finish_reason = choice.get("finish_reason")
        delta = choice.get("delta") or {}
        if delta.get("content") is not None:
            content_parts.append(str(delta.get("content") or ""))
        if delta.get("reasoning_content") is not None:
            reasoning_parts.append(str(delta.get("reasoning_content") or ""))
        for tool_delta in delta.get("tool_calls") or []:
            index = int(tool_delta.get("index", 0))
            call = tool_calls_by_index.setdefault(
                index,
                {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
            )
            if tool_delta.get("id"):
                call["id"] = str(tool_delta["id"])
            if tool_delta.get("type"):
                call["type"] = str(tool_delta["type"])
            function_delta = tool_delta.get("function") or {}
            if function_delta.get("name") is not None:
                call["function"]["name"] += str(function_delta.get("name") or "")
            if function_delta.get("arguments") is not None:
                call["function"]["arguments"] += str(function_delta.get("arguments") or "")
    if chunk_count == 0:
        raise RuntimeError(
            "provider returned empty streaming response "
            f"stdout_len={len(stdout)} stderr_len={len(stderr)} stdout_tail={stdout[-2000:]!r} "
            f"stderr_tail={stderr[-2000:]!r}"
        )
    message: dict[str, Any] = {
        "role": "assistant",
        "content": "".join(content_parts),
    }
    if reasoning_parts:
        message["reasoning_content"] = "".join(reasoning_parts)
    tool_calls = [tool_calls_by_index[index] for index in sorted(tool_calls_by_index)]
    if tool_calls:
        message["tool_calls"] = tool_calls
    response = {
        **metadata,
        "choices": [{"index": 0, "message": message, "finish_reason": finish_reason}],
        "usage": usage,
        "streaming_chunk_count": chunk_count,
    }
    return response


TOOLS = [
    {"type": "function", "function": {"name": "list_files", "description": "List readable task files and writable submission files.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a public task or submission text file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Create or replace a submission file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "run_evas", "description": "Run EVAS against the task-local visible test. Testbench tasks require one public case name from evas_runtime.json.", "parameters": {"type": "object", "properties": {"case": {"type": "string"}}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "finalize", "description": "Finalize the current submission.", "parameters": {"type": "object", "properties": {}}}},
]
SKILL_TOOLS = [
    {"type": "function", "function": {"name": "list_skills", "description": "List available read-only skill packages for this mode.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "read_skill", "description": "Read one text file from an available skill package.", "parameters": {"type": "object", "properties": {"skill": {"type": "string"}, "path": {"type": "string", "description": "Relative path inside the skill package, such as SKILL.md or references/runtime-contract.md."}}, "required": ["skill", "path"], "additionalProperties": False}}},
]
TEXT_SKILL_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".json", ".va"}
MAX_SKILL_FILE_BYTES = 256 * 1024


def command_result(
    command: str,
    runtime: Path,
    timeout_s: float,
    submission_dir: Path | None = None,
    extra_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    effective_submission = submission_dir or runtime / "public" / "submission"
    env = os.environ.copy()
    env.update({
        "VABENCH_RUNTIME_DIR": str(runtime),
        "VABENCH_PUBLIC_DIR": str(runtime / "public"),
        "VABENCH_SUBMISSION_DIR": str(effective_submission),
        "VABENCH_FINAL_SUBMISSION_DIR": str(effective_submission),
        "VABENCH_EVALUATOR_DIR": str(runtime / "evaluator"),
        "VABENCH_TRUSTED_REPLAY_RESULT": str(
            runtime / "evidence" / "trusted_replay_result.json"
        ),
    })
    env.update(extra_env or {})
    started = time.monotonic()
    try:
        completed = subprocess.run(
            shlex.split(command), cwd=REPO, env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_s, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else exc.stderr
        return {
            "execution_status": "timeout",
            "returncode": None,
            "stdout": (stdout or "")[-12000:],
            "stderr": (stderr or "")[-4000:],
            "elapsed_s": time.monotonic() - started,
        }
    except OSError as exc:
        return {
            "execution_status": "launch_error",
            "returncode": None,
            "stdout": "",
            "stderr": str(exc)[:4000],
            "elapsed_s": time.monotonic() - started,
        }
    return {
        "execution_status": "completed",
        "returncode": completed.returncode,
        "stdout": completed.stdout[-12000:],
        "stderr": completed.stderr[-4000:],
        "elapsed_s": time.monotonic() - started,
    }


def argv_result(argv: list[str], runtime: Path, timeout_s: int) -> dict[str, Any]:
    """Run one operator-selected executable with benchmark-controlled arguments."""
    started = time.monotonic()
    try:
        completed = subprocess.run(
            argv,
            cwd=runtime,
            env=os.environ.copy(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else exc.stderr
        return {
            "execution_status": "timeout",
            "returncode": None,
            "stdout": (stdout or "")[-12000:],
            "stderr": (stderr or "")[-4000:],
            "elapsed_s": time.monotonic() - started,
        }
    except OSError as exc:
        return {
            "execution_status": "launch_error",
            "returncode": None,
            "stdout": "",
            "stderr": str(exc)[:4000],
            "elapsed_s": time.monotonic() - started,
        }
    return {
        "execution_status": "completed",
        "returncode": completed.returncode,
        "stdout": completed.stdout[-12000:],
        "stderr": completed.stderr[-4000:],
        "elapsed_s": time.monotonic() - started,
    }


def confined_path(root: Path, relative: str) -> Path:
    path = root / safe_relative(relative)
    path.resolve().relative_to(root.resolve())
    return path


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


def validate_public_testbench(candidate: Path) -> None:
    if candidate.is_symlink() or candidate.stat().st_size > 1_000_000:
        raise ValueError("candidate testbench must be a regular file no larger than 1 MB")
    text = candidate.read_text(encoding="utf-8")
    uncommented = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    uncommented = "\n".join(line.split("//", 1)[0] for line in uncommented.splitlines())
    if PUBLIC_ESCAPE_RE.search(uncommented):
        raise ValueError("candidate testbench contains a forbidden process or network escape")
    includes = PUBLIC_INCLUDE_RE.findall(uncommented)
    if not includes:
        raise ValueError("candidate testbench must include its public DUT fixture")
    for raw in includes:
        include = Path(raw.replace("\\", "/"))
        if include.is_absolute() or ".." in include.parts:
            raise ValueError("candidate testbench include escapes the public DUT fixture")
        if not include.parts or include.parts[0] != "dut":
            raise ValueError("candidate testbench includes must remain below ./dut")


def run_public_evas(
    runtime: Path,
    arguments: dict[str, Any],
    timeout_s: float,
    evas_command: str,
) -> dict[str, Any]:
    """Execute only the fixed public EVAS contract, never an agent-supplied command."""
    source_diagnostics = submission_source_diagnostics(runtime)
    if source_diagnostics:
        return {
            "execution_status": "candidate_rejected",
            "returncode": 2,
            "stdout": "",
            "stderr": "candidate source rejected: " + "; ".join(source_diagnostics),
            "elapsed_s": 0.0,
            "status": "fail",
        }
    public = runtime / "public"
    task = public / "task"
    submission = public / "submission"
    contract_path = task / "evas_runtime.json"
    if not contract_path.is_file():
        return {"status": "unavailable", "reason": "public EVAS runtime contract is missing"}
    contract = read_json(contract_path)
    schema_version = str(contract.get("schema_version") or "")
    expected_working_directory = (
        "public_root"
        if schema_version == "r52-direct-evas-testbench-reference-v1"
        else "runtime_package_root"
    )
    if contract.get("working_directory") != expected_working_directory:
        raise ValueError("unsupported EVAS working directory")
    executable = shlex.split(evas_command)
    if not executable:
        raise ValueError("empty EVAS executable command")

    runtime_version = schema_version.rsplit("-v", 1)[-1]
    portable_runtime = runtime_version == "3"
    if portable_runtime:
        if contract.get("compatibility_mode") != "portable":
            raise ValueError("v3 public EVAS runtimes must declare portable compatibility mode")
        strict_args: list[str] = []
    else:
        strict_args = ["--spectre-strict"]
    requested_case = arguments.get("case")
    if schema_version in DIRECT_DUT_RUNTIME_SCHEMAS:
        if requested_case not in (None, ""):
            raise ValueError("DUT and bugfix visible tests do not accept a case")
        expected_output = (
            "public/submission/evas-output"
            if schema_version.endswith("-v1")
            else "/tmp/vabench-visible/evas-output"
        )
        expected_command = (
            "evas simulate public/task/visible_test.scs -o "
            f"{expected_output}"
            + ("" if portable_runtime else " --spectre-strict")
        )
        if contract.get("command") != expected_command:
            raise ValueError("unrecognized public EVAS command contract")
        deck = confined_path(runtime, "public/task/visible_test.scs")
        output = confined_path(runtime, ".vabench-visible/evas-output")
        if not deck.is_file():
            raise FileNotFoundError("visible_test.scs is missing")
        argv = [*executable, "simulate", str(deck), "-o", str(output), *strict_args]
        result = argv_result(argv, runtime, timeout_s)
        result.update({
            "status": "pass" if result.get("returncode") == 0 else "fail",
            "case": None,
            "test": "public/task/visible_test.scs",
        })
        return result

    if schema_version not in DIRECT_TESTBENCH_RUNTIME_SCHEMAS:
        raise ValueError(f"unsupported public EVAS runtime schema: {schema_version!r}")
    if schema_version == "r52-direct-evas-testbench-reference-v1":
        if requested_case not in (None, "", "reference"):
            raise ValueError("public Testbench EVAS feedback is reference-only")
        if contract.get("feedback_scope") != "reference_dut_only":
            raise ValueError("unrecognized public Testbench EVAS feedback scope")
        if contract.get("candidate") != "submission/testbench.scs":
            raise ValueError("unrecognized testbench candidate path")
        if contract.get("reference_dut_root") != "task/supplied_dut":
            raise ValueError("unrecognized public reference DUT path")
        candidate = confined_path(submission, "testbench.scs")
        if not candidate.is_file():
            raise FileNotFoundError("submission/testbench.scs is missing")
        validate_public_testbench(candidate)
        reference_dut = confined_path(task, "supplied_dut")
        if not reference_dut.is_dir():
            raise FileNotFoundError("public reference DUT is missing")
        scratch_root = runtime / ".vabench-visible"
        run_dir = confined_path(scratch_root, "reference")
        if run_dir.exists():
            shutil.rmtree(run_dir)
        run_dir.mkdir(parents=True)
        shutil.copy2(candidate, run_dir / "testbench.scs")
        shutil.copytree(reference_dut, run_dir / "dut")
        output = confined_path(scratch_root, "evas-output/reference")
        argv = [
            *executable,
            "simulate",
            str(run_dir / "testbench.scs"),
            "-o",
            str(output),
            *strict_args,
        ]
        result = argv_result(argv, runtime, timeout_s)
        result.update({
            "status": "pass" if result.get("returncode") == 0 else "fail",
            "case": "reference",
            "test": ".vabench-visible/reference/testbench.scs",
        })
        return result
    if contract.get("fixture_policy") != "read_only_and_identical_for_visible_and_final_replay":
        raise ValueError("unsupported public fixture policy")
    if contract.get("candidate") != "public/submission/testbench.scs":
        raise ValueError("unrecognized testbench candidate path")
    if portable_runtime and not str(contract.get("candidate_command_template") or "").endswith(
        "-o /tmp/vabench-visible/evas-output/{case}"
    ):
        raise ValueError("unrecognized portable testbench EVAS command contract")
    case = str(requested_case or "")
    cases = {
        str(row.get("case")): str(row.get("dut_root"))
        for row in contract.get("cases") or []
        if isinstance(row, dict)
    }
    expected_cases = {"reference", *(f"mutation_{index:02d}" for index in range(1, 6))}
    if set(cases) != expected_cases:
        raise ValueError("public EVAS testbench suite must contain reference plus five mutations")
    if case not in cases:
        raise ValueError(f"unknown public EVAS case: {case!r}; choose one of {sorted(cases)}")
    if not re.fullmatch(r"reference|mutation_0[1-5]", case):
        raise ValueError("public EVAS case name is outside the fixed suite")
    candidate = confined_path(submission, "testbench.scs")
    if not candidate.is_file():
        raise FileNotFoundError("submission/testbench.scs is missing")
    validate_public_testbench(candidate)
    fixture = confined_path(task, cases[case])
    fixture.resolve().relative_to((task / "visible_fixtures").resolve())
    if not fixture.is_dir():
        raise FileNotFoundError(f"public fixture is missing for {case}")

    scratch_root = runtime / ".vabench-visible"
    run_dir = confined_path(scratch_root, f"runs/{case}")
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    shutil.copy2(candidate, run_dir / "testbench.scs")
    shutil.copytree(fixture, run_dir / "dut")
    output = confined_path(scratch_root, f"evas-output/{case}")
    argv = [
        *executable,
        "simulate",
        str(run_dir / "testbench.scs"),
        "-o",
        str(output),
        *strict_args,
    ]
    result = argv_result(argv, runtime, timeout_s)
    result.update({
        "status": "pass" if result.get("returncode") == 0 else "fail",
        "case": case,
        "test": (
            f"submission/runs/{case}/testbench.scs"
            if schema_version.endswith("-v1")
            else f".vabench-visible/runs/{case}/testbench.scs"
        ),
    })
    return result


def load_trusted_replay_adapter_result(runtime: Path) -> dict[str, Any] | None:
    path = runtime / "evidence" / "trusted_replay_result.json"
    if not path.is_file():
        return None
    try:
        value = read_json(path)
    except (OSError, json.JSONDecodeError):
        return {"status": "infrastructure_failure", "diagnostics": ["invalid_result_json"]}
    if not isinstance(value, dict):
        return {
            "status": "infrastructure_failure",
            "diagnostics": ["trusted_replay_result_must_be_an_object"],
        }
    return value


class FinalReplayReservedError(RuntimeError):
    """A terminal scoring runtime cannot reenter generation or final judging."""


def assert_final_replay_not_started(runtime: Path) -> None:
    reservation = runtime / "evidence/bound-final-test"
    if reservation.exists() or reservation.is_symlink():
        raise FinalReplayReservedError("final replay already reserved; model reentry and in-place retry are forbidden")


def run_trusted_replay(
    runtime: Path,
    command: str | None,
    timeout_s: int,
    evas_command: str,
    final_submission: dict[str, Any] | None = None,
    *,
    final_test_profile: dict[str, Any] | None = None,
    episode_context: Any = None,
) -> dict[str, Any]:
    assert_final_replay_not_started(runtime)
    if final_test_profile is not None or episode_context is not None:
        if final_test_profile is None or episode_context is None or not command or final_submission is None:
            raise ValueError("bound replay requires profile, context, command and frozen submission")
        from final_replay import execute_bound_replay

        return execute_bound_replay(
            runtime=runtime, command=command, timeout_s=timeout_s, evas_command=evas_command,
            final_submission=final_submission, final_test_profile=final_test_profile,
            context=episode_context, execute=_run_trusted_replay,
        )
    return _run_trusted_replay(runtime, command, timeout_s, evas_command, final_submission)


def _run_trusted_replay(
    runtime: Path, command: str | None, timeout_s: int, evas_command: str,
    final_submission: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result_path = runtime / "evidence" / "trusted_replay_result.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.unlink(missing_ok=True)
    test_manifest = RESULT_PROTOCOL.hash_test_tree(runtime / "evaluator")
    identity = RESULT_PROTOCOL.evas_identity(shlex.split(evas_command))
    submission_dir = runtime / "evidence" / "final_submission"
    command_record = (
        command_result(
            command,
            runtime,
            timeout_s,
            submission_dir,
            {"VABENCH_EVAS_COMMAND": evas_command},
        )
        if command
        else None
    )
    adapter_result = load_trusted_replay_adapter_result(runtime) if command else None
    return RESULT_PROTOCOL.trusted_replay(
        command_record,
        adapter_result,
        test_manifest,
        identity,
        (final_submission or {}).get("tree_sha256"),
    )


def attach_experiment_result(
    result: dict[str, Any],
    runtime: Path,
    messages: list[dict[str, Any]],
    args: argparse.Namespace,
    model_status: str,
) -> None:
    gate = submission_artifact_gate(runtime)
    final_submission = RESULT_PROTOCOL.snapshot_submission(runtime, gate)
    replay = run_trusted_replay(
        runtime,
        args.final_judge_command if gate["passed"] else None,
        args.judge_timeout_s,
        args.evas_command,
        final_submission,
    )
    result["experiment_result"] = RESULT_PROTOCOL.build_experiment_result(
        cell=result.get("cell") or {},
        model_status=model_status,
        messages=messages,
        artifact_gate=gate,
        runtime=runtime,
        replay=replay,
        final_submission=final_submission,
    )
    result["skill_lookup_events"] = read_skill_lookup_events(runtime)
    if replay.get("command") is not None:
        result["final_judge"] = replay["command"]


def compact_text_lines(text: str, *, limit: int = 24) -> list[str]:
    """Keep high-signal feedback lines without echoing simulator counters.

    Feedback stdout can include thousands of low-level simulator timing and
    instrumentation lines.  Returning all of that to the model repeatedly burns
    provider context and token telemetry without materially improving repairs.  Keep the
    public oracle summaries, validation diagnostics, and concrete errors.
    """
    semantic: list[str] = []
    errors: list[str] = []
    markers: list[str] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line in seen:
            continue
        seen.add(line)
        lowered = line.lower()
        clipped = line[:1000]
        if re.fullmatch(r"required_trace_missing_node_count\s*=\s*0", lowered):
            continue
        if (
            re.search(r"\bP_[A-Z0-9_]+\b", line)
            or any(
                token in lowered
                for token in (
                    "mismatch",
                    "expected=",
                    "observed=",
                    "failure_detail=",
                    "failures=",
                    "missing_",
                    "metric_gap=",
                    "tolerance=",
                    "checked=",
                    "coverage=",
                )
            )
            or line.startswith("reference:")
            or re.match(r"negative_[0-9]+:", line)
        ):
            semantic.append(clipped)
        elif (
            "simulation failed" in lowered
            or "failed to compile" in lowered
            or "failed to parse" in lowered
            or "parse error" in lowered
            or "syntax error" in lowered
            or "invalid source" in lowered
            or "missing required" in lowered
            or "timed out" in lowered
            or "rustsimprogram rejection:" in lowered
            or "not_lowered" in lowered
            or re.search(r"\b[A-Za-z_][A-Za-z0-9_]*(?:Error|Exception):", line)
            or re.search(r"(^|\s)(error|fatal|panic|exception)(\s|:|\[)", lowered)
            or any(
                token in lowered
                for token in (
                    "unexpected token",
                    "unknown parameter",
                    "unknown instance",
                    "unsupported construct",
                    "unresolved reference",
                    "no such file",
                )
            )
        ):
            errors.append(clipped)
        elif line.startswith(FEEDBACK_SIGNAL_PREFIXES):
            markers.append(clipped)

    selected: list[str] = []
    for group in (semantic, errors, markers):
        for line in group:
            if line not in selected:
                selected.append(line)
            if len(selected) >= limit:
                return selected
    if selected:
        return selected
    tail = [line.strip() for line in text.splitlines() if line.strip()]
    return [line[:1000] for line in tail[-min(limit, 6):]]


def compact_feedback_result(result: dict[str, Any]) -> dict[str, Any]:
    stdout = str(result.get("stdout") or "")
    stderr = str(result.get("stderr") or "")
    lines = compact_text_lines("\n".join(part for part in (stdout, stderr) if part))
    markers = [line for line in lines if line.startswith("FEEDBACK_")]
    compact: dict[str, Any] = {
        "schema_version": "v4-feedback-tool-result-compact-v1",
        "returncode": result.get("returncode"),
        "elapsed_s": result.get("elapsed_s"),
        "status": "pass" if result.get("returncode") == 0 else "fail",
        "markers": markers[-4:],
        "diagnostics": lines,
        "stdout_chars": len(stdout),
        "stderr_chars": len(stderr),
        "compacted": True,
    }
    if stderr:
        compact["stderr_excerpt"] = compact_text_lines(stderr, limit=12)
    return compact


def complete_one_missing_json_closer(raw: str) -> dict[str, Any] | None:
    expected: list[str] = []
    in_string = False
    escaped = False
    for character in raw:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            expected.append("}")
        elif character == "[":
            expected.append("]")
        elif character in "}]":
            if not expected or expected.pop() != character:
                return None
    if in_string or escaped or len(expected) != 1:
        return None
    try:
        decoded = json.loads(raw + expected[-1])
    except json.JSONDecodeError:
        return None
    return decoded if isinstance(decoded, dict) else None


def decode_tool_arguments(
    name: str, raw_arguments: str | None,
) -> tuple[dict[str, Any], bool, str | None]:
    raw = raw_arguments or "{}"
    try:
        decoded = json.loads(raw)
        if not isinstance(decoded, dict):
            raise ValueError("tool arguments must be a JSON object")
        return decoded, True, None
    except json.JSONDecodeError:
        if name != "submit_artifacts":
            raise

    stripped = raw.lstrip()
    if stripped.endswith(">}"):
        without_marker_fragment = stripped[:-2] + "}"
        try:
            decoded = json.loads(without_marker_fragment)
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(decoded, dict):
                return decoded, False, "removed_trailing_marker_fragment"
    completed = complete_one_missing_json_closer(stripped)
    if completed is not None:
        return completed, False, "completed_missing_closer"
    decoded, end = json.JSONDecoder().raw_decode(stripped)
    if not isinstance(decoded, dict):
        raise ValueError("submit_artifacts arguments must be a JSON object")
    trailing = stripped[end:].strip()
    if not trailing or any(character not in "}]" for character in trailing):
        raise ValueError("ambiguous trailing submit_artifacts content")
    artifacts = decoded.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("submit_artifacts requires an artifacts object")
    redundant = {
        key: value for key, value in decoded.items() if key != "artifacts"
    }
    if any(
        key not in artifacts or value != artifacts[key]
        for key, value in redundant.items()
    ):
        raise ValueError("conflicting submit_artifacts wrapper fields")
    return {"artifacts": artifacts}, False, "redundant_artifact_wrapper"


def execute_tool(
    name: str,
    arguments: dict[str, Any],
    runtime: Path,
    timeout_s: int,
    evas_command: str,
) -> tuple[str, bool]:
    public = runtime / "public"
    submission = public / "submission"
    if name == "list_skills":
        return json.dumps(list_available_skills(runtime), sort_keys=True), False
    if name == "read_skill":
        return read_skill_file(runtime, str(arguments["skill"]), str(arguments["path"])), False
    if name == "list_files":
        rows = []
        for root, label in ((public / "task", "task"), (submission, "submission")):
            rows.extend(f"{label}/{p.relative_to(root).as_posix()}" for p in sorted(root.rglob("*")) if p.is_file())
        return json.dumps({"files": rows}), False
    if name == "read_file":
        relative = safe_relative(str(arguments["path"]))
        if relative.parts[:2] == ("public", "task"):
            relative = Path("task", *relative.parts[2:])
        elif relative.parts[:2] == ("public", "submission"):
            relative = Path("submission", *relative.parts[2:])
        elif relative.parts[0] not in {"task", "submission"}:
            relative = Path("submission") / relative
        path = public / relative
        path.resolve().relative_to(public.resolve())
        relative_key = relative.as_posix()
        if relative_key in PROMPT_EMBEDDED_TASK_FILES:
            summary = file_digest_summary(path)
            return json.dumps({
                "status": "already_in_initial_prompt",
                "path": relative_key,
                "note": (
                    "This immutable task file was included verbatim in the initial prompt; "
                    "use that copy instead of spending another tool-result round on it."
                ),
                **summary,
            }), False
        immutable_task_file = relative.parts[:1] == ("task",)
        if immutable_task_file:
            delivered = read_tool_delivery_cache(runtime)
            if relative_key in delivered:
                summary = file_digest_summary(path)
                return json.dumps({
                    "status": "already_provided_in_this_episode",
                    "path": relative_key,
                    "note": "This read-only task file was already returned earlier in the conversation.",
                    **summary,
                }), False
        text = path.read_text(encoding="utf-8")
        if immutable_task_file:
            delivered = read_tool_delivery_cache(runtime)
            delivered.add(relative_key)
            write_tool_delivery_cache(runtime, delivered)
        return text, False
    if name == "write_file":
        relative = submission_relative(str(arguments["path"]))
        path = submission / relative
        path.resolve().relative_to(submission.resolve())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(arguments["content"]), encoding="utf-8")
        return json.dumps({"written": relative.as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}), False
    if name == "submit_artifacts":
        raw_artifacts = arguments.get("artifacts")
        if not isinstance(raw_artifacts, dict):
            raise ValueError("submit_artifacts requires an artifacts object")
        expected = expected_candidate_artifacts(runtime)
        observed = [str(path) for path in raw_artifacts]
        diagnostics = [
            *(f"missing_artifact_path:{path}" for path in expected if path not in observed),
            *(
                f"undeclared_artifact_path:{path}"
                for path in observed
                if path not in set(expected)
            ),
        ]
        if diagnostics:
            raise ValueError(", ".join(diagnostics))
        mapping: dict[str, str] = {}
        for path in expected:
            content = raw_artifacts[path]
            if not isinstance(content, str) or not content.strip():
                raise ValueError(f"empty_or_nontext_artifact:{path}")
            mapping[path] = content
        saved = write_artifact_mapping(mapping, runtime)
        gate = submission_artifact_gate(runtime)
        if not gate["passed"]:
            raise ValueError(", ".join(gate["diagnostics"]))
        return json.dumps({
            "status": "submitted",
            "saved_files": saved,
            "artifact_gate": gate,
        }, sort_keys=True), True
    if name == "run_evas":
        return json.dumps(run_public_evas(runtime, arguments, timeout_s, evas_command)), False
    if name == "finalize":
        return json.dumps({"status": "finalized"}), True
    raise ValueError(f"unknown tool: {name}")


def list_available_skills(runtime: Path) -> dict[str, Any]:
    public_path = runtime / "public"
    if public_path.is_symlink():
        raise ValueError("runtime public root is a symlink")
    public_root = public_path.resolve()
    skills_path = public_path / "skills"
    if skills_path.is_symlink():
        raise ValueError("runtime skills root is a symlink")
    skills_root = skills_path.resolve()
    try:
        skills_root.relative_to(public_root)
    except ValueError as exc:
        raise ValueError("runtime skills root escapes the public bundle") from exc
    manifest_path = skills_path / "SNAPSHOT_MANIFEST.json"
    if not manifest_path.is_file():
        return {"schema_version": "v4-runtime-skill-list-v1", "skills": {}}
    if manifest_path.is_symlink():
        raise ValueError("runtime skill manifest is a symlink")
    manifest = read_json(manifest_path)
    if manifest.get("schema_version") != "v4-runtime-skill-manifest-v1":
        raise ValueError("runtime skill manifest schema mismatch")
    skills = manifest.get("skills") or {}
    if not isinstance(skills, dict):
        raise ValueError("runtime skill manifest skills must be an object")
    result: dict[str, dict[str, Any]] = {}
    for raw_skill_id, record in sorted(skills.items()):
        skill_id = str(raw_skill_id)
        if re.fullmatch(r"[a-z0-9][a-z0-9-]*", skill_id) is None:
            raise ValueError(f"invalid runtime skill identifier: {skill_id!r}")
        if not isinstance(record, dict):
            raise ValueError(f"invalid runtime skill record: {skill_id}")
        if record.get("skill_file") != f"public/skills/{skill_id}/SKILL.md":
            raise ValueError(f"runtime skill has a noncanonical SKILL.md path: {skill_id}")
        raw_root = runtime / "public" / "skills" / skill_id
        if raw_root.is_symlink():
            raise ValueError(f"runtime skill root is a symlink: {skill_id}")
        root = raw_root.resolve()
        if not (root / "SKILL.md").is_file():
            raise ValueError(f"runtime skill is missing SKILL.md: {skill_id}")
        if any(item.is_symlink() for item in root.rglob("*")):
            raise ValueError(f"runtime skill contains a symlink: {skill_id}")
        observed_tree = skill_tree_sha(root)
        if record.get("tree_sha256") != observed_tree:
            raise ValueError(f"runtime skill tree hash mismatch: {skill_id}")
        files = record.get("files") or []
        indexed_files = []
        indexed_paths: set[str] = set()
        for file_record in files:
            if not isinstance(file_record, dict):
                raise ValueError(f"invalid runtime skill file record: {skill_id}")
            relative = safe_relative(str(file_record.get("path") or ""))
            if relative.as_posix() in indexed_paths:
                raise ValueError(
                    f"runtime skill file index has a duplicate: {skill_id}/{relative}"
                )
            indexed_paths.add(relative.as_posix())
            target = (root / relative).resolve()
            target.relative_to(root)
            if not target.is_file():
                raise ValueError(
                    f"runtime skill manifest names a missing file: {skill_id}/{relative}"
                )
            observed = file_digest_summary(target)
            if (
                file_record.get("sha256") != observed["sha256"]
                or file_record.get("bytes") != observed["bytes"]
            ):
                raise ValueError(
                    f"runtime skill file hash mismatch: {skill_id}/{relative}"
                )
            indexed_files.append({"path": relative.as_posix(), **observed})
        actual_paths = {
            item.relative_to(root).as_posix()
            for item in root.rglob("*")
            if item.is_file()
        }
        if actual_paths != {record["path"] for record in indexed_files}:
            raise ValueError(f"runtime skill file index mismatch: {skill_id}")
        result[skill_id] = {
            "skill_file": record.get("skill_file"),
            "tree_sha256": observed_tree,
            "files": indexed_files,
        }
    return {
        "schema_version": "v4-runtime-skill-list-v1",
        "skills": result,
    }


def skill_tree_sha(root: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(root.rglob("*")):
        if item.is_file():
            digest.update(item.relative_to(root).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(item.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def active_tool_schemas(runtime: Path, mode: str) -> list[dict[str, Any]] | None:
    policy_path = runtime / "MODEL_ACCESS_POLICY.json"
    if not policy_path.is_file():
        raise ValueError("runtime model access policy is missing")
    policy = read_json(policy_path)
    if str(policy.get("mode") or "") != mode:
        raise ValueError("runtime model access policy mode mismatch")
    skill_tool_names = [tool["function"]["name"] for tool in SKILL_TOOLS]
    provider_tools = policy.get("provider_tools") or []
    if provider_tools not in ([], skill_tool_names):
        raise ValueError("runtime model access policy declares unsupported provider tools")
    manifest_path = runtime / "public" / "skills" / "SNAPSHOT_MANIFEST.json"
    has_skills = manifest_path.is_file()
    if bool(provider_tools) != has_skills:
        raise ValueError("runtime skill manifest and provider-tool policy disagree")
    if has_skills:
        listed_skills = set(list_available_skills(runtime).get("skills") or {})
        policy_skills = set((policy.get("available_skills") or {}).keys())
        if listed_skills != policy_skills:
            raise ValueError("runtime skill manifest and model access policy disagree")
    if mode in AGENTIC:
        return [*TOOLS, *SKILL_TOOLS] if has_skills else TOOLS
    submission_tool = submit_artifacts_tool_schema(runtime)
    if has_skills:
        return [*SKILL_TOOLS, submission_tool]
    return [submission_tool]


def read_skill_file(runtime: Path, skill_id: str, raw_path: str) -> str:
    manifest = list_available_skills(runtime)
    skill_record = (manifest.get("skills") or {}).get(skill_id)
    if not isinstance(skill_record, dict):
        raise ValueError(f"skill is not available in this mode: {skill_id}")
    relative = safe_relative(raw_path)
    if relative.suffix.lower() not in TEXT_SKILL_EXTENSIONS:
        raise ValueError(f"unsupported skill file type: {relative.suffix}")
    indexed_files = {
        str(record.get("path")): record
        for record in skill_record.get("files") or []
        if isinstance(record, dict)
    }
    if relative.as_posix() not in indexed_files:
        raise ValueError(f"skill file is unavailable: {skill_id}/{relative.as_posix()}")
    raw_root = runtime / "public" / "skills" / skill_id
    root = raw_root.resolve()
    unresolved = root / relative
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError(f"skill file is unavailable: {skill_id}/{relative.as_posix()}")
    target = unresolved.resolve()
    target.relative_to(root)
    if not target.is_file():
        raise ValueError(f"skill file is unavailable: {skill_id}/{relative.as_posix()}")
    summary = file_digest_summary(target)
    expected = indexed_files[relative.as_posix()]
    if summary != {"bytes": expected.get("bytes"), "sha256": expected.get("sha256")}:
        raise ValueError(f"skill file changed after manifest validation: {skill_id}/{relative}")
    if summary["bytes"] > MAX_SKILL_FILE_BYTES:
        raise ValueError(f"skill file exceeds delivery limit: {skill_id}/{relative}")
    delivered = read_tool_delivery_cache(runtime)
    cache_key = f"skills/{skill_id}/{relative.as_posix()}"
    if cache_key in delivered:
        write_skill_lookup_event(runtime, skill_id, relative.as_posix(), target, cached=True)
        return json.dumps({
            "status": "already_provided_in_this_episode",
            "path": cache_key,
            **summary,
        }, sort_keys=True)
    text = target.read_text(encoding="utf-8")
    delivered.add(cache_key)
    write_tool_delivery_cache(runtime, delivered)
    write_skill_lookup_event(runtime, skill_id, relative.as_posix(), target, cached=False)
    return text


def write_skill_lookup_event(
    runtime: Path, skill_id: str, relative: str, target: Path, *, cached: bool
) -> None:
    path = runtime / "evidence" / "skill_lookup_events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "schema_version": "v4-skill-lookup-event-v1",
        "skill": skill_id,
        "path": relative,
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "cached": cached,
        "timestamp": now(),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def read_skill_lookup_events(runtime: Path) -> list[dict[str, Any]]:
    path = runtime / "evidence" / "skill_lookup_events.jsonl"
    if not path.is_file():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def expected_candidate_artifacts(runtime: Path) -> list[str]:
    policy_path = runtime / "evaluator" / "score_policy.json"
    if not policy_path.is_file():
        return []
    policy = read_json(policy_path)
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


def validated_artifact_mapping(
    pairs: list[tuple[str, str]], expected: list[str]
) -> dict[str, str] | None:
    if not pairs or not expected:
        return None
    mapping: dict[str, str] = {}
    expected_set = set(expected)
    for raw, content in pairs:
        try:
            relative = safe_relative(raw).as_posix()
        except ValueError:
            return None
        if relative not in expected_set or relative in mapping:
            return None
        mapping[relative] = content
    return mapping if set(mapping) == expected_set else None


def last_complete_artifact_bundle(
    pairs: list[tuple[str, str]], expected: list[str]
) -> tuple[dict[str, str] | None, bool]:
    """Select the last complete ordered label bundle without reading semantics."""
    expected_set = set(expected)
    current: dict[str, str] = {}
    complete: dict[str, str] | None = None
    saw_restart = False
    for raw, content in pairs:
        try:
            relative = safe_relative(raw).as_posix()
        except ValueError:
            return None, saw_restart
        if relative not in expected_set or not content.strip():
            return None, saw_restart
        if relative in current:
            current = {}
            saw_restart = True
        current[relative] = content
        if set(current) == expected_set:
            if complete is not None:
                saw_restart = True
            complete = dict(current)
            current = {}
    return complete, saw_restart


def exact_envelope_mapping(
    text: str, expected: list[str]
) -> tuple[dict[str, str] | None, list[str]]:
    diagnostics: list[str] = []
    matches = list(ARTIFACT_RE.finditer(text))
    if not matches:
        return None, ["no_exact_artifact_blocks"]

    outside_parts: list[str] = []
    cursor = 0
    for match in matches:
        outside_parts.append(text[cursor:match.start()])
        cursor = match.end()
    outside_parts.append(text[cursor:])
    if any(part.strip() for part in outside_parts):
        diagnostics.append("non_whitespace_outside_artifact_blocks")

    observed: list[str] = []
    mapping: dict[str, str] = {}
    expected_set = set(expected)
    for match in matches:
        raw, content = match.group(1), match.group(2)
        try:
            relative = safe_relative(raw).as_posix()
        except ValueError:
            diagnostics.append(f"unsafe_artifact_path:{raw}")
            continue
        observed.append(relative)
        if raw != relative:
            diagnostics.append(f"noncanonical_artifact_path:{raw}")
        elif relative not in expected_set:
            diagnostics.append(f"undeclared_artifact_path:{relative}")
        elif relative in mapping:
            diagnostics.append(f"duplicate_artifact_path:{relative}")
        else:
            mapping[relative] = content
        if "<<<VABENCH_ARTIFACT" in content or "<<<END_VABENCH_ARTIFACT" in content:
            diagnostics.append(f"ambiguous_artifact_marker:{relative}")

    missing = [relative for relative in expected if relative not in mapping]
    diagnostics.extend(f"missing_artifact_path:{relative}" for relative in missing)
    if observed != expected:
        diagnostics.append("artifact_blocks_not_in_canonical_order")
    if diagnostics:
        return None, diagnostics
    return mapping, []


def artifact_label(line: str, expected: list[str]) -> str | None:
    matches: set[str] = set()
    for token in FILENAME_TOKEN_RE.findall(line):
        try:
            candidate = safe_relative(token).as_posix()
        except ValueError:
            continue
        for item in expected:
            if candidate == item or Path(candidate).name == Path(item).name:
                matches.add(item)
    return next(iter(matches)) if len(matches) == 1 else None


def leading_comment_label(content: str, expected: list[str]) -> tuple[str | None, bool]:
    labels: set[str] = set()
    for line in content.splitlines():
        if not line.strip():
            continue
        if not re.match(r"^\s*//", line):
            break
        label = artifact_label(line, expected)
        if label:
            labels.add(label)
    return (next(iter(labels)), False) if len(labels) == 1 else (None, len(labels) > 1)


def split_labeled_fenced_sections(
    content: str, expected: list[str]
) -> tuple[dict[str, str] | None, bool, bool]:
    lines = content.splitlines()
    labels: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        if not re.match(r"^\s*//", line):
            continue
        label = artifact_label(line, expected)
        if label:
            labels.append((index, label))
    if len(labels) < 2:
        return None, False, bool(labels)
    if any(line.strip() for line in lines[:labels[0][0]]):
        return None, False, True
    pairs: list[tuple[str, str]] = []
    for offset, (start, label) in enumerate(labels):
        stop = labels[offset + 1][0] if offset + 1 < len(labels) else len(lines)
        body = "\n".join(lines[start + 1:stop]).strip()
        if not body:
            return None, False, True
        pairs.append((label, body))
    mapping, restarted = last_complete_artifact_bundle(pairs, expected)
    return mapping, restarted, True


def labeled_fenced_mapping(text: str, expected: list[str]) -> tuple[dict[str, str] | None, str]:
    blocks = list(FENCED_BLOCK_RE.finditer(text))
    if len(blocks) == 1:
        sections, restarted, saw_sections = split_labeled_fenced_sections(
            blocks[0].group(1), expected
        )
        if sections is not None:
            protocol = "last_complete_labeled_bundle" if restarted else "labeled_sections_in_fenced_block"
            return sections, protocol
        if saw_sections:
            return None, "incomplete_labeled_bundle"

    pairs: list[tuple[str, str]] = []
    previous_end = 0
    for block in blocks:
        content = block.group(1)
        prefix_lines = [line for line in text[previous_end:block.start()].splitlines() if line.strip()]
        prefix_label = artifact_label(prefix_lines[-1], expected) if prefix_lines else None
        inline_label, inline_ambiguous = leading_comment_label(content, expected)
        if inline_ambiguous:
            return None, "ambiguous_labeled_artifacts"
        labels = {label for label in (prefix_label, inline_label) if label}
        if len(labels) != 1:
            return None, "ambiguous_labeled_artifacts" if labels else "unparsed"
        label = next(iter(labels))
        if not content.strip():
            return None, "unparsed"
        pairs.append((label, content))
        previous_end = block.end()
    mapping, restarted = last_complete_artifact_bundle(pairs, expected)
    if mapping is not None:
        protocol = "last_complete_labeled_bundle" if restarted else "labeled_fenced_blocks"
        return mapping, protocol
    return None, "incomplete_labeled_bundle" if pairs else "unparsed"


def write_artifact_mapping(mapping: dict[str, str], runtime: Path) -> list[str]:
    submission = runtime / "public" / "submission"
    saved: list[str] = []
    for relative in sorted(mapping):
        path = submission / relative
        path.resolve().relative_to(submission.resolve())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(mapping[relative], encoding="utf-8")
        saved.append(relative)
    return saved


def parse_direct_artifacts_detailed(
    text: str, runtime: Path
) -> tuple[dict[str, str] | None, str, list[str]]:
    expected = expected_candidate_artifacts(runtime)
    if not expected:
        return None, "invalid_exact_artifact_envelope", ["missing_candidate_artifact_contract"]

    mapping, diagnostics = exact_envelope_mapping(text, expected)
    if mapping is None:
        return None, "invalid_exact_artifact_envelope", diagnostics
    return mapping, "exact_artifact_envelope", []


def parse_direct_artifacts(text: str, runtime: Path) -> tuple[dict[str, str] | None, str]:
    mapping, protocol, _diagnostics = parse_direct_artifacts_detailed(text, runtime)
    return mapping, protocol


def parse_recoverable_direct_artifacts(
    text: str, runtime: Path
) -> tuple[dict[str, str] | None, str]:
    """Classify deterministic historical recoveries without changing live scoring."""
    expected = expected_candidate_artifacts(runtime)
    if not expected:
        return None, "missing_candidate_artifact_contract"

    mapping, protocol = parse_direct_artifacts(text, runtime)
    if mapping is None:
        exact_pairs = ARTIFACT_RE.findall(text)
        mapping, restarted = last_complete_artifact_bundle(exact_pairs, expected)
        if mapping is not None:
            protocol = "last_complete_labeled_bundle" if restarted else "noncanonical_artifact_envelope"
    if mapping is None:
        mapping, restarted = last_complete_artifact_bundle(
            RELAXED_ARTIFACT_RE.findall(text), expected
        )
        if mapping is not None:
            protocol = "last_complete_labeled_bundle" if restarted else "normalized_artifact_envelope"
    if mapping is None and len(expected) == 1:
        mapping, restarted = last_complete_artifact_bundle(
            FILENAME_ARTIFACT_RE.findall(text), expected
        )
        if mapping is not None:
            protocol = "last_complete_labeled_bundle" if restarted else "normalized_filename_artifact_envelope"
    if mapping is None and len(expected) == 1:
        mapping, restarted = last_complete_artifact_bundle(
            INPUT_ARTIFACT_RE.findall(text), expected
        )
        if mapping is not None:
            protocol = "last_complete_labeled_bundle" if restarted else "normalized_input_artifact_envelope"
    if mapping is None:
        mapping, protocol = labeled_fenced_mapping(text, expected)
    if mapping is None:
        blocks = FENCED_BLOCK_RE.findall(text)
        if len(expected) == 1 and len(blocks) == 1:
            mapping = {expected[0]: blocks[0]}
            protocol = "single_artifact_fenced_block"
    if mapping is None:
        return None, protocol
    return mapping, protocol


def extract_direct_with_protocol(text: str, runtime: Path) -> tuple[list[str], str]:
    mapping, protocol, _diagnostics = parse_direct_artifacts_detailed(text, runtime)
    if mapping is None:
        return [], protocol
    return write_artifact_mapping(mapping, runtime), protocol


def extract_recoverable_direct_with_protocol(
    text: str, runtime: Path
) -> tuple[list[str], str]:
    mapping, protocol = parse_recoverable_direct_artifacts(text, runtime)
    if mapping is None:
        return [], protocol
    return write_artifact_mapping(mapping, runtime), protocol


def direct_protocol_compliant(protocol: str) -> bool:
    return protocol == "exact_artifact_envelope"


def extract_direct(text: str, runtime: Path) -> list[str]:
    return extract_direct_with_protocol(text, runtime)[0]


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


def submission_complete(runtime: Path) -> bool:
    return bool(submission_artifact_gate(runtime)["passed"])


def extract_direct_submission(text: str, runtime: Path) -> dict[str, Any]:
    mapping, protocol, diagnostics = parse_direct_artifacts_detailed(text, runtime)
    saved = write_artifact_mapping(mapping, runtime) if mapping is not None else []
    gate = submission_artifact_gate(runtime) if mapping is not None else None
    compliant = bool(mapping is not None and gate and gate["passed"])
    return {
        "saved_files": saved,
        "extraction_protocol": protocol,
        "submission_protocol_compliant": compliant,
        "response_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "response_parser_version": DIRECT_PARSER_VERSION,
        "parse_diagnostics": diagnostics,
        "artifact_gate": gate,
        "artifact_sha256": dict((gate or {}).get("artifact_sha256") or {}),
    }


def extract_normalized_direct_submission(text: str, runtime: Path) -> dict[str, Any]:
    strict_mapping, strict_protocol, strict_diagnostics = (
        parse_direct_artifacts_detailed(text, runtime)
    )
    mapping = strict_mapping
    protocol = strict_protocol
    normalized = False
    if mapping is None:
        mapping, protocol = parse_recoverable_direct_artifacts(text, runtime)
        normalized = mapping is not None
    saved = write_artifact_mapping(mapping, runtime) if mapping is not None else []
    gate = submission_artifact_gate(runtime) if mapping is not None else None
    compliant = bool(mapping is not None and gate and gate["passed"])
    return {
        "saved_files": saved,
        "extraction_protocol": protocol,
        "submission_protocol_compliant": compliant,
        "original_protocol_compliant": strict_mapping is not None,
        "submission_transport": (
            "runner_normalized_text" if normalized else "model_text"
        ),
        "response_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "response_parser_version": DIRECT_PARSER_VERSION,
        "parse_diagnostics": [] if compliant else strict_diagnostics,
        "strict_parse_diagnostics": strict_diagnostics,
        "artifact_gate": gate,
        "artifact_sha256": dict((gate or {}).get("artifact_sha256") or {}),
    }


def gate_agentic_submission(runtime: Path, result: dict[str, Any]) -> bool:
    gate = submission_artifact_gate(runtime)
    result["artifact_gate"] = gate
    result["artifact_sha256"] = gate["artifact_sha256"]
    result["submission_protocol_compliant"] = bool(gate["passed"])
    return bool(gate["passed"])


def export_runtime(cell: dict[str, Any], release: Path, output: Path, *, timeout_s: int) -> None:
    command = [
        sys.executable, str(EXPORTER), "--release", str(release), "--task", cell["task_id"],
        "--mode", cell["mode"], "--output", str(output), "--per-turn-max-tokens",
        str(cell_per_turn_max_tokens(cell)), "--force",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=REPO,
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_s,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeExportError(f"runtime exporter could not complete: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip()[-2000:] or completed.stdout.strip()[-2000:]
        raise RuntimeExportError(
            f"runtime exporter exited with status {completed.returncode}: {detail}"
        )
    apply_experimental_arm_overlay(cell, output)


def apply_experimental_arm_overlay(cell: dict[str, Any], runtime: Path) -> None:
    arm = cell.get("experimental_arm")
    if arm is None:
        return
    policy_path = runtime / "MODEL_ACCESS_POLICY.json"
    policy = read_json(policy_path)
    policy["experimental_arm"] = arm
    policy["executable_feedback"] = bool(cell.get("executable_feedback"))
    policy["transport_tools"] = ["submit_artifacts"] if arm == "OneShot" else []
    if not cell.get("executable_feedback"):
        policy["executables"] = [
            executable
            for executable in policy.get("executables") or []
            if executable != "evas"
        ]
    write_json(policy_path, policy)

    prompt_path = runtime / (
        "agent_prompt.txt" if cell["process"] == "agentic" else "direct_prompt.txt"
    )
    if arm == "Agent-No-EVAS":
        (runtime / "public" / "task" / "evas_runtime.json").unlink(missing_ok=True)
        prompt = prompt_path.read_text(encoding="utf-8")
        start = prompt.find(AGENTIC_COMPONENT_START)
        end = prompt.find(AGENTIC_COMPONENT_END, start)
        if start < 0 or end < 0:
            raise RuntimeExportError(
                "Agent-No-EVAS runtime is missing its agentic wrapper"
            )
        replacement = (
            f"{AGENTIC_COMPONENT_START}\n\n{NO_EVAS_AGENTIC_WRAPPER.rstrip()}\n\n"
            f"{AGENTIC_COMPONENT_END}"
        )
        prompt_path.write_text(
            prompt[:start] + replacement + prompt[end + len(AGENTIC_COMPONENT_END):],
            encoding="utf-8",
        )

    effective_prompt = prompt_path.read_text(encoding="utf-8")
    write_json(
        runtime / "evidence" / "experimental_arm.json",
        {
            "schema_version": "v4-experimental-arm-v1",
            "experimental_arm": arm,
            "base_mode": cell["mode"],
            "process": cell["process"],
            "executable_feedback": bool(cell.get("executable_feedback")),
            "base_prompt_record_sha256": cell["prompt_record_sha256"],
            "effective_prompt_sha256": hashlib.sha256(
                effective_prompt.encode("utf-8")
            ).hexdigest(),
        },
    )


def run_mini_swe_agentic_cell(
    *,
    cell: dict[str, Any],
    args: argparse.Namespace,
    client: OpenAICompatible,
    runtime: Path,
    prompt: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    trajectory_path = runtime / "evidence" / "mini_swe_trajectory.json"
    if args.resume and trajectory_path.is_file():
        raise ValueError(
            "resuming an unfinished mini-SWE-agent trajectory is not supported; "
            "reuse only terminal campaign results"
        )

    def trajectory_messages() -> list[dict[str, Any]]:
        trajectory = read_json(trajectory_path) if trajectory_path.is_file() else {}
        return list(trajectory.get("messages") or [])

    started = time.monotonic()
    try:
        executable_feedback = bool(cell.get("executable_feedback", True))
        docker_image = (
            getattr(args, "mini_swe_image", DEFAULT_DOCKER_IMAGE)
            if executable_feedback
            else getattr(
                args,
                "mini_swe_no_evas_image",
                DEFAULT_NO_EVAS_DOCKER_IMAGE,
            )
        )
        episode = run_mini_swe_episode(
            runtime=runtime,
            prompt=prompt,
            client=client,
            per_turn_max_tokens=cell_per_turn_max_tokens(cell),
            agent_timeout_s=float(args.agent_timeout_s),
            request_timeout_s=float(args.request_timeout_s),
            tool_timeout_s=float(args.tool_timeout_s),
            sandbox_backend=args.mini_swe_sandbox,
            evas_command=args.evas_command,
            executable_feedback=executable_feedback,
            docker_command=getattr(args, "docker_command", "docker"),
            docker_image=docker_image,
            preflight_timeout_s=float(
                getattr(
                    args,
                    "mini_swe_preflight_timeout_s",
                    DEFAULT_MINI_SWE_PREFLIGHT_TIMEOUT_S,
                )
            ),
            preflight_attempts=int(
                getattr(
                    args,
                    "mini_swe_preflight_attempts",
                    DEFAULT_MINI_SWE_PREFLIGHT_ATTEMPTS,
                )
            ),
            startup_limiter=getattr(args, "_mini_swe_startup_limiter", None),
            candidate_artifacts=expected_candidate_artifacts(runtime),
            submission_gate=submission_artifact_gate,
            usage_parser=provider_output_usage,
            response_metadata=provider_response_metadata,
            trajectory_path=trajectory_path,
        )
    except ProviderContextWindowExceeded as exc:
        result.update(
            {
                "status": "context_window_exceeded",
                "termination_reason": "provider_context_window_exceeded",
                "provider_error": str(exc)[:4000],
                "incidents": [
                    {
                        "category": "provider_context_window_exceeded",
                        "component": "provider",
                        "error_type": type(exc).__name__,
                        "phase": "model",
                        "responsibility": "experiment_configuration",
                        "retryable": False,
                    }
                ],
                "finished_at": now(),
                "agent_elapsed_s": time.monotonic() - started,
            }
        )
        attach_experiment_result(
            result, runtime, trajectory_messages(), args, "provider_failure"
        )
        write_json(runtime / "evidence" / "campaign_result.json", result)
        return result
    except (subprocess.TimeoutExpired, ProviderRequestTimeout) as exc:
        elapsed_s = time.monotonic() - started
        if elapsed_s < float(args.agent_timeout_s):
            raise
        result.update(
            {
                "status": "agent_timeout",
                "termination_reason": "agent_timeout",
                "provider_error": str(exc)[:4000],
                "incidents": [
                    {
                        "category": "agent_walltime_exhausted",
                        "component": "mini_swe_agent",
                        "error_type": type(exc).__name__,
                        "phase": "agent",
                        "responsibility": "experiment_limit",
                        "retryable": True,
                    }
                ],
                "finished_at": now(),
                "agent_elapsed_s": elapsed_s,
            }
        )
        attach_experiment_result(
            result, runtime, trajectory_messages(), args, "agent_timeout"
        )
        write_json(runtime / "evidence" / "campaign_result.json", result)
        return result

    complete = bool(episode["artifact_complete"])
    explicit_submission = bool(episode["submitted"])
    exit_status = str(episode.get("exit_status") or "")
    evas_invocations = list(episode.get("evas_invocations") or [])
    commands = list(episode.get("commands") or [])
    incidents = evas_invocation_incidents(evas_invocations)
    resource_exhausted = any(
        (command.get("resources") or {}).get("exceeded") for command in commands
    )
    if resource_exhausted:
        incidents.append(
            {
                "category": "agent_resource_exhausted",
                "component": "mini_swe_agent",
                "phase": "tool",
                "responsibility": "model",
                "retryable": False,
            }
        )
    if exit_status == "TimeExceeded":
        incidents.append(
            {
                "category": "agent_walltime_exhausted",
                "component": "mini_swe_agent",
                "phase": "agent",
                "responsibility": "experiment_limit",
                "retryable": True,
            }
        )
    if not complete and exit_status != "TimeExceeded":
        incidents.append(
            {
                "category": "artifact_submission_failure",
                "component": "submission",
                "phase": "artifact",
                "responsibility": "model",
                "retryable": False,
            }
        )
    result.update(
        {
            "status": (
                "agent_resource_exhausted"
                if resource_exhausted
                else "submitted"
                if complete and explicit_submission
                else "workspace_ready"
                if complete
                else "agent_timeout"
                if exit_status == "TimeExceeded"
                else "invalid_submission"
            ),
            "termination_reason": (
                "agent_resource_exhausted"
                if resource_exhausted
                else "agent_timeout"
                if exit_status == "TimeExceeded"
                else "completed"
                if explicit_submission
                else "mini_swe_agent_exit"
            ),
            "finished_at": now(),
            "termination_policy": "wall_time",
            "output_tokens": episode["output_tokens"],
            "working_tokens": episode["output_tokens"],
            "output_token_budget": None,
            "per_turn_max_tokens": cell_per_turn_max_tokens(cell),
            "events": episode["events"],
            "agent_elapsed_s": episode["agent_elapsed_s"],
            "artifact_gate": episode["artifact_gate"],
            "artifact_sha256": episode["artifact_sha256"],
            "submission_protocol_compliant": explicit_submission,
            "submission_mode": (
                "explicit"
                if explicit_submission
                else "workspace_at_deadline"
                if complete and exit_status == "TimeExceeded"
                else "workspace_at_termination"
                if complete
                else "unavailable"
            ),
            "agent_scaffold": {
                key: episode.get(key)
                for key in (
                    "scaffold",
                    "scaffold_version",
                    "bash_tool_schema_sha256",
                    "system_prompt_sha256",
                    "bash_contract_sha256",
                    "trajectory_format",
                    "sandbox_backend",
                    "docker_image",
                    "docker_image_id",
                    "network",
                    "evaluator_mounted",
                    "executable_feedback",
                    "preflight_timeout_s",
                    "preflight_attempts",
                    "preflight_attempts_used",
                    "resource_limits",
                )
            },
            "public_agent_environment": {
                "backend": episode["sandbox_backend"],
                "image": episode.get("docker_image"),
                "image_id": episode.get("docker_image_id"),
                "executable_feedback": executable_feedback,
            },
            "mini_swe_exit_status": exit_status,
            "model_calls": episode["model_calls"],
            "bash_commands": commands,
            "available_skills": episode.get("available_skills") or {},
            "skill_command_events": episode.get("skill_command_events") or [],
            "evas_invocations": evas_invocations,
            "evas_usage": summarize_evas_invocations(evas_invocations),
            "incidents": incidents,
        }
    )
    attach_experiment_result(
        result,
        runtime,
        episode["messages"],
        args,
        "agent_resource_exhausted"
        if resource_exhausted
        else "agent_timeout"
        if exit_status == "TimeExceeded"
        else "completed"
        if complete
        else result["status"],
    )
    write_json(runtime / "evidence" / "campaign_result.json", result)
    return result


def run_cell(cell: dict[str, Any], args: argparse.Namespace, client: OpenAICompatible | None) -> dict[str, Any]:
    runtime = args.output / cell["cell_id"]
    assert_final_replay_not_started(runtime)
    for name in ("native-episode", "native-launcher"):
        native_reservation = runtime / "evidence" / name
        if native_reservation.exists() or native_reservation.is_symlink():
            raise FinalReplayReservedError("native episode already reserved; legacy model reentry is forbidden")
    result_path = runtime / "evidence" / "campaign_result.json"
    if getattr(args, "episode_backend", "legacy") == "native-mini-swe":
        if runtime.exists() or runtime.is_symlink():
            raise FinalReplayReservedError("native cell requires a fresh runtime; reentry forbidden")
        if getattr(args, "resume", False):
            raise ValueError("native-mini-swe campaign cells cannot be resumed in place")
        validate_native_mini_swe_cell(cell)
    if args.resume and result_path.is_file():
        previous = read_json(result_path)
        if previous.get("status") in RESUMABLE_TERMINAL_STATUSES:
            previous_cell = previous.get("cell") or {}
            if previous_cell.get("cell_id") != cell.get("cell_id"):
                raise ValueError("resumed campaign result cell_id does not match the requested cell")
            if previous.get("status") in ARTIFACT_READY_STATUSES:
                gate = submission_artifact_gate(runtime)
                if not gate["passed"]:
                    raise ValueError(
                        "resumed artifact-ready result no longer passes its artifact gate: "
                        + ", ".join(gate["diagnostics"])
                    )
                recorded_hashes = dict(previous.get("artifact_sha256") or {})
                if recorded_hashes and recorded_hashes != gate["artifact_sha256"]:
                    raise ValueError("resumed submission artifact hash does not match its result")
            if "experiment_result" not in previous:
                checkpoint_path = runtime / "evidence" / "conversation_checkpoint.json"
                checkpoint = read_json(checkpoint_path) if checkpoint_path.is_file() else {}
                attach_experiment_result(
                    previous, runtime, list(checkpoint.get("messages") or []), args, "completed"
                )
                write_json(result_path, previous)
            return previous
    conversation_path = runtime / "evidence" / "conversation_checkpoint.json"
    if not (args.resume and conversation_path.is_file()):
        export_runtime(cell, args.release, runtime, timeout_s=args.setup_timeout_s)
    if getattr(args, "episode_backend", "legacy") == "native-mini-swe":
        if args.dry_run:
            result = {
                "cell": cell,
                "started_at": now(),
                "runtime": str(runtime),
                "status": "prepared",
                "termination_policy": "wall_time",
                "agent_timeout_s": args.agent_timeout_s,
                "backend": "native-mini-swe",
                "finished_at": now(),
            }
            return result
        assert client is not None
        attempt_context = getattr(args, "_native_attempt_context", None)
        attempt_id = (attempt_context.attempt_id if attempt_context is not None
                      else f"{cell['cell_id']}-attempt-0001")
        run = run_prepared_native_mini_swe(
            runtime=runtime,
            cell=cell,
            client=client,
            attempt_id=attempt_id,
            evas_command=args.evas_command,
            release=args.release,
            final_judge_command=getattr(args, "final_judge_command", None),
            request_timeout_s=args.request_timeout_s,
            tool_timeout_s=args.tool_timeout_s,
            judge_timeout_s=args.judge_timeout_s,
            docker_image=(
                None
                if cell.get("experimental_arm") == "OneShot"
                else getattr(args, "mini_swe_image", DEFAULT_DOCKER_IMAGE)
                if bool(cell.get("executable_feedback", True))
                else getattr(
                    args,
                    "mini_swe_no_evas_image",
                    DEFAULT_NO_EVAS_DOCKER_IMAGE,
                )
            ),
            allow_insecure_test_sandbox=bool(
                getattr(args, "allow_insecure_test_sandbox", False)
                or getattr(args, "mini_swe_sandbox", None) == "none"
            ),
            campaign_file_sha256=getattr(args, "campaign_file_sha256", None),
            episode_context=attempt_context,
        )
        result = {
            "cell": cell,
            "started_at": now(),
            "runtime": str(runtime),
            "status": run.result.primary_outcome,
            "termination_reason": run.result.terminal_reason,
            "termination_policy": "wall_time",
            "agent_timeout_s": args.agent_timeout_s,
            "backend": "native-mini-swe",
            "artifact_path": (
                str(run.artifact_path.relative_to(runtime))
                if run.artifact_path is not None
                else None
            ),
            "score_sidecar_receipt": run.score_sidecar_receipt,
            "finished_at": now(),
        }
        write_native_dispatch_result(
            runtime,
            {
                **result,
                "attempt_id": attempt_id,
                "campaign_file_sha256": getattr(args, "campaign_file_sha256", None),
            },
        )
        return result
    prompt_path = runtime / ("agent_prompt.txt" if cell["mode"] in AGENTIC else "direct_prompt.txt")
    prompt = prompt_path.read_text(encoding="utf-8")
    agent_scaffold = getattr(args, "agent_scaffold", "native")
    mini_swe_agentic = cell["mode"] in AGENTIC and agent_scaffold == "mini-swe"
    agent_started_monotonic = time.monotonic()
    resumed_agent_elapsed_s = 0.0
    result: dict[str, Any] = {
        "cell": cell,
        "started_at": now(),
        "runtime": str(runtime),
        "status": "prepared",
        "termination_policy": "wall_time",
        "agent_timeout_s": args.agent_timeout_s,
        "agent_scaffold": MINI_SWE_SCAFFOLD_ID if mini_swe_agentic else "native-v4-loop",
        "evas_identity": getattr(args, "evas_identity", None),
        "available_skills": list_available_skills(runtime).get("skills") or {},
    }
    if mini_swe_agentic:
        executable_feedback = bool(cell.get("executable_feedback", True))
        result["public_agent_environment"] = {
            "backend": getattr(args, "mini_swe_sandbox", None),
            "image": (
                getattr(args, "mini_swe_image", DEFAULT_DOCKER_IMAGE)
                if executable_feedback
                else getattr(
                    args,
                    "mini_swe_no_evas_image",
                    DEFAULT_NO_EVAS_DOCKER_IMAGE,
                )
            ),
            "image_id": None,
            "executable_feedback": executable_feedback,
        }
    if args.dry_run:
        result["finished_at"] = now()
        write_json(runtime / "evidence" / "campaign_result.json", result)
        return result
    assert client is not None
    if mini_swe_agentic:
        return run_mini_swe_agentic_cell(
            cell=cell,
            args=args,
            client=client,
            runtime=runtime,
            prompt=prompt,
            result=result,
        )
    if args.resume and conversation_path.is_file():
        checkpoint = read_json(conversation_path)
        if checkpoint.get("cell_id") != cell["cell_id"]:
            raise ValueError("conversation checkpoint cell_id does not match the campaign cell")
        result["started_at"] = str(checkpoint.get("started_at") or result["started_at"])
        messages = list(checkpoint["messages"])
        output_tokens = int(checkpoint.get("output_tokens", checkpoint.get("working_tokens", 0)))
        events = list(checkpoint["events"])
        finalized = bool(checkpoint.get("finalized"))
        resumed_agent_elapsed_s = float(checkpoint.get("agent_elapsed_s") or 0.0)
    else:
        messages = []
        if cell.get("process") == "direct_one_shot":
            messages.append(
                {"role": "system", "content": ONESHOT_TRANSPORT_INSTRUCTION}
            )
        messages.append({"role": "user", "content": prompt})
        output_tokens = 0
        events = []
        finalized = False

    per_turn_max_tokens = cell_per_turn_max_tokens(cell)
    tools_for_cell = active_tool_schemas(runtime, str(cell["mode"]))
    agent_deadline = agent_started_monotonic + max(0.0, args.agent_timeout_s - resumed_agent_elapsed_s)
    submission_tool_normalized = any(
        event.get("name") == "submit_artifacts"
        and event.get("argument_protocol_compliant") is False
        for event in events
    )
    submission_transport_failures = sum(
        event.get("name") == "submit_artifacts"
        and event.get("transport_error") is True
        for event in events
    )
    submission_transport_failures_this_run = 0
    invalid_submit_bundle = False

    def current_agent_elapsed_s() -> float:
        return resumed_agent_elapsed_s + max(0.0, time.monotonic() - agent_started_monotonic)

    def remaining_agent_s() -> float:
        return max(0.0, agent_deadline - time.monotonic())

    def agent_time_expired() -> bool:
        return time.monotonic() >= agent_deadline

    def save_conversation() -> None:
        write_json(conversation_path, {
            "schema_version": "v4-calibration-conversation-checkpoint-v1",
            "cell_id": cell["cell_id"], "messages": messages,
            "started_at": result["started_at"],
            "output_tokens": output_tokens, "working_tokens": output_tokens, "events": events,
            "finalized": finalized,
            "termination_policy": "wall_time",
            "agent_timeout_s": args.agent_timeout_s,
            "agent_elapsed_s": current_agent_elapsed_s(),
            "per_turn_max_tokens": per_turn_max_tokens,
            "updated_at": now(),
        })

    def current_turn_hit_limit() -> bool:
        last_model = next(
            (event for event in reversed(events) if event.get("type") == "model"),
            {},
        )
        return model_event_hit_limit(last_model)

    def process_tool_calls(calls: list[dict[str, Any]]) -> None:
        nonlocal finalized, invalid_submit_bundle
        nonlocal submission_tool_normalized, submission_transport_failures
        nonlocal submission_transport_failures_this_run
        if (
            cell.get("process") == "direct_one_shot"
            and any(call.get("function", {}).get("name") == "submit_artifacts" for call in calls)
            and (
                len(calls) != 1
                or calls[0].get("function", {}).get("name") != "submit_artifacts"
            )
        ):
            invalid_submit_bundle = True
            events.append({
                "type": "tool",
                "name": "submit_artifacts",
                "reference_tokens": 0,
                "argument_protocol_compliant": False,
                "error": "submit_artifacts must be the only tool call",
            })
            save_conversation()
            return
        for call in calls:
            remaining = remaining_agent_s()
            if remaining <= 0:
                return
            function = call["function"]
            arguments: dict[str, Any] = {}
            argument_protocol_compliant = True
            argument_normalization: str | None = None
            transport_error = False
            decoding_arguments = True
            tool_error_type: str | None = None
            try:
                (
                    arguments,
                    argument_protocol_compliant,
                    argument_normalization,
                ) = decode_tool_arguments(
                    str(function.get("name") or ""),
                    function.get("arguments"),
                )
                if function.get("name") == "submit_artifacts":
                    submission_tool_normalized = (
                        submission_tool_normalized
                        or not argument_protocol_compliant
                    )
                decoding_arguments = False
                text, done = execute_tool(
                    function["name"],
                    arguments,
                    runtime,
                    max(0.1, min(float(args.tool_timeout_s), remaining)),
                    args.evas_command,
                )
            except Exception as exc:  # Model tool mistakes are episode evidence, not runner failures.
                tool_error_type = type(exc).__name__
                if (
                    function.get("name") == "submit_artifacts"
                    and decoding_arguments
                ):
                    argument_protocol_compliant = False
                    transport_error = True
                    submission_transport_failures += 1
                    submission_transport_failures_this_run += 1
                text = json.dumps({
                    "status": "tool_error",
                    "tool": function.get("name"),
                    "error_type": tool_error_type,
                    "error": str(exc)[:2000],
                })
                done = False
            delivered = reference_tokens(text)
            tool_event = {
                "type": "tool",
                "name": function["name"],
                "reference_tokens": delivered,
                "argument_protocol_compliant": argument_protocol_compliant,
            }
            if function["name"] == "submit_artifacts":
                raw_arguments = str(function.get("arguments") or "")
                tool_event["argument_sha256"] = hashlib.sha256(
                    raw_arguments.encode("utf-8")
                ).hexdigest()
                tool_event["transport_error"] = transport_error
                if tool_error_type is not None:
                    tool_event["error_type"] = tool_error_type
            if argument_normalization is not None:
                tool_event["argument_normalization"] = argument_normalization
            if function["name"] == "read_skill":
                tool_event.update({
                    "skill": str(arguments.get("skill") or ""),
                    "path": str(arguments.get("path") or ""),
                })
            events.append(tool_event)
            write_json(runtime / "evidence" / "campaign_checkpoint.json", {
                "cell_id": cell["cell_id"], "output_tokens": output_tokens,
                "working_tokens": output_tokens,
                "termination_policy": "wall_time",
                "per_turn_max_tokens": per_turn_max_tokens,
                "agent_elapsed_s": current_agent_elapsed_s(),
                "event_count": len(events), "events": events, "updated_at": now(),
            })
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": text})
            finalized = finalized or done
            save_conversation()

    def record_direct_tool_submission() -> None:
        gate = submission_artifact_gate(runtime)
        result.update({
            "status": "submitted" if gate["passed"] else "invalid_submission",
            "termination_reason": (
                "completed" if gate["passed"] else "invalid_submit_artifacts_call"
            ),
            "saved_files": list(gate["observed_artifacts"]) if gate["passed"] else [],
            "artifact_gate": gate,
            "artifact_sha256": dict(gate.get("artifact_sha256") or {}),
            "extraction_protocol": "submit_artifacts_tool-v1",
            "submission_transport": (
                "runner_normalized_tool"
                if submission_tool_normalized
                else "runner_managed"
            ),
            "original_protocol_compliant": not submission_tool_normalized,
            "submission_protocol_compliant": bool(gate["passed"]),
            "transport_retry_count": submission_transport_failures,
            "response_parser_version": None,
            "parse_diagnostics": (
                [] if gate["passed"] else ["invalid_submit_artifacts_call"]
            ),
        })

    def record_submission_transport_failure() -> None:
        result.update({
            "status": "provider_transport_failure",
            "termination_reason": "malformed_submit_artifacts_transport",
            "submission_protocol_compliant": False,
            "parse_diagnostics": ["malformed_submit_artifacts_transport"],
            "transport_failure_count": submission_transport_failures,
            "transport_failure_count_this_run": (
                submission_transport_failures_this_run
            ),
            "incidents": [{
                "category": "malformed_submit_artifacts_transport",
                "component": "provider",
                "phase": "submission_transport",
                "responsibility": "infrastructure",
                "retryable": True,
            }],
        })

    def model_limit_reason() -> str | None:
        return "model_output_limit" if current_turn_hit_limit() else None

    def set_terminal_submission_status(
        complete: bool,
        *,
        default_reason: str,
        incomplete_status: str = "invalid_submission",
        force_reason: str | None = None,
    ) -> None:
        reason = force_reason or model_limit_reason() or default_reason
        result["status"] = "submitted" if complete else incomplete_status
        result["termination_reason"] = reason if (complete or reason != "completed") else "completed"

    if cell["mode"] not in AGENTIC and len(messages) > 1 and args.resume:
        pending = pending_tool_calls(messages)
        if pending:
            process_tool_calls(pending)
            save_conversation()
            if invalid_submit_bundle:
                result.update({
                    "status": "invalid_submission",
                    "termination_reason": "invalid_submit_artifacts_call",
                    "submission_protocol_compliant": False,
                    "parse_diagnostics": ["mixed_submit_artifacts_tool_bundle"],
                })
            elif submission_transport_failures >= MAX_ONESHOT_TRANSPORT_FAILURES:
                record_submission_transport_failure()
            elif finalized:
                record_direct_tool_submission()
            if (
                invalid_submit_bundle
                or finalized
                or result.get("status") == "provider_transport_failure"
            ):
                result.update({
                    "finished_at": now(),
                    "output_tokens": output_tokens,
                    "working_tokens": output_tokens,
                    "output_token_budget": None,
                    "per_turn_max_tokens": per_turn_max_tokens,
                    "agent_elapsed_s": current_agent_elapsed_s(),
                    "events": events,
                    "recovered_from_checkpoint": True,
                })
                attach_experiment_result(
                    result,
                    runtime,
                    messages,
                    args,
                    (
                        "provider_failure"
                        if result.get("status") == "provider_transport_failure"
                        else "completed"
                    ),
                )
                write_json(runtime / "evidence" / "campaign_result.json", result)
                return result
        elif messages[-1].get("role") == "assistant":
            content = str(messages[-1].get("content") or "")
            direct_submission = extract_normalized_direct_submission(content, runtime)
            complete = bool(direct_submission["submission_protocol_compliant"])
            set_terminal_submission_status(complete, default_reason="completed")
            result.update({
                "finished_at": now(),
                "output_tokens": output_tokens,
                "working_tokens": output_tokens,
                "output_token_budget": None,
                "per_turn_max_tokens": per_turn_max_tokens,
                "agent_elapsed_s": current_agent_elapsed_s(),
                "events": events,
                "recovered_from_checkpoint": True,
                **direct_submission,
            })
            attach_experiment_result(result, runtime, messages, args, "completed")
            write_json(runtime / "evidence" / "campaign_result.json", result)
            return result
    if cell["mode"] in AGENTIC and args.resume:
        pending = pending_tool_calls(messages)
        if pending:
            process_tool_calls(pending)
        elif messages and messages[-1].get("role") == "assistant":
            complete = gate_agentic_submission(runtime, result)
            set_terminal_submission_status(complete, default_reason="completed")
        if finalized:
            complete = gate_agentic_submission(runtime, result)
            set_terminal_submission_status(complete, default_reason="completed")
    while not agent_time_expired() and not finalized and result.get("status") == "prepared":
        started = time.monotonic()
        try:
            response = client.complete(
                messages,
                per_turn_max_tokens,
                tools_for_cell,
                timeout_s=max(0.1, min(float(args.request_timeout_s), remaining_agent_s())),
            )
        except ProviderContextWindowExceeded as exc:
            result.update({
                "status": "context_window_exceeded",
                "termination_reason": "provider_context_window_exceeded",
                "provider_error": str(exc)[:4000],
            })
            break
        except (subprocess.TimeoutExpired, ProviderRequestTimeout) as exc:
            if agent_time_expired():
                complete = gate_agentic_submission(runtime, result) if cell["mode"] in AGENTIC else False
                set_terminal_submission_status(
                    complete,
                    default_reason="agent_timeout",
                    incomplete_status="agent_timeout",
                    force_reason="agent_timeout",
                )
                result["provider_error"] = str(exc)[:4000]
                break
            raise
        response_choice = response["choices"][0]
        choice = response_choice["message"]
        elapsed = time.monotonic() - started
        content = str(choice.get("content") or "")
        reasoning_content = str(choice.get("reasoning_content") or "")
        response_tool_calls = choice.get("tool_calls") or []
        tool_text = json.dumps(response_tool_calls, sort_keys=True) if response_tool_calls else ""
        usage = provider_output_usage(
            response.get("usage"),
            content,
            reasoning_text=reasoning_content,
            tool_text=tool_text,
        )
        output_tokens += int(usage["output_tokens"])
        model_event = {
            "type": "model",
            "elapsed_s": elapsed,
            "requested_max_tokens": per_turn_max_tokens,
            "finish_reason": response_choice.get("finish_reason"),
            "provider_output_tokens": usage["output_tokens"],
            "provider_reasoning_tokens": usage["reasoning_tokens"],
            "provider_visible_tokens": usage["visible_tokens"],
            "provider_token_source": usage["source"],
            "reference_tokens": reference_tokens(content),
            "provider_usage": response.get("usage"),
            "provider_response": provider_response_metadata(response),
        }
        events.append(model_event)
        write_json(runtime / "evidence" / "campaign_checkpoint.json", {
            "cell_id": cell["cell_id"], "output_tokens": output_tokens,
            "working_tokens": output_tokens,
            "termination_policy": "wall_time",
            "per_turn_max_tokens": per_turn_max_tokens,
            "agent_elapsed_s": current_agent_elapsed_s(),
            "event_count": len(events), "events": events, "updated_at": now(),
        })
        messages.append(choice)
        save_conversation()
        if cell["mode"] not in AGENTIC:
            calls = choice.get("tool_calls") or []
            if calls:
                process_tool_calls(calls)
                if invalid_submit_bundle:
                    result.update({
                        "status": "invalid_submission",
                        "termination_reason": "invalid_submit_artifacts_call",
                        "submission_protocol_compliant": False,
                        "parse_diagnostics": ["mixed_submit_artifacts_tool_bundle"],
                    })
                    break
                if (
                    submission_transport_failures
                    >= MAX_ONESHOT_TRANSPORT_FAILURES
                ):
                    record_submission_transport_failure()
                    break
                if finalized:
                    record_direct_tool_submission()
                    break
                continue
            direct_submission = extract_normalized_direct_submission(content, runtime)
            complete = bool(direct_submission["submission_protocol_compliant"])
            if not complete and submission_transport_failures:
                record_submission_transport_failure()
                break
            hit_limit = model_event_hit_limit(model_event)
            result.update({
                "status": "submitted" if complete else "invalid_submission",
                "termination_reason": "model_output_limit" if hit_limit else "completed",
                **direct_submission,
            })
            break
        calls = choice.get("tool_calls") or []
        if not calls:
            hit_limit = model_event_hit_limit(model_event)
            complete = gate_agentic_submission(runtime, result)
            result["status"] = "submitted" if complete else "invalid_submission"
            result["termination_reason"] = "model_output_limit" if hit_limit else "completed"
            break
        process_tool_calls(calls)
        if finalized:
            complete = gate_agentic_submission(runtime, result)
            set_terminal_submission_status(complete, default_reason="completed")
    if result.get("status") == "prepared":
        complete = gate_agentic_submission(runtime, result) if cell["mode"] in AGENTIC else False
        set_terminal_submission_status(
            complete,
            default_reason="agent_timeout",
            incomplete_status="agent_timeout",
            force_reason="agent_timeout",
        )
    result.update({
        "finished_at": now(),
        "output_tokens": output_tokens,
        "working_tokens": output_tokens,
        "output_token_budget": None,
        "per_turn_max_tokens": per_turn_max_tokens,
        "agent_elapsed_s": current_agent_elapsed_s(),
        "events": events,
    })
    attach_experiment_result(
        result,
        runtime,
        messages,
        args,
        (
            "provider_failure"
            if result.get("status") == "provider_transport_failure"
            else "completed"
        ),
    )
    write_json(runtime / "evidence" / "campaign_result.json", result)
    return result


def run_cell_preserving_failure(
    cell: dict[str, Any], args: argparse.Namespace, client: OpenAICompatible | None,
    *, client_factory=None,
) -> dict[str, Any]:
    if (getattr(args, "episode_backend", "legacy") == "native-mini-swe"
            and getattr(args, "native_max_attempts", 1) > 1 and not args.dry_run):
        from run_native_attempts import run_native_attempt_sequence, retry_policy

        if args.resume:
            raise ValueError("native attempt sequences cannot resume")
        if client_factory is None:
            if not isinstance(client, OpenAICompatible):
                raise ValueError("retry requires a fresh client factory")

            def client_factory():
                return OpenAICompatible(
                    base_url=client.endpoint, model=client.model, api_key=client.api_key,
                    timeout_s=client.timeout_s, temperature=client.temperature,
                    stream=client.stream,
                )
        return run_native_attempt_sequence(
            cell=cell, args=args, client_factory=client_factory,
            retry_policy=retry_policy(args.native_max_attempts),
        )
    try:
        return run_cell(cell, args, client)
    except FinalReplayReservedError:
        # Do not attach a new result or modify a terminal scoring runtime.
        raise
    except Exception as exc:  # Preserve failed paid episodes for audit and resume diagnosis.
        runtime = args.output / cell["cell_id"]
        error = str(exc)[:4000]
        trace = traceback.format_exc()[-12000:]
        if client is not None and hasattr(client, "_redact"):
            error = client._redact(error)
            trace = client._redact(trace)
        classification = classify_execution_exception(exc)
        if getattr(args, "episode_backend", "legacy") == "native-mini-swe":
            failure = {
                "cell": cell,
                "runtime": str(runtime),
                "status": classification["status"],
                "termination_reason": classification["termination_reason"],
                "error_type": type(exc).__name__,
                "error": error,
                "traceback": trace,
                "incidents": [classification["incident"]],
                "finished_at": now(),
                "attempt_id": (
                    args._native_attempt_context.attempt_id
                    if getattr(args, "_native_attempt_context", None) is not None
                    else f"{cell['cell_id']}-attempt-0001"
                ),
                "campaign_file_sha256": getattr(args, "campaign_file_sha256", None),
            }
            return write_native_dispatch_result(runtime, failure)
        failure = {
            "cell": cell,
            "status": classification["status"],
            "termination_reason": classification["termination_reason"],
            "error_type": type(exc).__name__,
            "error": error,
            "traceback": trace,
            "incidents": [classification["incident"]],
            "finished_at": now(),
        }
        checkpoint_path = runtime / "evidence" / "conversation_checkpoint.json"
        checkpoint = read_json(checkpoint_path) if checkpoint_path.is_file() else {}
        trajectory_path = runtime / "evidence" / "mini_swe_trajectory.json"
        trajectory = read_json(trajectory_path) if trajectory_path.is_file() else {}
        failure_messages = list(
            checkpoint.get("messages") or trajectory.get("messages") or []
        )
        attach_experiment_result(
            failure, runtime, failure_messages, args, classification["model_status"]
        )
        write_json(runtime / "evidence" / "campaign_result.json", failure)
        return failure


def stored_results(output: Path) -> list[dict[str, Any]]:
    return [
        read_json(path)
        for path in sorted(output.glob("v4-*/evidence/campaign_result.json"))
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key-file")
    parser.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--cell")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument(
        "--agent-scaffold",
        choices=("mini-swe", "native"),
        default="mini-swe",
        help="Agent controller for G2-G5. G0/G1 remain direct-generation conditions.",
    )
    parser.add_argument(
        "--episode-backend",
        choices=("legacy", "native-mini-swe"),
        default="legacy",
        help="Opt-in episode implementation; legacy preserves the historical path.",
    )
    parser.add_argument("--native-max-attempts", type=int, default=1)
    parser.add_argument(
        "--mini-swe-sandbox",
        choices=("auto", "docker", "sandbox-exec", "bubblewrap", "none"),
        default="auto",
        help="Shell backend. Formal mini-SWE runs use the shared Docker environment.",
    )
    parser.add_argument("--docker-command", default="docker")
    parser.add_argument("--mini-swe-image", default=DEFAULT_DOCKER_IMAGE)
    parser.add_argument(
        "--mini-swe-no-evas-image",
        default=DEFAULT_NO_EVAS_DOCKER_IMAGE,
    )
    parser.add_argument("--setup-timeout-s", type=int, default=DEFAULT_SETUP_TIMEOUT_S)
    parser.add_argument("--request-timeout-s", type=int, default=DEFAULT_REQUEST_TIMEOUT_S)
    parser.add_argument("--tool-timeout-s", type=int, default=DEFAULT_TOOL_TIMEOUT_S)
    parser.add_argument("--judge-timeout-s", type=int, default=DEFAULT_JUDGE_TIMEOUT_S)
    parser.add_argument(
        "--mini-swe-preflight-timeout-s",
        type=float,
        default=DEFAULT_MINI_SWE_PREFLIGHT_TIMEOUT_S,
        help="Wall-clock deadline for each Docker sandbox preflight attempt.",
    )
    parser.add_argument(
        "--mini-swe-preflight-attempts",
        type=int,
        default=DEFAULT_MINI_SWE_PREFLIGHT_ATTEMPTS,
        help="Attempts for Docker preflight timeouts; boundary failures are never retried.",
    )
    parser.add_argument(
        "--mini-swe-startup-workers",
        type=int,
        default=DEFAULT_MINI_SWE_STARTUP_WORKERS,
        help="Maximum concurrent Docker create/start/preflight operations.",
    )
    parser.add_argument("--final-judge-command")
    parser.add_argument(
        "--evas-command",
        help="Explicit pinned EVAS command; required unless --dry-run is used.",
    )
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--stream", action="store_true", help="Use OpenAI-compatible SSE streaming responses.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    args.campaign = args.campaign.resolve()
    args.release = args.release.resolve()
    args.output = args.output.resolve()
    campaign = read_json(args.campaign)
    experiment_policy = load_experiment_policy()
    observed_policy_hash = experiment_policy_sha256()
    if campaign.get("experiment_policy_sha256") != observed_policy_hash:
        raise SystemExit(
            "campaign experiment policy differs from EXPERIMENT_POLICY.json"
        )
    args.agent_timeout_s = int(experiment_policy["agent_wall_time_seconds"])
    if campaign.get("agent_wall_time_seconds") != args.agent_timeout_s:
        raise SystemExit(
            "campaign agent wall time differs from EXPERIMENT_POLICY.json"
        )
    if (
        campaign.get("timeout_finalization")
        != experiment_policy["timeout_finalization"]
    ):
        raise SystemExit(
            "campaign timeout finalization differs from EXPERIMENT_POLICY.json"
        )
    expected_mini_swe_image = (campaign.get("execution_config") or {}).get(
        "mini_swe_image"
    )
    if expected_mini_swe_image and args.mini_swe_image != expected_mini_swe_image:
        raise SystemExit(
            "campaign shared Docker image does not match --mini-swe-image: "
            f"expected={expected_mini_swe_image} observed={args.mini_swe_image}"
        )
    expected_no_evas_image = (campaign.get("execution_config") or {}).get(
        "mini_swe_no_evas_image"
    )
    if (
        expected_no_evas_image
        and args.mini_swe_no_evas_image != expected_no_evas_image
    ):
        raise SystemExit(
            "campaign Agent-No-EVAS Docker image does not match "
            "--mini-swe-no-evas-image: "
            f"expected={expected_no_evas_image} "
            f"observed={args.mini_swe_no_evas_image}"
        )
    execution_config = campaign.get("execution_config") or {}
    from run_native_attempts import retry_policy
    try:
        native_retry_policy = retry_policy(args.native_max_attempts).to_document()
    except (TypeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    if args.episode_backend == "legacy" and args.native_max_attempts != 1:
        raise SystemExit("native retries require a native episode backend")
    expected_retry_policy = execution_config.get("native_retry_policy", retry_policy(1).to_document())
    if native_retry_policy != expected_retry_policy:
        raise SystemExit("campaign frozen retry policy differs from --native-max-attempts")
    expected_agent_scaffold = execution_config.get("agent_scaffold")
    if expected_agent_scaffold and args.agent_scaffold != expected_agent_scaffold:
        raise SystemExit(
            "campaign agent scaffold does not match --agent-scaffold: "
            f"expected={expected_agent_scaffold} observed={args.agent_scaffold}"
        )
    expected_episode_backend = execution_config.get(
        "episode_backend", "legacy"
    )
    if args.episode_backend != expected_episode_backend:
        raise SystemExit(
            "campaign episode backend does not match --episode-backend: "
            f"expected={expected_episode_backend} observed={args.episode_backend}"
        )
    for field, observed in (
        ("setup_timeout_s", args.setup_timeout_s),
        ("request_timeout_s", args.request_timeout_s),
        ("tool_timeout_s", args.tool_timeout_s),
        ("judge_timeout_s", args.judge_timeout_s),
        ("per_turn_max_tokens", None),
        ("temperature", args.temperature),
        ("stream", args.stream),
    ):
        expected = execution_config.get(field)
        if expected is not None and observed is not None and observed != expected:
            raise SystemExit(
                f"campaign {field} does not match CLI: "
                f"expected={expected} observed={observed}"
            )
    expected_evas_identity = (campaign.get("execution_config") or {}).get(
        "evas_identity"
    )
    if args.evas_command:
        args.evas_identity = validate_pinned_evas_identity(
            args.evas_command, expected_evas_identity
        )
    else:
        args.evas_identity = None
    expected_release_hash = str(campaign.get("release_manifest_sha256") or "")
    observed_release_hash = hashlib.sha256((args.release / "MANIFEST.json").read_bytes()).hexdigest()
    if expected_release_hash != observed_release_hash:
        raise SystemExit(
            "campaign release manifest does not match --release: "
            f"expected={expected_release_hash or '<missing>'} observed={observed_release_hash}"
        )
    cells = list(campaign["cells"])
    validate_campaign_cells(cells, args.release)
    args.campaign_file_sha256 = hashlib.sha256(args.campaign.read_bytes()).hexdigest()
    if args.episode_backend == "native-mini-swe" and (
        args.cell or args.limit is not None
    ):
        raise SystemExit(
            "native-mini-swe executes the frozen campaign schedule; "
            "--cell and --limit are not supported"
        )
    if args.cell:
        cells = [row for row in cells if row["cell_id"] == args.cell]
    if args.limit is not None:
        cells = cells[:args.limit]
    if not cells:
        raise SystemExit("no matching campaign cells")
    if args.episode_backend == "native-mini-swe":
        if args.agent_scaffold != "mini-swe":
            raise SystemExit("native-mini-swe requires --agent-scaffold mini-swe")
        if args.resume:
            raise SystemExit("native-mini-swe does not support --resume")
        if args.limit is not None:
            raise SystemExit(
                "native-mini-swe does not support --limit; freeze the intended "
                "selection before execution"
            )
        for cell in cells:
            try:
                validate_native_mini_swe_cell(cell)
            except ValueError as exc:
                raise SystemExit(str(exc)) from exc
    requires_evas = any(
        bool(cell.get("executable_feedback", cell.get("evas_cli_available")))
        for cell in cells
    )
    if not args.dry_run and (
        (requires_evas and not args.evas_command)
        or (args.episode_backend == "native-mini-swe" and not args.evas_command)
    ):
        raise SystemExit("--evas-command is required for executable campaigns")
    uses_mini_swe = args.agent_scaffold == "mini-swe" and any(
        cell["mode"] in AGENTIC for cell in cells
    )
    if uses_mini_swe and args.mini_swe_sandbox == "auto" and not args.dry_run:
        args.mini_swe_sandbox = default_sandbox_backend()
    if uses_mini_swe and args.mini_swe_sandbox == "none" and not args.dry_run:
        raise SystemExit(
            "--mini-swe-sandbox none is test-only; use a supported secure sandbox "
            "for executable G2-G5 campaigns"
        )
    if (
        uses_mini_swe
        and args.mini_swe_sandbox not in {"docker", "auto"}
        and not args.dry_run
    ):
        raise SystemExit(
            "paper-valid mini-SWE campaigns require --mini-swe-sandbox docker; "
            "legacy host sandboxes are retained only for sensitivity tests"
        )
    if args.workers < 1:
        raise SystemExit("--workers must be at least 1")
    if min(
        args.agent_timeout_s,
        args.setup_timeout_s,
        args.request_timeout_s,
        args.tool_timeout_s,
        args.judge_timeout_s,
        args.mini_swe_preflight_timeout_s,
        args.mini_swe_preflight_attempts,
        args.mini_swe_startup_workers,
    ) < 1:
        raise SystemExit(
            "timeouts, preflight attempts, and startup workers must be positive"
        )
    args._mini_swe_startup_limiter = threading.BoundedSemaphore(
        args.mini_swe_startup_workers
    )
    key = "" if args.dry_run else load_key(args.api_key_file, args.api_key_env)
    if not args.dry_run:
        os.environ.pop(args.api_key_env, None)
    client = None if args.dry_run else OpenAICompatible(
        base_url=args.base_url, model=campaign["model"], api_key=key,
        timeout_s=args.request_timeout_s, temperature=args.temperature, stream=args.stream,
    )
    args.output.mkdir(parents=True, exist_ok=True)
    if args.workers == 1:
        results = [run_cell_preserving_failure(cell, args, client) for cell in cells]
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(lambda cell: run_cell_preserving_failure(cell, args, client), cells))
    all_results = (
        results
        if args.episode_backend == "native-mini-swe"
        else stored_results(args.output)
    )
    image_summary = summarize_public_agent_images(all_results)
    summary = {
        "schema_version": "v4-calibration-run-summary-v1",
        "campaign": str(args.campaign),
        "dry_run": args.dry_run,
        "evas_identity": args.evas_identity,
        "public_agent_environment": {
            "backend": args.mini_swe_sandbox if uses_mini_swe else None,
            "image": args.mini_swe_image if uses_mini_swe else None,
            "no_evas_image": (
                args.mini_swe_no_evas_image if uses_mini_swe else None
            ),
            "preflight_timeout_s": (
                args.mini_swe_preflight_timeout_s if uses_mini_swe else None
            ),
            "preflight_attempts": (
                args.mini_swe_preflight_attempts if uses_mini_swe else None
            ),
            "startup_workers": (
                args.mini_swe_startup_workers if uses_mini_swe else None
            ),
            **image_summary,
        },
        "result_count": len(all_results),
        "statuses": {},
    }
    for row in all_results:
        status = row["status"]
        summary["statuses"][status] = summary["statuses"].get(status, 0) + 1
    write_json(args.output / "SUMMARY.json", summary)
    print(json.dumps(summary, indent=2))
    return 1 if (
        summary["statuses"].get("runner_error")
        or not summary["public_agent_environment"]["identity_consistent"]
    ) else 0


if __name__ == "__main__":
    raise SystemExit(main())
