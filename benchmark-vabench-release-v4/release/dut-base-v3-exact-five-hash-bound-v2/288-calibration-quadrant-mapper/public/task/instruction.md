# Calibration Quadrant Mapper

Implement one Verilog-A source file named `calibration_quadrant_mapper.va`.

## Task Contract

Build a voltage-domain analog/mixed-signal helper or monitor. Calibration quadrant mapper using explicit scalar conditions rather than multidimensional array state.

## Public Verilog-A Interface

```verilog
module calibration_quadrant_mapper(in0, in1, in2, in3, ctrl0, ctrl1, vdd, vss, en, out, flag, metric);
```

All ports are electrical. `vdd` and `vss` are the local rails, `en` is an
active-high enable, `in0` through `in3` are voltage-coded analog or lane inputs,
`ctrl0` and `ctrl1` are voltage-coded control inputs, and `out`, `flag`, and
`metric` are voltage-coded observables.

## Public Parameter Contract

- `vth = 0.45 V`: logic threshold for voltage-coded controls.
- `vhi = 0.9 V`: high level for output observables.
- `span_min = 0.62 V`, `span_max = 1.28 V`: legal local supply span measured as
  `V(vdd, vss)`.
- `tr = 50p`: output transition smoothing time.

## Required Behavior

Measure analog inputs relative to the local `vss` rail and normalize by the
current local supply span. Let `span = V(vdd, vss)` and treat the row as valid
only when `V(en) > vth` and `span_min <= span <= span_max`; otherwise drive
`out`, `flag`, and `metric` to `0 V`. If `span` is below `0.05 V`, use
`0.05 V` as the normalization span. Define `clip01(y)` as `y` limited to the
range `[0, 1]`, `x0..x3 = clip01((V(inN) - V(vss)) / span)`,
`c0 = clip01(V(ctrl0) / vhi)`, and `c1 = clip01(V(ctrl1) / vhi)`.

Use the two control levels as a voltage-coded quadrant select: choose `x0` when
`c1 <= 0.5` and `c0 <= 0.5`, `x1` when `c1 <= 0.5` and `c0 > 0.5`, `x2` when
`c1 > 0.5` and `c0 <= 0.5`, and `x3` when `c1 > 0.5` and `c0 > 0.5`. Compute
`core = 0.88 * selected + 0.04`, drive `out = vhi * clip01(core)`, assert
`flag = vhi` when either `c0 > 0.5` or `c1 > 0.5`, otherwise drive
`flag = 0 V`, and drive
`metric = vhi * clip01(((c1 > 0.5 ? 2.0 : 0.0) + (c0 > 0.5 ? 1.0 : 0.0)) / 3.0)`.

## Modeling Constraints

Use Spectre-compatible voltage-domain Verilog-A. Do not use unsupported
`wreal`, `logic`, `assign`, `always`, `task/endtask`, `connectmodule`,
`connectrules`, `specify`, `generate`, recursion, packed logic buses, or
multidimensional array syntax. Do not generate a testbench, checker logic,
current contributions, transistor devices, `ddt()`, or `idt()`.

## Output Contract

Return only `calibration_quadrant_mapper.va` implementing the public module. The file must
compile under Spectre-compatible Verilog-A and must not require additional
modules, nonstandard include files, or testbench changes.
