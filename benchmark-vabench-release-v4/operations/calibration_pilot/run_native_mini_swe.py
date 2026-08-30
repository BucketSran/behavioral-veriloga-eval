#!/usr/bin/env python3
"""Opt-in single-cell native mini-swe launcher; legacy campaigns stay unchanged."""

from __future__ import annotations

from pathlib import Path
from copy import deepcopy
from collections.abc import Mapping
import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import mini_swe_vabench as mini  # noqa: E402
import run_campaign as runner  # noqa: E402
import native_episode  # noqa: E402
import public_validation  # noqa: E402
import final_replay  # noqa: E402
from runners.agent_harness import (  # noqa: E402
    AgentAction,
    EpisodeContext,
    EnvironmentStep,
    FrozenSubmission,
    JsonlTrajectoryRecorder,
    Observation,
    ProposalNormalizationError,
    ToolExecutionRejection,
    ToolRegistry,
    backend_profile_sha256,
)
from runners.agent_harness.proposals import (  # noqa: E402
    ProposalEnvelope,
    normalize_proposal,
)
from runners.agent_harness.evidence_export import build_reviewer_evidence_export  # noqa: E402
from runners.agent_harness.trajectory import read_trajectory  # noqa: E402
from runners.agent_harness.backends.mini_swe import (  # noqa: E402
    MiniSwePolicyBridge,
    MiniSweBashEnvironmentBridge,
    mini_swe_bash_tool_descriptor,
)


def _sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _redact(value, credential):
    if isinstance(value, str):
        return (
            value.replace(credential, "<redacted-provider-credential>")
            if credential
            else value
        )
    if isinstance(value, dict):
        return {
            _redact(key, credential): _redact(item, credential)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item, credential) for item in value]
    return value


def _backend_profile(episode_backend="native-mini-swe", proposal_format="native_tool_calls"):
    if episode_backend not in {"native-mini-swe", "native-reasoning"}:
        raise ValueError("unsupported native backend")
    if proposal_format not in {"native_tool_calls", "strict_json"}:
        raise ValueError("unsupported proposal format")
    if episode_backend != "native-reasoning" and proposal_format != "native_tool_calls":
        raise ValueError("strict_json requires native-reasoning")
    profile = {
        "schema_version": "vaevas-backend-profile-v1",
        "backend_profile_id": "mini-swe/native-single-cell-v1",
        "backend_family": "mini_swe",
        "backend_version": mini.MINI_SWE_AGENT_VERSION,
        "inference_mode": "single_trajectory",
        "supported_proposal_formats": ["native_tool_calls"],
        "preferred_proposal_format": "native_tool_calls",
        "action_schema_id": "vaevas-action-v1",
        "observation_schema_id": "vaevas-observation-v1",
        "proposal_normalizer_id": "vaevas-proposal-normalizer-v1",
        "model_interface": {
            "protocol": "openai_compatible_chat_completions",
            "supports_streaming": True,
            "supports_native_tool_calls": True,
            "supports_strict_json": False,
        },
        "state_scope": {
            "memory_scope": "episode_local",
            "shares_state_across_tasks": False,
            "shares_state_across_conditions": False,
        },
        "requires_campaign_contracts": [
            "model_identity",
            "decoding_policy",
            "turn_budget",
            "wall_time_budget",
            "condition_identity",
        ],
        "requires_environment_contracts": [
            "clean_room_runtime",
            "proposal_tool_allowlist",
            "trajectory_sink",
            "candidate_store",
            "submission_freeze",
            "final_judge",
        ],
    }
    if episode_backend == "native-reasoning":
        profile.update({
            "backend_profile_id": "alphaapollo/reasoning-single-cell-v1",
            "backend_family": "alphaapollo_reasoning", "backend_version": "1",
            "supported_proposal_formats": ["native_tool_calls", "strict_json"],
            "preferred_proposal_format": proposal_format,
        })
        profile["model_interface"]["supports_strict_json"] = True
    return profile


