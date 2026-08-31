#!/usr/bin/env python3
"""Pinned mini-SWE-agent adapter for vaBench bash-only episodes.

The benchmark harness owns task selection, runtime export, scoring, and
telemetry.  This module owns only the model -> bash -> observation loop used
by G2--G5.  Evaluator assets never enter the model-visible shell sandbox.
"""
from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import threading
import time
from types import SimpleNamespace
from typing import Any, Callable


MINI_SWE_AGENT_VERSION = "2.4.5"
MINI_SWE_SCAFFOLD_ID = "mini-swe-agent-2.4.5-vabench-docker-evas-v3"
DEFAULT_DOCKER_IMAGE = "vabench-agent-runtime:0.8.7"
DEFAULT_NO_EVAS_DOCKER_IMAGE = "vabench-agent-runtime:0.8.7-no-evas"
CANDIDATE_TREE_SCHEMA_VERSION = "v4-candidate-tree-sha256-v1"
CANDIDATE_TREE_HASH_ERROR_SHA256 = hashlib.sha256(
    b"vabench-candidate-tree-hash-error-v1"
).hexdigest()
COMMAND_OUTPUT_CAPTURE_BYTES = 1 * 1024 * 1024
COMMAND_OUTPUT_HEAD_BYTES = 64 * 1024
MODEL_OUTPUT_BYTES = 12_000
MODEL_OUTPUT_HEAD_BYTES = 4_000
PUBLIC_EVAS_FEEDBACK_SCHEMA_VERSION = "vaevas-public-evas-feedback-v1"
PUBLIC_EVAS_MAX_INVOCATIONS = 16
SUBMISSION_QUOTA_BYTES = 64 * 1024 * 1024
WORK_QUOTA_BYTES = 512 * 1024 * 1024
# Bash reports file-size limits in 1024-byte blocks on the supported hosts.
COMMAND_FILE_SIZE_BLOCKS = 64 * 1024
BASH_TOOL = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Execute a bash command in the isolated vaBench public workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The bash command to execute."}
            },
            "required": ["command"],
            "additionalProperties": False,
        },
    },
}

SYSTEM_PROMPT = (
    "You are a behavioral Verilog-A engineer operating in an isolated shell. "
    "Use the bash tool to inspect the public task, create or edit only declared "
    "artifacts under public/submission/, invoke the pinned EVAS executable directly "
    "when useful, inspect its public output yourself, and submit."
)

BASH_CONTRACT = r"""
<vabench_bash_contract>
This is an interactive bash-only episode. Every assistant turn must contain at
least one bash tool call.

Workspace:
- public/task/ is read-only public task material.
- public/skills/ is read-only and exists only in skill-enabled modes; read
  public/skills/<id>/SKILL.md before applying a skill.
- public/submission/ is the only writable candidate-artifact directory.
- work/ is writable scratch space and is never scored.
- /tmp/vabench-visible/evas-output/ contains public EVAS logs and waveforms.
- evaluator, gold implementations, checker source, private mutations, and final
  score cases are not mounted in this shell.

Commands:
- Use ordinary non-interactive shell commands to inspect public/task/ and edit
  public/submission/.
- `evas` is a real, pinned executable in PATH. `evas --help`, pipes, redirection,
  and compound shell commands behave normally.
- Follow public/task/evas_runtime.json and invoke `evas` directly. The sandboxed
  launcher keeps its documented `/tmp/vabench-visible/evas-output` destination
  inside this task container; inspect logs and tran.csv there yourself.
- `vabench-submit` is a real command in PATH. Run it after every declared artifact
  is complete. A rejected submission returns diagnostics and the episode continues.

The container has no network. Do not create symlinks or modify public/task/.
</vabench_bash_contract>
""".strip()

NO_EVAS_SYSTEM_PROMPT = (
    "You are a behavioral Verilog-A engineer operating in an isolated shell. "
    "Use the bash tool to inspect the public task, create or edit only declared "
    "artifacts under public/submission/, reason from the public specification and "
    "files without executable simulator feedback, and submit."
)

NO_EVAS_BASH_CONTRACT = r"""
<vabench_bash_contract>
This is an interactive bash-only episode. Every assistant turn must contain at
least one bash tool call.

Workspace:
- public/task/ is read-only public task material.
- public/skills/ is read-only and exists only in skill-enabled modes; read
  public/skills/<id>/SKILL.md before applying a skill.
- public/submission/ is the only writable candidate-artifact directory.
- work/ is writable scratch space and is never scored.
- evaluator, gold implementations, checker source, private mutations, final
  score cases are not available in this shell.
- EVAS execution is not available in this experimental arm.

Commands:
- Use ordinary non-interactive shell commands to inspect public/task/ and edit
  public/submission/.
- `vabench-submit` is a real command in PATH. Run it after every declared artifact
  is complete. A rejected submission returns diagnostics and the episode continues.

The container has no network. Do not create symlinks or modify public/task/.
</vabench_bash_contract>
""".strip()


class MiniSweAgentUnavailable(RuntimeError):
    """Raised when the pinned mini-SWE-agent package is unavailable or mismatched."""


def _candidate_artifact_paths(
    raw_paths: list[str] | tuple[str, ...],
) -> tuple[str, ...]:
    normalized: list[str] = []
    for raw in raw_paths:
        path = PurePosixPath(str(raw).replace("\\", "/"))
        if not path.parts or path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe candidate artifact path: {raw!r}")
        normalized.append(path.as_posix())
    return tuple(sorted(normalized))


def _candidate_tree_hasher_source(
    candidate_artifacts: tuple[str, ...], *, candidate_root: str
) -> str:
    return f"""import errno
import hashlib
import os
from pathlib import PurePosixPath
import stat

SCHEMA_VERSION = {CANDIDATE_TREE_SCHEMA_VERSION!r}
CANDIDATE_ROOT = {candidate_root!r}
CANDIDATE_ARTIFACTS = {candidate_artifacts!r}


def frame(digest, value):
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)


def candidate_state(relative):
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        directory_fd = os.open(CANDIDATE_ROOT, directory_flags)
    except OSError:
        return b"missing", None, None
    try:
        parts = PurePosixPath(relative).parts
        for part in parts[:-1]:
            try:
                next_fd = os.open(
                    part,
                    directory_flags | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=directory_fd,
                )
            except FileNotFoundError:
                return b"missing", None, None
            except OSError as exc:
                if exc.errno in {{errno.ELOOP, errno.ENOTDIR}}:
                    return b"unsafe_ancestor", None, None
                return b"unreadable", None, None
            os.close(directory_fd)
            directory_fd = next_fd
        try:
            artifact_fd = os.open(
                parts[-1],
                os.O_RDONLY
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_NONBLOCK", 0),
                dir_fd=directory_fd,
            )
        except FileNotFoundError:
            return b"missing", None, None
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                return b"symlink", None, None
            if exc.errno == errno.ENOTDIR:
                return b"unsafe_ancestor", None, None
            return b"unreadable", None, None
        try:
            metadata = os.fstat(artifact_fd)
            if not stat.S_ISREG(metadata.st_mode):
                state = (
                    b"directory"
                    if stat.S_ISDIR(metadata.st_mode)
                    else b"non_regular"
                )
                return state, None, None
            content = hashlib.sha256()
            size = 0
            while True:
                chunk = os.read(artifact_fd, 1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                content.update(chunk)
            return b"file", size, content.digest()
        except OSError:
            return b"unreadable", None, None
        finally:
            os.close(artifact_fd)
    finally:
        os.close(directory_fd)


tree = hashlib.sha256()
frame(tree, SCHEMA_VERSION.encode())
for relative in CANDIDATE_ARTIFACTS:
    frame(tree, relative.encode())
    state, size, content_sha256 = candidate_state(relative)
    frame(tree, state)
    if state == b"file":
        frame(tree, str(size).encode())
        frame(tree, content_sha256)
print(tree.hexdigest())
"""


