# QTZ Differential 2level Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `QTZ Differential 2level` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `qtz_differential_2level.va`:
  - Module `qtz_differential_2level` (entry)
    - position 0: `vinp` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `vrefp` (input, electrical)
    - position 3: `vrefn` (input, electrical)
    - position 4: `clk` (input, electrical)
    - position 5: `dout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `qtz_differential_2level` as `XDUT` with ordered public binding: vinp=vinp, vinn=vinn, vrefp=vrefp, vrefn=vrefn, clk=clk, dout=dout.

## Public Parameter Contract

- `qtz_differential_2level.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `qtz_differential_2level.ttol` defaults to `5p`; valid range: finite; overrides ttol.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_SIGNED_CODE`: exercise and make observable: Initialize the signed output code to `-0.5`. Required traces: `time`, `clk`, `dout`, `vinn`, `vinp`, `vrefn`, `vrefp`.
- `P_DIFFERENTIAL_MIDPOINT_DECISION`: exercise and make observable: On each rising `clk`, compare `vinp-vinn` with the midpoint between `vrefn` and `vrefp`. Required traces: `time`, `clk`, `dout`, `vinn`, `vinp`, `vrefn`, `vrefp`.
- `P_BIPOLAR_TWO_LEVEL_OUTPUT`: exercise and make observable: Drive `dout` to the signed `+0.5` or `-0.5` level rather than a unipolar code. Required traces: `time`, `clk`, `dout`, `vinn`, `vinp`, `vrefn`, `vrefp`.
- `P_CLOCKED_OUTPUT_HOLD`: exercise and make observable: Between rising clock decisions, hold the previous quantized output value. Required traces: `time`, `clk`, `dout`, `vinn`, `vinp`, `vrefn`, `vrefp`.

The required trace names are: `time`, `clk`, `dout`, `vinn`, `vinp`, `vrefn`, `vrefp`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
