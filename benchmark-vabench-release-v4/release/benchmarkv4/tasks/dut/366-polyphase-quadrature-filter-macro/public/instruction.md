# Polyphase Quadrature Filter Macro

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `polyphase_quadrature_filter.va`
- Public top module: `polyphase_quadrature_filter`
- Required public module: `polyphase_quadrature_filter`

The submitted source must include the target artifact and public module listed above. The public top module is the required deliverable boundary; optional helper modules may be included only when they are part of the DUT source package, not external stimulus or harness code.

## Public Verilog-A Interface

Declare top module `polyphase_quadrature_filter` with positional electrical ports `vin, clk, rst, enable, i_out, q_out, amp_metric, phase_metric, valid`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vcm = 0.45 V`: common-mode reference.
- `vth = 0.45 V`: threshold for clock and control inputs.
- `alpha = 0.25`: sampled-state smoothing factor.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when `enable` is low, clear path states, metrics, `valid`, and drive outputs to `vcm`.
- On each rising `clk` edge while enabled, update an in-phase sampled state from `vin`.
- Update a quadrature sampled state using the previous in-phase state so the Q output is phase-shifted relative to I.
- Drive `i_out` and `q_out` around `vcm` from the two path states.
- Report a bounded phase/order metric on `phase_metric` and an amplitude-balance metric on `amp_metric`.
- Assert `valid` after at least four enabled sample updates.
- The I and Q outputs must not collapse to identical waveforms during enabled operation.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add external stimulus decks, private validation code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The top-level observable contract should be verifiable from the public signals.

## Output Contract

Return exactly these complete source artifacts:

- `polyphase_quadrature_filter.va`
