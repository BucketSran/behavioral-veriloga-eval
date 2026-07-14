# SAR CDAC Residue Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `SAR CDAC Residue` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `sar_cdac_residue` as `XDUT` with ordered public binding: VIN=vin, CLK=clk, S6=s6, S5=s5, S4=s4, S3=s3, S2=s2, S1=s1, VRES=vres.

## Public Parameter Contract

- `sar_cdac_residue.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the rising CLK sampling threshold at one half of vdd.
- `sar_cdac_residue.vrefp` defaults to `0.9` V; valid range: vrefp > vrefn; sets the upper endpoint of the reference span used by all residue steps.
- `sar_cdac_residue.vrefn` defaults to `0.0` V; valid range: vrefn < vrefp; sets the lower endpoint of the reference span used by all residue steps.
- `sar_cdac_residue.tr` defaults to `1e-12` s; valid range: tr > 0; sets the transition time of the VRES voltage output.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INPUT_SAMPLE`: exercise and make observable: At initial_step and each rising CLK crossing through vdd/2, the residue state samples VIN. Required traces: `time`, `vin`, `clk`, `vres`.
- `P_S6_HALF_ADD`: exercise and make observable: Each falling S6 crossing through vdd/2 adds one half of the public reference span to the current residue. Required traces: `time`, `s6`, `vres`.
- `P_BINARY_SUBTRACTIONS`: exercise and make observable: Rising crossings of S5, S4, S3, S2, and S1 through vdd/2 subtract one fourth, one eighth, one sixteenth, one thirty-second, and one sixty-fourth of the public reference span respectively. Required traces: `time`, `s5`, `s4`, `s3`, `s2`, `s1`, `vres`.
- `P_EDGE_POLARITY`: exercise and make observable: S6 updates only on falling vdd/2 threshold crossings, while S5 through S1 update only on rising vdd/2 threshold crossings. Required traces: `time`, `s6`, `s5`, `s4`, `s3`, `s2`, `s1`, `vres`.
- `P_ACCUMULATED_STATE`: exercise and make observable: Between declared sampling and switch events, VRES represents and holds the accumulated residue state. Required traces: `time`, `vin`, `clk`, `s6`, `s5`, `s4`, `s3`, `s2`, `s1`, `vres`.
- `P_OUTPUT_TRANSITION`: exercise and make observable: VRES changes from the residue state using the declared tr transition time. Required traces: `time`, `vres`.

The required trace names are: `time`, `vin`, `clk`, `s6`, `s5`, `s4`, `s3`, `s2`, `s1`, `vres`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
