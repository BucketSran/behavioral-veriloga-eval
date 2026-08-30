from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "evaluator-closure.yml"


def test_evaluator_closure_gates_generic_agent_harness_contracts() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert workflow.count('"runners/agent_harness/**"') == 2
    assert workflow.count('"schemas/vaevas-*-v1.schema.json"') == 2
    assert workflow.count('"tests/test_agent_harness_*.py"') == 2
    assert "tests/test_agent_harness_*.py \\" in workflow


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
