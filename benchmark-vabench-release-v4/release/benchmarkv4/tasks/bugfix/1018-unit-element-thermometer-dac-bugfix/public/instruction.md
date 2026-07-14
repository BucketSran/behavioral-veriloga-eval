# Unit Element Thermometer DAC Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `thermometer_dac_15seg.va`:
  - Module `thermometer_dac_15seg` (entry)
    - position 0: `seg0` (input, electrical)
    - position 1: `seg1` (input, electrical)
    - position 2: `seg2` (input, electrical)
    - position 3: `seg3` (input, electrical)
    - position 4: `seg4` (input, electrical)
    - position 5: `seg5` (input, electrical)
    - position 6: `seg6` (input, electrical)
    - position 7: `seg7` (input, electrical)
    - position 8: `seg8` (input, electrical)
    - position 9: `seg9` (input, electrical)
    - position 10: `seg10` (input, electrical)
    - position 11: `seg11` (input, electrical)
    - position 12: `seg12` (input, electrical)
    - position 13: `seg13` (input, electrical)
    - position 14: `seg14` (input, electrical)
    - position 15: `vref` (input, electrical)
    - position 16: `vss` (input, electrical)
    - position 17: `aout` (output, electrical)

## Public Parameter Contract

- `thermometer_dac_15seg.vth` defaults to `0.45` V; valid range: finite real; sets the active threshold applied independently to every segment input.
- `thermometer_dac_15seg.tr` defaults to `5e-10` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ZERO_SCALE`: restore: With no active segment inputs, aout equals the vss endpoint after transition settling. Required traces: `time`, `seg0`, `seg1`, `seg2`, `seg3`, `seg4`, `seg5`, `seg6`, `seg7`, `seg8`, `seg9`, `seg10`, `seg11`, `seg12`, `seg13`, `seg14`, `vss`, `aout`.
- `P_FULL_SCALE`: restore: With all fifteen segment inputs active, aout equals the vref endpoint after transition settling. Required traces: `time`, `seg0`, `seg1`, `seg2`, `seg3`, `seg4`, `seg5`, `seg6`, `seg7`, `seg8`, `seg9`, `seg10`, `seg11`, `seg12`, `seg13`, `seg14`, `vref`, `aout`.
- `P_UNIT_ELEMENT_WEIGHT`: restore: Each input above vth contributes exactly one fifteenth of the vref-minus-vss span, including seg14. Required traces: `time`, `seg0`, `seg1`, `seg2`, `seg3`, `seg4`, `seg5`, `seg6`, `seg7`, `seg8`, `seg9`, `seg10`, `seg11`, `seg12`, `seg13`, `seg14`, `vref`, `vss`, `aout`.
- `P_PERMUTATION_INVARIANCE`: restore: Any two segment patterns with the same active count produce the same settled aout. Required traces: `time`, `seg0`, `seg1`, `seg2`, `seg3`, `seg4`, `seg5`, `seg6`, `seg7`, `seg8`, `seg9`, `seg10`, `seg11`, `seg12`, `seg13`, `seg14`, `aout`.
- `P_COUNT_MONOTONICITY`: restore: Increasing the active segment count cannot reduce the settled DAC output for vref above vss. Required traces: `time`, `seg0`, `seg1`, `seg2`, `seg3`, `seg4`, `seg5`, `seg6`, `seg7`, `seg8`, `seg9`, `seg10`, `seg11`, `seg12`, `seg13`, `seg14`, `vref`, `vss`, `aout`.

## Modeling Constraints

- Use all fifteen public segment inputs as identical unit elements.
- Use deterministic smoothed voltage-domain output behavior.
- Do not use current contributions, ddt(), idt(), validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `thermometer_dac_15seg.va`.
Every supplied `.va` file is editable; do not add or omit files.
