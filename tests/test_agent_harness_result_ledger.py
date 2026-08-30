from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "operations"
    / "calibration_pilot"
    / "result_ledger.py"
)
SPEC = importlib.util.spec_from_file_location("result_ledger_test_module", MODULE_PATH)
assert SPEC and SPEC.loader
result_ledger = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(result_ledger)
CALIBRATION = ROOT / "benchmark-vabench-release-v4" / "operations" / "calibration_pilot"
if str(CALIBRATION) not in sys.path:
    sys.path.insert(0, str(CALIBRATION))
BUILD_SPEC = importlib.util.spec_from_file_location(
    "result_ledger_build_campaign_test_module",
    CALIBRATION / "build_campaign.py",
)
assert BUILD_SPEC and BUILD_SPEC.loader
build_campaign_module = importlib.util.module_from_spec(BUILD_SPEC)
BUILD_SPEC.loader.exec_module(build_campaign_module)

SHA_A = "a" * 64
SHA_B = "b" * 64


def _campaign() -> dict:
    cells = []
    for arm in ("OneShot", "Agent-No-EVAS", "Agentic"):
        cells.append(
            {
                "cell_id": f"v4-001-dut-m0-r0-{arm}",
                "task_id": "v4-001",
                "family_id": "001",
                "form": "dut",
                "experimental_arm": arm,
                "model": "fixture-model",
                "repetition": 0,
                "mode": "G0" if arm == "OneShot" else "G2",
                "prompt": "do not leak this prompt",
            }
        )
    return {
        "schema_version": "fixture-campaign",
        "campaign_id": "fixture-campaign",
        "cells": cells,
        "execution_config": {
            "episode_backend": "native-mini-swe",
            "native_retry_policy": {"max_attempts": 2},
        },
    }


def _row(cell: dict, *, score: int | None, status: str, attempts: list[dict] | None = None) -> dict:
    row = {
        **{key: cell[key] for key in (
            "cell_id",
            "task_id",
            "family_id",
            "form",
            "mode",
            "experimental_arm",
        )},
        "backend": "native-mini-swe",
        "attempt_id": attempts[-1]["attempt_id"] if attempts else f"{cell['cell_id']}-attempt-0001",
        "submission_status": "submitted" if score is not None else "not_submitted",
        "judge_status": status,
        "terminal_reason": "submitted" if score is not None else status,
        "termination_reason": "submitted" if score is not None else status,
        "score": score,
        "output_tokens": 10 if score is not None else None,
        "metering": {
            "provider": {
                "requests": 1,
                "usage": {"completion_tokens": 10 if score is not None else None},
            },
            "tools": {"requests": 2},
        },
        "evas_usage": {"calls_executed": 1 if score is not None else 0},
        "trusted_replay": {
            "final_test_profile": {
                "score_sidecar_contract": {"score_authority": "development_only"}
            },
            "derived_score_sidecar_reference": {"sha256": SHA_A},
        },
        "native_evidence": {
            "files": {"runtime_sha256": SHA_B},
            "artifact_sha256": SHA_A,
        },
        "raw_output": "do not leak raw output",
    }
    for key in ("model", "repetition"):
        if key in cell:
            row[key] = cell[key]
    if attempts is not None:
        row["attempt_sequence"] = {
            "schema_version": "vaevas-native-attempt-sequence-v1",
            "selection_sha256": SHA_B,
            "attempts": attempts,
        }
        row["attempt_count"] = len(attempts)
    return row


def _attempt(attempt_id: str, *, provider_requests: int | None, output_tokens: int | None) -> dict:
    return {
        "attempt_id": attempt_id,
        "retry_index": 0,
        "parent_attempt_id": None,
        "retry_reason": None,
        "primary_outcome": "passed",
        "terminal_reason": "submitted",
        "native_row_sha256": SHA_A,
        "costs": {
            "provider_requests": provider_requests,
            "tool_requests": 2,
            "output_tokens": output_tokens,
            "evas_invocations": 1,
        },
    }


