# L2 CDAC 4b Residue Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `L2 CDAC 4b Residue` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `l2_cdac_4b_residue.va`:
  - Module `l2_cdac_4b_residue` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clks` (input, electrical)
    - position 2: `dctrl1` (input, electrical)
    - position 3: `dctrl2` (input, electrical)
    - position 4: `dctrl3` (input, electrical)
    - position 5: `vres` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `l2_cdac_4b_residue` as `XDUT` with ordered public binding: vin=vin, clks=clks, dctrl1=dctrl1, dctrl2=dctrl2, dctrl3=dctrl3, vres=vres.

## Public Parameter Contract

- `l2_cdac_4b_residue.vdd` defaults to `1`; valid range: finite; overrides vdd.
- `l2_cdac_4b_residue.vrefp` defaults to `1`; valid range: finite; overrides vrefp.
- `l2_cdac_4b_residue.vrefn` defaults to `0`; valid range: finite; overrides vrefn.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_FALLING_CLOCK_SAMPLE`: exercise and make observable: `vin` is sampled into the residue on initial step and on falling `clks` crossings through `vdd/2`. Required traces: `time`, `vin`, `clks`, `vres`.
- `P_CONTROL_STEP_WEIGHTS`: exercise and make observable: Rising control crossings add positive capacitive reference steps: `dctrl3` is half scale, `dctrl2` quarter scale, and `dctrl1` eighth scale. Required traces: `time`, `dctrl1`, `dctrl2`, `dctrl3`, `vres`.
- `P_RETAINED_RESIDUE_OUTPUT`: exercise and make observable: `vres` retains the accumulated sampled residue between clock/control events. Required traces: `time`, `vin`, `clks`, `dctrl1`, `dctrl2`, `dctrl3`, `vres`.

The required trace names are: `time`, `vin`, `clks`, `dctrl1`, `dctrl2`, `dctrl3`, `vres`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
