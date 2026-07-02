#!/usr/bin/env python3
"""Compatibility stub — ``run_adaptive_repair`` has moved to ``runners/legacy/``.

Its layered-repair policy + progress ranking has been absorbed into the
unified agent at ``runners/agent/`` (enable with ``config.loop.layered_repair``
or ``python -m runners.agent run --layered``). This stub preserves the old
import path for ``constrained_patch_repair.py`` and ``mechanical_patch_repair.py``,
which still import ``from run_adaptive_repair import ...`` (including private
helpers like ``_progress_rank`` and ``_classify_repair_layer``).
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
    "runners/run_adaptive_repair.py has moved to runners/legacy/ and its "
    "layered-repair feature is now in runners/agent/ (config.loop.layered_repair).",
    DeprecationWarning,
    stacklevel=2,
)

from legacy.run_adaptive_repair import *  # noqa: E402,F401,F403
# Re-export ALL public + private names (downstream consumers import private
# helpers like _progress_rank, _classify_repair_layer, _score_quick).
import legacy.run_adaptive_repair as _mod  # noqa: E402
for _name in dir(_mod):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_mod, _name)
del _mod

if __name__ == "__main__":
    from legacy.run_adaptive_repair import main
    raise SystemExit(main())
