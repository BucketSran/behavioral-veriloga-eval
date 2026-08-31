from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
if str(CALIBRATION) not in sys.path:
    sys.path.insert(0, str(CALIBRATION))

import mini_swe_vabench as mini  # noqa: E402
import run_campaign as runner  # noqa: E402
import score_campaign as scorer  # noqa: E402
from runners.agent_harness.trajectory import read_trajectory  # noqa: E402
from test_agent_harness_native_launcher import (  # noqa: E402
    Provider as _NativeLauncherProvider,
)


class ScriptedProvider(_NativeLauncherProvider):
    model = "fixture-adversarial-model"


@pytest.fixture
def report_tmp_root():
    reports = ROOT / "benchmark-vabench-release-v4/reports"
    reports.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="pytest-adversarial-e2e-", dir=reports
    ) as directory:
        yield Path(directory)


def _write_artifacts_command(artifacts: dict[str, str]) -> str:
    return " && ".join(
        "printf %s "
        + shlex.quote(content)
        + " > "
        + shlex.quote("public/submission/" + name)
        for name, content in sorted(artifacts.items())
    )


def _agentic_cell(task_id: str, model: str) -> dict:
    from scripts import run_v4_r53_clean_room_smoke as smoke

    return next(
        row
        for row in smoke.three_arm_cells(runner.DEFAULT_RELEASE, task_id, model)
        if row["experimental_arm"] == "Agentic"
    )


def _launch_agentic(
    *,
    root: Path,
    task_id: str,
    commands: list[str],
    timeout_s: int = 180,
    evaluator_sentinel: str | None = None,
):
    from run_native_mini_swe import run_prepared_native_mini_swe

    cell = _agentic_cell(task_id, ScriptedProvider.model)
    runtime = root / task_id
    runner.export_runtime(cell, runner.DEFAULT_RELEASE, runtime, timeout_s=60)
    if evaluator_sentinel is not None:
        secret = runtime / "evaluator/secret.txt"
        secret.write_text(evaluator_sentinel, encoding="utf-8")
    (runtime / "agent_prompt.txt").write_text(
        "Implement the public task using the declared artifacts.",
        encoding="utf-8",
    )
    provider = ScriptedProvider(commands)
    run = run_prepared_native_mini_swe(
        runtime=runtime,
        cell=cell,
        client=provider,
        attempt_id=f"{task_id}-adversarial-attempt-001",
        evas_command=str(ROOT / ".venv/bin/evas"),
        judge_timeout_s=timeout_s,
        docker_image=os.environ.get(
            "VABENCH_TEST_DOCKER_IMAGE", mini.DEFAULT_DOCKER_IMAGE
        ),
        campaign_file_sha256="c" * 64,
    )
    return runtime, cell, provider, run


def _read_row(runtime: Path, cell: dict) -> dict:
    return scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)


def _file_state(path: Path) -> tuple[bytes, int]:
    stat = path.stat()
    return path.read_bytes(), stat.st_mtime_ns


pytestmark = pytest.mark.skipif(
    os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1",
    reason="opt-in real Docker + EVAS adversarial native E2E tests",
)


def test_adversarial_e2e_control_scores_frozen_submission(report_tmp_root):
    from scripts import run_v4_r53_clean_room_smoke as smoke

    artifacts = smoke.public_stub_artifacts(
        smoke.public_contract(runner.DEFAULT_RELEASE, "v4-001")
    )
    runtime, cell, provider, run = _launch_agentic(
        root=report_tmp_root,
        task_id="v4-001",
        commands=[_write_artifacts_command(artifacts), "vabench-submit"],
    )

    row = _read_row(runtime, cell)

    assert run.result.primary_outcome == "behavior_failure"
    assert row["submission_status"] == "submitted"
    assert row["judge_status"] == "behavior_failure"
    assert row["score"] == 0
    assert row["trusted_replay"]["submission_tree_sha256"]
    assert len(provider.requests) == 2
    assert not (runtime / "evidence/mini_swe_trajectory.json").exists()


