# PFD Up Down State Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `pfd_up_down_state.va`:
  - Module `pfd_up_down_state` (entry)
    - position 0: `ref` (input, electrical)
    - position 1: `fb` (input, electrical)
    - position 2: `up` (output, electrical)
    - position 3: `down` (output, electrical)

## Public Parameter Contract

- `pfd_up_down_state.vdd` defaults to `1.2`; valid range: finite; overrides vdd.
- `pfd_up_down_state.tdel` defaults to `10p`; valid range: finite; overrides tdel.
- `pfd_up_down_state.tr` defaults to `10p`; valid range: finite; overrides tr.
- `pfd_up_down_state.tf` defaults to `10p`; valid range: finite; overrides tf.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DETECT_RISING_REF_AND_FB_CROSSINGS`: restore: Detect rising `ref` and `fb` crossings at `vdd/2`. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_MAINTAIN_AN_INTEGER_DETECTOR_STATE_BOUNDED`: restore: Maintain an integer detector state bounded to `-1`, `0`, or `+1`. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_A_RISING_REF_EDGE_INCREMENTS_THE`: restore: A rising `ref` edge increments the state up to `+1`. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_A_RISING_FB_EDGE_DECREMENTS_THE`: restore: A rising `fb` edge decrements the state down to `-1`. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_DRIVE_UP_HIGH_WHEN_THE_STATE`: restore: Drive `up` high when the state is `+1`. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_DRIVE_DOWN_HIGH_WHEN_THE_STATE`: restore: Drive `down` high when the state is `-1`. Required traces: `time`, `down`, `fb`, `ref`, `up`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pfd_up_down_state.va`.
Every supplied `.va` file is editable; do not add or omit files.
