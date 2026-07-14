# Acquisition Limited Sample And Hold Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `acquisition_limited_sample_hold.va`:
  - Module `acquisition_limited_sample_hold` (entry)
    - position 0: `sample` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `vout` (output, electrical)
    - position 4: `metric` (output, electrical)

## Public Parameter Contract

- `acquisition_limited_sample_hold.vth` defaults to `0.45` V; valid range: vth > 0; sets the sample and reset logic threshold.
- `acquisition_limited_sample_hold.vinit` defaults to `0.45` V; valid range: any finite voltage; sets the initial and reset held-output voltage.
- `acquisition_limited_sample_hold.alpha` defaults to `0.42`; valid range: 0 < alpha <= 1; sets the fraction of the remaining vin-to-vout error acquired per update.
- `acquisition_limited_sample_hold.tick` defaults to `1e-09` s; valid range: tick > 0; sets the interval between acquisition updates while sample is high.
- `acquisition_limited_sample_hold.tr` defaults to `2e-10` s; valid range: tr > 0; sets vout and metric transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET`: restore: While rst is above vth, vout returns to vinit and metric is low. Required traces: `time`, `rst`, `vout`, `metric`.
- `P_ACQUISITION_ENABLE`: restore: When sample is above vth and reset is inactive, metric is high and vout is allowed to acquire vin. Required traces: `time`, `sample`, `rst`, `vin`, `vout`, `metric`.
- `P_FINITE_ACQUISITION`: restore: At each tick during acquisition, vout advances by alpha times the remaining difference from the current vin rather than jumping instantaneously. Required traces: `time`, `sample`, `vin`, `vout`.
- `P_ACQUISITION_CONVERGENCE`: restore: For a constant vin and repeated acquisition updates, vout moves monotonically toward vin without overshoot for the declared alpha range. Required traces: `time`, `sample`, `vin`, `vout`.
- `P_HOLD`: restore: A falling sample crossing freezes the last acquired value; vout holds it and metric remains low until acquisition resumes or reset is asserted. Required traces: `time`, `sample`, `rst`, `vin`, `vout`, `metric`.

## Modeling Constraints

- Use deterministic timer-driven acquisition state and continuous voltage output contributions.
- Preserve the acquired state between sample windows.
- Do not add undeclared ports, hidden tracking paths, or validation-only sample times.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `acquisition_limited_sample_hold.va`.
Every supplied `.va` file is editable; do not add or omit files.
