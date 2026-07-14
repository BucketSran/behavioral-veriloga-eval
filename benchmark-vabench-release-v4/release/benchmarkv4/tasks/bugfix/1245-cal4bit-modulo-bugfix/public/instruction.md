# CAL4bit Modulo Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `cal4bit_modulo.va`:
  - Module `cal4bit_modulo` (entry)
    - position 0: `ain` (input, electrical)
    - position 1: `d0` (output, electrical)
    - position 2: `d1` (output, electrical)
    - position 3: `d2` (output, electrical)
    - position 4: `d3` (output, electrical)

## Public Parameter Contract

- `cal4bit_modulo.vh` defaults to `0.9`; valid range: finite; overrides vh.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_FLOOR_V_AIN_TO_AN_INTEGER`: restore: Floor `V(ain)` to an integer code, clamp the code to the valid 4-bit range `0..15`, and emit the clamped code on `d0..d3`. Active bits should be near `vh`; inactive bits should be near `0 V`. Required traces: `time`, `ain`, `d0`, `d1`, `d2`, `d3`.
- `P_PROVIDE_OVERRIDEABLE_PUBLIC_PARAMETER_VH_0`: restore: Provide overrideable public parameter `vh = 0.9 V` for the output logic-high level. The output low level is `0 V`. Required traces: `time`, `ain`, `d0`, `d1`, `d2`, `d3`.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: restore: Use deterministic voltage-domain Verilog-A and smooth voltage-coded output transitions. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels. Required traces: `time`, `ain`, `d0`, `d1`, `d2`, `d3`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `cal4bit_modulo.va`.
Every supplied `.va` file is editable; do not add or omit files.
