# Crystal Oscillator Startup Monitor

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `crystal_oscillator_startup_monitor.va`
- Public top module: `crystal_oscillator_startup_monitor`
- Required public module: `crystal_oscillator_startup_monitor`

The submitted source must include the target artifact and public module listed above. The public top module is the required deliverable boundary; optional helper modules may be included only when they are part of the DUT source package, not external stimulus or harness code.

## Public Verilog-A Interface

Declare top module `crystal_oscillator_startup_monitor` with positional electrical ports `enable, rst, clk_ref, osc_out, amp_metric, valid, startup_done`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vcm = 0.45 V`: oscillator common-mode reference.
- `vth = 0.45 V`: threshold for enable, reset, and reference clock.
- `amp_step = 30e-3 V`: amplitude growth per reference-clock edge.
- `amp_target = 0.3 V`: amplitude required for startup done.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when `enable` is low, clear oscillator amplitude, `osc_out`, `valid`, and `startup_done`.
- Increase a behavioral amplitude state by `amp_step` on each rising `clk_ref` edge while enabled until `amp_target` is reached.
- Clamp the amplitude at `amp_target` and expose it on `amp_metric`.
- Toggle `osc_out` from `clk_ref` only after the amplitude state is nonzero.
- Assert `startup_done` when `amp_metric` reaches `amp_target`.
- Assert `valid` after two consecutive sliced oscillator periods after startup is done.
- This DUT is a behavioral startup monitor and must not require a crystal resonator or branch-current model.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add external stimulus decks, private validation code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The top-level observable contract should be verifiable from the public signals.

## Output Contract

Return exactly these complete source artifacts:

- `crystal_oscillator_startup_monitor.va`
