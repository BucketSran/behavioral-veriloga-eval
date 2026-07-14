# Voltage Match Window Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `voltage_match_window.va`:
  - Module `voltage_match_window` (entry)
    - position 0: `vin1` (input, electrical)
    - position 1: `vin2` (input, electrical)
    - position 2: `vout` (output, electrical)

## Public Parameter Contract

- `voltage_match_window.match_tol` defaults to `0.05 from [0:inf)`; valid range: finite; overrides match_tol.
- `voltage_match_window.vh` defaults to `0.9`; valid range: finite; overrides vh.
- `voltage_match_window.tr` defaults to `20p from [0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_COMPARE_THE_ANALOG_VOLTAGE_DIFFERENCE_DIRECTLY`: restore: Compare the analog voltage difference directly. Drive `vout` near `vh` when `abs(V(vin1) - V(vin2)) <= match_tol`; otherwise drive it near `0 V`. The decision should be deterministic and memoryless, with a smoothed voltage transition on the output. Required traces: `time`, `vin1`, `vin2`, `vout`.
- `P_MATCH_TOL_0_05_V_FROM`: restore: `match_tol = 0.05 V from [0:inf)`: maximum allowed absolute input difference for a match. Required traces: `time`, `vin1`, `vin2`, `vout`.
- `P_VH_0_9_V_MATCH_OUTPUT`: restore: `vh = 0.9 V`: match output level. Required traces: `time`, `vin1`, `vin2`, `vout`.
- `P_TR_20_PS_FROM_0_INF`: restore: `tr = 20 ps from [0:inf)`: output transition smoothing time. Required traces: `time`, `vin1`, `vin2`, `vout`.
- `P_MATCH_TOL_0_05_V_FROM_2`: restore: - `match_tol = 0.05 V from [0:inf)`: maximum allowed absolute input difference for a match. - `vh = 0.9 V`: match output level. - `tr = 20 ps from [0:inf)`: output transition smoothing time. Required traces: `time`, `vin1`, `vin2`, `vout`.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: restore: Use deterministic voltage-domain Verilog-A and voltage contributions only. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels. Required traces: `time`, `vin1`, `vin2`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `voltage_match_window.va`.
Every supplied `.va` file is editable; do not add or omit files.
