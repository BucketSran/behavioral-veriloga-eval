# PA AM/PM Memory Tap Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `pa_ampm_memory_tap_macro.va`:
  - Module `pa_ampm_memory_tap_macro` (entry)
    - position 0: `vin` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `drive` (inout, electrical)
    - position 5: `vout` (inout, electrical)
    - position 6: `am_metric` (inout, electrical)
    - position 7: `pm_metric` (inout, electrical)
    - position 8: `valid` (inout, electrical)

## Public Parameter Contract

- `pa_ampm_memory_tap_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `pa_ampm_memory_tap_macro.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `pa_ampm_memory_tap_macro.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `pa_ampm_memory_tap_macro.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `pa_ampm_memory_tap_macro.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `pa_ampm_memory_tap_macro.drive_start` defaults to `0.55`; valid range: finite; overrides drive_start.
- `pa_ampm_memory_tap_macro.memory_gain` defaults to `0.2`; valid range: finite; overrides memory_gain.
- `pa_ampm_memory_tap_macro.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: restore: On reset or when disabled, drive `vout` to `vcm`, clear metrics, and clear `valid`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `drive`, `vout`, `am_metric`, `pm_metric`, `valid`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: restore: On each enabled rising `clk` edge, sample input amplitude and drive level. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `drive`, `vout`, `am_metric`, `pm_metric`, `valid`.
- `P_APPLY_AN_AM_GAIN_COMPRESSION_PROXY`: restore: Apply an AM gain compression proxy as drive increases. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `drive`, `vout`, `am_metric`, `pm_metric`, `valid`.
- `P_APPLY_A_ONE_SAMPLE_MEMORY_TERM`: restore: Apply a one-sample memory term that changes output polarity metric after large input changes. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `drive`, `vout`, `am_metric`, `pm_metric`, `valid`.
- `P_EXPOSE_AM_AND_PM_PROXIES_SEPARATELY`: restore: Expose AM and PM proxies separately and assert `valid` after the first update. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `drive`, `vout`, `am_metric`, `pm_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pa_ampm_memory_tap_macro.va`.
Every supplied `.va` file is editable; do not add or omit files.
