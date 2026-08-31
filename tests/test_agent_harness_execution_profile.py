from __future__ import annotations

import json
import time

import pytest

from runners.agent_harness.phase_timing import measure_phase
from scripts import profile_native_execution as profile


def _cells(count: int = 4) -> list[dict]:
    return [
        {
            "cell_id": f"cell-{index:03d}",
            "task_id": "v4-001",
            "family_id": "001",
            "form": "dut",
            "mode": "G2",
            "experimental_arm": "Agentic",
        }
        for index in range(count)
    ]


def _stable_executor(cell: dict, context: profile.CellExecutionContext) -> dict:
    with measure_phase("model"):
        time.sleep(0.01)
    with measure_phase("tool"):
        time.sleep(0.005)
    with measure_phase("freeze"):
        pass
    with measure_phase("final_judge"):
        pass
    content = f"fixed-public-stub:{cell['cell_id']}"
    return {
        "cell_id": cell["cell_id"],
        "attempt_id": context.attempt_id,
        "status": "behavior_failure",
        "submission_files": {"model.va": content},
        "submission_tree_sha256": profile.sha256_text(content),
        "verdict": {"judge_status": "behavior_failure", "score": 0},
    }


def test_fixed_profile_records_queue_timing_and_worker_invariants(tmp_path):
    report = profile.profile_workload(
        tmp_path / "profile",
        cells=_cells(),
        worker_counts=(1, 2),
        execute_cell=_stable_executor,
    )
    assert report["schema_version"] == "vaevas-native-execution-profile-v1"
    assert report["claim_scope"] == "execution_profile_not_model_quality"
    assert report["comparison"]["submission_and_verdict_stable"] is True
    by_workers = {run["workers"]: run for run in report["runs"]}
    assert by_workers[1]["peak_active_cells"] == 1
    assert by_workers[2]["peak_active_cells"] >= 2
    for run in report["runs"]:
        assert run["cell_count"] == 4
        assert run["terminal_count"] == 4
        assert run["throughput_cells_per_s"] > 0
        assert run["resources"]["cpu_peak"] is None
        assert run["resources"]["ram_peak_bytes"] is None
        assert run["resources"]["peak_containers"] is None
        assert [cell["cell_id"] for cell in run["cells"]] == [cell["cell_id"] for cell in _cells()]
        assert all(cell["queue_delay_s"] >= 0 for cell in run["cells"])
        assert all(cell["phase_timing"]["cell_id"] == cell["cell_id"] for cell in run["cells"])
        assert all("model" in cell["phase_timing"]["phases"] for cell in run["cells"])


def test_profile_rejects_missing_duplicate_and_drifting_results(tmp_path):
    def duplicated_executor(cell: dict, context: profile.CellExecutionContext) -> dict:
        row = _stable_executor(cell, context)
        row["cell_id"] = "cell-000"
        return row

    with pytest.raises(ValueError, match="failed"):
        profile.profile_workload(tmp_path / "duplicate", cells=_cells(2), worker_counts=(1,), execute_cell=duplicated_executor)

    def drifting_executor(cell: dict, context: profile.CellExecutionContext) -> dict:
        row = _stable_executor(cell, context)
        row["submission_files"]["model.va"] += f":workers={context.workers}"
        return row

    with pytest.raises(ValueError, match="differs across workers"):
        profile.profile_workload(tmp_path / "drift", cells=_cells(2), worker_counts=(1, 2), execute_cell=drifting_executor)


def test_cli_fixture_writes_report_without_credentials_or_live_models(tmp_path, capsys):
    output = tmp_path / "reports"
    assert profile.main(["--output-root", str(output), "--fixture", "--workers", "1,2"]) == 0
    captured = json.loads(capsys.readouterr().out)
    report_path = output / "native-execution-profile.json"
    report = json.loads(report_path.read_text())
    assert captured["report_sha256"] == profile.sha256_file(report_path)
    assert report["workload"]["provider"] == "deterministic_fixture"
    assert report["workload"]["live_model_calls"] == 0
    assert report["comparison"]["submission_and_verdict_stable"] is True


@pytest.mark.parametrize("field,value", [("cell_id", "wrong-cell"), ("attempt_id", "wrong-attempt"),
                                        ("submission_files", {}), ("verdict", {}),
                                        ("submission_tree_sha256", None)])
def test_profile_rejects_unbound_or_empty_evidence(tmp_path, field, value):
    def invalid(cell, context):
        return {**_stable_executor(cell, context), field: value}
    with pytest.raises(ValueError, match="failed"):
        profile.profile_workload(tmp_path / "invalid", cells=_cells(1), execute_cell=invalid)


def test_profile_never_overwrites_or_leaks_exception_payloads(tmp_path):
    root = tmp_path / "once"
    profile.profile_workload(root, cells=_cells(1), execute_cell=_stable_executor)
    before = (root / "native-execution-profile.json").read_bytes()
    with pytest.raises(FileExistsError):
        profile.profile_workload(root, cells=_cells(1), execute_cell=_stable_executor)
    assert (root / "native-execution-profile.json").read_bytes() == before
    def broken(cell, context):
        raise RuntimeError("PRIVATE_SENTINEL")
    with pytest.raises(ValueError) as caught:
        profile.profile_workload(tmp_path / "broken", cells=_cells(1), execute_cell=broken)
    assert "PRIVATE_SENTINEL" not in str(caught.value)


def test_profile_exports_only_structural_verdict(tmp_path):
    def enriched(cell, context):
        row = _stable_executor(cell, context)
        row["verdict"]["private"] = "PRIVATE_SENTINEL"
        return row
    report = profile.profile_workload(tmp_path / "safe", cells=_cells(1), execute_cell=enriched)
    assert "PRIVATE_SENTINEL" not in json.dumps(report)
