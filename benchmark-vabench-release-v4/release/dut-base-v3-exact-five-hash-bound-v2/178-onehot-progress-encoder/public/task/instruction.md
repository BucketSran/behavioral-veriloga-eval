# One-Hot Progress Encoder

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: conversion timing/control support.
- Target artifact: `onehot_progress_encoder.va`.
- Role: one-hot progress marker with count output.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module onehot_progress_encoder(ck, d0, d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14, d15, sum);
```

`ck` is the progress clock, `d0..d15` are one-hot progress outputs, and `sum` is the scalar count output. All ports are electrical.

## Public Parameter Contract

No overrideable public parameters are required. Use a 0.5 V clock threshold and 0/1 V voltage-coded outputs.

## Required Behavior

Initialize all progress outputs and the count to zero. On each rising `ck` crossing, set the next progress bit high and increment the count until all sixteen bits have been asserted. Drive `sum` with the current count value and hold all state between clock events.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `onehot_progress_encoder.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
