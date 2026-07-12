# L2 CDAC 4b Switch

## Task Contract

- Form: `dut`.
- Level: `L2`.
- Category: data-converter capacitive DAC.
- Target artifact: `l2_cdac_4b_switch.va`.
- Role: ready-triggered 4-bit capacitive DAC switching model with fixed source basis.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module l2_cdac_4b_switch(din1, din2, din3, din4, rdy, aout);
```

`din1..din4` are voltage-coded DAC input bits, `rdy` is the update event, and `aout` is the analog output. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameters `vdd = 1.1` and `vth = 0.55`. Use `vth` for input-bit and ready-edge decisions.

## Required Behavior

The first rising `rdy` edge only arms the DAC and leaves the initialized output at zero. On each later rising `rdy` edge, sample `din1..din4` against `vth` with switched weights `0.5, 1, 2, 4` from `din1` through `din4`. The source-normalization basis is a total weight of 8.5: the 7.5 total switched weight plus a fixed non-switching reference contribution of 1.0.

Let `switched_weight` be the sum of the enabled switched weights on that `rdy` edge. Map the sampled ratio to a bipolar single-ended output as `(switched_weight / 8.5) * 2.0 * vdd - vdd`. Thus no enabled input bits produce `-vdd`, and all enabled input bits produce `((7.5 / 8.5) * 2.0 - 1.0) * vdd`.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `l2_cdac_4b_switch.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
