"""Fresh-attempt orchestration for opt-in native mini-swe campaign cells."""

from __future__ import annotations

from argparse import Namespace
from collections.abc import Callable, Mapping
from copy import copy, deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import run_campaign as runner  # noqa: E402
import score_campaign as scorer  # noqa: E402
from runners.agent_harness.attempt_sequence import (  # noqa: E402
    AttemptRecord,
    AttemptOutcome,
    AttemptSequenceError,
    RetryPolicy,
    read_attempt_sequence_resume_state,
    run_attempt_sequence,
)
from runners.agent_harness.state import EpisodeContext  # noqa: E402
from runners.agent_harness.budget import validate_model_call_limit  # noqa: E402


TRANSPORT_ERROR_TYPES = frozenset(
    {
        "TimeoutError",
        "ConnectionError",
        "ProviderRequestTimeout",
        "ProviderTransportError",
        "TimeoutExpired",
    }
)


ClientFactory = Callable[[], Any]


def retry_policy(max_attempts: int) -> RetryPolicy:
    return RetryPolicy(max_attempts=max_attempts, retry_categories=frozenset(
        {"provider_transport", "sandbox_startup"}
    ))


def run_native_attempt_sequence(
    *,
    cell: dict[str, Any],
    args: Namespace,
    client_factory: ClientFactory,
    retry_policy: RetryPolicy,
    resume: bool = False,
) -> dict[str, Any]:
    """Run one native campaign cell through fresh infrastructure attempts."""
    _validate_inputs(cell=cell, args=args, client_factory=client_factory, retry_policy=retry_policy)
    campaign_sha = _campaign_file_sha256(args)
    root = args.output / cell["cell_id"]
    limit = validate_model_call_limit(getattr(args, "native_model_call_limit", None))
    initial_context = _initial_context(cell, limit)
    if resume:
        validate_native_attempt_resume(
            root, cell, campaign_sha, retry_policy, model_call_limit=limit)

    def execute(context: EpisodeContext, reserved_runtime: Path) -> AttemptOutcome:
        attempt_args = copy(args)
        attempt_args.output = reserved_runtime
        attempt_args._native_attempt_context = context
        attempt_args.resume = False
        attempt_args.native_max_attempts = 1
        client = client_factory()
        runner.run_cell_preserving_failure(cell, attempt_args, client)
        cell_runtime = reserved_runtime / cell["cell_id"]
        row = scorer.read_native_cell(
            cell_runtime,
            cell,
            campaign_file_sha256=campaign_sha,
        )
        outcome = _attempt_outcome_from_row(row=row, root=root, cell_runtime=cell_runtime)
        _write_json_once(
            root / context.attempt_id / "native-row.json",
            {
                "schema_version": "vaevas-native-attempt-row-v1",
                "attempt_id": context.attempt_id,
                "row": row,
                "row_sha256": _canonical_sha256(row),
            },
        )
        return outcome

    run_attempt_sequence(
        initial_context=initial_context,
        output_root=root,
        retry_policy=retry_policy,
        execute=execute,
        resume=resume,
    )
    return read_native_attempt_sequence(
        root,
        cell,
        campaign_file_sha256=campaign_sha,
        expected_retry_policy=retry_policy,
    )


def validate_native_attempt_resume(
    root: Path,
    cell: dict[str, Any],
    campaign_file_sha256: str,
    expected_retry_policy: RetryPolicy,
    *,
    model_call_limit: int | None = None,
) -> dict[str, Any]:
    """Validate existing native attempt evidence before any resumed client is created."""
    state = read_attempt_sequence_resume_state(
        output_root=root,
        initial_context=_initial_context(cell, model_call_limit),
        retry_policy=expected_retry_policy,
    )
    attempts, _ = _validate_native_attempt_records(
        root=state.output_root,
        cell=cell,
        campaign_file_sha256=campaign_file_sha256,
        records=state.attempts,
    )
    return {
        "schema_version": "vaevas-native-attempt-resume-validation-v1",
        "root": str(state.output_root),
        "complete": state.complete,
        "terminal_selection_missing": state.terminal_selection_missing,
        "resumable": bool(state.next_context is not None or state.terminal_selection_missing),
        "attempt_count": len(attempts),
        "next_attempt_id": state.next_context.attempt_id if state.next_context is not None else None,
        "attempts": attempts,
    }


