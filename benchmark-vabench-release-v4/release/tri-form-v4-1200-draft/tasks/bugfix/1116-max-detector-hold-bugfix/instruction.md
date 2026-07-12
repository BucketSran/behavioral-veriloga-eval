# Max Detector Hold Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `max_detector_hold.va`:
  - Module `max_detector_hold` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_INPUT`: restore: At simulation start, the held output is initialized from the input rather than from a fixed rail. Required traces: `time`, `vin`, `vout`.
- `P_CAPTURE_NEW_MAX`: restore: Whenever vin exceeds every previously observed value, vout updates to that new maximum. Required traces: `time`, `vin`, `vout`.
- `P_HOLD_ON_FALL`: restore: When vin falls below the held maximum, vout retains the previously captured maximum. Required traces: `time`, `vin`, `vout`.
- `P_MONOTONE_OUTPUT`: restore: Across transient operation, vout is monotone nondecreasing. Required traces: `time`, `vin`, `vout`.
- `P_RUNNING_MAX`: restore: At each observation time, vout equals the maximum vin value observed from simulation start through that time. Required traces: `time`, `vin`, `vout`.

## Modeling Constraints

- Use deterministic Spectre-compatible analog state for the running maximum.
- Use voltage-domain output behavior without an undeclared reset.
- Do not implement a follower, minimum detector, final-sample detector, current contribution, or validation-only hook.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `max_detector_hold.va`.
Every supplied `.va` file is editable; do not add or omit files.
