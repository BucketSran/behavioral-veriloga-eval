# Op-amp Feedback Settling Monitor Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Op-amp Feedback Settling Monitor` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `opamp_feedback_settling.va`:
  - Module `opamp_feedback_settling` (entry)
    - position 0: `vin` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `gain_2` (inout, electrical)
    - position 5: `gain_1` (inout, electrical)
    - position 6: `gain_0` (inout, electrical)
    - position 7: `vout` (inout, electrical)
    - position 8: `error_metric` (inout, electrical)
    - position 9: `settled` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `opamp_feedback_settling` as `XDUT` with ordered public binding: vin=vin, clk=clk, rst=rst, enable=enable, gain_2=gain_2, gain_1=gain_1, gain_0=gain_0, vout=vout, error_metric=error_metric, settled=settled.

## Public Parameter Contract

- `opamp_feedback_settling.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `opamp_feedback_settling.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `opamp_feedback_settling.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `opamp_feedback_settling.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `opamp_feedback_settling.gain_lsb` defaults to `0.5`; valid range: finite; overrides gain_lsb.
- `opamp_feedback_settling.alpha` defaults to `0.3`; valid range: finite; overrides alpha.
- `opamp_feedback_settling.settle_tol` defaults to `40e-3`; valid range: finite; overrides settle_tol.
- `opamp_feedback_settling.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `opamp_feedback_settling.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_ENABLE_IS`: exercise and make observable: On reset or when `enable` is low, drive `vout` to `vcm`, clear `error_metric`, and clear `settled`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `settled`.
- `P_DECODE_GAIN_2_GAIN_0_INTO`: exercise and make observable: Decode `gain_2..gain_0` into a closed-loop target gain of at least unity. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `settled`.
- `P_UPDATE_VOUT_ONCE_PER_RISING_CLK`: exercise and make observable: Update `vout` once per rising `clk` edge toward the target closed-loop output using `alpha`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `settled`.
- `P_CLAMP_VOUT_TO_THE_RANGE_VSS`: exercise and make observable: Clamp `vout` to the range `vss` through `vdd`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `settled`.
- `P_ERROR_METRIC_MUST_EXPOSE_THE_SIGNED`: exercise and make observable: `error_metric` must expose the signed difference between the current output and the target closed-loop value. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `settled`.
- `P_ASSERT_SETTLED_AFTER_THREE_CONSECUTIVE_UPDATES`: exercise and make observable: Assert `settled` after three consecutive updates where the absolute error is below `settle_tol`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `settled`.

The required trace names are: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `settled`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
