"""Read-only result projections for the legacy/native workflow comparison."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

import final_replay
import score_campaign
from native_episode import read_final_score_receipt

from runners.agent_harness import EpisodeContext
from runners.agent_harness import final_test_profile_sha256

_LEGACY_SCHEMA = "vaevas-comparison-legacy-final-v1"
_HASH_RE = re.compile(r"[0-9a-f]{64}")
_CELL_IDENTITY = (
    "cell_id",
    "task_id",
    "family_id",
    "form",
    "mode",
    "experimental_arm",
)
_OPTIONAL_LEGACY_GENERATION = (
    "evidence/conversation_checkpoint.json",
    "evidence/mini_swe_trajectory.json",
)
_UNSTARTED_STATUSES = {"not_started"}


def read_backend_cell(
    runtime: Path,
    backend: str,
    cell: dict[str, Any],
    *,
    campaign_file_sha256: str,
    expected_image_id: str | None = None,
) -> dict[str, Any]:
    """Read one backend's existing evidence without executing a scorer."""
    if backend == "legacy":
        return read_legacy_cell(
            runtime,
            cell,
            campaign_file_sha256=campaign_file_sha256,
            expected_image_id=expected_image_id,
        )
    if backend in {"native-mini-swe", "native-reasoning"}:
        row = score_campaign.read_native_cell(
            runtime, cell, campaign_file_sha256=campaign_file_sha256,
        )
        if row.get("backend") != backend:
            raise ValueError("native evidence backend identity mismatch")
        if expected_image_id is not None:
            observed = _observed_image_id(row)
            if observed is None:
                observed = _read_native_manifest_image_id(runtime)
            if observed != expected_image_id:
                raise ValueError("observed image identity mismatch")
        return row
    raise ValueError(f"unsupported comparison backend: {backend}")


def read_legacy_cell(
    runtime: Path,
    cell: dict[str, Any],
    *,
    campaign_file_sha256: str,
    expected_image_id: str | None = None,
) -> dict[str, Any]:
    """Validate one legacy cell's existing generation/freeze/final sidecar.

    This reader never calls the judge, refreezes a submission, repairs evidence,
    or exposes raw conversations. A submitted legacy result without a bound
    score receipt is rejected; an unsubmitted terminal failure remains unscored.
    """
    _require_sha256(campaign_file_sha256, field_name="campaign_file_sha256")
    runtime = _safe_runtime(runtime, label="legacy")
    envelope = _read_json(
        _evidence_path(runtime, "evidence/comparison-legacy-final.json")
    )
    if envelope.get("schema_version") != _LEGACY_SCHEMA:
        raise ValueError("unsupported legacy comparison envelope")
    if envelope.get("campaign_file_sha256") != campaign_file_sha256:
        raise ValueError("legacy campaign identity mismatch")
    envelope_cell = envelope.get("cell")
    if not isinstance(envelope_cell, dict) or not _same_cell_identity(
        envelope_cell, cell
    ):
        raise ValueError("legacy envelope differs from scheduled cell")
    attempt_id = envelope.get("attempt_id")
    if attempt_id != f"{cell['cell_id']}-attempt-0001":
        raise ValueError("legacy attempt identity mismatch")

    hashes = _verify_generation_files(runtime, envelope)
    hashes["evidence/comparison-legacy-final.json"] = hashlib.sha256(
        _evidence_path(runtime, "evidence/comparison-legacy-final.json").read_bytes()
    ).hexdigest()
    result = _read_json(_evidence_path(runtime, "evidence/campaign_result.json"))
    result_cell = result.get("cell")
    if not isinstance(result_cell, dict) or not _same_cell_identity(
        result_cell, cell
    ):
        raise ValueError("legacy campaign result differs from scheduled cell")
    _check_expected_image(result, expected_image_id)

    experiment = result.get("experiment_result")
    if not isinstance(experiment, dict):
        raise ValueError("legacy campaign result is missing experiment_result")
    final_submission = experiment.get("final_submission")
    receipt = envelope.get("score_sidecar_receipt")
    profile = envelope.get("final_test_profile")
    if not isinstance(profile, dict):
        raise TypeError("legacy final_test_profile must be an object")
    if profile.get("campaign_config_sha256") != campaign_file_sha256:
        raise ValueError("legacy final profile campaign identity mismatch")
    final_test_profile_sha256(profile)

    base_row = {
        **{key: cell[key] for key in _CELL_IDENTITY},
        "comparison_cell_id": cell.get("comparison_cell_id", cell["cell_id"]),
        "backend": "legacy",
        "attempt_id": attempt_id,
        "model_status": result.get("model_status"),
        "terminal_reason": _terminal_reason(result, experiment),
        "submission_status": "not_submitted",
        "judge_status": experiment.get("outcome"),
        "outcome": experiment.get("outcome"),
        "score": None,
        "legacy_evidence": {"files": hashes},
    }
    if final_submission is None or (
        isinstance(final_submission, dict)
        and final_submission.get("status") != "available"
    ):
        if receipt is not None or (runtime / "evidence/bound-final-test").exists():
            raise ValueError("legacy unscored failure must not carry final receipt")
        if isinstance(final_submission, dict):
            base_row["submission_status"] = final_submission.get(
                "status", "not_submitted"
            )
        return base_row
    if not isinstance(final_submission, dict):
        raise TypeError("legacy final_submission must be an object")
    if receipt is None:
        raise ValueError("legacy submitted result is missing final receipt")
    _verify_bound_final_request(runtime, profile, cell, attempt_id, final_submission)
    submission = final_replay._verify_submission(runtime, deepcopy(final_submission))
    context = EpisodeContext(
        episode_id=cell["cell_id"],
        attempt_id=attempt_id,
        task_id=cell["task_id"],
        condition=cell["experimental_arm"],
        max_steps=4,
    )
    judgment, _sidecar = read_final_score_receipt(
        runtime=runtime,
        context=context,
        profile=profile,
        receipt=receipt,
        submission=submission,
    )
    if judgment.judge_engine != "evas":
        raise ValueError("legacy final receipt uses an unsupported judge")
    for relative in ("evidence/bound-final-test/request.json", receipt["path"]):
        hashes[relative] = hashlib.sha256(_evidence_path(runtime, relative).read_bytes()).hexdigest()
    base_row.update(
        {
            "submission_status": "submitted",
            "judge_status": judgment.status,
            "outcome": judgment.status,
            "terminal_reason": _terminal_reason(result, experiment) or "submitted",
            "score": judgment.score,
            "trusted_replay": {
                "status": judgment.status,
                "submission_tree_sha256": submission.tree_sha256,
                "final_test_profile_sha256": final_test_profile_sha256(profile),
                "score_sidecar_receipt": deepcopy(dict(receipt)),
            },
            "score_sidecar_receipt": deepcopy(dict(receipt)),
        }
    )
    return base_row


