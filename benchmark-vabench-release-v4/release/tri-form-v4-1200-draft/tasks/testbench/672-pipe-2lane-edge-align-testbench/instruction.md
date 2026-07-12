# Pipe 2lane Edge Align Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Pipe 2lane Edge Align` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `pipe_2lane_edge_align.va`:
  - Module `pipe_2lane_edge_align` (entry)
    - position 0: `din1` (input, electrical)
    - position 1: `din2` (input, electrical)
    - position 2: `clk_align` (input, electrical)
    - position 3: `dout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `pipe_2lane_edge_align` as `XDUT` with ordered public binding: din1=din1, din2=din2, clk_align=clk_align, dout=dout.

## Public Parameter Contract

- `pipe_2lane_edge_align.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_LANE1_STATE`: exercise and make observable: Before alignment edges, the output state initializes from `din1`. Required traces: `time`, `din1`, `dout`.
- `P_RISING_EDGE_LANE1`: exercise and make observable: A rising `clk_align` crossing samples and publishes `din1`. Required traces: `time`, `clk_align`, `din1`, `dout`.
- `P_FALLING_EDGE_LANE2`: exercise and make observable: A falling `clk_align` crossing samples and publishes `din2`. Required traces: `time`, `clk_align`, `din2`, `dout`.
- `P_SELECTED_LEVEL_HOLD`: exercise and make observable: `dout` holds the last selected lane level with full output amplitude between alignment edges. Required traces: `time`, `clk_align`, `din1`, `din2`, `dout`.

The required trace names are: `time`, `din1`, `din2`, `clk_align`, `dout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
