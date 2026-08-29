from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from runners.agent_harness import (
    EpisodeContext,
    FinalJudgment,
    FinalTestExecution,
    FrozenSubmission,
    ProfileBoundFinalJudge,
    final_test_profile_sha256,
    profile_input_identity_sha256,
)
from runners.agent_harness.authority_adapters import AuthorityAdapterError

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64
SHA_F = "f" * 64


def _context() -> EpisodeContext:
    return EpisodeContext(
        episode_id="episode-001",
        attempt_id="attempt-001",
        task_id="v4-001",
        condition="Agentic+EVAS",
        max_steps=1,
    )


def _profile(**updates: Any) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "schema_version": "vaevas-final-test-profile-v1",
        "profile_id": "r53/evas-0.8.7-final-test",
        "benchmark_release": "benchmarkv4-r53",
        "benchmark_manifest_sha256": SHA_A,
        "judge": {"engine": "evas", "version": "0.8.7"},
        "judge_identity_sha256": SHA_B,
        "checker_identity_sha256": SHA_C,
        "runtime_identity_sha256": SHA_D,
        "campaign_config_sha256": SHA_E,
        "command_signature_sha256": SHA_F,
        "authority_phase": "post_submission_freeze_only",
        "visibility": "trusted_only",
        "model_observation_allowed": False,
        "memory_entry_allowed": False,
        "candidate_selection_allowed": False,
        "repair_allowed": False,
        "input_scope": "frozen_submission_tree",
        "submission_binding_required": True,
        "score_sidecar_required": True,
        "structured_result_contract": {
            "schema_id": "vaevas-structured-result-v1",
            "requires_structured_verdict": True,
        },
        "score_sidecar_contract": {
            "schema_id": "vaevas-score-sidecar-v1",
            "immutable": True,
            "binds_submission_tree": True,
            "score_authority": "development_only",
        },
        "spectre_policy": {
            "required": False,
            "trigger": "conditional_evas_or_external_protocol_change",
            "spectre_judge_identity_sha256": None,
            "spectre_command_signature_sha256": None,
            "spectre_report_schema_id": None,
        },
    }
    profile.update(updates)
    return profile


def _submission() -> FrozenSubmission:
    return FrozenSubmission(tree_sha256=SHA_A, artifacts=("model.va",))


def _judgment() -> FinalJudgment:
    return FinalJudgment(
        status="passed",
        judge_engine="evas",
        score=1.0,
        submission_tree_sha256=SHA_A,
    )


def _sidecar(**updates: Any) -> dict[str, Any]:
    sidecar: dict[str, Any] = {
        "schema_version": "vaevas-score-sidecar-v1",
        "benchmark_release": "benchmarkv4-r53",
        "benchmark_manifest_sha256": SHA_A,
        "score_authority": "development_only",
        "immutable": True,
        "binds_submission_tree": True,
        "submission_tree_sha256": SHA_A,
        "judge": {
            "engine": "evas",
            "version": "0.8.7",
            "identity_sha256": SHA_B,
        },
        "checker_identity_sha256": SHA_C,
        "runtime_identity_sha256": SHA_D,
        "campaign_config_sha256": SHA_E,
        "command_signature_sha256": SHA_F,
        "structured_result": {"status": "passed", "score": 1.0},
        "model_observation_allowed": False,
        "memory_entry_allowed": False,
    }
    sidecar.update(updates)
    return sidecar


def test_profile_bound_final_judge_binds_submission_profile_and_sidecar() -> None:
    calls: list[str] = []

    def execute(
        submission: FrozenSubmission,
        profile: dict[str, Any],
    ) -> FinalTestExecution:
        calls.append(submission.tree_sha256)
        assert profile["profile_id"] == "r53/evas-0.8.7-final-test"
        profile["profile_id"] = "executor-local-mutation"
        return FinalTestExecution(judgment=_judgment(), score_sidecar=_sidecar())

    profile = _profile()
    adapter = ProfileBoundFinalJudge(
        context=_context(),
        final_test_profile=profile,
        execute=execute,
    )
    profile["profile_id"] = "caller-mutation"

    judgment = adapter.judge(_submission())

    assert judgment == _judgment()
    assert calls == [SHA_A]
    assert adapter.final_test_profile_sha256 == final_test_profile_sha256(
        _profile()
    )
    assert adapter.profile_input_identity_sha256 == profile_input_identity_sha256(
        profile_sha256=adapter.final_test_profile_sha256,
        input_kind="frozen_submission_tree",
        input_sha256=SHA_A,
        attempt_id="attempt-001",
        task_id="v4-001",
    )
    detached = adapter.score_sidecar
    detached["structured_result"]["status"] = "tampered"
    assert adapter.score_sidecar["structured_result"]["status"] == "passed"
    assert len(adapter.score_sidecar_sha256) == 64


