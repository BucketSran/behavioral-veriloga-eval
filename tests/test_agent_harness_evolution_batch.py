"""Evolution batch recovery preserves completed cells and retry lineage."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
sys.path.insert(0, str(CALIBRATION))

import result_protocol  # noqa: E402
from runners.agent_harness import (  # noqa: E402
    final_test_profile_sha256, profile_input_identity_sha256, public_validation_profile_sha256,
)
from scripts import run_v4_r53_clean_room_smoke as smoke  # noqa: E402

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64
SHA_F = "f" * 64


def _campaign(tmp_path: Path, count: int = 1) -> tuple[Path, list[dict]]:
    campaign = smoke.campaign_builder.build_campaign(
        smoke.DEFAULT_RELEASE,
        family_ids=["001", "002"][:count],
        model_provider="fixture",
        model="placeholder",
        per_turn_max_tokens=4096,
        repetitions=1,
        three_arm_g0_g2=True,
    )
    path = tmp_path / "source-campaign.json"
    path.write_text(json.dumps(campaign), encoding="utf-8")
    cells = [
        cell for cell in campaign["cells"]
        if cell["form"] == "dut" and cell["experimental_arm"] == "Agentic"
    ][:count]
    return path, cells


def _roster(tmp_path: Path) -> Path:
    path = tmp_path / "branches.json"
    path.write_text(
        json.dumps([
            {
                "branch_id": "a",
                "model": "fixture-model",
                "base_url": "https://provider.invalid/v1",
                "api_key_env": "EVOLUTION_BATCH_KEY",
            },
        ]),
        encoding="utf-8",
    )
    return path


def _latest_index(output: Path) -> dict:
    return json.loads(sorted((output / ".batch").glob("index-*.json"))[-1].read_text())


def _final_profile(*, campaign_config_sha256: str) -> dict:
    return {
        "schema_version": "vaevas-final-test-profile-v1",
        "profile_id": "r53/evas-0.8.7-final-test",
        "benchmark_release": "benchmarkv4-r53",
        "benchmark_manifest_sha256": SHA_A,
        "judge": {"engine": "evas", "version": "0.8.7"},
        "judge_identity_sha256": SHA_B,
        "checker_identity_sha256": SHA_C,
        "runtime_identity_sha256": SHA_D,
        "campaign_config_sha256": campaign_config_sha256,
        "command_signature_sha256": SHA_F,
        "authority_phase": "post_submission_freeze_only",
        "visibility": "trusted_only",
        "model_observation_allowed": False,
        "memory_entry_allowed": False,
        "candidate_selection_allowed": False,
        "repair_allowed": False,
        "input_scope": "frozen_submission_tree",
        "submission_binding_required": True,
        "score_sidecar_required": True,
        "structured_result_contract": {
            "schema_id": "vaevas-structured-result-v1",
            "requires_structured_verdict": True,
        },
        "score_sidecar_contract": {
            "schema_id": "vaevas-score-sidecar-v1",
            "immutable": True,
            "binds_submission_tree": True,
            "score_authority": "development_only",
        },
        "spectre_policy": {
            "required": False,
            "trigger": "conditional_evas_or_external_protocol_change",
            "spectre_judge_identity_sha256": None,
            "spectre_command_signature_sha256": None,
            "spectre_report_schema_id": None,
        },
    }


def _fixture_config(run_dir, cell):
    import run_native_evolution as engine
    from test_agent_harness_native_evolution import REASONING_BACKEND_SHA
    campaign = json.loads((run_dir.parent / "campaign.json").read_text())
    config = engine._native_evolution_config_document(
        cell=cell, release=smoke.DEFAULT_RELEASE, output_dir=run_dir.resolve(),
        branches=[engine.NativeEvolutionBranch(
            item["branch_id"], item["model"], REASONING_BACKEND_SHA, lambda: None,
        ) for item in campaign["branches"]], condition=cell["experimental_arm"],
        budgets=campaign["per_branch_budgets"], rounds=campaign["rounds"],
        max_steps=campaign["per_branch_budgets"]["model_calls"],
        timeout_s=campaign["timeout_s"], request_timeout_s=campaign["request_timeout_s"],
        branch_sandbox_backend="docker", branch_docker_image=campaign["branch_docker_image"],
        public_validation_docker_image=campaign["public_validation_docker_image"],
        command=shlex.join([sys.executable, str(CALIBRATION / "trusted_replay_adapter.py")]),
        evas_command="/fixture/evas", campaign_file_sha256=smoke.sha256_file(run_dir.parent / "campaign.json"),
    )
    config["declared_information_surface"] = engine.runner.declared_information_surface(
        cell["experimental_arm"], evolution=True,
    )
    return config


def _write_completed_evolution_result(run_dir: Path, *, cell: dict, score: float = 0.0,
                                      wrong_rounds: bool = False) -> None:
    from run_native_evolution import _canonical_sha256
    from test_agent_harness_native_evolution import _profile
    config = _fixture_config(run_dir, cell)
    if wrong_rounds:
        config["rounds"] += 1
    campaign_config_sha256 = _canonical_sha256(config)
    final_profile = _final_profile(campaign_config_sha256=campaign_config_sha256)
    public_profile = _profile("public", campaign_config_sha256=campaign_config_sha256)
    public_profile["benchmark_manifest_sha256"] = final_profile["benchmark_manifest_sha256"]
    submission_root = run_dir / "final-runtime/evidence/final_submission"
    submission_root.mkdir(parents=True)
    (submission_root / "candidate.va").write_text(
        "// public candidate\n",
        encoding="utf-8",
    )
    submission_sha256 = result_protocol.hash_test_tree(submission_root)["tree_sha256"]
    request = {
        "schema_version": "vaevas-native-evolution-request-v1",
        "manifest_sha256": SHA_A,
        "campaign_config_sha256": campaign_config_sha256,
        "campaign_file_sha256": smoke.sha256_file(run_dir.parent / "campaign.json"),
        "cell": cell,
        "config": config,
        "public_validation_profile_sha256": public_validation_profile_sha256(public_profile),
        "final_test_profile_sha256": final_test_profile_sha256(final_profile),
    }
    sidecar = {
        "schema_version": "vaevas-score-sidecar-v1",
        "benchmark_release": "benchmarkv4-r53",
        "benchmark_manifest_sha256": SHA_A,
        "score_authority": "development_only",
        "immutable": True,
        "binds_submission_tree": True,
        "submission_tree_sha256": submission_sha256,
        "judge": {"engine": "evas", "version": "0.8.7", "identity_sha256": SHA_B},
        "checker_identity_sha256": SHA_C,
        "runtime_identity_sha256": SHA_D,
        "campaign_config_sha256": campaign_config_sha256,
        "command_signature_sha256": SHA_F,
        "structured_result": {"status": "behavior_failure", "score": score},
        "model_observation_allowed": False,
        "memory_entry_allowed": False,
    }
    (run_dir / "final-runtime/evidence/score-sidecars").mkdir(parents=True)
    (run_dir / "public-validation-profile.json").write_text(json.dumps(public_profile), encoding="utf-8")
    (run_dir / "final-test-profile.json").write_text(json.dumps(final_profile), encoding="utf-8")
    (run_dir / "request.json").write_text(json.dumps(request), encoding="utf-8")
    (run_dir / "setup-request.json").write_text(json.dumps({
        "schema_version": "vaevas-native-evolution-setup-v1", "config": config,
        "campaign_file_sha256": request["campaign_file_sha256"],
    }))
    sidecar_bytes = json.dumps(sidecar, sort_keys=True, separators=(",", ":")).encode()
    sidecar_sha = hashlib.sha256(sidecar_bytes).hexdigest()
    sidecar_path = run_dir / "final-runtime/evidence/score-sidecars" / f"{sidecar_sha}.json"
    sidecar_path.write_bytes(sidecar_bytes)
    final = {
        "schema_version": "vaevas-native-evolution-final-result-v1",
        "status": "completed",
        "manifest_sha256": SHA_A,
        "campaign_config_sha256": campaign_config_sha256,
        "selected_candidate": {
            "candidate_id": "a-round-0000",
            "branch_id": "a",
            "round_index": 0,
            "candidate_tree_sha256": submission_sha256,
        },
        "final_judgment": {
            "status": "behavior_failure",
            "judge_engine": "evas",
            "score": score,
            "submission_tree_sha256": submission_sha256,
        },
        "score_sidecar_receipt": {
            "path": sidecar_path.relative_to(run_dir / "final-runtime").as_posix(),
            "sha256": sidecar_sha,
            "submission_tree_sha256": submission_sha256,
            "final_profile_sha256": final_test_profile_sha256(final_profile),
            "final_profile_input_identity_sha256": profile_input_identity_sha256(
                profile_sha256=final_test_profile_sha256(final_profile), input_kind="frozen_submission_tree",
                input_sha256=submission_sha256, attempt_id="a-round-0000-final", task_id=cell["task_id"],
            ),
            "episode_id": "a-round-0000/final",
            "attempt_id": "a-round-0000-final",
            "task_id": cell["task_id"],
        },
        "branch_usage": {"model_calls": 1, "public_validation_calls": 1},
        "branch_record_count": 1,
        "failure_retryable": False,
    }
    (run_dir / "final-result.json").write_text(json.dumps(final), encoding="utf-8")


def _write_forged_completed_evolution_result(run_dir: Path, *, score: float = 0.0) -> None:
    sidecar = {
        "schema_id": "vaevas-score-sidecar-v1",
        "score_authority": "development_only",
        "judge_engine": "evas",
        "judge_version": "0.8.7",
        "submission_tree_sha256": "b" * 64,
        "structured_result": {"status": "behavior_failure", "score": score},
    }
    sidecar_bytes = json.dumps(sidecar, sort_keys=True, separators=(",", ":")).encode()
    sidecar_sha = hashlib.sha256(sidecar_bytes).hexdigest()
    sidecar_path = run_dir / "final-runtime/evidence/score-sidecars" / f"{sidecar_sha}.json"
    sidecar_path.parent.mkdir(parents=True)
    sidecar_path.write_bytes(sidecar_bytes)
    (run_dir / "final-runtime/public/submission").mkdir(parents=True)
    (run_dir / "final-runtime/public/submission/candidate.va").write_text(
        "// public candidate\n",
        encoding="utf-8",
    )
    final = {
        "schema_version": "vaevas-native-evolution-final-result-v1",
        "status": "completed",
        "manifest_sha256": "a" * 64,
        "campaign_config_sha256": "c" * 64,
        "selected_candidate": {
            "candidate_id": "a-round-0000",
            "branch_id": "a",
            "round_index": 0,
            "candidate_tree_sha256": "b" * 64,
        },
        "final_judgment": {
            "status": "behavior_failure",
            "judge_engine": "evas",
            "score": score,
            "submission_tree_sha256": "b" * 64,
        },
        "score_sidecar_receipt": {
            "path": sidecar_path.relative_to(run_dir / "final-runtime").as_posix(),
            "sha256": sidecar_sha,
            "submission_tree_sha256": "b" * 64,
            "final_profile_sha256": "d" * 64,
            "final_profile_input_identity_sha256": "e" * 64,
            "episode_id": "a-round-0000/final",
            "attempt_id": "a-round-0000-final",
            "task_id": "v4-001",
        },
        "branch_usage": {"model_calls": 1, "public_validation_calls": 1},
        "branch_record_count": 1,
        "failure_retryable": False,
    }
    (run_dir / "final-result.json").write_text(json.dumps(final), encoding="utf-8")


def _write_setup_failed_result(run_dir: Path) -> None:
    from run_native_evolution import _canonical_sha256, _evolution_evidence_summary
    campaign = json.loads((run_dir.parent / "campaign.json").read_text())
    config = _fixture_config(run_dir, campaign["cell"])
    run_dir.mkdir(parents=True)
    final = {
        "schema_version": "vaevas-native-evolution-final-result-v1",
        "status": "setup_failed",
        "manifest_sha256": None,
        "campaign_config_sha256": _canonical_sha256(config),
        "selected_candidate": None,
        "final_judgment": None,
        "score_sidecar_receipt": None,
        "branch_usage": None,
        "branch_record_count": None,
        "failure_retryable": True,
        "failure_phase": "setup",
    }
    (run_dir / "setup-request.json").write_text(json.dumps({
        "schema_version": "vaevas-native-evolution-setup-v1", "config": config,
        "campaign_file_sha256": smoke.sha256_file(run_dir.parent / "campaign.json"),
    }), encoding="utf-8")
    final.update(_evolution_evidence_summary(run_dir))
    (run_dir / "final-result.json").write_text(json.dumps(final), encoding="utf-8")


@pytest.mark.parametrize("entry_name", ["unexpected", "attempt-0002", "attempt-0001-extra"])
def test_attempt_scan_rejects_unaccounted_paths(tmp_path, entry_name):
    batch = importlib.import_module("evolution_batch")
    runtime = tmp_path / "cell"
    (runtime / entry_name).mkdir(parents=True)
    with pytest.raises(ValueError, match="attempt path"):
        batch.attempt_records(runtime, expected_source_cell_id="cell", expected_campaign={})


@pytest.mark.parametrize("previous_status", ["completed", "in_flight", "unsafe_setup"])
def test_attempt_scan_rejects_continuation_after_unsafe_boundary(tmp_path, monkeypatch, previous_status):
    batch = importlib.import_module("evolution_batch")
    runtime = tmp_path / "cell"
    for index in (1, 2):
        attempt = batch.attempt_dir(runtime, index)
        (attempt / "run").mkdir(parents=True)
        campaign = {"parent_attempt_id": batch.attempt_id("cell", 1) if index == 2 else None}
        (attempt / "campaign.json").write_text(json.dumps(campaign))
        if index == 2 or previous_status != "in_flight":
            (attempt / "run/final-result.json").write_text("{}")
    monkeypatch.setattr(batch, "validate_terminal_result", lambda *_args, **_kwargs: {
        "status": "completed" if previous_status == "completed" else "setup_failed",
    })
    monkeypatch.setattr(batch, "safe_setup_retry", lambda *_args, **_kwargs: False)
    with pytest.raises(ValueError, match="unsafe.*predecessor"):
        batch.attempt_records(runtime, expected_source_cell_id="cell", expected_campaign={})


def test_attempt_scan_rejects_frozen_cap_overflow(tmp_path):
    batch = importlib.import_module("evolution_batch")
    (tmp_path / "attempt-0001").mkdir()
    (tmp_path / "attempt-0002").mkdir()
    with pytest.raises(ValueError, match="attempt cap"):
        batch.attempt_records(tmp_path, expected_source_cell_id="cell", expected_campaign={}, max_attempts=1)


def test_evolution_executes_and_records_frozen_public_image(tmp_path):
    import run_native_evolution as engine
    from test_agent_harness_native_evolution import (
        REASONING_BACKEND_SHA, _fake_ops, _ScriptedReasoningClient,
    )

    ops, *_unused, environments = _fake_ops(tmp_path)
    image = "sha256:" + "2" * 64
    engine.run_native_evolution(
        cell={"cell_id": "cell", "task_id": "task", "mode": "G2"},
        release=tmp_path / "release", output_dir=tmp_path / "run",
        branches=[engine.NativeEvolutionBranch(
            "branch-good", "fixture", REASONING_BACKEND_SHA,
            lambda: _ScriptedReasoningClient("fixture", ["write", "vabench-submit"]),
        )], command="fake-final", evas_command="fake-evas", rounds=1, max_steps=2,
        budgets={"model_calls": 3, "tool_calls": 3, "public_validation_calls": 1},
        ops=ops, public_validation_docker_image=image,
    )
    assert [row["docker_image"] for row in environments if row["branch"] is None] == [image]
    request = json.loads((tmp_path / "run/request.json").read_text())
    assert request["config"]["public_validation"]["docker_image"] == image


def test_batch_dry_run_freezes_all_cells_without_clients_or_evas(tmp_path, monkeypatch):
    entry = importlib.import_module("run_evolution_campaign")
    campaign, cells = _campaign(tmp_path, count=2)
    roster = _roster(tmp_path)
    output = tmp_path / "batch"

    def forbidden(*_args, **_kwargs):
        raise AssertionError("batch dry-run must not initialize providers or EVAS")

    monkeypatch.setattr(entry.runner, "OpenAICompatible", forbidden)
    monkeypatch.setattr(entry.runner, "resolve_pinned_evas_identity", forbidden)

    assert entry.main([
        "--campaign", str(campaign),
        "--branches-json", str(roster),
        "--output-root", str(output),
        "--batch",
        "--dry-run",
        "--cell", cells[0]["cell_id"],
        "--cell", cells[1]["cell_id"],
    ]) == 0

    batch_manifest = json.loads((output / ".batch/manifest.json").read_text())
    assert batch_manifest["cell_ids"] == [cell["cell_id"] for cell in cells]
    frozen = batch_manifest["manifest"]
    assert frozen["dry_run"] is True
    assert frozen["evaluator"]["command_sha256"] == hashlib.sha256(b"").hexdigest()
    assert frozen["observed_images"] == {}
    assert frozen["request_timeout_s"] > 0
    assert frozen["timeout_s"] > 0
    assert frozen["wall_time_seconds"] > 0
    index = json.loads((output / ".batch/index-000000.json").read_text())
    assert [row["status"] for row in index["rows"]] == ["prepared", "prepared"]
    assert not list(output.glob("*/attempt-*"))


@pytest.mark.parametrize("interrupt_receipt", [False, True])
def test_batch_resume_reuses_completed_zero_score_without_provider_or_judge(tmp_path, monkeypatch, interrupt_receipt):
    entry = importlib.import_module("run_evolution_campaign")
    campaign, (cell,) = _campaign(tmp_path)
    roster = _roster(tmp_path)
    output = tmp_path / "batch"
    calls = []

    monkeypatch.setenv("EVOLUTION_BATCH_KEY", "fixture-secret")
    monkeypatch.setattr(entry.runner, "resolve_pinned_evas_identity", lambda _: {})
    monkeypatch.setattr(entry, "docker_image_identity", lambda *_args, **_kwargs: "sha256:" + "1" * 64)

    def fake_run(**kwargs):
        calls.append(kwargs)
        _write_completed_evolution_result(kwargs["output_dir"], cell=kwargs["cell"], score=0.0)
        return SimpleNamespace(manifest_sha256="a" * 64)

    monkeypatch.setattr(entry, "run_native_evolution", fake_run)
    command = [
        "--campaign", str(campaign), "--branches-json", str(roster),
        "--output-root", str(output), "--batch", "--cell", cell["cell_id"],
        "--evas-command", "/fixture/evas",
    ]
    if interrupt_receipt:
        with monkeypatch.context() as patch:
            def interrupted(*_args, **_kwargs):
                raise KeyboardInterrupt("after terminal, before batch receipt")
            patch.setattr(entry.BatchRun, "record", interrupted)
            with pytest.raises(KeyboardInterrupt):
                entry.main(command)
    else:
        assert entry.main(command) == 0
    assert len(calls) == 1
    assert calls[0]["public_validation_docker_image"] == "sha256:" + "1" * 64
    if not interrupt_receipt:
        assert _latest_index(output)["rows"][0]["score"] == 0.0

    def forbidden(*_args, **_kwargs):
        raise AssertionError("completed batch cell must be reused without calls")

    monkeypatch.setattr(entry, "run_native_evolution", forbidden)
    monkeypatch.setattr(entry.runner, "resolve_pinned_evas_identity", forbidden)
    assert entry.main([
        "--campaign", str(campaign), "--branches-json", str(roster),
        "--output-root", str(output), "--batch", "--resume", "--cell", cell["cell_id"],
        "--evas-command", "/fixture/evas",
    ]) == 0
    second_index = _latest_index(output)
    assert second_index["rows"][0]["batch_reuse"] is True
    assert second_index["rows"][0]["terminal_status"] == "completed"
    assert second_index["rows"][0]["score"] == 0.0


def test_batch_resume_blocks_unknown_in_flight_cell_before_credentials(tmp_path, monkeypatch):
    entry = importlib.import_module("run_evolution_campaign")
    campaign, cells = _campaign(tmp_path, count=2)
    roster = _roster(tmp_path)
    output = tmp_path / "batch"

    monkeypatch.setenv("EVOLUTION_BATCH_KEY", "fixture-secret")
    monkeypatch.setattr(entry.runner, "resolve_pinned_evas_identity", lambda _: {})
    monkeypatch.setattr(entry, "docker_image_identity", lambda *_args, **_kwargs: "sha256:" + "1" * 64)

    def interrupted(**kwargs):
        (kwargs["output_dir"] / "setup-request.json").mkdir(parents=True)
        raise RuntimeError("lost before terminal result")

    monkeypatch.setattr(entry, "run_native_evolution", interrupted)
    with pytest.raises(RuntimeError, match="lost before terminal"):
        entry.main([
            "--campaign", str(campaign), "--branches-json", str(roster),
            "--output-root", str(output), "--batch",
            "--cell", cells[0]["cell_id"], "--cell", cells[1]["cell_id"],
            "--evas-command", "/fixture/evas",
        ])

    def forbidden(*_args, **_kwargs):
        raise AssertionError("blocked batch must not initialize providers, keys, or EVAS")

    monkeypatch.delenv("EVOLUTION_BATCH_KEY", raising=False)
    monkeypatch.setattr(entry.runner, "OpenAICompatible", forbidden)
    monkeypatch.setattr(entry.runner, "load_key", forbidden)
    monkeypatch.setattr(entry.runner, "resolve_pinned_evas_identity", forbidden)
    with pytest.raises(ValueError, match="terminal result"):
        entry.main([
        "--campaign", str(campaign), "--branches-json", str(roster),
        "--output-root", str(output), "--batch", "--resume",
        "--cell", cells[0]["cell_id"], "--cell", cells[1]["cell_id"],
        "--evas-command", "/fixture/evas",
        ])
    index = _latest_index(output)
    assert index["rows"][0]["status"] == "blocked"
    assert index["rows"][0]["block_reason"] == "existing_attempt_without_terminal_result"
    assert index["rows"][1]["status"] == "scheduled"


def test_batch_corrupt_receipt_keeps_full_blocked_index_before_credentials(tmp_path, monkeypatch):
    entry = importlib.import_module("run_evolution_campaign")
    campaign, cells = _campaign(tmp_path, count=2)
    roster = _roster(tmp_path)
    output = tmp_path / "batch"
    monkeypatch.setattr(entry, "docker_image_identity", lambda *_args, **_kwargs: "sha256:" + "1" * 64)

    def corrupt_read(_self, cell_id, _runtime):
        if cell_id == cells[0]["cell_id"]:
            raise ValueError("corrupt terminal receipt")
        return None

    def forbidden(*_args, **_kwargs):
        raise AssertionError("a blocked batch must not initialize credentials")

    monkeypatch.setattr(entry.BatchRun, "read", corrupt_read)
    monkeypatch.setattr(entry.runner, "load_key", forbidden)
    with pytest.raises(ValueError, match="invalid_existing_attempt_evidence"):
        entry.main([
            "--campaign", str(campaign), "--branches-json", str(roster),
            "--output-root", str(output), "--batch", "--evas-command", "/fixture/evas",
            "--cell", cells[0]["cell_id"], "--cell", cells[1]["cell_id"],
        ])
    assert [row["status"] for row in _latest_index(output)["rows"]] == ["blocked", "scheduled"]


def test_batch_retries_safe_setup_failure_in_same_run_with_parent_lineage(tmp_path, monkeypatch):
    entry = importlib.import_module("run_evolution_campaign")
    campaign, (cell,) = _campaign(tmp_path)
    roster = _roster(tmp_path)
    output = tmp_path / "batch"
    calls = []

    monkeypatch.setenv("EVOLUTION_BATCH_KEY", "fixture-secret")
    monkeypatch.setattr(entry.runner, "resolve_pinned_evas_identity", lambda _: {})
    monkeypatch.setattr(entry, "docker_image_identity", lambda *_args, **_kwargs: "sha256:" + "1" * 64)

    def fake_run(**kwargs):
        calls.append(kwargs)
        if kwargs["output_dir"].parent.name == "attempt-0001":
            _write_setup_failed_result(kwargs["output_dir"])
            raise RuntimeError("setup failed after terminal result")
        _write_completed_evolution_result(kwargs["output_dir"], cell=kwargs["cell"], score=0.0)
        return SimpleNamespace(manifest_sha256="a" * 64)

    monkeypatch.setattr(entry, "run_native_evolution", fake_run)
    assert entry.main([
        "--campaign", str(campaign), "--branches-json", str(roster),
        "--output-root", str(output), "--batch", "--cell", cell["cell_id"],
        "--batch-max-attempts", "2", "--evas-command", "/fixture/evas",
    ]) == 0
    assert [call["output_dir"].parent.name for call in calls] == ["attempt-0001", "attempt-0002"]
    index = _latest_index(output)
    row = index["rows"][0]
    assert row["attempts"][0]["status"] == "setup_failed"
    assert row["attempts"][1]["parent_attempt_id"] == row["attempts"][0]["attempt_id"]


def test_batch_resume_continues_only_sealed_setup_prefix(tmp_path, monkeypatch):
    entry = importlib.import_module("run_evolution_campaign")
    campaign, (cell,) = _campaign(tmp_path)
    roster = _roster(tmp_path)
    output = tmp_path / "batch"
    monkeypatch.setenv("EVOLUTION_BATCH_KEY", "fixture-secret")
    monkeypatch.setattr(entry.runner, "resolve_pinned_evas_identity", lambda _: {})
    monkeypatch.setattr(entry, "docker_image_identity", lambda *_args, **_kwargs: "sha256:" + "1" * 64)
    calls = []

    def fake_run(**kwargs):
        root = kwargs["output_dir"]
        calls.append(root.parent.name)
        if root.parent.name == "attempt-0001":
            _write_setup_failed_result(root)
            raise RuntimeError("setup failed")
        _write_completed_evolution_result(root, cell=kwargs["cell"])

    monkeypatch.setattr(entry, "run_native_evolution", fake_run)
    command = [
        "--campaign", str(campaign), "--branches-json", str(roster), "--output-root", str(output),
        "--batch", "--cell", cell["cell_id"], "--batch-max-attempts", "2", "--evas-command", "/fixture/evas",
    ]
    second = output / cell["cell_id"] / "attempt-0002"
    original_mkdir = Path.mkdir
    def interrupted_mkdir(path, *args, **kwargs):
        if path == second:
            raise KeyboardInterrupt("before next fresh attempt")
        return original_mkdir(path, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(Path, "mkdir", interrupted_mkdir)
        with pytest.raises(KeyboardInterrupt):
            entry.main(command)
    first = output / cell["cell_id"] / "attempt-0001"
    before = {path: path.read_bytes() for path in first.rglob("*") if path.is_file()}
    monkeypatch.setenv("EVOLUTION_BATCH_KEY", "fixture-secret")
    assert entry.main([*command, "--resume"]) == 0
    assert calls == ["attempt-0001", "attempt-0002"]
    attempts = _latest_index(output)["rows"][0]["attempts"]
    assert attempts[1]["parent_attempt_id"] == attempts[0]["attempt_id"]
    assert all(path.read_bytes() == content for path, content in before.items())


def test_batch_keeps_safe_setup_failure_unrecorded_when_attempt_cap_exhausts(tmp_path, monkeypatch):
    entry = importlib.import_module("run_evolution_campaign")
    campaign, (cell,) = _campaign(tmp_path)
    roster = _roster(tmp_path)
    output = tmp_path / "batch"

    monkeypatch.setenv("EVOLUTION_BATCH_KEY", "fixture-secret")
    monkeypatch.setattr(entry.runner, "resolve_pinned_evas_identity", lambda _: {})
    monkeypatch.setattr(entry, "docker_image_identity", lambda *_args, **_kwargs: "sha256:" + "1" * 64)

    def fake_run(**kwargs):
        _write_setup_failed_result(kwargs["output_dir"])
        raise RuntimeError("setup failed after terminal result")

    monkeypatch.setattr(entry, "run_native_evolution", fake_run)
    with pytest.raises(ValueError, match="attempt cap exhausted"):
        entry.main([
            "--campaign", str(campaign), "--branches-json", str(roster),
            "--output-root", str(output), "--batch", "--cell", cell["cell_id"],
            "--evas-command", "/fixture/evas",
        ])
    index = _latest_index(output)
    row = index["rows"][0]
    assert row["status"] == "retryable_setup_failed"
    assert not (output / ".batch" / f"cell-{cell['cell_id']}.json").exists()


def test_batch_rejects_dry_run_to_execution_drift_before_clients(tmp_path, monkeypatch):
    entry = importlib.import_module("run_evolution_campaign")
    campaign, (cell,) = _campaign(tmp_path)
    roster = _roster(tmp_path)
    output = tmp_path / "batch"

    assert entry.main([
        "--campaign", str(campaign), "--branches-json", str(roster),
        "--output-root", str(output), "--batch", "--dry-run", "--cell", cell["cell_id"],
    ]) == 0
    monkeypatch.setattr(entry, "docker_image_identity", lambda *_args, **_kwargs: "sha256:" + "1" * 64)
    monkeypatch.setattr(entry.runner, "OpenAICompatible", lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("drift must reject before providers")
    ))
    with pytest.raises(ValueError, match="differs"):
        entry.main([
            "--campaign", str(campaign), "--branches-json", str(roster),
            "--output-root", str(output), "--batch", "--resume", "--cell", cell["cell_id"],
            "--evas-command", "/fixture/evas",
        ])


def test_batch_rejects_forged_completed_result_and_malformed_attempts(tmp_path, monkeypatch):
    entry = importlib.import_module("run_evolution_campaign")
    campaign, (cell,) = _campaign(tmp_path)
    roster = _roster(tmp_path)
    output = tmp_path / "batch"

    assert entry.main([
        "--campaign", str(campaign), "--branches-json", str(roster),
        "--output-root", str(output), "--batch", "--dry-run", "--cell", cell["cell_id"],
    ]) == 0
    attempt = output / cell["cell_id"] / "attempt-0001"
    attempt.mkdir(parents=True)
    (attempt / "campaign.json").write_text("{}", encoding="utf-8")
    _write_forged_completed_evolution_result(attempt / "run")

    with pytest.raises(ValueError, match="invalid_existing_attempt"):
        entry.main([
            "--campaign", str(campaign), "--branches-json", str(roster),
            "--output-root", str(output), "--batch", "--resume", "--dry-run", "--cell", cell["cell_id"],
        ])


@pytest.mark.parametrize("mutation", [
    "missing_config", "wrong_rounds", "public_profile", "task_id", "attempt_id", "episode_id",
    "final_profile_sha256", "final_profile_input_identity_sha256",
])
def test_batch_rejects_misbound_completed_evidence(tmp_path, monkeypatch, mutation):
    entry = importlib.import_module("run_evolution_campaign")
    campaign, (cell,) = _campaign(tmp_path)
    roster = _roster(tmp_path)
    monkeypatch.setenv("EVOLUTION_BATCH_KEY", "fixture-secret")
    monkeypatch.setattr(entry.runner, "resolve_pinned_evas_identity", lambda _: {})
    monkeypatch.setattr(entry, "docker_image_identity", lambda *_args, **_kwargs: "sha256:" + "1" * 64)

    def fake_run(**kwargs):
        root = kwargs["output_dir"]
        _write_completed_evolution_result(root, cell=kwargs["cell"], wrong_rounds=mutation == "wrong_rounds")
        if mutation == "missing_config":
            path = root / "request.json"
            doc = json.loads(path.read_text())
            doc.pop("config")
        elif mutation == "public_profile":
            path = root / "public-validation-profile.json"
            doc = json.loads(path.read_text())
            doc["profile_id"] = "different-profile"
        elif mutation == "wrong_rounds":
            return
        else:
            path = root / "final-result.json"
            doc = json.loads(path.read_text())
            doc["score_sidecar_receipt"][mutation] = "f" * 64
        path.write_text(json.dumps(doc))

    monkeypatch.setattr(entry, "run_native_evolution", fake_run)
    with pytest.raises(ValueError):
        entry.main([
            "--campaign", str(campaign), "--branches-json", str(roster),
            "--output-root", str(tmp_path / "batch"), "--batch", "--cell", cell["cell_id"],
            "--evas-command", "/fixture/evas",
        ])


@pytest.mark.parametrize("marker", ["broken_request", "public-validation-runtime", "final-runtime", "unknown"])
def test_setup_retry_rejects_ambiguous_lifecycle_artifacts(tmp_path, monkeypatch, marker):
    entry = importlib.import_module("run_evolution_campaign")
    campaign, (cell,) = _campaign(tmp_path)
    roster = _roster(tmp_path)
    calls = []
    monkeypatch.setenv("EVOLUTION_BATCH_KEY", "fixture-secret")
    monkeypatch.setattr(entry.runner, "resolve_pinned_evas_identity", lambda _: {})
    monkeypatch.setattr(entry, "docker_image_identity", lambda *_args, **_kwargs: "sha256:" + "1" * 64)

    def fake_run(**kwargs):
        root = kwargs["output_dir"]
        calls.append(root)
        _write_setup_failed_result(root)
        if marker == "broken_request":
            (root / "request.json").symlink_to("missing")
        else:
            (root / marker).mkdir()
        raise RuntimeError("setup failed")

    monkeypatch.setattr(entry, "run_native_evolution", fake_run)
    with pytest.raises(ValueError):
        entry.main([
            "--campaign", str(campaign), "--branches-json", str(roster),
            "--output-root", str(tmp_path / "batch"), "--batch", "--cell", cell["cell_id"],
            "--batch-max-attempts", "2", "--evas-command", "/fixture/evas",
        ])
    assert len(calls) == 1


@pytest.mark.skipif(
    os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1",
    reason="opt-in real Docker/EVAS Evolution batch resume regression",
)
def test_r53_docker_evolution_batch_resume(tmp_path, monkeypatch):
    entry = importlib.import_module("run_evolution_campaign")
    from test_agent_harness_native_launcher import Provider

    campaign, (cell,) = _campaign(tmp_path)
    roster = _roster(tmp_path)
    output = tmp_path / "batch"
    clients = []

    def scripted_provider(*, model, **_kwargs):
        artifacts = smoke.public_stub_artifacts(
            smoke.public_contract(smoke.DEFAULT_RELEASE, cell["task_id"])
        )
        commands = []
        for name, content in artifacts.items():
            payload = content + "// batch candidate\n"
            commands.append(
                f"printf %s {shlex.quote(payload)} > public/submission/{name}"
            )
        commands.append("vabench-submit")
        client = Provider(commands)
        client.model = model
        clients.append(client)
        return client

    monkeypatch.setenv("EVOLUTION_BATCH_KEY", "scripted-fixture-secret")
    monkeypatch.setattr(entry.runner, "OpenAICompatible", scripted_provider)
    command = [
        "--campaign", str(campaign),
        "--branches-json", str(roster),
        "--output-root", str(output),
        "--batch",
        "--cell", cell["cell_id"],
        "--rounds", "1",
        "--model-calls", "5",
        "--tool-calls", "5",
        "--request-timeout-s", "15",
        "--timeout-s", "120",
        "--evas-command", str(ROOT / ".venv/bin/evas"),
    ]
    assert entry.main(command) == 0
    first = _latest_index(output)["rows"][0]
    assert first["terminal_status"] == "completed"
    assert first["score"] == 0.0
    assert len(clients) == 1
    assert (output / cell["cell_id"] / "attempt-0001/run/final-result.json").is_file()

    before = {path: path.read_bytes() for path in (output / cell["cell_id"]).rglob("*") if path.is_file()}
    code = """
import json, sys
sys.path.insert(0, sys.argv[1])
import run_evolution_campaign as entry
def forbidden(*args, **kwargs):
    raise AssertionError('completed recovery must not call provider, key loader or judge')
entry.runner.OpenAICompatible = forbidden
entry.runner.load_key = forbidden
entry.runner.resolve_pinned_evas_identity = forbidden
entry.runner.run_trusted_replay = forbidden
entry.run_native_evolution = forbidden
raise SystemExit(entry.main(json.loads(sys.stdin.read())))
"""
    recovered = subprocess.run([sys.executable, "-c", code, str(CALIBRATION)],
                               input=json.dumps([*command, "--resume"]), text=True,
                               capture_output=True, timeout=60)
    assert recovered.returncode == 0, recovered.stderr
    reused = _latest_index(output)["rows"][0]
    assert reused["batch_reuse"] is True
    assert reused["terminal_status"] == "completed"
    assert all(path.read_bytes() == content for path, content in before.items())
