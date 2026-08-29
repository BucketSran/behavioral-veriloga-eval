from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_POLICY = (
    ROOT / "benchmark-vabench-release-v4" / "EXPERIMENT_POLICY.json"
)
AGENT_WALL_TIME_SECONDS = json.loads(
    EXPERIMENT_POLICY.read_text(encoding="utf-8")
)["agent_wall_time_seconds"]
RELEASE = ROOT / "benchmark-vabench-release-v4" / "release" / "benchmarkv4"
R49_RELEASE = ROOT / "benchmark-vabench-release-v4" / "release" / "benchmarkv4-r49"
R52_RELEASE = ROOT / "benchmark-vabench-release-v4" / "release" / "benchmarkv4-r52"
BUILD_CAMPAIGN = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "operations"
    / "calibration_pilot"
    / "build_campaign.py"
)
RUN_CAMPAIGN_WRAPPER = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "runners"
    / "run_benchmarkv4_campaign.py"
)
RUN_CAMPAIGN_DETACHED = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "runners"
    / "run_benchmarkv4_campaign_detached.sh"
)
RUN_CAMPAIGN = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "operations"
    / "calibration_pilot"
    / "run_campaign.py"
)
SCORE_CAMPAIGN = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "operations"
    / "calibration_pilot"
    / "score_campaign.py"
)
TRUSTED_REPLAY_ADAPTER = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "operations"
    / "calibration_pilot"
    / "trusted_replay_adapter.py"
)
TESTBENCH_SECURITY = ROOT / "benchmark-vabench-release-v4" / "runners" / "testbench_security.py"
DERIVED_TESTBENCH_ORACLE = (
    ROOT / "benchmark-vabench-release-v4" / "runners" / "derived_testbench_oracle.py"
)
RENDER_HARNESS = ROOT / "benchmark-vabench-release-v4" / "scripts" / "render_v4_harness.py"
FEEDBACK_ADAPTER = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "operations"
    / "calibration_pilot"
    / "feedback_adapter.py"
)
PREPARE_BUDGET_REUSE = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "operations"
    / "calibration_pilot"
    / "prepare_budget_reuse.py"
)
MATERIALIZE_RELEASE = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "operations"
    / "tri_form_derivation_prep"
    / "materialize_tri_form_release.py"
)


