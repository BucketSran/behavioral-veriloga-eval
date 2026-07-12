# Coarse 3-Bit Quantizer With Residue

## Task Contract

Implement `coarse_qtz_3bit_residue.va` as a continuous coarse 3-bit voltage quantizer with residue output.

## Public Verilog-A Interface

Use this module signature:

```verilog
module coarse_qtz_3bit_residue(vin, d0, d1, d2, vres);
```

All ports are scalar `electrical` nodes. `vin` is the analog input, `d0..d2` are voltage-coded output bits with `d0` as the least significant bit, and `vres` is the analog residue.

## Public Parameter Contract

- `vref`: positive and negative clipping magnitude for the input range, default `1.0`.
- `vdd`: high output level for the binary code bits, default `1.0`.

## Required Behavior

- Clip `vin` to the range from `-vref` to `+vref`.
- Quantize the clipped value into eight 3-bit codes using round-to-nearest behavior.
- Saturate the code at the endpoints.
- Use uniformly spaced quantization levels starting at `-vref`, with one LSB equal to one eighth of the full input span.
- Drive `d0`, `d1`, and `d2` as LSB-to-MSB voltage-coded bits.
- Drive `vres` as the clipped input minus the selected quantized analog level.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A. Do not emit a support testbench, add checker logic, hard-code testbench waveform sample points, add simulator side channels, use current contributions, `ddt()`, or `idt()`.

## Output Contract

Return exactly one source artifact named `coarse_qtz_3bit_residue.va`.
