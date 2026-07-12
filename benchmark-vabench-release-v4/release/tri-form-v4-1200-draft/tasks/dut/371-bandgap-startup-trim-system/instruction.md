# Bandgap Startup and Trim System

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `bandgap_trim_top.va`, `startup_detector.va`, `ptat_ctat_core.va`, `trim_controller.va`
- Public top module: `bandgap_trim_top`
- Required public modules: `bandgap_trim_top`, `startup_detector`, `ptat_ctat_core`, `trim_controller`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `bandgap_trim_top` with positional electrical ports `vdd_sense, clk, rst, trim_req, temp_proxy, vref, trim_3, trim_2, trim_1, trim_0, ready, error_metric`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vhi = 0.9 V`: logic high output level.
- `vlo = 0.0 V`: logic low output level.
- `vpor = 0.72 V`: startup threshold for `vdd_sense`.
- `vref_nom = 0.6 V`: nominal reference target.
- `trim_lsb = 2e-3 V`: reference correction per trim-code step.
- `ready_tol = 5e-3 V`: ready tolerance around the reference target.
- `vth = 0.45 V`: threshold for clock, reset, and trim request.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when `vdd_sense` is below `vpor`, clear the trim code, `ready`, `error_metric`, and drive `vref` low.
- `startup_detector` enables the reference only after `vdd_sense` has been above `vpor` for two consecutive rising `clk` edges.
- `ptat_ctat_core` must generate a behavioral reference metric from `temp_proxy` around `vref_nom`.
- When `trim_req` is high, `trim_controller` updates the 4-bit trim code once per rising `clk` edge to reduce reference error.
- `vref` must reflect the core reference plus trim correction and remain clamped between `vlo` and `vhi`.
- Drive `trim_3..trim_0` as voltage-coded copies of the trim code.
- Assert `ready` after three consecutive enabled updates with `error_metric` magnitude within `ready_tol`.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `bandgap_trim_top.va`
- `startup_detector.va`
- `ptat_ctat_core.va`
- `trim_controller.va`
