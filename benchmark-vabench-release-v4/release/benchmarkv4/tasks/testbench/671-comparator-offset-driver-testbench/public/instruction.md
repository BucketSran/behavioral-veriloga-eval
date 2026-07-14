# Comparator Offset Driver Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Comparator Offset Driver` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `comparator_offset_binary_driver.va`:
  - Module `comparator_offset_binary_driver` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `dcmpp` (input, electrical)
    - position 2: `vinp` (output, electrical)
    - position 3: `vinn` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `comparator_offset_binary_driver` as `XDUT` with ordered public binding: clk=clk, dcmpp=dcmpp, vinp=vinp, vinn=vinn.

## Public Parameter Contract

- `comparator_offset_binary_driver.vdd` defaults to `0.9`; valid range: finite; overrides vdd.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_FALLING_CLOCK_DECISION_SAMPLE`: exercise and make observable: On each falling `clk` threshold crossing, sample `dcmpp` to choose the next binary-search direction. Required traces: `time`, `clk`, `dcmpp`, `vinp`, `vinn`.
- `P_DECISION_POLARITY_UPDATE`: exercise and make observable: A high decision moves the differential input negative and a low decision moves it positive. Required traces: `time`, `clk`, `dcmpp`, `vinp`, `vinn`.
- `P_HALVING_SEARCH_STEP`: exercise and make observable: The differential search step halves after each sampled decision. Required traces: `time`, `clk`, `dcmpp`, `vinp`, `vinn`.
- `P_COMMON_MODE_HALF_SCALE_DRIVE`: exercise and make observable: `vinp` and `vinn` are driven symmetrically around the common-mode level with half differential amplitude on each side. Required traces: `time`, `vinp`, `vinn`.

The required trace names are: `time`, `clk`, `dcmpp`, `vinp`, `vinn`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
