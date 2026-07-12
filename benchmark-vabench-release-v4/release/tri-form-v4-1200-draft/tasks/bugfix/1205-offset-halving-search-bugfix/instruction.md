# Offset Halving Search Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `offset_halving_search.va`:
  - Module `offset_halving_search` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `dcmpp` (input, electrical)
    - position 2: `vinp` (output, electrical)
    - position 3: `vinn` (output, electrical)

## Public Parameter Contract

- `offset_halving_search.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `offset_halving_search.step_initial` defaults to `0.16`; valid range: finite; overrides step_initial.
- `offset_halving_search.step_min` defaults to `0.02`; valid range: finite; overrides step_min.
- `offset_halving_search.diff_limit` defaults to `0.12`; valid range: finite; overrides diff_limit.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIALIZE_THE_DIFFERENTIAL_TRIM_RESIDUE_TO`: restore: Initialize the differential trim residue to zero and the active step to `step_initial`. On each falling `clk` crossing before lockout, sample `dcmpp`: a high decision moves the differential trim negative and a low decision moves it positive. Clamp the signed residue to `+/-diff_limit`. Halve the active step after each update; once the next step would be below `step_min`, lock the trim code and hold the existing residue for later clock edges. Drive `vinp` and `vinn` symmetrically around `0.5*vdd` from the current residue. Required traces: `time`, `clk`, `dcmpp`, `vinn`, `vinp`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `offset_halving_search.va`.
Every supplied `.va` file is editable; do not add or omit files.
