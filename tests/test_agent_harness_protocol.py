from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path

import jsonschema
import pytest

from runners.agent_harness import AgentAction, Observation


ROOT = Path(__file__).resolve().parents[1]
ACTION_SCHEMA_PATH = ROOT / "schemas" / "vaevas-action-v1.schema.json"
OBSERVATION_SCHEMA_PATH = ROOT / "schemas" / "vaevas-observation-v1.schema.json"


def _load_schema(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_action_and_observation_expose_detached_canonical_documents() -> None:
    candidate_sha256 = "a" * 64
    action = AgentAction(
        action_id="action-1",
        tool_name="bash",
        arguments={"argv": ["printf", "ok"]},
        source_backend="mini-swe",
        candidate_tree_sha256=candidate_sha256,
    )
    observation = Observation(
        observation_id="observation-1",
        tool_name="bash",
        status="completed",
        payload={"stdout": "ok", "exit_code": 0},
        candidate_tree_sha256=candidate_sha256,
        budget_delta={"tool_calls": 1},
    )

    action_document = action.to_document()
    observation_document = observation.to_document()

    assert action_document == {
        "schema_version": "vaevas-action-v1",
        "action_id": "action-1",
        "tool_name": "bash",
        "arguments": {"argv": ["printf", "ok"]},
        "arguments_sha256": action.arguments_sha256,
        "source_backend": "mini-swe",
        "candidate_tree_sha256": candidate_sha256,
    }
    assert observation_document == {
        "schema_version": "vaevas-observation-v1",
        "observation_id": "observation-1",
        "tool_name": "bash",
        "status": "completed",
        "payload": {"stdout": "ok", "exit_code": 0},
        "payload_sha256": observation.payload_sha256,
        "candidate_tree_sha256": candidate_sha256,
        "truncated": False,
        "budget_delta": {"tool_calls": 1},
    }

    action_document["arguments"]["argv"].append("mutated")
    observation_document["payload"]["stdout"] = "mutated"

    assert action.to_document()["arguments"] == {"argv": ["printf", "ok"]}
    assert observation.to_document()["payload"] == {
        "stdout": "ok",
        "exit_code": 0,
    }


def test_canonical_action_and_observation_documents_follow_strict_schemas() -> None:
    action = AgentAction(
        action_id="action-domain-placeholder",
        tool_name="domain.future_placeholder",
        arguments={"query": {"node": "out"}},
        source_backend="alphaapollo-reasoning",
    )
    observation = Observation(
        observation_id="observation-domain-placeholder",
        tool_name="domain.future_placeholder",
        status="denied",
        payload={"reason": "capability_not_registered"},
    )

    jsonschema.validate(action.to_document(), _load_schema(ACTION_SCHEMA_PATH))
    jsonschema.validate(
        observation.to_document(),
        _load_schema(OBSERVATION_SCHEMA_PATH),
    )


@pytest.mark.parametrize(
    ("schema_path", "document"),
    [
        (
            ACTION_SCHEMA_PATH,
            AgentAction(
                action_id="action-1",
                tool_name="bash",
                arguments={},
                source_backend="mini-swe",
            ).to_document(),
        ),
        (
            OBSERVATION_SCHEMA_PATH,
            Observation(
                observation_id="observation-1",
                tool_name="bash",
                status="completed",
                payload={},
            ).to_document(),
        ),
    ],
)
def test_protocol_schemas_reject_extra_properties(
    schema_path: Path,
    document: dict[str, object],
) -> None:
    document["unexpected"] = True

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(document, _load_schema(schema_path))


def test_canonical_hashes_ignore_mapping_insertion_order() -> None:
    first_action = AgentAction(
        action_id="action-1",
        tool_name="bash",
        arguments={"env": {"B": "2", "A": "1"}, "argv": ["true"]},
        source_backend="mini-swe",
    )
    second_action = AgentAction(
        action_id="action-2",
        tool_name="bash",
        arguments={"argv": ["true"], "env": {"A": "1", "B": "2"}},
        source_backend="mini-swe",
    )
    first_observation = Observation(
        observation_id="observation-1",
        tool_name="bash",
        status="completed",
        payload={"stderr": "", "stdout": "ok"},
    )
    second_observation = Observation(
        observation_id="observation-2",
        tool_name="bash",
        status="completed",
        payload={"stdout": "ok", "stderr": ""},
    )

    assert first_action.arguments_sha256 == second_action.arguments_sha256
    assert first_observation.payload_sha256 == second_observation.payload_sha256


@pytest.mark.parametrize(
    "factory",
    [
        lambda: AgentAction(
            action_id="action-1",
            tool_name="bash",
            arguments=["not", "an", "object"],  # type: ignore[arg-type]
            source_backend="mini-swe",
        ),
        lambda: Observation(
            observation_id="observation-1",
            tool_name="bash",
            status="completed",
            payload=["not", "an", "object"],  # type: ignore[arg-type]
        ),
        lambda: Observation(
            observation_id="observation-1",
            tool_name="bash",
            status="completed",
            payload={},
            budget_delta={"tool_calls": 1.5},  # type: ignore[dict-item]
        ),
        lambda: AgentAction(
            action_id="action-1",
            tool_name="bash",
            arguments={1: "non-string key"},  # type: ignore[dict-item]
            source_backend="mini-swe",
        ),
        lambda: Observation(
            observation_id="observation-1",
            tool_name="bash",
            status="completed",
            payload={"value": float("nan")},
        ),
    ],
)
def test_protocol_objects_reject_values_without_canonical_json_documents(
    factory: Callable[[], object],
) -> None:
    with pytest.raises((TypeError, ValueError)):
        factory()
