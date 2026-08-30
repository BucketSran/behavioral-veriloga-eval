"""Coordinator-owned fresh public execution, never sandbox-marker authority.

The host/Docker daemon and exclusive source-workspace ownership are trusted.
Receipts are hash joins, not signatures or protection against simulator exploits.
This module is not automatically exposed to a model or an Evolution branch.
"""

from __future__ import annotations

from copy import deepcopy
import base64
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import shlex
import subprocess
import tempfile
import time
import uuid

import mini_swe_vabench as mini
from public_validation import public_execution_contract
from result_protocol import canonical_sha256
from runners.agent_harness import (
    EpisodeContext, profile_input_identity_sha256, public_validation_profile_sha256,
)
from runners.agent_harness.tools import waveform_summary as waveform

MAX_FILES = 256
MAX_FILE_BYTES = 1_000_000
MAX_TREE_BYTES = 16 * 1024 * 1024

# Fixed code and fixed output-root argument, run with isolated Python imports.
# Directory descriptors reject links in every component, including the CSV root.
OUTPUT_READER = r'''
import base64, errno, json, os, stat, sys
fds = []
try:
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    fds.append(fd)
    for part in sys.argv[1].strip('/').split('/'):
        fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
        fds.append(fd)
    fd = os.open('tran.csv', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    fds.append(fd)
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode):
        result = {'status': 'invalid'}
    elif info.st_size > int(sys.argv[2]):
        result = {'status': 'too_large'}
    else:
        with os.fdopen(os.dup(fd), 'rb') as stream:
            raw = stream.read(int(sys.argv[2]) + 1)
        result = ({'status': 'too_large'} if len(raw) > int(sys.argv[2]) else
                  {'status': 'available', 'data': base64.b64encode(raw).decode('ascii')})
except OSError as error:
    result = {'status': 'missing' if error.errno == errno.ENOENT else 'invalid'}
finally:
    for fd in reversed(fds):
        os.close(fd)
print(json.dumps(result))
'''


class PublicWaveformError(RuntimeError):
    """No usable receipt; preserve primary failure and separate cleanup incidents."""

    def __init__(self, primary: Exception, cleanup_incidents: list[dict]) -> None:
        super().__init__(str(primary))
        self.primary_type = type(primary).__name__
        self.cleanup_incidents = deepcopy(cleanup_incidents)


