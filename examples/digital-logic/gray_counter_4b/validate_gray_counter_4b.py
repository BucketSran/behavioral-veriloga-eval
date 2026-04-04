"""Validate gray_counter_4b: 4-bit Gray Code Counter.

Testbench: 100MHz clock, reset deasserts at t=51ns, run 2us (covers full 16-state cycle x12).
Expected:
  - exactly 1 output bit changes per clock cycle (Gray code property)
  - all 16 Gray codes appear in the output
  - sequence repeats correctly (mod-16 wrap)
"""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'gray_counter_4b'


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0

    vdd = data['clk'].max()
    vth = vdd * 0.5
    clk = data['clk']
    g3  = (data['g3'] > vth).astype(int)
    g2  = (data['g2'] > vth).astype(int)
    g1  = (data['g1'] > vth).astype(int)
    g0  = (data['g0'] > vth).astype(int)

    # Sample gray code at mid-period after each rising clock edge
    clk_hi  = (clk > vth).astype(int)
    edge_idx = np.where(np.diff(clk_hi) > 0)[0]

    # Collect gray codes just after each edge (settle window)
    codes = []
    for idx in edge_idx:
        settle = min(idx + 8, len(g3) - 1)
        code = (g3[settle] << 3) | (g2[settle] << 2) | (g1[settle] << 1) | g0[settle]
        codes.append(code)

    # Skip first few (may be in reset)
    t_ns = data['time'] * 1e9
    post_reset_edges = [codes[i] for i, idx in enumerate(edge_idx)
                        if t_ns[idx] > 55.0 and i < len(codes)]

    if len(post_reset_edges) < 20:
        print(f"FAIL: not enough post-reset edges ({len(post_reset_edges)})")
        failures += 1
        return failures

    # Gray code property: consecutive codes differ by exactly 1 bit
    bad_transitions = 0
    for a, b in zip(post_reset_edges[:-1], post_reset_edges[1:]):
        diff = a ^ b
        if bin(diff).count('1') != 1:
            bad_transitions += 1

    if bad_transitions > 0:
        print(f"FAIL: {bad_transitions} transitions changed != 1 bit (Gray code property violated)")
        failures += 1

    # All 16 codes must appear
    unique_codes = set(post_reset_edges)
    if len(unique_codes) < 16:
        missing = set(range(16)) - unique_codes
        # Expected gray codes for 0-15
        expected_grays = {i ^ (i >> 1) for i in range(16)}
        if not expected_grays.issubset(unique_codes):
            print(f"FAIL: only {len(unique_codes)} unique Gray codes seen (expected 16)")
            failures += 1

    if failures == 0:
        print(f"[CSV] All assertions passed. ({len(unique_codes)} unique codes, "
              f"0 bad transitions in {len(post_reset_edges)} edges)")
    return failures


if __name__ == '__main__':
    raise SystemExit(0 if validate_csv() == 0 else 1)
