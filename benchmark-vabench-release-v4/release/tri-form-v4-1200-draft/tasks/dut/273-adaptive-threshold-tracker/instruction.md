# Adaptive Threshold Tracker

## Task Contract
Implement the DUT form for canonical family `273` as Spectre-compatible voltage-domain behavioral Verilog-A. Produce exactly `adaptive_threshold_tracker.va` and satisfy the public observable contract below for `Adaptive Threshold Tracker`. The task level is `L1` and the category is `comparator_decision`.

## Public Verilog-A Interface
```verilog
module adaptive_threshold_tracker(clk, rst, vin, adapt, trip, threshold_mon, margin_metric);
```
All listed ports are electrical and must keep this order:
- `clk` (input, electrical, position 0)
- `rst` (input, electrical, position 1)
- `vin` (input, electrical, position 2)
- `adapt` (input, electrical, position 3)
- `trip` (output, electrical, position 4)
- `threshold_mon` (output, electrical, position 5)
- `margin_metric` (output, electrical, position 6)

## Public Parameter Contract
- `vth` (real, default `0.45`): overrides vth.
- `vhi` (real, default `0.9`): overrides vhi.
- `threshold_init` (real, default `0.45`): overrides threshold_init.
- `threshold_min` (real, default `0.25`): overrides threshold_min.
- `threshold_max` (real, default `0.70`): overrides threshold_max.
- `adapt_alpha` (real, default `0.75`): overrides adapt_alpha.
- `margin_fullscale` (real, default `0.45`): overrides margin_fullscale.
- `tr` (real, default `60p`): overrides tr.

## Required Behavior
- `P_INITIALIZE_THE_STORED_THRESHOLD_TO_THRESHOLD`: Initialize the stored threshold to `threshold_init`, `threshold_mon` to `threshold_init`, and the other observables to zero. On each rising clock crossing, reset the stored threshold and outputs to those initial values while `rst` is high. Otherwise compare `vin` against the previously stored threshold: drive `trip = vhi` when `V(vin) > old_threshold`, otherwise drive `trip = 0 V`. Drive `margin_metric = vhi * clip01(abs(V(vin) - old_threshold) / margin_fullscale)`.
- `P_WHEN_ADAPT_VTH_UPDATE_THE_STORED`: When `adapt > vth`, update the stored threshold after the comparison using `threshold = clamp(adapt_alpha * old_threshold + (1.0 - adapt_alpha) * V(vin), threshold_min, threshold_max)`. Drive `threshold_mon` with the resulting next-sample threshold. Hold the last observable values between rising clock crossings.

The evaluator saves and may inspect these public trace signals: `time`, `adapt`, `clk`, `margin_metric`, `rst`, `threshold_mon`, `trip`, `vin`.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only internals, or simulator side channels.
- Do not emit checker code, score logic, private oracle assumptions, or testbench-specific timing shortcuts.
- No public support source files are required; the solver DUT bundle consists only of the requested target artifact(s).
- Keep candidate DUT code separate from evaluator/testbench files; the solver-owned boundary is the target artifact list only.

## Output Contract
Return only the Verilog-A source artifact(s) named in Section 1. The artifact(s) must compile without nonstandard include files, generated testbenches, undeclared helper modules outside the declared bundle, or changes to the public/evaluator decks.
