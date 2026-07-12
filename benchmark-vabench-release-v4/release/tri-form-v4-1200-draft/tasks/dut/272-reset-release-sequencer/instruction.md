# Reset Release Sequencer

## Task Contract
Implement the DUT form for canonical family `272` as Spectre-compatible voltage-domain behavioral Verilog-A. Produce exactly `reset_release_sequencer.va` and satisfy the public observable contract below for `Reset Release Sequencer`. The task level is `L1` and the category is `bias_reference_power_management`.

## Public Verilog-A Interface
```verilog
module reset_release_sequencer(clk, rst, supply_ok, bias_ok, stage1, stage2, ready, progress);
```
All listed ports are electrical and must keep this order:
- `clk` (input, electrical, position 0)
- `rst` (input, electrical, position 1)
- `supply_ok` (input, electrical, position 2)
- `bias_ok` (input, electrical, position 3)
- `stage1` (output, electrical, position 4)
- `stage2` (output, electrical, position 5)
- `ready` (output, electrical, position 6)
- `progress` (output, electrical, position 7)

## Public Parameter Contract
- `vth` (real, default `0.45`): overrides vth.
- `vhi` (real, default `0.9`): overrides vhi.
- `final_stage` (integer, default `3`): overrides final_stage.
- `tr` (real, default `60p`): overrides tr.

## Required Behavior
- `P_INITIALIZE_THE_INTERNAL_STAGE_COUNT_AND`: Initialize the internal stage count and all observables to zero. On each rising clock crossing, clear the stage count when `rst` is high, `supply_ok <= vth`, or `bias_ok <= vth`. Otherwise increment the stage count by one until it reaches `final_stage`.
- `P_AFTER_UPDATING_THE_STAGE_COUNT_DRIVE`: After updating the stage count, drive `stage1 = vhi` when `stage_count >= 1`, `stage2 = vhi` when `stage_count >= 2`, and `ready = vhi` when `stage_count >= final_stage`; otherwise drive each of those observables to `0 V`. Drive `progress = vhi * clip01(stage_count / final_stage)`. Hold the last observable values between rising clock crossings.

The evaluator saves and may inspect these public trace signals: `time`, `bias_ok`, `clk`, `progress`, `ready`, `rst`, `stage1`, `stage2`, `supply_ok`.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only internals, or simulator side channels.
- Do not emit checker code, score logic, private oracle assumptions, or testbench-specific timing shortcuts.
- No public support source files are required; the solver DUT bundle consists only of the requested target artifact(s).
- Keep candidate DUT code separate from evaluator/testbench files; the solver-owned boundary is the target artifact list only.

## Output Contract
Return only the Verilog-A source artifact(s) named in Section 1. The artifact(s) must compile without nonstandard include files, generated testbenches, undeclared helper modules outside the declared bundle, or changes to the public/evaluator decks.
