# Settling Time Measurement Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `settling_time_measurement_tb.va`:
  - Module `settling_time_measurement_tb` (entry)
    - position 0: `step` (input, electrical)
    - position 1: `vout` (output, electrical)
    - position 2: `done` (output, electrical)

## Public Parameter Contract

- `settling_time_measurement_tb.tr` defaults to `3e-10` s; valid range: finite real; use tr >= 0 for physical transition smoothing; sets smoothing for vout and done.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_ZERO_STATE`: restore: The settling-response state initializes to 0 V and vout begins from that state. Required traces: `time`, `vout`.
- `P_FIRST_ORDER_UPDATE`: restore: At each 1 ns update, the response advances by 0.04 times the difference between step and its previous value. Required traces: `time`, `step`, `vout`.
- `P_RESPONSE_CONVERGENCE`: restore: For a constant input step, vout approaches the step value monotonically without overshoot under the public recurrence. Required traces: `time`, `step`, `vout`.
- `P_DONE_TIME_GATE`: restore: Done remains low through 120 ns regardless of the response level. Required traces: `time`, `vout`, `done`.
- `P_DONE_SETTLED_GATE`: restore: After 120 ns, done is high only while the internal settled response is above 0.75 V and otherwise remains low. Required traces: `time`, `step`, `vout`, `done`.

## Modeling Constraints

- Implement the public 1 ns discrete-time first-order settling response and completion flag as a DUT measurement helper.
- Use smoothed voltage contributions only.
- Do not emit a Spectre deck or use current contributions, transistor-level devices, waveform files, validation artifacts, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `settling_time_measurement_tb.va`.
Every supplied `.va` file is editable; do not add or omit files.
