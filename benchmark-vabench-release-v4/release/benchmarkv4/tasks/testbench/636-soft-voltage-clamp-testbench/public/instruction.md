# Soft Voltage Clamp Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Soft Voltage Clamp` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `soft_voltage_clamp_behavior.va`:
  - Module `soft_voltage_clamp_behavior` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)
    - position 2: `vgnd` (input, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `soft_voltage_clamp_behavior` as `XDUT` with ordered public binding: vin=vin, vout=vout, vgnd=vgnd.

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_REFERENCED_INPUT_OUTPUT`: exercise and make observable: Use `V(vin, vgnd)` as input and drive `V(vout, vgnd)` as output. Required traces: `time`, `vin`, `vout`.
- `P_LINEAR_MIDDLE_REGION`: exercise and make observable: Pass the input linearly for `0.0 V <= V(vin, vgnd) <= 0.4 V`. Required traces: `time`, `vin`, `vout`.
- `P_SOFT_LOWER_LIMIT`: exercise and make observable: Below 0.0 V, apply an exponential soft lower limit that approaches -0.2 V with a 0.2 V softness span. Required traces: `time`, `vin`, `vout`.
- `P_SOFT_UPPER_LIMIT`: exercise and make observable: Above 0.4 V, apply an exponential soft upper limit that approaches 0.6 V with a 0.2 V softness span. Required traces: `time`, `vin`, `vout`.

The required trace names are: `time`, `vin`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
