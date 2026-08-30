"""Native mini-swe campaign dispatch and strict native score accounting."""

from __future__ import annotations

import json
import hashlib
from argparse import Namespace
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
WRAPPER = ROOT / "benchmark-vabench-release-v4/runners/run_benchmarkv4_campaign.py"
sys.path.insert(0, str(CALIBRATION))

import run_campaign as runner  # noqa: E402
import score_campaign as scorer  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("form,task_id", [("dut", "v4-001"), ("testbench", "v4-501")])
def test_wrapper_dry_run_records_native_episode_backend_without_legacy_fallback(
    tmp_path: Path, form: str, task_id: str,
) -> None:
    output = tmp_path / "native-campaign"
    completed = subprocess.run(
        [
            sys.executable,
            str(WRAPPER),
            "--output-root",
            str(output),
            "--model",
            "fixture-model",
            "--task-id",
            task_id,
            "--form",
            form,
            "--comparison-profile",
            "executable-feedback-control",
            "--episode-backend",
            "native-mini-swe",
            "--dry-run",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr

    campaign = read_json(output / "campaign.json")
    execution = campaign["execution_config"]
    assert execution["episode_backend"] == "native-mini-swe"
    assert execution["agent_scaffold"] == "mini-swe"
    assert {cell["experimental_arm"] for cell in campaign["cells"]} == {
        "OneShot",
        "Agent-No-EVAS",
        "Agentic",
    }

    summary = read_json(output / "wrapper_summary.json")
    command = summary["command"]
    assert "--episode-backend" in command
    assert command[command.index("--episode-backend") + 1] == "native-mini-swe"
    assert "--agent-scaffold" in command
    assert command[command.index("--agent-scaffold") + 1] == "mini-swe"


@pytest.mark.parametrize(
    ("extra_args", "message"),
    [
        (["--agent-scaffold", "native"], "agent-scaffold"),
        (["--limit", "1"], "limit"),
        (["--resume"], "resume"),
    ],
)
def test_wrapper_rejects_unfrozen_native_campaign_combinations(
    tmp_path: Path, extra_args: list[str], message: str
) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(WRAPPER),
            "--output-root",
            str(tmp_path / "native-campaign"),
            "--model",
            "fixture-model",
            "--task-id",
            "v4-001",
            "--comparison-profile",
            "executable-feedback-control",
            "--episode-backend",
            "native-mini-swe",
            "--dry-run",
            *extra_args,
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    assert completed.returncode != 0
    assert message in completed.stderr or message in completed.stdout


@pytest.mark.parametrize(
    ("arm", "mode", "process", "feedback", "expected_image"),
    [
        ("OneShot", "G0", "direct", False, None),
        ("Agent-No-EVAS", "G2", "agentic", False, "image:no-evas"),
        ("Agentic", "G2", "agentic", True, "image:evas"),
    ],
)
def test_run_campaign_native_backend_dispatches_prepared_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arm: str,
    mode: str,
    process: str,
    feedback: bool,
    expected_image: str | None,
) -> None:
    cell = {
        "cell_id": f"v4-001-{mode}-r00-{arm.lower().replace('-', '')}",
        "task_id": "v4-001",
        "family_id": "001",
        "form": "dut",
        "mode": mode,
        "process": process,
        "experimental_arm": arm,
        "base_mode": mode,
        "executable_feedback": feedback,
        "per_turn_max_tokens": 128,
    }
    args = Namespace(
        output=tmp_path,
        release=runner.DEFAULT_RELEASE,
        setup_timeout_s=10,
        request_timeout_s=11,
        tool_timeout_s=12,
        judge_timeout_s=13,
        agent_timeout_s=14,
        episode_backend="native-mini-swe",
        agent_scaffold="mini-swe",
        dry_run=False,
        resume=False,
        evas_command="/usr/bin/evas-fixture",
        final_judge_command="/usr/bin/final-fixture",
        mini_swe_image="image:evas",
        mini_swe_no_evas_image="image:no-evas",
        allow_insecure_test_sandbox=True,
    )
    client = SimpleNamespace(model="fixture-model")
    calls: list[dict] = []

    def fake_export(observed_cell, release, runtime, *, timeout_s):
        assert observed_cell == cell
        assert release == runner.DEFAULT_RELEASE
        assert runtime == tmp_path / cell["cell_id"]
        assert timeout_s == 10
        (runtime / "evidence").mkdir(parents=True)

    def fake_launch(**kwargs):
        calls.append(kwargs)
        (kwargs["runtime"] / "evidence/native-launcher").mkdir(parents=True)
        return SimpleNamespace(
            result=SimpleNamespace(
                primary_outcome="behavior_failure",
                terminal_reason="submitted",
            ),
            artifact_path=kwargs["runtime"] / "evidence/native-episode/scored-results/a.json",
            score_sidecar_receipt={"sha256": "a" * 64},
        )

    monkeypatch.setattr(runner, "export_runtime", fake_export)
    monkeypatch.setattr(runner, "run_prepared_native_mini_swe", fake_launch)

    result = runner.run_cell(cell, args, client)

    assert result["backend"] == "native-mini-swe"
    assert result["status"] == "behavior_failure"
    assert result["termination_reason"] == "submitted"
    assert result["cell"] == cell
    assert len(calls) == 1
    call = calls[0]
    assert call["runtime"] == tmp_path / cell["cell_id"]
    assert call["cell"] == cell
    assert call["client"] is client
    assert call["attempt_id"] == f"{cell['cell_id']}-attempt-0001"
    assert call["campaign_file_sha256"] is None
    assert call["evas_command"] == "/usr/bin/evas-fixture"
    assert call["final_judge_command"] == "/usr/bin/final-fixture"
    assert call["docker_image"] == expected_image
    assert not (tmp_path / cell["cell_id"] / "evidence/campaign_result.json").exists()


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"form": "unsupported"}, "DUT/bugfix/Testbench"),
        ({"experimental_arm": None}, "experimental arm"),
        ({"experimental_arm": "Agentic", "mode": "G3"}, "experimental arm"),
    ],
)
def test_run_campaign_native_backend_rejects_unsupported_cells_before_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: dict,
    message: str,
) -> None:
    cell = {
        "cell_id": "v4-001-G2-r00-agentic",
        "task_id": "v4-001",
        "family_id": "001",
        "form": "dut",
        "mode": "G2",
        "process": "agentic",
        "experimental_arm": "Agentic",
        "base_mode": "G2",
        "executable_feedback": True,
        "per_turn_max_tokens": 128,
        **override,
    }
    args = Namespace(
        output=tmp_path,
        release=runner.DEFAULT_RELEASE,
        setup_timeout_s=10,
        request_timeout_s=11,
        tool_timeout_s=12,
        judge_timeout_s=13,
        agent_timeout_s=14,
        episode_backend="native-mini-swe",
        agent_scaffold="mini-swe",
        dry_run=False,
        resume=False,
        evas_command="/usr/bin/evas-fixture",
        final_judge_command="/usr/bin/final-fixture",
        mini_swe_image="image:evas",
        mini_swe_no_evas_image="image:no-evas",
    )
    exported = False

    def fake_export(*args, **kwargs):
        nonlocal exported
        exported = True

    monkeypatch.setattr(runner, "export_runtime", fake_export)

    with pytest.raises(ValueError, match=message):
        runner.run_cell(cell, args, SimpleNamespace(model="fixture-model"))
    assert exported is False


