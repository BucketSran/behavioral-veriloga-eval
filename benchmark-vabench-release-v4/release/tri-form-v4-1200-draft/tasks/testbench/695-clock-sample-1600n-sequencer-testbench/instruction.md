# Clock Sample 1600n Sequencer Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Clock Sample 1600n Sequencer` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `clock_sample_1600n_sequencer.va`:
  - Module `clock_sample_1600n_sequencer` (entry)
    - position 0: `rst` (output, electrical)
    - position 1: `s` (output, electrical)
    - position 2: `nc` (output, electrical)
    - position 3: `res` (output, electrical)
    - position 4: `conv` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `clock_sample_1600n_sequencer` as `XDUT` with ordered public binding: rst=rst, s=s, nc=nc, res=res, conv=conv.

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_PERIODIC_16NS_FRAME`: exercise and make observable: Generate a repeating 16 ns ADC timing frame. Required traces: `time`, `conv`, `nc`, `res`, `rst`, `s`.
- `P_RESET_AND_SAMPLE_WINDOWS`: exercise and make observable: `rst` and `s` are high only in the declared frame windows, including both sample windows. Required traces: `time`, `conv`, `nc`, `res`, `rst`, `s`.
- `P_NONOVERLAP_AND_RESIDUE_WINDOWS`: exercise and make observable: `nc` and `res` use the declared non-overlap and residue windows without swapping outputs. Required traces: `time`, `conv`, `nc`, `res`, `rst`, `s`.
- `P_CONVERSION_OUTPUT_TIMING`: exercise and make observable: `conv` is asserted in the declared conversion windows with valid timing and level. Required traces: `time`, `conv`, `nc`, `res`, `rst`, `s`.

The required trace names are: `time`, `conv`, `nc`, `res`, `rst`, `s`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
