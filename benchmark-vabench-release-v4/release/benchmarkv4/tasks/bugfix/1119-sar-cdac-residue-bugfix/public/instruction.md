# SAR CDAC Residue Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `sar_cdac_residue.va`:
  - Module `sar_cdac_residue` (entry)
    - position 0: `VIN` (input, electrical)
    - position 1: `CLK` (input, electrical)
    - position 2: `S6` (input, electrical)
    - position 3: `S5` (input, electrical)
    - position 4: `S4` (input, electrical)
    - position 5: `S3` (input, electrical)
    - position 6: `S2` (input, electrical)
    - position 7: `S1` (input, electrical)
    - position 8: `VRES` (output, electrical)

## Public Parameter Contract

- `sar_cdac_residue.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the rising CLK sampling threshold at one half of vdd.
- `sar_cdac_residue.vrefp` defaults to `0.9` V; valid range: vrefp > vrefn; sets the upper endpoint of the reference span used by all residue steps.
- `sar_cdac_residue.vrefn` defaults to `0.0` V; valid range: vrefn < vrefp; sets the lower endpoint of the reference span used by all residue steps.
- `sar_cdac_residue.tr` defaults to `1e-12` s; valid range: tr > 0; sets the transition time of the VRES voltage output.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INPUT_SAMPLE`: restore: At initial_step and each rising CLK crossing through vdd/2, the residue state samples VIN. Required traces: `time`, `vin`, `clk`, `vres`.
- `P_S6_HALF_ADD`: restore: Each falling S6 crossing through vdd/2 adds one half of the public reference span to the current residue. Required traces: `time`, `s6`, `vres`.
- `P_BINARY_SUBTRACTIONS`: restore: Rising crossings of S5, S4, S3, S2, and S1 through vdd/2 subtract one fourth, one eighth, one sixteenth, one thirty-second, and one sixty-fourth of the public reference span respectively. Required traces: `time`, `s5`, `s4`, `s3`, `s2`, `s1`, `vres`.
- `P_EDGE_POLARITY`: restore: S6 updates only on falling vdd/2 threshold crossings, while S5 through S1 update only on rising vdd/2 threshold crossings. Required traces: `time`, `s6`, `s5`, `s4`, `s3`, `s2`, `s1`, `vres`.
- `P_ACCUMULATED_STATE`: restore: Between declared sampling and switch events, VRES represents and holds the accumulated residue state. Required traces: `time`, `vin`, `clk`, `s6`, `s5`, `s4`, `s3`, `s2`, `s1`, `vres`.
- `P_OUTPUT_TRANSITION`: restore: VRES changes from the residue state using the declared tr transition time. Required traces: `time`, `vres`.

## Modeling Constraints

- Use deterministic event-driven residue state updates with the declared edge directions.
- Use the full vrefp minus vrefn span for every weighted update.
- Do not omit S1, substitute different edge polarities, use current contributions, or add validation-only hooks.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `sar_cdac_residue.va`.
Every supplied `.va` file is editable; do not add or omit files.