def validate_native_cell(cell: dict) -> str:
    """Return the supported native condition name or fail before model use."""
    condition = str(cell.get("experimental_arm") or "")
    if cell.get("form") not in {"dut", "bugfix", "testbench"}:
        raise ValueError("native launcher supports DUT/bugfix/Testbench forms only")
    if condition == "Agentic":
        if (
            cell.get("mode") != "G2"
            or cell.get("executable_feedback") is not True
        ):
            raise ValueError("native Agentic requires G2 executable feedback")
        return condition
    if condition == "Agent-No-EVAS":
        if (
            cell.get("mode") != "G2"
            or cell.get("executable_feedback") is not False
        ):
            raise ValueError("native Agent-No-EVAS requires G2 without feedback")
        return condition
    if condition == "OneShot":
        if (
            cell.get("mode") != "G0"
            or cell.get("process") != "direct_one_shot"
            or cell.get("executable_feedback") is not False
        ):
            raise ValueError("native OneShot requires G0 direct one-shot transport")
        return condition
    raise ValueError(
        "native launcher supports OneShot, Agent-No-EVAS, and Agentic only"
    )


def _native_prompt_path(runtime: Path, condition: str) -> Path:
    prompt_name = "direct_prompt.txt" if condition == "OneShot" else "agent_prompt.txt"
    return runtime / prompt_name


def _interactive_prompt(prompt: str, condition: str) -> str:
    """Reuse the public shell contract without imposing a provider wire format."""
    contract = (
        mini.BASH_CONTRACT if condition == "Agentic" else mini.NO_EVAS_BASH_CONTRACT
    )
    contract = contract.replace(
        "Every assistant turn must contain at\nleast one bash tool call.",
        "Choose exactly one bash action per turn in the configured response format.",
    ).replace(
        "Workspace:\n",
        "Workspace:\n- Each command starts in /workspace in a fresh shell; cd does not persist\n"
        "  across calls. Relative public/ paths are resolved from /workspace.\n",
    )
    return prompt.rstrip() + "\n\n" + contract


def _select_docker_image(condition: str, docker_image: str | None) -> str | None:
    if condition == "OneShot":
        if docker_image not in {None, ""}:
            raise ValueError("native OneShot does not use a Bash runtime image")
        return None
    expected = (
        mini.DEFAULT_NO_EVAS_DOCKER_IMAGE
        if condition == "Agent-No-EVAS"
        else mini.DEFAULT_DOCKER_IMAGE
    )
    if docker_image in {None, ""}:
        return expected
    if condition == "Agent-No-EVAS" and docker_image != expected:
        raise ValueError(
            "native Agent-No-EVAS requires the paired no-EVAS Docker image"
        )
    return docker_image


class _RecordedClient:
    """Record decoded API exchanges, never auth headers or provider credentials."""

    def __init__(self, client, record, context):
        self.client, self.record, self.context = client, record, context
        self.model = client.model
        self.calls = 0

    def complete(self, messages, max_tokens, tools, *, timeout_s=None):
        self.calls += 1
        capture_supported = getattr(self.client, "supports_transport_capture", False) is True
        identity = {
            "request_id": f"{self.context.attempt_id}/request-{self.calls:04d}",
            "action_id": f"{self.context.attempt_id}-{self.calls:04d}",
        }
        self.record(
            "provider_request",
            {
                **identity,
                "messages": deepcopy(messages),
                "max_tokens": max_tokens,
                "tools": deepcopy(tools),
                "timeout_s": timeout_s,
                "transport_capture_supported": capture_supported,
            },
        )
        try:
            transport = {}
            if capture_supported:
                transport["transport_observer"] = lambda payload: self.record(
                    "provider_transport_attempt",
                    _redact({**identity, **payload}, getattr(self.client, "api_key", "")),
                )
            response = self.client.complete(
                messages, max_tokens, tools, timeout_s=timeout_s, **transport,
            )
        except Exception as exc:
            self.record(
                "provider_failure", {**identity, "error_type": type(exc).__name__}
            )
            message = _redact(str(exc), getattr(self.client, "api_key", ""))
            raise RuntimeError(f"provider {type(exc).__name__}: {message}") from None
        response = _redact(response, getattr(self.client, "api_key", ""))
        self.record("provider_response", {**identity, "response": deepcopy(response)})
        return response


class _RecordedEnvironment(MiniSweBashEnvironmentBridge):
    def __init__(self, *, record, **kwargs):
        super().__init__(**kwargs)
        self.record = record

    def step(self, action, capability):
        self.record("tool_request", action.to_document())
        self._legacy_environment.private_output_sink = lambda capture: self.record(
            "tool_output_capture", {"action_id": action.action_id, **capture},
        )
        try:
            result = super().step(action, capability)
        except Exception as exc:
            self.record("tool_failure", {
                "action_id": action.action_id, "error_type": type(exc).__name__,
            })
            raise
        finally:
            self._legacy_environment.private_output_sink = None
        if hasattr(result, "observation"):
            self.record(
                "tool_result",
                {
                    "action_id": action.action_id,
                    "observation": result.observation.to_document(),
                },
            )
        else:
            self.record("tool_failure", {
                "action_id": action.action_id, "error_type": type(result).__name__,
            })
        return result


