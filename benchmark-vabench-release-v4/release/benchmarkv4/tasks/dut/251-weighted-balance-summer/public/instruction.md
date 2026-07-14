# Weighted Balance Summer
## Task Contract
Implement `weighted_balance_summer.va`, a L1 voltage-domain signal conditioning and measurement DUT for Weighted Balance Summer.
## Public Verilog-A Interface
Declare `module weighted_balance_summer(in0, in1, in2, in3, ctrl0, ctrl1, vdd, vss, en, out, flag, metric);` with scalar electrical ports. Port order is normative: `in0` (input), `in1` (input), `in2` (input), `in3` (input), `ctrl0` (input), `ctrl1` (input), `vdd` (input), `vss` (input), `en` (input), `out` (output), `flag` (output), `metric` (output).
## Public Parameter Contract
- `vth = 0.45`: overrides vth.
- `vhi = 0.9`: overrides vhi.
- `span_min = 0.62`: overrides span_min.
- `span_max = 1.28`: overrides span_max.
- `tr = 50p`: overrides tr.

## Required Behavior
- `P_MEASURE_ANALOG_INPUTS_RELATIVE_TO_THE`: Measure analog inputs relative to the local `vss` rail and normalize by the current local supply span. Let `span = V(vdd, vss)` and treat the row as valid only when `V(en) > vth` and `span_min <= span <= span_max`; otherwise drive `out`, `flag`, and `metric` to `0 V`. If `span` is below `0.05 V`, use `0.05 V` as the normalization span. Define `clip01(y)` as `y` limited to the range `[0, 1]` and `x0..x3 = clip01((V(inN) - V(vss)) / span)`.
- `P_COMPUTE_THE_WEIGHTED_BALANCE_SUM_AS`: Compute the weighted balance sum as `core = 0.36 * x0 + 0.28 * x1 + 0.18 * x2 + 0.10 * x3 + 0.04`. When valid, drive `out = vhi * clip01(core)`, assert `flag = vhi` when `core > 0.48` and otherwise drive `flag = 0 V`, and drive `metric = vhi * clip01(abs(x0 - x1) / 0.55)`.
- `P_BUILD_A_VOLTAGE_DOMAIN_ANALOG_MIXED`: Build a voltage-domain analog/mixed-signal helper or monitor. Weighted analog summer with balance qualification and a voltage-coded imbalance metric.
- `P_VTH_0_45_V_LOGIC_THRESHOLD`: `vth = 0.45 V`: logic threshold for voltage-coded controls.
- `P_VHI_0_9_V_HIGH_LEVEL`: `vhi = 0.9 V`: high level for output observables.
- `P_SPAN_MIN_0_62_V_SPAN`: `span_min = 0.62 V`, `span_max = 1.28 V`: legal local supply span measured as

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only implementation details, or simulator side channels.
- Do not emit a testbench, checker logic, undeclared probe nodes, hard-coded validation stimuli, waveform sample windows, or simulator side channels.
- Use only the public module interface, public parameters, and observable behavior specified here.

## Output Contract
Return exactly one source artifact named `weighted_balance_summer.va`. The candidate bundle must not require additional modules, nonstandard include files, or testbench changes.
