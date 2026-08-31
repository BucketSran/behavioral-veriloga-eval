"""Fresh-attempt retry coordination for native harness launches."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
import hashlib
import json
import math
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .state import EpisodeContext


ALLOWED_RETRY_CATEGORIES = frozenset({"provider_transport", "sandbox_startup"})


class AttemptSequenceError(RuntimeError):
    """Attempt sequence setup or receipt validation failed closed."""


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int
    retry_categories: frozenset[str]
    schema_version: str = field(default="vaevas-retry-policy-v1", init=False)

    def __post_init__(self) -> None:
        if isinstance(self.max_attempts, bool) or not isinstance(self.max_attempts, int):
            raise TypeError("max_attempts must be an integer")
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be positive")
        if self.max_attempts > 100:
            raise ValueError("max_attempts must be finite and bounded")
        if not isinstance(self.retry_categories, frozenset):
            raise TypeError("retry_categories must be a frozenset")
        for category in self.retry_categories:
            _require_identity(category, field_name="retry category")
            if category not in ALLOWED_RETRY_CATEGORIES:
                raise ValueError(f"forbidden retry category: {category}")

    def to_document(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "max_attempts": self.max_attempts,
            "retry_categories": sorted(self.retry_categories),
        }


@dataclass(frozen=True, slots=True)
class AttemptOutcome:
    primary_outcome: str
    terminal_reason: str
    failure_category: str | None = None
    failure_phase: str | None = None
    submission_frozen: bool = False
    final_started: bool = False
    evidence: Mapping[str, Any] = field(default_factory=dict)
    score: float | None = None

    def __post_init__(self) -> None:
        _require_identity(self.primary_outcome, field_name="primary_outcome")
        _require_identity(self.terminal_reason, field_name="terminal_reason")
        if not isinstance(self.submission_frozen, bool):
            raise TypeError("submission_frozen must be a boolean")
        if not isinstance(self.final_started, bool):
            raise TypeError("final_started must be a boolean")
        if self.failure_category is not None:
            _require_identity(self.failure_category, field_name="failure_category")
        if self.failure_phase is not None:
            _require_identity(self.failure_phase, field_name="failure_phase")
        if self.score is not None and not (
            isinstance(self.score, (int, float))
            and not isinstance(self.score, bool)
            and math.isfinite(float(self.score))
        ):
            raise ValueError("score must be finite when present")
        object.__setattr__(
            self,
            "evidence",
            _freeze_json_object(self.evidence, field_name="evidence"),
        )

    @classmethod
    def from_value(cls, value: "AttemptOutcome | Mapping[str, Any]") -> "AttemptOutcome":
        if isinstance(value, AttemptOutcome):
            return value
        if not isinstance(value, Mapping):
            raise TypeError("execute must return AttemptOutcome or mapping")
        return cls(
            primary_outcome=_required_str(value, "primary_outcome"),
            terminal_reason=_required_str(value, "terminal_reason"),
            failure_category=_optional_str(value.get("failure_category")),
            failure_phase=_optional_str(value.get("failure_phase")),
            submission_frozen=_optional_bool(value, "submission_frozen"),
            final_started=_optional_bool(value, "final_started"),
            evidence=value.get("evidence", {}),
            score=value.get("score"),
        )

    def to_document(self) -> dict[str, Any]:
        return {
            "primary_outcome": self.primary_outcome,
            "terminal_reason": self.terminal_reason,
            "failure_category": self.failure_category,
            "failure_phase": self.failure_phase,
            "submission_frozen": self.submission_frozen,
            "final_started": self.final_started,
            "evidence": _json_ready(self.evidence),
            "score_present": self.score is not None,
        }


@dataclass(frozen=True, slots=True)
class AttemptRecord:
    context: EpisodeContext
    runtime_path: Path
    request_sha256: str
    outcome: AttemptOutcome
    outcome_sha256: str
    retry_decision: Mapping[str, Any]
    attempt_receipt_sha256: str


@dataclass(frozen=True, slots=True)
class AttemptSequenceResult:
    output_root: Path
    policy_sha256: str
    attempts: tuple[AttemptRecord, ...]
    selected_attempt_id: str
    selection_sha256: str

    @property
    def selected(self) -> AttemptOutcome:
        for attempt in self.attempts:
            if attempt.context.attempt_id == self.selected_attempt_id:
                return attempt.outcome
        raise AttemptSequenceError("selected attempt is missing")

    @property
    def attempt_count(self) -> int:
        return len(self.attempts)


@dataclass(frozen=True, slots=True)
class AttemptSequenceResumeState:
    output_root: Path
    policy_sha256: str
    attempts: tuple[AttemptRecord, ...]
    selected_attempt_id: str | None
    selection_sha256: str | None
    next_context: EpisodeContext | None

    @property
    def complete(self) -> bool:
        return self.selected_attempt_id is not None

    @property
    def terminal_selection_missing(self) -> bool:
        return self.selected_attempt_id is None and self.next_context is None


ExecuteAttempt = Callable[[EpisodeContext, Path], AttemptOutcome | Mapping[str, Any]]


def run_attempt_sequence(
    *,
    initial_context: EpisodeContext,
    output_root: Path,
    retry_policy: RetryPolicy,
    execute: ExecuteAttempt,
    resume: bool = False,
) -> AttemptSequenceResult:
    """Run fresh attempts until a terminal selection can be written."""
    if not isinstance(initial_context, EpisodeContext):
        raise TypeError("initial_context must be an EpisodeContext")
    if not isinstance(output_root, Path):
        raise TypeError("output_root must be a Path")
    if not isinstance(retry_policy, RetryPolicy):
        raise TypeError("retry_policy must be a RetryPolicy")
    if not callable(execute):
        raise TypeError("execute must be callable")
    if (
        initial_context.retry_index != 0
        or initial_context.parent_attempt_id is not None
        or initial_context.retry_reason is not None
    ):
        raise AttemptSequenceError("initial_context must describe a root attempt")

    policy_document = retry_policy.to_document()
    policy_sha256 = _canonical_sha256(policy_document)
    sequence_request = _sequence_request_document(
        initial_context=initial_context,
        retry_policy=retry_policy,
        policy_sha256=policy_sha256,
    )
    sequence_request_sha256 = _canonical_sha256(sequence_request)

    attempts: list[AttemptRecord] = []
    if resume:
        state = read_attempt_sequence_resume_state(
            output_root=output_root,
            initial_context=initial_context,
            retry_policy=retry_policy,
        )
        attempts = list(state.attempts)
        if state.complete:
            assert state.selected_attempt_id is not None
            assert state.selection_sha256 is not None
            return AttemptSequenceResult(
                output_root=state.output_root,
                policy_sha256=policy_sha256,
                attempts=tuple(attempts),
                selected_attempt_id=state.selected_attempt_id,
                selection_sha256=state.selection_sha256,
            )
        root = state.output_root
        context = state.next_context
        if context is None:
            selection_sha256 = _write_selection(
                root=root,
                sequence_request_sha256=sequence_request_sha256,
                policy_sha256=policy_sha256,
                attempts=attempts,
            )
            return AttemptSequenceResult(
                output_root=root,
                policy_sha256=policy_sha256,
                attempts=tuple(attempts),
                selected_attempt_id=attempts[-1].context.attempt_id,
                selection_sha256=selection_sha256,
            )
    else:
        root = _reserve_output_root(output_root)
        _write_receipt(root / "request.json", sequence_request)
        context = initial_context
    if context is None:
        raise AttemptSequenceError("attempt sequence has no resumable context")
    while True:
        attempt_dir, runtime = _reserve_attempt_runtime(root, context.attempt_id)
        request = {
            "schema_version": "vaevas-attempt-request-v1",
            "sequence_request_sha256": sequence_request_sha256,
            "retry_policy_sha256": policy_sha256,
            "context": _context_document(context),
            "runtime_path": runtime.relative_to(root).as_posix(),
        }
        request_sha256 = _write_receipt(attempt_dir / "request.json", request)
        try:
            outcome = AttemptOutcome.from_value(execute(context, runtime))
        except Exception as exc:
            outcome = AttemptOutcome(
                primary_outcome="infrastructure_failure",
                terminal_reason="callback_exception",
                failure_category="unresolved_callback_exception",
                failure_phase="unresolved",
                evidence={"error_type": type(exc).__name__},
            )
        if "model_calls" in context.budget_limits:
            try:
                _model_calls_after(_context_document(context), outcome.evidence)
            except AttemptSequenceError:
                # Unknown usage cannot be interpreted as zero or retried safely.
                outcome = replace(
                    outcome, primary_outcome="infrastructure_failure",
                    terminal_reason="model_call_accounting_unknown", score=None,
                    failure_category="unresolved_callback_exception", failure_phase="unresolved",
                )
        outcome_document = outcome.to_document()
        outcome_sha256 = _canonical_sha256(outcome_document)
        retry_decision = _retry_decision(
            outcome=outcome,
            policy=retry_policy,
            current_attempt_count=len(attempts) + 1,
            next_attempt_id=_retry_attempt_id(initial_context, len(attempts) + 1),
        )
        attempt_receipt = {
            "schema_version": "vaevas-attempt-receipt-v1",
            "sequence_request_sha256": sequence_request_sha256,
            "retry_policy_sha256": policy_sha256,
            "request_sha256": request_sha256,
            "context": _context_document(context),
            "runtime_path": runtime.relative_to(root).as_posix(),
            "outcome": outcome_document,
            "outcome_sha256": outcome_sha256,
            "retry_decision": retry_decision,
        }
        attempt_receipt_sha256 = _write_receipt(attempt_dir / "attempt.json", attempt_receipt)
        attempts.append(
            AttemptRecord(
                context=context,
                runtime_path=runtime,
                request_sha256=request_sha256,
                outcome=outcome,
                outcome_sha256=outcome_sha256,
                retry_decision=retry_decision,
                attempt_receipt_sha256=attempt_receipt_sha256,
            )
        )
        if not retry_decision["retry_allowed"]:
            break
        context = context.next_attempt(
            attempt_id=str(retry_decision["next_attempt_id"]),
            reason=str(outcome.failure_category),
        )
        if "model_calls" in context.budget_limits:
            context = replace(context, model_calls_before_attempt=_model_calls_after(
                _context_document(context), outcome.evidence,
            ))

    selection_sha256 = _write_selection(
        root=root,
        sequence_request_sha256=sequence_request_sha256,
        policy_sha256=policy_sha256,
        attempts=attempts,
    )
    return AttemptSequenceResult(
        output_root=root,
        policy_sha256=policy_sha256,
        attempts=tuple(attempts),
        selected_attempt_id=attempts[-1].context.attempt_id,
        selection_sha256=selection_sha256,
    )


def read_attempt_sequence_resume_state(
    *,
    output_root: Path,
    initial_context: EpisodeContext,
    retry_policy: RetryPolicy,
) -> AttemptSequenceResumeState:
    """Validate an existing sequence and report whether it is complete or resumable."""
    if not isinstance(initial_context, EpisodeContext):
        raise TypeError("initial_context must be an EpisodeContext")
    if not isinstance(output_root, Path):
        raise TypeError("output_root must be a Path")
    if not isinstance(retry_policy, RetryPolicy):
        raise TypeError("retry_policy must be a RetryPolicy")
    root = _validated_existing_root(output_root)
    policy_document = retry_policy.to_document()
    policy_sha256 = _canonical_sha256(policy_document)
    sequence_request = _read_receipt(root / "request.json")
    expected_request = _sequence_request_document(
        initial_context=initial_context,
        retry_policy=retry_policy,
        policy_sha256=policy_sha256,
    )
    if sequence_request != expected_request:
        raise AttemptSequenceError("attempt sequence request drift")
    sequence_request_sha256 = _canonical_sha256(sequence_request)
    if (root / "selection.json").exists() or (root / "selection.json").is_symlink():
        if not verify_attempt_sequence_receipts(root):
            raise AttemptSequenceError("attempt sequence receipts failed verification")
        selection = _read_receipt(root / "selection.json")
        attempts = _load_attempt_records_from_selection(
            root=root,
            initial_context=_context_document(initial_context),
            policy=retry_policy,
            selection=selection,
            sequence_request_sha256=sequence_request_sha256,
            policy_sha256=policy_sha256,
        )
        return AttemptSequenceResumeState(
            output_root=root,
            policy_sha256=policy_sha256,
            attempts=attempts,
            selected_attempt_id=str(selection["selected_attempt_id"]),
            selection_sha256=_canonical_sha256(selection),
            next_context=None,
        )
    attempts, next_context = _load_attempt_prefix(
        root=root,
        initial_context=initial_context,
        policy=retry_policy,
        sequence_request_sha256=sequence_request_sha256,
        policy_sha256=policy_sha256,
    )
    return AttemptSequenceResumeState(
        output_root=root,
        policy_sha256=policy_sha256,
        attempts=attempts,
        selected_attempt_id=None,
        selection_sha256=None,
        next_context=next_context,
    )


def _write_selection(
    *,
    root: Path,
    sequence_request_sha256: str,
    policy_sha256: str,
    attempts: list[AttemptRecord],
) -> str:
    if not attempts:
        raise AttemptSequenceError("attempt sequence has no attempts")
    selected = attempts[-1]
    return _write_receipt(root / "selection.json", {
        "schema_version": "vaevas-attempt-selection-v1",
        "sequence_request_sha256": sequence_request_sha256,
        "retry_policy_sha256": policy_sha256,
        "attempt_receipts": [
            {
                "attempt_id": attempt.context.attempt_id,
                "receipt_sha256": attempt.attempt_receipt_sha256,
                "outcome_sha256": attempt.outcome_sha256,
            }
            for attempt in attempts
        ],
        "selected_attempt_id": selected.context.attempt_id,
        "selected_attempt_receipt_sha256": selected.attempt_receipt_sha256,
        "selection_reason": "last_terminal_attempt",
    })


def verify_attempt_sequence_receipts(output_root: Path) -> bool:
    """Verify immutable source hashes and terminal selection joins."""
    try:
        root = _validated_existing_root(output_root)
        sequence_request = _read_receipt(root / "request.json")
        if sequence_request.get("schema_version") != "vaevas-attempt-sequence-request-v1":
            return False
        if not _has_exact_keys(
            sequence_request,
            {
                "schema_version",
                "initial_context",
                "retry_policy_sha256",
                "retry_policy",
            },
        ):
            return False
        sequence_request_sha256 = _canonical_sha256(sequence_request)
        initial_context = _validated_context_document(
            sequence_request.get("initial_context"), expected=None
        )
        if not _initial_lineage_is_root(initial_context):
            return False
        policy_document = _validated_policy_document(sequence_request.get("retry_policy"))
        policy = RetryPolicy(
            max_attempts=policy_document["max_attempts"],
            retry_categories=frozenset(policy_document["retry_categories"]),
        )
        if sequence_request.get("retry_policy_sha256") != _canonical_sha256(policy_document):
            return False
        selection = _read_receipt(root / "selection.json")
        if selection.get("schema_version") != "vaevas-attempt-selection-v1":
            return False
        if not _has_exact_keys(
            selection,
            {
                "schema_version",
                "sequence_request_sha256",
                "retry_policy_sha256",
                "attempt_receipts",
                "selected_attempt_id",
                "selected_attempt_receipt_sha256",
                "selection_reason",
            },
        ):
            return False
        if selection.get("sequence_request_sha256") != sequence_request_sha256:
            return False
        if selection.get("retry_policy_sha256") != sequence_request.get("retry_policy_sha256"):
            return False
        attempts = selection.get("attempt_receipts")
        if (not isinstance(attempts, list) or not attempts
                or any(not isinstance(row, Mapping) for row in attempts)):
            return False
        selected_id = selection.get("selected_attempt_id")
        selected_receipt_sha256 = selection.get("selected_attempt_receipt_sha256")
        if selected_id != attempts[-1].get("attempt_id"):
            return False
        if selected_receipt_sha256 != attempts[-1].get("receipt_sha256"):
            return False
        if selection.get("selection_reason") != "last_terminal_attempt":
            return False
        records = _load_attempt_records_from_selection(
            root=root,
            initial_context=initial_context,
            policy=policy,
            selection=selection,
            sequence_request_sha256=sequence_request_sha256,
            policy_sha256=str(sequence_request["retry_policy_sha256"]),
        )
        seen_ids: set[str] = set()
        for row, record in zip(attempts, records, strict=True):
            if not isinstance(row, Mapping):
                return False
            if not _has_exact_keys(row, {"attempt_id", "receipt_sha256", "outcome_sha256"}):
                return False
            if row.get("attempt_id") != record.context.attempt_id:
                return False
            if row.get("attempt_id") in seen_ids:
                return False
            seen_ids.add(record.context.attempt_id)
            if row.get("receipt_sha256") != record.attempt_receipt_sha256:
                return False
            if row.get("outcome_sha256") != record.outcome_sha256:
                return False
            if (
                record.context.attempt_id == selected_id
                and row.get("receipt_sha256") != selected_receipt_sha256
            ):
                return False
        return selected_id in seen_ids
    except (OSError, TypeError, ValueError, AttemptSequenceError, json.JSONDecodeError):
        return False


def _sequence_request_document(
    *,
    initial_context: EpisodeContext,
    retry_policy: RetryPolicy,
    policy_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": "vaevas-attempt-sequence-request-v1",
        "initial_context": _context_document(initial_context),
        "retry_policy_sha256": policy_sha256,
        "retry_policy": retry_policy.to_document(),
    }


def _load_attempt_records_from_selection(
    *,
    root: Path,
    initial_context: Mapping[str, Any],
    policy: RetryPolicy,
    selection: Mapping[str, Any],
    sequence_request_sha256: str,
    policy_sha256: str,
) -> tuple[AttemptRecord, ...]:
    rows = selection["attempt_receipts"]
    if (not isinstance(rows, list) or not rows or len(rows) > policy.max_attempts
            or any(not isinstance(row, Mapping) or not _has_exact_keys(
                row, {"attempt_id", "receipt_sha256", "outcome_sha256"}) for row in rows)):
        raise AttemptSequenceError("invalid selection attempt roster")
    records: list[AttemptRecord] = []
    previous_attempt_id: str | None = None
    previous_failure_category: str | None = None
    previous_model_calls = initial_context.get("model_calls_before_attempt", 0)
    for index, row in enumerate(rows):
        next_attempt_id = None
        if index + 1 < len(rows):
            next_attempt_id = rows[index + 1]["attempt_id"]
        record, previous_model_calls = _load_attempt_record(
            root=root,
            attempt_id=row["attempt_id"],
            initial_context=initial_context,
            policy=policy,
            sequence_request_sha256=sequence_request_sha256,
            policy_sha256=policy_sha256,
            previous_attempt_id=previous_attempt_id,
            previous_failure_category=previous_failure_category,
            previous_model_calls=previous_model_calls,
            expected_retry_index=index,
            expected_next_attempt_id=next_attempt_id,
        )
        if (record.retry_decision["retry_allowed"] is not (index + 1 < len(rows))
                or record.retry_decision["next_attempt_id"] != next_attempt_id):
            raise AttemptSequenceError("selection must end at the first non-retry terminal receipt")
        records.append(record)
        previous_attempt_id = record.context.attempt_id
        previous_failure_category = record.outcome.failure_category
    _validate_sequence_entries(root, records)
    return tuple(records)


def _validate_sequence_entries(root: Path, records: Sequence[AttemptRecord]) -> None:
    allowed = {"request.json", "selection.json", *(record.context.attempt_id for record in records)}
    if any(path.name not in allowed for path in root.iterdir()):
        raise AttemptSequenceError("sequence contains unrostered attempt activity")


def _load_attempt_prefix(
    *,
    root: Path,
    initial_context: EpisodeContext,
    policy: RetryPolicy,
    sequence_request_sha256: str,
    policy_sha256: str,
) -> tuple[tuple[AttemptRecord, ...], EpisodeContext | None]:
    initial_document = _context_document(initial_context)
    records: list[AttemptRecord] = []
    attempt_id = initial_context.attempt_id
    previous_attempt_id: str | None = None
    previous_failure_category: str | None = None
    previous_model_calls = initial_document.get("model_calls_before_attempt", 0)
    index = 0
    while (root / attempt_id).exists() or (root / attempt_id).is_symlink():
        attempt_dir = root / attempt_id
        if (
            not (attempt_dir / "request.json").is_file()
            or not (attempt_dir / "attempt.json").is_file()
        ):
            raise AttemptSequenceError("partial attempt cannot be resumed")
        record, previous_model_calls = _load_attempt_record(
            root=root,
            attempt_id=attempt_id,
            initial_context=initial_document,
            policy=policy,
            sequence_request_sha256=sequence_request_sha256,
            policy_sha256=policy_sha256,
            previous_attempt_id=previous_attempt_id,
            previous_failure_category=previous_failure_category,
            previous_model_calls=previous_model_calls,
            expected_retry_index=index,
            expected_next_attempt_id=_retry_attempt_id_from_index(
                initial_context.attempt_id,
                index + 1,
            ),
        )
        records.append(record)
        if not record.retry_decision["retry_allowed"]:
            _validate_sequence_entries(root, records)
            return tuple(records), None
        previous_attempt_id = record.context.attempt_id
        previous_failure_category = record.outcome.failure_category
        attempt_id = str(record.retry_decision["next_attempt_id"])
        index += 1
    if records:
        _validate_sequence_entries(root, records)
        last = records[-1]
        context = last.context.next_attempt(
            attempt_id=str(last.retry_decision["next_attempt_id"]),
            reason=str(last.outcome.failure_category),
        )
        if "model_calls" in context.budget_limits:
            context = replace(context, model_calls_before_attempt=previous_model_calls)
        return tuple(records), context
    raise AttemptSequenceError("partial attempt sequence has no attempts")


def _load_attempt_record(
    *,
    root: Path,
    attempt_id: str,
    initial_context: Mapping[str, Any],
    policy: RetryPolicy,
    sequence_request_sha256: str,
    policy_sha256: str,
    previous_attempt_id: str | None,
    previous_failure_category: str | None,
    previous_model_calls: int,
    expected_retry_index: int,
    expected_next_attempt_id: str | None,
) -> tuple[AttemptRecord, int]:
    if not _valid_path_segment(attempt_id):
        raise AttemptSequenceError("invalid attempt_id")
    attempt_dir = root / attempt_id
    if not _is_confined_directory(attempt_dir, root):
        raise AttemptSequenceError("attempt directory escaped output root")
    request_path = attempt_dir / "request.json"
    attempt_path = attempt_dir / "attempt.json"
    if not request_path.is_file() or not attempt_path.is_file():
        raise AttemptSequenceError("partial attempt cannot be resumed")
    request = _read_receipt(request_path)
    attempt = _read_receipt(attempt_path)
    if request.get("schema_version") != "vaevas-attempt-request-v1":
        raise AttemptSequenceError("invalid attempt request schema")
    if attempt.get("schema_version") != "vaevas-attempt-receipt-v1":
        raise AttemptSequenceError("invalid attempt receipt schema")
    if not _has_exact_keys(
        request,
        {
            "schema_version",
            "sequence_request_sha256",
            "retry_policy_sha256",
            "context",
            "runtime_path",
        },
    ) or not _has_exact_keys(
        attempt,
        {
            "schema_version", "sequence_request_sha256", "retry_policy_sha256",
            "request_sha256", "context", "runtime_path", "outcome", "outcome_sha256",
            "retry_decision",
        },
    ):
        raise AttemptSequenceError("attempt receipt contains unknown or missing keys")
    request_context = _validated_context_document(
        request.get("context"),
        expected=initial_context,
    )
    attempt_context = _validated_context_document(
        attempt.get("context"),
        expected=initial_context,
    )
    if request_context != attempt_context:
        raise AttemptSequenceError("attempt context mismatch")
    if request_context.get("model_calls_before_attempt", 0) != previous_model_calls:
        raise AttemptSequenceError("model-call lineage mismatch")
    if request_context["attempt_id"] != attempt_id:
        raise AttemptSequenceError("attempt identity mismatch")
    if not _expected_lineage(
        context=request_context,
        initial_context=initial_context,
        previous_attempt_id=previous_attempt_id,
        previous_failure_category=previous_failure_category,
        expected_retry_index=expected_retry_index,
    ):
        raise AttemptSequenceError("attempt lineage mismatch")
    runtime_path = request.get("runtime_path")
    if runtime_path != attempt.get("runtime_path"):
        raise AttemptSequenceError("runtime path mismatch")
    if not isinstance(runtime_path, str) or not _valid_relative_path(runtime_path):
        raise AttemptSequenceError("runtime path is invalid")
    runtime = root / runtime_path
    if not _is_confined_directory(runtime, attempt_dir):
        raise AttemptSequenceError("runtime directory escaped attempt")
    if request.get("sequence_request_sha256") != sequence_request_sha256:
        raise AttemptSequenceError("sequence request hash mismatch")
    if attempt.get("sequence_request_sha256") != sequence_request_sha256:
        raise AttemptSequenceError("sequence request hash mismatch")
    if (
        request.get("retry_policy_sha256") != policy_sha256
        or attempt.get("retry_policy_sha256") != policy_sha256
    ):
        raise AttemptSequenceError("retry policy hash mismatch")
    request_sha256 = _canonical_sha256(request)
    if attempt.get("request_sha256") != request_sha256:
        raise AttemptSequenceError("attempt request hash mismatch")
    outcome = _validated_outcome_document(attempt.get("outcome"))
    next_model_calls = previous_model_calls
    if "model_calls" in request_context["budget_limits"]:
        try:
            next_model_calls = _model_calls_after(request_context, outcome["evidence"])
        except AttemptSequenceError as exc:
            if not (
                outcome.get("failure_category") == "unresolved_callback_exception"
                and outcome.get("failure_phase") == "unresolved"
                and outcome.get("primary_outcome") == "infrastructure_failure"
                and outcome.get("terminal_reason") == "model_call_accounting_unknown"
                and outcome.get("score_present") is False
            ):
                raise exc
    if attempt.get("outcome_sha256") != _canonical_sha256(outcome):
        raise AttemptSequenceError("outcome hash mismatch")
    decision = attempt.get("retry_decision")
    if not _valid_retry_decision(decision):
        raise AttemptSequenceError("retry decision is invalid")
    computed_decision = _retry_decision(
        outcome=AttemptOutcome.from_value(outcome),
        policy=policy,
        current_attempt_count=expected_retry_index + 1,
        next_attempt_id=expected_next_attempt_id
        or _retry_attempt_id_from_index(initial_context["attempt_id"], expected_retry_index + 1),
    )
    if dict(decision) != computed_decision:
        raise AttemptSequenceError("retry decision mismatch")
    context = _context_from_document(request_context)
    record = AttemptRecord(
        context=context,
        runtime_path=runtime,
        request_sha256=request_sha256,
        outcome=AttemptOutcome.from_value(outcome),
        outcome_sha256=str(attempt["outcome_sha256"]),
        retry_decision=dict(decision),
        attempt_receipt_sha256=_canonical_sha256(attempt),
    )
    return record, next_model_calls


def _context_from_document(document: Mapping[str, Any]) -> EpisodeContext:
    return EpisodeContext(
        episode_id=str(document["episode_id"]),
        attempt_id=str(document["attempt_id"]),
        task_id=str(document["task_id"]),
        condition=str(document["condition"]),
        max_steps=document["max_steps"],
        budget_limits=document["budget_limits"],
        parent_attempt_id=document["parent_attempt_id"],
        retry_index=document["retry_index"],
        retry_reason=document["retry_reason"],
        model_calls_before_attempt=document.get("model_calls_before_attempt", 0),
    )


def _retry_decision(
    *,
    outcome: AttemptOutcome,
    policy: RetryPolicy,
    current_attempt_count: int,
    next_attempt_id: str,
) -> dict[str, Any]:
    reason = _retry_rejection_reason(outcome, policy, current_attempt_count)
    allowed = reason == "pre_final_infrastructure_failure"
    return {
        "retry_allowed": allowed,
        "reason": reason,
        "next_attempt_id": next_attempt_id if allowed else None,
    }


def _retry_rejection_reason(
    outcome: AttemptOutcome,
    policy: RetryPolicy,
    current_attempt_count: int,
) -> str:
    if outcome.primary_outcome != "infrastructure_failure":
        return "not_infrastructure_failure"
    if outcome.failure_category == "unresolved_callback_exception" or outcome.failure_phase == "unresolved":
        return "unresolved_callback_exception"
    if outcome.evidence.get("model_call_budget", {}).get("remaining") == 0:
        return "model_call_limit"
    if outcome.submission_frozen or outcome.final_started:
        return "post_freeze_failure"
    if outcome.failure_phase != "pre_final":
        return "not_pre_final"
    if outcome.failure_category not in policy.retry_categories:
        return "category_not_whitelisted"
    if current_attempt_count >= policy.max_attempts:
        return "max_attempts_exhausted"
    return "pre_final_infrastructure_failure"


def _retry_attempt_id(initial_context: EpisodeContext, retry_number: int) -> str:
    return f"{initial_context.attempt_id}-retry-{retry_number:04d}"


def _retry_attempt_id_from_index(initial_attempt_id: str, retry_number: int) -> str:
    return f"{initial_attempt_id}-retry-{retry_number:04d}"


def _reserve_output_root(output_root: Path) -> Path:
    if output_root.is_symlink():
        raise AttemptSequenceError("output root must not be a symlink")
    try:
        output_root.mkdir(mode=0o700, parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise AttemptSequenceError("attempt sequence requires a fresh output root") from exc
    except OSError as exc:
        raise AttemptSequenceError(f"failed to reserve output root: {exc}") from exc
    return output_root.resolve(strict=True)


def _validated_existing_root(output_root: Path) -> Path:
    if output_root.is_symlink():
        raise AttemptSequenceError("output root must not be a symlink")
    root = output_root.resolve(strict=True)
    if not root.is_dir():
        raise AttemptSequenceError("output root must be a directory")
    return root


def _reserve_attempt_runtime(root: Path, attempt_id: str) -> tuple[Path, Path]:
    _require_identity(attempt_id, field_name="attempt_id")
    if "/" in attempt_id or attempt_id in {".", ".."}:
        raise AttemptSequenceError("attempt_id must be a confined path segment")
    attempt_dir = root / attempt_id
    try:
        attempt_dir.mkdir(mode=0o700, exist_ok=False)
        runtime = attempt_dir / "runtime"
        runtime.mkdir(mode=0o700, exist_ok=False)
    except FileExistsError as exc:
        raise AttemptSequenceError("attempt output already exists") from exc
    if attempt_dir.is_symlink() or runtime.is_symlink():
        raise AttemptSequenceError("attempt paths must not be symlinks")
    if attempt_dir.resolve(strict=True).parent != root:
        raise AttemptSequenceError("attempt directory escaped output root")
    if runtime.resolve(strict=True).parent != attempt_dir.resolve(strict=True):
        raise AttemptSequenceError("runtime directory escaped attempt directory")
    return attempt_dir, runtime


def _write_receipt(path: Path, document: Mapping[str, Any]) -> str:
    payload = _canonical_json_bytes(document)
    digest = hashlib.sha256(payload).hexdigest()
    with path.open("xb") as handle:
        handle.write(payload)
        handle.write(b"\n")
        handle.flush()
        os.fsync(handle.fileno())
    path.chmod(0o444)
    _fsync_directory(path.parent)
    return digest


def _read_receipt(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise AttemptSequenceError("receipt must not be a symlink")
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_json_object_without_duplicate_keys,
    )
    if not isinstance(value, dict):
        raise AttemptSequenceError("receipt must be a JSON object")
    return value


def _json_object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AttemptSequenceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _context_document(context: EpisodeContext) -> dict[str, Any]:
    return {
        "episode_id": context.episode_id,
        "attempt_id": context.attempt_id,
        "task_id": context.task_id,
        "condition": context.condition,
        "max_steps": context.max_steps,
        "budget_limits": _json_ready(context.budget_limits),
        **({"model_calls_before_attempt": context.model_calls_before_attempt}
           if "model_calls" in context.budget_limits else {}),
        "parent_attempt_id": context.parent_attempt_id,
        "retry_index": context.retry_index,
        "retry_reason": context.retry_reason,
    }


def _required_str(value: Mapping[str, Any], field_name: str) -> str:
    item = value.get(field_name)
    if not isinstance(item, str) or not item.strip():
        raise ValueError(f"{field_name} must be non-empty")
    return item


def _optional_bool(value: Mapping[str, Any], field_name: str) -> bool:
    if field_name not in value:
        return False
    item = value[field_name]
    if not isinstance(item, bool):
        raise TypeError(f"{field_name} must be a boolean")
    return item


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("optional identity fields must be non-empty strings")
    return value


def _validated_policy_document(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise AttemptSequenceError("retry policy must be an object")
    if not _has_exact_keys(value, {"schema_version", "max_attempts", "retry_categories"}):
        raise AttemptSequenceError("retry policy contains unknown or missing keys")
    if value.get("schema_version") != "vaevas-retry-policy-v1":
        raise AttemptSequenceError("invalid retry policy schema")
    max_attempts = value.get("max_attempts")
    categories = value.get("retry_categories")
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int):
        raise AttemptSequenceError("invalid retry policy max_attempts")
    if not isinstance(categories, list) or any(
        not isinstance(category, str) for category in categories
    ):
        raise AttemptSequenceError("invalid retry policy categories")
    policy = RetryPolicy(max_attempts=max_attempts, retry_categories=frozenset(categories))
    document = policy.to_document()
    if dict(value) != document:
        raise AttemptSequenceError("retry policy is not canonical")
    return document


def _validated_context_document(
    value: object,
    *,
    expected: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise AttemptSequenceError("context must be an object")
    if not _has_exact_keys(
        value,
        {
            "episode_id",
            "attempt_id",
            "task_id",
            "condition",
            "max_steps",
            "budget_limits",
            "parent_attempt_id",
            "retry_index",
            "retry_reason",
        } | ({"model_calls_before_attempt"} if "model_calls" in value.get("budget_limits", {}) else set()),
    ):
        raise AttemptSequenceError("context contains unknown or missing keys")
    required_strings = ("episode_id", "attempt_id", "task_id", "condition")
    for field_name in required_strings:
        if not isinstance(value.get(field_name), str) or not value[field_name].strip():
            raise AttemptSequenceError(f"invalid context {field_name}")
    if not _valid_path_segment(value["attempt_id"]):
        raise AttemptSequenceError("invalid context attempt_id")
    max_steps = value.get("max_steps")
    if max_steps is not None and (isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps <= 0):
        raise AttemptSequenceError("invalid context max_steps")
    budget_limits = value.get("budget_limits")
    if not isinstance(budget_limits, Mapping):
        raise AttemptSequenceError("invalid context budget_limits")
    for key, item in budget_limits.items():
        if not isinstance(key, str) or not key.strip():
            raise AttemptSequenceError("invalid budget counter")
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise AttemptSequenceError("invalid budget limit")
        if key == "model_calls" and item == 0:
            raise AttemptSequenceError("model-call limit must be positive")
    retry_index = value.get("retry_index")
    if isinstance(retry_index, bool) or not isinstance(retry_index, int) or retry_index < 0:
        raise AttemptSequenceError("invalid context retry_index")
    parent_attempt_id = value.get("parent_attempt_id")
    retry_reason = value.get("retry_reason")
    if parent_attempt_id is not None and (
        not isinstance(parent_attempt_id, str) or not _valid_path_segment(parent_attempt_id)
    ):
        raise AttemptSequenceError("invalid parent_attempt_id")
    if retry_reason is not None and (not isinstance(retry_reason, str) or not retry_reason.strip()):
        raise AttemptSequenceError("invalid retry_reason")
    document = {
        "episode_id": value["episode_id"],
        "attempt_id": value["attempt_id"],
        "task_id": value["task_id"],
        "condition": value["condition"],
        "max_steps": max_steps,
        "budget_limits": dict(budget_limits),
        "parent_attempt_id": parent_attempt_id,
        "retry_index": retry_index,
        "retry_reason": retry_reason,
    }
    if "model_calls" in budget_limits:
        prior = value.get("model_calls_before_attempt")
        if type(prior) is not int or not 0 <= prior <= budget_limits["model_calls"]:
            raise AttemptSequenceError("invalid prior model calls")
        document["model_calls_before_attempt"] = prior
    if expected is not None:
        for field_name in ("episode_id", "task_id", "condition", "max_steps", "budget_limits"):
            if document[field_name] != expected[field_name]:
                raise AttemptSequenceError("context drift")
    return document


def _model_calls_after(context: Mapping, evidence: Mapping) -> int:
    """Validate cumulative usage before allowing a fresh attempt; never refund."""
    budget = evidence.get("model_call_budget")
    limit = context["budget_limits"]["model_calls"]
    before = context["model_calls_before_attempt"]
    if not isinstance(budget, Mapping) or any(type(value) is not int for value in budget.values()):
        raise AttemptSequenceError("missing or invalid model-call accounting")
    admitted = budget.get("admitted_in_attempt", -1)
    used = before + admitted
    if (admitted < 0 or used > limit or dict(budget) != {
            "limit": limit, "used_before_attempt": before, "admitted_in_attempt": admitted,
            "used_total": used, "remaining": limit - used}):
        raise AttemptSequenceError("model-call accounting mismatch")
    return used


def _validated_outcome_document(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise AttemptSequenceError("outcome must be an object")
    if not _has_exact_keys(
        value,
        {
            "primary_outcome",
            "terminal_reason",
            "failure_category",
            "failure_phase",
            "submission_frozen",
            "final_started",
            "evidence",
            "score_present",
        },
    ):
        raise AttemptSequenceError("outcome contains unknown or missing keys")
    for field_name in ("primary_outcome", "terminal_reason"):
        if not isinstance(value.get(field_name), str) or not value[field_name].strip():
            raise AttemptSequenceError(f"invalid outcome {field_name}")
    for field_name in ("failure_category", "failure_phase"):
        item = value.get(field_name)
        if item is not None and (not isinstance(item, str) or not item.strip()):
            raise AttemptSequenceError(f"invalid outcome {field_name}")
    for field_name in ("submission_frozen", "final_started", "score_present"):
        if not isinstance(value.get(field_name), bool):
            raise AttemptSequenceError(f"invalid outcome {field_name}")
    evidence = value.get("evidence")
    if not isinstance(evidence, Mapping):
        raise AttemptSequenceError("invalid outcome evidence")
    return {
        "primary_outcome": value["primary_outcome"],
        "terminal_reason": value["terminal_reason"],
        "failure_category": value.get("failure_category"),
        "failure_phase": value.get("failure_phase"),
        "submission_frozen": value["submission_frozen"],
        "final_started": value["final_started"],
        "evidence": dict(evidence),
        "score_present": value["score_present"],
    }


def _expected_lineage(
    *,
    context: Mapping[str, Any],
    initial_context: Mapping[str, Any],
    previous_attempt_id: str | None,
    previous_failure_category: str | None,
    expected_retry_index: int,
) -> bool:
    if previous_attempt_id is None:
        return (
            context["attempt_id"] == initial_context["attempt_id"]
            and context["retry_index"] == 0
            and context["parent_attempt_id"] is None
            and context["retry_reason"] is None
        )
    return (
        context["retry_index"] == expected_retry_index
        and context["parent_attempt_id"] == previous_attempt_id
        and context["retry_reason"] == previous_failure_category
    )


def _valid_retry_decision(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    if not _has_exact_keys(value, {"retry_allowed", "reason", "next_attempt_id"}):
        return False
    allowed = value.get("retry_allowed")
    if not isinstance(allowed, bool):
        return False
    reason = value.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        return False
    next_attempt_id = value.get("next_attempt_id")
    if allowed:
        return isinstance(next_attempt_id, str) and _valid_path_segment(next_attempt_id)
    return next_attempt_id is None


def _initial_lineage_is_root(context: Mapping[str, Any]) -> bool:
    return (
        context["retry_index"] == 0
        and context["parent_attempt_id"] is None
        and context["retry_reason"] is None
    )


def _has_exact_keys(value: Mapping[str, Any], expected: set[str]) -> bool:
    return set(value) == expected


def _valid_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _valid_path_segment(value: str) -> bool:
    return bool(value) and value not in {".", ".."} and "/" not in value and "\\" not in value


def _valid_relative_path(value: str) -> bool:
    path = Path(value)
    return not path.is_absolute() and all(_valid_path_segment(part) for part in path.parts)


def _is_confined_directory(path: Path, parent: Path) -> bool:
    if path.is_symlink():
        return False
    try:
        resolved = path.resolve(strict=True)
        parent_resolved = parent.resolve(strict=True)
    except OSError:
        return False
    return resolved.is_dir() and resolved.parent == parent_resolved


def _require_identity(value: str, *, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be non-empty")


def _freeze_json_object(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a JSON object")
    return _freeze_json(value)


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_json(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        return value
    raise TypeError(f"value is not JSON-compatible: {type(value).__name__}")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    return value


def _canonical_json_bytes(document: Any) -> bytes:
    return json.dumps(
        _json_ready(document),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _canonical_sha256(document: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(document)).hexdigest()


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(directory, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
