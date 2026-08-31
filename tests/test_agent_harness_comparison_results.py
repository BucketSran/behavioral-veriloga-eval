from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import sys
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(OPS))

from runners.agent_harness import (  # noqa: E402
    EpisodeContext,
    FinalJudgment,
    FrozenSubmission,
    final_test_profile_sha256,
    write_immutable_score_sidecar,
)
import result_protocol  # noqa: E402

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64
SHA_F = "f" * 64
CAMPAIGN_SHA = "1" * 64


def _cell(
    cell_id: str = "ln001-dut-legacy",
    *,
    backend: str = "legacy",
    task_id: str = "v4-001",
    form: str = "dut",
) -> dict[str, Any]:
    return {
        "comparison_cell_id": cell_id,
        "cell_id": cell_id,
        "task_id": task_id,
        "family_id": "001",
        "form": form,
        "mode": "G2",
        "experimental_arm": "Agentic",
        "backend": backend,
    }


def _profile() -> dict[str, Any]:
    return {
        "schema_version": "vaevas-final-test-profile-v1",
        "profile_id": "r53/evas-0.8.7-final-test",
        "benchmark_release": "benchmarkv4-r53",
        "benchmark_manifest_sha256": SHA_A,
        "judge": {"engine": "evas", "version": "0.8.7"},
        "judge_identity_sha256": SHA_B,
        "checker_identity_sha256": SHA_C,
        "runtime_identity_sha256": SHA_D,
        "campaign_config_sha256": CAMPAIGN_SHA,
        "command_signature_sha256": SHA_F,
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
            "schema_id": "vabench-trusted-replay-status-v1",
            "requires_structured_verdict": True,
        },
        "score_sidecar_contract": {
            "schema_id": "vaevas-score-sidecar-v1",
            "immutable": True,
            "binds_submission_tree": True,
            "score_authority": "development_only",
        },
        "spectre_policy": {
            "required": False,
            "trigger": "conditional_evas_or_external_protocol_change",
            "spectre_judge_identity_sha256": None,
            "spectre_command_signature_sha256": None,
            "spectre_report_schema_id": None,
        },
    }


