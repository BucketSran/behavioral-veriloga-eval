# DFE Error-proxy Loop

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `dfe_error_proxy_loop_top.va`, `decision_history.va`, `feedback_correction_core.va`
- Public top module: `dfe_error_proxy_loop_top`
- Required public modules: `dfe_error_proxy_loop_top`, `decision_history`, `feedback_correction_core`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the top-level DUT entry point; helper modules must be part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `dfe_error_proxy_loop_top` with positional electrical ports `sample_in, decision_clk, rst, enable, tap_1, tap_0, corrected_out, error_metric, converged`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.
- `residual_tol = 35e-3 V`: convergence tolerance.

## Required Behavior

- On reset or when disabled, clear taps, corrected output, error metric, and `converged`.
- On each enabled decision clock, latch the sign of `sample_in - vcm` as the current decision.
- Use the previous decision history to subtract a two-tap feedback estimate from the live sample.
- Expose the absolute residual on `error_metric`.
- Assert `converged` when the residual remains below `residual_tol` for three decisions.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. Keep required public modules present and meaningful, and keep top-level behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `dfe_error_proxy_loop_top.va`
- `decision_history.va`
- `feedback_correction_core.va`
