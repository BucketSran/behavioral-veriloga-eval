# Settling Window Detector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `settling_window_detector.va`:
  - Module `settling_window_detector` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `target` (input, electrical)
    - position 2: `tol` (input, electrical)
    - position 3: `settled` (output, electrical)
    - position 4: `t_code0` (output, electrical)
    - position 5: `t_code1` (output, electrical)
    - position 6: `t_code2` (output, electrical)
    - position 7: `t_code3` (output, electrical)
    - position 8: `t_code4` (output, electrical)
    - position 9: `t_code5` (output, electrical)
    - position 10: `t_code6` (output, electrical)
    - position 11: `t_code7` (output, electrical)

## Public Parameter Contract

- `settling_window_detector.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded settled and time-code high level.
- `settling_window_detector.tr` defaults to `2e-11` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_WINDOW_DEFINITION`: restore: The input is qualified in-window exactly while the absolute vin-to-target error is no greater than tol. Required traces: `time`, `vin`, `target`, `tol`, `settled`, `t_code0`, `t_code1`, `t_code2`, `t_code3`, `t_code4`, `t_code5`, `t_code6`, `t_code7`.
- `P_ENTRY_AND_HOLD`: restore: Entering the window records the entry time, but settled remains low until vin has stayed continuously in-window for at least 20 ns. Required traces: `time`, `vin`, `target`, `tol`, `settled`, `t_code0`, `t_code1`, `t_code2`, `t_code3`, `t_code4`, `t_code5`, `t_code6`, `t_code7`.
- `P_EXIT_RESETS_QUALIFICATION`: restore: Leaving the tolerance window before or after qualification clears the entry state, drives settled low, and clears the time code. Required traces: `time`, `vin`, `target`, `tol`, `settled`, `t_code0`, `t_code1`, `t_code2`, `t_code3`, `t_code4`, `t_code5`, `t_code6`, `t_code7`.
- `P_ENTRY_TIME_CODE`: restore: After qualification, t_code[7:0] reports the rounded window-entry time in whole nanoseconds, saturated to 0 through 255. Required traces: `time`, `vin`, `target`, `tol`, `settled`, `t_code0`, `t_code1`, `t_code2`, `t_code3`, `t_code4`, `t_code5`, `t_code6`, `t_code7`.
- `P_BIT_ORDER_AND_LEVELS`: restore: t_code0 is the least significant bit and t_code7 is the most significant bit; asserted outputs use vdd and inactive outputs use 0 V. Required traces: `time`, `settled`, `t_code0`, `t_code1`, `t_code2`, `t_code3`, `t_code4`, `t_code5`, `t_code6`, `t_code7`.

## Modeling Constraints

- Use deterministic continuous window qualification with stored entry-time state.
- Treat the public 20 ns hold interval and 1 ns time-code quantum as circuit-contract values, not stimulus timing.
- Use smooth voltage contributions for all outputs.
- Do not add hidden observables, validation hooks, current contributions, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `settling_window_detector.va`.
Every supplied `.va` file is editable; do not add or omit files.
