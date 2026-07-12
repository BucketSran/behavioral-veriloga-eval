# Edge Delay Qualified Driver

Implement one Verilog-A source file named `edge_delay_qualified_driver.va`.

## Task Contract

Build a voltage-domain analog/mixed-signal helper or monitor. Clock-edge qualified delay-style driver replacing specify/specparam timing with explicit event state.

## Public Verilog-A Interface

```verilog
module edge_delay_qualified_driver(clk, rst, in0, in1, in2, in3, ctrl0, ctrl1, vdd, vss, en, out, flag, metric);
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
local supply span is outside the public range. The DUT updates its observable state on the public clock edge and clears state while reset is high. Drive `out` with the
task-specific bounded analog result, drive `flag` with the task-specific
qualification condition, and drive `metric` with a bounded diagnostic magnitude.

## Modeling Constraints

Use Spectre-compatible voltage-domain Verilog-A. Do not use unsupported
`wreal`, `logic`, `assign`, `always`, `task/endtask`, `connectmodule`,
`connectrules`, `specify`, `generate`, recursion, packed logic buses, or
multidimensional array syntax. Do not generate a testbench, checker logic,
current contributions, transistor devices, `ddt()`, or `idt()`.

## Output Contract

Return only `edge_delay_qualified_driver.va` implementing the public module. The file must
compile under Spectre-compatible Verilog-A and must not require additional
modules, nonstandard include files, or testbench changes.
