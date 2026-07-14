# Comparator Offset Calibration Loop Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `comparator_offset_calibration_loop.va`:
  - Module `comparator_offset_calibration_loop` (entry)
    - position 0: `vdd` (input, electrical)
    - position 1: `vss` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `dcmpp` (input, electrical)
    - position 4: `vinp` (output, electrical)
    - position 5: `vinn` (output, electrical)
    - position 6: `offset_est` (output, electrical)
    - position 7: `valid` (output, electrical)

## Public Parameter Contract

- `comparator_offset_calibration_loop.step_initial` defaults to `0.064` V; valid range: step_initial > 0; sets the first signed differential search increment.
- `comparator_offset_calibration_loop.iterations` defaults to `7` updates; valid range: iterations >= 1; sets the number of falling-clock updates before valid asserts.
- `comparator_offset_calibration_loop.tr` defaults to `2e-11` s; valid range: tr >= 0; sets transition smoothing for generated stimulus, estimate, and valid outputs.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ZERO_INITIAL_ESTIMATE`: restore: The signed estimate initializes to zero, the search increment initializes to step_initial, and valid begins low. Required traces: `time`, `offset_est`, `valid`.
- `P_FALLING_EDGE_UPDATE`: restore: The calibration state updates only on falling clk crossings through the midpoint of vdd and vss. Required traces: `time`, `vdd`, `vss`, `clk`, `dcmpp`, `offset_est`.
- `P_DECISION_DIRECTION`: restore: At an update, a high dcmpp decreases the estimate by the current step and a low dcmpp increases it by the current step. Required traces: `time`, `clk`, `dcmpp`, `offset_est`.
- `P_SUCCESSIVE_STEP_HALVING`: restore: The magnitude of the search increment halves after every update, yielding a successive-approximation trajectory. Required traces: `time`, `clk`, `dcmpp`, `offset_est`.
- `P_SYMMETRIC_DIFFERENTIAL_STIMULUS`: restore: Vinp and vinn remain symmetric around mid-supply and vinp minus vinn equals offset_est. Required traces: `time`, `vdd`, `vss`, `vinp`, `vinn`, `offset_est`.
- `P_VALID_COMPLETION`: restore: Valid remains at vss until iterations updates complete, then rises to vdd and the reported estimate resolves the supplied comparator trip point represented by vos_ref within the search resolution. Required traces: `time`, `vdd`, `vss`, `clk`, `offset_est`, `valid`, `vos_ref`.

## Modeling Constraints

- Treat the companion comparator as a supplied harness component coupled only through the declared voltage-domain ports.
- Update search state on falling clock events and drive symmetric stimulus and status through smoothed voltage contributions.
- Do not use current contributions, ddt(), idt(), validation hooks, hard-coded waveform sample points, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `comparator_offset_calibration_loop.va`.
Every supplied `.va` file is editable; do not add or omit files.