class _FreshEnvironment(mini.VaBenchBashEnvironment):
    """Reuse sandbox setup; observe cleanup errors ignored by legacy close()."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cleanup_incidents: list[dict] = []

    def close(self) -> None:
        if self._docker_container is None:
            return
        try:
            result = subprocess.run(
                [*shlex.split(self.docker_command), "rm", "-f", self._docker_container],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=30, check=False,
            )
            if result.returncode:
                self.cleanup_incidents.append({"stage": "container_cleanup", "returncode": result.returncode})
                return
            self._docker_container = None
        except (OSError, subprocess.TimeoutExpired) as error:
            self.cleanup_incidents.append({"stage": "container_cleanup", "error_type": type(error).__name__})


def _read_tree(root: Path, names: tuple[str, ...] | None = None) -> dict[str, bytes]:
    if not root.is_dir() or any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError("public input root must be a regular non-symlink directory")
    discovered = []
    for count, path in enumerate(root.rglob("*"), 1):
        if count > MAX_FILES:
            raise ValueError("public input tree exceeds entry limit")
        if path.is_symlink() or not path.is_dir():
            discovered.append(path.relative_to(root).as_posix())
    if names is not None and (not names or len(set(names)) != len(names) or set(names) != set(discovered)):
        raise ValueError("candidate declarations do not match public input files")
    result = {}
    total = 0
    for name in sorted(discovered):
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != name:
            raise ValueError("unsafe public input path")
        path = root / name
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("public inputs cannot contain symlinks")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE_BYTES:
                raise ValueError("public input must be a bounded regular file")
            raw = stream.read(MAX_FILE_BYTES + 1)
        total += len(raw)
        if len(raw) > MAX_FILE_BYTES or total > MAX_TREE_BYTES:
            raise ValueError("public input bytes exceed limit")
        result[name] = raw
    return result


def _tree_sha256(files: dict[str, bytes]) -> str:
    return canonical_sha256([
        {"path": name, "sha256": hashlib.sha256(raw).hexdigest()}
        for name, raw in sorted(files.items())
    ])


class IsolatedPublicWaveformExecutor:
    def __init__(
        self, *, runtime: Path, context: EpisodeContext,
        candidate_artifacts: tuple[str, ...], release: Path,
        campaign_config_sha256: str, docker_image_id: str,
        timeout_s: float = 60, docker_command: str = "docker",
    ) -> None:
        if context.condition != "Agentic":
            raise ValueError("public waveform execution requires Agentic")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", docker_image_id):
            raise ValueError("an immutable Docker image ID is required")
        if not math.isfinite(timeout_s) or not 0 < timeout_s <= 120:
            raise ValueError("waveform execution timeout must be in (0, 120]")
        self.runtime = runtime
        self.context = context
        self.names = tuple(candidate_artifacts)
        self.image_id = docker_image_id
        self.timeout_s = timeout_s
        self.docker_command = docker_command
        self._invalidated = False
        self._task = _read_tree(runtime / "public/task")
        contract = json.loads(self._task["evas_runtime.json"])
        command, self.scope = public_execution_contract(contract)
        self.command = command.replace("evas simulate ", "/usr/local/bin/evas simulate ")
        self.output_root = "/tmp/vabench-visible/evas-output"
        if self.scope == "reference_dut_only":
            reference = {name.removeprefix("supplied_dut/"): raw for name, raw in self._task.items() if name.startswith("supplied_dut/")}
            digest = hashlib.sha256()
            for name, raw in sorted(reference.items()):
                digest.update(name.encode() + b"\0" + raw + b"\0")
            if self.names != ("testbench.scs",) or not reference or digest.hexdigest() != contract.get("reference_dut_tree_sha256"):
                raise ValueError("public Testbench reference identity mismatch")
            self.output_root += "/reference"
        manifest_bytes = (release / "MANIFEST.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        if manifest.get("release_revision") != "r53" or manifest.get("runtime_requirements", {}).get("evas_version") != "0.8.7":
            raise ValueError("public waveform requires r53 + EVAS 0.8.7")
        self._profile = {
            "schema_version": "vaevas-public-validation-profile-v1",
            "profile_id": "r53/evas-0.8.7-isolated-public-waveform",
            "benchmark_release": "benchmarkv4-r53",
            "benchmark_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "campaign_config_sha256": campaign_config_sha256,
            "evaluator": {"engine": "evas", "version": "0.8.7"},
            "evaluator_identity_sha256": canonical_sha256({"image_id": docker_image_id, "executable": "/usr/local/bin/evas", "version": "0.8.7"}),
            "checker_identity_sha256": canonical_sha256({"scope": self.scope, "public_tree_sha256": _tree_sha256(self._task), "command": self.command, "candidate_artifacts": self.names}),
            "runtime_identity_sha256": canonical_sha256({
                "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "environment_sha256": hashlib.sha256(Path(mini.__file__).read_bytes()).hexdigest(),
                "parser_sha256": hashlib.sha256(Path(waveform.__file__).read_bytes()).hexdigest(),
                "contract_sources": {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                                     for name in ("public_validation.py", "run_campaign.py")},
                "waveform_policy_sha256": waveform.waveform_policy_sha256(),
                "timeout_s": timeout_s, "submission_read_only": True,
                "max_entries": MAX_FILES, "max_file_bytes": MAX_FILE_BYTES, "max_tree_bytes": MAX_TREE_BYTES,
            }),
            "authority_phase": "in_episode", "visibility": "model_observation",
            "memory_policy": "episode_local_public_only", "input_scope": "candidate_tree",
            "allowed_feedback": ["runtime", "waveform_summary"],
            "candidate_binding_required": True, "may_select_candidates": True,
        }
        self.profile_sha256 = public_validation_profile_sha256(self._profile)
        self._settings_sha256 = self._settings_identity()

    @property
    def profile(self) -> dict:
        return deepcopy(self._profile)

    def candidate_tree_sha256(self) -> str:
        return _tree_sha256(_read_tree(self.runtime / "public/submission", self.names))

    def _settings_identity(self) -> str:
        return canonical_sha256({
            "runtime": str(self.runtime), "names": self.names, "image": self.image_id,
            "timeout_s": self.timeout_s, "docker": self.docker_command,
            "command": self.command, "scope": self.scope, "output_root": self.output_root,
            "attempt": self.context.attempt_id, "task": self.context.task_id,
            "condition": self.context.condition,
        })

    def _check_source(self, candidate: str) -> None:
        if self._settings_identity() != self._settings_sha256 or public_validation_profile_sha256(self._profile) != self.profile_sha256:
            raise ValueError("public waveform authority drift")
        for relative in (
            "evidence/final_submission", "evidence/bound-final-test",
            "public/work/.tmp/submission-request", "public/.tmp/submission-request",
        ):
            path = self.runtime / relative
            if path.exists() or path.is_symlink():
                raise ValueError("public waveform forbidden after terminal freeze")
        if _read_tree(self.runtime / "public/task") != self._task:
            raise ValueError("public waveform task drift")
        if self.candidate_tree_sha256() != candidate:
            raise ValueError("public waveform candidate drift")

    def validate(self, *, candidate_tree_sha256: str) -> dict:
        if self._invalidated:
            raise ValueError("public waveform executor invalidated; discard this attempt")
        self._invalidated = True
        self._check_source(candidate_tree_sha256)
        candidate = _read_tree(self.runtime / "public/submission", self.names)
        if _tree_sha256(candidate) != candidate_tree_sha256:
            raise ValueError("copied candidate identity mismatch")
        # The runtime's operator-owned parent is already Docker-shareable. macOS
        # system temp roots need not be visible to the Docker VM. This sibling
        # is outside all original task/submission/work mounts, not model scratch.
        temporary = tempfile.TemporaryDirectory(prefix=".public-waveform-", dir=self.runtime.parent)
        fresh = Path(temporary.name).resolve()
        environment = None
        primary = None
        receipt = None
        incidents = []
        try:
            for directory, files in (("task", self._task), ("submission", candidate)):
                root = fresh / "public" / directory
                root.mkdir(parents=True)
                for name, raw in files.items():
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with path.open("xb") as stream:
                        stream.write(raw)
                if _read_tree(root) != files:
                    raise ValueError("copied public input identity mismatch")
            if self.scope == "reference_dut_only":
                from run_campaign import validate_public_testbench
                validate_public_testbench(fresh / "public/submission/testbench.scs")
            deadline = time.monotonic() + self.timeout_s
            environment = _FreshEnvironment(
                fresh, timeout_s=self.timeout_s, deadline_monotonic=deadline,
                sandbox_backend="docker", evas_command="evas",
                docker_command=self.docker_command, docker_image=self.image_id,
                submission_read_only=True, candidate_artifacts=self.names,
                submission_gate=lambda _: {"passed": False},
            )
            identity = environment.inspect_public_evas()
            if identity["image_id"] != self.image_id or not re.search(r"\bevas-sim\s+0\.8\.7\b", identity["version_output"]):
                raise ValueError("public waveform image/version identity mismatch")
            self._check_source(candidate_tree_sha256)
            result = environment._run_sandboxed(self.command)
            if result["resources"]["exceeded"]:
                raise RuntimeError("public waveform resource limit exceeded")
            status = "succeeded" if result["returncode"] == 0 else "timed_out" if result["returncode"] in (-1, 124) else "failed"
            summary = None
            if status == "succeeded":
                captured = subprocess.run(
                    [*shlex.split(self.docker_command), "exec", environment._docker_container,
                     "/usr/local/bin/python3", "-I", "-c", OUTPUT_READER,
                     self.output_root, str(waveform.MAX_BYTES)],
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=max(0.001, min(10, deadline - time.monotonic())), check=False,
                )
                if captured.returncode or len(captured.stdout) > 2 * waveform.MAX_BYTES:
                    raise RuntimeError("public waveform capture failed")
                packet = json.loads(captured.stdout)
                if packet.get("status") == "available" and set(packet) == {"status", "data"}:
                    raw = base64.b64decode(packet["data"], validate=True)
                    summary = waveform.summarize_waveform_bytes(raw)
                elif packet in ({"status": "missing"}, {"status": "invalid"}, {"status": "too_large"}):
                    summary = {**packet, "source_sha256": None, "policy_sha256": waveform.waveform_policy_sha256()}
                else:
                    raise ValueError("invalid public waveform capture packet")
            self._check_source(candidate_tree_sha256)
            if _read_tree(fresh / "public/submission", self.names) != candidate or _read_tree(fresh / "public/task") != self._task:
                raise ValueError("isolated public input drift")
            receipt = {
                "schema_version": "vaevas-public-waveform-receipt-v1",
                "authority": "public_diagnostic", "task_correctness": "not_evaluated",
                "attempt_id": self.context.attempt_id, "task_id": self.context.task_id,
                "invocation_id": str(uuid.uuid4()), "candidate_tree_sha256": candidate_tree_sha256,
                "profile_sha256": self.profile_sha256,
                "profile_input_identity_sha256": profile_input_identity_sha256(
                    profile_sha256=self.profile_sha256, input_kind="candidate_tree",
                    input_sha256=candidate_tree_sha256, attempt_id=self.context.attempt_id,
                    task_id=self.context.task_id,
                ),
                "image_id": identity["image_id"], "command_sha256": hashlib.sha256(self.command.encode()).hexdigest(),
                "public_task_tree_sha256": _tree_sha256(self._task), "feedback_scope": self.scope,
                "status": status, "returncode": result["returncode"], "elapsed_s": result["elapsed_s"],
                "waveform_summary": summary, "waveform_summary_sha256": canonical_sha256(summary),
            }
        except Exception as error:
            primary = error
        finally:
            if environment is not None:
                environment.close()
                incidents.extend(environment.cleanup_incidents)
            try:
                temporary.cleanup()
            except OSError as error:
                incidents.append({"stage": "scratch_cleanup", "error_type": type(error).__name__})
        if primary is not None:
            raise PublicWaveformError(primary, incidents) from primary
        assert receipt is not None
        receipt["cleanup_incidents"] = incidents
        receipt["usable_feedback"] = not incidents and receipt["status"] != "timed_out"
        if not receipt["usable_feedback"]:
            receipt["waveform_summary"] = None
            receipt["waveform_summary_sha256"] = canonical_sha256(None)
        receipt["receipt_sha256"] = canonical_sha256(receipt)
        self._invalidated = bool(incidents) or receipt["status"] == "timed_out"
        return receipt
