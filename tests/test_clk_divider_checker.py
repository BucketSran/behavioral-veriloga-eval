from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

import simulate_evas as sim  # noqa: E402


def _rows_for_clk_divider(rise_times: list[float], lock_rise: float = 14.0) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for step in range(0, 61):
        t = step * 0.5
        clk_phase = t % 1.0
        clk_in = 0.9 if 0.0 < clk_phase <= 0.5 else 0.0
        clk_out = 0.0
        for rise_t in rise_times:
            if rise_t < t <= rise_t + 1.0:
                clk_out = 0.9
                break
        rows.append(
            {
                "time": t,
                "clk_in": clk_in,
                "clk_out": clk_out,
                "lock": 0.9 if t >= lock_rise else 0.0,
                "div_code_0": 0.9,
                "div_code_1": 0.0,
                "div_code_2": 0.9,
                "div_code_3": 0.0,
                "div_code_4": 0.0,
                "div_code_5": 0.0,
                "div_code_6": 0.0,
                "div_code_7": 0.0,
            }
        )
    return rows


def test_clk_divider_checker_accepts_exact_ratio_periods() -> None:
    rows = _rows_for_clk_divider([4.0, 9.0, 14.0])

    ok, note = sim.check_clk_divider(rows)

    assert ok
    assert "ratio_code=5" in note
    assert "period_match=1.000" in note


def test_clk_divider_checker_rejects_mixed_periods_even_if_average_ratio_matches() -> None:
    rows = _rows_for_clk_divider([4.0, 8.0, 14.0])

    ok, note = sim.check_clk_divider(rows)

    assert not ok
    assert "ratio_code=5" in note
    assert "period_match=" in note
