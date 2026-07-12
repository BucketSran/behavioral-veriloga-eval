# Comparator Decision Capture Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Comparator Decision Capture` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `comparator_decision_capture.va`:
  - Module `comparator_decision_capture` (entry)
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
- Instantiate `comparator_decision_capture` as `XDUT` with ordered public binding: clk=clk, rst=rst, in0=in0, in1=in1, in2=in2, in3=in3, ctrl0=ctrl0, ctrl1=ctrl1, vdd=vdd, vss=vss, en=en, out=out, flag=flag, metric=metric.

## Public Parameter Contract

- `comparator_decision_capture.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `comparator_decision_capture.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `comparator_decision_capture.span_min` defaults to `0.62`; valid range: finite; overrides span_min.
- `comparator_decision_capture.span_max` defaults to `1.28`; valid range: finite; overrides span_max.
- `comparator_decision_capture.tr` defaults to `50p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_MEASURE_ANALOG_INPUTS_RELATIVE_TO_THE`: exercise and make observable: Measure analog inputs relative to the local `vss` rail and normalize by the current local supply span. Let `span = V(vdd, vss)` and treat the row as valid only when `V(en) > vth` and `span_min <= span <= span_max`. If `span` is below `0.05 V`, use `0.05 V` as the normalization span. Define `clip01(y)` as `y` limited to the range `[0, 1]` and `x0..x3 = clip01((V(inN) - V(vss)) / span)`. Required traces: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.
- `P_INITIALIZE_ALL_OBSERVABLE_STATE_TO_0`: exercise and make observable: Initialize all observable state to `0 V`. On a rising crossing of `clk` or a rising crossing of `rst`, clear all observables when `rst` is high or the row is not valid. Otherwise sample the comparator decision: drive `out = vhi` and `flag = vhi` when `x0 > x1`, and drive both to `0 V` when `x0 <= x1`. Drive `metric = vhi * clip01(abs(x0 - x1))` as the sampled decision margin. Hold the last observable values between update events. Required traces: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.
- `P_BUILD_A_VOLTAGE_DOMAIN_ANALOG_MIXED`: exercise and make observable: Build a voltage-domain analog/mixed-signal helper or monitor. Clocked comparator-decision capture with reset clearing and margin metric. Required traces: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.
- `P_VTH_0_45_V_LOGIC_THRESHOLD`: exercise and make observable: `vth = 0.45 V`: logic threshold for voltage-coded controls. Required traces: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.
- `P_VHI_0_9_V_HIGH_LEVEL`: exercise and make observable: `vhi = 0.9 V`: high level for output observables. Required traces: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.
- `P_SPAN_MIN_0_62_V_SPAN`: exercise and make observable: `span_min = 0.62 V`, `span_max = 1.28 V`: legal local supply span measured as Required traces: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.

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
