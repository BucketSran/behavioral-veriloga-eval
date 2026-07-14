# LNA Gain Compression Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `lna_gain_compression_macro.va`:
  - Module `lna_gain_compression_macro` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

## Public Parameter Contract

- `lna_gain_compression_macro.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `lna_gain_compression_macro.vth` defaults to `0.45` V; valid range: finite real; sets clk and rst logic threshold.
- `lna_gain_compression_macro.gain` defaults to `2.2` V/V; valid range: gain > 0; sets small-signal gain about 0.45 V common mode.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_AND_RESET_COMMON_MODE`: restore: Initialization sets out to 0.45 V and clears metric; an active-high reset sampled on a rising clk crossing restores the same state. Required traces: `time`, `clk`, `rst`, `out`, `metric`.
- `P_SMALL_SIGNAL_GAIN`: restore: For linear values from 0.14 V through 0.76 V, out equals 0.45 V plus gain times the sampled vin deviation and metric is 0.1 V. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_POSITIVE_COMPRESSION`: restore: Above linear 0.76 V, excess signal is compressed by factor 0.28 and metric is 0.8 V. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_NEGATIVE_COMPRESSION`: restore: Below linear 0.14 V, excess signal is compressed by factor 0.28 and metric is 0.8 V. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_FINAL_OUTPUT_CLAMP`: restore: The final held output remains within 0.04 V through 0.86 V. Required traces: `time`, `out`.
- `P_CLOCKED_HOLD`: restore: Out and metric update on rising clock crossings and hold between samples. Required traces: `time`, `clk`, `vin`, `out`, `metric`.

## Modeling Constraints

- Use deterministic rising-edge sampled piecewise gain compression.
- Use smoothed voltage contributions only.
- Do not use current contributions, transistor-level devices, AC/noise analysis, KCL/KVL assumptions, or validation side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `lna_gain_compression_macro.va`.
Every supplied `.va` file is editable; do not add or omit files.
