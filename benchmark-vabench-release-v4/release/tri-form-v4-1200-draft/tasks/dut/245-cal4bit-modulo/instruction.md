# CAL4bit Modulo
## Task Contract
Implement `cal4bit_modulo.va`, a L1 voltage-domain calibration control DUT for CAL4bit Modulo.
## Public Verilog-A Interface
Declare `module cal4bit_modulo(ain, d0, d1, d2, d3);` with scalar electrical ports. Port order is normative: `ain` (input), `d0` (output), `d1` (output), `d2` (output), `d3` (output).
## Public Parameter Contract
- `vh = 0.9`: overrides vh.

## Required Behavior
- `P_FLOOR_V_AIN_TO_AN_INTEGER`: Floor `V(ain)` to an integer code, clamp the code to the valid 4-bit range `0..15`, and emit the clamped code on `d0..d3`. Active bits should be near `vh`; inactive bits should be near `0 V`.
- `P_PROVIDE_OVERRIDEABLE_PUBLIC_PARAMETER_VH_0`: Provide overrideable public parameter `vh = 0.9 V` for the output logic-high level. The output low level is `0 V`.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: Use deterministic voltage-domain Verilog-A and smooth voltage-coded output transitions. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only implementation details, or simulator side channels.
- Do not emit a testbench, checker logic, undeclared probe nodes, hard-coded validation stimuli, waveform sample windows, or simulator side channels.
- Use only the public module interface, public parameters, and observable behavior specified here.

## Output Contract
Return exactly one source artifact named `cal4bit_modulo.va`. The candidate bundle must not require additional modules, nonstandard include files, or testbench changes.
