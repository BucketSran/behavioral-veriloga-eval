# Enable Qualified Bias Hold

## Task Contract
Implement the DUT form for canonical family `264` as Spectre-compatible voltage-domain behavioral Verilog-A. Produce exactly `enable_qualified_bias_hold.va` and satisfy the public observable contract below for `Enable Qualified Bias Hold`. The task level is `L2` and the category is `bias_reference_power_management`.

## Public Verilog-A Interface
```verilog
module enable_qualified_bias_hold(clk, rst, in0, in1, in2, in3, ctrl0, ctrl1, vdd, vss, en, out, flag, metric);
```
All listed ports are electrical and must keep this order:
- `clk` (input, electrical, position 0)
- `rst` (input, electrical, position 1)
- `in0` (input, electrical, position 2)
- `in1` (input, electrical, position 3)
- `in2` (input, electrical, position 4)
- `in3` (input, electrical, position 5)
- `ctrl0` (input, electrical, position 6)
- `ctrl1` (input, electrical, position 7)
- `vdd` (input, electrical, position 8)
- `vss` (input, electrical, position 9)
- `en` (input, electrical, position 10)
- `out` (output, electrical, position 11)
- `flag` (output, electrical, position 12)
- `metric` (output, electrical, position 13)

## Public Parameter Contract
- `vth` (real, default `0.45`): overrides vth.
- `vhi` (real, default `0.9`): overrides vhi.
- `span_min` (real, default `0.62`): overrides span_min.
- `span_max` (real, default `1.28`): overrides span_max.
- `tr` (real, default `50p`): overrides tr.

## Required Behavior
- `P_MEASURE_ANALOG_INPUTS_RELATIVE_TO_THE`: Measure analog inputs relative to the local `vss` rail and normalize by the current local supply span. Let `span = V(vdd, vss)` and treat the row as valid only when `V(en) > vth` and `span_min <= span <= span_max`. If `span` is below `0.05 V`, use `0.05 V` as the normalization span. Define `clip01(y)` as `y` limited to the range `[0, 1]`, `x0..x3 = clip01((V(inN) - V(vss)) / span)`, and `c0 = clip01(V(ctrl0) / vhi)`.
- `P_INITIALIZE_THE_HELD_BIAS_OUTPUT_FLAG`: Initialize the held bias output, `flag`, and `metric` to `0 V`. On a rising edge of `clk`, clear all observables when `rst` is high or the row is not valid. Otherwise, when `c0 > 0.45`, update the held output to `out = vhi * clip01(0.70 * x0 + 0.30 * x1)` and assert `flag = vhi`. When `c0 <= 0.45`, hold the previous output value and drive `flag = 0 V`. After the update or hold decision, drive `metric = vhi * clip01(abs((out / vhi) - x2))`. Hold the last observable values between rising clock edges, except that a reset assertion clears them.

The evaluator saves and may inspect these public trace signals: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only internals, or simulator side channels.
- Do not emit checker code, score logic, private oracle assumptions, or testbench-specific timing shortcuts.
- No public support source files are required; the solver DUT bundle consists only of the requested target artifact(s).
- Keep candidate DUT code separate from evaluator/testbench files; the solver-owned boundary is the target artifact list only.

## Output Contract
Return only the Verilog-A source artifact(s) named in Section 1. The artifact(s) must compile without nonstandard include files, generated testbenches, undeclared helper modules outside the declared bundle, or changes to the public/evaluator decks.
