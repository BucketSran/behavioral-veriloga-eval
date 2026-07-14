# LNA Gain-compression Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `lna_gain_compression_macro.va`:
  - Module `lna_gain_compression_macro` (entry)
    - position 0: `vin` (inout, electrical)
    - position 1: `enable` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `vout` (inout, electrical)
    - position 4: `gain_metric` (inout, electrical)
    - position 5: `compression_flag` (inout, electrical)

## Public Parameter Contract

- `lna_gain_compression_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `lna_gain_compression_macro.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `lna_gain_compression_macro.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `lna_gain_compression_macro.small_gain` defaults to `4.0`; valid range: finite; overrides small_gain.
- `lna_gain_compression_macro.input_clip` defaults to `0.18`; valid range: finite; overrides input_clip.
- `lna_gain_compression_macro.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `lna_gain_compression_macro.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: restore: On reset or when disabled, drive `vout` to `vcm`, clear `gain_metric`, and clear `compression_flag`. Required traces: `time`, `vin`, `enable`, `rst`, `vout`, `gain_metric`, `compression_flag`.
- `P_WHEN_ENABLED_PROVIDE_HIGH_GAIN_FOR`: restore: When enabled, provide high gain for small input deviations around `vcm`. Required traces: `time`, `vin`, `enable`, `rst`, `vout`, `gain_metric`, `compression_flag`.
- `P_REDUCE_EFFECTIVE_GAIN_MONOTONICALLY_WHEN_THE`: restore: Reduce effective gain monotonically when the absolute input deviation exceeds `input_clip`. Required traces: `time`, `vin`, `enable`, `rst`, `vout`, `gain_metric`, `compression_flag`.
- `P_EXPOSE_ACTIVE_GAIN_ON_GAIN_METRIC`: restore: Expose active gain on `gain_metric` and assert `compression_flag` during compressed operation. Required traces: `time`, `vin`, `enable`, `rst`, `vout`, `gain_metric`, `compression_flag`.
- `P_CLAMP_VOUT_INSIDE_VSS_VDD`: restore: Clamp `vout` inside `[vss, vdd]`. Required traces: `time`, `vin`, `enable`, `rst`, `vout`, `gain_metric`, `compression_flag`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `lna_gain_compression_macro.va`.
Every supplied `.va` file is editable; do not add or omit files.
