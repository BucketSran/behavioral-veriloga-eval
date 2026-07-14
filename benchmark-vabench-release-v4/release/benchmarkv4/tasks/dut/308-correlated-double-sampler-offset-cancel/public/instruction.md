# Correlated Double Sampler Offset-cancel Macro

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `correlated_double_sampler_top.va`, `reset_sample_latch.va`, `signal_sample_latch.va`
- Public top module: `correlated_double_sampler_top`
- Required public modules: `correlated_double_sampler_top`, `reset_sample_latch`, `signal_sample_latch`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the top-level DUT entry point; helper modules must be part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `correlated_double_sampler_top` with positional electrical ports `vin, clk, rst, sample_reset, sample_signal, vout, offset_dbg, valid`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.
- `cds_gain = 1.0`: correlated-difference gain.

## Required Behavior

- On reset, clear reset-sample, signal-sample, output, debug metric, and `valid`.
- On a rising `clk` edge with `sample_reset` high, capture `vin` as the reset/reference sample.
- On a later rising `clk` edge with `sample_signal` high, capture `vin` as the signal sample.
- Drive `vout` as `vcm` plus the signal-minus-reset difference scaled by `cds_gain`.
- Expose the reset sample on `offset_dbg` and assert `valid` only after a complete reset/signal pair.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. Keep required public modules present and meaningful, and keep top-level behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `correlated_double_sampler_top.va`
- `reset_sample_latch.va`
- `signal_sample_latch.va`
