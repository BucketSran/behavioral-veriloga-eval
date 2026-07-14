# Windowed Event Rate Monitor

## Task Contract
Implement the DUT form for canonical family `271` as Spectre-compatible voltage-domain behavioral Verilog-A. Produce exactly `windowed_event_rate_monitor.va` and satisfy the public observable contract below for `Windowed Event Rate Monitor`. The task level is `L1` and the category is `measurement_instrumentation_flows`.

## Public Verilog-A Interface
```verilog
module windowed_event_rate_monitor(clk, rst, event_in, gate, rate, average);
```
All listed ports are electrical and must keep this order:
- `clk` (input, electrical, position 0)
- `rst` (input, electrical, position 1)
- `event_in` (input, electrical, position 2)
- `gate` (input, electrical, position 3)
- `rate` (output, electrical, position 4)
- `average` (output, electrical, position 5)

## Public Parameter Contract
- `vth` (real, default `0.45`): overrides vth.
- `vhi` (real, default `0.9`): overrides vhi.
- `window_count` (integer, default `5`): overrides window_count.
- `tr` (real, default `60p`): overrides tr.

## Required Behavior
- `P_INITIALIZE_EVENT_COUNT_SAMPLE_COUNT_RATE`: Initialize `event_count`, `sample_count`, `rate`, and `average` to zero. On each rising clock crossing, clear the measurement window and both observables when `rst` is high or `gate <= vth`. Otherwise increment `sample_count`, increment `event_count` when `event_in > vth`, and drive `rate = vhi * clip01(event_count / window_count)`.
- `P_FOR_THE_SAME_GATED_SAMPLE_WINDOW`: For the same gated sample window, drive `average = vhi * clip01(event_count / sample_count)`. Hold the last observable values between rising clock crossings.

The evaluator saves and may inspect these public trace signals: `time`, `average`, `clk`, `event_in`, `gate`, `rate`, `rst`.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only internals, or simulator side channels.
- Do not emit checker code, score logic, private oracle assumptions, or testbench-specific timing shortcuts.
- No public support source files are required; the solver DUT bundle consists only of the requested target artifact(s).
- Keep candidate DUT code separate from evaluator/testbench files; the solver-owned boundary is the target artifact list only.

## Output Contract
Return only the Verilog-A source artifact(s) named in Section 1. The artifact(s) must compile without nonstandard include files, generated testbenches, undeclared helper modules outside the declared bundle, or changes to the public/evaluator decks.
