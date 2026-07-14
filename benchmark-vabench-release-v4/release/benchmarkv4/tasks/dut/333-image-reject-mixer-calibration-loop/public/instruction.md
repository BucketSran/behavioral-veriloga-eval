# Image-reject Mixer Calibration Loop

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `image_reject_mixer_cal_loop_top.va`, `quadrature_mixer_proxy.va`, `image_cal_controller.va`
- Public top module: `image_reject_mixer_cal_loop_top`
- Required public modules: `image_reject_mixer_cal_loop_top`, `quadrature_mixer_proxy`, `image_cal_controller`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the top-level DUT entry point; helper modules must be part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `image_reject_mixer_cal_loop_top` with positional electrical ports `rf_in, lo_i, lo_q, clk, rst, enable, i_out, q_out, image_metric, calibrated`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.
- `image_tol = 40e-3 V`: calibration threshold.

## Required Behavior

- On reset or when disabled, clear outputs, image metric, and `calibrated`.
- On each enabled rising `clk` edge, sample RF and quadrature LO inputs as voltage-domain mixer proxies.
- Generate I and Q outputs using opposite LO polarities.
- Update a simple gain/phase correction state to reduce the image metric.
- Assert `calibrated` after three consecutive updates with image metric below `image_tol`.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. Keep required public modules present and meaningful, and keep top-level behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `image_reject_mixer_cal_loop_top.va`
- `quadrature_mixer_proxy.va`
- `image_cal_controller.va`
