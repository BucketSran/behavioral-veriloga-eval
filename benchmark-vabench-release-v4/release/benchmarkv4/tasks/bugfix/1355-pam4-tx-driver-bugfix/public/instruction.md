# PAM4 Transmitter Driver Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

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

The repaired bundle must satisfy every public property:

- `P_RESET_CLEAR`: restore: Reset clears mapped level, transition delta, and output drive. Required traces: `time`, `rst`, `vout`, `level_1`, `level_0`, `delta_dbg`.
- `P_GRAY_LEVEL_MAP`: restore: The input bits map to levels 0, 1, 2, 3 in the declared Gray order. Required traces: `time`, `bit_msb`, `bit_lsb`, `clk`, `rst`, `level_1`, `level_0`.
- `P_LEVEL_DAC`: restore: The mapped level selects the corresponding level-step voltage. Required traces: `time`, `clk`, `rst`, `level_1`, `level_0`, `vout`.
- `P_PREEMPHASIS`: restore: Enabled pre-emphasis follows the sign of the symbol-to-symbol mapped-level transition. Required traces: `time`, `bit_msb`, `bit_lsb`, `clk`, `rst`, `emph_en`, `vout`, `level_1`, `level_0`, `delta_dbg`.
- `P_OUTPUT_CLAMP`: restore: The driven output remains between VSS and VDD. Required traces: `time`, `rst`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Preserve the declared module graph, port order, parameter override behavior, and public trace observability.
- Do not hard-code evaluator stimulus, stop times, sample windows, checker tolerances, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pam4_tx_top.va`, `gray_mapper.va`, `level_dac.va`, `preemphasis_driver.va`.
Every supplied `.va` file is editable; do not add or omit files.
