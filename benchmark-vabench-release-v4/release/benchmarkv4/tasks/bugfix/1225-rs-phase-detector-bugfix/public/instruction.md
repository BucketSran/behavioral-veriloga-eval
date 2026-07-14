# RS Phase Detector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `rs_phase_detector.va`:
  - Module `rs_phase_detector` (entry)
    - position 0: `ref` (input, electrical)
    - position 1: `fb` (input, electrical)
    - position 2: `up` (output, electrical)
    - position 3: `down` (output, electrical)

## Public Parameter Contract

- `rs_phase_detector.vdd` defaults to `1.2`; valid range: finite; overrides vdd.
- `rs_phase_detector.tdel` defaults to `10p`; valid range: finite; overrides tdel.
- `rs_phase_detector.tr` defaults to `10p`; valid range: finite; overrides tr.
- `rs_phase_detector.tf` defaults to `10p`; valid range: finite; overrides tf.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DETECT_RISING_REF_AND_FB_CROSSINGS`: restore: Detect rising `ref` and `fb` crossings at `vdd/2`. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_A_RISING_REF_EDGE_SETS_THE`: restore: A rising `ref` edge sets the latch state so `up` is high and `down` is low. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_A_RISING_FB_EDGE_RESETS_THE`: restore: A rising `fb` edge resets the latch state so `up` is low and `down` is high. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_HOLD_THE_MOST_RECENT_LATCH_STATE`: restore: Hold the most recent latch state between qualifying input edges. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_INITIALIZE_TO_THE_RESET_STATE_WITH`: restore: Initialize to the reset state with `up` low and `down` high. Required traces: `time`, `down`, `fb`, `ref`, `up`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `rs_phase_detector.va`.
Every supplied `.va` file is editable; do not add or omit files.
