from __future__ import annotations

import json
from pathlib import Path

import pytest

from runners.agent_harness import EpisodeContext, JsonlTrajectoryRecorder, read_trajectory
from runners.agent_harness.evidence_export import (
    EvidenceExportError,
    build_reviewer_evidence_export,
)


SHA_A = "a" * 64
SHA_B = "b" * 64


def test_supported_but_missing_transport_capture_is_not_complete(tmp_path):
    trajectory = _controller_events(tmp_path)
    private = _record(tmp_path / "missing-transport.jsonl", _provider_exchange(
        "attempt-001/request-0001", "attempt-001-0001", None,
        transport_capture_supported=True,
    ))
    exported = build_reviewer_evidence_export(
        trajectory_events=trajectory, private_events=private,
        trajectory_bytes=_events_to_bytes(trajectory), private_event_bytes=_events_to_bytes(private),
    )
    assert exported["usage"]["provider"]["unobserved_transport_request_count"] == 1
    assert exported["usage"]["completeness"]["all_provider_transport_attempts_joined"] is False


def test_export_preserves_signed_process_status_and_hides_unknown_finish_reason(tmp_path):
    trajectory = _controller_events(tmp_path)
    provider_rows = _provider_exchange("attempt-001/request-0001", "attempt-001-0001", None)
    provider_rows[-1][3]["response"]["choices"][0]["finish_reason"] = "PRIVATE_SENTINEL"
    capture = _tool_capture("attempt-001-0001")
    capture[3]["returncode"] = -9
    rows = [*provider_rows,
            ("launcher", "tool_request", "harness", {"action_id": "attempt-001-0001"}),
            capture,
            ("launcher", "tool_failure", "harness", {"action_id": "attempt-001-0001"})]
    private = _record(tmp_path / "private-signed.jsonl", rows)
    exported = build_reviewer_evidence_export(
        trajectory_events=trajectory, private_events=private,
        trajectory_bytes=_events_to_bytes(trajectory), private_event_bytes=_events_to_bytes(private),
    )
    assert "PRIVATE_SENTINEL" not in json.dumps(exported)
    captured = next(row for row in exported["ledger"] if row["event_type"] == "tool_output_capture")
    assert captured["payload"]["tool_output_capture"]["returncode"] == -9


def _context() -> EpisodeContext:
    return EpisodeContext(
        episode_id="cell-001",
        attempt_id="attempt-001",
        task_id="v4-001",
        condition="Agentic",
        max_steps=None,
    )


def _events_to_bytes(events: list[dict]) -> bytes:
    return b"".join(
        json.dumps(event, sort_keys=True).encode("utf-8") + b"\n"
        for event in events
    )


def _record(path: Path, rows: list[tuple[str, str, str, dict]]) -> list[dict]:
    recorder = JsonlTrajectoryRecorder(path)
    context = _context()
    for actor, event_type, visibility, payload in rows:
        recorder.append(
            context=context,
            actor=actor,
            event_type=event_type,
            visibility=visibility,  # type: ignore[arg-type]
            payload=payload,
        )
    return read_trajectory(path)


def _controller_events(
    tmp_path: Path,
    *,
    backend_profile_sha256: str = SHA_A,
    budget_delta: dict | None = None,
) -> list[dict]:
    return _record(
        tmp_path / "trajectory.jsonl",
        [
            (
                "controller",
                "episode_started",
                "harness",
                {
                    "backend_profile_sha256": backend_profile_sha256,
                    "public_validation_profile_sha256": SHA_B,
                    "final_test_profile_sha256": SHA_A,
                },
            ),
            (
                "policy",
                "action_proposed",
                "model",
                {
                    "action_id": "attempt-001-0001",
                    "tool_name": "bash",
                    "candidate_tree_sha256": SHA_A,
                    "arguments": {"command": "echo fixture-secret"},
                },
            ),
            (
                "controller",
                "action_authorized",
                "harness",
                {
                    "action_id": "attempt-001-0001",
                    "tool_name": "bash",
                    "candidate_tree_sha256": SHA_A,
                },
            ),
            (
                "controller",
                "budget_updated",
                "harness",
                {
                    "action_id": "attempt-001-0001",
                    "delta": budget_delta
                    if budget_delta is not None
                    else {"model_calls": 1, "public_validation_calls": 0},
                    "consumed": budget_delta
                    if budget_delta is not None
                    else {"model_calls": 1, "public_validation_calls": 0},
                },
            ),
            (
                "environment",
                "environment_observed",
                "model",
                {
                    "action_id": "attempt-001-0001",
                    "tool_name": "bash",
                    "status": "succeeded",
                    "candidate_tree_sha256": SHA_B,
                    "terminal_reason": None,
                    "payload": {"output": "public simulator diagnostic"},
                },
            ),
            (
                "environment",
                "submission_frozen",
                "harness",
                {
                    "submission_tree_sha256": SHA_B,
                    "candidate_tree_sha256": SHA_B,
                    "artifact_paths": ["model.va"],
                },
            ),
            (
                "final_judge",
                "final_judgment_completed",
                "trusted",
                {
                    "primary_outcome": "behavior_failure",
                    "terminal_reason": "submitted",
                    "hidden_diagnostics": "FINAL_JUDGE_SENTINEL",
                },
            ),
            ("environment", "cleanup_completed", "harness", {}),
            (
                "controller",
                "episode_completed",
                "harness",
                {
                    "primary_outcome": "behavior_failure",
                    "terminal_reason": "submitted",
                },
            ),
        ],
    )


