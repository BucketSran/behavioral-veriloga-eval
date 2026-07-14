# Enable Saturating Ready Counter

Implement one Verilog-A source file named `enable_saturating_ready_counter.va`.

## Task Contract

Build a voltage-domain analog/mixed-signal helper or monitor. Enable-qualified saturating ready counter for power/reference settling flows.

## Public Verilog-A Interface

```verilog
module enable_saturating_ready_counter(clk, rst, in0, in1, in2, in3, ctrl0, ctrl1, vdd, vss, en, out, flag, metric);
```

All ports are electrical. `vdd` and `vss` are the local rails, `en` is an
active-high enable, `in0` through `in3` are voltage-coded analog or lane inputs,
`ctrl0` and `ctrl1` are voltage-coded control inputs, and `out`, `flag`, and
`metric` are voltage-coded observables. For this row, `clk` is the sampling
clock and `rst` clears the observable state.

## Public Parameter Contract

- `vth = 0.45 V`: logic threshold for voltage-coded controls.
- `vhi = 0.9 V`: high level for output observables.
- `span_min = 0.62 V`, `span_max = 1.28 V`: legal local supply span measured as
  `V(vdd, vss)`.
- `tr = 50p`: output transition smoothing time.

## Required Behavior

Measure analog inputs relative to the local `vss` rail and normalize by the
current local supply span. Let `span = V(vdd, vss)` and treat the row as valid
only when `V(en) > vth` and `span_min <= span <= span_max`. If `span` is below
`0.05 V`, use `0.05 V` as the normalization span. Define `clip01(y)` as `y`
limited to the range `[0, 1]` and
`x0..x3 = clip01((V(inN) - V(vss)) / span)`.

Initialize a sampled ready count to zero. On a rising edge of `clk` or on reset
assertion, clear the count and all observables when `rst` is high or the row is
not valid. Otherwise, increment the count by one and saturate it at `4.0` when
`x0 > 0.25` and `x1 > 0.20`; clear the count to zero when either condition is
not met. After the update, drive `out = vhi * clip01(count / 4.0)`, assert
`flag = vhi` when `count >= 3.0`, otherwise drive `flag = 0 V`, and drive
`metric = vhi * clip01(abs(x0 - x1))`. Hold the last observable values between
update events.

## Modeling Constraints

Use Spectre-compatible voltage-domain Verilog-A. Do not use unsupported
`wreal`, `logic`, `assign`, `always`, `task/endtask`, `connectmodule`,
`connectrules`, `specify`, `generate`, recursion, packed logic buses, or
multidimensional array syntax. Do not generate a testbench, checker logic,
current contributions, transistor devices, `ddt()`, or `idt()`.

## Output Contract

Return only `enable_saturating_ready_counter.va` implementing the public module. The file must
compile under Spectre-compatible Verilog-A and must not require additional
modules, nonstandard include files, or testbench changes.
