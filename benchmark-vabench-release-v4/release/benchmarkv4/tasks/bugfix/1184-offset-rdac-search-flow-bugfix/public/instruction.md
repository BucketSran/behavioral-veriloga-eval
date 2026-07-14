# Offset RDAC Search Flow Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `offset_rdac_search_flow.va`:
  - Module `offset_rdac_search_flow` (entry)
    - position 0: `ck` (input, electrical)
    - position 1: `d` (input, electrical)
    - position 2: `vinp` (output, electrical)
    - position 3: `vinn` (output, electrical)
    - position 4: `vrefp` (output, electrical)
    - position 5: `vrefn` (output, electrical)
    - position 6: `dc0` (output, electrical)
    - position 7: `dc1` (output, electrical)
    - position 8: `dc2` (output, electrical)
    - position 9: `dc3` (output, electrical)
    - position 10: `dc4` (output, electrical)
    - position 11: `dc5` (output, electrical)
    - position 12: `dc6` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_TWO_PHASE_CLOCKED_FLOW`: restore: Rising `ck` crossings execute the deterministic RDAC-refinement phase before the offset-search phase, using `d < 0.5 V` as the low comparator direction. Required traces: `time`, `ck`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `vinn`, `vinp`, `vrefn`, `vrefp`.
- `P_REFERENCE_AND_CODE_INITIALIZATION`: restore: Initialize `vref`, `vin`, and the 7-bit RDAC trial code to the declared reference-grid and MSB-first state. Required traces: `time`, `ck`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `vinn`, `vinp`, `vrefn`, `vrefp`.
- `P_RDAC_REFINEMENT_SEQUENCE`: restore: The six RDAC refinement clocks resolve the current bit and assert the next lower trial bit in the declared order. Required traces: `time`, `ck`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `vinn`, `vinp`, `vrefn`, `vrefp`.
- `P_OFFSET_SEARCH_BISECTION`: restore: The eight offset-search clocks compare consecutive directions, halve the search step on direction changes, and update `vin/vref` with the declared polarity. Required traces: `time`, `ck`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `vinn`, `vinp`, `vrefn`, `vrefp`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `offset_rdac_search_flow.va`.
Every supplied `.va` file is editable; do not add or omit files.