def _private_events(
    tmp_path: Path,
    *,
    with_usage: bool = True,
    candidate_tree_sha256: str = SHA_A,
    max_tokens=128,
    timeout_s=10,
) -> list[dict]:
    usage = (
        {"prompt_tokens": 17, "completion_tokens": 5, "total_tokens": 22}
        if with_usage
        else None
    )
    payload_usage = {"usage": usage} if usage is not None else {}
    return _record(
        tmp_path / "private-events.jsonl",
        [
            (
                "launcher",
                "provider_request",
                "harness",
                {
                    "request_id": "attempt-001/request-0001",
                    "action_id": "attempt-001-0001",
                    "messages": [{"role": "user", "content": "fixture-secret"}],
                    "max_tokens": max_tokens,
                    "timeout_s": timeout_s,
                },
            ),
            (
                "launcher",
                "provider_response",
                "harness",
                {
                    "request_id": "attempt-001/request-0001",
                    "action_id": "attempt-001-0001",
                    "response": {
                        "id": "response-001",
                        "model": "fixture-model",
                        "choices": [
                            {
                                "finish_reason": "tool_calls",
                                "message": {
                                    "content": "fixture-secret",
                                    "tool_calls": [
                                        {
                                            "function": {
                                                "arguments": "{\"command\":\"secret\"}"
                                            }
                                        }
                                    ],
                                },
                            }
                        ],
                        **payload_usage,
                    },
                },
            ),
            (
                "launcher",
                "tool_request",
                "harness",
                {
                    "action_id": "attempt-001-0001",
                    "tool_name": "bash",
                    "arguments": {"command": "echo fixture-secret"},
                    "candidate_tree_sha256": candidate_tree_sha256,
                },
            ),
            (
                "launcher",
                "tool_result",
                "harness",
                {
                    "action_id": "attempt-001-0001",
                    "observation": {
                        "tool_name": "bash",
                        "status": "succeeded",
                        "payload": {"output": "fixture-secret"},
                        "candidate_tree_sha256": SHA_B,
                    },
                },
            ),
        ],
    )


def _provider_exchange(
    request_id: str,
    action_id: str,
    usage: dict[str, int] | None,
    *,
    transport_capture_supported: bool | None = None,
) -> list[tuple[str, str, str, dict]]:
    request = {"request_id": request_id, "action_id": action_id}
    if transport_capture_supported is not None:
        request["transport_capture_supported"] = transport_capture_supported
    response: dict = {
        "id": f"response-{request_id.rsplit('-', 1)[-1]}",
        "model": "fixture-model",
        "choices": [{"finish_reason": "stop", "message": {"content": "secret"}}],
    }
    if usage is not None:
        response["usage"] = usage
    return [
        (
            "launcher",
            "provider_request",
            "harness",
            request,
        ),
        (
            "launcher",
            "provider_response",
            "harness",
            {
                "request_id": request_id,
                "action_id": action_id,
                "response": response,
            },
        ),
    ]


def _transport_attempt(
    request_id: str,
    action_id: str,
    ordinal: int,
    *,
    capture_complete: bool = True,
) -> tuple[str, str, str, dict]:
    return (
        "launcher",
        "provider_transport_attempt",
        "harness",
        {
            "request_id": request_id,
            "action_id": action_id,
            "transport_attempt": ordinal,
            "returncode": 0,
            "error_type": None,
            "capture_complete": capture_complete,
            "elapsed_s": 0.25,
            "stdout": {
                "encoding": "utf8_redacted_decoded_transport",
                "text": "raw secret stdout",
                "bytes_sha256": SHA_A,
                "total_bytes": 20,
                "retained_bytes": 12,
                "truncated_bytes": 8,
            },
            "stderr": {
                "encoding": "utf8_redacted_decoded_transport",
                "text": "raw secret stderr",
                "bytes_sha256": SHA_B,
                "total_bytes": 0,
                "retained_bytes": 0,
                "truncated_bytes": 0,
            },
        },
    )


def _tool_event(
    event_type: str,
    action_id: str,
    *,
    tool_name: str = "bash",
) -> tuple[str, str, str, dict]:
    payload: dict = {"action_id": action_id}
    if event_type == "tool_request":
        payload.update(
            {
                "tool_name": tool_name,
                "arguments": {"command": "echo secret"},
                "candidate_tree_sha256": SHA_A,
            }
        )
    elif event_type == "tool_result":
        payload["observation"] = {
            "tool_name": tool_name,
            "status": "succeeded",
            "payload": {"output": "secret"},
            "candidate_tree_sha256": SHA_B,
        }
    elif event_type == "tool_failure":
        payload.update(
            {
                "tool_name": tool_name,
                "failure_category": "infrastructure_failure",
                "status": "failed",
            }
        )
    else:
        raise AssertionError(event_type)
    return ("launcher", event_type, "harness", payload)


