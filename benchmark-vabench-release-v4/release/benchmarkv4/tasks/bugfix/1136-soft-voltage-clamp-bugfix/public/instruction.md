# Soft Voltage Clamp Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `soft_voltage_clamp_behavior.va`:
  - Module `soft_voltage_clamp_behavior` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)
    - position 2: `vgnd` (input, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_REFERENCED_INPUT_OUTPUT`: restore: Use `V(vin, vgnd)` as input and drive `V(vout, vgnd)` as output. Required traces: `time`, `vin`, `vout`.
- `P_LINEAR_MIDDLE_REGION`: restore: Pass the input linearly for `0.0 V <= V(vin, vgnd) <= 0.4 V`. Required traces: `time`, `vin`, `vout`.
- `P_SOFT_LOWER_LIMIT`: restore: Below 0.0 V, apply an exponential soft lower limit that approaches -0.2 V with a 0.2 V softness span. Required traces: `time`, `vin`, `vout`.
- `P_SOFT_UPPER_LIMIT`: restore: Above 0.4 V, apply an exponential soft upper limit that approaches 0.6 V with a 0.2 V softness span. Required traces: `time`, `vin`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `soft_voltage_clamp_behavior.va`.
Every supplied `.va` file is editable; do not add or omit files.