def _sidecar(score: float = 1.0, *, submission_tree_sha256: str = SHA_A) -> dict[str, Any]:
    status = "passed" if score == 1.0 else "behavior_failure"
    return {
        "schema_version": "vaevas-score-sidecar-v1",
        "benchmark_release": "benchmarkv4-r53",
        "benchmark_manifest_sha256": SHA_A,
        "score_authority": "development_only",
        "immutable": True,
        "binds_submission_tree": True,
        "submission_tree_sha256": submission_tree_sha256,
        "judge": {
            "engine": "evas",
            "version": "0.8.7",
            "identity_sha256": SHA_B,
        },
        "checker_identity_sha256": SHA_C,
        "runtime_identity_sha256": SHA_D,
        "campaign_config_sha256": CAMPAIGN_SHA,
        "command_signature_sha256": SHA_F,
        "structured_result": {"status": status, "score": score},
        "model_observation_allowed": False,
        "memory_entry_allowed": False,
    }


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_legacy_runtime(
    runtime: Path,
    cell: dict[str, Any],
    *,
    score: float | None = 1.0,
    receipt: bool = True,
) -> None:
    campaign_cell = {key: cell[key] for key in (
        "cell_id",
        "task_id",
        "family_id",
        "form",
        "mode",
        "experimental_arm",
    )}
    evidence = runtime / "evidence"
    final_submission = evidence / "final_submission"
    final_submission.mkdir(parents=True)
    model = final_submission / "model.va"
    model.write_text("module model; endmodule\n")
    frozen = result_protocol.hash_test_tree(final_submission)
    model_sha = _sha(model)
    final_submission_manifest = {
        "status": "available" if score is not None or receipt else "no_submission",
        "immutable": True,
        "tree_sha256": frozen["tree_sha256"] if score is not None or receipt else None,
        "artifacts": (
            [{"path": "model.va", "sha256": model_sha}]
            if score is not None or receipt
            else []
        ),
    }
    campaign_result = {
        "cell": campaign_cell,
        "termination_reason": "submitted" if score is not None else "provider_error",
        "model_status": "completed",
        "experiment_result": {
            "outcome": "passed" if score == 1.0 else "behavior_failure",
            "final_submission": final_submission_manifest,
            "model_execution": {
                "status": "submitted" if score is not None else "provider_error"
            },
        },
    }
    result_path = evidence / "campaign_result.json"
    result_path.write_text(json.dumps(campaign_result, sort_keys=True))
    checkpoint = evidence / "conversation_checkpoint.json"
    checkpoint.write_text(json.dumps({"messages": [{"role": "assistant", "content": "ok"}]}))
    trajectory = evidence / "mini_swe_trajectory.json"
    trajectory.write_text(json.dumps({"events": []}))
    profile = _profile()
    sidecar_receipt = None
    if receipt and score is not None:
        context = EpisodeContext(
            episode_id=cell["cell_id"],
            attempt_id=f"{cell['cell_id']}-attempt-0001",
            task_id=cell["task_id"],
            condition=cell["experimental_arm"],
            max_steps=4,
        )
        submission = FrozenSubmission(frozen["tree_sha256"], ("model.va",))
        sidecar = _sidecar(score, submission_tree_sha256=frozen["tree_sha256"])
        judgment = FinalJudgment(
            status=sidecar["structured_result"]["status"],
            judge_engine="evas",
            score=score,
            submission_tree_sha256=frozen["tree_sha256"],
        )
        record = write_immutable_score_sidecar(
            output_dir=evidence,
            context=context,
            submission=submission,
            judgment=judgment,
            final_test_profile=profile,
            score_sidecar=sidecar,
        )
        sidecar_receipt = {
            "path": record.path.relative_to(runtime).as_posix(),
            "sha256": record.sha256,
            "episode_id": context.episode_id,
            "attempt_id": context.attempt_id,
            "task_id": context.task_id,
            "submission_tree_sha256": record.submission_tree_sha256,
            "final_profile_sha256": record.final_profile_sha256,
            "final_profile_input_identity_sha256": record.final_profile_input_identity_sha256,
        }
        reservation = evidence / "bound-final-test"
        reservation.mkdir()
        (reservation / "request.json").write_text(
            json.dumps(
                {
                    "profile": profile,
                    "episode_id": cell["cell_id"],
                    "attempt_id": context.attempt_id,
                    "task_id": cell["task_id"],
                    "submission_tree_sha256": frozen["tree_sha256"],
                },
                sort_keys=True,
            )
        )
    envelope = {
        "schema_version": "vaevas-comparison-legacy-final-v1",
        "cell": campaign_cell,
        "campaign_file_sha256": CAMPAIGN_SHA,
        "attempt_id": f"{cell['cell_id']}-attempt-0001",
        "final_test_profile": profile,
        "score_sidecar_receipt": sidecar_receipt,
        "generation_files": {
            "evidence/campaign_result.json": _sha(result_path),
            "evidence/conversation_checkpoint.json": _sha(checkpoint),
            "evidence/mini_swe_trajectory.json": _sha(trajectory),
        },
    }
    (evidence / "comparison-legacy-final.json").write_text(
        json.dumps(envelope, sort_keys=True)
    )


def test_read_legacy_cell_validates_bound_final_receipt_without_rejudging(tmp_path):
    comparison_results = importlib.import_module("comparison_results")
    runtime = tmp_path / "ln001-dut-legacy"
    cell = _cell()
    _write_legacy_runtime(runtime, cell)

    row = comparison_results.read_legacy_cell(
        runtime, cell, campaign_file_sha256=CAMPAIGN_SHA
    )

    assert row["backend"] == "legacy"
    assert row["cell_id"] == cell["cell_id"]
    assert row["task_id"] == "v4-001"
    assert row["score"] == 1.0
    assert row["score_sidecar_receipt"]["final_profile_sha256"] == (
        final_test_profile_sha256(_profile())
    )
    assert row["legacy_evidence"]["files"]["evidence/campaign_result.json"]
    assert "messages" not in json.dumps(row)


