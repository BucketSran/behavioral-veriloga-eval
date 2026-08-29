from __future__ import annotations

from collections.abc import Callable

import pytest

from runners.agent_harness import (
    ProposalEnvelope,
    ProposalFormat,
    ProposalNormalizationError,
    normalize_proposal,
)


TRUSTED = {
    "action_id": "action-1",
    "source_backend": "mini-swe",
    "candidate_tree_sha256": "a" * 64,
    "accepted_tool_names": frozenset({"bash"}),
}


def test_native_and_strict_json_proposals_normalize_to_the_same_action() -> None:
    native = normalize_proposal(
        ProposalEnvelope(proposal_format="native_tool_calls", **TRUSTED),
        [
            {
                "type": "function",
                "function": {
                    "name": "bash",
                    "arguments": '{"command":"printf ok"}',
                },
            }
        ],
    )
    strict_json = normalize_proposal(
        ProposalEnvelope(proposal_format="strict_json", **TRUSTED),
        '{"tool_name":"bash","arguments":{"command":"printf ok"}}',
    )

    assert native.to_document() == strict_json.to_document()


@pytest.mark.parametrize(
    "reserved_field",
    [
        "action_id",
        "source_backend",
        "candidate_tree_sha256",
        "arguments_sha256",
        "schema_version",
    ],
)
def test_strict_json_proposal_cannot_supply_trusted_fields(
    reserved_field: str,
) -> None:
    proposal = (
        '{"tool_name":"bash","arguments":{"command":"true"},'
        f'"{reserved_field}":"forged"}}'
    )

    with pytest.raises(ProposalNormalizationError, match="unexpected_fields"):
        normalize_proposal(
            ProposalEnvelope(proposal_format="strict_json", **TRUSTED),
            proposal,
        )


@pytest.mark.parametrize(
    ("proposal", "error_code"),
    [
        ('{"tool_name":"bash",', "malformed_json"),
        ('{"tool_name":"bash","tool_name":"bash","arguments":{}}', "duplicate_key"),
        ('{"tool_name":"bash","arguments":{"value":NaN}}', "invalid_number"),
        ('{"tool_name":"bash","arguments":[]}', "invalid_arguments"),
        ('["bash",{}]', "invalid_json_root"),
        ('{"tool_name":"bash"}', "missing_fields"),
        ('{"tool_name":"bash","arguments":{},"extra":true}', "unexpected_fields"),
        ('```json\n{"tool_name":"bash","arguments":{}}\n```', "malformed_json"),
    ],
)
def test_strict_json_proposal_fails_closed(
    proposal: str,
    error_code: str,
) -> None:
    with pytest.raises(ProposalNormalizationError, match=error_code):
        normalize_proposal(
            ProposalEnvelope(proposal_format="strict_json", **TRUSTED),
            proposal,
        )


@pytest.mark.parametrize(
    ("proposal", "error_code"),
    [
        ([], "action_count"),
        (
            [
                {
                    "type": "function",
                    "function": {"name": "bash", "arguments": "{}"},
                },
                {
                    "type": "function",
                    "function": {"name": "bash", "arguments": "{}"},
                },
            ],
            "action_count",
        ),
        (
            [{"type": "text", "function": {"name": "bash", "arguments": "{}"}}],
            "invalid_call_type",
        ),
        (
            [
                {
                    "unexpected": True,
                    "type": "function",
                    "function": {"name": "bash", "arguments": "{}"},
                }
            ],
            "unexpected_fields",
        ),
        (
            [
                {
                    "id": 7,
                    "type": "function",
                    "function": {"name": "bash", "arguments": "{}"},
                }
            ],
            "invalid_provider_call_id",
        ),
        (
            [
                {
                    "type": "function",
                    "function": {"name": "bash", "arguments": []},
                }
            ],
            "invalid_json_transport",
        ),
        (
            [
                {
                    "type": "function",
                    "function": {"name": "bash", "arguments": "[]"},
                }
            ],
            "invalid_json_root",
        ),
    ],
)
def test_native_tool_call_proposal_fails_closed(
    proposal: object,
    error_code: str,
) -> None:
    with pytest.raises(ProposalNormalizationError, match=error_code):
        normalize_proposal(
            ProposalEnvelope(proposal_format="native_tool_calls", **TRUSTED),
            proposal,
        )


def test_unknown_tool_is_rejected_before_an_action_is_created() -> None:
    with pytest.raises(ProposalNormalizationError, match="unknown_tool"):
        normalize_proposal(
            ProposalEnvelope(proposal_format="strict_json", **TRUSTED),
            '{"tool_name":"future.domain.tool","arguments":{}}',
        )


def test_native_provider_id_is_accepted_but_cannot_override_trusted_action_id() -> None:
    action = normalize_proposal(
        ProposalEnvelope(proposal_format="native_tool_calls", **TRUSTED),
        [
            {
                "id": "untrusted-provider-call-id",
                "type": "function",
                "function": {"name": "bash", "arguments": "{}"},
            }
        ],
    )

    assert action.action_id == TRUSTED["action_id"]
    assert "untrusted-provider-call-id" not in action.to_document().values()


@pytest.mark.parametrize(
    ("proposal_format", "proposal"),
    [
        (
            "strict_json",
            '{"tool_name":"bash","arguments":{"value":1e999}}',
        ),
        (
            "native_tool_calls",
            [
                {
                    "type": "function",
                    "function": {
                        "name": "bash",
                        "arguments": '{"value":1e999}',
                    },
                }
            ],
        ),
    ],
)
def test_numeric_overflow_is_a_classified_proposal_rejection(
    proposal_format: ProposalFormat,
    proposal: object,
) -> None:
    with pytest.raises(ProposalNormalizationError, match="invalid_number"):
        normalize_proposal(
            ProposalEnvelope(
                proposal_format=proposal_format,
                **TRUSTED,
            ),
            proposal,
        )


@pytest.mark.parametrize(
    "factory",
    [
        lambda: ProposalEnvelope(
            proposal_format="strict_json",
            **{**TRUSTED, "action_id": ""},
        ),
        lambda: ProposalEnvelope(
            proposal_format="strict_json",
            **{**TRUSTED, "source_backend": ""},
        ),
        lambda: ProposalEnvelope(
            proposal_format="strict_json",
            **{**TRUSTED, "candidate_tree_sha256": "not-a-sha256"},
        ),
        lambda: ProposalEnvelope(
            proposal_format="strict_json",
            **{**TRUSTED, "accepted_tool_names": frozenset({""})},
        ),
    ],
)
def test_trusted_proposal_envelope_rejects_invalid_identity(
    factory: Callable[[], ProposalEnvelope],
) -> None:
    with pytest.raises((TypeError, ValueError)):
        factory()
