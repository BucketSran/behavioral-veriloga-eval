# Saturation Recovery Limiter

## Task Contract
Implement the DUT form for canonical family `269` as Spectre-compatible voltage-domain behavioral Verilog-A. Produce exactly `saturation_recovery_limiter.va` and satisfy the public observable contract below for `Saturation Recovery Limiter`. The task level is `L1` and the category is `signal_conditioning_and_measurement`.

## Public Verilog-A Interface
```verilog
module saturation_recovery_limiter(vin, en, out, sat, recovery_metric);
```
All listed ports are electrical and must keep this order:
- `vin` (input, electrical, position 0)
- `en` (input, electrical, position 1)
- `out` (output, electrical, position 2)
- `sat` (output, electrical, position 3)
- `recovery_metric` (output, electrical, position 4)

## Public Parameter Contract
- `vth` (real, default `0.45`): overrides vth.
- `vhi` (real, default `0.9`): overrides vhi.
- `vlo` (real, default `0.12`): overrides vlo.
- `vlimit` (real, default `0.78`): overrides vlimit.
- `tr` (real, default `60p`): overrides tr.

## Required Behavior
- `P_CLAMP_THE_ENABLED_INPUT_BETWEEN_THE`: Clamp the enabled input between the public low and high limiter levels.
- `P_DRIVE_A_SATURATION_FLAG_WHEN_EITHER`: Drive a saturation flag when either limiter boundary is active.
- `P_CLEAR_OUTPUT_FLAG_AND_RECOVERY_METRIC`: Clear output, flag, and recovery metric while enable is low.
- `P_COMPUTE_LIMITED_CLAMP_V_VIN_VLO`: Compute `limited = clamp(V(vin), vlo, vlimit)` while enabled and drive `out`
- `P_DRIVE_SAT_VHI_WHEN_ENABLED_AND`: Drive `sat = vhi` when enabled and `V(vin)` is outside `[vlo, vlimit]`;
- `P_DRIVE_THE_RECOVERY_METRIC_AS`: Drive the recovery metric as

The evaluator saves and may inspect these public trace signals: `time`, `en`, `out`, `recovery_metric`, `sat`, `vin`.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only internals, or simulator side channels.
- Do not emit checker code, score logic, private oracle assumptions, or testbench-specific timing shortcuts.
- No public support source files are required; the solver DUT bundle consists only of the requested target artifact(s).
- Keep candidate DUT code separate from evaluator/testbench files; the solver-owned boundary is the target artifact list only.

## Output Contract
Return only the Verilog-A source artifact(s) named in Section 1. The artifact(s) must compile without nonstandard include files, generated testbenches, undeclared helper modules outside the declared bundle, or changes to the public/evaluator decks.
