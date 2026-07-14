# Differential Amplifier Core Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `differential_amplifier_core.va`:
  - Module `differential_amplifier_core` (entry)
    - position 0: `sigin_p` (input, electrical)
    - position 1: `sigin_n` (input, electrical)
    - position 2: `sigout` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DIFFERENTIAL_INPUT`: restore: Use `V(sigin_p, sigin_n)` as the input signal. Required traces: `time`, `sigin_p`, `sigin_n`, `sigout`.
- `P_INPUT_OFFSET`: restore: Subtract the fixed 0.05 V input-referred offset before applying gain. Required traces: `time`, `sigin_p`, `sigin_n`, `sigout`.
- `P_GAIN_TWO_OUTPUT`: restore: Drive `sigout` to `2.0 * (V(sigin_p, sigin_n) - 0.05)`. Required traces: `time`, `sigin_p`, `sigin_n`, `sigout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `differential_amplifier_core.va`.
Every supplied `.va` file is editable; do not add or omit files.
