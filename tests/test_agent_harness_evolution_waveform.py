from __future__ import annotations

import hashlib
import json
import sys
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
sys.path.insert(0, str(CALIBRATION))

import run_native_evolution as evolution  # noqa: E402
from runners.agent_harness import (  # noqa: E402
    FinalJudgment,
    backend_profile_sha256,
    profile_input_identity_sha256,
    public_validation_profile_sha256,
)
from run_native_mini_swe import _backend_profile  # noqa: E402


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64
IMAGE_ID = "sha256:" + "9" * 64
REASONING_BACKEND_SHA = backend_profile_sha256(
    _backend_profile("native-reasoning", "native_tool_calls")
)


def _sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


class _ScriptedReasoningClient:
    def __init__(self, model: str, commands: list[str]) -> None:
        self.model = model
        self.commands = list(commands)
        self.calls = 0

    def complete(self, messages, max_tokens, tools, *, timeout_s=None):
        del messages, max_tokens, tools, timeout_s
        self.calls += 1
        command = self.commands.pop(0)
        return {
            "id": f"response-{self.calls}",
            "model": self.model,
            "choices": [{
                "finish_reason": "tool_calls",
                "message": {"role": "assistant", "tool_calls": [{
                    "id": f"call-{self.calls}",
                    "type": "function",
                    "function": {
                        "name": "bash",
                        "arguments": json.dumps({"command": command}),
                    },
                }]},
            }],
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }


class _FakeLegacyEnvironment:
    def __init__(self, runtime: Path, *, submitted: type[Exception], requests: list[dict[str, Any]], **kwargs) -> None:
        self.runtime = runtime
        self.workspace = runtime / "public"
        self.candidate_artifacts = ("model.va",)
        self.submit_sentinel = self.workspace / "work/.tmp/submission-request"
        self.submit_sentinel.parent.mkdir(parents=True, exist_ok=True)
        (self.workspace / "submission").mkdir(parents=True, exist_ok=True)
        self.submitted = submitted
        self.requests = requests
        self.requests.append(kwargs)

    def preflight(self) -> None:
        return None

    def execute(self, action: dict[str, Any], cwd: str = "") -> dict[str, Any]:
        del cwd
        command = action["command"]
        if command == "write":
            (self.workspace / "submission/model.va").write_text("module wave; endmodule\n", encoding="utf-8")
            return {"output": "wrote", "returncode": 0, "exception_info": ""}
        if command == "vabench-submit":
            self.submit_sentinel.touch()
            raise self.submitted({"status": "Submitted"})
        raise AssertionError(command)

    def close(self) -> None:
        return None


def _public_profile(*, campaign_config_sha256: str) -> dict[str, Any]:
    return {
        "schema_version": "vaevas-public-validation-profile-v1",
        "profile_id": "r53/evas-0.8.7-isolated-public-waveform",
        "benchmark_release": "benchmarkv4-r53",
        "benchmark_manifest_sha256": SHA_A,
        "checker_identity_sha256": SHA_B,
        "runtime_identity_sha256": SHA_C,
        "campaign_config_sha256": campaign_config_sha256,
        "evaluator": {"engine": "evas", "version": "0.8.7"},
        "evaluator_identity_sha256": SHA_D,
        "authority_phase": "in_episode",
        "visibility": "model_observation",
        "memory_policy": "episode_local_public_only",
        "input_scope": "candidate_tree",
        "allowed_feedback": ["runtime", "waveform_summary"],
        "candidate_binding_required": True,
        "may_select_candidates": True,
    }


def _waveform_public_profile(*, runtime: Path, campaign_config_sha256: str, image_id: str) -> dict[str, Any]:
    task = evolution.public_waveform_runtime._read_tree(runtime / "public/task")
    command, scope = evolution.public_validation.public_execution_contract(json.loads(task["evas_runtime.json"]))
    command = command.replace("evas simulate ", "/usr/local/bin/evas simulate ")
    public_task_sha = evolution.public_waveform_runtime._tree_sha256(task)
    return {
        **_public_profile(campaign_config_sha256=campaign_config_sha256),
        "checker_identity_sha256": evolution._canonical_sha256({
            "scope": scope,
            "public_tree_sha256": public_task_sha,
            "command": command,
            "candidate_artifacts": evolution.runner.expected_candidate_artifacts(runtime),
        }),
        "evaluator_identity_sha256": evolution._canonical_sha256({
            "image_id": image_id,
            "executable": "/usr/local/bin/evas",
            "version": "0.8.7",
        }),
    }


def _waveform_public_input(runtime: Path) -> tuple[str, str, str]:
    task = evolution.public_waveform_runtime._read_tree(runtime / "public/task")
    command, scope = evolution.public_validation.public_execution_contract(json.loads(task["evas_runtime.json"]))
    command = command.replace("evas simulate ", "/usr/local/bin/evas simulate ")
    return hashlib.sha256(command.encode()).hexdigest(), evolution.public_waveform_runtime._tree_sha256(task), scope


