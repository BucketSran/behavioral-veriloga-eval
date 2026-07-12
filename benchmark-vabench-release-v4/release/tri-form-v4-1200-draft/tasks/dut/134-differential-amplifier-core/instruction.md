# Differential Amplifier Core

## Task Contract
Implement the Verilog-A DUT `differential_amplifier_core.va` for a differential-input, single-ended gain core with a fixed input-referred offset.

## Public Verilog-A Interface
Provide `module differential_amplifier_core(sigin_p, sigin_n, sigout);` with electrical inputs `sigin_p`, `sigin_n` and electrical output `sigout`.

## Public Parameter Contract
This task has no public parameters.

## Required Behavior
Use `V(sigin_p, sigin_n)` as the input. Subtract a 0.05 V input-referred offset, apply a fixed voltage gain of 2.0, and drive the resulting single-ended output voltage on `sigout`.

## Modeling Constraints
Use a direct voltage-domain contribution. Do not add rail clipping, filtering, current contributions, transistor devices, or testbench-specific behavior.

## Output Contract
Submit only the completed Verilog-A module in `differential_amplifier_core.va`.
