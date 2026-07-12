# Ideal Differential Opamp Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `ideal_differential_opamp.va`:
  - Module `ideal_differential_opamp` (entry)
    - position 0: `vinp` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `voutp` (output, electrical)
    - position 3: `voutn` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_FIXED_COMMON_MODE`: restore: Maintain both outputs symmetric around a fixed 0.5 V common mode. Required traces: `time`, `voutp`, `voutn`.
- `P_DIFFERENTIAL_GAIN_FOUR`: restore: Make the differential output `V(voutp) - V(voutn)` equal to four times `V(vinp, vinn)`. Required traces: `time`, `vinp`, `vinn`, `voutp`, `voutn`.
- `P_OUTPUT_POLARITY`: restore: For positive `V(vinp, vinn)`, drive `voutp` above common mode and `voutn` below common mode. Required traces: `time`, `vinp`, `vinn`, `voutp`, `voutn`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `ideal_differential_opamp.va`.
Every supplied `.va` file is editable; do not add or omit files.
