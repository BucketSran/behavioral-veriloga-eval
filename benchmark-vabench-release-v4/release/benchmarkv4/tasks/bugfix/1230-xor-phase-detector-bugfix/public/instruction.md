# XOR Phase Detector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `xor_phase_detector.va`:
  - Module `xor_phase_detector` (entry)
    - position 0: `ref` (input, electrical)
    - position 1: `fb` (input, electrical)
    - position 2: `up` (output, electrical)
    - position 3: `down` (output, electrical)

## Public Parameter Contract

- `xor_phase_detector.vdd` defaults to `1.2`; valid range: finite; overrides vdd.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INTERPRET_REF_AND_FB_LOGIC_LEVELS`: restore: Interpret `ref` and `fb` logic levels using a threshold of `vdd/2`. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_DRIVE_UP_HIGH_WHEN_THE_INTERPRETED`: restore: Drive `up` high when the interpreted `ref` and `fb` levels differ. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_DRIVE_DOWN_HIGH_WHEN_THE_INTERPRETED`: restore: Drive `down` high when the interpreted `ref` and `fb` levels match. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_UPDATE_OUTPUTS_COMBINATIONALLY_FROM_THE_CURREN`: restore: Update outputs combinationally from the current input voltages. Required traces: `time`, `down`, `fb`, `ref`, `up`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `xor_phase_detector.va`.
Every supplied `.va` file is editable; do not add or omit files.
