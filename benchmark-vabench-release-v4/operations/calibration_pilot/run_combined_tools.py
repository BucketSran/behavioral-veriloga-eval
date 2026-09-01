"""Opt-in single-task Reasoning/Evolution + retrieval + waveform acceptance.

Reuse the existing engines and spending guard; never modify the legacy/native
comparison protocol. Preparation is not authority to make paid requests.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_campaign import build_campaign  # noqa: E402
import comparison_live as live_transport  # noqa: E402
from deepseek_budget import (  # noqa: E402
    DeepSeekPilotBudget,
    MAX_OUTPUT_TOKENS,
    MODEL,
    PRICING_REVIEWED_ON,
    PilotBudgetStop,
)
import run_campaign as runner  # noqa: E402
from runners.agent_harness.batch_resume import (  # noqa: E402
    _atomic_once, _tree, file_sha256, source_identity,
)
from runners.agent_harness.tools.offline_docs import (  # noqa: E402
    OfflineDocsCorpus, corpus_profile_sha256, validate_corpus_profile,
)

BACKENDS = ("native-reasoning", "evolution")
INTERVENTIONS = {
    "baseline": {"name": "baseline", "offline_docs": False, "public_waveform": False},
    "rag-waveform": {"name": "rag-waveform", "offline_docs": True, "public_waveform": True},
}
EVIDENCE_SCOPES = {
    False: {
        "baseline": "synthetic_provider_condition",
        "rag-waveform": "synthetic_provider_integration",
    },
    True: {
        "baseline": "real_model_condition_observation",
        "rag-waveform": "real_model_combined_acceptance",
    },
}
CLAIM_SCOPES = {
    "baseline": "single_task_condition_diagnostic_not_population_or_individual_causality",
    "rag-waveform": "combined_connectivity_not_individual_effect_or_model_quality",
}
JUDGE_COMMAND = shlex.join([sys.executable, str(HERE / "trusted_replay_adapter.py")])


def _source_cell(family_id, form, *, live):
    campaign = build_campaign(
        runner.DEFAULT_RELEASE, family_ids=[family_id],
        model_provider="deepseek" if live else "free-combined-fixture",
        model=MODEL, per_turn_max_tokens=MAX_OUTPUT_TOKENS,
        repetitions=1, three_arm_g0_g2=True,
    )
    cells = [cell for cell in campaign["cells"]
             if cell["form"] == form.lower() and cell["experimental_arm"] == "Agentic"]
    if len(cells) != 1:
        raise ValueError("select one released task form")
    runner.validate_campaign_cells(cells, runner.DEFAULT_RELEASE)
    return cells[0]


def _controls(backend, *, rounds, branch_count, model_calls, tool_calls, public_calls):
    if backend not in BACKENDS:
        raise ValueError("unsupported combined backend")
    values = (rounds, branch_count, model_calls, tool_calls, public_calls)
    if any(type(value) is not int or value < 1 for value in values):
        raise ValueError("combined limits must be positive integers")
    if branch_count > 5:
        raise ValueError("combined acceptance supports at most five branches")
    return {"rounds": rounds if backend == "evolution" else 1,
            "branch_count": branch_count if backend == "evolution" else 1,
            "model_calls": model_calls, "tool_calls": tool_calls,
            "public_validation_calls": public_calls, "watchdog_s": 1800,
            "wall_time_seconds": runner.load_experiment_policy()["agent_wall_time_seconds"],
            "branch_memory_scope": "same_task_run_next_round_public_only",
            "final_policy": "one_selected_frozen_submission_no_feedback",
            "selection": "existing_engine_public_status_then_candidate_id"}


def freeze_combined(root: Path, *, backend: str, family_id: str, form: str,
                    docs_corpus: OfflineDocsCorpus, image_id: str, branch_image_id: str,
                    evas_identity: dict, currency: str, cap: str, live=False,
                    intervention="rag-waveform",
                    rounds=2, branch_count=2, model_calls=8, tool_calls=8, public_calls=1) -> dict:
    """Freeze one task and all optional interventions; no key or HTTP access."""
    controls = _controls(backend, rounds=rounds, branch_count=branch_count,
                         model_calls=model_calls, tool_calls=tool_calls, public_calls=public_calls)
    if type(live) is not bool:
        raise ValueError("live preparation must be explicit")
    if intervention not in INTERVENTIONS:
        raise ValueError("unsupported intervention")
    if any(not re.fullmatch(r"sha256:[0-9a-f]{64}", image) for image in (image_id, branch_image_id)):
        raise ValueError("resolved Docker image IDs required")
    profile = live_transport.build_provider_profile(currency=currency, cap=cap)
    docs_corpus.assert_model_context_allowed(external_provider=live)
    cell = _source_cell(family_id, form, live=live)
    budget_ids = [f"branch-{index:02d}" for index in range(controls["branch_count"])]
    manifest = {
        "schema_version": "vaevas-combined-tools-v1", "backend": backend,
        "live": live, "live_authorized": False,
        "evidence_scope": EVIDENCE_SCOPES[live][intervention],
        "family_id": family_id, "form": form, "source_cell": cell,
        "controls": controls, "budget_ids": budget_ids,
        "image_id": image_id, "branch_image_id": branch_image_id,
        "evas_identity": deepcopy(evas_identity),
        "intervention": deepcopy(INTERVENTIONS[intervention]),
        "public_waveform": INTERVENTIONS[intervention]["public_waveform"],
        "docs_profile": docs_corpus.profile, "provider_profile": profile,
        "budget": {"currency": currency, "cap": profile["cap"]},
        "release_manifest_sha256": file_sha256(runner.DEFAULT_RELEASE / "MANIFEST.json"),
        "experiment_policy_sha256": runner.experiment_policy_sha256(),
        "source_identity": source_identity(ROOT),
        "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "claim_scope": CLAIM_SCOPES[intervention],
    }
    root.mkdir(parents=True, mode=0o700, exist_ok=False)
    _atomic_once(root / "combined-manifest.json", manifest)
    return manifest


def _document(root, relative):
    from run_legacy_native_comparison import _source_path
    return json.loads(_source_path(root, relative).read_text())


def _validate_frozen(root, *, current_source):
    value = _document(root, "combined-manifest.json")
    if value.get("schema_version") != "vaevas-combined-tools-v1" or value.get("live_authorized") is not False:
        raise ValueError("invalid combined manifest")
    intervention = value.get("intervention", INTERVENTIONS["rag-waveform"])
    if (type(value.get("live")) is not bool or intervention not in INTERVENTIONS.values()
            or value.get("public_waveform") is not intervention["public_waveform"]):
        raise ValueError("combined intervention mismatch")
    intervention_name = intervention["name"]
    if (value.get("evidence_scope") != EVIDENCE_SCOPES[value["live"]][intervention_name]
            or value.get("claim_scope") != CLAIM_SCOPES[intervention_name]):
        raise ValueError("combined evidence/claim scope mismatch")
    controls = value["controls"]
    expected = _controls(value["backend"], rounds=controls["rounds"], branch_count=controls["branch_count"],
                         model_calls=controls["model_calls"], tool_calls=controls["tool_calls"],
                         public_calls=controls["public_validation_calls"])
    if controls != expected or value["budget_ids"] != [f"branch-{i:02d}" for i in range(controls["branch_count"])]:
        raise ValueError("combined schedule/control drift")
    if value["source_cell"] != _source_cell(value["family_id"], value["form"], live=value["live"]):
        raise ValueError("combined released source cell drift")
    if (value["release_manifest_sha256"] != file_sha256(runner.DEFAULT_RELEASE / "MANIFEST.json")
            or value["experiment_policy_sha256"] != runner.experiment_policy_sha256()):
        raise ValueError("combined release/policy drift")
    if current_source and value["source_identity"] != source_identity(ROOT):
        raise ValueError("combined source drift")
    validate_corpus_profile(value["docs_profile"])
    live_transport.validate_provider_profile(value["provider_profile"], **value["budget"])
    return value


def inspect_combined(root: Path) -> dict:
    manifest = _validate_frozen(root, current_source=False)
    intervention = manifest.get("intervention", INTERVENTIONS["rag-waveform"])
    return {"manifest_sha256": file_sha256(root / "combined-manifest.json"),
            "live_authorized": False, "backend": manifest["backend"],
            "task_id": manifest["source_cell"]["task_id"],
            "provider_profile": manifest["provider_profile"],
            "controls": manifest["controls"], "docs_profile": manifest["docs_profile"],
            "intervention": intervention,
            "public_waveform": intervention["public_waveform"],
            "evidence_scope": manifest["evidence_scope"]}


def _authorization(root, manifest):
    return {"schema_version": "vaevas-combined-live-authorization-v1",
            "manifest_sha256": file_sha256(root / "combined-manifest.json"),
            "approved_cap": manifest["budget"]["cap"], "currency": manifest["budget"]["currency"],
            "authority": "operator_assertion_not_authenticated_identity"}


def _validate_inputs(root, docs_corpus, evas_command):
    manifest = _validate_frozen(root, current_source=True)
    if docs_corpus.profile != manifest["docs_profile"]:
        raise ValueError("combined corpus drift")
    docs_corpus.assert_model_context_allowed(external_provider=manifest["live"])
    runner.validate_pinned_evas_identity(evas_command, manifest["evas_identity"])
    for key in ("image_id", "branch_image_id"):
        if live_transport.docker_image_identity(manifest[key]) != manifest[key]:
            raise ValueError("combined Docker image drift")
    if any((root / name).exists() for name in (
            "execution-start.json", "execution.json", "budget.jsonl", "campaign.json", "run")):
        raise ValueError("combined execution cannot resume")
    return manifest


def execute_live(root: Path, *, docs_corpus: OfflineDocsCorpus, expected_manifest_sha256: str,
                 approved_cap: str, currency: str, credential_file: Path, evas_command: str) -> dict:
    """Explicit one-use launch; assertions prevent accidents, not forged authority."""
    live_transport.clear_provider_environment()
    manifest = _validate_frozen(root, current_source=True)
    if (file_sha256(root / "combined-manifest.json") != expected_manifest_sha256
            or manifest["live"] is not True or manifest["budget"] != {"currency": currency, "cap": approved_cap}):
        raise ValueError("combined live manifest/cap assertion mismatch")
    # Validate corpus before touching runtime, credentials or a provider.
    if docs_corpus.profile != manifest["docs_profile"]:
        raise ValueError("combined corpus drift")
    docs_corpus.assert_model_context_allowed(external_provider=True)
    live_transport.validate_provider_profile(manifest["provider_profile"], **manifest["budget"], for_launch=True)
    _validate_inputs(root, docs_corpus, evas_command)
    if credential_file.resolve().is_relative_to(ROOT):
        raise ValueError("credentials must remain repository-external")
    _atomic_once(root / "live-authorization.json", _authorization(root, manifest))
    key = live_transport.load_pilot_key(credential_file, "DEEPSEEK_API_KEY")
    preflight = live_transport.provider_preflight(key)
    if preflight["currency"] != currency:
        raise ValueError("account currency differs from combined preparation")
    _atomic_once(root / "provider-preflight.json", preflight)
    return _execute(root, manifest, docs_corpus=docs_corpus, evas_command=evas_command,
                    client_factory=lambda **kwargs: live_transport.LiveComparisonClient(
                        **kwargs, api_key=key, profile=manifest["provider_profile"]))


def execute_fixture(root: Path, *, docs_corpus: OfflineDocsCorpus, evas_command: str,
                    scripted_response) -> dict:
    """Free transport fixture through the same engines and spending admission."""
    from run_legacy_native_comparison import _ScriptedComparisonClient
    manifest = _validate_frozen(root, current_source=True)
    if manifest["live"] or not callable(scripted_response):
        raise ValueError("fixture entry requires free preparation and scripted responses")
    _validate_inputs(root, docs_corpus, evas_command)
    return _execute(root, manifest, docs_corpus=docs_corpus, evas_command=evas_command,
                    client_factory=lambda **kwargs: _ScriptedComparisonClient(
                        **kwargs, scripted_response=scripted_response))


def _run_campaign(manifest, *, docs_corpus, evas_command):
    from run_native_evolution import evolution_extension_config
    controls = manifest["controls"]
    intervention = manifest.get("intervention", INTERVENTIONS["rag-waveform"])
    cell = deepcopy(manifest["source_cell"])
    if manifest["backend"] == "evolution":
        cell.update(cell_id=cell["cell_id"] + "-combined-evolution",
                    experimental_arm="AlphaApollo-Evolution+EVAS")
    campaign = {
        "schema_version": "vaevas-combined-engine-campaign-v1",
        "source_cell_id": manifest["source_cell"]["cell_id"], "cell": cell,
        "condition": cell["experimental_arm"], "backend": manifest["backend"],
        "branches": [{"branch_id": key, "model": MODEL} for key in manifest["budget_ids"]],
        "rounds": controls["rounds"], "per_branch_budgets": {
            key: controls[key] for key in ("model_calls", "tool_calls", "public_validation_calls")},
        "timeout_s": controls["watchdog_s"], "request_timeout_s": controls["watchdog_s"],
        "branch_sandbox_backend": "docker", "branch_docker_image": manifest["branch_image_id"],
        "public_validation_docker_image": manifest["image_id"],
        "final_command_sha256": hashlib.sha256(JUDGE_COMMAND.encode()).hexdigest(),
        "evas_command_sha256": hashlib.sha256(evas_command.encode()).hexdigest(),
    }
    extensions = evolution_extension_config(
        docs_corpus=docs_corpus if intervention["offline_docs"] else None,
        public_waveform=intervention["public_waveform"],
        public_waveform_max_calls=(
            controls["public_validation_calls"] if intervention["public_waveform"] else None
        ),
    )
    if extensions:
        campaign["extensions"] = extensions
    return campaign


def _read_campaign(root, manifest):
    campaign = _document(root, "campaign.json")
    docs = SimpleNamespace(profile=manifest["docs_profile"],
                           profile_sha256=corpus_profile_sha256(manifest["docs_profile"]), intervention=(
        "synthetic-frozen-docs-v1" if manifest["docs_profile"]["schema_version"] == 1
        else "reviewed-local-docs-v2"))
    expected = _run_campaign(manifest, docs_corpus=docs, evas_command="")
    # The command is bound to the engine profile/receipt; do not resolve a local
    # executable or run EVAS from this read-only evidence projection.
    digest = campaign.get("evas_command_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("combined evaluator command binding is missing")
    expected["evas_command_sha256"] = digest
    if campaign != expected:
        raise ValueError("combined campaign differs from frozen controls")
    return campaign


def _read_budget(root, manifest):
    """Validate the existing guard's serialized journal; never reserve or send."""
    from run_legacy_native_comparison import _source_path
    events = [json.loads(line) for line in _source_path(root, "budget.jsonl").read_text().splitlines()]
    profile = manifest["provider_profile"]
    pricing_date = (
        "2026-08-30"
        if profile.get("reviewed_on") == live_transport.PREVIOUS_REVIEWED_ON
        else PRICING_REVIEWED_ON
    )
    limit = manifest["controls"]["model_calls"] * manifest["controls"]["rounds"]
    expected = {"event": "opened", "cell_ids": manifest["budget_ids"], **manifest["budget"],
                "model": profile["model"], "model_call_limit_per_cell": limit,
                "input_miss_peak_per_million": profile["input_peak_per_million"],
                "output_peak_per_million": profile["output_peak_per_million"],
                "context_token_bound": profile["context_token_bound"],
                "max_output_tokens": profile["decoding"]["max_tokens"],
                "pricing_date": pricing_date, "may_enter_model_memory": False,
                "committed_upper_bound": "0"}
    if not events or events[0] != expected:
        raise ValueError("combined budget identity mismatch")
    calls = dict.fromkeys(manifest["budget_ids"], 0)
    costs = dict.fromkeys(calls, Decimal(0))
    reservations = dict.fromkeys(calls, 0)
    committed, stopped, censored, pending = Decimal(0), False, False, None
    for event in events[1:]:
        kind, key = event.get("event"), event.get("cell_id")
        value = Decimal(event["committed_upper_bound"])
        if (key not in calls or stopped or not value.is_finite()
                or not 0 <= value <= Decimal(manifest["budget"]["cap"])):
            raise ValueError("combined budget amount/order mismatch")
        expected_value = committed
        if kind == "model_call" and pending is None:
            calls[key] += 1
            if calls[key] > limit or type(event.get("model_call")) is not int or event["model_call"] != calls[key]:
                raise ValueError("combined budget call sequence mismatch")
        elif kind == "reserved" and pending is None:
            max_tokens = event.get("max_tokens")
            if (type(max_tokens) is not int or not 0 < max_tokens <= MAX_OUTPUT_TOKENS
                    or calls[key] < 1 or event.get("model_call") != calls[key]):
                raise ValueError("combined reservation call mismatch")
            reservation = (profile["context_token_bound"] * Decimal(profile["input_peak_per_million"])
                           + max_tokens * Decimal(profile["output_peak_per_million"])) / 1_000_000
            if Decimal(event["reservation"]) != reservation:
                raise ValueError("combined reservation amount mismatch")
            expected_value += reservation
            pending = (key, reservation)
            reservations[key] += 1
        elif kind == "reconciled" and pending is not None and pending[0] == key:
            measured = Decimal(event["request_upper_bound"])
            if (not measured.is_finite() or not 0 <= measured <= pending[1]
                    or not re.fullmatch(r"[0-9a-f]{64}", event.get("response_sha256", ""))):
                raise ValueError("combined reconciliation amount/response mismatch")
            expected_value -= pending[1] - measured
            pending = None
        elif kind == "cell_stopped" and pending is None:
            if event.get("reason") != "model_call_limit" or calls[key] != limit:
                raise ValueError("combined budget cell-stop mismatch")
            censored = True
        elif kind == "stopped":
            reason = event.get("reason")
            if not ((reason == "insufficient_reservation" and pending is None)
                    or (reason == "unknown_request_cost" and pending is not None and pending[0] == key)):
                raise ValueError("combined budget stop mismatch")
            stopped = censored = True
            pending = None  # Unknown costs retain the entire reservation.
        else:
            raise ValueError("combined budget event ordering mismatch")
        if value != expected_value:
            raise ValueError("combined budget accounting mismatch")
        costs[key] += value - committed
        committed = value
    if pending is not None:
        raise ValueError("combined budget has an unfinished reservation")
    return {"currency": manifest["budget"]["currency"], "guard_upper_bound": str(committed),
            "model_calls": sum(calls.values()), "transport_reservations": sum(reservations.values()),
            "censored": censored, "per_branch": [
                {"branch_id": key, "model_calls": calls[key], "transport_reservations": reservations[key],
                 "guard_upper_bound": str(costs[key])} for key in calls]}


