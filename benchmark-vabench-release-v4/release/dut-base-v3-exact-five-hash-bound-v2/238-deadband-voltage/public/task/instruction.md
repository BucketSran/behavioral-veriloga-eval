# Deadband Voltage

## Task Contract
Implement `deadband_voltage.va`, a single-ended voltage-domain deadband shaper. This row is a baseband signal-conditioning variant and should be counted carefully against other single-ended deadband primitives.

## Public Verilog-A Interface
Declare module `deadband_voltage(sigin, sigout)` with scalar electrical ports. `sigin` is the signed input voltage and `sigout` is the shaped output voltage.

## Public Parameter Contract
Provide overrideable public parameters:

- `sigin_dead_low = -0.25 V`: inclusive lower deadband edge.
- `sigin_dead_high = 0.25 V`: inclusive upper deadband edge.

## Required Behavior
Inside the deadband window, including both edges, drive `sigout` to `0 V`. Below the lower edge, drive the signed excess below `sigin_dead_low`. Above the upper edge, drive the signed excess above `sigin_dead_high`. The output should preserve sign outside the window and be continuous at both thresholds.

## Modeling Constraints
Use deterministic voltage-domain Verilog-A and voltage contributions only. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels.

## Output Contract
Return exactly one source artifact named `deadband_voltage.va`.
