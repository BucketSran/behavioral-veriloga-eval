# 2-tap DFE Receiver

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `dfe_rx_top.va`, `slicer.va`, `feedback_filter.va`, `decision_latch.va`
- Public top module: `dfe_rx_top`
- Required public modules: `dfe_rx_top`, `slicer`, `feedback_filter`, `decision_latch`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `dfe_rx_top` with positional electrical ports `vin, clk, rst, tap1_1, tap1_0, tap2_1, tap2_0, decision, fb_metric, slicer_in_dbg`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vcm = 0.45 V`: slicer threshold center.
- `vth = 0.45 V`: threshold for clock, reset, and tap-code inputs.
- `tap_lsb = 20e-3 V`: feedback correction per tap-code step.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset, clear the decision history, `decision`, `fb_metric`, and `slicer_in_dbg`.
- On each rising `clk` edge, `feedback_filter` must compute feedback from the previous two decisions only.
- The current slicer input is `V(vin)` minus the computed feedback correction.
- `slicer` must drive the new decision high when the corrected slicer input is greater than or equal to `vcm`, otherwise low.
- `decision_latch` must update the two-decision history after the new decision is produced.
- `fb_metric` must expose the signed feedback correction used for the active decision.
- `slicer_in_dbg` must expose the corrected slicer input used by the active decision.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `dfe_rx_top.va`
- `slicer.va`
- `feedback_filter.va`
- `decision_latch.va`
