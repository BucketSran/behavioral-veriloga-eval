from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest

from runners.agent_harness.attempt_sequence import (
    AttemptOutcome,
    AttemptSequenceError,
    RetryPolicy,
    run_attempt_sequence,
    verify_attempt_sequence_receipts,
)
from runners.agent_harness.state import EpisodeContext


@pytest.mark.parametrize("evidence", [{}, {"model_call_budget": {}}, {"model_call_budget": {"used_total": True}}])
def test_missing_budget_accounting_cannot_remain_successful(tmp_path, evidence):
    context = EpisodeContext("cell", "attempt", "task", "Agentic", None, {"model_calls": 3})
    root = tmp_path / "sequence"
    result = run_attempt_sequence(
        initial_context=context, output_root=root, retry_policy=_policy(),
        execute=lambda *_: AttemptOutcome("passed", "submitted", score=1.0, evidence=evidence),
    )
    assert result.selected.primary_outcome == "infrastructure_failure"
    assert result.selected.terminal_reason == "model_call_accounting_unknown"
    assert result.selected.score is None and result.attempt_count == 1
    assert verify_attempt_sequence_receipts(root)
    receipt = _receipt(root / "attempt/attempt.json")
    receipt["outcome"].update(primary_outcome="passed", terminal_reason="submitted", score_present=True)
    receipt["retry_decision"]["reason"] = "not_infrastructure_failure"
    _overwrite_receipt(root / "attempt/attempt.json", receipt)
    _rewrite_attempt_and_selection_hashes(root, "attempt")
    assert not verify_attempt_sequence_receipts(root)


def _context() -> EpisodeContext:
    return EpisodeContext(
        episode_id="episode-001",
        attempt_id="attempt-001",
        task_id="v4-001",
        condition="Agentic+EVAS",
        max_steps=4,
        budget_limits={"tool_call": 3},
    )


def test_verifier_rejects_rehashed_zero_model_call_limit(tmp_path):
    root = tmp_path / "sequence"
    context = EpisodeContext("cell", "attempt", "task", "Agentic", None, {"model_calls": 1})
    run_attempt_sequence(
        initial_context=context, output_root=root, retry_policy=_policy(),
        execute=lambda *_: AttemptOutcome("infrastructure_failure", "fixture", evidence={
            "model_call_budget": {"limit": 1, "used_before_attempt": 0,
                                  "admitted_in_attempt": 0, "used_total": 0, "remaining": 1},
        }),
    )
    assert verify_attempt_sequence_receipts(root)
    sequence = _receipt(root / "request.json")
    sequence["initial_context"]["budget_limits"]["model_calls"] = 0
    _overwrite_receipt(root / "request.json", sequence)
    sequence_hash = _canonical_sha256(sequence)
    for name in ("request.json", "attempt.json"):
        path = root / "attempt" / name
        document = _receipt(path)
        document["sequence_request_sha256"] = sequence_hash
        document["context"]["budget_limits"]["model_calls"] = 0
        if name == "attempt.json":
            document["outcome"]["evidence"]["model_call_budget"].update(limit=0, remaining=0)
            document["retry_decision"]["reason"] = "model_call_limit"
        _overwrite_receipt(path, document)
    selection = _receipt(root / "selection.json")
    selection["sequence_request_sha256"] = sequence_hash
    _overwrite_receipt(root / "selection.json", selection)
    _rewrite_request_hashes(root, "attempt")
    assert not verify_attempt_sequence_receipts(root)


def _policy() -> RetryPolicy:
    return RetryPolicy(
        max_attempts=2,
        retry_categories=frozenset({"sandbox_startup", "provider_transport"}),
    )


