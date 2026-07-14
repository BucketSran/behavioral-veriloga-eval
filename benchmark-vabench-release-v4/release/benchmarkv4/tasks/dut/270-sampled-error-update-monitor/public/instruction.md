# Sampled Error Update Monitor

## Task Contract
Implement the DUT form for canonical family `270` as Spectre-compatible voltage-domain behavioral Verilog-A. Produce exactly `sampled_error_update_monitor.va` and satisfy the public observable contract below for `Sampled Error Update Monitor`. The task level is `L2` and the category is `calibration_control`.

## Public Verilog-A Interface
```verilog
module sampled_error_update_monitor(clk, rst, sample, target, coef, out, err_metric, progress);
```
All listed ports are electrical and must keep this order:
- `clk` (input, electrical, position 0)
- `rst` (input, electrical, position 1)
- `sample` (input, electrical, position 2)
- `target` (input, electrical, position 3)
- `coef` (input, electrical, position 4)
- `out` (output, electrical, position 5)
- `err_metric` (output, electrical, position 6)
- `progress` (output, electrical, position 7)

## Public Parameter Contract
- `vth` (real, default `0.45`): overrides vth.
- `vhi` (real, default `0.9`): overrides vhi.
- `err_fullscale` (real, default `0.50`): overrides err_fullscale.
- `err_window` (real, default `0.040`): overrides err_window.
- `ready_count` (integer, default `3`): overrides ready_count.
- `tr` (real, default `60p`): overrides tr.

## Required Behavior
- `P_RESET_CLEARS_STATE_AND_OBSERVABLES`: While rst is high at a rising clock edge, clear the stable count, out, err_metric, and progress.
- `P_CORRECTED_OUTPUT_USES_SAMPLE_TARGET_AND_COEF`: At each enabled rising clock edge, compute the clipped coefficient and drive the clamped corrected sample from sample, target, and coef.
- `P_ERROR_METRIC_REPORTS_ABSOLUTE_ERROR`: Drive err_metric from the bounded absolute target-minus-sample error.
- `P_PROGRESS_COUNTS_CONSECUTIVE_IN_WINDOW_SAMPLES`: Increment progress only for consecutive in-window sampled errors, clear it on an out-of-window sample, and saturate at ready_count.

The evaluator saves and may inspect these public trace signals: `time`, `clk`, `coef`, `err_metric`, `out`, `progress`, `rst`, `sample`, `target`.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only internals, or simulator side channels.
- Do not emit checker code, score logic, private oracle assumptions, or testbench-specific timing shortcuts.
- No public support source files are required; the solver DUT bundle consists only of the requested target artifact(s).
- Keep candidate DUT code separate from evaluator/testbench files; the solver-owned boundary is the target artifact list only.

## Output Contract
Return only the Verilog-A source artifact(s) named in Section 1. The artifact(s) must compile without nonstandard include files, generated testbenches, undeclared helper modules outside the declared bundle, or changes to the public/evaluator decks.
