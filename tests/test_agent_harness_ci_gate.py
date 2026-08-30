from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "evaluator-closure.yml"


def test_pilot_credential_helper_changes_trigger_its_regressions():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert workflow.count('"benchmark-vabench-release-v4/operations/calibration_pilot/pilot_credentials.py"') == 2
    assert "tests/test_agent_harness_*.py \\" in workflow


def test_budgeted_pilot_client_changes_trigger_free_native_integration():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert workflow.count('"benchmark-vabench-release-v4/operations/calibration_pilot/deepseek_budget.py"') == 2
    assert "tests/test_agent_harness_deepseek_budget_smoke.py::test_budgeted_client_reaches_native_freeze_and_evas_sidecar" in workflow


def test_evaluator_closure_tracks_recovery_ledger_and_real_evolution():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    prefix = '"benchmark-vabench-release-v4/operations/calibration_pilot/'
    for name in ("run_native_attempts.py", "result_ledger.py", "run_native_evolution.py", "run_evolution_campaign.py"):
        assert workflow.count(prefix + name + '"') == 2
    assert "tests/test_agent_harness_evolution_campaign.py::test_r53_docker_native_evolution_selected_final_only" in workflow


def test_evaluator_closure_gates_generic_agent_harness_contracts() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert workflow.count('"runners/agent_harness/**"') == 2
    assert workflow.count('"schemas/vaevas-*-v1.schema.json"') == 2
    assert workflow.count('"tests/test_agent_harness_*.py"') == 2
    assert "tests/test_agent_harness_*.py \\" in workflow


def test_evaluator_closure_tracks_absent_public_authority_schema() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert workflow.count('"schemas/vaevas-result-artifact-v2.schema.json"') == 2


def test_evaluator_closure_gates_all_native_three_arm_campaign() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "tests/test_agent_harness_native_campaign_smoke.py::test_r53_docker_all_native_three_arm_campaign" in workflow
    assert workflow.count('"benchmark-vabench-release-v4/runners/run_benchmarkv4_campaign.py"') == 2


def test_evaluator_closure_runs_bound_production_replay_smoke() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    prefix = '"benchmark-vabench-release-v4/operations/calibration_pilot/'
    assert workflow.count(prefix + 'final_replay.py"') == 2
    assert workflow.count(prefix + 'run_campaign.py"') == 2
    assert workflow.count('"tests/test_score_campaign_reuse.py"') == 2
    assert "tests/test_score_campaign_reuse.py \\" in workflow
    assert "--bound-final-authority" in workflow
    assert 'cell["bound_final_test"]["sidecar_hash_verified"]' in workflow
    assert 'cell["bound_final_test"]["generation_evidence_unchanged"]' in workflow


def test_evaluator_closure_installs_and_runs_locked_agentic_extra() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "uv sync --locked --group dev --extra agentic --python 3.11.13" in workflow
    runs = [
        line.strip()
        for line in workflow.splitlines()
        if line.strip().startswith("uv run ")
    ]
    assert runs
    assert all(line.startswith("uv run --locked --extra agentic ") for line in runs)


def test_evaluator_closure_runs_public_validation_docker_native_trajectory() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    prefix = '"benchmark-vabench-release-v4/operations/calibration_pilot/'
    assert workflow.count(prefix + 'public_validation.py"') == 2
    assert workflow.count(prefix + 'mini_swe_vabench.py"') == 2
    assert "VABENCH_TEST_DOCKER_RUNTIME: '1'" in workflow
    assert (
        "tests/test_agent_harness_production_public_validation.py::"
        "test_r53_docker_public_validation_native_trajectory_smoke"
    ) in workflow


def test_evaluator_closure_runs_native_episode_result_join() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    prefix = '"benchmark-vabench-release-v4/operations/calibration_pilot/'
    assert workflow.count(prefix + 'native_episode.py"') == 2
    assert (
        "tests/test_agent_harness_native_episode.py::test_r53_docker_native_episode_result_join"
    ) in workflow


def test_evaluator_closure_runs_native_launcher_provider_to_score() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    prefix = '"benchmark-vabench-release-v4/operations/calibration_pilot/'
    assert workflow.count(prefix + 'run_native_mini_swe.py"') == 2
    assert "tests/test_agent_harness_native_launcher.py::test_r53_docker_native_launcher_provider_to_score" in workflow
