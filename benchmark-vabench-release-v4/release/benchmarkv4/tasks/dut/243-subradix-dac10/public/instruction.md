# Subradix DAC10
## Task Contract
Implement `subradix_dac10.va`, a L1 voltage-domain data converter DUT for Subradix DAC10.
## Public Verilog-A Interface
Declare `module subradix_dac10(vd9, vd8, vd7, vd6, vd5, vd4, vd3, vd2, vd1, vd0, vout);` with scalar electrical ports. Port order is normative: `vd9` (input), `vd8` (input), `vd7` (input), `vd6` (input), `vd5` (input), `vd4` (input), `vd3` (input), `vd2` (input), `vd1` (input), `vd0` (input), `vout` (output).
## Public Parameter Contract
- `vth = 0.45`: overrides vth.
- `vref = 1.0`: overrides vref.

## Required Behavior
- `P_TREAT_EACH_INPUT_AS_LOGIC_ONE`: Treat each input as logic one when its voltage is greater than `vth`. Decode `vd9..vd0` as a sub-radix word whose adjacent bit weights follow radix `1.8`, with `vd0` weight one and `vd9` weight `1.8^9`. Scale the active-weight sum by the all-ones sub-radix weight sum so that all ones maps to `vref`.
- `P_VTH_0_45_V_DECISION_THRESHOLD`: `vth = 0.45 V`: decision threshold for each input bit.
- `P_VREF_1_0_V_OUTPUT_FULL`: `vref = 1.0 V`: output full-scale/reference voltage.
- `P_VTH_0_45_V_DECISION_THRESHOLD_2`: - `vth = 0.45 V`: decision threshold for each input bit. - `vref = 1.0 V`: output full-scale/reference voltage.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: Use deterministic voltage-domain Verilog-A and voltage contributions only. It is acceptable to express sub-radix weights with portable real arithmetic such as `pow(1.8, k)`. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only implementation details, or simulator side channels.
- Do not emit a testbench, checker logic, undeclared probe nodes, hard-coded validation stimuli, waveform sample windows, or simulator side channels.
- Use only the public module interface, public parameters, and observable behavior specified here.

## Output Contract
Return exactly one source artifact named `subradix_dac10.va`. The candidate bundle must not require additional modules, nonstandard include files, or testbench changes.
