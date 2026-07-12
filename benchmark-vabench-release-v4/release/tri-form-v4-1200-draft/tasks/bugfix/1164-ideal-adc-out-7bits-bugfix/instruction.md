# Ideal ADC Out 7bits Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `ideal_adc_out_7bits_scalar.va`:
  - Module `ideal_adc_out_7bits_scalar` (entry)
    - position 0: `din0` (input, electrical)
    - position 1: `din1` (input, electrical)
    - position 2: `din2` (input, electrical)
    - position 3: `din3` (input, electrical)
    - position 4: `din4` (input, electrical)
    - position 5: `din5` (input, electrical)
    - position 6: `din6` (input, electrical)
    - position 7: `dout` (output, electrical)

## Public Parameter Contract

- `ideal_adc_out_7bits_scalar.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_THRESHOLD_CODE_DETECTION`: restore: Each `din` input is interpreted as asserted only when it is above `vth`. Required traces: `time`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `dout`.
- `P_WEIGHTED_GROUP_SUM`: restore: `din6` through `din2` contribute 16, 8, 4, 2, and 1 unit groups, while `din1` and `din0` contribute half-LSB and quarter-LSB trim groups. Required traces: `time`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `dout`.
- `P_SCALED_SCALAR_OUTPUT`: restore: `dout` represents the correctly scaled fractional scalar sum without fixed offsets or denominator errors. Required traces: `time`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `dout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `ideal_adc_out_7bits_scalar.va`.
Every supplied `.va` file is editable; do not add or omit files.
