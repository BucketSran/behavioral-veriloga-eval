# Threshold Comparator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `comparator.va`:
  - Module `comparator` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `VINP` (input, electrical)
    - position 3: `VINN` (input, electrical)
    - position 4: `OUT_P` (output, electrical)

## Public Parameter Contract

- `comparator.tedge` defaults to `1e-10` s; valid range: tedge > 0; sets OUT_P rail-transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_DECISION`: restore: At initialization, OUT_P reflects the sign of VINP minus VINN. Required traces: `time`, `VINP`, `VINN`, `OUT_P`.
- `P_RISING_DIFFERENTIAL`: restore: When VINP crosses above VINN, OUT_P transitions to the VDD rail. Required traces: `time`, `VDD`, `VINP`, `VINN`, `OUT_P`.
- `P_FALLING_DIFFERENTIAL`: restore: When VINP crosses below VINN, OUT_P transitions to the VSS rail. Required traces: `time`, `VSS`, `VINP`, `VINN`, `OUT_P`.
- `P_BIDIRECTIONAL_RESPONSE`: restore: Repeated differential crossings in either direction update the retained decision without requiring a clock or reset. Required traces: `time`, `VINP`, `VINN`, `OUT_P`.
- `P_RAIL_SMOOTHING`: restore: OUT_P is rail-referenced and changes with finite transition smoothing set by tedge. Required traces: `time`, `VDD`, `VSS`, `OUT_P`.

## Modeling Constraints

- Use deterministic event-driven voltage-domain comparator state.
- Drive the output contribution outside threshold-crossing event blocks.
- Do not use current contributions, ddt(), idt(), validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `comparator.va`.
Every supplied `.va` file is editable; do not add or omit files.
