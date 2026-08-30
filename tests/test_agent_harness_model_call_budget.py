"""Public controller budget contracts; no hosted provider or paid requests."""

import pytest
from dataclasses import replace
from copy import deepcopy

from runners.agent_harness import (
    AgentAction, EpisodeContext, EpisodeController, JsonlTrajectoryRecorder,
    read_trajectory, validate_trajectory_semantics,
)
from runners.agent_harness.budget import BudgetLedger
from test_agent_harness_controller import (
    FakePublicValidator, PublicValidationEnvironment, TerminalFinalJudge,
    _controller_registry,
)


@pytest.mark.parametrize("limit", [1, 2, 5, 11])
@pytest.mark.parametrize("submit_last", [False, True])
def test_controller_admits_exactly_n_calls_and_executes_nth_action(tmp_path, limit, submit_last):
    seen, log = [], []

    class Policy:
        def act(self, observation):
            seen.append(dict(observation.payload))
            return AgentAction(
                action_id=f"call-{len(seen)}",
                tool_name="submit" if submit_last and len(seen) == limit else "public_validate",
                arguments={}, source_backend="fixture", candidate_tree_sha256="a" * 64,
            )

    path = tmp_path / "trajectory.jsonl"
    result = EpisodeController(
        policy=Policy(),
        environment=PublicValidationEnvironment(log, FakePublicValidator(log)),
        final_judge=TerminalFinalJudge(log),
        tool_registry=_controller_registry("public_validate", "submit"),
        trajectory=JsonlTrajectoryRecorder(path),
        public_validation_profile_sha256="b" * 64,
    ).run(EpisodeContext("cell", "attempt", "task", "Agentic+EVAS", limit + 2,
                         budget_limits={"model_calls": limit}))
    assert len(seen) == limit
    assert [item["model_call_budget"] for item in seen] == [
        {"limit": limit, "call_number": index, "remaining_after_this_call": limit - index}
        for index in range(1, limit + 1)
    ]
    assert log.count("step:public_validate") + log.count("step:submit") == limit
    assert log[-1] == "close"
    if submit_last:
        assert result.terminal_reason == "submitted" and result.final_judgment.score == 1.0
    else:
        assert result.primary_outcome == "budget_exhausted"
        assert result.terminal_reason == "model_call_limit"
        assert result.final_judgment is result.submission is None
        assert "final_judge" not in log and "freeze" not in log
    events = read_trajectory(path)
    assert validate_trajectory_semantics(events)
    admitted = [event for event in events if event["event_type"] == "model_call_admitted"]
    assert len(admitted) == limit
    assert events[-1]["payload"]["model_call_budget"] == {
        "limit": limit, "used_before_attempt": 0, "admitted_in_attempt": limit,
        "used_total": limit, "remaining": 0,
    }
    from runners.agent_harness.trajectory import _event_sha256
    for field in ("call_number", "remaining_after_this_call", "missing_event_type"):
        changed = deepcopy(events)
        target = next(e for e in changed if e["event_type"] == "model_call_admitted")
        if field == "missing_event_type":
            target.pop("event_type")
        else:
            target["payload"][field] += 1
        tail = None
        for event in changed:
            event.pop("event_sha256")
            event["prev_event_sha256"] = tail
            event["event_sha256"] = tail = _event_sha256(event)
        assert not validate_trajectory_semantics(changed)


@pytest.mark.parametrize("offset", [0, 2, 3])
def test_failed_calls_are_reserved_and_carried_without_refund(tmp_path, offset):
    seen, log = [], []

    class FailingPolicy:
        def act(self, observation):
            seen.append(observation.payload["model_call_budget"])
            raise ConnectionError("fixture transport failure")

    context = EpisodeContext("cell", "attempt", "task", "Agentic+EVAS", 10,
                             budget_limits={"model_calls": 3},
                             model_calls_before_attempt=offset)
    path = tmp_path / "trajectory.jsonl"
    result = EpisodeController(
        policy=FailingPolicy(),
        environment=PublicValidationEnvironment(log, FakePublicValidator(log)),
        final_judge=TerminalFinalJudge(log),
        tool_registry=_controller_registry("public_validate", "submit"),
        trajectory=JsonlTrajectoryRecorder(path),
        public_validation_profile_sha256="b" * 64,
    ).run(context)
    assert len(seen) == int(offset < 3)
    assert result.terminal_reason == ("model_call_limit" if offset == 3 else "infrastructure_failure")
    events = read_trajectory(path)
    assert validate_trajectory_semantics(events)
    assert events[-1]["payload"]["model_call_budget"]["used_total"] == min(offset + 1, 3)
    assert result.final_judgment is None
    if offset == 3:
        from runners.agent_harness.trajectory import _event_sha256
        changed = deepcopy(events)
        changed[0]["payload"]["budget_limits"]["model_calls"] = 0
        changed[0]["payload"]["model_calls_before_attempt"] = 0
        changed[-1]["payload"]["model_call_budget"] = {
            key: 0 for key in changed[-1]["payload"]["model_call_budget"]
        }
        tail = None
        for event in changed:
            event.pop("event_sha256")
            event["prev_event_sha256"] = tail
            event["event_sha256"] = tail = _event_sha256(event)
        assert not validate_trajectory_semantics(changed)
    with pytest.raises((TypeError, ValueError)):
        replace(context, model_calls_before_attempt=4)


@pytest.mark.parametrize("surface", ["context", "ledger"])
def test_core_rejects_zero_model_call_limit(surface):
    with pytest.raises(ValueError):
        if surface == "context":
            EpisodeContext("cell", "attempt", "task", "Agentic", 2, {"model_calls": 0})
        else:
            BudgetLedger({"model_calls": 0})


@pytest.mark.parametrize("invalid", [-1, True, 1.5, "2"])
def test_context_rejects_invalid_prior_call_count(invalid):
    with pytest.raises((TypeError, ValueError)):
        EpisodeContext("cell", "attempt", "task", "Agentic+EVAS", 10,
                       budget_limits={"model_calls": 3}, model_calls_before_attempt=invalid)


@pytest.mark.parametrize("expires", [False, True])
def test_call_exhaustion_never_invokes_deadline_finalizer(tmp_path, monkeypatch, expires):
    import runners.agent_harness.controller as module

    clock, log = [0.0], []
    monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])

    class Environment(PublicValidationEnvironment):
        def step(self, action, capability):
            result = super().step(action, capability)
            clock[0] = 10.0 if expires else 0.0
            return result

    class Policy:
        def act(self, observation):
            return AgentAction("first", "public_validate", {}, "fixture", "a" * 64)

    def forbidden_finalizer():
        pytest.fail("call exhaustion cannot synthesize submission via deadline")

    path = tmp_path / "trace.jsonl"
    result = EpisodeController(
        policy=Policy(), environment=Environment(log, FakePublicValidator(log)),
        final_judge=TerminalFinalJudge(log), tool_registry=_controller_registry("public_validate", "submit"),
        trajectory=JsonlTrajectoryRecorder(path), public_validation_profile_sha256="b" * 64,
        deadline_monotonic=5.0, deadline_finalizer=forbidden_finalizer,
    ).run(EpisodeContext("cell", "attempt", "task", "Agentic+EVAS", 1, {"model_calls": 1}))
    assert result.terminal_reason == "model_call_limit"
    assert result.final_judgment is None
    assert validate_trajectory_semantics(read_trajectory(path))
