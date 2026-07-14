# PA AM/PM Memory Tap Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `PA AM/PM Memory Tap Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `pa_ampm_memory_tap_macro` as `XDUT` with ordered public binding: vin=vin, clk=clk, rst=rst, enable=enable, drive=drive, vout=vout, am_metric=am_metric, pm_metric=pm_metric, valid=valid.

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

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: exercise and make observable: On reset or when disabled, drive `vout` to `vcm`, clear metrics, and clear `valid`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `drive`, `vout`, `am_metric`, `pm_metric`, `valid`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: exercise and make observable: On each enabled rising `clk` edge, sample input amplitude and drive level. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `drive`, `vout`, `am_metric`, `pm_metric`, `valid`.
- `P_APPLY_AN_AM_GAIN_COMPRESSION_PROXY`: exercise and make observable: Apply an AM gain compression proxy as drive increases. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `drive`, `vout`, `am_metric`, `pm_metric`, `valid`.
- `P_APPLY_A_ONE_SAMPLE_MEMORY_TERM`: exercise and make observable: Apply a one-sample memory term that changes output polarity metric after large input changes. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `drive`, `vout`, `am_metric`, `pm_metric`, `valid`.
- `P_EXPOSE_AM_AND_PM_PROXIES_SEPARATELY`: exercise and make observable: Expose AM and PM proxies separately and assert `valid` after the first update. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `drive`, `vout`, `am_metric`, `pm_metric`, `valid`.

The required trace names are: `time`, `vin`, `clk`, `rst`, `enable`, `drive`, `vout`, `am_metric`, `pm_metric`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
