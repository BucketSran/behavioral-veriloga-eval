# Capacitive-feedback Amplifier Macro

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `capacitive_feedback_amplifier_macro.va`
- Public top module: `capacitive_feedback_amplifier_macro`
- Required public module: `capacitive_feedback_amplifier_macro`

The submitted source must include the target artifact and public module listed above. The public top module is the top-level DUT entry point; optional helper modules may be included only when they are part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `capacitive_feedback_amplifier_macro` with positional electrical ports `vin, clk, rst, enable, gain_1, gain_0, vout, sampled_metric, settled`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.
- `gain_step = 0.75`: gain increment per code.
- `settle_tol = 10e-3 V`: settling tolerance.

## Required Behavior

- On reset or when disabled, drive `vout` to `vcm`, clear `sampled_metric`, and clear `settled`.
- On each rising `clk` edge while enabled, sample `vin` and decode `gain_1..gain_0` as a programmable capacitor ratio.
- Drive `sampled_metric` with the held input sample.
- Move `vout` toward `vcm + gain * (sample - vcm)` with bounded per-update movement.
- Assert `settled` after the output has stayed within `settle_tol` of the target for two enabled updates.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

The exact gain contract is `code = (gain_0 > vth ? 1 : 0) + 2*(gain_1 > vth ? 1 : 0)`, `gain = 1.0 + gain_step*code`, and, on each accepted edge, `vout = clamp(vcm + gain*(sample - vcm), vss, vdd)`. Do not apply an additional slew step.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. Keep the top-level observable behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `capacitive_feedback_amplifier_macro.va`