def test_read_legacy_cell_fails_closed_when_submitted_without_final_receipt(tmp_path):
    comparison_results = importlib.import_module("comparison_results")
    runtime = tmp_path / "ln001-dut-legacy"
    cell = _cell()
    _write_legacy_runtime(runtime, cell, receipt=False)

    with pytest.raises(ValueError, match="receipt"):
        comparison_results.read_legacy_cell(
            runtime, cell, campaign_file_sha256=CAMPAIGN_SHA
        )


def test_read_legacy_cell_keeps_no_submission_failure_unscored(tmp_path):
    comparison_results = importlib.import_module("comparison_results")
    runtime = tmp_path / "ln001-dut-legacy"
    cell = _cell()
    _write_legacy_runtime(runtime, cell, score=None, receipt=False)

    row = comparison_results.read_legacy_cell(
        runtime, cell, campaign_file_sha256=CAMPAIGN_SHA
    )

    assert row["score"] is None
    assert row["submission_status"] == "no_submission"
    assert row["terminal_reason"] == "provider_error"
    assert "trusted_replay" not in row


def test_read_legacy_cell_rejects_wrong_observed_image(tmp_path):
    comparison_results = importlib.import_module("comparison_results")
    runtime = tmp_path / "ln001-dut-legacy"
    cell = _cell()
    _write_legacy_runtime(runtime, cell)
    result_path = runtime / "evidence/campaign_result.json"
    result = json.loads(result_path.read_text())
    result["public_agent_environment"] = {"image_id": "sha256:" + "b" * 64}
    result_path.write_text(json.dumps(result, sort_keys=True))
    envelope_path = runtime / "evidence/comparison-legacy-final.json"
    envelope = json.loads(envelope_path.read_text())
    envelope["generation_files"]["evidence/campaign_result.json"] = _sha(result_path)
    envelope_path.write_text(json.dumps(envelope, sort_keys=True))

    with pytest.raises(ValueError, match="image"):
        comparison_results.read_legacy_cell(
            runtime,
            cell,
            campaign_file_sha256=CAMPAIGN_SHA,
            expected_image_id="sha256:" + "a" * 64,
        )


def test_legacy_generation_cell_model_cannot_drift_behind_new_hash(tmp_path):
    module = importlib.import_module("comparison_results")
    cell = _cell()
    _write_legacy_runtime(tmp_path, cell)
    result_path = tmp_path / "evidence/campaign_result.json"
    result = json.loads(result_path.read_text())
    result["cell"]["model"] = "different-model"
    result_path.write_text(json.dumps(result))
    envelope_path = tmp_path / "evidence/comparison-legacy-final.json"
    envelope = json.loads(envelope_path.read_text())
    envelope["generation_files"]["evidence/campaign_result.json"] = _sha(result_path)
    envelope_path.write_text(json.dumps(envelope))
    with pytest.raises(ValueError, match="scheduled cell"):
        module.read_legacy_cell(tmp_path, cell, campaign_file_sha256=CAMPAIGN_SHA)


def test_read_backend_cell_delegates_native_to_existing_reader(monkeypatch, tmp_path):
    comparison_results = importlib.import_module("comparison_results")
    cell = _cell("ln002-dut-native", backend="native-mini-swe")
    calls = []

    def fake_reader(runtime, scheduled, *, campaign_file_sha256):
        calls.append((runtime, scheduled, campaign_file_sha256))
        return {
            "cell_id": scheduled["cell_id"],
            "task_id": scheduled["task_id"],
            "family_id": scheduled["family_id"],
            "form": scheduled["form"],
            "mode": scheduled["mode"],
            "experimental_arm": scheduled["experimental_arm"],
            "backend": "native-mini-swe",
            "score": 0.0,
            "public_agent_environment": {"image_id": "sha256:" + "a" * 64},
        }

    monkeypatch.setattr(comparison_results.score_campaign, "read_native_cell", fake_reader)

    row = comparison_results.read_backend_cell(
        tmp_path,
        "native-mini-swe",
        cell,
        campaign_file_sha256=CAMPAIGN_SHA,
        expected_image_id="sha256:" + "a" * 64,
    )

    assert row["score"] == 0.0
    assert calls == [(tmp_path, cell, CAMPAIGN_SHA)]


