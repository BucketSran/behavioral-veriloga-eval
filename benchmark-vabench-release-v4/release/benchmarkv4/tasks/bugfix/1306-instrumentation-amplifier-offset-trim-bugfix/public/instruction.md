# Instrumentation Amplifier Offset-trim System Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `instrumentation_amp_offset_trim_top.va`:
  - Module `instrumentation_amp_offset_trim_top` (entry)
    - position 0: `vinp` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `cal_en` (input, electrical)
    - position 5: `trim_2` (input, electrical)
    - position 6: `trim_1` (input, electrical)
    - position 7: `trim_0` (input, electrical)
    - position 8: `vout` (output, electrical)
    - position 9: `offset_metric` (output, electrical)
    - position 10: `ready` (output, electrical)
- Artifact `diff_gain_core.va`:
  - Module `diff_gain_core` (required_submodule)
    - position 0: `vinp` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `corr` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `vout` (output, electrical)
    - position 5: `offset_metric` (output, electrical)
- Artifact `offset_trim_controller.va`:
  - Module `offset_trim_controller` (required_submodule)
    - position 0: `vinp` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `cal_en` (input, electrical)
    - position 5: `trim_2` (input, electrical)
    - position 6: `trim_1` (input, electrical)
    - position 7: `trim_0` (input, electrical)
    - position 8: `corr` (output, electrical)
    - position 9: `ready` (output, electrical)

## Public Parameter Contract

- `instrumentation_amp_offset_trim_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `instrumentation_amp_offset_trim_top.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `instrumentation_amp_offset_trim_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `instrumentation_amp_offset_trim_top.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `instrumentation_amp_offset_trim_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `instrumentation_amp_offset_trim_top.diff_gain` defaults to `8.0`; valid range: finite; overrides diff_gain.
- `instrumentation_amp_offset_trim_top.trim_lsb` defaults to `8e-3`; valid range: finite; overrides trim_lsb.
- `diff_gain_core.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `diff_gain_core.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `diff_gain_core.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `diff_gain_core.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `diff_gain_core.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `diff_gain_core.diff_gain` defaults to `8.0`; valid range: finite; overrides diff_gain.
- `offset_trim_controller.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `offset_trim_controller.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `offset_trim_controller.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `offset_trim_controller.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `offset_trim_controller.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `offset_trim_controller.trim_lsb` defaults to `8e-3`; valid range: finite; overrides trim_lsb.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_CLEAR_THE_TRIM_STATE`: restore: On reset, clear the trim state, drive `vout` to `vcm`, clear `offset_metric`, and clear `ready`. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `cal_en`, `trim_2`, `trim_1`, `trim_0`, `vout`, `offset_metric`, `ready`.
- `P_DECODE_TRIM_2_TRIM_0_AS`: restore: Decode `trim_2..trim_0` as a signed offset correction around zero. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `cal_en`, `trim_2`, `trim_1`, `trim_0`, `vout`, `offset_metric`, `ready`.
- `P_WHILE_CAL_EN_IS_HIGH_UPDATE`: restore: While `cal_en` is high, update the internal trim accumulator once per rising `clk` edge toward reducing the measured input offset. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `cal_en`, `trim_2`, `trim_1`, `trim_0`, `vout`, `offset_metric`, `ready`.
- `P_DRIVE_VOUT_FROM_THE_CORRECTED_DIFFERENTIAL`: restore: Drive `vout` from the corrected differential input and clamp to the output rails. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `cal_en`, `trim_2`, `trim_1`, `trim_0`, `vout`, `offset_metric`, `ready`.
- `P_EXPOSE_THE_ACTIVE_CORRECTION_ON_OFFSET`: restore: Expose the active correction on `offset_metric` and assert `ready` after three calibration updates. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `cal_en`, `trim_2`, `trim_1`, `trim_0`, `vout`, `offset_metric`, `ready`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: restore: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `cal_en`, `trim_2`, `trim_1`, `trim_0`, `vout`, `offset_metric`, `ready`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `instrumentation_amp_offset_trim_top.va`, `diff_gain_core.va`, `offset_trim_controller.va`.
Every supplied `.va` file is editable; do not add or omit files.
