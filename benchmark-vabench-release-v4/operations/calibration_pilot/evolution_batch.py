"""Outer batch recovery helpers for the Evolution campaign CLI."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any

import result_protocol
from native_episode import read_final_score_receipt
from runners.agent_harness import EpisodeContext, FrozenSubmission
from runners.agent_harness.authority_profiles import final_test_profile_sha256, public_validation_profile_sha256
from runners.agent_harness.batch_resume import file_sha256


TERMINAL_STATUSES = {
    "completed",
    "evolution_failed",
    "final_failed",
    "public_cleanup_failed",
    "setup_failed",
}


def attempt_id(cell_id: str, index: int) -> str:
    return f"{cell_id}-evolution-attempt-{index:04d}"


def attempt_dir(cell_runtime: Path, index: int) -> Path:
    return cell_runtime / f"attempt-{index:04d}"


def attempt_records(
    cell_runtime: Path,
    *,
    expected_source_cell_id: str,
    expected_campaign: Mapping[str, Any],
    max_attempts: int | None = None,
) -> list[dict[str, Any]]:
    if cell_runtime.is_symlink():
        raise ValueError("batch cell attempt path must not be a symlink")
    if not cell_runtime.exists():
        return []
    records = []
    attempts = sorted(cell_runtime.iterdir())
    if max_attempts is not None and len(attempts) > max_attempts:
        raise ValueError("Evolution batch attempt cap exceeded")
    for offset, path in enumerate(attempts, start=1):
        if path.name != f"attempt-{offset:04d}" or path.is_symlink() or not path.is_dir():
            raise ValueError("batch cell attempt path is not a directory")
        if records and not records[-1]["safe_setup_retry"]:
            raise ValueError("Evolution attempt has an unsafe retry predecessor")
        index = offset
        campaign = _read_attempt_campaign(path)
        expected_parent = attempt_id(expected_source_cell_id, index - 1) if index > 1 else None
        if campaign.get("parent_attempt_id") != expected_parent:
            raise ValueError("Evolution attempt parent lineage mismatch")
        comparable = {key: value for key, value in campaign.items()
                      if key not in {"dry_run", "parent_attempt_id"}}
        expected_comparable = {key: value for key, value in expected_campaign.items()
                               if key not in {"dry_run", "parent_attempt_id"}}
        if comparable != expected_comparable:
            raise ValueError("Evolution attempt campaign identity mismatch")
        final_path = path / "run/final-result.json"
        if final_path.exists():
            final = validate_terminal_result(
                path / "run",
                expected_source_cell_id=expected_source_cell_id,
                expected_campaign=campaign,
            )
            records.append({
                "attempt_id": attempt_id(expected_source_cell_id, index),
                "parent_attempt_id": campaign.get("parent_attempt_id"),
                "attempt_index": index,
                "path": path.name,
                "status": final["status"],
                "terminal_result_sha256": file_sha256(final_path),
                "safe_setup_retry": safe_setup_retry(path / "run", final),
            })
        else:
            records.append({
                "attempt_id": attempt_id(expected_source_cell_id, index),
                "parent_attempt_id": campaign.get("parent_attempt_id"),
                "attempt_index": index,
                "path": path.name,
                "status": "in_flight",
                "safe_setup_retry": False,
            })
    return records


def validate_terminal_result(
    run_dir: Path,
    *,
    expected_source_cell_id: str,
    expected_campaign: Mapping[str, Any],
) -> dict[str, Any]:
    final_path = run_dir / "final-result.json"
    if not final_path.is_file() or final_path.is_symlink():
        raise ValueError("Evolution terminal result is missing")
    final = _read_document(final_path)
    if final.get("schema_version") != "vaevas-native-evolution-final-result-v1":
        raise ValueError("Evolution terminal result schema mismatch")
    status = final.get("status")
    if status not in TERMINAL_STATUSES:
        raise ValueError("Evolution terminal status is not recognized")
    config, config_sha = _validated_config(run_dir, expected_campaign)
    if final.get("campaign_config_sha256") != config_sha:
        raise ValueError("Evolution terminal config hash mismatch")
    request_path = run_dir / "request.json"
    if status != "setup_failed":
        if not request_path.is_file() or request_path.is_symlink():
            raise ValueError("Evolution terminal result is missing request evidence")
        request = _read_document(request_path)
        if (request.get("schema_version") != "vaevas-native-evolution-request-v1"
                or request.get("config") != config or request.get("campaign_config_sha256") != config_sha):
            raise ValueError("Evolution request config mismatch")
        if request.get("campaign_file_sha256") != file_sha256(run_dir.parent / "campaign.json"):
            raise ValueError("Evolution request campaign hash mismatch")
        if request.get("cell") != expected_campaign.get("cell"):
            raise ValueError("Evolution request cell identity mismatch")
    if status == "completed":
        _validate_completed_result(
            run_dir,
            final,
            expected_source_cell_id=expected_source_cell_id,
            expected_campaign=expected_campaign,
        )
    return final


def safe_setup_retry(run_dir: Path, final: Mapping[str, Any]) -> bool:
    """A retry is allowed only before branch/model/final activity began."""
    try:
        from run_native_evolution import _canonical_sha256, _evolution_evidence_summary
        if (run_dir.is_symlink()
                or {path.name for path in run_dir.iterdir()} != {"setup-request.json", "final-result.json"}
                or any(path.is_symlink() for path in run_dir.iterdir())):
            return False
        setup = _read_document(run_dir / "setup-request.json")
        summary = _evolution_evidence_summary(run_dir)
        return (
            final.get("status") == "setup_failed"
            and final.get("failure_phase") == "setup" and final.get("failure_retryable") is True
            and all(final.get(key) is None for key in (
                "manifest_sha256", "selected_candidate", "final_judgment", "score_sidecar_receipt",
                "branch_usage", "branch_record_count",
            ))
            and setup.get("schema_version") == "vaevas-native-evolution-setup-v1"
            and setup.get("campaign_file_sha256") == file_sha256(run_dir.parent / "campaign.json")
            and _canonical_sha256(setup["config"]) == final.get("campaign_config_sha256")
            and all(final.get(key) == summary[key] for key in (
                "denominator", "all_branch_costs", "branch_evidence", "source",
            ))
        )
    except (ValueError, TypeError, KeyError, OSError, AttributeError):
        return False


def row_from_terminal(
    *,
    source_cell_id: str,
    cell_runtime: Path,
    terminal_attempt_dir: Path,
    attempts: Sequence[Mapping[str, Any]],
    expected_campaign: Mapping[str, Any],
    batch_reuse: bool,
) -> dict[str, Any]:
    final = validate_terminal_result(
        terminal_attempt_dir / "run",
        expected_source_cell_id=source_cell_id,
        expected_campaign=expected_campaign,
    )
    judgment = final.get("final_judgment")
    return {
        "schema_version": "vaevas-evolution-batch-row-v1",
        "cell_id": source_cell_id,
        "source_cell_id": source_cell_id,
        "status": "completed" if final["status"] != "setup_failed" else "blocked",
        "terminal_status": final["status"],
        "final_judgment_status": judgment.get("status") if isinstance(judgment, Mapping) else None,
        "score": judgment.get("score") if isinstance(judgment, Mapping) else None,
        "judge_engine": judgment.get("judge_engine") if isinstance(judgment, Mapping) else None,
        "runtime": cell_runtime.name,
        "terminal_attempt_id": attempt_id(source_cell_id, int(terminal_attempt_dir.name.rsplit("-", 1)[1])),
        "terminal_result_sha256": file_sha256(terminal_attempt_dir / "run/final-result.json"),
        "batch_reuse": batch_reuse,
        "attempts": [dict(attempt) for attempt in attempts],
    }


def setup_retry_row(
    *,
    source_cell_id: str,
    cell_runtime: Path,
    attempts: Sequence[Mapping[str, Any]],
    reason: str,
) -> dict[str, Any]:
    return {
        "schema_version": "vaevas-evolution-batch-row-v1",
        "cell_id": source_cell_id,
        "source_cell_id": source_cell_id,
        "status": "retryable_setup_failed",
        "block_reason": reason,
        "runtime": cell_runtime.name,
        "batch_reuse": False,
        "attempts": [dict(attempt) for attempt in attempts],
    }


def blocked_row(
    *,
    source_cell_id: str,
    cell_runtime: Path,
    reason: str,
    attempts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "vaevas-evolution-batch-row-v1",
        "cell_id": source_cell_id,
        "source_cell_id": source_cell_id,
        "status": "blocked",
        "block_reason": reason,
        "runtime": cell_runtime.name,
        "batch_reuse": False,
        "attempts": [dict(attempt) for attempt in attempts],
    }


def prepared_row(source_cell_id: str) -> dict[str, Any]:
    return {
        "schema_version": "vaevas-evolution-batch-row-v1",
        "cell_id": source_cell_id,
        "source_cell_id": source_cell_id,
        "status": "prepared",
        "batch_reuse": False,
        "attempts": [],
    }


def _read_document(path: Path) -> dict[str, Any]:
    if not path.is_file() or any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("Evolution evidence must be a regular confined file")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Evolution evidence must be an object")
    return value


def _validated_config(run_dir: Path, campaign: Mapping[str, Any]) -> tuple[dict, str]:
    # Reconstruct with the existing engine builder, without constructing clients.
    import run_native_evolution as engine
    setup = _read_document(run_dir / "setup-request.json")
    config = setup.get("config")
    if setup.get("schema_version") != "vaevas-native-evolution-setup-v1" or not isinstance(config, dict):
        raise ValueError("Evolution setup config is missing")
    campaign_sha = file_sha256(run_dir.parent / "campaign.json")
    if setup.get("campaign_file_sha256") != campaign_sha:
        raise ValueError("Evolution setup campaign hash mismatch")
    for field, identity in (("command", "final_command_sha256"), ("evas_command", "evas_command_sha256")):
        value = config.get(field)
        if not isinstance(value, str) or hashlib.sha256(value.encode()).hexdigest() != campaign.get(identity):
            raise ValueError("Evolution command identity mismatch")
    backend_sha = engine.backend_profile_sha256(engine._backend_profile("native-reasoning"))
    branches = [engine.NativeEvolutionBranch(
        item["branch_id"], item["model"], backend_sha, lambda: None,
    ) for item in campaign["branches"]]
    expected = engine._native_evolution_config_document(
        cell=campaign["cell"], release=engine.runner.DEFAULT_RELEASE,
        output_dir=run_dir.resolve(), branches=branches, condition=campaign["condition"],
        budgets=campaign["per_branch_budgets"], rounds=campaign["rounds"],
        max_steps=campaign["per_branch_budgets"]["model_calls"],
        timeout_s=campaign["timeout_s"], request_timeout_s=campaign["request_timeout_s"],
        branch_sandbox_backend=campaign["branch_sandbox_backend"],
        branch_docker_image=campaign["branch_docker_image"],
        public_validation_docker_image=campaign["public_validation_docker_image"],
        command=config["command"], evas_command=config["evas_command"],
        campaign_file_sha256=campaign_sha,
    )
    expected["declared_information_surface"] = engine.runner.declared_information_surface(
        campaign["condition"], evolution=True,
    )
    if config != expected:
        raise ValueError("Evolution config differs from the frozen attempt campaign")
    return config, engine._canonical_sha256(config)


def _validate_completed_result(
    run_dir: Path,
    final: Mapping[str, Any],
    *,
    expected_source_cell_id: str,
    expected_campaign: Mapping[str, Any],
) -> None:
    request = _read_document(run_dir / "request.json")
    public_profile = _read_document(run_dir / "public-validation-profile.json")
    final_profile = _read_document(run_dir / "final-test-profile.json")
    if request.get("manifest_sha256") != final.get("manifest_sha256"):
        raise ValueError("Evolution final result manifest mismatch")
    if request.get("campaign_config_sha256") != final.get("campaign_config_sha256"):
        raise ValueError("Evolution final result config mismatch")
    if request.get("public_validation_profile_sha256") is None or request.get("final_test_profile_sha256") is None:
        raise ValueError("Evolution request lacks authority profile hashes")
    if final_test_profile_sha256(final_profile) != request["final_test_profile_sha256"]:
        raise ValueError("Evolution final profile hash mismatch")
    if public_validation_profile_sha256(public_profile) != request["public_validation_profile_sha256"]:
        raise ValueError("Evolution public profile hash mismatch")
    if any(public_profile.get(key) != final_profile.get(key) for key in (
        "benchmark_release", "benchmark_manifest_sha256",
    )):
        raise ValueError("Evolution authority profile benchmark mismatch")
    if public_profile.get("campaign_config_sha256") != final_profile.get("campaign_config_sha256"):
        raise ValueError("Evolution authority profile config mismatch")
    if final_profile.get("campaign_config_sha256") != final.get("campaign_config_sha256"):
        raise ValueError("Evolution final profile is not bound to the final config")
    if expected_campaign.get("source_cell_id") != expected_source_cell_id:
        raise ValueError("Evolution source cell identity mismatch")
    judgment = final.get("final_judgment")
    receipt = final.get("score_sidecar_receipt")
    if not isinstance(judgment, Mapping) or not isinstance(receipt, Mapping):
        raise ValueError("completed Evolution result requires final judgment and score sidecar")
    if judgment.get("judge_engine") != "evas":
        raise ValueError("completed Evolution result must bind the EVAS judge")
    submission = _frozen_submission_from_evidence(run_dir)
    selected = final.get("selected_candidate")
    if not isinstance(selected, Mapping):
        raise ValueError("completed Evolution result requires a selected candidate")
    if selected.get("candidate_tree_sha256") != submission.tree_sha256:
        raise ValueError("selected candidate does not match frozen submission evidence")
    if judgment.get("submission_tree_sha256") != submission.tree_sha256:
        raise ValueError("final judgment does not bind the frozen submission evidence")
    if receipt.get("submission_tree_sha256") != submission.tree_sha256:
        raise ValueError("score sidecar receipt does not bind the final submission")
    observed, _ = read_final_score_receipt(
        runtime=run_dir / "final-runtime", profile=final_profile,
        receipt=receipt, submission=submission,
        context=EpisodeContext(
            episode_id=f"{selected['candidate_id']}/final",
            attempt_id=f"{selected['candidate_id']}-final",
            task_id=expected_campaign["cell"]["task_id"], condition=expected_campaign["condition"],
            max_steps=None,
        ),
    )
    if asdict(observed) != judgment or isinstance(judgment.get("score"), bool):
        raise ValueError("Evolution judgment differs from its score sidecar")


def _frozen_submission_from_evidence(run_dir: Path) -> FrozenSubmission:
    root = run_dir / "final-runtime/evidence/final_submission"
    if root.is_symlink() or not root.is_dir():
        raise ValueError("frozen submission evidence is missing")
    if any(path.is_symlink() for path in root.rglob("*")):
        raise ValueError("frozen submission evidence must not contain symlinks")
    manifest = result_protocol.hash_test_tree(root)
    artifacts = tuple(sorted(row["path"] for row in manifest["files"]))
    if not artifacts:
        raise ValueError("frozen submission evidence must be nonempty")
    return FrozenSubmission(
        tree_sha256=str(manifest["tree_sha256"]),
        artifacts=artifacts,
    )


def _read_attempt_campaign(attempt_root: Path) -> dict[str, Any]:
    path = attempt_root / "campaign.json"
    if not path.is_file() or path.is_symlink():
        raise ValueError("Evolution attempt campaign is missing")
    return json.loads(path.read_text(encoding="utf-8"))