def _tool_capture(
    action_id: str,
    *,
    capture_complete: bool = True,
    truncated_bytes: int = 5,
) -> tuple[str, str, str, dict]:
    return (
        "launcher",
        "tool_output_capture",
        "harness",
        {
            "schema_version": "vabench-private-tool-output-capture-v1",
            "action_id": action_id,
            "tool_name": "bash",
            "returncode": 0,
            "elapsed_s": 0.5,
            "output_sha256": SHA_A,
            "output_total_bytes": 100,
            "output_captured_bytes": 95,
            "output_truncated_bytes": truncated_bytes,
            "output_capture_complete": capture_complete,
            "output_capture_eof": True,
            "output_capture_read_error": False,
            "retained_output_scope": "bounded_head_tail_pre_model_capture",
            "output": "raw secret output",
            "resources": {"secret_resource_path": "/private/tmp/secret"},
        },
    )


def test_reviewer_export_binds_sources_and_excludes_model_visible_content(
    tmp_path: Path,
) -> None:
    trajectory = _controller_events(tmp_path)
    private = _private_events(tmp_path)

    export = build_reviewer_evidence_export(
        trajectory_events=trajectory,
        private_events=private,
        trajectory_bytes=_events_to_bytes(trajectory),
        private_event_bytes=_events_to_bytes(private),
    )

    assert export["schema_version"] == "vaevas-reviewer-evidence-export-v1"
    assert export["normalizer_id"] == "vaevas-reviewer-evidence-normalizer-v1"
    assert export["export_sha256"]
    assert export["source"]["trajectory"]["bytes_sha256"]
    assert export["source"]["private_events"]["tail_event_sha256"] == private[-1][
        "event_sha256"
    ]
    assert len(export["ledger"]) == len(trajectory) + len(private)
    assert export["ledger"][0]["source_event_sha256"] == trajectory[0]["event_sha256"]
    assert export["ledger"][0]["identity"] == {
        "episode_id": "cell-001",
        "attempt_id": "attempt-001",
        "task_id": "v4-001",
        "condition": "Agentic",
    }
    provider_payload = next(
        row["payload"]
        for row in export["ledger"]
        if row["event_type"] == "provider_response"
    )
    assert provider_payload["provider_response"] == {
        "response_id_sha256": provider_payload["provider_response"][
            "response_id_sha256"
        ],
        "model_sha256": provider_payload["provider_response"]["model_sha256"],
        "finish_reason": "tool_calls",
    }
    assert len(provider_payload["provider_response"]["response_id_sha256"]) == 64
    assert len(provider_payload["provider_response"]["model_sha256"]) == 64
    assert "response_id" not in provider_payload["provider_response"]
    assert "model" not in provider_payload["provider_response"]
    dumped = json.dumps(export, sort_keys=True)
    for forbidden in (
        "fixture-secret",
        "fixture-model",
        "response-001",
        "raw secret",
        "public simulator diagnostic",
        "FINAL_JUDGE_SENTINEL",
        "messages",
        "arguments",
        "command",
        '"response":',
        "hidden_diagnostics",
    ):
        assert forbidden not in dumped
    assert export["visibility_contract"] == {
        "audience": "reviewer_only",
        "may_enter_model_observation": False,
        "may_enter_shared_memory": False,
        "final_judge_payload_exported": False,
    }


def test_export_normalizes_joined_usage_and_missingness(tmp_path: Path) -> None:
    trajectory = _controller_events(tmp_path)
    private = _private_events(tmp_path, with_usage=True)

    export = build_reviewer_evidence_export(
        trajectory_events=trajectory,
        private_events=private,
        trajectory_bytes=_events_to_bytes(trajectory),
        private_event_bytes=_events_to_bytes(private),
    )

    assert export["usage"] == {
        "completeness": {
            "all_provider_requests_joined": True,
            "all_provider_requests_resolved": True,
            "all_provider_transport_attempts_joined": False,
            "provider_usage_complete": True,
            "all_tool_requests_resolved": True,
        },
        "provider": {
            "requests": 1,
            "responses": 1,
            "failures": 0,
            "transport_attempts": 0,
            "unobserved_transport_request_count": 1,
            "transport_capture_supported": False,
            "transport_capture_complete": None,
            "transport_elapsed_s": None,
            "transport_stdout_total_bytes": 0,
            "transport_stderr_total_bytes": 0,
            "usage_status": "reported",
            "unknown_usage_fields": [],
            "unknown_optional_usage_fields": ["reasoning_tokens"],
            "usage": {
                "prompt_tokens": 17,
                "completion_tokens": 5,
                "total_tokens": 22,
                "reasoning_tokens": None,
            },
        },
        "tools": {
            "requests": 1,
            "results": 1,
            "failures": 0,
            "captures": 0,
            "unresolved_requests": 0,
            "capture_complete": None,
            "capture_truncated_bytes": 0,
            "capture_total_bytes": 0,
            "capture_captured_bytes": 0,
        },
    }


