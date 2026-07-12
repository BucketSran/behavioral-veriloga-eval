# Fine/coarse TDC Encoder

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `fine_coarse_tdc_encoder_top.va`, `coarse_counter.va`, `fine_residual_metric.va`
- Public top module: `fine_coarse_tdc_encoder_top`
- Required public modules: `fine_coarse_tdc_encoder_top`, `coarse_counter`, `fine_residual_metric`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the top-level DUT entry point; helper modules must be part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `fine_coarse_tdc_encoder_top` with positional electrical ports `start, stop, ref_clk, rst, enable, coarse_3, coarse_2, coarse_1, coarse_0, fine_metric, valid`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, clear coarse code, fine metric, and `valid`.
- A rising `start` edge arms a measurement and clears the coarse counter.
- Count rising `ref_clk` edges until the first rising `stop` edge.
- Latch the coarse count into `coarse_3..coarse_0` and expose a fine residual proxy on `fine_metric`.
- Assert `valid` only after the stop edge completes the measurement.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. Keep required public modules present and meaningful, and keep top-level behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `fine_coarse_tdc_encoder_top.va`
- `coarse_counter.va`
- `fine_residual_metric.va`
