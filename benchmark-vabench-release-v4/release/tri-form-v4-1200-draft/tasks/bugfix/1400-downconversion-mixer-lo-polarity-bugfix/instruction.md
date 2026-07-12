# Downconversion Mixer with LO Polarity Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `downconversion_mixer_lo_polarity.va`:
  - Module `downconversion_mixer_lo_polarity` (entry)
    - position 0: `rf_in` (input, electrical)
    - position 1: `lo_i` (input, electrical)
    - position 2: `lo_q` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `enable` (input, electrical)
    - position 5: `i_out` (output, electrical)
    - position 6: `q_out` (output, electrical)
    - position 7: `lo_i_metric` (output, electrical)
    - position 8: `lo_q_metric` (output, electrical)
    - position 9: `polarity_ok` (output, electrical)

## Public Parameter Contract

- `downconversion_mixer_lo_polarity.vdd` defaults to `0.9` V; valid range: vdd > vss; sets the logic-high output level.
- `downconversion_mixer_lo_polarity.vss` defaults to `0.0` V; valid range: vss < vdd; sets the logic-low output level.
- `downconversion_mixer_lo_polarity.vcm` defaults to `0.45` V; valid range: vss < vcm < vdd; sets RF and output common mode.
- `downconversion_mixer_lo_polarity.vth` defaults to `0.45` V; valid range: vss < vth < vdd; sets the digital-voltage crossing threshold.
- `downconversion_mixer_lo_polarity.conversion_gain` defaults to `0.5` 1; valid range: conversion_gain >= 0; sets baseband conversion gain.
- `downconversion_mixer_lo_polarity.tr` defaults to `2e-10` s; valid range: tr > 0; sets discrete polarity/status smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CENTER`: restore: Reset or disable centers I/Q outputs and clears LO metrics and polarity_ok. Required traces: `time`, `rf_in`, `lo_i`, `lo_q`, `rst`, `enable`, `i_out`, `q_out`, `lo_i_metric`, `lo_q_metric`, `polarity_ok`.
- `P_LO_POLARITY_METRICS`: restore: Each LO threshold state selects signed polarity and is mirrored by its public metric. Required traces: `time`, `rf_in`, `lo_i`, `lo_q`, `rst`, `enable`, `i_out`, `q_out`, `lo_i_metric`, `lo_q_metric`, `polarity_ok`.
- `P_IQ_CONVERSION`: restore: I and Q outputs follow the declared common-mode referenced conversion-gain equations with independent LO signs. Required traces: `time`, `rf_in`, `lo_i`, `lo_q`, `rst`, `enable`, `i_out`, `q_out`, `lo_i_metric`, `lo_q_metric`, `polarity_ok`.
- `P_OUTPUT_CLAMP`: restore: Both baseband outputs remain within the declared supply rails. Required traces: `time`, `rf_in`, `lo_i`, `lo_q`, `rst`, `enable`, `i_out`, `q_out`, `lo_i_metric`, `lo_q_metric`, `polarity_ok`.
- `P_POLARITY_QUALIFICATION`: restore: polarity_ok asserts only after both LO controls have toggled while enabled. Required traces: `time`, `rf_in`, `lo_i`, `lo_q`, `rst`, `enable`, `i_out`, `q_out`, `lo_i_metric`, `lo_q_metric`, `polarity_ok`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not use current contributions, transistor-level devices, validation logic, or simulator side channels.
- Do not hard-code evaluator stimulus timing, stop times, sample windows, or checker tolerances.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `downconversion_mixer_lo_polarity.va`.
Every supplied `.va` file is editable; do not add or omit files.
