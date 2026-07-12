# Clocked SAR Comparator

## Task Contract

Implement the requested Verilog-A artifact for `Clocked SAR Comparator`.
- Form: `dut`
- Level: `L1`
- Category: `data_converter`
- Target artifact(s): `clocked_sar_comparator.va`

Implement `clocked_sar_comparator.va` in Verilog-A as a converter front-end
interface primitive: a differential analog input is latched into voltage-coded
decision outputs for a SAR-style readout path.

## Public Verilog-A Interface

Declare module `clocked_sar_comparator(CMPCK, VINN, VINP, DCMPN, DCMPP)` with
scalar electrical voltage-domain ports. `CMPCK` is the comparator clock,
`VINP` and `VINN` are the differential analog input pair, and
`DCMPP`/`DCMPN` are the voltage-coded decision outputs that bridge the analog
comparison into the SAR decision path.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vdd = 0.9 V`: logic high level and clock threshold reference.
- `td_cmp = 20p`: comparator output delay.
- `tr = 5p`: output transition smoothing time.

## Required Behavior

- Initialize both decision outputs high.
- Whenever `CMPCK` falls through `vdd/2`, precharge/reset both decision outputs
  high.
- Whenever `CMPCK` rises through `vdd/2`, latch a differential decision:
  `DCMPP` goes high when `VINP > VINN`, `DCMPN` goes high when `VINP < VINN`,
  and both outputs go low for an equal-input decision.
- Hold the latched or precharged state until the next clock event.
- Drive outputs as smooth voltage-domain levels using the configured delay and
  transition time.

## Modeling Constraints

Return only `clocked_sar_comparator.va`. Do not emit a Spectre testbench,
validation logic, validation-only hooks, or simulator-specific side channels. Use
voltage contributions only; do not use current contributions, `ddt()`, or
`idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `clocked_sar_comparator.va`. Do not include explanatory prose outside the source artifact contents.
