# Smooth Limiting Diffamp Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `limiting_diffamp.va`:
  - Module `limiting_diffamp` (entry)
    - position 0: `sigin_p` (input, electrical)
    - position 1: `sigin_n` (input, electrical)
    - position 2: `sigout` (output, electrical)

## Public Parameter Contract

- `limiting_diffamp.gain` defaults to `4.0`; valid range: finite; overrides gain.
- `limiting_diffamp.limit` defaults to `0.75 from (0:inf)`; valid range: finite; overrides limit.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ODD_DIFFERENTIAL_POLARITY`: restore: Compute `V(sigin_p, sigin_n)`, preserve polarity, and drive an odd differential transfer. Required traces: `time`, `sigin_n`, `sigin_p`, `sigout`.
- `P_SMALL_SIGNAL_GAIN`: restore: Near zero differential input, drive approximately `gain * V(sigin_p, sigin_n)`. Required traces: `time`, `sigin_n`, `sigin_p`, `sigout`.
- `P_SMOOTH_SYMMETRIC_LIMITING`: restore: For large positive and negative differential inputs, smoothly approach `+limit` and `-limit` without a hard clamp. Required traces: `time`, `sigin_n`, `sigin_p`, `sigout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `limiting_diffamp.va`.
Every supplied `.va` file is editable; do not add or omit files.
