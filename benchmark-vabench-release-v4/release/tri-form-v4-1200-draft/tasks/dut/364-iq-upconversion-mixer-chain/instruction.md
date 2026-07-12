# I/Q Upconversion Mixer Chain

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `iq_upconversion_mixer.va`
- Public top module: `iq_upconversion_mixer`
- Required public module: `iq_upconversion_mixer`

The submitted source must include the target artifact and public module listed above. The public top module is the module instantiated by the evaluator; optional helper modules may be included only when they are part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `iq_upconversion_mixer` with positional electrical ports `i_in, q_in, lo_i, lo_q, rst, enable, rf_out, i_mix_dbg, q_mix_dbg, quad_ok`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vcm = 0.45 V`: common-mode reference for single-ended signals.
- `vth = 0.45 V`: threshold for LO and control inputs.
- `gain = 1.0`: mixer conversion gain.
- `tr = 200 ps`: smoothing time for discrete LO-polarity and `quad_ok` transitions; continuous baseband path values remain continuous analog contributions.

## Required Behavior

- On reset or when `enable` is low, drive `rf_out`, `i_mix_dbg`, and `q_mix_dbg` to `vcm` and clear `quad_ok`.
- Interpret `lo_i` and `lo_q` as quadrature LO phases and assert `quad_ok` when both phases are toggling.
- Interpret each LO as +1 above `vth` and -1 otherwise. Define the I-path contribution as `gain * (V(i_in) - vcm) * lo_i_sign` and the Q-path contribution as `-gain * (V(q_in) - vcm) * lo_q_sign`.
- Drive `i_mix_dbg` and `q_mix_dbg` to `vcm` plus their respective signed path contribution.
- Drive `rf_out` to `vcm` plus the sum of the two path contributions, bounded to `vss..vdd`.
- Assert `quad_ok` only after both LO inputs have exhibited at least one threshold crossing since the latest reset or enable. When either LO phase is missing, hold `quad_ok` low and keep the RF output bounded around `vcm`.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The evaluator may use behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `iq_upconversion_mixer.va`
