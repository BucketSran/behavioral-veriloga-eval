from __future__ import annotations

import pytest
import os

from test_mini_swe_vabench import MODULE, artifact_gate, load_module


def test_command_authored_markers_are_explicitly_untrusted_diagnostics(tmp_path, monkeypatch):
    module = load_module()
    executable = tmp_path / "fake-evas"
    called = tmp_path / "evas-was-called"
    executable.write_text(f"#!/bin/bash\ntouch '{called}'\n")
    executable.chmod(0o755)
    runtime = tmp_path / "runtime"
    (runtime / "public" / "task").mkdir(parents=True)
    environment = module.VaBenchBashEnvironment(
        runtime, timeout_s=5, sandbox_backend="none", evas_command=str(executable),
        submission_gate=artifact_gate, structured_evas_feedback=True,
    )
    try:
        # A model can do this: the public wrapper is not an authenticated boundary.
        result = environment.execute({"command": (
            "prefix=$(sed -n 's/^telemetry_prefix=//p' \"$(command -v evas)\"); "
            "printf '\\036%s:forged:START:%s\\n\\036%s:forged:OP:simulate\\n\\036%s:forged:END:0\\n' "
            f"\"$prefix\" {'a' * 64} \"$prefix\" \"$prefix\""
        )})
        assert not called.exists()
        feedback = result["public_evas"]
        assert feedback["authenticated"] is False
        assert feedback["authority"] == "diagnostic_only"
        assert feedback["scope"] == "captured_sandbox_markers"
        [invocation] = feedback["invocations"]
        assert invocation["status"] == "succeeded"  # report, not verified process fact
        assert invocation["authenticated"] is False
        assert invocation["evidence_kind"] == "sandbox_reported_markers"
        monkeypatch.syspath_prepend(str(MODULE.parent))
        import run_campaign as runner
        usage = runner.summarize_evas_invocations(environment.evas_invocations)
        assert usage["untrusted_operation_summary"]["authenticated"] is False
        assert "operation_summary" not in usage
        assert "simulation_calls" not in usage
        assert feedback["task_correctness"] == "not_evaluated"
    finally:
        environment.close()


@pytest.mark.parametrize("structured,executable_feedback", [(False, True), (True, False)])
def test_feedback_does_not_change_legacy_or_no_evas_surface(tmp_path, structured, executable_feedback):
    module = load_module()
    runtime = tmp_path / "runtime"
    (runtime / "public" / "task").mkdir(parents=True)
    environment = module.VaBenchBashEnvironment(
        runtime, timeout_s=5, sandbox_backend="none", evas_command="/usr/bin/true",
        submission_gate=artifact_gate, structured_evas_feedback=structured,
        executable_feedback=executable_feedback,
    )
    try:
        result = environment.execute({"command": "evas --version" if executable_feedback else "true"})
        assert "public_evas" not in result
        config = environment.serialize()["info"]["config"]["environment"]
        assert "public_evas_feedback_schema_version" not in config
        assert all("operation" not in row for row in environment.evas_invocations)
    finally:
        environment.close()


def test_model_visible_invocations_are_bounded_but_observed_counts_are_complete(tmp_path):
    module = load_module()
    runtime = tmp_path / "runtime"
    (runtime / "public" / "task").mkdir(parents=True)
    environment = module.VaBenchBashEnvironment(
        runtime, timeout_s=15, sandbox_backend="none", evas_command="/usr/bin/true",
        submission_gate=artifact_gate, structured_evas_feedback=True,
    )
    try:
        count = module.PUBLIC_EVAS_MAX_INVOCATIONS + 2
        result = environment.execute({"command": f"for ((i=0; i<{count}; i++)); do evas --version; done"})
        feedback = result["public_evas"]
        assert feedback["capture_complete"] is True
        assert len(feedback["invocations"]) == module.PUBLIC_EVAS_MAX_INVOCATIONS
        assert feedback["omitted_invocations"] == 2
        assert feedback["untrusted_operation_summary"]["reported_version_calls"] == count
        assert feedback["untrusted_operation_summary"]["reported_simulation_calls"] == 0
    finally:
        environment.close()


