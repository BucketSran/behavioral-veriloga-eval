# Rail Normalized Metric Mapper Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `rail_normalized_metric_mapper.va`:
  - Module `rail_normalized_metric_mapper` (entry)
    - position 0: `meas` (input, electrical)
    - position 1: `vdd` (input, electrical)
    - position 2: `vss` (input, electrical)
    - position 3: `en` (input, electrical)
    - position 4: `norm` (output, electrical)
    - position 5: `valid` (output, electrical)

## Public Parameter Contract

- `rail_normalized_metric_mapper.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `rail_normalized_metric_mapper.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `rail_normalized_metric_mapper.span_min` defaults to `0.60`; valid range: finite; overrides span_min.
- `rail_normalized_metric_mapper.span_max` defaults to `1.20`; valid range: finite; overrides span_max.
- `rail_normalized_metric_mapper.tr` defaults to `50p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_NORMALIZE_MEAS_RELATIVE_TO_THE_LOCAL`: restore: Normalize meas relative to the local V(vdd,vss) span and vss rail. Required traces: `time`, `en`, `meas`, `norm`, `valid`, `vdd`, `vss`.
- `P_CLIP_THE_NORMALIZED_METRIC_TO_THE`: restore: Clip the normalized metric to the public voltage-coded range. Required traces: `time`, `en`, `meas`, `norm`, `valid`, `vdd`, `vss`.
- `P_ASSERT_VALID_ONLY_WHEN_ENABLE_IS`: restore: Assert valid only when enable is high, supply span is valid, and the measurement lies inside the local rail window. Required traces: `time`, `en`, `meas`, `norm`, `valid`, `vdd`, `vss`.
- `P_CLEAR_NORM_AND_VALID_WHILE_DISABLED`: restore: Clear norm and valid while disabled or under the minimum supply span. Required traces: `time`, `en`, `meas`, `norm`, `valid`, `vdd`, `vss`.
- `P_USE_LOCAL_ANALOG_HELPER_FUNCTIONS_RATHER`: restore: Use local analog helper functions rather than user task/endtask syntax. Required traces: `time`, `en`, `meas`, `norm`, `valid`, `vdd`, `vss`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `rail_normalized_metric_mapper.va`.
Every supplied `.va` file is editable; do not add or omit files.
