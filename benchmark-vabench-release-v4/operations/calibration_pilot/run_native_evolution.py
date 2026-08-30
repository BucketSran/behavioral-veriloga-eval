#!/usr/bin/env python3
"""Opt-in native Evolution runner for vaEVAS candidate-only branches.

This composition layer runs generation branches through the same typed
controller/tool/trajectory path as native episodes, freezes only candidate
snapshots during evolution, then scores exactly the selected candidate in a
fresh final runtime.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import threading
import time
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import mini_swe_vabench as mini  # noqa: E402
import final_replay  # noqa: E402
import native_episode  # noqa: E402
import public_validation  # noqa: E402
import run_campaign as runner  # noqa: E402
from run_native_mini_swe import _RecordedClient, _RecordedEnvironment, _backend_profile, _redact  # noqa: E402

from runners.agent_harness.authority_profiles import (  # noqa: E402
    final_test_profile_sha256,
    public_validation_profile_sha256,
)
from runners.agent_harness.backend_profile import backend_profile_sha256  # noqa: E402
from runners.agent_harness.backends.mini_swe import (  # noqa: E402
    mini_swe_bash_tool_descriptor,
)
from runners.agent_harness.backends.reasoning import ReasoningPolicy  # noqa: E402
from runners.agent_harness.controller import EpisodeController  # noqa: E402
from runners.agent_harness.contracts import CandidateTerminalHandler  # noqa: E402
from runners.agent_harness.evolution_manifest import (  # noqa: E402
    evolution_manifest_sha256,
)
from runners.agent_harness.evolution_runtime import (  # noqa: E402
    EvolutionBranchRequest,
    EvolutionRuntimeResult,
    run_evolution_rounds,
)
from runners.agent_harness.evidence_export import EvidenceExportError  # noqa: E402
from runners.agent_harness.evidence_export import _usage_summary as private_event_usage_summary  # noqa: E402
from runners.agent_harness.state import (  # noqa: E402
    CandidateEpisodeResult,
    CandidateSnapshot,
    EpisodeContext,
    FinalJudgment,
    FrozenSubmission,
    Observation,
)
from runners.agent_harness.tool_registry import ToolRegistry  # noqa: E402
from runners.agent_harness.tools.offline_docs_tool import OfflineDocsTool, docs_prompt  # noqa: E402
from runners.agent_harness.trajectory import (  # noqa: E402
    JsonlTrajectoryRecorder,
    read_trajectory,
    validate_candidate_trajectory_semantics,
)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class NativeEvolutionBranch:
    """One frozen branch/model entry in an Evolution roster."""

    branch_id: str
    model_ref: str
    backend_profile_sha256: str
    client_factory: Callable[[], Any]


@dataclass(frozen=True, slots=True)
class PublicValidationResult:
    """Public-only signal used by Evolution selection."""

    status: str
    sim_success: float
    event_sha256: str


@dataclass(frozen=True, slots=True)
class NativeEvolutionOps:
    """Injectable external operations; defaults are production adapters."""

    export_runtime: Callable[..., None] | None = None
    make_branch_environment: Callable[..., Any] | None = None
    validate_public_candidate: Callable[..., PublicValidationResult] | None = None
    build_public_validation_profile: Callable[..., Mapping[str, Any]] | None = None
    build_final_test_profile: Callable[..., Mapping[str, Any]] | None = None
    make_final_judge: Callable[..., Any] | None = None
    quiesce_environment: Callable[..., None] | None = None


@dataclass(frozen=True, slots=True)
class NativeEvolutionRun:
    """Terminal result for one native Evolution run."""

    manifest: Mapping[str, Any]
    manifest_sha256: str
    evolution_result: EvolutionRuntimeResult
    selected_candidate: Mapping[str, Any]
    final_judgment: FinalJudgment
    score_sidecar_receipt: Mapping[str, Any] | None
    output_dir: Path
    final_runtime: Path


class _Submitted(Exception):
    pass


class _PrivateJsonlRecorder:
    def __init__(self, path: Path, *, context: EpisodeContext) -> None:
        self.path = path
        self.events: list[dict[str, Any]] = []
        self.context = context
        self.credential = ""
        self._sink = JsonlTrajectoryRecorder(path)

    def record(self, event_type: str, payload: Mapping[str, Any]) -> None:
        safe_payload = _redact(_json_ready(dict(payload)), self.credential)
        self._sink.append(
            context=self.context,
            actor="native_evolution",
            event_type=event_type,
            visibility="trusted",
            payload=safe_payload,
        )
        event = read_trajectory(self.path)[-1]
        self.events.append(event)

    def close(self) -> None:
        with self.path.open("rb") as handle:
            os.fsync(handle.fileno())
        self.path.chmod(0o400)

    def count(self, event_type: str) -> int:
        return sum(1 for event in self.events if event["event_type"] == event_type)


class _CandidateSnapshotHandler(CandidateTerminalHandler):
    def __init__(
        self,
        *,
        runtime: Path,
        output_path: Path,
        context: EpisodeContext,
        environment: Any,
        ops: NativeEvolutionOps,
        allow_insecure_test_sandbox: bool,
    ) -> None:
        self.runtime = runtime
        self.output_path = output_path
        self.context = context
        self.environment = environment
        self.ops = ops
        self.allow_insecure_test_sandbox = allow_insecure_test_sandbox

    def capture_candidate(
        self,
        *,
        context: EpisodeContext,
        expected_candidate_tree_sha256: str,
        terminal_reason: str,
    ) -> CandidateSnapshot:
        if context != self.context:
            raise ValueError("candidate snapshot context mismatch")
        _quiesce = self.ops.quiesce_environment or _default_quiesce_environment
        _quiesce(
            environment=self.environment,
            allow_insecure_test_sandbox=self.allow_insecure_test_sandbox,
        )
        gate = runner.submission_artifact_gate(self.runtime)
        if not gate["passed"]:
            raise ValueError("candidate submission gate rejected the branch")
        tree_sha256 = _candidate_tree_sha256(self.runtime)
        if tree_sha256 != expected_candidate_tree_sha256:
            raise ValueError("candidate snapshot does not match terminal hash")
        artifacts = tuple(sorted(gate["expected_artifacts"]))
        store = _store_candidate_snapshot(
            runtime=self.runtime,
            destination=self.output_path / "candidate-store" / tree_sha256,
            artifacts=artifacts,
            tree_sha256=tree_sha256,
            terminal_reason=terminal_reason,
        )
        return CandidateSnapshot(store["tree_sha256"], tuple(store["artifacts"]))

    def complete(
        self,
        *,
        context: EpisodeContext,
        candidate_snapshot: CandidateSnapshot,
        terminal_reason: str,
    ) -> CandidateEpisodeResult:
        return CandidateEpisodeResult(
            context=context,
            terminal_reason=terminal_reason,
            candidate_snapshot=candidate_snapshot,
            incidents=(),
        )


class _SharedPublicValidator:
    def __init__(
        self,
        *,
        cell: Mapping[str, Any],
        release: Path,
        runtime: Path,
        profile: Mapping[str, Any],
        timeout_s: int,
        evas_command: str,
        allow_insecure_test_sandbox: bool,
        ops: NativeEvolutionOps,
        environment: Any | None = None,
    ) -> None:
        self.cell = dict(cell)
        self.release = release
        self.runtime = runtime
        self.profile = dict(profile)
        self.timeout_s = timeout_s
        self.evas_command = evas_command
        self.allow_insecure_test_sandbox = allow_insecure_test_sandbox
        self.ops = ops
        self.lock = threading.Lock()
        self.environment: Any | None = environment
        self._invalidated = False

    def validate(
        self,
        *,
        request: EvolutionBranchRequest,
        snapshot: CandidateSnapshot,
        candidate_store: Path,
        context: EpisodeContext,
    ) -> PublicValidationResult:
        with self.lock:
            if self._invalidated:
                raise ValueError("public validation authority is invalidated")
            try:
                validate = self.ops.validate_public_candidate
                if validate is not None:
                    try:
                        result = _normalize_public_validation_result(
                            validate(
                                request=request,
                                snapshot=snapshot,
                                candidate_store=candidate_store,
                                context=context,
                                validator=self,
                            )
                        )
                    except Exception:
                        self._invalidated = True
                        raise
                    self._archive_public_receipt(
                        request=request,
                        snapshot=snapshot,
                        candidate_store=candidate_store,
                        context=context,
                        result=result,
                        observation=None,
                    )
                    return result
                if self.environment is None:
                    _export_runtime(self.ops, self.cell, self.release, self.runtime, self.timeout_s)
                    self.environment = _default_make_branch_environment(
                        runtime=self.runtime,
                        cell=self.cell,
                        branch=None,
                        context=context,
                        timeout_s=self.timeout_s,
                        evas_command=self.evas_command,
                        sandbox_backend="docker",
                        docker_image=mini.DEFAULT_DOCKER_IMAGE,
                        executable_feedback=True,
                        deadline_monotonic=request.deadline_monotonic,
                        submitted_exception=_Submitted,
                    )
                    _preflight(self.environment)
                _replace_submission_from_store(
                    source=candidate_store / "submission",
                    runtime=self.runtime,
                    artifacts=snapshot.artifacts,
                )
                validator = public_validation.PublicEvasValidator(
                    environment=self.environment,
                    context=context,
                    public_validation_profile=dict(self.profile),
                    allow_insecure_test_sandbox=self.allow_insecure_test_sandbox,
                )
                try:
                    observation = validator.validate(candidate_tree_sha256=snapshot.tree_sha256)
                except Exception:
                    self._invalidated = True
                    raise
                result = PublicValidationResult(
                    status=observation.status,
                    sim_success=1.0 if observation.status == "succeeded" else 0.0,
                    event_sha256=_canonical_sha256(observation.to_document()),
                )
                self._archive_public_receipt(
                    request=request,
                    snapshot=snapshot,
                    candidate_store=candidate_store,
                    context=context,
                    result=result,
                    observation=observation,
                )
                return result
            except Exception:
                self._invalidated = True
                raise

    def close(self) -> None:
        if self.environment is not None:
            close = getattr(self.environment, "close", None)
            if callable(close):
                close()
            self.environment = None

    def _archive_public_receipt(
        self,
        *,
        request: EvolutionBranchRequest,
        snapshot: CandidateSnapshot,
        candidate_store: Path,
        context: EpisodeContext,
        result: PublicValidationResult,
        observation: Observation | None,
    ) -> None:
        _write_once_json(
            request.output_path / "public-validation.json",
            {
                "schema_version": "vaevas-native-evolution-public-validation-receipt-v1",
                "manifest_sha256": request.manifest_sha256,
                "branch_id": request.branch_id,
                "round_index": request.round_index,
                "candidate_tree_sha256": snapshot.tree_sha256,
                "candidate_store_sha256": _candidate_store_manifest_sha(candidate_store),
                "context": _context_document(context),
                "profile_input_identity_sha256": public_validation.profile_input_identity_sha256(
                    profile_sha256=public_validation_profile_sha256(self.profile),
                    input_kind="candidate_tree",
                    input_sha256=snapshot.tree_sha256,
                    attempt_id=context.attempt_id,
                    task_id=context.task_id,
                ),
                "result": {
                    "status": result.status,
                    "sim_success": result.sim_success,
                    "event_sha256": result.event_sha256,
                },
                "observation": observation.to_document() if observation else None,
            },
        )


def build_native_evolution_manifest(
    *,
    manifest_id: str,
    condition: str,
    branches: Sequence[NativeEvolutionBranch],
    budgets: Mapping[str, int],
    rounds: int,
    tool_registry_sha256: str,
    public_validation_profile_sha256_value: str,
    final_test_profile_sha256_value: str,
) -> dict[str, Any]:
    per_branch = _budget_map(budgets)
    total = {
        key: int(value) * len(branches) * int(rounds)
        for key, value in per_branch.items()
    }
    manifest = {
        "schema_version": "vaevas-evolution-manifest-v1",
        "manifest_id": manifest_id,
        "condition": condition,
        "benchmark_release": "benchmarkv4-r53",
        "evaluator": {"engine": "evas", "version": "0.8.7"},
        "rounds": int(rounds),
        "branch_roster": [
            {
                "branch_id": branch.branch_id,
                "backend_profile_sha256": branch.backend_profile_sha256,
                "model_ref": branch.model_ref,
            }
            for branch in branches
        ],
        "budgets": {"per_branch": per_branch, "total": total},
        "tool_registry_sha256": tool_registry_sha256,
        "public_validation_profile_sha256": public_validation_profile_sha256_value,
        "final_test_profile_sha256": final_test_profile_sha256_value,
        "memory_policy": "episode_local_public_only",
        "round_barrier_policy": "strict_all_branches_or_declared_timeout",
        "branch_timeout_policy": "classify_branch_timeout_and_seal_round",
        "global_deadline_policy": "discard_unsealed_round_use_prior_incumbent",
        "selection_rule": {
            "metrics": [{"name": "sim_success", "direction": "maximize"}],
            "tiebreak": ["candidate_tree_sha256", "candidate_id"],
        },
        "final_submission_policy": "freeze_selected_candidate_then_final_test_once",
    }
    evolution_manifest_sha256(manifest)
    return manifest


def run_native_evolution(
    *,
    cell: Mapping[str, Any],
    release: Path,
    output_dir: Path,
    branches: Sequence[NativeEvolutionBranch],
    public_validation_profile: Mapping[str, Any] | None = None,
    final_test_profile: Mapping[str, Any] | None = None,
    command: str,
    evas_command: str,
    rounds: int,
    max_steps: int,
    budgets: Mapping[str, int],
    timeout_s: int = 120,
    request_timeout_s: float | None = None,
    branch_sandbox_backend: str = "docker",
    branch_docker_image: str | None = None,
    allow_insecure_test_sandbox: bool = False,
    deadline_monotonic: float | None = None,
    campaign_file_sha256: str | None = None,
    max_workers: int | None = None,
    docs_corpus: Any | None = None,
    ops: NativeEvolutionOps | None = None,
) -> NativeEvolutionRun:
    """Run candidate-only Evolution and final-score the selected candidate once."""
    ops = ops or NativeEvolutionOps()
    condition = str(cell.get("experimental_arm") or "Evolution+EVAS")
    docs_tool = None
    if docs_corpus is not None:
        if condition != "AlphaApollo-Evolution+EVAS":
            raise ValueError("synthetic Evolution docs require AlphaApollo-Evolution+EVAS")
        docs_tool = OfflineDocsTool(docs_corpus, condition=condition)
    output_dir = output_dir.resolve()
    if output_dir.exists() or output_dir.is_symlink():
        raise RuntimeError("native evolution output_dir must be fresh")
    output_dir.mkdir(mode=0o700, parents=True)
    if not branches:
        raise ValueError("branches must not be empty")
    descriptors = [mini_swe_bash_tool_descriptor(allowed_conditions=[condition])]
    if docs_tool is not None:
        descriptors.append(docs_tool.descriptor)
    tool_registry = ToolRegistry(descriptors)
    _validate_branch_contracts(branches)
    config_doc = _native_evolution_config_document(
        cell=cell,
        release=release,
        output_dir=output_dir,
        branches=branches,
        condition=condition,
        budgets=budgets,
        rounds=rounds,
        max_steps=max_steps,
        timeout_s=timeout_s,
        request_timeout_s=request_timeout_s,
        branch_sandbox_backend=branch_sandbox_backend,
        branch_docker_image=branch_docker_image or mini.DEFAULT_NO_EVAS_DOCKER_IMAGE,
        command=command,
        evas_command=evas_command,
        campaign_file_sha256=campaign_file_sha256,
    )
    if docs_tool is not None:
        config_doc["extensions"] = {"offline_docs": {
            "profile": docs_tool.profile, "profile_sha256": docs_corpus.profile_sha256,
            "intervention": "synthetic-frozen-docs-v1", "tool_name": "vaevas_docs_search",
        }}
    config_doc["declared_information_surface"] = runner.declared_information_surface(
        condition, evolution=True, extensions=config_doc.get("extensions"),
    )
    campaign_config_sha = _canonical_sha256(config_doc)
    _write_once_json(output_dir / "setup-request.json", {
        "schema_version": "vaevas-native-evolution-setup-v1", "config": config_doc,
        "campaign_file_sha256": campaign_file_sha256,
    })
    prepared_public_environment: Any | None = None
    prepared_final_runtime = False
    try:
        if public_validation_profile is None:
            prepared_public_environment = _prepare_public_validation_environment(
                ops=ops,
                cell=cell,
                release=release,
                runtime=output_dir / "public-validation-runtime",
                timeout_s=timeout_s,
                evas_command=evas_command,
                deadline_monotonic=deadline_monotonic,
                allow_insecure_test_sandbox=allow_insecure_test_sandbox,
            )
            builder = ops.build_public_validation_profile or public_validation.build_public_validation_profile
            public_validation_profile = builder(
                environment=prepared_public_environment,
                release=release,
                campaign_config_sha256=campaign_config_sha,
                allow_insecure_test_sandbox=allow_insecure_test_sandbox,
            )
        if final_test_profile is None:
            final_runtime = output_dir / "final-runtime"
            _export_runtime(ops, cell, release, final_runtime, timeout_s)
            prepared_final_runtime = True
            builder = ops.build_final_test_profile or final_replay.build_final_test_profile
            final_test_profile = builder(
                runtime=final_runtime,
                release=release,
                campaign_config_sha256=campaign_config_sha,
                command=command,
                timeout_s=timeout_s,
                evas_command=evas_command,
            )
        public_profile = dict(public_validation_profile)
        final_profile = dict(final_test_profile)
        _validate_profile_binding(
            profile=public_profile,
            kind="public validation",
            campaign_config_sha256=campaign_config_sha,
        )
        _validate_profile_binding(
            profile=final_profile,
            kind="final test",
            campaign_config_sha256=campaign_config_sha,
        )
        public_sha = public_validation_profile_sha256(public_profile)
        final_sha = final_test_profile_sha256(final_profile)
        _write_once_json(output_dir / "public-validation-profile.json", public_profile)
        _write_once_json(output_dir / "final-test-profile.json", final_profile)
        manifest = build_native_evolution_manifest(
            manifest_id=str(cell.get("cell_id") or cell.get("task_id") or output_dir.name),
            condition=condition,
            branches=branches,
            budgets=budgets,
            rounds=rounds,
            tool_registry_sha256=tool_registry.registry_sha256,
            public_validation_profile_sha256_value=public_sha,
            final_test_profile_sha256_value=final_sha,
        )
        manifest_sha = evolution_manifest_sha256(manifest)
        _write_once_json(
            output_dir / "request.json",
            {
                "schema_version": "vaevas-native-evolution-request-v1",
                "manifest_sha256": manifest_sha,
                "campaign_config_sha256": campaign_config_sha,
                "campaign_file_sha256": campaign_file_sha256,
                "cell": _json_ready(dict(cell)),
                "rounds": rounds,
                "branch_count": len(branches),
                "config": config_doc,
                "public_validation_profile_sha256": public_sha,
                "final_test_profile_sha256": final_sha,
            },
        )
        branch_by_id = {branch.branch_id: branch for branch in branches}
        public_checker = _SharedPublicValidator(
            cell=cell,
            release=release,
            runtime=output_dir / "public-validation-runtime",
            profile=public_profile,
            timeout_s=timeout_s,
            evas_command=evas_command,
            allow_insecure_test_sandbox=allow_insecure_test_sandbox,
            ops=ops,
            environment=prepared_public_environment,
        )
    except BaseException as exc:
        if prepared_public_environment is not None:
            try:
                prepared_public_environment.close()
            except Exception as cleanup_exc:
                _write_once_json(output_dir / "public-cleanup-incident.json", {
                    "error_type": type(cleanup_exc).__name__,
                    "message_sha256": hashlib.sha256(str(cleanup_exc).encode()).hexdigest(),
                })
        if isinstance(exc, Exception):
            _write_failure_final_result(
                output_dir=output_dir, manifest_sha256=None,
                campaign_config_sha256=campaign_config_sha, error=exc, status="setup_failed",
            )
        raise

    def branch_callback(request: EvolutionBranchRequest) -> Mapping[str, Any]:
        branch = branch_by_id[request.branch_id]
        return _run_branch(
            request=request,
            branch=branch,
            cell=cell,
            release=release,
            condition=condition,
            tool_registry=tool_registry,
            public_checker=public_checker,
            public_validation_profile_sha256_value=public_sha,
            timeout_s=timeout_s,
            request_timeout_s=request_timeout_s,
            branch_sandbox_backend=branch_sandbox_backend,
            branch_docker_image=branch_docker_image,
            allow_insecure_test_sandbox=allow_insecure_test_sandbox,
            max_steps=max_steps,
            docs_corpus=docs_corpus,
            ops=ops,
        )

    try:
        evolution_result = run_evolution_rounds(
            manifest=manifest,
            output_dir=output_dir / "evolution",
            branch_callback=branch_callback,
            deadline_monotonic=deadline_monotonic,
            max_workers=max_workers,
        )
    except Exception as exc:
        _write_failure_final_result(
            output_dir=output_dir,
            manifest_sha256=manifest_sha,
            campaign_config_sha256=campaign_config_sha,
            error=exc,
        )
        raise RuntimeError("native evolution produced no selected candidate") from exc
    finally:
        try:
            public_checker.close()
        except Exception as exc:
            _write_once_json(output_dir / "public-cleanup-incident.json", {
                "error_type": type(exc).__name__,
                "message_sha256": hashlib.sha256(str(exc).encode()).hexdigest(),
            })
            if "evolution_result" in locals():
                _write_failure_final_result(
                    output_dir=output_dir, manifest_sha256=manifest_sha,
                    campaign_config_sha256=campaign_config_sha, error=exc,
                    evolution_result=evolution_result, status="public_cleanup_failed",
                )
                raise
    if evolution_result.selected_candidate is None:
        _write_failure_final_result(
            output_dir=output_dir,
            manifest_sha256=manifest_sha,
            campaign_config_sha256=campaign_config_sha,
            error=RuntimeError("no selected candidate"),
            evolution_result=evolution_result,
        )
        raise RuntimeError("native evolution produced no selected candidate")
    selected = dict(evolution_result.selected_candidate)
    final_runtime = output_dir / "final-runtime"
    final_started = time.monotonic()
    try:
        final_judgment, receipt = _score_selected_candidate(
            selected_candidate=selected,
            branches_dir=output_dir / "evolution" / "branches",
            cell=cell, release=release, runtime=final_runtime,
            final_test_profile=final_profile, command=command,
            timeout_s=timeout_s, evas_command=evas_command,
            ops=ops, runtime_prepared=prepared_final_runtime,
        )
    except Exception as exc:
        _write_failure_final_result(
            output_dir=output_dir, manifest_sha256=manifest_sha,
            campaign_config_sha256=campaign_config_sha, error=exc,
            evolution_result=evolution_result, selected_candidate=selected,
            status="final_failed",
        )
        raise
    _write_once_json(
        output_dir / "final-result.json",
        {
            "schema_version": "vaevas-native-evolution-final-result-v1",
            "status": "completed",
            "manifest_sha256": manifest_sha,
            "campaign_config_sha256": campaign_config_sha,
            "selected_candidate": selected,
            "final_judgment": {
                "status": final_judgment.status,
                "judge_engine": final_judgment.judge_engine,
                "score": final_judgment.score,
                "submission_tree_sha256": final_judgment.submission_tree_sha256,
            },
            "score_sidecar_receipt": _json_ready(receipt),
            "branch_usage": _json_ready(evolution_result.usage),
            "branch_record_count": len(evolution_result.branch_records),
            "final_elapsed_s": time.monotonic() - final_started,
            **_terminal_failure_fields("completed", final_judgment=final_judgment),
            **_evolution_evidence_summary(output_dir),
        },
    )
    return NativeEvolutionRun(
        manifest=manifest,
        manifest_sha256=manifest_sha,
        evolution_result=evolution_result,
        selected_candidate=selected,
        final_judgment=final_judgment,
        score_sidecar_receipt=receipt,
        output_dir=output_dir,
        final_runtime=final_runtime,
    )


def _run_branch(
    *,
    request: EvolutionBranchRequest,
    branch: NativeEvolutionBranch,
    cell: Mapping[str, Any],
    release: Path,
    condition: str,
    tool_registry: ToolRegistry,
    public_checker: _SharedPublicValidator,
    public_validation_profile_sha256_value: str,
    timeout_s: int,
    request_timeout_s: float | None,
    branch_sandbox_backend: str,
    branch_docker_image: str | None,
    allow_insecure_test_sandbox: bool,
    max_steps: int,
    docs_corpus: Any | None,
    ops: NativeEvolutionOps,
) -> Mapping[str, Any]:
    runtime = request.output_path / "runtime"
    context = EpisodeContext(
        episode_id=f"{request.manifest_sha256}/round-{request.round_index:04d}",
        attempt_id=f"{request.branch_id}-round-{request.round_index:04d}",
        task_id=str(cell.get("task_id") or ""),
        condition=condition,
        max_steps=max_steps,
        budget_limits=dict(request.allowance),
    )
    recorder = _PrivateJsonlRecorder(request.output_path / "private-events.jsonl", context=context)
    environment = None
    recorded_client = None
    public_validation_calls = 0
    controller_closed_environment = False
    started = time.monotonic()
    try:
        docs_tool = OfflineDocsTool(docs_corpus, condition=condition) if docs_corpus is not None else None
        generation_cell = _branch_generation_cell(cell)
        _export_runtime(ops, generation_cell, release, runtime, timeout_s)
        make_environment = ops.make_branch_environment or _default_make_branch_environment
        environment = make_environment(
            runtime=runtime,
            cell=generation_cell,
            branch=branch,
            context=context,
            timeout_s=timeout_s,
            evas_command="evas",
            sandbox_backend=branch_sandbox_backend,
            docker_image=branch_docker_image or mini.DEFAULT_NO_EVAS_DOCKER_IMAGE,
            executable_feedback=False,
            deadline_monotonic=request.deadline_monotonic,
            submitted_exception=_Submitted,
        )
        _preflight(environment)
        _write_once_json(request.output_path / "branch-runtime.json", {
            "manifest_sha256": request.manifest_sha256,
            "branch_id": request.branch_id, "round_index": request.round_index,
            "model_ref": branch.model_ref, "backend_profile_sha256": branch.backend_profile_sha256,
            "requested_image": branch_docker_image or mini.DEFAULT_NO_EVAS_DOCKER_IMAGE,
            "observed_image_id": getattr(environment, "docker_image_id", None),
            "sandbox_backend": branch_sandbox_backend, "executable_feedback": False,
            "logical_condition": condition, "exported_experimental_arm": "Agent-No-EVAS",
        })
        client = branch.client_factory()
        if getattr(client, "model", None) != branch.model_ref:
            raise ValueError("branch client model must match roster model_ref")
        recorder.credential = str(getattr(client, "api_key", "") or "")
        recorded_client = _RecordedClient(client, recorder.record, context)
        toolset = tool_registry.resolve(condition_id=condition, model_visible=True)
        policy = ReasoningPolicy(
            client=recorded_client,
            context=context,
            proposal_format="native_tool_calls",
            tools=_provider_tools(toolset.capabilities),
            accepted_tool_names=toolset.accepted_tool_names,
            max_tokens=_cell_max_tokens(cell),
            timeout_s=request_timeout_s,
            deadline_monotonic=request.deadline_monotonic,
            source_backend=f"alphaapollo/evolution-reasoning:{branch.model_ref}",
        )

        def candidate_hash() -> str:
            return _candidate_tree_sha256(runtime)

        bridge = _RecordedEnvironment(
            record=recorder.record,
            legacy_environment=environment,
            task_payload=_branch_task_payload(
                runtime=runtime,
                context=context,
                request=request,
                docs_profile=docs_tool.profile if docs_tool is not None else None,
            ),
            docs_tool=docs_tool,
            candidate_tree_sha256=candidate_hash,
            freeze_submission=_final_freeze_forbidden,
            submitted_exception_types=(_Submitted,),
        )
        handler = _CandidateSnapshotHandler(
            runtime=runtime,
            output_path=request.output_path,
            context=context,
            environment=environment,
            ops=ops,
            allow_insecure_test_sandbox=allow_insecure_test_sandbox,
        )
        trajectory_path = request.output_path / "candidate-trajectory.jsonl"
        controller_kwargs: dict[str, Any] = {
            "policy": policy,
            "environment": bridge,
            "tool_registry": tool_registry,
            "candidate_terminal_handler": handler,
            "trajectory": JsonlTrajectoryRecorder(trajectory_path),
            "public_validation_profile_sha256": public_validation_profile_sha256_value,
        }
        if request.deadline_monotonic is not None:
            controller_kwargs["deadline_monotonic"] = request.deadline_monotonic
            controller_kwargs["deadline_finalizer"] = lambda: (
                candidate_hash()
                if runner.submission_artifact_gate(runtime)["passed"]
                else None
            )
        result = EpisodeController(**controller_kwargs).run(context)
        controller_closed_environment = True
        events = read_trajectory(trajectory_path)
        if not validate_candidate_trajectory_semantics(events):
            raise RuntimeError("candidate trajectory failed semantic validation")
        if not isinstance(result, CandidateEpisodeResult) or result.failure is not None or result.incidents:
            raise RuntimeError("candidate branch did not produce a usable snapshot")
        candidate_store = request.output_path / "candidate-store" / result.candidate_snapshot.tree_sha256
        if int(request.allowance["public_validation_calls"]) <= 0:
            raise RuntimeError("public validation budget exhausted before checker call")
        public_validation_calls = 1
        validation = public_checker.validate(
            request=request,
            snapshot=result.candidate_snapshot,
            candidate_store=candidate_store,
            context=context,
        )
        status = "completed" if validation.sim_success >= 0.0 else "branch_failed"
        return {
            "candidate_id": _candidate_id(request, result.candidate_snapshot.tree_sha256),
            "candidate_tree_sha256": result.candidate_snapshot.tree_sha256,
            "status": status,
            "public_validation": {
                "profile_sha256": public_validation_profile_sha256_value,
                "metrics": {"sim_success": float(validation.sim_success)}
                if status == "completed"
                else {},
                "event_sha256": validation.event_sha256,
            },
            "usage": _usage(
                recorded_client=recorded_client,
                recorder=recorder,
                public_validation_calls=public_validation_calls,
            ),
        }
    except Exception as exc:
        recorder.record(
            "branch_failure",
            {
                "branch_id": request.branch_id,
                "round_index": request.round_index,
                "error_type": type(exc).__name__,
                "message_sha256": hashlib.sha256(str(exc).encode()).hexdigest(),
            },
        )
        usage = _usage(
            recorded_client=recorded_client,
            recorder=recorder,
            public_validation_calls=public_validation_calls,
            allowance=request.allowance,
        )
        event_sha = _canonical_sha256(
            {
                "schema_version": "vaevas-native-evolution-branch-failure-v1",
                "branch_id": request.branch_id,
                "round_index": request.round_index,
                "error_type": type(exc).__name__,
                "message_sha256": hashlib.sha256(str(exc).encode()).hexdigest(),
            }
        )
        return {
            "candidate_id": f"{request.branch_id}-round-{request.round_index:04d}-failed",
            "candidate_tree_sha256": _failure_candidate_sha(request),
            "status": "branch_failed",
            "public_validation": {
                "profile_sha256": public_validation_profile_sha256_value,
                "metrics": {},
                "event_sha256": event_sha,
            },
            "usage": usage,
        }
    finally:
        if environment is not None and not controller_closed_environment:
            try:
                environment.close()
            except Exception as exc:
                recorder.record("branch_environment_cleanup_failed", {"error_type": type(exc).__name__})
        recorder.close()
        _write_branch_audit_sidecar(
            output_path=request.output_path,
            provider_usage=_safe_private_usage_summary(recorder),
            evidence=_branch_evidence_receipts(request.output_path),
            wall_time_s=time.monotonic() - started,
        )


def _score_selected_candidate(
    *,
    selected_candidate: Mapping[str, Any],
    branches_dir: Path,
    cell: Mapping[str, Any],
    release: Path,
    runtime: Path,
    final_test_profile: Mapping[str, Any],
    command: str,
    timeout_s: int,
    evas_command: str,
    ops: NativeEvolutionOps,
    runtime_prepared: bool = False,
) -> tuple[FinalJudgment, Mapping[str, Any] | None]:
    store = _candidate_store_for_selection(
        branches_dir=branches_dir,
        selected_candidate=selected_candidate,
    )
    if not runtime_prepared:
        _export_runtime(ops, cell, release, runtime, timeout_s)
    _replace_submission_from_store(
        source=store / "submission",
        runtime=runtime,
        artifacts=tuple(json.loads((store / "manifest.json").read_text())["artifacts"]),
    )
    gate = runner.submission_artifact_gate(runtime)
    if not gate["passed"]:
        raise ValueError("selected candidate failed final submission gate")
    manifest = runner.RESULT_PROTOCOL.snapshot_submission(runtime, gate)
    submission = FrozenSubmission(
        manifest["tree_sha256"], tuple(sorted(gate["expected_artifacts"]))
    )
    if submission.tree_sha256 != selected_candidate["candidate_tree_sha256"]:
        raise ValueError("selected candidate drifted before final scoring")
    context = EpisodeContext(
        episode_id=f"{selected_candidate['candidate_id']}/final",
        attempt_id=f"{selected_candidate['candidate_id']}-final",
        task_id=str(cell.get("task_id") or ""),
        condition=str(cell.get("experimental_arm") or "Evolution+EVAS"),
        max_steps=None,
    )
    factory = ops.make_final_judge or native_episode._ProductionFinalJudge
    judge = factory(
        runtime=runtime,
        context=context,
        profile=dict(final_test_profile),
        command=command,
        timeout_s=timeout_s,
        evas_command=evas_command,
    )
    judgment = judge.judge(submission)
    return judgment, getattr(judge, "receipt", None)


def _default_make_branch_environment(
    *,
    runtime: Path,
    cell: Mapping[str, Any],
    branch: NativeEvolutionBranch | None,
    context: EpisodeContext,
    timeout_s: int,
    evas_command: str,
    sandbox_backend: str,
    docker_image: str,
    executable_feedback: bool,
    deadline_monotonic: float | None,
    submitted_exception: type[Exception],
) -> mini.VaBenchBashEnvironment:
    del cell, branch, context
    environment = mini.VaBenchBashEnvironment(
        runtime,
        timeout_s=timeout_s,
        sandbox_backend=sandbox_backend,
        evas_command=evas_command,
        executable_feedback=executable_feedback,
        docker_image=docker_image,
        deadline_monotonic=deadline_monotonic,
        submission_gate=runner.submission_artifact_gate,
        candidate_artifacts=runner.expected_candidate_artifacts(runtime),
    )
    environment.bind_submitted_exception(submitted_exception)
    return environment


def _prepare_public_validation_environment(
    *,
    ops: NativeEvolutionOps,
    cell: Mapping[str, Any],
    release: Path,
    runtime: Path,
    timeout_s: int,
    evas_command: str,
    deadline_monotonic: float | None,
    allow_insecure_test_sandbox: bool,
) -> Any:
    _export_runtime(ops, cell, release, runtime, timeout_s)
    make_environment = ops.make_branch_environment or _default_make_branch_environment
    context = EpisodeContext(
        episode_id=f"{str(cell.get('cell_id') or cell.get('task_id') or 'native-evolution')}/public-validation",
        attempt_id="public-validation-profile-freeze",
        task_id=str(cell.get("task_id") or ""),
        condition=str(cell.get("experimental_arm") or "Evolution+EVAS"),
        max_steps=None,
    )
    environment = make_environment(
        runtime=runtime,
        cell=cell,
        branch=None,
        context=context,
        timeout_s=timeout_s,
        evas_command=evas_command,
        sandbox_backend="docker",
        docker_image=mini.DEFAULT_DOCKER_IMAGE,
        executable_feedback=True,
        deadline_monotonic=deadline_monotonic,
        submitted_exception=_Submitted,
    )
    try:
        _preflight(environment)
    except BaseException:
        environment.close()
        raise
    return environment


def _validate_branch_contracts(branches: Sequence[NativeEvolutionBranch]) -> None:
    expected_backend_sha = backend_profile_sha256(
        _backend_profile("native-reasoning", "native_tool_calls")
    )
    seen: set[str] = set()
    for branch in branches:
        if not branch.branch_id or "/" in branch.branch_id or branch.branch_id in {".", ".."}:
            raise ValueError("branch_id must be a safe non-empty path segment")
        if branch.branch_id in seen:
            raise ValueError("branch_id values must be unique")
        seen.add(branch.branch_id)
        if not SHA256_RE.fullmatch(branch.backend_profile_sha256):
            raise ValueError("backend_profile_sha256 must be a SHA-256 digest")
        if branch.backend_profile_sha256 != expected_backend_sha:
            raise ValueError("backend_profile_sha256 must match native-reasoning profile")
        if not isinstance(branch.model_ref, str) or not branch.model_ref.strip():
            raise ValueError("model_ref must be non-empty")


def _validate_profile_binding(
    *,
    profile: Mapping[str, Any],
    kind: str,
    campaign_config_sha256: str,
) -> None:
    if profile.get("benchmark_release") != "benchmarkv4-r53":
        raise ValueError(f"{kind} profile must bind benchmarkv4-r53")
    evaluator = profile.get("evaluator") or profile.get("judge") or {}
    if not isinstance(evaluator, Mapping) or evaluator.get("engine") != "evas" or evaluator.get("version") != "0.8.7":
        raise ValueError(f"{kind} profile must bind EVAS 0.8.7")
    if profile.get("campaign_config_sha256") != campaign_config_sha256:
        raise ValueError(f"{kind} profile campaign_config_sha256 mismatch")


def _native_evolution_config_document(
    *,
    cell: Mapping[str, Any],
    release: Path,
    output_dir: Path,
    branches: Sequence[NativeEvolutionBranch],
    condition: str,
    budgets: Mapping[str, int],
    rounds: int,
    max_steps: int,
    timeout_s: int,
    request_timeout_s: float | None,
    branch_sandbox_backend: str,
    branch_docker_image: str,
    command: str,
    evas_command: str,
    campaign_file_sha256: str | None,
) -> dict[str, Any]:
    if campaign_file_sha256 is not None and not SHA256_RE.fullmatch(campaign_file_sha256):
        raise ValueError("campaign_file_sha256 must be a SHA-256 digest")
    return {
        "schema_version": "vaevas-native-evolution-config-v1",
        "benchmark_release": "benchmarkv4-r53",
        "evaluator": {"engine": "evas", "version": "0.8.7"},
        "cell": _json_ready(dict(cell)),
        "release": str(release.resolve()),
        "output_dir": str(output_dir),
        "condition": condition,
        "rounds": int(rounds),
        "max_steps": int(max_steps),
        "budgets": _budget_map(budgets),
        "request_timeout_s": request_timeout_s,
        "timeout_s": int(timeout_s),
        "command": command,
        "evas_command": evas_command,
        "campaign_file_sha256": campaign_file_sha256,
        "branch_generation": {
            "sandbox_backend": branch_sandbox_backend,
            "docker_image": branch_docker_image,
            "executable_feedback": False,
            "exported_experimental_arm": "Agent-No-EVAS",
        },
        "branch_roster": [
            {
                "branch_id": branch.branch_id,
                "model_ref": branch.model_ref,
                "backend_profile_sha256": branch.backend_profile_sha256,
                "source_backend": f"alphaapollo/evolution-reasoning:{branch.model_ref}",
                "inference_knobs": {
                    "proposal_format": "native_tool_calls",
                    "max_tokens": _cell_max_tokens(cell),
                },
            }
            for branch in branches
        ],
        "source": _source_identity(),
    }


def _source_identity() -> dict[str, str]:
    sources = {}
    for name in (
        "run_native_evolution.py",
        "run_native_mini_swe.py",
        "native_episode.py",
        "public_validation.py",
        "final_replay.py",
        "mini_swe_vabench.py",
    ):
        path = HERE / name
        sources[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    for path in sorted((REPO / "runners/agent_harness").rglob("*.py")):
        sources[str(path.relative_to(REPO))] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ("run_campaign.py", "result_protocol.py"):
        sources[name] = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
    return sources


def _preflight(environment: Any) -> None:
    preflight = getattr(environment, "preflight", None)
    if callable(preflight):
        preflight()


def _branch_task_payload(
    *,
    runtime: Path,
    context: EpisodeContext,
    request: EvolutionBranchRequest,
    docs_profile: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "task_id": context.task_id,
        "agent_prompt": _read_optional_prompt(runtime / "agent_prompt.txt"),
        "generation_contract": (
            "This is a candidate-only Evolution branch. Bash has no EVAS runtime. "
            "Use the public task and sealed prior candidate code/validation feedback. "
            "Write a complete candidate and call vabench-submit. The coordinator "
            "runs public validation after branch completion; final tests are never feedback."
        ),
        "public_snapshot": _json_ready(request.public_snapshot),
        "prior_candidates": _prior_candidate_payloads(request),
    }
    if docs_profile is not None:
        payload["generation_contract"] += docs_prompt(docs_profile)
    return payload


def _read_optional_prompt(path: Path) -> str | None:
    if not path.is_file() or path.is_symlink():
        return None
    return path.read_text(encoding="utf-8")


def _prior_candidate_payloads(request: EvolutionBranchRequest) -> list[dict[str, Any]]:
    memory = request.public_snapshot.get("memory_snapshot")
    if not isinstance(memory, Mapping):
        return []
    entries = memory.get("entries")
    if not isinstance(entries, (list, tuple)):
        return []
    branches_dir = request.output_path.parents[1]
    payloads = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        tree_sha = entry.get("candidate_tree_sha256")
        candidate_id = entry.get("candidate_id")
        if not isinstance(tree_sha, str) or not SHA256_RE.fullmatch(tree_sha):
            continue
        store = _find_candidate_store(
            branches_dir=branches_dir,
            tree_sha256=tree_sha,
            candidate_id=str(candidate_id) if candidate_id else None,
            current_round_index=request.round_index,
        )
        if store is None:
            continue
        _validated_candidate_store_manifest(
            store,
            expected_tree_sha256=tree_sha,
            expected_candidate_id=str(candidate_id) if candidate_id else None,
        )
        public_feedback = _public_feedback_for_prior_candidate(
            store=store,
            entry=entry,
            tree_sha256=tree_sha,
            candidate_id=str(candidate_id) if candidate_id else None,
            manifest_sha256=request.manifest_sha256,
        )
        payloads.append(
            {
                "candidate_id": candidate_id,
                "candidate_tree_sha256": tree_sha,
                "artifacts": _read_candidate_artifacts(store),
                "public_validation": public_feedback,
            }
        )
    return payloads


def _find_candidate_store(
    *,
    branches_dir: Path,
    tree_sha256: str,
    candidate_id: str | None = None,
    current_round_index: int | None = None,
) -> Path | None:
    if not SHA256_RE.fullmatch(tree_sha256):
        raise ValueError("candidate tree hash must be a SHA-256 digest")
    if candidate_id is None:
        raise ValueError("sealed candidate identity is required for store lookup")
    identity = _parse_candidate_id(candidate_id, tree_sha256=tree_sha256)
    if current_round_index is not None and identity["round_index"] >= current_round_index:
        raise ValueError("prior candidate store must come from a sealed earlier round")
    store = (
        branches_dir
        / f"round-{identity['round_index']:04d}"
        / identity["branch_id"]
        / "candidate-store"
        / tree_sha256
    )
    if not _is_confined(store, branches_dir):
        raise ValueError("candidate store path escaped branches directory")
    if not store.is_dir() or store.is_symlink():
        return None
    _validated_candidate_store_manifest(
        store,
        expected_tree_sha256=tree_sha256,
        expected_candidate_id=candidate_id,
    )
    return store


def _read_candidate_artifacts(store: Path) -> dict[str, str]:
    manifest = _validated_candidate_store_manifest(store)
    artifacts: dict[str, str] = {}
    for relative in manifest.get("artifacts", []):
        safe_relative = _safe_artifact_path(relative)
        path = _confined_existing_file(
            store / "submission",
            safe_relative,
            label="candidate artifact",
        )
        artifacts[relative] = path.read_text(encoding="utf-8")
    return artifacts


def _candidate_store_manifest_sha(candidate_store: Path) -> str:
    _validated_candidate_store_manifest(candidate_store)
    manifest = candidate_store / "manifest.json"
    if not manifest.is_file() or manifest.is_symlink():
        raise ValueError("candidate store manifest is missing")
    return hashlib.sha256(manifest.read_bytes()).hexdigest()


def _public_feedback_for_prior_candidate(
    *,
    store: Path,
    entry: Mapping[str, Any],
    tree_sha256: str,
    candidate_id: str | None,
    manifest_sha256: str,
) -> Mapping[str, Any]:
    summary = _json_ready(entry.get("summary", {}))
    receipt_path = store.parents[1] / "public-validation.json"
    if not receipt_path.is_file() or receipt_path.is_symlink():
        return {"summary": summary}
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema_version") != "vaevas-native-evolution-public-validation-receipt-v1":
        raise ValueError("public validation receipt schema mismatch")
    if receipt.get("manifest_sha256") != manifest_sha256:
        raise ValueError("public validation receipt manifest mismatch")
    if receipt.get("candidate_store_sha256") != _candidate_store_manifest_sha(store):
        raise ValueError("public validation receipt store mismatch")
    identity = _parse_candidate_id(candidate_id, tree_sha256=tree_sha256) if candidate_id else None
    if identity is not None:
        if receipt.get("branch_id") != identity["branch_id"] or receipt.get("round_index") != identity["round_index"]:
            raise ValueError("public validation receipt identity mismatch")
    if receipt.get("candidate_tree_sha256") != tree_sha256:
        raise ValueError("public validation receipt candidate hash mismatch")
    result = receipt.get("result")
    if not isinstance(result, Mapping):
        raise ValueError("public validation receipt result is missing")
    event_sha = result.get("event_sha256")
    if not isinstance(event_sha, str) or not SHA256_RE.fullmatch(event_sha):
        raise ValueError("public validation receipt event hash is invalid")
    source_event_sha = entry.get("source_event_sha256")
    if source_event_sha is not None and source_event_sha != event_sha:
        raise ValueError("public validation receipt event hash mismatch")
    observation = receipt.get("observation")
    if observation is not None:
        if not isinstance(observation, Mapping):
            raise ValueError("public validation receipt observation is invalid")
        if _canonical_sha256(observation) != event_sha:
            raise ValueError("public validation observation hash mismatch")
        if observation.get("candidate_tree_sha256") != tree_sha256:
            raise ValueError("public validation observation candidate hash mismatch")
        validation_profile_sha = observation.get("validation_profile_sha256")
        if validation_profile_sha is not None and not SHA256_RE.fullmatch(str(validation_profile_sha)):
            raise ValueError("public validation observation profile hash is invalid")
    return {
        "summary": summary,
        "result": _json_ready(result),
        "observation": _json_ready(observation),
    }


def _context_document(context: EpisodeContext) -> dict[str, Any]:
    return {
        "episode_id": context.episode_id,
        "attempt_id": context.attempt_id,
        "task_id": context.task_id,
        "condition": context.condition,
        "max_steps": context.max_steps,
        "budget_limits": dict(context.budget_limits),
        "parent_attempt_id": context.parent_attempt_id,
        "retry_index": context.retry_index,
        "retry_reason": context.retry_reason,
    }


def _safe_private_usage_summary(recorder: _PrivateJsonlRecorder) -> Mapping[str, Any]:
    try:
        return private_event_usage_summary(read_trajectory(recorder.path))
    except (EvidenceExportError, FileNotFoundError, json.JSONDecodeError) as exc:
        return {
            "completeness": {"provider_usage_complete": False},
            "error_type": type(exc).__name__,
            "error_sha256": hashlib.sha256(str(exc).encode()).hexdigest(),
        }


def _branch_evidence_receipts(output_path: Path) -> dict[str, Mapping[str, Any]]:
    receipts: dict[str, Mapping[str, Any]] = {}
    for name in ("private-events.jsonl", "candidate-trajectory.jsonl", "public-validation.json", "branch-runtime.json"):
        path = output_path / name
        if path.is_file() and not path.is_symlink():
            receipts[name] = {
                "path": name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
    return receipts


def _write_branch_audit_sidecar(
    *,
    output_path: Path,
    provider_usage: Mapping[str, Any],
    evidence: Mapping[str, Any],
    wall_time_s: float,
) -> None:
    _write_once_json(
        output_path / "branch-audit.json",
        {
            "schema_version": "vaevas-native-evolution-branch-audit-v1",
            "provider_usage": _json_ready(provider_usage),
            "evidence": _json_ready(evidence),
            "wall_time_s": wall_time_s,
            "visibility_contract": {
                "audience": "reviewer_only",
                "may_enter_model_observation": False,
                "may_enter_shared_memory": False,
                "final_judge_payload_exported": False,
            },
        },
    )


def _terminal_failure_fields(status: str, *, final_judgment: FinalJudgment | None = None) -> dict[str, Any]:
    """Reuse the common taxonomy; execution status is not a candidate verdict."""
    phase = {
        "setup_failed": "setup", "public_cleanup_failed": "public_cleanup",
        "final_failed": "final_replay", "completed": "final_replay",
    }.get(status, "evolution_selection")
    protocol = runner.RESULT_PROTOCOL
    if final_judgment is not None and final_judgment.status in protocol.REPLAY_STATUSES:
        taxonomy = protocol.replay_failure_taxonomy(final_judgment.status, None, None)
    elif status in {"setup_failed", "public_cleanup_failed", "final_failed"}:
        taxonomy = protocol.normalize_failure_taxonomy(
            {}, primary_class="infrastructure", stage="infrastructure",
            responsibility="system", retryable=True,
        )
    else:
        taxonomy = protocol.normalize_failure_taxonomy(
            {}, primary_class=None, stage="not_scored", responsibility="undetermined", retryable=False,
        )
    return {
        "failure_taxonomy": taxonomy, "failure_phase": phase,
        "failure_class": taxonomy["primary_class"], "failure_stage": taxonomy["stage"],
        "failure_responsibility": taxonomy["responsibility"], "failure_retryable": taxonomy["retryable"],
    }


def _write_failure_final_result(
    *,
    output_dir: Path,
    manifest_sha256: str | None,
    campaign_config_sha256: str,
    error: Exception,
    evolution_result: EvolutionRuntimeResult | None = None,
    selected_candidate: Mapping[str, Any] | None = None,
    status: str = "evolution_failed",
) -> None:
    target = output_dir / "final-result.json"
    if target.exists():
        return
    _write_once_json(
        target,
        {
            "schema_version": "vaevas-native-evolution-final-result-v1",
            "status": status,
            "manifest_sha256": manifest_sha256,
            "campaign_config_sha256": campaign_config_sha256,
            "selected_candidate": selected_candidate,
            "final_judgment": None,
            "score_sidecar_receipt": None,
            "branch_usage": _json_ready(evolution_result.usage) if evolution_result else None,
            "branch_record_count": len(evolution_result.branch_records) if evolution_result else None,
            "error": {
                "type": type(error).__name__,
                "message_sha256": hashlib.sha256(str(error).encode()).hexdigest(),
            },
            **_terminal_failure_fields(status),
            **_evolution_evidence_summary(output_dir),
        },
    )


def _evolution_evidence_summary(output_dir: Path) -> dict[str, Any]:
    """One reviewer-only record per scheduled branch, including failed rounds."""
    request_path = output_dir / "request.json"
    if not request_path.exists():
        request_path = output_dir / "setup-request.json"
    request = json.loads(request_path.read_text())
    config = request["config"]
    records = []
    fields = ("model_calls", "tool_calls", "public_validation_calls", "prompt_tokens",
              "completion_tokens", "total_tokens", "reasoning_tokens", "transport_attempts",
              "transport_elapsed_s", "wall_time_s")
    values: dict[str, list[Any]] = {key: [] for key in fields}
    for round_index in range(config["rounds"]):
        for branch in config["branch_roster"]:
            relative = Path("evolution/branches") / f"round-{round_index:04d}" / branch["branch_id"]
            path = output_dir / relative
            result_path, audit_path = path / "result.json", path / "branch-audit.json"
            result = json.loads(result_path.read_text())["branch_record"] if result_path.is_file() else None
            audit = json.loads(audit_path.read_text()) if audit_path.is_file() else None
            started = (path / "request.json").exists()
            usage = result.get("usage", {}) if result else {}
            provider = audit.get("provider_usage", {}).get("provider", {}) if audit else {}
            token_usage = provider.get("usage", {})
            costs = {
                key: usage.get(key) for key in ("model_calls", "tool_calls", "public_validation_calls")
            } | {key: token_usage.get(key) for key in (
                "prompt_tokens", "completion_tokens", "total_tokens", "reasoning_tokens"
            )} | {key: provider.get(key) for key in ("transport_attempts", "transport_elapsed_s")}
            costs["wall_time_s"] = audit.get("wall_time_s") if audit else None
            if not started:
                costs = dict.fromkeys(fields, 0)
            for key, value in costs.items():
                values[key].append(value)
            evidence = {}
            for name in ("request.json", "result.json", "branch-audit.json"):
                source = path / name
                if source.is_file() and not source.is_symlink():
                    evidence[name] = {"path": str(relative / name),
                                      "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
            records.append({"round_index": round_index, "branch_id": branch["branch_id"],
                            "model_ref": branch["model_ref"], "started": started,
                            "status": result["status"] if result else "incomplete" if started else "not_started",
                            "costs": costs, "evidence": evidence})
    totals = {}
    for key, observed in values.items():
        known = sum(value for value in observed if value is not None)
        unknown = sum(value is None for value in observed)
        totals[key] = {"total": None if unknown else known,
                       "known_subtotal": known, "unknown_count": unknown}
    return {
        "denominator": {"scheduled_cells": 1, "scheduled_branches": len(records),
                        "observed_branches": sum(record["started"] for record in records)},
        "all_branch_costs": totals, "branch_evidence": records,
        **({"extensions": config["extensions"]} if "extensions" in config else {}),
        **({"declared_information_surface": config["declared_information_surface"]}
           if "declared_information_surface" in config else {}),
        "source": {"request_sha256": hashlib.sha256(request_path.read_bytes()).hexdigest(),
                   "campaign_file_sha256": request.get("campaign_file_sha256")},
        "claim_boundary": {"condition": config["condition"], "score_authority": "development_only",
                           "estimand": "multi_model_round_evolution_selected_candidate",
                           "model_quality_claim_allowed": False, "single_trajectory_pooling_allowed": False,
                           "may_enter_shared_memory": False},
    }


def _branch_generation_cell(cell: Mapping[str, Any]) -> dict[str, Any]:
    """Only generation gets the NoEVAS overlay; checker runtimes keep the cell."""
    return {**cell, "experimental_arm": "Agent-No-EVAS", "executable_feedback": False}


def _export_runtime(
    ops: NativeEvolutionOps,
    cell: Mapping[str, Any],
    release: Path,
    output: Path,
    timeout_s: int,
) -> None:
    export = ops.export_runtime or runner.export_runtime
    export(dict(cell), release, output, timeout_s=timeout_s)


def _default_quiesce_environment(
    *,
    environment: Any,
    allow_insecure_test_sandbox: bool,
) -> None:
    if allow_insecure_test_sandbox:
        return
    container = getattr(environment, "_docker_container", None)
    if not container:
        raise RuntimeError("cannot quiesce a production sandbox without its container")
    subprocess = __import__("subprocess")
    subprocess.run(["docker", "pause", container], check=True, capture_output=True, timeout=30)
    observed = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Paused}}", container],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if observed.stdout.strip() != "true":
        raise RuntimeError("native evolution sandbox writers were not quiesced")


def _provider_tools(capabilities: Sequence[Any]) -> list[dict[str, Any]]:
    tools = []
    for capability in capabilities:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": capability.tool_name,
                    "description": f"vaEVAS harness tool {capability.tool_name}",
                    "parameters": _json_ready(dict(capability.argument_schema)),
                },
            }
        )
    return tools


def _candidate_tree_sha256(runtime: Path) -> str:
    root = runtime / "public" / "submission"
    if root.is_symlink() or any(path.is_symlink() for path in root.rglob("*")):
        raise ValueError("candidate tree cannot contain symlinks")
    return runner.RESULT_PROTOCOL.hash_test_tree(root)["tree_sha256"]


def _store_candidate_snapshot(
    *,
    runtime: Path,
    destination: Path,
    artifacts: tuple[str, ...],
    tree_sha256: str,
    terminal_reason: str,
) -> Mapping[str, Any]:
    if not SHA256_RE.fullmatch(tree_sha256):
        raise ValueError("candidate tree hash must be a SHA-256 digest")
    if destination.exists() or destination.is_symlink():
        raise RuntimeError("candidate snapshot store already exists")
    destination.mkdir(parents=True, mode=0o700)
    submission = destination / "submission"
    submission.mkdir()
    source_root = runtime / "public" / "submission"
    safe_artifacts = tuple(_safe_artifact_path(relative) for relative in artifacts)
    for relative in artifacts:
        safe_relative = _safe_artifact_path(relative)
        source = _confined_existing_file(
            source_root,
            safe_relative,
            label="candidate artifact source",
        )
        target = _confined_destination(submission, safe_relative, label="candidate artifact target")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        target.chmod(0o444)
    observed_tree_sha = _artifact_tree_sha256(submission, safe_artifacts)
    if observed_tree_sha != tree_sha256:
        raise ValueError("candidate store hash mismatch after snapshot copy")
    identity = _store_identity_from_path(destination, tree_sha256=tree_sha256)
    manifest = {
        "schema_version": "vaevas-native-evolution-candidate-snapshot-v1",
        "tree_sha256": tree_sha256,
        "artifacts": list(safe_artifacts),
        "terminal_reason": terminal_reason,
        **identity,
    }
    _write_once_json(destination / "manifest.json", manifest)
    for directory in sorted((path for path in submission.rglob("*") if path.is_dir()), reverse=True):
        directory.chmod(0o555)
    submission.chmod(0o555)
    destination.chmod(0o555)
    return manifest


def _replace_submission_from_store(
    *,
    source: Path,
    runtime: Path,
    artifacts: tuple[str, ...],
) -> None:
    target_root = runtime / "public" / "submission"
    if target_root.is_symlink() or source.is_symlink():
        raise ValueError("submission roots cannot be symlinks")
    store = source.parent
    manifest = _validated_candidate_store_manifest(store)
    safe_artifacts = tuple(_safe_artifact_path(relative) for relative in artifacts)
    if tuple(manifest["artifacts"]) != safe_artifacts:
        raise ValueError("stored candidate artifact list mismatch")
    target_root.mkdir(parents=True, exist_ok=True)
    for path in sorted(target_root.rglob("*"), reverse=True):
        if path.is_symlink():
            raise ValueError("existing submission contains symlink")
        if path.is_file():
            path.chmod(0o644)
            path.unlink()
        elif path.is_dir():
            path.chmod(0o755)
            path.rmdir()
    for relative in safe_artifacts:
        src = _confined_existing_file(
            source,
            relative,
            label="stored candidate artifact",
        )
        dst = _confined_destination(target_root, relative, label="final submission artifact")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    if _artifact_tree_sha256(target_root, safe_artifacts) != manifest["tree_sha256"]:
        raise ValueError("candidate store hash mismatch after final copy")


def _candidate_store_for_selection(
    *,
    branches_dir: Path,
    selected_candidate: Mapping[str, Any],
) -> Path:
    branch_id = str(selected_candidate["branch_id"])
    round_index = int(selected_candidate["round_index"])
    tree_sha256 = str(selected_candidate["candidate_tree_sha256"])
    store = (
        branches_dir
        / f"round-{round_index:04d}"
        / branch_id
        / "candidate-store"
        / tree_sha256
    )
    if not store.is_dir():
        raise FileNotFoundError("selected candidate store is missing")
    _validated_candidate_store_manifest(
        store,
        expected_tree_sha256=tree_sha256,
        expected_candidate_id=str(selected_candidate["candidate_id"]),
    )
    return store


def _validated_candidate_store_manifest(
    store: Path,
    *,
    expected_tree_sha256: str | None = None,
    expected_candidate_id: str | None = None,
) -> dict[str, Any]:
    if store.is_symlink() or not store.is_dir():
        raise ValueError("candidate store must be a regular directory")
    manifest_path = store / "manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("candidate store manifest is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "vaevas-native-evolution-candidate-snapshot-v1":
        raise ValueError("candidate store manifest schema mismatch")
    tree_sha256 = str(manifest.get("tree_sha256") or "")
    if not SHA256_RE.fullmatch(tree_sha256):
        raise ValueError("candidate store manifest tree hash must be SHA-256")
    if expected_tree_sha256 is not None and tree_sha256 != expected_tree_sha256:
        raise ValueError("candidate store hash mismatch")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("candidate store artifacts must be a non-empty list")
    safe_artifacts = tuple(_safe_artifact_path(relative) for relative in artifacts)
    actual = _artifact_tree_sha256(store / "submission", safe_artifacts)
    if actual != tree_sha256:
        raise ValueError("candidate store hash mismatch")
    candidate_id = manifest.get("candidate_id")
    if expected_candidate_id is not None:
        if candidate_id is None:
            identity = _parse_candidate_id(expected_candidate_id, tree_sha256=tree_sha256)
            expected_path = (
                f"round-{identity['round_index']:04d}"
                f"/{identity['branch_id']}/candidate-store/{tree_sha256}"
            )
            if store.as_posix().endswith(expected_path) is not True:
                raise ValueError("candidate store identity mismatch")
        elif candidate_id != expected_candidate_id:
            raise ValueError("candidate store identity mismatch")
    manifest = dict(manifest)
    manifest["artifacts"] = list(safe_artifacts)
    return manifest


def _safe_artifact_path(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("candidate artifact path must be a non-empty string")
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != value:
        raise ValueError("candidate artifact path must stay inside submission")
    return value


def _confined_existing_file(root: Path, relative: str, *, label: str) -> Path:
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"{label} root must be a regular directory")
    path = root / relative
    if not _is_confined(path, root):
        raise ValueError(f"{label} path escaped root")
    _reject_symlink_path(path, root=root, label=label)
    if not path.is_file():
        raise ValueError(f"{label} is unavailable")
    return path


def _confined_destination(root: Path, relative: str, *, label: str) -> Path:
    if root.is_symlink():
        raise ValueError(f"{label} root cannot be a symlink")
    path = root / relative
    if not _is_confined(path, root):
        raise ValueError(f"{label} path escaped root")
    _reject_symlink_path(path, root=root, label=label, allow_missing_leaf=True)
    return path


def _reject_symlink_path(
    path: Path,
    *,
    root: Path,
    label: str,
    allow_missing_leaf: bool = False,
) -> None:
    current = path
    checked: list[Path] = []
    while True:
        checked.append(current)
        if current == root:
            break
        if current.parent == current:
            break
        current = current.parent
    for entry in checked:
        if allow_missing_leaf and entry == path and not entry.exists() and not entry.is_symlink():
            continue
        if entry.is_symlink():
            raise ValueError(f"{label} cannot contain symlinks")


def _artifact_tree_sha256(root: Path, artifacts: tuple[str, ...]) -> str:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("candidate artifact root must be a regular directory")
    expected = sorted(artifacts)
    actual = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("stored candidate artifact cannot contain symlinks")
        if path.is_file():
            actual.append(path.relative_to(root).as_posix())
    if sorted(actual) != expected:
        raise ValueError("candidate store artifact set mismatch")
    for relative in expected:
        _confined_existing_file(root, relative, label="candidate artifact")
    return runner.RESULT_PROTOCOL.hash_test_tree(root)["tree_sha256"]


def _parse_candidate_id(candidate_id: str, *, tree_sha256: str) -> dict[str, Any]:
    prefix = tree_sha256[:12]
    match = re.fullmatch(rf"(?P<branch_id>[^/]+)-round-(?P<round_index>\d{{4}})-{prefix}", candidate_id)
    if match is None:
        raise ValueError("sealed candidate identity does not match candidate tree")
    return {
        "branch_id": match.group("branch_id"),
        "round_index": int(match.group("round_index")),
    }


def _store_identity_from_path(destination: Path, *, tree_sha256: str) -> dict[str, Any]:
    parts = destination.parts
    try:
        candidate_store_index = len(parts) - 2
        if parts[candidate_store_index] != "candidate-store":
            return {}
        branch_id = parts[candidate_store_index - 1]
        round_part = parts[candidate_store_index - 2]
        match = re.fullmatch(r"round-(\d{4})", round_part)
        if match is None:
            return {}
        round_index = int(match.group(1))
    except IndexError:
        return {}
    return {
        "branch_id": branch_id,
        "round_index": round_index,
        "candidate_id": f"{branch_id}-round-{round_index:04d}-{tree_sha256[:12]}",
    }


def _is_confined(path: Path, root: Path) -> bool:
    root_resolved = root.resolve(strict=False)
    path_resolved = path.resolve(strict=False)
    return path_resolved == root_resolved or root_resolved in path_resolved.parents


def _final_freeze_forbidden() -> FrozenSubmission:
    raise AssertionError("candidate evolution branch must not final-freeze submissions")


def _normalize_public_validation_result(value: Any) -> PublicValidationResult:
    if isinstance(value, PublicValidationResult):
        result = value
    elif isinstance(value, Observation):
        result = PublicValidationResult(
            status=value.status,
            sim_success=1.0 if value.status == "succeeded" else 0.0,
            event_sha256=_canonical_sha256(value.to_document()),
        )
    elif isinstance(value, Mapping):
        result = PublicValidationResult(
            status=str(value["status"]),
            sim_success=float(value["sim_success"]),
            event_sha256=str(value["event_sha256"]),
        )
    else:
        raise TypeError("public validation result must be structured")
    if not result.status:
        raise ValueError("public validation status must be non-empty")
    if result.sim_success not in {0.0, 1.0}:
        raise ValueError("sim_success must be a binary public simulation metric")
    if not SHA256_RE.fullmatch(result.event_sha256):
        raise ValueError("public validation event_sha256 must be a SHA-256 digest")
    return result


def _budget_map(value: Mapping[str, int]) -> dict[str, int]:
    expected = {"model_calls", "tool_calls", "public_validation_calls"}
    if set(value) != expected:
        raise ValueError("budgets must contain exact model/tool/public counters")
    normalized = {}
    for key in expected:
        counter = value[key]
        if isinstance(counter, bool) or not isinstance(counter, int) or counter < 0:
            raise ValueError("budget counters must be non-negative integers")
        normalized[key] = counter
    return dict(sorted(normalized.items()))


def _cell_max_tokens(cell: Mapping[str, Any], *, default: int = 4096) -> int:
    for field in ("per_turn_max_tokens", "max_output_tokens", "max_working_tokens"):
        value = cell.get(field)
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            return value
    return default


def _usage(
    *,
    recorded_client: Any | None,
    recorder: _PrivateJsonlRecorder,
    public_validation_calls: int,
    allowance: Mapping[str, int] | None = None,
) -> dict[str, int]:
    model_calls = int(getattr(recorded_client, "calls", 0) or 0)
    tool_calls = recorder.count("tool_request")
    usage = {
        "model_calls": model_calls,
        "tool_calls": tool_calls,
        "public_validation_calls": public_validation_calls,
    }
    return usage


def _candidate_id(request: EvolutionBranchRequest, tree_sha256: str) -> str:
    return f"{request.branch_id}-round-{request.round_index:04d}-{tree_sha256[:12]}"


def _failure_candidate_sha(request: EvolutionBranchRequest) -> str:
    return _canonical_sha256(
        {
            "kind": "native_evolution_branch_failure",
            "manifest_sha256": request.manifest_sha256,
            "branch_id": request.branch_id,
            "round_index": request.round_index,
        }
    )


def _write_once_json(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(_json_ready(dict(document)), handle, sort_keys=True, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        os.fchmod(handle.fileno(), 0o444)


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            _json_ready(dict(value)),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    ).hexdigest()


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value
