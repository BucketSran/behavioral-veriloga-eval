# PWM Ramp Modulator Front-end Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `pwm_ramp_modulator.va`:
  - Module `pwm_ramp_modulator` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `vctrl` (input, electrical)
    - position 4: `ramp_out` (output, electrical)
    - position 5: `pwm_out` (output, electrical)
    - position 6: `cycle_start` (output, electrical)
    - position 7: `duty_metric` (output, electrical)

## Public Parameter Contract

- `pwm_ramp_modulator.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `pwm_ramp_modulator.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `pwm_ramp_modulator.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `pwm_ramp_modulator.ramp_step` defaults to `0.15`; valid range: finite; overrides ramp_step.
- `pwm_ramp_modulator.tr` defaults to `100p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_OR_A_LOW_ENABLE_CLEARS`: restore: Reset or a low `enable` clears the ramp, PWM output, cycle marker, and duty metric. Required traces: `time`, `clk`, `rst`, `enable`, `vctrl`, `ramp_out`, `pwm_out`, `cycle_start`, `duty_metric`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: restore: On each enabled rising `clk` edge, advance `ramp_out` by `ramp_step` and wrap to `vss` at full scale. Required traces: `time`, `clk`, `rst`, `enable`, `vctrl`, `ramp_out`, `pwm_out`, `cycle_start`, `duty_metric`.
- `P_CYCLE_START_PULSES_HIGH_FOR_THE`: restore: `cycle_start` pulses high for the clock edge where the ramp wraps. Required traces: `time`, `clk`, `rst`, `enable`, `vctrl`, `ramp_out`, `pwm_out`, `cycle_start`, `duty_metric`.
- `P_PWM_OUT_IS_HIGH_WHEN_VCTRL`: restore: `pwm_out` is high when `vctrl` is greater than the current ramp value and low otherwise. Required traces: `time`, `clk`, `rst`, `enable`, `vctrl`, `ramp_out`, `pwm_out`, `cycle_start`, `duty_metric`.
- `P_DUTY_METRIC_TRACKS_THE_CLIPPED_DUTY`: restore: `duty_metric` tracks the clipped duty command between `vss` and `vdd`. Required traces: `time`, `clk`, `rst`, `enable`, `vctrl`, `ramp_out`, `pwm_out`, `cycle_start`, `duty_metric`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pwm_ramp_modulator.va`.
Every supplied `.va` file is editable; do not add or omit files.
