# SST Driver Impedance Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `sst_driver_macro.va`:
  - Module `sst_driver_macro` (entry)
    - position 0: `data` (input, electrical)
    - position 1: `enable` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `z_2` (input, electrical)
    - position 5: `z_1` (input, electrical)
    - position 6: `z_0` (input, electrical)
    - position 7: `vout` (output, electrical)
    - position 8: `swing_metric` (output, electrical)
    - position 9: `z_metric` (output, electrical)

## Public Parameter Contract

- `sst_driver_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module sst_driver_macro.
- `sst_driver_macro.vss` defaults to `0.0`; valid range: finite; overrides vss for module sst_driver_macro.
- `sst_driver_macro.vcm` defaults to `0.45`; valid range: finite; overrides vcm for module sst_driver_macro.
- `sst_driver_macro.vth` defaults to `0.45`; valid range: finite; overrides vth for module sst_driver_macro.
- `sst_driver_macro.swing_min` defaults to `0.15`; valid range: finite; overrides swing_min for module sst_driver_macro.
- `sst_driver_macro.swing_lsb` defaults to `25e-3`; valid range: finite; overrides swing_lsb for module sst_driver_macro.
- `sst_driver_macro.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr for module sst_driver_macro.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CLEAR`: restore: Reset or low enable drives common mode and clears public metrics. Required traces: `time`, `rst`, `enable`, `vout`, `swing_metric`, `z_metric`.
- `P_CLOCKED_DATA`: restore: The data decision updates only on enabled rising clock edges. Required traces: `time`, `data`, `enable`, `clk`, `rst`, `vout`.
- `P_SWING_MAPPING`: restore: The trim code selects swing_min plus swing_lsb per code step. Required traces: `time`, `z_2`, `z_1`, `z_0`, `vout`, `swing_metric`.
- `P_DATA_POLARITY`: restore: High and low latched data drive equal-polarity swings around VCM. Required traces: `time`, `data`, `clk`, `rst`, `enable`, `vout`, `swing_metric`.
- `P_TRIM_METRIC`: restore: The trim metric maps unsigned codes 0 and 7 to the public rails linearly. Required traces: `time`, `z_2`, `z_1`, `z_0`, `z_metric`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Preserve the declared module graph, port order, parameter override behavior, and public trace observability.
- Do not hard-code evaluator stimulus, stop times, sample windows, checker tolerances, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `sst_driver_macro.va`.
Every supplied `.va` file is editable; do not add or omit files.
