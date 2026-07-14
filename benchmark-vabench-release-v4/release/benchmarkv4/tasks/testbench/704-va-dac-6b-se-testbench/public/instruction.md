# VA DAC 6b SE Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `VA DAC 6b SE` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `va_dac_6b_se` as `XDUT` with ordered public binding: din0=din0, din1=din1, din2=din2, din3=din3, din4=din4, din5=din5, rdy=rdy, aout=aout.

## Public Parameter Contract

- `va_dac_6b_se.vdd` defaults to `1.0`; valid range: finite; overrides vdd.
- `va_dac_6b_se.vth` defaults to `0.5`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_EACH_RISING_RDY_CROSSING_SAMPLE`: exercise and make observable: On each rising `rdy` crossing, sample `din0..din5` with switched weights `0.5, 1, 2, 4, 8, 16` from `din0` through `din5`. Map the sampled weighted code to a bipolar single-ended output scaled by `vdd` using this public normalization: Required traces: `time`, `aout`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `rdy`.
- `P_TEXT_WEIGHTED_CODE_16_DIN5_8`: exercise and make observable: ```text weighted_code = 16*din5 + 8*din4 + 4*din3 + 2*din2 + 1*din1 + 0.5*din0 aout = (weighted_code / 47.5) * 2.0 * vdd - vdd ``` Required traces: `time`, `aout`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `rdy`.
- `P_EACH_DIN_TERM_IS_1_WHEN`: exercise and make observable: Each `din*` term is `1` when the corresponding voltage is above `vth` and `0` otherwise. The denominator `47.5` is the fixed source normalization basis including the non-switching reference contribution. Required traces: `time`, `aout`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `rdy`.

The required trace names are: `time`, `aout`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `rdy`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
