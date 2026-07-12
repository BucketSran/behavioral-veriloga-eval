# Rail Ramp Rate Startup Monitor

Implement one Verilog-A source file named `rail_ramp_rate_startup_monitor.va`.

## Task Contract

Build a voltage-domain startup monitor for a locally supplied analog block. The
module samples the local rail on a clock, checks whether the rail is inside the
allowed operating window, qualifies the startup ramp rate, and releases a
startup-ready flag only after the rail has settled for consecutive sampled
updates.

## Public Verilog-A Interface

```verilog
module rail_ramp_rate_startup_monitor(clk, vdd, vss, en, rail_ok, ramp_ok, startup_ready, slew_metric);
```

All ports are electrical. `clk` is the sampling clock. `vdd` and `vss` are the
local supply rails. `en` is an active-high monitor enable. `rail_ok` reports the
sampled local supply window result, `ramp_ok` reports whether the sampled rail
movement is acceptable for the current startup phase, `startup_ready` is the
delayed readiness output, and `slew_metric` exposes bounded sampled rail
movement.

## Public Parameter Contract

- `vth = 0.45 V`: logic threshold for `clk` and `en`.
- `vhi = 0.9 V`: high level for voltage-coded outputs.
- `vdd_min = 0.72 V`, `vdd_max = 1.08 V`: valid `V(vdd, vss)` operating
  window.
- `vready = 0.86 V`: sampled rail level above which settling qualification is
  required before readiness can assert.
- `dv_min = 0.025 V`, `dv_max = 0.20 V`: acceptable positive sampled rail
  movement before the rail reaches `vready`.
- `dv_settle_max = 0.030 V`: maximum absolute sampled rail movement while the
  rail is settling above `vready`.
- `ready_cycles = 3`: number of consecutive settled sampled updates required
  before `startup_ready` may assert.
- `tr = 60p`: output transition smoothing time.

## Required Behavior

On each rising crossing of `clk`, sample `V(vdd, vss)` and compute the sampled
change from the previous clock update. Drive `rail_ok` high only while `en` is
high and the sampled local supply is inside the public operating window. Before
the sampled rail reaches `vready`, drive `ramp_ok` high only when the sampled
positive rail movement is between `dv_min` and `dv_max`. Once the sampled rail
is at or above `vready`, drive `ramp_ok` high only when the absolute sampled
movement is no larger than `dv_settle_max`. Accumulate consecutive settled
samples only when `rail_ok` is high, `ramp_ok` is high, and the rail is at or
above `vready`; clear that accumulator on any sampled invalid condition. Assert
`startup_ready` only after `ready_cycles` consecutive settled updates. Drive
`slew_metric` as `vhi * clip(abs(delta_v) / dv_max, 0, 1)`. Smooth the
voltage-coded outputs with `transition()`.

## Modeling Constraints

Use voltage-domain behavioral Verilog-A only. Do not generate a testbench,
checker logic, branch current contributions, transistor devices, `ddt()`, or
`idt()`. Do not hard-code evaluator stimulus times.

## Output Contract

Return only `rail_ramp_rate_startup_monitor.va` implementing the public module.
The file must compile under Spectre-compatible Verilog-A and must not require
additional modules, include files beyond standard disciplines, or testbench
changes.