@pytest.fixture(scope="session")
def r45_release(tmp_path_factory: pytest.TempPathFactory) -> Path:
    release = tmp_path_factory.mktemp("benchmarkv4-r45") / "release"
    subprocess.run(
        [
            sys.executable,
            str(MATERIALIZE_RELEASE),
            "--release-revision",
            "r45",
            "--output",
            str(release),
            "--force",
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        check=True,
    )
    return release


def load_build_campaign():
    spec = importlib.util.spec_from_file_location("build_campaign", BUILD_CAMPAIGN)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_run_campaign():
    spec = importlib.util.spec_from_file_location("run_campaign", RUN_CAMPAIGN)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_score_campaign():
    spec = importlib.util.spec_from_file_location("score_campaign_test", SCORE_CAMPAIGN)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_trusted_replay_adapter():
    spec = importlib.util.spec_from_file_location(
        "trusted_replay_adapter_test", TRUSTED_REPLAY_ADAPTER
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_run_campaign_wrapper():
    spec = importlib.util.spec_from_file_location(
        "run_benchmarkv4_campaign_test", RUN_CAMPAIGN_WRAPPER
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_testbench_security():
    spec = importlib.util.spec_from_file_location("testbench_security", TESTBENCH_SECURITY)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_derived_testbench_oracle():
    spec = importlib.util.spec_from_file_location(
        "derived_testbench_oracle", DERIVED_TESTBENCH_ORACLE
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_feedback_adapter():
    spec = importlib.util.spec_from_file_location("feedback_adapter", FEEDBACK_ADAPTER)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_render_harness():
    spec = importlib.util.spec_from_file_location("render_v4_harness", RENDER_HARNESS)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_prepare_budget_reuse():
    spec = importlib.util.spec_from_file_location("prepare_budget_reuse", PREPARE_BUDGET_REUSE)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_runtime_policy(runtime: Path, artifacts: list[str]) -> None:
    evaluator = runtime / "evaluator"
    evaluator.mkdir(parents=True)
    (evaluator / "score_policy.json").write_text(
        json.dumps({"candidate_artifacts": artifacts}),
        encoding="utf-8",
    )


def campaign_cell(mode: str, release: Path = RELEASE) -> dict:
    campaign = load_build_campaign().build_campaign(
        release,
        family_ids=["001"],
        model_provider="test",
        model="test-model",
        per_turn_max_tokens=4096,
        repetitions=1,
    )
    return next(
        cell
        for cell in campaign["cells"]
        if cell["task_id"] == "v4-001" and cell["mode"] == mode
    )


def run_args(output: Path, release: Path = RELEASE) -> SimpleNamespace:
    return SimpleNamespace(
        output=output,
        release=release,
        resume=False,
        dry_run=False,
        final_judge_command=None,
        agent_timeout_s=AGENT_WALL_TIME_SECONDS,
        setup_timeout_s=1800,
        request_timeout_s=1800,
        tool_timeout_s=30,
        judge_timeout_s=30,
        evas_command="evas",
    )


class FakeClient:
    def __init__(self, message: dict, *, finish_reason: str = "stop") -> None:
        self.message = message
        self.finish_reason = finish_reason

    def complete(self, _messages, _max_tokens, _tools, **_kwargs):
        return {
            "id": "fake-response",
            "model": "test-model",
            "choices": [
                {"message": self.message, "finish_reason": self.finish_reason}
            ],
            "usage": {"completion_tokens": 32},
        }


class UnexpectedClientCall:
    def complete(self, *_args, **_kwargs):
        raise AssertionError("resume should finish checkpointed tool calls before another model call")


class MiniSweFakeClient:
    model = "test-model"

    def __init__(self, commands: list[str]) -> None:
        self.commands = list(commands)

    def complete(self, _messages, _max_tokens, _tools, **_kwargs):
        command = self.commands.pop(0)
        return {
            "id": f"mini-{len(self.commands)}",
            "model": self.model,
            "choices": [
                {
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": f"call-{len(self.commands)}",
                                "type": "function",
                                "function": {
                                    "name": "bash",
                                    "arguments": json.dumps({"command": command}),
                                },
                            }
                        ],
                    },
                }
            ],
            "usage": {"completion_tokens": 7},
        }


def fake_evas_command(tmp_path: Path) -> str:
    script = tmp_path / "fake_evas.py"
    script.write_text(
        """from pathlib import Path
import json
import sys
args = sys.argv[1:]
output = Path(args[args.index('-o') + 1])
output.mkdir(parents=True, exist_ok=True)
(output / 'invocation.json').write_text(json.dumps({'argv': args, 'cwd': str(Path.cwd())}))
""",
        encoding="utf-8",
    )
    return f"{sys.executable} {script}"


def test_active_agent_tools_expose_restricted_evas_not_feedback() -> None:
    runner = load_run_campaign()
    names = [tool["function"]["name"] for tool in runner.TOOLS]
    assert names == ["list_files", "read_file", "write_file", "run_evas", "finalize"]


def test_campaign_runner_defaults_to_latest_r53_release() -> None:
    runner = load_run_campaign()
    wrapper = load_run_campaign_wrapper()

    assert runner.DEFAULT_RELEASE.name == "benchmarkv4-r53"
    assert wrapper.DEFAULT_RELEASE == runner.DEFAULT_RELEASE
    assert (
        "--agent-timeout-s"
        not in wrapper.build_parser()._option_string_actions
    )


@pytest.mark.parametrize(
    ("release_revision", "runtime_version"),
    [("r45", 1), ("r45", 2), ("r47", 2), ("r50", 2), ("r51", 2)],
)
def test_run_evas_dut_uses_fixed_public_contract(
    tmp_path: Path, release_revision: str, runtime_version: int,
) -> None:
    runner = load_run_campaign()
    runtime = tmp_path / "runtime"
    task = runtime / "public" / "task"
    submission = runtime / "public" / "submission"
    task.mkdir(parents=True)
    submission.mkdir(parents=True)
    (task / "visible_test.scs").write_text("tran tran stop=1n\n", encoding="utf-8")
    output_contract = (
        "/tmp/vabench-visible/evas-output"
        if runtime_version == 2
        else "public/submission/evas-output"
    )
    (task / "evas_runtime.json").write_text(json.dumps({
        "schema_version": f"{release_revision}-direct-evas-runtime-v{runtime_version}",
        "command": f"evas simulate public/task/visible_test.scs -o {output_contract} --spectre-strict",
        "working_directory": "runtime_package_root",
    }) + "\n", encoding="utf-8")

    result = runner.run_public_evas(runtime, {}, 30, fake_evas_command(tmp_path))

    assert result["status"] == "pass"
    output = runtime / ".vabench-visible" / "evas-output"
    invocation = json.loads((output / "invocation.json").read_text(encoding="utf-8"))
    assert invocation["cwd"] == str(runtime)
    assert invocation["argv"][0] == "simulate"
    assert Path(invocation["argv"][1]) == task / "visible_test.scs"
    assert Path(invocation["argv"][invocation["argv"].index("-o") + 1]) == output
    assert "--spectre-strict" in invocation["argv"]


@pytest.mark.parametrize(
    ("task_name", "expects_spectre_strict"),
    [
        ("001-bang-bang-phase-detector", True),
        ("1001-bang-bang-phase-detector-bugfix", True),
        ("102-clocked-sine-source", False),
        ("1102-clocked-sine-source-bugfix", False),
    ],
)
def test_run_evas_accepts_published_r52_dut_and_bugfix_contracts(
    tmp_path: Path, task_name: str, expects_spectre_strict: bool,
) -> None:
    runner = load_run_campaign()
    runtime = tmp_path / task_name
    task = runtime / "public" / "task"
    submission = runtime / "public" / "submission"
    shutil.copytree(R52_RELEASE / "tasks" / task_name / "public", task)
    submission.mkdir(parents=True)

    result = runner.run_public_evas(runtime, {}, 30, fake_evas_command(tmp_path))

    assert result["status"] == "pass"
    output = runtime / ".vabench-visible" / "evas-output"
    invocation = json.loads((output / "invocation.json").read_text(encoding="utf-8"))
    assert ("--spectre-strict" in invocation["argv"]) is expects_spectre_strict


def test_run_evas_dut_honors_portable_rdist_contract(tmp_path: Path) -> None:
    runner = load_run_campaign()
    runtime = tmp_path / "runtime"
    task = runtime / "public" / "task"
    submission = runtime / "public" / "submission"
    task.mkdir(parents=True)
    submission.mkdir(parents=True)
    (task / "visible_test.scs").write_text("tran tran stop=1n\n", encoding="utf-8")
    (task / "evas_runtime.json").write_text(json.dumps({
        "schema_version": "r51-direct-evas-runtime-v3",
        "compatibility_mode": "portable",
        "command": (
            "evas simulate public/task/visible_test.scs "
            "-o /tmp/vabench-visible/evas-output"
        ),
        "working_directory": "runtime_package_root",
    }) + "\n", encoding="utf-8")

    result = runner.run_public_evas(runtime, {}, 30, fake_evas_command(tmp_path))

    assert result["status"] == "pass"
    invocation = json.loads(
        (runtime / ".vabench-visible" / "evas-output" / "invocation.json").read_text(
            encoding="utf-8"
        )
    )
    assert "--spectre-strict" not in invocation["argv"]


@pytest.mark.parametrize("attack", ["symlink", "private_include"])
def test_run_evas_rejects_candidate_source_escape_before_execution(
    tmp_path: Path, attack: str
) -> None:
    runner = load_run_campaign()
    runtime = tmp_path / "runtime"
    task = runtime / "public" / "task"
    submission = runtime / "public" / "submission"
    evaluator = runtime / "evaluator" / "solution"
    task.mkdir(parents=True)
    submission.mkdir(parents=True)
    evaluator.mkdir(parents=True)
    private = evaluator / "private.va"
    private.write_text("PRIVATE_GOLD_MARKER", encoding="utf-8")
    (task / "visible_test.scs").write_text("tran tran stop=1n\n", encoding="utf-8")
    (task / "evas_runtime.json").write_text(
        json.dumps(
            {
                "schema_version": "r47-direct-evas-runtime-v2",
                "command": (
                    "evas simulate public/task/visible_test.scs -o "
                    "/tmp/vabench-visible/evas-output --spectre-strict"
                ),
                "working_directory": "runtime_package_root",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    candidate = submission / "model.va"
    if attack == "symlink":
        candidate.symlink_to(private)
    else:
        candidate.write_text(
            '`include "../../evaluator/solution/private.va"\nmodule model; endmodule\n',
            encoding="utf-8",
        )

    result = runner.run_public_evas(runtime, {}, 30, fake_evas_command(tmp_path))

    assert result["execution_status"] == "candidate_rejected"
    assert result["returncode"] != 0
    assert "PRIVATE_GOLD_MARKER" not in json.dumps(result)
    assert not (runtime / ".vabench-visible" / "evas-output" / "invocation.json").exists()


@pytest.mark.parametrize(
    ("release_revision", "runtime_version"),
    [("r45", 1), ("r45", 2), ("r47", 2), ("r50", 2), ("r51", 2)],
)
def test_run_evas_testbench_uses_candidate_and_public_case_only(
    tmp_path: Path, release_revision: str, runtime_version: int,
) -> None:
    runner = load_run_campaign()
    runtime = tmp_path / "runtime"
    task = runtime / "public" / "task"
    submission = runtime / "public" / "submission"
    fixture_roots = {}
    for case in ["reference", *(f"mutation_{index:02d}" for index in range(1, 6))]:
        fixture_roots[case] = task / "visible_fixtures" / case / "dut"
        fixture_roots[case].mkdir(parents=True)
        (fixture_roots[case] / "dut.va").write_text(
            f"module dut; // {case}\nendmodule\n", encoding="utf-8"
        )
    fixture = fixture_roots["reference"]
    submission.mkdir(parents=True)
    (submission / "testbench.scs").write_text('ahdl_include "./dut/dut.va"\n', encoding="utf-8")
    (task / "evas_runtime.json").write_text(json.dumps({
        "schema_version": f"{release_revision}-direct-evas-testbench-suite-v{runtime_version}",
        "candidate": "public/submission/testbench.scs",
        "fixture_policy": "read_only_and_identical_for_visible_and_final_replay",
        "working_directory": "runtime_package_root",
        "cases": [
            {"case": case, "dut_root": f"visible_fixtures/{case}/dut"}
            for case in fixture_roots
        ],
    }) + "\n", encoding="utf-8")

    result = runner.run_public_evas(
        runtime, {"case": "reference"}, 30, fake_evas_command(tmp_path)
    )

    assert result["status"] == "pass"
    scratch_root = runtime / ".vabench-visible"
    run_dir = scratch_root / "runs" / "reference"
    assert (run_dir / "testbench.scs").read_bytes() == (submission / "testbench.scs").read_bytes()
    assert (run_dir / "dut" / "dut.va").read_bytes() == (fixture / "dut.va").read_bytes()
    write_runtime_policy(runtime, ["testbench.scs"])
    assert runner.submission_artifact_gate(runtime)["passed"] is True
    try:
        runner.run_public_evas(
            runtime, {"case": "../../evaluator"}, 30, fake_evas_command(tmp_path)
        )
    except ValueError as exc:
        assert "unknown public EVAS case" in str(exc)
    else:
        raise AssertionError("run_evas accepted a case outside the public suite")

    (submission / "testbench.scs").write_text(
        'ahdl_include "/etc/passwd"\n', encoding="utf-8"
    )
    rejected = runner.run_public_evas(
        runtime, {"case": "reference"}, 30, fake_evas_command(tmp_path)
    )
    assert rejected["execution_status"] == "candidate_rejected"
    assert "unsafe_source_include" in rejected["stderr"]


def test_run_evas_testbench_honors_portable_rdist_contract(tmp_path: Path) -> None:
    runner = load_run_campaign()
    runtime = tmp_path / "runtime"
    task = runtime / "public" / "task"
    submission = runtime / "public" / "submission"
    cases = []
    for case in ["reference", *(f"mutation_{index:02d}" for index in range(1, 6))]:
        fixture = task / "visible_fixtures" / case / "dut"
        fixture.mkdir(parents=True)
        (fixture / "dut.va").write_text("module dut; endmodule\n", encoding="utf-8")
        cases.append({"case": case, "dut_root": f"visible_fixtures/{case}/dut"})
    submission.mkdir(parents=True)
    (submission / "testbench.scs").write_text(
        'ahdl_include "./dut/dut.va"\n', encoding="utf-8"
    )
    (task / "evas_runtime.json").write_text(json.dumps({
        "schema_version": "r51-direct-evas-testbench-suite-v3",
        "compatibility_mode": "portable",
        "candidate": "public/submission/testbench.scs",
        "candidate_command_template": (
            "evas simulate /tmp/vabench-visible/runs/{case}/testbench.scs "
            "-o /tmp/vabench-visible/evas-output/{case}"
        ),
        "fixture_policy": "read_only_and_identical_for_visible_and_final_replay",
        "working_directory": "runtime_package_root",
        "cases": cases,
    }) + "\n", encoding="utf-8")

    result = runner.run_public_evas(
        runtime, {"case": "reference"}, 30, fake_evas_command(tmp_path)
    )

    assert result["status"] == "pass"
    assert result["test"] == ".vabench-visible/runs/reference/testbench.scs"
    invocation = json.loads(
        (
            runtime
            / ".vabench-visible"
            / "evas-output"
            / "reference"
            / "invocation.json"
        ).read_text(encoding="utf-8")
    )
    assert "--spectre-strict" not in invocation["argv"]


def test_r47_runtime_rejects_legacy_v1_schema(tmp_path: Path) -> None:
    runner = load_run_campaign()
    runtime = tmp_path / "runtime"
    task = runtime / "public" / "task"
    submission = runtime / "public" / "submission"
    task.mkdir(parents=True)
    submission.mkdir(parents=True)
    (task / "visible_test.scs").write_text("tran tran stop=1n\n", encoding="utf-8")
    (task / "evas_runtime.json").write_text(json.dumps({
        "schema_version": "r47-direct-evas-runtime-v1",
        "command": "evas simulate public/task/visible_test.scs -o public/submission/evas-output --spectre-strict",
        "working_directory": "runtime_package_root",
    }) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported public EVAS runtime schema"):
        runner.run_public_evas(runtime, {}, 30, fake_evas_command(tmp_path))


def test_build_campaign_samples_complete_benchmarkv4_families_without_prompt_records() -> None:
    builder = load_build_campaign()

    campaign = builder.build_campaign(
        RELEASE,
        sample_families=2,
        seed=20260715,
        model_provider="openai-compatible",
        model="deepseek-v4-flash",
        per_turn_max_tokens=65536,
        repetitions=1,
    )

    assert campaign["schema_version"] == "v4-calibration-campaign-v3"
    assert campaign["termination_policy"] == "wall_time"
    assert campaign["budget_metric"] == "agent_wall_time_seconds"
    assert campaign["agent_wall_time_seconds"] == 1800
    assert campaign["experiment_policy_sha256"] == hashlib.sha256(
        EXPERIMENT_POLICY.read_bytes()
    ).hexdigest()
    assert campaign["timeout_finalization"] == {
        "artifact_source": "latest_complete_declared_submission",
        "score_complete_artifact": True,
        "termination_reason": "agent_timeout",
    }
    assert campaign["token_accounting"] == "telemetry_only"
    assert campaign["per_turn_max_tokens"] == 65536
    assert campaign["release"].endswith("release/benchmarkv4")
    assert campaign["family_count"] == 2
    assert campaign["task_count"] == 6
    assert campaign["cell_count"] == 36
    assert campaign["selection"]["method"] == "complete_family_sample_without_replacement"

    by_mode = {cell["mode"]: cell for cell in campaign["cells"][:6]}
    assert by_mode["G0"]["process"] == "direct_one_shot"
    assert by_mode["G0"]["evas_cli_available"] is False
    assert by_mode["G1"]["process"] == "direct_one_shot"
    assert by_mode["G2"]["process"] == "agentic"
    assert by_mode["G2"]["evas_cli_available"] is True
    assert by_mode["G5"]["response_protocol"] == "v4-strict-workspace-finalizer-v1"


def test_executable_feedback_control_builds_three_matched_arms() -> None:
    builder = load_build_campaign()
    wrapper = load_run_campaign_wrapper()
    campaign = builder.build_campaign(
        R52_RELEASE,
        family_ids=["001"],
        model_provider="openai-compatible",
        model="deepseek-v4-flash",
        per_turn_max_tokens=65536,
        repetitions=1,
    )

    control = wrapper.build_executable_feedback_control(campaign)
    by_arm = {
        arm: [
            cell
            for cell in control["cells"]
            if cell["experimental_arm"] == arm
        ]
        for arm in ("OneShot", "Agent-No-EVAS", "Agentic")
    }

    assert control["arms"] == ["OneShot", "Agent-No-EVAS", "Agentic"]
    assert control["cell_count"] == 9
    assert {cell["mode"] for cell in by_arm["OneShot"]} == {"G0"}
    assert {cell["mode"] for cell in by_arm["Agent-No-EVAS"]} == {"G2"}
    assert {cell["mode"] for cell in by_arm["Agentic"]} == {"G2"}
    assert {
        cell["executable_feedback"] for cell in by_arm["Agent-No-EVAS"]
    } == {False}
    assert {cell["executable_feedback"] for cell in by_arm["Agentic"]} == {True}
    assert len({cell["task_id"] for cell in control["cells"]}) == 3


def test_executable_feedback_control_scales_to_all_r52_families() -> None:
    builder = load_build_campaign()
    wrapper = load_run_campaign_wrapper()
    campaign = builder.build_campaign(
        R52_RELEASE,
        sample_families=400,
        seed=20260726,
        model_provider="openai-compatible",
        model="deepseek-v4-flash",
        per_turn_max_tokens=65536,
        repetitions=1,
    )

    control = wrapper.build_executable_feedback_control(campaign)

    assert control["family_count"] == 400
    assert control["task_count"] == 1200
    assert control["cell_count"] == 3600
    assert {
        arm: sum(
            cell["experimental_arm"] == arm for cell in control["cells"]
        )
        for arm in control["arms"]
    } == {
        "OneShot": 1200,
        "Agent-No-EVAS": 1200,
        "Agentic": 1200,
    }


def test_campaign_wrapper_exposes_agent_no_evas_control_profile(
    tmp_path: Path,
) -> None:
    output = tmp_path / "three-arm-control"
    completed = subprocess.run(
        [
            sys.executable,
            str(RUN_CAMPAIGN_WRAPPER),
            "--release",
            str(R52_RELEASE),
            "--task-id",
            "v4-001",
            "--comparison-profile",
            "executable-feedback-control",
            "--output-root",
            str(output),
            "--model",
            "test-model",
            "--dry-run",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    campaign = json.loads((output / "campaign.json").read_text(encoding="utf-8"))
    assert campaign["cell_count"] == 3
    assert campaign["filters"]["experimental_arms"] == []
    assert campaign["execution_config"]["mini_swe_no_evas_image"] == (
        "vabench-agent-runtime:0.8.7-no-evas"
    )
    assert campaign["execution_config"]["mini_swe_preflight_timeout_s"] == 60
    assert campaign["execution_config"]["mini_swe_preflight_attempts"] == 2
    assert campaign["execution_config"]["mini_swe_startup_workers"] == 8
    wrapper = json.loads(
        (output / "wrapper_summary.json").read_text(encoding="utf-8")
    )
    assert wrapper["mini_swe_preflight_timeout_s"] == 60
    assert wrapper["mini_swe_preflight_attempts"] == 2
    assert wrapper["mini_swe_startup_workers"] == 8
    assert "--mini-swe-preflight-timeout-s" in wrapper["command"]
    assert "--mini-swe-preflight-attempts" in wrapper["command"]
    assert "--mini-swe-startup-workers" in wrapper["command"]
    assert {cell["experimental_arm"] for cell in campaign["cells"]} == {
        "OneShot",
        "Agent-No-EVAS",
        "Agentic",
    }
    no_evas_cell = next(
        cell
        for cell in campaign["cells"]
        if cell["experimental_arm"] == "Agent-No-EVAS"
    )
    runtime = output / "run" / no_evas_cell["cell_id"]
    assert not (runtime / "public" / "task" / "evas_runtime.json").exists()
    effective_prompt = (runtime / "agent_prompt.txt").read_text(encoding="utf-8")
    assert "EVAS execution is not available" in effective_prompt
    policy = json.loads(
        (runtime / "MODEL_ACCESS_POLICY.json").read_text(encoding="utf-8")
    )
    assert "evas" not in policy["executables"]
    assert policy["experimental_arm"] == "Agent-No-EVAS"
    arm_record = json.loads(
        (runtime / "evidence" / "experimental_arm.json").read_text(
            encoding="utf-8"
        )
    )
    assert arm_record["base_prompt_record_sha256"] == no_evas_cell[
        "prompt_record_sha256"
    ]
    assert arm_record["effective_prompt_sha256"] == hashlib.sha256(
        effective_prompt.encode()
    ).hexdigest()


def test_direct_parser_recovers_single_file_filename_marker_without_strict_compliance(
    tmp_path: Path,
) -> None:
    runner = load_run_campaign()
    runtime = tmp_path / "runtime"
    write_runtime_policy(runtime, ["element_shuffler.va"])

    text = (
        "<<<element_shuffler.va>>>\n"
        "module element_shuffler; endmodule\n"
        "<<<END_VABENCH_ARTIFACT>>>"
    )

    strict_mapping, strict_protocol = runner.parse_direct_artifacts(text, runtime)
    mapping, protocol = runner.parse_recoverable_direct_artifacts(text, runtime)

    assert strict_mapping is None
    assert strict_protocol == "invalid_exact_artifact_envelope"
    assert protocol == "normalized_filename_artifact_envelope"
    assert mapping == {"element_shuffler.va": "module element_shuffler; endmodule"}
    assert runner.direct_protocol_compliant(protocol) is False


def test_direct_parser_recovers_single_file_input_marker_without_strict_compliance(
    tmp_path: Path,
) -> None:
    runner = load_run_campaign()
    runtime = tmp_path / "runtime"
    write_runtime_policy(runtime, ["flash_folded_dac4.va"])

    text = (
        '<<<VABENCH_INPUT_ARTIFACT path="flash_folded_dac4.va">>\n'
        "module flash_folded_dac4; endmodule\n"
        "<<<END_VABENCH_ARTIFACT>>>"
    )

    strict_mapping, strict_protocol = runner.parse_direct_artifacts(text, runtime)
    mapping, protocol = runner.parse_recoverable_direct_artifacts(text, runtime)

    assert strict_mapping is None
    assert strict_protocol == "invalid_exact_artifact_envelope"
    assert protocol == "normalized_input_artifact_envelope"
    assert mapping == {"flash_folded_dac4.va": "module flash_folded_dac4; endmodule"}
    assert runner.direct_protocol_compliant(protocol) is False


def test_direct_parser_preserves_exact_body_and_records_evidence(tmp_path: Path) -> None:
    runner = load_run_campaign()
    runtime = tmp_path / "runtime"
    write_runtime_policy(runtime, ["nested/model.va"])
    (runtime / "public" / "submission").mkdir(parents=True)
    body = "\nmodule model;\nendmodule\n"
    text = (
        '<<<VABENCH_ARTIFACT path="nested/model.va">>>\n'
        f"{body}\n"
        "<<<END_VABENCH_ARTIFACT>>>\n"
    )

    result = runner.extract_direct_submission(text, runtime)

    artifact = runtime / "public" / "submission" / "nested" / "model.va"
    assert result["submission_protocol_compliant"] is True
    assert result["parse_diagnostics"] == []
    assert artifact.read_text(encoding="utf-8") == body
    assert result["response_sha256"] == hashlib.sha256(text.encode()).hexdigest()
    assert result["artifact_sha256"]["nested/model.va"] == hashlib.sha256(
        body.encode()
    ).hexdigest()


def test_direct_submission_tool_requires_the_complete_declared_bundle(
    tmp_path: Path,
) -> None:
    runner = load_run_campaign()
    runtime = tmp_path / "runtime"
    write_runtime_policy(runtime, ["model.va", "support.inc"])
    (runtime / "MODEL_ACCESS_POLICY.json").write_text(
        json.dumps({
            "mode": "G0",
            "available_skills": {},
            "provider_tools": [],
        }),
        encoding="utf-8",
    )

    tools = runner.active_tool_schemas(runtime, "G0")

    assert tools is not None
    assert [tool["function"]["name"] for tool in tools] == ["submit_artifacts"]
    artifacts = tools[0]["function"]["parameters"]["properties"]["artifacts"]
    assert artifacts["required"] == ["model.va", "support.inc"]
    assert artifacts["additionalProperties"] is False


def test_submit_artifacts_writes_only_a_complete_declared_bundle(tmp_path: Path) -> None:
    runner = load_run_campaign()
    runtime = tmp_path / "runtime"
    write_runtime_policy(runtime, ["top.va", "blocks/child.va"])
    (runtime / "public" / "submission").mkdir(parents=True)

    text, finalized = runner.execute_tool(
        "submit_artifacts",
        {
            "artifacts": {
                "top.va": "module top; endmodule\n",
                "blocks/child.va": "module child; endmodule\n",
            }
        },
        runtime,
        30,
        "evas",
    )

    result = json.loads(text)
    assert finalized is True
    assert result["status"] == "submitted"
    assert result["saved_files"] == ["blocks/child.va", "top.va"]

    with pytest.raises(ValueError, match="missing_artifact_path:blocks/child.va"):
        runner.execute_tool(
            "submit_artifacts",
            {"artifacts": {"top.va": "module top; endmodule\n"}},
            runtime,
            30,
            "evas",
        )


def test_direct_text_fallback_normalizes_transport_without_reading_semantics(
    tmp_path: Path,
) -> None:
    runner = load_run_campaign()
    runtime = tmp_path / "runtime"
    write_runtime_policy(runtime, ["model.va"])
    (runtime / "public" / "submission").mkdir(parents=True)

    result = runner.extract_normalized_direct_submission(
        "```verilog\nmodule model; endmodule\n```",
        runtime,
    )

    assert result["submission_protocol_compliant"] is True
    assert result["original_protocol_compliant"] is False
    assert result["submission_transport"] == "runner_normalized_text"
    assert (runtime / "public" / "submission" / "model.va").read_text(
        encoding="utf-8"
    ) == "module model; endmodule\n"


def test_submit_artifacts_normalizer_accepts_only_identical_redundant_content() -> None:
    runner = load_run_campaign()
    artifacts = {"model.va": "module model; endmodule\n"}

    decoded, compliant, normalization = runner.decode_tool_arguments(
        "submit_artifacts",
        json.dumps({"artifacts": artifacts, **artifacts}) + "}",
    )

    assert decoded == {"artifacts": artifacts}
    assert compliant is False
    assert normalization == "redundant_artifact_wrapper"
    with pytest.raises(ValueError, match="conflicting submit_artifacts wrapper fields"):
        runner.decode_tool_arguments(
            "submit_artifacts",
            json.dumps({
                "artifacts": artifacts,
                "model.va": "module conflicting; endmodule\n",
            }) + "}",
        )


def test_submit_artifacts_normalizer_completes_one_missing_object_closer() -> None:
    runner = load_run_campaign()
    artifacts = {"testbench.scs": "simulator lang=spectre\n"}
    malformed = json.dumps({"artifacts": artifacts})[:-1]

    decoded, compliant, normalization = runner.decode_tool_arguments(
        "submit_artifacts", malformed
    )

    assert decoded == {"artifacts": artifacts}
    assert compliant is False
    assert normalization == "completed_missing_closer"


def test_submit_artifacts_normalizer_removes_trailing_marker_fragment() -> None:
    runner = load_run_campaign()
    artifacts = {"testbench.scs": "save vout\n"}
    malformed = json.dumps({"artifacts": artifacts})[:-1] + ">}"

    decoded, compliant, normalization = runner.decode_tool_arguments(
        "submit_artifacts", malformed
    )

    assert decoded == {"artifacts": artifacts}
    assert compliant is False
    assert normalization == "removed_trailing_marker_fragment"


def test_submit_artifacts_tool_uses_provider_neutral_auto_tool_choice() -> None:
    runner = load_run_campaign()
    client = runner.OpenAICompatible(
        base_url="https://provider.invalid/v1",
        model="test-model",
        api_key="test-key",
        timeout_s=30,
        temperature=0.0,
        stream=True,
    )
    captured: dict[str, object] = {}

    def capture(payload, *, timeout_s):
        captured.update(payload)
        return {"choices": [{"message": {"role": "assistant", "content": ""}}]}

    client._complete_stream = capture
    client.complete(
        [{"role": "user", "content": "task"}],
        4096,
        [{
            "type": "function",
            "function": {
                "name": "submit_artifacts",
                "parameters": {"type": "object", "properties": {}},
            },
        }],
    )

    assert captured["tool_choice"] == "auto"


def test_direct_run_cell_submits_with_one_transport_tool_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = load_run_campaign()
    cell = {
        "cell_id": "v4-001-G0-r0",
        "task_id": "v4-001",
        "mode": "G0",
        "process": "direct_one_shot",
        "per_turn_max_tokens": 4096,
    }
    args = run_args(tmp_path / "run", tmp_path / "release")

    def prepare_runtime(
        _cell: dict, _release: Path, runtime: Path, *, timeout_s: int
    ) -> None:
        assert timeout_s == args.setup_timeout_s
        (runtime / "public" / "submission").mkdir(parents=True)
        (runtime / "evaluator").mkdir(parents=True)
        (runtime / "direct_prompt.txt").write_text("Create model.va.\n")
        (runtime / "evaluator" / "score_policy.json").write_text(
            json.dumps({"candidate_artifacts": ["model.va"]})
        )
        (runtime / "MODEL_ACCESS_POLICY.json").write_text(
            json.dumps({
                "mode": "G0",
                "available_skills": {},
                "provider_tools": [],
            })
        )

    monkeypatch.setattr(runner, "export_runtime", prepare_runtime)

    class SubmitClient:
        def complete(self, messages, _max_tokens, tools, **_kwargs):
            assert messages[0] == {
                "role": "system",
                "content": runner.ONESHOT_TRANSPORT_INSTRUCTION,
            }
            assert [tool["function"]["name"] for tool in tools] == [
                "submit_artifacts"
            ]
            return {
                "choices": [{
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [{
                            "id": "submit-call",
                            "type": "function",
                            "function": {
                                "name": "submit_artifacts",
                                "arguments": json.dumps({
                                    "artifacts": {
                                        "model.va": "module model; endmodule\n"
                                    }
                                }),
                            },
                        }],
                    },
                }],
                "usage": {"completion_tokens": 16},
            }

    result = runner.run_cell(cell, args, SubmitClient())

    assert result["status"] == "submitted"
    assert result["submission_protocol_compliant"] is True
    assert result["extraction_protocol"] == "submit_artifacts_tool-v1"
    assert result["submission_transport"] == "runner_managed"


def test_direct_transport_failures_are_bounded_and_not_scored_as_model_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = load_run_campaign()
    cell = {
        "cell_id": "v4-001-G0-r0",
        "task_id": "v4-001",
        "mode": "G0",
        "process": "direct_one_shot",
        "per_turn_max_tokens": 4096,
    }
    args = run_args(tmp_path / "run", tmp_path / "release")

    def prepare_runtime(
        _cell: dict, _release: Path, runtime: Path, *, timeout_s: int
    ) -> None:
        (runtime / "public" / "submission").mkdir(parents=True)
        (runtime / "evaluator").mkdir(parents=True)
        (runtime / "direct_prompt.txt").write_text("Create model.va.\n")
        (runtime / "evaluator" / "score_policy.json").write_text(
            json.dumps({"candidate_artifacts": ["model.va"]})
        )
        (runtime / "MODEL_ACCESS_POLICY.json").write_text(
            json.dumps({"mode": "G0", "available_skills": {}, "provider_tools": []})
        )

    monkeypatch.setattr(runner, "export_runtime", prepare_runtime)

    class MalformedTransportClient:
        calls = 0

        def complete(self, _messages, _max_tokens, _tools, **_kwargs):
            self.calls += 1
            if self.calls > 2:
                raise AssertionError("submission transport retries were not bounded")
            return {
                "choices": [{
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [{
                            "id": f"submit-call-{self.calls}",
                            "type": "function",
                            "function": {
                                "name": "submit_artifacts",
                                "arguments": '{"artifacts":',
                            },
                        }],
                    },
                }],
                "usage": {"completion_tokens": 8},
            }

    client = MalformedTransportClient()
    result = runner.run_cell(cell, args, client)

    assert client.calls == 2
    assert result["status"] == "provider_transport_failure"
    assert result["termination_reason"] == "malformed_submit_artifacts_transport"
    assert result["submission_protocol_compliant"] is False
    assert result["experiment_result"]["outcome"] == "infrastructure_failure"
    assert result["experiment_result"]["score_eligible"] is False
    assert result["incidents"] == [{
        "category": "malformed_submit_artifacts_transport",
        "component": "provider",
        "phase": "submission_transport",
        "responsibility": "infrastructure",
        "retryable": True,
    }]
    tool_events = [
        event for event in result["events"] if event.get("name") == "submit_artifacts"
    ]
    assert len(tool_events) == 2
    assert all(event["argument_protocol_compliant"] is False for event in tool_events)
    assert all(event["transport_error"] is True for event in tool_events)


def test_direct_transport_retry_can_submit_without_checker_feedback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = load_run_campaign()
    cell = {
        "cell_id": "v4-001-G0-r0",
        "task_id": "v4-001",
        "mode": "G0",
        "process": "direct_one_shot",
        "per_turn_max_tokens": 4096,
    }
    args = run_args(tmp_path / "run", tmp_path / "release")

    def prepare_runtime(
        _cell: dict, _release: Path, runtime: Path, *, timeout_s: int
    ) -> None:
        (runtime / "public" / "submission").mkdir(parents=True)
        (runtime / "evaluator").mkdir(parents=True)
        (runtime / "direct_prompt.txt").write_text("Create model.va.\n")
        (runtime / "evaluator" / "score_policy.json").write_text(
            json.dumps({"candidate_artifacts": ["model.va"]})
        )
        (runtime / "MODEL_ACCESS_POLICY.json").write_text(
            json.dumps({"mode": "G0", "available_skills": {}, "provider_tools": []})
        )

    monkeypatch.setattr(runner, "export_runtime", prepare_runtime)

    class RetryClient:
        calls = 0

        def complete(self, messages, _max_tokens, _tools, **_kwargs):
            self.calls += 1
            arguments = (
                '{"artifacts":'
                if self.calls == 1
                else json.dumps({
                    "artifacts": {"model.va": "module model; endmodule\n"}
                })
            )
            if self.calls == 2:
                tool_feedback = json.loads(messages[-1]["content"])
                assert tool_feedback["status"] == "tool_error"
                assert tool_feedback["tool"] == "submit_artifacts"
                assert "checker" not in messages[-1]["content"].lower()
            return {
                "choices": [{
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [{
                            "id": f"submit-call-{self.calls}",
                            "type": "function",
                            "function": {
                                "name": "submit_artifacts",
                                "arguments": arguments,
                            },
                        }],
                    },
                }],
                "usage": {"completion_tokens": 8},
            }

    client = RetryClient()
    result = runner.run_cell(cell, args, client)

    assert client.calls == 2
    assert result["status"] == "submitted"
    assert result["transport_retry_count"] == 1
    assert result["submission_transport"] == "runner_managed"
    assert (
        args.output / cell["cell_id"] / "public" / "submission" / "model.va"
    ).read_text() == "module model; endmodule\n"


def test_direct_resume_finalizes_a_pending_submit_artifacts_call(
    tmp_path: Path,
) -> None:
    runner = load_run_campaign()
    cell = {
        "cell_id": "v4-001-G0-r0",
        "task_id": "v4-001",
        "mode": "G0",
        "process": "direct_one_shot",
        "per_turn_max_tokens": 4096,
    }
    args = run_args(tmp_path / "run", tmp_path / "release")
    args.resume = True
    runtime = args.output / cell["cell_id"]
    (runtime / "public" / "submission").mkdir(parents=True)
    (runtime / "evaluator").mkdir(parents=True)
    (runtime / "evidence").mkdir(parents=True)
    (runtime / "direct_prompt.txt").write_text("Create model.va.\n")
    (runtime / "evaluator" / "score_policy.json").write_text(
        json.dumps({"candidate_artifacts": ["model.va"]})
    )
    (runtime / "MODEL_ACCESS_POLICY.json").write_text(
        json.dumps({"mode": "G0", "available_skills": {}, "provider_tools": []})
    )
    (runtime / "evidence" / "conversation_checkpoint.json").write_text(
        json.dumps({
            "cell_id": cell["cell_id"],
            "started_at": "2026-07-24T00:00:00+00:00",
            "messages": [
                {"role": "system", "content": runner.ONESHOT_TRANSPORT_INSTRUCTION},
                {"role": "user", "content": "Create model.va."},
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{
                        "id": "submit-call",
                        "type": "function",
                        "function": {
                            "name": "submit_artifacts",
                            "arguments": json.dumps({
                                "artifacts": {
                                    "model.va": "module model; endmodule\n"
                                }
                            }),
                        },
                    }],
                },
            ],
            "output_tokens": 16,
            "events": [],
            "finalized": False,
            "agent_elapsed_s": 1.0,
        })
    )

    result = runner.run_cell(cell, args, object())

    assert result["status"] == "submitted"
    assert result["recovered_from_checkpoint"] is True
    assert result["termination_reason"] == "completed"


def test_direct_resume_keeps_transport_retry_limit_episode_scoped(
    tmp_path: Path,
) -> None:
    runner = load_run_campaign()
    cell = {
        "cell_id": "v4-001-G0-r0",
        "task_id": "v4-001",
        "mode": "G0",
        "process": "direct_one_shot",
        "per_turn_max_tokens": 4096,
    }
    args = run_args(tmp_path / "run", tmp_path / "release")
    args.resume = True
    runtime = args.output / cell["cell_id"]
    (runtime / "public" / "submission").mkdir(parents=True)
    (runtime / "evaluator").mkdir(parents=True)
    (runtime / "evidence").mkdir(parents=True)
    (runtime / "direct_prompt.txt").write_text("Create model.va.\n")
    (runtime / "evaluator" / "score_policy.json").write_text(
        json.dumps({"candidate_artifacts": ["model.va"]})
    )
    (runtime / "MODEL_ACCESS_POLICY.json").write_text(
        json.dumps({"mode": "G0", "available_skills": {}, "provider_tools": []})
    )
    (runtime / "evidence" / "conversation_checkpoint.json").write_text(
        json.dumps({
            "cell_id": cell["cell_id"],
            "started_at": "2026-07-24T00:00:00+00:00",
            "messages": [
                {"role": "system", "content": runner.ONESHOT_TRANSPORT_INSTRUCTION},
                {"role": "user", "content": "Create model.va."},
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{
                        "id": "submit-call",
                        "type": "function",
                        "function": {
                            "name": "submit_artifacts",
                            "arguments": '{"artifacts":{"model.va":"broken"',
                        },
                    }],
                },
            ],
            "output_tokens": 16,
            "events": [{
                "type": "tool",
                "name": "submit_artifacts",
                "transport_error": True,
            }],
            "finalized": False,
            "agent_elapsed_s": 1.0,
        })
    )

    result = runner.run_cell(cell, args, object())

    assert result["status"] == "provider_transport_failure"
    assert result["transport_failure_count"] == 2
    assert result["transport_failure_count_this_run"] == 1
    assert result["recovered_from_checkpoint"] is True


