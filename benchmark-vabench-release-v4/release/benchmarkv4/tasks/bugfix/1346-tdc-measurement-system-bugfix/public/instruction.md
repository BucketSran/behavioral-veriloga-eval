# TDC Event Measurement System Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `tdc_measurement_top.va`:
  - Module `tdc_measurement_top` (entry)
    - position 0: `start` (input, electrical)
    - position 1: `stop` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `code_7` (output, electrical)
    - position 5: `code_6` (output, electrical)
    - position 6: `code_5` (output, electrical)
    - position 7: `code_4` (output, electrical)
    - position 8: `code_3` (output, electrical)
    - position 9: `code_2` (output, electrical)
    - position 10: `code_1` (output, electrical)
    - position 11: `code_0` (output, electrical)
    - position 12: `valid` (output, electrical)
    - position 13: `overflow` (output, electrical)
- Artifact `edge_detector.va`:
  - Module `edge_detector` (required_submodule)
    - position 0: `start` (input, electrical)
    - position 1: `stop` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `clear_i` (input, electrical)
    - position 4: `start_evt` (output, electrical)
    - position 5: `stop_evt` (output, electrical)
- Artifact `interval_counter.va`:
  - Module `interval_counter` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `start_evt` (input, electrical)
    - position 3: `stop_evt` (input, electrical)
    - position 4: `count_7` (output, electrical)
    - position 5: `count_6` (output, electrical)
    - position 6: `count_5` (output, electrical)
    - position 7: `count_4` (output, electrical)
    - position 8: `count_3` (output, electrical)
    - position 9: `count_2` (output, electrical)
    - position 10: `count_1` (output, electrical)
    - position 11: `count_0` (output, electrical)
    - position 12: `valid_i` (output, electrical)
    - position 13: `overflow_i` (output, electrical)
    - position 14: `clear_o` (output, electrical)
- Artifact `binary_encoder.va`:
  - Module `binary_encoder` (required_submodule)
    - position 0: `count_7` (input, electrical)
    - position 1: `count_6` (input, electrical)
    - position 2: `count_5` (input, electrical)
    - position 3: `count_4` (input, electrical)
    - position 4: `count_3` (input, electrical)
    - position 5: `count_2` (input, electrical)
    - position 6: `count_1` (input, electrical)
    - position 7: `count_0` (input, electrical)
    - position 8: `code_7` (output, electrical)
    - position 9: `code_6` (output, electrical)
    - position 10: `code_5` (output, electrical)
    - position 11: `code_4` (output, electrical)
    - position 12: `code_3` (output, electrical)
    - position 13: `code_2` (output, electrical)
    - position 14: `code_1` (output, electrical)
    - position 15: `code_0` (output, electrical)
- Artifact `valid_latch.va`:
  - Module `valid_latch` (required_submodule)
    - position 0: `rst` (input, electrical)
    - position 1: `start_evt` (input, electrical)
    - position 2: `valid_i` (input, electrical)
    - position 3: `overflow_i` (input, electrical)
    - position 4: `valid` (output, electrical)
    - position 5: `overflow` (output, electrical)

## Public Parameter Contract

- `tdc_measurement_top.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `tdc_measurement_top.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `tdc_measurement_top.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `tdc_measurement_top.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `edge_detector.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `edge_detector.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `edge_detector.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `edge_detector.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `interval_counter.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `interval_counter.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `interval_counter.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `interval_counter.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `binary_encoder.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `binary_encoder.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `binary_encoder.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `binary_encoder.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `valid_latch.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `valid_latch.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `valid_latch.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `valid_latch.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_TDC_RESET_CLEAR`: restore: Reset clears count code, valid, and overflow. Required traces: `time`, `rst`, `code_7`, `code_6`, `code_5`, `code_4`, `code_3`, `code_2`, `code_1`, `code_0`, `valid`, `overflow`.
- `P_TDC_RESTART_CLEAR`: restore: Each rising start edge begins a new interval and clears valid and overflow. Required traces: `time`, `start`, `rst`, `valid`, `overflow`.
- `P_TDC_INTERVAL_COUNT`: restore: The first stop after start latches the number of intervening rising clock edges. Required traces: `time`, `start`, `stop`, `clk`, `code_7`, `code_6`, `code_5`, `code_4`, `code_3`, `code_2`, `code_1`, `code_0`.
- `P_TDC_VALID_LATCH`: restore: A completed interval asserts valid and preserves its code until restart or reset. Required traces: `time`, `start`, `stop`, `clk`, `valid`, `code_7`, `code_0`.
- `P_TDC_OVERFLOW`: restore: The 256th armed clock saturates code at 255, asserts overflow and valid, and disarms. Required traces: `time`, `start`, `stop`, `clk`, `code_7`, `code_6`, `code_5`, `code_4`, `code_3`, `code_2`, `code_1`, `code_0`, `valid`, `overflow`.

## Modeling Constraints

- Use deterministic voltage-domain transient behavioral Verilog-A.
- Preserve the declared multi-module architecture and exact public artifact interfaces.
- Do not use current contributions, unsupported continuous operators, validation logic, hard-coded evaluator timing, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `tdc_measurement_top.va`, `edge_detector.va`, `interval_counter.va`, `binary_encoder.va`, `valid_latch.va`.
Every supplied `.va` file is editable; do not add or omit files.
