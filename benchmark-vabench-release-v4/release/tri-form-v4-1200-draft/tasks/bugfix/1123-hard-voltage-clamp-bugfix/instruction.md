# Hard Voltage Clamp Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `hard_voltage_clamp_behavior.va`:
  - Module `hard_voltage_clamp_behavior` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)
    - position 2: `vgnd` (input, electrical)

## Public Parameter Contract

- `hard_voltage_clamp_behavior.vclamp_upper` defaults to `1`; valid range: finite; overrides vclamp_upper.
- `hard_voltage_clamp_behavior.vclamp_lower` defaults to `0`; valid range: finite; overrides vclamp_lower.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_GROUND_REFERENCED_INPUT`: restore: Measure the clamp input as `V(vin, vgnd)` and drive `V(vout, vgnd)` relative to the same reference. Required traces: `time`, `vin`, `vout`.
- `P_PASSBAND_TRANSFER`: restore: When the referenced input lies inside `[vclamp_lower, vclamp_upper]`, pass that referenced voltage to the output. Required traces: `time`, `vin`, `vout`.
- `P_LOWER_CLAMP`: restore: When the referenced input is below `vclamp_lower`, drive the lower clamp value. Required traces: `time`, `vin`, `vout`.
- `P_UPPER_CLAMP`: restore: When the referenced input is above `vclamp_upper`, drive the upper clamp value. Required traces: `time`, `vin`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `hard_voltage_clamp_behavior.va`.
Every supplied `.va` file is editable; do not add or omit files.
