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

import run_campaign as runner  # noqa: E402
from native_episode import _write_once  # noqa: E402
from run_native_evolution import NativeEvolutionBranch, run_native_evolution  # noqa: E402
from run_native_mini_swe import _backend_profile  # noqa: E402
from runners.agent_harness import backend_profile_sha256  # noqa: E402


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
    parser.add_argument("--cell", required=True)
    parser.add_argument("--branches-json", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
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
           args.request_timeout_s, args.timeout_s) < 1:
        raise ValueError("rounds, budgets and watchdogs must be positive")
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
    selected = [cell for cell in source["cells"] if cell["cell_id"] == args.cell]
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
        "source_cell_id": args.cell, "cell": cell,
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


if __name__ == "__main__":
    raise SystemExit(main())
