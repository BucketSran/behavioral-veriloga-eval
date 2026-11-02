#!/usr/bin/env python3
"""Evaluate completed calibration submissions and aggregate their telemetry."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import importlib.util
import json
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def evaluate_cell(
    result_path: Path,
    command: str | None,
    timeout_s: int,
    evas_command: str | None = None,
) -> dict[str, Any]:
    result = read_json(result_path)
    cell = result["cell"]
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
    if (
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
        final_submission = RUNNER.RESULT_PROTOCOL.snapshot_submission(runtime, artifact_gate)
        replay = RUNNER.run_trusted_replay(
            runtime, command, timeout_s, evas_command, final_submission
        )
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
        write_json(result_path, result)
        row["judge_status"] = replay["status"]
        row["outcome"] = experiment["outcome"]
        row["trusted_replay"] = replay
    return row


def summarize(rows: list[dict[str, Any]], judge_kind: str) -> dict[str, Any]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        grouped[f"form:{row['form']}"][row["judge_status"]] += 1
        grouped[f"mode:{row['mode']}"][row["judge_status"]] += 1
        if row.get("experimental_arm"):
            grouped[f"arm:{row['experimental_arm']}"][row["judge_status"]] += 1

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
            telemetry[value] = {
                "cell_count": len(selected),
                "output_tokens_total": sum(output),
                "output_tokens_median": statistics.median(output),
                "working_tokens_total": sum(output),
                "working_tokens_median": statistics.median(output),
                "episode_elapsed_s_median": statistics.median(elapsed) if elapsed else None,
                "model_calls_total": sum(int(row.get("telemetry", {}).get("model_calls", 0)) for row in selected),
                "tool_calls_total": sum(int(row.get("telemetry", {}).get("tool_calls_total", 0)) for row in selected),
                "evas_calls_total": sum(int(row.get("telemetry", {}).get("evas_calls", 0)) for row in selected),
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
                "legacy_feedback_calls_total": sum(
                    int(row.get("telemetry", {}).get("legacy_feedback_calls", 0))
                    for row in selected
                ),
                "provider_reasoning_tokens_total": sum(
                    int(row.get("telemetry", {}).get("provider_reasoning_tokens_total", 0))
                    for row in selected
                ),
                "budget_hit_model_calls": sum(
                    int(row.get("telemetry", {}).get("budget_hit_model_calls", 0))
                    for row in selected
                ),
            }
        return telemetry

    telemetry_by_mode = telemetry_by("mode")
    telemetry_by_arm = telemetry_by("experimental_arm")
    return {
        "schema_version": "v4-calibration-score-report-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "judge_kind": judge_kind,
        "score_authority": (
            "final"
            if judge_kind in {"final_trusted_replay", "final_spectre"}
            else "legacy_provisional_feedback_only"
        ),
        "cell_count": len(rows),
        "submission_statuses": dict(Counter(row["submission_status"] for row in rows)),
        "judge_statuses": dict(Counter(row["judge_status"] for row in rows)),
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
    parser.add_argument("--timeout-s", type=int, default=120)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--evas-command")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.campaign_output = resolve_cli_path(args.campaign_output)
    args.output = resolve_cli_path(args.output) if args.output else None
    args.judge_command = normalize_judge_command(args.judge_command)
    if args.workers < 1:
        raise SystemExit("--workers must be at least 1")
    if args.judge_kind in {"final_trusted_replay", "final_spectre"} and not args.judge_command:
        raise SystemExit(f"--judge-kind {args.judge_kind} requires --judge-command")
    if args.judge_command and not args.evas_command:
        raise SystemExit("--evas-command is required when replay executes")
    result_paths = sorted(args.campaign_output.glob("v4-*/evidence/campaign_result.json"))
    if not result_paths:
        raise SystemExit(f"no campaign results under {args.campaign_output}")
    if args.workers == 1:
        rows = [
            evaluate_cell(path, args.judge_command, args.timeout_s, args.evas_command)
            for path in result_paths
        ]
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            rows = list(pool.map(
                lambda path: evaluate_cell(
                    path, args.judge_command, args.timeout_s, args.evas_command
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
