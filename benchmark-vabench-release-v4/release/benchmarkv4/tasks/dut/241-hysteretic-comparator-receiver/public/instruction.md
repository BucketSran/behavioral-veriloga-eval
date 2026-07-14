# Hysteretic Comparator Receiver
## Task Contract
Implement `hysteretic_comparator_receiver.va`, a L1 voltage-domain comparator DUT for Hysteretic Comparator Receiver.
## Public Verilog-A Interface
Declare `module hysteretic_comparator_receiver(inp, inm, out);` with scalar electrical ports. Port order is normative: `inp` (input), `inm` (input), `out` (output).
## Public Parameter Contract
- `vout_high = 0.9`: overrides vout_high.
- `vout_low = 0.0`: overrides vout_low.
- `offset = 0.0`: overrides offset.
- `vhys = 40e-3 from [0:inf)`: overrides vhys.
- `td = 400p from [0:inf)`: overrides td.
- `tr = 80p from [0:inf)`: overrides tr.

## Required Behavior
- `P_DEFINE_UPPER_TH_OFFSET_VHYS_2`: Define `upper_th = offset + vhys/2` and `lower_th = offset - vhys/2`. On initialization, set the output state high if `V(inp,inm)` is at or above the upper threshold; otherwise set it low. After initialization, switch high only on a rising crossing of `upper_th`, switch low only on a falling crossing of `lower_th`, and hold the previous state inside the hysteresis band. Drive `out` to the selected rail with delay `td` and transition time `tr`.
- `P_VOUT_HIGH_0_9_V_HIGH`: `vout_high = 0.9 V`: high output rail.
- `P_VOUT_LOW_0_0_V_LOW`: `vout_low = 0.0 V`: low output rail.
- `P_OFFSET_0_0_V_INPUT_REFERRED`: `offset = 0.0 V`: input-referred switching offset.
- `P_VHYS_40_MV_FROM_0_INF`: `vhys = 40 mV from [0:inf)`: total hysteresis width.
- `P_TD_400_PS_FROM_0_INF`: `td = 400 ps from [0:inf)`: propagation delay from a qualifying threshold crossing to the output state change.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only implementation details, or simulator side channels.
- Do not emit a testbench, checker logic, undeclared probe nodes, hard-coded validation stimuli, waveform sample windows, or simulator side channels.
- Use only the public module interface, public parameters, and observable behavior specified here.

## Output Contract
Return exactly one source artifact named `hysteretic_comparator_receiver.va`. The candidate bundle must not require additional modules, nonstandard include files, or testbench changes.
