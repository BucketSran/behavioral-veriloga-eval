"""Validate serializer_8b: 8-bit Parallel-to-Serial Converter.

Testbench: data=0xA5 (1010_0101), LOAD pulse at t~5ns, CLK 200MHz from t=10ns.
Expected serial output MSB-first: 1, 0, 1, 0, 0, 1, 0, 1 = 0xA5.
Tolerance: at least 2 consecutive LOAD cycles must serialize correctly.
"""
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent.parent.parent / 'output' / 'serializer_8b'

EXPECTED_BITS = [1, 0, 1, 0, 0, 1, 0, 1]  # 0xA5 MSB-first


def validate_csv(out_dir: Path = OUT) -> int:
    data = np.genfromtxt(out_dir / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    failures = 0

    t    = data['time']
    clk  = data['clk']
    load = data['load']
    sout = data['sout']

    vdd = clk.max()
    vth = vdd * 0.5

    clk_hi   = (clk  > vth).astype(int)
    load_hi  = (load > vth).astype(int)
    sout_hi  = (sout > vth).astype(int)

    # Find all CLK rising edges
    clk_edges = np.where(np.diff(clk_hi) > 0)[0]
    # Find LOAD falling edges (end of load pulse)
    load_fall = np.where(np.diff(load_hi) < 0)[0]

    if len(load_fall) == 0:
        print("FAIL: LOAD never deasserted")
        return 1

    captured_frames = []
    for lf in load_fall:
        # Collect next 8 CLK edges after LOAD falls
        post_edges = clk_edges[clk_edges > lf]
        if len(post_edges) < 8:
            continue
        bits = []
        for idx in post_edges[:8]:
            settle = min(idx + 6, len(sout_hi) - 1)
            bits.append(int(sout_hi[settle]))
        captured_frames.append(bits)

    if len(captured_frames) == 0:
        print("FAIL: could not capture any serialized frame")
        return 1

    frame_failures = 0
    for i, bits in enumerate(captured_frames):
        if bits != EXPECTED_BITS:
            print(f"FAIL: frame {i}: got {bits}, expected {EXPECTED_BITS}")
            frame_failures += 1

    if frame_failures > 0:
        failures += 1

    if failures == 0:
        print(f"[CSV] All assertions passed. "
              f"({len(captured_frames)} frames, all match 0xA5 = {EXPECTED_BITS})")
    return failures


if __name__ == '__main__':
    raise SystemExit(0 if validate_csv() == 0 else 1)
