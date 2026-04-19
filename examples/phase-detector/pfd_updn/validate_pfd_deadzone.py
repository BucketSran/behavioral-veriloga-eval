"""Validate pfd_updn near deadzone behavior.

Testbench: REF leads DIV by only 100ps.
Expected:
  - UP pulses are present but short.
  - DN stays mostly LOW.
  - UP/DN overlap is not sustained.
"""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / "output" / "pfd_updn_deadzone"


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / "tran.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
    failures = 0

    vth = data["ref"].max() * 0.5
    up = (data["up"] > vth).astype(int)
    dn = (data["dn"] > vth).astype(int)

    up_frac = up.mean()
    dn_frac = dn.mean()
    both_hi = up & dn

    run_len = 0
    max_run = 0
    for bit in both_hi:
        if bit:
            run_len += 1
            max_run = max(max_run, run_len)
        else:
            run_len = 0

    up_pulses = int(np.sum(np.diff(up) > 0))

    if not (0.001 <= up_frac <= 0.03):
        print(f"FAIL: UP duty {up_frac:.3%} outside expected near-deadzone range")
        failures += 1
    if dn_frac > 0.002:
        print(f"FAIL: DN duty unexpectedly high ({dn_frac:.3%}) for REF-leading near-deadzone case")
        failures += 1
    if max_run > 6:
        print(f"FAIL: UP/DN overlap lasted {max_run} samples")
        failures += 1
    if up_pulses < 10:
        print(f"FAIL: only {up_pulses} UP pulses (expected >= 10)")
        failures += 1

    if failures == 0:
        print(f"[CSV] All assertions passed. (UP={up_frac:.3%}, DN={dn_frac:.3%}, pulses={up_pulses})")
    return failures


if __name__ == "__main__":
    raise SystemExit(0 if validate_csv() == 0 else 1)
