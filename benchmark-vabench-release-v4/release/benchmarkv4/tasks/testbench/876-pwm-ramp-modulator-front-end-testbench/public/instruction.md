# PWM Ramp Modulator Front-end Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `PWM Ramp Modulator Front-end` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `pwm_ramp_modulator` as `XDUT` with ordered public binding: clk=clk, rst=rst, enable=enable, vctrl=vctrl, ramp_out=ramp_out, pwm_out=pwm_out, cycle_start=cycle_start, duty_metric=duty_metric.

## Public Parameter Contract

- `pwm_ramp_modulator.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `pwm_ramp_modulator.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `pwm_ramp_modulator.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `pwm_ramp_modulator.ramp_step` defaults to `0.15`; valid range: finite; overrides ramp_step.
- `pwm_ramp_modulator.tr` defaults to `100p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_OR_A_LOW_ENABLE_CLEARS`: exercise and make observable: Reset or a low `enable` clears the ramp, PWM output, cycle marker, and duty metric. Required traces: `time`, `clk`, `rst`, `enable`, `vctrl`, `ramp_out`, `pwm_out`, `cycle_start`, `duty_metric`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: exercise and make observable: On each enabled rising `clk` edge, advance `ramp_out` by `ramp_step` and wrap to `vss` at full scale. Required traces: `time`, `clk`, `rst`, `enable`, `vctrl`, `ramp_out`, `pwm_out`, `cycle_start`, `duty_metric`.
- `P_CYCLE_START_PULSES_HIGH_FOR_THE`: exercise and make observable: `cycle_start` pulses high for the clock edge where the ramp wraps. Required traces: `time`, `clk`, `rst`, `enable`, `vctrl`, `ramp_out`, `pwm_out`, `cycle_start`, `duty_metric`.
- `P_PWM_OUT_IS_HIGH_WHEN_VCTRL`: exercise and make observable: `pwm_out` is high when `vctrl` is greater than the current ramp value and low otherwise. Required traces: `time`, `clk`, `rst`, `enable`, `vctrl`, `ramp_out`, `pwm_out`, `cycle_start`, `duty_metric`.
- `P_DUTY_METRIC_TRACKS_THE_CLIPPED_DUTY`: exercise and make observable: `duty_metric` tracks the clipped duty command between `vss` and `vdd`. Required traces: `time`, `clk`, `rst`, `enable`, `vctrl`, `ramp_out`, `pwm_out`, `cycle_start`, `duty_metric`.

The required trace names are: `time`, `clk`, `rst`, `enable`, `vctrl`, `ramp_out`, `pwm_out`, `cycle_start`, `duty_metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
