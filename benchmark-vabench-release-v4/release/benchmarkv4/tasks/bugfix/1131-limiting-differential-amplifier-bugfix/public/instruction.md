# Limiting Differential Amplifier Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `limiting_differential_amplifier.va`:
  - Module `limiting_differential_amplifier` (entry)
    - position 0: `sigin_p` (input, electrical)
    - position 1: `sigin_n` (input, electrical)
    - position 2: `sigout` (output, electrical)

## Public Parameter Contract

- `limiting_differential_amplifier.gain` defaults to `1`; valid range: finite; overrides gain.
- `limiting_differential_amplifier.sigout_high` defaults to `10`; valid range: finite; overrides sigout_high.
- `limiting_differential_amplifier.sigout_low` defaults to `-10`; valid range: finite; overrides sigout_low.
- `limiting_differential_amplifier.sigin_offset` defaults to `0`; valid range: finite; overrides sigin_offset.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_OFFSET_CORRECTED_DIFFERENTIAL_GAIN`: restore: Compute `gain * (V(sigin_p, sigin_n) - sigin_offset)`. Required traces: `time`, `sigin_p`, `sigin_n`, `sigout`.
- `P_OUTPUT_MIDPOINT_REFERENCE`: restore: Center the amplified value at `(sigout_high + sigout_low) / 2`. Required traces: `time`, `sigin_p`, `sigin_n`, `sigout`.
- `P_OUTPUT_RAIL_CLAMP`: restore: Clamp the final target to the inclusive interval `[sigout_low, sigout_high]`. Required traces: `time`, `sigin_p`, `sigin_n`, `sigout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `limiting_differential_amplifier.va`.
Every supplied `.va` file is editable; do not add or omit files.
