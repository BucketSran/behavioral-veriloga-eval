# SARFEND Logic 4b Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `SARFEND Logic 4b` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `sarfend_logic_4b.va`:
  - Module `sarfend_logic_4b` (entry)
    - position 0: `clks` (input, electrical)
    - position 1: `dcomp` (input, electrical)
    - position 2: `dcompb` (input, electrical)
    - position 3: `test` (input, electrical)
    - position 4: `dtest0` (input, electrical)
    - position 5: `dtest1` (input, electrical)
    - position 6: `dtest2` (input, electrical)
    - position 7: `dtest3` (input, electrical)
    - position 8: `clkc` (output, electrical)
    - position 9: `dp1` (output, electrical)
    - position 10: `dp2` (output, electrical)
    - position 11: `dp3` (output, electrical)
    - position 12: `dp4` (output, electrical)
    - position 13: `dm1` (output, electrical)
    - position 14: `dm2` (output, electrical)
    - position 15: `dm3` (output, electrical)
    - position 16: `dm4` (output, electrical)
    - position 17: `dout0` (output, electrical)
    - position 18: `dout1` (output, electrical)
    - position 19: `dout2` (output, electrical)
    - position 20: `dout3` (output, electrical)

Stable public Spectre binding:

The submitted `testbench.scs` must use the supplied DUT through this public binding:

- Include path: `./dut/sarfend_logic_4b.va`
- DUT instance: `XDUT (clks dcomp dcompb test dtest0 dtest1 dtest2 dtest3 clkc dp1 dp2 dp3 dp4 dm1 dm2 dm3 dm4 dout0 dout1 dout2 dout3) sarfend_logic_4b`
- Required saved public traces: `clkc`, `clks`, `dcomp`, `dcompb`, `dm1`, `dm2`, `dm3`, `dm4`, `dout0`, `dout1`, `dout2`, `dout3`, `dp1`, `dp2`, `dp3`, `dp4`, `dtest0`, `dtest1`, `dtest2`, `dtest3`, `test`
- Use one bounded transient analysis with a finite positive stop time.

You must design the stimulus yourself. Save traces as bare public signal names
(for example `clk`, not suffixed or hierarchical forms such as `clk:V` or
`XDUT.clk`). Do not redefine the DUT, drive DUT output nets, save
hierarchical/private nodes, or use checker/gold/internal files.

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CONVERSION_RESET_AND_PREVIOUS_WORD`: exercise and make observable: Each rising `clks` crossing publishes the previous DAC-P word on `dout0..dout3`, resets the conversion pointer, and initializes controls for a new conversion. Required traces: `time`, `clkc`, `clks`, `dcomp`, `dcompb`, `dm1`, `dm2`, `dm3`, `dm4`, `dout0`, `dout1`, `dout2`, `dout3`, `dp1`, `dp2`, `dp3`, `dp4`, `dtest0`, `dtest1`, `dtest2`, `dtest3`, `test`.
- `P_SAMPLE_AND_COMPARATOR_DECISIONS`: exercise and make observable: The conversion captures comparator inputs and updates SAR decisions with the declared `dcomp/dcompb` polarity. Required traces: `time`, `clkc`, `clks`, `dcomp`, `dcompb`, `dm1`, `dm2`, `dm3`, `dm4`, `dout0`, `dout1`, `dout2`, `dout3`, `dp1`, `dp2`, `dp3`, `dp4`, `dtest0`, `dtest1`, `dtest2`, `dtest3`, `test`.
- `P_TEST_OVERRIDE_BEHAVIOR`: exercise and make observable: The public test override controls the DAC/control outputs when asserted and does not corrupt normal conversion state. Required traces: `time`, `clkc`, `clks`, `dcomp`, `dcompb`, `dm1`, `dm2`, `dm3`, `dm4`, `dout0`, `dout1`, `dout2`, `dout3`, `dp1`, `dp2`, `dp3`, `dp4`, `dtest0`, `dtest1`, `dtest2`, `dtest3`, `test`.
- `P_DOUT_BIT_MAPPING`: exercise and make observable: `dout0..dout3` preserve the declared bit order of the previous DAC-P state. Required traces: `time`, `clkc`, `clks`, `dcomp`, `dcompb`, `dm1`, `dm2`, `dm3`, `dm4`, `dout0`, `dout1`, `dout2`, `dout3`, `dp1`, `dp2`, `dp3`, `dp4`, `dtest0`, `dtest1`, `dtest2`, `dtest3`, `test`.
- `P_LOGIC_OUTPUT_LEVELS`: exercise and make observable: Handshake, DAC-control, and data outputs use full voltage-coded low/high levels. Required traces: `time`, `clkc`, `clks`, `dcomp`, `dcompb`, `dm1`, `dm2`, `dm3`, `dm4`, `dout0`, `dout1`, `dout2`, `dout3`, `dp1`, `dp2`, `dp3`, `dp4`, `dtest0`, `dtest1`, `dtest2`, `dtest3`, `test`.


The following canonical public behavior is normative for this derived form:

On each rising `clks` crossing, publish the previous cycle DAC-P word on `dout0..dout3`, reset the conversion pointer, initialize the DAC controls for a new conversion, capture the test override word, and clear `clkc`. On falling `clks`, assert `clkc` to start comparison. While `clks` is low, comparator output reset/recovery should reassert `clkc`; comparator decision activity should capture one MSB-to-LSB decision per step. With `test` low, use the live comparator decision; with `test` high, use the captured test bit for that step. Drive complementary `dp`/`dm` controls and stop requesting comparisons after four decisions.


The required trace names are: `time`, `clkc`, `clks`, `dcomp`, `dcompb`, `dm1`, `dm2`, `dm3`, `dm4`, `dout0`, `dout1`, `dout2`, `dout3`, `dp1`, `dp2`, `dp3`, `dp4`, `dtest0`, `dtest1`, `dtest2`, `dtest3`, `test`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.

- `dout3=dp4`, `dout2=dp3`, `dout1=dp2`, and `dout0=dp1`

- `dp4=dm4=0` and `dp3=dm3=dp2=dm2=dp1=dm1=1`

- consume the test override bits in the order `dtest3`, `dtest2`, `dtest1`, then `dtest0`
