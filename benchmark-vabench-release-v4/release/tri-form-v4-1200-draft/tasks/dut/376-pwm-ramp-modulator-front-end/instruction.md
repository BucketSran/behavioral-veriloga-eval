# PWM Ramp Modulator Front-end

## Task Contract

Implement one Verilog-A DUT artifact for `PWM Ramp Modulator Front-end`.

- Target artifact: `pwm_ramp_modulator.va`
- Public top module: `pwm_ramp_modulator`
- Task level: `L1`
- Circuit category: `power_control`

## Public Verilog-A Interface

Declare module `pwm_ramp_modulator` with positional electrical ports `clk, rst, enable, vctrl, ramp_out, pwm_out, cycle_start, duty_metric`. All ports are electrical.

`clk`, `rst`, and `enable` are voltage-coded controls. `vctrl` is the analog duty command. `ramp_out`, `pwm_out`, `cycle_start`, and `duty_metric` are observable voltage-domain outputs.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vdd = 0.9 V`: logic-high and ramp full-scale level
- `vss = 0.0 V`: logic-low and ramp reset level
- `vth = 0.45 V`: logic threshold for controls
- `ramp_step = 0.15 V`: ramp increment per enabled clock edge
- `tr = 100 ps`: output transition smoothing time

## Required Behavior

- Reset or a low `enable` clears the ramp, PWM output, cycle marker, and duty metric.
- On each enabled rising `clk` edge, advance `ramp_out` by `ramp_step` and wrap to `vss` at full scale.
- `cycle_start` pulses high for the clock edge where the ramp wraps.
- `pwm_out` is high when `vctrl` is greater than the current ramp value and low otherwise.
- `duty_metric` tracks the clipped duty command between `vss` and `vdd`.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not use current contributions, transistor-level devices, AC/noise analysis, random sources, table files, or topology-level assumptions. Use explicit initialization for stored state and smooth public voltage outputs with transition-style behavior.

Do not add extra ports, debug-only files, verification harnesses, simulation decks, generated result files, logs, reports, or pass/fail flags.

## Output Contract

Return exactly one complete source artifact named `pwm_ramp_modulator.va`.
