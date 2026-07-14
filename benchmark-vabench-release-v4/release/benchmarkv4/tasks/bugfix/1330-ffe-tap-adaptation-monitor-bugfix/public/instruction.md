# FFE Tap Adaptation Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

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

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear tap states, output, adapt metric, and `done`. Required traces: `time`, `err_in`, `clk`, `rst`, `enable`, `tap_pre`, `tap_post`, `main_out`, `adapt_metric`, `done`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: restore: On each enabled rising `clk` edge, update pre and post tap signs according to `err_in - vcm`. Required traces: `time`, `err_in`, `clk`, `rst`, `enable`, `tap_pre`, `tap_post`, `main_out`, `adapt_metric`, `done`.
- `P_DRIVE_MAIN_OUT_AS_THE_CURRENT`: restore: Drive `main_out` as the current main cursor correction around `vcm`. Required traces: `time`, `err_in`, `clk`, `rst`, `enable`, `tap_pre`, `tap_post`, `main_out`, `adapt_metric`, `done`.
- `P_EXPOSE_AGGREGATE_TAP_MAGNITUDE_ON_ADAPT`: restore: Expose aggregate tap magnitude on `adapt_metric`. Required traces: `time`, `err_in`, `clk`, `rst`, `enable`, `tap_pre`, `tap_post`, `main_out`, `adapt_metric`, `done`.
- `P_ASSERT_DONE_AFTER_SIX_ENABLED_ADAPTATION`: restore: Assert `done` after six enabled adaptation updates. Required traces: `time`, `err_in`, `clk`, `rst`, `enable`, `tap_pre`, `tap_post`, `main_out`, `adapt_metric`, `done`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `ffe_tap_adaptation_monitor_top.va`, `tap_update_controller.va`, `cursor_metric_core.va`.
Every supplied `.va` file is editable; do not add or omit files.
