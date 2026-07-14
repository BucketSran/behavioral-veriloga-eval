# Resettable Phase Toggle Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `resettable_phase_toggle_monitor.va`:
  - Module `resettable_phase_toggle_monitor` (entry)
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

- `resettable_phase_toggle_monitor.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `resettable_phase_toggle_monitor.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `resettable_phase_toggle_monitor.span_min` defaults to `0.62`; valid range: finite; overrides span_min.
- `resettable_phase_toggle_monitor.span_max` defaults to `1.28`; valid range: finite; overrides span_max.
- `resettable_phase_toggle_monitor.tr` defaults to `50p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_MEASURE_ANALOG_INPUTS_RELATIVE_TO_THE`: restore: Measure analog inputs relative to the local `vss` rail and normalize by the current local supply span. Let `span = V(vdd, vss)` and treat the row as valid only when `V(en) > vth` and `span_min <= span <= span_max`. If `span` is below `0.05 V`, use `0.05 V` as the normalization span. Define `clip01(y)` as `y` limited to the range `[0, 1]` and `x0..x3 = clip01((V(inN) - V(vss)) / span)`. Required traces: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.
- `P_INITIALIZE_ALL_OBSERVABLE_STATE_TO_0`: restore: Initialize all observable state to `0 V`. On a rising crossing of `clk` or a rising crossing of `rst`, clear `out`, `flag`, and `metric` when `rst` is high or the row is not valid. Otherwise, when `x0 > 0.50`, toggle `out` between `0 V` and `vhi` and set `flag` equal to the new `out` value; when `x0 <= 0.50`, hold the previous `out` and `flag` values. On every valid update, drive `metric = vhi * clip01(abs(x0 - x1))`; hold observable values between update events. Required traces: `time`, `clk`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `rst`, `vdd`, `vss`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `resettable_phase_toggle_monitor.va`.
Every supplied `.va` file is editable; do not add or omit files.
