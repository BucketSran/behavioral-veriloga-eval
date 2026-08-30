from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "evaluator-closure.yml"


def test_evaluator_closure_gates_generic_agent_harness_contracts() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert workflow.count('"runners/agent_harness/**"') == 2
    assert workflow.count('"schemas/vaevas-*-v1.schema.json"') == 2
    assert workflow.count('"tests/test_agent_harness_*.py"') == 2
    assert "tests/test_agent_harness_*.py \\" in workflow


def test_evaluator_closure_tracks_absent_public_authority_schema() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert workflow.count('"schemas/vaevas-result-artifact-v2.schema.json"') == 2


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
