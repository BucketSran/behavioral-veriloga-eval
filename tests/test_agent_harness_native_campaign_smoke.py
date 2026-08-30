"""DUT/bugfix all-native connectivity, deliberately not model performance."""

from concurrent.futures import ThreadPoolExecutor
import os
import subprocess
import sys

import pytest

from scripts import run_v4_r53_clean_room_smoke as smoke


def test_public_stub_supports_the_bugfix_artifact_contract():
    contract = smoke.public_contract(smoke.DEFAULT_RELEASE, "v4-1001")
    artifacts = smoke.public_stub_artifacts(contract)
    assert sorted(artifacts) == sorted(contract["target_artifacts"])
    assert all("not a reference solution" in content for content in artifacts.values())


def test_r53_docker_all_native_three_arm_campaign(tmp_path):
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in real Docker/EVAS two-form three-arm campaign")

    campaign = smoke.campaign_builder.build_campaign(
        smoke.DEFAULT_RELEASE,
        family_ids=["001"],
        model_provider="deterministic-public-contract-smoke",
        model=smoke.DEFAULT_MODEL,
        per_turn_max_tokens=4096,
        repetitions=1,
        three_arm_g0_g2=True,
    )
    cells = [cell for cell in campaign["cells"] if cell["form"] in {"dut", "bugfix"}]
    assert len(cells) == 6
    campaign["cells"] = cells
    campaign["execution_config"] = {
        "episode_backend": "native-mini-swe", "workers": 2,
        "automatic_cell_retry": False,
        "evidence_scope": "deterministic_connectivity_not_model_quality",
    }
    campaign_path = tmp_path / "campaign.json"
    smoke.write_immutable_json(campaign_path, campaign)
    campaign_sha = smoke.sha256_file(campaign_path)
    args = smoke.parse_args([
        "--output-root", str(tmp_path),
        "--evas-command", str(smoke.ROOT / ".venv/bin/evas"),
    ])
    args.evas_command, identity = smoke.resolve_evas_command(args.evas_command)
    smoke.configure_runner_args(args, tmp_path / "run", identity)
    args.episode_backend = "native-mini-swe"
    args.campaign_file_sha256 = campaign_sha

    def execute(cell):
        contract = smoke.public_contract(smoke.DEFAULT_RELEASE, cell["task_id"])
        client = smoke.client_for_arm(
            cell["experimental_arm"], smoke.public_stub_artifacts(contract),
            smoke.DEFAULT_MODEL, contract["evas"]["command"],
        )
        return smoke.run_campaign.run_cell_preserving_failure(cell, args, client)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(execute, cells))
    assert all(result["status"] == "behavior_failure" for result in results), results

    def evidence_hashes():
        return {
            str(path.relative_to(args.output)): smoke.sha256_file(path)
            for path in args.output.rglob("*") if path.is_file()
        }

    before = evidence_hashes()
    report_path = tmp_path / "SCORE.json"
    completed = subprocess.run([
        sys.executable, str(smoke.CALIBRATION / "score_campaign.py"),
        "--campaign-output", str(args.output), "--campaign", str(campaign_path),
        "--episode-backend", "native-mini-swe", "--workers", "2",
        "--judge-kind", "final_trusted_replay",
        "--output", str(report_path),
    ], text=True, capture_output=True, timeout=60, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = smoke.read_json(report_path)
    assert report["cell_count"] == 6
    assert report["score_authority"] == "development_only"
    assert report["judge_statuses"] == {"behavior_failure": 6}
    assert evidence_hashes() == before
    assert smoke.sha256_file(campaign_path) == campaign_sha

    evidence_index = []
    for cell in cells:
        runtime = args.output / cell["cell_id"]
        row = smoke.score_campaign.read_native_cell(
            runtime, cell, campaign_file_sha256=campaign_sha,
        )
        manifest = smoke.read_json(runtime / "evidence/native-launcher/manifest.json")
        result = smoke.read_json(runtime / "evidence/native-launcher/result.json")
        request = smoke.read_json(runtime / "evidence/native-episode/request.json")
        arm = cell["experimental_arm"]
        assert not (runtime / "evidence/campaign_result.json").exists()
        assert row["attempt_id"] == f"{cell['cell_id']}-attempt-0001"
        assert manifest["environment"]["network"] is False
        assert manifest["environment"]["evaluator_mounted"] is False
        if arm == "Agentic":
            assert request["public_validation_profile_sha256"]
            assert row["evas_usage"]["calls_executed"] >= 1
        else:
            assert request["public_validation_profile"] is None
            assert request["public_validation_profile_sha256"] is None
            assert row["evas_usage"]["calls_executed"] == 0
        if arm == "Agent-No-EVAS":
            assert manifest["environment"]["docker_image"] == smoke.DEFAULT_NO_EVAS_IMAGE
            assert not (runtime / "public/.tools/evas-runtime.json").exists()
        if arm == "OneShot":
            assert result["model_telemetry"]["call_count"] == 1
            assert manifest["environment"]["docker_image"] is None
        sidecar_ref = row["trusted_replay"]["derived_score_sidecar_reference"]
        sidecar = smoke.read_json(runtime / sidecar_ref["path"])
        assert sidecar["judge"]["engine"] == "evas"
        assert sidecar["score_authority"] == "development_only"
        assert smoke.sha256_file(runtime / sidecar_ref["path"]) == sidecar_ref["sha256"]
        evidence_index.append({
            "cell_id": cell["cell_id"], "form": cell["form"], "arm": arm,
            "artifact_file_sha256": row["native_evidence"]["artifact_file_sha256"],
            "sidecar_sha256": sidecar_ref["sha256"],
            "trajectory_sha256": smoke.sha256_file(runtime / "evidence/native-episode/trajectory.jsonl"),
        })
    smoke.write_immutable_json(tmp_path / "smoke-evidence-index.json", {
        "status": "PASS", "claim_scope": "six_cell_connectivity_only",
        "model_score_claim_allowed": False, "paper_result_claim_allowed": False,
        "campaign_sha256": campaign_sha, "score_report_sha256": smoke.sha256_file(report_path),
        "cells": evidence_index,
    })
