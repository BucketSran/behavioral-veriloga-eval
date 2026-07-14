# DAC Ideal 4b Offset Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `dac_ideal_4b_offset.va`:
  - Module `dac_ideal_4b_offset` (entry)
    - position 0: `din0` (input, electrical)
    - position 1: `din1` (input, electrical)
    - position 2: `din2` (input, electrical)
    - position 3: `din3` (input, electrical)
    - position 4: `dout` (output, electrical)

## Public Parameter Contract

- `dac_ideal_4b_offset.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `dac_ideal_4b_offset.offset` defaults to `0.239`; valid range: finite; overrides offset.
- `dac_ideal_4b_offset.scaling` defaults to `32.0 * 10.0 / 9.0`; valid range: finite; overrides scaling.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_THRESHOLDED_4BIT_CODE`: restore: `din3` is the MSB and `din0` is the LSB of a 4-bit unsigned code using threshold `vth`. Required traces: `time`, `din0`, `din1`, `din2`, `din3`, `dout`.
- `P_OFFSET_PLUS_SCALED_TRIM`: restore: The output equals the public `offset` plus the code-scaled trim increment using the public `scaling` factor. Required traces: `time`, `din0`, `din1`, `din2`, `din3`, `dout`.
- `P_EVENT_UPDATED_OUTPUT`: restore: `dout` updates on input threshold crossings or initial step and otherwise holds the smooth voltage output. Required traces: `time`, `din0`, `din1`, `din2`, `din3`, `dout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `dac_ideal_4b_offset.va`.
Every supplied `.va` file is editable; do not add or omit files.
