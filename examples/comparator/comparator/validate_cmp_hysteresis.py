"""Validate cmp_hysteresis: differential hysteresis comparator.

Expected:
  - OUTP stays LOW before the upward threshold crossing.
  - OUTP stays HIGH in the middle of the sweep after the rising trip point.
  - OUTP returns LOW only after the lower threshold is crossed on the way down.
"""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / "output" / "comparator" / "cmp_hysteresis"
_VTH = 0.45


def _first_crossing(t: np.ndarray, y: np.ndarray, thresh: float, rising: bool) -> float | None:
    for idx in range(1, len(y)):
        if rising and y[idx - 1] < thresh <= y[idx]:
            return float(t[idx])
        if (not rising) and y[idx - 1] > thresh >= y[idx]:
            return float(t[idx])
    return None


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / "tran.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
    failures = 0

    t_ns = data["time"] * 1e9
    out_p = data["out_p"]

    pre = out_p[t_ns < 20.0]
    mid = out_p[(t_ns > 35.0) & (t_ns < 60.0)]
    post = out_p[t_ns > 75.0]

    if len(pre) == 0 or (pre < _VTH).mean() < 0.95:
        print("FAIL: OUTP not stably LOW before upward trip")
        failures += 1
    if len(mid) == 0 or (mid > _VTH).mean() < 0.95:
        print("FAIL: OUTP not stably HIGH in hysteresis hold window")
        failures += 1
    if len(post) == 0 or (post < _VTH).mean() < 0.95:
        print("FAIL: OUTP not back LOW after downward trip")
        failures += 1

    rise_t = _first_crossing(t_ns, out_p, _VTH, rising=True)
    fall_t = _first_crossing(t_ns, out_p, _VTH, rising=False)
    if rise_t is None or not (29.0 <= rise_t <= 31.5):
        print(f"FAIL: rising threshold crossing at {rise_t} ns (expected about 30 ns)")
        failures += 1
    if fall_t is None or not (68.5 <= fall_t <= 71.5):
        print(f"FAIL: falling threshold crossing at {fall_t} ns (expected about 70 ns)")
        failures += 1

    if failures == 0:
        print(f"[CSV] All assertions passed. (rise_t={rise_t:.3f}ns, fall_t={fall_t:.3f}ns)")
    return failures


if __name__ == "__main__":
    raise SystemExit(0 if validate_csv() == 0 else 1)