def test_score_campaign_native_backend_reads_frozen_schedule_without_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cell = {
        "cell_id": "v4-001-G2-r00-agentic",
        "task_id": "v4-001",
        "family_id": "001",
        "form": "dut",
        "mode": "G2",
        "process": "agentic",
        "experimental_arm": "Agentic",
        "base_mode": "G2",
        "executable_feedback": True,
    }
    campaign = {"schema_version": "fixture", "cells": [cell]}
    campaign_path = tmp_path / "campaign.json"
    campaign_path.write_text(json.dumps(campaign, sort_keys=True), encoding="utf-8")
    run_root = tmp_path / "run"
    run_root.mkdir()
    output = tmp_path / "score.json"
    calls: list[tuple[Path, dict, str]] = []

    def fake_read_native_cell(runtime, scheduled_cell, *, campaign_file_sha256):
        calls.append((runtime, scheduled_cell, campaign_file_sha256))
        return {
            **scheduled_cell,
            "backend": "native-mini-swe",
            "submission_status": "submitted",
            "judge_status": "passed",
            "outcome": "passed",
            "score": 1,
            "trusted_replay": {
                "final_test_profile": {
                    "score_sidecar_contract": {
                        "score_authority": "development_only",
                    },
                },
                "derived_score_sidecar_reference": {
                    "path": "evidence/score-sidecars/a.json",
                    "sha256": "a" * 64,
                },
            },
        }

    monkeypatch.setattr(scorer, "read_native_cell", fake_read_native_cell)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "score_campaign.py",
            "--campaign-output",
            str(run_root),
            "--campaign",
            str(campaign_path),
            "--judge-kind",
            "final_trusted_replay",
            "--episode-backend",
            "native-mini-swe",
            "--output",
            str(output),
        ],
    )

    assert scorer.main() == 0
    report = read_json(output)
    assert report["cell_count"] == 1
    assert report["rows"][0]["backend"] == "native-mini-swe"
    assert calls == [
        (
            run_root / cell["cell_id"],
            cell,
            hashlib.sha256(campaign_path.read_bytes()).hexdigest(),
        )
    ]