def join_six_cell_comparison(
    schedule: list[dict[str, Any]], rows: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build six audit rows and three task-matched pairs without imputation."""
    if len(schedule) != 6 or len(rows) != 6:
        raise ValueError("comparison join requires exactly six scheduled rows")
    scheduled_by_id = _unique_by_comparison_id(schedule, label="schedule")
    rows_by_id = _unique_by_comparison_id(rows, label="rows")
    if set(scheduled_by_id) != set(rows_by_id):
        raise ValueError("comparison rows must exactly match the schedule")

    audit_rows: list[dict[str, Any]] = []
    for scheduled in schedule:
        row = deepcopy(rows_by_id[_comparison_id(scheduled)])
        _validate_row_against_schedule(scheduled, row)
        _validate_row_score(row)
        audit_rows.append(row)

    return {
        "schema_version": "vaevas-legacy-native-comparison-results-v1",
        "audit_rows": audit_rows,
        "paired_rows": _build_pairs(audit_rows),
    }


def _build_pairs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, dict[str, Any]]] = {}
    for row in rows:
        key = (row["family_id"], row["task_id"], row["form"])
        grouped.setdefault(key, {})[row["backend"]] = row
    pairs = []
    for key in sorted(grouped):
        bucket = grouped[key]
        if set(bucket) != {"legacy", "native-mini-swe"}:
            raise ValueError("each task pair must contain legacy and native-mini-swe")
        legacy = bucket["legacy"]
        native = bucket["native-mini-swe"]
        left = legacy["score"]
        right = native["score"]
        complete = _pair_score_eligible(legacy) and _pair_score_eligible(native)
        score_delta = None if not complete else right - left
        pairs.append(
            {
                "family_id": key[0],
                "task_id": key[1],
                "form": key[2],
                "legacy_comparison_cell_id": legacy["comparison_cell_id"],
                "native_comparison_cell_id": native["comparison_cell_id"],
                "legacy_score": left,
                "native_score": right,
                "score_delta": score_delta,
                "guard_upper_bound_delta": _paired_delta(legacy, native, "guard_upper_bound", complete),
                "elapsed_s_delta": _paired_delta(legacy, native, "elapsed_s", complete),
                "complete": complete,
            }
        )
    if len(pairs) != 3:
        raise ValueError("comparison join requires exactly three paired rows")
    return pairs


def _paired_delta(legacy, native, field, complete):
    left, right = legacy.get(field), native.get(field)
    if not complete or left is None or right is None:
        return None
    if field == "guard_upper_bound":
        return str(Decimal(right) - Decimal(left))
    return right - left


def _validate_row_against_schedule(
    scheduled: dict[str, Any], row: dict[str, Any]
) -> None:
    if row.get("comparison_cell_id") != _comparison_id(scheduled):
        raise ValueError("row identity differs from scheduled comparison cell")
    for key in ("cell_id", "backend", "task_id", "family_id", "form"):
        if row.get(key) != scheduled.get(key):
            raise ValueError(f"row identity mismatch: {key}")
    if row.get("backend") not in {"legacy", "native-mini-swe"}:
        raise ValueError("comparison join supports only legacy/native-mini-swe")
    status = row.get("status")
    disposition = row.get("disposition")
    if status in _UNSTARTED_STATUSES or disposition in _UNSTARTED_STATUSES:
        if row.get("started") is True or row.get("score") is not None or row.get("evidence") is not None:
            raise ValueError("not-started rows must have null score and evidence")
        return
    evidence = row.get("evidence")
    if _row_requires_evidence(row):
        if not isinstance(evidence, dict):
            raise ValueError("started rows require evidence")
    if isinstance(evidence, dict):
        for key in ("cell_id", "backend", "task_id", "family_id", "form"):
            if evidence.get(key) != scheduled.get(key):
                raise ValueError(f"terminal evidence identity mismatch: {key}")
        if evidence.get("score") != row.get("score"):
            raise ValueError("row score differs from evidence score")


def _validate_row_score(row: dict[str, Any]) -> None:
    for field in ("score", "elapsed_s"):
        value = row.get(field)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{field} must be numeric or null")
        if not math.isfinite(float(value)):
            raise ValueError(f"{field} must be finite")
        if field == "elapsed_s" and value < 0:
            raise ValueError("elapsed_s must be nonnegative")
    cost = row.get("guard_upper_bound")
    if cost is not None:
        if not isinstance(cost, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", cost):
            raise ValueError("guard_upper_bound must be a nonnegative decimal string")
    evidence = row.get("evidence")
    if isinstance(evidence, dict):
        value = evidence.get("score")
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise ValueError("evidence score must be finite")


def _verify_generation_files(
    runtime: Path, envelope: dict[str, Any]
) -> dict[str, str]:
    files = envelope.get("generation_files")
    if not isinstance(files, dict):
        raise TypeError("legacy generation_files must be an object")
    required = {"evidence/campaign_result.json"}
    for relative in _OPTIONAL_LEGACY_GENERATION:
        if (runtime / relative).exists():
            required.add(relative)
    if required != set(files):
        raise ValueError("legacy generation file hashes are incomplete")
    observed: dict[str, str] = {}
    for relative, expected in files.items():
        _require_relative_path(relative)
        _require_sha256(expected, field_name=f"{relative} sha256")
        path = _evidence_path(runtime, relative)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            raise ValueError("legacy generation evidence digest mismatch")
        observed[relative] = digest
    return observed


def _verify_bound_final_request(
    runtime: Path,
    profile: dict[str, Any],
    cell: dict[str, Any],
    attempt_id: str,
    final_submission: dict[str, Any],
) -> None:
    request_path = runtime / "evidence/bound-final-test/request.json"
    if not request_path.is_file():
        raise ValueError("legacy final receipt is missing bound final request")
    request = _read_json(_evidence_path(runtime, "evidence/bound-final-test/request.json"))
    expected_submission = final_replay._verify_submission(runtime, deepcopy(final_submission))
    expected = {
        "profile": profile,
        "episode_id": cell["cell_id"],
        "attempt_id": attempt_id,
        "task_id": cell["task_id"],
        "submission_tree_sha256": expected_submission.tree_sha256,
    }
    if request != expected:
        raise ValueError("legacy bound final request identity mismatch")


def _same_cell_identity(left: dict[str, Any], right: dict[str, Any]) -> bool:
    wrapper_keys = {"comparison_cell_id", "backend", "order", "runtime"}
    return ({key: value for key, value in left.items() if key not in wrapper_keys}
            == {key: value for key, value in right.items() if key not in wrapper_keys})


def _terminal_reason(
    result: dict[str, Any], experiment: dict[str, Any]
) -> str | None:
    reason = result.get("termination_reason") or experiment.get("terminal_reason")
    if isinstance(reason, str) and reason:
        return reason
    model_execution = experiment.get("model_execution")
    if isinstance(model_execution, dict):
        status = model_execution.get("status")
        if isinstance(status, str) and status:
            return status
    return None


def _row_requires_evidence(row: dict[str, Any]) -> bool:
    if row.get("budget_censored") is True:
        return False
    if (
        row.get("disposition") == "incomplete_evidence"
        or row.get("status") == "incomplete_evidence"
    ):
        return False
    return not (row.get("status") in _UNSTARTED_STATUSES
                or row.get("disposition") in _UNSTARTED_STATUSES)


def _pair_score_eligible(row: dict[str, Any]) -> bool:
    if row.get("budget_censored") is True:
        return False
    if (
        row.get("disposition") == "incomplete_evidence"
        or row.get("status") == "incomplete_evidence"
    ):
        return False
    return row.get("score") is not None


def _check_expected_image(
    row_or_result: dict[str, Any], expected_image_id: str | None
) -> None:
    if expected_image_id is None:
        return
    observed = _observed_image_id(row_or_result)
    if observed != expected_image_id:
        raise ValueError("observed image identity mismatch")


def _observed_image_id(row_or_result: dict[str, Any]) -> str | None:
    environment = row_or_result.get("public_agent_environment") or {}
    if isinstance(environment, dict) and environment.get("image_id"):
        return environment["image_id"]
    launcher_environment = row_or_result.get("environment") or {}
    if isinstance(launcher_environment, dict) and launcher_environment.get("image_id"):
        return launcher_environment["image_id"]
    value = row_or_result.get("docker_image_id")
    return value if isinstance(value, str) and value else None


def _read_native_manifest_image_id(runtime: Path) -> str | None:
    runtime = _safe_runtime(runtime, label="native")
    result_path = runtime / "evidence/native-launcher/result.json"
    if not result_path.is_file():
        return None
    result = _read_json(_evidence_path(runtime, "evidence/native-launcher/result.json"))
    digest = result.get("manifest_sha256")
    if not isinstance(digest, str):
        return None
    _require_sha256(digest, field_name="native manifest sha256")
    manifest_path = _evidence_path(runtime, "evidence/native-launcher/manifest.json")
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != digest:
        raise ValueError("native manifest digest mismatch")
    manifest = _read_json(manifest_path)
    return _observed_image_id(manifest)


def _safe_runtime(runtime: Path, *, label: str) -> Path:
    if not isinstance(runtime, Path):
        raise TypeError("runtime must be a Path")
    if runtime.is_symlink():
        raise ValueError(f"{label} evidence must not use symlinks")
    resolved = runtime.resolve()
    if not resolved.exists() or not resolved.is_dir():
        raise ValueError(f"{label} runtime must be an existing directory")
    return resolved


def _evidence_path(runtime: Path, relative: str) -> Path:
    _require_relative_path(relative)
    path = runtime / relative
    if any(part.is_symlink() for part in (path, *path.parents) if part != runtime.parent):
        raise ValueError("comparison evidence must not use symlinks")
    if not path.is_file():
        raise ValueError(f"missing comparison evidence: {relative}")
    return path


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise TypeError("comparison evidence must be a JSON object")
    return value


def _require_relative_path(relative: str) -> None:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != relative:
        raise ValueError("unsafe comparison evidence path")


def _require_sha256(value: Any, *, field_name: str) -> None:
    if not isinstance(value, str) or not _HASH_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


def _comparison_id(row: dict[str, Any]) -> str:
    value = row.get("comparison_cell_id") or row.get("cell_id")
    if not isinstance(value, str) or not value:
        raise ValueError("comparison row is missing comparison_cell_id")
    return value


def _unique_by_comparison_id(
    rows: list[dict[str, Any]], *, label: str
) -> dict[str, dict[str, Any]]:
    keyed: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = _comparison_id(row)
        if key in keyed:
            raise ValueError(f"duplicate {label} comparison cell: {key}")
        keyed[key] = row
    return keyed
