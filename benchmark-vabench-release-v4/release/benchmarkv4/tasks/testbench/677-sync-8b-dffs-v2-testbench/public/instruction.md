# Sync 8b DFFs V2 Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Sync 8b DFFs V2` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `sync_8b_dffs_v2.va`:
  - Module `sync_8b_dffs_v2` (entry)
    - position 0: `ck1` (input, electrical)
    - position 1: `ck2` (input, electrical)
    - position 2: `ck3` (input, electrical)
    - position 3: `ck4` (input, electrical)
    - position 4: `ck5` (input, electrical)
    - position 5: `ck6` (input, electrical)
    - position 6: `ck7` (input, electrical)
    - position 7: `ck8` (input, electrical)
    - position 8: `ck9` (input, electrical)
    - position 9: `dl0` (input, electrical)
    - position 10: `dl1` (input, electrical)
    - position 11: `dl2` (input, electrical)
    - position 12: `dl3` (input, electrical)
    - position 13: `dl4` (input, electrical)
    - position 14: `dl5` (input, electrical)
    - position 15: `dl6` (input, electrical)
    - position 16: `dl7` (input, electrical)
    - position 17: `dl8` (input, electrical)
    - position 18: `do0` (output, electrical)
    - position 19: `do1` (output, electrical)
    - position 20: `do2` (output, electrical)
    - position 21: `do3` (output, electrical)
    - position 22: `do4` (output, electrical)
    - position 23: `do5` (output, electrical)
    - position 24: `do6` (output, electrical)
    - position 25: `do7` (output, electrical)
    - position 26: `do8` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `sync_8b_dffs_v2` as `XDUT` with ordered public binding: ck1=ck1, ck2=ck2, ck3=ck3, ck4=ck4, ck5=ck5, ck6=ck6, ck7=ck7, ck8=ck8, ck9=ck9, dl0=dl0, dl1=dl1, dl2=dl2, dl3=dl3, dl4=dl4, dl5=dl5, dl6=dl6, dl7=dl7, dl8=dl8, do0=do0, do1=do1, do2=do2, do3=do3, do4=do4, do5=do5, do6=do6, do7=do7, do8=do8.

## Public Parameter Contract

- `sync_8b_dffs_v2.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `sync_8b_dffs_v2.tt` defaults to `20p`; valid range: finite; overrides tt.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_PHASED_CAPTURE_ORDER`: exercise and make observable: Each phase clock captures its corresponding `dl` input and shifts previously captured upper-phase data down the chain in the specified order. Required traces: `time`, `ck1`, `ck2`, `ck3`, `ck4`, `ck5`, `ck6`, `ck7`, `ck8`, `ck9`, `dl0`, `dl1`, `dl2`, `dl3`, `dl4`, `dl5`, `dl6`, `dl7`, `dl8`, `do0`, `do1`, `do2`, `do3`, `do4`, `do5`, `do6`, `do7`, `do8`.
- `P_INTERMEDIATE_OUTPUT_CAPTURE`: exercise and make observable: Intermediate outputs, including `do4`, reflect their synchronized pipeline state rather than a stuck or skipped stage. Required traces: `time`, `ck4`, `ck5`, `dl4`, `do4`.
- `P_FINAL_OUTPUT_CAPTURE`: exercise and make observable: The most delayed output `do8` reflects the final synchronized stage with correct polarity. Required traces: `time`, `ck8`, `ck9`, `dl8`, `do8`.
- `P_FULL_LEVEL_OUTPUTS`: exercise and make observable: All `do` outputs drive full voltage-coded levels for their captured state. Required traces: `time`, `do0`, `do1`, `do2`, `do3`, `do4`, `do5`, `do6`, `do7`, `do8`.

The required trace names are: `time`, `ck1`, `ck2`, `ck3`, `ck4`, `ck5`, `ck6`, `ck7`, `ck8`, `ck9`, `dl0`, `dl1`, `dl2`, `dl3`, `dl4`, `dl5`, `dl6`, `dl7`, `dl8`, `do0`, `do1`, `do2`, `do3`, `do4`, `do5`, `do6`, `do7`, `do8`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
