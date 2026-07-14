# Voltage Match Window
## Task Contract
Implement `voltage_match_window.va`, a L1 voltage-domain calibration control DUT for Voltage Match Window.
## Public Verilog-A Interface
Declare `module voltage_match_window(vin1, vin2, vout);` with scalar electrical ports. Port order is normative: `vin1` (input), `vin2` (input), `vout` (output).
## Public Parameter Contract
- `match_tol = 0.05 from [0:inf)`: overrides match_tol.
- `vh = 0.9`: overrides vh.
- `tr = 20p from [0:inf)`: overrides tr.

## Required Behavior
- `P_COMPARE_THE_ANALOG_VOLTAGE_DIFFERENCE_DIRECTLY`: Compare the analog voltage difference directly. Drive `vout` near `vh` when `abs(V(vin1) - V(vin2)) <= match_tol`; otherwise drive it near `0 V`. The decision should be deterministic and memoryless, with a smoothed voltage transition on the output.
- `P_MATCH_TOL_0_05_V_FROM`: `match_tol = 0.05 V from [0:inf)`: maximum allowed absolute input difference for a match.
- `P_VH_0_9_V_MATCH_OUTPUT`: `vh = 0.9 V`: match output level.
- `P_TR_20_PS_FROM_0_INF`: `tr = 20 ps from [0:inf)`: output transition smoothing time.
- `P_MATCH_TOL_0_05_V_FROM_2`: - `match_tol = 0.05 V from [0:inf)`: maximum allowed absolute input difference for a match. - `vh = 0.9 V`: match output level. - `tr = 20 ps from [0:inf)`: output transition smoothing time.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: Use deterministic voltage-domain Verilog-A and voltage contributions only. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only implementation details, or simulator side channels.
- Do not emit a testbench, checker logic, undeclared probe nodes, hard-coded validation stimuli, waveform sample windows, or simulator side channels.
- Use only the public module interface, public parameters, and observable behavior specified here.

## Output Contract
Return exactly one source artifact named `voltage_match_window.va`. The candidate bundle must not require additional modules, nonstandard include files, or testbench changes.
