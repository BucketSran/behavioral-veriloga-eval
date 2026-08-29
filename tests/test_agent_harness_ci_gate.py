from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "evaluator-closure.yml"


def test_evaluator_closure_gates_generic_agent_harness_contracts() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert workflow.count('"runners/agent_harness/**"') == 2
    assert workflow.count('"schemas/vaevas-*-v1.schema.json"') == 2
    assert workflow.count('"tests/test_agent_harness_*.py"') == 2
    assert "tests/test_agent_harness_*.py \\" in workflow