def test_score_campaign_native_backend_rejects_non_evas_judge_label(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    campaign_path = tmp_path / "campaign.json"
    campaign_path.write_text(json.dumps({"cells": []}), encoding="utf-8")
    run_root = tmp_path / "run"
    run_root.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "score_campaign.py",
            "--campaign-output",
            str(run_root),
            "--campaign",
            str(campaign_path),
            "--judge-kind",
            "final_spectre",
            "--episode-backend",
            "native-mini-swe",
        ],
    )

    with pytest.raises(SystemExit, match="final_trusted_replay"):
        scorer.main()


def test_native_dispatch_infrastructure_failure_is_counted_without_legacy_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cell = {
        "cell_id": "v4-001-G2-r00-agentic",
        "task_id": "v4-001",
        "family_id": "001",
        "form": "dut",
        "mode": "G2",
        "process": "agentic",
        "experimental_arm": "Agentic",
        "base_mode": "G2",
        "executable_feedback": True,
        "per_turn_max_tokens": 128,
    }
    args = Namespace(
        output=tmp_path,
        release=runner.DEFAULT_RELEASE,
        setup_timeout_s=10,
        request_timeout_s=11,
        tool_timeout_s=12,
        judge_timeout_s=13,
        agent_timeout_s=14,
        episode_backend="native-mini-swe",
        agent_scaffold="mini-swe",
        dry_run=False,
        resume=False,
        evas_command="/usr/bin/evas-fixture",
        final_judge_command="/usr/bin/final-fixture",
        mini_swe_image="image:evas",
        mini_swe_no_evas_image="image:no-evas",
        campaign_file_sha256="b" * 64,
    )

    def fail_export(*args, **kwargs):
        raise runner.RuntimeExportError("fixture exporter failed")

    monkeypatch.setattr(runner, "export_runtime", fail_export)

    result = runner.run_cell_preserving_failure(
        cell, args, SimpleNamespace(model="fixture-model")
    )
    runtime = tmp_path / cell["cell_id"]
    assert result["backend"] == "native-mini-swe"
    assert result["status"] == "infrastructure_failure"
    assert result["termination_reason"] == "runtime_export_failure"
    assert not (runtime / "evidence/campaign_result.json").exists()

    row = scorer.read_native_cell(
        runtime,
        cell,
        campaign_file_sha256="b" * 64,
    )
    assert row["backend"] == "native-mini-swe"
    assert row["judge_status"] == "infrastructure_failure"
    assert row["score"] is None
    assert row["failure_class"] == "infrastructure"
    assert "trusted_replay" not in row
    scorer.summarize([row], "final_trusted_replay", scheduled_cells=[cell])


def test_native_existing_dispatch_is_not_exported_or_overwritten(tmp_path, monkeypatch):
    cell = {"cell_id": "v4-reserved"}
    runtime = tmp_path / cell["cell_id"]
    receipt = runtime / "evidence/native-dispatch/result.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text("preserve previous attempt")
    args = Namespace(output=tmp_path, episode_backend="native-mini-swe", resume=False)
    monkeypatch.setattr(runner, "validate_native_mini_swe_cell", lambda _: None)
    with pytest.raises(runner.FinalReplayReservedError):
        runner.run_cell_preserving_failure(cell, args, None)
    assert receipt.read_text() == "preserve previous attempt"


def test_native_wrapper_preserves_existing_campaign_before_dispatch(tmp_path):
    output = tmp_path / "existing-campaign"
    output.mkdir()
    manifest = output / "campaign.json"
    manifest.write_text("frozen original manifest")
    completed = subprocess.run([
        sys.executable, str(WRAPPER), "--output-root", str(output),
        "--model", "fixture-model", "--task-id", "v4-001", "--form", "dut",
        "--comparison-profile", "executable-feedback-control",
        "--episode-backend", "native-mini-swe", "--dry-run",
    ], text=True, capture_output=True, timeout=60, check=False)
    assert completed.returncode != 0
    assert manifest.read_text() == "frozen original manifest"
    assert not (output / "run").exists()
