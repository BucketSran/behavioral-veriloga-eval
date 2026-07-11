# Unit Element Thermometer DAC Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Unit Element Thermometer DAC` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `thermometer_dac_15seg` as `XDUT` with ordered public binding: seg0=seg0, seg1=seg1, seg2=seg2, seg3=seg3, seg4=seg4, seg5=seg5, seg6=seg6, seg7=seg7, seg8=seg8, seg9=seg9, seg10=seg10, seg11=seg11, seg12=seg12, seg13=seg13, seg14=seg14, vref=vref, vss=vss, aout=aout.

## Public Parameter Contract

- `thermometer_dac_15seg.vth` defaults to `0.45` V; valid range: finite real; sets the active threshold applied independently to every segment input.
- `thermometer_dac_15seg.tr` defaults to `5e-10` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ZERO_SCALE`: exercise and make observable: With no active segment inputs, aout equals the vss endpoint after transition settling. Required traces: `time`, `seg0`, `seg1`, `seg2`, `seg3`, `seg4`, `seg5`, `seg6`, `seg7`, `seg8`, `seg9`, `seg10`, `seg11`, `seg12`, `seg13`, `seg14`, `vss`, `aout`.
- `P_FULL_SCALE`: exercise and make observable: With all fifteen segment inputs active, aout equals the vref endpoint after transition settling. Required traces: `time`, `seg0`, `seg1`, `seg2`, `seg3`, `seg4`, `seg5`, `seg6`, `seg7`, `seg8`, `seg9`, `seg10`, `seg11`, `seg12`, `seg13`, `seg14`, `vref`, `aout`.
- `P_UNIT_ELEMENT_WEIGHT`: exercise and make observable: Each input above vth contributes exactly one fifteenth of the vref-minus-vss span, including seg14. Required traces: `time`, `seg0`, `seg1`, `seg2`, `seg3`, `seg4`, `seg5`, `seg6`, `seg7`, `seg8`, `seg9`, `seg10`, `seg11`, `seg12`, `seg13`, `seg14`, `vref`, `vss`, `aout`.
- `P_PERMUTATION_INVARIANCE`: exercise and make observable: Any two segment patterns with the same active count produce the same settled aout. Required traces: `time`, `seg0`, `seg1`, `seg2`, `seg3`, `seg4`, `seg5`, `seg6`, `seg7`, `seg8`, `seg9`, `seg10`, `seg11`, `seg12`, `seg13`, `seg14`, `aout`.
- `P_COUNT_MONOTONICITY`: exercise and make observable: Increasing the active segment count cannot reduce the settled DAC output for vref above vss. Required traces: `time`, `seg0`, `seg1`, `seg2`, `seg3`, `seg4`, `seg5`, `seg6`, `seg7`, `seg8`, `seg9`, `seg10`, `seg11`, `seg12`, `seg13`, `seg14`, `vref`, `vss`, `aout`.

The required trace names are: `time`, `seg0`, `seg1`, `seg2`, `seg3`, `seg4`, `seg5`, `seg6`, `seg7`, `seg8`, `seg9`, `seg10`, `seg11`, `seg12`, `seg13`, `seg14`, `vref`, `vss`, `aout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
