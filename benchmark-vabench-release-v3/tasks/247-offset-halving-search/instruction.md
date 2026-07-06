# Offset Trim Halving Search

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: comparator calibration/control primitive.
- Target artifact: `offset_halving_search.va`.
- Role: bounded comparator-directed differential offset trim with halving and lockout.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module offset_halving_search(clk, dcmpp, vinp, vinn);
```

`clk` is the update clock, `dcmpp` is the comparator decision input, and `vinp`/`vinn` are generated differential trim stimulus outputs. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameters `vdd = 0.9`, `step_initial = 0.16`, `step_min = 0.02`, and `diff_limit = 0.12`. Use `0.5*vdd` as the clock and decision threshold. `step_initial`, `step_min`, and `diff_limit` are differential-voltage quantities.

## Required Behavior

Initialize the differential trim residue to zero and the active step to `step_initial`. On each falling `clk` crossing before lockout, sample `dcmpp`: a high decision moves the differential trim negative and a low decision moves it positive. Clamp the signed residue to `+/-diff_limit`. Halve the active step after each update; once the next step would be below `step_min`, lock the trim code and hold the existing residue for later clock edges. Drive `vinp` and `vinn` symmetrically around `0.5*vdd` from the current residue.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `offset_halving_search.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
