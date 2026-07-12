# Peak Detector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `peak_detector.va`:
  - Module `peak_detector` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vout` (output, electrical)

## Public Parameter Contract

- `peak_detector.vth` defaults to `0.45` V; valid range: vth > 0; sets the active-high reset threshold.
- `peak_detector.tr` defaults to `5e-10` s; valid range: tr > 0; sets vout rise and fall smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_ZERO`: restore: The retained peak and vout initialize to 0 V. Required traces: `time`, `vout`.
- `P_SAMPLED_MEASUREMENT`: restore: When reset is inactive, vin is considered for peak updates at periodic 500 ps sample instants. Required traces: `time`, `vin`, `rst`, `vout`.
- `P_MAX_RETENTION`: restore: At each sample, a vin value above the retained peak replaces it; lower or equal samples leave vout unchanged. Required traces: `time`, `vin`, `rst`, `vout`.
- `P_MONOTONIC_HOLD`: restore: Between resets, the retained peak does not decrease and remains held between sample instants. Required traces: `time`, `vin`, `rst`, `vout`.
- `P_RESET_CLEAR`: restore: While rst is above vth, the retained peak is cleared and vout returns to 0 V. Required traces: `time`, `rst`, `vout`.
- `P_OUTPUT_SMOOTHING`: restore: Changes of the retained peak appear on vout with finite transition smoothing set by tr. Required traces: `time`, `vout`.

## Modeling Constraints

- Use deterministic 500 ps timer sampling and retained voltage-domain state.
- Reset takes precedence over peak accumulation while asserted.
- Do not add undeclared sample controls, files, or validation-only outputs.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `peak_detector.va`.
Every supplied `.va` file is editable; do not add or omit files.
