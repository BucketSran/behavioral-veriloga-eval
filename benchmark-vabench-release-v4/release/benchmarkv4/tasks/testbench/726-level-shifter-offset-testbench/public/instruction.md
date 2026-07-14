# Level Shifter Offset Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Level Shifter Offset` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `level_shifter_offset.va`:
  - Module `level_shifter_offset` (entry)
    - position 0: `sigin` (input, electrical)
    - position 1: `sigout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `level_shifter_offset` as `XDUT` with ordered public binding: sigin=sigin, sigout=sigout.

## Public Parameter Contract

- `level_shifter_offset.sigshift` defaults to `0.35`; valid range: finite; overrides sigshift.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_DRIVE_SIGOUT_TO_V_SIGIN_PLUS_SIGSHIFT`: exercise and make observable: Drive `sigout` to `V(sigin) + sigshift` for the current input voltage. Required traces: `time`, `sigin`, `sigout`.
- `P_PRESERVE_UNITY_GAIN_WHILE_ADDING_OFFSET`: exercise and make observable: Preserve unity gain from `sigin` to `sigout` while adding the configured `sigshift` offset; input changes must appear at `sigout` with the same voltage step size. Required traces: `time`, `sigin`, `sigout`.

The required trace names are: `time`, `sigin`, `sigout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
