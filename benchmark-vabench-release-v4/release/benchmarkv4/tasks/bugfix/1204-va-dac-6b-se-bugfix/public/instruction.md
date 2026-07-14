# VA DAC 6b SE Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `va_dac_6b_se.va`:
  - Module `va_dac_6b_se` (entry)
    - position 0: `din0` (input, electrical)
    - position 1: `din1` (input, electrical)
    - position 2: `din2` (input, electrical)
    - position 3: `din3` (input, electrical)
    - position 4: `din4` (input, electrical)
    - position 5: `din5` (input, electrical)
    - position 6: `rdy` (input, electrical)
    - position 7: `aout` (output, electrical)

## Public Parameter Contract

- `va_dac_6b_se.vdd` defaults to `1.0`; valid range: finite; overrides vdd.
- `va_dac_6b_se.vth` defaults to `0.5`; valid range: finite; overrides vth.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_EACH_RISING_RDY_CROSSING_SAMPLE`: restore: On each rising `rdy` crossing, sample `din0..din5` with switched weights `0.5, 1, 2, 4, 8, 16` from `din0` through `din5`. Map the sampled weighted code to a bipolar single-ended output scaled by `vdd` using this public normalization: Required traces: `time`, `aout`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `rdy`.
- `P_TEXT_WEIGHTED_CODE_16_DIN5_8`: restore: ```text weighted_code = 16*din5 + 8*din4 + 4*din3 + 2*din2 + 1*din1 + 0.5*din0 aout = (weighted_code / 47.5) * 2.0 * vdd - vdd ``` Required traces: `time`, `aout`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `rdy`.
- `P_EACH_DIN_TERM_IS_1_WHEN`: restore: Each `din*` term is `1` when the corresponding voltage is above `vth` and `0` otherwise. The denominator `47.5` is the fixed source normalization basis including the non-switching reference contribution. Required traces: `time`, `aout`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `rdy`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `va_dac_6b_se.va`.
Every supplied `.va` file is editable; do not add or omit files.
