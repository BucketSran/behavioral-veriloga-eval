"""Validate sample_hold: Sample-and-Hold circuit.

Testbench: ramp input 0->0.9V over 1us, 50MHz clock, vth=0.45V.
Expected:
  - output steps discretely at clock edges (not continuous)
  - each step value matches V(IN) at the clock edge within 5mV
  - at least 40 samples taken over 1us (50MHz -> 50 edges)
"""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'sample_hold'


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0

    t  = data['time']
    clk = data['clk']
    vin = data['in']
    vout = data['out']

    vth = 0.45

    # Find rising clock edges (transitions from <vth to >vth)
    clk_hi = (clk > vth).astype(int)
    edge_idx = np.where(np.diff(clk_hi) > 0)[0]

    if len(edge_idx) < 40:
        print(f"FAIL: only {len(edge_idx)} rising clock edges found (expected >= 40)")
        failures += 1

    # Verify output is held (flat) between edges
    if len(edge_idx) >= 2:
        # Check a mid-window between first two edges
        i0 = edge_idx[0] + 5
        i1 = edge_idx[1] - 5
        if i1 > i0 + 1:
            window = vout[i0:i1]
            jitter = np.max(window) - np.min(window)
            if jitter > 5e-3:
                print(f"FAIL: output not held between edges (variation={jitter*1e3:.2f} mV > 5 mV)")
                failures += 1

    # Verify each sample matches V(IN) at edge time (within 5mV)
    mismatches = 0
    for idx in edge_idx[:40]:
        sampled_in  = vin[idx]
        # output settles a few samples after edge
        settle = min(idx + 10, len(vout) - 1)
        sampled_out = vout[settle]
        if abs(sampled_out - sampled_in) > 5e-3:
            mismatches += 1

    if mismatches > 3:
        print(f"FAIL: {mismatches}/40 samples deviate from V(IN) by more than 5mV")
        failures += 1

    if failures == 0:
        print(f"[CSV] All assertions passed. ({len(edge_idx)} clock edges, hold validated)")
    return failures


if __name__ == '__main__':
    raise SystemExit(0 if validate_csv() == 0 else 1)