def test_final_judge_adapter_is_single_use_even_after_executor_failure() -> None:
    def fail(
        submission: FrozenSubmission,
        profile: dict[str, Any],
    ) -> FinalTestExecution:
        del submission, profile
        raise RuntimeError("judge unavailable")

    adapter = ProfileBoundFinalJudge(
        context=_context(),
        final_test_profile=_profile(),
        execute=fail,
    )

    with pytest.raises(RuntimeError, match="judge unavailable"):
        adapter.judge(_submission())
    with pytest.raises(AuthorityAdapterError, match="already invoked"):
        adapter.judge(_submission())


@pytest.mark.parametrize(
    ("profile_updates", "sidecar_updates", "message"),
    [
        ({}, {"checker_identity_sha256": SHA_D}, "checker_identity_sha256"),
        ({}, {"submission_tree_sha256": SHA_B}, "submission_tree_sha256"),
        ({}, {"score_authority": "formal"}, "score_authority"),
        (
            {
                "score_sidecar_contract": {
                    "schema_id": "future-score-sidecar-v2",
                    "immutable": True,
                    "binds_submission_tree": True,
                }
            },
            {},
            "score sidecar schema",
        ),
    ],
)
def test_final_judge_adapter_rejects_sidecar_authority_mismatch(
    profile_updates: dict[str, Any],
    sidecar_updates: dict[str, Any],
    message: str,
) -> None:
    profile = _profile(**deepcopy(profile_updates))

    def execute(
        submission: FrozenSubmission,
        received_profile: dict[str, Any],
    ) -> FinalTestExecution:
        del submission, received_profile
        return FinalTestExecution(
            judgment=_judgment(),
            score_sidecar=_sidecar(**deepcopy(sidecar_updates)),
        )

    adapter = ProfileBoundFinalJudge(
        context=_context(),
        final_test_profile=profile,
        execute=execute,
    )

    with pytest.raises(ValueError, match=message):
        adapter.judge(_submission())
    assert adapter.profile_input_identity_sha256 is None
    assert adapter.score_sidecar is None
    assert adapter.score_sidecar_sha256 is None


def test_legacy_final_profile_defaults_to_development_only_authority() -> None:
    profile = _profile()
    profile["score_sidecar_contract"].pop("score_authority")

    def execute(
        submission: FrozenSubmission,
        received_profile: dict[str, Any],
    ) -> FinalTestExecution:
        del submission, received_profile
        return FinalTestExecution(
            judgment=_judgment(),
            score_sidecar=_sidecar(score_authority="formal"),
        )

    adapter = ProfileBoundFinalJudge(
        context=_context(),
        final_test_profile=profile,
        execute=execute,
    )

    with pytest.raises(ValueError, match="score_authority"):
        adapter.judge(_submission())


def test_final_judge_accepts_formal_authority_only_when_profile_declares_it() -> None:
    profile = _profile(
        score_sidecar_contract={
            "schema_id": "vaevas-score-sidecar-v1",
            "immutable": True,
            "binds_submission_tree": True,
            "score_authority": "formal",
        }
    )

    def execute(
        submission: FrozenSubmission,
        received_profile: dict[str, Any],
    ) -> FinalTestExecution:
        del submission, received_profile
        return FinalTestExecution(
            judgment=_judgment(),
            score_sidecar=_sidecar(score_authority="formal"),
        )

    adapter = ProfileBoundFinalJudge(
        context=_context(),
        final_test_profile=profile,
        execute=execute,
    )

    assert adapter.judge(_submission()) == _judgment()
    assert adapter.score_sidecar["score_authority"] == "formal"
