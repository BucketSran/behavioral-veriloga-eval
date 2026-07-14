# Bounded Tail Dither Shaper

## Task Contract
Implement the DUT form for canonical family `276` as Spectre-compatible voltage-domain behavioral Verilog-A. Produce exactly `bounded_tail_dither_shaper.va` and satisfy the public observable contract below for `Bounded Tail Dither Shaper`. The task level is `L2` and the category is `signal_conditioning_and_measurement`.

## Public Verilog-A Interface
```verilog
module bounded_tail_dither_shaper(clk, rst, in0, in1, in2, in3, ctrl0, ctrl1, vdd, vss, en, out, flag, metric);
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
- `P_MEASURE_ANALOG_INPUTS_RELATIVE_TO_THE`: Measure analog inputs relative to the local `vss` rail and normalize by the current local supply span `span = V(vdd, vss)`. Clear all observables when `en` is low or when `span` is outside `[span_min, span_max]`. The DUT updates its observable state on rising `clk` crossings and clears state while `rst` is high.
- `P_FOR_EACH_VALID_UPDATE_COMPUTE`: For each valid update, compute:
- `P_TEXT_X0_CLIP01_V_IN0_V`: ```text x0 = clip01((V(in0) - V(vss)) / span) x1 = clip01((V(in1) - V(vss)) / span) c0 = clip01(V(ctrl0) / vhi) aux = clip01(abs(x0 - x1) + 0.35*c0) acc = clip01(0.62*previous_acc + 0.32*aux) out = vhi*acc flag = vhi when acc > 0.58, otherwise 0 metric = vhi*aux ```
- `P_RESET_DISABLED_AND_OUT_OF_RANGE`: Reset, disabled, and out-of-range supply conditions set `previous_acc`, `out`, `flag`, and `metric` to 0. Preserve `in2`, `in3`, and `ctrl1` as public interface inputs; they are not part of the bounded-tail update formula for this task.

The evaluator saves and may inspect these public trace signals: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only internals, or simulator side channels.
- Do not emit checker code, score logic, private oracle assumptions, or testbench-specific timing shortcuts.
- No public support source files are required; the solver DUT bundle consists only of the requested target artifact(s).
- Keep candidate DUT code separate from evaluator/testbench files; the solver-owned boundary is the target artifact list only.

## Output Contract
Return only the Verilog-A source artifact(s) named in Section 1. The artifact(s) must compile without nonstandard include files, generated testbenches, undeclared helper modules outside the declared bundle, or changes to the public/evaluator decks.
