# Deserializer DEMUX Alignment Macro

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `deserializer_demux_alignment_macro.va`
- Public top module: `deserializer_demux_alignment_macro`
- Required public module: `deserializer_demux_alignment_macro`

The submitted source must include the target artifact and public module listed above. The public top module is the required deliverable boundary; optional helper modules may be included only when they are part of the DUT source package, not external stimulus or harness code.

## Public Verilog-A Interface

Declare top module `deserializer_demux_alignment_macro` with positional electrical ports `clk, rst, enable, serial_in, align_pulse, out0, out1, out2, out3, phase_metric, word_valid`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for digital-voltage inputs.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, clear all parallel outputs, `phase_metric`, and `word_valid`.
- A rising `align_pulse` resets the slot pointer so the next sampled serial bit is written to `out0`.
- On each rising `clk` edge while enabled, sample `serial_in` into the active output slot and advance the slot pointer.
- Assert `word_valid` after all four output slots have been updated since the most recent alignment event.
- `phase_metric` must expose the active slot pointer.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add external stimulus decks, private validation code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The top-level observable contract should be verifiable from the public signals.

## Output Contract

Return exactly these complete source artifacts:

- `deserializer_demux_alignment_macro.va`
