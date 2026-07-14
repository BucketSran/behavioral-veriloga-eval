# Duty-cycle Corrector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `dcc_top.va`:
  - Module `dcc_top` (entry)
    - position 0: `clk_in` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `clk_out` (output, electrical)
    - position 4: `trim_3` (output, electrical)
    - position 5: `trim_2` (output, electrical)
    - position 6: `trim_1` (output, electrical)
    - position 7: `trim_0` (output, electrical)
    - position 8: `duty_metric` (output, electrical)
    - position 9: `locked` (output, electrical)
- Artifact `duty_meter.va`:
  - Module `duty_meter` (required_submodule)
    - position 0: `clk_in` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `duty_metric` (output, electrical)
    - position 4: `measure_clk` (output, electrical)
- Artifact `trim_controller.va`:
  - Module `trim_controller` (required_submodule)
    - position 0: `measure_clk` (input, electrical)
    - position 1: `duty_metric` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `trim_3` (output, electrical)
    - position 5: `trim_2` (output, electrical)
    - position 6: `trim_1` (output, electrical)
    - position 7: `trim_0` (output, electrical)
    - position 8: `locked` (output, electrical)
- Artifact `delay_pair.va`:
  - Module `delay_pair` (required_submodule)
    - position 0: `clk_in` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `trim_3` (input, electrical)
    - position 4: `trim_2` (input, electrical)
    - position 5: `trim_1` (input, electrical)
    - position 6: `trim_0` (input, electrical)
    - position 7: `clk_out` (output, electrical)

## Public Parameter Contract

- `dcc_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module dcc_top.
- `dcc_top.vss` defaults to `0.0`; valid range: finite; overrides vss for module dcc_top.
- `dcc_top.vth` defaults to `0.45`; valid range: finite; overrides vth for module dcc_top.
- `dcc_top.target_duty` defaults to `0.5`; valid range: finite; overrides target_duty for module dcc_top.
- `dcc_top.duty_tol` defaults to `0.03`; valid range: finite; overrides duty_tol for module dcc_top.
- `dcc_top.trim_step` defaults to `5e-12`; valid range: finite; overrides trim_step for module dcc_top.
- `dcc_top.tr` defaults to `100p`; valid range: finite; overrides tr for module dcc_top.
- `duty_meter.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module duty_meter.
- `duty_meter.vss` defaults to `0.0`; valid range: finite; overrides vss for module duty_meter.
- `duty_meter.vth` defaults to `0.45`; valid range: finite; overrides vth for module duty_meter.
- `duty_meter.tr` defaults to `100p`; valid range: finite; overrides tr for module duty_meter.
- `trim_controller.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module trim_controller.
- `trim_controller.vss` defaults to `0.0`; valid range: finite; overrides vss for module trim_controller.
- `trim_controller.vth` defaults to `0.45`; valid range: finite; overrides vth for module trim_controller.
- `trim_controller.target_duty` defaults to `0.5`; valid range: finite; overrides target_duty for module trim_controller.
- `trim_controller.duty_tol` defaults to `0.03`; valid range: finite; overrides duty_tol for module trim_controller.
- `trim_controller.tr` defaults to `100p`; valid range: finite; overrides tr for module trim_controller.
- `delay_pair.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module delay_pair.
- `delay_pair.vss` defaults to `0.0`; valid range: finite; overrides vss for module delay_pair.
- `delay_pair.vth` defaults to `0.45`; valid range: finite; overrides vth for module delay_pair.
- `delay_pair.trim_step` defaults to `5e-12`; valid range: finite; overrides trim_step for module delay_pair.
- `delay_pair.tr` defaults to `100p`; valid range: finite; overrides tr for module delay_pair.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CLEAR`: restore: Reset or low enable clears trim, duty metric, lock, and output clock. Required traces: `time`, `clk_in`, `rst`, `enable`, `clk_out`, `trim_3`, `trim_2`, `trim_1`, `trim_0`, `duty_metric`, `locked`.
- `P_DUTY_MEASUREMENT`: restore: The metric reports high-time fraction over each complete input-clock cycle. Required traces: `time`, `clk_in`, `rst`, `enable`, `duty_metric`.
- `P_TRIM_DIRECTION`: restore: The trim code moves up below the target window and down above it, with rail saturation. Required traces: `time`, `clk_in`, `rst`, `enable`, `trim_3`, `trim_2`, `trim_1`, `trim_0`, `duty_metric`.
- `P_EDGE_DELAY`: restore: Rising edges pass without intentional delay while falling edges receive the latched trim-code delay. Required traces: `time`, `clk_in`, `clk_out`, `rst`, `enable`, `trim_3`, `trim_2`, `trim_1`, `trim_0`.
- `P_LOCK_QUALIFICATION`: restore: Lock asserts after three consecutive measured cycles inside the target window. Required traces: `time`, `clk_in`, `rst`, `enable`, `duty_metric`, `locked`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Preserve the declared module graph, port order, parameter override behavior, and public trace observability.
- Do not hard-code evaluator stimulus, stop times, sample windows, checker tolerances, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `dcc_top.va`, `duty_meter.va`, `trim_controller.va`, `delay_pair.va`.
Every supplied `.va` file is editable; do not add or omit files.
