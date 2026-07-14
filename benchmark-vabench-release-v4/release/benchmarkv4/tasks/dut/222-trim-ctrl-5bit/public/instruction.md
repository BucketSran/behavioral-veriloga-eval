# Trim Ctrl 5bit

## Task Contract

Implement `trim_ctrl_5bit.va` as a voltage-domain scalar-to-trim-code encoder for a calibration control word.

## Public Verilog-A Interface

Use this module signature:

```verilog
module trim_ctrl_5bit(ain, dout0, dout1, dout2, dout3, dout4);
```

All ports are scalar `electrical` nodes. `ain` is an analog code-level input. `dout0..dout4` are voltage-coded trim-control bits, with `dout0` as the least significant bit.

## Public Parameter Contract

- `vh`: output high level, default `0.9`.
- `tr`: output rise/fall transition time, default `20p`.

## Required Behavior

- Convert `V(ain)` to the nearest integer code using half-up rounding.
- Clamp the code to the valid 5-bit trim range `0..31`.
- Drive `dout0..dout4` from the clamped binary code, LSB first.
- Drive high bits near `vh` and low bits near 0 V.
- Update deterministically as the analog input changes.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A only. Do not add checker logic, out-of-band test hooks, simulator side channels, current contributions, `ddt()`, or `idt()`.

## Output Contract

Return exactly one source artifact named `trim_ctrl_5bit.va`.