def _receipt(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _overwrite_receipt(path: Path, value: dict) -> None:
    path.chmod(0o644)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _rewrite_attempt_and_selection_hashes(root: Path, attempt_id: str) -> None:
    attempt_path = root / attempt_id / "attempt.json"
    attempt = _receipt(attempt_path)
    attempt["outcome_sha256"] = _canonical_sha256(attempt["outcome"])
    attempt_sha256 = _canonical_sha256(attempt)
    _overwrite_receipt(attempt_path, attempt)

    selection_path = root / "selection.json"
    selection = _receipt(selection_path)
    for row in selection["attempt_receipts"]:
        if row["attempt_id"] == attempt_id:
            row["receipt_sha256"] = attempt_sha256
            row["outcome_sha256"] = attempt["outcome_sha256"]
    if selection["selected_attempt_id"] == attempt_id:
        selection["selected_attempt_receipt_sha256"] = attempt_sha256
    _overwrite_receipt(selection_path, selection)


def _rewrite_request_hashes(root: Path, attempt_id: str) -> None:
    request_path = root / attempt_id / "request.json"
    request = _receipt(request_path)
    request_sha256 = _canonical_sha256(request)

    attempt_path = root / attempt_id / "attempt.json"
    attempt = _receipt(attempt_path)
    attempt["request_sha256"] = request_sha256
    _overwrite_receipt(attempt_path, attempt)
    _rewrite_attempt_and_selection_hashes(root, attempt_id)


def test_attempt_sequence_records_single_success_without_retry(tmp_path: Path) -> None:
    calls: list[tuple[EpisodeContext, Path]] = []

    def execute(context: EpisodeContext, runtime: Path) -> AttemptOutcome:
        calls.append((context, runtime))
        assert context == _context()
        assert runtime.is_dir()
        (runtime / "marker.txt").write_text("fresh", encoding="utf-8")
        return AttemptOutcome(
            primary_outcome="pass",
            terminal_reason="completed",
            evidence={"result_sha256": "a" * 64},
        )

    result = run_attempt_sequence(
        initial_context=_context(),
        output_root=tmp_path / "sequence",
        retry_policy=_policy(),
        execute=execute,
    )

    assert result.selected_attempt_id == "attempt-001"
    assert result.attempt_count == 1
    assert result.selected.primary_outcome == "pass"
    assert calls == [(_context(), tmp_path / "sequence" / "attempt-001" / "runtime")]
    assert _receipt(tmp_path / "sequence" / "attempt-001" / "request.json")["context"]["attempt_id"] == "attempt-001"
    assert _receipt(tmp_path / "sequence" / "selection.json")["selected_attempt_id"] == "attempt-001"
    assert verify_attempt_sequence_receipts(tmp_path / "sequence") is True


def test_resume_reuses_completed_selection_without_execute(tmp_path: Path) -> None:
    root = tmp_path / "sequence"
    first = run_attempt_sequence(
        initial_context=_context(),
        output_root=root,
        retry_policy=_policy(),
        execute=lambda _context, _runtime: AttemptOutcome("pass", "completed"),
    )

    resumed = run_attempt_sequence(
        initial_context=_context(),
        output_root=root,
        retry_policy=_policy(),
        resume=True,
        execute=lambda _context, _runtime: pytest.fail("completed resume must not execute"),
    )

    assert resumed.selected_attempt_id == first.selected_attempt_id
    assert resumed.selection_sha256 == first.selection_sha256
    assert resumed.attempt_count == 1


def test_selection_cannot_mark_retryable_last_receipt_as_complete(tmp_path):
    root = tmp_path / "sequence"
    run_attempt_sequence(initial_context=_context(), output_root=root, retry_policy=_policy(),
                         execute=lambda *_: AttemptOutcome("pass", "completed"))
    receipt = _receipt(root / "attempt-001/attempt.json")
    receipt["outcome"] = AttemptOutcome(
        "infrastructure_failure", "startup", failure_category="sandbox_startup",
        failure_phase="pre_final").to_document()
    receipt["retry_decision"] = {"retry_allowed": True, "reason": "pre_final_infrastructure_failure",
                                 "next_attempt_id": "attempt-001-retry-0001"}
    _overwrite_receipt(root / "attempt-001/attempt.json", receipt)
    _rewrite_attempt_and_selection_hashes(root, "attempt-001")
    assert not verify_attempt_sequence_receipts(root)


@pytest.mark.parametrize("selection_present", [False, True])
def test_unrostered_attempt_blocks_terminal_reuse_and_selection_repair(tmp_path, selection_present):
    root = tmp_path / "sequence"
    run_attempt_sequence(initial_context=_context(), output_root=root, retry_policy=_policy(),
                         execute=lambda *_: AttemptOutcome("pass", "completed"))
    if not selection_present:
        (root / "selection.json").unlink()
    stray = root / "attempt-001-retry-0001"
    stray.mkdir()
    (stray / "request.json").write_text("{}")
    with pytest.raises(AttemptSequenceError):
        run_attempt_sequence(initial_context=_context(), output_root=root, retry_policy=_policy(),
                             resume=True, execute=lambda *_: pytest.fail("must not execute"))
    assert (root / "selection.json").exists() is selection_present


@pytest.mark.parametrize("row", [None, {}, "invalid"])
def test_malformed_selection_row_fails_closed_without_raising_keyerror(tmp_path, row):
    root = tmp_path / "sequence"
    run_attempt_sequence(initial_context=_context(), output_root=root, retry_policy=_policy(),
                         execute=lambda *_: AttemptOutcome("pass", "completed"))
    selection = _receipt(root / "selection.json")
    selection["attempt_receipts"].insert(0, row)
    _overwrite_receipt(root / "selection.json", selection)
    assert not verify_attempt_sequence_receipts(root)


def test_resume_continues_after_last_sealed_retry_allowed_attempt(tmp_path: Path) -> None:
    root = tmp_path / "sequence"
    run_attempt_sequence(
        initial_context=_context(),
        output_root=root,
        retry_policy=RetryPolicy(max_attempts=1, retry_categories=frozenset({"sandbox_startup"})),
        execute=lambda _context, _runtime: AttemptOutcome(
            "infrastructure_failure",
            "retryable transport",
            failure_category="sandbox_startup",
            failure_phase="pre_final",
        ),
    )
    (root / "selection.json").chmod(0o644)
    (root / "selection.json").unlink()
    request = _receipt(root / "request.json")
    policy = RetryPolicy(max_attempts=2, retry_categories=frozenset({"sandbox_startup"}))
    request["retry_policy"] = policy.to_document()
    request["retry_policy_sha256"] = _canonical_sha256(policy.to_document())
    sequence_request_sha256 = _canonical_sha256(request)
    _overwrite_receipt(root / "request.json", request)
    attempt_request = _receipt(root / "attempt-001" / "request.json")
    attempt_request["sequence_request_sha256"] = sequence_request_sha256
    attempt_request["retry_policy_sha256"] = request["retry_policy_sha256"]
    _overwrite_receipt(root / "attempt-001" / "request.json", attempt_request)
    receipt = _receipt(root / "attempt-001" / "attempt.json")
    receipt["sequence_request_sha256"] = sequence_request_sha256
    receipt["retry_policy_sha256"] = request["retry_policy_sha256"]
    receipt["request_sha256"] = _canonical_sha256(attempt_request)
    receipt["retry_decision"] = {
        "retry_allowed": True,
        "reason": "pre_final_infrastructure_failure",
        "next_attempt_id": "attempt-001-retry-0001",
    }
    _overwrite_receipt(root / "attempt-001" / "attempt.json", receipt)

    calls: list[str] = []
    resumed = run_attempt_sequence(
        initial_context=_context(),
        output_root=root,
        retry_policy=policy,
        resume=True,
        execute=lambda context, _runtime: calls.append(context.attempt_id) or AttemptOutcome("pass", "completed"),
    )

    assert calls == ["attempt-001-retry-0001"]
    assert resumed.selected_attempt_id == "attempt-001-retry-0001"
    assert resumed.attempt_count == 2
    assert verify_attempt_sequence_receipts(root)


@pytest.mark.parametrize("limit", [2, 5])
def test_between_attempt_resume_keeps_original_call_limit(tmp_path, monkeypatch, limit):
    from runners.agent_harness import attempt_sequence as sequence
    root = tmp_path / "sequence"
    context = EpisodeContext("cell", "attempt", "task", "Agentic", None, {"model_calls": limit})
    policy = RetryPolicy(max_attempts=6, retry_categories=frozenset({"provider_transport"}))
    original_reserve = sequence._reserve_attempt_runtime
    calls = []

    def execute(current, _runtime):
        before = current.model_calls_before_attempt
        calls.append(before)
        return AttemptOutcome("infrastructure_failure", "transport",
                              failure_category="provider_transport", failure_phase="pre_final",
                              evidence={"model_call_budget": {
                                  "limit": limit, "used_before_attempt": before,
                                  "admitted_in_attempt": 1, "used_total": before + 1,
                                  "remaining": limit - before - 1}})

    def interrupt(root, attempt_id):
        if "retry" in attempt_id:
            raise KeyboardInterrupt("sealed boundary")
        return original_reserve(root, attempt_id)

    with monkeypatch.context() as patch:
        patch.setattr(sequence, "_reserve_attempt_runtime", interrupt)
        with pytest.raises(KeyboardInterrupt):
            run_attempt_sequence(initial_context=context, output_root=root,
                                 retry_policy=policy, execute=execute)
    assert calls == [0]
    resumed = run_attempt_sequence(initial_context=context, output_root=root,
                                   retry_policy=policy, execute=execute, resume=True)
    assert calls == list(range(limit))
    assert resumed.attempt_count == limit
    assert resumed.attempts[-1].retry_decision["reason"] == "model_call_limit"
    assert verify_attempt_sequence_receipts(root)


def test_resume_publishes_missing_selection_after_terminal_attempt(tmp_path: Path) -> None:
    root = tmp_path / "sequence"
    run_attempt_sequence(
        initial_context=_context(),
        output_root=root,
        retry_policy=_policy(),
        execute=lambda _context, _runtime: AttemptOutcome("pass", "completed"),
    )
    (root / "selection.json").chmod(0o644)
    (root / "selection.json").unlink()

    resumed = run_attempt_sequence(
        initial_context=_context(),
        output_root=root,
        retry_policy=_policy(),
        resume=True,
        execute=lambda _context, _runtime: pytest.fail("terminal resume must not execute"),
    )

    assert resumed.selected_attempt_id == "attempt-001"
    assert resumed.attempt_count == 1
    assert (root / "selection.json").is_file()
    assert verify_attempt_sequence_receipts(root)


def test_resume_rejects_partial_attempt_request_without_execution(tmp_path: Path) -> None:
    root = tmp_path / "sequence"
    calls = 0

    def execute(_context: EpisodeContext, _runtime: Path) -> AttemptOutcome:
        nonlocal calls
        calls += 1
        return AttemptOutcome("pass", "completed")

    run_attempt_sequence(
        initial_context=_context(),
        output_root=root,
        retry_policy=_policy(),
        execute=execute,
    )
    (root / "selection.json").chmod(0o644)
    (root / "selection.json").unlink()
    (root / "attempt-001" / "attempt.json").chmod(0o644)
    (root / "attempt-001" / "attempt.json").unlink()

    with pytest.raises(AttemptSequenceError, match="partial attempt"):
        run_attempt_sequence(
            initial_context=_context(),
            output_root=root,
            retry_policy=_policy(),
            resume=True,
            execute=execute,
        )

    assert calls == 1


def test_pre_final_infrastructure_failure_gets_fresh_retry_with_parent_lineage(tmp_path: Path) -> None:
    seen: list[tuple[str, str | None, int, Path, bool]] = []

    def execute(context: EpisodeContext, runtime: Path) -> AttemptOutcome:
        seen.append(
            (
                context.attempt_id,
                context.parent_attempt_id,
                context.retry_index,
                runtime,
                (runtime / "state.txt").exists(),
            )
        )
        (runtime / "state.txt").write_text(context.attempt_id, encoding="utf-8")
        if context.retry_index == 0:
            return AttemptOutcome(
                primary_outcome="infrastructure_failure",
                terminal_reason="sandbox failed before model",
                failure_category="sandbox_startup",
                failure_phase="pre_final",
            )
        return {
            "primary_outcome": "pass",
            "terminal_reason": "completed",
            "evidence": {"result_sha256": "b" * 64},
        }

    result = run_attempt_sequence(
        initial_context=_context(),
        output_root=tmp_path / "sequence",
        retry_policy=_policy(),
        execute=execute,
    )

    assert result.selected_attempt_id == "attempt-001-retry-0001"
    assert result.attempt_count == 2
    assert seen == [
        ("attempt-001", None, 0, tmp_path / "sequence" / "attempt-001" / "runtime", False),
        (
            "attempt-001-retry-0001",
            "attempt-001",
            1,
            tmp_path / "sequence" / "attempt-001-retry-0001" / "runtime",
            False,
        ),
    ]
    first = _receipt(tmp_path / "sequence" / "attempt-001" / "attempt.json")
    assert first["retry_decision"] == {
        "retry_allowed": True,
        "reason": "pre_final_infrastructure_failure",
        "next_attempt_id": "attempt-001-retry-0001",
    }
    second_request = _receipt(
        tmp_path / "sequence" / "attempt-001-retry-0001" / "request.json"
    )
    assert second_request["context"]["parent_attempt_id"] == "attempt-001"
    assert second_request["context"]["retry_reason"] == "sandbox_startup"
    assert verify_attempt_sequence_receipts(tmp_path / "sequence") is True


@pytest.mark.parametrize(
    ("outcome", "reason"),
    [
        (
            AttemptOutcome(
                "candidate_failure",
                "compile failed",
                failure_category="candidate_compile",
                failure_phase="candidate",
            ),
            "not_infrastructure_failure",
        ),
        (
            AttemptOutcome(
                "protocol_failure",
                "bad action",
                failure_category="malformed_action",
                failure_phase="protocol",
            ),
            "not_infrastructure_failure",
        ),
        (
            AttemptOutcome(
                "infrastructure_failure",
                "agent timeout",
                failure_category="agent_timeout",
                failure_phase="agent_timeout",
            ),
            "not_pre_final",
        ),
        (
            AttemptOutcome(
                "infrastructure_failure",
                "final judge failed",
                failure_category="final_judge",
                failure_phase="final_judge",
            ),
            "not_pre_final",
        ),
        (
            AttemptOutcome(
                "infrastructure_failure",
                "cleanup failed",
                failure_category="cleanup",
                failure_phase="cleanup",
            ),
            "not_pre_final",
        ),
        (
            AttemptOutcome(
                "infrastructure_failure",
                "unknown crash",
                failure_category="unknown",
                failure_phase="pre_final",
            ),
            "category_not_whitelisted",
        ),
        (
            AttemptOutcome(
                "infrastructure_failure",
                "post freeze failed",
                failure_category="sandbox_startup",
                failure_phase="pre_final",
                submission_frozen=True,
            ),
            "post_freeze_failure",
        ),
    ],
)
def test_rejected_categories_are_counted_without_retry(
    tmp_path: Path,
    outcome: AttemptOutcome,
    reason: str,
) -> None:
    calls = 0

    def execute(_context: EpisodeContext, _runtime: Path) -> AttemptOutcome:
        nonlocal calls
        calls += 1
        return outcome

    result = run_attempt_sequence(
        initial_context=_context(),
        output_root=tmp_path / reason,
        retry_policy=_policy(),
        execute=execute,
    )

    assert calls == 1
    assert result.selected_attempt_id == "attempt-001"
    assert result.attempts[0].retry_decision["retry_allowed"] is False
    assert result.attempts[0].retry_decision["reason"] == reason


def test_existing_or_symlink_output_root_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "sequence"
    root.mkdir()
    with pytest.raises(AttemptSequenceError, match="fresh output root"):
        run_attempt_sequence(
            initial_context=_context(),
            output_root=root,
            retry_policy=_policy(),
            execute=lambda _context, _runtime: AttemptOutcome("pass", "completed"),
        )

    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "linked-sequence"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(AttemptSequenceError, match="must not be a symlink"):
        run_attempt_sequence(
            initial_context=_context(),
            output_root=link,
            retry_policy=_policy(),
            execute=lambda _context, _runtime: AttemptOutcome("pass", "completed"),
        )


def test_callback_crash_is_preserved_as_unresolved_without_retry(tmp_path: Path) -> None:
    def execute(_context: EpisodeContext, runtime: Path) -> AttemptOutcome:
        (runtime / "partial.log").write_text("started", encoding="utf-8")
        raise RuntimeError("provider socket disappeared")

    result = run_attempt_sequence(
        initial_context=_context(),
        output_root=tmp_path / "sequence",
        retry_policy=_policy(),
        execute=execute,
    )

    assert result.attempt_count == 1
    assert result.selected.primary_outcome == "infrastructure_failure"
    assert result.selected.failure_category == "unresolved_callback_exception"
    assert result.attempts[0].retry_decision == {
        "retry_allowed": False,
        "reason": "unresolved_callback_exception",
        "next_attempt_id": None,
    }
    assert (tmp_path / "sequence" / "attempt-001" / "runtime" / "partial.log").is_file()
    assert verify_attempt_sequence_receipts(tmp_path / "sequence") is True


@pytest.mark.parametrize("raised", [KeyboardInterrupt, SystemExit])
def test_control_flow_exceptions_are_not_swallowed_or_selected(
    tmp_path: Path,
    raised: type[BaseException],
) -> None:
    def execute(_context: EpisodeContext, runtime: Path) -> AttemptOutcome:
        (runtime / "partial.log").write_text("started", encoding="utf-8")
        raise raised()

    with pytest.raises(raised):
        run_attempt_sequence(
            initial_context=_context(),
            output_root=tmp_path / raised.__name__,
            retry_policy=_policy(),
            execute=execute,
        )

    assert (tmp_path / raised.__name__ / "attempt-001" / "request.json").is_file()
    assert not (tmp_path / raised.__name__ / "selection.json").exists()


def test_policy_identity_drift_and_receipt_tampering_are_detected(tmp_path: Path) -> None:
    result = run_attempt_sequence(
        initial_context=_context(),
        output_root=tmp_path / "sequence",
        retry_policy=_policy(),
        execute=lambda _context, _runtime: AttemptOutcome("pass", "completed"),
    )

    assert result.policy_sha256 == _receipt(tmp_path / "sequence" / "request.json")["retry_policy_sha256"]
    assert verify_attempt_sequence_receipts(tmp_path / "sequence") is True
    selection = _receipt(tmp_path / "sequence" / "selection.json")
    selection["selected_attempt_id"] = "other"
    _overwrite_receipt(tmp_path / "sequence" / "selection.json", selection)

    assert verify_attempt_sequence_receipts(tmp_path / "sequence") is False


@pytest.mark.parametrize(
    "forbidden_category",
    [
        "candidate_compile",
        "protocol_failure",
        "agent_timeout",
        "budget_exhausted",
        "cleanup",
        "final_judge",
        "postfreeze",
        "unknown",
    ],
)
def test_retry_policy_rejects_forbidden_categories(forbidden_category: str) -> None:
    with pytest.raises(ValueError, match="forbidden retry category"):
        RetryPolicy(max_attempts=2, retry_categories=frozenset({forbidden_category}))


def test_mapping_outcome_rejects_string_booleans_and_bool_score() -> None:
    with pytest.raises(TypeError, match="submission_frozen"):
        AttemptOutcome.from_value({
            "primary_outcome": "infrastructure_failure",
            "terminal_reason": "bad bool",
            "submission_frozen": "false",
        })
    with pytest.raises(TypeError, match="final_started"):
        AttemptOutcome.from_value({
            "primary_outcome": "infrastructure_failure",
            "terminal_reason": "bad bool",
            "final_started": "false",
        })
    with pytest.raises(ValueError, match="score"):
        AttemptOutcome("pass", "completed", score=True)  # type: ignore[arg-type]


def test_direct_outcome_constructor_rejects_non_boolean_terminal_flags() -> None:
    with pytest.raises(TypeError, match="submission_frozen"):
        AttemptOutcome("pass", "completed", submission_frozen="false")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="final_started"):
        AttemptOutcome("pass", "completed", final_started="false")  # type: ignore[arg-type]


