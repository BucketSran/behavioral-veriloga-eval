# Configurable Startup Policy

Implement one Verilog-A source file named `configurable_startup_policy.va`.

## Task Contract

Build a voltage-domain analog/mixed-signal helper or monitor. Parameter-style startup policy selector replacing unsupported preprocessor variants with runtime-observable behavior.

## Public Verilog-A Interface

```verilog
module configurable_startup_policy(in0, in1, in2, in3, ctrl0, ctrl1, vdd, vss, en, out, flag, metric);
```

All ports are electrical. `vdd` and `vss` are the local rails, `en` is an
active-high enable, `in0` through `in3` are voltage-coded analog or lane inputs,
`ctrl0` and `ctrl1` are voltage-coded control inputs, and `out`, `flag`, and
`metric` are voltage-coded observables. For clocked rows, `clk` is the sampling
clock and `rst` clears the observable state.

## Public Parameter Contract

- `vth = 0.45 V`: logic threshold for voltage-coded controls.
- `vhi = 0.9 V`: high level for output observables.
- `span_min = 0.62 V`, `span_max = 1.28 V`: legal local supply span measured as
  `V(vdd, vss)`.
- `tr = 50p`: output transition smoothing time.

## Required Behavior

Let `span = V(vdd, vss)` and `x0 = clip01((V(in0) - V(vss)) / max(span, 0.05))`.
The row is valid exactly when `V(en) > vth` and
`span_min <= span <= span_max`; otherwise drive all outputs to `0 V`.
When valid, drive `out = vhi * x0`, assert `flag = vhi` exactly when
`0.24 <= x0 <= 0.72` and `clip01(V(ctrl0) / vhi) > 0.35`, and drive
`metric = vhi * clip01(abs(x0 - 0.48) / 0.48)`. Inputs `in1..in3` and
`ctrl1` do not affect these observables.

## Modeling Constraints

Use Spectre-compatible voltage-domain Verilog-A. Do not use unsupported
`wreal`, `logic`, `assign`, `always`, `task/endtask`, `connectmodule`,
`connectrules`, `specify`, `generate`, recursion, packed logic buses, or
multidimensional array syntax. Do not generate a testbench, checker logic,
current contributions, transistor devices, `ddt()`, or `idt()`.

## Output Contract

Return only `configurable_startup_policy.va` implementing the public module. The file must
compile under Spectre-compatible Verilog-A and must not require additional
modules, nonstandard include files, or testbench changes.
