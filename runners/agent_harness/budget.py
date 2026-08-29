"""Attempt-scoped hard budget accounting bound to trusted tool capabilities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .tool_registry import ToolCapability


_CAPABILITY_COSTS: dict[str, dict[str, int]] = {
    "no_budget": {},
    "tool_call": {"tool_calls": 1},
    "public_validation": {"tool_calls": 1, "public_validation_calls": 1},
    "submission": {"tool_calls": 1},
}


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

    def __init__(self, limits: Mapping[str, int]) -> None:
        self._limits = dict(limits)
        self._consumed: dict[str, int] = {}

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
