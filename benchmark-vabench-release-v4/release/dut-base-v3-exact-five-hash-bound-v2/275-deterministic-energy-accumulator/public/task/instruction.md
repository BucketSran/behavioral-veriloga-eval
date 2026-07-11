# Deterministic Energy Accumulator

## Task Contract
Implement the DUT form for canonical family `275` as Spectre-compatible voltage-domain behavioral Verilog-A. Produce exactly `deterministic_energy_accumulator.va` and satisfy the public observable contract below for `Deterministic Energy Accumulator`. The task level is `L2` and the category is `measurement_control`.

## Public Verilog-A Interface
```verilog
module deterministic_energy_accumulator(clk, rst, in0, in1, in2, in3, ctrl0, ctrl1, vdd, vss, en, out, flag, metric);
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
- `P_INITIALIZE_THE_ACCUMULATOR_STATE_AND_ALL`: Initialize the accumulator state and all observables to `0 V`. On a rising edge of `clk` or on reset assertion, clear the accumulator and all observables when `rst` is high or the row is not valid. Otherwise compute `aux = clip01(abs(x0 - x1) + 0.35 * c0)`, update `acc = clip01(0.62 * acc + 0.32 * aux)`, drive `out = vhi * acc`, assert `flag = vhi` when `acc > 0.58`, otherwise drive `flag = 0 V`, and drive `metric = vhi * aux`. Hold the last observable values between update events.

The evaluator saves and may inspect these public trace signals: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only internals, or simulator side channels.
- Do not emit checker code, score logic, private oracle assumptions, or testbench-specific timing shortcuts.
- No public support source files are required; the solver DUT bundle consists only of the requested target artifact(s).
- Keep candidate DUT code separate from evaluator/testbench files; the solver-owned boundary is the target artifact list only.

## Output Contract
Return only the Verilog-A source artifact(s) named in Section 1. The artifact(s) must compile without nonstandard include files, generated testbenches, undeclared helper modules outside the declared bundle, or changes to the public/evaluator decks.
