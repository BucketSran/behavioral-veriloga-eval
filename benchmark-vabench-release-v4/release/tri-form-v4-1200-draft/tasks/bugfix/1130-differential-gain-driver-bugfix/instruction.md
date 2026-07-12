# Differential Gain Driver Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `differential_gain_driver.va`:
  - Module `differential_gain_driver` (entry)
    - position 0: `sigin_p` (input, electrical)
    - position 1: `sigin_n` (input, electrical)
    - position 2: `sigout_p` (output, electrical)
    - position 3: `sigout_n` (output, electrical)
    - position 4: `sigref` (input, electrical)

## Public Parameter Contract

- `differential_gain_driver.gain` defaults to `1`; valid range: finite; overrides gain.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DIFFERENTIAL_INPUT_GAIN`: restore: Read `V(sigin_p, sigin_n)` and multiply it by the overridable `gain` parameter. Required traces: `time`, `sigin_p`, `sigin_n`, `sigout_p`, `sigout_n`, `sigref`.
- `P_BALANCED_HALF_SPLIT`: restore: Drive `sigout_p` and `sigout_n` as equal and opposite half-swings around `sigref`. Required traces: `time`, `sigin_p`, `sigin_n`, `sigout_p`, `sigout_n`, `sigref`.
- `P_OUTPUT_POLARITY`: restore: For a positive input differential, `sigout_p` rises relative to `sigref` and `sigout_n` falls relative to `sigref`. Required traces: `time`, `sigin_p`, `sigin_n`, `sigout_p`, `sigout_n`, `sigref`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `differential_gain_driver.va`.
Every supplied `.va` file is editable; do not add or omit files.
