# Thermometer Bus Encoder Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `thermometer_bus_encoder.va`:
  - Module `thermometer_bus_encoder` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `t0` (output, electrical)
    - position 2: `t1` (output, electrical)
    - position 3: `t2` (output, electrical)
    - position 4: `t3` (output, electrical)
    - position 5: `t4` (output, electrical)
    - position 6: `t5` (output, electrical)
    - position 7: `t6` (output, electrical)
    - position 8: `t7` (output, electrical)
    - position 9: `t8` (output, electrical)
    - position 10: `t9` (output, electrical)
    - position 11: `t10` (output, electrical)
    - position 12: `t11` (output, electrical)
    - position 13: `t12` (output, electrical)
    - position 14: `t13` (output, electrical)
    - position 15: `t14` (output, electrical)
    - position 16: `t15` (output, electrical)

## Public Parameter Contract

- `thermometer_bus_encoder.vref` defaults to `1` V; valid range: vref > 0; sets the analog full-scale reference and segment span.
- `thermometer_bus_encoder.vh` defaults to `0.9` V; valid range: vh > 0; sets the voltage-coded segment high level.
- `thermometer_bus_encoder.tr` defaults to `2e-11` s; valid range: tr > 0; sets segment-output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_PREFIX_CODE`: restore: Active segment outputs always form a contiguous prefix beginning at t0; no higher segment may be high while a lower segment is low. Required traces: `time`, `vin`, `t0`, `t1`, `t2`, `t3`, `t4`, `t5`, `t6`, `t7`, `t8`, `t9`, `t10`, `t11`, `t12`, `t13`, `t14`, `t15`.
- `P_ORDERED_ACTIVATION`: restore: As vin increases, segments activate in order t0 through t15 and the active-segment count never decreases. Required traces: `time`, `vin`, `t0`, `t1`, `t2`, `t3`, `t4`, `t5`, `t6`, `t7`, `t8`, `t9`, `t10`, `t11`, `t12`, `t13`, `t14`, `t15`.
- `P_UNIFORM_SEGMENTS`: restore: The clipped 0-to-vref input span selects among sixteen equal-width thermometer segments. Required traces: `time`, `vin`, `t0`, `t1`, `t2`, `t3`, `t4`, `t5`, `t6`, `t7`, `t8`, `t9`, `t10`, `t11`, `t12`, `t13`, `t14`, `t15`.
- `P_INPUT_CLIPPING`: restore: Inputs at or below 0 V produce no active segments, and inputs at or above vref produce all sixteen active segments. Required traces: `time`, `vin`, `t0`, `t1`, `t2`, `t3`, `t4`, `t5`, `t6`, `t7`, `t8`, `t9`, `t10`, `t11`, `t12`, `t13`, `t14`, `t15`.
- `P_OUTPUT_LEVELS`: restore: Each inactive segment approaches 0 V and each active segment approaches vh with finite transition smoothing. Required traces: `time`, `t0`, `t1`, `t2`, `t3`, `t4`, `t5`, `t6`, `t7`, `t8`, `t9`, `t10`, `t11`, `t12`, `t13`, `t14`, `t15`.

## Modeling Constraints

- Use deterministic combinational voltage-domain thermometer encoding.
- Preserve segment order from t0 through t15.
- Use smooth voltage contributions and do not emit a binary-coded word, hidden state, validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `thermometer_bus_encoder.va`.
Every supplied `.va` file is editable; do not add or omit files.
