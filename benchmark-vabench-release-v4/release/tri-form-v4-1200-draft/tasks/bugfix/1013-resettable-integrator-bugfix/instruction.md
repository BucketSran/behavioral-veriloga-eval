# Resettable Integrator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `resettable_integrator.va`:
  - Module `resettable_integrator` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vout` (output, electrical)

## Public Parameter Contract

- `resettable_integrator.vth` defaults to `0.45` V; valid range: vth > 0; sets active-high reset threshold.
- `resettable_integrator.gain` defaults to `1000000000.0` 1/s; valid range: gain >= 0; sets accumulation gain per input volt.
- `resettable_integrator.dt` defaults to `1e-09` s; valid range: dt > 0; sets periodic state update interval.
- `resettable_integrator.vmax` defaults to `0.85` V; valid range: vmax >= 0; sets accumulator upper clamp.
- `resettable_integrator.tr` defaults to `5e-10` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_ZERO`: restore: vout begins at 0 V. Required traces: `time`, `vout`.
- `P_TIMER_INTEGRATION`: restore: While reset is low, each dt timer event adds gain*vin*dt to the accumulator. Required traces: `time`, `vin`, `rst`, `vout`.
- `P_ACTIVE_HIGH_RESET`: restore: When rst is above vth at a timer event, the accumulator and vout return toward 0 V and later restart from zero. Required traces: `time`, `vin`, `rst`, `vout`.
- `P_ACCUMULATOR_CLAMP`: restore: vout remains in the closed 0 V to vmax range. Required traces: `time`, `vout`.
- `P_EVENT_HOLD`: restore: The accumulated state changes only on dt timer events. Required traces: `time`, `vin`, `rst`, `vout`.

## Modeling Constraints

- Use deterministic timer-updated voltage-domain behavior.
- Use voltage contributions only.
- Do not use current contributions, ddt(), idt(), undeclared state outputs, or validation hooks.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `resettable_integrator.va`.
Every supplied `.va` file is editable; do not add or omit files.
