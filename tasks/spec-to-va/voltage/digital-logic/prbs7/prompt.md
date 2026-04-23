Write a Verilog-A module named `prbs7_ref`.

Create a 7-bit pseudo-random bit sequence (PRBS-7) generator in Verilog-A. Clock-driven, with a serial output and a parallel 7-bit state bus output. Use LFSR with XOR feedback taps at positions 7 and 6.

Expected behavior:
- 7-bit LFSR generating pseudo-random sequence
- Max-length polynomial: x^7 + x^6 + 1 (or equivalent)
- Sequence length = 2^7 - 1 = 127 states before repeating
Ports:
- `clk`: input electrical
- `rst_n`: input electrical
- `en`: input electrical
- `serial_out`: output electrical
- `state_0`: output electrical
- `state_1`: output electrical
- `state_2`: output electrical
- `state_3`: output electrical
- `state_4`: output electrical
- `state_5`: output electrical
- `state_6`: output electrical

Write EVAS-compatible Verilog-A (pure voltage-domain behavioral model, no current contributions).
