# Clocked Mux4 Sampler

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: sampled-data routing primitive.
- Target artifact: `clocked_mux4_sampler.va`.
- Role: clocked four-input mux sampler with update hold and reset.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module clocked_mux4_sampler(dsel0, dsel1, din0, din1, din2, din3, update, rst, clks, dout);
```

`dsel0/dsel1` select one of four input voltages, `din0..din3` are data inputs, `update` enables reselection, `rst` is an active-high reset, `clks` is the sampling clock, and `dout` is the held output. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameters `vth = 0.45`, `tdel = 1p`, `tr = 20p`, and `tf = 20p`.

## Required Behavior

When `rst` is high, force the selected channel to `din0` and drive `dout` from `din0`. On each falling `clks` crossing while reset is inactive, if `update` is high, latch the two select bits and sample the selected input; if `update` is low, hold the previous selection and output value. Drive the held output with the public transition timing.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `clocked_mux4_sampler.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
