# Comparator Decision Capture
## Task Contract
Implement `comparator_decision_capture.va`, a L2 voltage-domain comparator decision DUT for Comparator Decision Capture.
## Public Verilog-A Interface
Declare `module comparator_decision_capture(clk, rst, in0, in1, in2, in3, ctrl0, ctrl1, vdd, vss, en, out, flag, metric);` with scalar electrical ports. Port order is normative: `clk` (input), `rst` (input), `in0` (input), `in1` (input), `in2` (input), `in3` (input), `ctrl0` (input), `ctrl1` (input), `vdd` (input), `vss` (input), `en` (input), `out` (output), `flag` (output), `metric` (output).
## Public Parameter Contract
- `vth = 0.45`: overrides vth.
- `vhi = 0.9`: overrides vhi.
- `span_min = 0.62`: overrides span_min.
- `span_max = 1.28`: overrides span_max.
- `tr = 50p`: overrides tr.

## Required Behavior
- `P_MEASURE_ANALOG_INPUTS_RELATIVE_TO_THE`: Measure analog inputs relative to the local `vss` rail and normalize by the current local supply span. Let `span = V(vdd, vss)` and treat the row as valid only when `V(en) > vth` and `span_min <= span <= span_max`. If `span` is below `0.05 V`, use `0.05 V` as the normalization span. Define `clip01(y)` as `y` limited to the range `[0, 1]` and `x0..x3 = clip01((V(inN) - V(vss)) / span)`.
- `P_INITIALIZE_ALL_OBSERVABLE_STATE_TO_0`: Initialize all observable state to `0 V`. On a rising crossing of `clk` or a rising crossing of `rst`, clear all observables when `rst` is high or the row is not valid. Otherwise sample the comparator decision: drive `out = vhi` and `flag = vhi` when `x0 > x1`, and drive both to `0 V` when `x0 <= x1`. Drive `metric = vhi * clip01(abs(x0 - x1))` as the sampled decision margin. Hold the last observable values between update events.
- `P_BUILD_A_VOLTAGE_DOMAIN_ANALOG_MIXED`: Build a voltage-domain analog/mixed-signal helper or monitor. Clocked comparator-decision capture with reset clearing and margin metric.
- `P_VTH_0_45_V_LOGIC_THRESHOLD`: `vth = 0.45 V`: logic threshold for voltage-coded controls.
- `P_VHI_0_9_V_HIGH_LEVEL`: `vhi = 0.9 V`: high level for output observables.
- `P_SPAN_MIN_0_62_V_SPAN`: `span_min = 0.62 V`, `span_max = 1.28 V`: legal local supply span measured as

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only implementation details, or simulator side channels.
- Do not emit a testbench, checker logic, undeclared probe nodes, hard-coded validation stimuli, waveform sample windows, or simulator side channels.
- Use only the public module interface, public parameters, and observable behavior specified here.

## Output Contract
Return exactly one source artifact named `comparator_decision_capture.va`. The candidate bundle must not require additional modules, nonstandard include files, or testbench changes.
