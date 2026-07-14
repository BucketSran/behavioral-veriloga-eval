# Folded Flash DAC 4b Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Folded Flash DAC 4b` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `folded_flash_dac_4b.va`:
  - Module `folded_flash_dac_4b` (entry)
    - position 0: `vd4` (input, electrical)
    - position 1: `vd3` (input, electrical)
    - position 2: `vd2` (input, electrical)
    - position 3: `vd1` (input, electrical)
    - position 4: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `folded_flash_dac_4b` as `XDUT` with ordered public binding: vd4=vd4, vd3=vd3, vd2=vd2, vd1=vd1, vout=vout.

## Public Parameter Contract

- `folded_flash_dac_4b.vref` defaults to `1 from [0:inf]`; valid range: finite; overrides vref.
- `folded_flash_dac_4b.trise` defaults to `1p from [0:inf]`; valid range: finite; overrides trise.
- `folded_flash_dac_4b.tfall` defaults to `1p from [0:inf]`; valid range: finite; overrides tfall.
- `folded_flash_dac_4b.tdel` defaults to `0 from [0:inf]`; valid range: finite; overrides tdel.
- `folded_flash_dac_4b.vtrans` defaults to `0.45`; valid range: finite; overrides vtrans.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_VOLTAGE_CODED_SUBCODE_DECODE`: exercise and make observable: `vd1` through `vd3` form the lower subcode and `vd4` selects the folded branch using `vtrans`. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vout`.
- `P_FOLD_MIRROR_TRANSFER`: exercise and make observable: The upper folded branch mirrors the subcode around the fold center instead of using a direct unsigned code. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vout`.
- `P_OUTPUT_SCALE_DENOMINATOR`: exercise and make observable: The folded code is scaled by the declared 4-bit denominator and reference before driving `vout`. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vout`.

The required trace names are: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
