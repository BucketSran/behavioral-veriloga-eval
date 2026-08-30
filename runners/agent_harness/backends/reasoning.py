"""Episode-local reasoning policy for the generic vaEVAS harness."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
import time
from typing import Any, Protocol

from ..proposals import (
    ProposalEnvelope,
    ProposalFormat,
    ProposalNormalizationError,
    normalize_proposal,
)
from ..state import AgentAction, EpisodeContext, Observation


DEFAULT_REASONING_SYSTEM_PROMPT = (
    "You are a vaEVAS reasoning backend. Use only the public observation "
    "provided in this episode and choose exactly one allowed action. Do not "
    "invent trusted harness metadata."
)


class ReasoningClient(Protocol):
    """Local/API-compatible chat client boundary used by the policy."""

    def complete(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        tools: list[dict[str, Any]],
        *,
        timeout_s: float | None = None,
    ) -> Mapping[str, Any]: ...


@dataclass(frozen=True, slots=True)
class _PendingNativeToolResult:
    assistant_message: dict[str, Any]
    tool_call_id: str


class ReasoningPolicy:
    """Convert one reasoning-model response into one trusted harness action.

    The policy owns only provider-message assembly and safe telemetry. The
    controller still owns budgets, environment dispatch, freeze, and judging.
    """

    def __init__(
        self,
        *,
        client: ReasoningClient,
        context: EpisodeContext,
        proposal_format: ProposalFormat,
        tools: Sequence[Mapping[str, Any]],
        accepted_tool_names: frozenset[str],
        max_tokens: int,
        timeout_s: float | None = None,
        deadline_monotonic: float | None = None,
        source_backend: str = "alphaapollo/reasoning-v1",
        system_prompt: str = DEFAULT_REASONING_SYSTEM_PROMPT,
    ) -> None:
        if proposal_format not in {"native_tool_calls", "strict_json"}:
            raise ValueError(f"unsupported proposal_format: {proposal_format}")
        if not isinstance(accepted_tool_names, frozenset):
            raise TypeError("accepted_tool_names must be a frozenset")
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int):
            raise TypeError("max_tokens must be a positive integer")
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        timeout_s = _validate_timeout_s(timeout_s)
        deadline_monotonic = _validate_deadline_monotonic(deadline_monotonic)
        if not source_backend.strip():
            raise ValueError("source_backend must be non-empty")
        if not system_prompt.strip():
            raise ValueError("system_prompt must be non-empty")
        system_prompt = _effective_system_prompt(
            base_prompt=system_prompt,
            proposal_format=proposal_format,
            tools=tools,
            accepted_tool_names=accepted_tool_names,
        )
        self.client = client
        self.context = context
        self.proposal_format = proposal_format
        self.tools = [deepcopy(dict(tool)) for tool in tools]
        self.accepted_tool_names = accepted_tool_names
        self.max_tokens = max_tokens
        self.timeout_s = timeout_s
        self.deadline_monotonic = deadline_monotonic
        self.source_backend = source_backend
        self.system_prompt = system_prompt
        self._messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt}
        ]
        self._next_action_number = 1
        self._pending_native_tool_result: _PendingNativeToolResult | None = None
        self._seen_provider_call_ids: set[str] = set()
        self._calls: list[dict[str, Any]] = []

    def act(self, observation: Observation) -> AgentAction:
        """Return exactly one candidate-bound action for one public observation."""
        if observation.candidate_tree_sha256 is None:
            raise ValueError("candidate_tree_sha256 is required for reasoning actions")
        action_id = f"{self.context.attempt_id}-{self._next_action_number:04d}"
        messages = self._request_messages(observation)
        tools = self._request_tools()
        request_timeout_s = self._request_timeout_s()
        response = self.client.complete(
            deepcopy(messages),
            self.max_tokens,
            deepcopy(tools),
            timeout_s=request_timeout_s,
        )
        message, finish_reason = _response_message(response)
        proposal = self._proposal_from_message(message)
        provider_call_id = self._fresh_provider_call_id(proposal)
        action = normalize_proposal(
            ProposalEnvelope(
                action_id=action_id,
                source_backend=self.source_backend,
                accepted_tool_names=self.accepted_tool_names,
                proposal_format=self.proposal_format,
                candidate_tree_sha256=observation.candidate_tree_sha256,
            ),
            proposal,
        )
        if provider_call_id is not None:
            self._seen_provider_call_ids.add(provider_call_id)
        self._messages = messages
        self._append_assistant_message(message, provider_call_id=provider_call_id)
        self._record_call(
            response=response,
            action_id=action_id,
            finish_reason=finish_reason,
            request_messages=messages,
            request_tools=tools,
            request_timeout_s=request_timeout_s,
        )
        self._next_action_number += 1
        return action

    def serialize(self) -> dict[str, Any]:
        """Return provider metadata safe to join into private evidence."""
        return {
            "info": {
                "schema_version": "vaevas-reasoning-policy-telemetry-v1",
                "backend": self.source_backend,
                "model": _optional_string(getattr(self.client, "model", None)),
                "episode_id": self.context.episode_id,
                "attempt_id": self.context.attempt_id,
                "proposal_format": self.proposal_format,
                "call_count": len(self._calls),
                "calls": deepcopy(self._calls),
            }
        }

    def _request_messages(self, observation: Observation) -> list[dict[str, Any]]:
        content = _request_content(self.context, observation)
        if self.proposal_format == "strict_json":
            messages = deepcopy(self._messages)
            messages.append({"role": "user", "content": content})
            return messages
        messages = deepcopy(self._messages)
        if self._pending_native_tool_result is not None:
            pending = self._pending_native_tool_result
            messages.append(deepcopy(pending.assistant_message))
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": pending.tool_call_id,
                    "content": content,
                }
            )
            self._pending_native_tool_result = None
            return messages
        messages.append({"role": "user", "content": content})
        return messages

    def _request_tools(self) -> list[dict[str, Any]]:
        if self.proposal_format == "strict_json":
            return []
        return deepcopy(self.tools)

    def _proposal_from_message(self, message: Mapping[str, Any]) -> object:
        if self.proposal_format == "strict_json":
            content = message.get("content")
            if not isinstance(content, str):
                raise ProposalNormalizationError(
                    "missing_content",
                    "strict JSON reasoning response requires string content",
                )
            return content
        if "tool_calls" not in message:
            raise ProposalNormalizationError(
                "missing_tool_calls",
                "native reasoning response does not contain tool_calls",
            )
        return message["tool_calls"]

    def _fresh_provider_call_id(self, proposal: object) -> str | None:
        if self.proposal_format != "native_tool_calls":
            return None
        provider_call_id = _native_provider_call_id(proposal)
        if provider_call_id in self._seen_provider_call_ids:
            raise ProposalNormalizationError(
                "duplicate_provider_call_id",
                "native reasoning provider call ids must be unique within an episode",
            )
        return provider_call_id

    def _append_assistant_message(
        self,
        message: Mapping[str, Any],
        *,
        provider_call_id: str | None,
    ) -> None:
        if self.proposal_format == "strict_json":
            self._messages.append(_safe_assistant_message(message))
            return
        if provider_call_id is None:
            return
        assistant = _safe_assistant_message(message)
        self._pending_native_tool_result = _PendingNativeToolResult(
            assistant_message=assistant,
            tool_call_id=provider_call_id,
        )

    def _record_call(
        self,
        *,
        response: Mapping[str, Any],
        action_id: str,
        finish_reason: object,
        request_messages: list[dict[str, Any]],
        request_tools: list[dict[str, Any]],
        request_timeout_s: float | None,
    ) -> None:
        call_number = len(self._calls) + 1
        message, _ = _response_message(response)
        self._calls.append(
            {
                "request_id": f"{self.context.attempt_id}/request-{call_number:04d}",
                "action_id": action_id,
                "proposal_format": self.proposal_format,
                "requested_max_tokens": self.max_tokens,
                "timeout_s": request_timeout_s,
                "configured_timeout_s": self.timeout_s,
                "deadline_monotonic": self.deadline_monotonic,
                "request_message_count": len(request_messages),
                "request_tools_count": len(request_tools),
                "response_id": _optional_string(response.get("id")),
                "response_model": _optional_string(response.get("model")),
                "finish_reason": _optional_string(finish_reason),
                "message_content_sha256": _optional_sha256_text(message.get("content")),
                "tool_calls_sha256": _optional_sha256_json(message.get("tool_calls")),
                "usage": _usage_summary(response.get("usage")),
            }
        )

    def _request_timeout_s(self) -> float | None:
        if self.deadline_monotonic is None:
            return self.timeout_s
        remaining_s = self.deadline_monotonic - time.monotonic()
        if remaining_s <= 0:
            raise TimeoutError("reasoning policy deadline expired before model call")
        if self.timeout_s is None:
            return remaining_s
        return min(self.timeout_s, remaining_s)


def _response_message(response: Mapping[str, Any]) -> tuple[Mapping[str, Any], object]:
    choices = response.get("choices")
    if not isinstance(choices, Sequence) or isinstance(choices, (str, bytes)) or len(choices) != 1:
        raise ProposalNormalizationError(
            "invalid_response_choices",
            "reasoning response must contain exactly one choice",
        )
    choice = choices[0]
    if not isinstance(choice, Mapping):
        raise ProposalNormalizationError("invalid_response_choice", "choice must be an object")
    message = choice.get("message")
    if not isinstance(message, Mapping):
        raise ProposalNormalizationError(
            "invalid_response_message",
            "choice message must be an object",
        )
    return message, choice.get("finish_reason")


def _native_provider_call_id(proposal: object) -> str:
    if not isinstance(proposal, Sequence) or isinstance(proposal, (str, bytes)):
        raise ProposalNormalizationError(
            "invalid_native_transport",
            "native reasoning proposal must be a tool-call sequence",
        )
    if len(proposal) != 1:
        raise ProposalNormalizationError(
            "action_count",
            "native reasoning proposal must contain exactly one call",
        )
    call = proposal[0]
    if not isinstance(call, Mapping):
        raise ProposalNormalizationError(
            "invalid_call_shape",
            "native reasoning tool call must be an object",
        )
    if "id" not in call:
        raise ProposalNormalizationError(
            "missing_provider_call_id",
            "native reasoning tool call must include a provider call id",
        )
    call_id = call["id"]
    if not isinstance(call_id, str) or not call_id.strip():
        raise ProposalNormalizationError(
            "invalid_provider_call_id",
            "native reasoning provider call id must be a non-empty string",
        )
    return call_id


def _safe_assistant_message(message: Mapping[str, Any]) -> dict[str, Any]:
    assistant: dict[str, Any] = {"role": "assistant"}
    content = message.get("content")
    if isinstance(content, str):
        assistant["content"] = content
    tool_calls = message.get("tool_calls")
    if isinstance(tool_calls, Sequence) and not isinstance(tool_calls, (str, bytes)):
        assistant["tool_calls"] = deepcopy(list(tool_calls))
    return assistant


def _request_content(context: EpisodeContext, observation: Observation) -> str:
    return json.dumps(
        {
            "schema_version": "vaevas-reasoning-request-v1",
            "context": {
                "episode_id": context.episode_id,
                "attempt_id": context.attempt_id,
                "task_id": context.task_id,
                "condition": context.condition,
            },
            "observation": observation.to_document(),
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _validate_timeout_s(timeout_s: float | None) -> float | None:
    if timeout_s is None:
        return None
    if isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float)):
        raise TypeError("timeout_s must be a finite positive number or None")
    if not math.isfinite(timeout_s):
        raise ValueError("timeout_s must be finite")
    if timeout_s <= 0:
        raise ValueError("timeout_s must be positive")
    return float(timeout_s)


def _validate_deadline_monotonic(deadline_monotonic: float | None) -> float | None:
    if deadline_monotonic is None:
        return None
    if isinstance(deadline_monotonic, bool) or not isinstance(deadline_monotonic, (int, float)):
        raise TypeError("deadline_monotonic must be a finite number or None")
    if not math.isfinite(deadline_monotonic):
        raise ValueError("deadline_monotonic must be finite")
    return float(deadline_monotonic)


def _effective_system_prompt(
    *,
    base_prompt: str,
    proposal_format: ProposalFormat,
    tools: Sequence[Mapping[str, Any]],
    accepted_tool_names: frozenset[str],
) -> str:
    if proposal_format != "strict_json":
        return base_prompt
    contract = {
        "strict_json_output": {
            "description": (
                "Return exactly one standalone JSON object accepted by the "
                "vaevas proposal normalizer. Do not wrap it in Markdown."
            ),
            "required_shape": {
                "tool_name": "<one allowed tool name>",
                "arguments": {},
            },
            "required_fields": ["tool_name", "arguments"],
            "additionalProperties": False,
            "allowed_tool_names": sorted(accepted_tool_names),
            "allowed_tool_schemas": [deepcopy(dict(tool)) for tool in tools],
        }
    }
    return base_prompt + "\n\nStrict JSON proposal contract:\n" + json.dumps(
        contract,
        ensure_ascii=False,
        sort_keys=True,
    )


def _usage_summary(usage: object) -> dict[str, Any]:
    empty = {
        "input_tokens": None,
        "output_tokens": None,
        "reasoning_tokens": None,
        "source": "missing",
    }
    if not isinstance(usage, Mapping):
        return empty
    return {
        "input_tokens": _usage_token(usage, "input_tokens", "prompt_tokens"),
        "output_tokens": _usage_token(usage, "output_tokens", "completion_tokens"),
        "reasoning_tokens": _reasoning_tokens(usage),
        "source": "provider",
    }


def _reasoning_tokens(usage: Mapping[str, Any]) -> int | None:
    if "reasoning_tokens" in usage:
        return _token_value(usage["reasoning_tokens"], field_name="reasoning_tokens")
    if "completion_tokens_details" in usage:
        details = usage.get("completion_tokens_details")
        if isinstance(details, Mapping):
            if "reasoning_tokens" in details:
                return _token_value(
                    details["reasoning_tokens"],
                    field_name="completion_tokens_details.reasoning_tokens",
                )
    return None


def _usage_token(usage: Mapping[str, Any], primary: str, fallback: str) -> int | None:
    if primary in usage:
        return _token_value(usage[primary], field_name=primary)
    if fallback in usage:
        return _token_value(usage[fallback], field_name=fallback)
    return None


def _token_value(value: object, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ProposalNormalizationError(
            "invalid_provider_usage",
            f"provider usage field {field_name} must be a non-negative integer or null",
        )
    return value


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _optional_sha256_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _optional_sha256_json(value: object) -> str | None:
    if value is None:
        return None
    try:
        canonical = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError):
        return None
    return hashlib.sha256(canonical).hexdigest()
