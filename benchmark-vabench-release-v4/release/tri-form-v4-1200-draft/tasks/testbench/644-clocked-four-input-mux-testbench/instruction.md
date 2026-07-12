# Clocked Four Input Mux Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Clocked Four Input Mux` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `clocked_four_input_mux.va`:
  - Module `clocked_four_input_mux` (entry)
    - position 0: `dsel0` (input, electrical)
    - position 1: `dsel1` (input, electrical)
    - position 2: `din0` (input, electrical)
    - position 3: `din1` (input, electrical)
    - position 4: `din2` (input, electrical)
    - position 5: `din3` (input, electrical)
    - position 6: `clks` (input, electrical)
    - position 7: `dout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `clocked_four_input_mux` as `XDUT` with ordered public binding: dsel0=dsel0, dsel1=dsel1, din0=din0, din1=din1, din2=din2, din3=din3, clks=clks, dout=dout.

## Public Parameter Contract

- `clocked_four_input_mux.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `clocked_four_input_mux.tr` defaults to `20p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_FALLING_EDGE_SAMPLE_HOLD`: exercise and make observable: Only falling `clks` crossings through `vth` update `dout`; between those events the last selected input value is held. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `dout`, `dsel0`, `dsel1`.
- `P_SELECT_BIT_DECODE`: exercise and make observable: `dsel0` is the LSB and `dsel1` is the MSB when selecting among `din0` through `din3`. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `dout`, `dsel0`, `dsel1`.
- `P_ALL_FOUR_INPUTS_REACHABLE`: exercise and make observable: All four data inputs can be selected and forwarded to `dout` according to the two-bit select code. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `dout`, `dsel0`, `dsel1`.

The required trace names are: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `dout`, `dsel0`, `dsel1`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
