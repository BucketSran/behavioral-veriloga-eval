"""Validate mux_4to1: 4-to-1 Multiplexer.

Testbench: D0=0.1V, D1=0.3V, D2=0.6V, D3=0.8V (constant).
Select walks: SEL=0 (0-100ns), SEL=1 (100-200ns), SEL=2 (200-300ns), SEL=3 (300-400ns).
Expected output voltage at midpoint of each window:
  t=50ns  -> ~0.1V (D0)
  t=150ns -> ~0.3V (D1)
  t=250ns -> ~0.6V (D2)
  t=350ns -> ~0.8V (D3)
Tolerance: 20mV.
"""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'mux_4to1'

EXPECTED = [
    (50e-9,  0.1, "SEL=0 -> D0"),
    (150e-9, 0.3, "SEL=1 -> D1"),
    (250e-9, 0.6, "SEL=2 -> D2"),
    (350e-9, 0.8, "SEL=3 -> D3"),
]
TOL = 20e-3


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0
    t = data['time']
    y = data['y']

    for t_check, expected_v, label in EXPECTED:
        # Average output over a 20ns window centred on t_check
        mask = (t >= t_check - 10e-9) & (t <= t_check + 10e-9)
        if not mask.any():
            print(f"FAIL [{label}]: no samples near t={t_check*1e9:.0f}ns")
            failures += 1
            continue
        measured = y[mask].mean()
        if abs(measured - expected_v) > TOL:
            print(f"FAIL [{label}]: measured {measured:.4f}V, expected {expected_v:.4f}V "
                  f"(err={abs(measured-expected_v)*1e3:.1f} mV > {TOL*1e3:.0f} mV)")
            failures += 1

    if failures == 0:
        print("[CSV] All assertions passed. (4/4 select windows correct)")
    return failures


if __name__ == '__main__':
    raise SystemExit(0 if validate_csv() == 0 else 1)