def test_initial_context_must_be_root_attempt_before_output_root_creation(tmp_path: Path) -> None:
    retry_context = _context().next_attempt(
        attempt_id="attempt-001-retry-0001",
        reason="sandbox_startup",
    )

    with pytest.raises(AttemptSequenceError, match="initial_context"):
        run_attempt_sequence(
            initial_context=retry_context,
            output_root=tmp_path / "sequence",
            retry_policy=_policy(),
            execute=lambda _context, _runtime: AttemptOutcome("pass", "completed"),
        )

    assert not (tmp_path / "sequence").exists()


def test_verifier_rejects_policy_digest_drift(tmp_path: Path) -> None:
    run_attempt_sequence(
        initial_context=_context(),
        output_root=tmp_path / "sequence",
        retry_policy=_policy(),
        execute=lambda _context, _runtime: AttemptOutcome("pass", "completed"),
    )

    request = _receipt(tmp_path / "sequence" / "request.json")
    request["retry_policy"] = {**request["retry_policy"], "max_attempts": 3}
    _overwrite_receipt(tmp_path / "sequence" / "request.json", request)

    assert verify_attempt_sequence_receipts(tmp_path / "sequence") is False


def test_verifier_rejects_context_mismatch_and_bad_lineage(tmp_path: Path) -> None:
    run_attempt_sequence(
        initial_context=_context(),
        output_root=tmp_path / "sequence",
        retry_policy=_policy(),
        execute=lambda context, _runtime: AttemptOutcome(
            "infrastructure_failure",
            "retry once",
            failure_category="sandbox_startup",
            failure_phase="pre_final",
        )
        if context.retry_index == 0
        else AttemptOutcome("pass", "completed"),
    )

    retry_attempt = tmp_path / "sequence" / "attempt-001-retry-0001" / "attempt.json"
    receipt = _receipt(retry_attempt)
    receipt["context"]["parent_attempt_id"] = "wrong-parent"
    _overwrite_receipt(retry_attempt, receipt)

    assert verify_attempt_sequence_receipts(tmp_path / "sequence") is False


