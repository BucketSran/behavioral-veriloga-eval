# Saturation Recovery Limiter Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Saturation Recovery Limiter` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `saturation_recovery_limiter.va`:
  - Module `saturation_recovery_limiter` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `en` (input, electrical)
    - position 2: `out` (output, electrical)
    - position 3: `sat` (output, electrical)
    - position 4: `recovery_metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `saturation_recovery_limiter` as `XDUT` with ordered public binding: vin=vin, en=en, out=out, sat=sat, recovery_metric=recovery_metric.

## Public Parameter Contract

- `saturation_recovery_limiter.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `saturation_recovery_limiter.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `saturation_recovery_limiter.vlo` defaults to `0.12`; valid range: finite; overrides vlo.
- `saturation_recovery_limiter.vlimit` defaults to `0.78`; valid range: finite; overrides vlimit.
- `saturation_recovery_limiter.tr` defaults to `60p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CLAMP_THE_ENABLED_INPUT_BETWEEN_THE`: exercise and make observable: Clamp the enabled input between the public low and high limiter levels. Required traces: `time`, `en`, `out`, `recovery_metric`, `sat`, `vin`.
- `P_DRIVE_A_SATURATION_FLAG_WHEN_EITHER`: exercise and make observable: Drive a saturation flag when either limiter boundary is active. Required traces: `time`, `en`, `out`, `recovery_metric`, `sat`, `vin`.
- `P_CLEAR_OUTPUT_FLAG_AND_RECOVERY_METRIC`: exercise and make observable: Clear output, flag, and recovery metric while enable is low. Required traces: `time`, `en`, `out`, `recovery_metric`, `sat`, `vin`.
- `P_COMPUTE_LIMITED_CLAMP_V_VIN_VLO`: exercise and make observable: Compute `limited = clamp(V(vin), vlo, vlimit)` while enabled and drive `out` Required traces: `time`, `en`, `out`, `recovery_metric`, `sat`, `vin`.
- `P_DRIVE_SAT_VHI_WHEN_ENABLED_AND`: exercise and make observable: Drive `sat = vhi` when enabled and `V(vin)` is outside `[vlo, vlimit]`; Required traces: `time`, `en`, `out`, `recovery_metric`, `sat`, `vin`.
- `P_DRIVE_THE_RECOVERY_METRIC_AS`: exercise and make observable: Drive the recovery metric as Required traces: `time`, `en`, `out`, `recovery_metric`, `sat`, `vin`.

The required trace names are: `time`, `en`, `out`, `recovery_metric`, `sat`, `vin`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
