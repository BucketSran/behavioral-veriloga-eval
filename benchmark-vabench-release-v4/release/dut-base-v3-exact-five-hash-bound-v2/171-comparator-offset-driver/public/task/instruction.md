# Comparator Offset Binary Driver

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: comparator calibration/control primitive.
- Target artifact: `comparator_offset_binary_driver.va`.
- Role: binary-search differential stimulus driver for comparator offset measurement.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module comparator_offset_binary_driver(clk, dcmpp, vinp, vinn);
```

All ports are electrical. `clk` is the update clock, `dcmpp` is a voltage-coded comparator decision input, and `vinp`/`vinn` are generated differential stimulus outputs.

## Public Parameter Contract

Provide overrideable parameter `vdd = 0.9`. Use `0.5*vdd` as the clock and decision threshold. Use a 0.1 V initial search step.

## Required Behavior

Initialize the differential search residue to zero. On each falling `clk` threshold crossing, sample `dcmpp`: a high decision moves the differential input in the negative direction, and a low decision moves it in the positive direction. Halve the search step after every update. Drive `vinp` and `vinn` symmetrically around `0.5*vdd` from the current residue.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `comparator_offset_binary_driver.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
