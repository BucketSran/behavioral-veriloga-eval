# Dynamic Supply Enable Driver Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `dynamic_supply_enable_driver.va`:
  - Module `dynamic_supply_enable_driver` (entry)
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

- `dynamic_supply_enable_driver.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `dynamic_supply_enable_driver.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `dynamic_supply_enable_driver.span_min` defaults to `0.62`; valid range: finite; overrides span_min.
- `dynamic_supply_enable_driver.span_max` defaults to `1.28`; valid range: finite; overrides span_max.
- `dynamic_supply_enable_driver.tr` defaults to `50p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_MEASURE_ANALOG_INPUTS_RELATIVE_TO_THE`: restore: Measure analog inputs relative to the local `vss` rail and normalize by the current local supply span. Let `span = V(vdd, vss)` and treat the row as valid only when `V(en) > vth` and `span_min <= span <= span_max`; otherwise drive `out`, `flag`, and `metric` to `0 V`. If `span` is below `0.05 V`, use `0.05 V` as the normalization span. Define `clip01(y)` as `y` limited to the range `[0, 1]`, `x0 = clip01((V(in0) - V(vss)) / span)`, and `c1 = clip01(V(ctrl1) / vhi)`. Required traces: `time`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `vdd`, `vss`.
- `P_COMPUTE_CORE_0_76_X0_0`: restore: Compute `core = 0.76 * x0 + 0.18 * c1 + 0.12` and drive `out = vhi * clip01(core)` while valid. Assert `flag = vhi` when the local supply span is at least `0.78 V`, otherwise drive `flag = 0 V`. Drive `metric = vhi * clip01(abs((V(in0) - V(vss)) - 0.5 * span) / span)` as the bounded distance from the half-span input point. Required traces: `time`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `vdd`, `vss`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `dynamic_supply_enable_driver.va`.
Every supplied `.va` file is editable; do not add or omit files.