def test_verifier_rejects_retry_index_drift_even_when_hashes_are_updated(tmp_path: Path) -> None:
    run_attempt_sequence(
        initial_context=_context(),
        output_root=tmp_path / "sequence",
        retry_policy=_policy(),
        execute=lambda context, _runtime: AttemptOutcome(
            "infrastructure_failure",
            "retry once",
            failure_category="sandbox_startup",
            failure_phase="pre_final",
        )
        if context.retry_index == 0
        else AttemptOutcome("pass", "completed"),
    )

    root = tmp_path / "sequence"
    retry_request_path = root / "attempt-001-retry-0001" / "request.json"
    retry_request = _receipt(retry_request_path)
    retry_request["context"]["retry_index"] = 9
    _overwrite_receipt(retry_request_path, retry_request)

    retry_attempt_path = root / "attempt-001-retry-0001" / "attempt.json"
    retry_attempt = _receipt(retry_attempt_path)
    retry_attempt["context"]["retry_index"] = 9
    _overwrite_receipt(retry_attempt_path, retry_attempt)
    _rewrite_request_hashes(root, "attempt-001-retry-0001")

    assert verify_attempt_sequence_receipts(root) is False


def test_verifier_rejects_path_traversal_before_external_reads(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "request.json").write_text("not json", encoding="utf-8")
    (outside / "attempt.json").write_text("not json", encoding="utf-8")
    run_attempt_sequence(
        initial_context=_context(),
        output_root=tmp_path / "sequence",
        retry_policy=_policy(),
        execute=lambda _context, _runtime: AttemptOutcome("pass", "completed"),
    )

    selection_path = tmp_path / "sequence" / "selection.json"
    selection = _receipt(selection_path)
    selection["attempt_receipts"][0]["attempt_id"] = "../outside"
    _overwrite_receipt(selection_path, selection)

    assert verify_attempt_sequence_receipts(tmp_path / "sequence") is False