class _OneShotModel:
    """Single provider call using only the output submission transport."""

    def __init__(
        self,
        *,
        client,
        prompt: str,
        tools: list[dict],
        record,
        context: EpisodeContext,
        per_turn_max_tokens: int,
        request_timeout_s: int,
        deadline_monotonic: float,
    ) -> None:
        self.client = client
        self.prompt = prompt
        self.tools = deepcopy(tools)
        self.record = record
        self.context = context
        self.per_turn_max_tokens = per_turn_max_tokens
        self.request_timeout_s = request_timeout_s
        self.deadline_monotonic = deadline_monotonic
        self.events: list[dict] = []
        self.total_output_tokens = 0
        self.calls = 0

    def submit_once(self) -> dict:
        if self.calls:
            raise ProposalNormalizationError(
                "oneshot_reprompt_forbidden",
                "native OneShot allows exactly one model request",
            )
        self.calls += 1
        messages = [
            {"role": "system", "content": runner.ONESHOT_TRANSPORT_INSTRUCTION},
            {"role": "user", "content": self.prompt},
        ]
        timeout_s = min(
            float(self.request_timeout_s),
            max(0.1, self.deadline_monotonic - time.monotonic()),
        )
        started = time.monotonic()
        response = _RecordedClient(self.client, self.record, self.context).complete(
            messages, self.per_turn_max_tokens, self.tools, timeout_s=timeout_s,
        )
        choice_row = response["choices"][0]
        choice = dict(choice_row["message"])
        content = str(choice.get("content") or "")
        calls = list(choice.get("tool_calls") or [])
        usage = runner.provider_output_usage(
            response.get("usage"),
            content,
            reasoning_text=str(choice.get("reasoning_content") or ""),
            tool_text=json.dumps(calls, sort_keys=True) if calls else "",
        )
        self.total_output_tokens += int(usage["output_tokens"])
        self.events.append({
            "type": "model",
            "elapsed_s": time.monotonic() - started,
            "requested_max_tokens": self.per_turn_max_tokens,
            "finish_reason": choice_row.get("finish_reason"),
            "provider_output_tokens": usage["output_tokens"],
            "provider_reasoning_tokens": usage["reasoning_tokens"],
            "provider_visible_tokens": usage["visible_tokens"],
            "provider_token_source": usage["source"],
            "provider_usage": response.get("usage"),
            "provider_response": runner.provider_response_metadata(response),
        })
        return choice

    def serialize(self) -> dict:
        return {
            "info": {
                "model": self.client.model,
                "call_count": self.calls,
                "provider_output_tokens": self.total_output_tokens,
                "provider_events": self.events,
            }
        }


class _OneShotPolicy:
    def __init__(self, *, model: _OneShotModel, action_id_prefix: str) -> None:
        self.model = model
        self._action_id_prefix = action_id_prefix
        self._used = False

    def act(self, observation: Observation) -> AgentAction:
        if self._used:
            raise ProposalNormalizationError(
                "oneshot_reprompt_forbidden",
                "native OneShot allows exactly one model request",
            )
        self._used = True
        if observation.candidate_tree_sha256 is None:
            raise ValueError("candidate_tree_sha256 is required for OneShot")
        proposal = self.model.submit_once()
        return normalize_proposal(
            ProposalEnvelope(
                action_id=f"{self._action_id_prefix}-0001",
                source_backend="native-oneshot",
                accepted_tool_names=frozenset({"submit_artifacts"}),
                proposal_format="native_tool_calls",
                candidate_tree_sha256=observation.candidate_tree_sha256,
            ),
            proposal.get("tool_calls") or [],
        )


