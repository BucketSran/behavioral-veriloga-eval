# DFE Error-proxy Loop Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `DFE Error-proxy Loop` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `dfe_error_proxy_loop_top` as `XDUT` with ordered public binding: sample_in=sample_in, decision_clk=decision_clk, rst=rst, enable=enable, tap_1=tap_1, tap_0=tap_0, corrected_out=corrected_out, error_metric=error_metric, converged=converged.

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

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: exercise and make observable: On reset or when disabled, clear taps, corrected output, error metric, and `converged`. Required traces: `time`, `sample_in`, `decision_clk`, `rst`, `enable`, `tap_1`, `tap_0`, `corrected_out`, `error_metric`, `converged`.
- `P_ON_EACH_ENABLED_DECISION_CLOCK_LATCH`: exercise and make observable: On each enabled decision clock, latch the sign of `sample_in - vcm` as the current decision. Required traces: `time`, `sample_in`, `decision_clk`, `rst`, `enable`, `tap_1`, `tap_0`, `corrected_out`, `error_metric`, `converged`.
- `P_USE_THE_PREVIOUS_DECISION_HISTORY_TO`: exercise and make observable: Use the previous decision history to subtract a two-tap feedback estimate from the live sample. Required traces: `time`, `sample_in`, `decision_clk`, `rst`, `enable`, `tap_1`, `tap_0`, `corrected_out`, `error_metric`, `converged`.
- `P_EXPOSE_THE_ABSOLUTE_RESIDUAL_ON_ERROR`: exercise and make observable: Expose the absolute residual on `error_metric`. Required traces: `time`, `sample_in`, `decision_clk`, `rst`, `enable`, `tap_1`, `tap_0`, `corrected_out`, `error_metric`, `converged`.
- `P_ASSERT_CONVERGED_WHEN_THE_RESIDUAL_REMAINS`: exercise and make observable: Assert `converged` when the residual remains below `residual_tol` for three decisions. Required traces: `time`, `sample_in`, `decision_clk`, `rst`, `enable`, `tap_1`, `tap_0`, `corrected_out`, `error_metric`, `converged`.

The required trace names are: `time`, `sample_in`, `decision_clk`, `rst`, `enable`, `tap_1`, `tap_0`, `corrected_out`, `error_metric`, `converged`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
