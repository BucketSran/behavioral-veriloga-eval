# Power Mode Supply Current Metric

Implement one Verilog-A source file named `power_mode_supply_current_metric.va`.

## Task Contract

Build a voltage-domain bias/reference/power-management macro-model metric. The
module exposes an observable supply-current demand estimate as a voltage-coded
output across enable, power-down, operating mode, load demand, and local supply
conditions.

## Public Verilog-A Interface

```verilog
module power_mode_supply_current_metric(vdd, vss, en, pd, mode, load, isup_metric);
```

All ports are electrical. `vdd` and `vss` are the local supply rails, `en` is an
active-high enable control, `pd` is an active-high power-down control, `mode`
selects a low-current or high-current operating mode, `load` is a normalized
voltage-coded output-load demand, and `isup_metric` is a voltage-coded estimate
of supply-current demand for checking and system-level accounting.

## Public Parameter Contract

- `vth = 0.45 V`: logic threshold for `en`, `pd`, and `mode`.
- `vhi = 0.9 V`: full-scale input level for `load`.
- `vnom = 0.9 V`: nominal supply used for supply-ratio scaling.
- `iq0 = 0.08`, `iq1 = 0.14`: active quiescent metric levels for low and high
  current modes.
- `ipd = 0.01`: power-down metric level.
- `load_gain = 0.20`: additional active metric contribution at full load.
- `tr = 80p`: output transition smoothing time.

## Required Behavior

Drive `isup_metric` as a voltage-coded supply-current estimate. The estimate
must scale with the local supply ratio `V(vdd, vss) / vnom` clipped to the
range `[0, 1.5]`. Normalize load as `V(load, vss) / vhi` clipped to `[0, 1]`.
When the block is disabled or powered down, meaning `V(en) <= vth` or
`V(pd) > vth`, drive `isup_metric = ipd * supply_scale`. Otherwise choose the
active base metric as `iq1` when `V(mode) > vth` and `iq0` when `V(mode) <= vth`,
then drive `isup_metric = (base_metric + load_gain * load_norm) * supply_scale`.
The metric is not a real branch current; it is an observable behavioral
macro-model output.

## Modeling Constraints

Use voltage-domain behavioral Verilog-A only. Do not generate a testbench,
checker logic, branch current contributions, transistor devices, `ddt()`, or
`idt()`. Do not hard-code evaluator stimulus times.

## Output Contract

Return only `power_mode_supply_current_metric.va` implementing the public
module. The file must compile under Spectre-compatible Verilog-A and must not
require additional modules, include files beyond standard disciplines, or
testbench changes.
