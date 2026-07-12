# Deadband Window Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Deadband Window` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `deadband_window.va`:
  - Module `deadband_window` (entry)
    - position 0: `sigin` (input, electrical)
    - position 1: `sigout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `deadband_window` as `XDUT` with ordered public binding: sigin=sigin, sigout=sigout.

## Public Parameter Contract

- `deadband_window.dead_high` defaults to `0.1`; valid range: finite; overrides dead_high.
- `deadband_window.dead_low` defaults to `-0.1`; valid range: finite; overrides dead_low.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ZERO_INSIDE_DEADBAND`: exercise and make observable: For `dead_low <= V(sigin) <= dead_high`, drive `sigout` to 0 V. Required traces: `time`, `sigin`, `sigout`.
- `P_LOWER_RESIDUE`: exercise and make observable: For `V(sigin) < dead_low`, drive `sigout` to `V(sigin) - dead_low`. Required traces: `time`, `sigin`, `sigout`.
- `P_UPPER_RESIDUE`: exercise and make observable: For `V(sigin) > dead_high`, drive `sigout` to `V(sigin) - dead_high`. Required traces: `time`, `sigin`, `sigout`.

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
