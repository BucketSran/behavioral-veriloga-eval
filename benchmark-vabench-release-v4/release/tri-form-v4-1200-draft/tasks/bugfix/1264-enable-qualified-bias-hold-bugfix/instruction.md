# Enable Qualified Bias Hold Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `enable_qualified_bias_hold.va`:
  - Module `enable_qualified_bias_hold` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `in0` (input, electrical)
    - position 3: `in1` (input, electrical)
    - position 4: `in2` (input, electrical)
    - position 5: `in3` (input, electrical)
    - position 6: `ctrl0` (input, electrical)
    - position 7: `ctrl1` (input, electrical)
    - position 8: `vdd` (input, electrical)
    - position 9: `vss` (input, electrical)
    - position 10: `en` (input, electrical)
    - position 11: `out` (output, electrical)
    - position 12: `flag` (output, electrical)
    - position 13: `metric` (output, electrical)

## Public Parameter Contract

- `enable_qualified_bias_hold.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `enable_qualified_bias_hold.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `enable_qualified_bias_hold.span_min` defaults to `0.62`; valid range: finite; overrides span_min.
- `enable_qualified_bias_hold.span_max` defaults to `1.28`; valid range: finite; overrides span_max.
- `enable_qualified_bias_hold.tr` defaults to `50p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_MEASURE_ANALOG_INPUTS_RELATIVE_TO_THE`: restore: Measure analog inputs relative to the local `vss` rail and normalize by the current local supply span. Let `span = V(vdd, vss)` and treat the row as valid only when `V(en) > vth` and `span_min <= span <= span_max`. If `span` is below `0.05 V`, use `0.05 V` as the normalization span. Define `clip01(y)` as `y` limited to the range `[0, 1]`, `x0..x3 = clip01((V(inN) - V(vss)) / span)`, and `c0 = clip01(V(ctrl0) / vhi)`. Required traces: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.
- `P_INITIALIZE_THE_HELD_BIAS_OUTPUT_FLAG`: restore: Initialize the held bias output, `flag`, and `metric` to `0 V`. On a rising edge of `clk`, clear all observables when `rst` is high or the row is not valid. Otherwise, when `c0 > 0.45`, update the held output to `out = vhi * clip01(0.70 * x0 + 0.30 * x1)` and assert `flag = vhi`. When `c0 <= 0.45`, hold the previous output value and drive `flag = 0 V`. After the update or hold decision, drive `metric = vhi * clip01(abs((out / vhi) - x2))`. Hold the last observable values between rising clock edges, except that a reset assertion clears them. Required traces: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `enable_qualified_bias_hold.va`.
Every supplied `.va` file is editable; do not add or omit files.
