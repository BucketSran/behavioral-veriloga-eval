# PA Gain-compression and AM/PM Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `pa_gain_compression_ampm_macro.va`:
  - Module `pa_gain_compression_ampm_macro` (entry)
    - position 0: `vin` (inout, electrical)
    - position 1: `envelope` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `vout` (inout, electrical)
    - position 5: `gain_metric` (inout, electrical)
    - position 6: `phase_metric` (inout, electrical)
    - position 7: `compressed` (inout, electrical)

## Public Parameter Contract

- `pa_gain_compression_ampm_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `pa_gain_compression_ampm_macro.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `pa_gain_compression_ampm_macro.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `pa_gain_compression_ampm_macro.small_gain` defaults to `3.0`; valid range: finite; overrides small_gain.
- `pa_gain_compression_ampm_macro.comp_threshold` defaults to `0.2`; valid range: finite; overrides comp_threshold.
- `pa_gain_compression_ampm_macro.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `pa_gain_compression_ampm_macro.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: restore: On reset or when disabled, drive `vout` to `vcm`, clear metrics, and clear `compressed`. Required traces: `time`, `vin`, `envelope`, `enable`, `rst`, `vout`, `gain_metric`, `phase_metric`, `compressed`.
- `P_WHEN_ENABLED_AMPLIFY_VIN_VCM_WITH`: restore: When enabled, amplify `vin - vcm` with high small-signal gain at low envelope. Required traces: `time`, `vin`, `envelope`, `enable`, `rst`, `vout`, `gain_metric`, `phase_metric`, `compressed`.
- `P_AS_ENVELOPE_EXCEEDS_THE_COMPRESSION_THRESHOLD`: restore: As `envelope` exceeds the compression threshold, reduce the effective gain monotonically. Required traces: `time`, `vin`, `envelope`, `enable`, `rst`, `vout`, `gain_metric`, `phase_metric`, `compressed`.
- `P_EXPOSE_THE_ACTIVE_GAIN_ON_GAIN`: restore: Expose the active gain on `gain_metric` and a monotonic AM/PM proxy on `phase_metric`. Required traces: `time`, `vin`, `envelope`, `enable`, `rst`, `vout`, `gain_metric`, `phase_metric`, `compressed`.
- `P_ASSERT_COMPRESSED_WHEN_THE_EFFECTIVE_GAIN`: restore: Assert `compressed` when the effective gain is below the small-signal gain by the configured compression condition. Required traces: `time`, `vin`, `envelope`, `enable`, `rst`, `vout`, `gain_metric`, `phase_metric`, `compressed`.
- `P_CLAMP_VOUT_INSIDE_VSS_VDD`: restore: Clamp `vout` inside `[vss, vdd]`. Required traces: `time`, `vin`, `envelope`, `enable`, `rst`, `vout`, `gain_metric`, `phase_metric`, `compressed`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pa_gain_compression_ampm_macro.va`.
Every supplied `.va` file is editable; do not add or omit files.
