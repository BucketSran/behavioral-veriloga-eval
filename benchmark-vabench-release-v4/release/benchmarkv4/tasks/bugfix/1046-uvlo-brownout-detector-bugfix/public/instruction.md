# UVLO Brownout Detector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `uvlo_brownout_detector.va`:
  - Module `uvlo_brownout_detector` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

## Public Parameter Contract

- `uvlo_brownout_detector.tr` defaults to `1e-10` s; valid range: tr > 0; sets out and metric transition smoothing.
- `uvlo_brownout_detector.vth` defaults to `0.45` V; valid range: 0 < vth < 0.9; sets clk and rst voltage-coded logic threshold.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_FAULT`: restore: Active reset clears the power-good out signal and drives metric to the public fault code 0.9 V. Required traces: `time`, `clk`, `rst`, `out`, `metric`.
- `P_UPPER_TRIP_ASSERT`: restore: On a sampled update, vin strictly greater than 0.65 V asserts power-good out. Required traces: `time`, `clk`, `rst`, `vin`, `out`.
- `P_HYSTERESIS_HOLD`: restore: For sampled vin values from 0.55 V through 0.65 V inclusive, out preserves its previous power-good state. Required traces: `time`, `clk`, `vin`, `out`.
- `P_BROWNOUT_CLEAR`: restore: On a sampled update, vin strictly less than 0.55 V clears out to the brownout state. Required traces: `time`, `clk`, `rst`, `vin`, `out`.
- `P_STATUS_DISTINCTION`: restore: Metric is the checker-observable status code: 0.1 V when out is power-good high and 0.9 V when reset, undervoltage, or brownout is active. Required traces: `time`, `vin`, `out`, `metric`.

## Modeling Constraints

- Use deterministic sampled voltage-domain hysteresis state.
- Do not use current contributions, transistor-level devices, AC/noise analysis, or KCL/KVL regulation loops.
- Do not add validation-only state, ports, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `uvlo_brownout_detector.va`.
Every supplied `.va` file is editable; do not add or omit files.
