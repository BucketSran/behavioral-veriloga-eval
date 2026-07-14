# Two-stage Pipeline ADC Mini Chain Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Two-stage Pipeline ADC Mini Chain` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `pipeline_adc_top` as `XDUT` with ordered public binding: vin=vin, clk=clk, rst=rst, valid_i=valid_i, code_3=code_3, code_2=code_2, code_1=code_1, code_0=code_0, valid_o=valid_o, residue_dbg=residue_dbg.

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

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_PIPE_RESET_CLEAR`: exercise and make observable: Reset clears both stages, output code, valid_o, and residue_dbg. Required traces: `time`, `rst`, `code_3`, `code_2`, `code_1`, `code_0`, `valid_o`, `residue_dbg`.
- `P_PIPE_RESIDUE`: exercise and make observable: A valid input sample produces the four-times normalized residue for its coarse quarter range. Required traces: `time`, `vin`, `clk`, `rst`, `valid_i`, `residue_dbg`.
- `P_PIPE_ALIGNED_CODE`: exercise and make observable: The delayed coarse and fine decisions align into the clamped 4-bit conversion code. Required traces: `time`, `vin`, `clk`, `valid_i`, `code_3`, `code_2`, `code_1`, `code_0`, `valid_o`.
- `P_PIPE_VALID_LATENCY`: exercise and make observable: valid_o accompanies each completed pipeline result and no reset result is marked valid. Required traces: `time`, `clk`, `rst`, `valid_i`, `valid_o`.

The required trace names are: `time`, `vin`, `clk`, `rst`, `valid_i`, `code_3`, `code_2`, `code_1`, `code_0`, `valid_o`, `residue_dbg`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
