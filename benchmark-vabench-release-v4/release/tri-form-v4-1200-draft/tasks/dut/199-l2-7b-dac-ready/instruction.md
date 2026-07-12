# Ready-Triggered 7-bit Capacitive DAC

## Task Contract

- Form: `dut`.
- Level: `L2`.
- Category: data-converter capacitive DAC.
- Target artifact: `l2_7b_dac_ready.va`.
- Role: ready-triggered 7-bit single-ended capacitive weighted DAC with fixed unit capacitance.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module l2_7b_dac_ready(din1, din2, din3, din4, din5, din6, din7, rdy, aout);
```

`din1..din7` are voltage-coded DAC input bits, `rdy` is the update event, and `aout` is the analog output. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameters `vdd = 0.9` and `vth = 0.45`. Use `vth` for input-bit and ready-edge decisions.

## Required Behavior

The first rising `rdy` edge only arms the DAC and leaves the initialized output at zero. On each later rising `rdy` edge, sample `din1..din7` with switched capacitor weights `0.5, 1, 2, 4, 8, 16, 32` from `din1` through `din7`. Normalize the bipolar single-ended output against the full capacitive basis, including one additional fixed non-switching unit capacitance. An all-zero sampled code should drive near `-vdd`; an all-one sampled code remains below `+vdd` because of the fixed unit.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `l2_7b_dac_ready.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
