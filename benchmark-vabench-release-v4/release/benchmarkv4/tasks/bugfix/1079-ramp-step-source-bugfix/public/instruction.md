# Ramp Step Source Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `bound_step_period_guard_ref.va`:
  - Module `bound_step_period_guard_ref` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `guard_out` (output, electrical)
    - position 3: `phase_out` (output, electrical)

## Public Parameter Contract

- `bound_step_period_guard_ref.period` defaults to `8e-09` s; valid range: period > 0; sets the repetition interval and phase-ramp wrap time.
- `bound_step_period_guard_ref.pulse_w` defaults to `1.5e-09` s; valid range: pulse_w > 0; sets the guard_out high duration from the start of each period; values at least as large as period leave no low remainder in that period.
- `bound_step_period_guard_ref.points_per_period` defaults to `16.0`; valid range: points_per_period > 0; sets transient timestep guidance used to resolve the ramp and guard pulse without changing their ideal timing.
- `bound_step_period_guard_ref.tedge` defaults to `4e-11` s; valid range: tedge > 0; sets guard_out transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_PHASE_RAMP`: restore: Within each period, phase_out rises linearly from VSS toward VDD as normalized phase advances from zero toward one. Required traces: `time`, `VDD`, `VSS`, `phase_out`.
- `P_PHASE_WRAP`: restore: At each period boundary, phase_out wraps from the end of the ramp back to VSS and begins the next ramp. Required traces: `time`, `VDD`, `VSS`, `phase_out`.
- `P_GUARD_WINDOW`: restore: guard_out is at VDD during the first min(pulse_w, period) seconds of each period. Required traces: `time`, `VDD`, `VSS`, `guard_out`.
- `P_GUARD_LOW`: restore: If pulse_w is less than period, guard_out remains at VSS after the guard window and before the next period boundary; if pulse_w is greater than or equal to period, guard_out has no low remainder in that period. Required traces: `time`, `VDD`, `VSS`, `guard_out`.
- `P_RAIL_TRACKING`: restore: Both outputs derive their low and high endpoints from the observed VSS and VDD rails rather than fixed absolute voltages. Required traces: `time`, `VDD`, `VSS`, `guard_out`, `phase_out`.
- `P_PERIODICITY`: restore: The ramp-wrap and guard-window pattern repeats every period with guard transitions smoothed by tedge. Required traces: `time`, `guard_out`, `phase_out`.

## Modeling Constraints

- Use deterministic rail-referenced voltage contributions.
- Timestep guidance may improve resolution but must not redefine the public ramp or guard timing.
- Do not add undeclared synchronization inputs, ports, or validation-only timing cases.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `bound_step_period_guard_ref.va`.
Every supplied `.va` file is editable; do not add or omit files.
