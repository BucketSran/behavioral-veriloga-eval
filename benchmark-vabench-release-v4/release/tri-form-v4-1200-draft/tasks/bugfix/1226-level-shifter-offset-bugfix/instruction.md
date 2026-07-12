# Level Shifter Offset Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `level_shifter_offset.va`:
  - Module `level_shifter_offset` (entry)
    - position 0: `sigin` (input, electrical)
    - position 1: `sigout` (output, electrical)

## Public Parameter Contract

- `level_shifter_offset.sigshift` defaults to `0.35`; valid range: finite; overrides sigshift.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DRIVE_SIGOUT_TO_V_SIGIN_PLUS_SIGSHIFT`: restore: Drive `sigout` to `V(sigin) + sigshift` for the current input voltage. Required traces: `time`, `sigin`, `sigout`.
- `P_PRESERVE_UNITY_GAIN_WHILE_ADDING_OFFSET`: restore: Preserve unity gain from `sigin` to `sigout` while adding the configured `sigshift` offset; input changes must appear at `sigout` with the same voltage step size. Required traces: `time`, `sigin`, `sigout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `level_shifter_offset.va`.
Every supplied `.va` file is editable; do not add or omit files.
