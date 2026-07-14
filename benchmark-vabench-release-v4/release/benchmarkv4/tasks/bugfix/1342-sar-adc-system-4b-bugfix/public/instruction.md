# 4-bit SAR ADC System Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `sar_adc_top.va`:
  - Module `sar_adc_top` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `start` (input, electrical)
    - position 4: `code_3` (output, electrical)
    - position 5: `code_2` (output, electrical)
    - position 6: `code_1` (output, electrical)
    - position 7: `code_0` (output, electrical)
    - position 8: `done` (output, electrical)
    - position 9: `sample_dbg` (output, electrical)
    - position 10: `dac_dbg` (output, electrical)
- Artifact `sample_hold.va`:
  - Module `sample_hold` (required_submodule)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `sample_en` (input, electrical)
    - position 4: `sample_o` (output, electrical)
    - position 5: `sample_dbg` (output, electrical)
- Artifact `sar_comparator.va`:
  - Module `sar_comparator` (required_submodule)
    - position 0: `sample_i` (input, electrical)
    - position 1: `dac_i` (input, electrical)
    - position 2: `cmp_o` (output, electrical)
- Artifact `sar_controller.va`:
  - Module `sar_controller` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `start` (input, electrical)
    - position 3: `cmp_i` (input, electrical)
    - position 4: `sample_en` (output, electrical)
    - position 5: `trial_3` (output, electrical)
    - position 6: `trial_2` (output, electrical)
    - position 7: `trial_1` (output, electrical)
    - position 8: `trial_0` (output, electrical)
    - position 9: `code_3` (output, electrical)
    - position 10: `code_2` (output, electrical)
    - position 11: `code_1` (output, electrical)
    - position 12: `code_0` (output, electrical)
    - position 13: `done` (output, electrical)
- Artifact `binary_weighted_cdac.va`:
  - Module `binary_weighted_cdac` (required_submodule)
    - position 0: `bit_3` (input, electrical)
    - position 1: `bit_2` (input, electrical)
    - position 2: `bit_1` (input, electrical)
    - position 3: `bit_0` (input, electrical)
    - position 4: `dac_o` (output, electrical)
    - position 5: `dac_dbg` (output, electrical)

## Public Parameter Contract

- `sar_adc_top.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `sar_adc_top.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `sar_adc_top.vref` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vref for this module.
- `sar_adc_top.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `sar_adc_top.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `sample_hold.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `sample_hold.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `sample_hold.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `sar_comparator.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `sar_comparator.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `sar_comparator.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `sar_comparator.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `sar_controller.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `sar_controller.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `sar_controller.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `sar_controller.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `binary_weighted_cdac.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `binary_weighted_cdac.vref` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vref for this module.
- `binary_weighted_cdac.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `binary_weighted_cdac.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_SAR_RESET_CLEAR`: restore: Reset clears conversion state, code, done, sample_dbg, and dac_dbg. Required traces: `time`, `rst`, `code_3`, `code_2`, `code_1`, `code_0`, `done`, `sample_dbg`, `dac_dbg`.
- `P_SAR_SAMPLE_HOLD`: restore: The first rising clock edge after start captures vin and sample_dbg holds that value through conversion. Required traces: `time`, `vin`, `clk`, `rst`, `start`, `sample_dbg`.
- `P_SAR_FINAL_CODE`: restore: Four MSB-first trials quantize the held sample to the clamped unsigned 4-bit SAR code. Required traces: `time`, `vin`, `clk`, `start`, `code_3`, `code_2`, `code_1`, `code_0`, `done`.
- `P_SAR_DAC_TRIAL`: restore: dac_dbg exposes vref times the active trial code divided by 16 and settles to the final-code DAC level. Required traces: `time`, `clk`, `code_3`, `code_2`, `code_1`, `code_0`, `done`, `dac_dbg`.

## Modeling Constraints

- Use deterministic voltage-domain transient behavioral Verilog-A.
- Preserve the declared multi-module architecture and exact public artifact interfaces.
- Do not use current contributions, unsupported continuous operators, validation logic, hard-coded evaluator timing, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `sar_adc_top.va`, `sample_hold.va`, `sar_comparator.va`, `sar_controller.va`, `binary_weighted_cdac.va`.
Every supplied `.va` file is editable; do not add or omit files.
