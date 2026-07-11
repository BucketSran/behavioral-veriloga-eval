# Element Shuffler Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Element Shuffler` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `element_shuffler.va`:
  - Module `element_shuffler` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst_n` (input, electrical)
    - position 2: `out0` (output, electrical)
    - position 3: `out1` (output, electrical)
    - position 4: `out2` (output, electrical)
    - position 5: `out3` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `element_shuffler` as `XDUT` with ordered public binding: clk=clk, rst_n=rst_n, out0=out0, out1=out1, out2=out2, out3=out3.

## Public Parameter Contract

- `element_shuffler.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets clk and rst_n decision threshold.
- `element_shuffler.vdd` defaults to `0.9` V; valid range: vdd > 0; sets active output high level.
- `element_shuffler.tr` defaults to `3e-10` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_START`: exercise and make observable: Active-low reset establishes the state so the first rising clk edge after release selects out2. Required traces: `time`, `clk`, `rst_n`, `out0`, `out1`, `out2`, `out3`.
- `P_PERMUTATION`: exercise and make observable: Rising clk edges advance the repeating out2, out0, out3, out1 permutation. Required traces: `time`, `clk`, `rst_n`, `out0`, `out1`, `out2`, `out3`.
- `P_ONE_HOT`: exercise and make observable: Exactly one output is high in every stable released-reset state. Required traces: `time`, `rst_n`, `out0`, `out1`, `out2`, `out3`.
- `P_RAIL_LEVELS`: exercise and make observable: The selected output approaches vdd and all other outputs approach 0 V with finite smoothing. Required traces: `time`, `out0`, `out1`, `out2`, `out3`.

The required trace names are: `time`, `clk`, `rst_n`, `out0`, `out1`, `out2`, `out3`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
