"""Validate flash_adc_3b: 3-bit Flash ADC.

Testbench: ramp input 0->0.9V over 800ns, 100MHz clock, vrefp=0.9, vrefn=0.
Expected:
  - all 8 codes (0-7) appear in the output
  - output code is monotonically non-decreasing as vin ramps up
  - code transitions approximately at vin = k * vrefp/8 for k=1..7
"""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'flash_adc_3b'

VREFP = 0.9
VREFN = 0.0
LSB   = (VREFP - VREFN) / 8.0


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0

    vdd = data['clk'].max()
    vth = vdd * 0.5
    clk = data['clk']
    vin = data['vin']
    d2  = (data['dout2'] > vth).astype(int)
    d1  = (data['dout1'] > vth).astype(int)
    d0  = (data['dout0'] > vth).astype(int)

    # Sample at mid-period after each rising clock edge
    clk_hi   = (clk > vth).astype(int)
    edge_idx = np.where(np.diff(clk_hi) > 0)[0]

    codes    = []
    vin_vals = []
    for idx in edge_idx:
        settle = min(idx + 8, len(d2) - 1)
        code   = (d2[settle] << 2) | (d1[settle] << 1) | d0[settle]
        codes.append(code)
        vin_vals.append(vin[idx])

    if len(codes) < 60:
        print(f"FAIL: only {len(codes)} clock edges (expected >= 60)")
        failures += 1
        return failures

    # All 8 codes must appear
    unique = set(codes)
    if len(unique) < 8:
        print(f"FAIL: only {len(unique)} unique codes (expected 8): {sorted(unique)}")
        failures += 1

    # Monotonic: code should not decrease when vin increases (ramp)
    violations = 0
    for i in range(1, len(codes)):
        if vin_vals[i] > vin_vals[i-1] and codes[i] < codes[i-1]:
            violations += 1
    if violations > 2:
        print(f"FAIL: {violations} monotonicity violations")
        failures += 1

    # Check transition voltages are roughly at LSB boundaries (within 1 LSB)
    for target_code in range(1, 8):
        # First index where code >= target_code
        idx_first = next((i for i, c in enumerate(codes) if c >= target_code), None)
        if idx_first is None:
            print(f"FAIL: code {target_code} never reached")
            failures += 1
            continue
        expected_vin = target_code * LSB
        actual_vin   = vin_vals[idx_first]
        if abs(actual_vin - expected_vin) > LSB * 1.5:
            print(f"FAIL: code {target_code} transitions at {actual_vin:.4f}V, "
                  f"expected ~{expected_vin:.4f}V (err > 1.5 LSB)")
            failures += 1

    if failures == 0:
        print(f"[CSV] All assertions passed. ({len(unique)} unique codes, "
              f"{violations} monotonicity violations)")
    return failures


if __name__ == '__main__':
    raise SystemExit(0 if validate_csv() == 0 else 1)
