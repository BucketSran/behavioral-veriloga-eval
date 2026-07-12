# Flash Folded DAC4
## Task Contract
Implement `flash_folded_dac4.va`, a L1 voltage-domain data converter DUT for Flash Folded DAC4.
## Public Verilog-A Interface
Declare `module flash_folded_dac4(vd4, vd3, vd2, vd1, vout);` with scalar electrical ports. Port order is normative: `vd4` (input), `vd3` (input), `vd2` (input), `vd1` (input), `vout` (output).
## Public Parameter Contract
- `vth = 0.45`: overrides vth.
- `vref = 1.0`: overrides vref.

## Required Behavior
- `P_TREAT_EACH_INPUT_BIT_AS_LOGIC`: Treat each input bit as logic one when its voltage is above `vth`. The MSB selects the folded half of the transfer. When `vd4` is high, add the lower-bit weighted value above midscale. When `vd4` is low, subtract the lower-bit weighted value from midscale. The lower bits use binary weights `4`, `2`, and `1`, and the output is scaled by `vref/16`.
- `P_VTH_0_45_V_DECISION_THRESHOLD`: `vth = 0.45 V`: decision threshold for each voltage-coded input bit.
- `P_VREF_1_0_V_OUTPUT_REFERENCE`: `vref = 1.0 V`: output reference/full-scale voltage.
- `P_VTH_0_45_V_DECISION_THRESHOLD_2`: - `vth = 0.45 V`: decision threshold for each voltage-coded input bit. - `vref = 1.0 V`: output reference/full-scale voltage.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: Use deterministic voltage-domain Verilog-A and voltage contributions only. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only implementation details, or simulator side channels.
- Do not emit a testbench, checker logic, undeclared probe nodes, hard-coded validation stimuli, waveform sample windows, or simulator side channels.
- Use only the public module interface, public parameters, and observable behavior specified here.

## Output Contract
Return exactly one source artifact named `flash_folded_dac4.va`. The candidate bundle must not require additional modules, nonstandard include files, or testbench changes.
