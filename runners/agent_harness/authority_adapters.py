"""Runtime adapters that enforce public/final evaluation authority profiles."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .authority_profiles import (
    final_test_profile_sha256,
    profile_input_identity_sha256,
)
from .result_artifact import (
    score_sidecar_sha256,
    validate_score_sidecar_authority,
)
from .state import EpisodeContext, FinalJudgment, FrozenSubmission


class AuthorityAdapterError(RuntimeError):
    """A classified lifecycle failure at an evaluation authority boundary."""


@dataclass(frozen=True, slots=True)
class FinalTestExecution:
    """Trusted final-judge output before authority validation."""

    judgment: FinalJudgment
    score_sidecar: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.judgment, FinalJudgment):
            raise TypeError("judgment must be a FinalJudgment")
        if not isinstance(self.score_sidecar, Mapping):
            raise TypeError("score_sidecar must be a JSON object")


FinalTestExecutor = Callable[
    [FrozenSubmission, dict[str, Any]],
    FinalTestExecution,
]


class ProfileBoundFinalJudge:
    """Run one final test against a frozen, detached authority profile."""

    def __init__(
        self,
        *,
        context: EpisodeContext,
        final_test_profile: Mapping[str, Any],
        execute: FinalTestExecutor,
    ) -> None:
        if not isinstance(context, EpisodeContext):
            raise TypeError("context must be an EpisodeContext")
        if not callable(execute):
            raise TypeError("execute must be callable")
        profile = deepcopy(dict(final_test_profile))
        profile_sha256 = final_test_profile_sha256(profile)
        self._context = context
        self._profile = profile
        self._profile_sha256 = profile_sha256
        self._execute = execute
        self._invoked = False
        self._profile_input_identity_sha256: str | None = None
        self._score_sidecar: dict[str, Any] | None = None
        self._score_sidecar_sha256: str | None = None

    @property
    def final_test_profile_sha256(self) -> str:
        return self._profile_sha256

    @property
    def profile_input_identity_sha256(self) -> str | None:
        return self._profile_input_identity_sha256

    @property
    def score_sidecar(self) -> dict[str, Any] | None:
        return deepcopy(self._score_sidecar)

    @property
    def score_sidecar_sha256(self) -> str | None:
        return self._score_sidecar_sha256

    def judge(self, submission: FrozenSubmission) -> FinalJudgment:
        """Run exactly one trusted final invocation against a frozen tree."""
        if self._invoked:
            raise AuthorityAdapterError("final judge adapter was already invoked")
        if not isinstance(submission, FrozenSubmission):
            raise TypeError("submission must be a FrozenSubmission")
        self._invoked = True
        execution = self._execute(submission, deepcopy(self._profile))
        if not isinstance(execution, FinalTestExecution):
            raise TypeError("final executor must return FinalTestExecution")
        sidecar = validate_score_sidecar_authority(
            score_sidecar=execution.score_sidecar,
            final_test_profile=self._profile,
            judgment=execution.judgment,
            submission=submission,
        )
        detached_sidecar = deepcopy(dict(sidecar))
        sidecar_sha256 = score_sidecar_sha256(detached_sidecar)
        input_identity_sha256 = profile_input_identity_sha256(
            profile_sha256=self._profile_sha256,
            input_kind="frozen_submission_tree",
            input_sha256=submission.tree_sha256,
            attempt_id=self._context.attempt_id,
            task_id=self._context.task_id,
        )
        self._score_sidecar = detached_sidecar
        self._score_sidecar_sha256 = sidecar_sha256
        self._profile_input_identity_sha256 = input_identity_sha256
        return execution.judgment
