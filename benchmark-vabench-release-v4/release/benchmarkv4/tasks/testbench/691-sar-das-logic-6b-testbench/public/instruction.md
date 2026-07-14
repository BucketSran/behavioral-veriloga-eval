# SAR DAS Logic 6b Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `SAR DAS Logic 6b` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `sar_das_logic_6b.va`:
  - Module `sar_das_logic_6b` (entry)
    - position 0: `clk_sampling` (input, electrical)
    - position 1: `clk_sar` (input, electrical)
    - position 2: `vcomp` (input, electrical)
    - position 3: `d1` (output, electrical)
    - position 4: `d2` (output, electrical)
    - position 5: `d3` (output, electrical)
    - position 6: `d4` (output, electrical)
    - position 7: `d5` (output, electrical)
    - position 8: `d6` (output, electrical)
    - position 9: `db1` (output, electrical)
    - position 10: `db2` (output, electrical)
    - position 11: `db3` (output, electrical)
    - position 12: `db4` (output, electrical)
    - position 13: `db5` (output, electrical)
    - position 14: `db6` (output, electrical)
    - position 15: `co` (output, electrical)
    - position 16: `cob` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `sar_das_logic_6b` as `XDUT` with ordered public binding: clk_sampling=clk_sampling, clk_sar=clk_sar, vcomp=vcomp, d1=d1, d2=d2, d3=d3, d4=d4, d5=d5, d6=d6, db1=db1, db2=db2, db3=db3, db4=db4, db5=db5, db6=db6, co=co, cob=cob.

## Public Parameter Contract

- `sar_das_logic_6b.tde` defaults to `50p`; valid range: finite; overrides tde.
- `sar_das_logic_6b.tdc` defaults to `50p`; valid range: finite; overrides tdc.
- `sar_das_logic_6b.vdd` defaults to `1.1`; valid range: finite; overrides vdd.
- `sar_das_logic_6b.vcm` defaults to `0.55`; valid range: finite; overrides vcm.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_SAMPLING_RESET_CONVERSION_STATE`: exercise and make observable: A rising `clk_sampling` transition clears controls and pulses, and a falling transition arms the SAR conversion sequence. Required traces: `time`, `clk_sampling`, `clk_sar`, `co`, `cob`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `db1`, `db2`, `db3`, `db4`, `db5`, `db6`, `vcomp`.
- `P_SAR_COMPARATOR_POLARITY`: exercise and make observable: Each rising `clk_sar` transition compares `vcomp` to `vcm` and drives `co/cob` with the declared polarity. Required traces: `time`, `clk_sampling`, `clk_sar`, `co`, `cob`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `db1`, `db2`, `db3`, `db4`, `db5`, `db6`, `vcomp`.
- `P_SIX_BIT_DECISION_SEQUENCE`: exercise and make observable: The SAR decisions update `d6..d1` in the declared order through the conversion. Required traces: `time`, `clk_sampling`, `clk_sar`, `co`, `cob`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `db1`, `db2`, `db3`, `db4`, `db5`, `db6`, `vcomp`.
- `P_CONTROL_OUTPUT_LEVELS`: exercise and make observable: Decision pulses and bit-control outputs use valid voltage-coded low/high levels. Required traces: `time`, `clk_sampling`, `clk_sar`, `co`, `cob`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `db1`, `db2`, `db3`, `db4`, `db5`, `db6`, `vcomp`.

The required trace names are: `time`, `clk_sampling`, `clk_sar`, `co`, `cob`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `db1`, `db2`, `db3`, `db4`, `db5`, `db6`, `vcomp`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
