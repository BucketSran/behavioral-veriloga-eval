# Switched-cap Phase Sequencer

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `switched_cap_phase_seq_top.va`, `nonoverlap_phase_gen.va`, `sample_switch_scheduler.va`, `hold_flagger.va`
- Public top module: `switched_cap_phase_seq_top`
- Required public modules: `switched_cap_phase_seq_top`, `nonoverlap_phase_gen`, `sample_switch_scheduler`, `hold_flagger`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `switched_cap_phase_seq_top` with positional electrical ports `clk, rst, enable, phi1, phi2, phi3, phi4, sample_cmd, hold_cmd, phase_code_1, phase_code_0, valid`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for clock, reset, and enable.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, clear all phase outputs, commands, phase-code outputs, and `valid`.
- `nonoverlap_phase_gen` must step through four one-hot non-overlapping phases on rising `clk` edges while enabled.
- `sample_switch_scheduler` must assert `sample_cmd` only during the sample phases and `hold_cmd` only during hold phases.
- `hold_flagger` must assert `valid` after a complete sample/hold phase sequence.
- `phase_code_1..phase_code_0` must expose the active phase index.
- No two phase outputs may be high at the same time.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `switched_cap_phase_seq_top.va`
- `nonoverlap_phase_gen.va`
- `sample_switch_scheduler.va`
- `hold_flagger.va`
