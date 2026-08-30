#!/usr/bin/env python3
"""Evaluate completed calibration submissions and aggregate their telemetry."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import statistics
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
RUNNER_PATH = HERE / "run_campaign.py"
SPEC = importlib.util.spec_from_file_location("v4_calibration_runner", RUNNER_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)

ARTIFACT_READY = {"submitted", "submitted_at_budget", "workspace_ready"}
DEFAULT_TRUSTED_REPLAY_TIMEOUT_S = 150
DEFAULT_TESTBENCH_TIMEOUT_S = 750
SCORE_AUTHORITY_BY_JUDGE_KIND = {
    "legacy_feedback_evas": "legacy_provisional_feedback_only",
    "final_trusted_replay": "development_only",
    "final_spectre": "formal",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def native_launcher_profile_config_sha256(manifest: dict[str, Any]) -> str:
    """Return the manifest identity used before profile receipt fields are added."""
    profile_bound_manifest = dict(manifest)
    profile_bound_manifest.pop("public_validation_profile_sha256", None)
    return RUNNER.RESULT_PROTOCOL.canonical_sha256(profile_bound_manifest)


def resolve_cli_path(path: Path) -> Path:
    """Resolve a CLI path from the user's cwd before worker cwd changes.

    The scoring adapter is executed by ``run_campaign.command_result`` with
    ``cwd=RUNNER.REPO``.  If the campaign output remains relative to the caller
    cwd, the adapter receives a relative ``VABENCH_RUNTIME_DIR`` and can resolve
    it against the wrong directory.  Always materialize filesystem paths before
    launching any judge process.
    """
    path = path.expanduser()
    if path.is_absolute():
        return path.resolve()
    return (Path.cwd() / path).resolve()


def resolve_command_path_token(token: str) -> str:
    """Convert existing relative path tokens in a judge command to absolutes.

    Two relative spellings are common in this repo:

    - from the benchmark repo root: ``benchmark-vabench-release-v4/...``;
    - from the workspace root: ``behavioral-veriloga-eval/...``.

    The judge command runs with ``cwd=RUNNER.REPO`` regardless of where
    ``score_campaign.py`` was invoked.  Normalizing existing path tokens avoids
    accidental double-prefixes such as
    ``behavioral-veriloga-eval/behavioral-veriloga-eval/...`` while preserving
    ordinary executable names like ``python3``.
    """
    if token.startswith("-"):
        return token
    candidate = Path(token).expanduser()
    if candidate.is_absolute():
        return str(candidate.resolve()) if candidate.exists() else token
    if "/" not in token and "\\" not in token:
        return token

    for base in (Path.cwd(), RUNNER.REPO, HERE):
        resolved = (base / candidate).resolve()
        if resolved.exists():
            return str(resolved)
    return token


def normalize_judge_command(command: str | None) -> str | None:
    if not command:
        return command
    parts = shlex.split(command)
    return shlex.join(resolve_command_path_token(part) for part in parts)


def attach_failure_taxonomy(
    row: dict[str, Any],
    experiment: dict[str, Any],
    *,
    fallback_model_status: str,
    artifact_gate: dict[str, Any],
) -> None:
    taxonomy = experiment.get("failure_taxonomy")
    if not isinstance(taxonomy, dict):
        submission = experiment.get("final_submission")
        if not isinstance(submission, dict):
            submission = {
                "status": (
                    "available" if artifact_gate.get("passed") else "no_submission"
                )
            }
        replay = experiment.get("final_trusted_replay")
        if not isinstance(replay, dict):
            replay = {"status": "not_run", "command": None}
        model_execution = experiment.get("model_execution")
        recorded_model_status = (
            model_execution.get("status")
            if isinstance(model_execution, dict)
            else None
        )
        model_status = recorded_model_status or fallback_model_status
        taxonomy = RUNNER.RESULT_PROTOCOL.terminal_failure_taxonomy(
            str(model_status), submission, replay
        )
    row["failure_taxonomy"] = taxonomy
    row["failure_class"] = taxonomy.get("primary_class")
    row["failure_stage"] = taxonomy.get("stage")
    row["failure_responsibility"] = taxonomy.get("responsibility")
    row["failure_retryable"] = taxonomy.get("retryable")


def provider_usage(events: list[dict[str, Any]]) -> dict[str, int]:
    totals: Counter[str] = Counter()
    for event in events:
        for key, value in (event.get("provider_usage") or {}).items():
            if isinstance(value, int):
                totals[key] += value
    return dict(sorted(totals.items()))


def event_telemetry(events: list[dict[str, Any]]) -> dict[str, Any]:
    tools = Counter(
        str(event["name"]) for event in events
        if event.get("type") == "tool" and event.get("name")
    )
    output_tokens = 0
    reasoning_tokens = 0
    visible_tokens = 0
    output_limit_hits = 0
    for event in events:
        if event.get("type") != "model":
            continue
        usage = event.get("provider_usage") or {}
        output = event.get("provider_output_tokens", usage.get("completion_tokens", 0))
        details = usage.get("completion_tokens_details") or {}
        reasoning = event.get(
            "provider_reasoning_tokens", details.get("reasoning_tokens", usage.get("reasoning_tokens", 0))
        )
        visible = event.get("provider_visible_tokens")
        output = int(output) if isinstance(output, int) else 0
        reasoning = int(reasoning) if isinstance(reasoning, int) else 0
        visible = int(visible) if isinstance(visible, int) else max(0, output - reasoning)
        output_tokens += output
        reasoning_tokens += reasoning
        visible_tokens += visible
        output_limit_hits += RUNNER.model_event_hit_limit(event)
    return {
        "model_calls": sum(event.get("type") == "model" for event in events),
        "model_elapsed_s": sum(
            float(event.get("elapsed_s", 0.0)) for event in events if event.get("type") == "model"
        ),
        "tool_calls": dict(sorted(tools.items())),
        "tool_calls_total": sum(tools.values()),
        "evas_calls": tools.get("run_evas", 0),
        "legacy_feedback_calls": tools.get("feedback", 0),
        "provider_output_tokens_total": output_tokens,
        "provider_reasoning_tokens_total": reasoning_tokens,
        "provider_visible_tokens_total": visible_tokens,
        "output_limit_model_calls": output_limit_hits,
        "budget_hit_model_calls": output_limit_hits,
    }


def elapsed_seconds(result: dict[str, Any]) -> float | None:
    agent_elapsed = result.get("agent_elapsed_s")
    if isinstance(agent_elapsed, (int, float)):
        return max(0.0, float(agent_elapsed))
    try:
        started = datetime.fromisoformat(str(result["started_at"]))
        finished = datetime.fromisoformat(str(result["finished_at"]))
    except (KeyError, TypeError, ValueError):
        return None
    return max(0.0, (finished - started).total_seconds())


def trusted_replay_timeout_s(
    cell: dict[str, Any],
    timeout_s: int,
    testbench_timeout_s: int,
) -> int:
    """Return the outer judge watchdog deadline for one trusted replay.

    Testbench judging runs the reference and five mutations sequentially.  The
    adapter bounds each simulation independently, so its outer process needs a
    watchdog covering all six runs rather than the single-run DUT/Bug Repair
    deadline. This is an evaluator fail-safe, not a candidate resource budget.
    """
    return testbench_timeout_s if cell.get("form") == "testbench" else timeout_s


def trusted_replay_input_signature(
    *,
    result: dict[str, Any],
    runtime: Path,
    command: str,
    replay_timeout_s: int,
    evas_command: str,
    final_submission: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    """Bind replay reuse to every frozen input and executable identity."""
    command_files: list[dict[str, str]] = []
    for token in shlex.split(command):
        path = Path(token)
        if path.is_file():
            resolved = path.resolve()
            command_files.append(
                {
                    "path": str(resolved),
                    "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
                }
            )
    signature = {
        "schema_version": "vabench-trusted-replay-input-signature-v1",
        "cell": result.get("cell") or {},
        "submission_tree_sha256": final_submission.get("tree_sha256"),
        "evaluator_manifest": RUNNER.RESULT_PROTOCOL.hash_test_tree(
            runtime / "evaluator"
        ),
        "evaluator": {
            "evas_profile": os.environ.get("VABENCH_EVAS_PROFILE", "r52").strip()
            or "r52",
        },
        "judge": {
            "command": command,
            "command_files": command_files,
            "outer_timeout_s": replay_timeout_s,
        },
        "evas": {
            "command": evas_command,
            "pinned_identity": result.get("evas_identity"),
        },
    }
    return signature, canonical_sha256(signature)


def trusted_replay_is_exactly_reusable(
    replay: dict[str, Any],
    signature: dict[str, Any],
    signature_sha256: str,
) -> bool:
    taxonomy = replay.get("failure_taxonomy")
    retryable = bool(
        isinstance(taxonomy, dict) and taxonomy.get("retryable") is True
    )
    return (
        not retryable
        and replay.get("input_signature") == signature
        and replay.get("input_signature_sha256") == signature_sha256
    )


def normalize_trusted_replay_watchdog(replay: dict[str, Any]) -> None:
    """The outer judge watchdog is evaluator infrastructure, not DUT runtime."""
    RUNNER.RESULT_PROTOCOL.normalize_trusted_replay_watchdog(replay)


def evaluate_cell(
    result_path: Path,
    command: str | None,
    timeout_s: int,
    evas_command: str | None = None,
    reuse_existing: bool = False,
    testbench_timeout_s: int = DEFAULT_TESTBENCH_TIMEOUT_S,
    write_back: bool = True,
    *,
    final_test_profile: dict[str, Any] | None = None,
    episode_context: Any = None,
) -> dict[str, Any]:
    bound = final_test_profile is not None or episode_context is not None
    if bound and (write_back or reuse_existing):
        raise ValueError("bound scoring forbids generation write-back and legacy replay reuse")
    if bound and (final_test_profile is None or episode_context is None):
        raise ValueError("bound scoring requires both final profile and episode context")
    result = read_json(result_path)
    cell = result["cell"]
    if bound:
        if (episode_context.episode_id != cell["cell_id"] or episode_context.task_id != cell["task_id"]
                or episode_context.condition != (cell.get("experimental_arm") or cell["mode"])):
            raise ValueError("bound scoring context does not match the campaign cell")
        prior = (result.get("experiment_result") or {}).get("final_trusted_replay") or {}
        if prior.get("executed") or result.get("final_judge") is not None:
            raise ValueError("final judge already executed; bound scoring cannot promote or rerun legacy evidence")
    runtime = result_path.parents[1].resolve()
    telemetry = event_telemetry(result.get("events") or [])
    artifact_gate = RUNNER.submission_artifact_gate(runtime)
    output_tokens = result.get("output_tokens")
    if not isinstance(output_tokens, int):
        provider_total = telemetry["provider_output_tokens_total"]
        output_tokens = provider_total if provider_total > 0 else result.get("working_tokens", 0)
    row: dict[str, Any] = {
        "cell_id": cell["cell_id"],
        "family_id": cell["family_id"],
        "task_id": cell["task_id"],
        "form": cell["form"],
        "mode": cell["mode"],
        "experimental_arm": cell.get("experimental_arm"),
        "submission_status": result["status"],
        "termination_reason": result.get("termination_reason"),
        "submission_mode": result.get("submission_mode"),
        "submission_protocol_compliant": result.get("submission_protocol_compliant"),
        "artifact_gate": artifact_gate,
        "output_tokens": output_tokens,
        "working_tokens": result.get("working_tokens", result.get("output_tokens", 0)),
        "provider_usage": provider_usage(result.get("events") or []),
        "telemetry": telemetry,
        "evas_usage": result.get("evas_usage") or {},
        "incidents": list(result.get("incidents") or []),
        "episode_elapsed_s": elapsed_seconds(result),
    }
    experiment = result.get("experiment_result") or {}
    attach_failure_taxonomy(
        row,
        experiment,
        fallback_model_status=str(result["status"]),
        artifact_gate=artifact_gate,
    )
    existing_replay = experiment.get("final_trusted_replay")
    final_submission: dict[str, Any] | None = None
    replay_signature: dict[str, Any] | None = None
    replay_signature_sha: str | None = None
    replay_timeout_s = trusted_replay_timeout_s(
        cell, timeout_s, testbench_timeout_s
    )
    if command and evas_command and artifact_gate["passed"]:
        final_submission = RUNNER.RESULT_PROTOCOL.snapshot_submission(
            runtime, artifact_gate
        )
        replay_signature, replay_signature_sha = trusted_replay_input_signature(
            result=result,
            runtime=runtime,
            command=command,
            replay_timeout_s=replay_timeout_s,
            evas_command=evas_command,
            final_submission=final_submission,
        )
    if (
        reuse_existing
        and result.get("final_judge") is not None
        and isinstance(existing_replay, dict)
        and existing_replay.get("status") not in {None, "not_run"}
        and replay_signature is not None
        and replay_signature_sha is not None
        and trusted_replay_is_exactly_reusable(
            existing_replay, replay_signature, replay_signature_sha
        )
    ):
        row["judge_status"] = existing_replay["status"]
        row["outcome"] = experiment.get("outcome", existing_replay["status"])
        row["trusted_replay"] = existing_replay
    elif (
        result["status"] not in ARTIFACT_READY or not artifact_gate["passed"]
    ):
        outcome = str(experiment.get("outcome") or "no_submission")
        row["judge_status"] = (
            outcome
            if outcome
            in {
                "agent_timeout",
                "agent_resource_exhausted",
                "no_submission",
                "infrastructure_failure",
            }
            else "no_submission"
        )
        if not artifact_gate["passed"]:
            row["judge_status_reason"] = "artifact_gate_failed"
        row["outcome"] = outcome
    elif not command:
        row["judge_status"] = "not_run"
        row["outcome"] = experiment.get("outcome", "not_scored")
    else:
        if not evas_command:
            raise ValueError("an explicit EVAS command is required for trusted replay")
        expected_identity = result.get("evas_identity")
        if expected_identity:
            RUNNER.validate_pinned_evas_identity(evas_command, expected_identity)
        if final_submission is None:
            final_submission = RUNNER.RESULT_PROTOCOL.snapshot_submission(
                runtime, artifact_gate
            )
        authority = ({"final_test_profile": final_test_profile, "episode_context": episode_context}
                     if bound else {})
        replay = RUNNER.run_trusted_replay(
            runtime, command, replay_timeout_s, evas_command, final_submission, **authority
        )
        normalize_trusted_replay_watchdog(replay)
        replay["input_signature"] = replay_signature
        replay["input_signature_sha256"] = replay_signature_sha
        checkpoint_path = runtime / "evidence" / "conversation_checkpoint.json"
        checkpoint = read_json(checkpoint_path) if checkpoint_path.is_file() else {}
        model_status = str(
            (experiment.get("model_execution") or {}).get("status") or "completed"
        )
        experiment = RUNNER.RESULT_PROTOCOL.build_experiment_result(
            cell=cell,
            model_status=model_status,
            messages=list(checkpoint.get("messages") or []),
            artifact_gate=artifact_gate,
            runtime=runtime,
            replay=replay,
            final_submission=final_submission,
        )
        result["experiment_result"] = experiment
        result["final_judge"] = replay["command"]
        if write_back:
            write_json(result_path, result)
        attach_failure_taxonomy(
            row,
            experiment,
            fallback_model_status=model_status,
            artifact_gate=artifact_gate,
        )
        row["judge_status"] = replay["status"]
        row["outcome"] = experiment["outcome"]
        row["trusted_replay"] = replay
    return row


def read_native_cell(
    runtime: Path, cell: dict[str, Any], *, campaign_file_sha256: str,
) -> dict[str, Any]:
    """Read a terminal native launcher attempt; never execute or refreeze it.

    The caller supplies the frozen scheduled cell and campaign file digest.
    Evidence corruption/incompletion raises, rather than becoming a model zero.
    This trusted report projection is not a public raw-trajectory export.
    """
    from runners.agent_harness import (
        backend_profile_sha256, read_trajectory,
        validate_scored_result_artifact, validate_trajectory_semantics,
    )
    from runners.agent_harness.authority_profiles import (
        episode_public_profile_sha256,
        final_test_profile_sha256,
    )
    from runners.agent_harness.trajectory import (
        validate_absent_public_authority,
        validate_trajectory,
    )

    if not isinstance(campaign_file_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", campaign_file_sha256):
        raise ValueError("expected campaign identity must be a SHA-256")
    if runtime.is_symlink():
        raise ValueError("native evidence must not use symlinks")
    runtime = runtime.resolve()
    hashes: dict[str, str] = {}

    def evidence(relative: str, expected: str | None = None) -> Path:
        path = runtime / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("unsafe native evidence path")
        if any(p.is_symlink() for p in (path, *path.parents) if p != runtime.parent):
            raise ValueError("native evidence must not use symlinks")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected is not None and digest != expected:
            raise ValueError("native evidence digest mismatch")
        hashes[relative] = digest
        return path

    prefix = "evidence/native-launcher/"
    if not (runtime / (prefix + "result.json")).is_file():
        dispatch = read_json(evidence("evidence/native-dispatch/result.json"))
        if (
            dispatch.get("schema_version") != "v4-native-dispatch-result-v1"
            or dispatch.get("backend") != "native-mini-swe"
            or dispatch.get("cell") != cell
            or dispatch.get("campaign_file_sha256") != campaign_file_sha256
        ):
            raise ValueError(
                "native dispatch evidence differs from scheduled campaign/cell"
            )
        status = dispatch.get("status")
        if status not in {
            "infrastructure_failure",
            "runner_error",
            "provider_error",
            "provider_timeout",
        }:
            raise ValueError("native dispatch receipt is not a terminal failure")
        row = {
            **{
                key: cell[key]
                for key in (
                    "cell_id",
                    "task_id",
                    "family_id",
                    "form",
                    "mode",
                    "experimental_arm",
                )
            },
            "backend": "native-mini-swe",
            "attempt_id": dispatch.get("attempt_id"),
            "submission_status": "not_submitted",
            "terminal_reason": dispatch["termination_reason"],
            "termination_reason": dispatch["termination_reason"],
            "judge_status": "infrastructure_failure",
            "outcome": "infrastructure_failure",
            "score": None,
            "output_tokens": 0,
            "telemetry": event_telemetry([]),
            "evas_usage": RUNNER.summarize_evas_invocations([]),
            "incidents": [
                {"category": incident["category"]}
                for incident in dispatch.get("incidents") or []
                if isinstance(incident, dict) and incident.get("category")
            ],
            "native_evidence": {"files": hashes},
        }
        attach_failure_taxonomy(
            row,
            {},
            fallback_model_status="runner_failure",
            artifact_gate={"passed": False},
        )
        return row
    result = read_json(evidence(prefix + "result.json"))
    manifest = read_json(evidence(prefix + "manifest.json", result["manifest_sha256"]))
    if manifest["cell"] != cell or manifest["campaign_file_sha256"] != campaign_file_sha256:
        raise ValueError("native evidence differs from scheduled campaign/cell")
    request = read_json(evidence("evidence/native-episode/request.json"))
    if request["backend_profile_sha256"] != backend_profile_sha256(manifest["backend_profile"]):
        raise ValueError("native backend identity mismatch")
    public_profile = request["public_validation_profile"]
    final_profile = request["final_test_profile"]
    expected_public_sha = episode_public_profile_sha256(
        public_validation_profile=public_profile,
        final_test_profile=final_profile,
        condition=cell["experimental_arm"],
    )
    if (
        request["public_validation_profile_sha256"] != expected_public_sha
        or request["final_test_profile_sha256"] != final_test_profile_sha256(final_profile)
    ):
        raise ValueError("native authority/config mismatch")
    outcome = read_json(evidence("evidence/native-episode/outcome.json"))
    events = read_trajectory(evidence(
        "evidence/native-episode/trajectory.jsonl", result["trajectory_sha256"],
    ))
    private = read_trajectory(evidence(
        prefix + "private-events.jsonl", result["private_events_sha256"],
    ))
    identity = {
        "episode_id": cell["cell_id"], "task_id": cell["task_id"],
        "condition": cell["experimental_arm"], "attempt_id": manifest["attempt_id"],
    }
    if (
        not validate_trajectory_semantics(events) or not validate_trajectory(private)
        or not private or private[-1]["event_sha256"] != result["private_events_tail_sha256"]
        or any(request[key] != value for key, value in identity.items())
        or any(event.get(key) != value for event in events + private for key, value in identity.items())
        or outcome["trajectory_tail_sha256"] != events[-1]["event_sha256"]
        or any(outcome[key] != result[key] or outcome[key] != events[-1]["payload"][key]
               for key in ("primary_outcome", "terminal_reason"))
    ):
        raise ValueError("native trajectory/terminal identity mismatch")
    if expected_public_sha is None and not validate_absent_public_authority(events):
        raise ValueError("native absent-public-authority trajectory mismatch")
    expected_config_sha = native_launcher_profile_config_sha256(manifest)
    for profile in [candidate for candidate in (public_profile, final_profile) if candidate is not None]:
        if profile["campaign_config_sha256"] != expected_config_sha:
            raise ValueError("native authority/config mismatch")
    row = {
        **{key: cell[key] for key in ("cell_id", "task_id", "family_id", "form", "mode", "experimental_arm")},
        "backend": "native-mini-swe",
        "attempt_id": manifest["attempt_id"],
        "submission_status": "not_submitted",
        "terminal_reason": outcome["terminal_reason"],
        "termination_reason": outcome["terminal_reason"],
        "judge_status": outcome["primary_outcome"], "outcome": outcome["primary_outcome"],
        "score": None,
        "output_tokens": result["model_telemetry"]["provider_output_tokens"],
        "telemetry": event_telemetry(result["model_telemetry"]["provider_events"]),
        "evas_usage": RUNNER.summarize_evas_invocations(result["evas_invocations"]),
        "incidents": [{"category": incident["category"]} for incident in outcome["incidents"]],
        "native_evidence": {
            "files": hashes, "artifact_path": result["artifact_path"],
            "artifact_file_sha256": result["artifact_file_sha256"], "artifact_sha256": None,
        },
    }
    artifact_path = result["artifact_path"]
    if artifact_path is None:
        failure = outcome["failure"]
        failed = [event["payload"] for event in events if event["event_type"] == "episode_failed"]
        if (
            result["artifact_file_sha256"] is not None or not failure or not failed
            or any(failed[-1].get(key) != failure[key] for key in ("category", "phase", "message"))
            or any(event["event_type"] == "final_judgment_completed" for event in events)
        ):
            raise ValueError("native unscored failure evidence mismatch")
        status = outcome["primary_outcome"]
        if status not in {"protocol_failure", "infrastructure_failure", "budget_exhausted", "agent_timeout"}:
            raise ValueError("unsupported native unscored terminal status")
        model_status = "runner_failure" if status == "infrastructure_failure" else status
        attach_failure_taxonomy(
            row, {}, fallback_model_status=model_status, artifact_gate={"passed": False},
        )
        return row
    if not isinstance(artifact_path, str) or not artifact_path.startswith(
        "evidence/native-episode/scored-results/"
    ):
        raise ValueError("native scored artifact is missing")
    artifact = read_json(evidence(artifact_path, result["artifact_file_sha256"]))
    if (
        artifact_path != f"evidence/native-episode/scored-results/{artifact['artifact_sha256']}.json"
        or any(artifact["contract_identity"][key] != request[key] for key in (
            "backend_profile_sha256", "registry_sha256", "effective_capability_sha256",
        ))
        or outcome["failure"] is not None
        or outcome["incidents"] != artifact["episode"]["incidents"]
    ):
        raise ValueError("native artifact/request identity mismatch")
    sidecar_sha = artifact["score_sidecar"]["sha256"]
    sidecar_path = f"evidence/score-sidecars/{sidecar_sha}.json"
    sidecar = read_json(evidence(sidecar_path, sidecar_sha))
    if not validate_scored_result_artifact(
        artifact, trajectory_events=events, score_sidecar=sidecar,
        public_validation_profile=public_profile,
        final_test_profile=final_profile,
    ):
        raise ValueError("native scored evidence join mismatch")
    frozen_root = runtime / "evidence/final_submission"
    if frozen_root.is_symlink() or any(path.is_symlink() for path in frozen_root.rglob("*")):
        raise ValueError("native frozen submission must not use symlinks")
    frozen = RUNNER.RESULT_PROTOCOL.hash_test_tree(frozen_root)
    if frozen["tree_sha256"] != artifact["submission"]["tree_sha256"]:
        raise ValueError("native frozen submission mismatch")
    row["native_evidence"]["artifact_sha256"] = artifact["artifact_sha256"]
    row.update({
        "submission_status": "submitted",
        "score": sidecar["structured_result"]["score"],
        "trusted_replay": {
            "status": outcome["primary_outcome"],
            "submission_tree_sha256": frozen["tree_sha256"],
            "final_test_profile": final_profile,
            "derived_score_sidecar_reference": {"path": sidecar_path, "sha256": sidecar_sha},
        },
    })
    attach_failure_taxonomy(
        row, {"final_submission": {"status": "available"}, "final_trusted_replay": row["trusted_replay"]},
        fallback_model_status="completed", artifact_gate={"passed": True},
    )
    return row


def summarize(
    rows: list[dict[str, Any]], judge_kind: str, *,
    scheduled_cells: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if scheduled_cells is not None:
        scheduled = {cell["cell_id"]: cell for cell in scheduled_cells}
        observed = {row["cell_id"]: row for row in rows}
        if (
            not scheduled
            or len(scheduled) != len(scheduled_cells)
            or len(observed) != len(rows)
            or scheduled.keys() != observed.keys()
        ):
            raise ValueError("rows must cover every scheduled cell exactly once")
        for cell_id, cell in scheduled.items():
            row = observed[cell_id]
            if row.get("judge_status") not in {
                "passed", "compile_failure", "runtime_failure", "behavior_failure",
                "infrastructure_failure", "agent_timeout", "agent_resource_exhausted",
                "no_submission", "protocol_failure", "budget_exhausted",
            }:
                raise ValueError("scheduled row must have a terminal disposition")
            if any(row.get(key) != cell.get(key) for key in (
                "task_id", "family_id", "form", "mode", "experimental_arm",
            )):
                raise ValueError("row identity differs from scheduled cell")
    for row in rows:
        replay = row.get("trusted_replay") or {}
        if "score_sidecar_receipt" in replay or "derived_score_sidecar_reference" in replay:
            profile = replay.get("final_test_profile") or {}
            authority = (profile.get("score_sidecar_contract") or {}).get("score_authority")
            if authority != SCORE_AUTHORITY_BY_JUDGE_KIND[judge_kind]:
                raise ValueError("bound sidecar authority does not match report judge kind")
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    failure_grouped: dict[str, Counter[str]] = defaultdict(Counter)
    failure_classes: Counter[str] = Counter()
    failure_stages: Counter[str] = Counter()
    failure_responsibilities: Counter[str] = Counter()
    secondary_failure_classes: Counter[str] = Counter()
    failed_case_ids: Counter[str] = Counter()
    failed_property_ids: Counter[str] = Counter()
    failed_mutation_ids: Counter[str] = Counter()
    for row in rows:
        grouped[f"form:{row['form']}"][row["judge_status"]] += 1
        grouped[f"mode:{row['mode']}"][row["judge_status"]] += 1
        if row.get("experimental_arm"):
            grouped[f"arm:{row['experimental_arm']}"][row["judge_status"]] += 1
        failure_class = row.get("failure_class")
        if not isinstance(failure_class, str) or not failure_class:
            continue
        failure_classes[failure_class] += 1
        failure_stage = row.get("failure_stage")
        if isinstance(failure_stage, str) and failure_stage:
            failure_stages[failure_stage] += 1
        responsibility = row.get("failure_responsibility")
        if isinstance(responsibility, str) and responsibility:
            failure_responsibilities[responsibility] += 1
        taxonomy = row.get("failure_taxonomy")
        if isinstance(taxonomy, dict):
            for field, counter in (
                ("secondary_classes", secondary_failure_classes),
                ("case_ids", failed_case_ids),
                ("property_ids", failed_property_ids),
                ("mutation_ids", failed_mutation_ids),
            ):
                for value in taxonomy.get(field) or []:
                    if isinstance(value, str) and value:
                        counter[value] += 1
        failure_grouped[f"form:{row['form']}"][failure_class] += 1
        failure_grouped[f"mode:{row['mode']}"][failure_class] += 1
        if row.get("experimental_arm"):
            failure_grouped[f"arm:{row['experimental_arm']}"][failure_class] += 1

    def telemetry_by(field: str) -> dict[str, Any]:
        telemetry = {}
        values = sorted(
            {str(row[field]) for row in rows if row.get(field) is not None}
        )
        for value in values:
            selected = [row for row in rows if row.get(field) == value]
            output = [
                int(row.get("output_tokens", row.get("working_tokens", 0)) or 0)
                for row in selected
            ]
            elapsed = [
                float(row["episode_elapsed_s"])
                for row in selected
                if row.get("episode_elapsed_s") is not None
            ]
            candidate_tree_hash_call_counts: Counter[str] = Counter()
            for row in selected:
                raw_counts = row.get("evas_usage", {}).get(
                    "candidate_tree_hash_call_counts", {}
                )
                if not isinstance(raw_counts, dict):
                    continue
                for candidate_hash, count in raw_counts.items():
                    if isinstance(candidate_hash, str) and candidate_hash:
                        candidate_tree_hash_call_counts[candidate_hash] += int(
                            count or 0
                        )
            telemetry[value] = {
                "cell_count": len(selected),
                "output_tokens_total": sum(output),
                "output_tokens_median": statistics.median(output),
                "working_tokens_total": sum(output),
                "working_tokens_median": statistics.median(output),
                "episode_elapsed_s_median": (
                    statistics.median(elapsed) if elapsed else None
                ),
                "model_calls_total": sum(
                    int(row.get("telemetry", {}).get("model_calls", 0))
                    for row in selected
                ),
                "tool_calls_total": sum(
                    int(row.get("telemetry", {}).get("tool_calls_total", 0))
                    for row in selected
                ),
                "evas_calls_total": sum(
                    int(row.get("telemetry", {}).get("evas_calls", 0))
                    for row in selected
                ),
                "direct_evas_calls_total": sum(
                    int(row.get("evas_usage", {}).get("calls_executed", 0))
                    for row in selected
                ),
                "direct_evas_successes_total": sum(
                    int(row.get("evas_usage", {}).get("calls_succeeded", 0))
                    for row in selected
                ),
                "direct_evas_failures_total": sum(
                    int(row.get("evas_usage", {}).get("calls_failed", 0))
                    for row in selected
                ),
                "direct_evas_timeouts_total": sum(
                    int(row.get("evas_usage", {}).get("calls_timed_out", 0))
                    for row in selected
                ),
                "direct_evas_unique_candidate_tree_hashes": sorted(
                    candidate_tree_hash_call_counts
                ),
                "direct_evas_candidate_tree_hash_call_counts": dict(
                    sorted(candidate_tree_hash_call_counts.items())
                ),
                "direct_evas_modified_reruns_total": sum(
                    int(
                        row.get("evas_usage", {}).get(
                            "modified_rerun_count", 0
                        )
                    )
                    for row in selected
                ),
                "direct_evas_unchanged_repeats_total": sum(
                    int(
                        row.get("evas_usage", {}).get(
                            "unchanged_repeat_count", 0
                        )
                    )
                    for row in selected
                ),
                "legacy_feedback_calls_total": sum(
                    int(row.get("telemetry", {}).get("legacy_feedback_calls", 0))
                    for row in selected
                ),
                "provider_reasoning_tokens_total": sum(
                    int(
                        row.get("telemetry", {}).get(
                            "provider_reasoning_tokens_total", 0
                        )
                    )
                    for row in selected
                ),
                "budget_hit_model_calls": sum(
                    int(
                        row.get("telemetry", {}).get(
                            "budget_hit_model_calls", 0
                        )
                    )
                    for row in selected
                ),
            }
        return telemetry

    telemetry_by_mode = telemetry_by("mode")
    telemetry_by_arm = telemetry_by("experimental_arm")
    return {
        "schema_version": "v4-calibration-score-report-v2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "judge_kind": judge_kind,
        "score_authority": SCORE_AUTHORITY_BY_JUDGE_KIND[judge_kind],
        "cell_count": len(rows),
        "submission_statuses": dict(Counter(row["submission_status"] for row in rows)),
        "judge_statuses": dict(Counter(row["judge_status"] for row in rows)),
        "failure_classes": dict(sorted(failure_classes.items())),
        "failure_stages": dict(sorted(failure_stages.items())),
        "failure_responsibilities": dict(
            sorted(failure_responsibilities.items())
        ),
        "secondary_failure_classes": dict(
            sorted(secondary_failure_classes.items())
        ),
        "failed_case_ids": dict(sorted(failed_case_ids.items())),
        "failed_property_ids": dict(sorted(failed_property_ids.items())),
        "failed_mutation_ids": dict(sorted(failed_mutation_ids.items())),
        "failure_retryability": {
            "retryable": sum(
                bool(row.get("failure_retryable"))
                for row in rows
                if row.get("failure_class")
            ),
            "non_retryable": sum(
                not bool(row.get("failure_retryable"))
                for row in rows
                if row.get("failure_class")
            ),
        },
        "incident_categories": dict(
            sorted(
                Counter(
                    str(incident.get("category") or "unknown")
                    for row in rows
                    for incident in row.get("incidents") or []
                ).items()
            )
        ),
        "breakdown": {key: dict(value) for key, value in sorted(grouped.items())},
        "failure_breakdown": {
            key: dict(value) for key, value in sorted(failure_grouped.items())
        },
        "telemetry_by_mode": telemetry_by_mode,
        "telemetry_by_arm": telemetry_by_arm,
        "rows": rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign-output", type=Path, required=True)
    parser.add_argument(
        "--campaign",
        type=Path,
        help="Frozen campaign manifest. Required for native-mini-swe scoring.",
    )
    parser.add_argument(
        "--episode-backend",
        choices=("legacy", "native-mini-swe"),
        default="legacy",
    )
    parser.add_argument(
        "--judge-kind",
        choices=("legacy_feedback_evas", "final_trusted_replay", "final_spectre"),
        required=True,
    )
    parser.add_argument("--judge-command")
    parser.add_argument(
        "--timeout-s",
        type=int,
        default=DEFAULT_TRUSTED_REPLAY_TIMEOUT_S,
        help=(
            "Outer trusted-replay watchdog for DUT and Bug Repair tasks. The "
            "default leaves process overhead beyond the adapter's 120-second "
            "inner simulation bound."
        ),
    )
    parser.add_argument(
        "--testbench-timeout-s",
        type=int,
        default=DEFAULT_TESTBENCH_TIMEOUT_S,
        help=(
            "Outer trusted-replay watchdog for Testbench tasks. The default "
            "covers the reference plus five sequential mutation simulations."
        ),
    )
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--evas-command")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse trusted-replay outcomes already persisted in campaign results.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.campaign_output = resolve_cli_path(args.campaign_output)
    args.campaign = resolve_cli_path(args.campaign) if args.campaign else None
    args.output = resolve_cli_path(args.output) if args.output else None
    args.judge_command = normalize_judge_command(args.judge_command)
    if args.workers < 1:
        raise SystemExit("--workers must be at least 1")
    if args.timeout_s < 1 or args.testbench_timeout_s < 1:
        raise SystemExit("replay timeouts must be positive")
    if args.episode_backend == "native-mini-swe" and args.resume:
        raise SystemExit("native-mini-swe scoring is read-only and does not resume")
    if args.episode_backend == "native-mini-swe" and args.campaign is None:
        raise SystemExit("--campaign is required for native-mini-swe scoring")
    if (
        args.episode_backend == "native-mini-swe"
        and args.judge_kind != "final_trusted_replay"
    ):
        raise SystemExit("native-mini-swe scoring reports final_trusted_replay only")
    if (
        args.judge_kind in {"final_trusted_replay", "final_spectre"}
        and not args.judge_command
        and args.episode_backend != "native-mini-swe"
    ):
        raise SystemExit(f"--judge-kind {args.judge_kind} requires --judge-command")
    if args.judge_command and not args.evas_command:
        raise SystemExit("--evas-command is required when replay executes")
    if args.episode_backend == "native-mini-swe":
        assert args.campaign is not None
        campaign = read_json(args.campaign)
        scheduled_cells = list(campaign["cells"])
        campaign_file_sha256 = hashlib.sha256(args.campaign.read_bytes()).hexdigest()
        if args.workers == 1:
            rows = [
                read_native_cell(
                    args.campaign_output / cell["cell_id"],
                    cell,
                    campaign_file_sha256=campaign_file_sha256,
                )
                for cell in scheduled_cells
            ]
        else:
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                rows = list(
                    pool.map(
                        lambda cell: read_native_cell(
                            args.campaign_output / cell["cell_id"],
                            cell,
                            campaign_file_sha256=campaign_file_sha256,
                        ),
                        scheduled_cells,
                    )
                )
        report = summarize(
            rows, args.judge_kind, scheduled_cells=scheduled_cells
        )
        output = (
            args.output
            or args.campaign_output / f"SCORE_{args.judge_kind.upper()}.json"
        )
        write_json(output, report)
        print(json.dumps({key: report[key] for key in (
            "judge_kind", "score_authority", "cell_count", "submission_statuses", "judge_statuses"
        )}, indent=2, sort_keys=True))
        return 0
    result_paths = sorted(args.campaign_output.glob("v4-*/evidence/campaign_result.json"))
    if not result_paths:
        raise SystemExit(f"no campaign results under {args.campaign_output}")
    if args.workers == 1:
        rows = [
            evaluate_cell(
                path,
                args.judge_command,
                args.timeout_s,
                args.evas_command,
                args.resume,
                args.testbench_timeout_s,
            )
            for path in result_paths
        ]
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            rows = list(pool.map(
                lambda path: evaluate_cell(
                    path,
                    args.judge_command,
                    args.timeout_s,
                    args.evas_command,
                    args.resume,
                    args.testbench_timeout_s,
                ),
                result_paths,
            ))
    report = summarize(rows, args.judge_kind)
    output = args.output or args.campaign_output / f"SCORE_{args.judge_kind.upper()}.json"
    write_json(output, report)
    print(json.dumps({key: report[key] for key in (
        "judge_kind", "score_authority", "cell_count", "submission_statuses", "judge_statuses"
    )}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
