"""Task-specific checker for canonical v4 DUT 053."""
from __future__ import annotations

from ..api import Checker
def check_v3_495_slew_rate_dac4(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "d3", "d2", "d1", "d0", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing slew-rate dac4 signals"
    expected = 0.0
    last_t = rows[0]["time"]
    max_err = 0.0
    max_endpoint_err = 0.0
    checked = 0
    ramp_checks = 0
    seen_codes: set[int] = set()
    settled_codes: set[int] = set()
    code_transitions = 0
    previous_code: int | None = None
    for row in rows[1:]:
        code = 0
        code += 8 if row["d3"] > 0.45 else 0
        code += 4 if row["d2"] > 0.45 else 0
        code += 2 if row["d1"] > 0.45 else 0
        code += 1 if row["d0"] > 0.45 else 0
        seen_codes.add(code)
        if previous_code is not None and code != previous_code:
            code_transitions += 1
        previous_code = code
        target = code / 15.0
        dt = max(0.0, row["time"] - last_t)
        step = 1e8 * dt
        if expected < target:
            expected = min(target, expected + step)
        elif expected > target:
            expected = max(target, expected - step)
        last_t = row["time"]
        if row["time"] < 0.5e-9:
            continue
        err = abs(row["vout"] - expected)
        max_err = max(max_err, err)
        checked += 1
        if abs(expected - target) >= 0.003:
            ramp_checks += 1
        if abs(expected - target) < 0.003:
            settled_codes.add(code)
        if abs(expected - target) < 0.003 and code in {0, 3, 6, 12, 15}:
            endpoint_err = abs(row["vout"] - target)
            max_endpoint_err = max(max_endpoint_err, endpoint_err)
    if checked == 0:
        return False, "insufficient_slew_samples=0"
    if len(seen_codes) < 3 or code_transitions < 2 or not {0, 15}.issubset(seen_codes):
        return False, (
            "insufficient_code_excitation="
            f"codes={sorted(seen_codes)},transitions={code_transitions},"
            "required=code0_code15_and_one_intermediate"
        )
    binary_discriminators = {code for code in settled_codes if code not in {0, 6, 9, 15}}
    if not {0, 15}.issubset(settled_codes) or not binary_discriminators:
        return False, (
            "insufficient_settled_code_coverage="
            f"settled={sorted(settled_codes)},required=endpoints_and_bit_order_discriminator"
        )
    if ramp_checks < 1:
        return False, f"insufficient_ramp_observation={ramp_checks}"
    if max_err > 0.075:
        return False, f"max_slew_error={max_err:.4f}"
    if max_endpoint_err > 0.020:
        return False, f"max_endpoint_error={max_endpoint_err:.4f}"
    return True, (
        f"slew_samples={checked} settled_codes={sorted(settled_codes)} ramp_checks={ramp_checks} "
        f"max_err={max_err:.4f} max_endpoint_err={max_endpoint_err:.4f}"
    )

CHECKER_ID = "v4_053_slew_rate_dac4"
CHECKER: Checker = check_v3_495_slew_rate_dac4
