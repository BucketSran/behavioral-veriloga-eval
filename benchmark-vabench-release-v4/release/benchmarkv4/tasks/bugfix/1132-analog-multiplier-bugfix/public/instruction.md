# Analog Multiplier Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `analog_multiplier_gain.va`:
  - Module `analog_multiplier_gain` (entry)
    - position 0: `sigin1` (input, electrical)
    - position 1: `sigin2` (input, electrical)
    - position 2: `sigout` (output, electrical)

## Public Parameter Contract

- `analog_multiplier_gain.gain` defaults to `1`; valid range: finite; overrides gain.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ANALOG_PRODUCT`: restore: Drive `sigout` to `V(sigin1) * V(sigin2)` scaled by `gain`, preserving product sign. Required traces: `time`, `sigin1`, `sigin2`, `sigout`.
- `P_GAIN_PARAMETER_APPLIED`: restore: Apply the overridable `gain` parameter multiplicatively to the input product. Required traces: `time`, `sigin1`, `sigin2`, `sigout`.
- `P_MULTIPLICATIVE_NOT_ADDITIVE`: restore: The transfer must be multiplicative and must not replace the product with addition or a square of one input. Required traces: `time`, `sigin1`, `sigin2`, `sigout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `analog_multiplier_gain.va`.
Every supplied `.va` file is editable; do not add or omit files.
