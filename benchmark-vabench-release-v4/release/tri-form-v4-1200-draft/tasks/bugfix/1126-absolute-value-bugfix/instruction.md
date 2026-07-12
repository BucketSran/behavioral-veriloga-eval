# Absolute Value Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `absolute_value_behavior.va`:
  - Module `absolute_value_behavior` (entry)
    - position 0: `sigin` (input, electrical)
    - position 1: `sigout` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_POSITIVE_INPUT_PASSTHROUGH`: restore: For nonnegative `V(sigin)`, drive `sigout` to the same nonnegative voltage. Required traces: `time`, `sigin`, `sigout`.
- `P_NEGATIVE_INPUT_REFLECTION`: restore: For negative `V(sigin)`, drive `sigout` to `-V(sigin)`. Required traces: `time`, `sigin`, `sigout`.
- `P_MEMORYLESS_ABSOLUTE_VALUE`: restore: The output is an instantaneous absolute-value function of `sigin` with no retained state or waveform schedule. Required traces: `time`, `sigin`, `sigout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `absolute_value_behavior.va`.
Every supplied `.va` file is editable; do not add or omit files.
