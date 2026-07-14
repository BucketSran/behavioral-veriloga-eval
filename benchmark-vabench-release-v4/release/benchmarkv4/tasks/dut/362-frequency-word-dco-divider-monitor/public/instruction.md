# Frequency-word DCO with Divider Monitor

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `frequency_word_dco.va`
- Public top module: `frequency_word_dco`
- Required public module: `frequency_word_dco`

The submitted source must include the target artifact and public module listed above. The public top module is the module instantiated by the evaluator; optional helper modules may be included only when they are part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `frequency_word_dco` with positional electrical ports `enable, rst, fcw_5, fcw_4, fcw_3, fcw_2, fcw_1, fcw_0, dco_clk, div_clk, freq_metric`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for enable, reset, and code bits.
- `f_min = 80.0e6 Hz`: minimum DCO frequency.
- `f_step = 2.0e6 Hz`: frequency increment per frequency-control word step.
- `f_max = 250.0e6 Hz`: maximum DCO frequency.
- `divide_ratio = 4`: fixed monitor divider ratio.
- `tr = 100 ps`: output transition smoothing time.

## Required Behavior

- On reset or when `enable` is low, stop toggling, clear `dco_clk`, `div_clk`, and `freq_metric`.
- Decode `fcw_5..fcw_0` as an unsigned frequency-control word.
- Map the decoded word to `min(f_max, f_min + f_step * code)`.
- Generate a free-running DCO clock while enabled using the mapped frequency.
- Toggle `div_clk` once per `divide_ratio` rising DCO edges and restart its edge counter whenever reset is asserted or enable is low.
- `freq_metric` must expose `vss + (vdd - vss) * (f_target - f_min) / (f_max - f_min)`.
- On enable, restart both clocks low and schedule the first `dco_clk` rising edge one half-period later. Sample the current frequency word at each DCO transition; a word change affects the next half-period and does not retime a transition already pending.
- Higher frequency-control words must produce nondecreasing DCO edge counts over the same observation window.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The evaluator may use behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `frequency_word_dco.va`