def test_direct_run_rejects_mixed_submit_artifacts_tool_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = load_run_campaign()
    cell = {
        "cell_id": "v4-001-G0-r0",
        "task_id": "v4-001",
        "mode": "G0",
        "process": "direct_one_shot",
        "per_turn_max_tokens": 4096,
    }
    args = run_args(tmp_path / "run", tmp_path / "release")

    def prepare_runtime(
        _cell: dict, _release: Path, runtime: Path, *, timeout_s: int
    ) -> None:
        (runtime / "public" / "submission").mkdir(parents=True)
        (runtime / "evaluator").mkdir(parents=True)
        (runtime / "direct_prompt.txt").write_text("Create model.va.\n")
        (runtime / "evaluator" / "score_policy.json").write_text(
            json.dumps({"candidate_artifacts": ["model.va"]})
        )
        (runtime / "MODEL_ACCESS_POLICY.json").write_text(
            json.dumps({"mode": "G0", "available_skills": {}, "provider_tools": []})
        )

    monkeypatch.setattr(runner, "export_runtime", prepare_runtime)

    class MixedClient:
        def complete(self, _messages, _max_tokens, _tools, **_kwargs):
            return {
                "choices": [{
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "read-call",
                                "type": "function",
                                "function": {
                                    "name": "read_skill",
                                    "arguments": "{}",
                                },
                            },
                            {
                                "id": "submit-call",
                                "type": "function",
                                "function": {
                                    "name": "submit_artifacts",
                                    "arguments": json.dumps({
                                        "artifacts": {
                                            "model.va": "module model; endmodule\n"
                                        }
                                    }),
                                },
                            },
                        ],
                    },
                }],
                "usage": {"completion_tokens": 16},
            }

    result = runner.run_cell(cell, args, MixedClient())

    assert result["status"] == "invalid_submission"
    assert result["termination_reason"] == "invalid_submit_artifacts_call"
    assert result["parse_diagnostics"] == ["mixed_submit_artifacts_tool_bundle"]


