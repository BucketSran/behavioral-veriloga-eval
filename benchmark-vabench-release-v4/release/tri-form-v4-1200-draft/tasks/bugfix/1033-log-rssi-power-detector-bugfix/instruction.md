# Log RSSI Power Detector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `log_rssi_power_detector.va`:
  - Module `log_rssi_power_detector` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

## Public Parameter Contract

- `log_rssi_power_detector.tr` defaults to `1e-10` s; valid range: tr > 0; sets rise and fall smoothing for out and metric.
- `log_rssi_power_detector.vth` defaults to `0.45` V; valid range: 0 < vth < 0.9; sets the voltage-coded clk and rst decision threshold.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_BASELINE`: restore: Initialization or active reset drives out to 0.12 V and metric to 0 V. Required traces: `time`, `rst`, `out`, `metric`.
- `P_CLOCKED_MAGNITUDE_SAMPLE`: restore: Each rising clk crossing while reset is inactive samples the magnitude abs(vin - 0.45 V); the held outputs do not track vin between samples. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_RSSI_BINS`: restore: Sampled magnitudes below 0.035 V, from 0.035 V to below 0.11 V, from 0.11 V to below 0.22 V, and at least 0.22 V map to out levels 0.12 V, 0.30 V, 0.54 V, and 0.72 V respectively. Required traces: `time`, `clk`, `vin`, `out`.
- `P_AMPLITUDE_METRIC`: restore: Metric equals three times the sampled magnitude, clamped to the 0 V to 0.9 V range. Required traces: `time`, `clk`, `vin`, `metric`.
- `P_OUTPUT_BOUNDS`: restore: Out remains within the public 0.08 V to 0.82 V clamp range with finite transition smoothing. Required traces: `time`, `out`.

## Modeling Constraints

- Use deterministic voltage-domain sampled behavior.
- Keep event-triggered state updates separate from unconditional output contributions.
- Do not add undeclared artifacts, ports, validation state, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `log_rssi_power_detector.va`.
Every supplied `.va` file is editable; do not add or omit files.
