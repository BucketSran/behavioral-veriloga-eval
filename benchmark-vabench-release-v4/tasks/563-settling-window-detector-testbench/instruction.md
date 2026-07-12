# Settling Window Detector Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Settling Window Detector` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `settling_window_detector` as `XDUT` with ordered public binding: vin=vin, target=target, tol=tol, settled=settled, t_code0=t_code0, t_code1=t_code1, t_code2=t_code2, t_code3=t_code3, t_code4=t_code4, t_code5=t_code5, t_code6=t_code6, t_code7=t_code7.

## Public Parameter Contract

- `settling_window_detector.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded settled and time-code high level.
- `settling_window_detector.tr` defaults to `2e-11` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_WINDOW_DEFINITION`: exercise and make observable: The input is qualified in-window exactly while the absolute vin-to-target error is no greater than tol. Required traces: `time`, `vin`, `target`, `tol`, `settled`, `t_code0`, `t_code1`, `t_code2`, `t_code3`, `t_code4`, `t_code5`, `t_code6`, `t_code7`.
- `P_ENTRY_AND_HOLD`: exercise and make observable: Entering the window records the entry time, but settled remains low until vin has stayed continuously in-window for at least 20 ns. Required traces: `time`, `vin`, `target`, `tol`, `settled`, `t_code0`, `t_code1`, `t_code2`, `t_code3`, `t_code4`, `t_code5`, `t_code6`, `t_code7`.
- `P_EXIT_RESETS_QUALIFICATION`: exercise and make observable: Leaving the tolerance window before or after qualification clears the entry state, drives settled low, and clears the time code. Required traces: `time`, `vin`, `target`, `tol`, `settled`, `t_code0`, `t_code1`, `t_code2`, `t_code3`, `t_code4`, `t_code5`, `t_code6`, `t_code7`.
- `P_ENTRY_TIME_CODE`: exercise and make observable: After qualification, t_code[7:0] reports the rounded window-entry time in whole nanoseconds, saturated to 0 through 255. Required traces: `time`, `vin`, `target`, `tol`, `settled`, `t_code0`, `t_code1`, `t_code2`, `t_code3`, `t_code4`, `t_code5`, `t_code6`, `t_code7`.
- `P_BIT_ORDER_AND_LEVELS`: exercise and make observable: t_code0 is the least significant bit and t_code7 is the most significant bit; asserted outputs use vdd and inactive outputs use 0 V. Required traces: `time`, `settled`, `t_code0`, `t_code1`, `t_code2`, `t_code3`, `t_code4`, `t_code5`, `t_code6`, `t_code7`.

The required trace names are: `time`, `vin`, `target`, `tol`, `settled`, `t_code0`, `t_code1`, `t_code2`, `t_code3`, `t_code4`, `t_code5`, `t_code6`, `t_code7`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