def test_read_backend_cell_checks_native_launcher_manifest_image_when_row_omits_it(
    monkeypatch, tmp_path
):
    comparison_results = importlib.import_module("comparison_results")
    runtime = tmp_path / "ln002-dut-native"
    evidence = runtime / "evidence/native-launcher"
    evidence.mkdir(parents=True)
    manifest = {"environment": {"image_id": "sha256:" + "a" * 64}}
    manifest_path = evidence / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True))
    (evidence / "result.json").write_text(
        json.dumps({"manifest_sha256": _sha(manifest_path)}, sort_keys=True)
    )
    cell = _cell("ln002-dut-native", backend="native-mini-swe")

    def fake_reader(runtime, scheduled, *, campaign_file_sha256):
        return {
            "cell_id": scheduled["cell_id"],
            "task_id": scheduled["task_id"],
            "family_id": scheduled["family_id"],
            "form": scheduled["form"],
            "mode": scheduled["mode"],
            "experimental_arm": scheduled["experimental_arm"],
            "backend": "native-mini-swe",
            "score": 0.0,
        }

    monkeypatch.setattr(comparison_results.score_campaign, "read_native_cell", fake_reader)

    comparison_results.read_backend_cell(
        runtime,
        "native-mini-swe",
        cell,
        campaign_file_sha256=CAMPAIGN_SHA,
        expected_image_id="sha256:" + "a" * 64,
    )
    with pytest.raises(ValueError, match="image"):
        comparison_results.read_backend_cell(
            runtime,
            "native-mini-swe",
            cell,
            campaign_file_sha256=CAMPAIGN_SHA,
            expected_image_id="sha256:" + "b" * 64,
        )


def _join_row(
    comparison_cell_id: str,
    *,
    backend: str,
    task_id: str,
    form: str,
    status: str,
    score: float | None,
) -> dict[str, Any]:
    identity = {
        "comparison_cell_id": comparison_cell_id,
        "cell_id": comparison_cell_id,
        "backend": backend,
        "task_id": task_id,
        "family_id": "001",
        "form": form,
    }
    return {
        **identity,
        "status": status,
        "score": score,
        "evidence": None if status == "not_started" else {**identity, "score": score},
    }


def test_join_six_cell_comparison_keeps_all_rows_and_null_incomplete_pairs():
    comparison_results = importlib.import_module("comparison_results")
    schedule = [
        _cell("ln001-dut-legacy", backend="legacy", task_id="v4-001", form="dut"),
        _cell("ln002-dut-native", backend="native-mini-swe", task_id="v4-001", form="dut"),
        _cell("ln003-bugfix-native", backend="native-mini-swe", task_id="v4-1001", form="bugfix"),
        _cell("ln004-bugfix-legacy", backend="legacy", task_id="v4-1001", form="bugfix"),
        _cell("ln005-tb-legacy", backend="legacy", task_id="v4-501", form="testbench"),
        _cell("ln006-tb-native", backend="native-mini-swe", task_id="v4-501", form="testbench"),
    ]
    rows = [
        _join_row(
            "ln001-dut-legacy",
            backend="legacy",
            task_id="v4-001",
            form="dut",
            status="scored",
            score=1.0,
        ),
        _join_row(
            "ln002-dut-native",
            backend="native-mini-swe",
            task_id="v4-001",
            form="dut",
            status="protocol_failure",
            score=None,
        ),
        _join_row(
            "ln003-bugfix-native",
            backend="native-mini-swe",
            task_id="v4-1001",
            form="bugfix",
            status="scored",
            score=0.0,
        ),
        _join_row(
            "ln004-bugfix-legacy",
            backend="legacy",
            task_id="v4-1001",
            form="bugfix",
            status="scored",
            score=1.0,
        ),
        _join_row(
            "ln005-tb-legacy",
            backend="legacy",
            task_id="v4-501",
            form="testbench",
            status="not_started",
            score=None,
        ),
        _join_row(
            "ln006-tb-native",
            backend="native-mini-swe",
            task_id="v4-501",
            form="testbench",
            status="not_started",
            score=None,
        ),
    ]

    joined = comparison_results.join_six_cell_comparison(schedule, rows)

    assert [row["comparison_cell_id"] for row in joined["audit_rows"]] == [
        row["comparison_cell_id"] for row in schedule
    ]
    assert len(joined["paired_rows"]) == 3
    assert joined["paired_rows"][0]["score_delta"] is None
    assert joined["paired_rows"][1]["score_delta"] == -1.0
    assert joined["paired_rows"][2]["score_delta"] is None


