# Falling Edge Calibration Sampler Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `falling_edge_calibration_sampler.va`:
  - Module `falling_edge_calibration_sampler` (entry)
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

- `falling_edge_calibration_sampler.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `falling_edge_calibration_sampler.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `falling_edge_calibration_sampler.span_min` defaults to `0.62`; valid range: finite; overrides span_min.
- `falling_edge_calibration_sampler.span_max` defaults to `1.28`; valid range: finite; overrides span_max.
- `falling_edge_calibration_sampler.tr` defaults to `50p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_MEASURE_ANALOG_INPUTS_RELATIVE_TO_THE`: restore: Measure analog inputs relative to the local `vss` rail and normalize by the current local supply span. Let `span = V(vdd, vss)` and treat the row as valid only when `V(en) > vth` and `span_min <= span <= span_max`. If `span` is below `0.05 V`, use `0.05 V` as the normalization span. Define `clip01(y)` as `y` limited to the range `[0, 1]` and `x0..x3 = clip01((V(inN) - V(vss)) / span)`. Required traces: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.
- `P_INITIALIZE_OUT_FLAG_AND_METRIC_TO`: restore: Initialize `out`, `flag`, and `metric` to `0 V`. On a falling edge of `clk`, clear all observables when `rst` is high or the row is not valid. Otherwise sample the comparison `x0 > x1`: drive `out = vhi` for true and `out = 0 V` for false, drive `flag` to the same value as `out`, and drive `metric = vhi * clip01(abs(x0 - x1))`. Hold the last observable values between falling clock edges, except that a reset assertion clears them. Required traces: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `falling_edge_calibration_sampler.va`.
Every supplied `.va` file is editable; do not add or omit files.
