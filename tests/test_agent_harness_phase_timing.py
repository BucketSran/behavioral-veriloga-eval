"""Optional timing measures execution without changing its result or failures."""

import pytest
from concurrent.futures import ThreadPoolExecutor
import json

from test_agent_harness_native_episode import native_case as native_case  # noqa: F401
from test_agent_harness_production_public_validation import public_case as public_case  # noqa: F401

from runners.agent_harness.phase_timing import collect_phases, measure_phase


def test_nested_phase_work_is_not_episode_wall_time():
    with collect_phases(cell_id="cell-1", attempt_id="attempt-1") as capture:
        with measure_phase("cell"):
            with measure_phase("model"):
                value = 42
    report = capture.to_document()
    assert value == 42
    assert report["cell_id"] == "cell-1"
    assert report["attempt_id"] == "attempt-1"
    assert report["elapsed_s"] >= report["phases"]["cell"]["work_s"]
    assert report["phases"]["model"]["count"] == 1
    assert "final_judge" not in report["phases"]
    assert all(span["duration_s"] >= 0 for span in report["spans"])
    assert all(span["status"] == "ok" for span in report["spans"])


def test_failure_keeps_exception_identity_without_payload():
    failure = TimeoutError("PRIVATE_PROVIDER_PAYLOAD")
    with collect_phases(cell_id="c", attempt_id="a") as capture:
        with pytest.raises(TimeoutError) as raised:
            with measure_phase("model"):
                raise failure
    assert raised.value is failure
    report = capture.to_document()
    assert report["spans"][0]["error_type"] == "TimeoutError"
    assert "PRIVATE_PROVIDER_PAYLOAD" not in json.dumps(report)
    with measure_phase("model"):
        pass
    assert capture.to_document() == report


def test_thread_and_nested_capture_do_not_mix_attempts():
    def run(number):
        with collect_phases(cell_id=f"cell-{number}", attempt_id=f"attempt-{number}") as outer:
            with measure_phase("cell"):
                with collect_phases(cell_id="child", attempt_id="child") as child:
                    with measure_phase("model"):
                        pass
                with measure_phase("tool"):
                    pass
        assert set(child.to_document()["phases"]) == {"model"}
        return outer.to_document()
    with ThreadPoolExecutor(max_workers=4) as pool:
        reports = list(pool.map(run, range(8)))
    assert [report["cell_id"] for report in reports] == [f"cell-{i}" for i in range(8)]
    assert all(set(report["phases"]) == {"cell", "tool"} for report in reports)


def test_real_native_entry_records_boundaries_without_changing_evidence(native_case):  # noqa: F811
    from test_agent_harness_native_launcher import (
        test_prepared_launcher_joins_provider_bash_freeze_and_final_result as exercise,
    )
    with collect_phases(cell_id="cell-001", attempt_id="attempt-001") as capture:
        exercise(native_case)
    report = capture.to_document()
    assert report["phases"]["model"]["count"] == 3
    assert report["phases"]["tool"]["count"] == 3
    assert report["phases"]["freeze"]["count"] == 1
    assert report["phases"]["final_judge"]["count"] == 1
    assert report["phases"]["setup"]["count"] == 1
    assert "FINAL_JUDGE_SENTINEL" not in json.dumps(report)
