"""Additional reporting paths preserve their native authority and estimands."""

import importlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"))


def test_legacy_comparison_exports_all_six_unstarted_rows_without_execution(tmp_path, monkeypatch):
    from test_agent_harness_workflow_comparison import _unstarted_fixture
    comparison, root, _, _ = _unstarted_fixture(tmp_path)
    before = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    def forbidden(*args, **kwargs):
        raise AssertionError("report must not execute")
    monkeypatch.setattr(comparison, "_execute_comparison", forbidden)
    source = importlib.import_module("reporting_sources")
    ledger = source.read_reporting_ledger("legacy-native-comparison", root)
    assert ledger["denominator"]["scheduled_cells"] == 6
    assert ledger["denominator"]["eligible_actual_score_cells"] == 0
    assert len(ledger["paired_summary"]["arms"]) == 2
    assert all(row["actual_score"] is None for row in ledger["records"])
    assert len({row["identity"]["cell_id"] for row in ledger["records"]}) == 6
    assert not ledger["single_trajectory_pooling_allowed"]
    assert ledger["records"][0]["details"]["score_authority"] == "development_only"
    assert before == {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_evolution_terminal_zero_and_candidate_identity_are_preserved(tmp_path, monkeypatch):
    from test_agent_harness_evolution_batch import (
        test_batch_resume_reuses_completed_zero_score_without_provider_or_judge as exercise,
    )
    exercise(tmp_path, monkeypatch, False)
    source = importlib.import_module("reporting_sources")
    attempt_root, = (tmp_path / "batch").glob("*/attempt-0001")
    ledger = source.read_reporting_ledger("evolution-single", attempt_root)
    record, = ledger["records"]
    assert record["actual_score"] == 0.0
    assert record["actual_score_eligible"]
    assert record["details"]["selected_candidate"]["candidate_id"] == "a-round-0000"
    assert record["hashes"]["score_sidecar_sha256"]
    assert record["costs"]["all_branch_costs"] is None  # old fixture lacks full costs
    assert "multi_model_round_evolution" in record["report_group"]


def test_combined_prepared_is_not_a_completed_score(tmp_path):
    from test_agent_harness_combined_tools import prepared
    _, root, _, _ = prepared(tmp_path)
    source = importlib.import_module("reporting_sources")
    with pytest.raises(ValueError, match="terminal"):
        source.read_reporting_ledger("combined-tools", root)


def test_combined_reporting_names_the_frozen_intervention(tmp_path, monkeypatch):
    import reporting_sources as source
    import run_combined_tools

    root = tmp_path / "baseline"
    root.mkdir()
    (root / "combined-manifest.json").write_text(json.dumps({
        "source_cell": {
            "cell_id": "v4-001-dut-agentic-r0",
            "task_id": "v4-001-dut",
            "family_id": "001",
            "form": "dut",
        },
    }))
    monkeypatch.setattr(run_combined_tools, "read_combined", lambda _: {
        "terminal": 1,
        "disposition": "completed",
        "backend": "native-reasoning",
        "score": 1.0,
        "manifest_sha256": "a" * 64,
        "intervention": {
            "name": "baseline", "offline_docs": False, "public_waveform": False,
        },
        "condition_acceptance_passed": True,
        "combined_acceptance_passed": False,
        "evidence_scope": "real_model_condition_observation",
        "paid_requests": None,
        "feature_use": {"features": {
            "offline_docs": {"attempted": 0, "succeeded": 0,
                             "feedback_exposed_requests": 0, "incomplete": []},
            "public_waveform": {"attempted": 0, "succeeded": 0,
                                "feedback_exposed_requests": 0, "incomplete": []},
        }},
        "cost": {"currency": "CNY", "guard_upper_bound": "0", "model_calls": 1,
                 "transport_reservations": 1, "censored": False},
    })

    _, records = source._combined(root)

    record, = records
    assert record["identity"]["intervention"] == "baseline"
    assert record["report_group"] == "combined-tools/baseline/native-reasoning"
    assert record["details"]["condition_acceptance_passed"] is True
    assert record["details"]["combined_acceptance_passed"] is False


def test_official_multipath_export_is_readonly_and_keeps_unscored(tmp_path, monkeypatch):
    pytest.importorskip("inspect_ai")
    from inspect_ai.log import read_eval_log
    from test_agent_harness_workflow_comparison import _unstarted_fixture
    from result_adapter import export_inspect
    comparison, root, _, _ = _unstarted_fixture(tmp_path)
    def forbidden(*args, **kwargs):
        raise AssertionError("export must not execute")
    monkeypatch.setattr(comparison, "_execute_comparison", forbidden)
    output = tmp_path / "viewer"
    receipt = export_inspect(None, root, output, source_kind="legacy-native-comparison")
    log = read_eval_log(output / "results.eval")
    assert receipt["scheduled_cells"] == 6
    assert log.results.scores[0].unscored_samples == 6
    assert log.eval.task_version == "vaevas-multipath-report-ledger-v1"
    assert "pooled" not in log.results.scores[0].metrics
    assert all("evidence" not in sample.metadata["vaevas"] for sample in log.samples)
    with pytest.raises(FileExistsError):
        export_inspect(None, root, output, source_kind="legacy-native-comparison")
    with pytest.raises(ValueError, match="outside"):
        export_inspect(None, root, root / "export", source_kind="legacy-native-comparison")


@pytest.mark.parametrize("backend", ["native-reasoning", "evolution"])
def test_real_combined_export_retains_costs_and_verified_score(tmp_path, monkeypatch, backend):
    from test_agent_harness_combined_tools import _exercise_real_combined
    from reporting_sources import read_reporting_ledger
    def verify(root, original):
        before = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        ledger = read_reporting_ledger("combined-tools", root)
        record, = ledger["records"]
        assert record["actual_score"] == original["score"]
        assert record["costs"]["budget"] == original["cost"]
        assert record["details"]["feature_use"]["public_waveform"]["attempted"] > 0
        if importlib.util.find_spec("inspect_ai") is not None:
            from result_adapter import export_inspect
            from inspect_ai.log import read_eval_log
            output = tmp_path / "viewer"
            export_inspect(None, root, output, source_kind="combined-tools")
            sample, = read_eval_log(output / "results.eval").samples
            assert sample.scores["vaevas_final"].value == original["score"]
        assert before == {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    _exercise_real_combined(tmp_path, monkeypatch, backend, False, verify)


def test_source_rejects_symlinks_and_drift(tmp_path):
    from test_agent_harness_workflow_comparison import _unstarted_fixture
    from reporting_sources import read_reporting_ledger
    _, root, _, _ = _unstarted_fixture(tmp_path)
    (root / "unexpected-link").symlink_to(root / "comparison-manifest.json")
    with pytest.raises(ValueError, match="symlink"):
        read_reporting_ledger("legacy-native-comparison", root)
    (root / "unexpected-link").unlink()
    manifest = root / "comparison-manifest.json"
    data = json.loads(manifest.read_bytes())
    data["score_authority"] = "untrusted_changed_value"
    manifest.chmod(0o600)
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        read_reporting_ledger("legacy-native-comparison", root)
