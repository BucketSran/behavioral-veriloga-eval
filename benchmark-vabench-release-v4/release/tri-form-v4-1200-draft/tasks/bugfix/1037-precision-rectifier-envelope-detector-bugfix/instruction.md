# Precision Rectifier Envelope Detector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `precision_rectifier_envelope_detector.va`:
  - Module `precision_rectifier_envelope_detector` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `rect` (output, electrical)
    - position 4: `env` (output, electrical)
    - position 5: `metric` (output, electrical)

## Public Parameter Contract

- `precision_rectifier_envelope_detector.vth` defaults to `0.45` V; valid range: 0 < vth < 0.9; sets the clk and rst voltage-coded decision threshold.
- `precision_rectifier_envelope_detector.vcm` defaults to `0.45` V; valid range: 0 <= vcm <= 0.9; sets rectification common mode and envelope reset level.
- `precision_rectifier_envelope_detector.decay` defaults to `0.018` V/update; valid range: decay >= 0; sets the envelope decrement on each sampled decay update.
- `precision_rectifier_envelope_detector.tr` defaults to `1.5e-10` s; valid range: tr > 0; sets env and metric transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_FULL_WAVE_RECTIFICATION`: restore: Rect equals vcm plus the absolute input deviation from vcm, so equal positive and negative excursions produce equal rectified levels, bounded to 0 V through 0.9 V. Required traces: `time`, `vin`, `rect`.
- `P_RESET_ENVELOPE`: restore: Initialization or a rising clk update with rst active restores env to vcm and clears envelope memory. Required traces: `time`, `clk`, `rst`, `env`, `metric`.
- `P_PEAK_ATTACK`: restore: At a rising clk update, a rectified value above the stored envelope is acquired immediately as the new env value. Required traces: `time`, `clk`, `rst`, `rect`, `env`.
- `P_BOUNDED_DECAY`: restore: When rect is below the stored envelope, each rising clk update lowers env by at most decay and never below rect or vcm. Required traces: `time`, `clk`, `rect`, `env`.
- `P_ENVELOPE_LAG_METRIC`: restore: Metric is high while env exceeds rect by more than 30 mV and low otherwise. Required traces: `time`, `rect`, `env`, `metric`.

## Modeling Constraints

- Drive rect as a continuous voltage-domain rectified observable and env/metric from event-updated state.
- Use voltage contributions only; do not use current contributions, transistor-level devices, or AC/noise behavior.
- Do not add validation-only ports, hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `precision_rectifier_envelope_detector.va`.
Every supplied `.va` file is editable; do not add or omit files.
