"""Environment-owned control loop for one vaEVAS episode attempt."""

from __future__ import annotations

from dataclasses import replace
from collections.abc import Callable
import itertools
import math
import time

from .budget import BudgetContractError, BudgetLedger, BudgetLimitExceeded
from .contracts import Environment, FinalJudge, Policy, TrajectorySink
from .state import (
    AgentAction,
    EpisodeContext,
    EpisodeResult,
    EnvironmentStep,
    EventVisibility,
    FailureDisposition,
    Incident,
    ToolExecutionRejection,
)
from .tool_registry import ToolCapability, ToolRegistry, ToolRegistryError


class _ControllerFailure(RuntimeError):
    def __init__(
        self,
        *,
        category: str,
        phase: str,
        message: str,
        primary_outcome: str = "protocol_failure",
        terminal_reason: str = "protocol_failure",
    ) -> None:
        super().__init__(message)
        self.primary_outcome = primary_outcome
        self.terminal_reason = terminal_reason
        self.disposition = FailureDisposition(
            category=category,
            phase=phase,
            message=message,
        )


class _ProtocolFailure(_ControllerFailure):
    pass


class EpisodeController:
    """Drive one bounded episode while keeping scoring behind submission freeze."""

    def __init__(
        self,
        *,
        policy: Policy,
        environment: Environment,
        final_judge: FinalJudge,
        tool_registry: ToolRegistry,
        trajectory: TrajectorySink | None = None,
        public_validation_profile_sha256: str | None = None,
        deadline_monotonic: float | None = None,
        deadline_finalizer: Callable[[], str | None] | None = None,
    ) -> None:
        if not isinstance(tool_registry, ToolRegistry):
            raise TypeError("tool_registry must be a ToolRegistry")
        self._policy = policy
        self._environment = environment
        self._final_judge = final_judge
        self._trajectory = trajectory
        self._tool_registry = tool_registry
        if public_validation_profile_sha256 is not None and (
            not isinstance(public_validation_profile_sha256, str)
            or len(public_validation_profile_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in public_validation_profile_sha256
            )
        ):
            raise ValueError(
                "public_validation_profile_sha256 must be a lowercase SHA-256 digest"
            )
        self._public_validation_profile_sha256 = (
            public_validation_profile_sha256
        )
        if (deadline_monotonic is None) != (deadline_finalizer is None):
            raise ValueError("deadline and trusted finalizer must be supplied together")
        if deadline_monotonic is not None and (
            not math.isfinite(deadline_monotonic) or not callable(deadline_finalizer)
        ):
            raise ValueError("deadline must be finite and finalizer callable")
        self._deadline = deadline_monotonic
        self._deadline_finalizer = deadline_finalizer

    def _record(
        self,
        context: EpisodeContext,
        *,
        actor: str,
        event_type: str,
        visibility: EventVisibility,
        payload: dict,
    ) -> None:
        if self._trajectory is None:
            return
        self._trajectory.append(
            context=context,
            actor=actor,
            event_type=event_type,
            visibility=visibility,
            payload=payload,
        )

    def _enforce_candidate_effect(
        self,
        context: EpisodeContext,
        *,
        action: AgentAction,
        capability: ToolCapability,
        before_sha256: str | None,
        step: EnvironmentStep,
    ) -> None:
        after_sha256 = step.observation.candidate_tree_sha256
        violation_message: str | None = None
        if (
            capability.candidate_effect in {"none", "read"}
            and after_sha256 != before_sha256
        ):
            violation_message = (
                f"{capability.candidate_effect} tool changed the trusted "
                "candidate tree"
            )
        elif capability.candidate_effect == "mutate" and after_sha256 is None:
            violation_message = "mutate tool did not report a candidate tree hash"
        elif capability.candidate_effect == "freeze" and (
            not step.done or step.terminal_reason != "submitted"
        ):
            violation_message = (
                "freeze tool must terminate the environment as submitted"
            )
        elif capability.candidate_effect == "freeze" and after_sha256 is None:
            violation_message = "freeze tool did not report a candidate tree hash"
        if violation_message is not None:
            self._record(
                context,
                actor="controller",
                event_type="candidate_transition_rejected",
                visibility="harness",
                payload={
                    "action_id": action.action_id,
                    "tool_name": capability.tool_name,
                    "tool_id": capability.tool_id,
                    "candidate_effect": capability.candidate_effect,
                    "candidate_tree_sha256_before": before_sha256,
                    "candidate_tree_sha256_after": after_sha256,
                    "descriptor_sha256": capability.descriptor_sha256,
                },
            )
            raise _ProtocolFailure(
                category="candidate_effect_violation",
                phase="environment_step",
                message=violation_message,
            )

    def run(self, context: EpisodeContext) -> EpisodeResult:
        result: EpisodeResult | None = None
        submission = None
        budget_ledger = BudgetLedger(context.budget_limits)
        phase = "tool_authority_resolution"

        def score_submission(expected_sha256, terminal_reason, capability=None):
            nonlocal phase, submission
            phase = "submission_freeze"
            frozen_submission = self._environment.freeze_submission()
            if (
                frozen_submission.tree_sha256
                != expected_sha256
            ):
                self._record(
                    context,
                    actor="controller",
                    event_type="submission_freeze_rejected",
                    visibility="harness",
                    payload={
                        "tool_name": capability.tool_name if capability else None,
                        "tool_id": capability.tool_id if capability else None,
                        "candidate_tree_sha256": (
                            expected_sha256
                        ),
                        "submission_tree_sha256": (
                            frozen_submission.tree_sha256
                        ),
                    },
                )
                raise _ProtocolFailure(
                    category="submission_freeze_mismatch",
                    phase="submission_freeze",
                    message=(
                        "frozen submission does not match the terminal "
                        "candidate observation"
                    ),
                )
            submission = frozen_submission
            self._record(
                context,
                actor="environment",
                event_type="submission_frozen",
                visibility="harness",
                payload={
                    "tree_sha256": submission.tree_sha256,
                    "artifacts": list(submission.artifacts),
                },
            )
            phase = "final_judge"
            final_judgment = self._final_judge.judge(submission)
            if final_judgment.submission_tree_sha256 != submission.tree_sha256:
                raise _ProtocolFailure(
                    category="final_judgment_submission_mismatch",
                    phase="final_judge",
                    message=(
                        "final judgment is not bound to the frozen submission"
                    ),
                )
            self._record(
                context,
                actor="final_judge",
                event_type="final_judgment_completed",
                visibility="trusted",
                payload={
                    "status": final_judgment.status,
                    "judge_engine": final_judgment.judge_engine,
                    "score": final_judgment.score,
                    "submission_tree_sha256": (
                        final_judgment.submission_tree_sha256
                    ),
                },
            )
            return EpisodeResult(
                context=context,
                primary_outcome=final_judgment.status,
                terminal_reason=terminal_reason,
                submission=submission,
                final_judgment=final_judgment,
                incidents=(),
            )

        def deadline_expired():
            return self._deadline is not None and time.monotonic() >= self._deadline

        def finalize_deadline():
            nonlocal phase
            phase = "deadline_finalization"
            self._record(
                context, actor="controller", event_type="deadline_reached",
                visibility="harness", payload={"terminal_reason": "agent_timeout"},
            )
            # Trusted runtime quiesces writers and gates the current tree.
            # None means incomplete; no model action or ordinary tool is invented.
            candidate = self._deadline_finalizer()
            if candidate is None:
                raise _ControllerFailure(
                    category="deadline_without_submission", phase=phase,
                    message="deadline reached without a complete declared submission",
                    primary_outcome="agent_timeout", terminal_reason="agent_timeout",
                )
            return score_submission(candidate, "agent_timeout")

        try:
            if context.max_steps is None and self._deadline is None:
                raise ValueError("unlimited steps require a trusted deadline")
            effective_toolset = self._tool_registry.resolve(
                condition_id=context.condition,
                model_visible=True,
            )
            self._record(
                context,
                actor="controller",
                event_type="episode_started",
                visibility="harness",
                payload={
                    "max_steps": context.max_steps,
                    "budget_limits": dict(context.budget_limits),
                    "effective_capability_sha256": (
                        effective_toolset.effective_capability_sha256
                    ),
                    "attempt_lineage": {
                        "parent_attempt_id": context.parent_attempt_id,
                        "retry_index": context.retry_index,
                        "retry_reason": context.retry_reason,
                    },
                },
            )
            phase = "environment_start"
            observation = self._environment.start(context)
            steps = range(context.max_steps) if context.max_steps is not None else itertools.count()
            for _ in steps:
                if deadline_expired():
                    result = finalize_deadline()
                    break
                phase = "policy_action"
                try:
                    action = self._policy.act(observation)
                except Exception as exc:
                    if not deadline_expired():
                        raise
                    self._record(
                        context, actor="policy", event_type="deadline_interruption",
                        visibility="harness", payload={"error_type": type(exc).__name__},
                    )
                    result = finalize_deadline()
                    break
                if deadline_expired():
                    result = finalize_deadline()
                    break
                self._record(
                    context,
                    actor="policy",
                    event_type="action_proposed",
                    visibility="model",
                    payload={
                        "schema_version": action.schema_version,
                        "action_id": action.action_id,
                        "tool_name": action.tool_name,
                        "arguments_sha256": action.arguments_sha256,
                        "source_backend": action.source_backend,
                        "candidate_tree_sha256": action.candidate_tree_sha256,
                    },
                )
                phase = "tool_authorization"
                try:
                    capability = self._tool_registry.authorize(
                        action.tool_name,
                        condition_id=context.condition,
                        model_visible=True,
                    )
                except ToolRegistryError as exc:
                    self._record(
                        context,
                        actor="controller",
                        event_type="action_rejected",
                        visibility="harness",
                        payload={
                            "action_id": action.action_id,
                            "tool_name": action.tool_name,
                            "candidate_tree_sha256": (
                                action.candidate_tree_sha256
                            ),
                            "candidate_tree_sha256_before": (
                                observation.candidate_tree_sha256
                            ),
                            "candidate_tree_sha256_after": (
                                observation.candidate_tree_sha256
                            ),
                            "source_backend": action.source_backend,
                            "rejection_code": exc.code,
                            "condition": context.condition,
                            "registry_sha256": (
                                self._tool_registry.registry_sha256
                            ),
                            "effective_capability_sha256": (
                                effective_toolset.effective_capability_sha256
                            ),
                        },
                    )
                    raise _ProtocolFailure(
                        category="tool_authorization_rejected",
                        phase="tool_authorization",
                        message=str(exc),
                    ) from exc
                if capability.evidence_policy["requires_candidate_binding"]:
                    expected_candidate_sha256 = (
                        observation.candidate_tree_sha256
                    )
                    if expected_candidate_sha256 is None:
                        rejection_code = "candidate_binding_unavailable"
                    elif action.candidate_tree_sha256 is None:
                        rejection_code = "missing_candidate_binding"
                    elif action.candidate_tree_sha256 != expected_candidate_sha256:
                        rejection_code = "candidate_binding_mismatch"
                    else:
                        rejection_code = None
                    if rejection_code is not None:
                        self._record(
                            context,
                            actor="controller",
                            event_type="action_rejected",
                            visibility="harness",
                            payload={
                                "action_id": action.action_id,
                                "tool_name": action.tool_name,
                                "tool_id": capability.tool_id,
                                "candidate_tree_sha256": (
                                    action.candidate_tree_sha256
                                ),
                                "expected_candidate_tree_sha256": (
                                    expected_candidate_sha256
                                ),
                                "rejection_code": rejection_code,
                                "condition": context.condition,
                                "effective_capability_sha256": (
                                    effective_toolset.effective_capability_sha256
                                ),
                            },
                        )
                        raise _ProtocolFailure(
                            category="tool_contract_rejected",
                            phase="tool_authorization",
                            message=(
                                f"{rejection_code}: action candidate binding "
                                "does not match the current environment state"
                            ),
                        )
                try:
                    budget_ledger.ensure_available(capability)
                except BudgetLimitExceeded as exc:
                    self._record(
                        context,
                        actor="controller",
                        event_type="action_rejected",
                        visibility="harness",
                        payload={
                            "action_id": action.action_id,
                            "tool_name": capability.tool_name,
                            "tool_id": capability.tool_id,
                            "rejection_code": exc.code,
                            "budget_counter": exc.counter,
                            "budget_limit": exc.limit,
                            "candidate_tree_sha256": (
                                observation.candidate_tree_sha256
                            ),
                        },
                    )
                    raise _ControllerFailure(
                        category=exc.code,
                        phase="controller_budget",
                        message=str(exc),
                        primary_outcome="budget_exhausted",
                        terminal_reason="hard_budget_exhausted",
                    ) from exc
                if (
                    capability.budget_class == "public_validation"
                    and self._public_validation_profile_sha256 is None
                ):
                    self._record(
                        context,
                        actor="controller",
                        event_type="action_rejected",
                        visibility="harness",
                        payload={
                            "action_id": action.action_id,
                            "tool_name": capability.tool_name,
                            "tool_id": capability.tool_id,
                            "rejection_code": "public_validation_profile_unbound",
                            "candidate_tree_sha256": (
                                observation.candidate_tree_sha256
                            ),
                        },
                    )
                    raise _ProtocolFailure(
                        category="public_validation_profile_unbound",
                        phase="public_validation_authority",
                        message=(
                            "public validation requires a campaign-bound "
                            "authority profile"
                        ),
                    )
                self._record(
                    context,
                    actor="controller",
                    event_type="action_authorized",
                    visibility="harness",
                    payload={
                        "action_id": action.action_id,
                        "tool_name": capability.tool_name,
                        "tool_id": capability.tool_id,
                        "tool_version": capability.tool_version,
                        "handler_id": capability.handler_id,
                        "descriptor_sha256": capability.descriptor_sha256,
                        "candidate_tree_sha256": action.candidate_tree_sha256,
                        "condition": context.condition,
                        "effective_capability_sha256": (
                            effective_toolset.effective_capability_sha256
                        ),
                    },
                )
                if deadline_expired():
                    self._record(
                        context, actor="controller", event_type="action_rejected",
                        visibility="harness", payload={
                            "action_id": action.action_id,
                            "tool_name": capability.tool_name,
                            "tool_id": capability.tool_id,
                            "rejection_code": "deadline_expired",
                            "candidate_tree_sha256": observation.candidate_tree_sha256,
                        },
                    )
                    result = finalize_deadline()
                    break
                phase = "environment_step"
                step = self._environment.step(action, capability)
                if isinstance(step, ToolExecutionRejection):
                    self._record(
                        context,
                        actor="environment",
                        event_type="action_rejected",
                        visibility="harness",
                        payload={
                            "action_id": action.action_id,
                            "tool_name": capability.tool_name,
                            "tool_id": capability.tool_id,
                            "rejection_code": step.code,
                            "source_backend": action.source_backend,
                            "candidate_tree_sha256_before": (
                                observation.candidate_tree_sha256
                            ),
                            "candidate_tree_sha256_after": (
                                step.candidate_tree_sha256
                            ),
                            "registry_sha256": (
                                self._tool_registry.registry_sha256
                            ),
                            "effective_capability_sha256": (
                                effective_toolset.effective_capability_sha256
                            ),
                        },
                    )
                    raise _ControllerFailure(
                        category=step.failure_category,
                        phase="tool_execution",
                        message=step.message,
                        primary_outcome=step.primary_outcome,
                        terminal_reason="tool_execution_rejected",
                    )
                self._enforce_candidate_effect(
                    context,
                    action=action,
                    capability=capability,
                    before_sha256=observation.candidate_tree_sha256,
                    step=step,
                )
                if capability.budget_class == "public_validation" and (
                    step.observation.validation_profile_sha256
                    != self._public_validation_profile_sha256
                ):
                    self._record(
                        context,
                        actor="controller",
                        event_type="public_validation_rejected",
                        visibility="harness",
                        payload={
                            "action_id": action.action_id,
                            "tool_name": capability.tool_name,
                            "tool_id": capability.tool_id,
                            "candidate_tree_sha256": (
                                step.observation.candidate_tree_sha256
                            ),
                            "expected_validation_profile_sha256": (
                                self._public_validation_profile_sha256
                            ),
                            "observed_validation_profile_sha256": (
                                step.observation.validation_profile_sha256
                            ),
                        },
                    )
                    raise _ProtocolFailure(
                        category="public_validation_profile_mismatch",
                        phase="public_validation_authority",
                        message=(
                            "public validation observation does not match "
                            "the campaign-bound authority profile"
                        ),
                    )
                try:
                    budget_update = budget_ledger.consume(
                        capability,
                        step.observation.budget_delta,
                    )
                except BudgetContractError as exc:
                    raise _ProtocolFailure(
                        category="budget_contract_violation",
                        phase="environment_step",
                        message=str(exc),
                    ) from exc
                self._record(
                    context,
                    actor="controller",
                    event_type="budget_updated",
                    visibility="harness",
                    payload={
                        "action_id": action.action_id,
                        "tool_name": capability.tool_name,
                        "budget_class": capability.budget_class,
                        "delta": budget_update.delta,
                        "consumed": budget_update.consumed,
                        "remaining": budget_update.remaining,
                    },
                )
                self._record(
                    context,
                    actor="environment",
                    event_type="environment_observed",
                    visibility="model",
                    payload={
                        "action_id": action.action_id,
                        "schema_version": step.observation.schema_version,
                        "observation_id": step.observation.observation_id,
                        "tool_name": step.observation.tool_name,
                        "status": step.observation.status,
                        "payload_sha256": step.observation.payload_sha256,
                        "truncated": step.observation.truncated,
                        "candidate_tree_sha256": (
                            step.observation.candidate_tree_sha256
                        ),
                        "validation_profile_sha256": (
                            step.observation.validation_profile_sha256
                        ),
                        "budget_delta": dict(step.observation.budget_delta),
                        "done": step.done,
                        "terminal_reason": step.terminal_reason,
                    },
                )
                observation = step.observation
                if deadline_expired():
                    result = finalize_deadline()
                    break
                if not step.done:
                    continue

                terminal_reason = step.terminal_reason or "environment_done"
                if terminal_reason != "submitted":
                    raise _ProtocolFailure(
                        category="invalid_terminal_reason",
                        phase="environment_step",
                        message=f"unsupported terminal reason: {terminal_reason}",
                    )

                result = score_submission(
                    observation.candidate_tree_sha256, terminal_reason, capability,
                )
                break
            if result is None:
                failure = FailureDisposition(
                    category="step_budget_exhausted",
                    phase="controller_budget",
                    message="episode exhausted max_steps without a terminal result",
                )
                result = EpisodeResult(
                    context=context,
                    primary_outcome="budget_exhausted",
                    terminal_reason="max_steps_exhausted",
                    submission=None,
                    final_judgment=None,
                    incidents=(),
                    failure=failure,
                )
                self._record(
                    context,
                    actor="controller",
                    event_type="episode_failed",
                    visibility="harness",
                    payload={
                        "primary_outcome": result.primary_outcome,
                        "category": failure.category,
                        "phase": failure.phase,
                        "message": failure.message,
                    },
                )
        except _ControllerFailure as exc:
            result = EpisodeResult(
                context=context,
                primary_outcome=exc.primary_outcome,
                terminal_reason=exc.terminal_reason,
                submission=submission,
                final_judgment=None,
                incidents=(),
                failure=exc.disposition,
            )
            self._record(
                context,
                actor="controller",
                event_type="episode_failed",
                visibility="harness",
                payload={
                    "primary_outcome": result.primary_outcome,
                    "category": exc.disposition.category,
                    "phase": exc.disposition.phase,
                    "message": exc.disposition.message,
                },
            )
        except Exception as exc:
            category_by_phase = {
                "policy_action": "backend_failure",
                "final_judge": "final_judge_failure",
            }
            failure = FailureDisposition(
                category=category_by_phase.get(phase, "environment_failure"),
                phase=phase,
                message=str(exc),
            )
            result = EpisodeResult(
                context=context,
                primary_outcome="infrastructure_failure",
                terminal_reason="infrastructure_failure",
                submission=submission,
                final_judgment=None,
                incidents=(),
                failure=failure,
            )
            self._record(
                context,
                actor="controller",
                event_type="episode_failed",
                visibility="harness",
                payload={
                    "primary_outcome": result.primary_outcome,
                    "category": failure.category,
                    "phase": failure.phase,
                    "message": failure.message,
                },
            )

        cleanup_incident: Incident | None = None
        try:
            self._environment.close()
        except Exception as exc:
            cleanup_incident = Incident(
                category="sandbox_cleanup_failure",
                message=str(exc),
            )
            self._record(
                context,
                actor="environment",
                event_type="cleanup_failed",
                visibility="harness",
                payload={
                    "category": cleanup_incident.category,
                    "message": cleanup_incident.message,
                },
            )
        else:
            self._record(
                context,
                actor="environment",
                event_type="cleanup_completed",
                visibility="harness",
                payload={},
            )

        assert result is not None
        if cleanup_incident is not None:
            result = replace(result, incidents=(cleanup_incident,))
        self._record(
            context,
            actor="controller",
            event_type="episode_completed",
            visibility="harness",
            payload={
                "primary_outcome": result.primary_outcome,
                "terminal_reason": result.terminal_reason,
                "incidents": [incident.category for incident in result.incidents],
            },
        )
        if self._trajectory is not None:
            result = replace(
                result,
                trajectory_tail_sha256=self._trajectory.tail_sha256,
            )
        return result
