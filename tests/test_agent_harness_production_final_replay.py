from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shlex
import sys
from types import SimpleNamespace

import pytest

from runners.agent_harness import EpisodeContext

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
sys.path.insert(0, str(CALIBRATION))

import run_campaign as runner  # noqa: E402
import final_replay  # noqa: E402
import score_campaign as scorer  # noqa: E402


@pytest.fixture
def replay_case(tmp_path):
    runtime = tmp_path / "runtime"
    submission = runtime / "public/submission"
    submission.mkdir(parents=True)
    (submission / "candidate.va").write_text("// public candidate\n")
    evaluator = runtime / "evaluator"
    evaluator.mkdir()
    (evaluator / "checker.py").write_text("# trusted checker fixture\n")
    (evaluator / "score_policy.json").write_text(
        json.dumps({"candidate_artifacts": ["candidate.va"]})
    )
    frozen = runner.RESULT_PROTOCOL.snapshot_submission(
        runtime,
        {
            "passed": True,
            "expected_artifacts": ["candidate.va"],
            "diagnostics": [],
        },
    )
    executable = tmp_path / "evas"
    executable.write_text("#!/bin/sh\necho 'evas-sim 0.8.7 (test double)'\n")
    executable.chmod(0o755)
    adapter = tmp_path / "judge.py"
    adapter.write_text(
        "import os, json\nfrom pathlib import Path\n"
        "root = Path(os.environ['VABENCH_RUNTIME_DIR'])\n"
        "(root / 'judge-called').touch()\n"
        "assert Path(os.environ['VABENCH_SUBMISSION_DIR']) == root / 'evidence/final_submission'\n"
        "Path(os.environ['VABENCH_TRUSTED_REPLAY_RESULT']).write_text(json.dumps({'status': 'behavior_failure'}))\n"
    )
    command = shlex.join([sys.executable, str(adapter)])
    context = EpisodeContext(
        episode_id="cell-001",
        attempt_id="attempt-001",
        task_id="v4-001",
        condition="OneShot",
        max_steps=1,
    )
    profile = final_replay.build_final_test_profile(
        runtime=runtime,
        release=runner.DEFAULT_RELEASE,
        campaign_config_sha256="a" * 64,
        command=command,
        timeout_s=10,
        evas_command=str(executable),
    )
    return runtime, frozen, executable, adapter, command, context, profile


def run_bound(case):
    runtime, frozen, executable, _, command, context, profile = case
    return runner.run_trusted_replay(
        runtime,
        command,
        10,
        str(executable),
        frozen,
        final_test_profile=profile,
        episode_context=context,
    )


def test_production_replay_writes_profile_bound_immutable_receipt(replay_case):
    runtime, frozen, _, _, _, _, profile = replay_case
    before = (runtime / "public/submission/candidate.va").read_bytes()

    replay = run_bound(replay_case)

    assert replay["status"] == "behavior_failure"
    receipt = replay["score_sidecar_receipt"]
    path = runtime / receipt["path"]
    assert path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == receipt["sha256"]
    sidecar = json.loads(path.read_text())
    assert sidecar["structured_result"] == {"status": "behavior_failure", "score": 0.0}
    assert sidecar["submission_tree_sha256"] == frozen["tree_sha256"]
    assert sidecar["score_authority"] == "development_only"
    assert receipt["final_profile_sha256"] == final_replay.final_test_profile_sha256(
        profile
    )
    assert replay["final_test_profile"] == profile
    assert (runtime / "public/submission/candidate.va").read_bytes() == before
    assert path.stat().st_mode & 0o222 == 0


@pytest.mark.parametrize("target", ["candidate", "checker", "command", "profile"])
def test_bound_replay_rejects_drift_before_judge_execution(replay_case, target):
    runtime, _, _, adapter, _, _, profile = replay_case
    if target == "profile":
        profile["judge_identity_sha256"] = "b" * 64
    else:
        path = {
            "candidate": runtime / "evidence/final_submission/candidate.va",
            "checker": runtime / "evaluator/checker.py",
            "command": adapter,
        }[target]
        path.chmod(0o644)
        path.write_text(path.read_text() + "\n# drift\n")
    with pytest.raises(ValueError, match="drift"):
        run_bound(replay_case)
    assert not (runtime / "judge-called").exists()
    assert not list(runtime.rglob("score-sidecars/*.json"))


def test_bound_replay_is_persistently_single_use_and_blocks_legacy_bypass(replay_case):
    runtime, frozen, executable, _, command, _, _ = replay_case
    run_bound(replay_case)
    called_at = (runtime / "judge-called").stat().st_mtime_ns
    output = (runtime / "evidence/trusted_replay_result.json").read_bytes()
    with pytest.raises(RuntimeError, match="already|reserved"):
        run_bound(replay_case)
    with pytest.raises(RuntimeError, match="already|reserved"):
        runner.run_trusted_replay(runtime, command, 10, str(executable), frozen)
    assert (runtime / "judge-called").stat().st_mtime_ns == called_at
    assert (runtime / "evidence/trusted_replay_result.json").read_bytes() == output


@pytest.mark.parametrize("target", ["candidate", "checker", "command"])
def test_bound_replay_rejects_post_execution_drift_and_stays_reserved(
    replay_case, monkeypatch, target
):
    runtime, _, _, adapter, *_ = replay_case
    execute = runner._run_trusted_replay

    def execute_then_drift(*args):
        replay = execute(*args)
        path = {
            "candidate": runtime / "evidence/final_submission/candidate.va",
            "checker": runtime / "evaluator/checker.py",
            "command": adapter,
        }[target]
        path.chmod(0o644)
        path.write_text(path.read_text() + "\n# post-execution drift\n")
        return replay

    monkeypatch.setattr(runner, "_run_trusted_replay", execute_then_drift)
    with pytest.raises(ValueError, match="drift"):
        run_bound(replay_case)
    assert (runtime / "judge-called").exists()
    assert not list(runtime.rglob("score-sidecars/*.json"))
    with pytest.raises(RuntimeError, match="already|reserved"):
        run_bound(replay_case)


