# Two-stage Pipeline ADC Mini Chain Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `pipeline_adc_top.va`:
  - Module `pipeline_adc_top` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `valid_i` (input, electrical)
    - position 4: `code_3` (output, electrical)
    - position 5: `code_2` (output, electrical)
    - position 6: `code_1` (output, electrical)
    - position 7: `code_0` (output, electrical)
    - position 8: `valid_o` (output, electrical)
    - position 9: `residue_dbg` (output, electrical)
- Artifact `stage1_quantizer.va`:
  - Module `stage1_quantizer` (required_submodule)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `valid_i` (input, electrical)
    - position 4: `bit_1` (output, electrical)
    - position 5: `bit_0` (output, electrical)
    - position 6: `valid_o` (output, electrical)
- Artifact `residue_amp.va`:
  - Module `residue_amp` (required_submodule)
    - position 0: `vin` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `s1_1` (input, electrical)
    - position 3: `s1_0` (input, electrical)
    - position 4: `residue_o` (output, electrical)
    - position 5: `residue_dbg` (output, electrical)
- Artifact `stage2_quantizer.va`:
  - Module `stage2_quantizer` (required_submodule)
    - position 0: `residue_i` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `valid_i` (input, electrical)
    - position 4: `bit_1` (output, electrical)
    - position 5: `bit_0` (output, electrical)
    - position 6: `valid_o` (output, electrical)
- Artifact `code_aligner.va`:
  - Module `code_aligner` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `s1_1` (input, electrical)
    - position 3: `s1_0` (input, electrical)
    - position 4: `s1_valid` (input, electrical)
    - position 5: `s2_1` (input, electrical)
    - position 6: `s2_0` (input, electrical)
    - position 7: `s2_valid` (input, electrical)
    - position 8: `code_3` (output, electrical)
    - position 9: `code_2` (output, electrical)
    - position 10: `code_1` (output, electrical)
    - position 11: `code_0` (output, electrical)
    - position 12: `valid_o` (output, electrical)

## Public Parameter Contract

- `pipeline_adc_top.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `pipeline_adc_top.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `pipeline_adc_top.vref` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vref for this module.
- `pipeline_adc_top.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `pipeline_adc_top.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `stage1_quantizer.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `stage1_quantizer.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `stage1_quantizer.vref` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vref for this module.
- `stage1_quantizer.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `stage1_quantizer.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `residue_amp.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `residue_amp.vref` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vref for this module.
- `residue_amp.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `residue_amp.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `stage2_quantizer.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `stage2_quantizer.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `stage2_quantizer.vref` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vref for this module.
- `stage2_quantizer.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `stage2_quantizer.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `code_aligner.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `code_aligner.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `code_aligner.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `code_aligner.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_PIPE_RESET_CLEAR`: restore: Reset clears both stages, output code, valid_o, and residue_dbg. Required traces: `time`, `rst`, `code_3`, `code_2`, `code_1`, `code_0`, `valid_o`, `residue_dbg`.
- `P_PIPE_RESIDUE`: restore: A valid input sample produces the four-times normalized residue for its coarse quarter range. Required traces: `time`, `vin`, `clk`, `rst`, `valid_i`, `residue_dbg`.
- `P_PIPE_ALIGNED_CODE`: restore: The delayed coarse and fine decisions align into the clamped 4-bit conversion code. Required traces: `time`, `vin`, `clk`, `valid_i`, `code_3`, `code_2`, `code_1`, `code_0`, `valid_o`.
- `P_PIPE_VALID_LATENCY`: restore: valid_o accompanies each completed pipeline result and no reset result is marked valid. Required traces: `time`, `clk`, `rst`, `valid_i`, `valid_o`.

## Modeling Constraints

- Use deterministic voltage-domain transient behavioral Verilog-A.
- Preserve the declared multi-module architecture and exact public artifact interfaces.
- Do not use current contributions, unsupported continuous operators, validation logic, hard-coded evaluator timing, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pipeline_adc_top.va`, `stage1_quantizer.va`, `residue_amp.va`, `stage2_quantizer.va`, `code_aligner.va`.
Every supplied `.va` file is editable; do not add or omit files.
