"""Opt-in mini-SWE compatibility bridges for the generic harness.

These adapters do not replace the production ``DefaultAgent`` path.  They
provide a typed comparison path whose trusted identities and candidate binding
are owned by the harness rather than copied from provider output.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol

from ..proposals import (
    ProposalEnvelope,
    ProposalNormalizationError,
    normalize_proposal,
)
from ..state import (
    AgentAction,
    EnvironmentStep,
    EpisodeContext,
    FrozenSubmission,
    Observation,
    ToolExecutionRejection,
)
from ..tool_registry import ToolCapability


MINI_SWE_BASH_HANDLER_ID = "mini_swe.execute_bash"


class LegacyBashEnvironment(Protocol):
    """The stable subset of mini-SWE's existing environment API we reuse."""

    def execute(
        self,
        action: dict[str, Any],
        cwd: str = "",
    ) -> Mapping[str, Any]: ...

    def close(self) -> None: ...


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


class MiniSweBashEnvironmentBridge:
    """Expose an existing mini-SWE Bash environment through typed contracts.

    Candidate identity and immutable freeze remain production-owned callbacks.
    This avoids inferring candidate state from optional EVAS telemetry and keeps
    the legacy ``execute(dict)`` method unchanged.
    """

    def __init__(
        self,
        *,
        legacy_environment: LegacyBashEnvironment,
        task_payload: Mapping[str, Any],
        candidate_tree_sha256: Callable[[], str],
        freeze_submission: Callable[[], FrozenSubmission],
        submitted_exception_types: tuple[type[BaseException], ...],
    ) -> None:
        if not isinstance(task_payload, Mapping):
            raise TypeError("task_payload must be a mapping")
        if not callable(candidate_tree_sha256):
            raise TypeError("candidate_tree_sha256 must be callable")
        if not callable(freeze_submission):
            raise TypeError("freeze_submission must be callable")
        if not isinstance(submitted_exception_types, tuple) or any(
            not isinstance(item, type) or not issubclass(item, BaseException)
            for item in submitted_exception_types
        ):
            raise TypeError(
                "submitted_exception_types must contain exception classes"
            )
        self._legacy_environment = legacy_environment
        self._task_payload = dict(task_payload)
        self._candidate_tree_sha256 = candidate_tree_sha256
        self._freeze_submission = freeze_submission
        self._submitted_exception_types = submitted_exception_types
        self._attempt_id: str | None = None
        self._next_observation_number = 1
        self._closed = False

    def start(self, context: EpisodeContext) -> Observation:
        if self._attempt_id is not None:
            raise RuntimeError("mini-SWE environment bridge is already started")
        if self._closed:
            raise RuntimeError("mini-SWE environment bridge is closed")
        self._attempt_id = context.attempt_id
        return Observation(
            observation_id=f"{context.attempt_id}/observation-0000",
            tool_name="task",
            status="ready",
            payload=self._task_payload,
            candidate_tree_sha256=self._candidate_tree_sha256(),
        )

    def step(
        self,
        action: AgentAction,
        capability: ToolCapability,
    ) -> EnvironmentStep | ToolExecutionRejection:
        if self._attempt_id is None:
            raise RuntimeError("mini-SWE environment bridge must be started")
        if self._closed:
            raise RuntimeError("mini-SWE environment bridge is closed")
        if (
            action.tool_name != "bash"
            or capability.tool_name != "bash"
            or capability.handler_id != MINI_SWE_BASH_HANDLER_ID
        ):
            return self._reject(
                code="unsupported_dispatch",
                message="mini-SWE compatibility bridge accepts only its bound Bash capability",
            )
        arguments = action.arguments
        if set(arguments) != {"command"} or not isinstance(
            arguments.get("command"),
            str,
        ):
            return self._reject(
                code="invalid_tool_arguments",
                message="mini-SWE Bash requires exactly one string command argument",
            )

        command = arguments["command"]
        try:
            raw_output = self._legacy_environment.execute(
                {"command": command},
                cwd="",
            )
        except BaseException as exc:
            if not isinstance(exc, self._submitted_exception_types):
                raise
            candidate_sha256 = self._candidate_tree_sha256()
            observation = self._observation(
                status="submitted",
                payload={
                    "output": "submission accepted",
                    "returncode": 0,
                    "exception_info": "",
                },
                candidate_tree_sha256=candidate_sha256,
            )
            return EnvironmentStep(
                observation=observation,
                done=True,
                terminal_reason="submitted",
            )

        if not isinstance(raw_output, Mapping):
            return self._reject(
                code="invalid_legacy_result",
                message="legacy Bash execution did not return an object",
            )
        try:
            payload = _legacy_output_payload(raw_output)
        except (TypeError, ValueError) as exc:
            return self._reject(
                code="invalid_legacy_result",
                message=str(exc),
            )
        candidate_sha256 = self._candidate_tree_sha256()
        return EnvironmentStep(
            observation=self._observation(
                status=(
                    "succeeded" if payload["returncode"] == 0 else "failed"
                ),
                payload=payload,
                candidate_tree_sha256=candidate_sha256,
                truncated=bool(payload.get("output_truncated_bytes", 0)),
            ),
            done=False,
        )

    def freeze_submission(self) -> FrozenSubmission:
        if self._attempt_id is None:
            raise RuntimeError("mini-SWE environment bridge must be started")
        return self._freeze_submission()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._legacy_environment.close()

    def _observation(
        self,
        *,
        status: str,
        payload: Mapping[str, Any],
        candidate_tree_sha256: str,
        truncated: bool = False,
    ) -> Observation:
        assert self._attempt_id is not None
        observation_number = self._next_observation_number
        self._next_observation_number += 1
        return Observation(
            observation_id=(
                f"{self._attempt_id}/observation-{observation_number:04d}"
            ),
            tool_name="bash",
            status=status,
            payload=payload,
            candidate_tree_sha256=candidate_tree_sha256,
            truncated=truncated,
        )

    def _reject(self, *, code: str, message: str) -> ToolExecutionRejection:
        return ToolExecutionRejection(
            code=code,
            failure_category="tool_contract_rejected",
            primary_outcome="protocol_failure",
            message=message,
            candidate_tree_sha256=self._candidate_tree_sha256(),
        )


