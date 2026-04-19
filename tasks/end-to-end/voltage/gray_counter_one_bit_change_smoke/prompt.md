Write a pure voltage-domain Verilog-A 4-bit Gray-code counter.

Requirements:

1. Ports: `vdd`, `vss`, `clk`, `rst`, `g0`, `g1`, `g2`, `g3`
2. On each rising edge of `clk`, if `rst` is low, increment a 4-bit binary count.
3. Drive outputs as Gray code: `gray = bin ^ (bin >> 1)`.
4. When `rst` is high, reset the counter to zero.
5. Adjacent output states must differ by exactly one bit.
6. Use only voltage-domain constructs compatible with EVAS.