class _OneShotSubmissionEnvironment:
    def __init__(self, *, runtime: Path, task_payload: Mapping[str, object]) -> None:
        self.runtime = runtime
        self._task_payload = dict(task_payload)
        self._attempt_id: str | None = None
        self._closed = False

    def start(self, context: EpisodeContext) -> Observation:
        if self._attempt_id is not None:
            raise RuntimeError("OneShot environment is already started")
        if self._closed:
            raise RuntimeError("OneShot environment is closed")
        self._attempt_id = context.attempt_id
        return Observation(
            observation_id=f"{context.attempt_id}/observation-0000",
            tool_name="task",
            status="ready",
            payload=self._task_payload,
            candidate_tree_sha256=self._candidate_hash(),
        )

    def step(
        self,
        action: AgentAction,
        capability,
    ) -> EnvironmentStep | ToolExecutionRejection:
        if self._attempt_id is None:
            raise RuntimeError("OneShot environment must be started")
        if self._closed:
            raise RuntimeError("OneShot environment is closed")
        if (
            action.tool_name != "submit_artifacts"
            or capability.tool_name != "submit_artifacts"
        ):
            return ToolExecutionRejection(
                code="unsupported_dispatch",
                failure_category="tool_contract_rejected",
                primary_outcome="protocol_failure",
                message="OneShot accepts only submit_artifacts",
                candidate_tree_sha256=self._candidate_hash(),
            )
        try:
            self._write_submission(action.arguments)
        except (TypeError, ValueError) as exc:
            return ToolExecutionRejection(
                code="invalid_submit_artifacts",
                failure_category="tool_contract_rejected",
                primary_outcome="protocol_failure",
                message=str(exc),
                candidate_tree_sha256=self._candidate_hash(),
            )
        candidate_sha256 = self._candidate_hash()
        return EnvironmentStep(
            observation=Observation(
                observation_id=f"{self._attempt_id}/observation-0001",
                tool_name="submit_artifacts",
                status="submitted",
                payload={"output": "submission accepted"},
                candidate_tree_sha256=candidate_sha256,
            ),
            done=True,
            terminal_reason="submitted",
        )

    def freeze_submission(self) -> FrozenSubmission:
        gate = runner.submission_artifact_gate(self.runtime)
        if not gate["passed"]:
            raise ValueError("native OneShot submission gate rejected the candidate")
        manifest = runner.RESULT_PROTOCOL.snapshot_submission(self.runtime, gate)
        return FrozenSubmission(
            manifest["tree_sha256"], tuple(sorted(gate["expected_artifacts"]))
        )

    def close(self) -> None:
        self._closed = True

    def _write_submission(self, arguments: Mapping[str, object]) -> None:
        if set(arguments) != {"artifacts"} or not isinstance(
            arguments.get("artifacts"), Mapping
        ):
            raise ValueError("submit_artifacts requires an artifacts object")
        expected = runner.expected_candidate_artifacts(self.runtime)
        artifacts = arguments["artifacts"]
        assert isinstance(artifacts, Mapping)
        if set(artifacts) != set(expected):
            raise ValueError("submit_artifacts must provide exactly declared artifacts")
        root = self.runtime / "public/submission"
        if root.is_symlink():
            raise ValueError("submission root cannot be a symlink")
        # Recheck immediately before writes, including intermediate directories.
        self._candidate_hash()
        for relative, content in artifacts.items():
            path = runner.safe_relative(str(relative))
            if path.as_posix() not in expected:
                raise ValueError("undeclared submit_artifacts path")
            if not isinstance(content, str):
                raise TypeError("submit_artifacts content must be strings")
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.is_symlink():
                raise ValueError("submission artifact cannot be a symlink")
            target.write_text(content, encoding="utf-8")

    def _candidate_hash(self) -> str:
        root = self.runtime / "public/submission"
        if root.is_symlink() or any(path.is_symlink() for path in root.rglob("*")):
            raise ValueError("candidate tree cannot contain symlinks")
        return runner.RESULT_PROTOCOL.hash_test_tree(root)["tree_sha256"]


def _submit_artifacts_tool_descriptor(runtime: Path) -> dict:
    schema = runner.submit_artifacts_tool_schema(runtime)["function"]["parameters"]
    return {
        "schema_version": "vaevas-tool-descriptor-v1",
        "tool_id": "native/submit-artifacts-v1",
        "tool_name": "submit_artifacts",
        "tool_version": "1",
        "lifecycle": "active",
        "model_visibility": "model_visible",
        "allowed_conditions": ["OneShot"],
        "budget_class": "submission",
        "state_effect": "terminal_submission",
        "candidate_effect": "freeze",
        "argument_schema": schema,
        "observation_schema": {
            "type": "object",
            "properties": {"output": {"type": "string"}},
            "required": ["output"],
            "additionalProperties": False,
        },
        "evidence_policy": {
            "records_private_evidence": False,
            "may_enter_model_observation": True,
            "may_enter_shared_memory": False,
            "requires_candidate_binding": True,
        },
        "handler_id": "native.submit_artifacts",
    }


