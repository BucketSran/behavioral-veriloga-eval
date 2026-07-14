# Safe Analog Divider Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `safe_analog_divider.va`:
  - Module `safe_analog_divider` (entry)
    - position 0: `signumer` (input, electrical)
    - position 1: `sigdenom` (input, electrical)
    - position 2: `sigout` (output, electrical)

## Public Parameter Contract

- `safe_analog_divider.gain` defaults to `1.0`; valid range: finite; overrides gain.
- `safe_analog_divider.min_sigdenom` defaults to `0.2 from (0:inf)`; valid range: finite; overrides min_sigdenom.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_USE_V_SIGDENOM_DIRECTLY_WHEN_ITS`: restore: For denominator magnitudes at least `min_sigdenom`, use `V(sigdenom)` directly in the divider transfer. Required traces: `time`, `sigdenom`, `signumer`, `sigout`.
- `P_WHEN_V_SIGDENOM_IS_POSITIVE_BUT`: restore: For positive denominator magnitudes below `min_sigdenom`, use `+min_sigdenom` as the guarded denominator. Required traces: `time`, `sigdenom`, `signumer`, `sigout`.
- `P_WHEN_V_SIGDENOM_IS_EXACTLY_ZERO`: restore: For exactly zero denominator, use `+min_sigdenom` as the guarded denominator. Required traces: `time`, `sigdenom`, `signumer`, `sigout`.
- `P_WHEN_V_SIGDENOM_IS_NEGATIVE_BUT`: restore: For negative denominator magnitudes below `min_sigdenom`, use `-min_sigdenom` as the guarded denominator. Required traces: `time`, `sigdenom`, `signumer`, `sigout`.
- `P_DRIVE_SIGOUT_TO_GAIN_V_SIGNUMER`: restore: Drive `sigout` to the observable transfer `gain * V(signumer) / guarded_denominator`. Required traces: `time`, `sigdenom`, `signumer`, `sigout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `safe_analog_divider.va`.
Every supplied `.va` file is editable; do not add or omit files.
