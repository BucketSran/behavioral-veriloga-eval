# FFE Tap Adaptation Monitor

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `ffe_tap_adaptation_monitor_top.va`, `tap_update_controller.va`, `cursor_metric_core.va`
- Public top module: `ffe_tap_adaptation_monitor_top`
- Required public modules: `ffe_tap_adaptation_monitor_top`, `tap_update_controller`, `cursor_metric_core`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the top-level DUT entry point; helper modules must be part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `ffe_tap_adaptation_monitor_top` with positional electrical ports `err_in, clk, rst, enable, tap_pre, tap_post, main_out, adapt_metric, done`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, clear tap states, output, adapt metric, and `done`.
- On each enabled rising `clk` edge, update pre and post tap signs according to `err_in - vcm`.
- Drive `main_out` as the current main cursor correction around `vcm`.
- Expose aggregate tap magnitude on `adapt_metric`.
- Assert `done` after six enabled adaptation updates.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. Keep required public modules present and meaningful, and keep top-level behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `ffe_tap_adaptation_monitor_top.va`
- `tap_update_controller.va`
- `cursor_metric_core.va`
