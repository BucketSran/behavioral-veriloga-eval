"""Real provider entrypoint and Docker-backed Evolution integration."""

from copy import deepcopy
import importlib
import json
import os
import shlex
import sys
import time
from types import SimpleNamespace

import pytest

from scripts import run_v4_r53_clean_room_smoke as smoke


def _campaign(tmp_path, form="dut"):
    campaign = smoke.campaign_builder.build_campaign(
        smoke.DEFAULT_RELEASE, family_ids=["001"], model_provider="fixture",
        model="placeholder", per_turn_max_tokens=4096, repetitions=1,
        three_arm_g0_g2=True,
    )
    path = tmp_path / "source-campaign.json"
    path.write_text(json.dumps(campaign))
    cell = next(cell for cell in campaign["cells"]
                if cell["form"] == form and cell["experimental_arm"] == "Agentic")
    return path, cell


def test_evolution_cli_dry_run_freezes_real_model_roster_without_credentials(tmp_path, monkeypatch):
    entry = importlib.import_module("run_evolution_campaign")
    def forbidden(*args, **kwargs):
        raise AssertionError("dry-run must not initialize providers or EVAS")
    monkeypatch.setattr(entry.runner, "OpenAICompatible", forbidden)
    monkeypatch.setattr(entry.runner, "resolve_pinned_evas_identity", forbidden)
    campaign, cell = _campaign(tmp_path)
    roster = tmp_path / "branches.json"
    roster.write_text(json.dumps([
        {"branch_id": "a", "model": "local-a", "base_url": "http://127.0.0.1:8000/v1"},
        {"branch_id": "b", "model": "api-b", "base_url": "https://provider.invalid/v1",
         "api_key_env": "UNSET_EVOLUTION_FIXTURE_KEY"},
    ]))
    output = tmp_path / "evolution"
    assert entry.main([
        "--campaign", str(campaign), "--cell", cell["cell_id"],
        "--branches-json", str(roster), "--output-root", str(output),
        "--rounds", "2", "--dry-run",
    ]) == 0
    frozen = json.loads((output / "campaign.json").read_text())
    assert frozen["condition"] == "AlphaApollo-Evolution+EVAS"
    assert [branch["model"] for branch in frozen["branches"]] == ["local-a", "api-b"]
    assert frozen["source_campaign_sha256"] == smoke.sha256_file(campaign)
    assert all("base_url" not in branch and len(branch["endpoint_sha256"]) == 64
               for branch in frozen["branches"])
    assert not (output / "run").exists()


def test_evolution_cli_wires_actual_provider_factories_without_network(tmp_path, monkeypatch):
    entry = importlib.import_module("run_evolution_campaign")
    campaign, cell = _campaign(tmp_path)
    roster = tmp_path / "roster.json"
    roster.write_text(json.dumps([{
        "branch_id": "a", "model": "real-api-name", "base_url": "https://provider.invalid/v1",
        "api_key_env": "EVOLUTION_FIXTURE_KEY",
    }]))
    monkeypatch.setenv("EVOLUTION_FIXTURE_KEY", "fixture-secret-value")
    monkeypatch.setattr(entry.runner, "resolve_pinned_evas_identity", lambda _: {})
    observed = []

    def execute(**kwargs):
        observed.append(kwargs)
        client = kwargs["branches"][0].client_factory()
        assert isinstance(client, entry.runner.OpenAICompatible)
        assert client.model == "real-api-name"
        assert client.api_key == "fixture-secret-value"
        assert "EVOLUTION_FIXTURE_KEY" not in os.environ
        assert kwargs["public_validation_profile"] is None
        assert kwargs["final_test_profile"] is None
        return SimpleNamespace(manifest_sha256="a" * 64)

    monkeypatch.setattr(entry, "run_native_evolution", execute)
    output = tmp_path / "out"
    assert entry.main([
        "--campaign", str(campaign), "--cell", cell["cell_id"], "--branches-json", str(roster),
        "--output-root", str(output), "--evas-command", "/fixture/evas",
    ]) == 0
    assert len(observed) == 1
    assert "fixture-secret-value" not in (output / "campaign.json").read_text()
    assert observed[0]["campaign_file_sha256"] == smoke.sha256_file(output / "campaign.json")


