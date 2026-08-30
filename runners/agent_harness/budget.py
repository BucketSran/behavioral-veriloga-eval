"""Attempt-scoped hard budget accounting bound to trusted tool capabilities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json

from .tool_registry import ToolCapability


_CAPABILITY_COSTS: dict[str, dict[str, int]] = {
    "no_budget": {},
    "tool_call": {"tool_calls": 1},
    "public_validation": {"tool_calls": 1, "public_validation_calls": 1},
    "submission": {"tool_calls": 1},
}


def validate_model_call_limit(value: int | None) -> int | None:
    if value is not None and (type(value) is not int or value <= 0):
        raise ValueError("model-call limit must be a positive integer or omitted")
    return value


def model_call_budget_text(payload: Mapping) -> str:
    """Public policy guidance; absence preserves uncapped request bytes."""
    budget = payload.get("model_call_budget")
    if budget is None:
        return ""
    return (
        "\n\nController model-call budget (logical requests, including this response): "
        + json.dumps(dict(budget), sort_keys=True)
        + "\nThis response's legal action can still execute when remaining is zero. "
        "Submit explicitly before the limit; reaching it without submission does not trigger scoring. "
        "Existing time and cost limits still apply."
    )


class BudgetContractError(ValueError):
    """The environment reported budget usage outside its resolved capability."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class BudgetLimitExceeded(RuntimeError):
    """One capability invocation would exceed an attempt-scoped hard limit."""

    def __init__(self, *, counter: str, limit: int) -> None:
        self.counter = counter
        self.limit = limit
        self.code = {
            "public_validation_calls": "public_validation_budget_exhausted",
            "tool_calls": "tool_budget_exhausted",
        }.get(counter, "budget_exhausted")
        super().__init__(f"{counter} hard limit exhausted at {limit}")


@dataclass(frozen=True, slots=True)
class BudgetUpdate:
    delta: dict[str, int]
    consumed: dict[str, int]
    remaining: dict[str, int]


class BudgetLedger:
    """Track one attempt; campaign/branch aggregation remains outside this module."""

    def __init__(self, limits: Mapping[str, int], *, model_calls_before_attempt: int = 0) -> None:
        if not isinstance(limits, Mapping):
            raise TypeError("budget limits must be a mapping")
        for counter, limit in limits.items():
            if not isinstance(counter, str) or not counter.strip():
                raise ValueError("budget counter names must be non-empty strings")
            if isinstance(limit, bool) or not isinstance(limit, int):
                raise TypeError("budget limits must be integers")
            if limit < 0:
                raise ValueError("budget limits cannot be negative")
        validate_model_call_limit(limits.get("model_calls"))
        self._limits = dict(limits)
        self._consumed: dict[str, int] = {}
        if (type(model_calls_before_attempt) is not int
                or not 0 <= model_calls_before_attempt <= limits.get("model_calls", 0)):
            raise ValueError("invalid prior model-call consumption")
        self._model_calls_before = model_calls_before_attempt
        if "model_calls" in limits:
            self._consumed["model_calls"] = model_calls_before_attempt

    def admit_model_call(self) -> dict[str, int] | None:
        """Reserve a logical policy request, including failed/invalid responses."""
        limit = self._limits.get("model_calls")
        if limit is None:
            return None
        used = self._consumed.get("model_calls", 0)
        if used >= limit:
            raise BudgetLimitExceeded(counter="model_calls", limit=limit)
        self._consumed["model_calls"] = used + 1
        return {"limit": limit, "call_number": used + 1,
                "remaining_after_this_call": limit - used - 1}

    def model_call_summary(self) -> dict[str, int] | None:
        limit = self._limits.get("model_calls")
        if limit is None:
            return None
        used = self._consumed.get("model_calls", 0)
        return {"limit": limit, "used_before_attempt": self._model_calls_before,
                "admitted_in_attempt": used - self._model_calls_before,
                "used_total": used, "remaining": limit - used}

    def ensure_available(self, capability: ToolCapability) -> None:
        for counter, amount in self._cost(capability).items():
            limit = self._limits.get(counter)
            if limit is not None and self._consumed.get(counter, 0) + amount > limit:
                raise BudgetLimitExceeded(counter=counter, limit=limit)

    def consume(
        self,
        capability: ToolCapability,
        reported_delta: Mapping[str, int],
    ) -> BudgetUpdate:
        self.ensure_available(capability)
        expected = self._cost(capability)
        for counter, amount in reported_delta.items():
            if counter not in expected:
                raise BudgetContractError(
                    "unbound_budget_delta",
                    f"{capability.tool_name} reported undeclared counter {counter}",
                )
            if amount != expected[counter]:
                raise BudgetContractError(
                    "budget_delta_mismatch",
                    f"{capability.tool_name} reported {counter}={amount}",
                )
        for counter, amount in expected.items():
            self._consumed[counter] = self._consumed.get(counter, 0) + amount
        remaining = {
            counter: limit - self._consumed.get(counter, 0)
            for counter, limit in self._limits.items()
        }
        return BudgetUpdate(
            delta=dict(expected),
            consumed=dict(sorted(self._consumed.items())),
            remaining=dict(sorted(remaining.items())),
        )

    @staticmethod
    def _cost(capability: ToolCapability) -> dict[str, int]:
        try:
            return _CAPABILITY_COSTS[capability.budget_class]
        except KeyError as exc:
            raise BudgetContractError(
                "uncallable_budget_class",
                f"cannot execute budget class {capability.budget_class}",
            ) from exc
