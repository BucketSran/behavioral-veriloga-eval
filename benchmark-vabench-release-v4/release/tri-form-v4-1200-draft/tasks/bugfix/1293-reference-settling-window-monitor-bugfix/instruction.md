# Reference Settling Window Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `reference_settling_window_monitor.va`:
  - Module `reference_settling_window_monitor` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `ref` (input, electrical)
    - position 3: `target` (input, electrical)
    - position 4: `valid` (output, electrical)
    - position 5: `err_metric` (output, electrical)
    - position 6: `settle_mon` (output, electrical)

## Public Parameter Contract

- `reference_settling_window_monitor.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `reference_settling_window_monitor.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `reference_settling_window_monitor.tol` defaults to `0.035`; valid range: finite; overrides tol.
- `reference_settling_window_monitor.err_scale` defaults to `0.20`; valid range: finite; overrides err_scale.
- `reference_settling_window_monitor.settle_cycles` defaults to `3`; valid range: finite; overrides settle_cycles.
- `reference_settling_window_monitor.tr` defaults to `80p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_EACH_RISING_CROSSING_OF_CLK`: restore: On each rising crossing of `clk`, measure the absolute difference between `ref` and `target`. Drive `err_metric` as the clipped error magnitude scaled by `err_scale`. While reset is high, clear the settling counter and keep `valid` low. Otherwise, increment the counter on each in-window sample, clear it on any out-of-window sample, and assert `valid` only after `settle_cycles` consecutive in-window samples. Drive `settle_mon` as bounded progress from 0 to `vhi`. Smooth all outputs with `transition()`. Required traces: `time`, `clk`, `err_metric`, `ref`, `rst`, `settle_mon`, `target`, `valid`.
- `P_BUILD_A_MEASUREMENT_STYLE_BIAS_REFERENCE`: restore: Build a measurement-style bias/reference monitor. The module samples a reference voltage against a target, reports the bounded error magnitude, and asserts validity only after consecutive in-window samples. Required traces: `time`, `clk`, `err_metric`, `ref`, `rst`, `settle_mon`, `target`, `valid`.
- `P_VTH_0_45_V_LOGIC_THRESHOLD`: restore: `vth = 0.45 V`: logic threshold for `clk` and `rst`. Required traces: `time`, `clk`, `err_metric`, `ref`, `rst`, `settle_mon`, `target`, `valid`.
- `P_VHI_0_9_V_HIGH_LEVEL`: restore: `vhi = 0.9 V`: high level for voltage-coded outputs. Required traces: `time`, `clk`, `err_metric`, `ref`, `rst`, `settle_mon`, `target`, `valid`.
- `P_TOL_0_035_V_ALLOWED_ABSOLUTE`: restore: `tol = 0.035 V`: allowed absolute error around `target`. Required traces: `time`, `clk`, `err_metric`, `ref`, `rst`, `settle_mon`, `target`, `valid`.
- `P_ERR_SCALE_0_20_V_ERROR`: restore: `err_scale = 0.20 V`: error that maps to full-scale `err_metric`. Required traces: `time`, `clk`, `err_metric`, `ref`, `rst`, `settle_mon`, `target`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `reference_settling_window_monitor.va`.
Every supplied `.va` file is editable; do not add or omit files.
