# RF Envelope Detector with Attack/Release Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `rf_envelope_detector_attack_release.va`:
  - Module `rf_envelope_detector_attack_release` (entry)
    - position 0: `vin` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `envelope` (inout, electrical)
    - position 5: `attack_metric` (inout, electrical)
    - position 6: `valid` (inout, electrical)

## Public Parameter Contract

- `rf_envelope_detector_attack_release.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `rf_envelope_detector_attack_release.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `rf_envelope_detector_attack_release.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `rf_envelope_detector_attack_release.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `rf_envelope_detector_attack_release.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `rf_envelope_detector_attack_release.attack_step` defaults to `120e-3`; valid range: finite; overrides attack_step.
- `rf_envelope_detector_attack_release.release_step` defaults to `30e-3`; valid range: finite; overrides release_step.
- `rf_envelope_detector_attack_release.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear envelope, metric, and `valid`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `envelope`, `attack_metric`, `valid`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: restore: On each enabled rising `clk` edge, estimate input magnitude as distance from `vcm`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `envelope`, `attack_metric`, `valid`.
- `P_USE_A_FASTER_ATTACK_STEP_WHEN`: restore: Use a faster attack step when magnitude rises and a slower release step when it falls. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `envelope`, `attack_metric`, `valid`.
- `P_DRIVE_ENVELOPE_WITH_THE_TRACKED_MAGNITUDE`: restore: Drive `envelope` with the tracked magnitude mapped into the public voltage range. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `envelope`, `attack_metric`, `valid`.
- `P_EXPOSE_WHETHER_THE_LAST_UPDATE_USED`: restore: Expose whether the last update used attack or release on `attack_metric`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `envelope`, `attack_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `rf_envelope_detector_attack_release.va`.
Every supplied `.va` file is editable; do not add or omit files.
