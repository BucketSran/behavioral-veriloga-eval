# PA Gain-compression and AM/PM Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `PA Gain-compression and AM/PM Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `pa_gain_compression_ampm_macro` as `XDUT` with ordered public binding: vin=vin, envelope=envelope, enable=enable, rst=rst, vout=vout, gain_metric=gain_metric, phase_metric=phase_metric, compressed=compressed.

## Public Parameter Contract

- `pa_gain_compression_ampm_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `pa_gain_compression_ampm_macro.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `pa_gain_compression_ampm_macro.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `pa_gain_compression_ampm_macro.small_gain` defaults to `3.0`; valid range: finite; overrides small_gain.
- `pa_gain_compression_ampm_macro.comp_threshold` defaults to `0.2`; valid range: finite; overrides comp_threshold.
- `pa_gain_compression_ampm_macro.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `pa_gain_compression_ampm_macro.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: exercise and make observable: On reset or when disabled, drive `vout` to `vcm`, clear metrics, and clear `compressed`. Required traces: `time`, `vin`, `envelope`, `enable`, `rst`, `vout`, `gain_metric`, `phase_metric`, `compressed`.
- `P_WHEN_ENABLED_AMPLIFY_VIN_VCM_WITH`: exercise and make observable: When enabled, amplify `vin - vcm` with high small-signal gain at low envelope. Required traces: `time`, `vin`, `envelope`, `enable`, `rst`, `vout`, `gain_metric`, `phase_metric`, `compressed`.
- `P_AS_ENVELOPE_EXCEEDS_THE_COMPRESSION_THRESHOLD`: exercise and make observable: As `envelope` exceeds the compression threshold, reduce the effective gain monotonically. Required traces: `time`, `vin`, `envelope`, `enable`, `rst`, `vout`, `gain_metric`, `phase_metric`, `compressed`.
- `P_EXPOSE_THE_ACTIVE_GAIN_ON_GAIN`: exercise and make observable: Expose the active gain on `gain_metric` and a monotonic AM/PM proxy on `phase_metric`. Required traces: `time`, `vin`, `envelope`, `enable`, `rst`, `vout`, `gain_metric`, `phase_metric`, `compressed`.
- `P_ASSERT_COMPRESSED_WHEN_THE_EFFECTIVE_GAIN`: exercise and make observable: Assert `compressed` when the effective gain is below the small-signal gain by the configured compression condition. Required traces: `time`, `vin`, `envelope`, `enable`, `rst`, `vout`, `gain_metric`, `phase_metric`, `compressed`.
- `P_CLAMP_VOUT_INSIDE_VSS_VDD`: exercise and make observable: Clamp `vout` inside `[vss, vdd]`. Required traces: `time`, `vin`, `envelope`, `enable`, `rst`, `vout`, `gain_metric`, `phase_metric`, `compressed`.

The required trace names are: `time`, `vin`, `envelope`, `enable`, `rst`, `vout`, `gain_metric`, `phase_metric`, `compressed`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