def test_verifier_rejects_non_last_selection_and_missing_runtime(tmp_path: Path) -> None:
    run_attempt_sequence(
        initial_context=_context(),
        output_root=tmp_path / "sequence",
        retry_policy=_policy(),
        execute=lambda context, _runtime: AttemptOutcome(
            "infrastructure_failure",
            "retry once",
            failure_category="sandbox_startup",
            failure_phase="pre_final",
        )
        if context.retry_index == 0
        else AttemptOutcome("pass", "completed"),
    )

    selection_path = tmp_path / "sequence" / "selection.json"
    selection = _receipt(selection_path)
    selection["selected_attempt_id"] = "attempt-001"
    selection["selected_attempt_receipt_sha256"] = selection["attempt_receipts"][0]["receipt_sha256"]
    _overwrite_receipt(selection_path, selection)

    assert verify_attempt_sequence_receipts(tmp_path / "sequence") is False

    run_attempt_sequence(
        initial_context=_context(),
        output_root=tmp_path / "missing-runtime",
        retry_policy=_policy(),
        execute=lambda _context, _runtime: AttemptOutcome("pass", "completed"),
    )
    (tmp_path / "missing-runtime" / "attempt-001" / "runtime").rmdir()

    assert verify_attempt_sequence_receipts(tmp_path / "missing-runtime") is False


