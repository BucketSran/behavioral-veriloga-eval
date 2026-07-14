# Sample And Hold With Droop Leakage

## Task Contract

Implement the requested Verilog-A artifact for `Sample And Hold With Droop Leakage`.
- Form: `dut`
- Level: `L1`
- Category: `sampling_analog_memory`
- Target artifact(s): `leaky_hold.va`

Implement `leaky_hold.va` in Verilog-A.

## Public Verilog-A Interface

Declare module `leaky_hold(sample, rst, vin, vout)` with scalar electrical
voltage-domain ports.

- `sample`: voltage-coded sample control.
- `rst`: active-high voltage-coded reset.
- `vin`: analog input voltage to be sampled.
- `vout`: held output voltage with leakage.

## Public Parameter Contract

- `vth`: logic threshold, default `0.45`.
- `decay`: held-value multiplier per leakage update, default `0.985`.
- `leak_period`: leakage update interval, default `1n`.
- `tr`: output transition smoothing time, default `500p`.

## Required Behavior

- On each rising `sample` crossing while reset is low, capture the current
  `vin` voltage into the held state.
- While reset is low, apply leakage by periodically multiplying the held state
  by `decay`.
- While reset is high, clear the held state to zero.
- Drive `vout` from the held state with smooth voltage-domain transitions.

## Modeling Constraints

Return only `leaky_hold.va`. Do not emit the validation harness, validation logic,
validation-only hooks, or simulator-specific side channels. Use voltage
contributions only; do not use current contributions, `ddt()`, or `idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `leaky_hold.va`. Do not include explanatory prose outside the source artifact contents.
