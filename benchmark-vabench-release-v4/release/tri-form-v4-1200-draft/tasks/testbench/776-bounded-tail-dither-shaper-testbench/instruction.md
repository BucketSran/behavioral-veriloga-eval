# Bounded Tail Dither Shaper Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Bounded Tail Dither Shaper` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `bounded_tail_dither_shaper.va`:
  - Module `bounded_tail_dither_shaper` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `in0` (input, electrical)
    - position 3: `in1` (input, electrical)
    - position 4: `in2` (input, electrical)
    - position 5: `in3` (input, electrical)
    - position 6: `ctrl0` (input, electrical)
    - position 7: `ctrl1` (input, electrical)
    - position 8: `vdd` (input, electrical)
    - position 9: `vss` (input, electrical)
    - position 10: `en` (input, electrical)
    - position 11: `out` (output, electrical)
    - position 12: `flag` (output, electrical)
    - position 13: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `bounded_tail_dither_shaper` as `XDUT` with ordered public binding: clk=clk, rst=rst, in0=in0, in1=in1, in2=in2, in3=in3, ctrl0=ctrl0, ctrl1=ctrl1, vdd=vdd, vss=vss, en=en, out=out, flag=flag, metric=metric.

## Public Parameter Contract

- `bounded_tail_dither_shaper.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `bounded_tail_dither_shaper.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `bounded_tail_dither_shaper.span_min` defaults to `0.62`; valid range: finite; overrides span_min.
- `bounded_tail_dither_shaper.span_max` defaults to `1.28`; valid range: finite; overrides span_max.
- `bounded_tail_dither_shaper.tr` defaults to `50p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_MEASURE_ANALOG_INPUTS_RELATIVE_TO_THE`: exercise and make observable: Measure analog inputs relative to the local `vss` rail and normalize by the current local supply span `span = V(vdd, vss)`. Clear all observables when `en` is low or when `span` is outside `[span_min, span_max]`. The DUT updates its observable state on rising `clk` crossings and clears state while `rst` is high. Required traces: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.
- `P_FOR_EACH_VALID_UPDATE_COMPUTE`: exercise and make observable: For each valid update, compute: Required traces: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.
- `P_TEXT_X0_CLIP01_V_IN0_V`: exercise and make observable: ```text x0 = clip01((V(in0) - V(vss)) / span) x1 = clip01((V(in1) - V(vss)) / span) c0 = clip01(V(ctrl0) / vhi) aux = clip01(abs(x0 - x1) + 0.35*c0) acc = clip01(0.62*previous_acc + 0.32*aux) out = vhi*acc flag = vhi when acc > 0.58, otherwise 0 metric = vhi*aux ``` Required traces: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.
- `P_RESET_DISABLED_AND_OUT_OF_RANGE`: exercise and make observable: Reset, disabled, and out-of-range supply conditions set `previous_acc`, `out`, `flag`, and `metric` to 0. Preserve `in2`, `in3`, and `ctrl1` as public interface inputs; they are not part of the bounded-tail update formula for this task. Required traces: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.

The required trace names are: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