def test_usage_fallback_counts_reasoning_and_tool_arguments() -> None:
    runner = load_run_campaign()

    usage = runner.provider_output_usage(
        None,
        "visible",
        reasoning_text="hidden reasoning",
        tool_text='{"content":"module x; endmodule"}',
    )

    assert usage["source"] == "reference_estimate"
    assert usage["reasoning_tokens"] > 0
    assert usage["visible_tokens"] > runner.reference_tokens("visible")
    assert usage["output_tokens"] == usage["reasoning_tokens"] + usage["visible_tokens"]


def test_campaign_validation_rejects_output_path_escape() -> None:
    runner = load_run_campaign()
    cell = campaign_cell("G0")
    cell["cell_id"] = "../../outside"

    try:
        runner.validate_campaign_cells([cell], RELEASE)
    except ValueError as exc:
        assert "invalid campaign cell_id" in str(exc)
    else:
        raise AssertionError("campaign validation accepted a path-escaping cell id")


def test_direct_parser_rejects_prose_and_wrong_order(tmp_path: Path) -> None:
    runner = load_run_campaign()
    runtime = tmp_path / "runtime"
    write_runtime_policy(runtime, ["first.va", "second.va"])
    (runtime / "public" / "submission").mkdir(parents=True)

    wrong_order = (
        '<<<VABENCH_ARTIFACT path="second.va">>>\nsecond\n<<<END_VABENCH_ARTIFACT>>>\n'
        '<<<VABENCH_ARTIFACT path="first.va">>>\nfirst\n<<<END_VABENCH_ARTIFACT>>>'
    )
    mapping, _protocol, diagnostics = runner.parse_direct_artifacts_detailed(
        wrong_order, runtime
    )
    assert mapping is None
    assert "artifact_blocks_not_in_canonical_order" in diagnostics

    prose = (
        "Here are the files:\n"
        '<<<VABENCH_ARTIFACT path="first.va">>>\nfirst\n<<<END_VABENCH_ARTIFACT>>>\n'
        '<<<VABENCH_ARTIFACT path="second.va">>>\nsecond\n<<<END_VABENCH_ARTIFACT>>>'
    )
    mapping, _protocol, diagnostics = runner.parse_direct_artifacts_detailed(prose, runtime)
    assert mapping is None
    assert "non_whitespace_outside_artifact_blocks" in diagnostics


def test_submission_gate_rejects_undeclared_files_and_symlinks(tmp_path: Path) -> None:
    runner = load_run_campaign()
    runtime = tmp_path / "runtime"
    write_runtime_policy(runtime, ["model.va"])
    submission = runtime / "public" / "submission"
    submission.mkdir(parents=True)
    (submission / "model.va").write_text("module model; endmodule", encoding="utf-8")
    (submission / "extra.va").write_text("extra", encoding="utf-8")
    (submission / "link.va").symlink_to(submission / "model.va")

    gate = runner.submission_artifact_gate(runtime)

    assert gate["passed"] is False
    assert "undeclared_artifact_path:extra.va" in gate["diagnostics"]
    assert "symlink_not_allowed:link.va" in gate["diagnostics"]


def test_feedback_compaction_keeps_actionable_property_diagnostics() -> None:
    runner = load_run_campaign()
    stdout = "\n".join(
        [
            "FEEDBACK_EVAS_ENGINE evas_version=0.8.2 evas_engine=evas2",
            "FEEDBACK_BEHAVIOR_FAIL",
            "solver counters: accepted=812 rejected=4",
            (
                "task=v4_312_interleaved_adc_skew_monitor | "
                "P_SKEW_METRIC:mismatch_count=2 expected=0.04 "
                "observed=0.11 time=8.2e-08 gap=0.07"
            ),
        ]
    )

    compact = runner.compact_feedback_result(
        {"returncode": 1, "stdout": stdout, "stderr": "", "elapsed_s": 0.4}
    )

    assert compact["diagnostics"][0].startswith("task=v4_312")
    assert "P_SKEW_METRIC" in compact["diagnostics"][0]
    assert compact["markers"] == [
        "FEEDBACK_EVAS_ENGINE evas_version=0.8.2 evas_engine=evas2",
        "FEEDBACK_BEHAVIOR_FAIL",
    ]
    assert all("solver counters" not in line for line in compact["diagnostics"])


def test_feedback_compaction_keeps_reference_failure_detail() -> None:
    runner = load_run_campaign()
    stdout = "\n".join(
        [
            "reference: missing_vin_step_samples initial_samples=[0.0, 0.0] initial_ok=True",
            "FEEDBACK_TB_REFERENCE_FAIL",
        ]
    )

    lines = runner.compact_text_lines(stdout)

    assert lines == [
        "reference: missing_vin_step_samples initial_samples=[0.0, 0.0] initial_ok=True",
        "FEEDBACK_TB_REFERENCE_FAIL",
    ]


def test_feedback_compaction_keeps_invalid_run_root_cause() -> None:
    runner = load_run_campaign()
    stdout = "\n".join(
        [
            "reference: evas_engine=evas2",
            "reference: simulation failed",
            "FEEDBACK_TB_INVALID_RUN",
        ]
    )
    stderr = "Error: tb_candidate.scs:17: unknown instance parameter 'period'"

    compact = runner.compact_feedback_result(
        {"returncode": 1, "stdout": stdout, "stderr": stderr, "elapsed_s": 0.2}
    )

    assert stderr in compact["diagnostics"]
    assert compact["diagnostics"].index(stderr) < compact["diagnostics"].index(
        "FEEDBACK_TB_INVALID_RUN"
    )


def test_feedback_compaction_keeps_rust_lowering_rejection() -> None:
    runner = load_run_campaign()
    stdout = "\n".join(
        [
            "required_trace_missing_node_count = 0",
            "Traceback (most recent call last):",
            (
                "RuntimeError: evas-rust full-model path was required but no supported "
                "whole-segment Rust runtime matched this design. RustSimProgram rejection: "
                "model:0:debounce_latch_Model:event_due_not_lowered"
            ),
            "FEEDBACK_EVAS_FAIL",
        ]
    )

    lines = runner.compact_text_lines(stdout)

    assert any(line.startswith("RuntimeError:") for line in lines)
    assert any("event_due_not_lowered" in line for line in lines)
    assert all("missing_node_count = 0" not in line for line in lines)
    assert lines.index(next(line for line in lines if line.startswith("RuntimeError:"))) < lines.index(
        "FEEDBACK_EVAS_FAIL"
    )


def test_direct_run_cell_submits_only_an_exact_artifact_response(
    tmp_path: Path, r45_release: Path
) -> None:
    runner = load_run_campaign()
    cell = campaign_cell("G0", r45_release)
    task = r45_release / "tasks" / "001-bang-bang-phase-detector"
    body = (task / "evaluator" / "solution" / "bbpd_ref.va").read_text(encoding="utf-8")
    response = (
        '<<<VABENCH_ARTIFACT path="bbpd_ref.va">>>\n'
        f"{body}\n"
        "<<<END_VABENCH_ARTIFACT>>>"
    )

    result = runner.run_cell(
        cell,
        run_args(tmp_path / "run", r45_release),
        FakeClient({"role": "assistant", "content": response}),
    )

    assert result["status"] == "submitted"
    assert result["submission_protocol_compliant"] is True
    assert result["artifact_gate"]["passed"] is True
    saved = tmp_path / "run" / cell["cell_id"] / "public" / "submission" / "bbpd_ref.va"
    assert saved.read_text(encoding="utf-8") == body


def test_direct_run_cell_records_model_output_limit_without_budget_status(
    tmp_path: Path, r45_release: Path
) -> None:
    runner = load_run_campaign()
    cell = campaign_cell("G0", r45_release)
    task = r45_release / "tasks" / "001-bang-bang-phase-detector"
    body = (task / "evaluator" / "solution" / "bbpd_ref.va").read_text(encoding="utf-8")
    response = (
        '<<<VABENCH_ARTIFACT path="bbpd_ref.va">>>\n'
        f"{body}\n"
        "<<<END_VABENCH_ARTIFACT>>>"
    )

    result = runner.run_cell(
        cell,
        run_args(tmp_path / "run", r45_release),
        FakeClient({"role": "assistant", "content": response}, finish_reason="length"),
    )

    assert result["status"] == "submitted"
    assert result["termination_reason"] == "model_output_limit"
    assert result["output_token_budget"] is None
    assert result["per_turn_max_tokens"] == 4096