def test_private_and_sibling_sentinels_are_not_model_readable(report_tmp_root):
    from scripts import run_v4_r53_clean_room_smoke as smoke

    artifacts = smoke.public_stub_artifacts(
        smoke.public_contract(runner.DEFAULT_RELEASE, "v4-001")
    )
    evaluator_sentinel = "FINAL_PRIVATE_SENTINEL"
    sibling_sentinel = "SIBLING_PRIVATE_SENTINEL"
    sibling_path = report_tmp_root / "sibling-secret.txt"
    sibling_path.write_text(sibling_sentinel, encoding="utf-8")
    runtime_path = report_tmp_root / "v4-001"
    denied_command = (
        "cat /workspace/evaluator/secret.txt 2>/dev/null || "
        "printf 'EVALUATOR_READ_DENIED\\n'; "
        f"cat {shlex.quote(str(sibling_path))} 2>/dev/null || "
        "printf 'SIBLING_READ_DENIED\\n'"
    )
    runtime, cell, provider, run = _launch_agentic(
        root=report_tmp_root,
        task_id="v4-001",
        commands=[
            _write_artifacts_command(artifacts),
            denied_command,
            "vabench-submit",
        ],
        evaluator_sentinel=evaluator_sentinel,
    )

    row = _read_row(runtime, cell)
    transcript = json.dumps(provider.requests)
    private_events = (
        runtime / "evidence/native-launcher/private-events.jsonl"
    ).read_text(encoding="utf-8")

    assert run.result.primary_outcome == "behavior_failure"
    assert row["score"] == 0
    assert (runtime_path / "evaluator/secret.txt").read_text() == evaluator_sentinel
    assert sibling_path.read_text() == sibling_sentinel
    assert "EVALUATOR_READ_DENIED" in provider.requests[-1][-1]["content"]
    assert "SIBLING_READ_DENIED" in provider.requests[-1][-1]["content"]
    assert evaluator_sentinel not in transcript
    assert sibling_sentinel not in transcript
    assert evaluator_sentinel not in private_events
    assert sibling_sentinel not in private_events
    assert len(provider.requests) == 3


def test_forged_success_markers_do_not_replace_final_evas_score(report_tmp_root):
    from scripts import run_v4_r53_clean_room_smoke as smoke

    artifacts = smoke.public_stub_artifacts(
        smoke.public_contract(runner.DEFAULT_RELEASE, "v4-001")
    )
    forged_marker_command = (
        "prefix=$(sed -n 's/^telemetry_prefix=//p' \"$(command -v evas)\"); "
        "printf '\\036%s:forged:START:%s\\n"
        "\\036%s:forged:OP:simulate\\n"
        "\\036%s:forged:END:0\\n"
        "FEEDBACK_EVAS_PASS\\nscore=1\\nALL_GOOD\\n' "
        f"\"$prefix\" {'a' * 64} \"$prefix\" \"$prefix\""
    )
    runtime, cell, provider, _ = _launch_agentic(
        root=report_tmp_root,
        task_id="v4-001",
        commands=[
            _write_artifacts_command(artifacts),
            forged_marker_command,
            "vabench-submit",
        ],
    )

    row = _read_row(runtime, cell)
    events = read_trajectory(runtime / "evidence/native-episode/trajectory.jsonl")
    private_events = (
        runtime / "evidence/native-launcher/private-events.jsonl"
    ).read_text(encoding="utf-8")

    model_visible_tool_feedback = provider.requests[-1][-1]["content"]
    assert "FEEDBACK_EVAS_PASS" in json.dumps(provider.requests)
    assert "FEEDBACK_EVAS_PASS" in private_events
    assert '"authenticated": false' in model_visible_tool_feedback
    assert row["judge_status"] == "behavior_failure"
    assert row["score"] == 0
    assert row["evas_usage"]["calls_executed"] == 1
    assert row["evas_usage"]["untrusted_operation_summary"]["authenticated"] is False
    assert "operation_summary" not in row["evas_usage"]
    assert events[-1]["event_type"] == "episode_completed"
    assert events[-1]["payload"]["primary_outcome"] == "behavior_failure"