def run_prepared_native_mini_swe(
    *,
    runtime: Path,
    cell: dict,
    client,
    attempt_id: str,
    evas_command: str,
    release: Path = runner.DEFAULT_RELEASE,
    final_judge_command: str | None = None,
    request_timeout_s: int = runner.DEFAULT_REQUEST_TIMEOUT_S,
    tool_timeout_s: int = runner.DEFAULT_TOOL_TIMEOUT_S,
    judge_timeout_s: int = runner.DEFAULT_JUDGE_TIMEOUT_S,
    docker_image: str | None = None,
    allow_insecure_test_sandbox: bool = False,
    campaign_file_sha256: str | None = None,
    episode_context: EpisodeContext | None = None,
    episode_backend: str = "native-mini-swe",
    reasoning_proposal_format: str = "native_tool_calls",
) -> native_episode.NativeEpisodeRun:
    """Run an exclusively owned fresh exported native tri-form cell.

    This API does not attest that a caller's export came from the sealed release.
    Use the CLI for exporter/config composition. No resume or automatic retry.
    """
    condition = validate_native_cell(cell)
    backend = _backend_profile(episode_backend, reasoning_proposal_format)
    docker_image = _select_docker_image(condition, docker_image)
    if min(request_timeout_s, tool_timeout_s, judge_timeout_s) <= 0:
        raise ValueError("infrastructure watchdogs must be positive")
    if runtime.is_symlink() or (runtime / "evidence").is_symlink():
        raise ValueError("runtime/evidence must not be a symlink")
    runtime = runtime.resolve()
    for name in (
        "native-launcher",
        "native-episode",
        "bound-final-test",
        "final_submission",
        "campaign_result.json",
        "conversation_checkpoint.json",
        "mini_swe_trajectory.json",
        "trusted_replay_result.json",
        "score-sidecars",
    ):
        path = runtime / "evidence" / name
        if path.exists() or path.is_symlink():
            raise RuntimeError(
                "native launcher requires a fresh runtime; attempt already reserved"
            )
    policy_config = runner.load_experiment_policy()
    context = episode_context or EpisodeContext(
        cell["cell_id"], attempt_id, cell["task_id"], condition, None
    )
    if (
        (context.episode_id, context.attempt_id, context.task_id, context.condition)
        != (cell["cell_id"], attempt_id, cell["task_id"], condition)
        or context.max_steps is not None or context.budget_limits
    ):
        raise ValueError("attempt context differs from frozen native cell policy")
    directory = runtime / "evidence/native-launcher"
    directory.parent.mkdir(parents=True, exist_ok=True)
    directory.mkdir(mode=0o700)
    trace_path = directory / "private-events.jsonl"
    trace = JsonlTrajectoryRecorder(trace_path)
    trace_path.chmod(0o600)
    credential = getattr(client, "api_key", "")

    def record(event_type, payload):
        trace.append(
            context=context,
            actor="launcher",
            event_type=event_type,
            visibility="harness",
            payload=_redact(payload, credential),
        )

    environment = None
    run = None
    try:
        deadline = time.monotonic() + policy_config["agent_wall_time_seconds"]
        submitted = None
        if condition != "OneShot":
            assert docker_image is not None
            environment = mini.VaBenchBashEnvironment(
                runtime,
                timeout_s=tool_timeout_s,
                sandbox_backend="none" if allow_insecure_test_sandbox else "docker",
                evas_command=evas_command,
                docker_image=docker_image,
                deadline_monotonic=deadline,
                submission_gate=runner.submission_artifact_gate,
                candidate_artifacts=runner.expected_candidate_artifacts(runtime),
                executable_feedback=(condition == "Agentic"),
            )
            try:
                environment.preflight()
            except (OSError, subprocess.TimeoutExpired) as exc:
                if time.monotonic() >= deadline:
                    raise RuntimeError("agent deadline exhausted during startup") from exc
                raise runner.SandboxStartupError("transient sandbox preflight failure") from exc
            _, submitted, _, _ = mini.load_mini_swe()
            environment.bind_submitted_exception(submitted)
        prompt = _native_prompt_path(runtime, condition).read_text()
        manifest = {
            "schema_version": "vaevas-native-launcher-manifest-v1",
            "cell": deepcopy(cell),
            "condition": condition,
            "attempt_id": attempt_id,
            "attempt_lineage": {
                "parent_attempt_id": context.parent_attempt_id,
                "retry_index": context.retry_index,
                "retry_reason": context.retry_reason,
            },
            "backend_profile": backend,
            "campaign_file_sha256": campaign_file_sha256,
            "model": client.model,
            "endpoint_sha256": hashlib.sha256(client.endpoint.encode()).hexdigest(),
            "temperature": client.temperature,
            "stream": client.stream,
            "provider_transport": "existing_adapter_up_to_three_internal_transport_attempts",
            "experiment_policy": policy_config,
            "experiment_policy_sha256": runner.experiment_policy_sha256(),
            "max_steps": None,
            "request_timeout_s": request_timeout_s,
            "tool_timeout_s": tool_timeout_s,
            "judge_timeout_s": judge_timeout_s,
            "environment": (
                {
                    **environment.serialize()["info"]["config"]["environment"],
                    "docker_image": docker_image,
                }
                if environment is not None
                else {
                    "sandbox_backend": "controller_managed_output_transport",
                    "docker_image": None,
                    "network": False,
                    "evaluator_mounted": False,
                }
            ),
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "source_sha256": {
                name: _sha_file(HERE / name)
                for name in (
                    "run_native_mini_swe.py",
                    "native_episode.py",
                    "mini_swe_vabench.py",
                )
            },
            "claim_scope": "development_only_opt_in_single_cell",
            "raw_trace_scope": "decoded_provider_exchanges_bounded_transport_and_tool_capture_v1",
            "reviewer_export_contract": "vaevas-reviewer-evidence-export-v1",
        }
        if episode_backend == "native-reasoning":
            manifest["source_sha256"]["reasoning_policy.py"] = _sha_file(
                REPO / "runners/agent_harness/backends/reasoning.py"
            )
        config_sha = runner.RESULT_PROTOCOL.canonical_sha256(manifest)
        public_profile = None
        public_profile_sha256 = None
        if condition == "Agentic":
            public_profile = public_validation.build_public_validation_profile(
                environment=environment,
                release=release,
                campaign_config_sha256=config_sha,
                allow_insecure_test_sandbox=allow_insecure_test_sandbox,
            )
            public_profile_sha256 = public_validation.public_validation_profile_sha256(
                public_profile
            )
        manifest["public_validation_profile_sha256"] = public_profile_sha256
        command = final_judge_command or shlex.join(
            [sys.executable, str(HERE / "trusted_replay_adapter.py")]
        )
        final_profile = final_replay.build_final_test_profile(
            runtime=runtime,
            release=release,
            campaign_config_sha256=config_sha,
            command=command,
            timeout_s=judge_timeout_s,
            evas_command=evas_command,
        )
        native_episode._write_once(directory / "manifest.json", manifest)
        paused = False

        def quiesce():
            nonlocal paused
            if paused or allow_insecure_test_sandbox:
                return
            if environment is None:
                return
            container = environment._docker_container
            if not container:
                raise RuntimeError("native sandbox unavailable at freeze")
            subprocess.run(
                ["docker", "pause", container],
                check=True,
                capture_output=True,
                timeout=30,
            )
            observed = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Paused}}", container],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if observed.stdout.strip() != "true":
                raise RuntimeError("native sandbox writers were not quiesced")
            paused = True
            record("workspace_quiesced", {"method": "verified_docker_pause"})

        def candidate_hash():
            root = runtime / "public/submission"
            if root.is_symlink() or any(path.is_symlink() for path in root.rglob("*")):
                raise ValueError("candidate tree cannot contain symlinks")
            return runner.RESULT_PROTOCOL.hash_test_tree(root)["tree_sha256"]

        def freeze():
            quiesce()
            gate = runner.submission_artifact_gate(runtime)
            if not gate["passed"]:
                raise ValueError("native submission gate rejected the candidate")
            manifest = runner.RESULT_PROTOCOL.snapshot_submission(runtime, gate)
            return FrozenSubmission(
                manifest["tree_sha256"], tuple(sorted(gate["expected_artifacts"]))
            )

        def deadline_finalize():
            quiesce()
            return (
                candidate_hash()
                if runner.submission_artifact_gate(runtime)["passed"]
                else None
            )

        if condition == "OneShot":
            tools = [runner.submit_artifacts_tool_schema(runtime)]
            model = _OneShotModel(
                client=client,
                prompt=prompt,
                tools=tools,
                record=record,
                context=context,
                per_turn_max_tokens=runner.cell_per_turn_max_tokens(cell),
                request_timeout_s=request_timeout_s,
                deadline_monotonic=deadline,
            )
            policy = _OneShotPolicy(model=model, action_id_prefix=attempt_id)
            bridge = _OneShotSubmissionEnvironment(
                runtime=runtime,
                task_payload={"prompt": prompt},
            )
            tool_registry = ToolRegistry([_submit_artifacts_tool_descriptor(runtime)])
        else:
            assert environment is not None and submitted is not None
            model = mini.VaBenchMiniModel(
                _RecordedClient(client, record, context),
                per_turn_max_tokens=runner.cell_per_turn_max_tokens(cell),
                request_timeout_s=request_timeout_s,
                deadline_monotonic=deadline,
                usage_parser=runner.provider_output_usage,
                response_metadata=runner.provider_response_metadata,
            )
            if episode_backend == "native-reasoning":
                from runners.agent_harness.backends.reasoning import ReasoningPolicy

                model = ReasoningPolicy(
                    client=_RecordedClient(client, record, context), context=context,
                    proposal_format=reasoning_proposal_format, tools=[mini.BASH_TOOL],
                    accepted_tool_names=frozenset({"bash"}),
                    max_tokens=runner.cell_per_turn_max_tokens(cell),
                    timeout_s=request_timeout_s, deadline_monotonic=deadline,
                )
                policy = model
            else:
                policy = NativeMiniSwePolicy(
                    model=model, prompt=prompt, action_id_prefix=attempt_id,
                    condition=condition,
                )
            bridge = _RecordedEnvironment(
                record=record,
                legacy_environment=environment,
                task_payload={"prompt": _interactive_prompt(prompt, condition)},
                candidate_tree_sha256=candidate_hash,
                freeze_submission=freeze,
                submitted_exception_types=(submitted,),
            )
            tool_registry = ToolRegistry(
                [mini_swe_bash_tool_descriptor(allowed_conditions=[condition])]
            )
        run = native_episode.run_native_episode(
            runtime=runtime,
            context=context,
            policy=policy,
            environment=bridge,
            tool_registry=tool_registry,
            backend_profile_sha256=backend_profile_sha256(backend),
            public_validation_profile=public_profile,
            final_test_profile=final_profile,
            command=command,
            timeout_s=judge_timeout_s,
            evas_command=evas_command,
            deadline_monotonic=deadline,
            deadline_finalizer=deadline_finalize,
        )
        reviewer_export = build_reviewer_evidence_export(
            trajectory_events=read_trajectory(run.trajectory_path),
            private_events=read_trajectory(trace_path),
            trajectory_bytes=run.trajectory_path.read_bytes(),
            private_event_bytes=trace_path.read_bytes(),
        )
        native_episode._write_once(directory / "reviewer-export.json", reviewer_export)
        native_episode._write_once(
            directory / "result.json",
            {
                "schema_version": "vaevas-native-launcher-result-v1",
                "manifest_sha256": _sha_file(directory / "manifest.json"),
                "private_events_sha256": _sha_file(trace_path),
                "private_events_tail_sha256": trace.tail_sha256,
                "trajectory_sha256": _sha_file(run.trajectory_path),
                "reviewer_export_sha256": _sha_file(directory / "reviewer-export.json"),
                "artifact_file_sha256": _sha_file(run.artifact_path)
                if run.artifact_path
                else None,
                "artifact_path": str(run.artifact_path.relative_to(runtime))
                if run.artifact_path
                else None,
                "model_telemetry": model.serialize()["info"],
                "evas_invocations": (
                    environment.evas_invocations if environment is not None else []
                ),
                "primary_outcome": run.result.primary_outcome,
                "terminal_reason": run.result.terminal_reason,
            },
        )
        return run
    except Exception as exc:
        record("launcher_failure", {"error_type": type(exc).__name__})
        raise
    finally:
        if environment is not None and run is None:
            try:
                environment.close()
            except Exception as exc:
                record("launcher_cleanup_failed", {"error_type": type(exc).__name__})
        with trace_path.open("rb") as handle:
            os.fsync(handle.fileno())
        trace_path.chmod(0o400)


