# Safe Voltage Divider Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `safe_voltage_divider.va`:
  - Module `safe_voltage_divider` (entry)
    - position 0: `signumer` (input, electrical)
    - position 1: `sigdenom` (input, electrical)
    - position 2: `sigout` (output, electrical)

## Public Parameter Contract

- `safe_voltage_divider.gain` defaults to `1`; valid range: finite; overrides gain.
- `safe_voltage_divider.min_sigdenom` defaults to `1.0e-9 from (0:inf)`; valid range: finite; overrides min_sigdenom.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_GAINED_DIVISION`: restore: Drive `sigout` to `gain * V(signumer) / guarded_denominator`. Required traces: `time`, `signumer`, `sigdenom`, `sigout`.
- `P_DENOMINATOR_MAGNITUDE_FLOOR`: restore: When `abs(V(sigdenom)) < min_sigdenom`, use a denominator magnitude of `min_sigdenom`. Required traces: `time`, `sigdenom`, `sigout`.
- `P_DENOMINATOR_SIGN_PRESERVED`: restore: Preserve the original denominator sign when applying the minimum denominator guard. Required traces: `time`, `signumer`, `sigdenom`, `sigout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `safe_voltage_divider.va`.
Every supplied `.va` file is editable; do not add or omit files.