@pytest.mark.parametrize("failure", ["missing_json", "malformed_json", "watchdog"])
def test_bound_replay_infrastructure_never_becomes_candidate_zero(replay_case, failure):
    import jsonschema

    runtime, frozen, executable, adapter, command, context, _ = replay_case
    adapter.write_text(
        {
            "missing_json": "pass\n",
            "malformed_json": "import os\nfrom pathlib import Path\nPath(os.environ['VABENCH_TRUSTED_REPLAY_RESULT']).write_text('bad json')\n",
            "watchdog": "import time\ntime.sleep(10)\n",
        }[failure]
    )
    timeout = 0.05 if failure == "watchdog" else 10
    profile = final_replay.build_final_test_profile(
        runtime=runtime,
        release=runner.DEFAULT_RELEASE,
        campaign_config_sha256="a" * 64,
        command=command,
        timeout_s=timeout,
        evas_command=str(executable),
    )
    replay = runner.run_trusted_replay(
        runtime,
        command,
        timeout,
        str(executable),
        frozen,
        final_test_profile=profile,
        episode_context=context,
    )
    receipt = replay["score_sidecar_receipt"]
    sidecar = json.loads((runtime / receipt["path"]).read_text())
    assert replay["status"] == "infrastructure_failure"
    assert sidecar["structured_result"] == {
        "status": "infrastructure_failure",
        "score": None,
    }
    runner.RESULT_PROTOCOL.validate_adapter_failure_taxonomy(
        replay["status"], replay["failure_taxonomy"]
    )
    result = runner.RESULT_PROTOCOL.build_experiment_result(
        cell={"cell_id": "cell-001", "task_id": "v4-001", "mode": "G0"},
        model_status="completed",
        messages=[],
        artifact_gate={},
        runtime=runtime,
        replay=replay,
        final_submission=frozen,
    )
    jsonschema.validate(
        result,
        json.loads(
            (ROOT / "schemas/vabench-experiment-result.schema.json").read_text()
        ),
    )
    with pytest.raises(RuntimeError, match="already|reserved"):
        run_bound(replay_case)


def test_bound_final_prevents_generation_reentry_even_without_campaign_result(
    replay_case,
):
    runtime = replay_case[0]
    run_bound(replay_case)
    args = SimpleNamespace(output=runtime.parent, resume=True)
    with pytest.raises(RuntimeError, match="final.*reserved|final.*started"):
        runner.run_cell({"cell_id": runtime.name}, args, None)


def test_bound_production_replay_preserves_experiment_schema(replay_case):
    import jsonschema

    runtime, frozen, *_ = replay_case
    replay = run_bound(replay_case)
    result = runner.RESULT_PROTOCOL.build_experiment_result(
        cell={"cell_id": "cell-001", "task_id": "v4-001", "mode": "G0"},
        model_status="completed",
        messages=[],
        artifact_gate={},
        runtime=runtime,
        replay=replay,
        final_submission=frozen,
    )
    jsonschema.validate(
        result,
        json.loads(
            (ROOT / "schemas/vabench-experiment-result.schema.json").read_text()
        ),
    )


def test_scorer_bound_path_returns_receipt_without_changing_generation_evidence(
    replay_case,
):
    runtime, _, executable, _, command, context, profile = replay_case
    result_path = runtime / "evidence/campaign_result.json"
    result_path.write_text(
        json.dumps(
            {
                "cell": {
                    "cell_id": context.episode_id,
                    "task_id": context.task_id,
                    "family_id": "fixture",
                    "form": "dut",
                    "mode": "G0",
                    "experimental_arm": "OneShot",
                },
                "status": "submitted",
                "events": [],
            }
        )
    )
    checkpoint = runtime / "evidence/conversation_checkpoint.json"
    checkpoint.write_text(
        json.dumps({"messages": [{"role": "assistant", "content": "public"}]})
    )
    before = (result_path.read_bytes(), checkpoint.read_bytes())
    row = scorer.evaluate_cell(
        result_path,
        command,
        10,
        str(executable),
        write_back=False,
        final_test_profile=profile,
        episode_context=context,
    )
    assert row["judge_status"] == "behavior_failure"
    assert row["trusted_replay"]["score_sidecar_receipt"]["task_id"] == context.task_id
    assert (result_path.read_bytes(), checkpoint.read_bytes()) == before
    with pytest.raises(ValueError, match="authority"):
        scorer.summarize([row], "final_spectre")


def test_relative_judge_script_is_hashed_from_execution_cwd(replay_case, monkeypatch):
    runtime, frozen, executable, adapter, _, context, _ = replay_case
    monkeypatch.setattr(runner, "REPO", adapter.parent)
    monkeypatch.setattr(final_replay, "REPO", adapter.parent)
    command = shlex.join([sys.executable, adapter.name])
    profile = final_replay.build_final_test_profile(
        runtime=runtime,
        release=runner.DEFAULT_RELEASE,
        campaign_config_sha256="a" * 64,
        command=command,
        timeout_s=10,
        evas_command=str(executable),
    )
    adapter.write_text(adapter.read_text() + "\n# changed after profile freeze\n")
    with pytest.raises(ValueError, match="drift"):
        runner.run_trusted_replay(
            runtime,
            command,
            10,
            str(executable),
            frozen,
            final_test_profile=profile,
            episode_context=context,
        )
    assert not (runtime / "judge-called").exists()
