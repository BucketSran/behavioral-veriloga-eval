from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCORE_CAMPAIGN = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "operations"
    / "calibration_pilot"
    / "score_campaign.py"
)


def load_score_campaign():
    spec = importlib.util.spec_from_file_location("score_campaign_reuse_test", SCORE_CAMPAIGN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_trusted_replay_resume_requires_exact_nonretryable_signature() -> None:
    scorer = load_score_campaign()
    signature = {"schema_version": "test", "submission": "frozen"}
    signature_sha = scorer.canonical_sha256(signature)
    replay = {
        "status": "behavior_failure",
        "input_signature": signature,
        "input_signature_sha256": signature_sha,
        "failure_taxonomy": {"retryable": False},
    }

    assert scorer.trusted_replay_is_exactly_reusable(
        replay, signature, signature_sha
    )
    assert not scorer.trusted_replay_is_exactly_reusable(
        replay, {**signature, "submission": "changed"}, signature_sha
    )
    replay["failure_taxonomy"]["retryable"] = True
    assert not scorer.trusted_replay_is_exactly_reusable(
        replay, signature, signature_sha
    )


def test_outer_trusted_replay_watchdog_is_retryable_infrastructure() -> None:
    scorer = load_score_campaign()
    replay = {
        "status": "runtime_failure",
        "command": {"execution_status": "timeout"},
        "diagnostics": ["trusted_replay_timeout"],
    }

    scorer.normalize_trusted_replay_watchdog(replay)

    assert replay["status"] == "infrastructure_failure"
    assert replay["failure_taxonomy"]["stage"] == "infrastructure"
    assert replay["diagnostics"] == ["trusted_replay_watchdog_timeout"]
    assert replay["failure_taxonomy"]["secondary_classes"] == ["timeout"]
    assert replay["failure_taxonomy"]["responsibility"] == "system"
    assert replay["failure_taxonomy"]["retryable"] is True
