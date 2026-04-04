"""Validate xor_phase_detector: XOR phase detector.

Testbench: REF 50MHz, DIV 50MHz with 2.5ns delay (90-degree phase shift).
Expected:
  - pd_out toggles actively (not stuck)
  - average duty cycle of pd_out is between 30% and 70% (near 50% for 90-deg shift)
  - at least 15 transitions observed over 200ns
"""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'xor_phase_detector'


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0

    vdd = data['ref'].max()
    vth = vdd * 0.5
    pd  = data['pd_out']

    hi_frac = (pd > vth).mean()
    if hi_frac < 0.10:
        print(f"FAIL: pd_out stuck LOW (high_frac={hi_frac:.2%})")
        failures += 1
    if hi_frac > 0.90:
        print(f"FAIL: pd_out stuck HIGH (high_frac={hi_frac:.2%})")
        failures += 1

    binary = (pd > vth).astype(int)
    transitions = int(np.sum(np.abs(np.diff(binary))))
    if transitions < 15:
        print(f"FAIL: only {transitions} transitions (expected >= 15)")
        failures += 1

    # For 90-deg phase shift on 50% duty-cycle clock, XOR duty = 50%
    if not (0.30 <= hi_frac <= 0.70):
        print(f"FAIL: duty cycle {hi_frac:.1%} outside [30%, 70%] for 90-deg phase shift")
        failures += 1

    if failures == 0:
        print(f"[CSV] All assertions passed. (duty={hi_frac:.1%}, {transitions} transitions)")
    return failures


if __name__ == '__main__':
    raise SystemExit(0 if validate_csv() == 0 else 1)
