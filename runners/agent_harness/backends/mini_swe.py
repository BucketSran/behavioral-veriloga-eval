"""Opt-in mini-SWE compatibility bridges for the generic harness.

These adapters do not replace the production ``DefaultAgent`` path.  They
provide a typed comparison path whose trusted identities and candidate binding
are owned by the harness rather than copied from provider output.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from ..proposals import (
    ProposalEnvelope,
    ProposalNormalizationError,
    normalize_proposal,
)
from ..state import AgentAction, Observation


class MiniSwePolicyBridge:
    """Normalize one mini-SWE-style native Bash proposal per policy step."""

    def __init__(
        self,
        *,
        propose: Callable[[Observation], object],
        action_id_prefix: str,
        source_backend: str = "mini-swe",
    ) -> None:
        if not callable(propose):
            raise TypeError("propose must be callable")
        if not action_id_prefix or not action_id_prefix.strip():
            raise ValueError("action_id_prefix must be non-empty")
        if not source_backend or not source_backend.strip():
            raise ValueError("source_backend must be non-empty")
        self._propose = propose
        self._action_id_prefix = action_id_prefix
        self._source_backend = source_backend
        self._next_action_number = 1

    def act(self, observation: Observation) -> AgentAction:
        """Return one candidate-bound action from provider-native tool calls."""
        if observation.candidate_tree_sha256 is None:
            raise ValueError(
                "candidate_tree_sha256 is required for mini-SWE Bash actions"
            )
        raw_proposal = self._propose(observation)
        native_calls = _native_tool_calls(raw_proposal)
        action_id = (
            f"{self._action_id_prefix}-{self._next_action_number:04d}"
        )
        action = normalize_proposal(
            ProposalEnvelope(
                action_id=action_id,
                source_backend=self._source_backend,
                accepted_tool_names=frozenset({"bash"}),
                proposal_format="native_tool_calls",
                candidate_tree_sha256=observation.candidate_tree_sha256,
            ),
            native_calls,
        )
        self._next_action_number += 1
        return action


def _native_tool_calls(proposal: object) -> object:
    if isinstance(proposal, Mapping):
        if "tool_calls" not in proposal:
            raise ProposalNormalizationError(
                "missing_tool_calls",
                "mini-SWE assistant message does not contain tool_calls",
            )
        return proposal["tool_calls"]
    if isinstance(proposal, Sequence) and not isinstance(
        proposal,
        (str, bytes),
    ):
        return proposal
    raise ProposalNormalizationError(
        "invalid_native_transport",
        "mini-SWE proposal must be an assistant message or tool-call sequence",
    )
