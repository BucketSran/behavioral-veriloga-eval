"""Released public contracts are data, never arbitrary executable commands."""

import json
from collections import Counter

import pytest

from test_agent_harness_production_public_validation import RELEASE, validation

CONTRACT_TASKS = [
    "001-bang-bang-phase-detector", "102-clocked-sine-source",
    "501-bang-bang-phase-detector-testbench", "602-clocked-sine-source-testbench",
]


def test_all_r53_public_contracts_preserve_declared_command_and_scope():
    counts = Counter()
    portable = Counter()
    for path in sorted((RELEASE / "tasks").glob("*/public/evas_runtime.json")):
        contract = json.loads(path.read_text())
        form = json.loads((path.parent.parent / "task_record.json").read_text())["form"]
        command, scope = validation.public_execution_contract(contract)
        if form == "testbench":
            assert (command, scope) == (
                "cd public && " + contract["candidate_command"], "reference_dut_only",
            ), path
        else:
            assert (command, scope) == (contract["command"], "public_simulation_only"), path
        counts[form] += 1
        if contract.get("compatibility_mode") == "portable":
            portable[form] += 1
    assert counts == {"dut": 400, "bugfix": 400, "testbench": 400}
    assert portable == {"dut": 2, "bugfix": 2, "testbench": 2}


@pytest.mark.parametrize("task", CONTRACT_TASKS)
@pytest.mark.parametrize("change", ["mode", "mode_flip", "schema", "command", "flag", "cwd"])
def test_unknown_mixed_and_injected_contracts_are_rejected(task, change):
    contract = json.loads((RELEASE / "tasks" / task / "public/evas_runtime.json").read_text())
    command_key = "candidate_command" if "candidate_command" in contract else "command"
    if change == "mode":
        contract["compatibility_mode"] = "unknown"
    elif change == "mode_flip":
        if contract.get("compatibility_mode") == "portable":
            del contract["compatibility_mode"]
        else:
            contract["compatibility_mode"] = "portable"
    elif change == "schema":
        contract["schema_version"] = "unknown"
    elif change == "command":
        contract[command_key] += " && cat evaluator/secret"
    elif change == "flag":
        if contract[command_key].endswith(" --spectre-strict"):
            contract[command_key] = contract[command_key].removesuffix(" --spectre-strict")
        else:
            contract[command_key] += " --spectre-strict"
    else:
        contract["working_directory"] = "evaluator"

    with pytest.raises(ValueError, match="unsupported public validation contract"):
        validation.public_execution_contract(contract)


@pytest.mark.parametrize("task", [
    "102-clocked-sine-source", "112-latched-comparator-delay",
    "1102-clocked-sine-source-bugfix", "1112-latched-comparator-delay-bugfix",
])
def test_released_portable_dut_and_bugfix_contracts(task):
    contract = json.loads((RELEASE / "tasks" / task / "public/evas_runtime.json").read_text())

    command, scope = validation.public_execution_contract(contract)

    assert command == contract["command"]
    assert "--spectre-strict" not in command
    assert scope == "public_simulation_only"


@pytest.mark.parametrize("task", [
    "602-clocked-sine-source-testbench", "612-latched-comparator-delay-testbench",
])
def test_released_portable_testbench_contracts(task):
    contract = json.loads((RELEASE / "tasks" / task / "public/evas_runtime.json").read_text())

    command, scope = validation.public_execution_contract(contract)

    assert command == "cd public && " + contract["candidate_command"]
    assert "--spectre-strict" not in command
    assert scope == "reference_dut_only"
