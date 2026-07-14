# Gain Estimator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `gain_estimator.va`:
  - Module `gain_estimator` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `vinp` (input, electrical)
    - position 3: `vinn` (input, electrical)
    - position 4: `voutp` (input, electrical)
    - position 5: `voutn` (input, electrical)
    - position 6: `gain_out` (output, electrical)
    - position 7: `valid` (output, electrical)

## Public Parameter Contract

- `gain_estimator.sample_period` defaults to `1e-09` s; valid range: sample_period > 0; sets periodic extrema-sampling interval.
- `gain_estimator.start_time` defaults to `2e-08` s; valid range: start_time >= 0; sets when samples begin contributing to extrema.
- `gain_estimator.gain_scale` defaults to `10.0` V/V represented at full scale; valid range: gain_scale > 0; sets gain represented by full-scale gain_out.
- `gain_estimator.min_input_span` defaults to `0.02` V; valid range: min_input_span > 0; sets minimum input span required to assert valid.
- `gain_estimator.tedge` defaults to `2e-10` s; valid range: tedge > 0; sets gain_out and valid transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_START_TIME_GATING`: restore: Samples before start_time do not contribute to measured input or output extrema and valid remains low. Required traces: `time`, `vinp`, `vinn`, `voutp`, `voutn`, `valid`.
- `P_PERIODIC_EXTREMA`: restore: At each sample_period after start_time, the estimator updates minima and maxima of the input and output differential voltages. Required traces: `time`, `vinp`, `vinn`, `voutp`, `voutn`, `gain_out`, `valid`.
- `P_VALIDITY_THRESHOLD`: restore: Valid remains rail-low until the observed input differential span exceeds min_input_span and remains rail-high afterwards. Required traces: `time`, `vdd`, `vss`, `vinp`, `vinn`, `valid`.
- `P_SPAN_RATIO`: restore: Once valid, the measured gain equals output differential span divided by input differential span. Required traces: `time`, `vinp`, `vinn`, `voutp`, `voutn`, `gain_out`, `valid`.
- `P_NORMALIZED_GAIN_OUTPUT`: restore: Gain_out equals the VDD-to-VSS rail span multiplied by measured gain divided by gain_scale. Required traces: `time`, `vdd`, `vss`, `gain_out`, `valid`.
- `P_EVENT_UPDATED_TARGETS`: restore: Gain_out and valid reflect event-updated retained targets with finite smoothing rather than continuously varying transition inputs. Required traces: `time`, `gain_out`, `valid`.

## Modeling Constraints

- Use deterministic periodic extrema sampling after start_time.
- Use event-updated metric and validity targets with rail-referenced smoothing.
- Do not generate testbenches or waveform artifacts or use current contributions, transistor-level devices, ddt, or idt.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `gain_estimator.va`.
Every supplied `.va` file is editable; do not add or omit files.