def read_native_attempt_sequence(
    root: Path,
    cell: dict[str, Any],
    *,
    campaign_file_sha256: str,
    expected_retry_policy: RetryPolicy,
) -> dict[str, Any]:
    """Read and validate a native attempt sequence without executing cells."""
    request = _read_json(root / "request.json")
    if request.get("retry_policy_sha256") != _canonical_sha256(expected_retry_policy.to_document()):
        raise ValueError("retry policy differs from attempt sequence")
    try:
        limit = request["initial_context"]["budget_limits"].get("model_calls")
        state = read_attempt_sequence_resume_state(
            output_root=root, initial_context=_initial_context(cell, limit),
            retry_policy=expected_retry_policy)
    except (AttemptSequenceError, KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"attempt sequence receipts failed verification: {exc}") from exc
    if not state.complete:
        raise ValueError("attempt sequence receipts failed verification: selection is missing")
    selection = _read_json(root / "selection.json")
    attempts, selected_row = _validate_native_attempt_records(
        root=state.output_root, cell=cell, campaign_file_sha256=campaign_file_sha256,
        records=state.attempts)
    if selected_row is None or attempts[-1]["attempt_id"] != selection["selected_attempt_id"]:
        raise ValueError("attempt sequence selected row mismatch")
    return _dispatch_document(
        selected_row=selected_row,
        attempts=attempts,
        root=root,
        retry_policy=expected_retry_policy,
        selection=selection,
    )


