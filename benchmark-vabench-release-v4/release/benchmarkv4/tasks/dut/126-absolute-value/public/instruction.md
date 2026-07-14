# Absolute Value Behavior

## Task Contract

Implement the requested Verilog-A artifact for `Absolute Value`.
- Form: `dut`
- Level: `L1`
- Category: `mixed_signal`
- Target artifact(s): `absolute_value_behavior.va`

Implement a pure voltage-domain absolute-value DUT.

## Public Verilog-A Interface

Declare module `absolute_value_behavior` with positional ports `sigin, sigout`.
Both ports are electrical.

## Public Parameter Contract

This task has no public parameters.

## Required Behavior

- `P_POSITIVE_INPUT_PASSTHROUGH`: For nonnegative `V(sigin)`, drive `sigout` to the same nonnegative voltage.

- `P_NEGATIVE_INPUT_REFLECTION`: For negative `V(sigin)`, drive `sigout` to `-V(sigin)`.

- `P_MEMORYLESS_ABSOLUTE_VALUE`: The output is an instantaneous absolute-value function of `sigin` with no retained state or waveform schedule.

## Modeling Constraints

Return only `absolute_value_behavior.va`. Use voltage contributions only. Do not
modify or emit the support testbench, add validation logic, hard-code validation-only
waveform sample points, add simulator-specific side channels, use current
contributions, `ddt()`, or `idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `absolute_value_behavior.va`. Do not include explanatory prose outside the source artifact contents.
