# CDAC 6b Stage1 Up

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: data-converter CDAC residue model.
- Target artifact: `cdac_6b_stage1_up.va`.
- Role: sampled CDAC residue with upward stage-1 switching.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module cdac_6b_stage1_up(vin, clks, dctrl0, dctrl1, dctrl2, dctrl3, dctrl4, dctrl5, vres);
```

`vin` is the sampled analog input, `clks` is the sampling clock, `dctrl0..dctrl5` are control bits, and `vres` is the residue output. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameter `vdd = 1.0`. Use `vdd/2` as the clock/control threshold and a normalized 1 V CDAC reference span.

## Required Behavior

At initialization and on each falling `clks` crossing, sample `vin` into the residue. On rising control crossings, add binary-weighted residue contributions: `dctrl5` adds 1/2, `dctrl4` 1/4, continuing down to `dctrl0` at 1/64. Hold and continuously drive the current residue state between events.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `cdac_6b_stage1_up.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
