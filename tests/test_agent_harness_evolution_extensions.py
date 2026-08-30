"""Frozen Evolution branch surfaces and explicit synthetic interventions."""

from copy import deepcopy
from dataclasses import replace
import json

from test_agent_harness_native_evolution import (
    REASONING_BACKEND_SHA, _ScriptedReasoningClient, _fake_ops, evolution,
)


def _run(tmp_path, *, ops=None, **kwargs):
    if ops is None:
        ops = _fake_ops(tmp_path)[0]
    options = dict(
        cell={"cell_id": "cell-1", "task_id": "task-1", "mode": "G2",
              "experimental_arm": "AlphaApollo-Evolution+EVAS", "executable_feedback": True},
        release=tmp_path / "release", output_dir=tmp_path / "run",
        branches=[evolution.NativeEvolutionBranch(
            "branch-good", "provider/good", REASONING_BACKEND_SHA,
            lambda: _ScriptedReasoningClient("provider/good", ["write", "vabench-submit"]),
        )],
        command="fake-final", evas_command="fake-evas", rounds=1, max_steps=2,
        budgets={"model_calls": 3, "tool_calls": 3, "public_validation_calls": 1},
        ops=ops,
    )
    options.update(kwargs)
    return evolution.run_native_evolution(**options)


def test_branch_generation_export_is_no_evas_while_checkers_keep_original_cell(tmp_path):
    ops, final_calls, validation_calls, _, environments = _fake_ops(tmp_path)
    exports = []

    def export(cell, release, output, **kwargs):
        exports.append((output.name, deepcopy(cell)))
        ops.export_runtime(cell, release, output, **kwargs)

    cell = {"cell_id": "cell-1", "task_id": "task-1", "mode": "G2",
            "experimental_arm": "AlphaApollo-Evolution+EVAS", "executable_feedback": True}
    before = deepcopy(cell)
    run = _run(tmp_path, cell=cell, ops=replace(ops, export_runtime=export))
    assert cell == before
    by_path = dict(exports)
    assert by_path["runtime"]["experimental_arm"] == "Agent-No-EVAS"
    assert by_path["runtime"]["executable_feedback"] is False
    branch_environment = next(row for row in environments if row["branch"] is not None)
    assert branch_environment["cell"]["experimental_arm"] == "Agent-No-EVAS"
    assert branch_environment["context"].condition == before["experimental_arm"]
    assert by_path["public-validation-runtime"] == before
    assert by_path["final-runtime"] == before
    assert len(final_calls) == len(validation_calls) == 1
    config = json.loads((run.output_dir / "request.json").read_text())["config"]
    assert config["condition"] == before["experimental_arm"]
    assert config["branch_generation"]["exported_experimental_arm"] == "Agent-No-EVAS"
    branch = next((run.output_dir / "evolution/branches").glob("round-*/*/branch-runtime.json"))
    assert json.loads(branch.read_text())["exported_experimental_arm"] == "Agent-No-EVAS"


def test_real_r53_branch_export_has_no_evas_runtime_or_stale_private_spectre_claim(tmp_path):
    from test_agent_harness_evolution_campaign import _campaign
    from scripts import run_v4_r53_clean_room_smoke as smoke

    _, original = _campaign(tmp_path)
    cell = {**original, "experimental_arm": "AlphaApollo-Evolution+EVAS"}
    generation = evolution._branch_generation_cell(cell)
    branch_runtime = tmp_path / "branch"
    checker_runtime = tmp_path / "checker"
    evolution.runner.export_runtime(generation, smoke.DEFAULT_RELEASE, branch_runtime, timeout_s=30)
    evolution.runner.export_runtime(cell, smoke.DEFAULT_RELEASE, checker_runtime, timeout_s=30)
    assert not (branch_runtime / "public/task/evas_runtime.json").exists()
    assert (checker_runtime / "public/task/evas_runtime.json").is_file()
    policy = json.loads((branch_runtime / "MODEL_ACCESS_POLICY.json").read_text())
    assert policy["experimental_arm"] == "Agent-No-EVAS"
    assert "evas" not in policy["executables"]
    prompt = (branch_runtime / "agent_prompt.txt").read_text()
    assert "EVAS execution is not available" in prompt
    assert "final private Spectre judge" not in prompt
    assert "frozen submission" in prompt
