# Successive Approximation Calibration Search FSM Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `successive_approximation_calibration_search_fsm.va`:
  - Module `successive_approximation_calibration_search_fsm` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

## Public Parameter Contract

- `successive_approximation_calibration_search_fsm.tr` defaults to `1e-10` s; valid range: tr > 0; sets out and metric transition smoothing.
- `successive_approximation_calibration_search_fsm.vth` defaults to `0.45` V; valid range: vmin < vth < vmax; sets clk and rst logic threshold.
- `successive_approximation_calibration_search_fsm.target` defaults to `0.45` V; valid range: vmin <= target <= vmax; sets zero-error decision point and reset trial value.
- `successive_approximation_calibration_search_fsm.step_init` defaults to `0.18` V; valid range: step_init > 0; sets the first signed trial adjustment and reset step size.
- `successive_approximation_calibration_search_fsm.vmin` defaults to `0.05` V; valid range: vmin < vmax; sets the lower trial-trim clamp.
- `successive_approximation_calibration_search_fsm.vmax` defaults to `0.85` V; valid range: vmax > vmin; sets the upper trial-trim clamp.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_SEARCH_STATE`: restore: Active reset restores out to target, the current step to step_init, the cycle count to zero, and metric low. Required traces: `time`, `clk`, `rst`, `out`, `metric`.
- `P_SIGNED_TRIAL_UPDATE`: restore: On each active rising clk update before completion, vin above target increases out by the current step and vin below target decreases it. Required traces: `time`, `clk`, `rst`, `vin`, `out`.
- `P_SUCCESSIVE_STEP_HALVING`: restore: The current step halves after every active decision update, yielding the public successive-approximation sequence from step_init. Required traces: `time`, `clk`, `vin`, `out`.
- `P_FOUR_STEP_DONE`: restore: Metric asserts after four active search updates and subsequent rising clocks hold the completed trial state until reset. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_TRIM_CLAMP`: restore: Out remains within vmin through vmax for every trial update. Required traces: `time`, `out`.

## Modeling Constraints

- Use deterministic clocked voltage-domain calibration state.
- Do not use current contributions, transistor-level devices, AC/noise behavior, or KCL/KVL solving assumptions.
- Do not add validation logic, hidden state observables, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `successive_approximation_calibration_search_fsm.va`.
Every supplied `.va` file is editable; do not add or omit files.
