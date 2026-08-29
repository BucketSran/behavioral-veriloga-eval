from runners.agent_harness import (
    EpisodeContext,
    JsonlTrajectoryRecorder,
    read_trajectory,
    validate_trajectory,
    validate_trajectory_semantics,
)


def _context(attempt_id: str) -> EpisodeContext:
    return EpisodeContext(
        episode_id="episode-001",
        attempt_id=attempt_id,
        task_id="v4-001",
        condition="Agentic+EVAS",
        max_steps=4,
    )


def test_semantic_validator_rejects_cross_attempt_event_chain(tmp_path) -> None:
    recorder = JsonlTrajectoryRecorder(tmp_path / "cross-attempt.jsonl")
    recorder.append(
        context=_context("attempt-001"),
        actor="controller",
        event_type="episode_started",
        visibility="harness",
        payload={},
    )
    recorder.append(
        context=_context("attempt-002"),
        actor="controller",
        event_type="episode_failed",
        visibility="harness",
        payload={},
    )
    recorder.append(
        context=_context("attempt-002"),
        actor="environment",
        event_type="cleanup_completed",
        visibility="harness",
        payload={},
    )
    recorder.append(
        context=_context("attempt-002"),
        actor="controller",
        event_type="episode_completed",
        visibility="harness",
        payload={},
    )
    events = read_trajectory(tmp_path / "cross-attempt.jsonl")

    assert validate_trajectory(events) is True
    assert validate_trajectory_semantics(events) is False


def test_semantic_validator_rejects_authorization_without_proposal(tmp_path) -> None:
    path = tmp_path / "missing-proposal.jsonl"
    recorder = JsonlTrajectoryRecorder(path)
    context = _context("attempt-001")
    for actor, event_type, payload in (
        ("controller", "episode_started", {}),
        (
            "controller",
            "action_authorized",
            {"action_id": "action-001", "tool_name": "bash"},
        ),
        ("controller", "episode_failed", {}),
        ("environment", "cleanup_completed", {}),
        ("controller", "episode_completed", {}),
    ):
        recorder.append(
            context=context,
            actor=actor,
            event_type=event_type,
            visibility="harness",
            payload=payload,
        )
    events = read_trajectory(path)

    assert validate_trajectory(events) is True
    assert validate_trajectory_semantics(events) is False


def test_semantic_validator_rejects_model_visible_final_judgment(tmp_path) -> None:
    path = tmp_path / "leaked-final-judgment.jsonl"
    recorder = JsonlTrajectoryRecorder(path)
    context = _context("attempt-001")
    for actor, event_type, visibility in (
        ("controller", "episode_started", "harness"),
        ("environment", "submission_frozen", "harness"),
        ("final_judge", "final_judgment_completed", "model"),
        ("environment", "cleanup_completed", "harness"),
        ("controller", "episode_completed", "harness"),
    ):
        recorder.append(
            context=context,
            actor=actor,
            event_type=event_type,
            visibility=visibility,  # type: ignore[arg-type]
            payload={},
        )
    events = read_trajectory(path)

    assert validate_trajectory(events) is True
    assert validate_trajectory_semantics(events) is False


def test_semantic_validator_rejects_model_event_after_submission_freeze(
    tmp_path,
) -> None:
    path = tmp_path / "post-freeze-model-event.jsonl"
    recorder = JsonlTrajectoryRecorder(path)
    context = _context("attempt-001")
    for actor, event_type, visibility in (
        ("controller", "episode_started", "harness"),
        ("environment", "submission_frozen", "harness"),
        ("environment", "debug_payload", "model"),
        ("final_judge", "final_judgment_completed", "trusted"),
        ("environment", "cleanup_completed", "harness"),
        ("controller", "episode_completed", "harness"),
    ):
        recorder.append(
            context=context,
            actor=actor,
            event_type=event_type,
            visibility=visibility,  # type: ignore[arg-type]
            payload={},
        )
    events = read_trajectory(path)

    assert validate_trajectory(events) is True
    assert validate_trajectory_semantics(events) is False


def test_semantic_validator_rejects_duplicate_submission_freeze(tmp_path) -> None:
    path = tmp_path / "duplicate-freeze.jsonl"
    recorder = JsonlTrajectoryRecorder(path)
    context = _context("attempt-001")
    for actor, event_type, visibility in (
        ("controller", "episode_started", "harness"),
        ("environment", "submission_frozen", "harness"),
        ("environment", "submission_frozen", "harness"),
        ("final_judge", "final_judgment_completed", "trusted"),
        ("environment", "cleanup_completed", "harness"),
        ("controller", "episode_completed", "harness"),
    ):
        recorder.append(
            context=context,
            actor=actor,
            event_type=event_type,
            visibility=visibility,  # type: ignore[arg-type]
            payload={},
        )

    assert validate_trajectory_semantics(read_trajectory(path)) is False


def test_semantic_validator_rejects_unclosed_action(tmp_path) -> None:
    path = tmp_path / "unclosed-action.jsonl"
    recorder = JsonlTrajectoryRecorder(path)
    context = _context("attempt-001")
    for actor, event_type, visibility, payload in (
        ("controller", "episode_started", "harness", {}),
        (
            "policy",
            "action_proposed",
            "model",
            {"action_id": "action-001"},
        ),
        ("controller", "episode_failed", "harness", {}),
        ("environment", "cleanup_completed", "harness", {}),
        ("controller", "episode_completed", "harness", {}),
    ):
        recorder.append(
            context=context,
            actor=actor,
            event_type=event_type,
            visibility=visibility,  # type: ignore[arg-type]
            payload=payload,
        )

    assert validate_trajectory_semantics(read_trajectory(path)) is False


def test_semantic_validator_rejects_missing_or_duplicate_cleanup(tmp_path) -> None:
    for cleanup_events in ((), ("cleanup_completed", "cleanup_failed")):
        path = tmp_path / f"cleanup-{len(cleanup_events)}.jsonl"
        recorder = JsonlTrajectoryRecorder(path)
        context = _context("attempt-001")
        recorder.append(
            context=context,
            actor="controller",
            event_type="episode_started",
            visibility="harness",
            payload={},
        )
        recorder.append(
            context=context,
            actor="controller",
            event_type="episode_failed",
            visibility="harness",
            payload={},
        )
        for event_type in cleanup_events:
            recorder.append(
                context=context,
                actor="environment",
                event_type=event_type,
                visibility="harness",
                payload={},
            )
        recorder.append(
            context=context,
            actor="controller",
            event_type="episode_completed",
            visibility="harness",
            payload={},
        )

        assert validate_trajectory_semantics(read_trajectory(path)) is False
