# Supply Bias Validity Gate

Implement one Verilog-A source file named `supply_bias_validity_gate.va`.

## Task Contract

Build a voltage-domain bias/reference/power-management DUT. The module reports
whether local supply, local ground, and local bias conditions are valid, then
gates a downstream drive-enable output with public enable and power-down inputs.

## Public Verilog-A Interface

```verilog
module supply_bias_validity_gate(vdd, vss, vbias, en, pd, ok, gated);
```

All ports are electrical. `vdd` and `vss` are the local supply rails, `vbias`
is a voltage-coded bias input referenced to `vss`, `en` is an active-high enable
control, `pd` is an active-high power-down control, `ok` reports whether the
analog supply and bias conditions are valid, and `gated` reports whether the
block should be allowed to drive downstream circuitry.

## Public Parameter Contract

- `vth = 0.45 V`: logic threshold for `en` and `pd`.
- `vhi = 0.9 V`: high level for `ok` and `gated`.
- `vdd_min = 0.75 V`, `vdd_max = 1.05 V`: valid supply-voltage window measured
  as `V(vdd, vss)`.
- `vss_max = 0.08 V`: maximum absolute ground-rail displacement allowed for
  normal operation.
- `vbias_min = 0.25 V`, `vbias_max = 0.75 V`: valid bias-voltage window
  measured as `V(vbias, vss)`.
- `tr = 50p`: output transition smoothing time.

## Required Behavior

Model a reusable supply/bias validity gate for a behavioral AMS block. Drive
`ok` high only when the local supply is inside the supply window, the local
ground rail is close enough to the global reference, and the bias input is
inside its `vss`-referenced window. Drive `gated` high only when `ok` is high,
`en` is high, and `pd` is low. Both outputs must be voltage-coded and smoothed
with `transition()`.

## Modeling Constraints

Use voltage-domain behavioral Verilog-A only. Do not generate a testbench,
checker logic, current contributions, transistor devices, `ddt()`, or `idt()`.
Do not hard-code evaluator stimulus times.

## Output Contract

Return only `supply_bias_validity_gate.va` implementing the public module. The
file must compile under Spectre-compatible Verilog-A and must not require
additional modules, include files beyond standard disciplines, or testbench
changes.
