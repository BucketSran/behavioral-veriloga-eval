# Power Enable Turn-On Delay Gate

Implement one Verilog-A source file named `power_enable_turnon_delay_gate.va`.

## Task Contract

Build a voltage-domain power sequencing DUT for a biased analog block. The
module samples supply, bias, enable, and power-down conditions, reports sampled
power validity, and releases downstream drive only after a consecutive valid
turn-on delay.

## Public Verilog-A Interface

```verilog
module power_enable_turnon_delay_gate(clk, vdd, vss, vbias, en, pd, pwr_ok, drive_en, delay_mon);
```

All ports are electrical. `clk` is the sequencing clock. `vdd` and `vss` are
the local supply rails. `vbias` is a voltage-coded bias input referenced to
`vss`. `en` is active-high enable, `pd` is active-high power-down, `pwr_ok`
reports the instantaneous power/bias/control validity state, `drive_en` reports
the delayed downstream drive enable, and `delay_mon` exposes bounded turn-on
progress.

## Public Parameter Contract

- `vth = 0.45 V`: logic threshold for `clk`, `en`, and `pd`.
- `vhi = 0.9 V`: high level for voltage-coded outputs.
- `vdd_min = 0.75 V`, `vdd_max = 1.05 V`: valid `V(vdd, vss)` window.
- `vbias_min = 0.25 V`, `vbias_max = 0.75 V`: valid `V(vbias, vss)` window.
- `delay_cycles = 3`: number of consecutive valid rising clock updates required
  before `drive_en` may assert.
- `tr = 60p`: output transition smoothing time.

## Required Behavior

On each rising crossing of `clk`, evaluate whether supply, bias, enable, and
power-down conditions allow operation. Drive `pwr_ok` high whenever the sampled
conditions are valid, meaning `vdd_min <= V(vdd, vss) <= vdd_max`,
`vbias_min <= V(vbias, vss) <= vbias_max`, `V(en) > vth`, and `V(pd) <= vth`.
Maintain an integer consecutive-valid counter. Increment the counter by one on
each sampled valid rising-clock update until it reaches `delay_cycles`; reset
the counter to zero on any sampled invalid update. After applying that update,
assert `drive_en` when the counter is greater than or equal to `delay_cycles`.
Drive `delay_mon = min(vhi, vhi * counter / delay_cycles)` as the bounded
voltage-coded turn-on progress value from `0 V` to `vhi`. Smooth all outputs
with `transition()`.

## Modeling Constraints

Use voltage-domain behavioral Verilog-A only. Do not generate a testbench,
checker logic, branch current contributions, transistor devices, `ddt()`, or
`idt()`. Do not hard-code evaluator stimulus times.

## Output Contract

Return only `power_enable_turnon_delay_gate.va` implementing the public module.
The file must compile under Spectre-compatible Verilog-A and must not require
additional modules, include files beyond standard disciplines, or testbench
changes.
