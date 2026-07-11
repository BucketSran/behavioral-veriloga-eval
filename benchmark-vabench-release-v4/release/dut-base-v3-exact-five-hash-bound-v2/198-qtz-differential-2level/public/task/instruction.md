# Differential Two-Level Quantizer

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: data-converter quantizer primitive.
- Target artifact: `qtz_differential_2level.va`.
- Role: clocked differential two-level signed quantizer.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module qtz_differential_2level(vinp, vinn, vrefp, vrefn, clk, dout);
```

`vinp/vinn` are sampled differential inputs, `vrefp/vrefn` define the reference threshold level, `clk` is the sampling clock, and `dout` is a signed code-voltage output. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameters `vth = 0.45` and `ttol = 5p`. Use `vth` and `ttol` for rising clock edge detection.

## Required Behavior

Initialize the signed output code to `-0.5`. On each rising `clk` crossing, compute `vinp-vinn` and compare it with the midpoint between `vrefn` and `vrefp`. Drive `dout` to `+0.5` when the sampled input difference is above that reference level and to `-0.5` otherwise. Hold the previous quantized code between clock edges.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `qtz_differential_2level.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
