# Aperture Delay Track And Hold

## Task Contract

Implement the requested Verilog-A artifact for `Aperture Delay Track And Hold`.
- Form: `dut`
- Level: `L1`
- Category: `sampling_analog_memory`
- Target artifact(s): `sample_hold_aperture_ref.va`

Implement `sample_hold_aperture_ref.va` in Verilog-A.

## Public Verilog-A Interface

Declare module `sample_hold_aperture_ref(VDD, VSS, clk, vin, vout)` with
scalar electrical voltage-domain ports. `clk` is a voltage-coded control input. `VDD` and `VSS` are public supply-observation ports for harness compatibility; they do not clamp, scale, or shift the held `vin` value.

## Public Parameter Contract

- `vth`: clock threshold, default `0.45`.
- `taperture`: aperture delay after a rising clock edge, default `200p`.
- `tedge`: output transition smoothing time, default `50p`.

## Required Behavior

- Initialize the held value from the initial value of `vin`.
- On each rising `clk` transition, arm a sample for `$abstime + taperture`.
- At the delayed aperture instant, capture the current value of `vin`.
- Hold the captured value on `vout` until the next delayed sample.
- Do not rail-limit `vout`; output the held `vin` value even if it is outside the instantaneous `VSS` to `VDD` interval.
- Drive `vout` with smooth voltage-domain transitions.

## Modeling Constraints

Return only `sample_hold_aperture_ref.va`. Do not emit the validation harness,
validation logic, validation-only hooks, or simulator-specific side channels. Use
voltage contributions only; do not use current contributions, `ddt()`, or
`idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `sample_hold_aperture_ref.va`. Do not include explanatory prose outside the source artifact contents.
