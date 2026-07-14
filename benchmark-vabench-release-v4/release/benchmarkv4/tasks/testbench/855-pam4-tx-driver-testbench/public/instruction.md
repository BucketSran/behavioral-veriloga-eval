# PAM4 Transmitter Driver Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `PAM4 Transmitter Driver` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `pam4_tx_top.va`:
  - Module `pam4_tx_top` (entry)
    - position 0: `bit_msb` (input, electrical)
    - position 1: `bit_lsb` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `emph_en` (input, electrical)
    - position 5: `vout` (output, electrical)
    - position 6: `level_1` (output, electrical)
    - position 7: `level_0` (output, electrical)
    - position 8: `delta_dbg` (output, electrical)
- Artifact `gray_mapper.va`:
  - Module `gray_mapper` (required_submodule)
    - position 0: `bit_msb` (input, electrical)
    - position 1: `bit_lsb` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `level_1` (output, electrical)
    - position 4: `level_0` (output, electrical)
- Artifact `level_dac.va`:
  - Module `level_dac` (required_submodule)
    - position 0: `level_1` (input, electrical)
    - position 1: `level_0` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `level_v` (output, electrical)
- Artifact `preemphasis_driver.va`:
  - Module `preemphasis_driver` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `emph_en` (input, electrical)
    - position 3: `level_1` (input, electrical)
    - position 4: `level_0` (input, electrical)
    - position 5: `level_v` (input, electrical)
    - position 6: `vout` (output, electrical)
    - position 7: `delta_dbg` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `pam4_tx_top` as `XDUT` with ordered public binding: bit_msb=bit_msb, bit_lsb=bit_lsb, clk=clk, rst=rst, emph_en=emph_en, vout=vout, level_1=level_1, level_0=level_0, delta_dbg=delta_dbg.

## Public Parameter Contract

- `pam4_tx_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module pam4_tx_top.
- `pam4_tx_top.vss` defaults to `0.0`; valid range: finite; overrides vss for module pam4_tx_top.
- `pam4_tx_top.vth` defaults to `0.45`; valid range: finite; overrides vth for module pam4_tx_top.
- `pam4_tx_top.level_step` defaults to `0.3`; valid range: finite; overrides level_step for module pam4_tx_top.
- `pam4_tx_top.emph_step` defaults to `60e-3`; valid range: finite; overrides emph_step for module pam4_tx_top.
- `pam4_tx_top.tr` defaults to `200e-12`; valid range: finite; overrides tr for module pam4_tx_top.
- `gray_mapper.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module gray_mapper.
- `gray_mapper.vss` defaults to `0.0`; valid range: finite; overrides vss for module gray_mapper.
- `gray_mapper.vth` defaults to `0.45`; valid range: finite; overrides vth for module gray_mapper.
- `gray_mapper.tr` defaults to `200e-12`; valid range: finite; overrides tr for module gray_mapper.
- `level_dac.vss` defaults to `0.0`; valid range: finite; overrides vss for module level_dac.
- `level_dac.vth` defaults to `0.45`; valid range: finite; overrides vth for module level_dac.
- `level_dac.level_step` defaults to `0.3`; valid range: finite; overrides level_step for module level_dac.
- `level_dac.tr` defaults to `200e-12`; valid range: finite; overrides tr for module level_dac.
- `preemphasis_driver.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module preemphasis_driver.
- `preemphasis_driver.vss` defaults to `0.0`; valid range: finite; overrides vss for module preemphasis_driver.
- `preemphasis_driver.vth` defaults to `0.45`; valid range: finite; overrides vth for module preemphasis_driver.
- `preemphasis_driver.level_step` defaults to `0.3`; valid range: finite; overrides level_step for module preemphasis_driver.
- `preemphasis_driver.emph_step` defaults to `60e-3`; valid range: finite; overrides emph_step for module preemphasis_driver.
- `preemphasis_driver.tr` defaults to `200e-12`; valid range: finite; overrides tr for module preemphasis_driver.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_CLEAR`: exercise and make observable: Reset clears mapped level, transition delta, and output drive. Required traces: `time`, `rst`, `vout`, `level_1`, `level_0`, `delta_dbg`.
- `P_GRAY_LEVEL_MAP`: exercise and make observable: The input bits map to levels 0, 1, 2, 3 in the declared Gray order. Required traces: `time`, `bit_msb`, `bit_lsb`, `clk`, `rst`, `level_1`, `level_0`.
- `P_LEVEL_DAC`: exercise and make observable: The mapped level selects the corresponding level-step voltage. Required traces: `time`, `clk`, `rst`, `level_1`, `level_0`, `vout`.
- `P_PREEMPHASIS`: exercise and make observable: Enabled pre-emphasis follows the sign of the symbol-to-symbol mapped-level transition. Required traces: `time`, `bit_msb`, `bit_lsb`, `clk`, `rst`, `emph_en`, `vout`, `level_1`, `level_0`, `delta_dbg`.
- `P_OUTPUT_CLAMP`: exercise and make observable: The driven output remains between VSS and VDD. Required traces: `time`, `rst`, `vout`.

The required trace names are: `time`, `bit_msb`, `bit_lsb`, `clk`, `rst`, `emph_en`, `vout`, `level_1`, `level_0`, `delta_dbg`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