def test_export_preserves_unknown_usage_as_null(tmp_path: Path) -> None:
    trajectory = _controller_events(tmp_path)
    private = _private_events(tmp_path, with_usage=False)

    export = build_reviewer_evidence_export(
        trajectory_events=trajectory,
        private_events=private,
        trajectory_bytes=_events_to_bytes(trajectory),
        private_event_bytes=_events_to_bytes(private),
    )

    assert export["usage"]["provider"]["usage"] == {
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
        "reasoning_tokens": None,
    }
    assert export["usage"]["provider"]["usage_status"] == "partial"
    assert export["usage"]["provider"]["unknown_usage_fields"] == [
        "completion_tokens",
        "prompt_tokens",
        "total_tokens",
    ]
    assert export["usage"]["provider"]["unknown_optional_usage_fields"] == [
        "reasoning_tokens"
    ]
    assert export["usage"]["completeness"]["provider_usage_complete"] is False


def test_export_keeps_partially_missing_usage_unknown(tmp_path: Path) -> None:
    trajectory = _controller_events(tmp_path)
    private = _record(
        tmp_path / "private-partial-usage.jsonl",
        [
            *_provider_exchange(
                "attempt-001/request-0001",
                "attempt-001-0001",
                None,
            ),
            *_provider_exchange(
                "attempt-001/request-0002",
                "attempt-001-0002",
                {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7},
            ),
        ],
    )

    export = build_reviewer_evidence_export(
        trajectory_events=trajectory,
        private_events=private,
        trajectory_bytes=_events_to_bytes(trajectory),
        private_event_bytes=_events_to_bytes(private),
    )

    assert export["usage"]["provider"]["usage"] == {
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
        "reasoning_tokens": None,
    }
    assert export["usage"]["provider"]["unknown_usage_fields"] == [
        "completion_tokens",
        "prompt_tokens",
        "total_tokens",
    ]
    assert export["usage"]["provider"]["unknown_optional_usage_fields"] == [
        "reasoning_tokens"
    ]
    assert export["usage"]["completeness"]["provider_usage_complete"] is False


def test_export_records_explicit_reasoning_tokens_without_estimation(
    tmp_path: Path,
) -> None:
    trajectory = _controller_events(tmp_path)
    private = _record(
        tmp_path / "private-reasoning-usage.jsonl",
        [
            *_provider_exchange(
                "attempt-001/request-0001",
                "attempt-001-0001",
                {
                    "prompt_tokens": 1,
                    "completion_tokens": 5,
                    "total_tokens": 6,
                    "completion_tokens_details": {"reasoning_tokens": 3},
                },
            ),
        ],
    )

    export = build_reviewer_evidence_export(
        trajectory_events=trajectory,
        private_events=private,
        trajectory_bytes=_events_to_bytes(trajectory),
        private_event_bytes=_events_to_bytes(private),
    )

    assert export["usage"]["provider"]["usage"] == {
        "prompt_tokens": 1,
        "completion_tokens": 5,
        "total_tokens": 6,
        "reasoning_tokens": 3,
    }
    assert export["usage"]["provider"]["unknown_optional_usage_fields"] == []
    assert export["usage"]["completeness"]["provider_usage_complete"] is True


def test_export_rejects_inconsistent_reasoning_token_sources(
    tmp_path: Path,
) -> None:
    trajectory = _controller_events(tmp_path)
    private = _record(
        tmp_path / "private-reasoning-usage-mismatch.jsonl",
        [
            *_provider_exchange(
                "attempt-001/request-0001",
                "attempt-001-0001",
                {
                    "prompt_tokens": 1,
                    "completion_tokens": 5,
                    "total_tokens": 6,
                    "reasoning_tokens": 2,
                    "completion_tokens_details": {"reasoning_tokens": 3},
                },
            ),
        ],
    )

    with pytest.raises(EvidenceExportError, match="reasoning_tokens"):
        build_reviewer_evidence_export(
            trajectory_events=trajectory,
            private_events=private,
            trajectory_bytes=_events_to_bytes(trajectory),
            private_event_bytes=_events_to_bytes(private),
        )


def test_export_reports_no_provider_calls_as_usage_unavailable(tmp_path: Path) -> None:
    trajectory = _controller_events(tmp_path)
    private = _record(
        tmp_path / "private-no-provider.jsonl",
        [_tool_event("tool_request", "attempt-001-0001")],
    )

    export = build_reviewer_evidence_export(
        trajectory_events=trajectory,
        private_events=private,
        trajectory_bytes=_events_to_bytes(trajectory),
        private_event_bytes=_events_to_bytes(private),
    )

    assert export["usage"]["provider"] == {
        "requests": 0,
        "responses": 0,
            "failures": 0,
            "transport_attempts": 0,
            "unobserved_transport_request_count": 0,
            "transport_capture_supported": False,
            "transport_capture_complete": None,
            "transport_elapsed_s": None,
            "transport_stdout_total_bytes": 0,
            "transport_stderr_total_bytes": 0,
            "usage_status": "no_calls",
            "unknown_usage_fields": [
                "completion_tokens",
                "prompt_tokens",
                "total_tokens",
            ],
            "unknown_optional_usage_fields": ["reasoning_tokens"],
            "usage": {
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
                "reasoning_tokens": None,
            },
        }
    assert export["usage"]["completeness"]["provider_usage_complete"] is False
    assert export["usage"]["completeness"]["all_tool_requests_resolved"] is False


