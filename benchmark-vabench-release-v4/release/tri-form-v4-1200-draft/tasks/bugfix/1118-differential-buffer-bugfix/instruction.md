# Differential Buffer Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `differential_buffer.va`:
  - Module `differential_buffer` (entry)
    - position 0: `VINP` (input, electrical)
    - position 1: `VINN` (input, electrical)
    - position 2: `VOUTP` (output, electrical)
    - position 3: `VOUTN` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_POSITIVE_UNITY`: restore: VOUTP continuously follows VINP with unity voltage gain and unchanged polarity. Required traces: `time`, `vinp`, `voutp`.
- `P_NEGATIVE_UNITY`: restore: VOUTN continuously follows VINN with unity voltage gain and unchanged polarity. Required traces: `time`, `vinn`, `voutn`.
- `P_CHANNEL_INDEPENDENCE`: restore: Each output depends on its corresponding input and is not cross-coupled to the opposite input. Required traces: `time`, `vinp`, `vinn`, `voutp`, `voutn`.
- `P_DIFFERENTIAL_PRESERVATION`: restore: The differential output VOUTP minus VOUTN equals the differential input VINP minus VINN. Required traces: `time`, `vinp`, `vinn`, `voutp`, `voutn`.
- `P_COMMON_MODE_PRESERVATION`: restore: The output pair preserves the input pair common-mode voltage without conversion or rail logic. Required traces: `time`, `vinp`, `vinn`, `voutp`, `voutn`.

## Modeling Constraints

- Use deterministic direct voltage contributions.
- Preserve channel polarity, unity gain, and continuous pass-through behavior.
- Do not add delay, gain control, rail clipping, retained state, current contributions, or validation-only hooks.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `differential_buffer.va`.
Every supplied `.va` file is editable; do not add or omit files.
