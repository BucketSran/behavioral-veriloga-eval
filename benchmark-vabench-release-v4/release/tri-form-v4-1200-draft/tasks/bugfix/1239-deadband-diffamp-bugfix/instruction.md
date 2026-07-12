# Deadband Diffamp Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `deadband_diffamp.va`:
  - Module `deadband_diffamp` (entry)
    - position 0: `sigin_p` (input, electrical)
    - position 1: `sigin_n` (input, electrical)
    - position 2: `sigout` (output, electrical)

## Public Parameter Contract

- `deadband_diffamp.sigin_dead_low` defaults to `-0.1`; valid range: finite; overrides sigin_dead_low.
- `deadband_diffamp.sigin_dead_high` defaults to `0.1`; valid range: finite; overrides sigin_dead_high.
- `deadband_diffamp.sigout_leak` defaults to `0.02`; valid range: finite; overrides sigout_leak.
- `deadband_diffamp.gain_low` defaults to `2.0`; valid range: finite; overrides gain_low.
- `deadband_diffamp.gain_high` defaults to `3.0`; valid range: finite; overrides gain_high.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DIFFERENTIAL_POLARITY`: restore: Compute the differential input as `V(sigin_p, sigin_n)` with the documented polarity. Required traces: `time`, `sigin_n`, `sigin_p`, `sigout`.
- `P_DEADBAND_LEAK_OUTPUT`: restore: Inside the inclusive differential deadband, drive the public leakage level `sigout_leak`. Required traces: `time`, `sigin_n`, `sigin_p`, `sigout`.
- `P_ASYMMETRIC_RESIDUE_GAINS`: restore: Below the lower threshold use `gain_low` for the low-side signed residue plus leakage; above the upper threshold use `gain_high` for the high-side signed residue plus leakage. Required traces: `time`, `sigin_n`, `sigin_p`, `sigout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `deadband_diffamp.va`.
Every supplied `.va` file is editable; do not add or omit files.