def test_g1_direct_run_cell_can_read_a_skill_before_submitting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = load_run_campaign()
    cell = {
        "cell_id": "v4-001-G1-r0",
        "task_id": "v4-001",
        "mode": "G1",
        "per_turn_max_tokens": 4096,
    }
    args = run_args(tmp_path / "run", tmp_path / "release")

    def prepare_runtime(
        _cell: dict, _release: Path, runtime: Path, *, timeout_s: int
    ) -> None:
        assert timeout_s == args.setup_timeout_s
        (runtime / "public" / "submission").mkdir(parents=True)
        (runtime / "evaluator").mkdir(parents=True)
        (runtime / "direct_prompt.txt").write_text(
            "Create dut.va. The veriloga skill is available by lookup.\n",
            encoding="utf-8",
        )
        (runtime / "evaluator" / "score_policy.json").write_text(
            json.dumps({"candidate_artifacts": ["dut.va"]}), encoding="utf-8"
        )
        skill = runtime / "public" / "skills" / "veriloga"
        skill.mkdir(parents=True)
        skill_file = skill / "SKILL.md"
        skill_file.write_text(
            "---\nname: veriloga\n---\n# Verilog-A language\n",
            encoding="utf-8",
        )
        file_bytes = skill_file.read_bytes()
        (runtime / "public" / "skills" / "SNAPSHOT_MANIFEST.json").write_text(
            json.dumps({
                "schema_version": "v4-runtime-skill-manifest-v1",
                "skills": {
                    "veriloga": {
                        "skill_file": "public/skills/veriloga/SKILL.md",
                        "tree_sha256": runner.skill_tree_sha(skill),
                        "files": [{
                            "path": "SKILL.md",
                            "bytes": len(file_bytes),
                            "sha256": hashlib.sha256(file_bytes).hexdigest(),
                        }],
                    }
                },
            }),
            encoding="utf-8",
        )
        (runtime / "MODEL_ACCESS_POLICY.json").write_text(
            json.dumps({
                "mode": "G1",
                "available_skills": {
                    "veriloga": {
                        "skill_file": "public/skills/veriloga/SKILL.md",
                        "tree_sha256": runner.skill_tree_sha(skill),
                    }
                },
                "provider_tools": ["list_skills", "read_skill"],
            }),
            encoding="utf-8",
        )

    class SkillThenArtifactClient:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, messages, _max_tokens, tools, **_kwargs):
            self.calls += 1
            names = [tool["function"]["name"] for tool in tools]
            assert names == ["list_skills", "read_skill", "submit_artifacts"]
            if self.calls == 1:
                return {
                    "id": "skill-read",
                    "model": "test-model",
                    "choices": [{
                        "finish_reason": "tool_calls",
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [{
                                "id": "read-veriloga",
                                "type": "function",
                                "function": {
                                    "name": "read_skill",
                                    "arguments": json.dumps({
                                        "skill": "veriloga",
                                        "path": "SKILL.md",
                                    }),
                                },
                            }],
                        },
                    }],
                    "usage": {"completion_tokens": 8},
                }
            assert messages[-1]["role"] == "tool"
            assert "# Verilog-A language" in messages[-1]["content"]
            return {
                "id": "artifact",
                "model": "test-model",
                "choices": [{
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": (
                            '<<<VABENCH_ARTIFACT path="dut.va">>>\n'
                            "module dut; endmodule\n"
                            "<<<END_VABENCH_ARTIFACT>>>"
                        ),
                    },
                }],
                "usage": {"completion_tokens": 16},
            }

    monkeypatch.setattr(runner, "export_runtime", prepare_runtime)
    client = SkillThenArtifactClient()
    result = runner.run_cell(cell, args, client)

    assert client.calls == 2
    assert result["status"] == "submitted"
    assert result["submission_protocol_compliant"] is True
    assert result["skill_lookup_events"] == [
        {
            "cached": False,
            "path": "SKILL.md",
            "schema_version": "v4-skill-lookup-event-v1",
            "sha256": hashlib.sha256(
                "---\nname: veriloga\n---\n# Verilog-A language\n".encode("utf-8")
            ).hexdigest(),
            "skill": "veriloga",
            "timestamp": result["skill_lookup_events"][0]["timestamp"],
        }
    ]
    assert any(
        event.get("name") == "read_skill"
        and event.get("skill") == "veriloga"
        and event.get("path") == "SKILL.md"
        for event in result["events"]
    )


def test_provider_context_window_is_a_cell_status_not_runner_error(
    tmp_path: Path, r45_release: Path
) -> None:
    runner = load_run_campaign()
    cell = campaign_cell("G2", r45_release)

    class ContextWindowClient:
        def complete(self, *_args, **_kwargs):
            raise runner.ProviderContextWindowExceeded("context length exceeded")

    result = runner.run_cell(
        cell, run_args(tmp_path / "run", r45_release), ContextWindowClient()
    )

    assert result["status"] == "context_window_exceeded"
    assert result["termination_reason"] == "provider_context_window_exceeded"
    assert "context length exceeded" in result["provider_error"]


def test_provider_request_timeout_is_not_mislabeled_as_agent_walltime(
    tmp_path: Path,
) -> None:
    runner = load_run_campaign()
    cell = campaign_cell("G2", R49_RELEASE)

    class RequestTimeoutClient:
        def complete(self, *_args, **_kwargs):
            raise runner.ProviderRequestTimeout("provider request exceeded 30s")

        @staticmethod
        def _redact(value: str) -> str:
            return value

    result = runner.run_cell_preserving_failure(
        cell,
        run_args(tmp_path / "run", R49_RELEASE),
        RequestTimeoutClient(),
    )

    assert result["status"] == "provider_timeout"
    assert result["termination_reason"] == "provider_request_timeout"
    assert result["error_type"] == "ProviderRequestTimeout"
    assert result["incidents"] == [
        {
            "category": "provider_request_timeout",
            "component": "provider",
            "error_type": "ProviderRequestTimeout",
            "phase": "model",
            "responsibility": "infrastructure",
            "retryable": True,
        }
    ]
    assert result["experiment_result"]["model_execution"]["status"] == "provider_failure"
    assert result.get("termination_reason") != "agent_timeout"


def test_runtime_export_failure_is_not_mislabeled_as_evas_failure() -> None:
    runner = load_run_campaign()
    classification = runner.classify_execution_exception(
        runner.RuntimeExportError("runtime exporter failed under /tmp/vaEvas")
    )

    assert classification["status"] == "infrastructure_failure"
    assert classification["termination_reason"] == "runtime_export_failure"
    assert classification["incident"]["component"] == "runner"
    assert classification["incident"]["phase"] == "setup"


def test_agentic_run_cell_rejects_an_undeclared_file_at_finalize(
    tmp_path: Path, r45_release: Path
) -> None:
    runner = load_run_campaign()
    cell = campaign_cell("G2", r45_release)
    message = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "write-required",
                "type": "function",
                "function": {
                    "name": "write_file",
                    "arguments": json.dumps(
                        {"path": "bbpd_ref.va", "content": "module bbpd_ref; endmodule"}
                    ),
                },
            },
            {
                "id": "write-extra",
                "type": "function",
                "function": {
                    "name": "write_file",
                    "arguments": json.dumps({"path": "extra.va", "content": "extra"}),
                },
            },
            {
                "id": "finalize",
                "type": "function",
                "function": {"name": "finalize", "arguments": "{}"},
            },
        ],
    }

    result = runner.run_cell(
        cell,
        run_args(tmp_path / "run", r45_release),
        FakeClient(message),
    )

    assert result["status"] == "invalid_submission"
    assert result["submission_protocol_compliant"] is False
    assert "undeclared_artifact_path:extra.va" in result["artifact_gate"]["diagnostics"]


def test_agentic_run_cell_uses_mini_swe_bash_scaffold_by_default_path(
    tmp_path: Path, r45_release: Path
) -> None:
    runner = load_run_campaign()
    cell = campaign_cell("G2", r45_release)
    args = run_args(tmp_path / "run", r45_release)
    args.agent_scaffold = "mini-swe"
    args.mini_swe_sandbox = "none"
    args.evas_command = fake_evas_command(tmp_path)
    client = MiniSweFakeClient(
        [
            "printf 'module bbpd_ref; endmodule\\n' > public/submission/bbpd_ref.va",
            "vabench-submit",
        ]
    )

    result = runner.run_cell(cell, args, client)

    assert result["status"] == "submitted"
    assert result["agent_scaffold"]["scaffold"] == (
        "mini-swe-agent-2.4.5-vabench-docker-evas-v3"
    )
    assert result["agent_scaffold"]["evaluator_mounted"] is False
    assert result["output_token_budget"] is None
    assert result["experiment_result"]["final_submission"]["status"] == "available"


def test_agent_no_evas_cell_selects_paired_image_and_disables_evas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = load_run_campaign()
    wrapper = load_run_campaign_wrapper()
    base = load_build_campaign().build_campaign(
        R52_RELEASE,
        family_ids=["001"],
        model_provider="test",
        model="test-model",
        per_turn_max_tokens=4096,
        repetitions=1,
    )
    cell = next(
        cell
        for cell in wrapper.build_executable_feedback_control(base)["cells"]
        if cell["task_id"] == "v4-001"
        and cell["experimental_arm"] == "Agent-No-EVAS"
    )
    args = run_args(tmp_path / "run", R52_RELEASE)
    args.agent_scaffold = "mini-swe"
    args.mini_swe_sandbox = "none"
    args.mini_swe_image = "with-evas"
    args.mini_swe_no_evas_image = "without-evas"
    captured: dict = {}

    def stop_after_capture(**kwargs):
        captured.update(kwargs)
        raise RuntimeError("captured")

    monkeypatch.setattr(runner, "run_mini_swe_episode", stop_after_capture)

    with pytest.raises(RuntimeError, match="captured"):
        runner.run_cell(cell, args, FakeClient({"role": "assistant", "content": ""}))

    assert captured["executable_feedback"] is False
    assert captured["docker_image"] == "without-evas"


def test_public_agent_image_identity_is_checked_per_experimental_arm() -> None:
    runner = load_run_campaign()
    summary = runner.summarize_public_agent_images(
        [
            {
                "cell": {"experimental_arm": "Agent-No-EVAS"},
                "agent_scaffold": {"docker_image_id": "sha256:no-evas"},
            },
            {
                "cell": {"experimental_arm": "Agentic"},
                "agent_scaffold": {"docker_image_id": "sha256:agentic"},
            },
        ]
    )

    assert summary["identity_consistent"] is True
    assert summary["observed_image_ids_by_arm"] == {
        "Agent-No-EVAS": ["sha256:no-evas"],
        "Agentic": ["sha256:agentic"],
    }


def test_mini_swe_r45_direct_evas_then_submit_keeps_scratch_outside_submission(
    tmp_path: Path, r45_release: Path
) -> None:
    runner = load_run_campaign()
    cell = campaign_cell("G2", r45_release)
    args = run_args(tmp_path / "run", r45_release)
    args.agent_scaffold = "mini-swe"
    args.mini_swe_sandbox = "none"
    args.evas_command = fake_evas_command(tmp_path)
    client = MiniSweFakeClient(
        [
            "printf 'module bbpd_ref; endmodule\\n' > public/submission/bbpd_ref.va",
            (
                "evas simulate public/task/visible_test.scs "
                "-o public/submission/evas-output --spectre-strict"
            ),
            "cat public/evas-output/invocation.json",
            "vabench-submit",
        ]
    )

    result = runner.run_cell(cell, args, client)

    submission = args.output / cell["cell_id"] / "public" / "submission"
    assert result["status"] == "submitted"
    assert result["artifact_gate"]["passed"] is True
    assert sorted(path.name for path in submission.iterdir()) == ["bbpd_ref.va"]
    assert (
        args.output
        / cell["cell_id"]
        / "public"
        / "evas-output"
        / "invocation.json"
    ).is_file()


def test_mini_swe_time_exceeded_preserves_walltime_reason_with_complete_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = load_run_campaign()
    cell = campaign_cell("G2", R49_RELEASE)
    args = run_args(tmp_path / "run", R49_RELEASE)
    args.agent_scaffold = "mini-swe"
    args.mini_swe_sandbox = "none"

    def fake_episode(**kwargs):
        assert kwargs["candidate_artifacts"] == ["bbpd_ref.va"]
        runtime = kwargs["runtime"]
        (runtime / "public" / "submission" / "bbpd_ref.va").write_text(
            "module bbpd_ref; endmodule\n", encoding="utf-8"
        )
        gate = runner.submission_artifact_gate(runtime)
        return {
            "scaffold": runner.MINI_SWE_SCAFFOLD_ID,
            "scaffold_version": "2.4.5",
            "bash_tool_schema_sha256": "bash-schema",
            "system_prompt_sha256": "system-prompt",
            "bash_contract_sha256": "bash-contract",
            "exit_status": "TimeExceeded",
            "submitted": False,
            "artifact_complete": True,
            "artifact_gate": gate,
            "artifact_sha256": gate["artifact_sha256"],
            "output_tokens": 17,
            "events": [],
            "commands": [],
            "evas_invocations": [
                {
                    "invocation_id": "fake-1",
                    "shell_command": "evas simulate public/task/visible_test.scs",
                    "shell_elapsed_s": 1.5,
                    "returncode": 1,
                    "status": "failed",
                }
            ],
            "model_calls": 1,
            "messages": [{"role": "assistant", "content": "partial answer"}],
            "agent_elapsed_s": float(AGENT_WALL_TIME_SECONDS),
            "trajectory_format": "mini-swe-agent-trajectory-v1",
            "sandbox_backend": "none",
            "network": False,
            "evaluator_mounted": False,
        }

    monkeypatch.setattr(runner, "run_mini_swe_episode", fake_episode)
    result = runner.run_cell(cell, args, FakeClient({"role": "assistant", "content": ""}))

    assert result["status"] == "workspace_ready"
    assert result["termination_reason"] == "agent_timeout"
    assert result["submission_mode"] == "workspace_at_deadline"
    assert result["submission_protocol_compliant"] is False
    assert result["artifact_gate"]["passed"] is True
    assert result["experiment_result"]["model_execution"]["status"] == "agent_timeout"
    assert result["evas_usage"]["calls_executed"] == 1
    assert result["evas_usage"]["calls_failed"] == 1
    assert result["evas_usage"]["last_status"] == "failed"
    assert result["incidents"][0]["category"] == "evas_command_failure"
    assert "public_feedback" not in result


