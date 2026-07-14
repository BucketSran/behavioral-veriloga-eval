# CAL4bit Modulo Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `CAL4bit Modulo` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `cal4bit_modulo.va`:
  - Module `cal4bit_modulo` (entry)
    - position 0: `ain` (input, electrical)
    - position 1: `d0` (output, electrical)
    - position 2: `d1` (output, electrical)
    - position 3: `d2` (output, electrical)
    - position 4: `d3` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `cal4bit_modulo` as `XDUT` with ordered public binding: ain=ain, d0=d0, d1=d1, d2=d2, d3=d3.

## Public Parameter Contract

- `cal4bit_modulo.vh` defaults to `0.9`; valid range: finite; overrides vh.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_FLOOR_V_AIN_TO_AN_INTEGER`: exercise and make observable: Floor `V(ain)` to an integer code, clamp the code to the valid 4-bit range `0..15`, and emit the clamped code on `d0..d3`. Active bits should be near `vh`; inactive bits should be near `0 V`. Required traces: `time`, `ain`, `d0`, `d1`, `d2`, `d3`.
- `P_PROVIDE_OVERRIDEABLE_PUBLIC_PARAMETER_VH_0`: exercise and make observable: Provide overrideable public parameter `vh = 0.9 V` for the output logic-high level. The output low level is `0 V`. Required traces: `time`, `ain`, `d0`, `d1`, `d2`, `d3`.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: exercise and make observable: Use deterministic voltage-domain Verilog-A and smooth voltage-coded output transitions. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels. Required traces: `time`, `ain`, `d0`, `d1`, `d2`, `d3`.

The required trace names are: `time`, `ain`, `d0`, `d1`, `d2`, `d3`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
