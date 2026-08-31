#!/usr/bin/env python3
"""Freeze and run one separately budgeted multi-model Evolution condition."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import sys
import time
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import evolution_batch  # noqa: E402
import mini_swe_vabench as mini  # noqa: E402
import run_campaign as runner  # noqa: E402
from native_episode import _write_once  # noqa: E402
from run_native_evolution import NativeEvolutionBranch, run_native_evolution  # noqa: E402
from run_native_mini_swe import _backend_profile  # noqa: E402
from runners.agent_harness import backend_profile_sha256  # noqa: E402
from runners.agent_harness.batch_resume import (  # noqa: E402
    BatchRun,
    docker_image_identity,
    file_sha256,
    source_identity,
)


def _roster(path: Path) -> list[dict]:
    value = runner.read_json(path)
    if not isinstance(value, list) or not value:
        raise ValueError("branch roster must be a nonempty array")
    result, ids = [], set()
    allowed = {"branch_id", "model", "base_url", "api_key_env", "temperature", "stream"}
    for item in value:
        if not isinstance(item, dict) or set(item) - allowed:
            raise ValueError("unknown roster field; credentials must use api_key_env")
        branch_id = item.get("branch_id")
        if not isinstance(branch_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", branch_id) or branch_id in ids:
            raise ValueError("branch IDs must be unique safe path segments")
        ids.add(branch_id)
        model, base_url = item.get("model"), item.get("base_url")
        if not isinstance(model, str) or not model.strip() or not isinstance(base_url, str):
            raise ValueError("branch requires model and base_url")
        endpoint = urlsplit(base_url)
        if (endpoint.username is not None or endpoint.password is not None
                or endpoint.query or endpoint.fragment):
            raise ValueError("endpoint cannot contain credentials/query/fragment")
        if endpoint.scheme not in {"http", "https"} or not endpoint.hostname:
            raise ValueError("endpoint requires an HTTP(S) URL")
        temperature = item.get("temperature", 0.0)
        if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not math.isfinite(temperature):
            raise ValueError("temperature must be finite")
        stream = item.get("stream", False)
        if not isinstance(stream, bool):
            raise ValueError("stream must be boolean")
        env = item.get("api_key_env")
        if env is not None and (not isinstance(env, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", env)):
            raise ValueError("api_key_env must name an environment variable")
        result.append({**item, "temperature": temperature, "stream": stream})
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--cell", action="append", required=True)
    parser.add_argument("--branches-json", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--batch", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--batch-max-attempts", type=int, default=1)
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--model-calls", type=int, default=8)
    parser.add_argument("--tool-calls", type=int, default=8)
    parser.add_argument("--public-validation-calls", type=int, default=1)
    parser.add_argument("--request-timeout-s", type=int, default=runner.DEFAULT_REQUEST_TIMEOUT_S)
    parser.add_argument("--timeout-s", type=int, default=runner.DEFAULT_JUDGE_TIMEOUT_S,
                        help="Infrastructure watchdog for export, tools and final replay.")
    parser.add_argument("--evas-command")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if min(args.rounds, args.model_calls, args.tool_calls, args.public_validation_calls,
           args.request_timeout_s, args.timeout_s, args.batch_max_attempts) < 1:
        raise ValueError("rounds, budgets and watchdogs must be positive")
    if args.batch:
        return _run_batch(args)
    if args.resume:
        raise ValueError("--resume is only supported by the explicit --batch path")
    if len(args.cell) != 1:
        raise ValueError("single-cell Evolution requires exactly one --cell")
    source = runner.read_json(args.campaign)
    release = runner.DEFAULT_RELEASE
    policy = runner.load_experiment_policy()
    for key, expected in {
        "release_manifest_sha256": hashlib.sha256((release / "MANIFEST.json").read_bytes()).hexdigest(),
        "experiment_policy_sha256": runner.experiment_policy_sha256(),
        "agent_wall_time_seconds": policy["agent_wall_time_seconds"],
        "timeout_finalization": policy["timeout_finalization"],
    }.items():
        if source.get(key) != expected:
            raise ValueError(f"campaign differs from pinned r53 policy: {key}")
    runner.validate_campaign_cells(source["cells"], release)
    selected = [cell for cell in source["cells"] if cell["cell_id"] == args.cell[0]]
    if len(selected) != 1 or selected[0].get("experimental_arm") != "Agentic":
        raise ValueError("select exactly one original Agentic cell as the public task source")
    roster = _roster(args.branches_json)
    condition = "AlphaApollo-Evolution+EVAS"
    cell = {**deepcopy(selected[0]), "cell_id": selected[0]["cell_id"] + "-evolution",
            "experimental_arm": condition}
    budgets = {"model_calls": args.model_calls, "tool_calls": args.tool_calls,
               "public_validation_calls": args.public_validation_calls}
    frozen = {
        "schema_version": "vaevas-evolution-campaign-v1", "condition": condition,
        "source_campaign_sha256": hashlib.sha256(args.campaign.read_bytes()).hexdigest(),
        "source_cell_id": args.cell[0], "cell": cell,
        "branches": [{key: value for key, value in branch.items() if key != "base_url"}
                     | {"endpoint_sha256": hashlib.sha256(branch["base_url"].encode()).hexdigest()}
                     for branch in roster],
        "roster_file_sha256": hashlib.sha256(args.branches_json.read_bytes()).hexdigest(),
        "rounds": args.rounds, "per_branch_budgets": budgets,
        "wall_time_seconds": policy["agent_wall_time_seconds"],
        "request_timeout_s": args.request_timeout_s, "timeout_s": args.timeout_s,
        "claim_scope": "development_only_separate_evolution_condition",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "dry_run": args.dry_run,
    }
    credentials = {}
    if not args.dry_run:
        if not args.evas_command:
            raise ValueError("--evas-command required for execution")
        runner.resolve_pinned_evas_identity(args.evas_command)
        for branch in roster:
            env = branch.get("api_key_env")
            credentials[branch["branch_id"]] = runner.load_key(None, env) if env else ""
        for env in {branch.get("api_key_env") for branch in roster} - {None}:
            os.environ.pop(env, None)
    args.output_root.mkdir(parents=True, mode=0o700, exist_ok=False)
    _write_once(args.output_root / "campaign.json", frozen)
    if args.dry_run:
        print(json.dumps({"status": "prepared", "condition": condition, "model_calls": 0}))
        return 0
    branches = []
    for branch in roster:
        def factory(branch=branch):
            return runner.OpenAICompatible(
                base_url=branch["base_url"], model=branch["model"],
                api_key=credentials[branch["branch_id"]], timeout_s=args.request_timeout_s,
                temperature=branch["temperature"], stream=branch["stream"],
            )
        branches.append(NativeEvolutionBranch(
            branch["branch_id"], branch["model"],
            backend_profile_sha256(_backend_profile("native-reasoning")), factory,
        ))
    run = run_native_evolution(
        cell=cell, release=release, output_dir=args.output_root / "run", branches=branches,
        public_validation_profile=None, final_test_profile=None,
        command=shlex.join([sys.executable, str(HERE / "trusted_replay_adapter.py")]),
        evas_command=args.evas_command, rounds=args.rounds, max_steps=args.model_calls,
        budgets=budgets, timeout_s=args.timeout_s, request_timeout_s=args.request_timeout_s,
        deadline_monotonic=time.monotonic() + policy["agent_wall_time_seconds"],
        campaign_file_sha256=hashlib.sha256((args.output_root / "campaign.json").read_bytes()).hexdigest(),
    )
    print(json.dumps({"condition": condition, "manifest_sha256": run.manifest_sha256,
                      "final_result": str(args.output_root / "run/final-result.json")}))
    return 0


def _run_batch(args: argparse.Namespace) -> int:
    source, release, policy, roster, selected, frozen = _prepare_batch(args)
    del source
    rows: list[dict] = []
    pending: list[tuple[dict, Path, int, list[dict], str | None]] = []
    errors: list[Exception] = []
    with BatchRun(args.output_root, frozen, [cell["cell_id"] for cell in selected],
                  resume=args.resume) as batch:
        for source_cell in selected:
            source_cell_id = source_cell["cell_id"]
            cell_runtime = args.output_root / source_cell_id
            try:
                recorded = batch.read(source_cell_id, cell_runtime)
                if recorded is not None:
                    reused = dict(recorded)
                    reused["batch_reuse"] = True
                    rows.append(reused)
                    continue
                campaign = _single_cell_manifest(
                    args=args,
                    source_cell=source_cell,
                    cell=_evolution_cell(source_cell),
                    roster=roster,
                    parent_attempt_id=None,
                )
                attempts = evolution_batch.attempt_records(
                    cell_runtime,
                    expected_source_cell_id=source_cell_id,
                    expected_campaign=campaign,
                    max_attempts=args.batch_max_attempts,
                )
            except Exception as exc:
                rows.append(evolution_batch.blocked_row(
                    source_cell_id=source_cell_id,
                    cell_runtime=cell_runtime,
                    reason="invalid_existing_attempt_evidence",
                    attempts=[],
                ))
                error = ValueError("invalid_existing_attempt_evidence")
                error.__cause__ = exc
                errors.append(error)
                continue
            if args.dry_run:
                rows.append(evolution_batch.prepared_row(source_cell_id))
                continue
            if attempts and attempts[-1]["status"] == "in_flight":
                rows.append(evolution_batch.blocked_row(
                    source_cell_id=source_cell_id,
                    cell_runtime=cell_runtime,
                    reason="existing_attempt_without_terminal_result",
                    attempts=attempts,
                ))
                errors.append(ValueError("existing Evolution attempt lacks a terminal result"))
                continue
            terminal_attempt = next((attempt for attempt in reversed(attempts)
                                     if attempt["status"] != "setup_failed"), None)
            if terminal_attempt is not None:
                terminal_dir = evolution_batch.attempt_dir(
                    cell_runtime, int(terminal_attempt["attempt_index"])
                )
                try:
                    row = evolution_batch.row_from_terminal(
                        source_cell_id=source_cell_id,
                        cell_runtime=cell_runtime,
                        terminal_attempt_dir=terminal_dir,
                        attempts=attempts,
                        expected_campaign=campaign,
                        batch_reuse=True,
                    )
                    batch.record(source_cell_id, row, cell_runtime)
                    rows.append(row)
                except Exception as exc:
                    rows.append(evolution_batch.blocked_row(
                        source_cell_id=source_cell_id, cell_runtime=cell_runtime,
                        reason="invalid_existing_terminal_evidence", attempts=attempts,
                    ))
                    errors.append(exc)
                continue
            parent = attempts[-1]["attempt_id"] if attempts else None
            if attempts and not attempts[-1]["safe_setup_retry"]:
                rows.append(evolution_batch.blocked_row(
                    source_cell_id=source_cell_id,
                    cell_runtime=cell_runtime,
                    reason="setup_failure_boundary_not_retryable",
                    attempts=attempts,
                ))
                errors.append(ValueError("setup_failed attempt is not at a safe retry boundary"))
                continue
            if len(attempts) >= args.batch_max_attempts:
                rows.append(evolution_batch.setup_retry_row(
                    source_cell_id=source_cell_id,
                    cell_runtime=cell_runtime,
                    reason="batch_attempt_cap_exhausted",
                    attempts=attempts,
                ))
                errors.append(ValueError("Evolution batch attempt cap exhausted"))
                continue
            pending.append((source_cell, cell_runtime, len(attempts) + 1, attempts, parent))
            rows.append({"cell_id": source_cell_id, "status": "scheduled"})
        batch.snapshot(rows)
        if errors:
            raise errors[0]
        if not pending:
            path = batch.snapshot(rows)
            print(json.dumps({"status": "batch_complete", "index": str(path), "model_calls": 0}))
            return 0
        if not args.evas_command:
            raise ValueError("--evas-command required for execution")
        runner.resolve_pinned_evas_identity(args.evas_command)
        credentials = _load_credentials(roster)
        branches = _branches(roster, credentials, args.request_timeout_s)
        budgets = _budgets(args)
        for source_cell, cell_runtime, index, attempts, parent in pending:
            rows = [{**item, "status": "started"} if item["cell_id"] == source_cell["cell_id"] else item
                    for item in rows]
            batch.snapshot(rows)
            cell = _evolution_cell(source_cell)
            current_index = index
            current_parent = parent
            while current_index <= args.batch_max_attempts:
                attempt_root = evolution_batch.attempt_dir(cell_runtime, current_index)
                attempt_root.mkdir(parents=True, mode=0o700, exist_ok=False)
                attempt_campaign = _single_cell_manifest(
                    args=args,
                    source_cell=source_cell,
                    cell=cell,
                    roster=roster,
                    parent_attempt_id=current_parent,
                )
                _write_once(attempt_root / "campaign.json", attempt_campaign)
                try:
                    run_native_evolution(
                        cell=cell, release=release, output_dir=attempt_root / "run",
                        branches=branches, public_validation_profile=None, final_test_profile=None,
                        command=shlex.join([sys.executable, str(HERE / "trusted_replay_adapter.py")]),
                        evas_command=args.evas_command, rounds=args.rounds, max_steps=args.model_calls,
                        budgets=budgets, timeout_s=args.timeout_s, request_timeout_s=args.request_timeout_s,
                        deadline_monotonic=time.monotonic() + policy["agent_wall_time_seconds"],
                        campaign_file_sha256=file_sha256(attempt_root / "campaign.json"),
                        branch_docker_image=frozen["observed_images"].get(mini.DEFAULT_NO_EVAS_DOCKER_IMAGE),
                        public_validation_docker_image=frozen["observed_images"].get(mini.DEFAULT_DOCKER_IMAGE),
                    )
                except Exception:
                    if not (attempt_root / "run/final-result.json").is_file():
                        raise
                updated_attempts = evolution_batch.attempt_records(
                    cell_runtime,
                    expected_source_cell_id=source_cell["cell_id"],
                    max_attempts=args.batch_max_attempts,
                    expected_campaign=_single_cell_manifest(
                        args=args,
                        source_cell=source_cell,
                        cell=cell,
                        roster=roster,
                        parent_attempt_id=None,
                    ),
                )
                final = evolution_batch.validate_terminal_result(
                    attempt_root / "run",
                    expected_source_cell_id=source_cell["cell_id"],
                    expected_campaign=attempt_campaign,
                )
                if (evolution_batch.safe_setup_retry(attempt_root / "run", final)
                        and current_index < args.batch_max_attempts):
                    current_parent = evolution_batch.attempt_id(source_cell["cell_id"], current_index)
                    current_index += 1
                    continue
                if final["status"] == "setup_failed":
                    if not evolution_batch.safe_setup_retry(attempt_root / "run", final):
                        row = evolution_batch.blocked_row(
                            source_cell_id=source_cell["cell_id"], cell_runtime=cell_runtime,
                            reason="setup_failure_boundary_not_retryable", attempts=updated_attempts,
                        )
                        rows = [row if item["cell_id"] == source_cell["cell_id"] else item for item in rows]
                        batch.snapshot(rows)
                        raise ValueError("setup_failed attempt is not at a safe retry boundary")
                    row = evolution_batch.setup_retry_row(
                        source_cell_id=source_cell["cell_id"],
                        cell_runtime=cell_runtime,
                        attempts=updated_attempts,
                        reason="batch_attempt_cap_exhausted",
                    )
                    rows = [row if item["cell_id"] == source_cell["cell_id"] else item for item in rows]
                    batch.snapshot(rows)
                    raise ValueError("Evolution batch attempt cap exhausted")
                row = evolution_batch.row_from_terminal(
                    source_cell_id=source_cell["cell_id"],
                    cell_runtime=cell_runtime,
                    terminal_attempt_dir=attempt_root,
                    attempts=updated_attempts,
                    expected_campaign=attempt_campaign,
                    batch_reuse=False,
                )
                batch.record(source_cell["cell_id"], row, cell_runtime)
                rows = [row if item["cell_id"] == source_cell["cell_id"] else item for item in rows]
                batch.snapshot(rows)
                break
        path = batch.snapshot(rows)
    print(json.dumps({"status": "batch_complete", "index": str(path), "model_calls": "see_cell_receipts"}))
    return 0


def _prepare_batch(args: argparse.Namespace) -> tuple[dict, Path, dict, list[dict], list[dict], dict]:
    if len(args.cell) != len(set(args.cell)):
        raise ValueError("batch cells must be unique")
    source = runner.read_json(args.campaign)
    release = runner.DEFAULT_RELEASE
    policy = runner.load_experiment_policy()
    for key, expected in {
        "release_manifest_sha256": hashlib.sha256((release / "MANIFEST.json").read_bytes()).hexdigest(),
        "experiment_policy_sha256": runner.experiment_policy_sha256(),
        "agent_wall_time_seconds": policy["agent_wall_time_seconds"],
        "timeout_finalization": policy["timeout_finalization"],
    }.items():
        if source.get(key) != expected:
            raise ValueError(f"campaign differs from pinned r53 policy: {key}")
    runner.validate_campaign_cells(source["cells"], release)
    by_id = {cell["cell_id"]: cell for cell in source["cells"]}
    selected = []
    for cell_id in args.cell:
        cell = by_id.get(cell_id)
        if cell is None or cell.get("experimental_arm") != "Agentic":
            raise ValueError("batch cells must be original Agentic cell IDs")
        selected.append(cell)
    roster = _roster(args.branches_json)
    observed_images = {}
    if not args.dry_run:
        for image in (mini.DEFAULT_NO_EVAS_DOCKER_IMAGE, mini.DEFAULT_DOCKER_IMAGE):
            observed_images[image] = docker_image_identity(image, timeout_s=args.timeout_s)
    args.observed_images = observed_images
    frozen = {
        "schema_version": "vaevas-evolution-batch-v1",
        "condition": "AlphaApollo-Evolution+EVAS",
        "source_campaign_sha256": file_sha256(args.campaign),
        "roster_file_sha256": file_sha256(args.branches_json),
        "source_identity": source_identity(REPO),
        "cell_ids": [cell["cell_id"] for cell in selected],
        "rounds": args.rounds,
        "per_branch_budgets": _budgets(args),
        "batch_max_attempts": args.batch_max_attempts,
        "dry_run": args.dry_run,
        "wall_time_seconds": policy["agent_wall_time_seconds"],
        "request_timeout_s": args.request_timeout_s,
        "timeout_s": args.timeout_s,
        "branch_sandbox_backend": "docker",
        "branch_docker_image": mini.DEFAULT_NO_EVAS_DOCKER_IMAGE,
        "public_validation_docker_image": mini.DEFAULT_DOCKER_IMAGE,
        "observed_images": observed_images,
        "evaluator": {
            "engine": "evas",
            "version": "0.8.7",
            "command_sha256": hashlib.sha256((args.evas_command or "").encode()).hexdigest(),
        },
        "claim_scope": "development_only_separate_evolution_condition_batch",
    }
    return source, release, policy, roster, selected, frozen


def _single_cell_manifest(
    *,
    args: argparse.Namespace,
    source_cell: dict,
    cell: dict,
    roster: list[dict],
    parent_attempt_id: str | None,
) -> dict:
    return {
        "schema_version": "vaevas-evolution-campaign-v1",
        "condition": "AlphaApollo-Evolution+EVAS",
        "source_campaign_sha256": file_sha256(args.campaign),
        "source_cell_id": source_cell["cell_id"],
        "cell": cell,
        "branches": [{key: value for key, value in branch.items() if key != "base_url"}
                     | {"endpoint_sha256": hashlib.sha256(branch["base_url"].encode()).hexdigest()}
                     for branch in roster],
        "roster_file_sha256": file_sha256(args.branches_json),
        "rounds": args.rounds,
        "per_branch_budgets": _budgets(args),
        "request_timeout_s": args.request_timeout_s,
        "timeout_s": args.timeout_s,
        "branch_sandbox_backend": "docker",
        "branch_docker_image": getattr(args, "observed_images", {}).get(
            mini.DEFAULT_NO_EVAS_DOCKER_IMAGE, mini.DEFAULT_NO_EVAS_DOCKER_IMAGE),
        "public_validation_docker_image": getattr(args, "observed_images", {}).get(
            mini.DEFAULT_DOCKER_IMAGE, mini.DEFAULT_DOCKER_IMAGE),
        "final_command_sha256": hashlib.sha256(shlex.join([
            sys.executable, str(HERE / "trusted_replay_adapter.py"),
        ]).encode()).hexdigest(),
        "evas_command_sha256": hashlib.sha256((args.evas_command or "").encode()).hexdigest(),
        "source_sha256": file_sha256(Path(__file__)),
        "parent_attempt_id": parent_attempt_id,
    }


def _evolution_cell(source_cell: dict) -> dict:
    return {**deepcopy(source_cell), "cell_id": source_cell["cell_id"] + "-evolution",
            "experimental_arm": "AlphaApollo-Evolution+EVAS"}


def _budgets(args: argparse.Namespace) -> dict[str, int]:
    return {"model_calls": args.model_calls, "tool_calls": args.tool_calls,
            "public_validation_calls": args.public_validation_calls}


def _load_credentials(roster: list[dict]) -> dict[str, str]:
    credentials = {}
    for branch in roster:
        env = branch.get("api_key_env")
        credentials[branch["branch_id"]] = runner.load_key(None, env) if env else ""
    for env in {branch.get("api_key_env") for branch in roster} - {None}:
        os.environ.pop(env, None)
    return credentials


def _branches(
    roster: list[dict],
    credentials: dict[str, str],
    request_timeout_s: int,
) -> list[NativeEvolutionBranch]:
    branches = []
    for branch in roster:
        def factory(branch=branch):
            return runner.OpenAICompatible(
                base_url=branch["base_url"], model=branch["model"],
                api_key=credentials[branch["branch_id"]], timeout_s=request_timeout_s,
                temperature=branch["temperature"], stream=branch["stream"],
            )
        branches.append(NativeEvolutionBranch(
            branch["branch_id"], branch["model"],
            backend_profile_sha256(_backend_profile("native-reasoning")), factory,
        ))
    return branches


if __name__ == "__main__":
    raise SystemExit(main())