def mini_swe_bash_tool_descriptor(
    *,
    allowed_conditions: Sequence[str],
) -> dict[str, Any]:
    """Return the canonical capability descriptor for the legacy Bash bridge."""
    return {
        "schema_version": "vaevas-tool-descriptor-v1",
        "tool_id": "mini-swe/bash-v1",
        "tool_name": "bash",
        "tool_version": "1",
        "lifecycle": "active",
        "model_visibility": "model_visible",
        "allowed_conditions": list(allowed_conditions),
        "budget_class": "tool_call",
        "state_effect": "candidate_mutation",
        "candidate_effect": "mutate",
        "argument_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
            "additionalProperties": False,
        },
        "observation_schema": {
            "type": "object",
            "properties": {
                "output": {"type": "string"},
                "returncode": {"type": "integer"},
                "exception_info": {"type": "string"},
            },
            "required": ["output", "returncode", "exception_info"],
            "additionalProperties": True,
        },
        "evidence_policy": {
            "records_private_evidence": False,
            "may_enter_model_observation": True,
            "may_enter_shared_memory": True,
            "requires_candidate_binding": True,
        },
        "handler_id": MINI_SWE_BASH_HANDLER_ID,
    }


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


def _legacy_output_payload(raw_output: Mapping[str, Any]) -> dict[str, Any]:
    output = raw_output.get("output", "")
    returncode = raw_output.get("returncode")
    exception_info = raw_output.get("exception_info", "")
    if not isinstance(output, str):
        raise TypeError("legacy Bash output must be a string")
    if isinstance(returncode, bool) or not isinstance(returncode, int):
        raise TypeError("legacy Bash returncode must be an integer")
    if not isinstance(exception_info, str):
        raise TypeError("legacy Bash exception_info must be a string")
    payload: dict[str, Any] = {
        "output": output,
        "returncode": returncode,
        "exception_info": exception_info,
    }
    optional_fields = (
        "elapsed_s",
        "output_total_bytes",
        "output_captured_bytes",
        "output_truncated_bytes",
        "resources",
        "public_evas",
    )
    for field_name in optional_fields:
        if field_name in raw_output:
            payload[field_name] = raw_output[field_name]
    return payload
