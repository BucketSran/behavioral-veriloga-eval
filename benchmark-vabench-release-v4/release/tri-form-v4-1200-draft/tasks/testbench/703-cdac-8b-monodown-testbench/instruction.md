# CDAC 8b Monodown Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `CDAC 8b Monodown` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `cdac_8b_monodown` as `XDUT` with ordered public binding: vin=vin, clks=clks, dctrl0=dctrl0, dctrl1=dctrl1, dctrl2=dctrl2, dctrl3=dctrl3, dctrl4=dctrl4, dctrl5=dctrl5, dctrl6=dctrl6, dctrl7=dctrl7, vres=vres.

## Public Parameter Contract

- `cdac_8b_monodown.vdd` defaults to `1.0`; valid range: finite; overrides vdd.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_AT_INITIALIZATION_AND_ON_EACH_FALLING`: exercise and make observable: At initialization and on each falling `clks` crossing, sample `vin` into the held residue. On rising control crossings, subtract the corresponding binary-weighted fraction from the held residue: `dctrl7` subtracts 1/2, `dctrl6` 1/4, continuing down to `dctrl0` at 1/256. Hold the current residue value between events. Required traces: `time`, `clks`, `dctrl0`, `dctrl1`, `dctrl2`, `dctrl3`, `dctrl4`, `dctrl5`, `dctrl6`, `dctrl7`, `vin`, `vres`.

The required trace names are: `time`, `clks`, `dctrl0`, `dctrl1`, `dctrl2`, `dctrl3`, `dctrl4`, `dctrl5`, `dctrl6`, `dctrl7`, `vin`, `vres`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
