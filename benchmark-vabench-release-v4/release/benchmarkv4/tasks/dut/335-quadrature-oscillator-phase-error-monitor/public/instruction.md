# Quadrature Oscillator Phase-error Monitor

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `quadrature_oscillator_phase_error_monitor.va`
- Public top module: `quadrature_oscillator_phase_error_monitor`
- Required public module: `quadrature_oscillator_phase_error_monitor`

The submitted source must include the target artifact and public module listed above. The public top module is the top-level DUT entry point; optional helper modules may be included only when they are part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `quadrature_oscillator_phase_error_monitor` with positional electrical ports `clk_i, clk_q, rst, enable, phase_error_metric, quadrature_ok, valid`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.
- `phase_tol = 60e-3 V`: quadrature metric tolerance.

## Required Behavior

- On reset or when disabled, clear phase metric, status, and `valid`.
- Track rising threshold crossings of `clk_i` and `clk_q`.
- Estimate a voltage-domain phase-error metric from the relative event order and interval proxy.
- Assert `quadrature_ok` when the measured phase proxy stays within `phase_tol` for two cycles.
- Assert `valid` after both I and Q edges have been observed.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. Keep the top-level observable behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `quadrature_oscillator_phase_error_monitor.va`
