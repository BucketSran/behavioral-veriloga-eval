"""Opt-in free comparison engineering; no credential loader or paid CLI.

One immutable schedule, existing legacy/native runners, one shared spending
guard. Live model/rate/fee authorization remains separate from this fixture API.
"""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import sys
import time

from build_campaign import DEFAULT_RELEASE, build_campaign
from deepseek_budget import (
    BudgetedDeepSeekClient,
    DeepSeekPilotBudget,
    MAX_OUTPUT_TOKENS,
    MODEL,
    PRICING_REVIEWED_ON,
    PilotBudgetStop,
    RATES,
)
import run_campaign as runner
from run_campaign import validate_campaign_cells
from runners.agent_harness.batch_resume import _atomic_once, file_sha256, source_identity


ROOT = Path(__file__).resolve().parents[3]
BLUEPRINT = ROOT / "docs/alphaapollo-migration/experiments/legacy-native-comparison-20260831.json"
BACKENDS = ("legacy", "native-mini-swe")
JUDGE_COMMAND = shlex.join([sys.executable, str(Path(__file__).parent / "trusted_replay_adapter.py")])


def _comparison_campaign(*, live=False):
    campaign = build_campaign(
        DEFAULT_RELEASE, family_ids=["001"], model_provider="deepseek" if live else "free-comparison-fixture",
        model=MODEL, per_turn_max_tokens=MAX_OUTPUT_TOKENS, repetitions=1, three_arm_g0_g2=True,
    )
    cells = [row for row in campaign["cells"] if row["experimental_arm"] == "Agentic"]
    validate_campaign_cells(cells, DEFAULT_RELEASE)
    campaign.update(cells=cells, cell_count=3, arm_count=1,
                    arms=[row for row in campaign["arms"] if row["experimental_arm"] == "Agentic"])
    return campaign


def _execution_config(backend, controls, evas_identity):
    return {**controls, "episode_backend": backend,
            "mini_swe_sandbox": "docker", "mini_swe_image": controls["image_id_for_live_run"],
            "native_max_attempts": 1, "native_model_call_limit": None,
            "evas_identity": evas_identity, "temperature": 0, "stream": True,
            "thinking": {"type": "disabled"}}


def freeze_comparison(root: Path, *, image_id: str, code_commit: str,
                      evas_identity: dict, currency="CNY", cap="5.00", provider_profile=None) -> dict:
    """Derive, never modify, the dated protocol; reserve a fresh fixture root."""
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
        raise ValueError("comparison requires a resolved Docker image ID")
    if not re.fullmatch(r"[0-9a-f]{40}", code_commit):
        raise ValueError("comparison requires an exact source revision")
    if currency not in RATES or not Decimal(cap).is_finite() or not 0 < Decimal(cap) <= RATES[currency][2]:
        raise ValueError("invalid comparison fixture cap")
    blueprint = json.loads(BLUEPRINT.read_text())
    if (blueprint["release_manifest_sha256"] != file_sha256(DEFAULT_RELEASE / "MANIFEST.json")
            or blueprint["live_authorized"] is not False):
        raise ValueError("comparison protocol/release drift")
    if provider_profile is not None:
        from comparison_live import validate_provider_profile
        validate_provider_profile(provider_profile, currency=currency, cap=cap)
    campaign = _comparison_campaign(live=provider_profile is not None)
    cells = campaign["cells"]
    root.mkdir(parents=True, mode=0o700, exist_ok=False)
    bindings = {}
    controls = deepcopy(blueprint["controls"])
    controls["image_id_for_live_run"] = image_id
    for backend in BACKENDS:
        directory = root / backend
        directory.mkdir(mode=0o700)
        campaign["execution_config"] = _execution_config(backend, controls, evas_identity)
        path = directory / "campaign.json"
        _atomic_once(path, campaign)
        bindings[backend] = {"path": path.relative_to(root).as_posix(), "sha256": file_sha256(path)}
    schedule = []
    for scheduled in blueprint["schedule"]:
        cell, = [row for row in cells if row["task_id"] == scheduled["task_id"]]
        backend = scheduled["episode_backend"]
        schedule.append({
            **deepcopy(cell), "comparison_cell_id": scheduled["cell_id"], "backend": backend,
            "order": scheduled["order"], "runtime": f"{backend}/run/{cell['cell_id']}",
        })
    manifest = {
        "schema_version": "vaevas-workflow-comparison-v1",
        "live_authorized": False, "evidence_scope": "free_fixture_not_real_model",
        "claim_scope": "comparison_engineering_not_model_quality",
        "blueprint_sha256": file_sha256(BLUEPRINT), "code_commit": code_commit,
        "source_identity": source_identity(ROOT),
        "release_manifest_sha256": blueprint["release_manifest_sha256"],
        "controls": controls, "campaigns": bindings, "schedule": schedule,
        "model": MODEL, "evas_identity": evas_identity, "score_authority": "development_only",
        "budget": {"currency": currency, "cap": str(Decimal(cap)),
                   "input_peak_per_million": str(RATES[currency][0]),
                   "output_peak_per_million": str(RATES[currency][1]),
                   "pricing_date": PRICING_REVIEWED_ON, "model_call_limit": None},
    }
    if provider_profile is not None:
        manifest.update(schema_version="vaevas-workflow-comparison-live-v1",
                        evidence_scope="real_model_workflow_comparison",
                        claim_scope="small_sample_workflow_comparison",
                        provider_profile=deepcopy(provider_profile))
    _atomic_once(root / "comparison-manifest.json", manifest)
    return manifest


