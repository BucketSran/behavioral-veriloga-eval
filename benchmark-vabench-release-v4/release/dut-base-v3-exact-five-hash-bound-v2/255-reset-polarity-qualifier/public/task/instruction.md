# Reset Polarity Qualifier
## Task Contract
Implement `reset_polarity_qualifier.va`, a L1 voltage-domain reset power control DUT for Reset Polarity Qualifier.
## Public Verilog-A Interface
Declare `module reset_polarity_qualifier(in0, in1, in2, in3, ctrl0, ctrl1, vdd, vss, en, out, flag, metric);` with scalar electrical ports. Port order is normative: `in0` (input), `in1` (input), `in2` (input), `in3` (input), `ctrl0` (input), `ctrl1` (input), `vdd` (input), `vss` (input), `en` (input), `out` (output), `flag` (output), `metric` (output).
## Public Parameter Contract
- `vth = 0.45`: overrides vth.
- `vhi = 0.9`: overrides vhi.
- `span_min = 0.62`: overrides span_min.
- `span_max = 1.28`: overrides span_max.
- `tr = 50p`: overrides tr.

## Required Behavior
- `P_MEASURE_ANALOG_INPUTS_RELATIVE_TO_THE`: Measure analog inputs relative to the local `vss` rail and normalize by the current local supply span. Let `span = V(vdd, vss)` and treat the row as valid only when `V(en) > vth` and `span_min <= span <= span_max`; otherwise drive `out`, `flag`, and `metric` to `0 V`. If `span` is below `0.05 V`, use `0.05 V` as the normalization span. Define `clip01(y)` as `y` limited to the range `[0, 1]`, `x0 = clip01((V(in0) - V(vss)) / span)`, and `c0 = clip01(V(ctrl0) / vhi)`.
- `P_DRIVE_OUT_VHI_CLIP01_X0_ASSERT`: Drive `out = vhi * clip01(x0)`. Assert `flag = vhi` only when the normalized release level is inside the public window `0.24 <= x0 <= 0.72` and `c0 > 0.35`; otherwise drive `flag = 0 V`. Drive `metric = vhi * clip01(abs(x0 - 0.48) / 0.48)` as the bounded distance from the center of the release window.
- `P_BUILD_A_VOLTAGE_DOMAIN_ANALOG_MIXED`: Build a voltage-domain analog/mixed-signal helper or monitor. Electrical reset-release qualifier that uses a rail-normalized input window and a voltage-coded control qualifier to produce a release flag inside a valid supply window.
- `P_VTH_0_45_V_LOGIC_THRESHOLD`: `vth = 0.45 V`: logic threshold for voltage-coded controls.
- `P_VHI_0_9_V_HIGH_LEVEL`: `vhi = 0.9 V`: high level for output observables.
- `P_SPAN_MIN_0_62_V_SPAN`: `span_min = 0.62 V`, `span_max = 1.28 V`: legal local supply span measured as

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only implementation details, or simulator side channels.
- Do not emit a testbench, checker logic, undeclared probe nodes, hard-coded validation stimuli, waveform sample windows, or simulator side channels.
- Use only the public module interface, public parameters, and observable behavior specified here.

## Output Contract
Return exactly one source artifact named `reset_polarity_qualifier.va`. The candidate bundle must not require additional modules, nonstandard include files, or testbench changes.
