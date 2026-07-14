# Linear PFD Gain Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `linear_pfd_gain.va`:
  - Module `linear_pfd_gain` (entry)
    - position 0: `in1` (input, electrical)
    - position 1: `in2` (input, electrical)
    - position 2: `out` (output, electrical)

## Public Parameter Contract

- `linear_pfd_gain.kphi` defaults to `2.03`; valid range: finite; overrides kphi.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DIFFERENTIAL_INPUT_POLARITY`: restore: `out` uses the input difference `in1 - in2`, preserving the specified differential polarity. Required traces: `time`, `in1`, `in2`, `out`.
- `P_KPHI_GAIN_SCALE`: restore: `out` is scaled by the public gain coefficient `kphi` rather than unit gain or an alternate scale. Required traces: `time`, `in1`, `in2`, `out`.
- `P_CONTINUOUS_ANALOG_TRACKING`: restore: `out` continuously tracks analog input changes without clocked state, clipping, or single-ended substitution. Required traces: `time`, `in1`, `in2`, `out`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `linear_pfd_gain.va`.
Every supplied `.va` file is editable; do not add or omit files.
