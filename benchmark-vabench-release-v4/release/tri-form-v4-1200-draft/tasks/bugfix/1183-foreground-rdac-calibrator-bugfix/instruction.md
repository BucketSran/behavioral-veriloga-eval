# Foreground RDAC Calibrator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `foreground_rdac_calibrator.va`:
  - Module `foreground_rdac_calibrator` (entry)
    - position 0: `ck` (input, electrical)
    - position 1: `d` (input, electrical)
    - position 2: `vrefp` (input, electrical)
    - position 3: `vrefn` (input, electrical)
    - position 4: `dc0` (output, electrical)
    - position 5: `dc1` (output, electrical)
    - position 6: `dc2` (output, electrical)
    - position 7: `dc3` (output, electrical)
    - position 8: `dc4` (output, electrical)
    - position 9: `dc5` (output, electrical)
    - position 10: `dc6` (output, electrical)
    - position 11: `cvinp` (output, electrical)
    - position 12: `cvinn` (output, electrical)
    - position 13: `en` (output, electrical)
    - position 14: `enb` (output, electrical)

## Public Parameter Contract

- `foreground_rdac_calibrator.vdd` defaults to `1.0`; valid range: finite; overrides vdd.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_MSB_TRIAL_CODE`: restore: At startup, calibration is active with `dc6` asserted and all lower RDAC bits deasserted. Required traces: `time`, `ck`, `cvinn`, `cvinp`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `en`, `enb`, `vrefn`, `vrefp`.
- `P_CLOCKED_RDAC_DECISION_SEQUENCE`: restore: On each rising `ck` crossing while active, resolve the current trial bit from `d` versus `vth` and advance from MSB to LSB. Required traces: `time`, `ck`, `cvinn`, `cvinp`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `en`, `enb`, `vrefn`, `vrefp`.
- `P_DECISION_POLARITY`: restore: Comparator-low and comparator-high decisions update the trial bit in the declared polarity without inverting the search direction. Required traces: `time`, `ck`, `cvinn`, `cvinp`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `en`, `enb`, `vrefn`, `vrefp`.
- `P_CALIBRATION_COMPLETION`: restore: After the final RDAC decision, deassert calibration enable and hold the completed code. Required traces: `time`, `ck`, `cvinn`, `cvinp`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `en`, `enb`, `vrefn`, `vrefp`.
- `P_RDAC_OUTPUT_LEVELS`: restore: All RDAC code and enable outputs remain voltage-coded at valid low/high levels. Required traces: `time`, `ck`, `cvinn`, `cvinp`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `en`, `enb`, `vrefn`, `vrefp`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `foreground_rdac_calibrator.va`.
Every supplied `.va` file is editable; do not add or omit files.
