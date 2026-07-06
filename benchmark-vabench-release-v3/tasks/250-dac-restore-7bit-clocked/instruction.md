# Resettable DAC Restore 7bit Clocked

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: data-converter DAC restore primitive.
- Target artifact: `dac_restore_7bit_clocked.va`.
- Role: clocked 7-bit binary code to centered restore voltage with active-high midscale restore.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module dac_restore_7bit_clocked(d6, d5, d4, d3, d2, d1, d0, clk, rst, vout);
```

`d6..d0` are voltage-coded input bits ordered MSB to LSB, `clk` is the update clock, `rst` is an active-high restore control, and `vout` is the restored analog output. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameter `vth = 0.45`. Use it for bit decisions, rising clock-edge detection, and reset detection.

## Required Behavior

When `rst` rises above threshold, immediately restore `vout` to the midscale value of 0 V. While `rst` remains high, ignore clock edges and hold the restored midscale value. When `rst` is low, each rising `clk` crossing decodes `d6..d0` as a 7-bit binary word and drives `vout` to the center of that code bin across a bipolar 1.8 V span from `-0.9 V` to `+0.9 V`. Hold the output between clock events.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `dac_restore_7bit_clocked.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