def test_export_requires_provider_resolution_after_matching_request_action(
    tmp_path: Path,
) -> None:
    trajectory = _controller_events(tmp_path)
    private = _record(
        tmp_path / "private-provider-mismatch-rebuilt.jsonl",
        [
            (
                "launcher",
                "provider_request",
                "harness",
                {
                    "request_id": "attempt-001/request-0001",
                    "action_id": "attempt-001-0001",
                },
            ),
            (
                "launcher",
                "provider_response",
                "harness",
                {
                    "request_id": "attempt-001/request-0001",
                    "action_id": "attempt-001-0002",
                    "response": {
                        "id": "response-001",
                        "choices": [{"finish_reason": "stop"}],
                        "usage": {
                            "prompt_tokens": 1,
                            "completion_tokens": 1,
                            "total_tokens": 2,
                        },
                    },
                },
            ),
        ],
    )

    with pytest.raises(EvidenceExportError, match="provider action_id mismatch"):
        build_reviewer_evidence_export(
            trajectory_events=trajectory,
            private_events=private,
            trajectory_bytes=_events_to_bytes(trajectory),
            private_event_bytes=_events_to_bytes(private),
        )


def test_export_rejects_provider_resolution_before_request(tmp_path: Path) -> None:
    trajectory = _controller_events(tmp_path)
    private = _record(
        tmp_path / "private-provider-reordered.jsonl",
        [
            (
                "launcher",
                "provider_response",
                "harness",
                {
                    "request_id": "attempt-001/request-0001",
                    "action_id": "attempt-001-0001",
                    "response": {"id": "response-001", "choices": []},
                },
            ),
            (
                "launcher",
                "provider_request",
                "harness",
                {
                    "request_id": "attempt-001/request-0001",
                    "action_id": "attempt-001-0001",
                },
            ),
        ],
    )

    with pytest.raises(EvidenceExportError, match="before provider request"):
        build_reviewer_evidence_export(
            trajectory_events=trajectory,
            private_events=private,
            trajectory_bytes=_events_to_bytes(trajectory),
            private_event_bytes=_events_to_bytes(private),
        )


def test_export_joins_tool_results_and_failures_by_action_id(tmp_path: Path) -> None:
    trajectory = _controller_events(tmp_path)
    private = _record(
        tmp_path / "private-tool-failure.jsonl",
        [
            _tool_event("tool_request", "attempt-001-0001"),
            _tool_event("tool_failure", "attempt-001-0001"),
            _tool_event("tool_request", "attempt-001-0002"),
            _tool_event("tool_result", "attempt-001-0002"),
        ],
    )

    export = build_reviewer_evidence_export(
        trajectory_events=trajectory,
        private_events=private,
        trajectory_bytes=_events_to_bytes(trajectory),
        private_event_bytes=_events_to_bytes(private),
    )

    assert export["usage"]["tools"] == {
        "requests": 2,
        "results": 1,
        "failures": 1,
        "captures": 0,
        "unresolved_requests": 0,
        "capture_complete": None,
        "capture_truncated_bytes": 0,
        "capture_total_bytes": 0,
        "capture_captured_bytes": 0,
    }
    assert export["usage"]["completeness"]["all_tool_requests_resolved"] is True


def test_export_separates_model_requests_from_transport_attempts(tmp_path: Path) -> None:
    trajectory = _controller_events(tmp_path)
    private = _record(
        tmp_path / "private-transport.jsonl",
        [
            (
                "launcher",
                "provider_request",
                "harness",
                {
                    "request_id": "attempt-001/request-0001",
                    "action_id": "attempt-001-0001",
                    "transport_capture_supported": True,
                },
            ),
            _transport_attempt("attempt-001/request-0001", "attempt-001-0001", 1),
            _transport_attempt("attempt-001/request-0001", "attempt-001-0001", 2),
            (
                "launcher",
                "provider_response",
                "harness",
                {
                    "request_id": "attempt-001/request-0001",
                    "action_id": "attempt-001-0001",
                    "response": {
                        "id": "response-001",
                        "model": "fixture-model",
                        "choices": [{"finish_reason": "stop"}],
                        "usage": {
                            "prompt_tokens": 1,
                            "completion_tokens": 2,
                            "total_tokens": 3,
                        },
                    },
                },
            ),
        ],
    )

    export = build_reviewer_evidence_export(
        trajectory_events=trajectory,
        private_events=private,
        trajectory_bytes=_events_to_bytes(trajectory),
        private_event_bytes=_events_to_bytes(private),
    )

    assert export["usage"]["provider"]["requests"] == 1
    assert export["usage"]["provider"]["transport_attempts"] == 2
    assert export["usage"]["provider"]["unobserved_transport_request_count"] == 0
    assert export["usage"]["provider"]["transport_capture_supported"] is True
    assert export["usage"]["provider"]["transport_capture_complete"] is True
    assert export["usage"]["provider"]["transport_elapsed_s"] == 0.5
    assert export["usage"]["provider"]["transport_stdout_total_bytes"] == 40
    assert export["usage"]["provider"]["transport_stderr_total_bytes"] == 0
    attempts = [
        row["payload"]["transport"]
        for row in export["ledger"]
        if row["event_type"] == "provider_transport_attempt"
    ]
    assert [attempt["transport_attempt"] for attempt in attempts] == [1, 2]
    assert attempts[0]["stdout"] == {
        "encoding": "utf8_redacted_decoded_transport",
        "bytes_sha256": SHA_A,
        "total_bytes": 20,
        "retained_bytes": 12,
        "truncated_bytes": 8,
    }
    assert attempts[0]["stderr"] == {
        "encoding": "utf8_redacted_decoded_transport",
        "bytes_sha256": SHA_B,
        "total_bytes": 0,
        "retained_bytes": 0,
        "truncated_bytes": 0,
    }
    dumped = json.dumps(export, sort_keys=True)
    assert "raw secret stdout" not in dumped
    assert "raw secret stderr" not in dumped


