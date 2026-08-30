"""Three-form all-native connectivity, deliberately not model performance."""

from concurrent.futures import ThreadPoolExecutor
import os
import subprocess
import sys

import pytest

from scripts import run_v4_r53_clean_room_smoke as smoke
from public_validation import public_execution_contract


def test_public_stub_supports_the_bugfix_artifact_contract():
    contract = smoke.public_contract(smoke.DEFAULT_RELEASE, "v4-1001")
    artifacts = smoke.public_stub_artifacts(contract)
    assert sorted(artifacts) == sorted(contract["target_artifacts"])
    assert all("not a reference solution" in content for content in artifacts.values())


def test_public_testbench_stub_uses_declared_binding_and_no_fault_knowledge(tmp_path):
    contract = smoke.public_contract(smoke.DEFAULT_RELEASE, "v4-501")
    artifacts = smoke.public_stub_artifacts(contract)
    assert list(artifacts) == ["testbench.scs"]
    deck = artifacts["testbench.scs"]
    template = contract["testbench_binding"]["source_path_template"]
    assert f'ahdl_include "{template.format(artifact_path="bbpd_ref.va")}"' in deck
    assert "XDUT (data clk retimed_data up down) bbpd_ref" in deck
    assert "not a reference solution" in deck
    candidate = tmp_path / "testbench.scs"
    candidate.write_text(deck)
    smoke.run_campaign.validate_public_testbench(candidate)


@pytest.mark.parametrize("episode_backend,native_max_attempts", [
    ("native-mini-swe", 1), ("native-mini-swe", 2), ("native-reasoning", 1),
])
def test_r53_docker_all_native_three_arm_campaign(tmp_path, native_max_attempts, episode_backend):
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in real Docker/EVAS three-form three-arm campaign")

    campaign = smoke.campaign_builder.build_campaign(
        smoke.DEFAULT_RELEASE,
        family_ids=["001"],
        model_provider="deterministic-public-contract-smoke",
        model=smoke.DEFAULT_MODEL,
        per_turn_max_tokens=4096,
        repetitions=1,
        three_arm_g0_g2=True,
    )
    cells = campaign["cells"]
    assert len(cells) == 9
    campaign["cells"] = cells
    campaign["execution_config"] = {
        "episode_backend": episode_backend, "workers": 2,
        "automatic_cell_retry": native_max_attempts > 1,
        "evidence_scope": "deterministic_connectivity_not_model_quality",
    }
    from run_native_attempts import retry_policy, read_native_attempt_sequence
    campaign["execution_config"]["native_retry_policy"] = retry_policy(native_max_attempts).to_document()
    campaign_path = tmp_path / "campaign.json"
    smoke.write_immutable_json(campaign_path, campaign)
    campaign_sha = smoke.sha256_file(campaign_path)
    args = smoke.parse_args([
        "--output-root", str(tmp_path),
        "--evas-command", str(smoke.ROOT / ".venv/bin/evas"),
    ])
    args.evas_command, identity = smoke.resolve_evas_command(args.evas_command)
    smoke.configure_runner_args(args, tmp_path / "run", identity)
    args.episode_backend = episode_backend
    args.campaign_file_sha256 = campaign_sha
    args.native_max_attempts = native_max_attempts

    def execute(cell):
        contract = smoke.public_contract(smoke.DEFAULT_RELEASE, cell["task_id"])
        public_root = (smoke.DEFAULT_RELEASE / smoke.task_index_row(
            smoke.DEFAULT_RELEASE, cell["task_id"]
        )["public_contract"]).parent / "public"
        command, _ = public_execution_contract(smoke.read_json(public_root / "evas_runtime.json"))
        clients = []

        def factory():
            client = smoke.client_for_arm(
                cell["experimental_arm"], smoke.public_stub_artifacts(contract),
                smoke.DEFAULT_MODEL, command,
            )
            if native_max_attempts > 1 and not clients:
                def unavailable(*args, **kwargs):
                    raise TimeoutError("deterministic transport outage before final")
                client.complete = unavailable
            clients.append(client)
            return client

        return smoke.run_campaign.run_cell_preserving_failure(
            cell, args, factory() if native_max_attempts == 1 else None,
            client_factory=factory,
        )

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
        "--episode-backend", episode_backend, "--workers", "2",
        "--judge-kind", "final_trusted_replay",
        "--output", str(report_path),
        "--ledger-output", str(tmp_path / "reviewer-ledger.json"),
    ], text=True, capture_output=True, timeout=60, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = smoke.read_json(report_path)
    assert report["cell_count"] == 9
    assert report["score_authority"] == "development_only"
    assert report["judge_statuses"] == {"behavior_failure": 9}
    ledger = smoke.read_json(tmp_path / "reviewer-ledger.json")
    assert ledger["denominator"]["scheduled_cells"] == 9
    assert report["result_ledger"]["ledger_sha256"] == ledger["ledger_sha256"]
    assert evidence_hashes() == before
    assert smoke.sha256_file(campaign_path) == campaign_sha

    evidence_index = []
    for cell in cells:
        runtime = args.output / cell["cell_id"]
        if native_max_attempts > 1:
            selected = read_native_attempt_sequence(
                runtime, cell, campaign_file_sha256=campaign_sha,
                expected_retry_policy=retry_policy(native_max_attempts),
            )
            assert selected["attempt_count"] == 2
            first, last = selected["attempt_sequence"]["attempts"]
            assert first["failure_category"] == "provider_transport"
            assert not (runtime / first["cell_runtime"] / "evidence/bound-final-test").exists()
            runtime = runtime / last["cell_runtime"]
        row = smoke.score_campaign.read_native_cell(
            runtime, cell, campaign_file_sha256=campaign_sha,
        )
        assert row["backend"] == episode_backend
        manifest = smoke.read_json(runtime / "evidence/native-launcher/manifest.json")
        result = smoke.read_json(runtime / "evidence/native-launcher/result.json")
        request = smoke.read_json(runtime / "evidence/native-episode/request.json")
        arm = cell["experimental_arm"]
        assert not (runtime / "evidence/campaign_result.json").exists()
        expected_attempt = f"{cell['cell_id']}-attempt-0001"
        if native_max_attempts > 1:
            expected_attempt += "-retry-0001"
        assert row["attempt_id"] == expected_attempt
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
        "status": "PASS", "claim_scope": "nine_cell_connectivity_only",
        "model_score_claim_allowed": False, "paper_result_claim_allowed": False,
        "campaign_sha256": campaign_sha, "score_report_sha256": smoke.sha256_file(report_path),
        "cells": evidence_index,
    })
