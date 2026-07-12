# Duty-cycle Window Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `duty_cycle_window_monitor.va`:
  - Module `duty_cycle_window_monitor` (entry)
    - position 0: `clk_in` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `duty_min` (inout, electrical)
    - position 4: `duty_max` (inout, electrical)
    - position 5: `duty_metric` (inout, electrical)
    - position 6: `in_window` (inout, electrical)
    - position 7: `valid` (inout, electrical)

## Public Parameter Contract

- `duty_cycle_window_monitor.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `duty_cycle_window_monitor.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `duty_cycle_window_monitor.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `duty_cycle_window_monitor.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `duty_cycle_window_monitor.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `duty_cycle_window_monitor.tick` defaults to `200p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear duty metric, window flag, and `valid`. Required traces: `time`, `clk_in`, `rst`, `enable`, `duty_min`, `duty_max`, `duty_metric`, `in_window`, `valid`.
- `P_MEASURE_HIGH_AND_LOW_INTERVALS_OVER`: restore: Measure high and low intervals over complete clock cycles using threshold crossings. Required traces: `time`, `clk_in`, `rst`, `enable`, `duty_min`, `duty_max`, `duty_metric`, `in_window`, `valid`.
- `P_DRIVE_DUTY_METRIC_AS_THE_MEASURED`: restore: Drive `duty_metric` as the measured high-time fraction mapped to the public voltage range. Required traces: `time`, `clk_in`, `rst`, `enable`, `duty_min`, `duty_max`, `duty_metric`, `in_window`, `valid`.
- `P_ASSERT_IN_WINDOW_ONLY_WHEN_THE`: restore: Assert `in_window` only when the measured duty lies between `duty_min` and `duty_max`. Required traces: `time`, `clk_in`, `rst`, `enable`, `duty_min`, `duty_max`, `duty_metric`, `in_window`, `valid`.
- `P_ASSERT_VALID_AFTER_A_COMPLETE_HIGH`: restore: Assert `valid` after a complete high/low cycle has been observed. Required traces: `time`, `clk_in`, `rst`, `enable`, `duty_min`, `duty_max`, `duty_metric`, `in_window`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `duty_cycle_window_monitor.va`.
Every supplied `.va` file is editable; do not add or omit files.
