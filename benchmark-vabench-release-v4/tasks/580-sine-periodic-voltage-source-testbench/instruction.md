# Sine Periodic Voltage Source Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Sine Periodic Voltage Source` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `multitone.va`:
  - Module `multitone` (entry)
    - position 0: `VSS` (input, electrical)
    - position 1: `OUT` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `multitone` as `XDUT` with ordered public binding: VSS=0, OUT=OUT.

## Public Parameter Contract

- `multitone.f1` defaults to `1000000.0` Hz; valid range: f1 > 0; sets the first sine-tone frequency.
- `multitone.f2` defaults to `2000000.0` Hz; valid range: f2 > 0; sets the second sine-tone frequency.
- `multitone.f3` defaults to `3000000.0` Hz; valid range: f3 > 0; sets the third sine-tone frequency.
- `multitone.a1` defaults to `0.2` V; valid range: any finite voltage amplitude; sets the signed amplitude of the first sine tone.
- `multitone.a2` defaults to `0.1` V; valid range: any finite voltage amplitude; sets the signed amplitude of the second sine tone.
- `multitone.a3` defaults to `0.05` V; valid range: any finite voltage amplitude; sets the signed amplitude of the third sine tone.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_FIRST_TONE`: exercise and make observable: The output includes a zero-phase sine component with frequency f1 and signed amplitude a1. Required traces: `time`, `OUT`.
- `P_SECOND_TONE`: exercise and make observable: The output includes a zero-phase sine component with frequency f2 and signed amplitude a2. Required traces: `time`, `OUT`.
- `P_THIRD_TONE`: exercise and make observable: The output includes a zero-phase sine component with frequency f3 and signed amplitude a3. Required traces: `time`, `OUT`.
- `P_LINEAR_SUPERPOSITION`: exercise and make observable: At every transient time t, OUT equals a1*sin(2*pi*f1*t) plus a2*sin(2*pi*f2*t) plus a3*sin(2*pi*f3*t). Required traces: `time`, `OUT`.
- `P_ZERO_INITIAL_PHASE`: exercise and make observable: With no added offset and zero initial phase for all tones, OUT is 0 V at t = 0. Required traces: `time`, `OUT`.

The required trace names are: `time`, `OUT`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
