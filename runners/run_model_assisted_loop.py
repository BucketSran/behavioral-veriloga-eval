#!/usr/bin/env python3
"""Compatibility stub — ``run_model_assisted_loop`` has moved to ``runners/legacy/``.

Its 8 experimental modes are now expressed as config knobs in the unified
agent at ``runners/agent/`` (``config.loop.prompt_mode`` × ``include_skill``
× ``max_rounds``). Run them via ``python -m runners.agent experiment``.
This stub preserves the old import path for ``constrained_patch_repair.py``
and ``mechanical_patch_repair.py``, which import helpers like
``_model_slug`` and ``_save_generated_response`` from here.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

_RUNNERS = Path(__file__).resolve().parent
if str(_RUNNERS) not in sys.path:
    sys.path.insert(0, str(_RUNNERS))
_LEGACY = _RUNNERS / "legacy"
if str(_LEGACY) not in sys.path:
    sys.path.insert(0, str(_LEGACY))

warnings.warn(
    "runners/run_model_assisted_loop.py has moved to runners/legacy/. Its 8 modes "
    "are now config-driven in runners/agent/ — use 'python -m runners.agent experiment'.",
    DeprecationWarning,
    stacklevel=2,
)

from legacy.run_model_assisted_loop import *  # noqa: E402,F401,F403
# Re-export ALL public + private names (downstream imports _model_slug,
# _save_generated_response, DEV24_TASK_IDS, etc.).
import legacy.run_model_assisted_loop as _mod  # noqa: E402
for _name in dir(_mod):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_mod, _name)
del _mod

if __name__ == "__main__":
    from legacy.run_model_assisted_loop import main
    raise SystemExit(main())
