# Max Detector Hold

## Task Contract

Implement the requested Verilog-A artifact for `Max Detector Hold`.
- Form: `dut`
- Level: `L1`
- Category: `mixed_signal`
- Target artifact(s): `max_detector_hold.va`

Implement the Verilog-A DUT `max_detector_hold.va` for a continuous maximum detector with hold behavior.

This is a single-DUT task. The testbench is a public verification scenario, not a table of values to copy into the DUT.

## Public Verilog-A Interface

Provide `module max_detector_hold(vin, vout);` with electrical input `vin` and electrical output `vout`.

## Public Parameter Contract

This task has no public parameters.

## Required Behavior

Initialize the held value from the input at the start of simulation. During transient simulation, update the held value only when `V(vin)` exceeds the previously held maximum. Drive `vout` to the held maximum, so `vout` is monotone nondecreasing even when `vin` falls.

## Modeling Constraints

Use analog state in a Spectre-compatible Verilog-A model. Do not implement a resettable peak detector, a minimum detector, a passthrough follower, or a final-value-only detector.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Submit only the completed Verilog-A module in `max_detector_hold.va`.
