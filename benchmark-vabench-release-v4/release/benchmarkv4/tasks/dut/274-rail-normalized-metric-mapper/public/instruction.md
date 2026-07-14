# Rail Normalized Metric Mapper

## Task Contract
Implement the DUT form for canonical family `274` as Spectre-compatible voltage-domain behavioral Verilog-A. Produce exactly `rail_normalized_metric_mapper.va` and satisfy the public observable contract below for `Rail Normalized Metric Mapper`. The task level is `L1` and the category is `measurement_instrumentation_flows`.

## Public Verilog-A Interface
```verilog
module rail_normalized_metric_mapper(meas, vdd, vss, en, norm, valid);
```
All listed ports are electrical and must keep this order:
- `meas` (input, electrical, position 0)
- `vdd` (input, electrical, position 1)
- `vss` (input, electrical, position 2)
- `en` (input, electrical, position 3)
- `norm` (output, electrical, position 4)
- `valid` (output, electrical, position 5)

## Public Parameter Contract
- `vth` (real, default `0.45`): overrides vth.
- `vhi` (real, default `0.9`): overrides vhi.
- `span_min` (real, default `0.60`): overrides span_min.
- `span_max` (real, default `1.20`): overrides span_max.
- `tr` (real, default `50p`): overrides tr.

## Required Behavior
- `P_NORMALIZE_MEAS_RELATIVE_TO_THE_LOCAL`: Normalize meas relative to the local V(vdd,vss) span and vss rail.
- `P_CLIP_THE_NORMALIZED_METRIC_TO_THE`: Clip the normalized metric to the public voltage-coded range.
- `P_ASSERT_VALID_ONLY_WHEN_ENABLE_IS`: Assert valid only when enable is high, supply span is valid, and the measurement lies inside the local rail window.
- `P_CLEAR_NORM_AND_VALID_WHILE_DISABLED`: Clear norm and valid while disabled or under the minimum supply span.
- `P_USE_LOCAL_ANALOG_HELPER_FUNCTIONS_RATHER`: Use local analog helper functions rather than user task/endtask syntax.

The evaluator saves and may inspect these public trace signals: `time`, `en`, `meas`, `norm`, `valid`, `vdd`, `vss`.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only internals, or simulator side channels.
- Do not emit checker code, score logic, private oracle assumptions, or testbench-specific timing shortcuts.
- No public support source files are required; the solver DUT bundle consists only of the requested target artifact(s).
- Keep candidate DUT code separate from evaluator/testbench files; the solver-owned boundary is the target artifact list only.

## Output Contract
Return only the Verilog-A source artifact(s) named in Section 1. The artifact(s) must compile without nonstandard include files, generated testbenches, undeclared helper modules outside the declared bundle, or changes to the public/evaluator decks.
