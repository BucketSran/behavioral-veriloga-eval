# PAM4 Slicer and Gray Decoder Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `pam4_slicer_gray_decoder.va`:
  - Module `pam4_slicer_gray_decoder` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `bit_msb` (output, electrical)
    - position 5: `bit_lsb` (output, electrical)
    - position 6: `level_metric` (output, electrical)
    - position 7: `valid` (output, electrical)

## Public Parameter Contract

- `pam4_slicer_gray_decoder.vdd` defaults to `0.9` V; valid range: vdd > vss; sets the logic-high output level.
- `pam4_slicer_gray_decoder.vss` defaults to `0.0` V; valid range: vss < vdd; sets the logic-low output level.
- `pam4_slicer_gray_decoder.vth` defaults to `0.45` V; valid range: vss < vth < vdd; sets the digital-voltage crossing threshold.
- `pam4_slicer_gray_decoder.t0` defaults to `0.225` V; valid range: t0 < t1; sets lower slice threshold.
- `pam4_slicer_gray_decoder.t1` defaults to `0.45` V; valid range: t0 < t1 < t2; sets middle slice threshold.
- `pam4_slicer_gray_decoder.t2` defaults to `0.675` V; valid range: t1 < t2; sets upper slice threshold.
- `pam4_slicer_gray_decoder.tr` defaults to `2e-10` s; valid range: tr > 0; sets transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CLEAR`: restore: Reset or disable clears both bits, level metric, and valid. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `bit_msb`, `bit_lsb`, `level_metric`, `valid`.
- `P_RISING_EDGE_SAMPLE_HOLD`: restore: vin is sliced only on enabled rising clk edges and outputs hold between samples. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `bit_msb`, `bit_lsb`, `level_metric`, `valid`.
- `P_PAM4_THRESHOLDS`: restore: The three ordered thresholds divide vin into levels zero through three. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `bit_msb`, `bit_lsb`, `level_metric`, `valid`.
- `P_GRAY_MAPPING`: restore: Levels zero through three map to Gray codes 00, 01, 11, and 10. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `bit_msb`, `bit_lsb`, `level_metric`, `valid`.
- `P_LEVEL_METRIC`: restore: level_metric reports the sliced level as vss plus k/3 of the output span. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `bit_msb`, `bit_lsb`, `level_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not use current contributions, transistor-level devices, validation logic, or simulator side channels.
- Do not hard-code evaluator stimulus timing, stop times, sample windows, or checker tolerances.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pam4_slicer_gray_decoder.va`.
Every supplied `.va` file is editable; do not add or omit files.
