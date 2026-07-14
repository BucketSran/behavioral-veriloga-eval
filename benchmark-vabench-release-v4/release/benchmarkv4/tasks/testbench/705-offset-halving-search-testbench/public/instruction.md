# Offset Halving Search Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Offset Halving Search` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `offset_halving_search.va`:
  - Module `offset_halving_search` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `dcmpp` (input, electrical)
    - position 2: `vinp` (output, electrical)
    - position 3: `vinn` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `offset_halving_search` as `XDUT` with ordered public binding: clk=clk, dcmpp=dcmpp, vinp=vinp, vinn=vinn.

## Public Parameter Contract

- `offset_halving_search.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `offset_halving_search.step_initial` defaults to `0.16`; valid range: finite; overrides step_initial.
- `offset_halving_search.step_min` defaults to `0.02`; valid range: finite; overrides step_min.
- `offset_halving_search.diff_limit` defaults to `0.12`; valid range: finite; overrides diff_limit.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIALIZE_THE_DIFFERENTIAL_TRIM_RESIDUE_TO`: exercise and make observable: Initialize the differential trim residue to zero and the active step to `step_initial`. On each falling `clk` crossing before lockout, sample `dcmpp`: a high decision moves the differential trim negative and a low decision moves it positive. Clamp the signed residue to `+/-diff_limit`. Halve the active step after each update; once the next step would be below `step_min`, lock the trim code and hold the existing residue for later clock edges. Drive `vinp` and `vinn` symmetrically around `0.5*vdd` from the current residue. Required traces: `time`, `clk`, `dcmpp`, `vinn`, `vinp`.

The required trace names are: `time`, `clk`, `dcmpp`, `vinn`, `vinp`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
