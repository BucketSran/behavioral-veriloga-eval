"""Public-example diagnostic, not a model benchmark or a new tool implementation."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
from pathlib import Path

import pytest

from runners.agent_harness import (
    EpisodeContext,
    EpisodeController,
    JsonlTrajectoryRecorder,
    ToolRegistry,
    read_trajectory,
    validate_trajectory_semantics,
)
from runners.agent_harness.backends.mini_swe import (
    MiniSweBashEnvironmentBridge,
    MiniSwePolicyBridge,
    mini_swe_bash_tool_descriptor,
)
from runners.agent_harness.tools.waveform_summary import summarize_waveform_bytes

ROOT = Path(__file__).resolve().parents[1]
OPERATIONS = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
EXAMPLE = ROOT / "examples/comparator/comparator"
GOOD_PREDICATE = "V(VINP) - V(VINN) - voffset > 0"
BAD_PREDICATE = "V(VINP) - V(VINN) - voffset < 0"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _faulty_source() -> str:
    source = (EXAMPLE / "cmp_ideal.va").read_text()
    assert source.count(GOOD_PREDICATE) == 1
    return source.replace(GOOD_PREDICATE, BAD_PREDICATE)


def test_public_comparator_fault_is_one_reversible_predicate_change():
    source = (EXAMPLE / "cmp_ideal.va").read_text()
    faulty = _faulty_source()
    assert faulty != source
    assert faulty.replace(BAD_PREDICATE, GOOD_PREDICATE) == source


def test_summary_statistics_do_not_determine_time_window_behavior():
    # Explicit illustrative CSV, not an EVAS output or a claim of equal real traces.
    before = summarize_waveform_bytes(b"time,out_p\n0,0\n1,1\n2,0\n3,0\n")
    after = summarize_waveform_bytes(b"time,out_p\n0,0\n1,0\n2,1\n3,0\n")
    assert before["status"] == after["status"] == "available"
    assert before["signals"] == after["signals"]
    assert before["source_sha256"] != after["source_sha256"]


def _simulation_command(stage: str) -> str:
    # Reuse the *public example* validator, deliberately declared as visible.
    check = (
        "import importlib.util; from pathlib import Path; "
        "s=importlib.util.spec_from_file_location('public_check',"
        "'public/task/validate_cmp_ideal.py'); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
        f"raise SystemExit(bool(m.validate_csv(Path('work/{stage}'))))"
    )
    return (
        f"evas simulate public/task/visible_test.scs -o work/{stage} --spectre-strict "
        f"> work/{stage}.log 2>&1\n"
        "sim_rc=$?\n"
        f"printf 'simulation_returncode=%s\\n' \"$sim_rc\"\n"
        f"cat work/{stage}.log\n"
        'if [ "$sim_rc" -ne 0 ]; then exit "$sim_rc"; fi\n'
        f"python -c {shlex.quote(check)}"
    )


@pytest.mark.skipif(
    os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1",
    reason="explicit free Docker/EVAS diagnostic opt-in required",
)
def test_public_comparator_debug_loop(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(OPERATIONS))
    from mini_swe_vabench import VaBenchBashEnvironment

    runtime = tmp_path / "public-debug-case"
    task = runtime / "public/task"
    task.mkdir(parents=True)
    candidate = runtime / "public/submission/cmp_ideal.va"
    candidate.parent.mkdir()
    candidate.write_text(_faulty_source())
    source_names = ("cmp_ideal.va", "tb_cmp_ideal.scs", "validate_cmp_ideal.py")
    source_hashes = {name: _sha((EXAMPLE / name).read_bytes()) for name in source_names}
    # Only relocate the include to the mutable candidate; keep stimulus bytes otherwise.
    deck = (EXAMPLE / "tb_cmp_ideal.scs").read_text()
    assert deck.count('"cmp_ideal.va"') == 1
    (task / "visible_test.scs").write_text(
        deck.replace('"cmp_ideal.va"', '"../submission/cmp_ideal.va"')
    )
    (task / "validate_cmp_ideal.py").write_bytes((EXAMPLE / "validate_cmp_ideal.py").read_bytes())

    def forbidden_terminal(*args, **kwargs):
        raise AssertionError("public diagnostic must not freeze or score")

    class NoFinalJudge:
        judge = staticmethod(forbidden_terminal)

    environment = VaBenchBashEnvironment(
        runtime, timeout_s=60, sandbox_backend="docker",
        evas_command=str(ROOT / ".venv/bin/evas"),
        docker_image="vabench-agent-runtime:0.8.7",
        candidate_artifacts=("cmp_ideal.va",), submission_gate=forbidden_terminal,
        structured_evas_feedback=True,
    )
    commands = [
        "evas --version",
        _simulation_command("faulty"),
        "sed -n '24,45p' public/submission/cmp_ideal.va",
        "sed -i " + shlex.quote(f"s/{BAD_PREDICATE}/{GOOD_PREDICATE}/")
        + " public/submission/cmp_ideal.va",
        _simulation_command("repaired"),
        "true",  # Receive the repaired public check before the declared diagnostic stop.
    ]
    observations = []

    def propose(observation):
        observations.append(observation.to_document())
        return {"tool_calls": [{
            "id": f"script-{len(observations)}", "type": "function",
            "function": {"name": "bash", "arguments": json.dumps({
                "command": commands[len(observations) - 1],
            })},
        }]}

    def candidate_hash():
        # Same path/file-digest convention as the production submission tree contract.
        from result_protocol import canonical_sha256
        return canonical_sha256([{"path": candidate.name, "sha256": _sha(candidate.read_bytes())}])

    initial_hash = candidate_hash()
    trajectory_path = runtime / "evidence/trajectory.jsonl"
    bridge = MiniSweBashEnvironmentBridge(
        legacy_environment=environment,
        task_payload={
            "scope": "public non-scored cmp_ideal diagnostic; scripted policy, no model",
            "expected_behavior": "VINP > VINN at rising CLK selects DCMPP; reversed input selects DCMPN",
            "public_validator": "public/task/validate_cmp_ideal.py",
        },
        candidate_tree_sha256=candidate_hash, freeze_submission=forbidden_terminal,
        submitted_exception_types=(),
    )
    controller = EpisodeController(
        policy=MiniSwePolicyBridge(propose=propose, action_id_prefix="public-debug"),
        environment=bridge,
        tool_registry=ToolRegistry([mini_swe_bash_tool_descriptor(allowed_conditions=["Agentic"])]),
        trajectory=JsonlTrajectoryRecorder(trajectory_path), final_judge=NoFinalJudge(),
    )
    try:
        result = controller.run(EpisodeContext(
            "public-comparator-debug", "scripted-1", "example-cmp-ideal", "Agentic", len(commands),
        ))
    finally:
        environment.close()
    (runtime / "evidence/policy-observations.json").write_text(json.dumps(observations, indent=2))
    assert result.primary_outcome == "budget_exhausted", result
    assert result.terminal_reason == "max_steps_exhausted"
    assert result.submission is None and result.final_judgment is None
    assert not result.incidents
    assert len(observations) == len(commands)
    failed = observations[2]
    repaired = observations[5]
    assert "evas-sim 0.8.7" in observations[1]["payload"]["output"]
    assert failed["status"] == "failed"
    assert failed["payload"]["returncode"] == 1
    assert "simulation_returncode=0" in failed["payload"]["output"]
    assert "FAIL: before swap" in failed["payload"]["output"]
    assert "diff=1.0000mV | dec=0" in failed["payload"]["output"]
    assert repaired["status"] == "succeeded"
    assert repaired["payload"]["returncode"] == 0
    assert "simulation_returncode=0" in repaired["payload"]["output"]
    assert "[CSV] All assertions passed." in repaired["payload"]["output"]
    assert "diff=1.0000mV | dec=1" in repaired["payload"]["output"]
    assert initial_hash == failed["candidate_tree_sha256"]
    assert initial_hash != repaired["candidate_tree_sha256"] == candidate_hash()
    assert candidate.read_bytes() == (EXAMPLE / "cmp_ideal.va").read_bytes()
    assert source_hashes == {name: _sha((EXAMPLE / name).read_bytes()) for name in source_names}

    events = read_trajectory(trajectory_path)
    assert validate_trajectory_semantics(events)
    assert not any(event["event_type"] in {"submission_frozen", "final_judgment_completed"} for event in events)
    observed = [event["payload"] for event in events if event["event_type"] == "environment_observed"]
    assert len(observed) == len(commands)
    # Controller records identity/payload hashes, not raw outputs; join them to
    # the next policy input (the initial task is not a tool-result event).
    for recorded, delivered in zip(observed[:-1], observations[1:], strict=True):
        for key in ("observation_id", "payload_sha256", "candidate_tree_sha256", "status"):
            assert recorded[key] == delivered[key]
    # Parser-only diagnostic over the same outputs; this is NOT a registered public-tool receipt.
    summaries = {
        stage: summarize_waveform_bytes((runtime / f"public/work/{stage}/tran.csv").read_bytes())
        for stage in ("faulty", "repaired")
    }
    assert all(summary["status"] == "available" for summary in summaries.values())
    for summary in summaries.values():
        output = next(signal for signal in summary["signals"] if signal["name"] == "out_p")
        assert output["min"] == 0 and output["max"] == pytest.approx(0.9)
    report = {
        "scope": "scripted public diagnostic; not a model, r53 score, or tool-utility result",
        "example_source_sha256": source_hashes,
        "harness_source_sha256": {
            str(path.relative_to(ROOT)): _sha(path.read_bytes()) for path in (
                Path(__file__), OPERATIONS / "mini_swe_vabench.py",
                ROOT / "runners/agent_harness/controller.py",
                ROOT / "runners/agent_harness/backends/mini_swe.py",
                ROOT / "runners/agent_harness/tools/waveform_summary.py",
            )
        },
        "docker_image_id": environment.docker_image_id,
        "commands": commands, "scripted_policy_calls": len(observations),
        "paid_requests": 0, "final_judge_calls": 0,
        "initial_candidate_tree_sha256": initial_hash,
        "repaired_candidate_tree_sha256": candidate_hash(),
        "trajectory_sha256": _sha(trajectory_path.read_bytes()),
        "policy_observations_sha256": _sha((runtime / "evidence/policy-observations.json").read_bytes()),
        "waveform_summaries": summaries,
        "diagnostic_stop": result.terminal_reason,
        "public_check_before_returncode": failed["payload"]["returncode"],
        "public_check_after_returncode": repaired["payload"]["returncode"],
    }
    (runtime / "evidence/case-report.json").write_text(json.dumps(report, indent=2))
