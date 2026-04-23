Write a pure voltage-domain Verilog-A 4-bit Gray-code counter.

Module name: `gray_counter_one_bit_change_ref`.

Requirements:

1. Ports: `vdd`, `vss`, `clk`, `rst`, `g0`, `g1`, `g2`, `g3`
2. On each rising edge of `clk`, if `rst` is low, increment a 4-bit binary count.
3. Drive outputs as Gray code: `gray = bin ^ (bin >> 1)`.
4. When `rst` is high, reset the counter to zero.
5. Adjacent output states must differ by exactly one bit.
6. Use only voltage-domain constructs compatible with EVAS.

Expected behavior:
- Between any two consecutive states, exactly one bit flips
- This is the defining property of Gray code
Ports:
- `vdd`: electrical
- `vss`: electrical
- `clk`: electrical
- `rst`: electrical
- `g0`: electrical
- `g1`: electrical
- `g2`: electrical
- `g3`: electrical (power rail)
- `vss`: inout electrical (power rail)
- `clk`: input electrical
- `rst`: input electrical
- `g0`: output electrical
- `g1`: output electrical
- `g2`: output electrical
- `g3`: output electrical

Write EVAS-compatible Verilog-A (pure voltage-domain behavioral model, no current contributions).
