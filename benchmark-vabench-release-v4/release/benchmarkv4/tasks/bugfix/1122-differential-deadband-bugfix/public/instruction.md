# Differential Deadband Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `differential_deadband.va`:
  - Module `differential_deadband` (entry)
    - position 0: `sigin_p` (input, electrical)
    - position 1: `sigin_n` (input, electrical)
    - position 2: `sigout` (output, electrical)

## Public Parameter Contract

- `differential_deadband.dead_high` defaults to `0.1`; valid range: finite; overrides dead_high.
- `differential_deadband.dead_low` defaults to `-0.1`; valid range: finite; overrides dead_low.
- `differential_deadband.gain` defaults to `1`; valid range: finite; overrides gain.
- `differential_deadband.leak` defaults to `0`; valid range: finite; overrides leak.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DIFFERENTIAL_INPUT`: restore: Use `V(sigin_p, sigin_n)` as the signed input error; do not collapse the transfer to one input terminal. Required traces: `time`, `sigin_p`, `sigin_n`, `sigout`.
- `P_LEAK_INSIDE_DEADBAND`: restore: For `dead_low <= V(sigin_p, sigin_n) <= dead_high`, drive `sigout` to the parameter `leak`. Required traces: `time`, `sigin_p`, `sigin_n`, `sigout`.
- `P_GAINED_RESIDUE_OUTSIDE_DEADBAND`: restore: Below `dead_low`, drive `gain * (diff - dead_low) + leak`; above `dead_high`, drive `gain * (diff - dead_high) + leak`. Required traces: `time`, `sigin_p`, `sigin_n`, `sigout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `differential_deadband.va`.
Every supplied `.va` file is editable; do not add or omit files.