def test_native_campaign_ledger_projects_safe_rows_and_cost_missingness() -> None:
    campaign = _campaign()
    attempts = [
        _attempt("attempt-1", provider_requests=1, output_tokens=4),
        _attempt("attempt-2", provider_requests=None, output_tokens=None),
    ]
    rows = [
        _row(campaign["cells"][0], score=0, status="behavior_failure"),
        _row(campaign["cells"][1], score=1, status="passed", attempts=attempts),
        _row(campaign["cells"][2], score=1, status="passed"),
    ]

    ledger = result_ledger.build_native_campaign_ledger(
        campaign,
        rows,
        campaign_file_sha256=SHA_A,
    )

    assert ledger["schema_version"] == "vabench-native-campaign-ledger-v1"
    assert ledger["source"]["campaign_file_sha256"] == SHA_A
    assert ledger["source"]["row_count"] == 3
    assert ledger["denominator"] == {
        "scheduled_cells": 3,
        "observed_rows": 3,
        "eligible_actual_score_cells": 3,
        "infrastructure_failure_cells": 0,
        "null_infra_denominator": 3,
    }
    assert ledger["claim_index"]["model_quality_claim"] == {
        "allowed": False,
        "reason": "ledger projection only; no formal/model-quality claim is generated",
    }
    assert ledger["claim_index"]["development_only"]["allowed"] is True
    assert ledger["claim_index"]["connectivity_only"]["allowed"] is False
    assert ledger["claim_index"]["realrununknown"]["allowed"] is False
    selected = ledger["records"][1]["selected_attempt"]
    assert selected["attempt_id"] == "attempt-2"
    assert ledger["records"][1]["backend"] == "native-mini-swe"
    assert ledger["records"][1]["identity_sources"] == {
        "model": "row",
        "repetition": "row",
    }
    assert ledger["records"][1]["attempt_costs"] == {
        "attempts": [
            {
                "attempt_id": "attempt-1",
                "costs": {
                    "provider_requests": 1,
                    "tool_requests": 2,
                    "output_tokens": 4,
                    "evas_invocations": 1,
                },
            },
            {
                "attempt_id": "attempt-2",
                "costs": {
                    "provider_requests": None,
                    "tool_requests": 2,
                    "output_tokens": None,
                    "evas_invocations": 1,
                },
            },
        ],
        "totals": {
            "provider_requests": None,
            "provider_requests_known_subtotal": 1,
            "provider_requests_unknown_count": 1,
            "tool_requests": 4,
            "tool_requests_known_subtotal": 4,
            "tool_requests_unknown_count": 0,
            "output_tokens": None,
            "output_tokens_known_subtotal": 4,
            "output_tokens_unknown_count": 1,
            "evas_invocations": 2,
            "evas_invocations_known_subtotal": 2,
            "evas_invocations_unknown_count": 0,
        },
    }
    dumped = json.dumps(ledger, sort_keys=True)
    assert "do not leak this prompt" not in dumped
    assert "do not leak raw output" not in dumped


def test_native_campaign_ledger_reports_three_arm_paired_delta_and_infra_gap() -> None:
    campaign = _campaign()
    rows = [
        _row(campaign["cells"][0], score=0, status="behavior_failure"),
        _row(campaign["cells"][1], score=None, status="infrastructure_failure"),
        _row(campaign["cells"][2], score=1, status="passed"),
    ]

    ledger = result_ledger.build_native_campaign_ledger(
        campaign,
        rows,
        campaign_file_sha256=SHA_A,
    )

    assert ledger["denominator"]["scheduled_cells"] == 3
    assert ledger["denominator"]["infrastructure_failure_cells"] == 1
    assert ledger["denominator"]["null_infra_denominator"] is None
    assert ledger["deadline_terminal_stats"] == {
        "deadline_primary": 0,
        "post_deadline": 0,
        "non_deadline_terminal": 3,
    }
    key = "native-mini-swe|v4-001|dut|fixture-model|0"
    assert ledger["paired_coverage"][key] == {
        "present_arms": ["Agent-No-EVAS", "Agentic", "OneShot"],
        "eligible_arms": ["Agentic", "OneShot"],
        "missing_arms": [],
        "ineligible_arms": {"Agent-No-EVAS": "infrastructure_failure"},
        "complete_three_arm_actual_score": False,
        "deltas": {
            "Agentic_minus_OneShot": 1,
            "Agentic_minus_Agent-No-EVAS": None,
            "Agent-No-EVAS_minus_OneShot": None,
        },
    }
    assert ledger["unmatched_reasons"] == {
        "ineligible_actual_score": {"infrastructure_failure": 1},
        "missing_arm": {},
    }


