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
import shlex
import statistics
from typing import Any


HERE = Path(__file__).resolve().parent
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


def summarize(rows: list[dict[str, Any]], judge_kind: str) -> dict[str, Any]:
    for row in rows:
        replay = row.get("trusted_replay") or {}
        if "score_sidecar_receipt" in replay:
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
    args.output = resolve_cli_path(args.output) if args.output else None
    args.judge_command = normalize_judge_command(args.judge_command)
    if args.workers < 1:
        raise SystemExit("--workers must be at least 1")
    if args.timeout_s < 1 or args.testbench_timeout_s < 1:
        raise SystemExit("replay timeouts must be positive")
    if args.judge_kind in {"final_trusted_replay", "final_spectre"} and not args.judge_command:
        raise SystemExit(f"--judge-kind {args.judge_kind} requires --judge-command")
    if args.judge_command and not args.evas_command:
        raise SystemExit("--evas-command is required when replay executes")
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
