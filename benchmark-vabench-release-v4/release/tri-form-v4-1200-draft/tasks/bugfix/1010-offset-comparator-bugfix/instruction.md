# Offset Comparator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `cmp_offset_ref.va`:
  - Module `cmp_offset_ref` (entry)
    - position 0: `VDD` (input, electrical)
    - position 1: `VSS` (input, electrical)
    - position 2: `CLK` (input, electrical)
    - position 3: `VINP` (input, electrical)
    - position 4: `VINN` (input, electrical)
    - position 5: `OUT_P` (output, electrical)

## Public Parameter Contract

- `cmp_offset_ref.vos` defaults to `0.005` V; valid range: vos >= 0; sets positive input-referred decision offset.
- `cmp_offset_ref.tt` defaults to `2e-11` s; valid range: tt > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RISING_EDGE_SAMPLE`: restore: OUT_P updates only on CLK rising crossings through the local rail midpoint. Required traces: `time`, `VDD`, `VSS`, `CLK`, `VINP`, `VINN`, `OUT_P`.
- `P_OFFSET_DECISION`: restore: OUT_P latches high only when VINP relative to VINN is greater than the positive vos threshold. Required traces: `time`, `CLK`, `VINP`, `VINN`, `OUT_P`.
- `P_LATCH_HOLD`: restore: OUT_P holds its sampled decision between rising clock edges. Required traces: `time`, `CLK`, `VINP`, `VINN`, `OUT_P`.
- `P_RAIL_REFERENCE`: restore: OUT_P low and high levels track VSS and VDD respectively with finite smoothing. Required traces: `time`, `VDD`, `VSS`, `OUT_P`.

## Modeling Constraints

- Use deterministic voltage-domain behavior and voltage contributions only.
- Keep sampled state updates in event blocks and output contribution unconditional.
- Do not expose undeclared state or validation outputs.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `cmp_offset_ref.va`.
Every supplied `.va` file is editable; do not add or omit files.