def _execute(root, manifest, *, docs_corpus, evas_command, client_factory):
    from run_native_evolution import NativeEvolutionBranch, run_native_evolution
    from run_native_mini_swe import _backend_profile, run_prepared_native_mini_swe
    from runners.agent_harness import backend_profile_sha256

    _atomic_once(root / "execution-start.json", {
        "schema_version": "vaevas-combined-start-v1",
        "manifest_sha256": file_sha256(root / "combined-manifest.json"),
    })
    campaign = _run_campaign(manifest, docs_corpus=docs_corpus, evas_command=evas_command)
    _atomic_once(root / "campaign.json", campaign)
    campaign_sha = file_sha256(root / "campaign.json")
    controls, runtime = manifest["controls"], root / "run"
    intervention = manifest.get("intervention", INTERVENTIONS["rag-waveform"])
    enabled_docs = docs_corpus if intervention["offline_docs"] else None
    enabled_waveform = intervention["public_waveform"]
    disposition, error_type = "completed", None
    started = time.monotonic()
    with DeepSeekPilotBudget(root / "budget.jsonl", cell_ids=manifest["budget_ids"],
                            model_call_limit=controls["model_calls"] * controls["rounds"],
                            **manifest["budget"]) as budget:
        def client(key):
            return client_factory(budget=budget, cell_id=key, request_observer=lambda *args: None)

        try:
            if manifest["backend"] == "evolution":
                branches = [NativeEvolutionBranch(
                    key, MODEL, backend_profile_sha256(_backend_profile("native-reasoning")),
                    lambda key=key: client(key),
                ) for key in manifest["budget_ids"]]
                run_native_evolution(
                    cell=campaign["cell"], release=runner.DEFAULT_RELEASE, output_dir=runtime,
                    branches=branches, command=JUDGE_COMMAND, evas_command=evas_command,
                    rounds=controls["rounds"], max_steps=controls["model_calls"],
                    budgets=campaign["per_branch_budgets"], timeout_s=controls["watchdog_s"],
                    request_timeout_s=controls["watchdog_s"],
                    branch_docker_image=manifest["branch_image_id"],
                    public_validation_docker_image=manifest["image_id"],
                    deadline_monotonic=time.monotonic() + controls["wall_time_seconds"],
                    campaign_file_sha256=campaign_sha, max_workers=controls["branch_count"],
                    docs_corpus=enabled_docs, public_waveform=enabled_waveform,
                )
            else:
                runner.export_runtime(campaign["cell"], runner.DEFAULT_RELEASE, runtime,
                                      timeout_s=controls["watchdog_s"])
                run_prepared_native_mini_swe(
                    runtime=runtime, cell=campaign["cell"], client=client(manifest["budget_ids"][0]),
                    attempt_id=campaign["cell"]["cell_id"] + "-combined-0001",
                    evas_command=evas_command, final_judge_command=JUDGE_COMMAND,
                    docker_image=manifest["image_id"], campaign_file_sha256=campaign_sha,
                    episode_backend="native-reasoning", model_call_limit=controls["model_calls"],
                    tool_call_limit=controls["tool_calls"], docs_corpus=enabled_docs,
                    public_waveform_max_calls=(
                        controls["public_validation_calls"] if enabled_waveform else None
                    ),
                    request_timeout_s=controls["watchdog_s"], tool_timeout_s=controls["watchdog_s"],
                    judge_timeout_s=controls["watchdog_s"],
                )
        except Exception as exc:
            disposition = "budget_censored" if isinstance(exc, PilotBudgetStop) else "incomplete_evidence"
            error_type = type(exc).__name__
        finally:
            if budget.stopped:
                disposition = "budget_censored"
    if _read_budget(root, manifest)["censored"]:
        disposition = "budget_censored"
    files = ["combined-manifest.json", "campaign.json", "budget.jsonl", "execution-start.json"]
    if manifest["live"]:
        files.extend(["live-authorization.json", "provider-preflight.json"])
    _atomic_once(root / "execution.json", {
        "schema_version": "vaevas-combined-execution-v1", "disposition": disposition,
        "error_type": error_type, "elapsed_s": time.monotonic() - started,
        "files": {name: file_sha256(root / name) for name in files},
        "runtime_tree": _tree(runtime) if runtime.exists() else None,
    })
    report = read_combined(root)
    _atomic_once(root / "combined-report.json", report)
    return report