def _final_profile(*, campaign_config_sha256: str) -> dict[str, Any]:
    return {
        "schema_version": "vaevas-final-test-profile-v1",
        "profile_id": "test-final",
        "benchmark_release": "benchmarkv4-r53",
        "benchmark_manifest_sha256": SHA_A,
        "checker_identity_sha256": SHA_B,
        "runtime_identity_sha256": SHA_C,
        "campaign_config_sha256": campaign_config_sha256,
        "judge": {"engine": "evas", "version": "0.8.7"},
        "judge_identity_sha256": SHA_D,
        "command_signature_sha256": SHA_E,
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


def _ops(tmp_path: Path):
    final_calls: list[str] = []
    environment_requests: list[dict[str, Any]] = []

    def export_runtime(cell, release, output, *, timeout_s):
        del timeout_s
        output.mkdir(parents=True, exist_ok=True)
        release.mkdir(parents=True, exist_ok=True)
        if not (release / "MANIFEST.json").exists():
            (release / "MANIFEST.json").write_text(
                json.dumps({"release_revision": "r53", "runtime_requirements": {"evas_version": "0.8.7"}}),
                encoding="utf-8",
            )
        (output / "public/task").mkdir(parents=True, exist_ok=True)
        (output / "public/submission").mkdir(parents=True, exist_ok=True)
        (output / "public/task/evas_runtime.json").write_text(
            json.dumps({
                "schema_version": "r53-direct-evas-runtime-v2",
                "working_directory": "runtime_package_root",
                "command": "evas simulate public/task/visible_test.scs -o /tmp/vabench-visible/evas-output --spectre-strict",
            }),
            encoding="utf-8",
        )
        (output / "evaluator").mkdir(parents=True, exist_ok=True)
        (output / "evaluator/score_policy.json").write_text(
            json.dumps({"candidate_artifacts": ["model.va"]}),
            encoding="utf-8",
        )
        (output / "export-cell.json").write_text(json.dumps(dict(cell), sort_keys=True), encoding="utf-8")

    def make_branch_environment(*, runtime, branch, submitted_exception, **kwargs):
        environment_requests.append({"branch": branch.branch_id if branch else None, **kwargs})
        return _FakeLegacyEnvironment(
            runtime,
            submitted=submitted_exception,
            requests=environment_requests,
            branch=branch.branch_id if branch else None,
            **kwargs,
        )

    def build_final_test_profile(**kwargs):
        return _final_profile(campaign_config_sha256=str(kwargs["campaign_config_sha256"]))

    class FinalJudge:
        def __init__(self, **kwargs):
            del kwargs
            self.receipt = {"path": "evidence/score-sidecars/test.json", "sha256": SHA_A}

        def judge(self, submission):
            final_calls.append(submission.tree_sha256)
            return FinalJudgment("passed", "evas", 1.0, submission.tree_sha256)

    return (
        evolution.NativeEvolutionOps(
            export_runtime=export_runtime,
            make_branch_environment=make_branch_environment,
            make_final_judge=FinalJudge,
            build_final_test_profile=build_final_test_profile,
            quiesce_environment=lambda **kwargs: None,
        ),
        final_calls,
        environment_requests,
    )


class _FakeWaveformExecutor:
    invocations: list[dict[str, Any]] = []

    def __init__(
        self,
        *,
        runtime: Path,
        context,
        candidate_artifacts,
        release,
        campaign_config_sha256,
        docker_image_id,
        timeout_s,
        deadline_monotonic=None,
    ) -> None:
        del release, deadline_monotonic
        self.runtime = runtime
        self.context = context
        self.candidate_artifacts = tuple(candidate_artifacts)
        self.image_id = docker_image_id
        self.timeout_s = timeout_s
        self.profile = _waveform_public_profile(
            runtime=runtime,
            campaign_config_sha256=campaign_config_sha256,
            image_id=docker_image_id,
        )
        self.profile_sha256 = public_validation_profile_sha256(self.profile)
        self.invocations.append({
            "phase": "construct",
            "condition": context.condition,
            "attempt_id": context.attempt_id,
            "artifacts": self.candidate_artifacts,
            "image_id": docker_image_id,
        })

    def validate(self, *, candidate_tree_sha256: str) -> dict[str, Any]:
        self.invocations.append({
            "phase": "validate",
            "attempt_id": self.context.attempt_id,
            "candidate_tree_sha256": candidate_tree_sha256,
        })
        command_sha, public_task_sha, scope = _waveform_public_input(self.runtime)
        receipt = {
            "schema_version": "vaevas-public-waveform-receipt-v1",
            "authority": "public_diagnostic",
            "task_correctness": "not_evaluated",
            "attempt_id": self.context.attempt_id,
            "task_id": self.context.task_id,
            "invocation_id": str(uuid.uuid4()),
            "candidate_tree_sha256": candidate_tree_sha256,
            "profile_sha256": self.profile_sha256,
            "profile_input_identity_sha256": profile_input_identity_sha256(
                profile_sha256=self.profile_sha256,
                input_kind="candidate_tree",
                input_sha256=candidate_tree_sha256,
                attempt_id=self.context.attempt_id,
                task_id=self.context.task_id,
            ),
            "image_id": self.image_id,
            "command_sha256": command_sha,
            "public_task_tree_sha256": public_task_sha,
            "feedback_scope": scope,
            "status": "failed",
            "returncode": 1,
            "elapsed_s": 0.01,
            "waveform_summary": None,
            "waveform_summary_sha256": _sha(None),
            "cleanup_incidents": [],
            "usable_feedback": True,
        }
        receipt["receipt_sha256"] = _sha(receipt)
        return receipt


def _run_waveform(tmp_path: Path, *, rounds: int = 2, budgets: dict[str, int] | None = None):
    ops, final_calls, environment_requests = _ops(tmp_path)
    factory_calls = 0

    def factory():
        nonlocal factory_calls
        factory_calls += 1
        return _ScriptedReasoningClient("provider/wave", ["write", "vabench-submit"])

    run = evolution.run_native_evolution(
        cell={"cell_id": "cell-wave", "task_id": "task-wave", "mode": "G2", "experimental_arm": "AlphaApollo-Evolution+EVAS"},
        release=tmp_path / "release",
        output_dir=tmp_path / "native-evolution",
        branches=[
            evolution.NativeEvolutionBranch(
                branch_id="branch-wave",
                model_ref="provider/wave",
                backend_profile_sha256=REASONING_BACKEND_SHA,
                client_factory=factory,
            )
        ],
        public_validation_profile=None,
        final_test_profile=None,
        command="fake-final",
        evas_command="fake-evas",
        rounds=rounds,
        max_steps=2,
        budgets=budgets or {"model_calls": 3, "tool_calls": 3, "public_validation_calls": 1},
        public_validation_docker_image=IMAGE_ID,
        public_waveform=True,
        ops=ops,
        max_workers=1,
    )
    return run, final_calls, environment_requests, factory_calls


def test_native_evolution_public_waveform_is_coordinator_owned_and_shared(monkeypatch, tmp_path: Path):
    _FakeWaveformExecutor.invocations = []
    monkeypatch.setattr(evolution.public_waveform_runtime, "IsolatedPublicWaveformExecutor", _FakeWaveformExecutor)

    run, final_calls, environment_requests, factory_calls = _run_waveform(tmp_path)

    validate_calls = [row for row in _FakeWaveformExecutor.invocations if row["phase"] == "validate"]
    assert len(validate_calls) == 2
    assert factory_calls == 2
    assert final_calls == [run.selected_candidate["candidate_tree_sha256"]]
    request_doc = json.loads((tmp_path / "native-evolution/request.json").read_text())
    assert request_doc["config"]["extensions"]["public_waveform"] == {
        "intervention": "isolated-public-waveform-v1",
        "tool_name": "vaevas_public_simulate",
        "max_public_validation_calls": 1,
    }
    assert request_doc["config"]["public_validation"] == {
        "docker_image": IMAGE_ID,
        "mode": "isolated_public_waveform",
        "legacy_public_validator_also_runs": False,
    }
    branch_envs = [row for row in environment_requests if row["branch"] == "branch-wave"]
    assert {row["executable_feedback"] for row in branch_envs} == {False}
    assert {row["docker_image"] for row in branch_envs} == {"vabench-agent-runtime:0.8.7-no-evas"}
    exported_profile = json.loads((tmp_path / "native-evolution/public-validation-profile.json").read_text())
    assert exported_profile["allowed_feedback"] == ["runtime", "waveform_summary"]
    provider_request = json.loads(
        (tmp_path / "native-evolution/evolution/branches/round-0001/branch-wave/private-events.jsonl").read_text().splitlines()[0]
    )
    prior_payload = provider_request["payload"]["messages"][1]["content"]
    assert "waveform_summary" in prior_payload
    assert "score_sidecar" not in prior_payload


def test_public_waveform_budget_exhaustion_fails_before_executor(monkeypatch, tmp_path: Path):
    _FakeWaveformExecutor.invocations = []
    monkeypatch.setattr(evolution.public_waveform_runtime, "IsolatedPublicWaveformExecutor", _FakeWaveformExecutor)

    with pytest.raises(ValueError, match="positive public validation budget"):
        _run_waveform(tmp_path, rounds=1, budgets={"model_calls": 3, "tool_calls": 3, "public_validation_calls": 0})

    assert _FakeWaveformExecutor.invocations == []


def test_public_waveform_prior_feedback_rejects_corrupt_receipt(monkeypatch, tmp_path: Path):
    _FakeWaveformExecutor.invocations = []
    monkeypatch.setattr(evolution.public_waveform_runtime, "IsolatedPublicWaveformExecutor", _FakeWaveformExecutor)
    run, *_ = _run_waveform(tmp_path, rounds=1)

    selected = dict(run.evolution_result.round_snapshots[0]["selected_candidate"])
    store = evolution._candidate_store_for_selection(
        branches_dir=tmp_path / "native-evolution/evolution/branches",
        selected_candidate=selected,
    )
    receipt_path = store.parents[1] / "public-validation.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["observation"]["payload"]["final_score"] = 1.0
    receipt["observation"]["payload_sha256"] = _sha(receipt["observation"]["payload"])
    receipt["result"]["event_sha256"] = evolution._canonical_sha256(receipt["observation"])
    receipt_path.chmod(0o644)
    receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")

    with pytest.raises(ValueError, match="public waveform observation contract mismatch"):
        evolution._public_feedback_for_prior_candidate(
            store=store,
            entry={
                "summary": selected["public_validation"]["metrics"],
                "source_event_sha256": receipt["result"]["event_sha256"],
                "candidate_id": selected["candidate_id"],
                "candidate_tree_sha256": selected["candidate_tree_sha256"],
            },
            tree_sha256=selected["candidate_tree_sha256"],
            candidate_id=selected["candidate_id"],
            manifest_sha256=run.manifest_sha256,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("image_id", "sha256:" + "8" * 64),
        ("command_sha256", SHA_E),
        ("public_task_tree_sha256", SHA_E),
        ("feedback_scope", "reference_dut_only"),
    ],
)
def test_public_waveform_prior_feedback_rejects_rehashed_receipt_input_drift(
    monkeypatch,
    tmp_path: Path,
    field: str,
    value: str,
):
    _FakeWaveformExecutor.invocations = []
    monkeypatch.setattr(evolution.public_waveform_runtime, "IsolatedPublicWaveformExecutor", _FakeWaveformExecutor)
    run, *_ = _run_waveform(tmp_path, rounds=1)

    selected = dict(run.evolution_result.round_snapshots[0]["selected_candidate"])
    store = evolution._candidate_store_for_selection(
        branches_dir=tmp_path / "native-evolution/evolution/branches",
        selected_candidate=selected,
    )
    receipt_path = store.parents[1] / "public-validation.json"
    receipt_doc = json.loads(receipt_path.read_text())
    nested = receipt_doc["observation"]["payload"]["receipt"]
    nested[field] = value
    nested["receipt_sha256"] = _sha({key: item for key, item in nested.items() if key != "receipt_sha256"})
    receipt_doc["observation"]["payload_sha256"] = _sha(receipt_doc["observation"]["payload"])
    receipt_doc["result"]["event_sha256"] = evolution._canonical_sha256(receipt_doc["observation"])
    receipt_path.chmod(0o644)
    receipt_path.write_text(json.dumps(receipt_doc, sort_keys=True), encoding="utf-8")

    with pytest.raises(ValueError, match="public waveform receipt/input mismatch"):
        evolution._public_feedback_for_prior_candidate(
            store=store,
            entry={
                "summary": selected["public_validation"]["metrics"],
                "source_event_sha256": receipt_doc["result"]["event_sha256"],
                "candidate_id": selected["candidate_id"],
                "candidate_tree_sha256": selected["candidate_tree_sha256"],
            },
            tree_sha256=selected["candidate_tree_sha256"],
            candidate_id=selected["candidate_id"],
            manifest_sha256=run.manifest_sha256,
        )


def test_public_waveform_rejects_profile_drift(monkeypatch, tmp_path: Path):
    class DriftExecutor(_FakeWaveformExecutor):
        def __init__(self, **kwargs) -> None:
            super().__init__(**kwargs)
            if self.context.attempt_id != "public-validation-profile-freeze":
                self.profile = {**self.profile, "checker_identity_sha256": SHA_E}
                self.profile_sha256 = public_validation_profile_sha256(self.profile)

    monkeypatch.setattr(evolution.public_waveform_runtime, "IsolatedPublicWaveformExecutor", DriftExecutor)

    with pytest.raises(RuntimeError, match="no selected candidate"):
        _run_waveform(tmp_path, rounds=1)

    doc = json.loads((tmp_path / "native-evolution/final-result.json").read_text())
    assert doc["status"] == "evolution_failed"
    branch = json.loads(
        (tmp_path / "native-evolution/evolution/branches/round-0000/branch-wave/result.json").read_text()
    )["branch_record"]
    assert branch["status"] == "branch_failed"
    assert branch["usage"]["public_validation_calls"] == 1
