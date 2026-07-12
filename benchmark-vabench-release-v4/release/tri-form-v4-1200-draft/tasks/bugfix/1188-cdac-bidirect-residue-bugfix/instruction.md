# CDAC Bidirect Residue Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `cdac_bidirect_residue.va`:
  - Module `cdac_bidirect_residue` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clks` (input, electrical)
    - position 2: `dctrl1` (input, electrical)
    - position 3: `dctrl2` (input, electrical)
    - position 4: `dctrl3` (input, electrical)
    - position 5: `dctrl4` (input, electrical)
    - position 6: `dctrl5` (input, electrical)
    - position 7: `dctrl6` (input, electrical)
    - position 8: `dctrl7` (input, electrical)
    - position 9: `vres` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_SAMPLE_RESIDUE_ON_CLKS_FALL`: restore: At initialization and on each falling `clks` crossing, sample `vin` into the residue state. Required traces: `time`, `clks`, `dctrl1`, `dctrl2`, `dctrl3`, `dctrl4`, `dctrl5`, `dctrl6`, `dctrl7`, `vin`, `vres`.
- `P_MSB_RESIDUE_STEP_SIGN`: restore: A falling `dctrl7` event adds the half-scale MSB residue step with the declared sign. Required traces: `time`, `clks`, `dctrl1`, `dctrl2`, `dctrl3`, `dctrl4`, `dctrl5`, `dctrl6`, `dctrl7`, `vin`, `vres`.
- `P_LOWER_BIT_RESIDUE_WEIGHTS`: restore: Falling `dctrl6..dctrl1` events apply the declared binary-weighted residue steps. Required traces: `time`, `clks`, `dctrl1`, `dctrl2`, `dctrl3`, `dctrl4`, `dctrl5`, `dctrl6`, `dctrl7`, `vin`, `vres`.
- `P_RESIDUE_OUTPUT_GAIN`: restore: `vres` drives the sampled residue with the declared gain and voltage scale. Required traces: `time`, `clks`, `dctrl1`, `dctrl2`, `dctrl3`, `dctrl4`, `dctrl5`, `dctrl6`, `dctrl7`, `vin`, `vres`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `cdac_bidirect_residue.va`.
Every supplied `.va` file is editable; do not add or omit files.