def test_complete_workspace_can_pass_even_when_agent_reaches_walltime() -> None:
    runner = load_run_campaign()

    outcome = runner.RESULT_PROTOCOL.terminal_outcome(
        "agent_timeout",
        {"status": "available"},
        {"status": "passed"},
    )

    assert outcome == "passed"


def test_resume_reuses_workspace_ready_without_model_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = load_run_campaign()
    cell = campaign_cell("G2", R49_RELEASE)
    args = run_args(tmp_path / "run", R49_RELEASE)
    args.resume = True
    runtime = args.output / cell["cell_id"]
    runner.export_runtime(cell, R49_RELEASE, runtime, timeout_s=30)
    candidate = runtime / "public" / "submission" / "bbpd_ref.va"
    candidate.write_text("module bbpd_ref; endmodule\n", encoding="utf-8")
    gate = runner.submission_artifact_gate(runtime)
    assert gate["passed"] is True
    previous = {
        "cell": cell,
        "status": "workspace_ready",
        "artifact_gate": gate,
        "artifact_sha256": gate["artifact_sha256"],
        "experiment_result": {"outcome": "passed"},
    }
    runner.write_json(runtime / "evidence" / "campaign_result.json", previous)

    def unexpected_episode(**_kwargs):
        raise AssertionError("resume must not call the model for workspace_ready")

    monkeypatch.setattr(runner, "run_mini_swe_episode", unexpected_episode)
    result = runner.run_cell(cell, args, None)

    assert result == previous
    assert candidate.read_text(encoding="utf-8") == "module bbpd_ref; endmodule\n"


def test_resource_exhaustion_is_not_scored_as_model_zero() -> None:
    runner = load_run_campaign()

    outcome = runner.RESULT_PROTOCOL.terminal_outcome(
        "agent_resource_exhausted",
        {"status": "available"},
        {"status": "passed"},
    )

    assert outcome == "agent_resource_exhausted"


def test_scorer_uses_six_run_outer_watchdog_for_testbench_replay() -> None:
    scorer = load_score_campaign()

    assert scorer.trusted_replay_timeout_s(
        {"form": "testbench"}, scorer.DEFAULT_TRUSTED_REPLAY_TIMEOUT_S, 750
    ) == 750


@pytest.mark.parametrize("form", ["dut", "bugfix"])
def test_scorer_keeps_single_run_timeout_for_non_testbench_forms(form: str) -> None:
    scorer = load_score_campaign()

    assert scorer.trusted_replay_timeout_s(
        {"form": form}, scorer.DEFAULT_TRUSTED_REPLAY_TIMEOUT_S, 750
    ) == 150


def test_trusted_replay_signature_binds_evas_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scorer = load_score_campaign()
    (tmp_path / "evaluator").mkdir()
    monkeypatch.setenv("VABENCH_EVAS_PROFILE", "r53")

    signature, _ = scorer.trusted_replay_input_signature(
        result={"cell": {}, "evas_identity": {"version_output": "evas-sim 0.8.7"}},
        runtime=tmp_path,
        command="python3",
        replay_timeout_s=150,
        evas_command="/opt/evas-0.8.7",
        final_submission={"tree_sha256": "a" * 64},
    )

    assert signature["evaluator"]["evas_profile"] == "r53"


@pytest.mark.parametrize(
    "notes",
    [
        ["reference: behavior_eval_timeout>60s"],
        ["neg_001: behavior_eval_no_result"],
        ["neg_002: behavior_eval_error=MemoryError"],
    ],
)
def test_testbench_checker_watchdog_is_infrastructure_failure(notes: list[str]) -> None:
    adapter = load_trusted_replay_adapter()
    reference = SimpleNamespace(outcome="invalid_run", notes=notes)

    result = adapter.classify_testbench_result(reference, [], [])

    assert result["status"] == "infrastructure_failure"
    assert result["failure_taxonomy"]["responsibility"] == "system"
    assert result["failure_taxonomy"]["retryable"] is True


@pytest.mark.parametrize(
    ("outcome", "expected"),
    [
        ("reference_pass", True),
        ("reference_fail", False),
        ("invalid_run", False),
    ],
)
def test_testbench_mutations_run_only_after_reference_passes(
    outcome: str,
    expected: bool,
) -> None:
    adapter = load_trusted_replay_adapter()

    assert adapter.reference_requires_mutation_replay(
        SimpleNamespace(outcome=outcome)
    ) is expected
def test_trusted_replay_strict_lint_preserves_configured_command_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = load_trusted_replay_adapter()
    submission = tmp_path / "submission"
    submission.mkdir()
    source = submission / "dut.va"
    source.write_text("module bad; endmodule\n", encoding="utf-8")
    monkeypatch.setenv(
        "VABENCH_EVAS_COMMAND", "/fake/evas --runtime-mode sealed"
    )

    def fake_run(command, **_kwargs):
        assert command[:5] == [
            "/fake/evas",
            "--runtime-mode",
            "sealed",
            "lint",
            str(source),
        ]
        assert "--spectre-strict" in command
        return SimpleNamespace(returncode=1, stdout="strict lint failed", stderr="")

    monkeypatch.setattr(adapter.subprocess, "run", fake_run)

    result = adapter.strict_spectre_lint_submission(submission)

    assert result is not None
    assert result["status"] == "compile_failure"
    assert result["failure_taxonomy"]["primary_class"] == "compile"


def test_trusted_replay_strict_lint_allows_clean_submission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = load_trusted_replay_adapter()
    submission = tmp_path / "submission"
    submission.mkdir()
    (submission / "dut.va").write_text("module ok; endmodule\n", encoding="utf-8")
    monkeypatch.setenv("VABENCH_EVAS_COMMAND", "/fake/evas")
    monkeypatch.setattr(
        adapter.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0, stdout="[]", stderr=""
        ),
    )

    assert adapter.strict_spectre_lint_submission(submission) is None


def test_testbench_strict_lint_stages_supplied_dut_before_resolving_include(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = load_trusted_replay_adapter()
    submission = tmp_path / "submission"
    submission.mkdir()
    (submission / "testbench.scs").write_text(
        'ahdl_include "./dut/dut.va"\n', encoding="utf-8"
    )
    source_eval = tmp_path / "evaluator"
    trusted_solution = source_eval / "trusted_solution"
    trusted_solution.mkdir(parents=True)
    (trusted_solution / "dut.va").write_text(
        "module dut; endmodule\n", encoding="utf-8"
    )
    contract = {
        "supplied_inputs": {
            "read_only_dut_artifacts": [
                {
                    "public_input_path": "supplied_dut/dut.va",
                    "testbench_include_path": "./dut/dut.va",
                }
            ]
        }
    }
    monkeypatch.setenv("VABENCH_EVAS_COMMAND", "/fake/evas")

    def fake_run(command, **_kwargs):
        linted = Path(command[2])
        assert linted.name == "testbench.scs"
        assert linted.parent != submission
        assert (linted.parent / "dut" / "dut.va").is_file()
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")

    monkeypatch.setattr(adapter.subprocess, "run", fake_run)

    assert (
        adapter.strict_spectre_lint_testbench_submission(
            submission=submission,
            source_eval=source_eval,
            target_artifacts=["dut.va"],
            public_contract=contract,
        )
        is None
    )
    assert not (submission / "dut").exists()


def test_scorer_accepts_complete_workspace_without_explicit_submit(
    tmp_path: Path,
) -> None:
    scorer = load_score_campaign()
    runtime = tmp_path / "v4-001-G2-r0"
    submission = runtime / "public" / "submission"
    submission.mkdir(parents=True)
    (submission / "model.va").write_text("module model; endmodule\n")
    write_runtime_policy(runtime, ["model.va"])
    candidate_hash = "c" * 64
    result_path = runtime / "evidence" / "campaign_result.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            {
                "cell": {
                    "cell_id": "v4-001-G2-r0",
                    "family_id": "001",
                    "task_id": "v4-001",
                    "form": "dut",
                    "mode": "G2",
                },
                "status": "workspace_ready",
                "termination_reason": "agent_timeout",
                "submission_mode": "workspace_at_deadline",
                "submission_protocol_compliant": False,
                "output_tokens": 10,
                "events": [],
                "evas_usage": {
                    "schema_version": "v4-direct-evas-usage-v2",
                    "calls_executed": 2,
                    "calls_succeeded": 1,
                    "calls_failed": 1,
                    "calls_timed_out": 0,
                    "calls_interrupted": 0,
                    "last_status": "succeeded",
                    "unique_candidate_tree_hashes": [candidate_hash],
                    "candidate_tree_hash_call_counts": {
                        candidate_hash: 2,
                    },
                    "modified_rerun_count": 0,
                    "unchanged_repeat_count": 1,
                },
                "incidents": [
                    {
                        "category": "evas_command_failure",
                        "component": "evas",
                        "phase": "tool",
                    }
                ],
            }
        )
    )

    row = scorer.evaluate_cell(result_path, None, 30)

    assert row["judge_status"] == "not_run"
    assert row["submission_mode"] == "workspace_at_deadline"
    assert row["evas_usage"]["calls_executed"] == 2
    assert row["incidents"][0]["category"] == "evas_command_failure"

    report = scorer.summarize([row], "legacy_feedback_evas")
    assert report["incident_categories"] == {"evas_command_failure": 1}
    assert report["telemetry_by_mode"]["G2"]["direct_evas_calls_total"] == 2
    assert report["telemetry_by_mode"]["G2"][
        "direct_evas_unique_candidate_tree_hashes"
    ] == [candidate_hash]
    assert report["telemetry_by_mode"]["G2"][
        "direct_evas_candidate_tree_hash_call_counts"
    ] == {candidate_hash: 2}
    assert report["telemetry_by_mode"]["G2"][
        "direct_evas_modified_reruns_total"
    ] == 0
    assert report["telemetry_by_mode"]["G2"][
        "direct_evas_unchanged_repeats_total"
    ] == 1


def test_scorer_keeps_agent_no_evas_separate_from_agentic() -> None:
    scorer = load_score_campaign()

    def row(arm: str, evas_calls: int) -> dict:
        return {
            "form": "dut",
            "mode": "G2",
            "experimental_arm": arm,
            "submission_status": "submitted",
            "judge_status": "pass",
            "incidents": [],
            "output_tokens": 10,
            "episode_elapsed_s": 1.0,
            "telemetry": {
                "model_calls": 1,
                "tool_calls_total": 2,
                "evas_calls": evas_calls,
                "legacy_feedback_calls": 0,
                "provider_reasoning_tokens_total": 0,
                "budget_hit_model_calls": 0,
            },
            "evas_usage": {
                "calls_executed": evas_calls,
                "calls_succeeded": evas_calls,
                "calls_failed": 0,
                "calls_timed_out": 0,
                "modified_rerun_count": 0,
                "unchanged_repeat_count": 0,
            },
        }

    report = scorer.summarize(
        [row("Agent-No-EVAS", 0), row("Agentic", 2)],
        "final_spectre",
    )

    assert report["breakdown"]["arm:Agent-No-EVAS"] == {"pass": 1}
    assert report["breakdown"]["arm:Agentic"] == {"pass": 1}
    assert report["telemetry_by_arm"]["Agent-No-EVAS"][
        "direct_evas_calls_total"
    ] == 0
    assert report["telemetry_by_arm"]["Agentic"]["direct_evas_calls_total"] == 2


@pytest.mark.parametrize(
    ("judge_kind", "expected_authority"),
    [
        ("legacy_feedback_evas", "legacy_provisional_feedback_only"),
        ("final_trusted_replay", "development_only"),
        ("final_spectre", "formal"),
    ],
)
def test_scorer_labels_authority_by_judge_kind(
    judge_kind: str,
    expected_authority: str,
) -> None:
    scorer = load_score_campaign()
    row = {
        "form": "dut",
        "mode": "G0",
        "experimental_arm": None,
        "submission_status": "submitted",
        "judge_status": "passed",
        "incidents": [],
        "output_tokens": 1,
        "episode_elapsed_s": 1.0,
        "telemetry": {},
        "evas_usage": {},
    }

    report = scorer.summarize([row], judge_kind)

    assert report["score_authority"] == expected_authority


