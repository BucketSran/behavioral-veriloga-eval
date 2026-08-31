#!/usr/bin/env python3
"""Opt-in six-cell development pilot; never the default benchmark entrypoint."""

import argparse
from collections import Counter
from decimal import Decimal
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import subprocess

from build_campaign import DEFAULT_RELEASE, build_campaign
from deepseek_budget import BudgetedDeepSeekClient, DeepSeekPilotBudget, MAX_OUTPUT_TOKENS, MODEL, RATES
from pilot_credentials import load_pilot_key
from run_campaign import resolve_pinned_evas_identity, run_cell_preserving_failure, validate_campaign_cells
from score_campaign import read_native_cell


BACKENDS = ("native-mini-swe", "native-reasoning")


def clear_provider_environment() -> None:
    for name in ("DEEPSEEK_API_KEY", "GLM_API_KEY", "VABENCH_API_KEY", "VAEVAS_API_KEY"):
        os.environ.pop(name, None)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_immutable(path: Path, document: dict) -> None:
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def provider_preflight(api_key: str) -> dict:
    """Read metadata on the fixed HTTPS origin; retain no balance or credential."""
    documents, hashes = {}, {}
    try:
        for path in ("/models", "/user/balance"):
            connection = http.client.HTTPSConnection("api.deepseek.com", timeout=30)
            try:
                connection.request("GET", path, headers={"Authorization": f"Bearer {api_key}"})
                response = connection.getresponse()
                body = response.read(65537)
                if response.status != 200 or len(body) > 65536:
                    raise ValueError("invalid metadata response")
                documents[path] = json.loads(body)
                hashes[path] = hashlib.sha256(body).hexdigest()
            finally:
                connection.close()
        if MODEL not in {row["id"] for row in documents["/models"]["data"]}:
            raise ValueError("model unavailable")
        balance = documents["/user/balance"]
        accounts = balance["balance_infos"]
        if balance["is_available"] is not True or len(accounts) != 1:
            raise ValueError("unavailable or ambiguous account")
        currency = accounts[0]["currency"]
        amount = Decimal(accounts[0]["total_balance"])
        if currency not in RATES or not amount.is_finite() or amount < RATES[currency][2]:
            raise ValueError("unsupported currency or insufficient balance")
        return {"currency": currency, "model_available": True, "response_sha256": hashes}
    except Exception:
        # Provider bodies, exception strings and account balances are private.
        raise ValueError("DeepSeek metadata preflight failed; no generation started") from None


def freeze_pilot(root: Path, *, preflight: dict, image_id: str,
                 code_commit: str, evas_identity: dict, model_call_limit: int = 8) -> dict:
    """Freeze identical Agentic cells and an alternating serial execution order."""
    if type(model_call_limit) is not int or model_call_limit <= 0:
        raise ValueError("pilot model-call limit must be a positive integer")
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    campaign = build_campaign(
        DEFAULT_RELEASE, sample_families=1, seed=20260830, model_provider="deepseek",
        model=MODEL, per_turn_max_tokens=MAX_OUTPUT_TOKENS, repetitions=1, three_arm_g0_g2=True,
    )
    cells = [cell for cell in campaign["cells"] if cell["experimental_arm"] == "Agentic"]
    if len(cells) != 3 or {cell["family_id"] for cell in cells} != {"029"}:
        raise ValueError("predeclared family selection changed")
    validate_campaign_cells(cells, DEFAULT_RELEASE)
    campaign.update(cells=cells, cell_count=3, arm_count=1,
                    arms=[arm for arm in campaign["arms"] if arm["experimental_arm"] == "Agentic"],
                    comparison_profile="development-native-backend-pilot")
    bindings, schedule = {}, []
    for backend in BACKENDS:
        directory = root / backend
        directory.mkdir(mode=0o700)
        campaign["execution_config"] = {
            "episode_backend": backend, "workers": 1, "native_max_attempts": 1,
            "native_model_call_limit": model_call_limit,
            "mini_swe_sandbox": "docker", "mini_swe_image": image_id,
            "reasoning_proposal_format": "native_tool_calls", "temperature": 0, "stream": True,
            "thinking": {"type": "disabled"}, "request_timeout_s": 120,
            "setup_timeout_s": 1800, "tool_timeout_s": 1800, "judge_timeout_s": 1800,
            "evas_identity": evas_identity,
        }
        path = directory / "campaign.json"
        write_immutable(path, campaign)
        bindings[backend] = {"path": str(path.relative_to(root)), "sha256": sha256(path)}
    for number, form in enumerate(("dut", "bugfix", "testbench")):
        cell = next(cell for cell in cells if cell["form"] == form)
        for backend in BACKENDS[::1 if number % 2 == 0 else -1]:
            schedule.append({"pilot_cell_id": f"{backend}:{cell['cell_id']}",
                             "backend": backend, **cell,
                             "runtime": f"{backend}/run/{cell['cell_id']}"})
    currency = preflight["currency"]
    manifest = {
        "schema_version": "v4-deepseek-development-pilot-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": MODEL, "thinking": {"type": "disabled"}, "temperature": 0,
        "currency": currency, "cap": str(RATES[currency][2]),
        "input_peak_miss_per_million": str(RATES[currency][0]),
        "output_peak_per_million": str(RATES[currency][1]), "pricing_date": "2026-08-30",
        "max_output_tokens": MAX_OUTPUT_TOKENS, "model_calls_per_cell": model_call_limit,
        "native_max_attempts": 1, "workers": 1, "preflight": preflight,
        "code_commit": code_commit, "docker_image_id": image_id, "evas_identity": evas_identity,
        "release_manifest_sha256": campaign["release_manifest_sha256"],
        "campaigns": bindings, "schedule": schedule, "scheduled_count": 6,
        "score_authority": "development_only", "may_enter_model_memory": False,
        "claim_scope": "tiny_engineering_pilot_not_baseline_or_model_ranking",
        "resume_allowed": False,
    }
    write_immutable(root / "pilot-manifest.json", manifest)
    return manifest


