# Mux4 Priority
## Task Contract
Implement `mux4_priority.va`, a L1 voltage-domain digital logic DUT for Mux4 Priority.
## Public Verilog-A Interface
Declare `module mux4_priority(sel0, sel1, in0, in1, in2, in3, out);` with scalar electrical ports. Port order is normative: `sel0` (input), `sel1` (input), `in0` (input), `in1` (input), `in2` (input), `in3` (input), `out` (output).
## Public Parameter Contract
- `vth = 0.45`: overrides vth.

## Required Behavior
- `P_DECODE_THE_SELECT_CODE_AS_SEL0`: Decode the select code as `sel0 + 2*sel1`. For code `0`, forward `in0` to `out`; for code `1`, forward `in1`; for code `2`, forward `in2`; for code `3`, forward `in3`. The selected analog voltage should pass through without quantization or rail coding.
- `P_PROVIDE_OVERRIDEABLE_PUBLIC_PARAMETER_VTH_0`: Provide overrideable public parameter `vth = 0.45 V` as the decision threshold for `sel0` and `sel1`.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: Use deterministic voltage-domain Verilog-A and voltage contributions only. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only implementation details, or simulator side channels.
- Do not emit a testbench, checker logic, undeclared probe nodes, hard-coded validation stimuli, waveform sample windows, or simulator side channels.
- Use only the public module interface, public parameters, and observable behavior specified here.

## Output Contract
Return exactly one source artifact named `mux4_priority.va`. The candidate bundle must not require additional modules, nonstandard include files, or testbench changes.