def test_evolution_cli_rejects_credentials_in_roster(tmp_path):
    entry = importlib.import_module("run_evolution_campaign")
    campaign, cell = _campaign(tmp_path)
    roster = tmp_path / "branches.json"
    roster.write_text(json.dumps([{
        "branch_id": "a", "model": "a", "base_url": "https://user:secret@example.invalid",
    }]))
    with pytest.raises(ValueError, match="credential"):
        entry.main([
            "--campaign", str(campaign), "--cell", cell["cell_id"],
            "--branches-json", str(roster), "--output-root", str(tmp_path / "out"), "--dry-run",
        ])
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("form", ["dut", "bugfix", "testbench"])
def test_r53_docker_native_evolution_selected_final_only(tmp_path, form):
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in real Docker/EVAS Evolution integration")
    import run_native_evolution as evolution
    from run_native_mini_swe import _backend_profile
    from runners.agent_harness import backend_profile_sha256
    from test_agent_harness_native_launcher import Provider

    _, original = _campaign(tmp_path, form)
    cell = {**original, "experimental_arm": "AlphaApollo-Evolution+EVAS"}
    artifacts = smoke.public_stub_artifacts(smoke.public_contract(smoke.DEFAULT_RELEASE, cell["task_id"]))
    clients = []

    def factory(model):
        commands = [
            "test ! -r /runtime/evaluator/check.py",
            *[f"printf %s {shlex.quote(content + '// candidate ' + model + chr(10))} > public/submission/{name}"
              for name, content in artifacts.items()],
            "vabench-submit",
        ]
        client = Provider(commands)
        client.model = model
        clients.append(client)
        return client

    branches = [evolution.NativeEvolutionBranch(
        branch_id=model, model_ref=model,
        backend_profile_sha256=backend_profile_sha256(_backend_profile("native-reasoning")),
        client_factory=lambda model=model: factory(model),
    ) for model in ("model-a", "model-b")]
    run = evolution.run_native_evolution(
        cell=cell, release=smoke.DEFAULT_RELEASE, output_dir=tmp_path / "run",
        branches=branches, public_validation_profile=None, final_test_profile=None,
        command=shlex.join([sys.executable, str(smoke.CALIBRATION / "trusted_replay_adapter.py")]),
        evas_command=str(smoke.ROOT / ".venv/bin/evas"),
        rounds=2, max_steps=5, budgets={"model_calls": 5, "tool_calls": 5, "public_validation_calls": 1},
        request_timeout_s=15, timeout_s=120, deadline_monotonic=time.monotonic() + 120,
        campaign_file_sha256="c" * 64,
    )
    assert len(clients) == 4
    assert len(run.evolution_result.round_snapshots) == 2
    assert run.final_judgment.status == "behavior_failure"
    assert run.score_sidecar_receipt
    assert run.final_judgment.submission_tree_sha256 == run.selected_candidate["candidate_tree_sha256"]
    assert len(list((tmp_path / "run").rglob("final_submission"))) == 1
    assert not list((tmp_path / "run/evolution/branches").rglob("bound-final-test"))
    assert run.evolution_result.usage["public_validation_calls"] == 4
    assert run.evolution_result.usage["model_calls"] == sum(len(client.requests) for client in clients)
    round_one_requests = [json.dumps(client.requests[0]) for client in clients[2:]]
    assert all("candidate model-a" in request and "candidate model-b" in request
               for request in round_one_requests)
    assert "final_judgment" not in json.dumps(deepcopy(run.evolution_result.memory_snapshots), default=dict)
    result = json.loads((tmp_path / "run/final-result.json").read_text())
    assert result["denominator"] == {"scheduled_cells": 1, "scheduled_branches": 4, "observed_branches": 4}
    assert result["all_branch_costs"]["model_calls"]["total"] == sum(len(client.requests) for client in clients)
    assert result["all_branch_costs"]["public_validation_calls"]["total"] == 4
    assert len(result["branch_evidence"]) == 4
    for branch in (tmp_path / "run/evolution/branches").glob("round-*/*/branch-runtime.json"):
        prepared = json.loads(branch.read_text())
        assert prepared["observed_image_id"].startswith("sha256:")
        assert prepared["executable_feedback"] is False
    smoke.write_immutable_json(tmp_path / "evolution-smoke-index.json", {
        "status": "PASS", "claim_scope": "connectivity_only", "form": form, "branch_count": 2, "rounds": 2,
        "selected_candidate": dict(run.selected_candidate),
        "manifest_sha256": run.manifest_sha256,
        "final_result_sha256": smoke.sha256_file(tmp_path / "run/final-result.json"),
    })
