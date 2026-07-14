# Single ADC 7b Weighted Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `single_adc_7b_weighted.va`:
  - Module `single_adc_7b_weighted` (entry)
    - position 0: `din0` (input, electrical)
    - position 1: `din1` (input, electrical)
    - position 2: `din2` (input, electrical)
    - position 3: `din3` (input, electrical)
    - position 4: `din4` (input, electrical)
    - position 5: `din5` (input, electrical)
    - position 6: `din6` (input, electrical)
    - position 7: `dout` (output, electrical)

## Public Parameter Contract

- `single_adc_7b_weighted.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INPUT_THRESHOLDING`: restore: Treat each `din` input as high only when it is above `vth`. Required traces: `time`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `dout`.
- `P_WEIGHTED_CODE_SUM`: restore: Sum the selected 7-bit weights, including the MSB contribution, using the declared weight basis. Required traces: `time`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `dout`.
- `P_NORMALIZED_SINGLE_ENDED_OUTPUT`: restore: Drive the normalized single-ended ADC output from the weighted code without extra fixed offsets or scale errors. Required traces: `time`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `dout`.
- `P_MONOTONIC_CODE_RESPONSE`: restore: The output changes monotonically with increasing selected code weight. Required traces: `time`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `dout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `single_adc_7b_weighted.va`.
Every supplied `.va` file is editable; do not add or omit files.
