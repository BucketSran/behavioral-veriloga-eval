from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "operations"
    / "tri_form_derivation_prep"
    / "audit_tri_form_reference_spectre.py"
)


@pytest.fixture(scope="module")
def audit():
    runners = str(ROOT / "runners")
    if runners not in sys.path:
        sys.path.insert(0, runners)
    spec = importlib.util.spec_from_file_location("audit_tri_form_reference_spectre", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_default_release_and_testbench_index_match_current_package(audit) -> None:
    assert audit.DEFAULT_RELEASE.name == "benchmarkv4"
    rows = audit.resolve_task_rows(audit.DEFAULT_RELEASE, [])

    assert len(rows) == 400
    assert {key: rows[0][key] for key in ("family_id", "form", "task_dir", "task_id")} == {
        "family_id": "001",
        "form": "testbench",
        "task_dir": "tasks/testbench/501-bang-bang-phase-detector-testbench",
        "task_id": "v4-501",
    }
    assert rows[0]["public_contract"] == "tasks/testbench/501-bang-bang-phase-detector-testbench/public_contract.json"

def test_resolve_task_rows_rejects_unknown_or_non_testbench_task(audit) -> None:
    with pytest.raises(SystemExit, match="unknown testbench task id"):
        audit.resolve_task_rows(audit.DEFAULT_RELEASE, ["v4-001"])


def test_checker_and_include_resolution_use_current_canonical_assets(audit) -> None:
    row = audit.resolve_task_rows(audit.DEFAULT_RELEASE, ["v4-501"])[0]
    task_dir = audit.DEFAULT_RELEASE / row["task_dir"]
    task_record = audit.read_json(task_dir / "task_record.json")
    tb_path = task_dir / "evaluator" / "reference_tb.scs"

    assert audit.checker_task_id(task_dir, task_record) == "v3_001_bang_bang_phase_detector"
    include_paths, missing = audit.include_paths_for_reference_tb(task_dir, tb_path)
    assert missing == []
    assert [path.name for path in include_paths] == ["bbpd_ref.va"]


def test_warning_extraction_classifies_known_infrastructure_noise(audit, tmp_path: Path) -> None:
    (tmp_path / "spectre.out").write_text(
        "WARNING (VACOMP-2435): benign compiler detail\n"
        "WARNING (CUSTOM-1): investigate this\n",
        encoding="utf-8",
    )

    warnings = audit.extract_warning_lines(
        tmp_path,
        {"warnings": ["remote_ahdlcmi_cache_prepare_failed rc=75"]},
    )

    assert len(warnings) == 3
    assert audit.is_benign_warning(warnings[0])
    assert audit.is_benign_warning(warnings[1])
    assert not audit.is_benign_warning(warnings[2])


def test_run_one_scores_reference_with_registered_checker(audit, tmp_path: Path, monkeypatch) -> None:
    row = audit.resolve_task_rows(audit.DEFAULT_RELEASE, ["v4-501"])[0]

    def fake_spectre_case(**kwargs):
        output_dir = kwargs["output_dir"]
        output_dir.mkdir(parents=True)
        (output_dir / "tran_spectre.csv").write_text("time,data\n0,0\n", encoding="utf-8")
        return {"ok": True, "status": "PASS", "warnings": [], "signals": ["data"], "rows": 1}

    monkeypatch.setattr(audit, "run_spectre_case", fake_spectre_case)
    monkeypatch.setattr(audit, "evaluate_behavior_with_timeout", lambda *args, **kwargs: (1.0, []))
    monkeypatch.setattr(audit, "validate_behavior_side_outputs", lambda *args, **kwargs: None)
    monkeypatch.setattr(audit, "behavior_side_output_names", lambda _checker_id: ())

    result = audit.run_one(
        release=audit.DEFAULT_RELEASE,
        row=row,
        output_root=tmp_path,
        spectre_backend="sui-direct",
        spectre_mode="ax",
        timeout_s=10,
        sui_host=None,
        sui_work_root=None,
        cadence_cshrc=None,
        keep_case_dirs=False,
    )

    assert result["status"] == "PASS"
    assert result["checker_task_id"] == "v3_001_bang_bang_phase_detector"
    assert result["behavior_score"] == 1.0
    assert not (tmp_path / "v4-501").exists()


def test_run_one_reports_unregistered_checker_without_starting_spectre(
    audit,
    tmp_path: Path,
    monkeypatch,
) -> None:
    row = audit.resolve_task_rows(audit.DEFAULT_RELEASE, ["v4-562"])[0]
    monkeypatch.setattr(
        audit,
        "run_spectre_case",
        lambda **_kwargs: pytest.fail("Spectre must not run without a registered checker"),
    )

    result = audit.run_one(
        release=audit.DEFAULT_RELEASE,
        row=row,
        output_root=tmp_path,
        spectre_backend="sui-direct",
        spectre_mode="ax",
        timeout_s=10,
        sui_host=None,
        sui_work_root=None,
        cadence_cshrc=None,
        keep_case_dirs=False,
    )

    assert result["status"] == "FAIL_CHECKER"
    assert "checker not registered" in result["notes"][0]