def test_native_campaign_ledger_separates_deadline_primary_and_post_deadline() -> None:
    campaign = _campaign()
    rows = [
        _row(campaign["cells"][0], score=0, status="behavior_failure"),
        _row(campaign["cells"][1], score=None, status="agent_timeout"),
        _row(campaign["cells"][2], score=1, status="passed"),
    ]
    rows[1]["terminal_reason"] = "deadline_expired"
    rows[2]["deadline_bucket"] = "post_deadline"

    ledger = result_ledger.build_native_campaign_ledger(
        campaign,
        rows,
        campaign_file_sha256=SHA_A,
    )

    assert ledger["deadline_terminal_stats"] == {
        "deadline_primary": 1,
        "post_deadline": 1,
        "non_deadline_terminal": 1,
    }


@pytest.mark.parametrize("drift", ["missing", "duplicate", "extra", "identity"])
def test_native_campaign_ledger_rejects_schedule_drift(drift: str) -> None:
    campaign = _campaign()
    rows = [
        _row(campaign["cells"][0], score=0, status="behavior_failure"),
        _row(campaign["cells"][1], score=1, status="passed"),
        _row(campaign["cells"][2], score=1, status="passed"),
    ]
    if drift == "missing":
        rows.pop()
    elif drift == "duplicate":
        rows[-1] = dict(rows[0])
    elif drift == "extra":
        rows.append({**rows[0], "cell_id": "extra"})
    else:
        rows[0]["form"] = "bugfix"

    with pytest.raises(ValueError, match="scheduled"):
        result_ledger.build_native_campaign_ledger(
            campaign,
            rows,
            campaign_file_sha256=SHA_A,
        )


def test_native_campaign_ledger_rejects_non_structural_or_invalid_fields() -> None:
    campaign = _campaign()
    rows = [_row(cell, score=1, status="passed") for cell in campaign["cells"]]
    rows[0]["score"] = True

    with pytest.raises(ValueError, match="score"):
        result_ledger.build_native_campaign_ledger(
            campaign,
            rows,
            campaign_file_sha256=SHA_A,
        )


def test_native_campaign_ledger_classifies_unknown_authority_without_claims() -> None:
    campaign = _campaign()
    rows = [_row(cell, score=1, status="passed") for cell in campaign["cells"]]
    rows[0].pop("trusted_replay")

    ledger = result_ledger.build_native_campaign_ledger(
        campaign,
        rows,
        campaign_file_sha256=SHA_A,
    )

    assert ledger["claim_index"]["development_only"]["allowed"] is False
    assert ledger["claim_index"]["realrununknown"]["allowed"] is True
    assert ledger["records"][0]["actual_score_eligible"] is False
    assert ledger["records"][0]["actual_score_ineligible_reason"] == "score_authority_unknown"
    assert ledger["claim_index"]["model_quality_claim"]["allowed"] is False


@pytest.mark.parametrize("arm", ["One-shot", "Agentic+EVAS", "Evolution"])
def test_native_campaign_ledger_rejects_non_single_trajectory_conditions(
    arm: str,
) -> None:
    campaign = _campaign()
    campaign["cells"][0]["experimental_arm"] = arm
    campaign["cells"][0]["cell_id"] = f"bad-{arm}"
    rows = [_row(cell, score=1, status="passed") for cell in campaign["cells"]]

    with pytest.raises(ValueError, match="experimental_arm"):
        result_ledger.build_native_campaign_ledger(
            campaign,
            rows,
            campaign_file_sha256=SHA_A,
        )


@pytest.mark.parametrize("backend", ["candidate-only", "Evolution", "legacy", None])
def test_native_campaign_ledger_rejects_unknown_or_candidate_only_backend(
    backend: str | None,
) -> None:
    campaign = _campaign()
    campaign["execution_config"].pop("episode_backend")
    rows = [_row(cell, score=1, status="passed") for cell in campaign["cells"]]
    if backend is None:
        rows[0].pop("backend")
    else:
        rows[0]["backend"] = backend

    with pytest.raises(ValueError, match="backend"):
        result_ledger.build_native_campaign_ledger(
            campaign,
            rows,
            campaign_file_sha256=SHA_A,
        )


