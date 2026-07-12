# Differential Common Mode Window Monitor

Implement one Verilog-A source file named
`differential_common_mode_window_monitor.va`.

## Task Contract

Build a voltage-domain input-validity monitor for a differential analog
front-end. The module checks whether the differential input magnitude remains
inside a public linear range, whether the instantaneous common-mode level stays
near a reference, and whether the enabled input pair is valid for downstream
behavioral processing.

## Public Verilog-A Interface

```verilog
module differential_common_mode_window_monitor(vip, vin, vcm_ref, en, diff_ok, cm_ok, valid, diff_metric, cm_metric);
```

All ports are electrical. `vip` and `vin` are the differential input pair.
`vcm_ref` is the common-mode reference. `en` is active-high enable. `diff_ok`
reports the differential magnitude window, `cm_ok` reports the common-mode
window, `valid` reports enabled full input validity, and `diff_metric` plus
`cm_metric` expose bounded analog error magnitudes.

## Public Parameter Contract

- `vth = 0.45 V`: logic threshold for `en`.
- `vhi = 0.9 V`: high level for voltage-coded outputs.
- `diff_max = 0.30 V`: maximum allowed `abs(V(vip) - V(vin))`.
- `diff_fullscale = 0.45 V`: full-scale value for `diff_metric`.
- `cm_tol = 0.080 V`: maximum allowed absolute common-mode error from
  `vcm_ref`.
- `cm_fullscale = 0.160 V`: full-scale value for `cm_metric`.
- `tr = 50p`: output transition smoothing time for Boolean outputs.

## Required Behavior

Continuously compute `vdiff = V(vip) - V(vin)` and
`vcm = 0.5 * (V(vip) + V(vin))`. Drive `diff_ok` high only while `en` is high
and `abs(vdiff)` is no larger than `diff_max`. Drive `cm_ok` high only while
`en` is high and `abs(vcm - V(vcm_ref))` is no larger than `cm_tol`. Drive
`valid` high only when both `diff_ok` and `cm_ok` would be high. Drive
`diff_metric` as `vhi * clip(abs(vdiff) / diff_fullscale, 0, 1)` and
`cm_metric` as `vhi * clip(abs(vcm - V(vcm_ref)) / cm_fullscale, 0, 1)`.
Smooth the voltage-coded Boolean outputs with `transition()`.

## Modeling Constraints

Use voltage-domain behavioral Verilog-A only. Do not generate a testbench,
checker logic, branch current contributions, transistor devices, `ddt()`, or
`idt()`. Do not hard-code evaluator stimulus times.

## Output Contract

Return only `differential_common_mode_window_monitor.va` implementing the public
module. The file must compile under Spectre-compatible Verilog-A and must not
require additional modules, include files beyond standard disciplines, or
testbench changes.
