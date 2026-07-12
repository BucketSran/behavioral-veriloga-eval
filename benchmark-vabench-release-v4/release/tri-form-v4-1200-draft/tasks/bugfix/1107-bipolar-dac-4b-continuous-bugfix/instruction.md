# Bipolar DAC 4b Continuous Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `bipolar_dac_4b_continuous.va`:
  - Module `bipolar_dac_4b_continuous` (entry)
    - position 0: `vd3` (input, electrical)
    - position 1: `vd2` (input, electrical)
    - position 2: `vd1` (input, electrical)
    - position 3: `vd0` (input, electrical)
    - position 4: `vout` (output, electrical)

## Public Parameter Contract

- `bipolar_dac_4b_continuous.vref` defaults to `0.9` V; valid range: vref > 0; sets positive and negative full-scale output magnitudes.
- `bipolar_dac_4b_continuous.trise` defaults to `2e-11` s; valid range: trise >= 0; sets vout rise smoothing.
- `bipolar_dac_4b_continuous.tfall` defaults to `2e-11` s; valid range: tfall >= 0; sets vout fall smoothing.
- `bipolar_dac_4b_continuous.tdel` defaults to `0.0` s; valid range: tdel >= 0; sets vout transition delay.
- `bipolar_dac_4b_continuous.vtrans` defaults to `0.45` V; valid range: finite real; sets the logic threshold for all four voltage-coded input bits.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_UNSIGNED_BIT_DECODE`: restore: Each input is decoded continuously as one only when its voltage exceeds vtrans, with vd3 as MSB and vd0 as LSB. Required traces: `time`, `vd3`, `vd2`, `vd1`, `vd0`, `vout`.
- `P_NEGATIVE_FULL_SCALE`: restore: Unsigned code 0 produces approximately negative vref. Required traces: `time`, `vd3`, `vd2`, `vd1`, `vd0`, `vout`.
- `P_POSITIVE_FULL_SCALE`: restore: Unsigned code 15 produces approximately positive vref. Required traces: `time`, `vd3`, `vd2`, `vd1`, `vd0`, `vout`.
- `P_UNIFORM_CODE_STEP`: restore: Every one-code increase raises the output target by the same voltage increment across codes 0 through 15. Required traces: `time`, `vd3`, `vd2`, `vd1`, `vd0`, `vout`.
- `P_MONOTONIC_TRANSFER`: restore: The output is strictly monotonic with increasing unsigned code for vref greater than zero. Required traces: `time`, `vd3`, `vd2`, `vd1`, `vd0`, `vout`.
- `P_CONTINUOUS_REEVALUATION`: restore: The DAC target responds to input-code threshold changes without requiring a clock event, using tdel, trise, and tfall for output timing. Required traces: `time`, `vd3`, `vd2`, `vd1`, `vd0`, `vout`.

## Modeling Constraints

- Decode the four voltage-coded bits continuously in the declared MSB-to-LSB order.
- Drive the affine bipolar transfer with a smoothed voltage contribution.
- Do not use current contributions, ddt(), idt(), file I/O, validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `bipolar_dac_4b_continuous.va`.
Every supplied `.va` file is editable; do not add or omit files.
