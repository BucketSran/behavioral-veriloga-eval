# Clocked Comparator Reset Low

## Task Contract

Implement the requested Verilog-A artifact for `Clocked Comparator Reset Low`.
- Form: `dut`
- Level: `L1`
- Category: `data_converter`
- Target artifact(s): `clocked_comparator_reset_low.va`

Implement a clocked differential comparator with reset-low voltage-coded
decision outputs.

## Public Verilog-A Interface

Declare module `clocked_comparator_reset_low` with positional ports `CMPCK,
VINN, VINP, DCMPN, DCMPP`. All ports are electrical. `CMPCK` is the comparator
clock, `VINP` and `VINN` are the differential analog inputs, and
`DCMPP`/`DCMPN` are complementary decision outputs.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vdd = 0.9 V`: logic high level and clock threshold reference.
- `td_cmp = 100p`: output decision delay.
- `tr = 10p`: output transition smoothing time.

## Required Behavior

- Initialize both decision outputs low.
- Whenever `CMPCK` falls through `vdd/2`, reset both decision outputs low.
- Whenever `CMPCK` rises through `vdd/2`, latch a differential decision:
  `DCMPP` high for `VINP > VINN`, `DCMPN` high for `VINP < VINN`, and both
  outputs remain low for an equal-input decision.
- Hold the latched or reset state until the next clock event.
- Drive outputs as smooth voltage-domain levels using the configured delay and
  transition time.

## Modeling Constraints

Return only `clocked_comparator_reset_low.va`. Use voltage contributions only.
Do not modify or emit the support testbench, add validation logic, hard-code
waveform sample points, add simulator-specific side channels, use current
contributions, `ddt()`, or `idt()`. Update local decision state in analog event
blocks and drive smoothed output contributions outside those event blocks.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `clocked_comparator_reset_low.va`. Do not include explanatory prose outside the source artifact contents.
