# SPI Shift Mux Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `spi_shift_mux.va`:
  - Module `spi_shift_mux` (entry)
    - position 0: `scki` (input, electrical)
    - position 1: `sdi` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `out0` (output, electrical)
    - position 4: `out1` (output, electrical)
    - position 5: `out2` (output, electrical)
    - position 6: `out3` (output, electrical)
    - position 7: `out4` (output, electrical)
    - position 8: `out5` (output, electrical)
    - position 9: `out6` (output, electrical)
    - position 10: `out7` (output, electrical)
    - position 11: `sdo` (output, electrical)
    - position 12: `scko` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_LOADS_DEFAULT_WORD`: restore: Initialization and active-high `rst` load the 8-bit word `10110010` with `out7` as the leftmost bit and `out0` as the rightmost bit. Required traces: `time`, `out0`, `out1`, `out2`, `out3`, `out4`, `out5`, `out6`, `out7`, `rst`, `scki`, `scko`, `sdi`, `sdo`.
- `P_SHIFT_ON_SCKI_TRANSITIONS`: restore: While reset is inactive, every `scki` transition shifts the register exactly once. Required traces: `time`, `out0`, `out1`, `out2`, `out3`, `out4`, `out5`, `out6`, `out7`, `rst`, `scki`, `scko`, `sdi`, `sdo`.
- `P_SHIFT_DIRECTION_AND_SDI_INSERTION`: restore: The shift moves bits toward higher output indexes and inserts `sdi` into the declared end of the register. Required traces: `time`, `out0`, `out1`, `out2`, `out3`, `out4`, `out5`, `out6`, `out7`, `rst`, `scki`, `scko`, `sdi`, `sdo`.
- `P_SDO_EXPOSES_SHIFTED_OUT_BIT`: restore: `sdo` exposes the shifted-out `out7` bit rather than another register bit. Required traces: `time`, `out0`, `out1`, `out2`, `out3`, `out4`, `out5`, `out6`, `out7`, `rst`, `scki`, `scko`, `sdi`, `sdo`.
- `P_OUTPUT_RAIL_LEVELS`: restore: The parallel outputs and `sdo` are voltage-coded at valid low/high levels. Required traces: `time`, `out0`, `out1`, `out2`, `out3`, `out4`, `out5`, `out6`, `out7`, `rst`, `scki`, `scko`, `sdi`, `sdo`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `spi_shift_mux.va`.
Every supplied `.va` file is editable; do not add or omit files.
