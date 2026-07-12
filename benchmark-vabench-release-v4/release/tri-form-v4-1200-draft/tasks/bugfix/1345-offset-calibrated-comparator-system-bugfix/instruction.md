# Offset-calibrated Comparator System Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `calibrated_comparator_top.va`:
  - Module `calibrated_comparator_top` (entry)
    - position 0: `vinp` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `cal_en` (input, electrical)
    - position 5: `cal_ref` (input, electrical)
    - position 6: `decision` (output, electrical)
    - position 7: `ready` (output, electrical)
    - position 8: `offset_3` (output, electrical)
    - position 9: `offset_2` (output, electrical)
    - position 10: `offset_1` (output, electrical)
    - position 11: `offset_0` (output, electrical)
    - position 12: `threshold_dbg` (output, electrical)
- Artifact `comparator_core.va`:
  - Module `comparator_core` (required_submodule)
    - position 0: `vinp` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `threshold_i` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `decision` (output, electrical)
- Artifact `offset_dac.va`:
  - Module `offset_dac` (required_submodule)
    - position 0: `offset_3` (input, electrical)
    - position 1: `offset_2` (input, electrical)
    - position 2: `offset_1` (input, electrical)
    - position 3: `offset_0` (input, electrical)
    - position 4: `rst` (input, electrical)
    - position 5: `threshold_dbg` (output, electrical)
- Artifact `calibration_fsm.va`:
  - Module `calibration_fsm` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `cal_en` (input, electrical)
    - position 3: `cal_ref` (input, electrical)
    - position 4: `ready` (output, electrical)
    - position 5: `offset_3` (output, electrical)
    - position 6: `offset_2` (output, electrical)
    - position 7: `offset_1` (output, electrical)
    - position 8: `offset_0` (output, electrical)

## Public Parameter Contract

- `calibrated_comparator_top.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `calibrated_comparator_top.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `calibrated_comparator_top.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `calibrated_comparator_top.offset_lsb` defaults to `5e-3` V; valid range: finite and consistent with the declared rail domain; overrides offset_lsb for this module.
- `calibrated_comparator_top.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `comparator_core.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `comparator_core.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `comparator_core.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `comparator_core.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `offset_dac.offset_lsb` defaults to `5e-3` V; valid range: finite and consistent with the declared rail domain; overrides offset_lsb for this module.
- `offset_dac.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `offset_dac.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `offset_dac.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.
- `calibration_fsm.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `calibration_fsm.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `calibration_fsm.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `calibration_fsm.tr` defaults to `200p` s; valid range: tr > 0; overrides tr for this module.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CAL_RESET_CLEAR`: restore: Reset clears offset code, decision, ready, and threshold_dbg. Required traces: `time`, `rst`, `offset_3`, `offset_2`, `offset_1`, `offset_0`, `decision`, `ready`, `threshold_dbg`.
- `P_CAL_CODE_UPDATE`: restore: Each enabled rising clock updates and clamps the offset code in the direction selected by cal_ref. Required traces: `time`, `clk`, `rst`, `cal_en`, `cal_ref`, `offset_3`, `offset_2`, `offset_1`, `offset_0`.
- `P_CAL_OFFSET_DAC`: restore: threshold_dbg equals signed code minus eight times offset_lsb outside reset. Required traces: `time`, `rst`, `offset_3`, `offset_2`, `offset_1`, `offset_0`, `threshold_dbg`.
- `P_CAL_READY_QUALIFICATION`: restore: ready asserts after four updates in one calibration window and the code holds while cal_en is low. Required traces: `time`, `clk`, `rst`, `cal_en`, `ready`, `offset_3`, `offset_2`, `offset_1`, `offset_0`.
- `P_CAL_COMPARATOR_DECISION`: restore: decision reflects the sign of vinp minus vinn plus threshold_dbg and is low in reset. Required traces: `time`, `vinp`, `vinn`, `rst`, `threshold_dbg`, `decision`.

## Modeling Constraints

- Use deterministic voltage-domain transient behavioral Verilog-A.
- Preserve the declared multi-module architecture and exact public artifact interfaces.
- Do not use current contributions, unsupported continuous operators, validation logic, hard-coded evaluator timing, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `calibrated_comparator_top.va`, `comparator_core.va`, `offset_dac.va`, `calibration_fsm.va`.
Every supplied `.va` file is editable; do not add or omit files.
