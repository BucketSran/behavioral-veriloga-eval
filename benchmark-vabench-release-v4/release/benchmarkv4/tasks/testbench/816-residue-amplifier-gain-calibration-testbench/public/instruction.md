# Residue Amplifier Gain-calibration Loop Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Residue Amplifier Gain-calibration Loop` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `residue_amp_gain_calibration_top.va`:
  - Module `residue_amp_gain_calibration_top` (entry)
    - position 0: `vin` (inout, electrical)
    - position 1: `residue_ref` (inout, electrical)
    - position 2: `clk` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `cal_en` (inout, electrical)
    - position 5: `gain_2` (inout, electrical)
    - position 6: `gain_1` (inout, electrical)
    - position 7: `gain_0` (inout, electrical)
    - position 8: `vout` (inout, electrical)
    - position 9: `error_metric` (inout, electrical)
    - position 10: `locked` (inout, electrical)
- Artifact `residue_amp_core.va`:
  - Module `residue_amp_core` (required_submodule)
    - position 0: `vin` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `cal_en` (inout, electrical)
    - position 3: `gain_2` (inout, electrical)
    - position 4: `gain_1` (inout, electrical)
    - position 5: `gain_0` (inout, electrical)
    - position 6: `vout` (inout, electrical)
- Artifact `gain_cal_controller.va`:
  - Module `gain_cal_controller` (required_submodule)
    - position 0: `residue` (inout, electrical)
    - position 1: `residue_ref` (inout, electrical)
    - position 2: `clk` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `cal_en` (inout, electrical)
    - position 5: `gain_2` (inout, electrical)
    - position 6: `gain_1` (inout, electrical)
    - position 7: `gain_0` (inout, electrical)
    - position 8: `error_metric` (inout, electrical)
    - position 9: `locked` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `residue_amp_gain_calibration_top` as `XDUT` with ordered public binding: vin=vin, residue_ref=residue_ref, clk=clk, rst=rst, cal_en=cal_en, gain_2=gain_2, gain_1=gain_1, gain_0=gain_0, vout=vout, error_metric=error_metric, locked=locked.

## Public Parameter Contract

- `residue_amp_gain_calibration_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `residue_amp_gain_calibration_top.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `residue_amp_gain_calibration_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `residue_amp_gain_calibration_top.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `residue_amp_gain_calibration_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `residue_amp_gain_calibration_top.base_gain` defaults to `2.0`; valid range: finite; overrides base_gain.
- `residue_amp_gain_calibration_top.gain_lsb` defaults to `0.25`; valid range: finite; overrides gain_lsb.
- `residue_amp_gain_calibration_top.lock_tol` defaults to `15e-3`; valid range: finite; overrides lock_tol.
- `residue_amp_core.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `residue_amp_core.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `residue_amp_core.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `residue_amp_core.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `residue_amp_core.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `residue_amp_core.base_gain` defaults to `2.0`; valid range: finite; overrides base_gain.
- `residue_amp_core.gain_lsb` defaults to `0.25`; valid range: finite; overrides gain_lsb.
- `residue_amp_core.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.
- `gain_cal_controller.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `gain_cal_controller.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `gain_cal_controller.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `gain_cal_controller.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `gain_cal_controller.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `gain_cal_controller.lock_tol` defaults to `15e-3`; valid range: finite; overrides lock_tol.
- `gain_cal_controller.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_CLEAR_GAIN_CODE_OUTPUT`: exercise and make observable: On reset, clear gain code, output, error metric, and `locked`. Required traces: `time`, `vin`, `residue_ref`, `clk`, `rst`, `cal_en`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `locked`.
- `P_WHILE_CAL_EN_IS_HIGH_COMPARE`: exercise and make observable: While `cal_en` is high, compare the current residue output against `residue_ref` on each rising `clk` edge. Required traces: `time`, `vin`, `residue_ref`, `clk`, `rst`, `cal_en`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `locked`.
- `P_INCREMENT_OR_DECREMENT_THE_GAIN_CODE`: exercise and make observable: Increment or decrement the gain code by one step to reduce the signed error. Required traces: `time`, `vin`, `residue_ref`, `clk`, `rst`, `cal_en`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `locked`.
- `P_DRIVE_VOUT_AS_A_CLAMPED_RESIDUE`: exercise and make observable: Drive `vout` as a clamped residue-amplified version of `vin - vcm` using the active gain code. Required traces: `time`, `vin`, `residue_ref`, `clk`, `rst`, `cal_en`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `locked`.
- `P_ASSERT_LOCKED_AFTER_THREE_CONSECUTIVE_UPDATES`: exercise and make observable: Assert `locked` after three consecutive updates with error magnitude below `lock_tol`. Required traces: `time`, `vin`, `residue_ref`, `clk`, `rst`, `cal_en`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `locked`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: exercise and make observable: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vin`, `residue_ref`, `clk`, `rst`, `cal_en`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `locked`.

The required trace names are: `time`, `vin`, `residue_ref`, `clk`, `rst`, `cal_en`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `locked`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
