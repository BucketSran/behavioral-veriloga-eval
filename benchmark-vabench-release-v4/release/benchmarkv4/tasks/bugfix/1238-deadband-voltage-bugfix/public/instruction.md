# Deadband Voltage Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `deadband_voltage.va`:
  - Module `deadband_voltage` (entry)
    - position 0: `sigin` (input, electrical)
    - position 1: `sigout` (output, electrical)

## Public Parameter Contract

- `deadband_voltage.sigin_dead_low` defaults to `-0.25`; valid range: finite; overrides sigin_dead_low.
- `deadband_voltage.sigin_dead_high` defaults to `0.25`; valid range: finite; overrides sigin_dead_high.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DEADBAND_ZERO_REGION`: restore: Inside the inclusive deadband window from `sigin_dead_low` to `sigin_dead_high`, drive `sigout` to `0 V`. Required traces: `time`, `sigin`, `sigout`.
- `P_SIGNED_RESIDUE_OUTSIDE_WINDOW`: restore: Below the lower edge, drive the signed excess below `sigin_dead_low`; above the upper edge, drive the signed excess above `sigin_dead_high` while preserving sign. Required traces: `time`, `sigin`, `sigout`.
- `P_DEADBAND_EDGE_CONTINUITY`: restore: Use the public lower and upper threshold values so the output is continuous at both deadband edges. Required traces: `time`, `sigin`, `sigout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `deadband_voltage.va`.
Every supplied `.va` file is editable; do not add or omit files.
