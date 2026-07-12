# VGA Step-response Classifier Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `VGA Step-response Classifier` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `vga_step_response_classifier.va`:
  - Module `vga_step_response_classifier` (entry)
    - position 0: `vin` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `gain_2` (inout, electrical)
    - position 5: `gain_1` (inout, electrical)
    - position 6: `gain_0` (inout, electrical)
    - position 7: `vout` (inout, electrical)
    - position 8: `overshoot_metric` (inout, electrical)
    - position 9: `settled` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `vga_step_response_classifier` as `XDUT` with ordered public binding: vin=vin, clk=clk, rst=rst, enable=enable, gain_2=gain_2, gain_1=gain_1, gain_0=gain_0, vout=vout, overshoot_metric=overshoot_metric, settled=settled.

## Public Parameter Contract

- `vga_step_response_classifier.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `vga_step_response_classifier.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `vga_step_response_classifier.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `vga_step_response_classifier.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `vga_step_response_classifier.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `vga_step_response_classifier.gain_lsb` defaults to `0.5`; valid range: finite; overrides gain_lsb.
- `vga_step_response_classifier.settle_tol` defaults to `12e-3`; valid range: finite; overrides settle_tol.
- `vga_step_response_classifier.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: exercise and make observable: On reset or when disabled, drive `vout` to `vcm`, clear metric, and clear `settled`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `overshoot_metric`, `settled`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: exercise and make observable: On each enabled rising `clk` edge, decode the gain code and update the target output from `vin`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `overshoot_metric`, `settled`.
- `P_APPLY_BOUNDED_SETTLING_WITH_A_CODE`: exercise and make observable: Apply bounded settling with a code-dependent overshoot proxy after large gain changes. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `overshoot_metric`, `settled`.
- `P_EXPOSE_OVERSHOOT_MAGNITUDE_ON_OVERSHOOT_METRIC`: exercise and make observable: Expose overshoot magnitude on `overshoot_metric`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `overshoot_metric`, `settled`.
- `P_ASSERT_SETTLED_AFTER_TWO_CONSECUTIVE_UPDATES`: exercise and make observable: Assert `settled` after two consecutive updates within `settle_tol` of the target. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `overshoot_metric`, `settled`.

The required trace names are: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `overshoot_metric`, `settled`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
