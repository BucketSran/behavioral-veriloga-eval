# Max Detector Hold Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Max Detector Hold` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `max_detector_hold.va`:
  - Module `max_detector_hold` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `max_detector_hold` as `XDUT` with ordered public binding: vin=vin, vout=vout.

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_INPUT`: exercise and make observable: At simulation start, the held output is initialized from the input rather than from a fixed rail. Required traces: `time`, `vin`, `vout`.
- `P_CAPTURE_NEW_MAX`: exercise and make observable: Whenever vin exceeds every previously observed value, vout updates to that new maximum. Required traces: `time`, `vin`, `vout`.
- `P_HOLD_ON_FALL`: exercise and make observable: When vin falls below the held maximum, vout retains the previously captured maximum. Required traces: `time`, `vin`, `vout`.
- `P_MONOTONE_OUTPUT`: exercise and make observable: Across transient operation, vout is monotone nondecreasing. Required traces: `time`, `vin`, `vout`.
- `P_RUNNING_MAX`: exercise and make observable: At each observation time, vout equals the maximum vin value observed from simulation start through that time. Required traces: `time`, `vin`, `vout`.

The required trace names are: `time`, `vin`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