@pytest.mark.parametrize(
    "rows,message",
    [
        (
            [
                _transport_attempt("attempt-001/request-0001", "attempt-001-0001", 1),
                (
                    "launcher",
                    "provider_request",
                    "harness",
                    {
                        "request_id": "attempt-001/request-0001",
                        "action_id": "attempt-001-0001",
                        "transport_capture_supported": True,
                    },
                ),
            ],
            "before provider request",
        ),
        (
            [
                (
                    "launcher",
                    "provider_request",
                    "harness",
                    {
                        "request_id": "attempt-001/request-0001",
                        "action_id": "attempt-001-0001",
                        "transport_capture_supported": True,
                    },
                ),
                _transport_attempt("attempt-001/request-0001", "attempt-001-0001", 2),
            ],
            "transport_attempt ordinal",
        ),
        (
            [
                (
                    "launcher",
                    "provider_request",
                    "harness",
                    {
                        "request_id": "attempt-001/request-0001",
                        "action_id": "attempt-001-0001",
                        "transport_capture_supported": True,
                    },
                ),
                _transport_attempt("attempt-001/request-0001", "attempt-001-0001", 1),
                _transport_attempt("attempt-001/request-0001", "attempt-001-0001", 1),
            ],
            "duplicate provider transport attempt",
        ),
        (
            [
                (
                    "launcher",
                    "provider_request",
                    "harness",
                    {
                        "request_id": "attempt-001/request-0001",
                        "action_id": "attempt-001-0001",
                        "transport_capture_supported": True,
                    },
                ),
                _transport_attempt("attempt-001/request-0001", "attempt-001-0002", 1),
            ],
            "provider transport action_id mismatch",
        ),
        (
            [
                *_provider_exchange(
                    "attempt-001/request-0001",
                    "attempt-001-0001",
                    {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    transport_capture_supported=True,
                ),
                _transport_attempt("attempt-001/request-0001", "attempt-001-0001", 1),
            ],
            "after response",
        ),
        (
            [
                (
                    "launcher",
                    "provider_request",
                    "harness",
                    {
                        "request_id": "attempt-001/request-0001",
                        "action_id": "attempt-001-0001",
                        "transport_capture_supported": True,
                    },
                ),
                (
                    lambda event: (
                        event[0],
                        event[1],
                        event[2],
                        {
                            **event[3],
                            "stdout": {
                                **event[3]["stdout"],
                                "bytes_sha256": "not-a-sha",
                            },
                        },
                    )
                )(_transport_attempt("attempt-001/request-0001", "attempt-001-0001", 1)),
            ],
            "sha256",
        ),
        (
            [
                (
                    "launcher",
                    "provider_request",
                    "harness",
                    {
                        "request_id": "attempt-001/request-0001",
                        "action_id": "attempt-001-0001",
                        "transport_capture_supported": True,
                    },
                ),
                (
                    lambda event: (
                        event[0],
                        event[1],
                        event[2],
                        {
                            **event[3],
                            "stdout": {
                                **event[3]["stdout"],
                                "retained_bytes": 13,
                            },
                        },
                    )
                )(_transport_attempt("attempt-001/request-0001", "attempt-001-0001", 1)),
            ],
            "byte counts",
        ),
    ],
)
def test_export_rejects_bad_provider_transport_attempts(
    tmp_path: Path,
    rows: list[tuple[str, str, str, dict]],
    message: str,
) -> None:
    trajectory = _controller_events(tmp_path)
    private = _record(tmp_path / f"private-{message}.jsonl", rows)

    with pytest.raises(EvidenceExportError, match=message):
        build_reviewer_evidence_export(
            trajectory_events=trajectory,
            private_events=private,
            trajectory_bytes=_events_to_bytes(trajectory),
            private_event_bytes=_events_to_bytes(private),
        )


def test_export_joins_tool_output_capture_before_result(tmp_path: Path) -> None:
    trajectory = _controller_events(tmp_path)
    private = _record(
        tmp_path / "private-tool-capture.jsonl",
        [
            _tool_event("tool_request", "attempt-001-0001"),
            _tool_capture("attempt-001-0001", capture_complete=False),
            _tool_event("tool_result", "attempt-001-0001"),
        ],
    )

    export = build_reviewer_evidence_export(
        trajectory_events=trajectory,
        private_events=private,
        trajectory_bytes=_events_to_bytes(trajectory),
        private_event_bytes=_events_to_bytes(private),
    )

    assert export["usage"]["tools"] == {
        "requests": 1,
        "results": 1,
        "failures": 0,
        "captures": 1,
        "unresolved_requests": 0,
        "capture_complete": False,
        "capture_truncated_bytes": 5,
        "capture_total_bytes": 100,
        "capture_captured_bytes": 95,
    }
    capture = [
        row["payload"]["tool_output_capture"]
        for row in export["ledger"]
        if row["event_type"] == "tool_output_capture"
    ][0]
    assert capture == {
        "schema_version": "vabench-private-tool-output-capture-v1",
        "tool_name": "bash",
        "returncode": 0,
        "elapsed_s": 0.5,
        "output_sha256": SHA_A,
        "output_total_bytes": 100,
        "output_captured_bytes": 95,
        "output_truncated_bytes": 5,
        "output_capture_complete": False,
        "output_capture_eof": True,
        "output_capture_read_error": False,
        "retained_output_scope": "bounded_head_tail_pre_model_capture",
    }
    dumped = json.dumps(export, sort_keys=True)
    assert "raw secret output" not in dumped
    assert "secret_resource_path" not in dumped


@pytest.mark.parametrize(
    "rows,message",
    [
        (
            [
                _tool_capture("attempt-001-0001"),
                _tool_event("tool_request", "attempt-001-0001"),
            ],
            "before tool request",
        ),
        (
            [
                _tool_event("tool_request", "attempt-001-0001"),
                _tool_event("tool_result", "attempt-001-0001"),
                _tool_capture("attempt-001-0001"),
            ],
            "after tool resolution",
        ),
        (
            [
                _tool_event("tool_request", "attempt-001-0001"),
                _tool_capture("attempt-001-0001"),
                _tool_capture("attempt-001-0001"),
            ],
            "duplicate tool output capture",
        ),
        (
            [
                _tool_event("tool_request", "attempt-001-0001"),
                _tool_capture("attempt-001-0001", truncated_bytes=-1),
            ],
            "non-negative integer",
        ),
        (
            [
                _tool_event("tool_request", "attempt-001-0001"),
                (
                    lambda event: (
                        event[0],
                        event[1],
                        event[2],
                        {**event[3], "output_sha256": "not-a-sha"},
                    )
                )(_tool_capture("attempt-001-0001")),
            ],
            "sha256",
        ),
        (
            [
                _tool_event("tool_request", "attempt-001-0001"),
                (
                    lambda event: (
                        event[0],
                        event[1],
                        event[2],
                        {**event[3], "output_captured_bytes": 96},
                    )
                )(_tool_capture("attempt-001-0001")),
            ],
            "byte counts",
        ),
    ],
)
def test_export_rejects_bad_tool_output_captures(
    tmp_path: Path,
    rows: list[tuple[str, str, str, dict]],
    message: str,
) -> None:
    trajectory = _controller_events(tmp_path)
    private = _record(tmp_path / f"private-{message}.jsonl", rows)

    with pytest.raises(EvidenceExportError, match=message):
        build_reviewer_evidence_export(
            trajectory_events=trajectory,
            private_events=private,
            trajectory_bytes=_events_to_bytes(trajectory),
            private_event_bytes=_events_to_bytes(private),
        )


def test_export_rejects_unknown_budget_counters(tmp_path: Path) -> None:
    trajectory = _controller_events(tmp_path, budget_delta={"surprise_counter": 1})
    private = _private_events(tmp_path)

    with pytest.raises(EvidenceExportError, match="budget counter"):
        build_reviewer_evidence_export(
            trajectory_events=trajectory,
            private_events=private,
            trajectory_bytes=_events_to_bytes(trajectory),
            private_event_bytes=_events_to_bytes(private),
        )


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("backend_profile_sha256", "not-a-sha", "sha256"),
        ("candidate_tree_sha256", "g" * 64, "sha256"),
        ("max_tokens", -1, "non-negative integer"),
        ("max_tokens", True, "non-negative integer"),
        ("timeout_s", float("inf"), "finite non-negative number"),
        ("timeout_s", -0.1, "finite non-negative number"),
    ],
)
def test_export_rejects_invalid_structural_values(
    tmp_path: Path,
    field: str,
    value,
    message: str,
) -> None:
    if field == "backend_profile_sha256":
        trajectory = _controller_events(tmp_path, backend_profile_sha256=value)
        private = _private_events(tmp_path)
    elif field == "candidate_tree_sha256":
        trajectory = _controller_events(tmp_path)
        private = _private_events(tmp_path, candidate_tree_sha256=value)
    elif field == "max_tokens":
        trajectory = _controller_events(tmp_path)
        private = _private_events(tmp_path, max_tokens=value)
    else:
        trajectory = _controller_events(tmp_path)
        private = _private_events(tmp_path, timeout_s=value)

    with pytest.raises(EvidenceExportError, match=message):
        build_reviewer_evidence_export(
            trajectory_events=trajectory,
            private_events=private,
            trajectory_bytes=_events_to_bytes(trajectory),
            private_event_bytes=_events_to_bytes(private),
        )


