# Offset RDAC Search Flow Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Offset RDAC Search Flow` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `offset_rdac_search_flow` as `XDUT` with ordered public binding: ck=ck, d=d, vinp=vinp, vinn=vinn, vrefp=vrefp, vrefn=vrefn, dc0=dc0, dc1=dc1, dc2=dc2, dc3=dc3, dc4=dc4, dc5=dc5, dc6=dc6.

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_TWO_PHASE_CLOCKED_FLOW`: exercise and make observable: Rising `ck` crossings execute the deterministic RDAC-refinement phase before the offset-search phase, using `d < 0.5 V` as the low comparator direction. Required traces: `time`, `ck`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `vinn`, `vinp`, `vrefn`, `vrefp`.
- `P_REFERENCE_AND_CODE_INITIALIZATION`: exercise and make observable: Initialize `vref`, `vin`, and the 7-bit RDAC trial code to the declared reference-grid and MSB-first state. Required traces: `time`, `ck`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `vinn`, `vinp`, `vrefn`, `vrefp`.
- `P_RDAC_REFINEMENT_SEQUENCE`: exercise and make observable: The six RDAC refinement clocks resolve the current bit and assert the next lower trial bit in the declared order. Required traces: `time`, `ck`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `vinn`, `vinp`, `vrefn`, `vrefp`.
- `P_OFFSET_SEARCH_BISECTION`: exercise and make observable: The eight offset-search clocks compare consecutive directions, halve the search step on direction changes, and update `vin/vref` with the declared polarity. Required traces: `time`, `ck`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `vinn`, `vinp`, `vrefn`, `vrefp`.

The required trace names are: `time`, `ck`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `vinn`, `vinp`, `vrefn`, `vrefp`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
