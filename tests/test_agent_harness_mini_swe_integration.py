from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

from runners.agent_harness import AgentAction, EpisodeContext, FrozenSubmission, ToolRegistry
from runners.agent_harness.backends.mini_swe import (
    MiniSweBashEnvironmentBridge,
    mini_swe_bash_tool_descriptor,
)


ROOT = Path(__file__).resolve().parents[1]
MINI_SWE_MODULE = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "operations"
    / "calibration_pilot"
    / "mini_swe_vabench.py"
)
RESULT_PROTOCOL_MODULE = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "operations"
    / "calibration_pilot"
    / "result_protocol.py"
)


class Submitted(Exception):
    pass


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _runtime(root: Path) -> Path:
    runtime = root / "runtime"
    (runtime / "public" / "task").mkdir(parents=True)
    (runtime / "public" / "task" / "instruction.md").write_text(
        "Generate model.va.",
        encoding="utf-8",
    )
    (runtime / "public" / "submission").mkdir(parents=True)
    (runtime / "evaluator").mkdir(parents=True)
    (runtime / "evaluator" / "secret.txt").write_text(
        "never model-visible",
        encoding="utf-8",
    )
    return runtime


def _artifact_gate(runtime: Path) -> dict[str, object]:
    relative = "model.va"
    artifact = runtime / "public" / "submission" / relative
    passed = artifact.is_file() and not artifact.is_symlink()
    return {
        "passed": passed,
        "expected_artifacts": [relative],
        "diagnostics": [] if passed else [f"missing:{relative}"],
        "artifact_sha256": (
            {relative: hashlib.sha256(artifact.read_bytes()).hexdigest()}
            if passed
            else {}
        ),
    }


def _candidate_tree_sha256(runtime: Path, result_protocol) -> str:
    artifact = runtime / "public" / "submission" / "model.va"
    if not artifact.is_file() or artifact.is_symlink():
        return result_protocol.canonical_sha256(
            [{"path": "model.va", "state": "missing"}]
        )
    return result_protocol.canonical_sha256(
        [
            {
                "path": "model.va",
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            }
        ]
    )


def _freeze_submission(
    runtime: Path,
    result_protocol,
) -> FrozenSubmission:
    snapshot = result_protocol.snapshot_submission(
        runtime,
        _artifact_gate(runtime),
    )
    return FrozenSubmission(
        tree_sha256=snapshot["tree_sha256"],
        artifacts=tuple(row["path"] for row in snapshot["artifacts"]),
    )


def _environment(module, runtime: Path):
    environment = module.VaBenchBashEnvironment(
        runtime,
        timeout_s=10,
        sandbox_backend="none",
        evas_command="",
        executable_feedback=False,
        submission_gate=_artifact_gate,
        candidate_artifacts=("model.va",),
    )
    environment.bind_submitted_exception(Submitted)
    return environment


def _action(
    action_id: str,
    command: str,
    candidate_tree_sha256: str,
) -> AgentAction:
    return AgentAction(
        action_id=action_id,
        tool_name="bash",
        arguments={"command": command},
        source_backend="mini-swe-agent-2.4.5",
        candidate_tree_sha256=candidate_tree_sha256,
    )


def _command_dispositions(environment) -> list[tuple[str, int]]:
    return [
        (str(row["kind"]), int(row["returncode"]))
        for row in environment.commands
    ]


def test_typed_bridge_matches_the_existing_mini_swe_execute_and_submission_path(
    tmp_path: Path,
) -> None:
    module = _load_module("mini_swe_vabench_compat_test", MINI_SWE_MODULE)
    result_protocol = _load_module(
        "result_protocol_compat_test",
        RESULT_PROTOCOL_MODULE,
    )
    direct_runtime = _runtime(tmp_path / "direct")
    bridge_runtime = _runtime(tmp_path / "bridge")
    direct = _environment(module, direct_runtime)
    legacy = _environment(module, bridge_runtime)
    bridge = MiniSweBashEnvironmentBridge(
        legacy_environment=legacy,
        task_payload={"message": "Generate model.va."},
        candidate_tree_sha256=lambda: _candidate_tree_sha256(
            bridge_runtime,
            result_protocol,
        ),
        freeze_submission=lambda: _freeze_submission(
            bridge_runtime,
            result_protocol,
        ),
        submitted_exception_types=(Submitted,),
    )
    capability = ToolRegistry(
        [mini_swe_bash_tool_descriptor(allowed_conditions=["Agentic-no-EVAS"])]
    ).authorize(
        "bash",
        condition_id="Agentic-no-EVAS",
        model_visible=True,
    )
    context = EpisodeContext(
        episode_id="episode-001",
        attempt_id="attempt-001",
        task_id="v4-001",
        condition="Agentic-no-EVAS",
        max_steps=2,
    )
    write_command = (
        "printf 'module model; endmodule\\n' > public/submission/model.va"
    )

    try:
        direct_output = direct.execute({"command": write_command})
        try:
            direct.execute({"command": "vabench-submit"})
        except Submitted:
            direct_submitted = True
        else:
            direct_submitted = False

        initial = bridge.start(context)
        write_step = bridge.step(
            _action("attempt-001/action-0001", write_command, initial.candidate_tree_sha256 or ""),
            capability,
        )
        assert not isinstance(write_step, type(None))
        terminal_step = bridge.step(
            _action(
                "attempt-001/action-0002",
                "vabench-submit",
                write_step.observation.candidate_tree_sha256 or "",  # type: ignore[union-attr]
            ),
            capability,
        )
        frozen = bridge.freeze_submission()
    finally:
        direct.close()
        bridge.close()

    assert direct_submitted is True
    assert direct_output["returncode"] == write_step.observation.payload["returncode"]  # type: ignore[union-attr]
    assert direct_output["output"] == write_step.observation.payload["output"]  # type: ignore[union-attr]
    assert terminal_step.done is True  # type: ignore[union-attr]
    assert terminal_step.terminal_reason == "submitted"  # type: ignore[union-attr]
    assert _command_dispositions(direct) == _command_dispositions(legacy) == [
        ("bash", 0),
        ("bash-submit", 0),
    ]
    assert _artifact_gate(direct_runtime)["artifact_sha256"] == _artifact_gate(
        bridge_runtime
    )["artifact_sha256"]
    assert frozen.tree_sha256 == terminal_step.observation.candidate_tree_sha256  # type: ignore[union-attr]
    assert frozen.artifacts == ("model.va",)
    frozen_bytes = (
        bridge_runtime / "evidence" / "final_submission" / "model.va"
    ).read_bytes()
    (bridge_runtime / "public" / "submission" / "model.va").write_text(
        "late mutation",
        encoding="utf-8",
    )
    assert (
        bridge_runtime / "evidence" / "final_submission" / "model.va"
    ).read_bytes() == frozen_bytes
    assert legacy.evas_invocations == []
    assert "never model-visible" not in str(write_step.observation.payload)  # type: ignore[union-attr]
