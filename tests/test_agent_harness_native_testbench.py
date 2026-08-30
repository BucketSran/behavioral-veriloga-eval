"""Native Testbench public authority binds only the released reference DUT."""

import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
sys.path.insert(0, str(CALIBRATION))

import mini_swe_vabench as mini  # noqa: E402
import public_validation as validation  # noqa: E402
from runners.agent_harness import EpisodeContext  # noqa: E402

RELEASE = ROOT / "benchmark-vabench-release-v4/release/benchmarkv4-r53"
PUBLIC = RELEASE / "tasks/501-bang-bang-phase-detector-testbench/public"


@pytest.fixture
def testbench_environment(tmp_path):
    runtime = tmp_path / "runtime"
    shutil.copytree(PUBLIC, runtime / "public/task")
    executable = tmp_path / "evas"
    executable.write_text("#!/bin/sh\necho 'evas-sim 0.8.7 (test double)'\n")
    executable.chmod(0o755)
    environment = mini.VaBenchBashEnvironment(
        runtime, timeout_s=10, sandbox_backend="none",
        evas_command=str(executable), submission_gate=lambda _: {"passed": False},
        candidate_artifacts=("testbench.scs",),
    )
    (environment.workspace / "submission/testbench.scs").write_text(
        'simulator lang=spectre\nahdl_include "dut/bbpd_ref.va"\ntran tran stop=1n\n'
    )
    yield environment
    environment.close()


def bind(environment):
    profile = validation.build_public_validation_profile(
        environment=environment, release=RELEASE,
        campaign_config_sha256="a" * 64, allow_insecure_test_sandbox=True,
    )
    return validation.PublicEvasValidator(
        environment=environment,
        context=EpisodeContext("cell-501", "attempt-001", "v4-501", "Agentic", 2),
        public_validation_profile=profile, allow_insecure_test_sandbox=True,
    ), profile


def test_native_testbench_accepts_pinned_reference_only_public_authority(testbench_environment):
    adapter, profile = bind(testbench_environment)
    assert profile["allowed_feedback"] == ["runtime", "log_excerpt"]
    assert adapter.candidate_tree_sha256()


def test_public_validation_executes_only_reference_and_returns_no_score(testbench_environment, monkeypatch):
    environment = testbench_environment
    adapter, _ = bind(environment)
    commands = []

    def execute(action):
        commands.append(action["command"])
        environment.evas_invocations.append({
            "candidate_tree_schema_version": mini.CANDIDATE_TREE_SCHEMA_VERSION,
            "candidate_tree_sha256": validation._invocation_tree_sha256(
                environment.workspace / "submission", environment.candidate_artifacts
            ),
            "invocation_id": "public-reference-1", "status": "succeeded", "returncode": 0,
        })
        return {"output": "reference diagnostic", "elapsed_s": 0.1,
                "output_truncated_bytes": 0, "output_captured_bytes": 20}

    monkeypatch.setattr(environment, "execute", execute)
    observation = adapter.validate(candidate_tree_sha256=adapter.candidate_tree_sha256())
    assert commands == ["cd public && " + validation.TESTBENCH_COMMAND]
    assert observation.payload["feedback_scope"] == "reference_dut_only"
    assert "score" not in observation.payload and "passed" not in observation.payload


@pytest.mark.parametrize("change", ["command", "binding", "scope", "reference", "symlink"])
def test_testbench_public_contract_drift_fails_before_execution(testbench_environment, change):
    environment = testbench_environment
    adapter, _ = bind(environment)
    task = environment.workspace / "task"
    contract_path = task / "evas_runtime.json"
    contract = json.loads(contract_path.read_text())
    if change == "command":
        contract["candidate_command"] += " && cat evaluator/secret"
    elif change == "binding":
        contract["reference_dut_root"] = "evaluator/faults"
    elif change == "scope":
        contract["feedback_scope"] = "reference_plus_five_hidden_faults"
    else:
        path = task / "supplied_dut/bbpd_ref.va"
        if change == "symlink":
            path.unlink()
            path.symlink_to(task / "evas_runtime.json")
        else:
            path.write_text("module changed; endmodule\n")
    contract_path.write_text(json.dumps(contract))
    with pytest.raises(ValueError):
        adapter.validate(candidate_tree_sha256=adapter.candidate_tree_sha256())
    assert environment.evas_invocations == []


@pytest.mark.parametrize("include", ["../evaluator/fault.va", "/tmp/fault.va", "other.va"])
def test_candidate_cannot_escape_reference_binding(testbench_environment, include):
    environment = testbench_environment
    adapter, _ = bind(environment)
    (environment.workspace / "submission/testbench.scs").write_text(f'ahdl_include "{include}"\n')
    with pytest.raises(ValueError, match="fixture|below ./dut"):
        adapter.validate(candidate_tree_sha256=adapter.candidate_tree_sha256())
    assert environment.evas_invocations == []
