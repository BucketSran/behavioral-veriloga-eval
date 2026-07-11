# DAC Restore 4bit Clocked

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: data-converter DAC restore primitive.
- Target artifact: `dac_restore_4bit_clocked.va`.
- Role: clocked 4-bit binary code to centered restore voltage.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module dac_restore_4bit_clocked(d3, d2, d1, d0, clk, vout);
```

`d3..d0` are voltage-coded input bits ordered MSB to LSB, `clk` is the update clock, and `vout` is the restored analog output. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameter `vth = 0.45`. Use it for bit decisions and rising clock-edge detection.

## Required Behavior

On each rising `clk` crossing, decode `d3..d0` as a 4-bit binary word and drive `vout` to the center of that code bin across a bipolar 1.8 V span from `-0.9 V` to `+0.9 V`. Hold the output between clock events.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `dac_restore_4bit_clocked.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
