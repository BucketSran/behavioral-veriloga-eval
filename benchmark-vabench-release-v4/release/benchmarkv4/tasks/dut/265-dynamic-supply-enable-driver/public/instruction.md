# Dynamic Supply Enable Driver

## Task Contract
Implement the DUT form for canonical family `265` as Spectre-compatible voltage-domain behavioral Verilog-A. Produce exactly `dynamic_supply_enable_driver.va` and satisfy the public observable contract below for `Dynamic Supply Enable Driver`. The task level is `L1` and the category is `bias_reference_power_management`.

## Public Verilog-A Interface
```verilog
module dynamic_supply_enable_driver(in0, in1, in2, in3, ctrl0, ctrl1, vdd, vss, en, out, flag, metric);
```
All listed ports are electrical and must keep this order:
- `in0` (input, electrical, position 0)
- `in1` (input, electrical, position 1)
- `in2` (input, electrical, position 2)
- `in3` (input, electrical, position 3)
- `ctrl0` (input, electrical, position 4)
- `ctrl1` (input, electrical, position 5)
- `vdd` (input, electrical, position 6)
- `vss` (input, electrical, position 7)
- `en` (input, electrical, position 8)
- `out` (output, electrical, position 9)
- `flag` (output, electrical, position 10)
- `metric` (output, electrical, position 11)

## Public Parameter Contract
- `vth` (real, default `0.45`): overrides vth.
- `vhi` (real, default `0.9`): overrides vhi.
- `span_min` (real, default `0.62`): overrides span_min.
- `span_max` (real, default `1.28`): overrides span_max.
- `tr` (real, default `50p`): overrides tr.

## Required Behavior
- `P_MEASURE_ANALOG_INPUTS_RELATIVE_TO_THE`: Measure analog inputs relative to the local `vss` rail and normalize by the current local supply span. Let `span = V(vdd, vss)` and treat the row as valid only when `V(en) > vth` and `span_min <= span <= span_max`; otherwise drive `out`, `flag`, and `metric` to `0 V`. If `span` is below `0.05 V`, use `0.05 V` as the normalization span. Define `clip01(y)` as `y` limited to the range `[0, 1]`, `x0 = clip01((V(in0) - V(vss)) / span)`, and `c1 = clip01(V(ctrl1) / vhi)`.
- `P_COMPUTE_CORE_0_76_X0_0`: Compute `core = 0.76 * x0 + 0.18 * c1 + 0.12` and drive `out = vhi * clip01(core)` while valid. Assert `flag = vhi` when the local supply span is at least `0.78 V`, otherwise drive `flag = 0 V`. Drive `metric = vhi * clip01(abs((V(in0) - V(vss)) - 0.5 * span) / span)` as the bounded distance from the half-span input point.

The evaluator saves and may inspect these public trace signals: `time`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `vdd`, `vss`.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only internals, or simulator side channels.
- Do not emit checker code, score logic, private oracle assumptions, or testbench-specific timing shortcuts.
- No public support source files are required; the solver DUT bundle consists only of the requested target artifact(s).
- Keep candidate DUT code separate from evaluator/testbench files; the solver-owned boundary is the target artifact list only.

## Output Contract
Return only the Verilog-A source artifact(s) named in Section 1. The artifact(s) must compile without nonstandard include files, generated testbenches, undeclared helper modules outside the declared bundle, or changes to the public/evaluator decks.
