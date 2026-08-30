from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
sys.path.insert(0, str(CALIBRATION))

import run_native_evolution as evolution  # noqa: E402
from run_native_mini_swe import _backend_profile  # noqa: E402
from runners.agent_harness import FinalJudgment, backend_profile_sha256  # noqa: E402


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64
SHA_F = "f" * 64
SHA_1 = "1" * 64
SHA_2 = "2" * 64
REASONING_BACKEND_SHA = backend_profile_sha256(
    _backend_profile("native-reasoning", "native_tool_calls")
)


class _ScriptedReasoningClient:
    def __init__(self, model: str, commands: list[str]) -> None:
        self.model = model
        self.commands = list(commands)
        self.calls = 0

    def complete(self, messages, max_tokens, tools, *, timeout_s=None):
        del messages, max_tokens, tools, timeout_s
        command = self.commands.pop(0)
        self.calls += 1
        return {
            "id": f"response-{self.model}-{self.calls}",
            "model": self.model,
            "choices": [
                {
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": f"call-{self.model}-{self.calls}",
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
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }


class _Submitted(Exception):
    pass


class _FakeLegacyEnvironment:
    def __init__(self, runtime: Path, *, content: str, submitted: type[Exception]) -> None:
        self.runtime = runtime
        self.workspace = runtime / "public"
        self.candidate_artifacts = ("model.va",)
        self.submit_sentinel = self.workspace / "work/.tmp/submission-request"
        self.submit_sentinel.parent.mkdir(parents=True, exist_ok=True)
        (self.workspace / "submission").mkdir(parents=True, exist_ok=True)
        self.content = content
        self.submitted = submitted
        self.closed = False

    def execute(self, action: dict[str, Any], cwd: str = "") -> dict[str, Any]:
        del cwd
        command = action["command"]
        if command == "write":
            (self.workspace / "submission/model.va").write_text(self.content, encoding="utf-8")
            return {"output": "wrote", "returncode": 0, "exception_info": ""}
        if command == "vabench-submit":
            self.submit_sentinel.touch()
            raise self.submitted({"status": "Submitted"})
        raise AssertionError(command)

    def close(self) -> None:
        self.closed = True


def _profile(kind: str, *, campaign_config_sha256: str = SHA_F) -> dict[str, Any]:
    shared = {
        "benchmark_release": "benchmarkv4-r53",
        "benchmark_manifest_sha256": SHA_C,
        "checker_identity_sha256": SHA_D,
        "runtime_identity_sha256": SHA_E,
        "campaign_config_sha256": campaign_config_sha256,
    }
    if kind == "public":
        return {
            "schema_version": "vaevas-public-validation-profile-v1",
            "profile_id": "test-public",
            **shared,
            "evaluator": {"engine": "evas", "version": "0.8.7"},
            "evaluator_identity_sha256": SHA_A,
            "authority_phase": "in_episode",
            "visibility": "model_observation",
            "memory_policy": "episode_local_public_only",
            "input_scope": "candidate_tree",
            "allowed_feedback": ["runtime", "log_excerpt"],
            "candidate_binding_required": True,
            "may_select_candidates": True,
        }
    return {
        "schema_version": "vaevas-final-test-profile-v1",
        "profile_id": "test-final",
        **shared,
        "judge": {"engine": "evas", "version": "0.8.7"},
        "judge_identity_sha256": SHA_B,
        "command_signature_sha256": SHA_A,
        "authority_phase": "post_submission_freeze_only",
        "visibility": "trusted_only",
        "model_observation_allowed": False,
        "memory_entry_allowed": False,
        "candidate_selection_allowed": False,
        "repair_allowed": False,
        "input_scope": "frozen_submission_tree",
        "submission_binding_required": True,
        "score_sidecar_required": True,
        "structured_result_contract": {
            "schema_id": "vabench-trusted-replay-result-v1",
            "requires_structured_verdict": True,
        },
        "score_sidecar_contract": {
            "schema_id": "vaevas-score-sidecar-v1",
            "immutable": True,
            "binds_submission_tree": True,
        },
        "spectre_policy": {
            "required": False,
            "trigger": "conditional_evas_or_external_protocol_change",
            "spectre_judge_identity_sha256": None,
            "spectre_command_signature_sha256": None,
            "spectre_report_schema_id": None,
        },
    }


def _fake_ops(tmp_path: Path):
    final_calls: list[str] = []
    validation_calls: list[tuple[str, str]] = []
    exported: list[Path] = []
    environment_requests: list[dict[str, Any]] = []

    def export_runtime(cell, release, output, *, timeout_s):
        del cell, release, timeout_s
        exported.append(output)
        (output / "public/task").mkdir(parents=True, exist_ok=True)
        (output / "public/submission").mkdir(parents=True, exist_ok=True)
        (output / "evaluator").mkdir(parents=True, exist_ok=True)
        (output / "evaluator/score_policy.json").write_text(
            json.dumps({"candidate_artifacts": ["model.va"]}),
            encoding="utf-8",
        )

    def make_branch_environment(*, runtime, branch, submitted_exception, **_kwargs):
        environment_requests.append({"branch": branch.branch_id if branch else None, **_kwargs})
        content = "module good; endmodule" if branch and branch.branch_id == "branch-good" else "module bad; endmodule"
        return _FakeLegacyEnvironment(runtime, content=content, submitted=submitted_exception)

    def build_public_validation_profile(**_kwargs):
        return _profile(
            "public",
            campaign_config_sha256=str(_kwargs["campaign_config_sha256"]),
        )

    def build_final_test_profile(**_kwargs):
        return _profile(
            "final",
            campaign_config_sha256=str(_kwargs["campaign_config_sha256"]),
        )

    def public_validate(*, request, snapshot, candidate_store, context, **_kwargs):
        del candidate_store, context
        validation_calls.append((snapshot.tree_sha256, snapshot.artifacts[0]))
        sim_success = 1.0 if request.branch_id == "branch-good" else 0.0
        return evolution.PublicValidationResult(
            status="succeeded" if sim_success else "failed",
            sim_success=sim_success,
            event_sha256=SHA_2 if sim_success else SHA_B,
        )

    class FinalJudge:
        def __init__(self, runtime, context, profile, command, timeout_s, evas_command):
            del runtime, profile, command, timeout_s, evas_command
            self.context = context
            self.receipt = {"path": "evidence/score-sidecars/test.json", "sha256": SHA_A}

        def judge(self, submission):
            final_calls.append(submission.tree_sha256)
            return FinalJudgment("passed", "evas", 1.0, submission.tree_sha256)

    ops = evolution.NativeEvolutionOps(
        export_runtime=export_runtime,
        make_branch_environment=make_branch_environment,
        validate_public_candidate=public_validate,
        make_final_judge=FinalJudge,
        build_public_validation_profile=build_public_validation_profile,
        build_final_test_profile=build_final_test_profile,
        quiesce_environment=lambda **kwargs: None,
    )
    return ops, final_calls, validation_calls, exported, environment_requests


def test_native_evolution_runs_candidate_branches_then_scores_only_selected(tmp_path: Path):
    ops, final_calls, validation_calls, exported, environment_requests = _fake_ops(tmp_path)
    clients = {
        "branch-good": lambda: _ScriptedReasoningClient("provider/good", ["write", "vabench-submit"]),
        "branch-bad": lambda: _ScriptedReasoningClient("provider/bad", ["write", "vabench-submit"]),
    }

    run = evolution.run_native_evolution(
        cell={"cell_id": "cell-1", "task_id": "task-1", "mode": "G2"},
        release=tmp_path / "release",
        output_dir=tmp_path / "native-evolution",
        branches=[
            evolution.NativeEvolutionBranch(
                branch_id="branch-good",
                model_ref="provider/good",
                backend_profile_sha256=REASONING_BACKEND_SHA,
                client_factory=clients["branch-good"],
            ),
            evolution.NativeEvolutionBranch(
                branch_id="branch-bad",
                model_ref="provider/bad",
                backend_profile_sha256=REASONING_BACKEND_SHA,
                client_factory=clients["branch-bad"],
            ),
        ],
        public_validation_profile=None,
        final_test_profile=None,
        command="fake-final",
        evas_command="fake-evas",
        rounds=1,
        max_steps=2,
        budgets={"model_calls": 3, "tool_calls": 3, "public_validation_calls": 1},
        ops=ops,
        max_workers=2,
    )

    assert run.evolution_result.final_judgment is None
    assert run.selected_candidate["branch_id"] == "branch-good"
    assert final_calls == [run.selected_candidate["candidate_tree_sha256"]]
    assert len(validation_calls) == 2
    assert all("final" not in json.dumps(snapshot, sort_keys=True) for snapshot in run.evolution_result.memory_snapshots)
    assert (tmp_path / "native-evolution/evolution/selection.json").is_file()
    branch_final_snapshots = list(
        (tmp_path / "native-evolution/evolution/branches").glob(
            "round-*/*/runtime/evidence/final_submission"
        )
    )
    assert branch_final_snapshots == []
    assert (tmp_path / "native-evolution/final-runtime/evidence/final_submission/model.va").read_text() == "module good; endmodule"
    assert {path.name for path in exported} >= {"runtime", "final-runtime"}
    branch_envs = [row for row in environment_requests if row["branch"] is not None]
    assert {row["executable_feedback"] for row in branch_envs} == {False}
    assert {row["docker_image"] for row in branch_envs} == {"vabench-agent-runtime:0.8.7-no-evas"}


def test_failed_branch_keeps_usage_and_does_not_block_successful_candidate(tmp_path: Path):
    ops, final_calls, _validation_calls, _exported, _environment_requests = _fake_ops(tmp_path)
    clients = {
        "branch-good": lambda: _ScriptedReasoningClient("provider/good", ["write", "vabench-submit"]),
        "branch-fail": lambda: _ScriptedReasoningClient("provider/fail", ["unsupported"]),
    }

    run = evolution.run_native_evolution(
        cell={"cell_id": "cell-1", "task_id": "task-1", "mode": "G2"},
        release=tmp_path / "release",
        output_dir=tmp_path / "native-evolution",
        branches=[
            evolution.NativeEvolutionBranch(
                branch_id="branch-good",
                model_ref="provider/good",
                backend_profile_sha256=REASONING_BACKEND_SHA,
                client_factory=clients["branch-good"],
            ),
            evolution.NativeEvolutionBranch(
                branch_id="branch-fail",
                model_ref="provider/fail",
                backend_profile_sha256=REASONING_BACKEND_SHA,
                client_factory=clients["branch-fail"],
            ),
        ],
        public_validation_profile=None,
        final_test_profile=None,
        command="fake-final",
        evas_command="fake-evas",
        rounds=1,
        max_steps=2,
        budgets={"model_calls": 3, "tool_calls": 3, "public_validation_calls": 1},
        ops=ops,
        max_workers=2,
    )

    records = {record["branch_id"]: record for record in run.evolution_result.branch_records}
    assert records["branch-fail"]["status"] == "branch_failed"
    assert records["branch-fail"]["usage"] == {
        "model_calls": 1,
        "tool_calls": 1,
        "public_validation_calls": 0,
    }
    assert run.selected_candidate["branch_id"] == "branch-good"
    assert len(final_calls) == 1


def test_profiles_can_be_bootstrapped_and_prepared_final_runtime_is_reused(tmp_path: Path):
    ops, final_calls, _validation_calls, exported, environment_requests = _fake_ops(tmp_path)

    run = evolution.run_native_evolution(
        cell={"cell_id": "cell-1", "task_id": "task-1", "mode": "G2"},
        release=tmp_path / "release",
        output_dir=tmp_path / "native-evolution",
        branches=[
            evolution.NativeEvolutionBranch(
                branch_id="branch-good",
                model_ref="provider/good",
                backend_profile_sha256=REASONING_BACKEND_SHA,
                client_factory=lambda: _ScriptedReasoningClient(
                    "provider/good", ["write", "vabench-submit"]
                ),
            )
        ],
        public_validation_profile=None,
        final_test_profile=None,
        command="fake-final",
        evas_command="fake-evas",
        rounds=1,
        max_steps=2,
        budgets={"model_calls": 3, "tool_calls": 3, "public_validation_calls": 1},
        campaign_file_sha256=SHA_A,
        ops=ops,
        max_workers=1,
    )

    request = json.loads((tmp_path / "native-evolution/request.json").read_text(encoding="utf-8"))
    campaign_sha = request["campaign_config_sha256"]
    assert run.manifest["public_validation_profile_sha256"] == evolution.public_validation_profile_sha256(
        _profile("public", campaign_config_sha256=campaign_sha)
    )
    assert run.manifest["final_test_profile_sha256"] == evolution.final_test_profile_sha256(
        _profile("final", campaign_config_sha256=campaign_sha)
    )
    assert [path.name for path in exported].count("final-runtime") == 1
    assert any(row["branch"] is None and row["executable_feedback"] is True for row in environment_requests)
    assert final_calls == [run.selected_candidate["candidate_tree_sha256"]]


def test_model_identity_and_backend_profile_are_bound_to_roster(tmp_path: Path):
    ops, *_ = _fake_ops(tmp_path)

    with pytest.raises(RuntimeError, match="no selected candidate"):
        evolution.run_native_evolution(
            cell={"cell_id": "cell-1", "task_id": "task-1", "mode": "G2"},
            release=tmp_path / "release",
            output_dir=tmp_path / "native-evolution-model",
            branches=[
                evolution.NativeEvolutionBranch(
                    branch_id="branch-good",
                    model_ref="provider/good",
                    backend_profile_sha256=REASONING_BACKEND_SHA,
                    client_factory=lambda: _ScriptedReasoningClient(
                        "different-model", ["write", "vabench-submit"]
                    ),
                )
            ],
            public_validation_profile=None,
            final_test_profile=None,
            command="fake-final",
            evas_command="fake-evas",
            rounds=1,
            max_steps=2,
            budgets={"model_calls": 3, "tool_calls": 3, "public_validation_calls": 1},
            ops=ops,
            max_workers=1,
        )

    with pytest.raises(ValueError, match="backend_profile_sha256"):
        evolution.run_native_evolution(
            cell={"cell_id": "cell-1", "task_id": "task-1", "mode": "G2"},
            release=tmp_path / "release",
            output_dir=tmp_path / "native-evolution-backend",
            branches=[
                evolution.NativeEvolutionBranch(
                    branch_id="branch-good",
                    model_ref="provider/good",
                    backend_profile_sha256=SHA_A,
                    client_factory=lambda: _ScriptedReasoningClient(
                        "provider/good", ["write", "vabench-submit"]
                    ),
                )
            ],
            public_validation_profile=None,
            final_test_profile=None,
            command="fake-final",
            evas_command="fake-evas",
            rounds=1,
            max_steps=2,
            budgets={"model_calls": 3, "tool_calls": 3, "public_validation_calls": 1},
            ops=ops,
            max_workers=1,
        )


def test_zero_public_validation_budget_blocks_before_checker_call(tmp_path: Path):
    ops, final_calls, validation_calls, _exported, _environment_requests = _fake_ops(tmp_path)

    with pytest.raises(RuntimeError, match="no selected candidate"):
        evolution.run_native_evolution(
            cell={"cell_id": "cell-1", "task_id": "task-1", "mode": "G2"},
            release=tmp_path / "release",
            output_dir=tmp_path / "native-evolution",
            branches=[
                evolution.NativeEvolutionBranch(
                    branch_id="branch-good",
                    model_ref="provider/good",
                    backend_profile_sha256=REASONING_BACKEND_SHA,
                    client_factory=lambda: _ScriptedReasoningClient(
                        "provider/good", ["write", "vabench-submit"]
                    ),
                )
            ],
            public_validation_profile=None,
            final_test_profile=None,
            command="fake-final",
            evas_command="fake-evas",
            rounds=1,
            max_steps=2,
            budgets={"model_calls": 3, "tool_calls": 3, "public_validation_calls": 0},
            ops=ops,
            max_workers=1,
        )

    assert validation_calls == []
    assert final_calls == []


def _run_small(tmp_path, *, ops=None, commands=None):
    if ops is None:
        ops, *_ = _fake_ops(tmp_path)
    return evolution.run_native_evolution(
        cell={"cell_id": "cell-1", "task_id": "task-1", "mode": "G2"},
        release=tmp_path / "release", output_dir=tmp_path / "run",
        branches=[evolution.NativeEvolutionBranch(
            "branch-good", "provider/good", REASONING_BACKEND_SHA,
            lambda: _ScriptedReasoningClient("provider/good", commands or ["write", "vabench-submit"]),
        )], command="fake-final", evas_command="fake-evas", rounds=1, max_steps=2,
        budgets={"model_calls": 3, "tool_calls": 3, "public_validation_calls": 1}, ops=ops,
    )


def test_final_failure_keeps_denominator_all_costs_and_no_second_judge(tmp_path):
    ops, *_ = _fake_ops(tmp_path)
    calls = []
    class FailingJudge:
        def __init__(self, **kwargs):
            pass
        def judge(self, submission):
            calls.append(submission.tree_sha256)
            raise RuntimeError("final transport failed")
    with pytest.raises(RuntimeError, match="final transport failed"):
        _run_small(tmp_path, ops=replace(ops, make_final_judge=FailingJudge))
    doc = json.loads((tmp_path / "run/final-result.json").read_text())
    assert doc["denominator"] == {"scheduled_cells": 1, "scheduled_branches": 1, "observed_branches": 1}
    assert doc["status"] == "final_failed" and doc["final_judgment"] is None
    assert doc["selected_candidate"]["candidate_tree_sha256"] == calls[0]
    assert doc["all_branch_costs"]["model_calls"]["total"] == 2
    assert len(doc["branch_evidence"]) == 1 and len(calls) == 1
    assert doc["failure_taxonomy"]["primary_class"] == "infrastructure"
    assert doc["failure_taxonomy"]["responsibility"] == "system"
    assert doc["failure_phase"] == "final_replay"


def test_all_failed_branches_still_have_audit_and_actual_costs(tmp_path):
    with pytest.raises(RuntimeError, match="no selected candidate"):
        _run_small(tmp_path, commands=["unsupported"])
    doc = json.loads((tmp_path / "run/final-result.json").read_text())
    assert doc["denominator"]["observed_branches"] == 1
    assert doc["all_branch_costs"]["model_calls"]["total"] == 1
    assert doc["failure_taxonomy"]["responsibility"] == "undetermined"
    assert doc["failure_taxonomy"]["primary_class"] is None
    branch = tmp_path / "run/evolution/branches/round-0000/branch-good"
    audit = json.loads((branch / "branch-audit.json").read_text())
    assert audit["evidence"]["private-events.jsonl"]["sha256"] == evolution.hashlib.sha256((branch / "private-events.jsonl").read_bytes()).hexdigest()


def test_cleanup_incident_discards_candidate_and_closes_once(tmp_path):
    ops, final_calls, validation_calls, *_ = _fake_ops(tmp_path)
    closed = []
    original = ops.make_branch_environment
    def make(**kwargs):
        env = original(**kwargs)
        if kwargs["branch"] is not None:
            def close():
                closed.append("branch")
                raise RuntimeError("cleanup failed")
            env.close = close
        return env
    with pytest.raises(RuntimeError, match="no selected candidate"):
        _run_small(tmp_path, ops=replace(ops, make_branch_environment=make))
    assert closed == ["branch"]
    assert not final_calls and not validation_calls


def test_usage_never_clamps_observed_overrun_to_allowance():
    from types import SimpleNamespace
    usage = evolution._usage(
        recorded_client=SimpleNamespace(calls=4), recorder=SimpleNamespace(count=lambda _: 3),
        public_validation_calls=1, allowance={"model_calls": 1, "tool_calls": 1, "public_validation_calls": 1},
    )
    assert usage == {"model_calls": 4, "tool_calls": 3, "public_validation_calls": 1}


@pytest.mark.parametrize("phase", ["preflight", "public_profile", "final_profile"])
def test_bootstrap_failure_closes_public_environment(tmp_path, phase):
    ops, *_ = _fake_ops(tmp_path)
    closed = []
    make = ops.make_branch_environment
    def fail(**kwargs):
        raise RuntimeError("bootstrap failed")
    def environment(**kwargs):
        env = make(**kwargs)
        env.close = lambda: closed.append("closed")
        if phase == "preflight":
            env.preflight = fail
        return env
    ops = replace(ops, make_branch_environment=environment)
    if phase == "public_profile":
        ops = replace(ops, build_public_validation_profile=fail)
    if phase == "final_profile":
        ops = replace(ops, build_final_test_profile=fail)
    with pytest.raises(RuntimeError, match="bootstrap failed"):
        _run_small(tmp_path, ops=ops)
    assert closed == ["closed"]
    doc = json.loads((tmp_path / "run/final-result.json").read_text())
    assert doc["status"] == "setup_failed"
    assert doc["denominator"]["scheduled_cells"] == 1
    assert doc["denominator"]["observed_branches"] == 0
    assert doc["failure_taxonomy"]["primary_class"] == "infrastructure"
    assert doc["failure_taxonomy"]["responsibility"] == "system"
    assert doc["failure_phase"] == "setup"


def test_public_cleanup_failure_preserves_null_terminal_record(tmp_path):
    ops, final_calls, *_ = _fake_ops(tmp_path)
    make = ops.make_branch_environment
    def environment(**kwargs):
        env = make(**kwargs)
        if kwargs["branch"] is None:
            def close():
                raise RuntimeError("public cleanup failed")
            env.close = close
        return env
    with pytest.raises(RuntimeError, match="public cleanup failed"):
        _run_small(tmp_path, ops=replace(ops, make_branch_environment=environment))
    doc = json.loads((tmp_path / "run/final-result.json").read_text())
    assert doc["status"] == "public_cleanup_failed" and doc["final_judgment"] is None
    assert doc["all_branch_costs"]["model_calls"]["total"] == 2
    assert not final_calls
    assert doc["failure_taxonomy"]["primary_class"] == "infrastructure"
    assert doc["failure_phase"] == "public_cleanup"


def test_completed_evolution_keeps_candidate_verdict_and_declared_surface(tmp_path):
    ops, *_ = _fake_ops(tmp_path)
    class CandidateFailureJudge:
        def __init__(self, **kwargs):
            self.receipt = None
        def judge(self, submission):
            return FinalJudgment("compile_failure", "evas", 0.0, submission.tree_sha256)
    _run_small(tmp_path, ops=replace(ops, make_final_judge=CandidateFailureJudge))
    doc = json.loads((tmp_path / "run/final-result.json").read_text())
    config = json.loads((tmp_path / "run/request.json").read_text())["config"]
    assert doc["status"] == "completed" and doc["final_judgment"]["status"] == "compile_failure"
    assert doc["failure_taxonomy"]["primary_class"] == "compile"
    assert doc["failure_taxonomy"]["responsibility"] == "candidate"
    assert doc["failure_phase"] == "final_replay"
    assert doc["declared_information_surface"] == config["declared_information_surface"]
    assert doc["declared_information_surface"]["generation_export_arm"] == "Agent-No-EVAS"
    assert doc["declared_information_surface"]["information_parity_established"] is False


def test_missing_production_container_cannot_be_quiesced():
    with pytest.raises(RuntimeError, match="quiesce"):
        evolution._default_quiesce_environment(environment=object(), allow_insecure_test_sandbox=False)


def test_evolution_freezes_profiles_and_reasoning_source_before_calls(tmp_path):
    run = _run_small(tmp_path)
    public = json.loads((tmp_path / "run/public-validation-profile.json").read_text())
    final = json.loads((tmp_path / "run/final-test-profile.json").read_text())
    assert evolution.public_validation_profile_sha256(public) == run.manifest["public_validation_profile_sha256"]
    assert evolution.final_test_profile_sha256(final) == run.manifest["final_test_profile_sha256"]
    request = json.loads((tmp_path / "run/request.json").read_text())
    assert "runners/agent_harness/backends/reasoning.py" in request["config"]["source"]
    prepared = json.loads((tmp_path / "run/evolution/branches/round-0000/branch-good/branch-runtime.json").read_text())
    assert prepared["model_ref"] == "provider/good"
    assert prepared["executable_feedback"] is False
    assert "observed_image_id" in prepared


def test_public_candidate_install_failure_latches_authority(tmp_path, monkeypatch):
    from types import SimpleNamespace
    calls = []
    def fail(**kwargs):
        calls.append(1)
        raise ValueError("candidate install failed")
    monkeypatch.setattr(evolution, "_replace_submission_from_store", fail)
    validator = evolution._SharedPublicValidator(
        cell={}, release=tmp_path, runtime=tmp_path, profile={}, timeout_s=1,
        evas_command="evas", allow_insecure_test_sandbox=True,
        ops=evolution.NativeEvolutionOps(), environment=object(),
    )
    for _ in range(2):
        with pytest.raises(ValueError):
            validator.validate(request=None, snapshot=SimpleNamespace(artifacts=()),
                               candidate_store=tmp_path, context=None)
    assert calls == [1]
