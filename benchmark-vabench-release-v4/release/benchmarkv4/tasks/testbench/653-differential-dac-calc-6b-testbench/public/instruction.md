# Differential DAC Calc 6b Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Differential DAC Calc 6b` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `differential_dac_calc_6b` as `XDUT` with ordered public binding: din0=din0, din1=din1, din2=din2, din3=din3, din4=din4, din5=din5, clks=clks, voutp=voutp, voutn=voutn.

## Public Parameter Contract

- `differential_dac_calc_6b.vth` defaults to `0.75`; valid range: finite; overrides vth.
- `differential_dac_calc_6b.vcm` defaults to `0.75`; valid range: finite; overrides vcm.
- `differential_dac_calc_6b.refp` defaults to `0.925`; valid range: finite; overrides refp.
- `differential_dac_calc_6b.refn` defaults to `0.575`; valid range: finite; overrides refn.
- `differential_dac_calc_6b.tt` defaults to `200p`; valid range: finite; overrides tt.
- `differential_dac_calc_6b.convdelay` defaults to `1n`; valid range: finite; overrides convdelay.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CLOCKED_SIX_BIT_WEIGHTED_CODE`: exercise and make observable: Each rising `clks` crossing samples `din0` through `din5` into the declared six-bit weighted DAC code. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `voutn`, `voutp`.
- `P_COMPLEMENTARY_DIFFERENTIAL_OUTPUTS`: exercise and make observable: `voutp` and `voutn` use complementary weighted sums about the common-mode value. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `voutn`, `voutp`.
- `P_OUTPUT_SWING_SCALE`: exercise and make observable: The differential outputs use the declared reference span and bit weights without extra swing scaling. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `voutn`, `voutp`.

The required trace names are: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `voutn`, `voutp`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
