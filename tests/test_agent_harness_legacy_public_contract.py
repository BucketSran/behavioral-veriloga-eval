"""Legacy native sensitivity dispatch, not simulator or model-quality evidence."""

import json
import shlex
import shutil
import sys
from pathlib import Path

import pytest
from test_benchmarkv4_calibration_pilot import fake_evas_command, load_run_campaign

RELEASE = (
    Path(__file__).resolve().parents[1]
    / "benchmark-vabench-release-v4/release/benchmarkv4-r53"
)
CONTRACT_TASKS = [
    "001-bang-bang-phase-detector",
    "102-clocked-sine-source",
    "501-bang-bang-phase-detector-testbench",
    "602-clocked-sine-source-testbench",
]


def public_runtime(tmp_path, task_name):
    runtime = tmp_path / "runtime"
    task = runtime / "public/task"
    # Only released public inputs are copied; no evaluator or hidden fixture.
    shutil.copytree(RELEASE / "tasks" / task_name / "public", task)
    submission = runtime / "public/submission"
    submission.mkdir()
    if task_name.endswith("-testbench"):
        (submission / "testbench.scs").write_text('ahdl_include "./dut/dut.va"\n')
    return runtime


@pytest.mark.parametrize(
    "task_name",
    [
        "001-bang-bang-phase-detector",
        "1001-bang-bang-phase-detector-bugfix",
        "102-clocked-sine-source",
        "1102-clocked-sine-source-bugfix",
        "112-latched-comparator-delay",
        "1112-latched-comparator-delay-bugfix",
    ],
)
def test_legacy_tool_accepts_released_r53_dut_and_bugfix(tmp_path, task_name):
    runner = load_run_campaign()
    runtime = public_runtime(tmp_path, task_name)
    contract = json.loads((runtime / "public/task/evas_runtime.json").read_text())
    strict_args = (
        [] if contract.get("compatibility_mode") == "portable" else ["--spectre-strict"]
    )

    response, done = runner.execute_tool(
        "run_evas",
        {},
        runtime,
        30,
        fake_evas_command(tmp_path),
    )

    result = json.loads(response)
    assert not done
    assert result["status"] == "pass"
    assert result["case"] is None
    assert result["test"] == "public/task/visible_test.scs"
    output = runtime / ".vabench-visible/evas-output"
    invocation = json.loads((output / "invocation.json").read_text())
    assert invocation == {
        "cwd": str(runtime),
        "argv": [
            "simulate",
            str(runtime / "public/task/visible_test.scs"),
            "-o",
            str(output),
            *strict_args,
        ],
    }


@pytest.mark.parametrize(
    "task_name",
    [
        "501-bang-bang-phase-detector-testbench",
        "602-clocked-sine-source-testbench",
        "612-latched-comparator-delay-testbench",
    ],
)
def test_legacy_tool_accepts_released_r53_reference_only_testbench(tmp_path, task_name):
    runner = load_run_campaign()
    runtime = public_runtime(tmp_path, task_name)
    contract = json.loads((runtime / "public/task/evas_runtime.json").read_text())
    strict_args = (
        [] if contract.get("compatibility_mode") == "portable" else ["--spectre-strict"]
    )

    response, done = runner.execute_tool(
        "run_evas",
        {"case": "reference"},
        runtime,
        30,
        fake_evas_command(tmp_path),
    )

    result = json.loads(response)
    assert not done
    assert result["status"] == "pass"
    assert result["case"] == "reference"
    assert result["test"] == ".vabench-visible/reference/testbench.scs"
    scratch = runtime / ".vabench-visible"
    output = scratch / "evas-output/reference"
    invocation = json.loads((output / "invocation.json").read_text())
    assert invocation == {
        "cwd": str(runtime),
        "argv": [
            "simulate",
            str(scratch / "reference/testbench.scs"),
            "-o",
            str(output),
            *strict_args,
        ],
    }
    assert (scratch / "reference/testbench.scs").read_bytes() == (
        runtime / "public/submission/testbench.scs"
    ).read_bytes()
    reference = runtime / "public/task/supplied_dut"
    expected = {
        p.relative_to(reference): p.read_bytes()
        for p in reference.rglob("*")
        if p.is_file()
    }
    copied = scratch / "reference/dut"
    assert {
        p.relative_to(copied): p.read_bytes() for p in copied.rglob("*") if p.is_file()
    } == expected
    assert {p.name for p in scratch.iterdir()} == {"reference", "evas-output"}