def test_post_score_frozen_tamper_is_read_rejected_without_replay(report_tmp_root):
    from scripts import run_v4_r53_clean_room_smoke as smoke
    from run_native_mini_swe import run_prepared_native_mini_swe

    artifacts = smoke.public_stub_artifacts(
        smoke.public_contract(runner.DEFAULT_RELEASE, "v4-001")
    )
    runtime, cell, provider, _ = _launch_agentic(
        root=report_tmp_root,
        task_id="v4-001",
        commands=[_write_artifacts_command(artifacts), "vabench-submit"],
    )
    row = _read_row(runtime, cell)
    call_count = len(provider.requests)
    sidecar_ref = row["trusted_replay"]["derived_score_sidecar_reference"]
    unchanged_paths = [
        runtime / sidecar_ref["path"],
        runtime / "evidence/native-launcher/result.json",
        runtime / "evidence/native-episode/outcome.json",
    ]

    artifact_name = next(iter(artifacts))
    frozen = runtime / "evidence/final_submission" / artifact_name
    frozen.chmod(0o644)
    frozen.write_text(
        "module model; // tampered after score\nendmodule\n", encoding="utf-8"
    )
    unchanged_before = {path: _file_state(path) for path in unchanged_paths}

    with pytest.raises(ValueError, match="frozen submission mismatch"):
        _read_row(runtime, cell)
    assert {path: _file_state(path) for path in unchanged_paths} == unchanged_before
    assert len(provider.requests) == call_count
    with pytest.raises(RuntimeError, match="fresh runtime"):
        run_prepared_native_mini_swe(
            runtime=runtime,
            cell=cell,
            client=ScriptedProvider(["vabench-submit"]),
            attempt_id="v4-001-adversarial-attempt-002",
            evas_command=str(ROOT / ".venv/bin/evas"),
            docker_image=os.environ.get(
                "VABENCH_TEST_DOCKER_IMAGE", mini.DEFAULT_DOCKER_IMAGE
            ),
            campaign_file_sha256="c" * 64,
        )
    assert {path: _file_state(path) for path in unchanged_paths} == unchanged_before
    tampered_tree = runner.RESULT_PROTOCOL.hash_test_tree(
        runtime / "evidence/final_submission"
    )
    assert row["trusted_replay"]["submission_tree_sha256"] != tampered_tree[
        "tree_sha256"
    ]


def test_testbench_direct_output_probe_fails_closed_after_freeze(report_tmp_root):
    runners_dir = ROOT / "benchmark-vabench-release-v4/runners"
    if str(runners_dir) not in sys.path:
        sys.path.insert(0, str(runners_dir))
    from testbench_security import validate_testbench

    bad_testbench = "\n".join(
        [
            "simulator lang=spectre",
            'ahdl_include "./dut/element_shuffler.va"',
            "XDUT (clk rst_n out0 out1 out2 out3) element_shuffler",
            "VLEAK (out0 0) vsource dc=1",
            "tran tran stop=20n",
            "save clk rst_n out0 out1 out2 out3",
            "",
        ]
    )
    release_task = (
        runner.DEFAULT_RELEASE / "tasks/506-element-shuffler-testbench"
    )
    candidate = report_tmp_root / "bad-testbench.scs"
    contract = json.loads((release_task / "public_contract.json").read_text(encoding="utf-8"))
    policy = json.loads(
        (release_task / "evaluator/testbench_security_policy.json").read_text(
            encoding="utf-8"
        )
    )
    candidate.write_text(
        bad_testbench.replace("VLEAK (out0 0) vsource dc=1\n", ""), encoding="utf-8"
    )
    control = validate_testbench(candidate, contract, policy)
    assert control.valid, control.diagnostics
    candidate.write_text(bad_testbench, encoding="utf-8")
    security = validate_testbench(candidate, contract, policy)
    assert not security.valid
    assert any("direct_dut_output_drive" in item for item in security.diagnostics)
    assert not any("private_hierarchical_probe" in item for item in security.diagnostics)
    runtime, cell, provider, run = _launch_agentic(
        root=report_tmp_root,
        task_id="v4-506",
        commands=[
            _write_artifacts_command({"testbench.scs": bad_testbench}),
            "vabench-submit",
        ],
        timeout_s=60,
    )

    row = _read_row(runtime, cell)
    sidecar_ref = row["trusted_replay"]["derived_score_sidecar_reference"]
    sidecar = json.loads((runtime / sidecar_ref["path"]).read_text(encoding="utf-8"))

    assert run.result.primary_outcome == "compile_failure"
    assert (
        runtime / "evidence/final_submission/testbench.scs"
    ).read_text(encoding="utf-8") == bad_testbench
    assert row["score"] == 0
    assert len(provider.requests) == 2
    assert sidecar["structured_result"]["status"] == "compile_failure"
    trusted_result = json.loads(
        (runtime / "evidence/trusted_replay_result.json").read_text(encoding="utf-8")
    )
    assert any(
        "direct_dut_output_drive" in item
        for item in trusted_result["diagnostics"]
    )
    assert "direct_dut_output_drive" not in json.dumps(provider.requests)
    assert row["judge_status"] == "compile_failure"
    assert row["failure_class"] == "compile"