def test_native_campaign_ledger_rejects_unannounced_mixed_backends() -> None:
    campaign = _campaign()
    campaign["execution_config"].pop("episode_backend")
    rows = [_row(cell, score=1, status="passed") for cell in campaign["cells"]]
    rows[1]["backend"] = "native-reasoning"

    with pytest.raises(ValueError, match="mixed backends"):
        result_ledger.build_native_campaign_ledger(
            campaign,
            rows,
            campaign_file_sha256=SHA_A,
        )


def test_native_campaign_ledger_binds_campaign_episode_backend_when_present() -> None:
    campaign = _campaign()
    campaign["execution_config"]["episode_backend"] = "native-reasoning"
    rows = [_row(cell, score=1, status="passed") for cell in campaign["cells"]]
    rows[0]["backend"] = "native-reasoning"
    rows[1]["backend"] = "native-reasoning"

    with pytest.raises(ValueError, match="episode_backend"):
        result_ledger.build_native_campaign_ledger(
            campaign,
            rows,
            campaign_file_sha256=SHA_A,
        )


def test_native_campaign_ledger_pairs_native_reasoning_backend_separately() -> None:
    campaign = _campaign()
    campaign["execution_config"]["episode_backend"] = "native-reasoning"
    rows = [_row(cell, score=1, status="passed") for cell in campaign["cells"]]
    for row in rows:
        row["backend"] = "native-reasoning"

    ledger = result_ledger.build_native_campaign_ledger(
        campaign,
        rows,
        campaign_file_sha256=SHA_A,
    )

    assert list(ledger["paired_coverage"]) == [
        "native-reasoning|v4-001|dut|fixture-model|0"
    ]


def test_native_campaign_ledger_accepts_actual_builder_campaign_rows_without_optional_metadata() -> None:
    campaign = build_campaign_module.build_campaign(
        build_campaign_module.DEFAULT_RELEASE,
        family_ids=["001"],
        seed=0,
        model_provider="openai-compatible",
        model="fixture-model",
        per_turn_max_tokens=128,
        repetitions=1,
        modes=None,
        three_arm_g0_g2=True,
    )
    assert "model" in campaign and "model" not in campaign["cells"][0]
    before = json.loads(json.dumps(campaign, sort_keys=True))
    rows = []
    for cell in campaign["cells"]:
        row = _row(cell, score=1, status="passed")
        row.pop("model", None)
        row.pop("repetition", None)
        rows.append(row)

    ledger = result_ledger.build_native_campaign_ledger(
        campaign,
        rows,
        campaign_file_sha256=SHA_A,
    )

    assert campaign == before
    assert ledger["denominator"]["scheduled_cells"] == 9
    assert ledger["records"][0]["identity"]["model"] == "fixture-model"
    assert ledger["records"][0]["identity"]["repetition"] == 0
    assert ledger["records"][0]["identity_sources"] == {
        "model": "campaign",
        "repetition": "campaign_cell",
    }
    assert set(ledger["paired_coverage"]) == {
        f"native-mini-swe|{cell['task_id']}|{cell['form']}|fixture-model|0"
        for cell in campaign["cells"]
    }


def test_native_campaign_ledger_rejects_row_model_or_repetition_drift_from_schedule() -> None:
    campaign = _campaign()
    rows = [_row(cell, score=1, status="passed") for cell in campaign["cells"]]
    rows[0]["model"] = "other-model"

    with pytest.raises(ValueError, match="scheduled row metadata mismatch"):
        result_ledger.build_native_campaign_ledger(
            campaign,
            rows,
            campaign_file_sha256=SHA_A,
        )

    rows = [_row(cell, score=1, status="passed") for cell in campaign["cells"]]
    rows[0]["repetition"] = 99
    with pytest.raises(ValueError, match="scheduled row metadata mismatch"):
        result_ledger.build_native_campaign_ledger(
            campaign,
            rows,
            campaign_file_sha256=SHA_A,
        )


@pytest.mark.parametrize("field", ["model", "repetition"])
def test_native_campaign_ledger_rejects_unidentifiable_pair_key(field: str) -> None:
    campaign = _campaign()
    for cell in campaign["cells"]:
        cell.pop(field)
    rows = [_row(cell, score=1, status="passed") for cell in campaign["cells"]]

    with pytest.raises(ValueError, match=field):
        result_ledger.build_native_campaign_ledger(
            campaign,
            rows,
            campaign_file_sha256=SHA_A,
        )
