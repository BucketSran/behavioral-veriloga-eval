# PA Compression Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `pa_compression_macro.va`:
  - Module `pa_compression_macro` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

## Public Parameter Contract

- `pa_compression_macro.tr` defaults to `1e-10` s; valid range: tr > 0; sets output and metric transition smoothing.
- `pa_compression_macro.vth` defaults to `0.45` V; valid range: 0 < vth < 0.9; sets clk and rst logic threshold.
- `pa_compression_macro.gain` defaults to `3.0`; valid range: gain > 0; sets the moderate-drive voltage gain about 0.45 V common mode.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_COMMON_MODE`: restore: Initialization or active reset returns out to 0.45 V common mode and clears metric to 0 V. Required traces: `time`, `clk`, `rst`, `out`, `metric`.
- `P_CLOCKED_UPDATE`: restore: Out and metric update from the sampled signed drive vin - 0.45 V on rising clk crossings and hold between updates. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_LINEAR_REGION`: restore: When 0.45 V + gain*(vin - 0.45 V) lies from 0.12 V through 0.78 V, out equals that target and metric is 0.1 V. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_SYMMETRIC_COMPRESSION`: restore: Targets above 0.78 V or below 0.12 V are compressed with slope 0.18 about the corresponding boundary, and metric is 0.85 V. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_OUTPUT_CLAMP`: restore: The compressed output remains within 0.02 V through 0.88 V with finite transition smoothing. Required traces: `time`, `out`.

## Modeling Constraints

- Use deterministic sampled voltage-domain behavior.
- Use voltage contributions only and smooth discontinuous output targets.
- Do not add undeclared artifacts, ports, test hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pa_compression_macro.va`.
Every supplied `.va` file is editable; do not add or omit files.
