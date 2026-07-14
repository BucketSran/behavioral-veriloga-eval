# Offset Gain Amplifier Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `offset_gain_amplifier.va`:
  - Module `offset_gain_amplifier` (entry)
    - position 0: `sigin` (input, electrical)
    - position 1: `sigout` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INPUT_OFFSET_SUBTRACTION`: restore: Subtract 0.2 V from `V(sigin)` before applying gain. Required traces: `time`, `sigin`, `sigout`.
- `P_FIXED_GAIN_THREE`: restore: Drive `sigout` to `3.0 * (V(sigin) - 0.2)`. Required traces: `time`, `sigin`, `sigout`.
- `P_DIRECT_MEMORYLESS_OUTPUT`: restore: Use a direct memoryless voltage output without clipping, filtering, current output, or stimulus-specific behavior. Required traces: `time`, `sigin`, `sigout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `offset_gain_amplifier.va`.
Every supplied `.va` file is editable; do not add or omit files.