def test_verifier_recomputes_retry_decision_even_when_hashes_are_updated(tmp_path: Path) -> None:
    run_attempt_sequence(
        initial_context=_context(),
        output_root=tmp_path / "sequence",
        retry_policy=_policy(),
        execute=lambda context, _runtime: AttemptOutcome(
            "infrastructure_failure",
            "retry once",
            failure_category="sandbox_startup",
            failure_phase="pre_final",
        )
        if context.retry_index == 0
        else AttemptOutcome("pass", "completed"),
    )

    root = tmp_path / "sequence"
    first_path = root / "attempt-001" / "attempt.json"
    first = _receipt(first_path)
    first["retry_decision"] = {
        "retry_allowed": False,
        "reason": "category_not_whitelisted",
        "next_attempt_id": None,
    }
    _overwrite_receipt(first_path, first)
    _rewrite_attempt_and_selection_hashes(root, "attempt-001")

    assert verify_attempt_sequence_receipts(root) is False


def test_verifier_rejects_retry_decision_not_joined_to_following_attempt(tmp_path: Path) -> None:
    run_attempt_sequence(
        initial_context=_context(),
        output_root=tmp_path / "sequence",
        retry_policy=_policy(),
        execute=lambda context, _runtime: AttemptOutcome(
            "infrastructure_failure",
            "retry once",
            failure_category="provider_transport",
            failure_phase="pre_final",
        )
        if context.retry_index == 0
        else AttemptOutcome("pass", "completed"),
    )

    root = tmp_path / "sequence"
    first_path = root / "attempt-001" / "attempt.json"
    first = _receipt(first_path)
    first["retry_decision"]["next_attempt_id"] = "attempt-001-retry-9999"
    _overwrite_receipt(first_path, first)
    _rewrite_attempt_and_selection_hashes(root, "attempt-001")

    assert verify_attempt_sequence_receipts(root) is False


