# Reference Settling Window Monitor

Implement one Verilog-A source file named `reference_settling_window_monitor.va`.

## Task Contract

Build a measurement-style bias/reference monitor. The module samples a
reference voltage against a target, reports the bounded error magnitude, and
asserts validity only after consecutive in-window samples.

## Public Verilog-A Interface

```verilog
module reference_settling_window_monitor(clk, rst, ref, target, valid, err_metric, settle_mon);
```

All ports are electrical. `clk` is the sampling clock, `rst` is active-high
reset, `ref` is the observed reference or bias voltage, `target` is the desired
reference level, `valid` reports stable in-window settling, `err_metric`
reports the bounded absolute error magnitude, and `settle_mon` exposes bounded
consecutive in-window progress.

## Public Parameter Contract

- `vth = 0.45 V`: logic threshold for `clk` and `rst`.
- `vhi = 0.9 V`: high level for voltage-coded outputs.
- `tol = 0.035 V`: allowed absolute error around `target`.
- `err_scale = 0.20 V`: error that maps to full-scale `err_metric`.
- `settle_cycles = 3`: consecutive in-window rising clock updates required
  before `valid` may assert.
- `tr = 80p`: output transition smoothing time.

## Required Behavior

On each rising crossing of `clk`, measure the absolute difference between `ref`
and `target`. Drive `err_metric` as the clipped error magnitude scaled by
`err_scale`. While reset is high, clear the settling counter and keep `valid`
low. Otherwise, increment the counter on each in-window sample, clear it on any
out-of-window sample, and assert `valid` only after `settle_cycles` consecutive
in-window samples. Drive `settle_mon` as bounded progress from 0 to `vhi`.
Smooth all outputs with `transition()`.

## Modeling Constraints

Use voltage-domain behavioral Verilog-A only. Do not generate a testbench,
checker logic, branch current contributions, transistor devices, `ddt()`, or
`idt()`. Do not hard-code evaluator stimulus times.

## Output Contract

Return only `reference_settling_window_monitor.va` implementing the public
module. The file must compile under Spectre-compatible Verilog-A and must not
require additional modules, include files beyond standard disciplines, or
testbench changes.
