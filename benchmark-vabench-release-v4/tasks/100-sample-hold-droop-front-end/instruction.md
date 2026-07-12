# Sample Hold Droop Front End

## Task Contract

Implement the requested Verilog-A artifact for `Sample Hold Droop Front End`.
- Form: `dut`
- Level: `L2`
- Category: `sampling_analog_memory`
- Target artifact(s): `sample_hold_droop_ref.va`

Implement `sample_hold_droop_ref.va` in Verilog-A.

## Public Verilog-A Interface

Declare module `sample_hold_droop_ref(vdd, vss, clk, vin, vout, valid, coarse)`
with scalar electrical voltage-domain ports.

- `vdd`, `vss`: local supply rails.
- `clk`: voltage-coded sampling clock.
- `vin`: analog input voltage.
- `vout`: sampled output voltage with bounded hold droop.
- `valid`: voltage-coded pulse indicating a completed sample.
- `coarse`: voltage-coded coarse decision derived from the held sample.

## Public Parameter Contract

- `vth`: clock and decision threshold, default `0.45`.
- `trf`: output transition smoothing time, default `40p`.
- `tau`: droop time constant, default `90n`.
- `dt`: droop update interval, default `0.5n`.
- `taperture`: sampling aperture delay after a rising clock crossing, default
  `200p`.
- `valid_width`: valid-pulse duration after the aperture sample, default `2n`.

## Required Behavior

Model a compact sampling front end:

- On each rising `clk` crossing, schedule a sample after `taperture`.
- At the aperture sample, capture `vin`, clamp the held value to the local
  `vss`-to-`vdd` range, update `vout`, assert `valid`, and update `coarse`.
- `coarse` is high when the sampled value is above `vth` and low otherwise.
- While the clock is low, apply bounded droop to the held output using `tau`
  and `dt`.
- Deassert `valid` after `valid_width`.

## Modeling Constraints

Return only `sample_hold_droop_ref.va`. Do not emit a Spectre testbench,
validation logic, validation-only hooks, or simulator-specific side channels. Use
voltage contributions only; do not use current contributions, `ddt()`, or
`idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `sample_hold_droop_ref.va`. Do not include explanatory prose outside the source artifact contents.
