# Explicit Replicated Stage Chain

Implement one Verilog-A source file named `explicit_replicated_stage_chain.va`.

## Task Contract

Build a voltage-domain analog/mixed-signal helper or monitor. Explicitly unrolled replicated-stage chain metric replacing generate/genvar syntax with observable stage composition.

## Public Verilog-A Interface

```verilog
module explicit_replicated_stage_chain(in0, in1, in2, in3, ctrl0, ctrl1, vdd, vss, en, out, flag, metric);
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

Let `span = V(vdd, vss)` and
`xN = clip01((V(inN) - V(vss)) / max(span, 0.05))` for all four inputs.
The row is valid exactly when `V(en) > vth` and
`span_min <= span <= span_max`; otherwise drive all outputs to `0 V`.
When valid, let `core = 0.36*x0 + 0.28*x1 + 0.18*x2 + 0.10*x3 + 0.04`.
Drive `out = vhi * clip01(core)`, assert `flag = vhi` exactly when
`core > 0.48`, and drive `metric = vhi * clip01(abs(x0 - x1) / 0.55)`.
The `ctrl0` and `ctrl1` inputs do not affect these observables.

## Modeling Constraints

Use Spectre-compatible voltage-domain Verilog-A. Do not use unsupported
`wreal`, `logic`, `assign`, `always`, `task/endtask`, `connectmodule`,
`connectrules`, `specify`, `generate`, recursion, packed logic buses, or
multidimensional array syntax. Do not generate a testbench, checker logic,
current contributions, transistor devices, `ddt()`, or `idt()`.

## Output Contract

Return only `explicit_replicated_stage_chain.va` implementing the public module. The file must
compile under Spectre-compatible Verilog-A and must not require additional
modules, nonstandard include files, or testbench changes.
