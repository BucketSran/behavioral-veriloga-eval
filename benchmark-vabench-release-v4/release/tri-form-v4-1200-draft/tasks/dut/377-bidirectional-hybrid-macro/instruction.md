# Bidirectional Hybrid Macro

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `bidirectional_hybrid_macro.va`
- Public top module: `bidirectional_hybrid_macro`
- Required public module: `bidirectional_hybrid_macro`

The submitted source must include the target artifact and public module listed above. The public top module is the module instantiated by the evaluator; optional helper modules may be included only when they are part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `bidirectional_hybrid_macro` with positional electrical ports `port_a, port_b, clk, rst, trim_2, trim_1, trim_0, sum_out, diff_out, forward_metric, reverse_metric, balance_ok`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vcm = 0.45 V`: common-mode reference.
- `vth = 0.45 V`: threshold for clock, reset, and trim-code inputs.
- `trim_lsb = 10e-3 V`: balance correction represented by one trim step.
- `balance_tol = 20e-3 V`: tolerance for balance qualification.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset, drive `sum_out` and `diff_out` to `vcm`, clear metrics, and clear `balance_ok`.
- Form voltage-domain sum and difference outputs from deviations of `port_a` and `port_b` around `vcm`.
- Decode `trim_2..trim_0` and apply a signed correction to reduce imbalance between the two paths.
- Update `forward_metric` and `reverse_metric` once per rising `clk` edge from the corrected sum/difference states.
- `balance_ok` must assert after two consecutive updates where the absolute metric mismatch is within `balance_tol`.
- Swapping the relative stimulus on `port_a` and `port_b` must swap the dominant forward/reverse metric relationship.
- This is a behavioral voltage-domain hybrid macro; it must not require an S-parameter file or branch-current RF network.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The evaluator may use behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `bidirectional_hybrid_macro.va`