def execute_comparison(root: Path, manifest: dict, *, evas_command: str, scripted_response) -> dict:
    """Execute free response fixtures only; no live provider or credential API."""
    if "provider_profile" in manifest:
        raise ValueError("live preparation requires the explicit live entrypoint")
    if not callable(scripted_response):
        raise ValueError("comparison requires an explicit scripted response callback")
    return _execute_comparison(root, manifest, evas_command=evas_command,
                               client_factory=lambda **kwargs: _ScriptedComparisonClient(
                                   **kwargs, scripted_response=scripted_response))


def _execute_comparison(root: Path, manifest: dict, *, evas_command: str, client_factory) -> dict:
    """Shared schedule/runner implementation; public entrypoints own transport."""
    from comparison_results import read_backend_cell
    from comparison_surface import observe_environment, snapshot_public_runtime, snapshot_request
    from final_replay import EpisodeContext, build_final_test_profile
    from score_campaign import evaluate_cell

    _validate_frozen(root, manifest)
    runner.validate_pinned_evas_identity(evas_command, manifest["evas_identity"])
    authorization_hash = None
    preflight_hash = None
    if "provider_profile" in manifest:
        from comparison_live import validate_live_authorization, validate_provider_preflight
        authorization_hash = validate_live_authorization(root, manifest)
        preflight_hash = validate_provider_preflight(root, manifest)
    # Exclusive creation is also the no-reentry boundary after any interruption.
    with os.fdopen(os.open(root / "execution.jsonl", os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "w") as progress:
        def record(event, **fields):
            progress.write(json.dumps({"event": event, **fields}, sort_keys=True, allow_nan=False) + "\n")
            progress.flush()
            os.fsync(progress.fileno())

        rows = []
        stop_reason = None
        with DeepSeekPilotBudget(root / "budget.jsonl", cell_ids=[
            row["comparison_cell_id"] for row in manifest["schedule"]
        ], currency=manifest["budget"]["currency"], cap=manifest["budget"]["cap"], model_call_limit=None) as budget:
            for scheduled in manifest["schedule"]:
                row = {key: scheduled[key] for key in (
                    "comparison_cell_id", "cell_id", "task_id", "family_id", "form", "backend", "runtime")}
                row.update(started=False, disposition="not_started", reason=stop_reason,
                           score=None, evidence=None, surface=None, elapsed_s=None)
                start_cost = budget.committed
                started = time.monotonic()
                runtime = root / row["runtime"]
                observations = {"requests": []}
                try:
                    if stop_reason is None:
                        _validate_frozen(root, manifest)
                        binding = manifest["campaigns"][row["backend"]]
                        campaign = json.loads((root / binding["path"]).read_text())
                        cell, = [item for item in campaign["cells"] if item["cell_id"] == row["cell_id"]]
                        profile = None

                        def prepared(observed_runtime):
                            nonlocal profile
                            observations["public_runtime"] = snapshot_public_runtime(observed_runtime)
                            if row["backend"] == "legacy":
                                profile = build_final_test_profile(
                                    runtime=observed_runtime, release=DEFAULT_RELEASE,
                                    campaign_config_sha256=binding["sha256"], command=JUDGE_COMMAND,
                                    timeout_s=1800, evas_command=evas_command,
                                )

                        def environment_observer(environment):
                            observations["environment"] = observe_environment(environment)
                            observed = observations["environment"]
                            if not all(observed["checks"].values()) or observed["image_id"] != manifest["controls"]["image_id_for_live_run"]:
                                raise ValueError("observed comparison environment mismatch")

                        def request_observer(payload, timeout_s):
                            if "environment" not in observations or "public_runtime" not in observations:
                                raise ValueError("request preceded actual public surface audit")
                            request = snapshot_request({**payload, "configured_watchdog_s": 1800}, timeout_s=timeout_s)
                            observations["requests"].append(request)
                            record("request_observed", comparison_cell_id=row["comparison_cell_id"], request=request)

                        args = argparse.Namespace(
                            output=root / row["backend"] / "run", release=DEFAULT_RELEASE,
                            resume=False, dry_run=False, episode_backend=row["backend"], agent_scaffold="mini-swe",
                            native_max_attempts=1, native_model_call_limit=None, reasoning_proposal_format="native_tool_calls",
                            agent_timeout_s=1800, setup_timeout_s=1800, request_timeout_s=1800,
                            tool_timeout_s=1800, judge_timeout_s=1800, final_judge_command=None,
                            mini_swe_sandbox="docker", mini_swe_image=manifest["controls"]["image_id_for_live_run"],
                            evas_command=evas_command, evas_identity=manifest["evas_identity"],
                            campaign_file_sha256=binding["sha256"],
                            _prepared_runtime_observer=prepared, _environment_observer=environment_observer,
                        )
                        row["started"] = True
                        record("cell_started", comparison_cell_id=row["comparison_cell_id"])
                        client = client_factory(
                            budget=budget, cell_id=row["comparison_cell_id"],
                            request_observer=request_observer,
                        )
                        runner.run_cell_preserving_failure(cell, args, client)
                        if row["backend"] == "legacy":
                            result_path = runtime / "evidence/campaign_result.json"
                            generation_files = {f"evidence/{name}": file_sha256(runtime / "evidence" / name)
                                                for name in ("campaign_result.json", "mini_swe_trajectory.json", "conversation_checkpoint.json")
                                                if (runtime / "evidence" / name).is_file()}
                            if profile is None:
                                raise ValueError("legacy public export/profile not observed")
                            attempt_id = f"{cell['cell_id']}-attempt-0001"
                            context = EpisodeContext(episode_id=cell["cell_id"], attempt_id=attempt_id,
                                                     task_id=cell["task_id"], condition="Agentic", max_steps=1)
                            scored = evaluate_cell(
                                result_path, JUDGE_COMMAND, 1800, evas_command,
                                testbench_timeout_s=1800, write_back=False,
                                final_test_profile=profile, episode_context=context,
                            )
                            _atomic_once(runtime / "evidence/comparison-legacy-final.json", {
                                "schema_version": "vaevas-comparison-legacy-final-v1", "cell": cell,
                                "campaign_file_sha256": binding["sha256"], "attempt_id": attempt_id,
                                "final_test_profile": profile, "generation_files": generation_files,
                                "score_sidecar_receipt": (scored.get("trusted_replay") or {}).get("score_sidecar_receipt"),
                            })
                        evidence = read_backend_cell(runtime, row["backend"], cell,
                                                     campaign_file_sha256=binding["sha256"],
                                                     expected_image_id=manifest["controls"]["image_id_for_live_run"])
                        row.update(evidence=evidence, score=evidence["score"], disposition="completed",
                                   reason=evidence.get("terminal_reason", evidence.get("termination_reason")))
                except PilotBudgetStop:
                    stop_reason = "budget_stopped"
                    row.update(disposition="budget_censored", reason=stop_reason, error_type="PilotBudgetStop")
                except BaseException as exc:
                    stop_reason = "interrupted" if isinstance(exc, KeyboardInterrupt) else "execution_or_evidence_failure"
                    row.update(disposition="incomplete_evidence", reason=stop_reason, error_type=type(exc).__name__)
                finally:
                    if row["started"]:
                        row["elapsed_s"] = time.monotonic() - started
                    if budget.stopped:
                        stop_reason = "budget_stopped"
                        row["budget_censored"] = True
                        if row["started"]:
                            stopped = [json.loads(line) for line in (root / "budget.jsonl").read_text().splitlines()
                                       if json.loads(line).get("event") == "stopped"]
                            reason = stopped[-1]["reason"] if stopped else "budget_stopped"
                            if reason not in {"insufficient_reservation", "unknown_request_cost"}:
                                reason = "budget_stopped"
                            row.update(disposition="budget_censored", reason=reason)
                    row["guard_upper_bound"] = str(budget.committed - start_cost)
                    row["model_calls"] = budget.model_calls[row["comparison_cell_id"]]
                    if observations["requests"]:
                        row["surface"] = {**observations, "request": observations["requests"][0]}
                    rows.append(row)
                    record("cell_terminal", row=row)
        _atomic_once(root / "comparison-execution.json", {
            "schema_version": "vaevas-comparison-execution-v1", "rows": rows,
            "manifest_sha256": file_sha256(root / "comparison-manifest.json"),
            "budget_sha256": file_sha256(root / "budget.jsonl"),
            "execution_sha256": file_sha256(root / "execution.jsonl"),
            **({"authorization_sha256": authorization_hash, "preflight_sha256": preflight_hash}
               if authorization_hash else {}),
        })
    report = read_comparison(root)
    _atomic_once(root / "comparison-report.json", report)
    return report


def _validate_frozen(root, manifest, *, current_source=True):
    if json.loads(_source_path(root, "comparison-manifest.json").read_text()) != manifest:
        raise ValueError("frozen comparison manifest mismatch")
    budget = manifest["budget"]
    currency, cap = budget["currency"], Decimal(budget["cap"])
    pricing_date = budget.get("pricing_date")
    if (currency not in RATES or not cap.is_finite() or not 0 < cap <= RATES[currency][2]
            or pricing_date not in {"2026-08-30", PRICING_REVIEWED_ON}
            or budget != {"currency": currency, "cap": str(cap),
                          "input_peak_per_million": str(RATES[currency][0]),
                          "output_peak_per_million": str(RATES[currency][1]),
                          "pricing_date": pricing_date, "model_call_limit": None}):
        raise ValueError("comparison budget differs from supported guard")
    blueprint = json.loads(BLUEPRINT.read_text())
    controls = {**blueprint["controls"], "image_id_for_live_run": manifest["controls"]["image_id_for_live_run"]}
    live = manifest["schema_version"] == "vaevas-workflow-comparison-live-v1"
    if live:
        from comparison_live import PREVIOUS_REVIEWED_ON, validate_provider_profile
        validate_provider_profile(manifest["provider_profile"], currency=manifest["budget"]["currency"],
                                  cap=manifest["budget"]["cap"])
        expected_pricing_date = (
            "2026-08-30"
            if manifest["provider_profile"].get("reviewed_on") == PREVIOUS_REVIEWED_ON
            else PRICING_REVIEWED_ON
        )
        if pricing_date != expected_pricing_date:
            raise ValueError("comparison provider/budget review mismatch")
    elif "provider_profile" in manifest:
        raise ValueError("free fixture cannot carry a live provider profile")
    if (manifest["schema_version"] not in {"vaevas-workflow-comparison-v1", "vaevas-workflow-comparison-live-v1"}
            or manifest["controls"] != controls or manifest["model"] != MODEL
            or manifest["live_authorized"] is not False
            or manifest["evidence_scope"] != ("real_model_workflow_comparison" if live else "free_fixture_not_real_model")
            or manifest["blueprint_sha256"] != file_sha256(BLUEPRINT)
            or manifest["release_manifest_sha256"] != file_sha256(DEFAULT_RELEASE / "MANIFEST.json")
            or (current_source and manifest["source_identity"] != source_identity(ROOT))):
        raise ValueError("frozen comparison manifest/source/protocol drift")
    if len(manifest["schedule"]) != 6 or set(manifest["campaigns"]) != set(BACKENDS):
        raise ValueError("comparison schedule mismatch")
    expected_campaign = _comparison_campaign(live=live)
    for backend, binding in manifest["campaigns"].items():
        if binding["path"] != f"{backend}/campaign.json" or file_sha256(_source_path(root, binding["path"])) != binding["sha256"]:
            raise ValueError("comparison campaign drift")
        campaign = json.loads((root / binding["path"]).read_text())
        expected = {**expected_campaign, "execution_config": _execution_config(backend, controls, manifest["evas_identity"])}
        if campaign != expected:
            raise ValueError("comparison campaign differs from protocol")
    for expected, row in zip(blueprint["schedule"], manifest["schedule"], strict=True):
        cell, = [cell for cell in expected_campaign["cells"] if cell["task_id"] == expected["task_id"]]
        if (row["comparison_cell_id"] != expected["cell_id"] or row["backend"] != expected["episode_backend"]
                or row["task_id"] != expected["task_id"] or row["order"] != expected["order"]
                or row["runtime"] != f"{row['backend']}/run/{cell['cell_id']}"
                or {key: value for key, value in row.items() if key not in {"comparison_cell_id", "backend", "order", "runtime"}} != cell):
            raise ValueError("comparison schedule mismatch")


def _source_path(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != relative:
        raise ValueError("unsafe comparison source path")
    target = root / path
    current = target
    while current != root.parent:
        if current.is_symlink():
            raise ValueError("comparison source must not use symlinks")
        if current == root:
            break
        current = current.parent
    if not target.exists():
        raise ValueError(f"missing comparison source: {relative}")
    return target


def _verify_budget_rows(root, manifest, rows):
    events = [json.loads(line) for line in _source_path(root, "budget.jsonl").read_text().splitlines()]
    expected = {"event": "opened", "cell_ids": [r["comparison_cell_id"] for r in rows],
                "currency": manifest["budget"]["currency"], "cap": manifest["budget"]["cap"],
                "model": manifest["model"], "model_call_limit_per_cell": None,
                "input_miss_peak_per_million": manifest["budget"]["input_peak_per_million"],
                "output_peak_per_million": manifest["budget"]["output_peak_per_million"],
                "pricing_date": manifest["budget"]["pricing_date"]}
    if not events or any(events[0].get(key) != value for key, value in expected.items()):
        raise ValueError("comparison budget identity mismatch")
    costs = dict.fromkeys(expected["cell_ids"], Decimal(0))
    calls = dict.fromkeys(expected["cell_ids"], 0)
    committed, stopped = Decimal(0), False
    for index, event in enumerate(events):
        kind = event["event"]
        value = Decimal(event["committed_upper_bound"])
        if not value.is_finite() or not 0 <= value <= Decimal(expected["cap"]):
            raise ValueError("invalid comparison budget amount")
        if index == 0:
            if value != 0:
                raise ValueError("comparison budget must start at zero")
            continue
        cell_id = event.get("cell_id")
        if cell_id not in costs or kind not in {"model_call", "reserved", "reconciled", "stopped"} or stopped:
            raise ValueError("comparison budget event ordering mismatch")
        costs[cell_id] += value - committed
        committed = value
        if kind == "model_call":
            calls[cell_id] += 1
            if event["model_call"] != calls[cell_id]:
                raise ValueError("comparison budget call sequence mismatch")
        stopped = kind == "stopped"
    for row in rows:
        cell_id = row["comparison_cell_id"]
        if (type(row.get("model_calls")) is not int or row["model_calls"] != calls[cell_id]
                or Decimal(row["guard_upper_bound"]) != costs[cell_id]):
            raise ValueError("comparison accounting differs from budget journal")


class _ScriptedComparisonClient(BudgetedDeepSeekClient):
    """Exercise the real payload/parser/reservation boundary without network."""

    def __init__(self, *, budget, cell_id, scripted_response, request_observer):
        super().__init__(budget=budget, cell_id=cell_id, api_key="free-fixture-only", timeout_s=1800)
        self.scripted_response = scripted_response
        self.request_observer = request_observer

    def _complete_stream(self, payload, *, timeout_s, transport_observer=None):
        self.request_observer(payload, timeout_s)
        self.payload = deepcopy(payload)
        return super()._complete_stream(payload, timeout_s=timeout_s, transport_observer=transport_observer)

    def _capture_transport(self, execute, *, attempt, observer):
        # Do not invoke execute: it is the curl closure. The caller supplies only
        # a deterministic response fixture, never a real provider credential.
        return super()._capture_transport(
            lambda: self.scripted_response(self.cell_id, deepcopy(self.payload)), attempt=attempt, observer=observer,
        )


def read_comparison(root: Path) -> dict:
    """Revalidate existing receipts and project rows; no model, freeze or judge."""
    from comparison_results import read_backend_cell, join_six_cell_comparison
    from comparison_surface import compare_surfaces

    manifest = json.loads(_source_path(root, "comparison-manifest.json").read_text())
    _validate_frozen(root, manifest, current_source=False)
    execution = json.loads(_source_path(root, "comparison-execution.json").read_text())
    live = "provider_profile" in manifest
    if live:
        from comparison_live import validate_live_authorization, validate_provider_preflight
        if (execution.get("authorization_sha256") != validate_live_authorization(root, manifest)
                or execution.get("preflight_sha256") != validate_provider_preflight(root, manifest)):
            raise ValueError("comparison live launch receipt drift")
    for key, relative in (("manifest_sha256", "comparison-manifest.json"),
                          ("budget_sha256", "budget.jsonl"), ("execution_sha256", "execution.jsonl")):
        if execution[key] != file_sha256(_source_path(root, relative)):
            raise ValueError("comparison source evidence drift")
    rows = execution["rows"]
    journal = [json.loads(line) for line in (root / "execution.jsonl").read_text().splitlines()]
    if rows != [event["row"] for event in journal if event["event"] == "cell_terminal"]:
        raise ValueError("comparison rows differ from terminal journal")
    report = join_six_cell_comparison(manifest["schedule"], rows)
    _verify_budget_rows(root, manifest, rows)
    scheduled_by_id = {row["comparison_cell_id"]: row for row in manifest["schedule"]}
    request_ids = {event["comparison_cell_id"] for event in journal if event["event"] == "request_observed"}
    if not request_ids <= set(scheduled_by_id):
        raise ValueError("comparison journal contains unscheduled request")
    for row in rows:
        surface = row.get("surface")
        requests = [event["request"] for event in journal if event["event"] == "request_observed"
                    and event["comparison_cell_id"] == row["comparison_cell_id"]]
        if requests != ([] if surface is None else surface.get("requests")):
            raise ValueError("comparison requests differ from journal")
        if surface is not None:
            if not requests or surface.get("request") != requests[0]:
                raise ValueError("comparison first request mismatch")
            for request in requests:
                if not compare_surfaces(surface, {**surface, "request": request})["all_common_checks_match"]:
                    raise ValueError("comparison request controls changed within cell")
                if (request["model"] != manifest["model"] or request["max_tokens"] != MAX_OUTPUT_TOKENS
                        or request["configured_watchdog_s"] != manifest["controls"]["request_timeout_s"]):
                    raise ValueError("comparison request differs from frozen controls")
        if row["disposition"] == "completed" and not row.get("budget_censored"):
            if not isinstance(surface, dict) or not compare_surfaces(surface, surface)["all_common_checks_match"]:
                raise ValueError("completed comparison row lacks valid surface evidence")
        if row["evidence"] is None:
            continue
        scheduled = scheduled_by_id[row["comparison_cell_id"]]
        binding = manifest["campaigns"][scheduled["backend"]]
        if file_sha256(root / binding["path"]) != binding["sha256"]:
            raise ValueError("comparison campaign drift")
        campaign = json.loads((root / binding["path"]).read_text())
        cell, = [item for item in campaign["cells"] if item["cell_id"] == scheduled["cell_id"]]
        observed = read_backend_cell(_source_path(root, scheduled["runtime"]), scheduled["backend"], cell,
                                     campaign_file_sha256=binding["sha256"],
                                     expected_image_id=manifest["controls"]["image_id_for_live_run"])
        if observed != row["evidence"]:
            raise ValueError("comparison terminal evidence drift")
    surfaces = []
    for task_id in ("v4-001", "v4-1001", "v4-501"):
        pair = {row["backend"]: row for row in rows if row["task_id"] == task_id}
        if all(pair[backend]["surface"] is not None for backend in BACKENDS):
            surfaces.append({"task_id": task_id, **compare_surfaces(
                pair["legacy"]["surface"], pair["native-mini-swe"]["surface"])})
    for paired in report["paired_rows"]:
        paired["matched_surface"] = any(item["task_id"] == paired["task_id"]
                                        and item["all_common_checks_match"] for item in surfaces)
        if not paired["matched_surface"]:
            paired.update(complete=False, score_delta=None, guard_upper_bound_delta=None, elapsed_s_delta=None)
    report.update(surface_pairs=surfaces, evidence_scope=manifest["evidence_scope"],
                  score_authority="development_only", manifest_sha256=execution["manifest_sha256"],
                  budget_sha256=execution["budget_sha256"], paid_requests=None if live else 0)
    if live:
        events = [json.loads(line) for line in (root / "budget.jsonl").read_text().splitlines()]
        report.update(authorization_sha256=execution["authorization_sha256"],
                      preflight_sha256=execution["preflight_sha256"],
                      potentially_billable_attempts=sum(event["event"] == "reserved" for event in events))
    return report