def read_combined(root: Path) -> dict:
    """Read existing terminal receipts only. Missing evidence is not a model zero."""
    from combined_tool_evidence import collect_feature_use
    import evolution_batch
    from score_campaign import read_native_cell

    manifest = _validate_frozen(root, current_source=False)
    intervention = manifest.get("intervention", INTERVENTIONS["rag-waveform"])
    result = {"schema_version": "vaevas-combined-report-v1", "backend": manifest["backend"],
              "manifest_sha256": file_sha256(root / "combined-manifest.json"),
              "evidence_scope": manifest["evidence_scope"], "scheduled": 1, "score": None,
              "intervention": intervention, "feature_use": None,
              "condition_acceptance_passed": False, "combined_acceptance_passed": False,
              "paid_requests": None if manifest["live"] else 0,
              "claim_scope": manifest["claim_scope"]}
    if not (root / "execution.json").exists():
        started = any((root / name).exists() for name in ("execution-start.json", "live-authorization.json"))
        return {**result, "disposition": "incomplete_evidence" if started else "prepared",
                "started": int(started), "terminal": 0, "cost": None}
    execution = _document(root, "execution.json")
    required = {"combined-manifest.json", "campaign.json", "budget.jsonl", "execution-start.json"}
    if manifest["live"]:
        required |= {"live-authorization.json", "provider-preflight.json"}
    if (execution.get("schema_version") != "vaevas-combined-execution-v1"
            or set(execution.get("files", {})) != required):
        raise ValueError("combined execution evidence is incomplete")
    for name, digest in execution["files"].items():
        if file_sha256(root / name) != digest:
            raise ValueError("combined evidence drift")
    if _document(root, "execution-start.json") != {
            "schema_version": "vaevas-combined-start-v1", "manifest_sha256": result["manifest_sha256"]}:
        raise ValueError("combined start manifest mismatch")
    if manifest["live"]:
        if _document(root, "live-authorization.json") != _authorization(root, manifest):
            raise ValueError("combined live authorization mismatch")
        live_transport.validate_provider_preflight(root, manifest)
    campaign = _read_campaign(root, manifest)
    runtime = root / "run"
    if execution["runtime_tree"] != (_tree(runtime) if runtime.exists() else None):
        raise ValueError("combined runtime evidence drift")
    cost = _read_budget(root, manifest)
    if (execution["disposition"] not in {"completed", "incomplete_evidence", "budget_censored"}
            or (cost["censored"] and execution["disposition"] != "budget_censored")):
        raise ValueError("combined execution/budget disposition mismatch")
    result.update(disposition=execution["disposition"], started=1, terminal=1,
                  cost=cost)
    if execution["disposition"] != "completed":
        return result
    if manifest["backend"] == "evolution":
        terminal = evolution_batch.validate_terminal_result(
            runtime, expected_source_cell_id=manifest["source_cell"]["cell_id"], expected_campaign=campaign)
        judgment = terminal.get("final_judgment") or {}
        result.update(score=judgment.get("score"), engine_status=terminal["status"],
                      denominator=terminal.get("denominator"), all_branch_costs=terminal.get("all_branch_costs"))
    else:
        terminal = read_native_cell(runtime, campaign["cell"],
                                    campaign_file_sha256=file_sha256(root / "campaign.json"))
        result.update(score=terminal.get("score"), engine_status=terminal["terminal_reason"])
    expected_features = {
        "offline_docs": intervention["offline_docs"],
        "public_waveform": intervention["public_waveform"],
    }
    result["feature_use"] = collect_feature_use(
        runtime,
        backend=manifest["backend"],
        expected_features=expected_features,
    )
    features = result["feature_use"]["features"]
    observed = all(
        (features[name].get("succeeded", 0) > 0 and not features[name].get("incomplete"))
        if enabled else (
            features[name].get("attempted") == 0
            and features[name].get("succeeded") == 0
            and features[name].get("feedback_exposed_requests") == 0
            and not features[name].get("incomplete")
        )
        for name, enabled in expected_features.items()
    )
    shared = (
        not intervention["public_waveform"]
        or manifest["backend"] != "evolution"
        or features["public_waveform"].get("feedback_exposed_requests", 0) > 0
    )
    result["condition_acceptance_passed"] = bool(observed and shared and result["score"] is not None)
    result["combined_acceptance_passed"] = bool(
        intervention["name"] == "rag-waveform" and result["condition_acceptance_passed"]
    )
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="freeze live configuration without key or HTTP access")
    prepare.add_argument("--backend", choices=BACKENDS, required=True)
    prepare.add_argument("--family-id", default="001")
    prepare.add_argument("--form", choices=("dut", "bugfix", "testbench"), default="dut")
    prepare.add_argument("--currency", choices=("CNY", "USD"), required=True)
    prepare.add_argument("--cap", required=True)
    prepare.add_argument("--image", default="vabench-agent-runtime:0.8.7")
    prepare.add_argument("--branch-image", default="vabench-agent-runtime:0.8.7-no-evas")
    prepare.add_argument("--rounds", type=int, default=2)
    prepare.add_argument("--branch-count", type=int, default=2)
    prepare.add_argument("--model-calls", type=int, default=8)
    prepare.add_argument("--tool-calls", type=int, default=8)
    prepare.add_argument("--public-calls", type=int, default=1)
    prepare.add_argument("--intervention", choices=tuple(INTERVENTIONS), default="rag-waveform")
    commands.add_parser("inspect", help="read preparation; no corpus or provider access")
    commands.add_parser("report", help="validate existing evidence; never run another final judge")
    run = commands.add_parser("run", help="explicitly asserted one-use potentially paid execution")
    run.add_argument("--expected-manifest-sha256", required=True)
    run.add_argument("--approve-cap", required=True)
    run.add_argument("--currency", choices=("CNY", "USD"), required=True)
    run.add_argument("--credential-file", type=Path, required=True)
    for command in (prepare, run):
        command.add_argument("--docs-root", type=Path, required=True)
        command.add_argument("--docs-manifest", type=Path, required=True)
        command.add_argument("--evas-command", required=True)
    for command in commands.choices.values():
        command.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command in {"prepare", "run"}:
            docs = OfflineDocsCorpus.from_manifest(args.docs_root, json.loads(args.docs_manifest.read_text()))
        if args.command == "prepare":
            live_transport.clear_provider_environment()
            freeze_combined(
                args.output_root, backend=args.backend, family_id=args.family_id, form=args.form,
                docs_corpus=docs, image_id=live_transport.docker_image_identity(args.image),
                branch_image_id=live_transport.docker_image_identity(args.branch_image),
                evas_identity=runner.resolve_pinned_evas_identity(args.evas_command),
                currency=args.currency, cap=args.cap, live=True, rounds=args.rounds,
                branch_count=args.branch_count, model_calls=args.model_calls,
                tool_calls=args.tool_calls, public_calls=args.public_calls,
                intervention=args.intervention,
            )
            result = inspect_combined(args.output_root)
        elif args.command == "run":
            result = execute_live(
                args.output_root, docs_corpus=docs, evas_command=args.evas_command,
                expected_manifest_sha256=args.expected_manifest_sha256,
                approved_cap=args.approve_cap, currency=args.currency, credential_file=args.credential_file,
            )
        elif args.command == "report":
            result = read_combined(args.output_root)
        else:
            result = inspect_combined(args.output_root)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 2 if args.command == "run" and result["disposition"] != "completed" else 0
    except Exception:
        print("Combined command failed; inspect frozen configuration/private evidence. No automatic retry.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
