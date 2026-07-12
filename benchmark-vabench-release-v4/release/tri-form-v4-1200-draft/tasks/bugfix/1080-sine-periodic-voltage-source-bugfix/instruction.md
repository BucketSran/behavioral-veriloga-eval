# Sine Periodic Voltage Source Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `multitone.va`:
  - Module `multitone` (entry)
    - position 0: `VSS` (input, electrical)
    - position 1: `OUT` (output, electrical)

## Public Parameter Contract

- `multitone.f1` defaults to `1000000.0` Hz; valid range: f1 > 0; sets the first sine-tone frequency.
- `multitone.f2` defaults to `2000000.0` Hz; valid range: f2 > 0; sets the second sine-tone frequency.
- `multitone.f3` defaults to `3000000.0` Hz; valid range: f3 > 0; sets the third sine-tone frequency.
- `multitone.a1` defaults to `0.2` V; valid range: any finite voltage amplitude; sets the signed amplitude of the first sine tone.
- `multitone.a2` defaults to `0.1` V; valid range: any finite voltage amplitude; sets the signed amplitude of the second sine tone.
- `multitone.a3` defaults to `0.05` V; valid range: any finite voltage amplitude; sets the signed amplitude of the third sine tone.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_FIRST_TONE`: restore: The output includes a zero-phase sine component with frequency f1 and signed amplitude a1. Required traces: `time`, `OUT`.
- `P_SECOND_TONE`: restore: The output includes a zero-phase sine component with frequency f2 and signed amplitude a2. Required traces: `time`, `OUT`.
- `P_THIRD_TONE`: restore: The output includes a zero-phase sine component with frequency f3 and signed amplitude a3. Required traces: `time`, `OUT`.
- `P_LINEAR_SUPERPOSITION`: restore: At every transient time t, OUT equals a1*sin(2*pi*f1*t) plus a2*sin(2*pi*f2*t) plus a3*sin(2*pi*f3*t). Required traces: `time`, `OUT`.
- `P_ZERO_INITIAL_PHASE`: restore: With no added offset and zero initial phase for all tones, OUT is 0 V at t = 0. Required traces: `time`, `OUT`.

## Modeling Constraints

- Use deterministic continuous voltage contribution from the declared three-tone sum.
- Drive OUT relative to the declared VSS reference port.
- Provide timestep guidance based on the highest declared frequency without altering the waveform contract.
- Do not add DC offsets, phase parameters, undeclared ports, or validation-only waveform branches.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `multitone.va`.
Every supplied `.va` file is editable; do not add or omit files.
