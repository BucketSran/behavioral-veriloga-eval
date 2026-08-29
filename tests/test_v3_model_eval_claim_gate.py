from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

import run_vabench_v3_model_eval as runner  # noqa: E402
from run_vabench_v3_model_eval import (  # noqa: E402
    EXPLORATORY_SCOPE,
    FORMAL_SCORE_SCOPE,
    write_summary,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def args_for(
    *,
    roster: Path,
    environment_evidence: Path,
    claim_scope: str,
    selection_surface: str = "counted",
) -> argparse.Namespace:
    return argparse.Namespace(
        model="fixture-model",
        stage="score",
        selection_surface=selection_surface,
        dry_run=False,
        score_roster=str(roster),
        claim_scope=claim_scope,
        environment_evidence=str(environment_evidence),
        evas_command="evas",
        persistent_evas_worker=False,
        score_workers=1,
        score_timeout_s=180,
        task=[],
        task_file=[],
        level=[],
        track=[],
        difficulty=[],
        category=[],
        exclude_spectre_divergent=False,
        limit=None,
    )


def counted_row() -> dict:
    return {
        "release_entry_id": "001-example",
        "task_id": "v3_001_example",
        "level": "L1",
        "track": "core",
        "category": "logic",
        "counted_in_score": True,
    }


def score(status: str) -> dict:
    return {
        "task_slug": "001-example",
        "task_id": "v3_001_example",
        "status": status,
        "evas_identity": dict(runner.EXPECTED_EVAS_IDENTITY),
        "scores": {
            "dut_compile": 1.0 if status == "PASS" else 0.0,
            "tb_compile": 1.0 if status == "PASS" else 0.0,
            "sim_correct": 1.0 if status == "PASS" else 0.0,
            "weighted_total": 1.0 if status == "PASS" else 0.0,
        },
        "required_score_axes": ["dut_compile", "tb_compile", "sim_correct"],
    }


def clean_repository() -> dict:
    return {
        "status": "available",
        "commit": "a" * 40,
        "dirty": False,
    }


def verified_environment() -> dict:
    return {
        "schema_version": "vabench-evaluator-environment-verification-v1",
        "status": "pass",
        "source": {
            "repository": {
                "status": "available",
                "commit": "a" * 40,
                "dirty": False,
            }
        },
        "live_python": {"status": "pass", "observed_version": "3.11.13"},
        "live_evas": {
            "status": "pass",
            "command": "evas",
            "observed": dict(runner.EXPECTED_EVAS_IDENTITY),
        },
    }


def scoring_args(*, generated_root: Path) -> argparse.Namespace:
    return argparse.Namespace(
        model="fixture-model",
        sample_idx=0,
        resume=False,
        generated_root=generated_root,
        score_timeout_s=10,
        selection_surface="candidate",
        temperature=0.0,
        top_p=1.0,
    )


def test_formal_claim_requires_and_indexes_complete_executed_evidence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    roster = tmp_path / "roster.json"
    environment = tmp_path / "environment.json"
    output_root = tmp_path / "run"
    write_json(roster, {"form_rows": [counted_row()]})
    write_json(environment, verified_environment())
    write_json(output_root / "evas_results" / "001-example" / "result.json", score("PASS"))
    monkeypatch.setattr(runner, "DEFAULT_SCORE_ROSTER", roster)

    summary = write_summary(
        rows=[counted_row()],
        generation=[],
        scores=[score("PASS")],
        output_root=output_root,
        args=args_for(
            roster=roster,
            environment_evidence=environment,
            claim_scope=FORMAL_SCORE_SCOPE,
        ),
        current_repository=clean_repository(),
        executed_python_version=runner.EXPECTED_PYTHON_VERSION,
    )

    assert summary["status"] == "completed"
    assert summary["claim_allowed"] is True
    assert summary["claim_gate"]["status"] == "allowed"
    assert summary["claim_gate"]["formal_judge"] == "pinned_strict_evas"
    assert summary["claim_gate"]["spectre_required"] is False
    assert summary["provenance"]["inputs"]["score_roster"]["sha256"]
    assert summary["provenance"]["score_results"][0]["result"]["sha256"]


def test_exploratory_scope_and_infrastructure_failure_block_claim(tmp_path: Path) -> None:
    roster = tmp_path / "roster.json"
    environment = tmp_path / "environment.json"
    output_root = tmp_path / "run"
    write_json(roster, {"form_rows": [counted_row()]})
    write_json(environment, verified_environment())
    write_json(
        output_root / "evas_results" / "001-example" / "result.json",
        score("FAIL_INFRA"),
    )

    summary = write_summary(
        rows=[counted_row()],
        generation=[],
        scores=[score("FAIL_INFRA")],
        output_root=output_root,
        args=args_for(
            roster=roster,
            environment_evidence=environment,
            claim_scope=EXPLORATORY_SCOPE,
        ),
        current_repository=clean_repository(),
        executed_python_version=runner.EXPECTED_PYTHON_VERSION,
    )

    assert summary["status"] == "completed_with_infrastructure_failures"
    assert summary["claim_allowed"] is False
    assert summary["claim_gate"]["blocking_reasons"] == [
        "claim_scope_is_exploratory",
        "score_evidence_has_infrastructure_failure",
    ]


def test_missing_environment_and_candidate_surface_block_formal_claim(tmp_path: Path) -> None:
    roster = tmp_path / "roster.json"
    output_root = tmp_path / "run"
    write_json(roster, {"form_rows": [counted_row()]})
    write_json(output_root / "evas_results" / "001-example" / "result.json", score("PASS"))

    summary = write_summary(
        rows=[counted_row()],
        generation=[],
        scores=[score("PASS")],
        output_root=output_root,
        args=args_for(
            roster=roster,
            environment_evidence=tmp_path / "missing.json",
            claim_scope=FORMAL_SCORE_SCOPE,
            selection_surface="candidate",
        ),
        current_repository=clean_repository(),
        executed_python_version=runner.EXPECTED_PYTHON_VERSION,
    )

    assert summary["claim_allowed"] is False
    assert "selection_surface_is_not_counted" in summary["claim_gate"]["blocking_reasons"]
    assert "environment_evidence_missing" in summary["claim_gate"]["blocking_reasons"]


def test_score_one_records_missing_sample_as_infrastructure_failure(tmp_path: Path) -> None:
    row = {
        **counted_row(),
        "target_artifacts": ["candidate.va"],
        "form": "dut",
        "difficulty": "D1",
    }

    result = runner.score_one(
        row,
        scoring_args(generated_root=tmp_path / "generated"),
        tmp_path / "scores",
    )

    assert result["status"] == "FAIL_INFRA"
    assert result["failure_class"] == "infrastructure"
    assert result["termination_reason"] == "missing_generated_sample"
    saved = json.loads(
        (tmp_path / "scores" / "001-example" / "result.json").read_text(encoding="utf-8")
    )
    assert saved["status"] == "FAIL_INFRA"


def test_score_one_records_candidate_and_hidden_evidence(tmp_path: Path, monkeypatch) -> None:
    task_root = tmp_path / "task"
    hidden = task_root / "test_hidden" / "hidden.scs"
    hidden.parent.mkdir(parents=True)
    hidden.write_text("simulator lang=spectre\n", encoding="utf-8")
    generated_root = tmp_path / "generated"
    sample = generated_root / "fixture-model" / "001-example" / "sample_0"
    sample.mkdir(parents=True)
    (sample / "candidate.va").write_text("module candidate; endmodule\n", encoding="utf-8")
    monkeypatch.setattr(runner, "task_dir", lambda _slug: task_root)
    def fake_run_case(*_args, **kwargs):
        output_root = kwargs["output_root"]
        output_root.mkdir(parents=True)
        write_json(output_root / "evas_identity.json", runner.EXPECTED_EVAS_IDENTITY)
        return {
            "status": "PASS",
            "checker_task_id": "v3_001_example",
            "scores": {
                "dut_compile": 1.0,
                "tb_compile": 1.0,
                "sim_correct": 1.0,
                "weighted_total": 1.0,
            },
            "notes": [],
            "timing": {},
        }

    monkeypatch.setattr(runner, "run_case", fake_run_case)
    row = {
        **counted_row(),
        "target_artifacts": ["candidate.va"],
        "form": "dut",
        "difficulty": "D1",
    }

    result = runner.score_one(
        row,
        scoring_args(generated_root=generated_root),
        tmp_path / "scores",
    )

    assert result["status"] == "PASS"
    assert result["failure_class"] is None
    assert result["evidence_artifacts"]["candidate"]["sha256"]
    assert result["evidence_artifacts"]["hidden_testbench"]["sha256"]
    assert result["claim_allowed"] is False


def test_score_one_reclassifies_missing_runtime_identity_as_infrastructure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    task_root = tmp_path / "task"
    hidden = task_root / "test_hidden" / "hidden.scs"
    hidden.parent.mkdir(parents=True)
    hidden.write_text("simulator lang=spectre\n", encoding="utf-8")
    generated_root = tmp_path / "generated"
    sample = generated_root / "fixture-model" / "001-example" / "sample_0"
    sample.mkdir(parents=True)
    (sample / "candidate.va").write_text("module candidate; endmodule\n", encoding="utf-8")
    monkeypatch.setattr(runner, "task_dir", lambda _slug: task_root)
    monkeypatch.setattr(
        runner,
        "run_case",
        lambda *_args, **_kwargs: {
            "status": "FAIL_DUT_COMPILE",
            "notes": ["strict_spectre_lint_error=FileNotFoundError: evas"],
        },
    )
    row = {**counted_row(), "target_artifacts": ["candidate.va"], "form": "dut"}

    result = runner.score_one(row, scoring_args(generated_root=generated_root), tmp_path / "scores")

    assert result["status"] == "FAIL_INFRA"
    assert result["failure_class"] == "infrastructure"
    assert result["termination_reason"] == "evaluator_runtime_unavailable"


def test_formal_claim_blocks_filtered_denominator_and_dirty_source(tmp_path: Path) -> None:
    roster = tmp_path / "roster.json"
    environment = tmp_path / "environment.json"
    output_root = tmp_path / "run"
    second_row = {**counted_row(), "release_entry_id": "002-example", "task_id": "v3_002_example"}
    write_json(roster, {"form_rows": [counted_row(), second_row]})
    dirty_environment = verified_environment()
    dirty_environment["source"]["repository"]["dirty"] = True
    write_json(environment, dirty_environment)
    write_json(output_root / "evas_results" / "001-example" / "result.json", score("PASS"))
    args = args_for(
        roster=roster,
        environment_evidence=environment,
        claim_scope=FORMAL_SCORE_SCOPE,
    )
    args.task = ["001-example"]

    summary = write_summary(
        rows=[counted_row()],
        generation=[],
        scores=[score("PASS")],
        output_root=output_root,
        args=args,
        current_repository=clean_repository(),
        executed_python_version=runner.EXPECTED_PYTHON_VERSION,
    )

    assert summary["claim_allowed"] is False
    assert "formal_denominator_is_filtered" in summary["claim_gate"]["blocking_reasons"]
    assert "formal_denominator_is_incomplete" in summary["claim_gate"]["blocking_reasons"]
    assert "formal_score_roster_is_not_canonical" in summary["claim_gate"]["blocking_reasons"]
    assert "environment_source_is_dirty" in summary["claim_gate"]["blocking_reasons"]


def test_formal_claim_binds_evas_command_and_disables_persistent_worker(tmp_path: Path) -> None:
    roster = tmp_path / "roster.json"
    environment = tmp_path / "environment.json"
    output_root = tmp_path / "run"
    write_json(roster, {"form_rows": [counted_row()]})
    write_json(environment, verified_environment())
    write_json(output_root / "evas_results" / "001-example" / "result.json", score("PASS"))
    args = args_for(
        roster=roster,
        environment_evidence=environment,
        claim_scope=FORMAL_SCORE_SCOPE,
    )
    args.evas_command = "/different/evas"
    args.persistent_evas_worker = True

    summary = write_summary(
        rows=[counted_row()],
        generation=[],
        scores=[score("PASS")],
        output_root=output_root,
        args=args,
        current_repository=clean_repository(),
        executed_python_version=runner.EXPECTED_PYTHON_VERSION,
    )

    assert summary["claim_allowed"] is False
    assert "executed_evas_command_not_bound_to_environment_evidence" in summary["claim_gate"]["blocking_reasons"]
    assert "persistent_evas_worker_not_allowed_for_formal_claim" in summary["claim_gate"]["blocking_reasons"]


def test_formal_claim_blocks_stale_source_and_invalid_metrics(tmp_path: Path) -> None:
    roster = tmp_path / "roster.json"
    environment = tmp_path / "environment.json"
    output_root = tmp_path / "run"
    invalid_score = score("PASS")
    del invalid_score["scores"]["weighted_total"]
    write_json(roster, {"form_rows": [counted_row()]})
    write_json(environment, verified_environment())
    write_json(
        output_root / "evas_results" / "001-example" / "result.json",
        invalid_score,
    )

    summary = write_summary(
        rows=[counted_row()],
        generation=[],
        scores=[invalid_score],
        output_root=output_root,
        args=args_for(
            roster=roster,
            environment_evidence=environment,
            claim_scope=FORMAL_SCORE_SCOPE,
        ),
        current_repository={
            "status": "available",
            "commit": "b" * 40,
            "dirty": False,
        },
        executed_python_version=runner.EXPECTED_PYTHON_VERSION,
    )

    assert summary["claim_allowed"] is False
    assert "score_evidence_metrics_invalid" in summary["claim_gate"]["blocking_reasons"]
    assert "score_status_metrics_inconsistent" in summary["claim_gate"]["blocking_reasons"]
    assert "environment_source_commit_is_stale" in summary["claim_gate"]["blocking_reasons"]


def test_formal_claim_blocks_out_of_range_and_inconsistent_weighted_score(
    tmp_path: Path,
) -> None:
    roster = tmp_path / "roster.json"
    environment = tmp_path / "environment.json"
    output_root = tmp_path / "run"
    corrupt_score = score("PASS")
    corrupt_score["scores"]["dut_compile"] = 2.0
    corrupt_score["scores"]["weighted_total"] = 0.5
    write_json(roster, {"form_rows": [counted_row()]})
    write_json(environment, verified_environment())
    write_json(
        output_root / "evas_results" / "001-example" / "result.json",
        corrupt_score,
    )

    summary = write_summary(
        rows=[counted_row()],
        generation=[],
        scores=[corrupt_score],
        output_root=output_root,
        args=args_for(
            roster=roster,
            environment_evidence=environment,
            claim_scope=FORMAL_SCORE_SCOPE,
        ),
        current_repository=clean_repository(),
        executed_python_version=runner.EXPECTED_PYTHON_VERSION,
    )

    assert summary["claim_allowed"] is False
    assert "score_evidence_metrics_invalid" in summary["claim_gate"]["blocking_reasons"]
    assert "score_status_metrics_inconsistent" in summary["claim_gate"]["blocking_reasons"]
