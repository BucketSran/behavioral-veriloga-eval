"""Validate pfd_updn: Phase-Frequency Detector.

Testbench: REF 50MHz, DIV 50MHz with 3ns lag (REF leads DIV).
Expected:
  - UP pulses appear (UP duty cycle > DN duty cycle, since REF leads)
  - UP and DN are never simultaneously high for long (reset logic works)
  - at least 10 UP pulses observed over 300ns
"""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'pfd_updn'


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0

    vdd = data['ref'].max()
    vth = vdd * 0.5
    up  = data['up']
    dn  = data['dn']

    up_hi = (up > vth).astype(int)
    dn_hi = (dn > vth).astype(int)

    # UP and DN should never be simultaneously high for long
    both_hi = up_hi & dn_hi
    # Allow a single-sample glitch (reset pulse); sustained overlap means bug
    run_len = 0
    max_run = 0
    for b in both_hi:
        if b:
            run_len += 1
            max_run = max(max_run, run_len)
        else:
            run_len = 0
    if max_run > 5:
        print(f"FAIL: UP and DN simultaneously high for {max_run} consecutive samples (reset failed)")
        failures += 1

    # REF leads DIV -> UP duty cycle should exceed DN duty cycle
    up_frac = up_hi.mean()
    dn_frac = dn_hi.mean()
    if up_frac < 0.01:
        print(f"FAIL: UP never high (up_frac={up_frac:.2%})")
        failures += 1

    if up_frac < dn_frac:
        print(f"FAIL: REF leads DIV but UP_frac ({up_frac:.2%}) < DN_frac ({dn_frac:.2%})")
        failures += 1

    # Count UP pulses
    up_pulses = int(np.sum(np.diff(up_hi) > 0))
    if up_pulses < 10:
        print(f"FAIL: only {up_pulses} UP pulses (expected >= 10)")
        failures += 1

    if failures == 0:
        print(f"[CSV] All assertions passed. (UP_frac={up_frac:.1%}, DN_frac={dn_frac:.1%}, "
              f"{up_pulses} UP pulses)")
    return failures


if __name__ == '__main__':
    raise SystemExit(0 if validate_csv() == 0 else 1)
