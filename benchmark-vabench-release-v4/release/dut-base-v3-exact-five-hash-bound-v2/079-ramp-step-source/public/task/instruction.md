# Ramp Step Source

## Task Contract

Implement the requested Verilog-A artifact for `Ramp Step Source`.
- Form: `dut`
- Level: `L1`
- Category: `stimulus_source_generators`
- Target artifact(s): `bound_step_period_guard_ref.va`

Implement `bound_step_period_guard_ref.va` in Verilog-A.

## Public Verilog-A Interface

Declare module `bound_step_period_guard_ref` with positional ports
`VDD, VSS, guard_out, phase_out`. `VDD` and `VSS` are electrical supply rails;
`guard_out` and `phase_out` are electrical outputs.

## Public Parameter Contract

- `period = 8 ns`: ramp period before any example harness override.
- `pulse_w = 1.5 ns`: guard-pulse high duration before any example harness override.
- `points_per_period = 16.0`: timestep guidance for resolving the ramp.
- `tedge = 40 ps`: guard output transition time.

## Required Behavior

Generate a periodic normalized phase ramp and a guard pulse. Within each
period, `phase_out` ramps from `VSS` toward `VDD` and wraps at the start of the
next period. `guard_out` is high during the first `min(pulse_w, period)` seconds
of each period. If `pulse_w >= period`, `guard_out` has no low remainder during
that period. The output levels should track the supplied rail
voltages, not hard-coded absolute rails.

Using `$bound_step(period / points_per_period)` is allowed to keep the narrow
guard pulse observable, but the scored behavior is the ramp wrap and guard
timing.

## Modeling Constraints

Return only `bound_step_period_guard_ref.va`. Do not generate a the simulator
example harness or validation logic. Do not use current contributions, `ddt()`, `idt()`,
transistor-level devices, AC/noise analysis, or simulator-specific side
channels.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `bound_step_period_guard_ref.va`. Do not include explanatory prose outside the source artifact contents.
