# Voltage Match Window Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Voltage Match Window` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `voltage_match_window.va`:
  - Module `voltage_match_window` (entry)
    - position 0: `vin1` (input, electrical)
    - position 1: `vin2` (input, electrical)
    - position 2: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `voltage_match_window` as `XDUT` with ordered public binding: vin1=vin1, vin2=vin2, vout=vout.

## Public Parameter Contract

- `voltage_match_window.match_tol` defaults to `0.05 from [0:inf)`; valid range: finite; overrides match_tol.
- `voltage_match_window.vh` defaults to `0.9`; valid range: finite; overrides vh.
- `voltage_match_window.tr` defaults to `20p from [0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_COMPARE_THE_ANALOG_VOLTAGE_DIFFERENCE_DIRECTLY`: exercise and make observable: Compare the analog voltage difference directly. Drive `vout` near `vh` when `abs(V(vin1) - V(vin2)) <= match_tol`; otherwise drive it near `0 V`. The decision should be deterministic and memoryless, with a smoothed voltage transition on the output. Required traces: `time`, `vin1`, `vin2`, `vout`.
- `P_MATCH_TOL_0_05_V_FROM`: exercise and make observable: `match_tol = 0.05 V from [0:inf)`: maximum allowed absolute input difference for a match. Required traces: `time`, `vin1`, `vin2`, `vout`.
- `P_VH_0_9_V_MATCH_OUTPUT`: exercise and make observable: `vh = 0.9 V`: match output level. Required traces: `time`, `vin1`, `vin2`, `vout`.
- `P_TR_20_PS_FROM_0_INF`: exercise and make observable: `tr = 20 ps from [0:inf)`: output transition smoothing time. Required traces: `time`, `vin1`, `vin2`, `vout`.
- `P_MATCH_TOL_0_05_V_FROM_2`: exercise and make observable: - `match_tol = 0.05 V from [0:inf)`: maximum allowed absolute input difference for a match. - `vh = 0.9 V`: match output level. - `tr = 20 ps from [0:inf)`: output transition smoothing time. Required traces: `time`, `vin1`, `vin2`, `vout`.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: exercise and make observable: Use deterministic voltage-domain Verilog-A and voltage contributions only. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels. Required traces: `time`, `vin1`, `vin2`, `vout`.

The required trace names are: `time`, `vin1`, `vin2`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