def _validate_native_attempt_records(
    *,
    root: Path,
    cell: dict[str, Any],
    campaign_file_sha256: str,
    records: tuple[AttemptRecord, ...],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    attempts: list[dict[str, Any]] = []
    native_row = None
    for record in records:
        attempt_id = record.context.attempt_id
        context = {
            "attempt_id": record.context.attempt_id,
            "parent_attempt_id": record.context.parent_attempt_id,
            "retry_index": record.context.retry_index,
            "retry_reason": record.context.retry_reason,
            "budget_limits": dict(record.context.budget_limits),
            **({"model_calls_before_attempt": record.context.model_calls_before_attempt}
               if "model_calls" in record.context.budget_limits else {}),
        }
        evidence = record.outcome.evidence
        cell_runtime = _cell_runtime_from_receipt(
            root=root,
            receipt={"runtime_path": record.runtime_path.relative_to(root).as_posix()},
            cell=cell,
        )
        relative_cell_runtime = cell_runtime.relative_to(root).as_posix()
        if evidence.get("cell_runtime") != relative_cell_runtime:
            raise ValueError("native attempt cell runtime evidence mismatch")
        native_row = scorer.read_native_cell(
            cell_runtime,
            cell,
            campaign_file_sha256=campaign_file_sha256,
        )
        native_sidecar = _read_native_row_sidecar(root=root, attempt_id=attempt_id)
        if (
            native_sidecar.get("attempt_id") != attempt_id
            or native_sidecar.get("row") != native_row
            or native_sidecar.get("row_sha256") != _canonical_sha256(native_row)
        ):
            raise ValueError("native row sidecar mismatch")
        _validate_native_row_identity(native_row, cell=cell, attempt_context=context)
        if evidence.get("model_call_budget") != native_row.get("model_call_budget"):
            raise ValueError("native attempt budget evidence mismatch")
        _validate_attempt_lineage_artifacts(cell_runtime=cell_runtime, context=context)
        if _canonical_sha256(native_row) != evidence["native_row_sha256"]:
            raise ValueError("native attempt source hash mismatch")
        observed_sources = source_hashes(cell_runtime)
        if observed_sources != evidence["source_hashes"]:
            raise ValueError("native attempt source hash mismatch")
        attempts.append({
            "attempt_id": attempt_id,
            "retry_index": record.context.retry_index,
            "parent_attempt_id": record.context.parent_attempt_id,
            "retry_reason": record.context.retry_reason,
            "primary_outcome": record.outcome.primary_outcome,
            "terminal_reason": record.outcome.terminal_reason,
            "failure_category": record.outcome.failure_category,
            "failure_phase": record.outcome.failure_phase,
            "submission_frozen": record.outcome.submission_frozen,
            "final_started": record.outcome.final_started,
            "retry_decision": dict(record.retry_decision),
            "cell_runtime": relative_cell_runtime,
            "native_row_sha256": evidence["native_row_sha256"],
            "source_hashes_sha256": _canonical_sha256(observed_sources),
            "costs": _attempt_costs(native_row),
        })
    return attempts, native_row


def source_hashes(runtime: Path) -> dict[str, Any]:
    """Return deterministic file source hashes for one native cell runtime."""
    runtime = runtime.resolve(strict=True)
    files = {
        path.relative_to(runtime).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(runtime.rglob("*"))
        if not path.is_symlink() and path.is_file()
    }
    return {
        "schema_version": "vaevas-native-attempt-source-hashes-v1",
        "runtime_sha256": _canonical_sha256(files),
        "files": files,
    }


def _validate_inputs(
    *,
    cell: dict[str, Any],
    args: Namespace,
    client_factory: ClientFactory,
    retry_policy: RetryPolicy,
) -> None:
    if not isinstance(cell, dict) or not isinstance(cell.get("cell_id"), str):
        raise TypeError("cell must be a campaign cell with cell_id")
    if not isinstance(args, Namespace):
        raise TypeError("args must be an argparse.Namespace")
    if not isinstance(getattr(args, "output", None), Path):
        raise TypeError("args.output must be a Path")
    if not callable(client_factory):
        raise TypeError("client_factory must be callable")
    if not isinstance(retry_policy, RetryPolicy):
        raise TypeError("retry_policy must be a RetryPolicy")


def _initial_context(cell: Mapping[str, Any], model_call_limit=None) -> EpisodeContext:
    return EpisodeContext(
        episode_id=str(cell["cell_id"]),
        attempt_id=f"{cell['cell_id']}-attempt-0001",
        task_id=str(cell["task_id"]),
        condition=str(cell["experimental_arm"]),
        max_steps=None,
        budget_limits={} if model_call_limit is None else {"model_calls": model_call_limit},
    )


def _campaign_file_sha256(args: Namespace) -> str:
    value = getattr(args, "campaign_file_sha256", None)
    if not isinstance(value, str) or len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("args.campaign_file_sha256 must be a SHA-256 digest")
    return value


def _attempt_outcome_from_row(
    *,
    row: Mapping[str, Any],
    root: Path,
    cell_runtime: Path,
) -> AttemptOutcome:
    primary = str(row.get("outcome") or row.get("judge_status") or "unknown")
    terminal = str(row.get("termination_reason") or row.get("terminal_reason") or primary)
    submission_frozen = row.get("submission_status") == "submitted"
    final_started = "trusted_replay" in row
    failure_category: str | None = None
    failure_phase: str | None = None
    if primary == "infrastructure_failure":
        unsafe_after_final_or_cleanup = (
            _has_post_freeze_or_cleanup_evidence(cell_runtime) or _has_cleanup_incident(row)
        )
        if (
            not unsafe_after_final_or_cleanup
            and not submission_frozen
            and not final_started
            and _has_provider_transport_failure(cell_runtime)
        ):
            failure_category = "provider_transport"
            failure_phase = "pre_final"
        elif (
            not unsafe_after_final_or_cleanup
            and not submission_frozen
            and not final_started
            and _has_sandbox_startup_incident(row)
        ):
            failure_category = "sandbox_startup"
            failure_phase = "pre_final"
        else:
            failure_category = "unknown"
            failure_phase = "unknown"
    evidence = {
        "cell_runtime": cell_runtime.relative_to(root).as_posix(),
        "native_row_sha256": _canonical_sha256(row),
        "source_hashes": source_hashes(cell_runtime),
    }
    if "model_call_budget" in row:
        evidence["model_call_budget"] = row["model_call_budget"]
    return AttemptOutcome(
        primary_outcome=primary,
        terminal_reason=terminal,
        failure_category=failure_category,
        failure_phase=failure_phase,
        submission_frozen=submission_frozen,
        final_started=final_started,
        evidence=evidence,
    )


def _has_provider_transport_failure(cell_runtime: Path) -> bool:
    path = cell_runtime / "evidence/native-launcher/private-events.jsonl"
    if not path.is_file() or path.is_symlink():
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if not isinstance(event, dict) or event.get("event_type") != "provider_failure":
            continue
        payload = event.get("payload")
        if isinstance(payload, dict) and payload.get("error_type") in TRANSPORT_ERROR_TYPES:
            return True
    return False


def _has_post_freeze_or_cleanup_evidence(cell_runtime: Path) -> bool:
    marker_paths = [
        cell_runtime / "evidence/final_submission",
        cell_runtime / "evidence/bound-final-test",
        cell_runtime / "evidence/score-sidecars",
        cell_runtime / "evidence/native-episode/scored-results",
        cell_runtime / "evidence/trusted_replay",
        cell_runtime / "evidence/final_trusted_replay",
        cell_runtime / "evidence/trusted_replay_result.json",
    ]
    if any(path.exists() or path.is_symlink() for path in marker_paths):
        return True
    private = cell_runtime / "evidence/native-launcher/private-events.jsonl"
    if private.is_file() and not private.is_symlink():
        for line in private.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if (
                isinstance(event, dict)
                and event.get("event_type") == "launcher_cleanup_failed"
            ):
                return True
    trajectory = cell_runtime / "evidence/native-episode/trajectory.jsonl"
    if trajectory.is_file() and not trajectory.is_symlink():
        for line in trajectory.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            event_type = event.get("event_type") if isinstance(event, dict) else None
            payload = event.get("payload") if isinstance(event, dict) else None
            if isinstance(event_type, str) and (
                event_type.startswith("final_") or event_type == "submission_frozen"
            ):
                return True
            if isinstance(payload, dict) and (
                payload.get("submission_frozen") is True
                or any(str(key).startswith("final_") for key in payload)
            ):
                return True
    return False


def _has_sandbox_startup_incident(row: Mapping[str, Any]) -> bool:
    incidents = row.get("incidents")
    return isinstance(incidents, list) and any(
        isinstance(incident, dict) and incident.get("category") == "sandbox_startup"
        for incident in incidents
    )


def _has_cleanup_incident(row: Mapping[str, Any]) -> bool:
    incidents = row.get("incidents")
    return isinstance(incidents, list) and any(
        isinstance(incident, dict)
        and incident.get("category") in {"cleanup", "cleanup_failed", "sandbox_cleanup_failure"}
        for incident in incidents
    )


def _attempt_costs(row: Mapping[str, Any]) -> dict[str, Any]:
    metering = row.get("metering")
    if not isinstance(metering, Mapping):
        return {
            "provider_requests": None,
            "tool_requests": None,
            "output_tokens": None,
            "evas_invocations": None,
        }
    provider = metering.get("provider")
    tools = metering.get("tools")
    provider_usage = provider.get("usage") if isinstance(provider, Mapping) else None
    evas_usage = row.get("evas_usage")
    return {
        "provider_requests": provider.get("requests") if isinstance(provider, Mapping) else None,
        "tool_requests": tools.get("requests") if isinstance(tools, Mapping) else None,
        "output_tokens": provider_usage.get("completion_tokens")
        if isinstance(provider_usage, Mapping)
        else row.get("output_tokens"),
        "evas_invocations": evas_usage.get("calls_executed")
        if isinstance(evas_usage, Mapping)
        else None,
    }


def _dispatch_document(
    *,
    selected_row: dict[str, Any],
    attempts: list[dict[str, Any]],
    root: Path,
    retry_policy: RetryPolicy,
    selection: Mapping[str, Any],
) -> dict[str, Any]:
    status = str(selected_row.get("judge_status") or selected_row.get("outcome"))
    result = deepcopy(selected_row)
    selected_costs = attempts[-1]["costs"]
    attempt_costs = {
        "schema_version": "vaevas-native-attempt-costs-v1",
        "selected_attempt_id": selection["selected_attempt_id"],
        "selected_costs": selected_costs,
        "summary": _summarize_attempt_costs(attempts),
        "attempts": [
            {"attempt_id": attempt["attempt_id"], "costs": attempt["costs"]}
            for attempt in attempts
        ],
    }
    result.update(
        {
            "schema_version": "vaevas-native-attempt-sequence-dispatch-v1",
            "backend": selected_row.get("backend", "native-mini-swe"),
            "status": status,
            "termination_reason": selected_row.get(
                "termination_reason",
                selected_row.get("terminal_reason", status),
            ),
            "attempt_id": selection["selected_attempt_id"],
            "attempt_count": len(attempts),
            "selected_costs": selected_costs,
            "attempt_costs": attempt_costs,
            "attempt_sequence": {
                "schema_version": "vaevas-native-attempt-sequence-v1",
                "root": str(root),
                "retry_policy_sha256": _canonical_sha256(retry_policy.to_document()),
                "selection_sha256": _canonical_sha256(selection),
                "attempts": attempts,
            },
        }
    )
    return result


def _summarize_attempt_costs(attempts: list[dict[str, Any]]) -> dict[str, dict[str, int | None]]:
    keys = ("provider_requests", "tool_requests", "output_tokens", "evas_invocations")
    summary: dict[str, dict[str, int | None]] = {}
    for key in keys:
        subtotal = 0
        unknown = 0
        for attempt in attempts:
            costs = attempt["costs"]
            value = costs.get(key) if isinstance(costs, Mapping) else None
            if value is None:
                unknown += 1
            else:
                subtotal += value
        summary[key] = {
            "total": None if unknown else subtotal,
            "reported_subtotal": subtotal,
            "unknown_attempts": unknown,
        }
    return summary


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    return value


def _read_native_row_sidecar(*, root: Path, attempt_id: str) -> dict[str, Any]:
    return _read_json(_confined_existing_file(root / attempt_id / "native-row.json", root))


def _cell_runtime_from_receipt(
    *,
    root: Path,
    receipt: Mapping[str, Any],
    cell: Mapping[str, Any],
) -> Path:
    runtime_path = receipt.get("runtime_path")
    cell_id = cell.get("cell_id")
    if not isinstance(runtime_path, str) or not _valid_relative_path(runtime_path):
        raise ValueError("native attempt runtime_path is invalid")
    if not isinstance(cell_id, str) or not _valid_path_segment(cell_id):
        raise ValueError("native cell_id is invalid")
    runtime = _confined_existing_directory(root / runtime_path, root)
    return _confined_existing_directory(runtime / cell_id, runtime)


def _validate_native_row_identity(
    row: Mapping[str, Any],
    *,
    cell: Mapping[str, Any],
    attempt_context: Mapping[str, Any],
) -> None:
    if row.get("attempt_id") != attempt_context.get("attempt_id"):
        raise ValueError("native row attempt identity mismatch")
    if "model_call_budget" in row:
        budget = row["model_call_budget"]
        if (budget["limit"] != attempt_context["budget_limits"].get("model_calls")
                or budget["used_before_attempt"] != attempt_context.get("model_calls_before_attempt")):
            raise ValueError("native row budget context mismatch")
    for key in ("cell_id", "task_id", "family_id", "form", "mode", "experimental_arm"):
        if row.get(key) != cell.get(key):
            raise ValueError("native row cell identity mismatch")


def _validate_attempt_lineage_artifacts(
    *,
    cell_runtime: Path,
    context: Mapping[str, Any],
) -> None:
    expected = {
        "parent_attempt_id": context.get("parent_attempt_id"),
        "retry_index": context.get("retry_index"),
        "retry_reason": context.get("retry_reason"),
    }
    manifest_path = cell_runtime / "evidence/native-launcher/manifest.json"
    if manifest_path.exists():
        manifest = _read_json(_confined_existing_file(manifest_path, cell_runtime))
        if manifest.get("attempt_id") != context.get("attempt_id"):
            raise ValueError("native attempt lineage manifest identity mismatch")
        if manifest.get("attempt_lineage") != expected:
            raise ValueError("native attempt lineage manifest mismatch")
    trajectory_path = cell_runtime / "evidence/native-episode/trajectory.jsonl"
    if trajectory_path.exists():
        trajectory = _confined_existing_file(trajectory_path, cell_runtime)
        first_event = None
        for line in trajectory.read_text(encoding="utf-8").splitlines():
            if line.strip():
                first_event = json.loads(line)
                break
        if not isinstance(first_event, dict) or first_event.get("event_type") != "episode_started":
            raise ValueError("native attempt lineage trajectory missing episode_started")
        payload = first_event.get("payload")
        if not isinstance(payload, dict) or payload.get("attempt_lineage") != expected:
            raise ValueError("native attempt lineage trajectory mismatch")


def _confined_existing_file(path: Path, parent: Path) -> Path:
    resolved = _confined_existing_path(path, parent)
    if not resolved.is_file():
        raise ValueError("native attempt path is not a file")
    return resolved


def _confined_existing_directory(path: Path, parent: Path) -> Path:
    resolved = _confined_existing_path(path, parent)
    if not resolved.is_dir():
        raise ValueError("native attempt path is not a directory")
    return resolved


def _confined_existing_path(path: Path, parent: Path) -> Path:
    if path.is_symlink():
        raise ValueError("native attempt path must not be a symlink")
    resolved_parent = parent.resolve(strict=True)
    resolved = path.resolve(strict=True)
    if resolved != resolved_parent and resolved_parent not in resolved.parents:
        raise ValueError("native attempt path escaped its root")
    for ancestor in [resolved, *resolved.parents]:
        if ancestor == resolved_parent:
            break
        if ancestor.is_symlink():
            raise ValueError("native attempt path must not use symlinks")
    return resolved


def _valid_relative_path(value: str) -> bool:
    path = Path(value)
    return not path.is_absolute() and all(_valid_path_segment(part) for part in path.parts)


def _valid_path_segment(value: str) -> bool:
    return bool(value) and value not in {".", ".."} and "/" not in value and "\\" not in value


def _write_json_once(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
