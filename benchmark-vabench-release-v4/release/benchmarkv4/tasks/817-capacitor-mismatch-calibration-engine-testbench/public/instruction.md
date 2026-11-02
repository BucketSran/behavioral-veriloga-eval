# Capacitor Mismatch Calibration Engine Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Capacitor Mismatch Calibration Engine` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `capacitor_mismatch_cal_engine_top.va`:
  - Module `capacitor_mismatch_cal_engine_top` (entry)
    - position 0: `err_in` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `cal_3` (inout, electrical)
    - position 5: `cal_2` (inout, electrical)
    - position 6: `cal_1` (inout, electrical)
    - position 7: `cal_0` (inout, electrical)
    - position 8: `correction_metric` (inout, electrical)
    - position 9: `done` (inout, electrical)
- Artifact `cal_code_accumulator.va`:
  - Module `cal_code_accumulator` (required_submodule)
    - position 0: `err_in` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `cal_3` (inout, electrical)
    - position 5: `cal_2` (inout, electrical)
    - position 6: `cal_1` (inout, electrical)
    - position 7: `cal_0` (inout, electrical)
    - position 8: `done` (inout, electrical)
- Artifact `correction_metric_dac.va`:
  - Module `correction_metric_dac` (required_submodule)
    - position 0: `cal_3` (inout, electrical)
    - position 1: `cal_2` (inout, electrical)
    - position 2: `cal_1` (inout, electrical)
    - position 3: `cal_0` (inout, electrical)
    - position 4: `rst` (inout, electrical)
    - position 5: `enable` (inout, electrical)
    - position 6: `correction_metric` (inout, electrical)

Stable public Spectre binding:

The submitted `testbench.scs` must use the supplied DUT through this public binding:

- Include paths: `./dut/capacitor_mismatch_cal_engine_top.va`, `./dut/cal_code_accumulator.va`, `./dut/correction_metric_dac.va`
- DUT instance: `XDUT (err_in clk rst enable cal_3 cal_2 cal_1 cal_0 correction_metric done) capacitor_mismatch_cal_engine_top`
- Required saved public traces: `err_in`, `clk`, `rst`, `enable`, `cal_3`, `cal_2`, `cal_1`, `cal_0`, `correction_metric`, `done`
- Use one bounded transient analysis with a finite positive stop time.

You must design the stimulus yourself. Save traces as bare public signal names
(for example `clk`, not suffixed or hierarchical forms such as `clk:V` or
`XDUT.clk`). Do not redefine the DUT, drive DUT output nets, save
hierarchical/private nodes, or use checker/gold/internal files.

## Public Parameter Contract

- `capacitor_mismatch_cal_engine_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `capacitor_mismatch_cal_engine_top.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `capacitor_mismatch_cal_engine_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `capacitor_mismatch_cal_engine_top.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `capacitor_mismatch_cal_engine_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `capacitor_mismatch_cal_engine_top.err_tol` defaults to `20e-3`; valid range: finite; overrides err_tol.
- `capacitor_mismatch_cal_engine_top.corr_lsb` defaults to `6e-3`; valid range: finite; overrides corr_lsb.
- `cal_code_accumulator.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `cal_code_accumulator.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `cal_code_accumulator.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `cal_code_accumulator.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `cal_code_accumulator.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `cal_code_accumulator.err_tol` defaults to `20e-3`; valid range: finite; overrides err_tol.
- `cal_code_accumulator.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.
- `correction_metric_dac.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `correction_metric_dac.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `correction_metric_dac.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `correction_metric_dac.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `correction_metric_dac.corr_lsb` defaults to `6e-3`; valid range: finite; overrides corr_lsb.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: exercise and make observable: On reset or when disabled, clear the calibration code, metric, and `done`. Required traces: `time`, `err_in`, `clk`, `rst`, `enable`, `cal_3`, `cal_2`, `cal_1`, `cal_0`, `correction_metric`, `done`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: exercise and make observable: On each enabled rising `clk` edge, update a signed correction accumulator using the sign of `err_in - vcm`. Required traces: `time`, `err_in`, `clk`, `rst`, `enable`, `cal_3`, `cal_2`, `cal_1`, `cal_0`, `correction_metric`, `done`.
- `P_SATURATE_THE_PUBLIC_4_BIT_CALIBRATION`: exercise and make observable: Saturate the public 4-bit calibration code at the endpoints. Required traces: `time`, `err_in`, `clk`, `rst`, `enable`, `cal_3`, `cal_2`, `cal_1`, `cal_0`, `correction_metric`, `done`.
- `P_DRIVE_CORRECTION_METRIC_AS_THE_VOLTAGE`: exercise and make observable: Drive `correction_metric` as the voltage-coded correction applied by the active code. Required traces: `time`, `err_in`, `clk`, `rst`, `enable`, `cal_3`, `cal_2`, `cal_1`, `cal_0`, `correction_metric`, `done`.
- `P_ASSERT_DONE_AFTER_EIGHT_ENABLED_UPDATES`: exercise and make observable: Assert `done` after eight enabled updates or when the error remains within `err_tol` for two updates. Required traces: `time`, `err_in`, `clk`, `rst`, `enable`, `cal_3`, `cal_2`, `cal_1`, `cal_0`, `correction_metric`, `done`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: exercise and make observable: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `err_in`, `clk`, `rst`, `enable`, `cal_3`, `cal_2`, `cal_1`, `cal_0`, `correction_metric`, `done`.


The following canonical public behavior is normative for this derived form:

- On reset or when disabled, clear the calibration code, metric, and `done`.
- On each enabled rising `clk` edge, update a signed correction accumulator using the sign of `err_in - vcm`.
- Saturate the public 4-bit calibration code at the endpoints.
- Drive `correction_metric` as the voltage-coded correction applied by the active code.
- Assert `done` after eight enabled updates or when the error remains within `err_tol` for two updates.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.


The required trace names are: `time`, `err_in`, `clk`, `rst`, `enable`, `cal_3`, `cal_2`, `cal_1`, `cal_0`, `correction_metric`, `done`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.

- cal_0+2*cal_1+4*cal_2+8*cal_3

- code*corr_lsb
