"""Opt-in public simulation observations; no checker or model tool is added.

The caller owns exclusive use of the environment and pre-generation campaign
freezing. Hash checks detect drift, not hostile concurrent mutation/rollback.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

import mini_swe_vabench as mini
from result_protocol import canonical_sha256
from runners.agent_harness import (
    EpisodeContext,
    Observation,
    profile_input_identity_sha256,
    public_validation_profile_sha256,
)

PUBLIC_COMMAND = (
    "evas simulate public/task/visible_test.scs "
    "-o /tmp/vabench-visible/evas-output --spectre-strict"
)
TESTBENCH_COMMAND = (
    "rm -rf /tmp/vabench-visible/reference /tmp/vabench-visible/evas-output/reference "
    "&& mkdir -p /tmp/vabench-visible/reference "
    "&& cp submission/testbench.scs /tmp/vabench-visible/reference/testbench.scs "
    '&& ln -sfn "$(pwd)/task/supplied_dut" /tmp/vabench-visible/reference/dut '
    "&& evas simulate /tmp/vabench-visible/reference/testbench.scs "
    "-o /tmp/vabench-visible/evas-output/reference --spectre-strict"
)
PORTABLE_PUBLIC_COMMAND = PUBLIC_COMMAND.removesuffix(" --spectre-strict")
PORTABLE_TESTBENCH_COMMAND = TESTBENCH_COMMAND.removesuffix(" --spectre-strict")


def public_execution_contract(contract: dict) -> tuple[str, str]:
    """Select a pinned public command, never an arbitrary command from metadata."""
    mode = contract.get("compatibility_mode")
    if mode not in (None, "portable"):
        raise ValueError("unsupported public validation contract")
    if (
        contract.get("schema_version") == "r53-direct-evas-runtime-v2"
        and mode is None
        and contract.get("working_directory") == "runtime_package_root"
        and contract.get("command") == PUBLIC_COMMAND
    ):
        return PUBLIC_COMMAND, "public_simulation_only"
    if (
        contract.get("schema_version") == "r53-direct-evas-runtime-v3"
        and mode == "portable"
        and contract.get("working_directory") == "runtime_package_root"
        and contract.get("command") == PORTABLE_PUBLIC_COMMAND
    ):
        return PORTABLE_PUBLIC_COMMAND, "public_simulation_only"
    testbench_command = (
        PORTABLE_TESTBENCH_COMMAND
        if mode == "portable"
        else TESTBENCH_COMMAND
    )
    expected = {
        "schema_version": "r53-direct-evas-testbench-reference-v1",
        "working_directory": "public_root",
        "candidate_command": testbench_command,
        "candidate": "submission/testbench.scs",
        "candidate_dut_binding": "./dut",
        "feedback_scope": "reference_dut_only",
        "reference_dut_root": "task/supplied_dut",
    }
    if all(contract.get(key) == value for key, value in expected.items()):
        return "cd public && " + testbench_command, "reference_dut_only"
    raise ValueError("unsupported public validation contract")


def _files(root: Path, names: tuple[str, ...]) -> list[dict[str, str]]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("public input root must be a regular directory")
    rows = []
    for name in names:
        relative = PurePosixPath(name)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative.as_posix() != name
        ):
            raise ValueError("unsafe public input path")
        path = root / name
        if any(
            part.is_symlink() for part in (path, *path.parents) if part != root.parent
        ):
            raise ValueError("public inputs cannot contain symlinks")
        if not path.is_file() or path.stat().st_size > 1_000_000:
            raise ValueError("public input must be a regular file at most 1 MB")
        rows.append(
            {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        )
    return rows


def _invocation_tree_sha256(root: Path, names: tuple[str, ...]) -> str:
    """Expected wrapper telemetry digest, distinct from the submission digest.

    The v4 wrapper frames schema/path/state/size/content hash (including absent
    files during generation). Validation only accepts complete regular files.
    Real-wrapper regression tests lock this projection to its existing schema.
    """
    rows = _files(root, names)
    digest = hashlib.sha256()

    def frame(value: bytes) -> None:
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)

    frame(mini.CANDIDATE_TREE_SCHEMA_VERSION.encode())
    for row in rows:
        frame(row["path"].encode())
        frame(b"file")
        frame(str((root / row["path"]).stat().st_size).encode())
        frame(bytes.fromhex(row["sha256"]))
    return digest.hexdigest()


def _authority(
    environment: mini.VaBenchBashEnvironment, *, allow_insecure_test_sandbox: bool
) -> dict:
    if (
        environment.config.sandbox_backend != "docker"
        and not allow_insecure_test_sandbox
    ):
        raise ValueError("public validation requires Docker")
    if not environment.executable_feedback:
        raise ValueError("public EVAS is disabled")
    names = environment.candidate_artifacts
    if not names or len(set(names)) != len(names):
        raise ValueError("candidate declarations must be nonempty and unique")
    task = environment.workspace / "task"
    public_files = _files(
        task,
        tuple(
            sorted(
                path.relative_to(task).as_posix()
                for path in task.rglob("*")
                if path.is_file() or path.is_symlink()
            )
        ),
    )
    contract = json.loads((task / "evas_runtime.json").read_text())
    command, scope = public_execution_contract(contract)
    if scope == "reference_dut_only":
        from run_campaign import skill_tree_sha

        if names != ("testbench.scs",):
            raise ValueError("public Testbench requires exactly testbench.scs")
        reference_files = [row for row in public_files if row["path"].startswith("supplied_dut/")]
        if not reference_files or skill_tree_sha(task / "supplied_dut") != contract.get("reference_dut_tree_sha256"):
            raise ValueError("public reference DUT identity mismatch")
    identity = environment.inspect_public_evas()
    if not re.search(r"\bevas-sim\s+0\.8\.7\b", identity["version_output"]):
        raise ValueError("public validation requires EVAS 0.8.7")
    config = environment.serialize()["info"]["config"]["environment"]
    # Exclude per-attempt locations and transient setup counters from identity.
    config = {
        key: value
        for key, value in config.items()
        if key not in {"cwd", "preflight_attempts_used"}
    }
    sources = {
        name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
        for name in ("public_validation.py", "mini_swe_vabench.py")
    }
    tools = _files(environment.tools_dir, (".candidate-tree-sha256.py", "evas"))
    return {
        "evaluator": {"engine": "evas", "version": "0.8.7"},
        "evaluator_identity_sha256": canonical_sha256(identity),
        # No public checker exists here: bind the public execution inputs instead.
        "checker_identity_sha256": canonical_sha256(
            {
                "kind": scope,
                "files": public_files,
                "command": command,
                "candidate_artifacts": list(names),
            }
        ),
        "runtime_identity_sha256": canonical_sha256(
            {
                "config": config,
                "sources": sources,
                "tools": tools,
            }
        ),
    }


def build_public_validation_profile(
    *,
    environment: mini.VaBenchBashEnvironment,
    release: Path,
    campaign_config_sha256: str,
    allow_insecure_test_sandbox: bool = False,
) -> dict[str, Any]:
    manifest_bytes = (release / "MANIFEST.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if (
        manifest.get("release_revision") != "r53"
        or manifest.get("runtime_requirements", {}).get("evas_version") != "0.8.7"
    ):
        raise ValueError("public validation requires r53 + EVAS 0.8.7")
    profile = {
        "schema_version": "vaevas-public-validation-profile-v1",
        "profile_id": "r53/evas-0.8.7-public-simulation",
        "benchmark_release": "benchmarkv4-r53",
        "benchmark_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "campaign_config_sha256": campaign_config_sha256,
        **_authority(
            environment, allow_insecure_test_sandbox=allow_insecure_test_sandbox
        ),
        "authority_phase": "in_episode",
        "visibility": "model_observation",
        "memory_policy": "episode_local_public_only",
        "input_scope": "candidate_tree",
        "allowed_feedback": ["runtime", "log_excerpt"],
        "candidate_binding_required": True,
        "may_select_candidates": True,
    }
    public_validation_profile_sha256(profile)
    return profile


class PublicEvasValidator:
    """Execute fixed public simulation in an exclusively owned environment."""

    def __init__(
        self,
        *,
        environment: mini.VaBenchBashEnvironment,
        context: EpisodeContext,
        public_validation_profile: dict[str, Any],
        allow_insecure_test_sandbox: bool = False,
    ) -> None:
        self.environment = environment
        self.context = context
        self._profile = deepcopy(public_validation_profile)
        self.profile_sha256 = public_validation_profile_sha256(self._profile)
        if self._profile["benchmark_release"] != "benchmarkv4-r53" or self._profile[
            "allowed_feedback"
        ] != ["runtime", "log_excerpt"]:
            raise ValueError("unsupported public validation profile")
        self._allow_test = allow_insecure_test_sandbox
        self._sequence = 0
        self._invalidated = False

    def candidate_tree_sha256(self) -> str:
        root = self.environment.workspace / "submission"
        names = self.environment.candidate_artifacts
        visible = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if not path.is_dir() or path.is_symlink()
        }
        if visible - set(names):
            raise ValueError("undeclared candidate input in submission")
        return canonical_sha256(_files(root, names))

    def _verify_authority(self) -> None:
        for path in (
            self.environment.runtime / "evidence/final_submission",
            self.environment.runtime / "evidence/bound-final-test",
            self.environment.submit_sentinel,
        ):
            if path.exists() or path.is_symlink():
                raise ValueError("public validation is forbidden after terminal freeze")
        observed = _authority(
            self.environment, allow_insecure_test_sandbox=self._allow_test
        )
        if any(self._profile[key] != value for key, value in observed.items()):
            raise ValueError("public validation authority drift")

    def validate(self, *, candidate_tree_sha256: str) -> Observation:
        if self._invalidated:
            raise ValueError(
                "public validation adapter is invalidated; discard this attempt"
            )
        self._invalidated = True
        observation = self._validate(candidate_tree_sha256=candidate_tree_sha256)
        self._invalidated = False
        return observation

    def _validate(self, *, candidate_tree_sha256: str) -> Observation:
        self._verify_authority()
        if self.candidate_tree_sha256() != candidate_tree_sha256:
            raise ValueError("public validation candidate drift")
        command, scope = public_execution_contract(json.loads(
            (self.environment.workspace / "task/evas_runtime.json").read_text()
        ))
        if scope == "reference_dut_only":
            from run_campaign import validate_public_testbench

            validate_public_testbench(self.environment.workspace / "submission/testbench.scs")
        expected_invocation_hash = _invocation_tree_sha256(
            self.environment.workspace / "submission", self.environment.candidate_artifacts
        )
        start = len(self.environment.evas_invocations)
        result = self.environment.execute({"command": command})
        self._verify_authority()
        if result.get("resources", {}).get("exceeded"):
            raise ValueError("public validation resource limit exceeded")
        if self.candidate_tree_sha256() != candidate_tree_sha256:
            raise ValueError("public validation candidate drift")
        invocations = self.environment.evas_invocations[start:]
        if len(invocations) != 1:
            raise ValueError(
                "public validation invocation evidence missing or ambiguous"
            )
        invocation = invocations[0]
        invocation_hash = invocation.get("candidate_tree_sha256")
        if (
            invocation.get("candidate_tree_schema_version")
            != mini.CANDIDATE_TREE_SCHEMA_VERSION
            or not isinstance(invocation_hash, str)
            or re.fullmatch(r"[0-9a-f]{64}", invocation_hash) is None
            or invocation_hash == mini.CANDIDATE_TREE_HASH_ERROR_SHA256
            or invocation_hash != expected_invocation_hash
        ):
            raise ValueError(
                "public validation invocation candidate identity unavailable or mismatched"
            )
        self._sequence += 1
        output = result["output"]
        return Observation(
            observation_id=f"{self.context.attempt_id}/public-validation-{self._sequence}",
            tool_name="run_evas",
            status=invocation["status"],
            candidate_tree_sha256=candidate_tree_sha256,
            validation_profile_sha256=self.profile_sha256,
            truncated=bool(
                result["output_truncated_bytes"]
                or result["output_captured_bytes"] > mini.MODEL_OUTPUT_BYTES
            ),
            budget_delta={"public_validation_calls": 1},
            payload={
                "feedback_scope": scope,
                "attempt_id": self.context.attempt_id,
                "task_id": self.context.task_id,
                "profile_input_identity_sha256": profile_input_identity_sha256(
                    profile_sha256=self.profile_sha256,
                    input_kind="candidate_tree",
                    input_sha256=candidate_tree_sha256,
                    attempt_id=self.context.attempt_id,
                    task_id=self.context.task_id,
                ),
                "invocation_id": invocation["invocation_id"],
                "invocation_candidate_schema": invocation[
                    "candidate_tree_schema_version"
                ],
                "invocation_candidate_sha256": invocation["candidate_tree_sha256"],
                "returncode": invocation["returncode"],
                "elapsed_s": result["elapsed_s"],
                "output": output,
                "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
            },
        )
