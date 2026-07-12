# Baseband Offset-and-gain Trim Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `baseband_offset_gain_trim_macro.va`:
  - Module `baseband_offset_gain_trim_macro` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `gain_2` (input, electrical)
    - position 5: `gain_1` (input, electrical)
    - position 6: `gain_0` (input, electrical)
    - position 7: `offset_2` (input, electrical)
    - position 8: `offset_1` (input, electrical)
    - position 9: `offset_0` (input, electrical)
    - position 10: `vout` (output, electrical)
    - position 11: `residual_metric` (output, electrical)
    - position 12: `valid` (output, electrical)

## Public Parameter Contract

- `baseband_offset_gain_trim_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `baseband_offset_gain_trim_macro.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `baseband_offset_gain_trim_macro.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `baseband_offset_gain_trim_macro.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `baseband_offset_gain_trim_macro.gain_base` defaults to `0.7`; valid range: finite; overrides gain_base.
- `baseband_offset_gain_trim_macro.gain_step` defaults to `0.1`; valid range: finite; overrides gain_step.
- `baseband_offset_gain_trim_macro.offset_lsb` defaults to `0.025`; valid range: finite; overrides offset_lsb.
- `baseband_offset_gain_trim_macro.tr` defaults to `150p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_OR_LOW_ENABLE_DRIVES_VOUT`: restore: Reset or low `enable` drives `vout` to common mode, clears residual metric, and clears `valid`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `offset_2`, `offset_1`, `offset_0`, `vout`, `residual_metric`, `valid`.
- `P_ON_EACH_ENABLED_RISING_CLK_SAMPLE`: restore: On each enabled rising `clk`, sample gain and offset trim codes. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `offset_2`, `offset_1`, `offset_0`, `vout`, `residual_metric`, `valid`.
- `P_USE_GAIN_GAIN_BASE_GAIN_STEP`: restore: Use `gain = gain_base + gain_step * gain_code`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `offset_2`, `offset_1`, `offset_0`, `vout`, `residual_metric`, `valid`.
- `P_USE_SIGNED_OFFSET_OFFSET_CODE_3`: restore: Use signed offset `(offset_code - 3) * offset_lsb`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `offset_2`, `offset_1`, `offset_0`, `vout`, `residual_metric`, `valid`.
- `P_DRIVE_VOUT_AS_THE_CLIPPED_GAIN`: restore: Drive `vout` as the clipped gain-and-offset adjusted input around common mode. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `offset_2`, `offset_1`, `offset_0`, `vout`, `residual_metric`, `valid`.
- `P_RESIDUAL_METRIC_REPORTS_THE_ABSOLUTE_OUTPUT`: restore: `residual_metric` reports the absolute output distance from common mode and `valid` marks that a trim sample has occurred. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `offset_2`, `offset_1`, `offset_0`, `vout`, `residual_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `baseband_offset_gain_trim_macro.va`.
Every supplied `.va` file is editable; do not add or omit files.
