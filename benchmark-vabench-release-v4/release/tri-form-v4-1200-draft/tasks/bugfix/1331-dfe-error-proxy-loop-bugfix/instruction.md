# DFE Error-proxy Loop Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `dfe_error_proxy_loop_top.va`:
  - Module `dfe_error_proxy_loop_top` (entry)
    - position 0: `sample_in` (inout, electrical)
    - position 1: `decision_clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `tap_1` (inout, electrical)
    - position 5: `tap_0` (inout, electrical)
    - position 6: `corrected_out` (inout, electrical)
    - position 7: `error_metric` (inout, electrical)
    - position 8: `converged` (inout, electrical)
- Artifact `decision_history.va`:
  - Module `decision_history` (required_submodule)
    - position 0: `a` (inout, electrical)
    - position 1: `b` (inout, electrical)
- Artifact `feedback_correction_core.va`:
  - Module `feedback_correction_core` (required_submodule)
    - position 0: `a` (inout, electrical)
    - position 1: `b` (inout, electrical)

## Public Parameter Contract

- `dfe_error_proxy_loop_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `dfe_error_proxy_loop_top.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `dfe_error_proxy_loop_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `dfe_error_proxy_loop_top.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `dfe_error_proxy_loop_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `dfe_error_proxy_loop_top.tick` defaults to `1n from (0:inf)`; valid range: finite; overrides tick.
- `decision_history.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `feedback_correction_core.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear taps, corrected output, error metric, and `converged`. Required traces: `time`, `sample_in`, `decision_clk`, `rst`, `enable`, `tap_1`, `tap_0`, `corrected_out`, `error_metric`, `converged`.
- `P_ON_EACH_ENABLED_DECISION_CLOCK_LATCH`: restore: On each enabled decision clock, latch the sign of `sample_in - vcm` as the current decision. Required traces: `time`, `sample_in`, `decision_clk`, `rst`, `enable`, `tap_1`, `tap_0`, `corrected_out`, `error_metric`, `converged`.
- `P_USE_THE_PREVIOUS_DECISION_HISTORY_TO`: restore: Use the previous decision history to subtract a two-tap feedback estimate from the live sample. Required traces: `time`, `sample_in`, `decision_clk`, `rst`, `enable`, `tap_1`, `tap_0`, `corrected_out`, `error_metric`, `converged`.
- `P_EXPOSE_THE_ABSOLUTE_RESIDUAL_ON_ERROR`: restore: Expose the absolute residual on `error_metric`. Required traces: `time`, `sample_in`, `decision_clk`, `rst`, `enable`, `tap_1`, `tap_0`, `corrected_out`, `error_metric`, `converged`.
- `P_ASSERT_CONVERGED_WHEN_THE_RESIDUAL_REMAINS`: restore: Assert `converged` when the residual remains below `residual_tol` for three decisions. Required traces: `time`, `sample_in`, `decision_clk`, `rst`, `enable`, `tap_1`, `tap_0`, `corrected_out`, `error_metric`, `converged`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `dfe_error_proxy_loop_top.va`, `decision_history.va`, `feedback_correction_core.va`.
Every supplied `.va` file is editable; do not add or omit files.
