"""Public interfaces for the vaEVAS agent harness."""

from .backend_profile import backend_profile_sha256
from .contracts import FinalJudge, PublicValidator
from .controller import EpisodeController
from .evolution_state import (
    CandidateLineage,
    MemorySnapshot,
    candidate_lineage_sha256,
    freeze_memory_snapshot,
    validate_candidate_lineage_graph,
)
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
from .tool_registry import (
    EffectiveToolset,
    ToolCapability,
    ToolRegistry,
    ToolRegistryError,
    tool_descriptor_sha256,
)
from .trajectory import (
    JsonlTrajectoryRecorder,
    project_model_visible_events,
    read_trajectory,
    validate_trajectory,
)

__all__ = [
    "AgentAction",
    "CandidateLineage",
    "EpisodeContext",
    "EpisodeController",
    "EpisodeResult",
    "EnvironmentStep",
    "EffectiveToolset",
    "EventVisibility",
    "FailureDisposition",
    "FinalJudge",
    "FinalJudgment",
    "FrozenSubmission",
    "Incident",
    "JsonlTrajectoryRecorder",
    "MemorySnapshot",
    "Observation",
    "ProposalEnvelope",
    "ProposalFormat",
    "ProposalNormalizationError",
    "PublicValidator",
    "ToolCapability",
    "ToolRegistry",
    "ToolRegistryError",
    "backend_profile_sha256",
    "candidate_lineage_sha256",
    "freeze_memory_snapshot",
    "normalize_proposal",
    "project_model_visible_events",
    "read_trajectory",
    "tool_descriptor_sha256",
    "validate_candidate_lineage_graph",
    "validate_trajectory",
]
