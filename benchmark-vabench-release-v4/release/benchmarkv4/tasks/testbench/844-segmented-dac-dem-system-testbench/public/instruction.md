# Segmented DAC with DEM Control Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Segmented DAC with DEM Control` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `segmented_dac_dem_top.va`:
  - Module `segmented_dac_dem_top` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `code_5` (input, electrical)
    - position 3: `code_4` (input, electrical)
    - position 4: `code_3` (input, electrical)
    - position 5: `code_2` (input, electrical)
    - position 6: `code_1` (input, electrical)
    - position 7: `code_0` (input, electrical)
    - position 8: `vout` (output, electrical)
    - position 9: `sel_7` (output, electrical)
    - position 10: `sel_6` (output, electrical)
    - position 11: `sel_5` (output, electrical)
    - position 12: `sel_4` (output, electrical)
    - position 13: `sel_3` (output, electrical)
    - position 14: `sel_2` (output, electrical)
    - position 15: `sel_1` (output, electrical)
    - position 16: `sel_0` (output, electrical)
    - position 17: `ptr_2` (output, electrical)
    - position 18: `ptr_1` (output, electrical)
    - position 19: `ptr_0` (output, electrical)
- Artifact `thermometer_decoder.va`:
  - Module `thermometer_decoder` (required_submodule)
    - position 0: `code_5` (input, electrical)
    - position 1: `code_4` (input, electrical)
    - position 2: `code_3` (input, electrical)
    - position 3: `req_2` (output, electrical)
    - position 4: `req_1` (output, electrical)
    - position 5: `req_0` (output, electrical)
- Artifact `binary_decoder.va`:
  - Module `binary_decoder` (required_submodule)
    - position 0: `code_2` (input, electrical)
    - position 1: `code_1` (input, electrical)
    - position 2: `code_0` (input, electrical)
    - position 3: `fine_2` (output, electrical)
    - position 4: `fine_1` (output, electrical)
    - position 5: `fine_0` (output, electrical)
- Artifact `dwa_rotator.va`:
  - Module `dwa_rotator` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `req_2` (input, electrical)
    - position 3: `req_1` (input, electrical)
    - position 4: `req_0` (input, electrical)
    - position 5: `sel_7` (output, electrical)
    - position 6: `sel_6` (output, electrical)
    - position 7: `sel_5` (output, electrical)
    - position 8: `sel_4` (output, electrical)
    - position 9: `sel_3` (output, electrical)
    - position 10: `sel_2` (output, electrical)
    - position 11: `sel_1` (output, electrical)
    - position 12: `sel_0` (output, electrical)
    - position 13: `ptr_2` (output, electrical)
    - position 14: `ptr_1` (output, electrical)
    - position 15: `ptr_0` (output, electrical)
- Artifact `dac_driver.va`:
  - Module `dac_driver` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `req_2` (input, electrical)
    - position 3: `req_1` (input, electrical)
    - position 4: `req_0` (input, electrical)
    - position 5: `fine_2` (input, electrical)
    - position 6: `fine_1` (input, electrical)
    - position 7: `fine_0` (input, electrical)
    - position 8: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `segmented_dac_dem_top` as `XDUT` with ordered public binding: clk=clk, rst=rst, code_5=code_5, code_4=code_4, code_3=code_3, code_2=code_2, code_1=code_1, code_0=code_0, vout=vout, sel_7=sel_7, sel_6=sel_6, sel_5=sel_5, sel_4=sel_4, sel_3=sel_3, sel_2=sel_2, sel_1=sel_1, sel_0=sel_0, ptr_2=ptr_2, ptr_1=ptr_1, ptr_0=ptr_0.

## Public Parameter Contract

- `segmented_dac_dem_top.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `segmented_dac_dem_top.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `segmented_dac_dem_top.vref` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vref for this module.
- `segmented_dac_dem_top.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `segmented_dac_dem_top.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `thermometer_decoder.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `thermometer_decoder.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `thermometer_decoder.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `thermometer_decoder.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `binary_decoder.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `binary_decoder.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `binary_decoder.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `binary_decoder.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `dwa_rotator.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `dwa_rotator.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `dwa_rotator.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `dwa_rotator.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `dac_driver.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `dac_driver.vref` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vref for this module.
- `dac_driver.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `dac_driver.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_DEM_RESET_CLEAR`: exercise and make observable: Reset clears vout, unit selection mask, and rotation pointer. Required traces: `time`, `clk`, `rst`, `vout`, `sel_7`, `sel_6`, `sel_5`, `sel_4`, `sel_3`, `sel_2`, `sel_1`, `sel_0`, `ptr_2`, `ptr_1`, `ptr_0`.
- `P_DEM_DAC_TRANSFER`: exercise and make observable: Each rising clock samples the unsigned 6-bit code and drives vref times code divided by 63. Required traces: `time`, `clk`, `code_5`, `code_4`, `code_3`, `code_2`, `code_1`, `code_0`, `vout`.
- `P_DEM_ROTATED_MASK`: exercise and make observable: The selection mask contains the requested number of consecutive circular unit elements starting at the prior pointer. Required traces: `time`, `clk`, `code_5`, `code_4`, `code_3`, `sel_7`, `sel_6`, `sel_5`, `sel_4`, `sel_3`, `sel_2`, `sel_1`, `sel_0`.
- `P_DEM_POINTER_ADVANCE`: exercise and make observable: After each update the pointer advances by the requested unit count modulo eight. Required traces: `time`, `clk`, `code_5`, `code_4`, `code_3`, `ptr_2`, `ptr_1`, `ptr_0`.

The required trace names are: `time`, `clk`, `rst`, `code_5`, `code_4`, `code_3`, `code_2`, `code_1`, `code_0`, `vout`, `sel_7`, `sel_6`, `sel_5`, `sel_4`, `sel_3`, `sel_2`, `sel_1`, `sel_0`, `ptr_2`, `ptr_1`, `ptr_0`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
