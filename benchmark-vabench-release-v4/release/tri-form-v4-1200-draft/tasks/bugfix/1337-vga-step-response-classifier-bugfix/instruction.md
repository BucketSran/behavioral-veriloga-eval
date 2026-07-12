# VGA Step-response Classifier Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `vga_step_response_classifier.va`:
  - Module `vga_step_response_classifier` (entry)
    - position 0: `vin` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `gain_2` (inout, electrical)
    - position 5: `gain_1` (inout, electrical)
    - position 6: `gain_0` (inout, electrical)
    - position 7: `vout` (inout, electrical)
    - position 8: `overshoot_metric` (inout, electrical)
    - position 9: `settled` (inout, electrical)

## Public Parameter Contract

- `vga_step_response_classifier.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `vga_step_response_classifier.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `vga_step_response_classifier.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `vga_step_response_classifier.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `vga_step_response_classifier.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `vga_step_response_classifier.gain_lsb` defaults to `0.5`; valid range: finite; overrides gain_lsb.
- `vga_step_response_classifier.settle_tol` defaults to `12e-3`; valid range: finite; overrides settle_tol.
- `vga_step_response_classifier.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: restore: On reset or when disabled, drive `vout` to `vcm`, clear metric, and clear `settled`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `overshoot_metric`, `settled`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: restore: On each enabled rising `clk` edge, decode the gain code and update the target output from `vin`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `overshoot_metric`, `settled`.
- `P_APPLY_BOUNDED_SETTLING_WITH_A_CODE`: restore: Apply bounded settling with a code-dependent overshoot proxy after large gain changes. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `overshoot_metric`, `settled`.
- `P_EXPOSE_OVERSHOOT_MAGNITUDE_ON_OVERSHOOT_METRIC`: restore: Expose overshoot magnitude on `overshoot_metric`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `overshoot_metric`, `settled`.
- `P_ASSERT_SETTLED_AFTER_TWO_CONSECUTIVE_UPDATES`: restore: Assert `settled` after two consecutive updates within `settle_tol` of the target. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `overshoot_metric`, `settled`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `vga_step_response_classifier.va`.
Every supplied `.va` file is editable; do not add or omit files.
