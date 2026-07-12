# Phase Detector Chopper Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `phase_detector_chopper.va`:
  - Module `phase_detector_chopper` (entry)
    - position 0: `vlocal_osc` (input, electrical)
    - position 1: `vin_rf` (input, electrical)
    - position 2: `vif` (output, electrical)

## Public Parameter Contract

- `phase_detector_chopper.gain` defaults to `1.25`; valid range: finite; overrides gain.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_POSITIVE_LO_GAIN_PATH`: restore: When `vlocal_osc` is positive, drive `vif = gain * vin_rf`. Required traces: `time`, `vif`, `vin_rf`, `vlocal_osc`.
- `P_NEGATIVE_LO_CHOP_PATH`: restore: When `vlocal_osc` is not positive, drive `vif = -gain * vin_rf`. Required traces: `time`, `vif`, `vin_rf`, `vlocal_osc`.
- `P_CONTINUOUS_TRACKING`: restore: `vif` tracks `vin_rf` and `vlocal_osc` continuously without clocked state or hidden latching. Required traces: `time`, `vif`, `vin_rf`, `vlocal_osc`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `phase_detector_chopper.va`.
Every supplied `.va` file is editable; do not add or omit files.
