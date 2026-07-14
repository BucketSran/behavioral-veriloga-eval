# TDC Ideal Edge Delta

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: measurement/timing support primitive.
- Target artifact: `tdc_ideal_edge_delta.va`.
- Role: ideal edge-interval timing detector.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module tdc_ideal_edge_delta(inp, inn, samp, vout);
```

`inp` and `inn` are measured edge inputs, `samp` starts a new measurement window, and `vout` is the normalized signed timing output. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameters `vth = 0.45` and `fullrange = 100p`. Use `vth` as the rising-edge threshold for all three inputs.

## Required Behavior

At initialization, clear both trigger flags and initialize the output state to zero. On each rising `samp` crossing, clear only the input trigger flags and keep the previous output until a new edge pair is measured. Within the window, record the rising threshold crossing time of `inp` and `inn`; once both have occurred, drive the output with the signed time difference `(time_inp - time_inn)` normalized by `fullrange`.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior. Do not clear the reported output on `samp`, count falling edges, clip the normalized result, or hard-code edge times.

## Output Contract

Return exactly one complete Verilog-A source file named `tdc_ideal_edge_delta.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
