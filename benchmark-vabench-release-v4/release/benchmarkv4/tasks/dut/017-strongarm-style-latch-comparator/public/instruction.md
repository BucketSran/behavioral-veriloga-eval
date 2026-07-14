# Strongarm Style Latch Comparator

## Task Contract

Implement the requested Verilog-A artifact for `Strongarm Style Latch Comparator`.
- Form: `dut`
- Level: `L1`
- Category: `comparator_decision`
- Target artifact(s): `cmp_strongarm.va`

Implement a voltage-domain StrongARM-style clocked latch comparator.

## Public Verilog-A Interface

Declare module `cmp_strongarm` with positional ports `CLK, VINN, VINP, DCMPN,
DCMPP, LP, LM, VSS, VDD`. All ports are electrical. `CLK` is the comparator
clock, `VINP` and `VINN` are the differential inputs, `DCMPP` and `DCMPN` are
the complementary decision outputs, `LP` and `LM` are latch-state monitor
outputs, and `VSS`/`VDD` are supply rails.

## Public Parameter Contract

Provide these overrideable public parameters:

- `td_cmp = 0`: comparator output delay.
- `voffset = 0`: input-referred offset subtracted from `VINP - VINN`.

## Required Behavior

- Initialize all public decision and latch-state outputs low.
- Use `V(VDD,VSS)/2` as the clock decision threshold.
- On each rising clock crossing, latch the sign of
  `V(VINP,VSS) - V(VINN,VSS) - voffset`.
- For a positive latched differential input, drive `DCMPP` and `LP` high while
  `DCMPN` and `LM` remain low. For a negative latched differential input, drive
  `DCMPN` and `LM` high while `DCMPP` and `LP` remain low.
- For an exactly zero effective differential input, keep both complementary
  decision states low.
- On each falling clock crossing, reset all public decision and latch-state
  outputs low.
- Hold the latched decision between clock events; the model must not become
  transparent while the clock is high.

## Modeling Constraints

Return only `cmp_strongarm.va`. Use voltage contributions only. Do not modify
or emit the support testbench, add validation logic, hard-code waveform sample
points, add simulator-specific side channels, use current contributions,
`ddt()`, or `idt()`. For Cadence-style event modeling, update discrete state in
`cross()`/`initial_step` event blocks and drive smoothed output contributions
outside those event blocks.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `cmp_strongarm.va`. Do not include explanatory prose outside the source artifact contents.
