# Ready Reduction Fault Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `ready_reduction_fault_monitor.va`:
  - Module `ready_reduction_fault_monitor` (entry)
    - position 0: `in0` (input, electrical)
    - position 1: `in1` (input, electrical)
    - position 2: `in2` (input, electrical)
    - position 3: `in3` (input, electrical)
    - position 4: `ctrl0` (input, electrical)
    - position 5: `ctrl1` (input, electrical)
    - position 6: `vdd` (input, electrical)
    - position 7: `vss` (input, electrical)
    - position 8: `en` (input, electrical)
    - position 9: `out` (output, electrical)
    - position 10: `flag` (output, electrical)
    - position 11: `metric` (output, electrical)

## Public Parameter Contract

- `ready_reduction_fault_monitor.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `ready_reduction_fault_monitor.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `ready_reduction_fault_monitor.span_min` defaults to `0.62`; valid range: finite; overrides span_min.
- `ready_reduction_fault_monitor.span_max` defaults to `1.28`; valid range: finite; overrides span_max.
- `ready_reduction_fault_monitor.tr` defaults to `50p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_MEASURE_ANALOG_INPUTS_RELATIVE_TO_THE`: restore: Measure analog inputs relative to the local `vss` rail and normalize by the current local supply span. Let `span = V(vdd, vss)` and treat the row as valid only when `V(en) > vth` and `span_min <= span <= span_max`; otherwise drive `out`, `flag`, and `metric` to `0 V`. If `span` is below `0.05 V`, use `0.05 V` as the normalization span. Define `clip01(y)` as `y` limited to the range `[0, 1]` and `x0..x3 = clip01((V(inN) - V(vss)) / span)`. Required traces: `time`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `vdd`, `vss`.
- `P_COUNT_HOW_MANY_OF_X0_X1`: restore: Count how many of `x0`, `x1`, `x2`, and `x3` are greater than `0.50`. Drive `out = vhi * clip01(count / 4.0)` and `metric = vhi * clip01(count / 4.0)`. Assert `flag = vhi` when `count >= 3`, otherwise drive `flag = 0 V`. Required traces: `time`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `vdd`, `vss`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `ready_reduction_fault_monitor.va`.
Every supplied `.va` file is editable; do not add or omit files.
