# FFE Tap Adaptation Monitor Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `FFE Tap Adaptation Monitor` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `ffe_tap_adaptation_monitor_top.va`:
  - Module `ffe_tap_adaptation_monitor_top` (entry)
    - position 0: `err_in` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `tap_pre` (inout, electrical)
    - position 5: `tap_post` (inout, electrical)
    - position 6: `main_out` (inout, electrical)
    - position 7: `adapt_metric` (inout, electrical)
    - position 8: `done` (inout, electrical)
- Artifact `tap_update_controller.va`:
  - Module `tap_update_controller` (required_submodule)
    - position 0: `err_in` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `tap_pre` (inout, electrical)
    - position 5: `tap_post` (inout, electrical)
    - position 6: `done` (inout, electrical)
- Artifact `cursor_metric_core.va`:
  - Module `cursor_metric_core` (required_submodule)
    - position 0: `err_in` (inout, electrical)
    - position 1: `tap_pre` (inout, electrical)
    - position 2: `tap_post` (inout, electrical)
    - position 3: `main_out` (inout, electrical)
    - position 4: `adapt_metric` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `ffe_tap_adaptation_monitor_top` as `XDUT` with ordered public binding: err_in=err_in, clk=clk, rst=rst, enable=enable, tap_pre=tap_pre, tap_post=tap_post, main_out=main_out, adapt_metric=adapt_metric, done=done.

## Public Parameter Contract

- `ffe_tap_adaptation_monitor_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `ffe_tap_adaptation_monitor_top.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `ffe_tap_adaptation_monitor_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `ffe_tap_adaptation_monitor_top.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `ffe_tap_adaptation_monitor_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `ffe_tap_adaptation_monitor_top.tap_limit` defaults to `3`; valid range: positive; sets the signed tap-code saturation limit in the controller.
- `tap_update_controller.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `tap_update_controller.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `tap_update_controller.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `tap_update_controller.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `tap_update_controller.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `tap_update_controller.tap_limit` defaults to `3`; valid range: positive; sets the signed tap-code saturation limit.
- `cursor_metric_core.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `cursor_metric_core.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `cursor_metric_core.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `cursor_metric_core.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: exercise and make observable: On reset or when disabled, clear tap states, output, adapt metric, and `done`. Required traces: `time`, `err_in`, `clk`, `rst`, `enable`, `tap_pre`, `tap_post`, `main_out`, `adapt_metric`, `done`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: exercise and make observable: On each enabled rising `clk` edge, update pre and post tap signs according to `err_in - vcm`. Required traces: `time`, `err_in`, `clk`, `rst`, `enable`, `tap_pre`, `tap_post`, `main_out`, `adapt_metric`, `done`.
- `P_DRIVE_MAIN_OUT_AS_THE_CURRENT`: exercise and make observable: Drive `main_out` as the current main cursor correction around `vcm`. Required traces: `time`, `err_in`, `clk`, `rst`, `enable`, `tap_pre`, `tap_post`, `main_out`, `adapt_metric`, `done`.
- `P_EXPOSE_AGGREGATE_TAP_MAGNITUDE_ON_ADAPT`: exercise and make observable: Expose aggregate tap magnitude on `adapt_metric`. Required traces: `time`, `err_in`, `clk`, `rst`, `enable`, `tap_pre`, `tap_post`, `main_out`, `adapt_metric`, `done`.
- `P_ASSERT_DONE_AFTER_SIX_ENABLED_ADAPTATION`: exercise and make observable: Assert `done` after six enabled adaptation updates. Required traces: `time`, `err_in`, `clk`, `rst`, `enable`, `tap_pre`, `tap_post`, `main_out`, `adapt_metric`, `done`.

The required trace names are: `time`, `err_in`, `clk`, `rst`, `enable`, `tap_pre`, `tap_post`, `main_out`, `adapt_metric`, `done`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