def test_mini_swe_provider_failure_keeps_partial_trajectory(
    tmp_path: Path, r45_release: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = load_run_campaign()
    cell = campaign_cell("G2", r45_release)
    args = run_args(tmp_path / "run", r45_release)
    args.agent_scaffold = "mini-swe"
    args.mini_swe_sandbox = "none"

    def failing_episode(**kwargs):
        trajectory_path = kwargs["trajectory_path"]
        trajectory_path.parent.mkdir(parents=True, exist_ok=True)
        trajectory_path.write_text(
            json.dumps(
                {
                    "messages": [
                        {"role": "user", "content": "task"},
                        {"role": "assistant", "content": "partial diagnosis"},
                    ]
                }
            ),
            encoding="utf-8",
        )
        raise runner.ProviderContextWindowExceeded("context length exceeded")

    monkeypatch.setattr(runner, "run_mini_swe_episode", failing_episode)
    result = runner.run_cell(cell, args, FakeClient({"role": "assistant", "content": ""}))

    assert result["status"] == "context_window_exceeded"
    raw = result["experiment_result"]["model_execution"]["raw_final_output"]
    assert raw["available"] is True
    assert raw["message"]["content"] == "partial diagnosis"


def test_agentic_resume_finishes_pending_checkpointed_tool_calls(
    tmp_path: Path, r45_release: Path
) -> None:
    runner = load_run_campaign()
    cell = campaign_cell("G2", r45_release)
    args = run_args(tmp_path / "run", r45_release)
    args.resume = True
    runtime = args.output / cell["cell_id"]
    runner.export_runtime(cell, r45_release, runtime, timeout_s=1800)
    prompt = (runtime / "agent_prompt.txt").read_text(encoding="utf-8")
    assistant = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "write-required",
                "type": "function",
                "function": {
                    "name": "write_file",
                    "arguments": json.dumps(
                        {"path": "bbpd_ref.va", "content": "module bbpd_ref; endmodule"}
                    ),
                },
            },
            {
                "id": "finalize",
                "type": "function",
                "function": {"name": "finalize", "arguments": "{}"},
            },
        ],
    }
    (runtime / "evidence" / "conversation_checkpoint.json").write_text(
        json.dumps(
            {
                "schema_version": "v4-calibration-conversation-checkpoint-v1",
                "cell_id": cell["cell_id"],
                "messages": [{"role": "user", "content": prompt}, assistant],
                "output_tokens": 32,
                "events": [
                    {
                        "type": "model",
                        "requested_max_tokens": 4096,
                        "provider_output_tokens": 32,
                        "finish_reason": "tool_calls",
                    }
                ],
                "finalized": False,
            }
        ),
        encoding="utf-8",
    )

    result = runner.run_cell(cell, args, UnexpectedClientCall())

    assert result["status"] == "submitted"
    assert result["artifact_gate"]["passed"] is True
    assert (runtime / "public" / "submission" / "bbpd_ref.va").is_file()


def test_agentic_resume_does_not_reset_elapsed_wall_time(
    tmp_path: Path, r45_release: Path
) -> None:
    runner = load_run_campaign()
    cell = campaign_cell("G2", r45_release)
    args = run_args(tmp_path / "run", r45_release)
    args.resume = True
    runtime = args.output / cell["cell_id"]
    runner.export_runtime(cell, r45_release, runtime, timeout_s=1800)
    prompt = (runtime / "agent_prompt.txt").read_text(encoding="utf-8")
    (runtime / "public" / "submission" / "bbpd_ref.va").write_text(
        "module bbpd_ref; endmodule\n",
        encoding="utf-8",
    )
    (runtime / "evidence" / "conversation_checkpoint.json").write_text(
        json.dumps(
            {
                "schema_version": "v4-calibration-conversation-checkpoint-v1",
                "cell_id": cell["cell_id"],
                "messages": [{"role": "user", "content": prompt}],
                "output_tokens": 0,
                "events": [],
                "finalized": False,
                "termination_policy": "wall_time",
                "agent_timeout_s": AGENT_WALL_TIME_SECONDS,
                "agent_elapsed_s": float(AGENT_WALL_TIME_SECONDS),
            }
        ),
        encoding="utf-8",
    )

    result = runner.run_cell(cell, args, UnexpectedClientCall())

    assert result["status"] == "submitted"
    assert result["termination_reason"] == "agent_timeout"
    assert result["agent_elapsed_s"] >= float(AGENT_WALL_TIME_SECONDS)
    assert result["artifact_gate"]["passed"] is True


