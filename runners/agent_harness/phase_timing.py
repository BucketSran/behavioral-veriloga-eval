"""Opt-in, payload-free execution timing; not score evidence or a scheduler.

Contexts are local to an execution thread/task. They are never injected into
model messages or authoritative trajectories. ``work_s`` sums spans of a phase;
it is not additive across nested phases and is not campaign wall time.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from datetime import datetime, timezone
from functools import wraps
import time


_PHASES = frozenset({
    "cell",
    "export",
    "setup",
    "model",
    "tool",
    "freeze",
    "final_judge",
    "cleanup",
})
_ACTIVE: ContextVar = ContextVar("vaevas_phase_timing", default=None)


def _utc():
    return datetime.now(timezone.utc).isoformat()


class PhaseTimings:
    def __init__(self, cell_id: str, attempt_id: str):
        if not all(isinstance(value, str) and value.strip() for value in (cell_id, attempt_id)):
            raise ValueError("timing requires cell and attempt identities")
        self.cell_id, self.attempt_id = cell_id, attempt_id
        self.started_at = _utc()
        self.started = time.perf_counter()
        self.ended = None
        self.ended_at = None
        self.spans = []

    def to_document(self) -> dict:
        if self.ended is None:
            raise ValueError("timing capture must finish before reporting")
        phases = {}
        for span in self.spans:
            summary = phases.setdefault(span["phase"], {"count": 0, "work_s": 0.0})
            summary["count"] += 1
            summary["work_s"] += span["duration_s"]
        return {
            "schema_version": "vaevas-phase-timing-v1",
            "cell_id": self.cell_id, "attempt_id": self.attempt_id,
            "started_at": self.started_at, "ended_at": self.ended_at,
            "elapsed_s": self.ended - self.started,
            "wall_time_policy": "observed_attempt_elapsed_not_additive_phase_sum",
            "phases": phases, "spans": deepcopy(self.spans),
        }


@contextmanager
def collect_phases(*, cell_id: str, attempt_id: str):
    """Collect one explicitly identified attempt; nesting restores its parent."""
    capture = PhaseTimings(cell_id, attempt_id)
    token = _ACTIVE.set(capture)
    try:
        yield capture
    finally:
        capture.ended = time.perf_counter()
        capture.ended_at = _utc()
        _ACTIVE.reset(token)


@contextmanager
def measure_phase(phase: str):
    """Measure a boundary when enabled; ``ok`` means returned, not task passed."""
    capture = _ACTIVE.get()
    if capture is None:
        yield
        return
    if phase not in _PHASES:
        raise ValueError("unknown execution phase")
    start = time.perf_counter()
    span = {"phase": phase, "started_at": _utc(),
            "start_offset_s": start - capture.started, "status": "ok", "error_type": None}
    capture.spans.append(span)
    try:
        yield
    except BaseException as exc:
        span.update(status="error", error_type=type(exc).__name__)
        raise
    finally:
        end = time.perf_counter()
        span.update(ended_at=_utc(), end_offset_s=end - capture.started, duration_s=end - start)


def timed_phase(phase: str):
    """Instrument a synchronous boundary with a no-clock disabled fast path."""
    if phase not in _PHASES:
        raise ValueError("unknown execution phase")

    def decorate(function):
        @wraps(function)
        def call(*args, **kwargs):
            if _ACTIVE.get() is None:
                return function(*args, **kwargs)
            with measure_phase(phase):
                return function(*args, **kwargs)
        return call
    return decorate
