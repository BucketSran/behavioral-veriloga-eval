# Power-On Reset Detector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `power_on_reset_detector.va`:
  - Module `power_on_reset_detector` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

## Public Parameter Contract

- `power_on_reset_detector.tr` defaults to `1e-10` s; valid range: tr > 0; sets output and metric transition smoothing.
- `power_on_reset_detector.vth` defaults to `0.45` V; valid range: 0 < vth < 0.9; sets clk and rst logic threshold.
- `power_on_reset_detector.vtrip` defaults to `0.62` V; valid range: 0 < vtrip < 0.9; sets the monitored-supply power-good threshold.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_ASSERTED_UNSAFE`: restore: Out is active-high reset and remains asserted while rst is high or vin is below vtrip. Required traces: `time`, `rst`, `vin`, `out`.
- `P_DELAYED_RELEASE`: restore: After rst releases and vin is power-good, out stays asserted for four rising clk updates before deasserting. Required traces: `time`, `clk`, `rst`, `vin`, `out`.
- `P_RELEASE_STATUS`: restore: Metric uses an intermediate status level during the release delay, is high after delayed reset release completes, and is cleared when reset is reasserted or supply is not power-good. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_FAULT_REASSERTION`: restore: A new reset assertion or a brownout below vtrip immediately reasserts out and clears the accumulated release delay, independent of the next clk edge. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_VOLTAGE_CODED_LEVELS`: restore: Out and metric use bounded voltage-coded low and high levels with finite transition smoothing. Required traces: `time`, `out`, `metric`.

## Modeling Constraints

- Use deterministic voltage-domain reset-sequencing behavior.
- Do not use current contributions, transistor-level devices, AC/noise analysis, or KCL/KVL regulation loops.
- Do not encode a particular validation stimulus, stop time, or sample window.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `power_on_reset_detector.va`.
Every supplied `.va` file is editable; do not add or omit files.
