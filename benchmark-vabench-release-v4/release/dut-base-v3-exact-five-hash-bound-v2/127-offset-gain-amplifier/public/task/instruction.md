# Offset Gain Amplifier

## Task Contract

Implement the requested Verilog-A artifact for `Offset Gain Amplifier`.
- Form: `dut`
- Level: `L1`
- Category: `mixed_signal`
- Target artifact(s): `offset_gain_amplifier.va`

- Base function: Single-ended offset-correcting gain stage
- Domain: `voltage`
- Output boundary: validation logic is external; do not generate validation harness or testbench, or measurement helper artifacts.

## Public Verilog-A Interface

`offset_gain_amplifier.va` must declare:

```verilog
module offset_gain_amplifier(sigin, sigout);
input sigin;
output sigout;
electrical sigin, sigout;
```

## Public Parameter Contract

This task has no public parameters.

## Required Behavior

- `P_INPUT_OFFSET_SUBTRACTION`: Subtract 0.2 V from `V(sigin)` before applying gain.

- `P_FIXED_GAIN_THREE`: Drive `sigout` to `3.0 * (V(sigin) - 0.2)`.

- `P_DIRECT_MEMORYLESS_OUTPUT`: Use a direct memoryless voltage output without clipping, filtering, current output, or stimulus-specific behavior.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `offset_gain_amplifier.va`.
Do not include explanatory prose outside the source artifact contents.
