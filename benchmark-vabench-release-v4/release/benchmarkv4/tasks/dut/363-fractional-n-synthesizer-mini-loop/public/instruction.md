# Fractional-N Synthesizer Mini Loop

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `fracn_synth_top.va`, `accumulator.va`, `multi_modulus_divider.va`, `ratio_monitor.va`
- Public top module: `fracn_synth_top`
- Required public modules: `fracn_synth_top`, `accumulator`, `multi_modulus_divider`, `ratio_monitor`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `fracn_synth_top` with positional electrical ports `ref_clk, dco_clk, rst, enable, frac_3, frac_2, frac_1, frac_0, div_clk, div_sel, avg_ratio_metric, valid`. All top-level ports are electrical.

Each required public helper module must be declared with these positional electrical ports:

- `accumulator(decision_tick, rst, enable, frac_3, frac_2, frac_1, frac_0, carry)`
- `multi_modulus_divider(dco_clk, rst, enable, carry, div_clk, div_sel, decision_tick)`
- `ratio_monitor(decision_tick, rst, enable, div_sel, avg_ratio_metric, valid)`

The top module must expose exactly the public top-level port order above and connect the required helper modules as part of the DUT package.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for clocks, reset, enable, and fraction bits.
- `n_int = 8`: integer divider ratio.
- `window_len = 16`: monitor window in divider updates.
- `tr = 100 ps`: output transition smoothing time.

## Required Behavior

- On reset or when `enable` is low, clear the accumulator, divider state, `div_clk`, `div_sel`, `avg_ratio_metric`, and `valid`.
- `accumulator` decodes `frac_3..frac_0` as a fractional command from 0 to 15 and accumulates it once per divider decision.
- `multi_modulus_divider` must select divide-by-`n_int` or divide-by-`n_int + 1` according to accumulator carry events.
- `div_sel` must expose whether the current divider interval is using the larger divide value.
- `div_clk` must be derived from `dco_clk` edges and must not be generated from `ref_clk` alone.
- `ratio_monitor` must report the average selected divide ratio over `window_len` decisions on `avg_ratio_metric` and assert `valid` at the end of each full window.
- Larger fractional commands must produce nondecreasing average divide-ratio metrics over equal windows.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `fracn_synth_top.va`
- `accumulator.va`
- `multi_modulus_divider.va`
- `ratio_monitor.va`
