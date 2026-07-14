# Fixed-frequency Oscillator Source

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `fixed_frequency_oscillator_source.va`
- Public top module: `fixed_frequency_oscillator_source`
- Required public module: `fixed_frequency_oscillator_source`

The submitted source must include the target artifact and public module listed above. The public top module is the required deliverable boundary; optional helper modules may be included only when they are part of the DUT source package, not external stimulus or harness code.

## Public Verilog-A Interface

Declare top module `fixed_frequency_oscillator_source` with positional electrical ports `enable, rst, osc_out, period_metric, valid`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `period = 20e-9 s`: oscillator period.
- `vth = 0.45 V`: threshold for `enable` and `rst`.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, drive `osc_out`, `period_metric`, and `valid` low.
- When enabled, generate a periodic voltage-domain clock that toggles between `vss` and `vdd` with the configured period.
- `period_metric` must expose a stable voltage-coded representation of the configured period after the first complete cycle.
- Assert `valid` after the first complete oscillator cycle following enable.
- Reset or disable must restart the oscillator phase deterministically.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add external stimulus decks, private validation code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The top-level observable contract should be verifiable from the public signals.

## Output Contract

Return exactly these complete source artifacts:

- `fixed_frequency_oscillator_source.va`
