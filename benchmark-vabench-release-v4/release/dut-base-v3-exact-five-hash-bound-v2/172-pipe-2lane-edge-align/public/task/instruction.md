# Pipe Two-Lane Edge Align

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: sampled-data alignment primitive.
- Target artifact: `pipe_2lane_edge_align.va`.
- Role: two-lane clock-edge data aligner.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module pipe_2lane_edge_align(din1, din2, clk_align, dout);
```

All ports are electrical. `din1` and `din2` are voltage-coded input lanes, `clk_align` selects the capture edge, and `dout` is the aligned output.

## Public Parameter Contract

Provide overrideable parameter `vth = 0.45` for input and clock decisions. Use smooth voltage transitions for `dout`.

## Required Behavior

Initialize the output state from `din1`. On a rising `clk_align` crossing, sample and publish `din1`. On a falling `clk_align` crossing, sample and publish `din2`. Hold the last sampled lane between clock events.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `pipe_2lane_edge_align.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
