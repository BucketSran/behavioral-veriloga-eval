# Quadrature LO Generator from Divided Clock

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `quadrature_lo_generator_divided_clock.va`
- Public top module: `quadrature_lo_generator_divided_clock`
- Required public module: `quadrature_lo_generator_divided_clock`

The submitted source must include the target artifact and public module listed above. The public top module is the module instantiated by the evaluator; optional helper modules may be included only when they are part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `quadrature_lo_generator_divided_clock` with positional electrical ports `clk_in, rst, enable, lo_i, lo_q, div_metric, quad_ok`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for clock, reset, and enable.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, clear `lo_i`, `lo_q`, `div_metric`, and `quad_ok`.
- On successive rising `clk_in` edges while enabled, generate the repeating
  state sequence `(lo_i, lo_q) = 10, 11, 01, 00`. Each state lasts one input
  clock period, so both outputs divide the input clock by four and `lo_q`
  trails `lo_i` by one quarter of the divided-clock period.
- `lo_i` and `lo_q` must have the same divided frequency and a deterministic quadrature phase relationship.
- `div_metric` must expose the state index `k` for the currently driven pair as
  `vss + (vdd - vss) * k / 3`, where the sequence above uses `k = 0..3`.
- Assert `quad_ok` after two complete quadrature output cycles with the expected state sequence.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The evaluator may use behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `quadrature_lo_generator_divided_clock.va`
