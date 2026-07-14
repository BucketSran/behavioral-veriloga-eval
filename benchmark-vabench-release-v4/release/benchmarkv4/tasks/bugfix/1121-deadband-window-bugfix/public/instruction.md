# Deadband Window Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `deadband_window.va`:
  - Module `deadband_window` (entry)
    - position 0: `sigin` (input, electrical)
    - position 1: `sigout` (output, electrical)

## Public Parameter Contract

- `deadband_window.dead_high` defaults to `0.1`; valid range: finite; overrides dead_high.
- `deadband_window.dead_low` defaults to `-0.1`; valid range: finite; overrides dead_low.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ZERO_INSIDE_DEADBAND`: restore: For `dead_low <= V(sigin) <= dead_high`, drive `sigout` to 0 V. Required traces: `time`, `sigin`, `sigout`.
- `P_LOWER_RESIDUE`: restore: For `V(sigin) < dead_low`, drive `sigout` to `V(sigin) - dead_low`. Required traces: `time`, `sigin`, `sigout`.
- `P_UPPER_RESIDUE`: restore: For `V(sigin) > dead_high`, drive `sigout` to `V(sigin) - dead_high`. Required traces: `time`, `sigin`, `sigout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `deadband_window.va`.
Every supplied `.va` file is editable; do not add or omit files.