def test_campaign_wrapper_dry_run_exports_agentic_cells(
    tmp_path: Path, r45_release: Path
) -> None:
    output = tmp_path / "campaign"
    completed = subprocess.run(
        [
            sys.executable,
            str(RUN_CAMPAIGN_WRAPPER),
            "--release",
            str(r45_release),
            "--sample-families",
            "1",
            "--seed",
            "20260715",
            "--mode",
            "G2",
            "--output-root",
            str(output),
            "--model",
            "deepseek-v4-flash",
            "--dry-run",
            "--workers",
            "1",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    campaign = json.loads((output / "campaign.json").read_text(encoding="utf-8"))
    assert campaign["cell_count"] == 3
    assert {cell["mode"] for cell in campaign["cells"]} == {"G2"}
    assert {cell["process"] for cell in campaign["cells"]} == {"agentic"}
    assert campaign["execution_config"]["agent_scaffold"] == "mini-swe"
    assert campaign["execution_config"]["token_accounting"] == "telemetry_only"
    summary = json.loads((output / "run" / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["statuses"] == {"prepared": 3}


def test_detached_campaign_launcher_survives_closed_caller_stdin(tmp_path: Path) -> None:
    assert RUN_CAMPAIGN_DETACHED.is_file()
    output = tmp_path / "detached-campaign"
    log = tmp_path / "detached-campaign.log"
    pid_file = tmp_path / "detached-campaign.pid"
    env = dict(os.environ)
    env["VABENCH_PYTHON"] = sys.executable
    completed = subprocess.run(
        [
            str(RUN_CAMPAIGN_DETACHED),
            "--log",
            str(log),
            "--pid-file",
            str(pid_file),
            "--",
            "--release",
            str(R49_RELEASE),
            "--task-id",
            "v4-012",
            "--mode",
            "G2",
            "--output-root",
            str(output),
            "--model",
            "deepseek-v4-flash",
            "--dry-run",
            "--workers",
            "2",
        ],
        cwd=ROOT,
        env=env,
        stdin=subprocess.PIPE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    summary_path = output / "run" / "SUMMARY.json"
    for _ in range(100):
        if summary_path.is_file():
            break
        time.sleep(0.05)
    assert summary_path.is_file(), log.read_text(encoding="utf-8", errors="replace")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["statuses"] == {"prepared": 1}
    assert pid_file.read_text(encoding="utf-8").strip().isdigit()


def test_runtime_export_isolates_exporter_standard_streams(tmp_path: Path) -> None:
    exporter_probe = tmp_path / "exporter_probe.py"
    exporter_probe.write_text(
        "import os\n"
        "for fd in (0, 1, 2):\n"
        "    os.fstat(fd)\n",
        encoding="utf-8",
    )
    helper = f"""
import importlib.util
import os
from pathlib import Path
import sys

runner_path = Path({str(RUN_CAMPAIGN)!r})
spec = importlib.util.spec_from_file_location("run_campaign_stdio_probe", runner_path)
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)
runner.EXPORTER = Path({str(exporter_probe)!r})
os.close(0)
runner.export_runtime(
    {{
        "cell_id": "v4-012-G0-r00",
        "task_id": "v4-012",
        "mode": "G0",
        "per_turn_max_tokens": 131072,
    }},
    Path({str(R49_RELEASE)!r}),
    Path({str(tmp_path / "runtime")!r}),
    timeout_s=30,
)
"""
    completed = subprocess.run(
        [sys.executable, "-c", helper],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_campaign_wrapper_requires_explicit_evas_for_executable_run(
    tmp_path: Path,
) -> None:
    clean_env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"DEEPSEEK_API_KEY", "VAEVAS_API_KEY"}
    }
    completed = subprocess.run(
        [
            sys.executable,
            str(RUN_CAMPAIGN_WRAPPER),
            "--release",
            str(R52_RELEASE),
            "--task-id",
            "v4-006",
            "--mode",
            "G2",
            "--output-root",
            str(tmp_path / "campaign"),
            "--model",
            "test-model",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=clean_env,
    )

    assert completed.returncode != 0
    assert "--evas-command is required for executable campaigns" in completed.stderr


def test_campaign_wrapper_records_resolved_evas_identity(
    tmp_path: Path,
) -> None:
    fake_evas = tmp_path / "fixed-evas"
    fake_evas.write_text(
        "#!/bin/bash\necho 'evas-sim 9.8.7 (ABI 20260721, revision test-rev)'\n",
        encoding="utf-8",
    )
    fake_evas.chmod(0o755)
    output = tmp_path / "campaign"

    completed = subprocess.run(
        [
            sys.executable,
            str(RUN_CAMPAIGN_WRAPPER),
            "--release",
            str(R49_RELEASE),
            "--task-id",
            "v4-006",
            "--mode",
            "G0",
            "--output-root",
            str(output),
            "--model",
            "test-model",
            "--evas-command",
            str(fake_evas),
            "--dry-run",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    execution = json.loads((output / "campaign.json").read_text())["execution_config"]
    assert execution["evas_command"] == str(fake_evas.resolve())
    assert execution["evas_identity"]["available"] is True
    assert execution["evas_identity"]["resolved_executable"] == str(fake_evas.resolve())
    assert execution["evas_identity"]["version_output"] == (
        "evas-sim 9.8.7 (ABI 20260721, revision test-rev)"
    )
    assert len(execution["evas_identity"]["executable_sha256"]) == 64


def test_runner_rejects_changed_evas_identity_before_execution(tmp_path: Path) -> None:
    runner = load_run_campaign()
    fake_evas = tmp_path / "fixed-evas"
    fake_evas.write_text("#!/bin/bash\necho 'evas-sim 1.0 revision-a'\n")
    fake_evas.chmod(0o755)
    expected = runner.resolve_pinned_evas_identity(str(fake_evas))
    fake_evas.write_text("#!/bin/bash\necho 'evas-sim 1.0 revision-b'\n")

    with pytest.raises(SystemExit, match="EVAS identity mismatch"):
        runner.validate_pinned_evas_identity(str(fake_evas), expected)


def test_scorer_requires_explicit_evas_for_trusted_replay(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCORE_CAMPAIGN),
            "--campaign-output",
            str(tmp_path),
            "--judge-kind",
            "final_trusted_replay",
            "--judge-command",
            "/usr/bin/true",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode != 0
    assert "--evas-command is required when replay executes" in completed.stderr


def test_campaign_wrapper_task_id_filter_does_not_require_selection(
    tmp_path: Path, r45_release: Path
) -> None:
    output = tmp_path / "campaign-task"
    completed = subprocess.run(
        [
            sys.executable,
            str(RUN_CAMPAIGN_WRAPPER),
            "--release",
            str(r45_release),
            "--task-id",
            "v4-006",
            "--mode",
            "G0",
            "--output-root",
            str(output),
            "--model",
            "deepseek-v4-flash",
            "--dry-run",
            "--workers",
            "1",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    campaign = json.loads((output / "campaign.json").read_text(encoding="utf-8"))
    assert campaign["cell_count"] == 1
    assert campaign["cells"][0]["task_id"] == "v4-006"
    assert campaign["cells"][0]["mode"] == "G0"


def test_campaign_wrapper_redacts_credential_and_operator_command_paths(
    tmp_path: Path, r45_release: Path,
) -> None:
    output = tmp_path / "campaign-redacted"
    secret_path = tmp_path / "private" / "provider.key"
    judge_command = f"python3 {tmp_path / 'private' / 'judge.py'}"
    completed = subprocess.run(
        [
            sys.executable,
            str(RUN_CAMPAIGN_WRAPPER),
            "--release",
            str(r45_release),
            "--task-id",
            "v4-001",
            "--mode",
            "G0",
            "--output-root",
            str(output),
            "--model",
            "test-model",
            "--api-key-file",
            str(secret_path),
            "--final-judge-command",
            judge_command,
            "--dry-run",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    summary_text = (output / "wrapper_summary.json").read_text(encoding="utf-8")
    campaign_text = (output / "campaign.json").read_text(encoding="utf-8")
    persisted_text = summary_text + campaign_text
    assert str(secret_path) not in persisted_text
    assert judge_command not in persisted_text
    assert "<redacted-credential-file>" in summary_text
    assert "<redacted-operator-command>" in summary_text


def test_budget_reuse_requires_identical_execution_configuration() -> None:
    reuse = load_prepare_budget_reuse()
    base = {
        "model_provider": "test-provider",
        "model": "test-model",
        "release_manifest_sha256": "a" * 64,
        "selection_manifest_sha256": "b" * 64,
        "per_turn_max_tokens": 4096,
        "max_output_tokens": 4096,
        "execution_config": {
            "temperature": 0.0,
            "stream": False,
            "base_url_sha256": "c" * 64,
            "evas_command_sha256": "d" * 64,
        },
    }
    target = json.loads(json.dumps(base))
    reuse.check_campaign_compatibility(base, target)

    target["per_turn_max_tokens"] = 65536
    target["max_output_tokens"] = 65536
    try:
        reuse.check_campaign_compatibility(base, target)
    except ValueError as exc:
        assert "per-turn token cap mismatch" in str(exc)
    else:
        raise AssertionError("reuse accepted a different per-turn token cap")

    target = json.loads(json.dumps(base))
    target["execution_config"]["temperature"] = 0.2
    try:
        reuse.check_campaign_compatibility(base, target)
    except ValueError as exc:
        assert "execution_config mismatch" in str(exc)
    else:
        raise AssertionError("reuse accepted a different decoding configuration")


def test_feedback_adapter_uses_exported_lowercase_task_record(tmp_path: Path) -> None:
    adapter = load_feedback_adapter()
    runtime = tmp_path / "runtime"
    (runtime / "evidence").mkdir(parents=True)
    (runtime / "evaluator").mkdir()
    (runtime / "evidence" / "attempt_record.json").write_text(
        json.dumps({"task_id": "v4-001"}), encoding="utf-8"
    )
    task_dir = RELEASE / "tasks" / "001-bang-bang-phase-detector"
    record = json.loads((task_dir / "task_record.json").read_text(encoding="utf-8"))
    (runtime / "evaluator" / "task_record.json").write_text(
        json.dumps(record), encoding="utf-8"
    )

    observed, task_dir = adapter.runtime_task(runtime)

    assert observed["task_id"] == "v4-001"
    assert task_dir.name == "001-bang-bang-phase-detector"


def test_feedback_adapter_uses_the_frozen_five_case_testbench_suite() -> None:
    adapter = load_feedback_adapter()
    evaluator = (
        RELEASE
        / "tasks"
        / "501-bang-bang-phase-detector-testbench"
        / "evaluator"
    )

    suite = adapter.testbench_negative_suite(evaluator)

    assert suite == [
        "neg_001_swap_outputs",
        "neg_003_never_clears_on_clock",
        "neg_004_both_outputs_on_direction",
        "neg_006_weak_high_level",
        "neg_005_retimed_ignored",
    ]


def test_harness_renderer_reproduces_tracked_profiles() -> None:
    renderer = load_render_harness()
    task_dir = RELEASE / "tasks" / "001-bang-bang-phase-detector"
    spec, spec_hash = renderer.load_spec(task_dir / "evaluator" / "harness_spec.json")

    for profile_name in ("feedback", "score"):
        observed = renderer.build_profile(spec, profile_name, spec_hash)
        expected = json.loads(
            (task_dir / "evaluator" / "profiles" / f"{profile_name}.json").read_text(
                encoding="utf-8"
            )
        )
        assert observed == expected


def test_benchmarkv4_testbench_security_uses_public_binding_schema(tmp_path: Path) -> None:
    security = load_testbench_security()
    task = RELEASE / "tasks" / "506-element-shuffler-testbench"
    contract = json.loads((task / "public_contract.json").read_text(encoding="utf-8"))
    policy = json.loads((task / "evaluator" / "score_policy.json").read_text(encoding="utf-8"))
    candidate = tmp_path / "testbench.scs"
    candidate.write_text(
        "\n".join(
            [
                "simulator lang=spectre",
                'ahdl_include "./dut/element_shuffler.va"',
                "XDUT (clk rst_n out0 out1 out2 out3) element_shuffler",
                "tran tran stop=20n",
                "save clk rst_n out0 out1 out2 out3",
            ]
        ),
        encoding="utf-8",
    )

    result = security.validate_testbench(candidate, contract, policy)

    assert result.valid, result.diagnostics


def test_benchmarkv4_testbench_security_rejects_suffixed_or_hierarchical_saves(
    tmp_path: Path,
) -> None:
    security = load_testbench_security()
    task = RELEASE / "tasks" / "506-element-shuffler-testbench"
    contract = json.loads((task / "public_contract.json").read_text(encoding="utf-8"))
    policy = json.loads((task / "evaluator" / "score_policy.json").read_text(encoding="utf-8"))
    candidate = tmp_path / "testbench.scs"
    candidate.write_text(
        "\n".join(
            [
                "simulator lang=spectre",
                'ahdl_include "./dut/element_shuffler.va"',
                "XDUT (clk rst_n out0 out1 out2 out3) element_shuffler",
                "tran tran stop=20n",
                "save clk:V rst_n:V out0:V out1:V out2:V out3:V",
            ]
        ),
        encoding="utf-8",
    )

    result = security.validate_testbench(candidate, contract, policy)

    assert not result.valid
    assert any("private_hierarchical_probe" in item for item in result.diagnostics)


def test_benchmarkv4_testbench_security_enforces_instance_parameters_and_uniqueness(
    tmp_path: Path,
) -> None:
    security = load_testbench_security()
    task = RELEASE / "tasks" / "506-element-shuffler-testbench"
    contract = json.loads((task / "public_contract.json").read_text(encoding="utf-8"))
    contract["testbench_binding"]["instances"][0]["parameter_overrides"] = {"width": 4}
    policy = json.loads(
        (task / "evaluator" / "testbench_security_policy.json").read_text(encoding="utf-8")
    )
    candidate = tmp_path / "testbench.scs"
    required_lines = [
        "simulator lang=spectre",
        'ahdl_include "./dut/element_shuffler.va"',
        "tran tran stop=20n",
        "save clk rst_n out0 out1 out2 out3",
    ]

    candidate.write_text(
        "\n".join(
            required_lines[:2]
            + ["XDUT (clk rst_n out0 out1 out2 out3) element_shuffler"]
            + required_lines[2:]
        ),
        encoding="utf-8",
    )
    missing_parameter = security.validate_testbench(candidate, contract, policy)
    assert not missing_parameter.valid
    assert any("declared_dut_binding" in item for item in missing_parameter.diagnostics)

    instance = "XDUT (clk rst_n out0 out1 out2 out3) element_shuffler width=4"
    candidate.write_text(
        "\n".join(required_lines[:2] + [instance, instance] + required_lines[2:]),
        encoding="utf-8",
    )
    duplicate = security.validate_testbench(candidate, contract, policy)
    assert not duplicate.valid
    assert any("declared_dut_binding" in item for item in duplicate.diagnostics)

    candidate.write_text(
        "\n".join(required_lines[:2] + [instance] + required_lines[2:]),
        encoding="utf-8",
    )
    valid = security.validate_testbench(candidate, contract, policy)
    assert valid.valid, valid.diagnostics


def test_benchmarkv4_testbench_security_allows_public_parameter_overrides(
    tmp_path: Path,
) -> None:
    security = load_testbench_security()
    task = RELEASE / "tasks" / "578-lfsr-prbs-generator-testbench"
    contract = json.loads((task / "public_contract.json").read_text(encoding="utf-8"))
    policy = json.loads(
        (task / "evaluator" / "testbench_security_policy.json").read_text(
            encoding="utf-8"
        )
    )
    candidate = tmp_path / "testbench.scs"
    common = [
        "simulator lang=spectre",
        'ahdl_include "./dut/prbs7_ref.va"',
        "tran tran stop=20n",
        "save clk rst_n en serial_out state_0 state_1 state_2 state_3 state_4 state_5 state_6",
    ]

    candidate.write_text(
        "\n".join(
            common[:2]
            + [
                "XDUT (clk rst_n en serial_out state_0 state_1 state_2 state_3 "
                "state_4 state_5 state_6) prbs7_ref seed=0"
            ]
            + common[2:]
        ),
        encoding="utf-8",
    )
    allowed = security.validate_testbench(candidate, contract, policy)
    assert allowed.valid, allowed.diagnostics

    candidate.write_text(
        candidate.read_text(encoding="utf-8").replace("seed=0", "private_seed=0"),
        encoding="utf-8",
    )
    unknown = security.validate_testbench(candidate, contract, policy)
    assert not unknown.valid
    assert any("declared_dut_binding" in item for item in unknown.diagnostics)


def test_benchmarkv4_testbench_security_accepts_sample_threshold_override(
    tmp_path: Path,
) -> None:
    security = load_testbench_security()
    task = RELEASE / "tasks" / "604-sample-and-hold-ideal-testbench"
    contract = json.loads((task / "public_contract.json").read_text(encoding="utf-8"))
    policy = json.loads(
        (task / "evaluator" / "testbench_security_policy.json").read_text(
            encoding="utf-8"
        )
    )
    candidate = tmp_path / "testbench.scs"
    candidate.write_text(
        "\n".join(
            [
                "simulator lang=spectre",
                'ahdl_include "./dut/source_sample_hold.va"',
                "XDUT (vin vout vclk) source_sample_hold vtrans_clk=0.8",
                "tran tran stop=8n",
                "save vclk vin vout",
            ]
        ),
        encoding="utf-8",
    )

    result = security.validate_testbench(candidate, contract, policy)

    assert result.valid, result.diagnostics


def test_testbench_security_allows_declared_read_only_support() -> None:
    security = load_testbench_security()
    contract = {
        "artifact_contract": {"files": [{"path": "dut.va"}]},
        "supplied_support_artifacts": ["supplied_dut/support/helper.va"],
        "testbench_binding": {"source_path_template": "./dut/{artifact_path}"},
    }

    assert security._allowed_includes(contract) == {
        "./dut/dut.va",
        "./dut/support/helper.va",
    }


def test_negative_bundle_prefers_declared_artifact_over_legacy_alias(tmp_path: Path) -> None:
    oracle = load_derived_testbench_oracle()
    bundle = tmp_path / "negative"
    bundle.mkdir()
    declared = bundle / "cmp_offset_ref.va"
    alias = bundle / "neg_001.va"
    declared.write_text("module cmp_offset_ref; endmodule\n", encoding="utf-8")
    alias.write_text("module legacy_alias; endmodule\n", encoding="utf-8")

    mapped = oracle._negative_bundle_sources(bundle, ["cmp_offset_ref.va"])

    assert mapped == {"cmp_offset_ref.va": declared}


def test_testbench_oracle_stages_modern_dut_and_support_paths(tmp_path: Path) -> None:
    oracle = load_derived_testbench_oracle()
    evaluator = tmp_path / "evaluator"
    (evaluator / "solution" / "support").mkdir(parents=True)
    (evaluator / "solution" / "dut.va").write_text(
        "module dut; endmodule\n", encoding="utf-8"
    )
    (evaluator / "solution" / "support" / "helper.va").write_text(
        "module helper; endmodule\n", encoding="utf-8"
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    oracle._prepare_dut_sources(
        package_root=ROOT,
        source_formal=evaluator,
        run_dir=run_dir,
        target_artifacts=["dut.va"],
        dut_subdir="dut",
        public_contract={
            "supplied_support_artifacts": ["supplied_dut/support/helper.va"]
        },
    )

    assert (run_dir / "dut" / "dut.va").is_file()
    assert (run_dir / "dut" / "support" / "helper.va").is_file()


def test_testbench_oracle_failure_excerpt_keeps_error_before_counters() -> None:
    oracle = load_derived_testbench_oracle()
    combined = "\n".join(
        [
            "Reading netlist tb_candidate.scs",
            "Error: tb_candidate.scs:4: ahdl source loaded with include",
            *(f"solver_counter_{index} = 0" for index in range(500)),
            "evas completes with 1 errors, 0 warnings.",
        ]
    )

    excerpt = oracle._simulation_failure_excerpt(combined)

    assert "Error: tb_candidate.scs:4" in excerpt
    assert "solver_counter_250" not in excerpt


def test_testbench_oracle_requires_pinned_evas_version(monkeypatch) -> None:
    oracle = load_derived_testbench_oracle()
    monkeypatch.setenv("EVAS_ENGINE", "evas2")
    monkeypatch.setenv("VAEVAS_DEFAULT_EVAS_ENGINE", "evas2")
    runtime_report = "\n".join(
        [
            f"Version {oracle.REQUIRED_EVAS_VERSION} -- Jul 2026",
            "evas_engine = evas-rust",
            "evas_rust_required = true",
            "evas_rust_full_model_required = true",
            "rust_full_model_required_failures = 0",
        ]
    )

    valid, note = oracle._validate_required_evas_engine(runtime_report, "evas2")
    stale, stale_note = oracle._validate_required_evas_engine(
        runtime_report.replace(
            f"Version {oracle.REQUIRED_EVAS_VERSION}", "Version 0.8.4"
        ),
        "evas2",
    )

    assert valid is True
    assert f"evas_version={oracle.REQUIRED_EVAS_VERSION}" in note
    assert stale is False
    assert "observed='0.8.4'" in stale_note


def test_testbench_oracle_accepts_r52_evas_without_legacy_backend_counters(
    monkeypatch,
) -> None:
    oracle = load_derived_testbench_oracle()
    monkeypatch.setenv("EVAS_ENGINE", "evas2")
    monkeypatch.setenv("VAEVAS_DEFAULT_EVAS_ENGINE", "evas2")

    valid, note = oracle._validate_required_evas_engine(
        f"Version {oracle.REQUIRED_EVAS_VERSION} -- Jul 2026\nsimulation complete",
        "evas2",
    )

    assert valid is True
    assert "evas_reported_engine=not_emitted" in note


def test_summarize_evas_invocations_derives_candidate_version_repeats() -> None:
    runner = load_run_campaign()
    first_hash = "a" * 64
    second_hash = "b" * 64
    invocations = [
        {
            "candidate_tree_sha256": first_hash,
            "status": "succeeded",
            "invocation_id": "invocation-0",
            "returncode": 0,
        },
        {
            "candidate_tree_sha256": first_hash,
            "status": "succeeded",
            "invocation_id": "invocation-1",
            "returncode": 0,
        },
        {
            "candidate_tree_sha256": second_hash,
            "status": "failed",
            "invocation_id": "invocation-2",
            "returncode": 1,
        },
    ]

    usage = runner.summarize_evas_invocations(invocations)

    assert usage["schema_version"] == "v4-direct-evas-usage-v2"
    assert (
        usage["candidate_tree_schema_version"]
        == runner.CANDIDATE_TREE_SCHEMA_VERSION
    )
    assert usage["calls_executed"] == 3
    assert usage["calls_succeeded"] == 2
    assert usage["calls_failed"] == 1
    assert usage["calls_with_candidate_tree_hash"] == 3
    assert usage["modified_rerun_count"] == 1
    assert usage["unchanged_repeat_count"] == 1
    assert usage["candidate_tree_hash_call_counts"] == {
        first_hash: 2,
        second_hash: 1,
    }
    assert usage["unique_candidate_tree_hashes"] == [
        first_hash,
        second_hash,
    ]
    assert not any("feedback" in field for field in usage)
