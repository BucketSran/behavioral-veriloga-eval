# Pipe15 Data Align

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: sampled-data pipeline alignment.
- Target artifact: `pipe15_data_align.va`.
- Role: 15-bit multi-latency pipeline output aligner.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module pipe15_data_align(samp, d0, d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14, do0, do1, do2, do3, do4, do5, do6, do7, do8, do9, do10, do11, do12, do13, do14);
```

`samp` is the sample clock, `d0..d14` are input bits, and `do0..do14` are aligned output bits. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameters `vth = 0.45` and `tt = 20p` for input/clock decisions and output transitions.

## Required Behavior

On each rising `samp` crossing, sample all input bits. Publish `do0..do2` from the current sample, `do3..do6` from the one-sample-delayed group, `do7..do10` from the two-sample-delayed group, and `do11..do14` from the four-sample-delayed group. Use zero for delayed history that is not yet available after startup, and hold outputs between sample events.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `pipe15_data_align.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
