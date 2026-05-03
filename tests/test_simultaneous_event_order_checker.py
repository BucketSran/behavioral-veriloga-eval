from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

import simulate_evas as sim  # noqa: E402


def test_simultaneous_event_order_checker_accepts_balanced_plateau_ramp() -> None:
    ok, note = sim._simultaneous_event_order_levels_ok([0.18, 0.36, 0.54, 0.72])

    assert ok
    assert "diffs=[0.18, 0.18, 0.18]" in note


def test_simultaneous_event_order_checker_rejects_exact_touch_artifact() -> None:
    ok, note = sim._simultaneous_event_order_levels_ok([0.6, 0.6, 0.6, 1.2])

    assert not ok
    assert "diffs=[0.0, 0.0, 0.6]" in note
