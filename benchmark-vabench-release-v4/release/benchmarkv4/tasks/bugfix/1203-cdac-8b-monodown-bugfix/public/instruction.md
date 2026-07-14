# CDAC 8b Monodown Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `cdac_8b_monodown.va`:
  - Module `cdac_8b_monodown` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clks` (input, electrical)
    - position 2: `dctrl0` (input, electrical)
    - position 3: `dctrl1` (input, electrical)
    - position 4: `dctrl2` (input, electrical)
    - position 5: `dctrl3` (input, electrical)
    - position 6: `dctrl4` (input, electrical)
    - position 7: `dctrl5` (input, electrical)
    - position 8: `dctrl6` (input, electrical)
    - position 9: `dctrl7` (input, electrical)
    - position 10: `vres` (output, electrical)

## Public Parameter Contract

- `cdac_8b_monodown.vdd` defaults to `1.0`; valid range: finite; overrides vdd.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_AT_INITIALIZATION_AND_ON_EACH_FALLING`: restore: At initialization and on each falling `clks` crossing, sample `vin` into the held residue. On rising control crossings, subtract the corresponding binary-weighted fraction from the held residue: `dctrl7` subtracts 1/2, `dctrl6` 1/4, continuing down to `dctrl0` at 1/256. Hold the current residue value between events. Required traces: `time`, `clks`, `dctrl0`, `dctrl1`, `dctrl2`, `dctrl3`, `dctrl4`, `dctrl5`, `dctrl6`, `dctrl7`, `vin`, `vres`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `cdac_8b_monodown.va`.
Every supplied `.va` file is editable; do not add or omit files.
