"""Public interfaces for the vaEVAS agent harness."""

from .backend_profile import backend_profile_sha256
from .contracts import FinalJudge, PublicValidator
from .controller import EpisodeController
from .proposals import (
    ProposalEnvelope,
    ProposalFormat,
    ProposalNormalizationError,
    normalize_proposal,
)
from .state import (
    AgentAction,
    EpisodeContext,
    EpisodeResult,
    EnvironmentStep,
    EventVisibility,
    FailureDisposition,
    FinalJudgment,
    FrozenSubmission,
    Incident,
    Observation,
)
from .trajectory import (
    JsonlTrajectoryRecorder,
    project_model_visible_events,
    read_trajectory,
    validate_trajectory,
)

__all__ = [
    "AgentAction",
    "EpisodeContext",
    "EpisodeController",
    "EpisodeResult",
    "EnvironmentStep",
    "EventVisibility",
    "FailureDisposition",
    "FinalJudge",
    "FinalJudgment",
    "FrozenSubmission",
    "Incident",
    "JsonlTrajectoryRecorder",
    "Observation",
    "ProposalEnvelope",
    "ProposalFormat",
    "ProposalNormalizationError",
    "PublicValidator",
    "backend_profile_sha256",
    "normalize_proposal",
    "project_model_visible_events",
    "read_trajectory",
    "validate_trajectory",
]