def test_verifier_rejects_terminal_row_that_still_allows_retry(tmp_path: Path) -> None:
    run_attempt_sequence(
        initial_context=_context(),
        output_root=tmp_path / "sequence",
        retry_policy=_policy(),
        execute=lambda _context, _runtime: AttemptOutcome("pass", "completed"),
    )

    root = tmp_path / "sequence"
    attempt_path = root / "attempt-001" / "attempt.json"
    attempt = _receipt(attempt_path)
    attempt["retry_decision"] = {
        "retry_allowed": True,
        "reason": "pre_final_infrastructure_failure",
        "next_attempt_id": "attempt-001-retry-0001",
    }
    _overwrite_receipt(attempt_path, attempt)
    _rewrite_attempt_and_selection_hashes(root, "attempt-001")

    assert verify_attempt_sequence_receipts(root) is False


def test_retry_policy_validates_finite_explicit_limits() -> None:
    with pytest.raises(ValueError, match="max_attempts"):
        RetryPolicy(max_attempts=0, retry_categories=frozenset({"sandbox_startup"}))
    with pytest.raises(TypeError, match="retry_categories"):
        RetryPolicy(max_attempts=2, retry_categories={"sandbox_startup"})  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="retry category"):
        RetryPolicy(max_attempts=2, retry_categories=frozenset({""}))
    with pytest.raises(TypeError, match="max_attempts"):
        RetryPolicy(max_attempts=True, retry_categories=frozenset({"sandbox_startup"}))  # type: ignore[arg-type]


def test_attempt_sequence_rejects_non_mapping_evidence_and_invalid_identity(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="initial_context"):
        run_attempt_sequence(  # type: ignore[arg-type]
            initial_context="attempt",
            output_root=tmp_path / "bad-context",
            retry_policy=_policy(),
            execute=lambda _context, _runtime: AttemptOutcome("pass", "completed"),
        )

    with pytest.raises(TypeError, match="evidence"):
        AttemptOutcome("pass", "completed", evidence=[])
