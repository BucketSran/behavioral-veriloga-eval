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

Measure analog inputs relative to the local `vss` rail and normalize by the
current local supply span. Clear all observables when `en` is low or when the
local supply span is outside the public range. Drive `out` with the
task-specific bounded analog result, drive `flag` with the task-specific
qualification condition, and drive `metric` with a bounded diagnostic magnitude.

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
