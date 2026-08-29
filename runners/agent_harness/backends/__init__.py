"""Backend compatibility surfaces for the generic agent harness."""

from .mini_swe import (
    MINI_SWE_BASH_HANDLER_ID,
    MiniSweBashEnvironmentBridge,
    MiniSwePolicyBridge,
    mini_swe_bash_tool_descriptor,
)

__all__ = [
    "MINI_SWE_BASH_HANDLER_ID",
    "MiniSweBashEnvironmentBridge",
    "MiniSwePolicyBridge",
    "mini_swe_bash_tool_descriptor",
]
