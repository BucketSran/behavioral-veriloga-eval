# SAR 13bit Serial Decoder

## Task Contract

Implement `sar_13bit_serial_decoder.va` as a voltage-domain serial decoder for an MSB-first 13-bit SAR decision stream.

## Public Verilog-A Interface

Use this module signature:

```verilog
module sar_13bit_serial_decoder(din, clks, ready, dout, dnum);
```

All ports are scalar `electrical` nodes. `din` is the serial decision bit, `ready` marks a bit decision to consume, `clks` publishes a completed frame, `dout` is the decoded analog result, and `dnum` reports the number of high decisions accumulated in the current frame.

## Public Parameter Contract

- `vth`: logic threshold, default `0.55`.

## Required Behavior

- Consume one MSB-first bit on each rising `ready` crossing, starting with bit 12 and ending with bit 0.
- Add the corresponding binary weight when `din` is high.
- Increment `dnum` for each high decision in the current frame.
- On each rising `clks` crossing, publish the previous frame as a normalized bipolar output.
- Map an all-low frame to `-0.5` and an all-high frame near `+0.5`.
- After publishing, reset the accumulator, high-bit count, and bit pointer for the next frame.

## Modeling Constraints

Use pure voltage-domain event-driven Verilog-A. Do not hard-code visible stimulus timing, testbench sample points, checker logic, or simulator side channels.

## Output Contract

Return exactly one source artifact named `sar_13bit_serial_decoder.va`.
