# Differential DAC Calc 6b Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `differential_dac_calc_6b.va`:
  - Module `differential_dac_calc_6b` (entry)
    - position 0: `din0` (input, electrical)
    - position 1: `din1` (input, electrical)
    - position 2: `din2` (input, electrical)
    - position 3: `din3` (input, electrical)
    - position 4: `din4` (input, electrical)
    - position 5: `din5` (input, electrical)
    - position 6: `clks` (input, electrical)
    - position 7: `voutp` (output, electrical)
    - position 8: `voutn` (output, electrical)

## Public Parameter Contract

- `differential_dac_calc_6b.vth` defaults to `0.75`; valid range: finite; overrides vth.
- `differential_dac_calc_6b.vcm` defaults to `0.75`; valid range: finite; overrides vcm.
- `differential_dac_calc_6b.refp` defaults to `0.925`; valid range: finite; overrides refp.
- `differential_dac_calc_6b.refn` defaults to `0.575`; valid range: finite; overrides refn.
- `differential_dac_calc_6b.tt` defaults to `200p`; valid range: finite; overrides tt.
- `differential_dac_calc_6b.convdelay` defaults to `1n`; valid range: finite; overrides convdelay.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CLOCKED_SIX_BIT_WEIGHTED_CODE`: restore: Each rising `clks` crossing samples `din0` through `din5` into the declared six-bit weighted DAC code. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `voutn`, `voutp`.
- `P_COMPLEMENTARY_DIFFERENTIAL_OUTPUTS`: restore: `voutp` and `voutn` use complementary weighted sums about the common-mode value. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `voutn`, `voutp`.
- `P_OUTPUT_SWING_SCALE`: restore: The differential outputs use the declared reference span and bit weights without extra swing scaling. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `voutn`, `voutp`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `differential_dac_calc_6b.va`.
Every supplied `.va` file is editable; do not add or omit files.
