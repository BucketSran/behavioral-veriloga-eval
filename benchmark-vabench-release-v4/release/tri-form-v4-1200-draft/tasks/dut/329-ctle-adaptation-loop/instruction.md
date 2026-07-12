# CTLE Adaptation Loop

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `ctle_adaptation_loop_top.va`, `ctle_boost_core.va`, `boost_adapt_controller.va`
- Public top module: `ctle_adaptation_loop_top`
- Required public modules: `ctle_adaptation_loop_top`, `ctle_boost_core`, `boost_adapt_controller`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the top-level DUT entry point; helper modules must be part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `ctle_adaptation_loop_top` with positional electrical ports `vin, edge_metric_in, clk, rst, enable, boost_2, boost_1, boost_0, vout, adapt_metric, locked`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.
- `edge_target = 0.55 V`: desired edge metric.
- `adapt_tol = 30e-3 V`: lock tolerance.

## Required Behavior

- On reset or when disabled, clear boost code, output, metric, and `locked`.
- On each enabled rising `clk` edge, compare `edge_metric_in` with `edge_target`.
- Increase boost code when edge metric is too low and decrease it when too high.
- Drive `vout` as a boosted version of `vin - vcm` using the active boost code.
- Assert `locked` after three consecutive updates within the target tolerance.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. Keep required public modules present and meaningful, and keep top-level behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `ctle_adaptation_loop_top.va`
- `ctle_boost_core.va`
- `boost_adapt_controller.va`
