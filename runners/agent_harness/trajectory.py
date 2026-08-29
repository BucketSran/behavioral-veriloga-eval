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


def project_model_visible_events(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return only events explicitly admitted to model-visible memory."""

    return [event for event in events if event.get("visibility") == "model"]