def execute_pilot(root: Path, manifest: dict, *, api_key: str, evas_command: str) -> dict:
    """Execute once, serially; project verified native evidence without rejudging."""
    clear_provider_environment()
    manifest_path = root / "pilot-manifest.json"
    if json.loads(manifest_path.read_text()) != manifest:
        raise ValueError("frozen pilot manifest mismatch")
    manifest_hash = sha256(manifest_path)
    journal_path = root / "budget.jsonl"
    rows, stop_reason = [], None
    progress_path = root / "execution.jsonl"
    with os.fdopen(os.open(progress_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as progress:
        def record(event, row):
            progress.write(json.dumps({"event": event, **row}, sort_keys=True) + "\n")
            progress.flush()
            os.fsync(progress.fileno())

        with DeepSeekPilotBudget(journal_path, cell_ids=[
            row["pilot_cell_id"] for row in manifest["schedule"]
        ], currency=manifest["currency"], cap=manifest["cap"],
                model_call_limit=manifest["model_calls_per_cell"]) as budget:
            for scheduled in manifest["schedule"]:
                row = {key: scheduled[key] for key in (
                    "pilot_cell_id", "cell_id", "task_id", "family_id", "form", "backend", "runtime")}
                row.update(started=False, score=None, native_evidence=None)
                binding = manifest["campaigns"][row["backend"]]
                row["campaign_sha256"] = binding["sha256"]
                unexpected_failure = False
                try:
                    if stop_reason:
                        row.update(disposition="not_started", reason=stop_reason)
                    else:
                        campaign_path = root / binding["path"]
                        if (sha256(manifest_path) != manifest_hash
                                or sha256(campaign_path) != binding["sha256"]
                                or sha256(DEFAULT_RELEASE / "MANIFEST.json") != manifest["release_manifest_sha256"]):
                            raise ValueError("frozen input drift")
                        campaign = json.loads(campaign_path.read_text())
                        if campaign["execution_config"].get("native_model_call_limit") != manifest["model_calls_per_cell"]:
                            raise ValueError("pilot call limit differs from frozen campaign")
                        cell = next(cell for cell in campaign["cells"] if cell["cell_id"] == row["cell_id"])
                        args = argparse.Namespace(
                            output=root / row["backend"] / "run", release=DEFAULT_RELEASE,
                            resume=False, dry_run=False, episode_backend=row["backend"],
                            native_max_attempts=1, agent_timeout_s=1800, setup_timeout_s=1800,
                            native_model_call_limit=manifest["model_calls_per_cell"],
                            request_timeout_s=120, tool_timeout_s=1800, judge_timeout_s=1800,
                            evas_command=evas_command, mini_swe_image=manifest["docker_image_id"],
                            mini_swe_sandbox="docker", campaign_file_sha256=binding["sha256"],
                            reasoning_proposal_format="native_tool_calls",
                        )
                        row["started"] = True
                        record("cell_started", row)
                        print(json.dumps({"cell_started": row["pilot_cell_id"]}), flush=True)
                        client = BudgetedDeepSeekClient(budget=budget, cell_id=row["pilot_cell_id"], api_key=api_key)
                        run_cell_preserving_failure(cell, args, client)
                        native = read_native_cell(root / row["runtime"], cell,
                                                  campaign_file_sha256=binding["sha256"])
                        row.update(disposition="completed", reason=native["terminal_reason"],
                                   score=native["score"], native_evidence=native)
                        if native["terminal_reason"] == "model_call_limit":
                            row.update(disposition="operationally_censored", score=None)
                        if native["judge_status"] == "infrastructure_failure":
                            row.update(disposition="operationally_censored", score=None)
                            stop_reason = "native_infrastructure_failure"
                except BaseException as exc:
                    # Preserve complete scheduling, but never echo provider exceptions.
                    stop_reason = "interrupted" if isinstance(exc, KeyboardInterrupt) else "pilot_execution_or_evidence_failure"
                    unexpected_failure = True
                    row.update(disposition="operationally_censored" if row["started"] else "not_started",
                               reason=stop_reason, score=None, error_type=type(exc).__name__)
                events = [json.loads(line) for line in journal_path.read_text().splitlines()]
                cell_events = [event for event in events if event.get("cell_id") == row["pilot_cell_id"]]
                stops = [event["reason"] for event in cell_events if event["event"] in {"stopped", "cell_stopped"}]
                if stops:
                    row.update(disposition="operationally_censored", reason=stops[-1], score=None)
                    # Native wrappers may classify a budget exception as infrastructure failure.
                    if not unexpected_failure:
                        stop_reason = stops[-1] if budget.stopped else None
                row.update(model_calls=budget.model_calls[row["pilot_cell_id"]],
                           http_attempts=sum(event["event"] == "reserved" for event in cell_events))
                rows.append(row)
                record("cell_terminal", row)
                print(json.dumps({"cell": row["pilot_cell_id"], "disposition": row["disposition"],
                                  "reason": row["reason"], "score": row["score"],
                                  "committed_upper_bound": str(budget.committed)}), flush=True)
            result = {
                "schema_version": "v4-deepseek-development-pilot-index-v1",
                "manifest_sha256": manifest_hash, "scheduled_count": len(manifest["schedule"]),
                "started_count": sum(row["started"] for row in rows), "rows": rows,
                "dispositions": dict(Counter(row["disposition"] for row in rows)),
                "currency": budget.currency, "cap": str(budget.cap),
                "committed_upper_bound": str(budget.committed), "not_an_invoice": True,
                "http_attempts": sum(row["http_attempts"] for row in rows),
                "score_authority": "development_only", "may_enter_model_memory": False,
                "stop_reason": stop_reason,
            }
    result.update(budget_journal_sha256=sha256(journal_path), execution_journal_sha256=sha256(progress_path))
    write_immutable(root / "pilot-index.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--credential-file", type=Path, required=True)
    parser.add_argument("--evas-command", required=True)
    args = parser.parse_args()
    clear_provider_environment()
    repo = DEFAULT_RELEASE.parents[2]
    try:
        if args.output_root.exists():
            raise ValueError("pilot output must be fresh; resume is forbidden")
        dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True)
        if dirty:
            raise ValueError("commit and verify source before live execution")
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        image_id = subprocess.check_output(
            ["docker", "image", "inspect", "vabench-agent-runtime:0.8.7", "--format", "{{.Id}}"], text=True,
        ).strip()
        identity = resolve_pinned_evas_identity(args.evas_command)
        if "evas-sim 0.8.7 " not in identity["version_output"] or not image_id.startswith("sha256:"):
            raise ValueError("pinned evaluator/image unavailable")
        key = load_pilot_key(args.credential_file, "DEEPSEEK_API_KEY")
        preflight = provider_preflight(key)
        manifest = freeze_pilot(args.output_root, preflight=preflight, image_id=image_id,
                                code_commit=commit, evas_identity=identity)
        result = execute_pilot(args.output_root, manifest, api_key=key, evas_command=args.evas_command)
        print(json.dumps({key: result[key] for key in ("scheduled_count", "dispositions", "committed_upper_bound", "currency")}))
        return 0 if not result["stop_reason"] else 2
    except Exception:
        print("Pilot launch failed; no automatic retry. Inspect private evidence or preflight configuration.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
