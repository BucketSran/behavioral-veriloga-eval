# I/Q Upconversion Mixer Chain Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `iq_upconversion_mixer.va`:
  - Module `iq_upconversion_mixer` (entry)
    - position 0: `i_in` (input, electrical)
    - position 1: `q_in` (input, electrical)
    - position 2: `lo_i` (input, electrical)
    - position 3: `lo_q` (input, electrical)
    - position 4: `rst` (input, electrical)
    - position 5: `enable` (input, electrical)
    - position 6: `rf_out` (output, electrical)
    - position 7: `i_mix_dbg` (output, electrical)
    - position 8: `q_mix_dbg` (output, electrical)
    - position 9: `quad_ok` (output, electrical)

## Public Parameter Contract

- `iq_upconversion_mixer.vdd` defaults to `0.9`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vdd behavior for module iq_upconversion_mixer.
- `iq_upconversion_mixer.vss` defaults to `0.0`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vss behavior for module iq_upconversion_mixer.
- `iq_upconversion_mixer.vcm` defaults to `0.45`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vcm behavior for module iq_upconversion_mixer.
- `iq_upconversion_mixer.vth` defaults to `0.45`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vth behavior for module iq_upconversion_mixer.
- `iq_upconversion_mixer.gain` defaults to `1.0`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public gain behavior for module iq_upconversion_mixer.
- `iq_upconversion_mixer.tr` defaults to `200p from (0:inf)` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public tr behavior for module iq_upconversion_mixer.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CLEAR`: restore: Reset or disabled operation drives RF and debug outputs to vcm and clears quad_ok. Required traces: `time`, `rst`, `enable`, `rf_out`, `i_mix_dbg`, `q_mix_dbg`, `quad_ok`.
- `P_IQ_SIGNED_MIXING`: restore: I and Q debug outputs equal vcm plus the specified signed LO products, including the negative Q-path convention. Required traces: `time`, `i_in`, `q_in`, `lo_i`, `lo_q`, `i_mix_dbg`, `q_mix_dbg`.
- `P_RF_SUM_CLAMP`: restore: rf_out equals the bounded sum of the I and Q path contributions about vcm. Required traces: `time`, `i_in`, `q_in`, `lo_i`, `lo_q`, `rf_out`, `i_mix_dbg`, `q_mix_dbg`.
- `P_QUADRATURE_ACTIVITY`: restore: quad_ok asserts only after each LO input has crossed threshold since the latest reset or enable event. Required traces: `time`, `lo_i`, `lo_q`, `rst`, `enable`, `quad_ok`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation.
- Use public voltage contributions only and preserve the declared artifact and module interfaces.
- Do not hard-code evaluator stimulus, sample windows, checker tolerances, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `iq_upconversion_mixer.va`.
Every supplied `.va` file is editable; do not add or omit files.
