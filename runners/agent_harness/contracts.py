"""Boundary protocols owned by the generic agent harness."""

from __future__ import annotations

from typing import Any, Mapping, Protocol

from .state import (
    AgentAction,
    CandidateEpisodeResult,
    CandidateSnapshot,
    EpisodeContext,
    EnvironmentStep,
    EventVisibility,
    FinalJudgment,
    FrozenSubmission,
    Observation,
    ToolExecutionRejection,
)
from .tool_registry import ToolCapability


class Policy(Protocol):
    def act(self, observation: Observation) -> AgentAction:
        """Produce the next structured action from a public observation."""


class Environment(Protocol):
    def start(self, context: EpisodeContext) -> Observation:
        """Start one clean-room attempt and return its public observation."""

    def step(
        self,
        action: AgentAction,
        capability: ToolCapability,
    ) -> EnvironmentStep | ToolExecutionRejection:
        """Apply one registry-authorized action to the owned environment."""

    def freeze_submission(self) -> FrozenSubmission:
        """Freeze and content-address the final submission."""

    def close(self) -> None:
        """Release resources owned by this attempt."""


class PublicValidator(Protocol):
    def validate(
        self,
        *,
        candidate_tree_sha256: str,
        profile_id: str,
    ) -> Observation:
        """Return model-visible feedback bound to one candidate and profile."""


class FinalJudge(Protocol):
    def judge(self, submission: FrozenSubmission) -> FinalJudgment:
        """Score an immutable frozen submission without returning an observation."""


class CandidateTerminalHandler(Protocol):
    def capture_candidate(
        self,
        *,
        context: EpisodeContext,
        expected_candidate_tree_sha256: str,
        terminal_reason: str,
    ) -> CandidateSnapshot:
        """Capture one candidate snapshot without invoking final freeze semantics."""

    def complete(
        self,
        *,
        context: EpisodeContext,
        candidate_snapshot: CandidateSnapshot,
        terminal_reason: str,
    ) -> CandidateEpisodeResult:
        """Accept one candidate snapshot without running a trusted final judge."""


class TrajectorySink(Protocol):
    @property
    def tail_sha256(self) -> str | None:
        """Return the current tamper-evident chain tail."""

    def append(
        self,
        *,
        context: EpisodeContext,
        actor: str,
        event_type: str,
        visibility: EventVisibility,
        payload: Mapping[str, Any],
    ) -> str:
        """Append one event and return its content hash."""