class _BoundedOutput:
    """Drain process output without allowing a command to exhaust host memory."""

    def __init__(self) -> None:
        self.head = bytearray()
        self.tail = bytearray()
        self.total_bytes = 0
        self._sha256 = hashlib.sha256()
        self.eof = False
        self.read_error = False

    def append(self, chunk: bytes) -> None:
        self.total_bytes += len(chunk)
        self._sha256.update(chunk)
        head_remaining = max(0, COMMAND_OUTPUT_HEAD_BYTES - len(self.head))
        if head_remaining:
            self.head.extend(chunk[:head_remaining])
            chunk = chunk[head_remaining:]
        if not chunk:
            return
        tail_limit = COMMAND_OUTPUT_CAPTURE_BYTES - COMMAND_OUTPUT_HEAD_BYTES
        self.tail.extend(chunk)
        if len(self.tail) > tail_limit:
            del self.tail[: len(self.tail) - tail_limit]

    @property
    def truncated_bytes(self) -> int:
        return max(0, self.total_bytes - len(self.head) - len(self.tail))

    def text(self) -> str:
        marker = b""
        if self.truncated_bytes:
            marker = (
                f"\n[vaBench truncated {self.truncated_bytes} command-output bytes]\n"
            ).encode()
        return bytes(self.head + marker + self.tail).decode("utf-8", errors="replace")

    @property
    def sha256(self) -> str:
        return self._sha256.hexdigest()


def load_mini_swe() -> tuple[type, type, type, Callable[..., list[dict[str, Any]]]]:
    # mini-SWE creates its global config directory at import time. Pin it to a
    # benchmark-owned temporary location instead of depending on user config.
    os.environ["MSWEA_SILENT_STARTUP"] = "1"
    os.environ["MSWEA_GLOBAL_CONFIG_DIR"] = "/tmp/vabench-mini-swe-agent"
    try:
        import minisweagent
        from minisweagent.agents.default import DefaultAgent
        from minisweagent.exceptions import FormatError, Submitted
        from minisweagent.models.utils.actions_toolcall import (
            format_toolcall_observation_messages,
        )
    except ImportError as exc:
        raise MiniSweAgentUnavailable(
            "mini-SWE-agent is required for G2-G5; install the pinned agentic extra"
        ) from exc
    if str(minisweagent.__version__) != MINI_SWE_AGENT_VERSION:
        raise MiniSweAgentUnavailable(
            "mini-SWE-agent version mismatch: "
            f"expected={MINI_SWE_AGENT_VERSION} observed={minisweagent.__version__}"
        )
    return DefaultAgent, Submitted, FormatError, format_toolcall_observation_messages


