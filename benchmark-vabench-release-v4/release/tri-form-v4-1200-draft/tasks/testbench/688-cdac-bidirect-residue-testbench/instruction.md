# CDAC Bidirect Residue Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `CDAC Bidirect Residue` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `cdac_bidirect_residue` as `XDUT` with ordered public binding: vin=vin, clks=clks, dctrl1=dctrl1, dctrl2=dctrl2, dctrl3=dctrl3, dctrl4=dctrl4, dctrl5=dctrl5, dctrl6=dctrl6, dctrl7=dctrl7, vres=vres.

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_SAMPLE_RESIDUE_ON_CLKS_FALL`: exercise and make observable: At initialization and on each falling `clks` crossing, sample `vin` into the residue state. Required traces: `time`, `clks`, `dctrl1`, `dctrl2`, `dctrl3`, `dctrl4`, `dctrl5`, `dctrl6`, `dctrl7`, `vin`, `vres`.
- `P_MSB_RESIDUE_STEP_SIGN`: exercise and make observable: A falling `dctrl7` event adds the half-scale MSB residue step with the declared sign. Required traces: `time`, `clks`, `dctrl1`, `dctrl2`, `dctrl3`, `dctrl4`, `dctrl5`, `dctrl6`, `dctrl7`, `vin`, `vres`.
- `P_LOWER_BIT_RESIDUE_WEIGHTS`: exercise and make observable: Falling `dctrl6..dctrl1` events apply the declared binary-weighted residue steps. Required traces: `time`, `clks`, `dctrl1`, `dctrl2`, `dctrl3`, `dctrl4`, `dctrl5`, `dctrl6`, `dctrl7`, `vin`, `vres`.
- `P_RESIDUE_OUTPUT_GAIN`: exercise and make observable: `vres` drives the sampled residue with the declared gain and voltage scale. Required traces: `time`, `clks`, `dctrl1`, `dctrl2`, `dctrl3`, `dctrl4`, `dctrl5`, `dctrl6`, `dctrl7`, `vin`, `vres`.

The required trace names are: `time`, `clks`, `dctrl1`, `dctrl2`, `dctrl3`, `dctrl4`, `dctrl5`, `dctrl6`, `dctrl7`, `vin`, `vres`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
