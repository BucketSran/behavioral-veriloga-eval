# Bipolar DAC 4b Continuous Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Bipolar DAC 4b Continuous` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `bipolar_dac_4b_continuous.va`:
  - Module `bipolar_dac_4b_continuous` (entry)
    - position 0: `vd3` (input, electrical)
    - position 1: `vd2` (input, electrical)
    - position 2: `vd1` (input, electrical)
    - position 3: `vd0` (input, electrical)
    - position 4: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `bipolar_dac_4b_continuous` as `XDUT` with ordered public binding: vd3=vd3, vd2=vd2, vd1=vd1, vd0=vd0, vout=vout.

## Public Parameter Contract

- `bipolar_dac_4b_continuous.vref` defaults to `0.9` V; valid range: vref > 0; sets positive and negative full-scale output magnitudes.
- `bipolar_dac_4b_continuous.trise` defaults to `2e-11` s; valid range: trise >= 0; sets vout rise smoothing.
- `bipolar_dac_4b_continuous.tfall` defaults to `2e-11` s; valid range: tfall >= 0; sets vout fall smoothing.
- `bipolar_dac_4b_continuous.tdel` defaults to `0.0` s; valid range: tdel >= 0; sets vout transition delay.
- `bipolar_dac_4b_continuous.vtrans` defaults to `0.45` V; valid range: finite real; sets the logic threshold for all four voltage-coded input bits.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_UNSIGNED_BIT_DECODE`: exercise and make observable: Each input is decoded continuously as one only when its voltage exceeds vtrans, with vd3 as MSB and vd0 as LSB. Required traces: `time`, `vd3`, `vd2`, `vd1`, `vd0`, `vout`.
- `P_NEGATIVE_FULL_SCALE`: exercise and make observable: Unsigned code 0 produces approximately negative vref. Required traces: `time`, `vd3`, `vd2`, `vd1`, `vd0`, `vout`.
- `P_POSITIVE_FULL_SCALE`: exercise and make observable: Unsigned code 15 produces approximately positive vref. Required traces: `time`, `vd3`, `vd2`, `vd1`, `vd0`, `vout`.
- `P_UNIFORM_CODE_STEP`: exercise and make observable: Every one-code increase raises the output target by the same voltage increment across codes 0 through 15. Required traces: `time`, `vd3`, `vd2`, `vd1`, `vd0`, `vout`.
- `P_MONOTONIC_TRANSFER`: exercise and make observable: The output is strictly monotonic with increasing unsigned code for vref greater than zero. Required traces: `time`, `vd3`, `vd2`, `vd1`, `vd0`, `vout`.
- `P_CONTINUOUS_REEVALUATION`: exercise and make observable: The DAC target responds to input-code threshold changes without requiring a clock event, using tdel, trise, and tfall for output timing. Required traces: `time`, `vd3`, `vd2`, `vd1`, `vd0`, `vout`.

The required trace names are: `time`, `vd3`, `vd2`, `vd1`, `vd0`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