def _json_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _skill_tree_sha(root: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(root.rglob("*")):
        if item.is_file():
            digest.update(item.relative_to(root).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(item.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def available_skills(runtime: Path) -> dict[str, Any]:
    skills_root = runtime / "public" / "skills"
    policy_path = runtime / "MODEL_ACCESS_POLICY.json"
    policy: dict[str, Any] = {}
    if policy_path.is_file():
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy_skills = policy.get("available_skills") or {}
    policy_mounts = policy.get("mounts") or []
    if not isinstance(policy_skills, dict) or not isinstance(policy_mounts, list):
        raise ValueError("invalid skill fields in MODEL_ACCESS_POLICY.json")
    if not skills_root.exists():
        if policy_skills or "public/skills:ro" in policy_mounts:
            raise ValueError("skill policy declares a missing public/skills directory")
        return {}
    if skills_root.is_symlink() or not skills_root.is_dir():
        raise ValueError("public/skills must be a real directory")
    if not policy_path.is_file():
        raise ValueError("public/skills exists without MODEL_ACCESS_POLICY.json")
    if "public/skills:ro" not in policy_mounts or not policy_skills:
        raise ValueError("public/skills is not authorized by MODEL_ACCESS_POLICY.json")
    manifest = skills_root / "SNAPSHOT_MANIFEST.json"
    if not manifest.is_file() or manifest.is_symlink():
        raise ValueError("public/skills has no regular snapshot manifest")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "v4-runtime-skill-manifest-v1":
        raise ValueError("runtime skill manifest schema mismatch")
    skills = payload.get("skills") or {}
    if not isinstance(skills, dict) or set(skills) != set(policy_skills):
        raise ValueError("runtime skill manifest and model access policy disagree")
    result: dict[str, Any] = {}
    for skill_id, record in skills.items():
        if not isinstance(record, dict):
            raise ValueError(f"invalid runtime skill record: {skill_id}")
        root = skills_root / str(skill_id)
        if root.is_symlink() or any(item.is_symlink() for item in root.rglob("*")):
            raise ValueError(f"runtime skill contains a symlink: {skill_id}")
        if record.get("skill_file") != f"public/skills/{skill_id}/SKILL.md":
            raise ValueError(f"runtime skill has a noncanonical SKILL.md path: {skill_id}")
        if not (root / "SKILL.md").is_file():
            raise ValueError(f"runtime skill is missing SKILL.md: {skill_id}")
        observed_tree = _skill_tree_sha(root)
        if (
            record.get("tree_sha256") != observed_tree
            or (policy_skills.get(skill_id) or {}).get("tree_sha256") != observed_tree
        ):
            raise ValueError(f"runtime skill hash mismatch: {skill_id}")
        result[str(skill_id)] = {
            "skill_file": record["skill_file"],
            "tree_sha256": observed_tree,
        }
    return result


def skill_command_events(commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for index, command in enumerate(commands):
        text = str(command.get("command") or "")
        if "public/skills" not in text and "/workspace/public/skills" not in text:
            continue
        events.append({
            "schema_version": "v4-bash-skill-command-v1",
            "command_index": index,
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "returncode": command.get("returncode"),
        })
    return events


def _sandbox_profile(
    workspace: Path, extra_read_roots: list[Path] | None = None
) -> str:
    escaped = str(workspace).replace('"', '\\"')
    runtime = str(workspace.parent).replace('"', '\\"')
    home = str(Path.home().resolve()).replace('"', '\\"')
    submission = str(workspace / "submission").replace('"', '\\"')
    temporary = str(workspace / ".tmp").replace('"', '\\"')
    rules = [
        "(version 1)",
        # Recent macOS releases abort some system binaries under a strict
        # file-read allowlist because their runtime dependencies are not a
        # stable public interface. Retain system execution capability, then
        # seal user data, temporary data, and the private runtime explicitly.
        "(allow default)",
        "(deny network*)",
        f'(deny file-read* (subpath "{home}"))',
        '(deny file-read* (subpath "/private/tmp") '
        '(subpath "/private/var/folders"))',
        f'(deny file-read* (subpath "{runtime}"))',
        f'(allow file-read* (subpath "{escaped}"))',
        # Traversal metadata is required for executing a pinned interpreter
        # below denied home/tmp trees. File contents and directory enumeration
        # remain denied outside explicit roots.
        f'(allow file-read-metadata (subpath "{home}") '
        '(subpath "/private/tmp") (subpath "/private/var/folders"))',
        "(deny file-write*)",
        f'(allow file-write* (subpath "{submission}") (subpath "{temporary}") '
        f'(subpath "{escaped}/evas-output") '
        '(literal "/dev/null") (literal "/dev/tty"))',
    ]
    for root in extra_read_roots or []:
        readable = str(root).replace('"', '\\"')
        selector = "literal" if root.is_file() else "subpath"
        rules.insert(-2, f'(allow file-read* ({selector} "{readable}"))')
    return "\n".join(rules)


def _bubblewrap_system_mounts() -> list[str]:
    mounts: list[str] = []
    for raw in ("/usr", "/bin", "/sbin", "/lib", "/lib64"):
        path = Path(raw)
        if path.is_symlink():
            mounts.extend(["--symlink", os.readlink(path), raw])
        elif path.exists():
            mounts.extend(["--ro-bind", raw, raw])
    return mounts


def _bubblewrap_parent_dirs(path: Path) -> list[str]:
    parents: list[Path] = []
    current = path.parent
    while current != current.parent:
        if str(current) in {"/usr", "/bin", "/sbin", "/lib", "/lib64"}:
            break
        parents.append(current)
        current = current.parent
    argv: list[str] = []
    for parent in reversed(parents):
        argv.extend(["--dir", str(parent)])
    return argv


def _bubblewrap_argv(
    executable: str,
    runtime: Path,
    extra_read_roots: list[Path],
    command: str,
) -> list[str]:
    workspace = runtime / "public"
    extra_mounts: list[str] = []
    created: set[str] = set()
    for root in extra_read_roots:
        parent_dirs = _bubblewrap_parent_dirs(root)
        for index in range(0, len(parent_dirs), 2):
            parent_args = parent_dirs[index : index + 2]
            if parent_args[1] not in created:
                extra_mounts.extend(parent_args)
                created.add(parent_args[1])
        extra_mounts.extend(["--ro-bind", str(root), str(root)])
    return [
        executable,
        "--die-with-parent",
        "--new-session",
        "--unshare-user",
        "--unshare-ipc",
        "--unshare-pid",
        "--unshare-net",
        "--unshare-uts",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        *_bubblewrap_system_mounts(),
        *extra_mounts,
        "--dir",
        "/workspace",
        "--ro-bind",
        str(workspace),
        "/workspace/public",
        "--bind",
        str(workspace / "submission"),
        "/workspace/public/submission",
        "--bind",
        str(workspace / "evas-output"),
        "/workspace/public/evas-output",
        "--bind",
        str(workspace / ".tmp"),
        "/workspace/public/.tmp",
        "--chdir",
        "/workspace/public",
        "--clearenv",
        "--setenv",
        "PATH",
        "/workspace/public/.tools:/usr/bin:/bin:/usr/sbin:/sbin",
        "--setenv",
        "HOME",
        "/workspace/public",
        "--setenv",
        "TMPDIR",
        "/workspace/public/.tmp",
        "--setenv",
        "VABENCH_EVAS_OUTPUT_ROOT",
        "/workspace/public/evas-output",
        "--setenv",
        "VABENCH_SUBMIT_SENTINEL",
        "/workspace/public/.tmp/submission-request",
        "--setenv",
        "LANG",
        "C.UTF-8",
        "--setenv",
        "LC_ALL",
        "C.UTF-8",
        "/bin/bash",
        "-c",
        command,
    ]


@dataclass
class BashEnvironmentConfig:
    cwd: str
    timeout: float
    sandbox_backend: str


def summarize_evas_operations(invocations: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize sandbox-reported markers, not authenticated process execution."""
    operations = [row.get("operation", "unknown") for row in invocations]
    simulation_statuses = [
        row.get("status", "unknown") for row in invocations
        if row.get("operation") == "simulate"
    ]
    statuses = ("succeeded", "failed", "timed_out", "interrupted", "unknown")
    return {
        "schema_version": "vaevas-public-evas-operations-v1",
        "scope": "captured_sandbox_markers",
        "authenticated": False,
        "authority": "diagnostic_only",
        "reported_calls": len(invocations),
        "reported_help_calls": operations.count("help"),
        "reported_version_calls": operations.count("version"),
        "reported_other_calls": operations.count("other"),
        "unclassified_markers": sum(op not in {"help", "version", "other", "simulate"} for op in operations),
        "reported_simulation_calls": len(simulation_statuses),
        "reported_simulation_status_counts": {
            status: sum((value if value in statuses else "unknown") == status for value in simulation_statuses)
            for status in statuses
        },
    }


class VaBenchBashEnvironment:
    """One bash tool over the model-visible public workspace.

    EVAS and submission are exposed as discoverable shell executables. Commands
    execute in an OS sandbox with no network and no read access to evaluator data.
    """

    def __init__(
        self,
        runtime: Path,
        *,
        timeout_s: float,
        sandbox_backend: str,
        evas_command: str,
        executable_feedback: bool = True,
        structured_evas_feedback: bool = False,
        submission_read_only: bool = False,
        docker_command: str = "docker",
        docker_image: str = "",
        preflight_timeout_s: float = 60.0,
        preflight_attempts: int = 2,
        startup_limiter: threading.Semaphore | None = None,
        deadline_monotonic: float | None = None,
        submission_gate: Callable[[Path], dict[str, Any]],
        candidate_artifacts: list[str] | tuple[str, ...] = (),
        private_output_sink: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        if submission_read_only and sandbox_backend != "docker":
            raise ValueError("read-only submission requires Docker")
        self.runtime = runtime.resolve()
        self.workspace = (self.runtime / "public").resolve()
        self.available_skills = available_skills(self.runtime)
        self.submission_gate = submission_gate
        self.deadline_monotonic = deadline_monotonic
        self.config = BashEnvironmentConfig(
            cwd=str(self.workspace), timeout=float(timeout_s), sandbox_backend=sandbox_backend
        )
        self.workspace.joinpath("submission").mkdir(parents=True, exist_ok=True)
        self.work_dir = self.workspace / "work"
        self.work_dir.mkdir(parents=True, exist_ok=True)
        scratch_root = self.work_dir if sandbox_backend == "docker" else self.workspace
        scratch_root.joinpath("evas-output").mkdir(parents=True, exist_ok=True)
        scratch_root.joinpath(".tmp").mkdir(parents=True, exist_ok=True)
        self.tools_dir = scratch_root / ".tools"
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        public_alias = self.workspace / "public"
        if not public_alias.exists() and not public_alias.is_symlink():
            public_alias.symlink_to(".", target_is_directory=True)
        self.submit_sentinel = scratch_root / ".tmp" / "submission-request"
        self.evas_command = evas_command
        self.executable_feedback = bool(executable_feedback)
        self.submission_read_only = bool(submission_read_only)
        self.structured_evas_feedback = bool(structured_evas_feedback and executable_feedback)
        self.docker_command = docker_command
        self.docker_image = docker_image
        if preflight_timeout_s <= 0:
            raise ValueError("preflight timeout must be positive")
        if preflight_attempts < 1:
            raise ValueError("preflight attempts must be at least 1")
        self.preflight_timeout_s = float(preflight_timeout_s)
        self.preflight_attempts = int(preflight_attempts)
        self.preflight_attempts_used = 0
        self.startup_limiter = startup_limiter
        self.candidate_artifacts = _candidate_artifact_paths(candidate_artifacts)
        self.docker_image_id: str | None = None
        self._docker_container: str | None = None
        self._docker_name = (
            "vabench-"
            + hashlib.sha256(str(self.runtime).encode()).hexdigest()[:12]
            + "-"
            + secrets.token_hex(4)
        )
        self._evas_telemetry_token = secrets.token_hex(16)
        self.evas_invocations: list[dict[str, Any]] = []
        self._install_shell_tools()
        self.commands: list[dict[str, Any]] = []
        self._submitted_exception: type | None = None
        self.private_output_sink = private_output_sink

    def _install_shell_tools(self) -> None:
        self.evas_read_roots: list[Path] = []
        if not self.executable_feedback:
            self._install_submit_tool()
            return
        if self.config.sandbox_backend == "docker":
            if not self.docker_image:
                raise ValueError("Docker backend requires a shared environment image")
            base = ["/usr/local/bin/evas"]
            self.evas_read_roots = []
        else:
            base = shlex.split(self.evas_command)
            if not base:
                raise ValueError("empty EVAS executable command")
            executable = shutil.which(base[0])
            if executable is None:
                raise ValueError(f"EVAS executable is unavailable: {base[0]}")
            base[0] = str(Path(executable).resolve())
            self.evas_read_roots = self._evas_read_roots(Path(base[0]), base[1:])
            if any(
                root == self.runtime or self.runtime in root.parents
                for root in self.evas_read_roots
            ):
                raise ValueError("EVAS executable runtime is inside the private task runtime")
        evas_wrapper = self.tools_dir / "evas"
        candidate_tree_hasher = self.tools_dir / ".candidate-tree-sha256.py"
        candidate_tree_hasher.write_text(
            _candidate_tree_hasher_source(
                self.candidate_artifacts,
                candidate_root=(
                    "/workspace/public/submission"
                    if self.config.sandbox_backend == "docker"
                    else str(self.workspace / "submission")
                ),
            ),
            encoding="utf-8",
        )
        candidate_tree_hasher.chmod(0o444)
        telemetry_prefix = f"VABENCH_EVAS:{self._evas_telemetry_token}"
        output_remap = ""
        operation_telemetry = ""
        if self.structured_evas_feedback:
            operation_telemetry = (
                "operation=other\n"
                "[[ ${args[0]-} == simulate ]] && operation=simulate\n"
                "skip_output=0\n"
                "for arg in \"${args[@]}\"; do\n"
                "  if ((skip_output)); then skip_output=0; continue; fi\n"
                "  case $arg in\n"
                "    --) break ;;\n"
                "    -o) skip_output=1 ;;\n"
                "    --help|-h) operation=help; break ;;\n"
                "    --version) operation=version; break ;;\n"
                "  esac\n"
                "done\n"
                "printf '\\036%s:%s:OP:%s\\n' \"$telemetry_prefix\" \"$invocation_id\" \"$operation\" >&9\n"
            )
        if self.config.sandbox_backend != "docker":
            output_remap = (
                "    if [[ $output == /tmp/vabench-visible/evas-output* ]]; then\n"
                "      suffix=${output#/tmp/vabench-visible/evas-output}\n"
                "      output=${VABENCH_EVAS_OUTPUT_ROOT}${suffix}\n"
                "      echo \"VABENCH_EVAS_OUTPUT=$output\" >&2\n"
                "    elif [[ $output == public/submission/evas-output* ]]; then\n"
                "      suffix=${output#public/submission/evas-output}\n"
                "      output=${VABENCH_EVAS_OUTPUT_ROOT}${suffix}\n"
                "      echo \"VABENCH_EVAS_OUTPUT=$output\" >&2\n"
                "    fi\n"
            )
        evas_wrapper.write_text(
            "#!/bin/bash\n"
            "set -e\n"
            "invocation_id=\"${BASHPID:-$$}-${RANDOM}\"\n"
            f"telemetry_prefix={shlex.quote(telemetry_prefix)}\n"
            "finish_telemetry() {\n"
            "  rc=$?\n"
            "  printf '\\036%s:%s:END:%s\\n' \"$telemetry_prefix\" \"$invocation_id\" \"$rc\" >&9\n"
            "}\n"
            "args=()\n"
            "while (($#)); do\n"
            "  if [[ $1 == -o ]]; then\n"
            "    shift\n"
            "    [[ $# -gt 0 ]] || { echo 'evas: -o requires a path' >&2; exit 2; }\n"
            "    output=$1\n"
            + output_remap
            +
            "    args+=(\"-o\" \"$output\")\n"
            "  else\n"
            "    args+=(\"$1\")\n"
            "  fi\n"
            "  shift\n"
            "done\n"
            "candidate_tree_hasher=\"${BASH_SOURCE[0]%/*}/.candidate-tree-sha256.py\"\n"
            "if [[ -d /Library/Developer/CommandLineTools ]]; then\n"
            "  candidate_tree_sha256=$(DEVELOPER_DIR=/Library/Developer/CommandLineTools "
            "python3 \"$candidate_tree_hasher\")"
            f" || candidate_tree_sha256={CANDIDATE_TREE_HASH_ERROR_SHA256}\n"
            "else\n"
            "  candidate_tree_sha256=$(python3 \"$candidate_tree_hasher\")"
            f" || candidate_tree_sha256={CANDIDATE_TREE_HASH_ERROR_SHA256}\n"
            "fi\n"
            "if [[ ! $candidate_tree_sha256 =~ ^[0-9a-f]{64}$ ]]; then\n"
            f"  candidate_tree_sha256={CANDIDATE_TREE_HASH_ERROR_SHA256}\n"
            "fi\n"
            "printf '\\036%s:%s:START:%s\\n' \"$telemetry_prefix\" \"$invocation_id\" "
            "\"$candidate_tree_sha256\" >&9\n"
            + operation_telemetry
            +
            "trap finish_telemetry EXIT\n"
            "set +e\n"
            f"{shlex.join(base)} \"${{args[@]}}\"\n"
            "exit $?\n",
            encoding="utf-8",
        )
        evas_wrapper.chmod(0o755)

        self._install_submit_tool()

    def _install_submit_tool(self) -> None:
        submit = self.tools_dir / "vabench-submit"
        submit.write_text(
            "#!/bin/bash\n"
            "set -e\n"
            ": > \"${VABENCH_SUBMIT_SENTINEL:?}\"\n",
            encoding="utf-8",
        )
        submit.chmod(0o755)

    @staticmethod
    def _evas_read_roots(executable: Path, arguments: list[str]) -> list[Path]:
        system_roots = tuple(
            Path(root) for root in ("/usr", "/bin", "/sbin", "/lib", "/lib64")
        )

        def system_path(path: Path) -> bool:
            return any(path == root or root in path.parents for root in system_roots)

        roots: list[Path] = []
        venv = executable.parent.parent
        roots.append(venv if (venv / "pyvenv.cfg").is_file() else executable)
        roots.extend(
            path
            for argument in arguments
            if (path := Path(argument)).is_absolute() and path.is_file()
        )
        try:
            first_line = executable.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
        except (OSError, IndexError):
            first_line = ""
        if first_line.startswith("#!"):
            interpreter = Path(first_line[2:].strip().split()[0])
            if interpreter.is_absolute():
                resolved = interpreter.resolve()
                if not system_path(resolved):
                    roots.append(resolved.parent.parent)
        unique: list[Path] = []
        for root in roots:
            resolved = root.resolve()
            if not system_path(resolved) and resolved not in unique:
                unique.append(resolved)
        return unique

    def bind_submitted_exception(self, exception_type: type) -> None:
        self._submitted_exception = exception_type

    def _remaining_command_timeout_s(self) -> float:
        if self.deadline_monotonic is None:
            return self.config.timeout
        return max(
            0.1,
            min(self.config.timeout, self.deadline_monotonic - time.monotonic()),
        )

    def get_template_vars(self, **kwargs: Any) -> dict[str, Any]:
        return {"workspace": str(self.workspace), **kwargs}

    def serialize(self) -> dict[str, Any]:
        return {
            "info": {
                "config": {
                    "environment": {
                        "cwd": str(self.workspace),
                        "timeout": self.config.timeout,
                        "sandbox_backend": self.config.sandbox_backend,
                        "docker_image": self.docker_image or None,
                        "image_id": self.docker_image_id,
                        "network": False,
                        "evaluator_mounted": False,
                        "executable_feedback": self.executable_feedback,
                        **({"submission_read_only": True} if self.submission_read_only else {}),
                        **({"public_evas_feedback_schema_version": PUBLIC_EVAS_FEEDBACK_SCHEMA_VERSION}
                           if self.structured_evas_feedback else {}),
                        "preflight_timeout_s": self.preflight_timeout_s,
                        "preflight_attempts": self.preflight_attempts,
                        "preflight_attempts_used": self.preflight_attempts_used,
                        "resource_limits": {
                            "command_output_capture_bytes": COMMAND_OUTPUT_CAPTURE_BYTES,
                            "command_file_size_blocks": COMMAND_FILE_SIZE_BLOCKS,
                            "submission_bytes": SUBMISSION_QUOTA_BYTES,
                            "work_bytes": WORK_QUOTA_BYTES,
                        },
                    }
                },
                "commands": self.commands,
            }
        }

    def preflight(self) -> None:
        """Fail before the first model call if the requested isolation is unusable."""
        if self.config.sandbox_backend == "none":
            return
        if self.config.sandbox_backend == "docker" and self.startup_limiter is not None:
            with self.startup_limiter:
                self._preflight()
            return
        self._preflight()

    def inspect_public_evas(self) -> dict[str, Any]:
        """Inspect the executable in this runtime, outside model/tool telemetry."""
        if not self.executable_feedback:
            raise ValueError("public EVAS is disabled")
        self.preflight()
        command = (
            "/usr/local/bin/evas --version"
            if self.config.sandbox_backend == "docker"
            else shlex.join([*shlex.split(self.evas_command), "--version"])
        )
        result = subprocess.run(
            self._sandbox_argv(command), cwd=self.workspace, env=self._shell_env(),
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=min(self.preflight_timeout_s, self._remaining_command_timeout_s()),
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError("public EVAS identity probe failed")
        return {"version_output": result.stdout.strip(), "image_id": self.docker_image_id}

    def _preflight(self) -> None:
        if self.config.sandbox_backend == "docker":
            self._ensure_docker_container()
        # ``test -r`` checks Unix permission bits and can still report a path as
        # readable when sandbox-exec would deny the actual filesystem access.
        # Probe a real directory read so macOS and namespace-based backends are
        # validated against the isolation property we rely on.
        executable_probe = (
            "command -v evas >/dev/null && evas --version >/dev/null"
            if self.executable_feedback
            else "! command -v evas >/dev/null"
        )
        argv = self._sandbox_argv(
            "test -r public/task/instruction.md "
            "&& { test ! -d public/skills || test -r public/skills/SNAPSHOT_MANIFEST.json; } "
            f"&& {executable_probe} "
            "&& ! /bin/ls ../evaluator >/dev/null 2>&1"
        )
        for attempt in range(1, self.preflight_attempts + 1):
            self.preflight_attempts_used = attempt
            try:
                probe = subprocess.run(
                    argv,
                    cwd=self.workspace,
                    env=self._shell_env(),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=min(
                        self.preflight_timeout_s,
                        self._remaining_command_timeout_s(),
                    ),
                    check=False,
                )
                break
            except subprocess.TimeoutExpired:
                if attempt == self.preflight_attempts:
                    raise
        if probe.returncode != 0:
            diagnostic = probe.stdout.strip()[:2000] or f"returncode={probe.returncode}"
            if "RTM_NEWADDR" in diagnostic or "unprivileged user namespaces" in diagnostic:
                diagnostic += (
                    " | Linux host policy blocked secure user/network namespaces. "
                    "On Ubuntu 24.04, use the distro system /usr/bin/bwrap with its "
                    "targeted AppArmor userns profile; do not disable network isolation."
                )
            raise RuntimeError(
                "mini-SWE sandbox preflight failed before the first model call: "
                + diagnostic
            )

    def _sandbox_argv(self, command: str) -> list[str]:
        command = (
            f"ulimit -f {COMMAND_FILE_SIZE_BLOCKS}\n"
            "exec 9>&1\n"
            + command
        )
        backend = self.config.sandbox_backend
        if backend == "docker":
            self._ensure_docker_container()
            assert self._docker_container is not None
            container_timeout_s = max(0.05, self._remaining_command_timeout_s() - 0.5)
            return [
                *shlex.split(self.docker_command),
                "exec",
                "-i",
                "--workdir",
                "/workspace",
                "--env",
                "PATH=/workspace/work/.tools:/usr/local/bin:/usr/bin:/bin",
                "--env",
                "HOME=/home/agent",
                "--env",
                "TMPDIR=/tmp",
                "--env",
                "VABENCH_SUBMIT_SENTINEL=/workspace/work/.tmp/submission-request",
                self._docker_container,
                "/usr/bin/timeout",
                "--signal=TERM",
                "--kill-after=1s",
                f"{container_timeout_s:.3f}s",
                "/bin/bash",
                "-c",
                command,
            ]
        if backend == "sandbox-exec":
            executable = shutil.which("sandbox-exec")
            if not executable:
                raise RuntimeError("sandbox-exec backend requested but unavailable")
            return [
                executable,
                "-p",
                _sandbox_profile(self.workspace, self.evas_read_roots),
                "/bin/bash",
                "-c",
                command,
            ]
        if backend == "bubblewrap":
            executable = shutil.which("bwrap")
            if not executable:
                raise RuntimeError("bubblewrap backend requested but bwrap is unavailable")
            return _bubblewrap_argv(
                executable, self.runtime, self.evas_read_roots, command
            )
        if backend == "none":
            return ["/bin/bash", "-c", command]
        raise RuntimeError(f"unsupported mini-SWE sandbox backend: {backend}")

    def _ensure_docker_container(self) -> None:
        if self._docker_container is not None:
            return
        docker = shlex.split(self.docker_command)
        if not docker:
            raise ValueError("empty Docker command")
        executable = shutil.which(docker[0])
        if executable is None:
            raise RuntimeError(f"Docker executable is unavailable: {docker[0]}")
        docker[0] = str(Path(executable).resolve())
        inspect = subprocess.run(
            [*docker, "image", "inspect", "--format", "{{.Id}}", self.docker_image],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=min(30.0, self._remaining_command_timeout_s()),
            check=False,
        )
        if inspect.returncode != 0 or not inspect.stdout.strip():
            raise RuntimeError(
                "shared vaBench Docker image is unavailable: "
                + (inspect.stdout.strip()[:2000] or self.docker_image)
            )
        self.docker_image_id = inspect.stdout.strip().splitlines()[-1]
        uid = os.getuid() if hasattr(os, "getuid") else 10001
        gid = os.getgid() if hasattr(os, "getgid") else 10001
        skill_mount: list[str] = []
        if self.available_skills:
            skill_mount = [
                "--mount",
                (
                    f"type=bind,src={self.workspace / 'skills'},"
                    "dst=/workspace/public/skills,readonly"
                ),
            ]
        create = subprocess.run(
            [
                *docker,
                "create",
                "--name",
                self._docker_name,
                "--platform",
                "linux/amd64",
                "--read-only",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--user",
                f"{uid}:{gid}",
                "--pids-limit=512",
                "--memory=4g",
                "--cpus=2",
                "--network=none",
                "--tmpfs",
                "/tmp:rw,nosuid,nodev,size=2g,mode=1777",
                "--tmpfs",
                f"/home/agent:rw,nosuid,nodev,size=256m,mode=0700,uid={uid},gid={gid}",
                "--mount",
                f"type=bind,src={self.workspace / 'task'},dst=/workspace/public/task,readonly",
                *skill_mount,
                "--mount",
                f"type=bind,src={self.workspace / 'submission'},dst=/workspace/public/submission"
                + (",readonly" if self.submission_read_only else ""),
                "--mount",
                f"type=bind,src={self.work_dir},dst=/workspace/work",
                "--workdir",
                "/workspace",
                self.docker_image_id,
                "/bin/sh",
                "-c",
                "while :; do sleep 3600; done",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=min(30.0, self._remaining_command_timeout_s()),
            check=False,
        )
        if create.returncode != 0:
            raise RuntimeError(
                "failed to create shared vaBench Docker container: "
                + create.stdout.strip()[:2000]
            )
        self._docker_container = create.stdout.strip().splitlines()[-1]
        start = subprocess.run(
            [*docker, "start", self._docker_container],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=min(30.0, self._remaining_command_timeout_s()),
            check=False,
        )
        if start.returncode != 0:
            diagnostic = start.stdout.strip()[:2000]
            self.close()
            raise RuntimeError("failed to start shared vaBench Docker container: " + diagnostic)

    def close(self) -> None:
        if self._docker_container is None:
            return
        container = self._docker_container
        self._docker_container = None
        subprocess.run(
            [*shlex.split(self.docker_command), "rm", "-f", container],
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
            check=False,
        )

    def _submit(self) -> dict[str, Any]:
        gate = self.submission_gate(self.runtime)
        if not gate.get("passed"):
            return {
                "output": json.dumps(
                    {"status": "submission_rejected", "diagnostics": gate.get("diagnostics") or []},
                    sort_keys=True,
                ),
                "returncode": 2,
                "exception_info": "",
            }
        if self._submitted_exception is None:
            raise RuntimeError("mini-SWE-agent Submitted exception was not bound")
        manifest = {
            "status": "submitted",
            "artifact_sha256": gate.get("artifact_sha256") or {},
        }
        raise self._submitted_exception(
            {
                "role": "exit",
                "content": json.dumps(manifest, sort_keys=True),
                "extra": {"exit_status": "Submitted", "submission": json.dumps(manifest, sort_keys=True)},
            }
        )

    def _shell_env(self) -> dict[str, str]:
        if self.config.sandbox_backend == "docker":
            return dict(os.environ)
        return {
            "PATH": f"{self.tools_dir}:/usr/bin:/bin:/usr/sbin:/sbin",
            "HOME": str(self.workspace),
            "TMPDIR": str(self.workspace / ".tmp"),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "VABENCH_EVAS_OUTPUT_ROOT": str(self.workspace / "evas-output"),
            "VABENCH_SUBMIT_SENTINEL": str(self.submit_sentinel),
        }

    @staticmethod
    def _directory_size(root: Path, stop_after: int) -> int:
        total = 0
        pending = [root]
        while pending:
            directory = pending.pop()
            try:
                entries = list(os.scandir(directory))
            except FileNotFoundError:
                continue
            for entry in entries:
                try:
                    if entry.is_symlink():
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        total += entry.stat(follow_symlinks=False).st_size
                except FileNotFoundError:
                    continue
                if total > stop_after:
                    return total
        return total

    def _resource_usage(self) -> dict[str, Any]:
        submission_bytes = self._directory_size(
            self.workspace / "submission", SUBMISSION_QUOTA_BYTES
        )
        work_bytes = self._directory_size(self.work_dir, WORK_QUOTA_BYTES)
        exceeded = []
        if submission_bytes > SUBMISSION_QUOTA_BYTES:
            exceeded.append("submission")
        if work_bytes > WORK_QUOTA_BYTES:
            exceeded.append("work")
        return {
            "submission_bytes": submission_bytes,
            "submission_limit_bytes": SUBMISSION_QUOTA_BYTES,
            "work_bytes": work_bytes,
            "work_limit_bytes": WORK_QUOTA_BYTES,
            "exceeded": exceeded,
        }

    @staticmethod
    def _model_visible_output(output: str) -> str:
        encoded = output.encode("utf-8", errors="replace")
        if len(encoded) <= MODEL_OUTPUT_BYTES:
            return output
        tail_bytes = MODEL_OUTPUT_BYTES - MODEL_OUTPUT_HEAD_BYTES
        removed = len(encoded) - MODEL_OUTPUT_BYTES
        return (
            encoded[:MODEL_OUTPUT_HEAD_BYTES].decode("utf-8", errors="replace")
            + f"\n[vaBench omitted {removed} captured bytes from the model observation]\n"
            + encoded[-tail_bytes:].decode("utf-8", errors="replace")
        )

    def _run_sandboxed(self, command: str) -> dict[str, Any]:
        env = self._shell_env()
        argv = self._sandbox_argv(command)
        started = time.monotonic()
        capture = _BoundedOutput()
        process = subprocess.Popen(
            argv,
            cwd=self.workspace,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        assert process.stdout is not None

        def drain_output() -> None:
            try:
                while chunk := process.stdout.read(64 * 1024):
                    capture.append(chunk)
                capture.eof = True
            except (OSError, ValueError):
                capture.read_error = True
                return

        reader = threading.Thread(target=drain_output, name="vabench-output", daemon=True)
        reader.start()
        host_timed_out = False
        try:
            returncode = process.wait(timeout=self._remaining_command_timeout_s())
        except subprocess.TimeoutExpired:
            host_timed_out = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (AttributeError, OSError):
                process.kill()
            process.wait()
            returncode = -1
        finally:
            reader.join(timeout=5.0)
            if reader.is_alive():
                process.stdout.close()
                reader.join(timeout=1.0)

        elapsed_s = time.monotonic() - started
        command_timed_out = host_timed_out or (
            self.config.sandbox_backend == "docker" and returncode == 124
        )
        first_invocation = len(self.evas_invocations)
        telemetry_capture_complete = (
            capture.eof and not capture.read_error and not reader.is_alive()
            and capture.truncated_bytes == 0
        )
        output = self._record_evas_invocations(
            capture.text(),
            command=command,
            elapsed_s=elapsed_s,
            command_timed_out=command_timed_out,
            capture_complete=telemetry_capture_complete if self.structured_evas_feedback else True,
        )
        resources = self._resource_usage()
        self._emit_private_output_capture(
            capture,
            returncode=returncode,
            elapsed_s=elapsed_s,
            resources=resources,
            capture_complete=(
                capture.eof and not capture.read_error and not reader.is_alive()
            ),
        )
        resource_exhausted = bool(resources["exceeded"])
        if resource_exhausted:
            returncode = 125
            output += "\n" + json.dumps(
                {"status": "agent_resource_exhausted", "resources": resources},
                sort_keys=True,
            )
        return {
            "output": self._model_visible_output(output),
            "returncode": returncode,
            "exception_info": (
                "agent workspace quota exceeded"
                if resource_exhausted
                else "bash command timed out within the episode wall-time limit"
                if command_timed_out
                else ""
            ),
            "elapsed_s": elapsed_s,
            "output_total_bytes": capture.total_bytes,
            "output_captured_bytes": min(
                capture.total_bytes, COMMAND_OUTPUT_CAPTURE_BYTES
            ),
            "output_truncated_bytes": capture.truncated_bytes,
            "resources": resources,
            **({"public_evas": self._public_evas_feedback(
                self.evas_invocations[first_invocation:],
                capture_complete=telemetry_capture_complete,
            )} if self.structured_evas_feedback else {}),
        }

    @staticmethod
    def _public_evas_feedback(
        invocations: list[dict[str, Any]], *, capture_complete: bool
    ) -> dict[str, Any]:
        # Arbitrary Bash can read/forge wrapper markers; never promote to authority.
        return {
            "schema_version": PUBLIC_EVAS_FEEDBACK_SCHEMA_VERSION,
            "scope": "captured_sandbox_markers",
            "authenticated": False,
            "authority": "diagnostic_only",
            "capture_complete": capture_complete,
            "task_correctness": "not_evaluated",
            "invocations": [
                {
                    "invocation_id": row["invocation_id"][:128],
                    "authenticated": False,
                    "evidence_kind": "sandbox_reported_markers",
                    "operation": row["operation"],
                    "status": row["status"],
                    "returncode": row["returncode"],
                    "candidate_tree_schema_version": row["candidate_tree_schema_version"],
                    "candidate_tree_sha256": (
                        row["candidate_tree_sha256"]
                        if re.fullmatch(r"[0-9a-f]{64}", row["candidate_tree_sha256"] or "")
                        else None
                    ),
                }
                for row in invocations[-PUBLIC_EVAS_MAX_INVOCATIONS:]
            ],
            "omitted_invocations": max(0, len(invocations) - PUBLIC_EVAS_MAX_INVOCATIONS),
            "untrusted_operation_summary": summarize_evas_operations(invocations),
        }

    def _emit_private_output_capture(
        self,
        capture: _BoundedOutput,
        *,
        returncode: int,
        elapsed_s: float,
        resources: dict[str, Any],
        capture_complete: bool,
    ) -> None:
        if self.private_output_sink is None:
            return
        self.private_output_sink(
            {
                "schema_version": "vabench-private-tool-output-capture-v1",
                "tool_name": "bash",
                "returncode": returncode,
                "elapsed_s": elapsed_s,
                "output_sha256": capture.sha256,
                "output_total_bytes": capture.total_bytes,
                "output_captured_bytes": min(
                    capture.total_bytes, COMMAND_OUTPUT_CAPTURE_BYTES
                ),
                "output_truncated_bytes": capture.truncated_bytes,
                "output_capture_complete": capture_complete,
                "output_capture_eof": capture.eof,
                "output_capture_read_error": capture.read_error,
                "retained_output_scope": "bounded_head_tail_pre_model_capture",
                "output": capture.text(),
                "resources": resources,
            }
        )

    def _record_evas_invocations(
        self,
        output: str,
        *,
        command: str,
        elapsed_s: float,
        command_timed_out: bool,
        capture_complete: bool = True,
    ) -> str:
        events = "START|END|OP" if self.structured_evas_feedback else "START|END"
        marker = re.compile(
            rf"\x1eVABENCH_EVAS:{re.escape(self._evas_telemetry_token)}:"
            rf"(?P<invocation_id>[^:\r\n]+):(?P<event>{events})"
            r"(?::(?P<payload>[^:\r\n]+))?\r?\n?"
        )
        active: dict[str, dict[str, Any]] = {}
        order: list[str] = []
        for match in marker.finditer(output):
            invocation_id = match.group("invocation_id")
            if match.group("event") == "START":
                if invocation_id not in active:
                    active[invocation_id] = {
                        "invocation_id": invocation_id,
                        "shell_command": command,
                        "shell_elapsed_s": elapsed_s,
                        "candidate_tree_schema_version": CANDIDATE_TREE_SCHEMA_VERSION,
                        "candidate_tree_sha256": match.group("payload"),
                        **({"operation": "unknown", "authenticated": False,
                            "evidence_kind": "sandbox_reported_markers"}
                           if self.structured_evas_feedback else {}),
                    }
                    order.append(invocation_id)
                continue
            row = active.get(invocation_id)
            if row is None:
                continue
            if match.group("event") == "OP":
                operation = match.group("payload")
                row["operation"] = operation if operation in {"simulate", "help", "version", "other"} else "unknown"
                continue
            raw_returncode = match.group("payload") or ""
            if self.structured_evas_feedback and (
                re.fullmatch(r"[0-9]{1,3}", raw_returncode) is None
                or int(raw_returncode) > 255
            ):
                row["returncode"] = None
                row["status"] = "unknown"
                continue
            returncode = int(match.group("payload") or 0)
            row["returncode"] = returncode
            row["status"] = "succeeded" if returncode == 0 else "failed"
        for invocation_id in order:
            row = active[invocation_id]
            if "status" not in row:
                row["returncode"] = None
                row["status"] = (
                    "unknown" if not capture_complete
                    else "timed_out" if command_timed_out else "interrupted"
                )
            self.evas_invocations.append(row)
        return marker.sub("", output)

    def execute(self, action: dict[str, Any], cwd: str = "") -> dict[str, Any]:
        del cwd
        command = str(action.get("command") or "")
        started = time.monotonic()
        kind = "bash"
        try:
            output = self._run_sandboxed(command)
            if self.submit_sentinel.is_file():
                self.submit_sentinel.unlink(missing_ok=True)
                kind = "bash-submit"
                output = self._submit()
        except Exception:
            self.commands.append(
                {
                    "command": command,
                    "kind": kind,
                    "returncode": 0 if kind == "bash-submit" else -1,
                    "elapsed_s": time.monotonic() - started,
                }
            )
            raise
        self.commands.append(
            {
                "command": command,
                "kind": kind,
                "returncode": output.get("returncode"),
                "elapsed_s": output.get("elapsed_s", time.monotonic() - started),
                "output_total_bytes": output.get("output_total_bytes", 0),
                "output_captured_bytes": output.get("output_captured_bytes", 0),
                "output_truncated_bytes": output.get("output_truncated_bytes", 0),
                "resources": output.get("resources") or {},
            }
        )
        return output


class VaBenchMiniModel:
    def __init__(
        self,
        client: Any,
        *,
        per_turn_max_tokens: int,
        request_timeout_s: float,
        deadline_monotonic: float,
        usage_parser: Callable[..., dict[str, Any]],
        response_metadata: Callable[[dict[str, Any]], dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> None:
        self.client = client
        self.per_turn_max_tokens = per_turn_max_tokens
        self.request_timeout_s = request_timeout_s
        self.deadline_monotonic = deadline_monotonic
        self.usage_parser = usage_parser
        self.response_metadata = response_metadata
        self.tools = deepcopy([BASH_TOOL] if tools is None else tools)
        self._tool_names = frozenset(tool["function"]["name"] for tool in self.tools)
        if "bash" not in self._tool_names or len(self._tool_names) != len(self.tools):
            raise ValueError("mini-SWE tools must be unique and include bash")
        self.config = SimpleNamespace(model_name=client.model)
        self.events: list[dict[str, Any]] = []
        self.total_output_tokens = 0
        self._format_observations: Callable[..., list[dict[str, Any]]] | None = None
        self._format_error: type | None = None

    def bind_mini_swe_protocol(
        self,
        formatter: Callable[..., list[dict[str, Any]]],
        format_error: type,
    ) -> None:
        self._format_observations = formatter
        self._format_error = format_error

    def get_template_vars(self, **kwargs: Any) -> dict[str, Any]:
        return {"model_name": self.client.model, **kwargs}

    def format_message(self, *, role: str, content: str, extra: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
        return {"role": role, "content": content, "extra": extra or {}, **kwargs}

    def query(self, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        del kwargs
        remaining = max(0.1, self.deadline_monotonic - time.monotonic())
        timeout_s = min(float(self.request_timeout_s), remaining)
        provider_messages = [
            {key: value for key, value in message.items() if key in {"role", "content", "tool_call_id", "tool_calls"}}
            for message in messages
            if message.get("role") != "exit"
        ]
        started = time.monotonic()
        response = self.client.complete(
            provider_messages,
            self.per_turn_max_tokens,
            deepcopy(self.tools),
            timeout_s=timeout_s,
        )
        choice_row = response["choices"][0]
        choice = dict(choice_row["message"])
        content = str(choice.get("content") or "")
        reasoning = str(choice.get("reasoning_content") or "")
        calls = list(choice.get("tool_calls") or [])
        usage = self.usage_parser(
            response.get("usage"),
            content,
            reasoning_text=reasoning,
            tool_text=json.dumps(calls, sort_keys=True) if calls else "",
        )
        self.total_output_tokens += int(usage["output_tokens"])
        event = {
            "type": "model",
            "elapsed_s": time.monotonic() - started,
            "requested_max_tokens": self.per_turn_max_tokens,
            "finish_reason": choice_row.get("finish_reason"),
            "provider_output_tokens": usage["output_tokens"],
            "provider_reasoning_tokens": usage["reasoning_tokens"],
            "provider_visible_tokens": usage["visible_tokens"],
            "provider_token_source": usage["source"],
            "provider_usage": response.get("usage"),
            "provider_response": self.response_metadata(response),
        }
        # Count every completed provider call, including responses that mini-SWE
        # subsequently rejects as malformed. Token accounting is telemetry only.
        self.events.append(event)
        actions: list[dict[str, Any]] = []
        if not calls:
            if self._format_error is None:
                raise RuntimeError("mini-SWE-agent FormatError was not bound")
            raise self._format_error(
                {
                    "role": "user",
                    "content": (
                        "No tool calls found in the response. Every response MUST "
                        "include at least one bash tool call."
                    ),
                    "extra": {"interrupt_type": "FormatError"},
                }
            )
        for call in calls:
            function = call.get("function") or {}
            if function.get("name") not in self._tool_names:
                if self._format_error is None:
                    raise RuntimeError("mini-SWE-agent FormatError was not bound")
                raise self._format_error(
                    {
                        "role": "user",
                        "content": (f"Unknown tool {function.get('name')!r}; use bash."
                                    if self._tool_names == frozenset({"bash"}) else
                                    f"Unknown tool {function.get('name')!r}; use a declared tool."),
                        "extra": {"interrupt_type": "FormatError"},
                    }
                )
            try:
                arguments = json.loads(function.get("arguments") or "{}")
            except json.JSONDecodeError as exc:
                if self._format_error is None:
                    raise RuntimeError("mini-SWE-agent FormatError was not bound") from exc
                raise self._format_error(
                    {
                        "role": "user",
                        "content": f"Invalid bash tool arguments: {exc}.",
                        "extra": {"interrupt_type": "FormatError"},
                    }
                ) from exc
            if not isinstance(arguments, dict) or (
                function["name"] == "bash" and not isinstance(arguments.get("command"), str)
            ):
                if self._format_error is None:
                    raise RuntimeError("mini-SWE-agent FormatError was not bound")
                raise self._format_error(
                    {
                        "role": "user",
                        "content": "The bash tool requires a string command argument.",
                        "extra": {"interrupt_type": "FormatError"},
                    }
                )
            actions.append({"command": arguments.get("command", ""), "tool_call_id": str(call.get("id") or "")})
        choice["extra"] = {"actions": actions, "cost": 0.0, "provider_event": event}
        return choice

    def format_observation_messages(
        self, message: dict[str, Any], outputs: list[dict[str, Any]], template_vars: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        if self._format_observations is None:
            raise RuntimeError("mini-SWE-agent observation formatter was not bound")
        return self._format_observations(
            actions=list((message.get("extra") or {}).get("actions") or []),
            outputs=outputs,
            observation_template=(
                "<returncode>{{ output.returncode }}</returncode>\n"
                "{% if output.exception_info %}<exception>{{ output.exception_info }}</exception>\n{% endif %}"
                "<output>\n{{ output.output[:12000] }}\n</output>"
            ),
            template_vars=template_vars or {},
        )

    def serialize(self) -> dict[str, Any]:
        return {
            "info": {
                "model": self.client.model,
                "provider_output_tokens": self.total_output_tokens,
                "provider_events": self.events,
            }
        }


def run_mini_swe_episode(
    *,
    runtime: Path,
    prompt: str,
    client: Any,
    per_turn_max_tokens: int,
    agent_timeout_s: float,
    request_timeout_s: float,
    tool_timeout_s: float,
    sandbox_backend: str,
    evas_command: str,
    executable_feedback: bool = True,
    docker_command: str = "docker",
    docker_image: str = DEFAULT_DOCKER_IMAGE,
    preflight_timeout_s: float = 60.0,
    preflight_attempts: int = 2,
    startup_limiter: threading.Semaphore | None = None,
    candidate_artifacts: list[str] | tuple[str, ...] = (),
    submission_gate: Callable[[Path], dict[str, Any]],
    usage_parser: Callable[..., dict[str, Any]],
    response_metadata: Callable[[dict[str, Any]], dict[str, Any]],
    trajectory_path: Path,
    environment_observer: Callable[[Any], None] | None = None,
) -> dict[str, Any]:
    DefaultAgent, Submitted, FormatError, observation_formatter = load_mini_swe()
    started = time.monotonic()
    deadline = started + float(agent_timeout_s)
    environment = VaBenchBashEnvironment(
        runtime,
        timeout_s=min(float(tool_timeout_s), float(agent_timeout_s)),
        sandbox_backend=sandbox_backend,
        evas_command=evas_command,
        executable_feedback=executable_feedback,
        docker_command=docker_command,
        docker_image=docker_image,
        preflight_timeout_s=preflight_timeout_s,
        preflight_attempts=preflight_attempts,
        startup_limiter=startup_limiter,
        deadline_monotonic=deadline,
        submission_gate=submission_gate,
        candidate_artifacts=candidate_artifacts,
    )
    try:
        environment.preflight()
        if environment_observer is not None:
            environment_observer(environment)
        environment.bind_submitted_exception(Submitted)
        model = VaBenchMiniModel(
            client,
            per_turn_max_tokens=per_turn_max_tokens,
            request_timeout_s=request_timeout_s,
            deadline_monotonic=deadline,
            usage_parser=usage_parser,
            response_metadata=response_metadata,
        )
        model.bind_mini_swe_protocol(observation_formatter, FormatError)
        system_prompt = SYSTEM_PROMPT if executable_feedback else NO_EVAS_SYSTEM_PROMPT
        bash_contract = BASH_CONTRACT if executable_feedback else NO_EVAS_BASH_CONTRACT
        agent = DefaultAgent(
            model,
            environment,
            system_template=system_prompt,
            instance_template="{{task}}",
            step_limit=0,
            cost_limit=0.0,
            wall_time_limit_seconds=max(1, int(agent_timeout_s)),
            # Keep malformed-turn recovery available without introducing another
            # episode cutoff. Submission, provider/context failure, and wall time
            # remain the only terminal conditions.
            max_consecutive_format_errors=0,
            output_path=trajectory_path,
        )
        task = prompt.rstrip() + "\n\n" + bash_contract
        outcome = agent.run(task)
        gate = submission_gate(runtime)
        serialized = agent.serialize()
        explicit_submission = outcome.get("exit_status") == "Submitted"
        return {
            "scaffold": MINI_SWE_SCAFFOLD_ID,
            "scaffold_version": MINI_SWE_AGENT_VERSION,
            "executable_feedback": executable_feedback,
            "bash_tool_schema_sha256": _json_digest(BASH_TOOL),
            "system_prompt_sha256": hashlib.sha256(system_prompt.encode()).hexdigest(),
            "bash_contract_sha256": hashlib.sha256(bash_contract.encode()).hexdigest(),
            "exit_status": outcome.get("exit_status"),
            "submission": outcome.get("submission", ""),
            "submitted": bool(explicit_submission and gate.get("passed")),
            "artifact_complete": bool(gate.get("passed")),
            "artifact_gate": gate,
            "artifact_sha256": gate.get("artifact_sha256") or {},
            "output_tokens": model.total_output_tokens,
            "events": model.events,
            "commands": environment.commands,
            "available_skills": available_skills(runtime),
            "skill_command_events": skill_command_events(environment.commands),
            "evas_invocations": environment.evas_invocations,
            "model_calls": len(model.events),
            "messages": list(serialized.get("messages") or []),
            "agent_elapsed_s": time.monotonic() - started,
            "trajectory_format": serialized.get("trajectory_format"),
            "sandbox_backend": sandbox_backend,
            "docker_image": docker_image if sandbox_backend == "docker" else None,
            "docker_image_id": environment.docker_image_id,
            "network": False,
            "evaluator_mounted": False,
            "preflight_timeout_s": environment.preflight_timeout_s,
            "preflight_attempts": environment.preflight_attempts,
            "preflight_attempts_used": environment.preflight_attempts_used,
            "resource_limits": {
                "command_output_capture_bytes": COMMAND_OUTPUT_CAPTURE_BYTES,
                "command_file_size_blocks": COMMAND_FILE_SIZE_BLOCKS,
                "submission_bytes": SUBMISSION_QUOTA_BYTES,
                "work_bytes": WORK_QUOTA_BYTES,
            },
        }
    finally:
        environment.close()


def default_sandbox_backend() -> str:
    if shutil.which("docker"):
        return "docker"
    raise RuntimeError(
        "the shared vaBench Docker environment is unavailable; install Docker and "
        "build environment/ before an executable mini-SWE campaign, or explicitly "
        "select --mini-swe-sandbox none only for local tests"
    )
