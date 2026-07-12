# DAC 5V Weighted 7b Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `dac_5v_weighted_7b.va`:
  - Module `dac_5v_weighted_7b` (entry)
    - position 0: `clks` (input, electrical)
    - position 1: `din0` (input, electrical)
    - position 2: `din1` (input, electrical)
    - position 3: `din2` (input, electrical)
    - position 4: `din3` (input, electrical)
    - position 5: `din4` (input, electrical)
    - position 6: `din5` (input, electrical)
    - position 7: `din6` (input, electrical)
    - position 8: `vout` (output, electrical)

## Public Parameter Contract

- `dac_5v_weighted_7b.vth` defaults to `0.75`; valid range: finite; overrides vth.
- `dac_5v_weighted_7b.tt` defaults to `200p from [1p:inf]`; valid range: finite; overrides tt.
- `dac_5v_weighted_7b.delay` defaults to `1n from [1p:inf]`; valid range: finite; overrides delay.
- `dac_5v_weighted_7b.refp` defaults to `5`; valid range: finite; overrides refp.
- `dac_5v_weighted_7b.refn` defaults to `1`; valid range: finite; overrides refn.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CLOCKED_SEVEN_BIT_WEIGHTED_SUM`: restore: Each rising `clks` crossing samples `din0` through `din6` into the declared seven-bit weighted DAC sum. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `vout`.
- `P_MSB_AND_TERMINATION_CONTRIBUTIONS`: restore: `din0` contributes the largest switched weight and the fixed termination contribution is included. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `vout`.
- `P_REFERENCE_ENDPOINTS_AND_SCALE`: restore: The output uses the declared `refp` and `refn` endpoints and full DAC scale. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `dac_5v_weighted_7b.va`.
Every supplied `.va` file is editable; do not add or omit files.