@pytest.mark.parametrize("task_name", CONTRACT_TASKS)
@pytest.mark.parametrize(
    "change", ["mode", "mode_flip", "schema", "command", "flag", "cwd"]
)
def test_legacy_tool_rejects_malformed_r53_contract_before_execution(
    tmp_path, task_name, change
):
    runner = load_run_campaign()
    runtime = public_runtime(tmp_path, task_name)
    path = runtime / "public/task/evas_runtime.json"
    contract = json.loads(path.read_text())
    command_key = "candidate_command" if "candidate_command" in contract else "command"
    if change == "mode":
        contract["compatibility_mode"] = "unknown"
    elif change == "mode_flip":
        contract["compatibility_mode"] = (
            None if contract.get("compatibility_mode") == "portable" else "portable"
        )
    elif change == "schema":
        contract["schema_version"] = "r53-direct-evas-runtime-v999"
    elif change == "command":
        contract[command_key] += " && echo UNAUTHORIZED_METADATA_COMMAND"
    elif change == "flag":
        command = contract[command_key]
        contract[command_key] = (
            command.removesuffix(" --spectre-strict")
            if command.endswith(" --spectre-strict")
            else command + " --spectre-strict"
        )
    else:
        contract["working_directory"] = "evaluator"
    path.write_text(json.dumps(contract))

    with pytest.raises(ValueError, match="unsupported public validation contract"):
        runner.execute_tool("run_evas", {}, runtime, 30, fake_evas_command(tmp_path))

    assert not (runtime / ".vabench-visible").exists()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("candidate", "../evaluator/testbench.scs"),
        ("candidate_dut_binding", "../evaluator"),
        ("feedback_scope", "mutation_suite"),
        ("reference_dut_root", "../evaluator"),
    ],
)
def test_legacy_r53_testbench_rejects_authority_rebinding(tmp_path, field, value):
    runner = load_run_campaign()
    runtime = public_runtime(tmp_path, "602-clocked-sine-source-testbench")
    path = runtime / "public/task/evas_runtime.json"
    contract = json.loads(path.read_text())
    contract[field] = value
    path.write_text(json.dumps(contract))

    with pytest.raises(ValueError, match="unsupported public validation contract"):
        runner.execute_tool("run_evas", {}, runtime, 30, fake_evas_command(tmp_path))

    assert not (runtime / ".vabench-visible").exists()


@pytest.mark.parametrize("task_name", CONTRACT_TASKS)
@pytest.mark.parametrize("case", ["mutation_01", "../../evaluator"])
def test_legacy_r53_tool_rejects_nonpublic_case_before_execution(
    tmp_path, task_name, case
):
    runner = load_run_campaign()
    runtime = public_runtime(tmp_path, task_name)

    with pytest.raises(ValueError, match="reference-only|do not accept a case"):
        runner.execute_tool(
            "run_evas", {"case": case}, runtime, 30, fake_evas_command(tmp_path)
        )

    assert not (runtime / ".vabench-visible").exists()


@pytest.mark.parametrize("case", [None, "", "reference"])
def test_legacy_r53_testbench_defaults_to_reference(tmp_path, case):
    runner = load_run_campaign()
    runtime = public_runtime(tmp_path, "602-clocked-sine-source-testbench")

    response, done = runner.execute_tool(
        "run_evas",
        {"case": case},
        runtime,
        30,
        fake_evas_command(tmp_path),
    )

    assert not done
    assert json.loads(response)["case"] == "reference"


@pytest.mark.parametrize("task_name", CONTRACT_TASKS)
def test_legacy_r53_public_process_failure_is_not_success(tmp_path, task_name):
    runner = load_run_campaign()
    runtime = public_runtime(tmp_path, task_name)
    executable = shlex.join([sys.executable, "-c", "import sys; sys.exit(7)"])

    response, done = runner.execute_tool("run_evas", {}, runtime, 30, executable)

    result = json.loads(response)
    assert not done
    assert result["returncode"] == 7
    assert result["status"] == "fail"
    assert "score" not in result


@pytest.mark.parametrize("task_name", CONTRACT_TASKS[:2])
def test_legacy_r52_dut_contracts_keep_strict_and_portable_behavior(
    tmp_path, task_name
):
    runner = load_run_campaign()
    runtime = public_runtime(tmp_path, task_name)
    path = runtime / "public/task/evas_runtime.json"
    contract = json.loads(path.read_text())
    contract["schema_version"] = contract["schema_version"].replace("r53-", "r52-", 1)
    path.write_text(json.dumps(contract))

    response, _ = runner.execute_tool(
        "run_evas", {}, runtime, 30, fake_evas_command(tmp_path)
    )

    assert json.loads(response)["status"] == "pass"
    invocation = json.loads(
        (runtime / ".vabench-visible/evas-output/invocation.json").read_text()
    )
    assert ("--spectre-strict" in invocation["argv"]) == (
        contract.get("compatibility_mode") is None
    )


def test_legacy_r52_reference_contract_keeps_existing_minimal_fields(tmp_path):
    runner = load_run_campaign()
    runtime = public_runtime(tmp_path, "501-bang-bang-phase-detector-testbench")
    path = runtime / "public/task/evas_runtime.json"
    contract = json.loads(path.read_text())
    contract["schema_version"] = "r52-direct-evas-testbench-reference-v1"
    # These fields were not required by the historical fixed-argv adapter.
    del contract["candidate_command"]
    del contract["candidate_dut_binding"]
    path.write_text(json.dumps(contract))

    response, _ = runner.execute_tool(
        "run_evas", {}, runtime, 30, fake_evas_command(tmp_path)
    )

    assert json.loads(response)["status"] == "pass"
    invocation = json.loads(
        (runtime / ".vabench-visible/evas-output/reference/invocation.json").read_text()
    )
    assert "--spectre-strict" in invocation["argv"]
