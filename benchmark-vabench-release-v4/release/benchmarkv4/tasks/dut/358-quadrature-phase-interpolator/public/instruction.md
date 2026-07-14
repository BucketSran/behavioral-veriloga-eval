# Quadrature Phase Interpolator

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `quadrature_phase_interpolator.va`
- Public top module: `quadrature_phase_interpolator`
- Required public module: `quadrature_phase_interpolator`

The submitted source must include the target artifact and public module listed above. The public top module is the required deliverable boundary; optional helper modules may be included only when they are part of the DUT source package, not external stimulus or harness code.

## Public Verilog-A Interface

Declare top module `quadrature_phase_interpolator` with positional electrical ports `clk_i, clk_q, rst, code_4, code_3, code_2, code_1, code_0, clk_out, quadrant_1, quadrant_0, phase_metric`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for clocks, reset, and code bits.
- `unit_delay = 5e-12 s`: phase step represented by one interpolation code.
- `tr = 100 ps`: output transition smoothing time.

## Required Behavior

- On reset, clear `clk_out`, quadrant outputs, and `phase_metric`.
- Observe the rising edges of `clk_i` and `clk_q` and maintain a four-quadrant phase reference.
- Decode `code_4..code_0` as an unsigned phase code from 0 to 31.
- Generate `clk_out` edges delayed from the selected quadrant reference by `unit_delay` times the intra-quadrant code.
- `quadrant_1..quadrant_0` must expose the selected quadrant.
- `phase_metric` must expose the decoded phase code as a voltage-level metric.
- The output edge delay must increase monotonically as the phase code increases, with wrap-around at the quadrant boundary.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add external stimulus decks, private validation code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The top-level observable contract should be verifiable from the public signals.

## Output Contract

Return exactly these complete source artifacts:

- `quadrature_phase_interpolator.va`
