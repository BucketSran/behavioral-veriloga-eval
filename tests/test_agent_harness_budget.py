from __future__ import annotations

import pytest

from runners.agent_harness import (
    BudgetLedger,
    BudgetLimitExceeded,
    ToolRegistry,
)


def _capability(*, budget_class: str = "public_validation"):
    descriptor = {
        "schema_version": "vaevas-tool-descriptor-v1",
        "tool_id": "core/public-validate-v1",
        "tool_name": "public_validate",
        "tool_version": "1",
        "lifecycle": "active",
        "model_visibility": "model_visible",
        "allowed_conditions": ["Agentic+EVAS"],
        "budget_class": budget_class,
        "state_effect": "read_only",
        "candidate_effect": "read",
        "argument_schema": {"type": "object"},
        "observation_schema": {"type": "object"},
        "evidence_policy": {
            "records_private_evidence": True,
            "may_enter_model_observation": True,
            "may_enter_shared_memory": True,
            "requires_candidate_binding": True,
        },
        "handler_id": "tool.public_validate",
    }
    return ToolRegistry([descriptor]).authorize(
        "public_validate",
        condition_id="Agentic+EVAS",
        model_visible=True,
    )


@pytest.mark.parametrize(
    "limits",
    [
        {"tool_calls": -1},
        {"tool_calls": True},
        {"tool_calls": 1.5},
        {"": 1},
    ],
)
def test_budget_ledger_rejects_invalid_direct_limits(limits) -> None:
    with pytest.raises((TypeError, ValueError)):
        BudgetLedger(limits)


def test_budget_ledger_consume_enforces_limit_without_caller_preflight() -> None:
    capability = _capability()
    ledger = BudgetLedger(
        {"tool_calls": 1, "public_validation_calls": 1}
    )

    first = ledger.consume(
        capability,
        {"public_validation_calls": 1},
    )

    assert first.consumed == {
        "public_validation_calls": 1,
        "tool_calls": 1,
    }
    with pytest.raises(
        BudgetLimitExceeded,
        match="hard limit exhausted",
    ):
        ledger.consume(capability, {"public_validation_calls": 1})


def test_budget_update_is_detached_from_ledger_state() -> None:
    capability = _capability()
    ledger = BudgetLedger(
        {"tool_calls": 2, "public_validation_calls": 2}
    )

    first = ledger.consume(capability, {})
    ledger.consume(capability, {})

    assert first.consumed == {
        "public_validation_calls": 1,
        "tool_calls": 1,
    }
    assert first.remaining == {
        "public_validation_calls": 1,
        "tool_calls": 1,
    }
