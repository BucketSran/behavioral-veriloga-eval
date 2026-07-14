# Saturation Recovery Limiter Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `saturation_recovery_limiter.va`:
  - Module `saturation_recovery_limiter` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `en` (input, electrical)
    - position 2: `out` (output, electrical)
    - position 3: `sat` (output, electrical)
    - position 4: `recovery_metric` (output, electrical)

## Public Parameter Contract

- `saturation_recovery_limiter.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `saturation_recovery_limiter.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `saturation_recovery_limiter.vlo` defaults to `0.12`; valid range: finite; overrides vlo.
- `saturation_recovery_limiter.vlimit` defaults to `0.78`; valid range: finite; overrides vlimit.
- `saturation_recovery_limiter.tr` defaults to `60p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CLAMP_THE_ENABLED_INPUT_BETWEEN_THE`: restore: Clamp the enabled input between the public low and high limiter levels. Required traces: `time`, `en`, `out`, `recovery_metric`, `sat`, `vin`.
- `P_DRIVE_A_SATURATION_FLAG_WHEN_EITHER`: restore: Drive a saturation flag when either limiter boundary is active. Required traces: `time`, `en`, `out`, `recovery_metric`, `sat`, `vin`.
- `P_CLEAR_OUTPUT_FLAG_AND_RECOVERY_METRIC`: restore: Clear output, flag, and recovery metric while enable is low. Required traces: `time`, `en`, `out`, `recovery_metric`, `sat`, `vin`.
- `P_COMPUTE_LIMITED_CLAMP_V_VIN_VLO`: restore: Compute `limited = clamp(V(vin), vlo, vlimit)` while enabled and drive `out` Required traces: `time`, `en`, `out`, `recovery_metric`, `sat`, `vin`.
- `P_DRIVE_SAT_VHI_WHEN_ENABLED_AND`: restore: Drive `sat = vhi` when enabled and `V(vin)` is outside `[vlo, vlimit]`; Required traces: `time`, `en`, `out`, `recovery_metric`, `sat`, `vin`.
- `P_DRIVE_THE_RECOVERY_METRIC_AS`: restore: Drive the recovery metric as Required traces: `time`, `en`, `out`, `recovery_metric`, `sat`, `vin`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `saturation_recovery_limiter.va`.
Every supplied `.va` file is editable; do not add or omit files.