def test_export_allows_null_timeout_and_nonterminal_terminal_reason(
    tmp_path: Path,
) -> None:
    trajectory = _controller_events(tmp_path)
    private = _private_events(tmp_path, timeout_s=None)

    export = build_reviewer_evidence_export(
        trajectory_events=trajectory,
        private_events=private,
        trajectory_bytes=_events_to_bytes(trajectory),
        private_event_bytes=_events_to_bytes(private),
    )

    observed = [
        row for row in export["ledger"] if row["event_type"] == "environment_observed"
    ][0]
    request = [
        row for row in export["ledger"] if row["event_type"] == "provider_request"
    ][0]
    assert observed["payload"]["terminal_reason"] is None
    assert request["payload"]["timeout_s"] is None


@pytest.mark.parametrize(
    "rows,message",
    [
        (
            [
                _tool_event("tool_result", "attempt-001-0001"),
                _tool_event("tool_request", "attempt-001-0001"),
            ],
            "before tool request",
        ),
        (
            [
                _tool_event("tool_request", "attempt-001-0001"),
                _tool_event("tool_request", "attempt-001-0001"),
            ],
            "duplicate tool request",
        ),
        (
            [
                _tool_event("tool_request", "attempt-001-0001"),
                _tool_event("tool_result", "attempt-001-0001"),
                _tool_event("tool_failure", "attempt-001-0001"),
            ],
            "duplicate tool resolution",
        ),
    ],
)
def test_export_rejects_bad_tool_request_resolution_pairs(
    tmp_path: Path,
    rows: list[tuple[str, str, str, dict]],
    message: str,
) -> None:
    trajectory = _controller_events(tmp_path)
    private = _record(tmp_path / f"private-{message}.jsonl", rows)

    with pytest.raises(EvidenceExportError, match=message):
        build_reviewer_evidence_export(
            trajectory_events=trajectory,
            private_events=private,
            trajectory_bytes=_events_to_bytes(trajectory),
            private_event_bytes=_events_to_bytes(private),
        )


