# Interleaved ADC Timing-skew Monitor

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `interleaved_adc_skew_monitor_top.va`, `sample_pair_latch.va`, `skew_metric_core.va`
- Public top module: `interleaved_adc_skew_monitor_top`
- Required public modules: `interleaved_adc_skew_monitor_top`, `sample_pair_latch`, `skew_metric_core`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the top-level DUT entry point; helper modules must be part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `interleaved_adc_skew_monitor_top` with positional electrical ports `vin_a, vin_b, clk_a, clk_b, rst, enable, skew_metric, magnitude_metric, alarm`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.
- `skew_limit = 40e-3 V`: alarm threshold for skew proxy.

## Required Behavior

- On reset or when disabled, clear both sample states and all metrics.
- Capture `vin_a` on rising `clk_a` and `vin_b` on rising `clk_b`.
- Estimate a skew proxy from the signed difference between the two most recent samples.
- Drive `skew_metric` with the absolute skew proxy and `magnitude_metric` with the average sample magnitude.
- Assert `alarm` when `skew_metric` exceeds `skew_limit` for two consecutive comparisons.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. Keep required public modules present and meaningful, and keep top-level behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `interleaved_adc_skew_monitor_top.va`
- `sample_pair_latch.va`
- `skew_metric_core.va`
