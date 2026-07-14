# Successive Approximation Calibration Search FSM Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Successive Approximation Calibration Search FSM` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `successive_approximation_calibration_search_fsm.va`:
  - Module `successive_approximation_calibration_search_fsm` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `successive_approximation_calibration_search_fsm` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, out=out, metric=metric.

## Public Parameter Contract

- `successive_approximation_calibration_search_fsm.tr` defaults to `1e-10` s; valid range: tr > 0; sets out and metric transition smoothing.
- `successive_approximation_calibration_search_fsm.vth` defaults to `0.45` V; valid range: vmin < vth < vmax; sets clk and rst logic threshold.
- `successive_approximation_calibration_search_fsm.target` defaults to `0.45` V; valid range: vmin <= target <= vmax; sets zero-error decision point and reset trial value.
- `successive_approximation_calibration_search_fsm.step_init` defaults to `0.18` V; valid range: step_init > 0; sets the first signed trial adjustment and reset step size.
- `successive_approximation_calibration_search_fsm.vmin` defaults to `0.05` V; valid range: vmin < vmax; sets the lower trial-trim clamp.
- `successive_approximation_calibration_search_fsm.vmax` defaults to `0.85` V; valid range: vmax > vmin; sets the upper trial-trim clamp.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_SEARCH_STATE`: exercise and make observable: Active reset restores out to target, the current step to step_init, the cycle count to zero, and metric low. Required traces: `time`, `clk`, `rst`, `out`, `metric`.
- `P_SIGNED_TRIAL_UPDATE`: exercise and make observable: On each active rising clk update before completion, vin above target increases out by the current step and vin below target decreases it. Required traces: `time`, `clk`, `rst`, `vin`, `out`.
- `P_SUCCESSIVE_STEP_HALVING`: exercise and make observable: The current step halves after every active decision update, yielding the public successive-approximation sequence from step_init. Required traces: `time`, `clk`, `vin`, `out`.
- `P_FOUR_STEP_DONE`: exercise and make observable: Metric asserts after four active search updates and subsequent rising clocks hold the completed trial state until reset. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_TRIM_CLAMP`: exercise and make observable: Out remains within vmin through vmax for every trial update. Required traces: `time`, `out`.

The required trace names are: `time`, `clk`, `rst`, `vin`, `out`, `metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