def test_export_rejects_tampered_trajectory(tmp_path: Path) -> None:
    trajectory = _controller_events(tmp_path)
    private = _private_events(tmp_path)
    trajectory[1]["payload"]["tool_name"] = "run_evas"

    with pytest.raises(EvidenceExportError, match="trajectory"):
        build_reviewer_evidence_export(
            trajectory_events=trajectory,
            private_events=private,
            trajectory_bytes=_events_to_bytes(trajectory),
            private_event_bytes=_events_to_bytes(private),
        )


def test_export_rejects_private_bytes_that_do_not_match_events(tmp_path: Path) -> None:
    trajectory = _controller_events(tmp_path)
    private = _private_events(tmp_path)
    mismatched_private = _events_to_bytes(private).replace(
        b"provider_request", b"provider_mutation", 1
    )

    with pytest.raises(EvidenceExportError, match="bytes do not match"):
        build_reviewer_evidence_export(
            trajectory_events=trajectory,
            private_events=private,
            trajectory_bytes=_events_to_bytes(trajectory),
            private_event_bytes=mismatched_private,
        )


def test_export_rejects_unresolved_provider_request(tmp_path: Path) -> None:
    trajectory = _controller_events(tmp_path)
    private = _record(
        tmp_path / "private-unresolved.jsonl",
        [
            (
                "launcher",
                "provider_request",
                "harness",
                {
                    "request_id": "attempt-001/request-0001",
                    "action_id": "attempt-001-0001",
                },
            )
        ],
    )

    with pytest.raises(EvidenceExportError, match="unresolved provider request"):
        build_reviewer_evidence_export(
            trajectory_events=trajectory,
            private_events=private,
            trajectory_bytes=_events_to_bytes(trajectory),
            private_event_bytes=_events_to_bytes(private),
        )


def test_export_rejects_duplicate_provider_request(tmp_path: Path) -> None:
    trajectory = _controller_events(tmp_path)
    private = _record(
        tmp_path / "private-duplicate.jsonl",
        [
            (
                "launcher",
                "provider_request",
                "harness",
                {
                    "request_id": "attempt-001/request-0001",
                    "action_id": "attempt-001-0001",
                },
            ),
            (
                "launcher",
                "provider_request",
                "harness",
                {
                    "request_id": "attempt-001/request-0001",
                    "action_id": "attempt-001-0002",
                },
            ),
        ],
    )

    with pytest.raises(EvidenceExportError, match="duplicate provider request"):
        build_reviewer_evidence_export(
            trajectory_events=trajectory,
            private_events=private,
            trajectory_bytes=_events_to_bytes(trajectory),
            private_event_bytes=_events_to_bytes(private),
        )


def test_export_rejects_non_string_identity_and_join_keys(tmp_path: Path) -> None:
    trajectory = _controller_events(tmp_path)
    private = _record(
        tmp_path / "private-non-string.jsonl",
        [
            (
                "launcher",
                "provider_request",
                "harness",
                {
                    "request_id": {"not": "a string"},
                    "action_id": "attempt-001-0001",
                },
            )
        ],
    )

    with pytest.raises(EvidenceExportError, match="request_id"):
        build_reviewer_evidence_export(
            trajectory_events=trajectory,
            private_events=private,
            trajectory_bytes=_events_to_bytes(trajectory),
            private_event_bytes=_events_to_bytes(private),
        )
