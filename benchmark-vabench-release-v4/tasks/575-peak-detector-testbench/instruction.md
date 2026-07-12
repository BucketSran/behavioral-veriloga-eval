# Peak Detector Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Peak Detector` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `peak_detector.va`:
  - Module `peak_detector` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `peak_detector` as `XDUT` with ordered public binding: vin=vin, rst=rst, vout=vout.

## Public Parameter Contract

- `peak_detector.vth` defaults to `0.45` V; valid range: vth > 0; sets the active-high reset threshold.
- `peak_detector.tr` defaults to `5e-10` s; valid range: tr > 0; sets vout rise and fall smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_ZERO`: exercise and make observable: The retained peak and vout initialize to 0 V. Required traces: `time`, `vout`.
- `P_SAMPLED_MEASUREMENT`: exercise and make observable: When reset is inactive, vin is considered for peak updates at periodic 500 ps sample instants. Required traces: `time`, `vin`, `rst`, `vout`.
- `P_MAX_RETENTION`: exercise and make observable: At each sample, a vin value above the retained peak replaces it; lower or equal samples leave vout unchanged. Required traces: `time`, `vin`, `rst`, `vout`.
- `P_MONOTONIC_HOLD`: exercise and make observable: Between resets, the retained peak does not decrease and remains held between sample instants. Required traces: `time`, `vin`, `rst`, `vout`.
- `P_RESET_CLEAR`: exercise and make observable: While rst is above vth, the retained peak is cleared and vout returns to 0 V. Required traces: `time`, `rst`, `vout`.
- `P_OUTPUT_SMOOTHING`: exercise and make observable: Changes of the retained peak appear on vout with finite transition smoothing set by tr. Required traces: `time`, `vout`.

The required trace names are: `time`, `vin`, `rst`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
