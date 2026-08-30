"""Append-only JSONL trajectory recording with a SHA-256 event chain."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Mapping

from .state import EpisodeContext, EventVisibility


_EVENT_VISIBILITIES = frozenset({"model", "harness", "trusted"})
_REQUIRED_EVENT_VISIBILITY = {
    "episode_started": "harness",
    "action_proposed": "model",
    "action_authorized": "harness",
    "action_rejected": "harness",
    "candidate_transition_rejected": "harness",
    "budget_updated": "harness",
    "environment_observed": "model",
    "submission_freeze_rejected": "harness",
    "submission_frozen": "harness",
    "final_judgment_completed": "trusted",
    "episode_failed": "harness",
    "cleanup_failed": "harness",
    "cleanup_completed": "harness",
    "episode_completed": "harness",
    "deadline_reached": "harness",
    "deadline_interruption": "harness",
}


def _event_sha256(event_without_hash: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        event_without_hash,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class JsonlTrajectoryRecorder:
    """Own a fresh attempt trajectory and append content-addressed events."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=False)
        self._sequence = 0
        self._tail_sha256: str | None = None

    @property
    def tail_sha256(self) -> str | None:
        return self._tail_sha256

    def append(
        self,
        *,
        context: EpisodeContext,
        actor: str,
        event_type: str,
        visibility: EventVisibility,
        payload: Mapping[str, Any],
    ) -> str:
        if visibility not in _EVENT_VISIBILITIES:
            raise ValueError(f"unsupported event visibility: {visibility}")
        event: dict[str, Any] = {
            "schema_version": "vaevas-trajectory-event-v1",
            "episode_id": context.episode_id,
            "attempt_id": context.attempt_id,
            "task_id": context.task_id,
            "condition": context.condition,
            "sequence": self._sequence,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "monotonic_ns": time.monotonic_ns(),
            "actor": actor,
            "event_type": event_type,
            "visibility": visibility,
            "payload": dict(payload),
            "prev_event_sha256": self._tail_sha256,
        }
        event["event_sha256"] = _event_sha256(event)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        self._sequence += 1
        self._tail_sha256 = event["event_sha256"]
        return self._tail_sha256


def read_trajectory(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def validate_trajectory(events: list[dict[str, Any]]) -> bool:
    previous_hash: str | None = None
    for sequence, event in enumerate(events):
        if event.get("sequence") != sequence:
            return False
        if event.get("prev_event_sha256") != previous_hash:
            return False
        recorded_hash = event.get("event_sha256")
        unhashed = dict(event)
        unhashed.pop("event_sha256", None)
        if recorded_hash != _event_sha256(unhashed):
            return False
        previous_hash = recorded_hash
    return True


def validate_trajectory_semantics(events: list[dict[str, Any]]) -> bool:
    """Validate attempt identity and lifecycle in an intact event chain."""

    if not events or not validate_trajectory(events):
        return False
    identity_fields = ("episode_id", "attempt_id", "task_id", "condition")
    expected_identity = tuple(events[0].get(field) for field in identity_fields)
    if any(value is None for value in expected_identity):
        return False
    if any(
        tuple(event.get(field) for field in identity_fields) != expected_identity
        for event in events
    ):
        return False
    event_types = [event.get("event_type") for event in events]
    if not (
        event_types[0] == "episode_started"
        and event_types[-1] == "episode_completed"
        and event_types.count("episode_started") == 1
        and event_types.count("episode_completed") == 1
    ):
        return False
    if any(
        event.get("event_type") in _REQUIRED_EVENT_VISIBILITY
        and event.get("visibility")
        != _REQUIRED_EVENT_VISIBILITY[event["event_type"]]
        for event in events
    ):
        return False
    terminal_count = event_types.count("episode_failed") + event_types.count(
        "final_judgment_completed"
    )
    if terminal_count != 1:
        return False
    cleanup_count = event_types.count("cleanup_completed") + event_types.count(
        "cleanup_failed"
    )
    if cleanup_count != 1 or event_types[-2] not in {
        "cleanup_completed",
        "cleanup_failed",
    }:
        return False
    if event_types.count("submission_frozen") > 1:
        return False
    deadline_count = event_types.count("deadline_reached")
    if deadline_count > 1:
        return False
    if not isinstance(events[-1].get("payload"), Mapping):
        return False
    terminal_reason = events[-1]["payload"].get("terminal_reason")
    if terminal_reason == "agent_timeout" and deadline_count != 1:
        return False
    if deadline_count:
        deadline_index = event_types.index("deadline_reached")
        if any(event.get("visibility") == "model" for event in events[deadline_index + 1:]):
            return False
        if "submission_frozen" in event_types and (
            deadline_index > event_types.index("submission_frozen")
            or ("final_judgment_completed" in event_types and terminal_reason != "agent_timeout")
        ):
            return False
    if "final_judgment_completed" in event_types and not (
        "submission_frozen" in event_types
        and event_types.index("submission_frozen")
        < event_types.index("final_judgment_completed")
    ):
        return False
    if "submission_frozen" in event_types:
        freeze_index = event_types.index("submission_frozen")
        if any(
            event.get("visibility") == "model"
            for event in events[freeze_index + 1 :]
        ):
            return False
    proposed_action_id: str | None = None
    authorized_action_id: str | None = None
    for event in events:
        event_type = event.get("event_type")
        payload = event.get("payload")
        if not isinstance(payload, Mapping):
            return False
        action_id = payload.get("action_id")
        if event_type == "action_proposed":
            if (
                not isinstance(action_id, str)
                or proposed_action_id is not None
                or authorized_action_id is not None
            ):
                return False
            proposed_action_id = action_id
        elif event_type == "action_authorized":
            if action_id != proposed_action_id or authorized_action_id is not None:
                return False
            authorized_action_id = action_id
        elif event_type == "action_rejected":
            if action_id != proposed_action_id:
                return False
            proposed_action_id = None
            authorized_action_id = None
        elif event_type == "candidate_transition_rejected":
            if action_id != authorized_action_id:
                return False
            proposed_action_id = None
            authorized_action_id = None
        elif event_type == "budget_updated":
            if action_id != authorized_action_id:
                return False
        elif event_type == "environment_observed":
            if action_id != authorized_action_id:
                return False
            proposed_action_id = None
            authorized_action_id = None
    return proposed_action_id is None and authorized_action_id is None


def project_model_visible_events(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return only events explicitly admitted to model-visible memory."""

    return [event for event in events if event.get("visibility") == "model"]