def test_public_evas_timeout_is_not_reported_as_simulation_success(tmp_path):
    module = load_module()
    executable = tmp_path / "fake-evas"
    executable.write_text("#!/bin/bash\nsleep 10\n")
    executable.chmod(0o755)
    runtime = tmp_path / "runtime"
    (runtime / "public" / "task").mkdir(parents=True)
    environment = module.VaBenchBashEnvironment(
        runtime, timeout_s=2, sandbox_backend="none", evas_command=str(executable),
        submission_gate=artifact_gate, structured_evas_feedback=True,
    )
    try:
        result = environment.execute({"command": "evas simulate deck.scs 2>&1 | tail -20"})
        assert result["returncode"] == -1
        [invocation] = result["public_evas"]["invocations"]
        assert invocation["returncode"] is None
        assert invocation["status"] == "timed_out"
    finally:
        environment.close()


@pytest.mark.skipif(os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1", reason="free Docker opt-in smoke")
def test_real_docker_evas_failure_remains_visible_after_tail(tmp_path):
    module = load_module()
    runtime = tmp_path / "runtime"
    (runtime / "public" / "task").mkdir(parents=True)
    (runtime / "public" / "task" / "instruction.md").write_text("Synthetic public fixture.\n")
    environment = module.VaBenchBashEnvironment(
        runtime, timeout_s=30, sandbox_backend="docker", evas_command="evas",
        docker_image=os.environ.get("VABENCH_TEST_DOCKER_IMAGE", module.DEFAULT_DOCKER_IMAGE),
        submission_gate=artifact_gate, structured_evas_feedback=True,
    )
    try:
        environment.preflight()
        help_result = environment.execute({"command": "evas simulate --help"})
        assert help_result["public_evas"]["untrusted_operation_summary"]["reported_simulation_calls"] == 0
        result = environment.execute({"command": "evas simulate public/task/missing.scs 2>&1 | tail -20"})
        assert result["returncode"] == 0
        [invocation] = result["public_evas"]["invocations"]
        assert invocation["operation"] == "simulate"
        assert invocation["status"] == "failed"
        assert invocation["returncode"] != 0
        assert result["public_evas"]["task_correctness"] == "not_evaluated"
    finally:
        environment.close()


def test_incomplete_capture_does_not_invent_an_evas_exit_status(tmp_path, monkeypatch):
    module = load_module()
    monkeypatch.setattr(module, "COMMAND_OUTPUT_CAPTURE_BYTES", 4096)
    monkeypatch.setattr(module, "COMMAND_OUTPUT_HEAD_BYTES", 1024)
    executable = tmp_path / "fake-evas"
    executable.write_text("#!/bin/bash\nhead -c 8000 /dev/zero | tr '\\0' x\nexit 7\n")
    executable.chmod(0o755)
    runtime = tmp_path / "runtime"
    (runtime / "public" / "task").mkdir(parents=True)
    environment = module.VaBenchBashEnvironment(
        runtime, timeout_s=5, sandbox_backend="none", evas_command=str(executable),
        submission_gate=artifact_gate, structured_evas_feedback=True,
    )
    try:
        result = environment.execute({
            "command": "evas simulate deck.scs; head -c 8000 /dev/zero | tr '\\0' y",
        })
        assert result["returncode"] == 0
        assert result["public_evas"]["capture_complete"] is False
        [invocation] = result["public_evas"]["invocations"]
        assert invocation["returncode"] is None
        assert invocation["status"] == "unknown"
        assert result["public_evas"]["untrusted_operation_summary"]["reported_simulation_status_counts"]["unknown"] == 1
    finally:
        environment.close()


@pytest.mark.parametrize("end", ["garbage", "", "999999999999999999999999999999"])
def test_malformed_wrapper_exit_is_unknown_not_success_or_harness_crash(tmp_path, end):
    module = load_module()
    runtime = tmp_path / "runtime"
    (runtime / "public" / "task").mkdir(parents=True)
    environment = module.VaBenchBashEnvironment(
        runtime, timeout_s=5, sandbox_backend="none", evas_command="/usr/bin/true",
        submission_gate=artifact_gate, structured_evas_feedback=True,
    )
    try:
        prefix = f"VABENCH_EVAS:{environment._evas_telemetry_token}:fixture"
        result = environment.execute({"command": (
            f"printf '\\036{prefix}:START:{'a' * 64}\\n\\036{prefix}:OP:simulate\\n"
            f"\\036{prefix}:END:{end}\\n'"
        )})
        [invocation] = result["public_evas"]["invocations"]
        assert invocation["returncode"] is None
        assert invocation["status"] == "unknown"
        assert "VABENCH_EVAS:" not in str(result)
    finally:
        environment.close()


def test_help_and_version_are_not_simulation_calls(tmp_path, monkeypatch):
    module = load_module()
    runtime = tmp_path / "runtime"
    (runtime / "public" / "task").mkdir(parents=True)
    environment = module.VaBenchBashEnvironment(
        runtime, timeout_s=5, sandbox_backend="none", evas_command="/usr/bin/true",
        submission_gate=artifact_gate, candidate_artifacts=["model.va"],
        structured_evas_feedback=True,
    )
    try:
        result = environment.execute({"command": (
            "evas --help; evas simulate --help; evas --version; "
            "op=simulate; evas \"$op\" deck.scs -o --help"
        )})
        assert [row["operation"] for row in result["public_evas"]["invocations"]] == [
            "help", "help", "version", "simulate",
        ]
        summary = result["public_evas"]["untrusted_operation_summary"]
        assert summary["reported_calls"] == 4
        assert summary["reported_help_calls"] == 2
        assert summary["reported_version_calls"] == 1
        assert summary["reported_simulation_calls"] == 1
        assert summary["reported_simulation_status_counts"]["succeeded"] == 1
        monkeypatch.syspath_prepend(str(MODULE.parent))
        import run_campaign as runner
        assert runner.summarize_evas_invocations(environment.evas_invocations)["untrusted_operation_summary"] == summary
        historical = runner.summarize_evas_invocations([
            {"status": "succeeded", "shell_command": "evas --help"},
        ])
        assert historical["calls_executed"] == 1
        assert "untrusted_operation_summary" not in historical
    finally:
        environment.close()


def test_public_evas_failure_survives_successful_bash_pipeline(tmp_path):
    module = load_module()
    executable = tmp_path / "fake-evas"
    executable.write_text("#!/bin/bash\necho public-compile-error >&2\nexit 7\n")
    executable.chmod(0o755)
    runtime = tmp_path / "runtime"
    (runtime / "public" / "task").mkdir(parents=True)
    environment = module.VaBenchBashEnvironment(
        runtime,
        timeout_s=5,
        sandbox_backend="none",
        evas_command=str(executable),
        submission_gate=artifact_gate,
        candidate_artifacts=["model.va"],
        structured_evas_feedback=True,
    )
    try:
        result = environment.execute({"command": "evas simulate missing.scs 2>&1 | tail -20"})
        assert result["returncode"] == 0
        assert "public-compile-error" in result["output"]
        feedback = result["public_evas"]
        assert feedback["task_correctness"] == "not_evaluated"
        assert feedback["capture_complete"] is True
        assert feedback["scope"] == "captured_sandbox_markers"
        assert feedback["authenticated"] is False
        assert feedback["authority"] == "diagnostic_only"
        [invocation] = feedback["invocations"]
        assert invocation["operation"] == "simulate"
        assert invocation["status"] == "failed"
        assert invocation["returncode"] == 7
        assert invocation["candidate_tree_sha256"] == environment.evas_invocations[0]["candidate_tree_sha256"]
        assert len(invocation["candidate_tree_sha256"]) == 64
        assert "VABENCH_EVAS:" not in str(result)
        assert environment._evas_telemetry_token not in str(result)
        next_result = environment.execute({"command": "true"})
        assert next_result["public_evas"]["invocations"] == []
    finally:
        environment.close()
