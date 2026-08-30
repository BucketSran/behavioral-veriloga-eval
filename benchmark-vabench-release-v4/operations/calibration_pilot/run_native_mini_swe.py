#!/usr/bin/env python3
"""Opt-in single-cell native mini-swe launcher; legacy campaigns stay unchanged."""

from __future__ import annotations

from pathlib import Path
from copy import deepcopy
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
    EpisodeContext,
    FrozenSubmission,
    JsonlTrajectoryRecorder,
    ProposalNormalizationError,
    ToolRegistry,
    backend_profile_sha256,
)
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


def _backend_profile():
    return {
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


class _RecordedClient:
    """Record decoded API exchanges, never auth headers or provider credentials."""

    def __init__(self, client, record, context):
        self.client, self.record, self.context = client, record, context
        self.model = client.model
        self.calls = 0

    def complete(self, messages, max_tokens, tools, *, timeout_s=None):
        self.calls += 1
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
            },
        )
        try:
            response = self.client.complete(
                messages, max_tokens, tools, timeout_s=timeout_s
            )
        except Exception as exc:
            self.record(
                "provider_failure", {**identity, "error_type": type(exc).__name__}
            )
            message = _redact(str(exc), getattr(self.client, "api_key", ""))
            raise RuntimeError(f"provider {type(exc).__name__}: {message}") from None
        self.record("provider_response", {**identity, "response": deepcopy(response)})
        return _redact(response, getattr(self.client, "api_key", ""))


class _RecordedEnvironment(MiniSweBashEnvironmentBridge):
    def __init__(self, *, record, **kwargs):
        super().__init__(**kwargs)
        self.record = record

    def step(self, action, capability):
        self.record("tool_request", action.to_document())
        result = super().step(action, capability)
        if hasattr(result, "observation"):
            self.record(
                "tool_result",
                {
                    "action_id": action.action_id,
                    "observation": result.observation.to_document(),
                },
            )
        return result


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
    docker_image: str = mini.DEFAULT_DOCKER_IMAGE,
    allow_insecure_test_sandbox: bool = False,
    campaign_file_sha256: str | None = None,
) -> native_episode.NativeEpisodeRun:
    """Run an exclusively owned fresh exported G2 Agentic DUT/bugfix cell.

    This API does not attest that a caller's export came from the sealed release.
    Use the CLI for exporter/config composition. No resume or automatic retry.
    """
    if (
        cell.get("mode") != "G2"
        or cell.get("form") not in {"dut", "bugfix"}
        or cell.get("experimental_arm") != "Agentic"
        or cell.get("executable_feedback") is not True
    ):
        raise ValueError(
            "native launcher currently supports G2 Agentic DUT/bugfix only"
        )
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
    context = EpisodeContext(
        cell["cell_id"], attempt_id, cell["task_id"], "Agentic", None
    )
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
        environment = mini.VaBenchBashEnvironment(
            runtime,
            timeout_s=tool_timeout_s,
            sandbox_backend="none" if allow_insecure_test_sandbox else "docker",
            evas_command=evas_command,
            docker_image=docker_image,
            deadline_monotonic=deadline,
            submission_gate=runner.submission_artifact_gate,
            candidate_artifacts=runner.expected_candidate_artifacts(runtime),
        )
        environment.preflight()
        _, submitted, _, _ = mini.load_mini_swe()
        environment.bind_submitted_exception(submitted)
        prompt = (runtime / "agent_prompt.txt").read_text()
        backend = _backend_profile()
        manifest = {
            "schema_version": "vaevas-native-launcher-manifest-v1",
            "cell": deepcopy(cell),
            "attempt_id": attempt_id,
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
            "environment": environment.serialize()["info"]["config"]["environment"],
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
            "raw_trace_scope": "decoded_provider_exchanges_and_bounded_tool_observations",
        }
        config_sha = runner.RESULT_PROTOCOL.canonical_sha256(manifest)
        public_profile = public_validation.build_public_validation_profile(
            environment=environment,
            release=release,
            campaign_config_sha256=config_sha,
            allow_insecure_test_sandbox=allow_insecure_test_sandbox,
        )
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
        model = mini.VaBenchMiniModel(
            _RecordedClient(client, record, context),
            per_turn_max_tokens=runner.cell_per_turn_max_tokens(cell),
            request_timeout_s=request_timeout_s,
            deadline_monotonic=deadline,
            usage_parser=runner.provider_output_usage,
            response_metadata=runner.provider_response_metadata,
        )
        policy = NativeMiniSwePolicy(
            model=model, prompt=prompt, action_id_prefix=attempt_id
        )
        paused = False

        def quiesce():
            nonlocal paused
            if paused or allow_insecure_test_sandbox:
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

        bridge = _RecordedEnvironment(
            record=record,
            legacy_environment=environment,
            task_payload={"prompt": prompt},
            candidate_tree_sha256=candidate_hash,
            freeze_submission=freeze,
            submitted_exception_types=(submitted,),
        )
        run = native_episode.run_native_episode(
            runtime=runtime,
            context=context,
            policy=policy,
            environment=bridge,
            tool_registry=ToolRegistry(
                [mini_swe_bash_tool_descriptor(allowed_conditions=["Agentic"])]
            ),
            backend_profile_sha256=backend_profile_sha256(backend),
            public_validation_profile=public_profile,
            final_test_profile=final_profile,
            command=command,
            timeout_s=judge_timeout_s,
            evas_command=evas_command,
            deadline_monotonic=deadline,
            deadline_finalizer=deadline_finalize,
        )
        native_episode._write_once(
            directory / "result.json",
            {
                "schema_version": "vaevas-native-launcher-result-v1",
                "manifest_sha256": _sha_file(directory / "manifest.json"),
                "private_events_sha256": _sha_file(trace_path),
                "private_events_tail_sha256": trace.tail_sha256,
                "trajectory_sha256": _sha_file(run.trajectory_path),
                "artifact_file_sha256": _sha_file(run.artifact_path)
                if run.artifact_path
                else None,
                "artifact_path": str(run.artifact_path.relative_to(runtime))
                if run.artifact_path
                else None,
                "model_telemetry": model.serialize()["info"],
                "evas_invocations": environment.evas_invocations,
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

    def __init__(self, *, model, prompt: str, action_id_prefix: str):
        _, _, format_error, formatter = mini.load_mini_swe()
        model.bind_mini_swe_protocol(formatter, format_error)
        self._format_error = format_error
        self.model = model
        self.messages = [
            model.format_message(role="system", content=mini.SYSTEM_PROMPT),
            model.format_message(
                role="user", content=prompt.rstrip() + "\n\n" + mini.BASH_CONTRACT
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
    if cell.get("experimental_arm") != "Agentic" or cell["form"] not in {
        "dut",
        "bugfix",
    }:
        parser.error("native launcher currently supports G2 Agentic DUT/bugfix only")
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
