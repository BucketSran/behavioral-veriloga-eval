# Clock-and-data Valid Qualifier Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `clock_data_valid_qualifier.va`:
  - Module `clock_data_valid_qualifier` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `data` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `valid_out` (output, electrical)
    - position 5: `edge_age_metric` (output, electrical)
    - position 6: `qualified` (output, electrical)

## Public Parameter Contract

- `clock_data_valid_qualifier.vdd` defaults to `0.9` V; valid range: vdd > vss; sets the logic-high output level.
- `clock_data_valid_qualifier.vss` defaults to `0.0` V; valid range: vss < vdd; sets the logic-low output level.
- `clock_data_valid_qualifier.vth` defaults to `0.45` V; valid range: vss < vth < vdd; sets the digital-voltage crossing threshold.
- `clock_data_valid_qualifier.max_age_cycles` defaults to `3` cycles; valid range: max_age_cycles >= 1; sets the inclusive qualification age limit.
- `clock_data_valid_qualifier.tr` defaults to `2e-10` s; valid range: tr > 0; sets transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CLEAR`: restore: Reset or disable clears valid, qualification, and the public age metric. Required traces: `time`, `clk`, `data`, `rst`, `enable`, `valid_out`, `edge_age_metric`, `qualified`.
- `P_DATA_EDGE_RESTART`: restore: Either polarity data edge restarts the age count at zero while enabled. Required traces: `time`, `clk`, `data`, `rst`, `enable`, `valid_out`, `edge_age_metric`, `qualified`.
- `P_CLOCKED_AGE`: restore: Each later rising clk edge increments age before qualification. Required traces: `time`, `clk`, `data`, `rst`, `enable`, `valid_out`, `edge_age_metric`, `qualified`.
- `P_INCLUSIVE_WINDOW`: restore: Ages one through max_age_cycles are qualified and older ages are not. Required traces: `time`, `clk`, `data`, `rst`, `enable`, `valid_out`, `edge_age_metric`, `qualified`.
- `P_REGISTERED_METRIC`: restore: valid_out is the registered qualified state and the metric reports saturated normalized age. Required traces: `time`, `clk`, `data`, `rst`, `enable`, `valid_out`, `edge_age_metric`, `qualified`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not use current contributions, transistor-level devices, validation logic, or simulator side channels.
- Do not hard-code evaluator stimulus timing, stop times, sample windows, or checker tolerances.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `clock_data_valid_qualifier.va`.
Every supplied `.va` file is editable; do not add or omit files.
