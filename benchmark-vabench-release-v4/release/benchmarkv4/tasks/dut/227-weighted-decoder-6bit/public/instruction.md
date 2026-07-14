# Weighted Decoder 6bit

## Task Contract

Implement `weighted_decoder_6bit.va` as a six-input voltage-coded weighted decoder for a binary data-converter word.

## Public Verilog-A Interface

Use this module signature:

```verilog
module weighted_decoder_6bit(vd1, vd2, vd3, vd4, vd5, vd6, vout);
```

All ports are scalar `electrical` nodes. `vd1` is the most significant input bit, `vd6` is the least significant input bit, and `vout` is the decoded analog output.

## Public Parameter Contract

- `vth`: digital decision threshold for each input bit, default `0.45`.
- `vref`: output full-scale/reference voltage, default `1.0`.

## Required Behavior

- Treat each input as logic 1 when its voltage is greater than `vth`, otherwise logic 0.
- Interpret `vd1..vd6` as an unsigned binary word with `vd1` as MSB and `vd6` as LSB.
- Scale the decoded code by `vref`.
- Map all-zero input to 0 V.
- Map all-ones input to `vref`.

## Modeling Constraints

Use voltage contributions only. Do not emit a support testbench, add checker logic, hard-code testbench waveform sample points, add simulator side channels, use current contributions, `ddt()`, or `idt()`.

## Output Contract

Return exactly one source artifact named `weighted_decoder_6bit.va`.
