# Fixed Gain Amplifier Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `gain_amp_fixed.va`:
  - Module `gain_amp_fixed` (entry)
    - position 0: `VIN_P` (input, electrical)
    - position 1: `VIN_N` (input, electrical)
    - position 2: `VOUT_P` (output, electrical)
    - position 3: `VOUT_N` (output, electrical)

## Public Parameter Contract

- `gain_amp_fixed.vdd` defaults to `0.9` V; valid range: vdd > 0; sets twice the output common-mode level.
- `gain_amp_fixed.ACTUAL_GAIN` defaults to `8.64` V/V; valid range: ACTUAL_GAIN > 0; sets positive differential voltage gain.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DIFFERENTIAL_GAIN`: restore: The output differential equals ACTUAL_GAIN times the input differential. Required traces: `time`, `vin_p`, `vin_n`, `vout_p`, `vout_n`.
- `P_POSITIVE_POLARITY`: restore: A positive input differential produces a positive output differential and a negative input differential produces a negative output differential. Required traces: `time`, `vin_p`, `vin_n`, `vout_p`, `vout_n`.
- `P_OUTPUT_COMMON_MODE`: restore: The output pair remains centered at vdd/2 independently of input common mode. Required traces: `time`, `vin_p`, `vin_n`, `vout_p`, `vout_n`.
- `P_SYMMETRIC_OUTPUT_PAIR`: restore: Half the amplified differential is added to VOUT_P and half is subtracted from VOUT_N. Required traces: `time`, `vin_p`, `vin_n`, `vout_p`, `vout_n`.
- `P_PARAMETER_OVERRIDES`: restore: Legal ACTUAL_GAIN and vdd overrides alter differential gain and output common mode according to their declared meanings. Required traces: `time`, `vin_p`, `vin_n`, `vout_p`, `vout_n`.

## Modeling Constraints

- Use deterministic pure voltage-domain differential amplification.
- Preserve the public positive polarity and vdd/2 common-mode relation.
- Do not use transistor-level devices, AC/noise analysis, waveform artifacts, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `gain_amp_fixed.va`.
Every supplied `.va` file is editable; do not add or omit files.
