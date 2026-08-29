from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_v3_clean_room_smoke.py"


def load_smoke_module():
    sys.path.insert(0, str(ROOT / "runners"))
    spec = importlib.util.spec_from_file_location("run_v3_clean_room_smoke", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_clean_room_smoke_uses_one_public_task_and_hidden_scorer(tmp_path, monkeypatch) -> None:
    smoke = load_smoke_module()
    output_root = tmp_path / "score-output"
    report_path = tmp_path / "smoke.json"
    calls = []

    def fake_score_one(row, args, output_root_arg):
        calls.append((row, args, output_root_arg))
        result_path = output_root_arg / row["release_entry_id"] / "result.json"
        result_path.parent.mkdir(parents=True)
        result = {
            "status": "PASS",
            "task_slug": row["release_entry_id"],
            "task_id": row["task_id"],
            "scores": {
                "dut_compile": 1.0,
                "tb_compile": 1.0,
                "sim_correct": 1.0,
                "weighted_total": 1.0,
            },
            "evidence_artifacts": {
                "hidden_testbench": {
                    "path": "benchmark-vabench-release-v3/tasks/014-sar-logic/test_hidden/tests/tb_sar_logic_4b_ref.scs",
                    "exists": True,
                }
            },
        }
        result_path.write_text(json.dumps(result), encoding="utf-8")
        return result

    monkeypatch.setattr(smoke.v3_eval, "score_one", fake_score_one)
    rc = smoke.main(
        [
            "--task",
            "014",
            "--output-root",
            str(output_root),
            "--out",
            str(report_path),
            "--json",
        ]
    )

    assert rc == 2
    assert len(calls) == 1
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["status"] == "PASS"
    assert payload["task"]["release_entry_id"] == "014-sar-logic"
    assert payload["clean_room_contract"]["private_paths_absent"] is True
    assert payload["clean_room_contract"]["forbidden_private_paths"] == []
    assert payload["cleanup"]["pre_cleanup_exists"] is True
    assert payload["cleanup"]["post_cleanup_exists"] is False
    assert payload["claim_allowed"] is False
    assert payload["failure"] is None
    assert "test_hidden" in payload["score"]["evidence_artifacts"]["hidden_testbench"]["path"]

    generated_root = calls[0][1].generated_root
    assert generated_root.name == "generated"
    clean_room_files = set(payload["clean_room_contract"]["visible_to_candidate"])
    assert clean_room_files == {"task/instruction.md", "task/starter/*", "submission/*"}


def test_clean_room_manifest_rejects_private_directory_names(tmp_path) -> None:
    smoke = load_smoke_module()
    clean_room = tmp_path / "room"
    (clean_room / "task").mkdir(parents=True)
    (clean_room / "task" / "instruction.md").write_text("public\n", encoding="utf-8")
    (clean_room / "test_hidden").mkdir()
    (clean_room / "test_hidden" / "hidden.scs").write_text("private\n", encoding="utf-8")

    manifest = smoke.clean_room_manifest(clean_room)

    assert manifest["private_paths_absent"] is False
    assert manifest["forbidden_private_paths"] == ["test_hidden/hidden.scs"]


def test_deterministic_fixture_adapter_requires_fixture_candidate(tmp_path) -> None:
    smoke = load_smoke_module()
    task_dir = tmp_path / "task"
    task_dir.mkdir()

    try:
        smoke.deterministic_candidate_source(task_dir, ["candidate.va"], "fixture", None)
    except ValueError as exc:
        assert "--fixture-candidate is required" in str(exc)
    else:
        raise AssertionError("fixture adapter without a fixture path should fail")


def test_failure_evidence_reclassifies_missing_rust_core_as_infrastructure() -> None:
    smoke = load_smoke_module()

    failure = smoke.failure_evidence(
        {
            "status": "FAIL_DUT_COMPILE",
            "failure_class": "candidate",
            "termination_reason": "fail_dut_compile",
            "evas_notes": [
                "returncode=1",
                "simulator_error=EVAS does not fall back to the Python simulation engine.",
            ],
            "evas_identity": {
                "rust_core_loadable": False,
                "rust_core_error": "Rust backend library not found",
            },
        }
    )

    assert failure is not None
    assert failure["runner_failure_class"] == "candidate"
    assert failure["smoke_failure_class"] == "infrastructure"