def test_join_keeps_incomplete_evidence_score_but_excludes_pair_delta():
    comparison_results = importlib.import_module("comparison_results")
    schedule = [
        _cell("ln001-dut-legacy", backend="legacy", task_id="v4-001", form="dut"),
        _cell("ln002-dut-native", backend="native-mini-swe", task_id="v4-001", form="dut"),
        _cell("ln003-bugfix-native", backend="native-mini-swe", task_id="v4-1001", form="bugfix"),
        _cell("ln004-bugfix-legacy", backend="legacy", task_id="v4-1001", form="bugfix"),
        _cell("ln005-tb-legacy", backend="legacy", task_id="v4-501", form="testbench"),
        _cell("ln006-tb-native", backend="native-mini-swe", task_id="v4-501", form="testbench"),
    ]
    rows = [
        _join_row(
            "ln001-dut-legacy",
            backend="legacy",
            task_id="v4-001",
            form="dut",
            status="scored",
            score=1.0,
        ),
        {
            **_join_row(
                "ln002-dut-native",
                backend="native-mini-swe",
                task_id="v4-001",
                form="dut",
                status="incomplete_evidence",
                score=0.0,
            ),
            "disposition": "incomplete_evidence",
            "evidence": None,
        },
        _join_row(
            "ln003-bugfix-native",
            backend="native-mini-swe",
            task_id="v4-1001",
            form="bugfix",
            status="not_started",
            score=None,
        ),
        _join_row(
            "ln004-bugfix-legacy",
            backend="legacy",
            task_id="v4-1001",
            form="bugfix",
            status="not_started",
            score=None,
        ),
        _join_row(
            "ln005-tb-legacy",
            backend="legacy",
            task_id="v4-501",
            form="testbench",
            status="not_started",
            score=None,
        ),
        _join_row(
            "ln006-tb-native",
            backend="native-mini-swe",
            task_id="v4-501",
            form="testbench",
            status="not_started",
            score=None,
        ),
    ]

    joined = comparison_results.join_six_cell_comparison(schedule, rows)

    assert joined["audit_rows"][1]["score"] == 0.0
    assert joined["paired_rows"][0]["score_delta"] is None
    assert joined["paired_rows"][0]["complete"] is False


