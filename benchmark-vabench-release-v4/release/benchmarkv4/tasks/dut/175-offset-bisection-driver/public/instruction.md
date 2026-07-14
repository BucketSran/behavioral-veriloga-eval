# Offset Bisection Driver

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: comparator calibration/control primitive.
- Target artifact: `offset_bisection_driver.va`.
- Role: bisection-style differential offset stimulus driver.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module offset_bisection_driver(clk, vout, vcm, vinp, vinn);
```

All ports are electrical. `clk` is the update clock, `vout` is the sampled comparator output, `vcm` is the output common-mode input, and `vinp`/`vinn` are generated differential stimulus outputs.

## Public Parameter Contract

Provide overrideable parameters `vth = 0.45` and `step_initial = 10m`. Use `vth` for the update clock and comparator decision threshold.

## Required Behavior

Initialize the differential residue to zero, the search step to `step_initial`, and the previous decision polarity to the low-decision direction. On each falling `clk` crossing, sample `vout`. A low decision (`vout < vth`) increases `vinp-vinn`, and a high decision (`vout >= vth`) decreases `vinp-vinn`. Halve the step only when the sampled polarity changes relative to the previous update; therefore the first low decision does not halve the step, while the first high decision halves the step before moving in the negative direction. Drive `vinp` and `vinn` symmetrically around `V(vcm)`.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `offset_bisection_driver.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
