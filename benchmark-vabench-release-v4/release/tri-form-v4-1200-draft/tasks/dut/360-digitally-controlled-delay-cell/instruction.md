# Digitally Controlled Delay Cell

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `digitally_controlled_delay_cell.va`
- Public top module: `digitally_controlled_delay_cell`
- Required public module: `digitally_controlled_delay_cell`

The submitted source must include the target artifact and public module listed above. The public top module is the module instantiated by the evaluator; optional helper modules may be included only when they are part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `digitally_controlled_delay_cell` with positional electrical ports `in_clk, load, rst, code_5, code_4, code_3, code_2, code_1, code_0, out_clk, delay_metric, valid`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for digital inputs.
- `delay_min = 20e-12 s`: minimum output delay.
- `delay_lsb = 3e-12 s`: delay added per code step.
- `tr = 100 ps`: output transition smoothing time.

## Required Behavior

- On reset, clear the latched code, `out_clk`, `delay_metric`, and `valid`.
- On rising `load`, capture `code_5..code_0` as an unsigned delay code.
- Map the latched code to a delay equal to `delay_min + delay_lsb * code`.
- For each rising edge of `in_clk`, produce a corresponding rising edge on `out_clk` after the mapped delay.
- Delay both rising and falling input edges by the same selected delay, preserving the input pulse width. Latch the selected delay independently at each originating edge so a later code load does not retime an already pending output edge.
- `delay_metric` must expose the latched code normalized onto `vss..vdd`, using `vss + (vdd - vss) * code / 63`.
- `valid` must assert after the first output pulse generated from a loaded code.
- Reset cancels pending delayed edges, clears the loaded-code state, and drives `out_clk` low.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The evaluator may use behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `digitally_controlled_delay_cell.va`