def test_join_rejects_duplicate_rows_and_nan_scores():
    comparison_results = importlib.import_module("comparison_results")
    schedule = [
        _cell("ln001-dut-legacy", backend="legacy", task_id="v4-001", form="dut"),
        _cell("ln002-dut-native", backend="native-mini-swe", task_id="v4-001", form="dut"),
        _cell("ln003-bugfix-native", backend="native-mini-swe", task_id="v4-1001", form="bugfix"),
        _cell("ln004-bugfix-legacy", backend="legacy", task_id="v4-1001", form="bugfix"),
        _cell("ln005-tb-legacy", backend="legacy", task_id="v4-501", form="testbench"),
        _cell("ln006-tb-native", backend="native-mini-swe", task_id="v4-501", form="testbench"),
    ]
    with pytest.raises(ValueError, match="six"):
        comparison_results.join_six_cell_comparison(schedule[:2], [])
    rows = [
        _join_row(
            "ln001-dut-legacy",
            backend="legacy",
            task_id="v4-001",
            form="dut",
            status="scored",
            score=float("nan"),
        ),
        _join_row(
            "ln001-dut-legacy",
            backend="legacy",
            task_id="v4-001",
            form="dut",
            status="scored",
            score=1.0,
        ),
        _join_row(
            "ln003-bugfix-native",
            backend="native-mini-swe",
            task_id="v4-1001",
            form="bugfix",
            status="not_started",
            score=None,
        ),
        _join_row(
            "ln004-bugfix-legacy",
            backend="legacy",
            task_id="v4-1001",
            form="bugfix",
            status="not_started",
            score=None,
        ),
        _join_row(
            "ln005-tb-legacy",
            backend="legacy",
            task_id="v4-501",
            form="testbench",
            status="not_started",
            score=None,
        ),
        _join_row(
            "ln006-tb-native",
            backend="native-mini-swe",
            task_id="v4-501",
            form="testbench",
            status="not_started",
            score=None,
        ),
    ]
    with pytest.raises(ValueError, match="duplicate|finite"):
        comparison_results.join_six_cell_comparison(schedule, rows)


def _completed_join():
    schedule = [_cell(f"{form}-{backend}", backend=backend, task_id=task_id, form=form)
                for task_id, form in (("v4-001", "dut"), ("v4-1001", "bugfix"), ("v4-501", "testbench"))
                for backend in ("legacy", "native-mini-swe")]
    rows = [_join_row(cell["cell_id"], backend=cell["backend"], task_id=cell["task_id"],
                      form=cell["form"], status="completed", score=0.0) for cell in schedule]
    return schedule, rows


def test_completed_null_score_still_requires_terminal_evidence():
    module = importlib.import_module("comparison_results")
    schedule, rows = _completed_join()
    rows[0].pop("status")
    rows[0].update(disposition="completed", started=True, score=None, evidence=None)
    with pytest.raises(ValueError, match="require evidence"):
        module.join_six_cell_comparison(schedule, rows)


@pytest.mark.parametrize("field,value", [("cell_id", "wrong"), ("backend", "native-reasoning"), ("task_id", "v4-002")])
def test_join_rejects_wrong_terminal_evidence_identity(field, value):
    module = importlib.import_module("comparison_results")
    schedule, rows = _completed_join()
    rows[0]["evidence"][field] = value
    with pytest.raises(ValueError, match="evidence identity"):
        module.join_six_cell_comparison(schedule, rows)


def test_legacy_reader_binds_envelope_and_final_request_bytes(tmp_path):
    module = importlib.import_module("comparison_results")
    _write_legacy_runtime(tmp_path, _cell())
    before = module.read_legacy_cell(tmp_path, _cell(), campaign_file_sha256=CAMPAIGN_SHA)
    files = before["legacy_evidence"]["files"]
    for relative in ("evidence/comparison-legacy-final.json", "evidence/bound-final-test/request.json",
                     before["score_sidecar_receipt"]["path"]):
        assert files[relative] == _sha(tmp_path / relative)


def test_pair_cost_is_guard_upper_bound_not_invoice_and_time_is_end_to_end():
    module = importlib.import_module("comparison_results")
    schedule, rows = _completed_join()
    rows[0].update(guard_upper_bound="0.1", elapsed_s=10.0)
    rows[1].update(guard_upper_bound="0.3", elapsed_s=25.0)
    report = module.join_six_cell_comparison(schedule, rows)
    pair = next(pair for pair in report["paired_rows"] if pair["task_id"] == "v4-001")
    assert pair["guard_upper_bound_delta"] == "0.2"
    assert pair["elapsed_s_delta"] == 15.0
    assert report["paired_rows"][1]["guard_upper_bound_delta"] is None