class NativeMiniSwePolicy:
    """Reuse the pinned mini-swe prompt and observation formatter, not its loop."""

    def __init__(self, *, model, prompt: str, action_id_prefix: str, condition="Agentic"):
        _, _, format_error, formatter = mini.load_mini_swe()
        model.bind_mini_swe_protocol(formatter, format_error)
        self._format_error = format_error
        self.model = model
        self.messages = [
            model.format_message(role="system", content=(
                mini.SYSTEM_PROMPT if condition == "Agentic" else mini.NO_EVAS_SYSTEM_PROMPT
            )),
            model.format_message(
                role="user", content=_interactive_prompt(prompt, condition)
            ),
        ]
        self._last_message = None
        self._bridge = MiniSwePolicyBridge(
            propose=self._propose,
            action_id_prefix=action_id_prefix,
        )

    def _propose(self, observation):
        if self._last_message is not None:
            self.messages.extend(
                self.model.format_observation_messages(
                    self._last_message,
                    [observation.to_document()["payload"]],
                )
            )
        try:
            message = self.model.query(self.messages)
        except self._format_error:
            # The opt-in controller deliberately does not reprompt like legacy
            # DefaultAgent. A malformed model action is still a protocol error,
            # not a provider outage; do not persist untrusted error text here.
            raise ProposalNormalizationError(
                "mini_swe_format_error", "mini-swe rejected the model action"
            ) from None
        self.messages.append(message)
        self._last_message = message
        return message

    def act(self, observation):
        return self._bridge.act(observation)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--cell", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New exclusive output directory; never resumed.",
    )
    parser.add_argument("--base-url")
    parser.add_argument("--api-key-env", default="VABENCH_API_KEY")
    parser.add_argument("--api-key-file")
    parser.add_argument("--evas-command")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--stream", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Export only; no provider, sandbox, or scoring.",
    )
    args = parser.parse_args(argv)
    campaign = runner.read_json(args.campaign)
    release = runner.DEFAULT_RELEASE
    policy = runner.load_experiment_policy()
    expected = {
        "experiment_policy_sha256": runner.experiment_policy_sha256(),
        "agent_wall_time_seconds": policy["agent_wall_time_seconds"],
        "timeout_finalization": policy["timeout_finalization"],
        "release_manifest_sha256": _sha_file(release / "MANIFEST.json"),
    }
    if any(campaign.get(key) != value for key, value in expected.items()):
        parser.error("campaign differs from pinned r53/experiment policy")
    runner.validate_campaign_cells(campaign["cells"], release)
    cells = [cell for cell in campaign["cells"] if cell["cell_id"] == args.cell]
    if len(cells) != 1:
        parser.error("select exactly one campaign cell")
    cell = cells[0]
    try:
        condition = validate_native_cell(cell)
    except ValueError as exc:
        parser.error(str(exc))
    if campaign.get("execution_config"):
        parser.error(
            "native launcher requires a campaign without legacy execution_config overrides"
        )
    if not args.dry_run and (not args.base_url or not args.evas_command):
        parser.error("--base-url and --evas-command are required unless --dry-run")
    client = None
    if not args.dry_run:
        runner.resolve_pinned_evas_identity(args.evas_command)
        key = runner.load_key(args.api_key_file, args.api_key_env)
        os.environ.pop(args.api_key_env, None)
        client = runner.OpenAICompatible(
            base_url=args.base_url,
            model=campaign["model"],
            api_key=key,
            timeout_s=runner.DEFAULT_REQUEST_TIMEOUT_S,
            temperature=args.temperature,
            stream=args.stream,
        )
    try:
        args.output.mkdir(mode=0o700, parents=True, exist_ok=False)
    except FileExistsError:
        parser.error("native launcher requires a fresh output directory")
    runtime = args.output.resolve() / "runtime"
    runner.export_runtime(
        cell, release, runtime, timeout_s=runner.DEFAULT_TOOL_TIMEOUT_S
    )
    prepared = {
        "status": "prepared",
        "runtime": str(runtime),
        "cell_id": cell["cell_id"],
        "campaign_file_sha256": _sha_file(args.campaign),
        "dry_run": args.dry_run,
    }
    native_episode._write_once(args.output / "prepared.json", prepared)
    if args.dry_run:
        print(json.dumps(prepared, sort_keys=True))
        return 0
    run = run_prepared_native_mini_swe(
        runtime=runtime,
        cell=cell,
        client=client,
        attempt_id=cell["cell_id"] + "-native-0001",
        evas_command=args.evas_command,
        docker_image=_select_docker_image(condition, None),
        campaign_file_sha256=prepared["campaign_file_sha256"],
    )
    print(
        json.dumps(
            {
                "status": run.result.primary_outcome,
                "terminal_reason": run.result.terminal_reason,
                "runtime": str(runtime),
                "artifact_path": str(run.artifact_path) if run.artifact_path else None,
            },
            sort_keys=True,
        )
    )
    return 0 if run.artifact_path else 1


if __name__ == "__main__":
    raise SystemExit(main())
